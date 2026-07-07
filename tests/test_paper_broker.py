import pytest

from trader_app.account import AccountService
from trader_app.broker.paper import PaperBroker
from trader_app.database import create_session_factory, initialize_database
from trader_app.models import Account


def make_broker(tmp_path, fee_rate=0.006):
    db_url = f"sqlite:///{tmp_path / 'broker.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    AccountService(session_factory).get_or_create_account(1000, 0.5)
    return session_factory, PaperBroker(session_factory, fee_rate=fee_rate)


def test_paper_buy_creates_open_trade(tmp_path):
    _, broker = make_broker(tmp_path)
    trade = broker.buy(product_id="BTC-USD", quantity=0.01, price=50000, strategy="test")
    assert trade.product_id == "BTC-USD"
    assert trade.status == "open"
    assert trade.entry_value_usd == 500
    assert trade.entry_fee_usd == pytest.approx(3.0)


def test_paper_buy_reserves_entry_fee_from_cash(tmp_path):
    session_factory, broker = make_broker(tmp_path, fee_rate=0.01)

    broker.buy(product_id="BTC-USD", quantity=1, price=100, strategy="test")

    with session_factory() as session:
        account = session.query(Account).one()
    assert account.cash_usd == pytest.approx(899)
    assert account.equity_usd == pytest.approx(999)


def test_closing_trade_updates_realized_pnl(tmp_path):
    session_factory, broker = make_broker(tmp_path, fee_rate=0.01)
    opened = broker.buy(product_id="BTC-USD", quantity=1, price=100, strategy="test")
    closed = broker.close_trade(opened.id, exit_price=110)
    assert closed.status == "closed"
    assert closed.entry_value_usd == pytest.approx(100)
    assert closed.entry_fee_usd == pytest.approx(1)
    assert closed.exit_fee_usd == pytest.approx(1.1)
    assert closed.realized_pnl_usd == pytest.approx(7.9)
    with session_factory() as session:
        account = session.query(Account).one()
    assert account.cash_usd == pytest.approx(1007.9)
    assert account.realized_pnl_usd == pytest.approx(7.9)


def test_buy_persists_stop_loss_and_take_profit(tmp_path):
    _, broker = make_broker(tmp_path)
    trade = broker.buy(
        product_id="BTC-USD",
        quantity=0.01,
        price=50000,
        strategy="test",
        stop_loss=49000,
        take_profit=52000,
    )
    assert trade.stop_loss_usd == 49000
    assert trade.take_profit_usd == 52000
