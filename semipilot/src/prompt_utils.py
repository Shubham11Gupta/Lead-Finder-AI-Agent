"""Prompt loading and JSON extraction helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_json_from_text(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = _strip_fences(raw)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start : end + 1]
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Model output was not valid JSON object.")


def _strip_fences(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()

