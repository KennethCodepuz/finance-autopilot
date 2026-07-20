from typing import Optional
from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Account(Base, TimestampMixin):
    """Stores financial accounts synced from Plaid."""
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plaid_account_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    item_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    official_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mask: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    balance_available: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    balance_current: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    iso_currency_code: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        cascade="all, delete-orphan",
    )
