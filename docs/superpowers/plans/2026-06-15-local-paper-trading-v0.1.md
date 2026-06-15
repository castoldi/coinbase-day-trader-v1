# Local Paper Trading v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable v0.1 local paper trading platform with Coinbase sandbox integration wiring, persistent SQLite state, a FastAPI backend, a React dashboard, operational scripts, docs, versioning, and safety-first defaults.

**Architecture:** Python owns configuration, persistence, paper trading, Coinbase integration checks, bot lifecycle, and API endpoints. React/Vite consumes the local FastAPI API and renders operational trading pages from real local state. SQLite is the single durable local store; `.env` is the only secrets source.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Pydantic Settings, httpx, pytest, uvicorn, SQLite, React, Vite, TypeScript, Vitest, Testing Library, Playwright for dashboard verification when available.

---

## Scope Check

The approved design covers several subsystems. This plan implements them as one v0.1 vertical slice because each subsystem is needed for a runnable bot/dashboard loop. The first price-action strategy is delivered as a transcript-gated strategy shell with explicit metadata and no real buy/sell signals until the video transcript is reviewed.

## File Structure

- Create: `pyproject.toml` - Python package metadata, dependencies, pytest config, console scripts.
- Create: `package.json` - root convenience scripts for dashboard commands.
- Create: `.env.example` - documented non-secret environment variables.
- Modify: `.gitignore` - ensure runtime outputs and secrets stay out of git.
- Create: `README.md` - public setup, safety disclaimer, usage, screenshots section.
- Create: `CHANGELOG.md` - v0.1.0 entry.
- Create: `AGENTS.md` - AI/developer operating instructions.
- Create: `VERSION` - current project version.
- Create: `logs/.gitkeep` - track logs directory without log files.
- Create: `data/.gitkeep` - track reusable market-data directory.
- Create: `src/trader_app/config.py` - typed settings and mode validation.
- Create: `src/trader_app/database.py` - SQLite engine/session helpers and table creation.
- Create: `src/trader_app/models.py` - SQLAlchemy tables.
- Create: `src/trader_app/account.py` - account initialization, rollover, and safety lock behavior.
- Create: `src/trader_app/strategies/base.py` - strategy interface and signal types.
- Create: `src/trader_app/strategies/price_action_transcript.py` - transcript-gated price-action shell.
- Create: `src/trader_app/strategies/registry.py` - single/list/ALL strategy selection.
- Create: `src/trader_app/broker/paper.py` - simulated order execution and trade persistence.
- Create: `src/trader_app/integrations/coinbase.py` - Coinbase sandbox/public client and smoke check.
- Create: `src/trader_app/bot/runner.py` - bot heartbeat, stale detection, and one-cycle paper execution shell.
- Create: `src/trader_app/backtests/periods.py` - standard backtest period calculation.
- Create: `src/trader_app/logging_config.py` - daily rotating compressed log setup.
- Create: `src/trader_app/api.py` - FastAPI app and dashboard endpoints.
- Create: `src/trader_app/cli.py` - command-line entry points.
- Create: `scripts/start_bot.ps1` - idempotent bot starter for Task Scheduler/manual calls.
- Create: `scripts/start_dashboard.ps1` - backend and dashboard starter.
- Create: `dashboard/package.json` - dashboard dependencies and scripts.
- Create: `dashboard/index.html` - Vite entry HTML.
- Create: `dashboard/src/main.tsx` - React app bootstrap.
- Create: `dashboard/src/api.ts` - typed API fetch helpers.
- Create: `dashboard/src/App.tsx` - page layout and routing state.
- Create: `dashboard/src/App.css` - dashboard styling.
- Test: `tests/` Python test suite for backend behavior.
- Test: `dashboard/src/App.test.tsx` dashboard render smoke test.

## Task 1: Project Metadata, Ignore Rules, And Docs Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `package.json`
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `AGENTS.md`
- Create: `VERSION`
- Create: `logs/.gitkeep`
- Create: `data/.gitkeep`

- [ ] **Step 1: Write docs/config expectation test**

Create `tests/test_project_files.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_secret_files_are_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in ignore
    assert "!.env.example" in ignore
    assert "logs/*" in ignore


def test_required_public_docs_exist():
    for name in ["README.md", "CHANGELOG.md", "AGENTS.md", "VERSION", ".env.example"]:
        assert (ROOT / name).exists(), f"{name} should exist"


def test_env_example_has_no_secret_values():
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "COINBASE_API_KEY_NAME=" in env_example
    assert "GMAIL_APP_PASSWORD=" in env_example
    assert "replace-me" not in env_example.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_files.py -v`

Expected: FAIL because `pyproject.toml`, docs, and `.env.example` do not exist yet.

- [ ] **Step 3: Create project metadata and public files**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "coinbase-day-trader-v1"
version = "0.1.0"
description = "Local-first Coinbase crypto paper trading bot and dashboard."
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "pydantic-settings>=2.4.0",
  "python-dotenv>=1.0.1",
  "sqlalchemy>=2.0.32",
  "uvicorn[standard]>=0.30.6",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.2",
  "pytest-cov>=5.0.0",
]

[project.scripts]
trader = "trader_app.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Create root `package.json`:

```json
{
  "name": "coinbase-day-trader-v1",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dashboard:install": "npm --prefix dashboard install",
    "dashboard:dev": "npm --prefix dashboard run dev",
    "dashboard:test": "npm --prefix dashboard test"
  }
}
```

Create `.env.example`:

```dotenv
APP_ENV=local
DATABASE_URL=sqlite:///./data/trader.sqlite3
TRADING_MODE=paper
BOT_STARTING_CASH_USD=1000
BOT_MAX_DRAWDOWN_FRACTION=0.5
BOT_HEARTBEAT_STALE_SECONDS=1800
DEFAULT_PRODUCTS=BTC-USD,ETH-USD,SOL-USD
DEFAULT_STRATEGIES=price_action_transcript

COINBASE_API_KEY_NAME=
COINBASE_API_PRIVATE_KEY=
COINBASE_SANDBOX_BASE_URL=https://api.coinbase.com

GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587
GMAIL_USER=
GMAIL_APP_PASSWORD=
EMAIL_TO=

API_HOST=127.0.0.1
API_PORT=8000
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=5173
```

Create `VERSION`:

```text
0.1.0
```

Create `README.md`:

```markdown
# Coinbase Day Trader v1

Local-first Coinbase crypto paper trading bot and dashboard.

## Financial Disclaimer

This project is experimental software. The owner is not a financial professional, and this repository does not provide financial advice. Do not use this software for live trading unless you understand the risks and have reviewed the code, configuration, exchange permissions, and strategy behavior yourself.

## Current Safety Mode

Version 0.1.0 supports local paper trading first. Coinbase integration is wired for sandbox/public API checks, but live order placement is intentionally blocked.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Fill only the values you need for local testing.
3. Install Python dependencies with `pip install -e .[dev]`.
4. Start the bot with `powershell -File scripts/start_bot.ps1 -Strategies ALL`.
5. Start the dashboard with `powershell -File scripts/start_dashboard.ps1`.

## Dashboard

Screenshots will be added after the dashboard is implemented and verified.

## Strategies

- `price_action_transcript`: price-action strategy shell gated on transcript review from the requested YouTube video.

## Backtests

Standard periods are 2024, 2025, 2026, and the last 30 days. Each run starts with 1000 USD paper cash.
```

Create `CHANGELOG.md`:

```markdown
# Changelog

## 0.1.0 - 2026-06-15

- Added approved local paper trading design.
- Started v0.1.0 implementation plan.
- Established safety-first project metadata and documentation.
```

Create `AGENTS.md`:

```markdown
# Agent Instructions

## Safety

- Never commit `.env` or secret values.
- Keep live Coinbase trading blocked until a future explicit implementation enables it.
- Treat local paper trading as the default mode.
- Use tests before production code changes.

## Versioning

- Update `VERSION` and `CHANGELOG.md` for meaningful changes.
- Commit focused changes.
- Tags use `vX.Y.Z-YYYYMMDD-HHMMSS-CT`.

## Operations

- Bot logs and dashboard logs live under `logs/`.
- Market data cache lives under `data/`.
- Runtime databases and logs are not committed.
```

Update `.gitignore` to keep existing rules and include:

```gitignore
.coverage
htmlcov/
data/*
!data/.gitkeep
```

Create empty files `logs/.gitkeep` and `data/.gitkeep`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_files.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add pyproject.toml package.json .env.example .gitignore README.md CHANGELOG.md AGENTS.md VERSION logs/.gitkeep data/.gitkeep tests/test_project_files.py
git commit -m "chore: scaffold project metadata"
```

## Task 2: Typed Configuration And Trading Mode Guardrails

**Files:**
- Create: `src/trader_app/__init__.py`
- Create: `src/trader_app/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
import pytest

from trader_app.config import Settings, TradingMode


def test_defaults_are_safe_for_paper_trading():
    settings = Settings()
    assert settings.trading_mode == TradingMode.PAPER
    assert settings.bot_starting_cash_usd == 1000
    assert settings.bot_max_drawdown_fraction == 0.5


def test_live_mode_fails_closed():
    with pytest.raises(ValueError, match="Live trading is not implemented"):
        Settings(TRADING_MODE="live")


def test_email_subject_prefix_is_constant():
    settings = Settings()
    assert settings.email_subject_prefix == "AI-BOT"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`

Expected: FAIL because `trader_app.config` does not exist.

- [ ] **Step 3: Implement settings**

Create `src/trader_app/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/trader_app/config.py`:

```python
from enum import StrEnum

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingMode(StrEnum):
    PAPER = "paper"
    COINBASE_SANDBOX = "coinbase_sandbox"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "local"
    database_url: str = "sqlite:///./data/trader.sqlite3"
    trading_mode: TradingMode = Field(default=TradingMode.PAPER, alias="TRADING_MODE")
    bot_starting_cash_usd: float = 1000
    bot_max_drawdown_fraction: float = 0.5
    bot_heartbeat_stale_seconds: int = 1800
    default_products: str = "BTC-USD,ETH-USD,SOL-USD"
    default_strategies: str = "price_action_transcript"
    coinbase_api_key_name: str = ""
    coinbase_api_private_key: str = ""
    coinbase_sandbox_base_url: str = "https://api.coinbase.com"
    gmail_smtp_host: str = "smtp.gmail.com"
    gmail_smtp_port: int = 587
    gmail_user: str = ""
    gmail_app_password: str = ""
    email_to: str = ""
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 5173
    email_subject_prefix: str = "AI-BOT"

    @model_validator(mode="after")
    def block_live_mode(self) -> "Settings":
        if self.trading_mode == TradingMode.LIVE:
            raise ValueError("Live trading is not implemented in v0.1.0")
        if not 0 < self.bot_max_drawdown_fraction <= 1:
            raise ValueError("bot_max_drawdown_fraction must be between 0 and 1")
        return self

    @property
    def products(self) -> list[str]:
        return [item.strip() for item in self.default_products.split(",") if item.strip()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/__init__.py src/trader_app/config.py tests/test_config.py
git commit -m "feat: add safe typed configuration"
```

## Task 3: SQLite Models And Account Safety

**Files:**
- Create: `src/trader_app/database.py`
- Create: `src/trader_app/models.py`
- Create: `src/trader_app/account.py`
- Test: `tests/test_account.py`

- [ ] **Step 1: Write failing account tests**

Create `tests/test_account.py`:

```python
from trader_app.account import AccountService
from trader_app.database import create_session_factory, initialize_database


def make_service(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    return AccountService(session_factory)


def test_account_starts_with_1000_usd(tmp_path):
    service = make_service(tmp_path)
    account = service.get_or_create_account(1000, 0.5)
    assert account.cash_usd == 1000
    assert account.equity_usd == 1000
    assert account.trading_enabled is True


def test_account_rolls_forward_after_loss(tmp_path):
    service = make_service(tmp_path)
    service.get_or_create_account(1000, 0.5)
    account = service.apply_realized_pnl(-200)
    assert account.cash_usd == 800
    assert account.equity_usd == 800
    assert account.trading_enabled is True


def test_account_locks_forever_at_half_initial_equity(tmp_path):
    service = make_service(tmp_path)
    service.get_or_create_account(1000, 0.5)
    account = service.apply_realized_pnl(-500)
    assert account.equity_usd == 500
    assert account.trading_enabled is False
    assert account.safety_lock_reason == "equity_at_or_below_50_percent"


def test_manual_reset_reallows_trading(tmp_path):
    service = make_service(tmp_path)
    service.get_or_create_account(1000, 0.5)
    service.apply_realized_pnl(-500)
    account = service.manual_reset_safety_lock()
    assert account.trading_enabled is True
    assert account.safety_lock_reason == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_account.py -v`

Expected: FAIL because database and account modules do not exist.

- [ ] **Step 3: Implement database, models, and account service**

Create `src/trader_app/database.py`:

```python
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from trader_app.models import Base


def create_session_factory(database_url: str) -> tuple[object, sessionmaker[Session]]:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database(engine: object) -> None:
    Base.metadata.create_all(bind=engine)


def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Create `src/trader_app/models.py`:

```python
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
```

Create `src/trader_app/account.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.models import Account


class AccountService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def get_or_create_account(self, starting_cash: float, max_drawdown_fraction: float) -> Account:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                account = Account(
                    initial_cash_usd=starting_cash,
                    cash_usd=starting_cash,
                    equity_usd=starting_cash,
                    realized_pnl_usd=0,
                    max_drawdown_fraction=max_drawdown_fraction,
                    trading_enabled=True,
                    safety_lock_reason="",
                )
                session.add(account)
                session.commit()
                session.refresh(account)
            return account

    def apply_realized_pnl(self, pnl_usd: float) -> Account:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            account.realized_pnl_usd += pnl_usd
            account.cash_usd += pnl_usd
            account.equity_usd += pnl_usd
            threshold = account.initial_cash_usd * account.max_drawdown_fraction
            if account.equity_usd <= threshold:
                account.trading_enabled = False
                account.safety_lock_reason = "equity_at_or_below_50_percent"
            session.commit()
            session.refresh(account)
            return account

    def manual_reset_safety_lock(self) -> Account:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            account.trading_enabled = True
            account.safety_lock_reason = ""
            session.commit()
            session.refresh(account)
            return account
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_account.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/database.py src/trader_app/models.py src/trader_app/account.py tests/test_account.py
git commit -m "feat: add paper account safety ledger"
```

## Task 4: Strategy Interface And Selection

**Files:**
- Create: `src/trader_app/strategies/__init__.py`
- Create: `src/trader_app/strategies/base.py`
- Create: `src/trader_app/strategies/price_action_transcript.py`
- Create: `src/trader_app/strategies/registry.py`
- Test: `tests/test_strategies.py`

- [ ] **Step 1: Write failing strategy tests**

Create `tests/test_strategies.py`:

```python
from trader_app.strategies.registry import available_strategies, load_strategies


def test_load_single_strategy():
    strategies = load_strategies("price_action_transcript")
    assert [strategy.name for strategy in strategies] == ["price_action_transcript"]


def test_load_all_strategies():
    strategies = load_strategies("ALL")
    assert [strategy.name for strategy in strategies] == list(available_strategies().keys())


def test_price_action_strategy_is_transcript_gated():
    strategy = load_strategies("price_action_transcript")[0]
    assert strategy.version == "0.1.0"
    assert strategy.requires_transcript_review is True
    assert strategy.generate_signal([]).action == "hold"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_strategies.py -v`

Expected: FAIL because strategy modules do not exist.

- [ ] **Step 3: Implement strategy interface and registry**

Create `src/trader_app/strategies/__init__.py`:

```python
from trader_app.strategies.registry import available_strategies, load_strategies

__all__ = ["available_strategies", "load_strategies"]
```

Create `src/trader_app/strategies/base.py`:

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Candle:
    product_id: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    action: str
    product_id: str | None = None
    confidence: float = 0
    reason: str = ""


class Strategy(Protocol):
    name: str
    version: str
    requires_transcript_review: bool

    def generate_signal(self, candles: list[Candle]) -> Signal:
        ...
```

Create `src/trader_app/strategies/price_action_transcript.py`:

```python
from trader_app.strategies.base import Candle, Signal


class PriceActionTranscriptStrategy:
    name = "price_action_transcript"
    version = "0.1.0"
    requires_transcript_review = True

    def generate_signal(self, candles: list[Candle]) -> Signal:
        return Signal(
            action="hold",
            confidence=0,
            reason="Strategy rules require transcript review before signals are enabled.",
        )
```

Create `src/trader_app/strategies/registry.py`:

```python
from trader_app.strategies.base import Strategy
from trader_app.strategies.price_action_transcript import PriceActionTranscriptStrategy


def available_strategies() -> dict[str, type[Strategy]]:
    return {
        "price_action_transcript": PriceActionTranscriptStrategy,
    }


def load_strategies(selection: str) -> list[Strategy]:
    registry = available_strategies()
    names = list(registry.keys()) if selection.strip().upper() == "ALL" else [
        item.strip() for item in selection.split(",") if item.strip()
    ]
    unknown = [name for name in names if name not in registry]
    if unknown:
        raise ValueError(f"Unknown strategies: {', '.join(unknown)}")
    return [registry[name]() for name in names]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_strategies.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/strategies tests/test_strategies.py
git commit -m "feat: add strategy registry"
```

## Task 5: Paper Broker And Trade Persistence

**Files:**
- Modify: `src/trader_app/models.py`
- Create: `src/trader_app/broker/__init__.py`
- Create: `src/trader_app/broker/paper.py`
- Test: `tests/test_paper_broker.py`

- [ ] **Step 1: Write failing broker test**

Create `tests/test_paper_broker.py`:

```python
from trader_app.account import AccountService
from trader_app.broker.paper import PaperBroker
from trader_app.database import create_session_factory, initialize_database


def make_broker(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'broker.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    AccountService(session_factory).get_or_create_account(1000, 0.5)
    return PaperBroker(session_factory)


def test_paper_buy_creates_open_trade(tmp_path):
    broker = make_broker(tmp_path)
    trade = broker.buy(product_id="BTC-USD", quantity=0.01, price=50000, strategy="test")
    assert trade.product_id == "BTC-USD"
    assert trade.status == "open"
    assert trade.entry_value_usd == 500


def test_closing_trade_updates_realized_pnl(tmp_path):
    broker = make_broker(tmp_path)
    opened = broker.buy(product_id="BTC-USD", quantity=0.01, price=50000, strategy="test")
    closed = broker.close_trade(opened.id, exit_price=51000)
    assert closed.status == "closed"
    assert closed.realized_pnl_usd == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_paper_broker.py -v`

Expected: FAIL because broker and trade model do not exist.

- [ ] **Step 3: Implement trade model and broker**

Append to `src/trader_app/models.py`:

```python
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
```

Create `src/trader_app/broker/__init__.py`:

```python
from trader_app.broker.paper import PaperBroker

__all__ = ["PaperBroker"]
```

Create `src/trader_app/broker/paper.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.account import AccountService
from trader_app.models import Account, Trade, utc_now


class PaperBroker:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.account_service = AccountService(session_factory)

    def buy(self, product_id: str, quantity: float, price: float, strategy: str) -> Trade:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            if not account.trading_enabled:
                raise RuntimeError("Trading is disabled by safety lock")
            entry_value = quantity * price
            if entry_value > account.cash_usd:
                raise RuntimeError("Insufficient paper cash")
            account.cash_usd -= entry_value
            trade = Trade(
                product_id=product_id,
                strategy=strategy,
                side="buy",
                status="open",
                quantity=quantity,
                entry_price_usd=price,
                entry_value_usd=entry_value,
                realized_pnl_usd=0,
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade

    def close_trade(self, trade_id: int, exit_price: float) -> Trade:
        with self.session_factory() as session:
            trade = session.get(Trade, trade_id)
            if trade is None:
                raise RuntimeError("Trade not found")
            if trade.status != "open":
                raise RuntimeError("Trade is not open")
            exit_value = trade.quantity * exit_price
            pnl = exit_value - trade.entry_value_usd
            trade.exit_price_usd = exit_price
            trade.realized_pnl_usd = pnl
            trade.status = "closed"
            trade.closed_at = utc_now()
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            account.cash_usd += exit_value
            account.equity_usd = account.cash_usd
            account.realized_pnl_usd += pnl
            threshold = account.initial_cash_usd * account.max_drawdown_fraction
            if account.equity_usd <= threshold:
                account.trading_enabled = False
                account.safety_lock_reason = "equity_at_or_below_50_percent"
            session.commit()
            session.refresh(trade)
            return trade
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_paper_broker.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/models.py src/trader_app/broker tests/test_paper_broker.py
git commit -m "feat: add paper broker trades"
```

## Task 6: Coinbase Sandbox Integration Smoke Client

**Files:**
- Create: `src/trader_app/integrations/__init__.py`
- Create: `src/trader_app/integrations/coinbase.py`
- Test: `tests/test_coinbase_integration.py`

- [ ] **Step 1: Write failing Coinbase client tests**

Create `tests/test_coinbase_integration.py`:

```python
import httpx
import pytest

from trader_app.integrations.coinbase import CoinbaseClient


def test_coinbase_client_uses_sandbox_header():
    client = CoinbaseClient(base_url="https://api.coinbase.com", sandbox=True)
    assert client.headers["X-Sandbox"] == "true"


@pytest.mark.asyncio
async def test_coinbase_smoke_check_parses_status():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"products": [{"product_id": "BTC-USD"}]})

    transport = httpx.MockTransport(handler)
    client = CoinbaseClient(base_url="https://api.coinbase.com", sandbox=True, transport=transport)
    result = await client.smoke_check()
    assert result["ok"] is True
    assert result["product_count"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_coinbase_integration.py -v`

Expected: FAIL because integration module does not exist or async pytest dependency is missing.

- [ ] **Step 3: Add pytest async dependency and implement client**

Add `"pytest-asyncio>=0.24.0"` to `[project.optional-dependencies].dev` in `pyproject.toml`.

Create `src/trader_app/integrations/__init__.py`:

```python
from trader_app.integrations.coinbase import CoinbaseClient

__all__ = ["CoinbaseClient"]
```

Create `src/trader_app/integrations/coinbase.py`:

```python
from typing import Any

import httpx


class CoinbaseClient:
    def __init__(
        self,
        base_url: str,
        sandbox: bool,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Accept": "application/json"}
        if sandbox:
            self.headers["X-Sandbox"] = "true"
        self.transport = transport

    async def smoke_check(self) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            transport=self.transport,
            timeout=10,
        ) as client:
            response = await client.get("/api/v3/brokerage/products")
            response.raise_for_status()
            payload = response.json()
            products = payload.get("products", [])
            return {"ok": True, "product_count": len(products)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pip install -e .[dev]` then `pytest tests/test_coinbase_integration.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add pyproject.toml src/trader_app/integrations tests/test_coinbase_integration.py
git commit -m "feat: add coinbase sandbox smoke client"
```

## Task 7: Bot Heartbeat And Idempotent Startup Command

**Files:**
- Modify: `src/trader_app/models.py`
- Create: `src/trader_app/bot/__init__.py`
- Create: `src/trader_app/bot/runner.py`
- Create: `src/trader_app/cli.py`
- Create: `scripts/start_bot.ps1`
- Test: `tests/test_bot_runner.py`

- [ ] **Step 1: Write failing bot runner tests**

Create `tests/test_bot_runner.py`:

```python
from datetime import timedelta

from trader_app.bot.runner import BotRunner
from trader_app.database import create_session_factory, initialize_database
from trader_app.models import utc_now


def make_runner(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'bot.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    return BotRunner(session_factory, stale_seconds=1800)


def test_first_start_records_running_heartbeat(tmp_path):
    runner = make_runner(tmp_path)
    status = runner.ensure_running(["price_action_transcript"])
    assert status["action"] == "started"
    assert status["status"] == "healthy"


def test_healthy_bot_is_not_started_twice(tmp_path):
    runner = make_runner(tmp_path)
    runner.ensure_running(["price_action_transcript"])
    status = runner.ensure_running(["price_action_transcript"])
    assert status["action"] == "already_running"


def test_stale_bot_is_restarted(tmp_path):
    runner = make_runner(tmp_path)
    runner.ensure_running(["price_action_transcript"])
    runner.mark_heartbeat(utc_now() - timedelta(seconds=1900))
    status = runner.ensure_running(["price_action_transcript"])
    assert status["action"] == "restarted"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_bot_runner.py -v`

Expected: FAIL because bot runner and heartbeat model do not exist.

- [ ] **Step 3: Implement bot heartbeat and CLI**

Append to `src/trader_app/models.py`:

```python
class BotStatus(Base):
    __tablename__ = "bot_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    strategies: Mapped[str] = mapped_column(String, nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
```

Create `src/trader_app/bot/__init__.py`:

```python
from trader_app.bot.runner import BotRunner

__all__ = ["BotRunner"]
```

Create `src/trader_app/bot/runner.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.models import BotStatus


class BotRunner:
    def __init__(self, session_factory: sessionmaker[Session], stale_seconds: int) -> None:
        self.session_factory = session_factory
        self.stale_seconds = stale_seconds

    def ensure_running(self, strategies: list[str]) -> dict[str, str]:
        now = datetime.now(timezone.utc)
        strategy_text = ",".join(strategies)
        with self.session_factory() as session:
            status = session.scalar(select(BotStatus).order_by(BotStatus.id.asc()))
            if status is None:
                status = BotStatus(status="healthy", strategies=strategy_text, last_heartbeat_at=now)
                session.add(status)
                action = "started"
            else:
                age = (now - status.last_heartbeat_at).total_seconds()
                if age <= self.stale_seconds and status.status == "healthy":
                    return {"action": "already_running", "status": status.status}
                status.status = "healthy"
                status.strategies = strategy_text
                status.last_heartbeat_at = now
                action = "restarted"
            session.commit()
            return {"action": action, "status": "healthy"}

    def mark_heartbeat(self, heartbeat_at: datetime) -> None:
        with self.session_factory() as session:
            status = session.scalar(select(BotStatus).order_by(BotStatus.id.asc()))
            if status is None:
                status = BotStatus(status="healthy", strategies="", last_heartbeat_at=heartbeat_at)
                session.add(status)
            else:
                status.last_heartbeat_at = heartbeat_at
            session.commit()
```

Create `src/trader_app/cli.py`:

```python
import argparse

from trader_app.account import AccountService
from trader_app.bot.runner import BotRunner
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.strategies.registry import load_strategies


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start-bot", "reset-safety"])
    parser.add_argument("--strategies", default="ALL")
    args = parser.parse_args()

    settings = Settings()
    engine, session_factory = create_session_factory(settings.database_url)
    initialize_database(engine)
    account_service = AccountService(session_factory)
    account_service.get_or_create_account(settings.bot_starting_cash_usd, settings.bot_max_drawdown_fraction)

    if args.command == "reset-safety":
        account_service.manual_reset_safety_lock()
        print("Safety lock reset")
        return

    strategies = load_strategies(args.strategies)
    runner = BotRunner(session_factory, settings.bot_heartbeat_stale_seconds)
    result = runner.ensure_running([strategy.name for strategy in strategies])
    print(result)
```

Create `scripts/start_bot.ps1`:

```powershell
param(
  [string]$Strategies = "ALL"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
trader start-bot --strategies $Strategies
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_bot_runner.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/models.py src/trader_app/bot src/trader_app/cli.py scripts/start_bot.ps1 tests/test_bot_runner.py
git commit -m "feat: add idempotent bot startup"
```

## Task 8: Backtest Standard Periods

**Files:**
- Create: `src/trader_app/backtests/__init__.py`
- Create: `src/trader_app/backtests/periods.py`
- Test: `tests/test_backtest_periods.py`

- [ ] **Step 1: Write failing period tests**

Create `tests/test_backtest_periods.py`:

```python
from datetime import date

from trader_app.backtests.periods import standard_periods


def test_standard_periods_include_required_windows():
    periods = standard_periods(today=date(2026, 6, 15))
    assert [period.name for period in periods] == ["2024", "2025", "2026", "last_30_days"]
    assert periods[0].start == date(2024, 1, 1)
    assert periods[0].end == date(2024, 12, 31)
    assert periods[3].start == date(2026, 5, 16)
    assert periods[3].starting_cash_usd == 1000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_backtest_periods.py -v`

Expected: FAIL because backtest modules do not exist.

- [ ] **Step 3: Implement standard periods**

Create `src/trader_app/backtests/__init__.py`:

```python
from trader_app.backtests.periods import BacktestPeriod, standard_periods

__all__ = ["BacktestPeriod", "standard_periods"]
```

Create `src/trader_app/backtests/periods.py`:

```python
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class BacktestPeriod:
    name: str
    start: date
    end: date
    starting_cash_usd: float = 1000


def standard_periods(today: date | None = None) -> list[BacktestPeriod]:
    current = today or date.today()
    return [
        BacktestPeriod("2024", date(2024, 1, 1), date(2024, 12, 31)),
        BacktestPeriod("2025", date(2025, 1, 1), date(2025, 12, 31)),
        BacktestPeriod("2026", date(2026, 1, 1), min(current, date(2026, 12, 31))),
        BacktestPeriod("last_30_days", current - timedelta(days=30), current),
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_backtest_periods.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/backtests tests/test_backtest_periods.py
git commit -m "feat: add standard backtest periods"
```

## Task 9: FastAPI Dashboard API

**Files:**
- Create: `src/trader_app/api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from trader_app.api import create_app
from trader_app.database import create_session_factory, initialize_database


def make_client(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'api.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    return TestClient(create_app(session_factory=session_factory))


def test_health_endpoint(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_summary_shape(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["account"]["initial_cash_usd"] == 1000
    assert payload["bot"]["status"] in ["not_started", "healthy"]
    assert payload["trades"]["open"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`

Expected: FAIL because API module does not exist.

- [ ] **Step 3: Implement API factory**

Create `src/trader_app/api.py`:

```python
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.account import AccountService
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.models import BotStatus, Trade


def create_app(session_factory: sessionmaker[Session] | None = None) -> FastAPI:
    settings = Settings()
    if session_factory is None:
        engine, session_factory = create_session_factory(settings.database_url)
        initialize_database(engine)

    account_service = AccountService(session_factory)
    app = FastAPI(title="Coinbase Day Trader API", version="0.1.0")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/dashboard/summary")
    def dashboard_summary() -> dict[str, object]:
        account = account_service.get_or_create_account(1000, 0.5)
        with session_factory() as session:
            bot = session.scalar(select(BotStatus).order_by(BotStatus.id.asc()))
            open_trades = session.scalars(select(Trade).where(Trade.status == "open")).all()
            closed_trades = session.scalars(select(Trade).where(Trade.status == "closed")).all()
        return {
            "account": {
                "initial_cash_usd": account.initial_cash_usd,
                "cash_usd": account.cash_usd,
                "equity_usd": account.equity_usd,
                "realized_pnl_usd": account.realized_pnl_usd,
                "trading_enabled": account.trading_enabled,
                "safety_lock_reason": account.safety_lock_reason,
            },
            "bot": {
                "status": bot.status if bot else "not_started",
                "strategies": bot.strategies.split(",") if bot and bot.strategies else [],
            },
            "trades": {
                "open": [_trade_to_dict(trade) for trade in open_trades],
                "closed": [_trade_to_dict(trade) for trade in closed_trades],
            },
        }

    return app


def _trade_to_dict(trade: Trade) -> dict[str, object]:
    return {
        "id": trade.id,
        "product_id": trade.product_id,
        "strategy": trade.strategy,
        "status": trade.status,
        "quantity": trade.quantity,
        "entry_price_usd": trade.entry_price_usd,
        "realized_pnl_usd": trade.realized_pnl_usd,
    }


app = create_app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/api.py tests/test_api.py
git commit -m "feat: add dashboard api"
```

## Task 10: Dashboard Shell

**Files:**
- Create: `dashboard/package.json`
- Create: `dashboard/index.html`
- Create: `dashboard/src/main.tsx`
- Create: `dashboard/src/api.ts`
- Create: `dashboard/src/App.tsx`
- Create: `dashboard/src/App.css`
- Create: `dashboard/src/App.test.tsx`
- Create: `scripts/start_dashboard.ps1`

- [ ] **Step 1: Write failing dashboard test**

Create `dashboard/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the live trading dashboard shell", () => {
    render(<App />);
    expect(screen.getByText("Live Trading")).toBeTruthy();
    expect(screen.getByText("Trading History")).toBeTruthy();
    expect(screen.getByText("Account Management")).toBeTruthy();
    expect(screen.getByText("Backtests")).toBeTruthy();
    expect(screen.getByText("Strategies")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix dashboard test -- --run`

Expected: FAIL because dashboard project files do not exist.

- [ ] **Step 3: Implement dashboard shell**

Create `dashboard/package.json`:

```json
{
  "name": "coinbase-day-trader-dashboard",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5173",
    "build": "tsc && vite build",
    "test": "vitest"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.2",
    "typescript": "^5.5.4",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.1",
    "@testing-library/jest-dom": "^6.4.8",
    "@types/react": "^18.3.4",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^24.1.1",
    "vitest": "^2.0.5"
  }
}
```

Create `dashboard/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Coinbase Day Trader</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `dashboard/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `dashboard/src/api.ts`:

```ts
export type DashboardSummary = {
  account: {
    initial_cash_usd: number;
    cash_usd: number;
    equity_usd: number;
    realized_pnl_usd: number;
    trading_enabled: boolean;
    safety_lock_reason: string;
  };
  bot: {
    status: string;
    strategies: string[];
  };
  trades: {
    open: unknown[];
    closed: unknown[];
  };
};

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch("/api/dashboard/summary");
  if (!response.ok) {
    throw new Error("Dashboard summary request failed");
  }
  return response.json();
}
```

Create `dashboard/src/App.tsx`:

```tsx
import { Activity, BarChart3, BookOpen, History, Landmark } from "lucide-react";

const navItems = [
  ["Live Trading", Activity],
  ["Trading History", History],
  ["Account Management", Landmark],
  ["Backtests", BarChart3],
  ["Strategies", BookOpen],
] as const;

export default function App() {
  return (
    <main className="appShell">
      <aside className="sidebar">
        <div className="brand">Coinbase Day Trader</div>
        <nav>
          {navItems.map(([label, Icon]) => (
            <button className="navButton" key={label} type="button" title={label}>
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Paper trading</p>
            <h1>Live Trading</h1>
          </div>
          <span className="statusPill">Local mode</span>
        </header>
        <section className="metricGrid" aria-label="Trading metrics">
          <article><span>Equity</span><strong>$1,000.00</strong></article>
          <article><span>Cash</span><strong>$1,000.00</strong></article>
          <article><span>PnL</span><strong>$0.00</strong></article>
          <article><span>Win Rate</span><strong>0%</strong></article>
        </section>
        <section className="tableSurface">
          <h2>Open Trades</h2>
          <p>No open trades.</p>
        </section>
      </section>
    </main>
  );
}
```

Create `dashboard/src/App.css`:

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Inter, Segoe UI, Arial, sans-serif;
  background: #f4f2ed;
  color: #17201b;
}

.appShell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px 1fr;
}

.sidebar {
  background: #13231d;
  color: white;
  padding: 24px 16px;
}

.brand {
  font-weight: 700;
  margin-bottom: 28px;
}

.navButton {
  width: 100%;
  height: 42px;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 0;
  border-radius: 6px;
  margin-bottom: 8px;
  padding: 0 12px;
  color: white;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.navButton:hover {
  background: #244236;
}

.workspace {
  padding: 28px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 4px;
  color: #5d6c64;
  font-size: 13px;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: 30px;
}

.statusPill {
  border: 1px solid #a9c9b6;
  border-radius: 999px;
  padding: 8px 12px;
  background: #e8f4ed;
}

.metricGrid {
  display: grid;
  grid-template-columns: repeat(4, minmax(140px, 1fr));
  gap: 14px;
}

.metricGrid article,
.tableSurface {
  background: white;
  border: 1px solid #d8ddd7;
  border-radius: 8px;
  padding: 18px;
}

.metricGrid span {
  display: block;
  color: #5d6c64;
  margin-bottom: 10px;
}

.metricGrid strong {
  font-size: 24px;
}

.tableSurface {
  margin-top: 18px;
}
```

Create `scripts/start_dashboard.ps1`:

```powershell
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "uvicorn trader_app.api:app --host 127.0.0.1 --port 8000"
npm --prefix dashboard run dev
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix dashboard install` then `npm --prefix dashboard test -- --run`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add dashboard scripts/start_dashboard.ps1
git commit -m "feat: add dashboard shell"
```

## Task 11: Logging Configuration

**Files:**
- Create: `src/trader_app/logging_config.py`
- Test: `tests/test_logging_config.py`

- [ ] **Step 1: Write failing logging test**

Create `tests/test_logging_config.py`:

```python
import logging

from trader_app.logging_config import configure_daily_logger


def test_configure_daily_logger_creates_log_file(tmp_path):
    logger = configure_daily_logger("bot", tmp_path)
    logger.info("hello")
    for handler in logger.handlers:
        handler.flush()
    assert (tmp_path / "bot.log").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_logging_config.py -v`

Expected: FAIL because logging config module does not exist.

- [ ] **Step 3: Implement daily logger**

Create `src/trader_app/logging_config.py`:

```python
import gzip
import logging
import shutil
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class CompressingTimedRotatingFileHandler(TimedRotatingFileHandler):
    def rotate(self, source: str, dest: str) -> None:
        super().rotate(source, dest)
        source_path = Path(dest)
        gzip_path = source_path.with_suffix(source_path.suffix + ".gz")
        with source_path.open("rb") as src, gzip_path.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb") as gz:
                shutil.copyfileobj(src, gz)
        source_path.unlink(missing_ok=True)


def configure_daily_logger(name: str, log_dir: str | Path = "logs") -> logging.Logger:
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = CompressingTimedRotatingFileHandler(
        path / f"{name}.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_logging_config.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/trader_app/logging_config.py tests/test_logging_config.py
git commit -m "feat: add rotating log configuration"
```

## Task 12: Final Verification, Version Tag, And GitHub Prep

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Run full backend test suite**

Run: `pytest -v`

Expected: all Python tests PASS.

- [ ] **Step 2: Run dashboard tests**

Run: `npm --prefix dashboard test -- --run`

Expected: all dashboard tests PASS.

- [ ] **Step 3: Verify secret safety**

Run: `git status --short --ignored`

Expected: `.env` appears ignored if present, and no secret files are staged.

- [ ] **Step 4: Update README and changelog with verified commands**

Update `README.md` test/setup sections to include the exact commands that passed:

```markdown
## Verification

Backend:

```powershell
pytest -v
```

Dashboard:

```powershell
npm --prefix dashboard test -- --run
```
```

Update `CHANGELOG.md` under `0.1.0`:

```markdown
- Added typed configuration with live-trading fail-closed behavior.
- Added SQLite paper account, safety lock, strategy registry, paper broker, Coinbase sandbox smoke client, bot heartbeat, standard backtest periods, FastAPI dashboard API, dashboard shell, and rotating logs.
```

- [ ] **Step 5: Commit final docs**

Run:

```bash
git add README.md CHANGELOG.md
git commit -m "docs: update v0.1.0 usage"
```

- [ ] **Step 6: Create version tag**

Run this PowerShell command:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
git tag "v0.1.0-$stamp-CT"
```

Expected: a tag like `v0.1.0-20260615-143000-CT`.

- [ ] **Step 7: Prepare GitHub repository**

Run:

```powershell
gh auth status
```

If authenticated, run:

```powershell
gh repo create castoldi/coinbase-day-trader-v1 --public --source . --remote origin --push
git push origin --tags
```

If not authenticated, stop and report that GitHub CLI authentication is required before creating and pushing the public repository.

## Self-Review

- Spec coverage: project metadata, `.env.example`, secret safety, paper-first mode, Coinbase sandbox smoke integration, bot idempotent startup, multiple strategy selection, account rollover and safety lock, dashboard pages shell, backtest periods, logs, README, changelog, AGENTS, version tag, and GitHub prep are covered.
- Deferred by design: live trading and complete price-action rules remain blocked until future explicit approval and transcript review.
- Completion-marker scan: this plan contains concrete implementation steps and the transcript-gated strategy has explicit hold behavior.
- Type consistency: `Settings`, `AccountService`, `PaperBroker`, `BotRunner`, `CoinbaseClient`, and `BacktestPeriod` names are introduced before use and remain consistent.
