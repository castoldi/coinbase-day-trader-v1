from email.message import EmailMessage

from trader_app.config import Settings
from trader_app.notifications.email import EmailNotifier


def settings_with(**overrides) -> Settings:
    base = {
        "gmail_user": "",
        "gmail_app_password": "",
        "notify_email": "",
        "email_to": "",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def test_disabled_when_no_credentials():
    sent: list[EmailMessage] = []
    notifier = EmailNotifier(settings_with(), sender=sent.append)
    assert notifier.enabled() is False
    assert notifier.send("Started", "bot is up") is False
    assert sent == []


def test_send_prefixes_subject_with_ai_bot():
    sent: list[EmailMessage] = []
    notifier = EmailNotifier(
        settings_with(gmail_user="me@gmail.com", gmail_app_password="secret", notify_email="me@gmail.com"),
        sender=sent.append,
    )
    assert notifier.enabled() is True
    assert notifier.send("Trade opened", "BTC-USD long") is True
    assert len(sent) == 1
    assert sent[0]["Subject"].startswith("AI-BOT")
    assert "Trade opened" in sent[0]["Subject"]
    assert sent[0]["To"] == "me@gmail.com"


def test_recipient_falls_back_to_gmail_user():
    notifier = EmailNotifier(
        settings_with(gmail_user="me@gmail.com", gmail_app_password="secret"),
        sender=lambda message: None,
    )
    assert notifier.recipient() == "me@gmail.com"
