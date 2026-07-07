from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.account import AccountService
from trader_app.broker.paper import PaperBroker
from trader_app.config import Settings
from trader_app.models import Account, Trade
from trader_app.strategies.base import Candle


class TradingEngine:
    """Runs one paper-trading cycle: load candles, evaluate strategies,
    manage open positions, and open new positions on confirmed signals.

    Designed to be invoked once per scheduled run (every ~30 minutes). All
    external inputs (candles, broker, notifier) are injectable for testing.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        settings: Settings,
        candle_loader: Callable[[str], list[Candle]],
        strategies: list,
        broker: PaperBroker | None = None,
        notifier=None,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.candle_loader = candle_loader
        self.strategies = strategies
        self.broker = broker or PaperBroker(session_factory, fee_rate=settings.backtest_fee_rate)
        self.notifier = notifier
        self.account_service = AccountService(session_factory)

    def run_cycle(self) -> dict[str, object]:
        account = self.account_service.get_or_create_account(
            self.settings.bot_starting_cash_usd, self.settings.bot_max_drawdown_fraction
        )
        if not account.trading_enabled:
            return {"status": "locked", "opened": 0, "closed": 0, "reason": account.safety_lock_reason}

        products = self.settings.products
        per_trade = self.settings.bot_starting_cash_usd / len(products) if products else 0.0
        opened = 0
        closed = 0

        for product_id in products:
            candles = self.candle_loader(product_id)
            if not candles:
                continue
            price = candles[-1].close

            for strategy in self.strategies:
                signal = strategy.generate_signal(candles)
                open_trades = self._open_trades(product_id, strategy.name)

                for trade in open_trades:
                    fill: float | None = None
                    if self._should_exit(trade, price, signal.action):
                        fill = price
                    else:
                        fill = self._strategy_exit(strategy, candles, trade.entry_price_usd)
                    if fill is not None:
                        self.broker.close_trade(trade.id, fill)
                        closed += 1
                        self._notify(
                            "Trade closed",
                            f"{product_id} closed at {fill:.2f} ({strategy.name}).",
                        )

                if not self._open_trades(product_id, strategy.name) and self._is_buy(signal):
                    account = self._current_account()
                    if not account.trading_enabled:
                        continue
                    spend = min(per_trade, account.cash_usd)
                    if spend > 0 and price > 0:
                        fee_rate = getattr(self.broker, "fee_rate", 0.0)
                        quantity = spend / (price * (1 + fee_rate))
                        self.broker.buy(
                            product_id=product_id,
                            quantity=quantity,
                            price=price,
                            strategy=strategy.name,
                            stop_loss=signal.stop_loss,
                            take_profit=signal.take_profit,
                        )
                        opened += 1
                        self._notify(
                            "Trade opened",
                            f"{product_id} long {quantity:.6f} @ {price:.2f} "
                            f"(SL {signal.stop_loss:.2f} / TP {signal.take_profit:.2f}, {strategy.name}).",
                        )

        if not self._current_account().trading_enabled:
            self._notify("Safety lock tripped", "Equity fell to the drawdown limit; trading is disabled.")

        return {"status": "ran", "opened": opened, "closed": closed}

    def _open_trades(self, product_id: str, strategy_name: str) -> list[Trade]:
        with self.session_factory() as session:
            return list(
                session.scalars(
                    select(Trade).where(
                        Trade.status == "open",
                        Trade.product_id == product_id,
                        Trade.strategy == strategy_name,
                    )
                ).all()
            )

    def _current_account(self) -> Account:
        with self.session_factory() as session:
            return session.scalar(select(Account).order_by(Account.id.asc()))

    @staticmethod
    def _is_buy(signal) -> bool:
        return signal.action == "buy" and signal.take_profit is not None

    @staticmethod
    def _strategy_exit(strategy, candles, entry_price: float) -> float | None:
        exit_signal = getattr(strategy, "exit_signal", None)
        if exit_signal is None:
            return None
        return exit_signal(candles, entry_price)

    @staticmethod
    def _should_exit(trade: Trade, price: float, action: str) -> bool:
        if trade.stop_loss_usd is not None and price <= trade.stop_loss_usd:
            return True
        if trade.take_profit_usd is not None and price >= trade.take_profit_usd:
            return True
        return action == "sell"

    def _notify(self, subject: str, body: str) -> None:
        if self.notifier is not None:
            self.notifier.send(subject, body)
