import asyncio
import logging
import secrets
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .config import settings
from .db import DemoBudget, DemoSession, SessionLocal, get_db, now
from .nvidia import NvidiaClient, ProviderError
from .rag import Chunk, RagSession, extract_chunks
from .security import token_hash

COOKIE = "knowledge_demo"
COOKIE_PATH = "/v1/demo"
EXAMPLE = (
    "Manual da equipe Aurora. O prazo para solicitar reembolso é de 15 dias corridos "
    "após a despesa. O pedido deve conter nota fiscal e ser enviado ao financeiro. "
    "A aprovação cabe à gestora Marina."
)


def cleanup_expired():
    with SessionLocal() as db:
        db.execute(delete(DemoSession).where(DemoSession.expires_at <= now()))
        db.commit()


@asynccontextmanager
async def demo_lifespan(app):
    async def cleanup_loop():
        while True:
            await asyncio.sleep(60)
            try:
                await run_in_threadpool(cleanup_expired)
            except SQLAlchemyError:
                logging.getLogger(__name__).warning("demo_cleanup_unavailable")

    task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def demo_access(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    if not settings().demo_enabled:
        raise HTTPException(503, "demo_disabled")
    if request.method != "GET" and request.headers.get("x-demo-request") != "1":
        raise HTTPException(403, "same_origin_required")
    origin = request.headers.get("origin")
    if origin and origin not in {f"https://{request.url.netloc}", f"http://{request.url.netloc}"}:
        raise HTTPException(403, "same_origin_required")


router = APIRouter(prefix=COOKIE_PATH, tags=["demo"], dependencies=[Depends(demo_access)])


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


def reserve_budget(db: Session, field: str):
    window = now().replace(minute=0, second=0, microsecond=0)
    db.execute(
        update(DemoBudget)
        .where(DemoBudget.id == 1, DemoBudget.window_start < window)
        .values(window_start=window, uploads=0, questions=0)
    )
    column = getattr(DemoBudget, field)
    limit = getattr(settings(), f"demo_{field}_per_hour")
    reserved = db.execute(
        update(DemoBudget)
        .where(DemoBudget.id == 1, column < limit)
        .values({field: column + 1})
        .returning(DemoBudget.id)
    ).scalar_one_or_none()
    if reserved is None:
        db.rollback()
        raise HTTPException(429, "demo_hourly_limit", headers={"Retry-After": "3600"})


def session_for(request: Request, db: Session) -> DemoSession:
    token = request.cookies.get(COOKIE, "")
    if not token or len(token) > 100:
        raise HTTPException(401, "demo_session_required")
    session = db.scalar(
        select(DemoSession).where(
            DemoSession.token_hash == token_hash(token), DemoSession.expires_at > now()
        )
    )
    if session is None:
        raise HTTPException(410, "demo_session_expired")
    return session


def session_info(session: DemoSession):
    return {
        "filename": session.filename,
        "questions_remaining": 5 - session.questions_used,
        "expires_at": session.expires_at.isoformat(),
        "busy": session.busy,
    }


def begin_upload(request: Request, db: Session):
    if request.cookies.get(COOKIE):
        session = db.scalar(
            select(DemoSession).where(
                DemoSession.token_hash == token_hash(request.cookies[COOKIE]),
                DemoSession.expires_at > now(),
            )
        )
        if session is not None:
            raise HTTPException(409, "remove_current_document_first")
    db.execute(delete(DemoSession).where(DemoSession.expires_at <= now()))
    reserve_budget(db, "uploads")
    db.commit()


def create_session(
    data: bytes, filename: str, mime: str, request: Request, response: Response, db: Session
):
    try:
        rag = RagSession(extract_chunks(data, mime), NvidiaClient())
    except ProviderError:
        logging.getLogger(__name__).warning("demo_rag_failed operation=document")
        raise HTTPException(503, "demo_provider_unavailable") from None
    except Exception:
        raise HTTPException(400, "document_not_readable_or_too_long") from None
    token = secrets.token_urlsafe(32)
    session = DemoSession(
        token_hash=token_hash(token),
        filename=filename,
        chunks=[asdict(chunk) for chunk in rag.chunks],
        vectors=rag.vectors,
        questions_used=0,
        busy=False,
        expires_at=now() + timedelta(minutes=30),
    )
    db.add(session)
    db.commit()
    response.set_cookie(
        COOKIE,
        token,
        max_age=1800,
        httponly=True,
        secure=request.url.hostname not in {"localhost", "127.0.0.1", "::1"},
        samesite="strict",
        path=COOKIE_PATH,
    )
    return session_info(session)


async def bounded_body(request: Request, limit: int) -> bytes:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > limit:
            raise HTTPException(413, "request_too_large")
        body.extend(chunk)
    return bytes(body)


@router.post("/document")
async def upload(
    request: Request,
    response: Response,
    filename: str = Query(min_length=1, max_length=255),
    db: Session = Depends(get_db),
):
    from .main import clean_filename, inspect_upload

    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(400, "unsupported_file_type")
    await run_in_threadpool(begin_upload, request, db)
    data = await bounded_body(request, settings().max_upload_bytes)
    mime, pages = await run_in_threadpool(inspect_upload, filename, data)
    if pages is not None and pages > settings().max_pdf_pages:
        raise HTTPException(400, "pdf_page_limit_exceeded")
    return await run_in_threadpool(
        create_session, data, clean_filename(filename), mime, request, response, db
    )


@router.post("/example")
def example(request: Request, response: Response, db: Session = Depends(get_db)):
    begin_upload(request, db)
    return create_session(
        EXAMPLE.encode(), "Manual da equipe Aurora", "text/plain", request, response, db
    )


@router.get("/session")
def status(request: Request, db: Session = Depends(get_db)):
    return session_info(session_for(request, db))


@router.delete("/session", status_code=204)
def remove(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE, "")
    db.execute(delete(DemoSession).where(DemoSession.token_hash == token_hash(token)))
    db.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)


def answer_question(request: Request, question: str, db: Session):
    session = session_for(request, db)
    claimed = db.execute(
        update(DemoSession)
        .where(
            DemoSession.token_hash == session.token_hash,
            DemoSession.expires_at > now(),
            DemoSession.busy.is_(False),
            DemoSession.questions_used < 5,
        )
        .values(busy=True, questions_used=DemoSession.questions_used + 1)
        .returning(DemoSession.questions_used)
        .execution_options(synchronize_session=False)
    ).scalar_one_or_none()
    if claimed is None:
        db.rollback()
        raise HTTPException(409, "session_busy_or_question_limit")
    reserve_budget(db, "questions")
    db.commit()
    try:
        rag = RagSession(
            [Chunk(**chunk) for chunk in session.chunks], NvidiaClient(), vectors=session.vectors
        )
        result = rag.ask(question)
        if (
            db.scalar(
                select(DemoSession.token_hash).where(
                    DemoSession.token_hash == session.token_hash, DemoSession.expires_at > now()
                )
            )
            is None
        ):
            raise HTTPException(410, "demo_session_expired")
        result["questions_remaining"] = 5 - claimed
        return result
    except ProviderError:
        logging.getLogger(__name__).warning("demo_rag_failed operation=question")
        raise HTTPException(503, "demo_provider_unavailable") from None
    finally:
        db.execute(
            update(DemoSession)
            .where(DemoSession.token_hash == session.token_hash)
            .values(busy=False)
        )
        db.commit()


@router.post("/questions")
async def ask(request: Request, db: Session = Depends(get_db)):
    body = await bounded_body(request, 8000)
    try:
        question = Question.model_validate_json(body).question.strip()
        if not question:
            raise ValueError("empty_question")
    except (ValidationError, ValueError):
        raise HTTPException(422, "invalid_question") from None
    return await run_in_threadpool(answer_question, request, question, db)
