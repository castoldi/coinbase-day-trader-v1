from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from trader_app.models import BotStatus


class BotRunner:
    def __init__(self, session_factory: sessionmaker[Session], stale_seconds: int) -> None:
        self.session_factory = session_factory
        self.stale_seconds = stale_seconds

    def ensure_running(self, strategies: list[str]) -> dict[str, str]:
        now = datetime.now(timezone.utc)
        strategy_text = ",".join(strategies)
        with self.session_factory() as session:
            status = session.scalar(select(BotStatus).order_by(BotStatus.id.asc()))
            if status is None:
                status = BotStatus(status="healthy", strategies=strategy_text, last_heartbeat_at=now)
                session.add(status)
                action = "started"
            else:
                heartbeat = status.last_heartbeat_at
                if heartbeat.tzinfo is None:
                    heartbeat = heartbeat.replace(tzinfo=timezone.utc)
                age = (now - heartbeat).total_seconds()
                if age <= self.stale_seconds and status.status == "healthy":
                    return {"action": "already_running", "status": status.status}
                status.status = "healthy"
                status.strategies = strategy_text
                status.last_heartbeat_at = now
                action = "restarted"
            session.commit()
            return {"action": action, "status": "healthy"}

    def mark_heartbeat(self, heartbeat_at: datetime) -> None:
        with self.session_factory() as session:
            status = session.scalar(select(BotStatus).order_by(BotStatus.id.asc()))
            if status is None:
                status = BotStatus(status="healthy", strategies="", last_heartbeat_at=heartbeat_at)
                session.add(status)
            else:
                status.last_heartbeat_at = heartbeat_at
            session.commit()
