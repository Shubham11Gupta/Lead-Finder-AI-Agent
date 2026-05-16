"""Normalize raw source candidates into lead-schema-shaped records."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from src.connectors.base import RawLeadCandidate


def normalize_candidate(
    candidate: RawLeadCandidate,
    *,
    now: datetime | None = None,
    default_region: str = "India",
) -> dict[str, Any]:
    """
    Convert a raw candidate into a lead-shaped record.

    Notes:
    - Fills unknown-safe defaults for required schema fields.
    - Keeps raw values where possible so validator can catch invalid enums.
    """
    payload = candidate.payload
    now_dt = now or datetime.now(tz=timezone.utc)
    now_iso = now_dt.isoformat()

    brand_name = _first_non_empty_str(payload, ["brand_name", "name"]) or "unknown_brand"
    primary_profile_url = _first_non_empty_str(
        payload,
        ["primary_profile_url", "profile_url", "url", "instagram_profile_url", "website_url"],
    ) or "https://unknown.local/profile"
    website_url = _first_non_empty_str(payload, ["website_url"])
    instagram_handle = _first_non_empty_str(payload, ["instagram_handle"]) or _extract_instagram_handle(
        primary_profile_url
    )
    whatsapp = _first_non_empty_str(payload, ["whatsapp_business_link_or_number", "whatsapp"])
    founder_email = _first_non_empty_str(payload, ["founder_or_growth_email", "email"])
    category = _first_non_empty_str(payload, ["category"]) or "unknown"
    region = _first_non_empty_str(payload, ["region"]) or default_region

    contact_channels = _normalize_channels(payload.get("contact_channels_available"))
    if founder_email and "email" not in contact_channels:
        contact_channels.append("email")
    if instagram_handle and "instagram_dm" not in contact_channels:
        contact_channels.append("instagram_dm")
    if whatsapp and "whatsapp" not in contact_channels:
        contact_channels.append("whatsapp")
    if not contact_channels and "instagram.com" in primary_profile_url.lower():
        # Social-first fallback path for first-touch discovery.
        contact_channels.append("instagram_dm")

    source_urls = _normalize_source_urls(candidate.evidence_urls, payload.get("source_urls"))

    brand_presence_type = _first_non_empty_str(payload, ["brand_presence_type"])
    if not brand_presence_type:
        brand_presence_type = "website_brand" if website_url else "social_first_unregistered"

    lead_id = _first_non_empty_str(payload, ["lead_id"]) or build_lead_id(
        primary_profile_url=primary_profile_url,
        brand_name=brand_name,
        region=region,
    )

    record: dict[str, Any] = {
        "lead_id": lead_id,
        "brand_name": brand_name,
        "brand_presence_type": brand_presence_type,
        "registration_status": _first_non_empty_str(payload, ["registration_status"]) or "unknown",
        "category": category,
        "stage": _first_non_empty_str(payload, ["stage"]) or "unknown",
        "region": region,
        "team_size": payload.get("team_size"),
        "primary_profile_url": primary_profile_url,
        "website_url": website_url,
        "instagram_handle": instagram_handle,
        "whatsapp_business_link_or_number": whatsapp,
        "contact_channels_available": contact_channels,
        "founder_or_growth_email": founder_email,
        "email_validity_signal": _first_non_empty_str(payload, ["email_validity_signal"]) or "unknown",
        "contact_form_status": _first_non_empty_str(payload, ["contact_form_status"]) or "unknown",
        "launch_recency_days": payload.get("launch_recency_days"),
        "ugc_review_depth_signal": _first_non_empty_str(payload, ["ugc_review_depth_signal"]) or "unknown",
        "paid_ads_signal": _first_non_empty_str(payload, ["paid_ads_signal"]) or "unknown",
        "public_review_request_signal": _first_non_empty_str(payload, ["public_review_request_signal"])
        or "unknown",
        "new_digital_presence_signal": _first_non_empty_str(payload, ["new_digital_presence_signal"])
        or "unknown",
        "social_presence_signal": _first_non_empty_str(payload, ["social_presence_signal"]) or "unknown",
        "sampling_feasibility": _first_non_empty_str(payload, ["sampling_feasibility"]) or "unknown",
        "shipping_capability": _first_non_empty_str(payload, ["shipping_capability"]) or "unknown",
        "margin_viability_signal": _first_non_empty_str(payload, ["margin_viability_signal"]) or "unknown",
        "outreach_status": _first_non_empty_str(payload, ["outreach_status"]) or "not_started",
        "response_status": _first_non_empty_str(payload, ["response_status"]) or "none",
        "contact_source": candidate.source_platform,
        "source_urls": source_urls,
        "notes": _first_non_empty_str(payload, ["notes"]),
        "last_verified_at": _first_non_empty_str(payload, ["last_verified_at"]) or now_iso,
        "created_at": _first_non_empty_str(payload, ["created_at"]) or now_iso,
        "updated_at": _first_non_empty_str(payload, ["updated_at"]) or now_iso,
    }

    # Keep optional scoring snapshot if raw payload already has them.
    for key in (
        "icp_fit_score",
        "need_intent_score",
        "operational_feasibility_score",
        "reachability_score",
        "penalties_applied",
        "final_score",
        "priority_bucket",
        "scored_at",
        "last_outreach_at",
    ):
        if key in payload:
            record[key] = payload[key]

    # Remove None values from optional fields to keep storage clean.
    return {k: v for k, v in record.items() if v is not None}


def build_lead_id(*, primary_profile_url: str, brand_name: str, region: str) -> str:
    seed = f"{primary_profile_url}|{brand_name.strip().lower()}|{region.strip().lower()}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"lead_{digest}"


def _first_non_empty_str(payload: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _extract_instagram_handle(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if "instagram.com" not in (parsed.netloc or "").lower():
        return None
    path_parts = [chunk for chunk in parsed.path.split("/") if chunk]
    if not path_parts:
        return None
    return path_parts[0].lstrip("@")


def _normalize_channels(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        candidates = [part.strip() for part in value.split(",")]
    elif isinstance(value, list):
        candidates = [item for item in value if isinstance(item, str)]
    else:
        return []
    normalized: list[str] = []
    for item in candidates:
        lowered = item.strip().lower()
        if lowered in {"email", "instagram_dm", "whatsapp"} and lowered not in normalized:
            normalized.append(lowered)
    return normalized


def _normalize_source_urls(*values: Any) -> list[str]:
    urls: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            candidate_values = [value]
        elif isinstance(value, list):
            candidate_values = [v for v in value if isinstance(v, str)]
        else:
            continue
        for url in candidate_values:
            cleaned = url.strip()
            if cleaned and cleaned not in urls:
                urls.append(cleaned)
    return urls
