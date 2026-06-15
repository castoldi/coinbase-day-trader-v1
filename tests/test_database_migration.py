from sqlalchemy import inspect, text

from trader_app.database import create_session_factory, initialize_database


def test_initialize_adds_missing_columns_to_existing_table(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'old.sqlite3'}"
    engine, _ = create_session_factory(db_url)
    # Simulate an older schema where the trades table lacks the newer columns.
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE trades ("
                "id INTEGER PRIMARY KEY, product_id TEXT, strategy TEXT, side TEXT, "
                "status TEXT, quantity FLOAT, entry_price_usd FLOAT, entry_value_usd FLOAT, "
                "exit_price_usd FLOAT, realized_pnl_usd FLOAT)"
            )
        )

    initialize_database(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("trades")}
    assert "stop_loss_usd" in columns
    assert "take_profit_usd" in columns
