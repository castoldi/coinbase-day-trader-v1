import pytest
from sqlalchemy import select

from trader_app.account import AccountService
from trader_app.bot.engine import TradingEngine
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.models import Account, Trade
from trader_app.strategies.base import Candle
from trader_app.strategies.ema_ribbon_reversal import EmaRibbonReversalStrategy


def reversal_candles() -> list[Candle]:
    closes: list[float] = []
    closes += [100 - i for i in range(40)]
    closes += [62 + 4 * i for i in range(25)]
    closes += [158 - 5 * i for i in range(6)]
    closes += [150, 160, 170, 180]
    return [
        Candle(
            product_id="BTC-USD",
            timestamp=f"2024-{(i % 12) + 1:02d}-01T00:00:00+00:00",
            open=close,
            high=close + 2,
            low=close - 2,
            close=close,
            volume=1000,
        )
        for i, close in enumerate(closes)
    ]


def small_strategy() -> EmaRibbonReversalStrategy:
    return EmaRibbonReversalStrategy(white_len=3, channel_len=8, trend_len=13, pullback_window=6)


def buy_prefix(strategy: EmaRibbonReversalStrategy) -> list[Candle]:
    candles = reversal_candles()
    for i in range(len(candles)):
        if strategy.generate_signal(candles[: i + 1]).action == "buy":
            return candles[: i + 1]
    raise AssertionError("expected a buy signal in the reversal series")


def make_engine(tmp_path, candle_loader, strategies, notifier=None, **settings_overrides):
    db_url = f"sqlite:///{tmp_path / 'engine.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    settings = Settings(_env_file=None, default_products="BTC-USD", **settings_overrides)
    AccountService(session_factory).get_or_create_account(1000, 0.5)
    return session_factory, TradingEngine(
        session_factory, settings, candle_loader=candle_loader, strategies=strategies, notifier=notifier
    )


def test_buy_signal_opens_paper_trade(tmp_path):
    strategy = small_strategy()
    prefix = buy_prefix(strategy)
    session_factory, engine = make_engine(tmp_path, lambda product_id: prefix, [strategy])

    result = engine.run_cycle()

    assert result["opened"] == 1
    with session_factory() as session:
        trades = session.scalars(select(Trade).where(Trade.status == "open")).all()
    assert len(trades) == 1
    assert trades[0].stop_loss_usd is not None
    assert trades[0].take_profit_usd is not None


def test_buy_signal_sizes_paper_trade_to_include_fees(tmp_path):
    strategy = small_strategy()
    prefix = buy_prefix(strategy)
    session_factory, engine = make_engine(
        tmp_path, lambda product_id: prefix, [strategy], backtest_fee_rate=0.01
    )

    engine.run_cycle()

    with session_factory() as session:
        trade = session.scalars(select(Trade).where(Trade.status == "open")).one()
        account = session.scalars(select(Account)).one()
    assert trade.entry_fee_usd == pytest.approx(trade.entry_value_usd * 0.01)
    assert trade.entry_value_usd + trade.entry_fee_usd == pytest.approx(1000)
    assert account.cash_usd == pytest.approx(0)


def test_take_profit_closes_open_trade(tmp_path):
    strategy = small_strategy()
    prefix = buy_prefix(strategy)
    session_factory, engine = make_engine(tmp_path, lambda product_id: prefix, [strategy])
    engine.run_cycle()

    with session_factory() as session:
        trade = session.scalars(select(Trade).where(Trade.status == "open")).one()
        take_profit = trade.take_profit_usd

    spike = Candle(
        product_id="BTC-USD",
        timestamp="2025-01-01T00:00:00+00:00",
        open=take_profit + 10,
        high=take_profit + 20,
        low=take_profit + 5,
        close=take_profit + 10,
        volume=1000,
    )
    engine.candle_loader = lambda product_id: [*prefix, spike]

    result = engine.run_cycle()
    assert result["closed"] == 1


def test_locked_account_does_not_trade(tmp_path):
    strategy = small_strategy()
    prefix = buy_prefix(strategy)
    session_factory, engine = make_engine(tmp_path, lambda product_id: prefix, [strategy])
    AccountService(session_factory).apply_realized_pnl(-600)  # trips the 50% lock

    result = engine.run_cycle()

    assert result["status"] == "locked"
    assert result["opened"] == 0


def test_notifier_called_on_open(tmp_path):
    strategy = small_strategy()
    prefix = buy_prefix(strategy)
    messages: list[tuple[str, str]] = []

    class FakeNotifier:
        def send(self, subject: str, body: str) -> bool:
            messages.append((subject, body))
            return True

    _, engine = make_engine(tmp_path, lambda product_id: prefix, [strategy], notifier=FakeNotifier())
    engine.run_cycle()

    assert any("opened" in subject.lower() for subject, _ in messages)
