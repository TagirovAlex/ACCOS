import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    ad_group_dn: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    permissions: Mapped[str] = mapped_column(Text, nullable=False, default="chat")
    start_balance: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
