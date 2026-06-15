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
