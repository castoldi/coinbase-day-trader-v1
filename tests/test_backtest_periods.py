from datetime import date

from trader_app.backtests.periods import standard_periods


def test_standard_periods_include_required_windows():
    periods = standard_periods(today=date(2026, 6, 15))
    assert [period.name for period in periods] == ["2024", "2025", "2026", "last_30_days"]
    assert periods[0].start == date(2024, 1, 1)
    assert periods[0].end == date(2024, 12, 31)
    assert periods[3].start == date(2026, 5, 16)
    assert periods[3].starting_cash_usd == 1000


def test_daily_is_the_default_granularity():
    assert standard_periods(today=date(2026, 6, 15)) == standard_periods("ONE_DAY", date(2026, 6, 15))


def test_intraday_granularities_use_recent_windows():
    periods = standard_periods("FIVE_MINUTE", today=date(2026, 6, 15))
    assert [period.name for period in periods] == ["last_30_days", "last_7_days", "last_3_days"]
    assert periods[0].start == date(2026, 5, 16)
    assert periods[-1].start == date(2026, 6, 12)
    assert all(period.end == date(2026, 6, 15) for period in periods)


def test_unknown_intraday_granularity_falls_back_to_one_week():
    periods = standard_periods("THIRTY_MINUTE", today=date(2026, 6, 15))
    assert [period.name for period in periods] == ["last_7_days"]
