"""Outreach draft generation models and constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SKIP_REASON_NOT_PRIORITY_BUCKET = "not_priority_bucket"
SKIP_REASON_OUTREACH_ALREADY_STARTED = "outreach_already_started"
SKIP_REASON_NO_REACHABLE_CHANNEL = "no_reachable_channel"
SKIP_REASON_NO_TEMPLATE_MATCH = "no_template_match"


@dataclass(slots=True)
class OutreachRunResult:
    run_id: str
    draft_queue: list[dict[str, Any]] = field(default_factory=list)
    skipped_outreach: list[dict[str, Any]] = field(default_factory=list)
    outreach_run_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "draft_queue": self.draft_queue,
            "skipped_outreach": self.skipped_outreach,
            "outreach_run_summary": self.outreach_run_summary,
        }

