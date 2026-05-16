"""Instagram connector that ingests manually collected local files."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

from .base import RawLeadCandidate, SourceConnector


class InstagramFileConnector(SourceConnector):
    """
    Read Instagram lead candidates from local files.

    Supported formats:
    1. CSV
    2. JSON (array of objects)
    3. JSONL (one JSON object per line)
    """

    def __init__(self, input_path: str | Path, *, name: str = "instagram_file") -> None:
        self.name = name
        self.input_path = Path(input_path)

    def discover(self, run_context: Mapping[str, Any] | None = None) -> list[RawLeadCandidate]:
        run_context = run_context or {}
        path = self._resolve_input_path(run_context)
        records = self._read_records(path)

        candidates: list[RawLeadCandidate] = []
        for record in records:
            payload = _normalize_record(record)
            evidence_urls = _collect_evidence_urls(payload)
            candidates.append(
                RawLeadCandidate(
                    source_platform="instagram",
                    payload=payload,
                    evidence_urls=evidence_urls,
                )
            )

        return candidates

    def _resolve_input_path(self, run_context: Mapping[str, Any]) -> Path:
        override = run_context.get("instagram_input_path")
        path = Path(override) if isinstance(override, str) and override.strip() else self.input_path
        if not path.exists():
            raise FileNotFoundError(f"Instagram input file not found: {path}")
        if not path.is_file():
            raise ValueError(f"Instagram input path is not a file: {path}")
        return path

    def _read_records(self, path: Path) -> list[dict[str, Any]]:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return _read_csv(path)
        if suffix == ".json":
            return _read_json(path)
        if suffix in {".jsonl", ".ndjson"}:
            return _read_jsonl(path)
        raise ValueError(f"Unsupported file type for Instagram connector: {path.suffix}")


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_clean_row(dict(row)) for row in reader]


def _read_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON input must be an array of objects.")
    rows: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        rows.append(_clean_row(dict(item)))
    return rows


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
            if isinstance(parsed, dict):
                rows.append(_clean_row(dict(parsed)))
    return rows


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if not isinstance(key, str):
            continue
        cleaned_key = key.strip()
        if not cleaned_key:
            continue
        if isinstance(value, str):
            cleaned[cleaned_key] = value.strip()
        else:
            cleaned[cleaned_key] = value
    return cleaned


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)

    payload["brand_name"] = _first_non_empty(
        payload,
        ["brand_name", "name", "brand"],
        default="unknown_brand",
    )
    payload["instagram_handle"] = _first_non_empty(payload, ["instagram_handle", "handle", "username"])
    payload["primary_profile_url"] = _first_non_empty(
        payload,
        ["primary_profile_url", "profile_url", "instagram_profile_url"],
    )
    if not payload["primary_profile_url"] and payload["instagram_handle"]:
        payload["primary_profile_url"] = f"https://instagram.com/{payload['instagram_handle']}"

    payload["whatsapp_business_link_or_number"] = _first_non_empty(
        payload,
        ["whatsapp_business_link_or_number", "whatsapp", "whatsapp_number"],
    )
    payload["founder_or_growth_email"] = _first_non_empty(
        payload,
        ["founder_or_growth_email", "email", "contact_email"],
    )
    payload["source_urls"] = _parse_url_list(
        _first_non_empty(payload, ["source_urls", "evidence_urls", "evidence_links"])
    )
    return payload


def _first_non_empty(payload: dict[str, Any], keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _parse_url_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    chunks = raw.replace(";", ",").split(",")
    urls: list[str] = []
    for chunk in chunks:
        url = chunk.strip()
        if url and url not in urls:
            urls.append(url)
    return urls


def _collect_evidence_urls(payload: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    profile = payload.get("primary_profile_url")
    if isinstance(profile, str) and profile.strip():
        urls.append(profile.strip())

    source_urls = payload.get("source_urls")
    if isinstance(source_urls, list):
        for url in source_urls:
            if isinstance(url, str) and url.strip() and url not in urls:
                urls.append(url.strip())

    return urls

