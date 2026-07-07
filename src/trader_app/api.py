import json
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.account import AccountService
from trader_app.backtests.service import BacktestService
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.models import BotStatus, Trade
from trader_app.strategies.catalog import strategy_catalog


def _cached_prices(products: list[str]) -> dict[str, float]:
    """Read the latest close from cached market data; returns what is available."""
    prices: dict[str, float] = {}
    market_dir = Path("data/market")
    for product_id in products:
        cache_path = market_dir / f"{product_id}-ONE_DAY.json"
        if not cache_path.exists():
            continue
        try:
            candles = json.loads(cache_path.read_text(encoding="utf-8")).get("candles", [])
        except (ValueError, OSError):
            continue
        if candles:
            prices[product_id] = float(candles[-1]["close"])
    return prices


def create_app(
    session_factory: sessionmaker[Session] | None = None,
    price_loader: Callable[[list[str]], dict[str, float]] | None = None,
) -> FastAPI:
    settings = Settings()
    if session_factory is None:
        engine, session_factory = create_session_factory(settings.database_url)
        initialize_database(engine)

    account_service = AccountService(session_factory)
    backtest_service = BacktestService(session_factory, settings)
    load_prices = price_loader or _cached_prices
    app = FastAPI(title="Coinbase Day Trader API", version="0.6.1")

    @app.middleware("http")
    async def no_store(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/dashboard/summary")
    def dashboard_summary() -> dict[str, object]:
        account = account_service.get_or_create_account(1000, 0.5)
        products = settings.products
        prices = load_prices(products)
        with session_factory() as session:
            bot = session.scalar(select(BotStatus).order_by(BotStatus.id.asc()))
            open_trades = session.scalars(select(Trade).where(Trade.status == "open")).all()
            closed_trades = session.scalars(
                select(Trade).where(Trade.status == "closed").order_by(Trade.closed_at.desc())
            ).all()
        closed_list = [_trade_to_dict(trade) for trade in closed_trades]
        wins = sum(1 for trade in closed_trades if trade.realized_pnl_usd > 0)
        win_rate = (wins / len(closed_trades) * 100) if closed_trades else 0.0
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
            "metrics": {
                "win_rate_pct": round(win_rate, 1),
                "closed_count": len(closed_trades),
                "open_count": len(open_trades),
            },
            "prices": [
                {"product_id": product_id, "price_usd": prices.get(product_id)}
                for product_id in products
            ],
            "trades": {
                "open": [_trade_to_dict(trade) for trade in open_trades],
                "closed": closed_list,
            },
        }

    @app.get("/api/backtests/summary")
    def backtests_summary() -> dict[str, object]:
        return backtest_service.get_backtests_summary()

    @app.get("/api/strategies")
    def strategies() -> dict[str, object]:
        return {"strategies": strategy_catalog()}

    return app


def _trade_to_dict(trade: Trade) -> dict[str, object]:
    return {
        "id": trade.id,
        "product_id": trade.product_id,
        "strategy": trade.strategy,
        "status": trade.status,
        "quantity": trade.quantity,
        "entry_price_usd": trade.entry_price_usd,
        "entry_value_usd": trade.entry_value_usd,
        "stop_loss_usd": trade.stop_loss_usd,
        "take_profit_usd": trade.take_profit_usd,
        "exit_price_usd": trade.exit_price_usd,
        "realized_pnl_usd": trade.realized_pnl_usd,
        "opened_at": trade.opened_at.isoformat() if trade.opened_at else None,
        "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
    }


app = create_app()
