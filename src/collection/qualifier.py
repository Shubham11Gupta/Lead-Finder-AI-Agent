"""Qualification gate logic for collection stage."""

from __future__ import annotations

from typing import Any

from .models import (
    SKIP_REASON_HARD_DISQUALIFIER,
    SKIP_REASON_INSUFFICIENT_EVIDENCE,
    SKIP_REASON_NO_REACHABLE_CHANNEL,
    SKIP_REASON_NON_CONSUMABLE,
    SKIP_REASON_SAMPLING_NOT_FEASIBLE,
)


CONSUMABLE_CATEGORY_KEYWORDS = {
    "beauty",
    "personal care",
    "nutrition",
    "snack",
    "pet",
    "health care",
    "healthcare",
    "consumable",
    "food",
    "beverage",
    "supplement",
}


def qualify_lead(lead: dict[str, Any]) -> tuple[bool, str | None]:
    """Return pass/fail and skip reason (if failed)."""
    category = _norm_text(lead.get("category"))
    if not category or category == "unknown":
        return False, SKIP_REASON_INSUFFICIENT_EVIDENCE
    if not _is_consumable_category(category):
        return False, SKIP_REASON_NON_CONSUMABLE

    if lead.get("hard_disqualifier_match") is True:
        return False, SKIP_REASON_HARD_DISQUALIFIER

    sampling_feasibility = _norm_text(lead.get("sampling_feasibility"))
    if sampling_feasibility == "no":
        return False, SKIP_REASON_SAMPLING_NOT_FEASIBLE

    if not _has_reachable_channel(lead):
        return False, SKIP_REASON_NO_REACHABLE_CHANNEL

    source_urls = lead.get("source_urls")
    if not isinstance(source_urls, list) or len([u for u in source_urls if isinstance(u, str) and u.strip()]) == 0:
        return False, SKIP_REASON_INSUFFICIENT_EVIDENCE

    return True, None


def filter_qualified_leads(leads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split leads into qualified and skipped groups."""
    qualified: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for lead in leads:
        passed, reason = qualify_lead(lead)
        if passed:
            qualified.append(lead)
            continue
        skipped.append(
            {
                "lead_id": lead.get("lead_id"),
                "reason": reason,
                "contact_source": lead.get("contact_source"),
            }
        )

    return qualified, skipped


def _has_reachable_channel(lead: dict[str, Any]) -> bool:
    channels = lead.get("contact_channels_available")
    if not isinstance(channels, list):
        return False

    channel_set = {item for item in channels if isinstance(item, str)}
    email = _norm_text(lead.get("founder_or_growth_email"))
    email_signal = _norm_text(lead.get("email_validity_signal"))
    ig = _norm_text(lead.get("instagram_handle")) or _norm_text(lead.get("primary_profile_url"))
    whatsapp = _norm_text(lead.get("whatsapp_business_link_or_number"))

    has_valid_email = "email" in channel_set and bool(email) and email_signal == "valid"
    has_ig_dm = "instagram_dm" in channel_set and bool(ig)
    has_whatsapp = "whatsapp" in channel_set and bool(whatsapp)
    return has_valid_email or has_ig_dm or has_whatsapp


def _is_consumable_category(category: str) -> bool:
    for keyword in CONSUMABLE_CATEGORY_KEYWORDS:
        if keyword in category:
            return True
    return False


def _norm_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip().lower()
    return stripped or None

