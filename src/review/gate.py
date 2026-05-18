"""Deterministic review gate for first-touch drafts."""

from __future__ import annotations

import re
from typing import Any


PROHIBITED_PATTERNS = [
    re.compile(r"\bguarantee(?:d)?\b", flags=re.IGNORECASE),
    re.compile(r"\b\d+\s*%\s*(?:roi|conversion|lift)\b", flags=re.IGNORECASE),
    re.compile(r"\bno[- ]risk\b", flags=re.IGNORECASE),
    re.compile(r"\bassured\b", flags=re.IGNORECASE),
]


def review_draft_queue(
    *,
    draft_queue: list[dict[str, Any]],
    lead_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    reviews: list[dict[str, Any]] = []
    approved_drafts: list[dict[str, Any]] = []
    rejected_drafts: list[dict[str, Any]] = []

    for draft in draft_queue:
        lead_id = str(draft.get("lead_id", "unknown"))
        lead = lead_by_id.get(lead_id, {})
        review = _review_single_draft(draft=draft, lead=lead)
        reviews.append(review)

        updated_draft = dict(draft)
        updated_draft["review_status"] = "approved" if review["decision"] == "approve" else "rejected"
        if review["decision"] == "approve":
            approved_drafts.append(updated_draft)
        else:
            rejected_drafts.append(updated_draft)

    return {
        "reviews": reviews,
        "approved_drafts": approved_drafts,
        "rejected_drafts": rejected_drafts,
        "review_summary": {
            "input_count": len(draft_queue),
            "approved_count": len(approved_drafts),
            "rejected_count": len(rejected_drafts),
        },
    }


def _review_single_draft(*, draft: dict[str, Any], lead: dict[str, Any]) -> dict[str, Any]:
    lead_id = str(draft.get("lead_id", "unknown"))
    channel = _norm(draft.get("channel_selected")) or "email"
    subject = _norm(draft.get("message_subject"))
    body = _norm(draft.get("message_draft")) or ""
    signal_reason = _norm(draft.get("personalization_reason"))
    issues: list[dict[str, str]] = []

    if not signal_reason:
        issues.append({"type": "relevance", "detail": "Missing personalization reason."})

    if not _has_clear_cta(body):
        issues.append({"type": "cta", "detail": "No clear CTA detected."})

    policy_issue = _policy_issue(subject=subject or "", body=body)
    if policy_issue:
        issues.append({"type": "policy", "detail": policy_issue})

    length_issue = _length_issue(channel=channel, body=body)
    if length_issue:
        issues.append({"type": "clarity", "detail": length_issue})

    tone_issue = _tone_issue(body)
    if tone_issue:
        issues.append({"type": "tone", "detail": tone_issue})

    decision = "approve" if not issues else "reject"
    return {
        "lead_id": lead_id,
        "decision": decision,
        "issues": issues,
        "revised_draft": {
            "message_subject": subject,
            "message_draft": body,
        },
        "review_notes": "auto_review_gate",
    }


def _has_clear_cta(body: str) -> bool:
    lowered = body.lower()
    if "?" in lowered:
        return True
    cta_markers = ["open to", "would you", "can we", "happy to share", "pilot"]
    return any(marker in lowered for marker in cta_markers)


def _policy_issue(*, subject: str, body: str) -> str | None:
    merged = f"{subject}\n{body}"
    for pattern in PROHIBITED_PATTERNS:
        if pattern.search(merged):
            return "Contains prohibited claim language."
    return None


def _length_issue(*, channel: str, body: str) -> str | None:
    words = len(body.split())
    if channel == "email":
        if words < 30 or words > 220:
            return "Email draft length outside recommended 30-220 words."
    elif channel in {"instagram_dm", "whatsapp"}:
        if words < 15 or words > 120:
            return "DM/WhatsApp draft length outside recommended 15-120 words."
    return None


def _tone_issue(body: str) -> str | None:
    lowered = body.lower()
    spammy = ["act now", "limited time", "urgent", "guaranteed"]
    if any(token in lowered for token in spammy):
        return "Tone appears spammy or pushy."
    return None


def _norm(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None
