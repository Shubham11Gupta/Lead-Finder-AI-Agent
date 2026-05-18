"""Gmail draft creation using Gmail API."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import GmailDraftConfig


TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_DRAFTS_URL = "https://gmail.googleapis.com/gmail/v1/users/{user_id}/drafts"


@dataclass(slots=True)
class GmailDraftResult:
    lead_id: str
    recipient: str
    status: str
    draft_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "recipient": self.recipient,
            "status": self.status,
            "draft_id": self.draft_id,
            "error": self.error,
        }


class GmailDraftClient:
    def __init__(self, config: GmailDraftConfig) -> None:
        self.config = config

    def create_draft(self, *, to_email: str, subject: str, body: str) -> str:
        access_token = self._resolve_access_token()
        message = EmailMessage()
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        payload = {"message": {"raw": encoded_message}}
        url = GMAIL_DRAFTS_URL.format(user_id=self.config.user_id)
        req = Request(
            url=url,
            method="POST",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
        )
        with urlopen(req, timeout=30) as response:  # nosec - fixed trusted Google API endpoint
            parsed = json.loads(response.read().decode("utf-8"))

        draft_id = parsed.get("id")
        if not isinstance(draft_id, str) or not draft_id.strip():
            raise ValueError("Gmail API response missing draft id.")
        return draft_id

    def _resolve_access_token(self) -> str:
        if self.config.oauth_access_token:
            return self.config.oauth_access_token

        if not (self.config.oauth_client_id and self.config.oauth_refresh_token):
            raise ValueError("Missing Gmail OAuth credentials: provide access token or client_id + refresh_token.")

        data = {
            "client_id": self.config.oauth_client_id,
            "refresh_token": self.config.oauth_refresh_token,
            "grant_type": "refresh_token",
        }
        if self.config.oauth_client_secret:
            data["client_secret"] = self.config.oauth_client_secret

        req = Request(
            url=TOKEN_URL,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode(data).encode("utf-8"),
        )
        with urlopen(req, timeout=20) as response:  # nosec - fixed trusted Google OAuth endpoint
            parsed = json.loads(response.read().decode("utf-8"))

        token = parsed.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("Failed to refresh Gmail access token.")
        return token.strip()

