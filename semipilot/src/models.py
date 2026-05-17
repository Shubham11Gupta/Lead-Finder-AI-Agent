"""Typed models for semipilot runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SemipilotConfig:
    openai_api_key: str
    model: str
    prompts_dir: Path
    output_dir: Path
    sender_name: str
    sender_company: str
    raw_evidence_path: Path
    replies_path: Path | None
    run_reply_classification: bool

