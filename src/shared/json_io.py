"""Small JSON file helpers for pipeline persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json_file(path: Path, *, default: Any) -> Any:
    if not path.exists():
        return default
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw)


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

