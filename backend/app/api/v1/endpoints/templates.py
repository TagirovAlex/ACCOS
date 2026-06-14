import json
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import get_db, get_current_user_id, require_admin
from app.core.paths import STATIC_DIR
from app.repositories.template_repository import DocTemplateRepository
from app.schemas.chat import BaseResponse

router = APIRouter(prefix="/admin/doc-templates", tags=["admin"])

TEMPLATES_DIR = STATIC_DIR / "templates"


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    file_path: str
    variables: str | None = None
    category: str | None = None


class TemplateListResponse(BaseResponse):
    templates: list[TemplateResponse] = []


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    repo = DocTemplateRepository(db)
    templates = await repo.list_all()
    return TemplateListResponse(templates=[
        TemplateResponse(id=str(t.id), name=t.name, description=t.description,
                         file_path=t.file_path, variables=t.variables, category=t.category)
        for t in templates
    ])


@router.post("", response_model=BaseResponse)
async def create_template(
    request: Request,
    name: str = "",
    description: str = "",
    variables: str = "",
    category: str = "",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "template.html").suffix
    unique_name = f"{uuid4().hex}{ext}"
    path = TEMPLATES_DIR / unique_name
    path.write_bytes(await file.read())
    repo = DocTemplateRepository(db)
    await repo.create(
        name=name or file.filename or "template",
        file_path=str(path),
        description=description or None,
        variables=variables or None,
        category=category or None,
    )
    await db.commit()
    return BaseResponse(success=True)


@router.put("/{template_id}", response_model=BaseResponse)
async def update_template(
    request: Request,
    template_id: str,
    name: str = "",
    description: str = "",
    variables: str = "",
    category: str = "",
    file: UploadFile | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    repo = DocTemplateRepository(db)
    tpl = await repo.get(UUID(template_id))
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    kwargs = {}
    if name:
        kwargs["name"] = name
    if description:
        kwargs["description"] = description
    if variables:
        kwargs["variables"] = variables
    if category:
        kwargs["category"] = category
    if file:
        ext = Path(file.filename or "template.html").suffix
        old = Path(tpl.file_path)
        if old.exists():
            old.unlink()
        new_path = TEMPLATES_DIR / f"{uuid4().hex}{ext}"
        new_path.write_bytes(await file.read())
        kwargs["file_path"] = str(new_path)
    await repo.update(UUID(template_id), **kwargs)
    await db.commit()
    return BaseResponse(success=True)


@router.delete("/{template_id}", response_model=BaseResponse)
async def delete_template(
    request: Request,
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    repo = DocTemplateRepository(db)
    tpl = await repo.get(UUID(template_id))
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    old = Path(tpl.file_path)
    if old.exists():
        old.unlink()
    await repo.delete(UUID(template_id))
    await db.commit()
    return BaseResponse(success=True)


@router.get("/generated-documents/{doc_id}/download")
async def download_generated_document(
    request: Request,
    doc_id: str,
    db: AsyncSession = Depends(get_db),
):
    from app.db.models.doc_template import GeneratedDocument
    doc = await db.get(GeneratedDocument, UUID(doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(doc.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(str(path), filename=doc.source_file or path.name)
