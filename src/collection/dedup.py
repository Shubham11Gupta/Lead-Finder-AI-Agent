"""Deduplication helpers for collected leads."""

from __future__ import annotations

from typing import Any

from .models import SKIP_REASON_DUPLICATE_MERGED


def deduplicate_leads(
    leads: list[dict[str, Any]],
    *,
    existing_leads: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deduplicate using the configured key precedence."""
    existing_leads = existing_leads or []
    unique: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    seen_indexes: dict[str, int] = {}
    existing_keys = _collect_existing_keys(existing_leads)

    for lead in leads:
        dedup_key = _dedup_key(lead)
        if dedup_key is None:
            unique.append(lead)
            continue

        if dedup_key in existing_keys:
            skipped.append(
                {
                    "lead_id": lead.get("lead_id"),
                    "reason": SKIP_REASON_DUPLICATE_MERGED,
                    "duplicate_key": dedup_key,
                    "duplicate_target": "existing",
                }
            )
            continue

        if dedup_key in seen_indexes:
            target_index = seen_indexes[dedup_key]
            _merge_lead_fields(unique[target_index], lead)
            skipped.append(
                {
                    "lead_id": lead.get("lead_id"),
                    "reason": SKIP_REASON_DUPLICATE_MERGED,
                    "duplicate_key": dedup_key,
                    "duplicate_target": unique[target_index].get("lead_id"),
                }
            )
            continue

        seen_indexes[dedup_key] = len(unique)
        unique.append(lead)

    return unique, skipped


def _collect_existing_keys(existing_leads: list[dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for lead in existing_leads:
        dedup_key = _dedup_key(lead)
        if dedup_key:
            keys.add(dedup_key)
    return keys


def _dedup_key(lead: dict[str, Any]) -> str | None:
    instagram = _norm_text(lead.get("instagram_handle"))
    if instagram:
        return f"ig:{instagram}"

    website = _norm_text(lead.get("website_url"))
    if website:
        return f"web:{website}"

    brand = _norm_text(lead.get("brand_name"))
    region = _norm_text(lead.get("region"))
    if brand and region:
        return f"brand_region:{brand}|{region}"

    return None


def _merge_lead_fields(primary: dict[str, Any], duplicate: dict[str, Any]) -> None:
    # Merge source evidence URLs.
    primary_urls = primary.get("source_urls") if isinstance(primary.get("source_urls"), list) else []
    duplicate_urls = duplicate.get("source_urls") if isinstance(duplicate.get("source_urls"), list) else []
    merged_urls: list[str] = []
    for url in [*primary_urls, *duplicate_urls]:
        if isinstance(url, str) and url.strip() and url not in merged_urls:
            merged_urls.append(url)
    if merged_urls:
        primary["source_urls"] = merged_urls

    # Update verification timestamp if duplicate has newer one.
    duplicate_verified = duplicate.get("last_verified_at")
    if isinstance(duplicate_verified, str) and duplicate_verified.strip():
        primary["last_verified_at"] = duplicate_verified.strip()

    # Capture alternate brand names in notes if they differ.
    p_brand = _norm_text(primary.get("brand_name"))
    d_brand = _norm_text(duplicate.get("brand_name"))
    if p_brand and d_brand and p_brand != d_brand:
        notes = primary.get("notes", "")
        extra_note = f"alternate_name:{duplicate.get('brand_name')}"
        if extra_note not in notes:
            separator = " | " if notes else ""
            primary["notes"] = f"{notes}{separator}{extra_note}"


def _norm_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip().lower()
    if not stripped:
        return None
    return stripped

