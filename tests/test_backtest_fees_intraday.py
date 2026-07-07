from datetime import date, datetime, timedelta, timezone

import pytest

from trader_app.backtests.service import BacktestService, CandlePoint
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.strategies.base import Signal


class BuyBelowStrategy:
    """Test strategy: buy once when price is below a threshold, take +10%."""

    name = "buy_below"
    version = "1.0.0"
    requires_transcript_review = False

    def __init__(self, threshold: float = 105.0, target_pct: float = 10.0) -> None:
        self.threshold = threshold
        self.target_pct = target_pct

    def generate_signal(self, candles):
        last = candles[-1]
        if last.close < self.threshold:
            return Signal(
                action="buy",
                product_id=last.product_id,
                entry_price=last.close,
                take_profit=last.close * (1 + self.target_pct / 100),
            )
        return Signal(action="hold", product_id=last.product_id)


class BuyWhenFlatStrategy:
    """Test strategy: always buy when flat with a small +1% target."""

    name = "buy_when_flat"
    version = "1.0.0"
    requires_transcript_review = False

    def generate_signal(self, candles):
        last = candles[-1]
        return Signal(
            action="buy",
            product_id=last.product_id,
            entry_price=last.close,
            take_profit=last.close * 1.01,
        )


def make_service(tmp_path, candle_loader, strategies, fee_rate=None, granularity="ONE_DAY", db_name="fees.sqlite3"):
    db_url = f"sqlite:///{tmp_path / db_name}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    settings = Settings(_env_file=None, default_products="BTC-USD")
    return BacktestService(
        session_factory,
        settings,
        candle_loader=candle_loader,
        strategies=strategies,
        fee_rate=fee_rate,
        granularity=granularity,
    )


def single_trade_loader():
    base = datetime(2024, 3, 1, tzinfo=timezone.utc)
    points = [
        CandlePoint(start=base, low=99, high=101, open=100, close=100, volume=1000),
        CandlePoint(start=base + timedelta(days=1), low=109, high=115, open=110, close=112, volume=1000),
    ]

    def candle_loader(product_id, start_date, end_date):
        return [p for p in points if start_date <= p.start.date() <= end_date]

    return candle_loader


def run_2024(runs):
    return next(run for run in runs if run.period_name == "2024")


def test_fees_reduce_returns(tmp_path):
    # One round trip: buy at 100, exit at the 110 take-profit.
    no_fee = make_service(tmp_path, single_trade_loader(), [BuyBelowStrategy()], fee_rate=0.0, db_name="a.sqlite3")
    with_fee = make_service(tmp_path, single_trade_loader(), [BuyBelowStrategy()], fee_rate=0.01, db_name="b.sqlite3")

    no_fee_run = run_2024(no_fee.run_standard_backtests(today=date(2026, 6, 15)))
    fee_run = run_2024(with_fee.run_standard_backtests(today=date(2026, 6, 15)))

    assert no_fee_run.trade_count == 1
    assert fee_run.trade_count == 1
    # Gross round trip is +10%; a 1% per-side fee eats ~2% of it.
    assert no_fee_run.total_return_pct == pytest.approx(10.0, rel=1e-6)
    assert fee_run.total_return_pct < no_fee_run.total_return_pct
    assert 7.0 < fee_run.total_return_pct < 8.5


def test_fees_can_flip_a_marginal_win_to_a_loss(tmp_path):
    # A +1% gross target is wiped out by a 1% per-side (2% round-trip) fee.
    no_fee = make_service(tmp_path, single_trade_loader(), [BuyBelowStrategy(target_pct=1.0)], fee_rate=0.0, db_name="a.sqlite3")
    with_fee = make_service(tmp_path, single_trade_loader(), [BuyBelowStrategy(target_pct=1.0)], fee_rate=0.01, db_name="b.sqlite3")

    assert run_2024(no_fee.run_standard_backtests(today=date(2026, 6, 15))).total_return_pct > 0
    assert run_2024(with_fee.run_standard_backtests(today=date(2026, 6, 15))).total_return_pct < 0


def test_intraday_bars_produce_many_trades_in_one_day(tmp_path):
    # 12 rising bars on a single calendar day inside the recent window. Per-bar
    # simulation must trade each bar; the old per-calendar-day logic would have
    # collapsed to one bar (at most one trade that day).
    trading_day = date(2026, 6, 14)
    base = datetime(trading_day.year, trading_day.month, trading_day.day, tzinfo=timezone.utc)
    points = []
    price = 100.0
    for i in range(12):
        price *= 1.02
        points.append(
            CandlePoint(
                start=base + timedelta(hours=i),
                low=price * 0.999,
                high=price * 1.02,
                open=price,
                close=price,
                volume=1000,
            )
        )

    def candle_loader(product_id, start_date, end_date):
        return [p for p in points if start_date <= p.start.date() <= end_date]

    # ONE_HOUR sweeps recent windows; "last_7_days" covers the trading day.
    service = make_service(
        tmp_path, candle_loader, [BuyWhenFlatStrategy()], fee_rate=0.0, granularity="ONE_HOUR"
    )
    runs = service.run_standard_backtests(today=date(2026, 6, 15))
    run = next(r for r in runs if r.period_name == "last_7_days")
    assert run.granularity == "ONE_HOUR"
    assert run.trade_count >= 5
    assert {p.start.date() for p in points} == {trading_day}
