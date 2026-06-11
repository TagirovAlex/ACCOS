import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

import hashlib
from urllib.parse import quote

from app.core.config import PROJECT_ROOT
from app.core.dependencies import get_db, get_current_user_id
from app.repositories.user_repository import UserRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.knowledge_service import KnowledgeService
from app.services.settings_service import SettingsService
from app.adapters.ldap_adapter import LDAPAdapter
from fastapi.responses import HTMLResponse

from app.schemas.knowledge import (
    KnowledgeUploadResponse,
    KnowledgeUploadBatchResponse,
    BatchUploadItem,
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

    file_hash = hashlib.sha256(content).hexdigest()

    svc = KnowledgeService(db)

    existing = await svc.repo.find_by_hash(file_hash)
    if existing:
        return KnowledgeUploadResponse(success=True, document_id=str(existing.id))

    safe_name = f"{uuid.uuid4().hex}.{ext}"

    folder_dir = folder.strip("/") if folder else ""
    knowledge_dir = PROJECT_ROOT / "static" / "knowledge"
    if folder_dir:
        knowledge_dir = knowledge_dir / folder_dir
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    file_path = knowledge_dir / safe_name
    file_path.write_bytes(content)
    if folder_dir:
        storage_path = f"static/knowledge/{folder_dir}/{safe_name}"
    else:
        storage_path = f"static/knowledge/{safe_name}"

    parsed_date = None
    if doc_date:
        try:
            parsed_date = datetime.fromisoformat(doc_date)
        except (ValueError, TypeError):
            parsed_date = None

    result = await svc.create_document(
        title=title or file.filename,
        filename=file.filename,
        content_type=ext,
        file_path=storage_path,
        folder=folder,
        file_hash=file_hash,
        ad_group_dn=ad_group_dn,
        doc_number=doc_number,
        doc_date=parsed_date,
        supersedes_doc_id=supersedes_doc_id,
        created_by=uuid.UUID(user_id),
    )
    return KnowledgeUploadResponse(success=True, document_id=str(result["document_id"]))


@router.post("/upload-batch", response_model=KnowledgeUploadBatchResponse)
async def upload_documents_batch(
    files: list[UploadFile] = File(...),
    folder: str = Form(""),
    ad_group_dn: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)

    results: list[BatchUploadItem] = []
    svc = KnowledgeService(db)

    for file in files:
        try:
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                results.append(BatchUploadItem(filename=file.filename, success=False, error=f"Unsupported file type: .{ext}"))
                continue

            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                results.append(BatchUploadItem(filename=file.filename, success=False, error="File too large (max 50 MB)"))
                continue

            file_hash = hashlib.sha256(content).hexdigest()
            existing = await svc.repo.find_by_hash(file_hash)
            if existing:
                results.append(BatchUploadItem(filename=file.filename, success=True, document_id=str(existing.id)))
                continue

            safe_name = f"{uuid.uuid4().hex}.{ext}"
            folder_dir = folder.strip("/") if folder else ""
            knowledge_dir = PROJECT_ROOT / "static" / "knowledge"
            if folder_dir:
                knowledge_dir = knowledge_dir / folder_dir
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            file_path = knowledge_dir / safe_name
            file_path.write_bytes(content)
            storage_path = f"static/knowledge/{folder_dir}/{safe_name}" if folder_dir else f"static/knowledge/{safe_name}"

            result = await svc.create_document(
                title=file.filename,
                filename=file.filename,
                content_type=ext,
                file_path=storage_path,
                folder=folder,
                file_hash=file_hash,
                ad_group_dn=ad_group_dn,
                created_by=uuid.UUID(user_id),
            )
            results.append(BatchUploadItem(filename=file.filename, success=True, document_id=result["document_id"]))
        except Exception as e:
            logger.error(f"Batch upload failed for {file.filename}: {e}")
            results.append(BatchUploadItem(filename=file.filename, success=False, error=str(e)[:200]))

    return KnowledgeUploadBatchResponse(success=True, results=results)


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


@router.post("/reindex-all")
async def reindex_all_documents(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)
    svc = KnowledgeService(db)
    result = await svc.reindex_all()
    return result


@router.post("/reindex-new")
async def reindex_new_documents(
    only_failed: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)
    svc = KnowledgeService(db)
    if only_failed:
        result = await svc.reindex_failed()
    else:
        result = await svc.reindex_new()
    return result


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

    file_hash = hashlib.sha256(content).hexdigest()
    safe_name = f"{uuid.uuid4().hex}.{ext}"

    svc = KnowledgeService(db)
    old_doc = await svc.get_document(doc_id)
    if not old_doc:
        raise HTTPException(404, "Original document not found")
    folder_dir = (old_doc.get("folder") or "").strip("/")
    knowledge_dir = PROJECT_ROOT / "static" / "knowledge"
    if folder_dir:
        knowledge_dir = knowledge_dir / folder_dir
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    file_path = knowledge_dir / safe_name
    file_path.write_bytes(content)
    if folder_dir:
        storage_path = f"static/knowledge/{folder_dir}/{safe_name}"
    else:
        storage_path = f"static/knowledge/{safe_name}"

    result = await svc.replace_document(
        old_id=doc_id,
        title=title or file.filename,
        filename=file.filename,
        content_type=ext,
        file_path=storage_path,
        file_hash=file_hash,
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


@router.get("/departments")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    ss = SettingsService(db)
    ldap_enabled = await ss.get_bool("ldap_enabled", False)
    if not ldap_enabled:
        return {"departments": []}
    server = await ss.get("ldap_server", "")
    domain = await ss.get("ldap_domain", "")
    base_dn = await ss.get("ldap_base_dn", "")
    clients_ou = await ss.get("ad_clients_ou", "")
    if not server or not clients_ou:
        return {"departments": []}
    bind_username = await ss.get("ldap_bind_username", "")
    bind_password = await ss.get("ldap_bind_password", "")
    bind_dn = await ss.get("ldap_bind_dn", "")
    adapter = LDAPAdapter(server=server, domain=domain, base_dn=base_dn,
                          bind_username=bind_username or None,
                          bind_password=bind_password or None,
                          bind_dn=bind_dn or None)
    ous = await adapter.list_ous(search_base=clients_ou)
    from app.repositories.user_repository import UserRepository
    user = await UserRepository(db).get(uuid.UUID(user_id))
    if user and user.admin_role == "none":
        hidden_raw = await ss.get("hidden_doc_folders", "")
        hidden = {h.strip().lower() for h in hidden_raw.split(",") if h.strip()}
        if hidden:
            ous = [d for d in ous if d.get("ou", "").lower() not in hidden]
    return {"departments": ous}


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


@router.get("/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_documents_manage(db, user_id)
    svc = KnowledgeService(db)
    chunks = await svc.get_document_chunks(doc_id)
    return {"chunks": chunks}


@router.get("/{doc_id}/preview", response_class=HTMLResponse)
async def preview_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = KnowledgeService(db)
    doc = await svc.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    file_abs = PROJECT_ROOT / doc["file_path"]
    if not file_abs.exists():
        doc_title = doc["title"] or doc["filename"]
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{doc_title}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
@media print {{ body {{ display: none; }} }}
</style></head><body>
<h2>{doc_title}</h2>
<p>Файл не найден на сервере.</p>
</body></html>"""

    doc_title = doc["title"] or doc["filename"]
    ext = doc["content_type"]
    file_url = quote(f"/{doc['file_path']}", safe="/")

    body_html = ""
    if ext in ("txt", "md"):
        content = file_abs.read_text("utf-8", errors="replace")
        import html
        body_html = f"<pre style=\"white-space:pre-wrap;word-break:break-word\">{html.escape(content)}</pre>"
    elif ext in ("png", "jpg", "jpeg"):
        import base64
        b64 = base64.b64encode(file_abs.read_bytes()).decode()
        body_html = f"<img src=\"data:image/{ext};base64,{b64}\" style=\"max-width:100%;height:auto\" />"
    elif ext == "pdf":
        import json
        from app.core.paths import STATIC_DIR as _SD
        cache_dir = _SD / "knowledge_preview" / str(doc_id)
        cache_info = cache_dir / "_info.json"
        file_mtime = file_abs.stat().st_mtime
        use_cache = False
        if cache_info.exists():
            try:
                info = json.loads(cache_info.read_text())
                if info.get("file_mtime") == file_mtime and info.get("page_count", 0) > 0:
                    use_cache = True
                    num_pages = info["page_count"]
            except Exception:
                pass
        if use_cache:
            pages_html = []
            for i in range(1, num_pages + 1):
                img_path = f"/static/knowledge_preview/{doc_id}/page_{i:04d}.jpg"
                pages_html.append(
                    f"<div style=\"margin-bottom:12px;text-align:center\">"
                    f"<p style=\"color:#666;font-size:12px;margin:4px 0\">Страница {i} из {num_pages}</p>"
                    f"<img src=\"{img_path}\" style=\"max-width:100%;height:auto;border-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,0.15)\" />"
                    f"</div>"
                )
            body_html = "".join(pages_html)
        else:
            import fitz
            import base64
            cache_dir.mkdir(parents=True, exist_ok=True)
            pdf_doc = fitz.open(str(file_abs))
            num_pages = len(pdf_doc)
            pages_html = []
            for page_num in range(num_pages):
                page = pdf_doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("jpeg")
                (cache_dir / f"page_{page_num + 1:04d}.jpg").write_bytes(img_data)
                b64 = base64.b64encode(img_data).decode()
                pages_html.append(
                    f"<div style=\"margin-bottom:12px;text-align:center\">"
                    f"<p style=\"color:#666;font-size:12px;margin:4px 0\">Страница {page_num + 1} из {num_pages}</p>"
                    f"<img src=\"data:image/jpeg;base64,{b64}\" style=\"max-width:100%;height:auto;border-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,0.15)\" />"
                    f"</div>"
                )
            pdf_doc.close()
            cache_info.write_text(json.dumps({"file_mtime": file_mtime, "page_count": num_pages}))
            body_html = "".join(pages_html)
    elif ext == "docx":
        from app.services.rag_service import extract_text_from_docx
        content = extract_text_from_docx(str(file_abs))
        import html as hlib
        body_html = f"<pre style=\"white-space:pre-wrap;word-break:break-word\">{hlib.escape(content)}</pre>"
    else:
        body_html = f"<p>Формат {ext} не поддерживается для просмотра.</p>"

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{doc_title}</title>
<style>
* {{ user-select: none; -webkit-user-select: none; }}
body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; padding: 16px; background: #f5f5f5; color: #222; }}
.container {{ max-width: 1000px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); padding: 24px; }}
h2 {{ margin-top: 0; color: #1a1a2e; }}
.meta {{ color: #666; font-size: 13px; margin-bottom: 16px; }}
pre {{ font-size: 14px; line-height: 1.6; }}
img {{ border-radius: 4px; }}
@media print {{ body {{ display: none; }} }}
</style></head><body>
<div class="container">
<h2>{doc_title}</h2>
<div class="meta">{doc["folder"] or "Общий доступ"} &middot; {ext.upper()}</div>
{body_html}
</div>
<script>
document.addEventListener("contextmenu", e => e.preventDefault());
document.addEventListener("keydown", e => {{
  if (e.ctrlKey && (e.key === "s" || e.key === "p")) e.preventDefault();
}});
</script>
</body></html>"""
