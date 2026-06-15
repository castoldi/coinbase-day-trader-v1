from trader_app.logging_config import configure_daily_logger


def test_configure_daily_logger_creates_log_file(tmp_path):
    logger = configure_daily_logger("bot", tmp_path)
    logger.info("hello")
    for handler in logger.handlers:
        handler.flush()
    assert (tmp_path / "bot.log").exists()
