import pytest

from trader_app.config import Settings, TradingMode


def test_defaults_are_safe_for_paper_trading():
    settings = Settings()
    assert settings.trading_mode == TradingMode.PAPER
    assert settings.bot_starting_cash_usd == 1000
    assert settings.bot_max_drawdown_fraction == 0.5


def test_live_mode_fails_closed():
    with pytest.raises(ValueError, match="Live trading is not implemented"):
        Settings(TRADING_MODE="live")


def test_email_subject_prefix_is_constant():
    settings = Settings()
    assert settings.email_subject_prefix == "AI-BOT"
