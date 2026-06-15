from datetime import timedelta

from trader_app.bot.runner import BotRunner
from trader_app.database import create_session_factory, initialize_database
from trader_app.models import utc_now


def make_runner(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'bot.sqlite3'}"
    engine, session_factory = create_session_factory(db_url)
    initialize_database(engine)
    return BotRunner(session_factory, stale_seconds=1800)


def test_first_start_records_running_heartbeat(tmp_path):
    runner = make_runner(tmp_path)
    status = runner.ensure_running(["price_action_transcript"])
    assert status["action"] == "started"
    assert status["status"] == "healthy"


def test_healthy_bot_is_not_started_twice(tmp_path):
    runner = make_runner(tmp_path)
    runner.ensure_running(["price_action_transcript"])
    status = runner.ensure_running(["price_action_transcript"])
    assert status["action"] == "already_running"


def test_stale_bot_is_restarted(tmp_path):
    runner = make_runner(tmp_path)
    runner.ensure_running(["price_action_transcript"])
    runner.mark_heartbeat(utc_now() - timedelta(seconds=1900))
    status = runner.ensure_running(["price_action_transcript"])
    assert status["action"] == "restarted"
