"""Collection data structures and constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SKIP_REASON_DUPLICATE_MERGED = "duplicate_merged"
SKIP_REASON_NON_CONSUMABLE = "non_consumable_category"
SKIP_REASON_NO_REACHABLE_CHANNEL = "no_reachable_channel"
SKIP_REASON_HARD_DISQUALIFIER = "hard_disqualifier_match"
SKIP_REASON_INSUFFICIENT_EVIDENCE = "insufficient_evidence"
SKIP_REASON_SAMPLING_NOT_FEASIBLE = "sampling_not_feasible"
SKIP_REASON_INVALID_SCHEMA = "invalid_schema"


@dataclass(slots=True)
class CollectionRunResult:
    run_id: str
    raw_discovered_leads: list[dict[str, Any]] = field(default_factory=list)
    qualified_leads_ready_for_scoring: list[dict[str, Any]] = field(default_factory=list)
    skipped_leads: list[dict[str, Any]] = field(default_factory=list)
    run_summary: dict[str, Any] = field(default_factory=dict)
    source_errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "raw_discovered_leads": self.raw_discovered_leads,
            "qualified_leads_ready_for_scoring": self.qualified_leads_ready_for_scoring,
            "skipped_leads": self.skipped_leads,
            "run_summary": self.run_summary,
            "source_errors": self.source_errors,
        }

