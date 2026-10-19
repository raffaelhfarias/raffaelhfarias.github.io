import argparse
import json
from pathlib import Path

from fastapi import HTTPException

from app.config import settings
from app.main import inspect_upload
from app.nvidia import NvidiaClient, ProviderError
from app.rag import RagSession, extract_chunks

EXAMPLE = (
    "Manual fictício da equipe Aurora. O prazo para solicitar reembolso é de 15 dias "
    "corridos após a despesa. O pedido deve conter nota fiscal e ser enviado ao financeiro. "
    "A aprovação cabe à gestora Marina. O limite por refeição é de R$ 45. "
    "O atendimento do financeiro ocorre de segunda a sexta-feira, das 9h às 17h."
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Avaliação privada do RAG com a API NVIDIA.")
    document = parser.add_mutually_exclusive_group(required=True)
    document.add_argument("--file", type=Path)
    document.add_argument("--example", action="store_true")
    parser.add_argument("--question", action="append", default=[])
    args = parser.parse_args(argv)
    if len(args.question) > 5:
        parser.error("Use no máximo cinco perguntas por execução.")
    print("Avaliação: o conteúdo extraído e as perguntas serão enviados à NVIDIA.")
    try:
        provider = NvidiaClient()
        if args.example:
            filename, data = "manual-aurora.txt", EXAMPLE.encode()
        else:
            filename = args.file.name
            with args.file.open("rb") as stream:
                data = stream.read(settings().max_upload_bytes + 1)
        if len(data) > settings().max_upload_bytes:
            raise ValueError("file_too_large")
        mime, pages = inspect_upload(filename, data)
        if pages and pages > settings().max_pdf_pages:
            raise ValueError("too_many_pages")
        session = RagSession(extract_chunks(data, mime), provider)
        print(f"Documento pronto: {filename}. Trechos: {len(session.chunks)}.")
        print("Cinco tentativas nesta execução; falhas do provedor também consomem tentativa.")
        questions = iter(args.question) if args.question else None
        while session.questions_used < 5:
            question = next(questions, None) if questions is not None else input("Pergunta: ")
            if question is None or question.strip().lower() == "/sair":
                break
            try:
                result = session.ask(question)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            except (ProviderError, ValueError) as exc:
                print(f"Falha: {exc}")
                if questions is not None:
                    return 1
        return 0
    except HTTPException as exc:
        print(f"Falha: {exc.detail}")
    except (ProviderError, ValueError) as exc:
        print(f"Falha: {exc}")
    except (EOFError, KeyboardInterrupt):
        return 0
    except Exception:
        print("Falha: não foi possível ler ou processar o documento.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
