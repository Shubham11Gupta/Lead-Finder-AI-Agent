"""Outreach draft engine for first-touch messaging."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping

from .models import (
    SKIP_REASON_NO_REACHABLE_CHANNEL,
    SKIP_REASON_NO_TEMPLATE_MATCH,
    SKIP_REASON_NOT_PRIORITY_BUCKET,
    SKIP_REASON_OUTREACH_ALREADY_STARTED,
    OutreachRunResult,
)
from .selector import infer_persona, infer_primary_signal, select_channel, select_template
from .templates import render_template


class OutreachDraftEngine:
    """Generate first-touch outreach drafts from scored leads."""

    def run(
        self,
        leads: list[dict[str, Any]],
        *,
        run_context: Mapping[str, Any] | None = None,
    ) -> OutreachRunResult:
        run_context = run_context or {}
        run_id = _resolve_run_id(run_context)
        sender_name = str(run_context.get("sender_name", "Trio&Buy Team"))
        sender_company = str(run_context.get("sender_company", "Trio&Buy"))
        now_iso = datetime.now(tz=timezone.utc).isoformat()

        draft_queue: list[dict[str, Any]] = []
        skipped_outreach: list[dict[str, Any]] = []

        for lead in leads:
            lead_copy = deepcopy(lead)

            if str(lead_copy.get("priority_bucket")) not in {"A", "B"}:
                skipped_outreach.append(
                    {"lead_id": lead_copy.get("lead_id"), "reason": SKIP_REASON_NOT_PRIORITY_BUCKET}
                )
                continue

            if str(lead_copy.get("outreach_status")) != "not_started":
                skipped_outreach.append(
                    {"lead_id": lead_copy.get("lead_id"), "reason": SKIP_REASON_OUTREACH_ALREADY_STARTED}
                )
                continue

            channel = select_channel(lead_copy)
            if channel is None:
                skipped_outreach.append(
                    {"lead_id": lead_copy.get("lead_id"), "reason": SKIP_REASON_NO_REACHABLE_CHANNEL}
                )
                continue

            persona = infer_persona(lead_copy, channel)
            signal = infer_primary_signal(lead_copy)
            lead_copy["signal_observed"] = _signal_phrase(signal)

            template = select_template(persona=persona, channel=channel, signal=signal)
            if template is None:
                skipped_outreach.append(
                    {
                        "lead_id": lead_copy.get("lead_id"),
                        "reason": SKIP_REASON_NO_TEMPLATE_MATCH,
                        "persona": persona,
                        "channel": channel,
                        "signal": signal,
                    }
                )
                continue

            subject, message_draft = render_template(
                template,
                lead=lead_copy,
                sender_name=sender_name,
                sender_company=sender_company,
            )

            draft_queue.append(
                {
                    "lead_id": lead_copy.get("lead_id"),
                    "channel_selected": channel,
                    "message_subject": subject,
                    "message_draft": message_draft,
                    "personalization_reason": _personalization_reason(signal, lead_copy),
                    "review_status": "pending_review",
                    "send_status": "not_sent",
                    "sent_at": None,
                    "last_outreach_at": None,
                    "response_status": lead_copy.get("response_status", "none"),
                    "outreach_status": "draft_ready",
                    "template_id": template.template_id,
                    "persona_selected": persona,
                    "signal_selected": signal,
                    "generated_at": now_iso,
                }
            )

        summary = _build_summary(draft_queue=draft_queue, skipped_outreach=skipped_outreach)
        return OutreachRunResult(
            run_id=run_id,
            draft_queue=draft_queue,
            skipped_outreach=skipped_outreach,
            outreach_run_summary=summary,
        )


def _resolve_run_id(run_context: Mapping[str, Any]) -> str:
    raw = run_context.get("outreach_run_id") or run_context.get("run_id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"outreach_run_{stamp}"


def _signal_phrase(signal: str) -> str:
    mapping = {
        "new_launch": "recent launch momentum",
        "paid_ads": "active performance marketing",
        "low_ugc": "low verified review depth",
        "review_request": "public feedback requests",
        "sampling": "sampling-ready product flow",
        "generic": "current growth signals",
    }
    return mapping.get(signal, "current growth signals")


def _personalization_reason(signal: str, lead: dict[str, Any]) -> str:
    brand = lead.get("brand_name", "lead")
    return f"Selected signal '{signal}' for {brand} based on verified lead fields."


def _build_summary(*, draft_queue: list[dict[str, Any]], skipped_outreach: list[dict[str, Any]]) -> dict[str, Any]:
    channel_counter = Counter()
    template_counter = Counter()
    skip_counter = Counter()

    for draft in draft_queue:
        channel = draft.get("channel_selected")
        template = draft.get("template_id")
        if isinstance(channel, str):
            channel_counter[channel] += 1
        if isinstance(template, str):
            template_counter[template] += 1

    for item in skipped_outreach:
        reason = item.get("reason")
        if isinstance(reason, str):
            skip_counter[reason] += 1

    return {
        "input_count": len(draft_queue) + len(skipped_outreach),
        "draft_count": len(draft_queue),
        "skipped_count": len(skipped_outreach),
        "channels": dict(channel_counter),
        "templates": dict(template_counter),
        "skip_reasons": dict(skip_counter),
    }

