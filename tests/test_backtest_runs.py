from datetime import date, datetime, timedelta, timezone

from trader_app.backtests.service import BacktestService, CandlePoint
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.strategies.ema_ribbon_reversal import EmaRibbonReversalStrategy


def make_service(tmp_path, candle_loader, strategies=None):
    db_url = f"sqlite:///{tmp_path / 'backtests.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    settings = Settings(_env_file=None)
    return BacktestService(
        session_factory, settings, candle_loader=candle_loader, strategies=strategies
    )


def reversal_closes() -> list[float]:
    closes: list[float] = []
    closes += [100 - i for i in range(40)]  # downtrend
    closes += [62 + 4 * i for i in range(25)]  # sharp reversal up
    closes += [158 - 5 * i for i in range(6)]  # pullback into ribbon
    closes += [150, 160, 170, 180]  # reclaim and continuation
    return closes


def reversal_candles(start: date) -> list[CandlePoint]:
    points: list[CandlePoint] = []
    for index, close in enumerate(reversal_closes()):
        timestamp = datetime(start.year, start.month, start.day, tzinfo=timezone.utc) + timedelta(days=index)
        points.append(
            CandlePoint(start=timestamp, low=close - 2, high=close + 2, open=close, close=close, volume=1000)
        )
    return points


def small_strategy():
    return EmaRibbonReversalStrategy(white_len=3, channel_len=8, trend_len=13, pullback_window=6)


def test_run_standard_backtests_records_required_periods(tmp_path):
    candles = reversal_candles(date(2024, 1, 1))

    def candle_loader(product_id, start_date, end_date):
        return [point for point in candles if start_date <= point.start.date() <= end_date]

    service = make_service(tmp_path, candle_loader, strategies=[small_strategy()])
    runs = service.run_standard_backtests(today=date(2026, 6, 15))

    assert [run.period_name for run in runs] == ["2024", "2025", "2026", "last_30_days"]


def test_backtest_executes_trades_when_strategy_signals(tmp_path):
    candles = reversal_candles(date(2024, 1, 1))

    def candle_loader(product_id, start_date, end_date):
        return [point for point in candles if start_date <= point.start.date() <= end_date]

    service = make_service(tmp_path, candle_loader, strategies=[small_strategy()])
    runs = service.run_standard_backtests(today=date(2026, 6, 15))

    run_2024 = next(run for run in runs if run.period_name == "2024")
    assert run_2024.trade_count >= 1
    assert run_2024.starting_cash_usd == 1000
    assert 0 <= run_2024.win_rate_pct <= 100


def test_period_without_data_stays_flat(tmp_path):
    candles = reversal_candles(date(2024, 1, 1))

    def candle_loader(product_id, start_date, end_date):
        return [point for point in candles if start_date <= point.start.date() <= end_date]

    service = make_service(tmp_path, candle_loader, strategies=[small_strategy()])
    runs = service.run_standard_backtests(today=date(2026, 6, 15))

    run_2025 = next(run for run in runs if run.period_name == "2025")
    assert run_2025.trade_count == 0
    assert run_2025.ending_equity_usd == 1000


def test_backtests_summary_reports_saved_runs(tmp_path):
    candles = reversal_candles(date(2024, 1, 1))

    def candle_loader(product_id, start_date, end_date):
        return [point for point in candles if start_date <= point.start.date() <= end_date]

    service = make_service(tmp_path, candle_loader, strategies=[small_strategy()])
    service.run_standard_backtests(today=date(2026, 6, 15))
    summary = service.get_backtests_summary()

    assert summary["total_runs"] == 4
    assert summary["periods"] == ["2024", "2025", "2026", "last_30_days"]
    assert summary["runs"][0]["strategy_name"] == "ema_ribbon_reversal"
