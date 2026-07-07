from datetime import date, datetime, timedelta, timezone

from trader_app.backtests.service import BacktestService, CandlePoint
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.strategies.stochastic_swing import StochasticSwingStrategy


def make_service(tmp_path, candle_loader, strategies):
    db_url = f"sqlite:///{tmp_path / 'stoch.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    settings = Settings(_env_file=None, default_products="BTC-USD")
    return BacktestService(
        session_factory, settings, candle_loader=candle_loader, strategies=strategies, granularity="ONE_DAY"
    )


def oscillating_points(start: date, cycles: int) -> list[CandlePoint]:
    points: list[CandlePoint] = []
    base = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    index = 0

    def add(close: float, high: float, low: float) -> None:
        nonlocal index
        points.append(
            CandlePoint(start=base + timedelta(days=index), low=low, high=high, open=close, close=close, volume=1000)
        )
        index += 1

    for _ in range(cycles):
        for _ in range(5):
            add(100, 101, 99)  # range
        add(95.1, 100, 95)  # oversold dip -> %K below 5 -> buy at 95.1, target ~97.95
        add(99, 100, 98)  # recovery touches target -> exit
        for _ in range(3):
            add(100, 101, 99)  # back to range
    return points


def test_stochastic_strategy_round_trips_multiple_trades(tmp_path):
    points = oscillating_points(date(2024, 1, 1), cycles=15)

    def candle_loader(product_id, start_date, end_date):
        return [point for point in points if start_date <= point.start.date() <= end_date]

    strategy = StochasticSwingStrategy(stoch_period=5, stoch_level=5, highest_period=5, target_pct=3.0)
    service = make_service(tmp_path, candle_loader, strategies=[strategy])
    runs = service.run_standard_backtests(today=date(2026, 6, 15))

    run_2024 = next(run for run in runs if run.period_name == "2024")
    # Many oversold dips, each opened and closed mid-series (not just a forced
    # close at period end), so the trade count is well above one.
    assert run_2024.trade_count >= 5
    assert run_2024.win_rate_pct > 0
