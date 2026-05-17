"""Config loading for semipilot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import SemipilotConfig


def load_config(config_path: str | Path) -> SemipilotConfig:
    path = Path(config_path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    api_key = _value(payload, "openai_api_key") or os.getenv("OPENAI_API_KEY", "")
    if not api_key.strip():
        raise ValueError("Missing OpenAI API key. Set `openai_api_key` in config or OPENAI_API_KEY.")

    prompts_dir = Path(_value(payload, "prompts_dir") or "docs/prompts")
    output_dir = Path(_value(payload, "output_dir") or "semipilot/runs")
    raw_evidence_path = Path(_value(payload, "raw_evidence_path") or "semipilot/input/raw_evidence.txt")

    replies_path_raw = _value(payload, "replies_path")
    replies_path = Path(replies_path_raw) if isinstance(replies_path_raw, str) and replies_path_raw.strip() else None

    return SemipilotConfig(
        openai_api_key=api_key.strip(),
        model=str(_value(payload, "model") or "gpt-5-mini"),
        prompts_dir=prompts_dir,
        output_dir=output_dir,
        sender_name=str(_value(payload, "sender_name") or "Trio&Buy Team"),
        sender_company=str(_value(payload, "sender_company") or "Trio&Buy"),
        raw_evidence_path=raw_evidence_path,
        replies_path=replies_path,
        run_reply_classification=bool(_value(payload, "run_reply_classification") or False),
    )


def _value(payload: dict[str, Any], key: str) -> Any:
    return payload.get(key)

