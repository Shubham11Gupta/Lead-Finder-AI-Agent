"""Typed models for semipilot runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SearchConfig:
    provider: str
    queries: list[str]
    max_results_per_query: int
    fetch_page_content: bool
    fetch_pages_per_query: int
    google_api_key: str | None
    google_cse_id: str | None
    serper_api_key: str | None
    region: str
    language: str


@dataclass(slots=True)
class GmailDraftConfig:
    enabled: bool
    user_id: str
    oauth_client_id: str | None
    oauth_client_secret: str | None
    oauth_refresh_token: str | None
    oauth_access_token: str | None
    subject_fallback: str
    only_review_approved: bool


@dataclass(slots=True)
class SemipilotConfig:
    openai_api_key: str
    model: str
    prompts_dir: Path
    output_dir: Path
    sender_name: str
    sender_company: str
    raw_evidence_path: Path | None
    search: SearchConfig
    gmail_drafts: GmailDraftConfig
    replies_path: Path | None
    run_reply_classification: bool
