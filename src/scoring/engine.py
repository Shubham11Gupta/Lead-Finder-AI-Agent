"""Scoring engine implementation for Step 18."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from .models import (
    SKIP_REASON_HARD_DISQUALIFIER,
    SKIP_REASON_MISSING_REQUIRED_FIELDS,
    SKIP_REASON_NO_REACHABLE_CHANNEL,
    SKIP_REASON_SAMPLING_NOT_FEASIBLE,
    ScoringRunResult,
)
from .rules import (
    compute_penalties,
    has_direct_reachable_channel,
    score_icp_fit,
    score_need_intent,
    score_operational_feasibility,
    score_reachability,
)


REQUIRED_SCORING_FIELDS = {
    "lead_id",
    "brand_name",
    "category",
    "stage",
    "region",
    "contact_channels_available",
    "email_validity_signal",
    "contact_form_status",
    "ugc_review_depth_signal",
    "paid_ads_signal",
    "public_review_request_signal",
    "new_digital_presence_signal",
    "social_presence_signal",
    "sampling_feasibility",
    "shipping_capability",
    "margin_viability_signal",
}


class ScoringEngine:
    """Deterministic scoring engine aligned to docs/lead-scoring-spec.md."""

    def run(
        self,
        leads: list[dict[str, Any]],
        *,
        run_context: Mapping[str, Any] | None = None,
    ) -> ScoringRunResult:
        run_context = run_context or {}
        run_id = _resolve_run_id(run_context)
        now_iso = datetime.now(tz=timezone.utc).isoformat()

        scored_leads: list[dict[str, Any]] = []
        skipped_scoring: list[dict[str, Any]] = []

        for lead in leads:
            lead_copy = deepcopy(lead)
            hard_skip_reason, skip_metadata = _hard_skip_reason(lead_copy)
            if hard_skip_reason:
                skipped_scoring.append(
                    {
                        "lead_id": lead_copy.get("lead_id"),
                        "reason": hard_skip_reason,
                        **skip_metadata,
                    }
                )
                continue

            icp = score_icp_fit(lead_copy)
            need = score_need_intent(lead_copy)
            feas = score_operational_feasibility(lead_copy)
            reach = score_reachability(lead_copy)

            base_score = icp.value + need.value + feas.value + reach.value
            penalty_total, penalties_applied = compute_penalties(lead_copy)
            final_score = max(0, min(100, base_score - penalty_total))
            priority_bucket = _priority_bucket(final_score)

            reasons = [*icp.reasons, *need.reasons, *feas.reasons, *reach.reasons]
            reason_log = _reason_log(
                final_score=final_score,
                icp=icp.value,
                need=need.value,
                feas=feas.value,
                reach=reach.value,
                penalty_total=penalty_total,
                priority_bucket=priority_bucket,
                reasons=reasons,
                penalties=penalties_applied,
            )

            lead_copy["icp_fit_score"] = icp.value
            lead_copy["need_intent_score"] = need.value
            lead_copy["operational_feasibility_score"] = feas.value
            lead_copy["reachability_score"] = reach.value
            lead_copy["penalties_applied"] = penalties_applied
            lead_copy["final_score"] = int(final_score)
            lead_copy["priority_bucket"] = priority_bucket
            lead_copy["scored_at"] = now_iso
            lead_copy["score_reason_log"] = reason_log
            lead_copy["scoring_reason_tags"] = reasons

            scored_leads.append(lead_copy)

        run_summary = _build_run_summary(
            input_count=len(leads),
            scored_leads=scored_leads,
            skipped_scoring=skipped_scoring,
        )

        return ScoringRunResult(
            run_id=run_id,
            scored_leads=scored_leads,
            skipped_scoring=skipped_scoring,
            scoring_run_summary=run_summary,
        )


def _hard_skip_reason(lead: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    missing_fields = sorted(field for field in REQUIRED_SCORING_FIELDS if field not in lead)
    if missing_fields:
        return SKIP_REASON_MISSING_REQUIRED_FIELDS, {"missing_fields": missing_fields}

    sampling_feasibility = _norm_text(lead.get("sampling_feasibility"))
    if sampling_feasibility == "no":
        return SKIP_REASON_SAMPLING_NOT_FEASIBLE, {}

    if lead.get("hard_disqualifier_match") is True:
        return SKIP_REASON_HARD_DISQUALIFIER, {}

    if not has_direct_reachable_channel(lead):
        return SKIP_REASON_NO_REACHABLE_CHANNEL, {}

    return None, {}


def _priority_bucket(final_score: float) -> str:
    if final_score >= 60:
        return "A"
    if final_score >= 30:
        return "B"
    return "skip"


def _reason_log(
    *,
    final_score: float,
    icp: int,
    need: int,
    feas: int,
    reach: int,
    penalty_total: int,
    priority_bucket: str,
    reasons: list[str],
    penalties: list[str],
) -> str:
    reasons_render = ",".join(reasons)
    penalties_render = ",".join(penalties)
    return (
        f"final={int(final_score)} | "
        f"icp={icp} need={need} feas={feas} reach={reach} | "
        f"penalties={penalty_total} ({penalties_render}) | "
        f"bucket={priority_bucket} | "
        f"reasons=[{reasons_render}]"
    )


def _build_run_summary(
    *,
    input_count: int,
    scored_leads: list[dict[str, Any]],
    skipped_scoring: list[dict[str, Any]],
) -> dict[str, Any]:
    bucket_counter = Counter()
    penalty_counter = Counter()
    skip_counter = Counter()
    total_final = 0

    for lead in scored_leads:
        bucket = lead.get("priority_bucket")
        if isinstance(bucket, str):
            bucket_counter[bucket] += 1
        total_final += int(lead.get("final_score", 0))

        penalties = lead.get("penalties_applied")
        if isinstance(penalties, list):
            for penalty in penalties:
                if isinstance(penalty, str):
                    penalty_counter[penalty] += 1

    for item in skipped_scoring:
        reason = item.get("reason")
        if isinstance(reason, str):
            skip_counter[reason] += 1

    scored_count = len(scored_leads)
    hard_skipped_count = len(skipped_scoring)
    avg_final = (total_final / scored_count) if scored_count else 0.0
    return {
        "input_count": input_count,
        "scored_count": scored_count,
        "hard_skipped_count": hard_skipped_count,
        "average_final_score": round(avg_final, 2),
        "bucket_counts": dict(bucket_counter),
        "skip_reasons": dict(skip_counter),
        "penalty_counts": dict(penalty_counter),
    }


def _resolve_run_id(run_context: Mapping[str, Any]) -> str:
    raw = run_context.get("score_run_id") or run_context.get("run_id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"score_run_{stamp}"


def _norm_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip().lower()
    return stripped or None

