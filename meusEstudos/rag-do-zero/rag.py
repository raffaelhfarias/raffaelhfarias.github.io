from __future__ import annotations

import argparse
from pathlib import Path


def split_text(text: str) -> list[str]:
    """Usa cada parágrafo como um chunk para preservar o contexto."""
    return [part.strip() for part in text.split("\n\n") if part.strip()]


def build_index(chunks: list[str]):
    import faiss
    from sentence_transformers import SentenceTransformer

    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embedder.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    # Produto interno entre vetores normalizados = similaridade de cosseno.
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return embedder, index


def retrieve(
    question: str,
    chunks: list[str],
    embedder,
    index,
    top_k: int = 1,
    min_score: float = 0.5,
):
    question_embedding = embedder.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    scores, positions = index.search(question_embedding, min(top_k, len(chunks)))

    return [
        (chunks[position], float(score))
        for position, score in zip(positions[0], scores[0])
        if position >= 0 and score >= min_score
    ]


def generate_answer(question: str, retrieved_chunks: list[tuple[str, float]]) -> str:
    if not retrieved_chunks:
        return "Não encontrei essa informação nos documentos."
    return retrieved_chunks[0][0]


def ask(question: str, document_path: Path, top_k: int) -> None:
    text = document_path.read_text(encoding="utf-8")
    chunks = split_text(text)
    embedder, index = build_index(chunks)
    retrieved_chunks = retrieve(question, chunks, embedder, index, top_k)

    print("\n--- Fontes recuperadas ---")
    for number, (chunk, score) in enumerate(retrieved_chunks, start=1):
        print(f"[{number}] similaridade={score:.3f}\n{chunk}\n")

    print("--- Resposta ---")
    print(generate_answer(question, retrieved_chunks))


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG mínimo executado localmente")
    parser.add_argument("--question", help="pergunta para o documento")
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("./knowledge.txt"),
        help="arquivo de texto usado como base de conhecimento",
    )
    parser.add_argument("--top-k", type=int, default=1)
    args = parser.parse_args()

    if args.question:
        ask(args.question, args.file, args.top_k)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
