"""Rule helpers for deterministic lead scoring."""

from __future__ import annotations

import re
from typing import Any

from .models import (
    PENALTY_NO_SAMPLING_FEASIBILITY,
    PENALTY_NON_CONSUMABLE,
    PENALTY_VERY_LOW_MARGIN,
    SectionScore,
)


ALLOWED_STAGES = {"pre_revenue", "pre_seed", "seed", "series_a"}
CONSUMABLE_KEYWORDS = {
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


def score_icp_fit(lead: dict[str, Any]) -> SectionScore:
    score = 0
    reasons: list[str] = []

    category = _norm_text(lead.get("category"))
    if category and is_consumable_category(category):
        score += 15
        reasons.append("category_match")

    stage = _norm_text(lead.get("stage"))
    if stage in ALLOWED_STAGES:
        score += 10
        reasons.append("stage_match")

    team_size = _parse_number(lead.get("team_size"))
    if team_size is not None and 1 <= team_size <= 60:
        score += 10
        reasons.append("team_match")

    region = _norm_text(lead.get("region"))
    if region and "india" in region:
        score += 5
        reasons.append("region_match")

    return SectionScore(value=min(score, 40), reasons=reasons)


def score_need_intent(lead: dict[str, Any]) -> SectionScore:
    score = 0
    reasons: list[str] = []

    launch_days = _parse_number(lead.get("launch_recency_days"))
    if launch_days is not None and 0 <= launch_days <= 90:
        score += 10
        reasons.append("new_launch")

    if _norm_text(lead.get("public_review_request_signal")) == "yes":
        score += 8
        reasons.append("public_feedback_request")

    if _norm_text(lead.get("new_digital_presence_signal")) == "yes":
        score += 7
        reasons.append("new_presence")

    if _norm_text(lead.get("ugc_review_depth_signal")) == "low":
        score += 5
        reasons.append("low_ugc")

    if _norm_text(lead.get("paid_ads_signal")) in {"high", "medium"}:
        score += 5
        reasons.append("active_ads")

    return SectionScore(value=min(score, 35), reasons=reasons)


def score_operational_feasibility(lead: dict[str, Any]) -> SectionScore:
    score = 0
    reasons: list[str] = []

    sampling = _norm_text(lead.get("sampling_feasibility"))
    if sampling == "yes":
        score += 5
        reasons.append("sampling_yes")
    elif sampling == "unknown":
        score += 2
        reasons.append("sampling_unknown")

    shipping = _norm_text(lead.get("shipping_capability"))
    if shipping == "yes":
        score += 5
        reasons.append("shipping_yes")
    elif shipping == "unknown":
        score += 2
        reasons.append("shipping_unknown")

    margin = _norm_text(lead.get("margin_viability_signal"))
    if margin == "high":
        score += 5
        reasons.append("margin_high")
    elif margin == "medium":
        score += 3
        reasons.append("margin_medium")

    return SectionScore(value=min(score, 15), reasons=reasons)


def score_reachability(lead: dict[str, Any]) -> SectionScore:
    score = 0
    reasons: list[str] = []

    if has_direct_reachable_channel(lead):
        score += 5
        reasons.append("direct_reachable_channel")

    instagram = _norm_text(lead.get("instagram_handle"))
    whatsapp = _norm_text(lead.get("whatsapp_business_link_or_number"))
    if instagram or whatsapp:
        score += 3
        reasons.append("social_fallback")

    if _norm_text(lead.get("contact_form_status")) == "working":
        score += 2
        reasons.append("working_contact_form")

    return SectionScore(value=min(score, 10), reasons=reasons)


def compute_penalties(lead: dict[str, Any]) -> tuple[int, list[str]]:
    total = 0
    applied: list[str] = []

    category = _norm_text(lead.get("category"))
    if category and not is_consumable_category(category):
        total += 40
        applied.append(PENALTY_NON_CONSUMABLE)

    if _norm_text(lead.get("margin_viability_signal")) == "low":
        total += 10
        applied.append(PENALTY_VERY_LOW_MARGIN)

    if _norm_text(lead.get("sampling_feasibility")) == "no":
        total += 15
        applied.append(PENALTY_NO_SAMPLING_FEASIBILITY)

    return total, applied


def is_consumable_category(category: str) -> bool:
    lowered = category.lower()
    return any(keyword in lowered for keyword in CONSUMABLE_KEYWORDS)


def has_direct_reachable_channel(lead: dict[str, Any]) -> bool:
    channels = lead.get("contact_channels_available")
    if not isinstance(channels, list):
        return False

    allowed = {item for item in channels if isinstance(item, str)}
    email_signal = _norm_text(lead.get("email_validity_signal"))
    email = _norm_text(lead.get("founder_or_growth_email"))
    ig = _norm_text(lead.get("instagram_handle")) or _norm_text(lead.get("primary_profile_url"))
    whatsapp = _norm_text(lead.get("whatsapp_business_link_or_number"))

    has_email = "email" in allowed and email_signal == "valid" and bool(email)
    has_ig = "instagram_dm" in allowed and bool(ig)
    has_whatsapp = "whatsapp" in allowed and bool(whatsapp)
    return has_email or has_ig or has_whatsapp


def _norm_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip().lower()
    return stripped or None


def _parse_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if not text:
        return None
    if "solo" in text:
        return 1.0
    match = re.search(r"[-+]?\d*\.?\d+", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None

