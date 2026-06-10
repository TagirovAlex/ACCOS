import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import PROJECT_ROOT
from app.core.dependencies import get_db, get_current_user_id
from app.repositories.user_repository import UserRepository
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import (
    KnowledgeUploadResponse,
    KnowledgeSearchQuery,
    KnowledgeSearchResponse,
    FolderListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 50 * 1024 * 1024


async def _require_documents_manage(db: AsyncSession, user_id: str):
    user = await UserRepository(db).get(uuid.UUID(user_id))
    if not user:
        raise HTTPException(401, "User not found")
    permissions = (user.permissions or "").split(",")
    if "documents_manage" not in permissions and not user.is_admin:
        raise HTTPException(403, "Permission denied: documents_manage required")
    return user


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    folder: str = Form(""),
    ad_group_dn: str | None = Form(None),
    doc_number: str | None = Form(None),
    doc_date: str | None = Form(None),
    supersedes_doc_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 50 MB)")

    doc_id = uuid.uuid4()
    knowledge_dir = PROJECT_ROOT / "static" / "knowledge" / str(doc_id)
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    file_path = knowledge_dir / file.filename
    file_path.write_bytes(content)
    storage_path = f"static/knowledge/{doc_id}/{file.filename}"

    parsed_date = None
    if doc_date:
        try:
            parsed_date = datetime.fromisoformat(doc_date)
        except (ValueError, TypeError):
            parsed_date = None

    svc = KnowledgeService(db)
    result = await svc.create_document(
        title=title or file.filename,
        filename=file.filename,
        content_type=ext,
        file_path=storage_path,
        folder=folder,
        ad_group_dn=ad_group_dn,
        doc_number=doc_number,
        doc_date=parsed_date,
        supersedes_doc_id=supersedes_doc_id,
        created_by=uuid.UUID(user_id),
    )
    return KnowledgeUploadResponse(success=True, document_id=str(result["document_id"]))


@router.get("/documents")
async def list_documents(
    folder: str | None = Query(None),
    include_inactive: bool = Query(False),
    skip: int = Query(0),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    db_user = await UserRepository(db).get(uuid.UUID(user_id))
    svc = KnowledgeService(db)
    ad_group_dns = getattr(db_user, "ad_group_dns", None)
    docs = await svc.list_documents(
        folder=folder,
        ad_group_dns=ad_group_dns,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit,
    )
    return docs


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = KnowledgeService(db)
    doc = await svc.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)
    svc = KnowledgeService(db)
    ok = await svc.delete_document(doc_id)
    if not ok:
        raise HTTPException(404, "Document not found")
    return {"success": True}


@router.post("/documents/{doc_id}/reindex")
async def reindex_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)
    svc = KnowledgeService(db)
    result = await svc.reindex_document(doc_id)
    if not result["success"]:
        raise HTTPException(400, result.get("error", "Reindex failed"))
    return result


@router.post("/documents/{doc_id}/replace")
async def replace_document(
    doc_id: uuid.UUID,
    file: UploadFile = File(...),
    title: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 50 MB)")

    new_id = uuid.uuid4()
    knowledge_dir = PROJECT_ROOT / "static" / "knowledge" / str(new_id)
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    file_path = knowledge_dir / file.filename
    file_path.write_bytes(content)
    storage_path = f"static/knowledge/{new_id}/{file.filename}"

    svc = KnowledgeService(db)
    result = await svc.replace_document(
        old_id=doc_id,
        title=title or file.filename,
        filename=file.filename,
        content_type=ext,
        file_path=storage_path,
        created_by=uuid.UUID(user_id),
    )
    if not result["success"]:
        raise HTTPException(400, result.get("error", "Replace failed"))
    return {"success": True, "new_document_id": result["document_id"]}


@router.get("/folders", response_model=FolderListResponse)
async def list_folders(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = KnowledgeService(db)
    folders = await svc.get_folders()
    return FolderListResponse(folders=folders)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    query: KnowledgeSearchQuery,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    db_user = await UserRepository(db).get(uuid.UUID(user_id))
    svc = KnowledgeService(db)
    ad_group_dns = getattr(db_user, "ad_group_dns", None)
    result = await svc.search(query.query, ad_group_dns)
    return result


@router.get("/search-docs")
async def search_documents_for_replace(
    q: str = Query("", min_length=1),
    limit: int = Query(10),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)
    svc = KnowledgeService(db)
    docs = await svc.search_documents(q, limit)
    return docs
