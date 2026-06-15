from trader_app.account import AccountService
from trader_app.database import create_session_factory, initialize_database


def make_service(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    return AccountService(session_factory)


def test_account_starts_with_1000_usd(tmp_path):
    service = make_service(tmp_path)
    account = service.get_or_create_account(1000, 0.5)
    assert account.cash_usd == 1000
    assert account.equity_usd == 1000
    assert account.trading_enabled is True


def test_account_rolls_forward_after_loss(tmp_path):
    service = make_service(tmp_path)
    service.get_or_create_account(1000, 0.5)
    account = service.apply_realized_pnl(-200)
    assert account.cash_usd == 800
    assert account.equity_usd == 800
    assert account.trading_enabled is True


def test_account_locks_forever_at_half_initial_equity(tmp_path):
    service = make_service(tmp_path)
    service.get_or_create_account(1000, 0.5)
    account = service.apply_realized_pnl(-500)
    assert account.equity_usd == 500
    assert account.trading_enabled is False
    assert account.safety_lock_reason == "equity_at_or_below_50_percent"


def test_manual_reset_reallows_trading(tmp_path):
    service = make_service(tmp_path)
    service.get_or_create_account(1000, 0.5)
    service.apply_realized_pnl(-500)
    account = service.manual_reset_safety_lock()
    assert account.trading_enabled is True
    assert account.safety_lock_reason == ""
