import smtplib
from collections.abc import Callable
from email.message import EmailMessage

from trader_app.config import Settings


class EmailNotifier:
    """Sends AI-BOT prefixed notification emails through Gmail SMTP.

    A ``sender`` callable can be injected for tests; in production it defaults
    to delivering the message over an authenticated Gmail SMTP connection.
    """

    def __init__(self, settings: Settings, sender: Callable[[EmailMessage], None] | None = None) -> None:
        self.settings = settings
        self._sender = sender or self._send_via_smtp

    def recipient(self) -> str:
        return self.settings.notify_email or self.settings.email_to or self.settings.gmail_user

    def enabled(self) -> bool:
        return bool(self.settings.gmail_user and self.settings.gmail_app_password and self.recipient())

    def send(self, subject: str, body: str) -> bool:
        if not self.enabled():
            return False
        message = EmailMessage()
        message["Subject"] = f"{self.settings.email_subject_prefix} {subject}"
        message["From"] = self.settings.gmail_user
        message["To"] = self.recipient()
        message.set_content(body)
        self._sender(message)
        return True

    def _send_via_smtp(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self.settings.gmail_smtp_host, self.settings.gmail_smtp_port) as server:
            server.starttls()
            server.login(self.settings.gmail_user, self.settings.gmail_app_password)
            server.send_message(message)
