import logging
import re
import uuid
from datetime import datetime, timezone

import tiktoken
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.rag_adapter import RAGAdapter
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    import pdfplumber
    text_parts = []
    num_pages = 0
    with pdfplumber.open(file_path) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    result = "\n".join(text_parts)
    stripped = result.strip()

    if stripped and num_pages > 0 and len(stripped) / num_pages > 20:
        return result

    import fitz
    import pytesseract
    from PIL import Image
    import io

    try:
        doc = fitz.open(file_path)
        ocr_parts = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img, lang="rus+eng")
            ocr_parts.append(text)
        doc.close()
        ocr_text = "\n".join(ocr_parts)
        if ocr_text.strip():
            return ocr_text
    except Exception as e:
        logger.error(f"OCR fallback failed for {file_path}: {e}")

    return result if stripped else ""


def extract_text_from_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_from_image(file_path: str) -> str:
    from PIL import Image
    import pytesseract
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang="rus+eng")
    return text


def extract_text(file_path: str, content_type: str) -> str:
    if content_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif content_type == "docx":
        return extract_text_from_docx(file_path)
    elif content_type in ("png", "jpeg", "jpg"):
        return extract_text_from_image(file_path)
    else:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()


SUPERSESSION_PATTERNS = [
    r"(?:отмен[ия]т|отменяется|призна[тью]\s*утратившим\s*силу|отменяет|взамен|вместо)\s*(?:приказ[аом]?\s*[№#]?\s*)?(\d[\d\-/]*)",
    r"отмен[ия]т[ься]?\s+.*?[№#]\s*(\d[\d\-/]*)",
    r"(?:признать\s+)?утратившим\s+силу\s+.*?[№#]\s*(\d[\d\-/]*)",
]


def detect_supersession(text: str) -> str | None:
    for pattern in SUPERSESSION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_content = encoder.decode(chunk_tokens)
        chunks.append(chunk_text_content)
        if end >= len(tokens):
            break
        start = end - overlap
    return chunks


class RAGService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeRepository(session)
        self.settings_svc = SettingsService(session)

    async def _get_adapter(self) -> RAGAdapter:
        model = await self.settings_svc.get("rag_embedding_model", "intfloat/multilingual-e5-small")
        if model.startswith("local/"):
            api_key = ""
            base_url = "local"
            model = model.replace("local/", "", 1)
        else:
            base_url = await self.settings_svc.get("lmstudio_base_url", "")
            api_key = await self.settings_svc.get("lmstudio_api_key", "")
        return RAGAdapter(base_url=base_url, model=model, api_key=api_key)

    async def index_document(self, document_id: uuid.UUID) -> dict:
        doc = await self.repo.get_document(document_id)
        if not doc:
            return {"success": False, "error": "Document not found"}

        try:
            doc.status = "indexing"
            await self.session.flush()

            file_path = doc.file_path
            if not file_path.startswith("/") and not file_path.startswith("C:"):
                from app.core.paths import STATIC_DIR
                rel = file_path.lstrip("static/")
                file_path = str(STATIC_DIR / rel)

            import os as _os
            if not _os.path.isfile(file_path) and doc.content_type == "doc_scrape":
                chunks = await self.repo.get_chunks_by_document(document_id)
                if chunks:
                    raw_text = "\n\n---PAGE BREAK---\n\n".join(c.content for c in chunks)
                else:
                    raw_text = ""
            else:
                raw_text = extract_text(file_path, doc.content_type)
            if not raw_text.strip():
                doc.status = "failed"
                doc.error_message = "No text could be extracted"
                return {"success": False, "error": "No text extracted"}

            chunk_size = await self.settings_svc.get_int("rag_chunk_size", 500)
            chunk_overlap = await self.settings_svc.get_int("rag_chunk_overlap", 50)
            chunks = chunk_text(raw_text, chunk_size, chunk_overlap)

            adapter = await self._get_adapter()
            embeddings = await adapter.embed(chunks)

            await self.repo.delete_chunks_by_document(document_id)

            for idx, chunk_content in enumerate(chunks):
                embedding = embeddings[idx] if embeddings and idx < len(embeddings) else None
                await self.repo.create_chunk(
                    document_id=document_id,
                    content=chunk_content,
                    chunk_index=idx,
                    embedding=embedding,
                    meta={"chunk": idx, "total_chunks": len(chunks)},
                )

            supersession_doc_number = detect_supersession(raw_text)
            if supersession_doc_number:
                logger.info(f"Detected supersession: doc {doc.doc_number} supersedes {supersession_doc_number}")
                target = await self.repo.get_document_by_doc_number(supersession_doc_number)
                if target and str(target.id) != str(document_id):
                    await self.repo.replace_document(target.id, document_id)
                    logger.info(f"Linked supersession: {supersession_doc_number} -> {doc.doc_number}")

            doc.status = "ready"
            await self.session.flush()
            return {"success": True, "chunks": len(chunks)}

        except Exception as e:
            logger.error(f"Indexing failed for {document_id}: {e}")
            doc.status = "failed"
            doc.error_message = str(e)
            await self.session.flush()
            return {"success": False, "error": str(e)}

    async def search(self, query: str, ad_group_dns: list[str] | None = None) -> dict:
        enabled = await self.settings_svc.get_bool("rag_enabled", False)
        if not enabled:
            return {"success": True, "results": []}

        adapter = await self._get_adapter()
        top_k = await self.settings_svc.get_int("rag_top_k", 5)
        min_score = await self.settings_svc.get_float("rag_min_score", 0.5)

        query_embeddings = await adapter.embed([query])
        if not query_embeddings or len(query_embeddings) == 0:
            return {"success": False, "error": "Failed to embed query"}

        query_embedding = query_embeddings[0]
        rows = await self.repo.vector_search(
            embedding=query_embedding,
            ad_group_dns=ad_group_dns,
            top_k=top_k,
            min_score=min_score,
        )

        if not rows:
            return {"success": True, "results": []}

        doc_map = {}
        for row in rows:
            doc_id = row["document_id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "document_id": doc_id,
                    "document_title": row["title"],
                    "folder": row["folder"],
                    "chunks": [],
                }
            doc_map[doc_id]["chunks"].append({
                "content": row["content"],
                "chunk_index": row["chunk_index"],
                "meta": row.get("meta"),
                "similarity": row["similarity"],
            })

        return {"success": True, "results": list(doc_map.values())}

    async def build_context(self, query: str, ad_group_dns: list[str] | None = None) -> str:
        result = await self.search(query, ad_group_dns)
        if not result.get("success") or not result.get("results"):
            return ""

        blocks = []
        for doc in result["results"]:
            doc_id = doc["document_id"]
            title = doc["document_title"]
            for chunk in doc["chunks"]:
                blocks.append(f"[doc: {doc_id}] {title}:\n{chunk['content']}")

        context = "\n\n".join(blocks)
        return context

    async def get_folders(self) -> list[str]:
        return await self.repo.list_folders()
