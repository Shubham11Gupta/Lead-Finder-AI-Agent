"""Config loading for semipilot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import GmailDraftConfig, SearchConfig, SemipilotConfig


def load_config(config_path: str | Path) -> SemipilotConfig:
    path = Path(config_path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    api_key = _value(payload, "openai_api_key") or os.getenv("OPENAI_API_KEY", "")
    if not api_key.strip():
        raise ValueError("Missing OpenAI API key. Set `openai_api_key` in config or OPENAI_API_KEY.")

    prompts_dir = Path(_value(payload, "prompts_dir") or "docs/prompts")
    output_dir = Path(_value(payload, "output_dir") or "semipilot/runs")

    raw_evidence_path_raw = _value(payload, "raw_evidence_path")
    raw_evidence_path = (
        Path(raw_evidence_path_raw) if isinstance(raw_evidence_path_raw, str) and raw_evidence_path_raw.strip() else None
    )

    replies_path_raw = _value(payload, "replies_path")
    replies_path = Path(replies_path_raw) if isinstance(replies_path_raw, str) and replies_path_raw.strip() else None

    search_payload = _dict_value(payload, "search")
    search_provider = str(search_payload.get("provider", "google_cse")).strip().lower()
    search_queries = _normalize_queries(search_payload.get("queries")) or _default_queries()

    search = SearchConfig(
        provider=search_provider,
        queries=search_queries,
        max_results_per_query=int(search_payload.get("max_results_per_query", 10)),
        fetch_page_content=bool(search_payload.get("fetch_page_content", True)),
        fetch_pages_per_query=int(search_payload.get("fetch_pages_per_query", 3)),
        google_api_key=_str_or_none(search_payload.get("google_api_key")) or _env_or_none("GOOGLE_API_KEY"),
        google_cse_id=_str_or_none(search_payload.get("google_cse_id")) or _env_or_none("GOOGLE_CSE_ID"),
        serper_api_key=_str_or_none(search_payload.get("serper_api_key")) or _env_or_none("SERPER_API_KEY"),
        region=str(search_payload.get("region", "in")),
        language=str(search_payload.get("language", "en")),
    )

    gmail_payload = _dict_value(payload, "gmail_drafts")
    gmail_drafts = GmailDraftConfig(
        enabled=bool(gmail_payload.get("enabled", False)),
        user_id=str(gmail_payload.get("user_id", "me")),
        oauth_client_id=_str_or_none(gmail_payload.get("oauth_client_id")) or _env_or_none("GOOGLE_OAUTH_CLIENT_ID"),
        oauth_client_secret=_str_or_none(gmail_payload.get("oauth_client_secret"))
        or _env_or_none("GOOGLE_OAUTH_CLIENT_SECRET"),
        oauth_refresh_token=_str_or_none(gmail_payload.get("oauth_refresh_token"))
        or _env_or_none("GOOGLE_OAUTH_REFRESH_TOKEN"),
        oauth_access_token=_str_or_none(gmail_payload.get("oauth_access_token")) or _env_or_none("GOOGLE_ACCESS_TOKEN"),
        subject_fallback=str(gmail_payload.get("subject_fallback", "Quick idea for your brand")),
        only_review_approved=bool(gmail_payload.get("only_review_approved", True)),
    )

    return SemipilotConfig(
        openai_api_key=api_key.strip(),
        model=str(_value(payload, "model") or "gpt-5-mini"),
        prompts_dir=prompts_dir,
        output_dir=output_dir,
        sender_name=str(_value(payload, "sender_name") or "Trio&Buy Team"),
        sender_company=str(_value(payload, "sender_company") or "Trio&Buy"),
        raw_evidence_path=raw_evidence_path,
        search=search,
        gmail_drafts=gmail_drafts,
        replies_path=replies_path,
        run_reply_classification=bool(_value(payload, "run_reply_classification") or False),
    )


def _value(payload: dict[str, Any], key: str) -> Any:
    return payload.get(key)


def _dict_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _env_or_none(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _str_or_none(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _normalize_queries(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                output.append(cleaned)
    return output


def _default_queries() -> list[str]:
    return [
        "new d2c beauty brand india launched",
        "new d2c snack startup india trial pack",
        "pre revenue d2c nutrition brand india",
        "india d2c pet care startup launched",
        "instagram d2c consumable brand india",
    ]
