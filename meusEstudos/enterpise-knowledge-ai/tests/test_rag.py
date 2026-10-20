import json
from io import BytesIO
from urllib.error import HTTPError, URLError
from zipfile import ZipFile

import pytest
from pydantic import SecretStr
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.config import Settings, settings
from app.nvidia import NvidiaClient, ProviderError
from app.rag import ABSTENTION, Chunk, RagSession, extract_chunks
from scripts import rag_demo


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(settings(), "nvidia_api_key", SecretStr("test-only-key"))
    return NvidiaClient()


def test_default_chat_model():
    assert (
        Settings.model_fields["nvidia_chat_model"].default
        == "nvidia/nemotron-3.5-super-vl-120b-a12b"
    )


def test_nvidia_key_is_required_and_masked(monkeypatch, caplog):
    monkeypatch.setattr(settings(), "nvidia_api_key", SecretStr(""))
    with pytest.raises(ProviderError, match="nvidia_key_not_configured"):
        NvidiaClient()
    assert "stage=configuration code=nvidia_key_not_configured" in caplog.text
    monkeypatch.setattr(settings(), "nvidia_api_key", SecretStr("test-only-key"))
    assert "test-only-key" not in repr(settings())


def test_embedding_batches_preserve_order_and_normalize(provider, monkeypatch):
    calls = []

    def request(endpoint, payload):
        calls.append((endpoint, payload))
        return {
            "data": [
                {"index": index, "embedding": [3, 4]}
                for index in reversed(range(len(payload["input"])))
            ]
        }

    monkeypatch.setattr(provider, "_request", request)
    assert provider.embed(["trecho"] * 17, "passage") == [[0.6, 0.8]] * 17
    assert [len(payload["input"]) for _, payload in calls] == [16, 1]
    assert all(endpoint == "embeddings" for endpoint, _ in calls)
    assert all(payload["input_type"] == "passage" for _, payload in calls)
    assert all(payload["truncate"] == "NONE" for _, payload in calls)


@pytest.mark.parametrize(
    "items",
    [
        [],
        [{"index": 1, "embedding": [1, 0]}],
        [{"index": 0, "embedding": [0, 0]}],
        [{"index": 0, "embedding": [float("nan"), 1]}],
        [{"index": 0, "embedding": ["1", 0]}],
        [{"index": 0, "embedding": None}],
    ],
)
def test_invalid_embeddings_fail_safely(provider, monkeypatch, items):
    monkeypatch.setattr(provider, "_request", lambda *_: {"data": items})
    with pytest.raises(ProviderError, match="nvidia_invalid_embeddings"):
        provider.embed(["texto"], "query")


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, "nvidia_access_denied"),
        (403, "nvidia_access_denied"),
        (422, "nvidia_request_failed"),
        (429, "nvidia_rate_limited"),
        (500, "nvidia_request_failed"),
    ],
)
@pytest.mark.parametrize(
    "endpoint,stage", [("embeddings", "embeddings"), ("chat/completions", "generation")]
)
def test_http_errors_do_not_leak_body_or_key(
    provider, monkeypatch, caplog, status, code, endpoint, stage
):
    def fail(*_args, **_kwargs):
        raise HTTPError("https://example.test", status, "private-error", {}, BytesIO(b"secret"))

    monkeypatch.setattr("app.nvidia.urlopen", fail)
    with pytest.raises(ProviderError) as caught:
        provider._request(endpoint, {"input": ["private document"]})
    assert str(caught.value) == code
    assert f"stage={stage} code={code} http_status={status}" in caplog.text
    assert all(
        value not in caplog.text
        for value in ("private document", "private-error", "secret", "test-only-key")
    )


@pytest.mark.parametrize("timeout", [False, True])
def test_network_failure_is_sanitized(provider, monkeypatch, caplog, timeout):
    def fail(*_args, **_kwargs):
        if timeout:
            raise URLError(TimeoutError("private-timeout-details"))
        raise URLError("private-network-details")

    monkeypatch.setattr("app.nvidia.urlopen", fail)
    with pytest.raises(ProviderError, match="^nvidia_unavailable$"):
        provider.embed(["texto"], "query")
    assert f"reason={'timeout' if timeout else 'network_error'}" in caplog.text
    assert f"error_type={'TimeoutError' if timeout else 'str'}" in caplog.text
    assert "private-" not in caplog.text


@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (200, b'{"data": []}', None),
        (200, b"not-json", "nvidia_invalid_response"),
        (200, b"[]", "nvidia_invalid_response"),
        (202, b"{}", "nvidia_response_not_ready"),
    ],
)
def test_transport_contract(provider, monkeypatch, status, body, expected):
    class Response(BytesIO):
        pass

    def respond(request, timeout):
        assert request.full_url == "https://integrate.api.nvidia.com/v1/embeddings"
        assert request.get_header("Authorization") == "Bearer test-only-key"
        assert json.loads(request.data) == {"input": ["texto"]}
        assert timeout == 60
        response = Response(body)
        response.status = status
        return response

    monkeypatch.setattr("app.nvidia.urlopen", respond)
    if expected:
        with pytest.raises(ProviderError, match=expected):
            provider._request("embeddings", {"input": ["texto"]})
    else:
        assert provider._request("embeddings", {"input": ["texto"]}) == {"data": []}


def test_chat_contract(provider, monkeypatch):
    calls = []

    def request(endpoint, payload):
        calls.append((endpoint, payload))
        return {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": '{"answer":"15 dias","source_ids":["chunk-1"]}'},
                }
            ]
        }

    monkeypatch.setattr(provider, "_request", request)
    sources = [{"id": "chunk-1", "text": "Prazo: 15 dias.", "page": 1}]
    assert provider.answer("Qual o prazo?", sources)["source_ids"] == ["chunk-1"]
    endpoint, payload = calls[0]
    assert endpoint == "chat/completions"
    assert payload["model"] == provider.chat_model
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}
    assert "reasoning_effort" not in payload
    assert payload["stream"] is False
    assert json.loads(payload["messages"][1]["content"])["sources"] == sources


@pytest.mark.parametrize(
    "content, reason, diagnostic",
    [
        ("private-answer-not-json", "stop", "invalid_json"),
        ("{}", "length", "completion_not_finished"),
        ("[]", "stop", "not_object"),
        ("{}", "private-finish-reason", "completion_not_finished"),
        ("{}", ["private-finish-reason"], "completion_not_finished"),
    ],
)
def test_invalid_or_truncated_chat_fails(
    provider, monkeypatch, caplog, content, reason, diagnostic
):
    monkeypatch.setattr(
        provider,
        "_request",
        lambda *_: {"choices": [{"finish_reason": reason, "message": {"content": content}}]},
    )
    with pytest.raises(ProviderError, match="nvidia_invalid_answer"):
        provider.answer("private-question", [{"text": "private-document"}])
    assert f"stage=answer_validation code=nvidia_invalid_answer reason={diagnostic}" in caplog.text
    assert f"finish_reason={reason if reason in ('stop', 'length') else 'unknown'}" in caplog.text
    assert "private-" not in caplog.text


def test_chunks_overlap_and_reject_empty_or_excessive_text():
    chunks = extract_chunks(b"a" * 1800, "text/plain")
    assert [len(chunk.text) for chunk in chunks] == [1000, 950]
    assert chunks[0].text[-150:] == chunks[1].text[:150]
    with pytest.raises(ValueError, match="no_extractable_text"):
        extract_chunks(b" \n ", "text/plain")
    with pytest.raises(ValueError, match="document_too_long"):
        extract_chunks(b"a" * 100_000, "text/plain")


def test_docx_paragraphs_have_no_invented_pages():
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Prazo:</w:t></w:r></w:p>"
            "<w:p><w:r><w:t>15 dias.</w:t></w:r></w:p></w:body></w:document>",
        )
    chunks = extract_chunks(
        stream.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert chunks == [Chunk("chunk-1", "Prazo: 15 dias.", None)]


def test_pdf_preserves_page_numbers():
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
    assert extract_chunks(stream.getvalue(), "application/pdf") == [
        Chunk("chunk-1", "Prazo: 15 dias.", 1)
    ]


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.result = {"answer": "O prazo é de 15 dias.", "source_ids": ["chunk-1"]}

    def embed(self, texts, input_type):
        self.calls.append(input_type)
        return [[1.0, 0.0] if "prazo" in text.lower() else [0.0, 1.0] for text in texts]

    def answer(self, question, sources):
        self.sources = sources
        return self.result


def test_session_indexes_once_and_retrieves_only_four_sources():
    provider = FakeProvider()
    chunks = [Chunk("chunk-1", "Prazo: 15 dias.", 2)] + [
        Chunk(f"chunk-{index}", "Outro assunto", None) for index in range(2, 8)
    ]
    session = RagSession(chunks, provider)
    for _ in range(5):
        result = session.ask("Qual o prazo?")
        assert result["sources"] == [{"id": "chunk-1", "text": "Prazo: 15 dias.", "page": 2}]
    assert len(provider.sources) == 4
    assert provider.sources[0]["id"] == "chunk-1"
    assert provider.calls == ["passage"] + ["query"] * 5
    with pytest.raises(ValueError, match="question_limit_reached"):
        session.ask("Sexta pergunta")
    assert provider.calls == ["passage"] + ["query"] * 5


def test_abstention_and_unknown_source_are_not_fabricated(caplog):
    provider = FakeProvider()
    session = RagSession([Chunk("chunk-1", "Prazo: 15 dias.", 1)], provider)
    provider.result = {"answer": "Resposta sem fonte", "source_ids": []}
    assert session.ask("Qual o salário?")["answer"] == ABSTENTION
    provider.result = {"answer": "Resposta", "source_ids": ["invented"]}
    with pytest.raises(ProviderError, match="invalid_answer_sources"):
        session.ask("Qual o prazo?")
    assert "stage=source_validation code=invalid_answer_sources" in caplog.text
    assert "Resposta" not in caplog.text
    assert session.questions_used == 2


def test_sessions_do_not_share_chunks_or_counters():
    first = RagSession([Chunk("chunk-1", "Prazo: 15 dias.", 1)], FakeProvider())
    second = RagSession([Chunk("chunk-1", "Outro documento", 3)], FakeProvider())
    first.ask("Qual o prazo?")
    assert second.questions_used == 0
    assert second.ask("Outra pergunta")["sources"][0]["text"] == "Outro documento"


def test_blank_question_does_not_call_provider():
    provider = FakeProvider()
    session = RagSession([Chunk("chunk-1", "Prazo: 15 dias.", 1)], provider)
    with pytest.raises(ValueError):
        session.ask(" ")
    assert session.questions_used == 0
    assert provider.calls == ["passage"]


def test_example_command_with_fake_provider(monkeypatch, capsys):
    monkeypatch.setattr(rag_demo, "NvidiaClient", FakeProvider)
    assert rag_demo.main(["--example", "--question", "Qual o prazo?"]) == 0
    output = capsys.readouterr().out
    assert '"questions_remaining": 4' in output
    assert "15 dias" in output


def test_example_without_key_fails_without_network(monkeypatch, capsys):
    monkeypatch.setattr(settings(), "nvidia_api_key", SecretStr(""))
    assert rag_demo.main(["--example", "--question", "Qual o prazo?"]) == 1
    assert "nvidia_key_not_configured" in capsys.readouterr().out
