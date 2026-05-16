"""Selection logic for persona, channel, signal, and template."""

from __future__ import annotations

from typing import Any

from .templates import (
    CHANNEL_EMAIL,
    CHANNEL_INSTAGRAM_DM,
    CHANNEL_WHATSAPP,
    PERSONA_BRAND,
    PERSONA_FOUNDER,
    PERSONA_GROWTH,
    SIGNAL_GENERIC,
    SIGNAL_LOW_UGC,
    SIGNAL_NEW_LAUNCH,
    SIGNAL_PAID_ADS,
    SIGNAL_REVIEW_REQUEST,
    SIGNAL_SAMPLING,
    TEMPLATE_LIBRARY,
    TemplateDefinition,
)


def select_channel(lead: dict[str, Any]) -> str | None:
    channels = _as_channel_set(lead.get("contact_channels_available"))
    email_valid = _norm(lead.get("email_validity_signal")) == "valid"
    email = _norm(lead.get("founder_or_growth_email"))
    ig = _norm(lead.get("instagram_handle")) or _looks_instagram_url(lead.get("primary_profile_url"))
    whatsapp = _norm(lead.get("whatsapp_business_link_or_number"))

    if CHANNEL_EMAIL in channels and email_valid and email:
        return CHANNEL_EMAIL
    if CHANNEL_INSTAGRAM_DM in channels and ig:
        return CHANNEL_INSTAGRAM_DM
    if CHANNEL_WHATSAPP in channels and whatsapp:
        return CHANNEL_WHATSAPP
    return None


def infer_persona(lead: dict[str, Any], channel: str) -> str:
    explicit = _norm(lead.get("persona")) or _norm(lead.get("target_persona"))
    if explicit:
        if "growth" in explicit:
            return PERSONA_GROWTH
        if "brand" in explicit or "e-commerce" in explicit or "ecommerce" in explicit:
            return PERSONA_BRAND
        if "founder" in explicit:
            return PERSONA_FOUNDER

    paid_ads = _norm(lead.get("paid_ads_signal"))
    ugc = _norm(lead.get("ugc_review_depth_signal"))
    review_req = _norm(lead.get("public_review_request_signal"))

    if channel == CHANNEL_WHATSAPP:
        return PERSONA_BRAND
    if paid_ads in {"high", "medium"}:
        return PERSONA_GROWTH
    if ugc in {"low", "unknown"} or review_req in {"yes", "unknown"}:
        return PERSONA_BRAND
    return PERSONA_FOUNDER


def infer_primary_signal(lead: dict[str, Any]) -> str:
    launch_days = _parse_number(lead.get("launch_recency_days"))
    if launch_days is not None and 0 <= launch_days <= 90:
        return SIGNAL_NEW_LAUNCH

    if _norm(lead.get("paid_ads_signal")) in {"high", "medium"}:
        return SIGNAL_PAID_ADS

    if _norm(lead.get("ugc_review_depth_signal")) in {"low", "unknown"}:
        return SIGNAL_LOW_UGC

    if _norm(lead.get("public_review_request_signal")) in {"yes", "unknown"}:
        return SIGNAL_REVIEW_REQUEST

    if _norm(lead.get("sampling_feasibility")) in {"yes", "unknown"}:
        return SIGNAL_SAMPLING

    return SIGNAL_GENERIC


def select_template(*, persona: str, channel: str, signal: str) -> TemplateDefinition | None:
    for template in TEMPLATE_LIBRARY:
        if template.persona == persona and template.channel == channel and signal in template.signals:
            return template

    # Fallback to generic in same persona+channel
    for template in TEMPLATE_LIBRARY:
        if template.persona == persona and template.channel == channel and SIGNAL_GENERIC in template.signals:
            return template
    return None


def _as_channel_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def _norm(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip().lower()
    return stripped or None


def _looks_instagram_url(value: Any) -> str | None:
    text = _norm(value)
    if not text:
        return None
    if "instagram.com" in text:
        return text
    return None


def _parse_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None

