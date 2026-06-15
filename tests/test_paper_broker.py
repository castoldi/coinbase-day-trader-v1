from trader_app.account import AccountService
from trader_app.broker.paper import PaperBroker
from trader_app.database import create_session_factory, initialize_database


def make_broker(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'broker.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    AccountService(session_factory).get_or_create_account(1000, 0.5)
    return PaperBroker(session_factory)


def test_paper_buy_creates_open_trade(tmp_path):
    broker = make_broker(tmp_path)
    trade = broker.buy(product_id="BTC-USD", quantity=0.01, price=50000, strategy="test")
    assert trade.product_id == "BTC-USD"
    assert trade.status == "open"
    assert trade.entry_value_usd == 500


def test_closing_trade_updates_realized_pnl(tmp_path):
    broker = make_broker(tmp_path)
    opened = broker.buy(product_id="BTC-USD", quantity=0.01, price=50000, strategy="test")
    closed = broker.close_trade(opened.id, exit_price=51000)
    assert closed.status == "closed"
    assert closed.realized_pnl_usd == 10
