"""Sender module exports."""

from .email_sender import EmailSendResult, SmtpEmailSender
from .gmail_draft_sender import GmailDraftSendResult, GmailDraftSender

__all__ = ["EmailSendResult", "SmtpEmailSender", "GmailDraftSendResult", "GmailDraftSender"]

