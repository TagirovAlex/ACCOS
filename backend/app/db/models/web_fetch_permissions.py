import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class WebFetchPermissions(Base):
    __tablename__ = "web_fetch_permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requests_per_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    requests_per_day: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    max_chars: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_usage_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    allowed_domains: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocked_domains: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
