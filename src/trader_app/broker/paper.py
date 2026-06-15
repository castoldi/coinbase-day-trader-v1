from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.models import Account, Trade, utc_now


class PaperBroker:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def buy(self, product_id: str, quantity: float, price: float, strategy: str) -> Trade:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            if not account.trading_enabled:
                raise RuntimeError("Trading is disabled by safety lock")
            entry_value = quantity * price
            if entry_value > account.cash_usd:
                raise RuntimeError("Insufficient paper cash")
            account.cash_usd -= entry_value
            trade = Trade(
                product_id=product_id,
                strategy=strategy,
                side="buy",
                status="open",
                quantity=quantity,
                entry_price_usd=price,
                entry_value_usd=entry_value,
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
            pnl = exit_value - trade.entry_value_usd
            trade.exit_price_usd = exit_price
            trade.realized_pnl_usd = pnl
            trade.status = "closed"
            trade.closed_at = utc_now()
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            account.cash_usd += exit_value
            account.equity_usd = account.cash_usd
            account.realized_pnl_usd += pnl
            threshold = account.initial_cash_usd * account.max_drawdown_fraction
            if account.equity_usd <= threshold:
                account.trading_enabled = False
                account.safety_lock_reason = "equity_at_or_below_50_percent"
            session.commit()
            session.refresh(trade)
            return trade
