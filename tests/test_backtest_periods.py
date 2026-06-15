from datetime import date

from trader_app.backtests.periods import standard_periods


def test_standard_periods_include_required_windows():
    periods = standard_periods(today=date(2026, 6, 15))
    assert [period.name for period in periods] == ["2024", "2025", "2026", "last_30_days"]
    assert periods[0].start == date(2024, 1, 1)
    assert periods[0].end == date(2024, 12, 31)
    assert periods[3].start == date(2026, 5, 16)
    assert periods[3].starting_cash_usd == 1000
