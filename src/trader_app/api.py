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
