import pytest

from trader_app.config import Settings, TradingMode


def test_defaults_are_safe_for_paper_trading():
    settings = Settings(_env_file=None)
    assert settings.trading_mode == TradingMode.PAPER
    assert settings.bot_starting_cash_usd == 1000
    assert settings.bot_max_drawdown_fraction == 0.5


def test_live_mode_fails_closed():
    with pytest.raises(ValueError, match="Live trading is not implemented"):
        Settings(TRADING_MODE="live")


def test_email_subject_prefix_is_constant():
    settings = Settings(_env_file=None)
    assert settings.email_subject_prefix == "AI-BOT"


def test_dashboard_default_port_is_8011():
    settings = Settings(_env_file=None)
    assert settings.dashboard_port == 8011


def test_api_default_port_is_7011():
    settings = Settings(_env_file=None)
    assert settings.api_port == 7011


def test_dashboard_default_host_allows_lan_access():
    settings = Settings(_env_file=None)
    assert settings.dashboard_host == "0.0.0.0"
