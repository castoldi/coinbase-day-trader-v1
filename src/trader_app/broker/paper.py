from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.models import Account, Trade, utc_now


class PaperBroker:
    def __init__(self, session_factory: sessionmaker[Session], fee_rate: float = 0.006) -> None:
        if fee_rate < 0:
            raise ValueError("fee_rate must be non-negative")
        self.session_factory = session_factory
        self.fee_rate = fee_rate

    def buy(
        self,
        product_id: str,
        quantity: float,
        price: float,
        strategy: str,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> Trade:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            if not account.trading_enabled:
                raise RuntimeError("Trading is disabled by safety lock")
            entry_value = quantity * price
            entry_fee = self._fee(entry_value)
            total_cost = entry_value + entry_fee
            if total_cost > account.cash_usd:
                raise RuntimeError("Insufficient paper cash")
            account.cash_usd -= total_cost
            account.equity_usd -= entry_fee
            trade = Trade(
                product_id=product_id,
                strategy=strategy,
                side="buy",
                status="open",
                quantity=quantity,
                entry_price_usd=price,
                entry_value_usd=entry_value,
                entry_fee_usd=entry_fee,
                stop_loss_usd=stop_loss,
                take_profit_usd=take_profit,
                realized_pnl_usd=0,
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade

    def close_trade(self, trade_id: int, exit_price: float) -> Trade:
        with self.session_factory() as session:
            trade = session.get(Trade, trade_id)
            if trade is None:
                raise RuntimeError("Trade not found")
            if trade.status != "open":
                raise RuntimeError("Trade is not open")
            exit_value = trade.quantity * exit_price
            entry_fee = trade.entry_fee_usd or 0.0
            exit_fee = self._fee(exit_value)
            net_exit_value = exit_value - exit_fee
            pnl = net_exit_value - trade.entry_value_usd - entry_fee
            trade.exit_price_usd = exit_price
            trade.exit_fee_usd = exit_fee
            trade.realized_pnl_usd = pnl
            trade.status = "closed"
            trade.closed_at = utc_now()
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            account.cash_usd += net_exit_value
            account.equity_usd = account.cash_usd
            account.realized_pnl_usd += pnl
            threshold = account.initial_cash_usd * account.max_drawdown_fraction
            if account.equity_usd <= threshold:
                account.trading_enabled = False
                account.safety_lock_reason = "equity_at_or_below_50_percent"
            session.commit()
            session.refresh(trade)
            return trade

    def _fee(self, notional_usd: float) -> float:
        return notional_usd * self.fee_rate
