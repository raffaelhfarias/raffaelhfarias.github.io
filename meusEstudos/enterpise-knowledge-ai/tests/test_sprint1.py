from datetime import timedelta
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import Base, Collection, Document, Membership, SessionToken, Tenant, User, get_db, now
from app.main import app
from app.security import hash_password, token_hash


@pytest.fixture(scope="session")
def password_hash():
    return hash_password("test-password")


@pytest.fixture
def database(password_hash):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        tenant_a, tenant_b = Tenant(name="A"), Tenant(name="B")
        alice = User(email="alice@test", password_hash=password_hash)
        bob = User(email="bob@test", password_hash=password_hash)
        viewer = User(email="viewer@test", password_hash=password_hash)
        editor = User(email="editor@test", password_hash=password_hash)
        db.add_all([tenant_a, tenant_b, alice, bob, viewer, editor])
        db.flush()
        db.add_all(
            [
                Membership(tenant_id=tenant_a.id, user_id=alice.id, role="owner"),
                Membership(tenant_id=tenant_b.id, user_id=bob.id, role="owner"),
                Membership(tenant_id=tenant_a.id, user_id=viewer.id, role="viewer"),
                Membership(tenant_id=tenant_a.id, user_id=editor.id, role="editor"),
            ]
        )
        db.commit()
        yield db
    engine.dispose()


class FakeStorage:
    def __init__(self):
        self.objects = {}

    def put(self, key, body, content_type):
        self.objects[key] = (body, content_type)


@pytest.fixture
def client(database, monkeypatch):
    def override():
        yield database

    app.dependency_overrides[get_db] = override
    fake = FakeStorage()
    monkeypatch.setattr("app.main.storage", lambda: fake)
    try:
        with TestClient(app) as test:
            yield test
    finally:
        app.dependency_overrides.clear()


def login(client, email="alice@test", password="test-password"):
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    if response.status_code == 200:
        data = response.json()
        client.headers.update(
            {
                "Authorization": f"Bearer {data['access_token']}",
                "X-Tenant-ID": data["tenants"][0]["id"],
            }
        )
    return response


def create_collection(client):
    response = client.post("/v1/collections", json={"name": "private"})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_collection_declares_required_tenant_header_in_openapi(client):
    schema = client.get("/openapi.json").json()
    parameters = schema["paths"]["/v1/collections"]["post"].get("parameters", [])
    tenant_headers = [
        parameter
        for parameter in parameters
        if parameter["name"] == "X-Tenant-ID" and parameter["in"] == "header"
    ]
    assert len(tenant_headers) == 1
    assert tenant_headers[0]["required"] is True


@pytest.mark.parametrize("extra_fields", [{}, {"tenant_id": "untrusted-body-tenant"}])
def test_create_collection_requires_tenant_header(client, extra_fields):
    login(client)
    client.headers.pop("X-Tenant-ID")
    response = client.post("/v1/collections", json={"name": "private", **extra_fields})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "X-Tenant-ID"]


def upload(client, collection_id, name="x.txt", content=b"hello"):
    return client.post(
        f"/v1/collections/{collection_id}/documents", files={"file": (name, content)}
    )


def docx_bytes(document_xml=None):
    data = BytesIO()
    with ZipFile(data, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                "</Types>"
            ),
        )
        archive.writestr(
            "word/document.xml",
            document_xml
            or (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>Hello</w:t></w:r></w:p></w:body></w:document>"
            ),
        )
    return data.getvalue()


def corrupted_docx_bytes():
    data = bytearray(docx_bytes())
    with ZipFile(BytesIO(data)) as archive:
        entry = archive.getinfo("word/document.xml")
        offset = entry.header_offset + 30 + len(entry.filename.encode()) + len(entry.extra)
    data[offset] = 0xFF
    return bytes(data)


def test_session_revocation_and_hashed_token(client, database):
    assert client.get("/v1/collections").status_code == 401
    response = login(client)
    assert response.status_code == 200
    raw = response.json()["access_token"]
    assert database.get(SessionToken, token_hash(raw)) is not None
    assert database.get(SessionToken, raw) is None
    assert not response.cookies
    assert client.post("/v1/auth/logout").status_code == 204
    assert client.get("/v1/collections").status_code == 401


@pytest.mark.parametrize("email,password", [("alice@test", "bad"), ("unknown@test", "bad")])
def test_invalid_credentials(client, email, password):
    assert login(client, email, password).status_code == 401


def test_expired_session(client, database):
    login(client)
    session = database.scalar(select(SessionToken))
    session.expires_at = now() - timedelta(seconds=1)
    database.commit()
    assert client.get("/v1/collections").status_code == 401


def test_cross_tenant_access_and_header_forgery(client):
    login(client)
    collection_id = create_collection(client)
    document_id = upload(client, collection_id).json()["document_id"]
    tenant_a = client.headers["X-Tenant-ID"]
    login(client, "bob@test")
    assert client.get("/v1/collections").json() == []
    assert client.get(f"/v1/collections/{collection_id}/documents").status_code == 404
    assert client.get(f"/v1/documents/{document_id}").status_code == 404
    assert upload(client, collection_id).status_code == 404
    client.headers["X-Tenant-ID"] = tenant_a
    assert client.post("/v1/collections", json={"name": "attack"}).status_code == 404


def test_membership_revocation_applies_to_existing_session(client, database):
    response = login(client)
    collection_id = create_collection(client)
    document_id = upload(client, collection_id).json()["document_id"]
    member = database.get(Membership, (client.headers["X-Tenant-ID"], response.json()["user_id"]))
    database.delete(member)
    database.commit()
    assert client.get("/v1/collections").json() == []
    assert client.get(f"/v1/documents/{document_id}").status_code == 404
    assert upload(client, collection_id).status_code == 404


def test_roles_and_empty_collection_name(client):
    login(client)
    assert client.post("/v1/collections", json={"name": "  "}).status_code == 422
    collection_id = create_collection(client)
    document_id = upload(client, collection_id).json()["document_id"]
    login(client, "viewer@test")
    assert client.get(f"/v1/documents/{document_id}").status_code == 200
    assert len(client.get("/v1/collections").json()) == 1
    assert client.post("/v1/collections", json={"name": "denied"}).status_code == 403
    assert upload(client, collection_id).status_code == 403
    login(client, "editor@test")
    assert upload(client, collection_id).status_code == 202


@pytest.mark.parametrize(
    "name,content",
    [
        ("x.pdf", b"not pdf"),
        ("x.pdf", b"%PDF-corrupted"),
        ("x.txt", b""),
        ("x.txt", b"a\x00b"),
        ("x.txt", b"\xff"),
        ("x.exe", b"hello"),
        ("x.docx", b"PK\x03\x04bad"),
        ("x.docx", docx_bytes("not XML")),
        ("x.docx", docx_bytes('<?xml version="1.0" encoding="bogus-encoding"?><x/>')),
        ("x.docx", docx_bytes('<?xml version="1.0" encoding="UTF-32"?><x/>')),
        ("x.docx", corrupted_docx_bytes()),
        ("x.docx", docx_bytes('<!DOCTYPE x [<!ENTITY x "attack">]><x/>')),
    ],
)
def test_rejects_invalid_uploads(client, database, name, content):
    login(client)
    collection_id = create_collection(client)
    assert upload(client, collection_id, name, content).status_code == 400
    assert database.scalar(select(func.count()).select_from(Document)) == 0


def test_file_and_page_limits(client, monkeypatch):
    login(client)
    collection_id = create_collection(client)
    monkeypatch.setattr(settings(), "max_upload_bytes", 10)
    assert upload(client, collection_id, content=b"x" * 11).status_code == 413
    monkeypatch.setattr(settings(), "max_upload_bytes", 20971520)
    monkeypatch.setattr(settings(), "max_pdf_pages", 1)
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    data = BytesIO()
    writer.write(data)
    assert upload(client, collection_id, "pages.pdf", data.getvalue()).status_code == 413


def test_docx_expansion_limit(client, monkeypatch):
    login(client)
    collection_id = create_collection(client)
    monkeypatch.setattr(settings(), "max_upload_bytes", 2000)
    data = docx_bytes("x" * 100000)
    assert len(data) < 2000
    response = upload(client, collection_id, "large.docx", data)
    assert response.status_code == 400
    assert response.json()["detail"] == "docx_expanded_size_exceeded"


def test_upload_storage_metadata_and_pagination(client, database):
    login(client)
    collection_id = create_collection(client)
    response = upload(client, collection_id, "../../hello.txt")
    assert response.status_code == 202
    document = database.get(Document, response.json()["document_id"])
    assert document.filename == "hello.txt"
    assert document.storage_key != document.filename
    assert document.status == "pending"
    assert upload(client, collection_id, "valid.docx", docx_bytes()).status_code == 202
    assert len(client.get(f"/v1/collections/{collection_id}/documents?page_size=1").json()) == 1
    assert client.get(f"/v1/collections/{collection_id}/documents?page=0").status_code == 422
    assert (
        client.get(
            f"/v1/collections/{collection_id}/documents?page=9223372036854775808"
        ).status_code
        == 422
    )


def test_storage_failure_is_sanitized_and_persisted(client, database, monkeypatch):
    class UnavailableStorage:
        def put(self, *args):
            raise RuntimeError("private storage credentials")

    monkeypatch.setattr("app.main.storage", UnavailableStorage)
    login(client)
    response = upload(client, create_collection(client))
    assert response.status_code == 503
    assert "private" not in response.text
    document = database.scalar(select(Document))
    assert document.status == "failed"
    assert document.error_code == "storage_upload_failed"


def test_database_rejects_cross_tenant_document(database):
    tenant_a, tenant_b = database.scalars(select(Tenant).order_by(Tenant.name)).all()
    alice = database.scalar(select(User).where(User.email == "alice@test"))
    collection = Collection(tenant_id=tenant_a.id, name="private", created_by=alice.id)
    database.add(collection)
    database.commit()
    database.add(
        Document(
            tenant_id=tenant_b.id,
            collection_id=collection.id,
            owner_id=alice.id,
            filename="x.txt",
            mime="text/plain",
            sha256="0" * 64,
            storage_key="forged",
            size_bytes=1,
        )
    )
    with pytest.raises(IntegrityError):
        database.commit()
    database.rollback()


def test_health(client):
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200


def test_readiness_database_failure_is_sanitized(client, database, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OperationalError("private connection URL", {}, Exception("database failed"))

    monkeypatch.setattr(database, "execute", unavailable)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "database_unavailable"
