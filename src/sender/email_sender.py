"""SMTP email sender for automated first-touch outreach."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any


@dataclass(slots=True)
class EmailSendResult:
    lead_id: str
    recipient: str
    status: str
    sent_at: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "recipient": self.recipient,
            "status": self.status,
            "sent_at": self.sent_at,
            "error": self.error,
        }


class SmtpEmailSender:
    """Sends outbound first-touch emails via SMTP."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        from_name: str,
        use_starttls: bool = True,
        use_ssl: bool = False,
        timeout_seconds: int = 30,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
        self.use_starttls = use_starttls
        self.use_ssl = use_ssl
        self.timeout_seconds = timeout_seconds

    def send(self, *, lead_id: str, to_email: str, subject: str, body: str) -> EmailSendResult:
        message = EmailMessage()
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout_seconds) as smtp:
                    smtp.login(self.username, self.password)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=self.timeout_seconds) as smtp:
                    smtp.ehlo()
                    if self.use_starttls:
                        smtp.starttls()
                        smtp.ehlo()
                    smtp.login(self.username, self.password)
                    smtp.send_message(message)
        except Exception as exc:  # pragma: no cover - live IO path
            return EmailSendResult(
                lead_id=lead_id,
                recipient=to_email,
                status="failed",
                sent_at=None,
                error=str(exc),
            )

        return EmailSendResult(
            lead_id=lead_id,
            recipient=to_email,
            status="sent",
            sent_at=datetime.now(tz=timezone.utc).isoformat(),
            error=None,
        )

