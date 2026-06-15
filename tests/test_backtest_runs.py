from datetime import date, datetime, timedelta, timezone

from trader_app.backtests.service import BacktestService, CandlePoint
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.strategies.ema_ribbon_reversal import EmaRibbonReversalStrategy


def make_service(tmp_path, candle_loader, strategies=None):
    db_url = f"sqlite:///{tmp_path / 'backtests.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    settings = Settings(_env_file=None)  # default products: BTC-USD, ETH-USD, SOL-USD
    return BacktestService(
        session_factory, settings, candle_loader=candle_loader, strategies=strategies
    )


def reversal_closes() -> list[float]:
    closes: list[float] = []
    closes += [100 - i for i in range(40)]
    closes += [62 + 4 * i for i in range(25)]
    closes += [158 - 5 * i for i in range(6)]
    closes += [150, 160, 170, 180]
    return closes


def candles_for(closes: list[float], start: date) -> list[CandlePoint]:
    base = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    return [
        CandlePoint(start=base + timedelta(days=i), low=c - 2, high=c + 2, open=c, close=c, volume=1000)
        for i, c in enumerate(closes)
    ]


def small_strategy():
    return EmaRibbonReversalStrategy(white_len=3, channel_len=8, trend_len=13, pullback_window=6)


def loader_with_signals_only_on_btc():
    btc = candles_for(reversal_closes(), date(2024, 1, 1))
    flat = candles_for([100.0] * len(reversal_closes()), date(2024, 1, 1))  # no signals

    def candle_loader(product_id, start_date, end_date):
        points = btc if product_id == "BTC-USD" else flat
        return [p for p in points if start_date <= p.start.date() <= end_date]

    return candle_loader


def runs_by(runs, period, product):
    return next(r for r in runs if r.period_name == period and r.product_id == product)


def test_one_run_per_period_and_coin(tmp_path):
    service = make_service(tmp_path, loader_with_signals_only_on_btc(), strategies=[small_strategy()])
    runs = service.run_standard_backtests(today=date(2026, 6, 15))

    # 4 periods x 3 coins
    assert len(runs) == 12
    assert {r.period_name for r in runs} == {"2024", "2025", "2026", "last_30_days"}
    assert {r.product_id for r in runs} == {"BTC-USD", "ETH-USD", "SOL-USD"}
    assert all(r.starting_cash_usd == 1000 for r in runs)


def test_results_differ_per_coin(tmp_path):
    service = make_service(tmp_path, loader_with_signals_only_on_btc(), strategies=[small_strategy()])
    runs = service.run_standard_backtests(today=date(2026, 6, 15))

    assert runs_by(runs, "2024", "BTC-USD").trade_count >= 1
    assert runs_by(runs, "2024", "ETH-USD").trade_count == 0
    assert runs_by(runs, "2024", "SOL-USD").trade_count == 0


def test_summary_exposes_product_id(tmp_path):
    service = make_service(tmp_path, loader_with_signals_only_on_btc(), strategies=[small_strategy()])
    service.run_standard_backtests(today=date(2026, 6, 15))
    summary = service.get_backtests_summary()

    assert summary["total_runs"] == 12
    assert all("product_id" in run for run in summary["runs"])
    assert summary["runs"][0]["strategy_name"] == "ema_ribbon_reversal"
