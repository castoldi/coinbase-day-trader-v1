from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class BacktestPeriod:
    name: str
    start: date
    end: date
    starting_cash_usd: float = 1000


# Recent-window lengths (in days) to backtest per granularity. Daily candles
# use calendar-year windows; intraday granularities use shorter rolling windows
# so the candle volume stays manageable and stays relevant to day trading.
RECENT_WINDOW_DAYS: dict[str, list[int]] = {
    "SIX_HOUR": [180, 90, 30],
    "ONE_HOUR": [90, 30, 7],
    "FIFTEEN_MINUTE": [60, 14, 7],
    "FIVE_MINUTE": [30, 7, 3],
    "ONE_MINUTE": [7, 3, 1],
}


def _daily_periods(current: date) -> list[BacktestPeriod]:
    return [
        BacktestPeriod("2024", date(2024, 1, 1), date(2024, 12, 31)),
        BacktestPeriod("2025", date(2025, 1, 1), date(2025, 12, 31)),
        BacktestPeriod("2026", date(2026, 1, 1), min(current, date(2026, 12, 31))),
        BacktestPeriod("last_30_days", current - timedelta(days=30), current),
    ]


def standard_periods(
    granularity: str = "ONE_DAY", today: date | None = None
) -> list[BacktestPeriod]:
    current = today or date.today()
    if granularity == "ONE_DAY":
        return _daily_periods(current)
    windows = RECENT_WINDOW_DAYS.get(granularity)
    if windows is None:
        # Unknown intraday granularity: fall back to a single recent week.
        windows = [7]
    return [
        BacktestPeriod(f"last_{days}_days", current - timedelta(days=days), current)
        for days in windows
    ]
