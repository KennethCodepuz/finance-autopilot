from typing import Any, Optional
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class OutboxLedger(Base, TimestampMixin):
    """Internal outbox ledger for proposed and pending financial tool actions."""
    __tablename__ = "outbox_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    idempotency_key_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("idempotency_keys.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)  # pending, processing, confirmed, failed, rejected
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(50), default="low", nullable=False)  # low, high
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    idempotency_key_rel: Mapped[Optional["IdempotencyKey"]] = relationship(
        "IdempotencyKey",
        back_populates="ledger_entries",
    )
