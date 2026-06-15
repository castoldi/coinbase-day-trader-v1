from fastapi.testclient import TestClient

from trader_app.api import create_app
from trader_app.database import create_session_factory, initialize_database


def make_client(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'api.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    return TestClient(create_app(session_factory=session_factory))


def test_health_endpoint(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_summary_shape(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["account"]["initial_cash_usd"] == 1000
    assert payload["bot"]["status"] in ["not_started", "healthy"]
    assert payload["trades"]["open"] == []
    assert "prices" in payload
    assert isinstance(payload["prices"], list)


def test_dashboard_summary_uses_injected_prices(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'api.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    client = TestClient(
        create_app(session_factory=session_factory, price_loader=lambda products: {"BTC-USD": 65000.0})
    )
    payload = client.get("/api/dashboard/summary").json()
    prices = {row["product_id"]: row["price_usd"] for row in payload["prices"]}
    assert prices["BTC-USD"] == 65000.0


def test_strategies_endpoint_describes_strategy_with_examples(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/strategies")
    assert response.status_code == 200
    payload = response.json()
    assert payload["strategies"], "expected at least one strategy"
    strategy = payload["strategies"][0]
    assert strategy["name"] == "ema_ribbon_reversal"
    assert {"entry", "stop_loss", "take_profit"} <= set(strategy["rules"].keys())
    assert len(strategy["examples"]) == 2
    example = strategy["examples"][0]
    assert example["candles"], "example must include candles"
    assert {"open", "high", "low", "close"} <= set(example["candles"][0].keys())
    assert {"entry", "stop_loss", "take_profit"} <= set(example.keys())
