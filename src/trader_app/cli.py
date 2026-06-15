import argparse
from datetime import date

from trader_app.account import AccountService
from trader_app.backtests.service import BacktestService
from trader_app.bot.engine import TradingEngine
from trader_app.bot.runner import BotRunner
from trader_app.config import Settings
from trader_app.database import create_session_factory, initialize_database
from trader_app.notifications.email import EmailNotifier
from trader_app.strategies.registry import load_strategies


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start-bot", "reset-safety", "run-backtests"])
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

    if args.command == "run-backtests":
        service = BacktestService(session_factory, settings, strategies=load_strategies("ALL"))
        runs = service.run_standard_backtests()
        print({"runs_recorded": len(runs), "periods": [run.period_name for run in runs]})
        return

    strategies = load_strategies(args.strategies)
    notifier = EmailNotifier(settings)
    runner = BotRunner(session_factory, settings.bot_heartbeat_stale_seconds)
    result = runner.ensure_running([strategy.name for strategy in strategies])

    service = BacktestService(session_factory, settings)

    def candle_loader(product_id: str):
        try:
            return service.load_strategy_candles(product_id, date(2024, 1, 1), date.today())
        except Exception:  # keep the bot alive even if market data is unavailable
            return []

    trading_engine = TradingEngine(
        session_factory, settings, candle_loader, strategies, notifier=notifier
    )
    cycle = trading_engine.run_cycle()

    if result["action"] in ("started", "restarted"):
        notifier.send(
            f"Bot {result['action']}",
            f"Strategies: {', '.join(strategy.name for strategy in strategies)}.",
        )

    print({**result, **cycle})


if __name__ == "__main__":
    main()
