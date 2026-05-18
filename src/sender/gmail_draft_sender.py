"""Gmail draft sender adapter."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_DRAFTS_URL = "https://gmail.googleapis.com/gmail/v1/users/{user_id}/drafts"


@dataclass(slots=True)
class GmailDraftSendResult:
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


class GmailDraftSender:
    def __init__(
        self,
        *,
        user_id: str = "me",
        oauth_client_id: str | None = None,
        oauth_client_secret: str | None = None,
        oauth_refresh_token: str | None = None,
        oauth_access_token: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret
        self.oauth_refresh_token = oauth_refresh_token
        self.oauth_access_token = oauth_access_token

    def create_draft(
        self,
        *,
        lead_id: str,
        to_email: str,
        subject: str,
        body: str,
        from_email: str | None = None,
    ) -> GmailDraftSendResult:
        message = EmailMessage()
        message["To"] = to_email
        message["Subject"] = subject
        if from_email:
            message["From"] = from_email
        message.set_content(body)

        encoded_raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        payload = {"message": {"raw": encoded_raw}}
        url = GMAIL_DRAFTS_URL.format(user_id=self.user_id)

        try:
            access_token = self._resolve_access_token()
            req = Request(
                url=url,
                method="POST",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(payload).encode("utf-8"),
            )
            with urlopen(req, timeout=30) as response:  # nosec - fixed trusted Google endpoint
                parsed = json.loads(response.read().decode("utf-8"))
            draft_id = parsed.get("id")
            if not isinstance(draft_id, str) or not draft_id.strip():
                raise ValueError("Gmail draft create response missing id.")
            return GmailDraftSendResult(
                lead_id=lead_id,
                recipient=to_email,
                status="draft_created",
                draft_id=draft_id,
                error=None,
            )
        except Exception as exc:  # pragma: no cover - network path
            return GmailDraftSendResult(
                lead_id=lead_id,
                recipient=to_email,
                status="failed",
                draft_id=None,
                error=str(exc),
            )

    def _resolve_access_token(self) -> str:
        if self.oauth_access_token and self.oauth_access_token.strip():
            return self.oauth_access_token.strip()

        if not (self.oauth_client_id and self.oauth_refresh_token):
            raise ValueError(
                "Missing Gmail OAuth credentials. Provide oauth_access_token or oauth_client_id + oauth_refresh_token."
            )

        data = {
            "client_id": self.oauth_client_id,
            "refresh_token": self.oauth_refresh_token,
            "grant_type": "refresh_token",
        }
        if self.oauth_client_secret:
            data["client_secret"] = self.oauth_client_secret

        req = Request(
            url=TOKEN_URL,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode(data).encode("utf-8"),
        )
        with urlopen(req, timeout=20) as response:  # nosec - fixed trusted Google endpoint
            parsed = json.loads(response.read().decode("utf-8"))
        token = parsed.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("Failed to obtain Gmail access token from refresh token.")
        return token.strip()

