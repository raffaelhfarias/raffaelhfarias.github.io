import logging
import math
from dataclasses import asdict, dataclass
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile

from pypdf import PdfReader

from .nvidia import NvidiaClient, ProviderError

ABSTENTION = "Não encontrei informações suficientes no documento para responder."
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    page: int | None


def extract_chunks(data: bytes, mime: str) -> list[Chunk]:
    if mime == "application/pdf":
        pages = [
            (number, page.extract_text() or "")
            for number, page in enumerate(PdfReader(BytesIO(data)).pages, start=1)
        ]
    elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with ZipFile(BytesIO(data)) as archive:
            document = ElementTree.fromstring(archive.read("word/document.xml"))
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        text = "\n".join(
            "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
            for paragraph in document.iter(f"{namespace}p")
        )
        pages = [(None, text)]
    elif mime == "text/plain":
        pages = [(None, data.decode("utf-8-sig"))]
    else:
        raise ValueError("unsupported_file_type")
    chunks = []
    for page, text in pages:
        text = " ".join(text.split())
        for start in range(0, len(text), 850):
            chunks.append(Chunk(f"chunk-{len(chunks) + 1}", text[start : start + 1000], page))
            if len(chunks) > 80:
                raise ValueError("document_too_long_for_evaluation")
            if start + 1000 >= len(text):
                break
    if not chunks:
        raise ValueError("no_extractable_text")
    return chunks


class RagSession:
    def __init__(self, chunks: list[Chunk], provider: NvidiaClient, vectors=None):
        if not chunks:
            raise ValueError("no_extractable_text")
        self.chunks = chunks
        self.provider = provider
        self.vectors = (
            vectors
            if vectors is not None
            else provider.embed([chunk.text for chunk in chunks], "passage")
        )
        self.questions_used = 0

    def ask(self, question: str) -> dict:
        question = question.strip()
        if not question or len(question) > 1000:
            raise ValueError("question_must_have_1_to_1000_characters")
        if self.questions_used >= 5:
            raise ValueError("question_limit_reached")
        self.questions_used += 1
        query = self.provider.embed([question], "query")[0]
        if len(query) != len(self.vectors[0]):
            logger.warning("rag_failure stage=retrieval code=embedding_dimensions_changed")
            raise ProviderError("embedding_dimensions_changed")
        scores = [
            sum(left * right for left, right in zip(query, vector, strict=True))
            for vector in self.vectors
        ]
        if not all(math.isfinite(score) for score in scores):
            logger.warning("rag_failure stage=retrieval code=nvidia_invalid_embeddings")
            raise ProviderError("nvidia_invalid_embeddings")
        indexes = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:4]
        sources = [asdict(self.chunks[index]) for index in indexes]
        result = self.provider.answer(question, sources)
        identifiers = result.get("source_ids")
        answer = result.get("answer")
        allowed = {source["id"] for source in sources}
        if (
            not isinstance(answer, str)
            or len(answer) > 6000
            or not isinstance(identifiers, list)
            or any(not isinstance(identifier, str) for identifier in identifiers)
            or not set(identifiers).issubset(allowed)
            or (identifiers and not answer.strip())
        ):
            logger.warning("rag_failure stage=source_validation code=invalid_answer_sources")
            raise ProviderError("invalid_answer_sources")
        return {
            "answer": answer.strip() if identifiers else ABSTENTION,
            "sources": [source for source in sources if source["id"] in identifiers],
            "questions_remaining": 5 - self.questions_used,
        }
