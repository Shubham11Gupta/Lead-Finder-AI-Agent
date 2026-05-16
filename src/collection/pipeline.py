"""Collection pipeline: discover -> normalize -> dedup -> qualify."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping

from src.connectors.base import RawLeadCandidate, SourceConnector
from src.schema import validate_lead_record

from .dedup import deduplicate_leads
from .models import CollectionRunResult, SKIP_REASON_INVALID_SCHEMA
from .normalizer import normalize_candidate
from .qualifier import filter_qualified_leads


class CollectionPipeline:
    """Phase 2 pipeline skeleton for collection workflow."""

    def __init__(self, connectors: list[SourceConnector]) -> None:
        self.connectors = connectors

    def run(
        self,
        *,
        run_context: Mapping[str, Any] | None = None,
        existing_leads: list[dict[str, Any]] | None = None,
    ) -> CollectionRunResult:
        run_context = run_context or {}
        run_id = _resolve_run_id(run_context)
        now = datetime.now(tz=timezone.utc)
        default_region = str(run_context.get("default_region", "India"))

        discovered_candidates: list[RawLeadCandidate] = []
        source_errors: list[dict[str, Any]] = []

        for connector in self.connectors:
            try:
                discovered_candidates.extend(connector.discover(run_context=run_context))
            except Exception as exc:  # pragma: no cover - defensive runtime behavior
                source_errors.append(
                    {
                        "source": getattr(connector, "name", connector.__class__.__name__),
                        "error": str(exc),
                    }
                )

        raw_discovered = [
            normalize_candidate(candidate, now=now, default_region=default_region) for candidate in discovered_candidates
        ]

        deduped, dedup_skips = deduplicate_leads(raw_discovered, existing_leads=existing_leads or [])
        qualified, qualification_skips = filter_qualified_leads(deduped)
        valid_qualified, schema_skips = _validate_qualified_leads(qualified)

        skipped_leads = [*dedup_skips, *qualification_skips, *schema_skips]
        run_summary = _build_run_summary(
            discovered_count=len(raw_discovered),
            deduped_unique_count=len(deduped),
            qualified_count=len(valid_qualified),
            skipped_leads=skipped_leads,
            source_errors=source_errors,
        )

        return CollectionRunResult(
            run_id=run_id,
            raw_discovered_leads=raw_discovered,
            qualified_leads_ready_for_scoring=valid_qualified,
            skipped_leads=skipped_leads,
            run_summary=run_summary,
            source_errors=source_errors,
        )


def _validate_qualified_leads(
    leads: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for lead in leads:
        result = validate_lead_record(lead)
        if result.is_valid:
            valid.append(result.normalized)
            continue
        skipped.append(
            {
                "lead_id": lead.get("lead_id"),
                "reason": SKIP_REASON_INVALID_SCHEMA,
                "issues": [issue.to_dict() for issue in result.issues],
            }
        )
    return valid, skipped


def _build_run_summary(
    *,
    discovered_count: int,
    deduped_unique_count: int,
    qualified_count: int,
    skipped_leads: list[dict[str, Any]],
    source_errors: list[dict[str, Any]],
) -> dict[str, Any]:
    reason_counter = Counter()
    for skip in skipped_leads:
        reason = skip.get("reason")
        if isinstance(reason, str):
            reason_counter[reason] += 1

    qualification_rate = (qualified_count / discovered_count) if discovered_count else 0.0
    return {
        "discovered_count": discovered_count,
        "deduped_unique_count": deduped_unique_count,
        "qualified_count": qualified_count,
        "skipped_count": len(skipped_leads),
        "qualification_rate": round(qualification_rate, 4),
        "skip_reasons": dict(reason_counter),
        "source_error_count": len(source_errors),
    }


def _resolve_run_id(run_context: Mapping[str, Any]) -> str:
    raw = run_context.get("run_id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"run_{stamp}"

