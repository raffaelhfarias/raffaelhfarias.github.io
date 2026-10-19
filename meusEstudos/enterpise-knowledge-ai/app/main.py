import hashlib
import re
import secrets
import zlib
from datetime import timedelta
from io import BytesIO
from uuid import uuid4
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field, field_validator
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import Collection, Document, Membership, SessionToken, Tenant, User, get_db, now
from .security import (
    current_user,
    hash_password,
    membership,
    require_role,
    token_hash,
    verify_password,
)
from .storage import storage

app = FastAPI(title="Enterprise Knowledge AI", version="0.1.0")
dummy_password_hash = hash_password(secrets.token_urlsafe(32))


class Login(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class CollectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value


def clean_filename(name: str) -> str:
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    value = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")
    return value[:255] or "upload"


def inspect_upload(filename: str, data: bytes) -> tuple[str, int | None]:
    lower = filename.lower()
    if not data:
        raise HTTPException(400, "empty_file")
    if lower.endswith(".pdf") and data.startswith(b"%PDF-"):
        try:
            pages = len(PdfReader(BytesIO(data), strict=False).pages)
        except Exception as exc:
            raise HTTPException(400, "invalid_pdf") from exc
        if not pages:
            raise HTTPException(400, "invalid_pdf")
        return "application/pdf", pages
    if lower.endswith(".docx") and data.startswith(b"PK\x03\x04"):
        try:
            with ZipFile(BytesIO(data)) as archive:
                names = set(archive.namelist())
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise HTTPException(400, "invalid_docx")
                if (
                    len(names) > 1000
                    or sum(item.file_size for item in archive.infolist())
                    > settings().max_upload_bytes * 5
                ):
                    raise HTTPException(400, "docx_expanded_size_exceeded")
                if any(name.lower().endswith("vbaproject.bin") for name in names):
                    raise HTTPException(400, "unsupported_file_type")
                xml_parts = [
                    archive.read(name) for name in ("[Content_Types].xml", "word/document.xml")
                ]
                if any(
                    b"<!DOCTYPE" in part or b"<!ENTITY" in part or b"\x00" in part
                    for part in xml_parts
                ):
                    raise HTTPException(400, "invalid_docx")
                content_types, document = [ElementTree.fromstring(part) for part in xml_parts]
                if (
                    document.tag
                    != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document"
                ):
                    raise HTTPException(400, "invalid_docx")
                expected_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
                overrides = content_types.findall(
                    "{http://schemas.openxmlformats.org/package/2006/content-types}Override"
                )
                if not any(
                    item.get("PartName") == "/word/document.xml"
                    and item.get("ContentType") == expected_type
                    for item in overrides
                ):
                    raise HTTPException(400, "invalid_docx")
        except (
            BadZipFile,
            ElementTree.ParseError,
            RuntimeError,
            NotImplementedError,
            LookupError,
            ValueError,
            zlib.error,
        ) as exc:
            raise HTTPException(400, "invalid_docx") from exc
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document", None
    if not lower.endswith(".txt") or data.startswith((b"%PDF-", b"PK\x03\x04")):
        raise HTTPException(400, "unsupported_file_type")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "unsupported_file_type") from exc
    if any(ord(character) < 32 and character not in "\t\n\r\f" for character in text):
        raise HTTPException(400, "unsupported_file_type")
    return "text/plain", None


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(select(User.id).limit(1))
    except SQLAlchemyError as exc:
        raise HTTPException(503, "database_unavailable") from exc
    return {"status": "ok"}


@app.post("/v1/auth/login")
def login(payload: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    password_valid = verify_password(
        payload.password, user.password_hash if user else dummy_password_hash
    )
    if not user or not password_valid:
        raise HTTPException(401, "invalid_credentials")
    raw = secrets.token_urlsafe(32)
    db.add(
        SessionToken(
            token_hash=token_hash(raw),
            user_id=user.id,
            expires_at=now() + timedelta(hours=settings().session_ttl_hours),
        )
    )
    db.commit()
    tenants = (
        db.execute(
            select(Tenant.id, Tenant.name, Membership.role)
            .join(Membership, Membership.tenant_id == Tenant.id)
            .where(Membership.user_id == user.id)
        )
        .mappings()
        .all()
    )
    return {
        "access_token": raw,
        "token_type": "bearer",
        "user_id": user.id,
        "expires_in": settings().session_ttl_hours * 3600,
        "tenants": [dict(tenant) for tenant in tenants],
    }


@app.post("/v1/auth/logout", status_code=204)
def logout(request: Request, db: Session = Depends(get_db), _user: User = Depends(current_user)):
    session = db.get(SessionToken, request.state.session_hash)
    if session:
        session.revoked_at = now()
        db.commit()
    return None


@app.post("/v1/collections", status_code=201)
def create_collection(
    request: Request,
    payload: CollectionIn,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(400, "x_tenant_id_required")
    item = require_role(db, user, tenant_id, "owner", "editor")
    collection = Collection(tenant_id=item.tenant_id, name=payload.name.strip(), created_by=user.id)
    db.add(collection)
    db.commit()
    return {"id": collection.id, "tenant_id": collection.tenant_id, "name": collection.name}


@app.get("/v1/collections")
def list_collections(db: Session = Depends(get_db), user: User = Depends(current_user)):
    tenant_ids = select(Membership.tenant_id).where(Membership.user_id == user.id)
    return [
        {"id": collection.id, "tenant_id": collection.tenant_id, "name": collection.name}
        for collection in db.scalars(
            select(Collection)
            .where(Collection.tenant_id.in_(tenant_ids))
            .order_by(Collection.created_at)
        ).all()
    ]


@app.post("/v1/collections/{collection_id}/documents", status_code=202)
def upload_document(
    collection_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(404, "not_found")
    require_role(db, user, collection.tenant_id, "owner", "editor")
    data = file.file.read(settings().max_upload_bytes + 1)
    if len(data) > settings().max_upload_bytes:
        raise HTTPException(413, "file_too_large")
    mime, pages = inspect_upload(file.filename or "upload", data)
    if pages is not None and pages > settings().max_pdf_pages:
        raise HTTPException(413, "too_many_pages")
    document = Document(
        tenant_id=collection.tenant_id,
        collection_id=collection.id,
        owner_id=user.id,
        filename=clean_filename(file.filename or "upload"),
        mime=mime,
        sha256=hashlib.sha256(data).hexdigest(),
        storage_key=str(uuid4()),
        size_bytes=len(data),
        page_count=pages,
        status="pending",
    )
    db.add(document)
    db.commit()
    try:
        storage().put(document.storage_key, data, mime)
    except Exception:
        document.status = "failed"
        document.error_code = "storage_upload_failed"
        db.commit()
        raise HTTPException(503, "storage_unavailable")
    return {"document_id": document.id, "status": document.status}


@app.get("/v1/collections/{collection_id}/documents")
def list_documents(
    collection_id: str,
    page: int = Query(1, ge=1, le=1_000_000),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    collection = db.get(Collection, collection_id)
    if not collection:
        raise HTTPException(404, "not_found")
    membership(db, user.id, collection.tenant_id)
    query = (
        select(Document)
        .where(Document.collection_id == collection_id, Document.tenant_id == collection.tenant_id)
        .order_by(Document.created_at.desc(), Document.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return [
        {
            "id": document.id,
            "filename": document.filename,
            "mime": document.mime,
            "size_bytes": document.size_bytes,
            "page_count": document.page_count,
            "status": document.status,
            "error_code": document.error_code,
            "created_at": document.created_at,
        }
        for document in db.scalars(query).all()
    ]


@app.get("/v1/documents/{document_id}")
def document_status(
    document_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "not_found")
    membership(db, user.id, document.tenant_id)
    return {
        "id": document.id,
        "collection_id": document.collection_id,
        "filename": document.filename,
        "status": document.status,
        "page_count": document.page_count,
        "error_code": document.error_code,
    }
