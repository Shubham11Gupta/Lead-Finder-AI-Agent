"""Suppression list manager."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.shared.json_io import read_json_file, write_json_file


def load_suppression_registry(path: str | Path) -> dict[str, Any]:
    data = read_json_file(Path(path), default={})
    registry = _normalize_registry(data)
    return registry


def save_suppression_registry(path: str | Path, registry: dict[str, Any]) -> None:
    write_json_file(Path(path), registry)


def is_lead_suppressed(lead: dict[str, Any], registry: dict[str, Any]) -> tuple[bool, str | None]:
    email = _norm(lead.get("founder_or_growth_email"))
    if email and email in registry["emails"]:
        return True, "email"

    instagram = _norm(lead.get("instagram_handle"))
    if instagram and instagram in registry["instagram_handles"]:
        return True, "instagram_handle"

    whatsapp = _norm(lead.get("whatsapp_business_link_or_number"))
    if whatsapp and whatsapp in registry["whatsapp_numbers"]:
        return True, "whatsapp"

    return False, None


def add_opt_out_to_suppression(
    *,
    lead: dict[str, Any],
    registry: dict[str, Any],
    reason: str = "opt_out_reply",
) -> dict[str, Any]:
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    email = _norm(lead.get("founder_or_growth_email"))
    instagram = _norm(lead.get("instagram_handle"))
    whatsapp = _norm(lead.get("whatsapp_business_link_or_number"))

    if email:
        registry["emails"][email] = {"reason": reason, "added_at": now_iso}
    if instagram:
        registry["instagram_handles"][instagram] = {"reason": reason, "added_at": now_iso}
    if whatsapp:
        registry["whatsapp_numbers"][whatsapp] = {"reason": reason, "added_at": now_iso}
    return registry


def _normalize_registry(data: Any) -> dict[str, Any]:
    base = {
        "emails": {},
        "instagram_handles": {},
        "whatsapp_numbers": {},
    }
    if not isinstance(data, dict):
        return base

    # Backward compatibility with old `suppressed_emails` list format.
    old_emails = data.get("suppressed_emails")
    if isinstance(old_emails, list):
        for item in old_emails:
            email = _norm(item)
            if email:
                base["emails"][email] = {"reason": "legacy_import", "added_at": ""}

    for key in ("emails", "instagram_handles", "whatsapp_numbers"):
        block = data.get(key)
        if isinstance(block, dict):
            for ident, meta in block.items():
                ident_norm = _norm(ident)
                if not ident_norm:
                    continue
                if isinstance(meta, dict):
                    base[key][ident_norm] = {
                        "reason": str(meta.get("reason", "unknown")),
                        "added_at": str(meta.get("added_at", "")),
                    }
                else:
                    base[key][ident_norm] = {"reason": "unknown", "added_at": ""}
    return base


def _norm(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip().lower()
    return cleaned if cleaned else None

