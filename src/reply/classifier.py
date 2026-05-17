"""Deterministic reply classifier aligned to docs prompts."""

from __future__ import annotations

from typing import Any


OPT_OUT_TERMS = {"unsubscribe", "stop", "remove me", "dont contact", "don't contact"}
POSITIVE_TERMS = {"interested", "sounds good", "lets talk", "let's talk", "yes", "share details"}
NEGATIVE_TERMS = {"not interested", "no thanks", "no need", "not now"}


def classify_reply(lead_id: str, reply_text: str) -> dict[str, Any]:
    text = (reply_text or "").strip().lower()

    if not text:
        return _result(lead_id, "unclear", "low", "manual_review_required", do_not_contact=False)

    if _contains_any(text, OPT_OUT_TERMS):
        return _result(lead_id, "opt_out", "high", "suppressed", do_not_contact=True)
    if _contains_any(text, NEGATIVE_TERMS):
        return _result(lead_id, "negative", "high", "closed_no_interest", do_not_contact=False)
    if _contains_any(text, POSITIVE_TERMS):
        return _result(lead_id, "positive", "medium", "handoff_required", do_not_contact=False)
    if "who are you" in text or "wrong" in text:
        return _result(lead_id, "not_relevant", "medium", "closed_not_relevant", do_not_contact=False)
    if "maybe" in text or "later" in text:
        return _result(lead_id, "neutral", "medium", "manual_reply_required", do_not_contact=False)

    return _result(lead_id, "unclear", "low", "manual_review_required", do_not_contact=False)


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _result(
    lead_id: str,
    reply_type: str,
    confidence: str,
    action_taken: str,
    *,
    do_not_contact: bool,
) -> dict[str, Any]:
    return {
        "lead_id": lead_id,
        "reply_type": reply_type,
        "classification_confidence": confidence,
        "action_taken": action_taken,
        "do_not_contact": do_not_contact,
        "notes": "auto_classified",
    }

