import argparse

from trader_app.account import AccountService
from trader_app.bot.runner import BotRunner
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.strategies.registry import load_strategies


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start-bot", "reset-safety"])
    parser.add_argument("--strategies", default="ALL")
    args = parser.parse_args()

    settings = Settings()
    engine, session_factory = create_session_factory(settings.database_url)
    initialize_database(engine)
    account_service = AccountService(session_factory)
    account_service.get_or_create_account(settings.bot_starting_cash_usd, settings.bot_max_drawdown_fraction)

    if args.command == "reset-safety":
        account_service.manual_reset_safety_lock()
        print("Safety lock reset")
        return

    strategies = load_strategies(args.strategies)
    runner = BotRunner(session_factory, settings.bot_heartbeat_stale_seconds)
    result = runner.ensure_running([strategy.name for strategy in strategies])
    print(result)
