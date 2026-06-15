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
