import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ad_group_dn: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    folder: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    doc_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    doc_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supersedes_doc_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), nullable=True)
    superseded_by_doc_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    supersedes = relationship("KnowledgeDocument", foreign_keys=[supersedes_doc_id], remote_side="KnowledgeDocument.id", lazy="select")
    superseded_by = relationship("KnowledgeDocument", foreign_keys=[superseded_by_doc_id], remote_side="KnowledgeDocument.id", lazy="select")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan", lazy="select")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    document = relationship("KnowledgeDocument", back_populates="chunks")
