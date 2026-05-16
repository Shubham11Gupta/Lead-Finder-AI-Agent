"""Scoring data structures and constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SKIP_REASON_SAMPLING_NOT_FEASIBLE = "sampling_not_feasible"
SKIP_REASON_NO_REACHABLE_CHANNEL = "no_reachable_channel"
SKIP_REASON_HARD_DISQUALIFIER = "hard_disqualifier_match"
SKIP_REASON_MISSING_REQUIRED_FIELDS = "missing_required_scoring_fields"

PENALTY_NON_CONSUMABLE = "non_consumable"
PENALTY_VERY_LOW_MARGIN = "very_low_margin"
PENALTY_NO_SAMPLING_FEASIBILITY = "no_sampling_feasibility"


@dataclass(slots=True)
class SectionScore:
    value: int
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ScoringRunResult:
    run_id: str
    scored_leads: list[dict[str, Any]] = field(default_factory=list)
    skipped_scoring: list[dict[str, Any]] = field(default_factory=list)
    scoring_run_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scored_leads": self.scored_leads,
            "skipped_scoring": self.skipped_scoring,
            "scoring_run_summary": self.scoring_run_summary,
        }

