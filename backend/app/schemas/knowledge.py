from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: str
    filename: str
    content_type: str
    status: str
    file_hash: str | None = None
    ad_group_dn: str | None = None
    folder: str = ""
    doc_number: str | None = None
    doc_date: datetime | None = None
    is_active: bool = True
    supersedes_doc_id: str | None = None
    superseded_by_doc_id: str | None = None
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeChunkResponse(BaseModel):
    content: str
    chunk_index: int
    meta: dict | None = None
    similarity: float | None = None


class KnowledgeSearchResult(BaseModel):
    document_id: str
    document_title: str
    folder: str
    chunks: list[KnowledgeChunkResponse]


class KnowledgeDocumentCreate(BaseModel):
    title: str
    filename: str
    content_type: str
    folder: str = ""
    ad_group_dn: str | None = None
    doc_number: str | None = None
    doc_date: datetime | None = None
    supersedes_doc_id: str | None = None


class KnowledgeDocumentReplace(BaseModel):
    supersedes_doc_id: str


class KnowledgeUploadResponse(BaseModel):
    success: bool
    document_id: str
    error: str | None = None


class KnowledgeSearchQuery(BaseModel):
    query: str
    top_k: int = 5
    min_score: float = 0.5


class KnowledgeSearchResponse(BaseModel):
    success: bool
    results: list[KnowledgeSearchResult] = []
    error: str | None = None


class FolderListResponse(BaseModel):
    folders: list[str]
