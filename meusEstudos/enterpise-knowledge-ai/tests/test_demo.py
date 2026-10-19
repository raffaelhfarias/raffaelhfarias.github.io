from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO
from threading import Event
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy import create_engine, func, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app import demo
from app.config import settings
from app.db import Base, DemoBudget, DemoSession, get_db, now
from app.main import app
from app.nvidia import ProviderError
from app.security import token_hash

HEADERS = {"X-Demo-Request": "1"}


class Provider:
    passages = 0

    def embed(self, texts, input_type):
        if input_type == "passage":
            self.passages += 1
        return [[1.0, 0.0] for text in texts]

    def answer(self, question, sources):
        if "salário" in question:
            return {"answer": "", "source_ids": []}
        return {"answer": "15 dias corridos.", "source_ids": [sources[0]["id"]]}


@pytest.fixture
def environment(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{(tmp_path / 'demo.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        db.add(DemoBudget(id=1, window_start=now(), uploads=0, questions=0))
        db.commit()

    def database():
        with factory() as db:
            yield db

    provider = Provider()
    monkeypatch.setattr(demo, "NvidiaClient", lambda: provider)
    monkeypatch.setattr(demo, "SessionLocal", factory)
    monkeypatch.setattr(settings(), "demo_enabled", True)
    app.dependency_overrides[get_db] = database
    with TestClient(app, base_url="https://testserver", headers=HEADERS) as client:
        yield client, factory, provider
    app.dependency_overrides.clear()
    engine.dispose()


def test_example_questions_abstention_reload_and_removal(environment):
    client, factory, provider = environment
    response = client.post("/v1/demo/example")
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie
    assert "no-store" in response.headers["cache-control"]
    secret = client.cookies.get(demo.COOKIE)
    with factory() as db:
        assert db.get(DemoSession, token_hash(secret)) is not None
        assert db.get(DemoSession, secret) is None
    result = client.post("/v1/demo/questions", json={"question": "Qual é o prazo?"})
    assert result.status_code == 200
    assert result.json()["questions_remaining"] == 4
    assert "15 dias" in result.json()["sources"][0]["text"]
    result = client.post("/v1/demo/questions", json={"question": "Qual é o salário?"})
    assert result.json()["sources"] == []
    assert "Não encontrei" in result.json()["answer"]
    assert provider.passages == 1
    assert client.get("/v1/demo/session").json()["questions_remaining"] == 3
    assert client.post("/v1/demo/example").status_code == 409
    assert client.delete("/v1/demo/session").status_code == 204
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(DemoSession)) == 0
    assert client.get("/v1/demo/session").status_code == 401


def test_five_attempts_are_enforced_server_side(environment):
    client, _factory, _provider = environment
    client.post("/v1/demo/example")
    for remaining in range(4, -1, -1):
        result = client.post("/v1/demo/questions", json={"question": "Prazo?"})
        assert result.json()["questions_remaining"] == remaining
    assert client.post("/v1/demo/questions", json={"question": "Mais?"}).status_code == 409


def test_sessions_are_isolated_and_expire(environment):
    client, factory, _provider = environment
    client.post("/v1/demo/example")
    with TestClient(app, base_url="https://testserver", headers=HEADERS) as stranger:
        assert stranger.get("/v1/demo/session").status_code == 401
        stranger.cookies.set(demo.COOKIE, "forged")
        assert stranger.get("/v1/demo/session").status_code == 410
        assert stranger.post("/v1/demo/questions", json={"question": "Prazo?"}).status_code == 410
        stranger.delete("/v1/demo/session")
    assert client.get("/v1/demo/session").status_code == 200
    with factory() as db:
        db.execute(update(DemoSession).values(expires_at=now() - timedelta(seconds=1)))
        db.commit()
    assert client.get("/v1/demo/session").status_code == 410
    assert client.post("/v1/demo/questions", json={"question": "Prazo?"}).status_code == 410
    demo.cleanup_expired()
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(DemoSession)) == 0


def test_shared_budget_survives_session_deletion(environment, monkeypatch):
    client, factory, _provider = environment
    monkeypatch.setattr(settings(), "demo_uploads_per_hour", 1)
    client.post("/v1/demo/example")
    client.delete("/v1/demo/session")
    response = client.post("/v1/demo/example")
    assert response.status_code == 429
    assert "no-store" in response.headers["cache-control"]
    with factory() as db:
        db.execute(update(DemoBudget).values(window_start=now() - timedelta(hours=1)))
        db.commit()
    assert client.post("/v1/demo/example").status_code == 200


def test_shared_question_budget_does_not_consume_session_attempt(environment, monkeypatch):
    client, _factory, _provider = environment
    monkeypatch.setattr(settings(), "demo_questions_per_hour", 1)
    client.post("/v1/demo/example")
    assert client.post("/v1/demo/questions", json={"question": "Prazo?"}).status_code == 200
    assert client.post("/v1/demo/questions", json={"question": "Prazo?"}).status_code == 429
    assert client.get("/v1/demo/session").json()["questions_remaining"] == 4


def test_provider_error_is_sanitized_and_counts_attempt(environment, monkeypatch):
    client, _factory, provider = environment
    client.post("/v1/demo/example")

    def fail(*args):
        raise ProviderError("private-key-or-document-content")

    monkeypatch.setattr(provider, "answer", fail)
    response = client.post("/v1/demo/questions", json={"question": "Prazo?"})
    assert response.status_code == 503
    assert "private-key" not in response.text
    info = client.get("/v1/demo/session").json()
    assert info["questions_remaining"] == 4 and info["busy"] is False


def test_concurrent_question_is_rejected_without_extra_provider_call(environment, monkeypatch):
    client, _factory, provider = environment
    client.post("/v1/demo/example")
    entered, release = Event(), Event()

    def slow_answer(question, sources):
        entered.set()
        assert release.wait(5)
        return {"answer": "15 dias.", "source_ids": [sources[0]["id"]]}

    monkeypatch.setattr(provider, "answer", slow_answer)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(client.post, "/v1/demo/questions", json={"question": "Prazo?"})
        try:
            assert entered.wait(5)
            response = client.post("/v1/demo/questions", json={"question": "Outra?"})
            assert response.status_code == 409
        finally:
            release.set()
        assert pending.result().status_code == 200
    assert client.get("/v1/demo/session").json()["questions_remaining"] == 4


def test_docx_upload_validates_and_extracts_content(environment):
    client, _factory, _provider = environment
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        )
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Reembolso em 15 dias.</w:t></w:r></w:p></w:body></w:document>',
        )
    response = client.post("/v1/demo/document?filename=manual.docx", content=buffer.getvalue())
    assert response.status_code == 200
    result = client.post("/v1/demo/questions", json={"question": "Prazo?"}).json()
    assert "Reembolso em 15 dias" in result["sources"][0]["text"]


@pytest.mark.parametrize(
    "filename,content",
    [("x.pdf", b"fake"), ("x.docx", b"fake"), ("x.txt", b"text"), ("x.pdf", b"")],
)
def test_invalid_files_do_not_reach_provider(environment, filename, content):
    client, _factory, provider = environment
    assert client.post(f"/v1/demo/document?filename={filename}", content=content).status_code == 400
    assert provider.passages == 0


def test_bounded_bodies_empty_questions_and_feature_gate(environment, monkeypatch):
    client, _factory, _provider = environment
    monkeypatch.setattr(settings(), "max_upload_bytes", 10)
    assert client.post("/v1/demo/document?filename=x.pdf", content=b"x" * 11).status_code == 413
    assert client.post("/v1/demo/questions", content=b"x" * 8001).status_code == 413
    assert client.post("/v1/demo/questions", json={"question": " "}).status_code == 422
    assert client.post("/v1/demo/questions", json={"question": "x" * 1001}).status_code == 422
    assert client.post("/v1/demo/example", headers={"X-Demo-Request": ""}).status_code == 403
    assert (
        client.post("/v1/demo/example", headers={"Origin": "https://another.test"}).status_code
        == 403
    )
    monkeypatch.setattr(settings(), "demo_enabled", False)
    assert client.post("/v1/demo/example").status_code == 503


def test_pdf_upload_has_page_source_and_rejects_page_limit(environment, monkeypatch):
    client, _factory, provider = environment
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    contents = DecodedStreamObject()
    contents.set_data(b"BT /F1 12 Tf 10 100 Td (Prazo: 15 dias.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(contents)
    stream = BytesIO()
    writer.write(stream)
    assert (
        client.post("/v1/demo/document?filename=prazo.pdf", content=stream.getvalue()).status_code
        == 200
    )
    result = client.post("/v1/demo/questions", json={"question": "Prazo?"}).json()
    assert result["sources"][0]["page"] == 1
    client.delete("/v1/demo/session")
    writer.add_blank_page(width=300, height=300)
    stream = BytesIO()
    writer.write(stream)
    monkeypatch.setattr(settings(), "max_pdf_pages", 1)
    assert (
        client.post("/v1/demo/document?filename=grande.pdf", content=stream.getvalue()).status_code
        == 400
    )
    assert provider.passages == 1


def test_session_expiring_during_answer_does_not_return_sources(environment, monkeypatch):
    client, factory, provider = environment
    client.post("/v1/demo/example")

    def expire(question, sources):
        with factory() as db:
            db.execute(update(DemoSession).values(expires_at=now() - timedelta(seconds=1)))
            db.commit()
        return {"answer": "15 dias.", "source_ids": [sources[0]["id"]]}

    monkeypatch.setattr(provider, "answer", expire)
    response = client.post("/v1/demo/questions", json={"question": "Prazo?"})
    assert response.status_code == 410
    assert "sources" not in response.json()


def test_upload_budget_is_atomic_during_concurrent_provider_work(environment, monkeypatch):
    client, _factory, provider = environment
    monkeypatch.setattr(settings(), "demo_uploads_per_hour", 1)
    entered, release = Event(), Event()

    def slow_embed(texts, input_type):
        entered.set()
        assert release.wait(5)
        return [[1.0, 0.0] for text in texts]

    monkeypatch.setattr(provider, "embed", slow_embed)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(client.post, "/v1/demo/example")
        try:
            assert entered.wait(5)
            assert client.post("/v1/demo/example").status_code == 429
        finally:
            release.set()
        assert pending.result().status_code == 200


def test_database_error_does_not_expose_document_parameters(environment):
    client, _factory, _provider = environment

    class UnavailableDatabase:
        def scalar(self, statement):
            raise OperationalError("query", {"document": "private text"}, Exception("secret"))

    def unavailable():
        yield UnavailableDatabase()

    app.dependency_overrides[get_db] = unavailable
    client.cookies.set(demo.COOKIE, "opaque-token")
    response = client.get("/v1/demo/session")
    assert response.status_code == 503
    assert response.json() == {"detail": "demo_database_unavailable"}
    assert "no-store" in response.headers["cache-control"]


def test_https_origin_and_secure_cookie_behind_http_reverse_proxy(environment):
    _client, _factory, _provider = environment
    with TestClient(
        app,
        base_url="http://testserver",
        headers={
            **HEADERS,
            "Origin": "https://testserver",
        },
    ) as proxy:
        response = proxy.post("/v1/demo/example")
        assert response.status_code == 200
        assert "Secure" in response.headers["set-cookie"]
