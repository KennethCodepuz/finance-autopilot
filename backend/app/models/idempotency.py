from datetime import datetime
from typing import Any, Optional
from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class IdempotencyKey(Base, TimestampMixin):
    """Tracks idempotency keys for client->backend and backend->Plaid calls to prevent double execution."""
    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="processing", nullable=False)  # processing, completed
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    ledger_entries: Mapped[list["OutboxLedger"]] = relationship("OutboxLedger", back_populates="idempotency_key_rel")
