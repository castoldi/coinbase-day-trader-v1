from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    initial_cash_usd: Mapped[float] = mapped_column(Float, nullable=False)
    cash_usd: Mapped[float] = mapped_column(Float, nullable=False)
    equity_usd: Mapped[float] = mapped_column(Float, nullable=False)
    realized_pnl_usd: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    max_drawdown_fraction: Mapped[float] = mapped_column(Float, nullable=False)
    trading_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    safety_lock_reason: Mapped[str] = mapped_column(String, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(String, nullable=False)
    strategy: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    entry_value_usd: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl_usd: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BotStatus(Base):
    __tablename__ = "bot_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    strategies: Mapped[str] = mapped_column(String, nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
