from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.models import Account


class AccountService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def get_or_create_account(self, starting_cash: float, max_drawdown_fraction: float) -> Account:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                account = Account(
                    initial_cash_usd=starting_cash,
                    cash_usd=starting_cash,
                    equity_usd=starting_cash,
                    realized_pnl_usd=0,
                    max_drawdown_fraction=max_drawdown_fraction,
                    trading_enabled=True,
                    safety_lock_reason="",
                )
                session.add(account)
                session.commit()
                session.refresh(account)
            return account

    def apply_realized_pnl(self, pnl_usd: float) -> Account:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            account.realized_pnl_usd += pnl_usd
            account.cash_usd += pnl_usd
            account.equity_usd += pnl_usd
            threshold = account.initial_cash_usd * account.max_drawdown_fraction
            if account.equity_usd <= threshold:
                account.trading_enabled = False
                account.safety_lock_reason = "equity_at_or_below_50_percent"
            session.commit()
            session.refresh(account)
            return account

    def manual_reset_safety_lock(self) -> Account:
        with self.session_factory() as session:
            account = session.scalar(select(Account).order_by(Account.id.asc()))
            if account is None:
                raise RuntimeError("Account has not been initialized")
            account.trading_enabled = True
            account.safety_lock_reason = ""
            session.commit()
            session.refresh(account)
            return account
