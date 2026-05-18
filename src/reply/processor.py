"""Reply intake processing: classify, route, and update suppression."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.suppression import add_opt_out_to_suppression

from .classifier import classify_reply


@dataclass(slots=True)
class ReplyProcessingResult:
    reply_log: list[dict[str, Any]] = field(default_factory=list)
    manual_handoff_queue: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    suppression_registry: dict[str, Any] = field(default_factory=dict)


def process_replies(
    *,
    replies: list[dict[str, Any]],
    lead_by_id: dict[str, dict[str, Any]],
    outbound_by_lead_id: dict[str, dict[str, Any]],
    suppression_registry: dict[str, Any],
) -> ReplyProcessingResult:
    reply_log: list[dict[str, Any]] = []
    handoff_queue: list[dict[str, Any]] = []
    counter: dict[str, int] = {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "not_relevant": 0,
        "opt_out": 0,
        "unclear": 0,
    }

    for item in replies:
        if not isinstance(item, dict):
            continue
        lead_id = str(item.get("lead_id", "unknown_lead"))
        reply_text = str(item.get("reply_text", ""))
        channel = str(item.get("channel_selected", "email"))
        received_at = str(item.get("reply_received_at", datetime.now(tz=timezone.utc).isoformat()))

        classified = classify_reply(lead_id=lead_id, reply_text=reply_text)
        reply_type = str(classified.get("reply_type"))
        counter[reply_type] = counter.get(reply_type, 0) + 1

        action_taken, action_owner, response_status, outreach_status = _map_action(reply_type)
        do_not_contact = bool(classified.get("do_not_contact", False))

        lead = lead_by_id.get(lead_id, {})
        outbound = outbound_by_lead_id.get(lead_id, {})

        if reply_type == "opt_out":
            suppression_registry = add_opt_out_to_suppression(lead=lead, registry=suppression_registry)

        log_item = {
            "lead_id": lead_id,
            "channel_selected": channel,
            "reply_text": reply_text,
            "reply_received_at": received_at,
            "reply_type": reply_type,
            "classification_confidence": classified.get("classification_confidence", "low"),
            "action_taken": action_taken,
            "action_owner": action_owner,
            "response_status": response_status,
            "outreach_status": outreach_status,
            "do_not_contact": do_not_contact,
            "manual_task_id": None,
            "notes": classified.get("notes", "auto_classified"),
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        reply_log.append(log_item)

        if reply_type in {"positive", "neutral", "unclear"}:
            handoff_queue.append(
                {
                    "lead_id": lead_id,
                    "reply_type": reply_type,
                    "recommended_action": action_taken,
                    "brand_snapshot": {
                        "brand_name": lead.get("brand_name"),
                        "category": lead.get("category"),
                        "region": lead.get("region"),
                    },
                    "outbound_message": {
                        "channel_selected": outbound.get("channel_selected"),
                        "message_subject": outbound.get("message_subject"),
                        "message_draft": outbound.get("message_draft"),
                        "sent_at": outbound.get("sent_at") or outbound.get("created_at"),
                    },
                    "inbound_reply_text": reply_text,
                    "created_at": datetime.now(tz=timezone.utc).isoformat(),
                }
            )

    summary = {
        "total_replies": len(reply_log),
        "category_counts": counter,
        "manual_handoff_count": len(handoff_queue),
    }
    return ReplyProcessingResult(
        reply_log=reply_log,
        manual_handoff_queue=handoff_queue,
        summary=summary,
        suppression_registry=suppression_registry,
    )


def _map_action(reply_type: str) -> tuple[str, str, str, str]:
    if reply_type == "positive":
        return "handoff_required", "founder_team", "positive", "replied"
    if reply_type == "neutral":
        return "manual_reply_required", "founder_team", "neutral", "replied"
    if reply_type == "negative":
        return "closed_no_interest", "system", "negative", "closed"
    if reply_type == "not_relevant":
        return "closed_not_relevant", "system", "negative", "closed"
    if reply_type == "opt_out":
        return "suppressed", "system", "negative", "closed"
    return "manual_review_required", "founder_team", "none", "replied"

