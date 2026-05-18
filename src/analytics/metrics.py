"""Daily metrics snapshot builder."""

from __future__ import annotations

from typing import Any


def build_daily_metrics_snapshot(
    *,
    collection_result: dict[str, Any],
    scoring_result: dict[str, Any],
    outreach_result: dict[str, Any],
    review_result: dict[str, Any],
    dispatch_log: dict[str, Any],
    reply_result: dict[str, Any],
) -> dict[str, Any]:
    discovered = int(collection_result.get("run_summary", {}).get("discovered_count", 0))
    qualified = int(collection_result.get("run_summary", {}).get("qualified_count", 0))

    scored_leads = scoring_result.get("scored_leads", [])
    scored_a = _count_where(scored_leads, "priority_bucket", "A")
    scored_b = _count_where(scored_leads, "priority_bucket", "B")

    draft_ready = len(outreach_result.get("draft_queue", []))
    approved = int(review_result.get("review_summary", {}).get("approved_count", 0))

    dispatch_events = dispatch_log.get("events", [])
    sent = _count_status(dispatch_events, {"sent", "draft_created"})
    replied = len(reply_result.get("reply_log", []))

    category_counts = reply_result.get("summary", {}).get("category_counts", {})
    positive_reply = int(category_counts.get("positive", 0))
    neutral_reply = int(category_counts.get("neutral", 0))
    negative_reply = int(category_counts.get("negative", 0)) + int(category_counts.get("not_relevant", 0))
    opt_out = int(category_counts.get("opt_out", 0))

    metrics = {
        "funnel_counts": {
            "discovered": discovered,
            "qualified": qualified,
            "scored_a": scored_a,
            "scored_b": scored_b,
            "draft_ready": draft_ready,
            "approved": approved,
            "sent": sent,
            "replied": replied,
            "positive_reply": positive_reply,
            "neutral_reply": neutral_reply,
            "negative_reply": negative_reply,
            "opt_out": opt_out,
        },
        "rates": {
            "qualification_rate": _safe_rate(qualified, discovered),
            "priority_a_rate": _safe_rate(scored_a, qualified),
            "priority_b_rate": _safe_rate(scored_b, qualified),
            "draft_rate": _safe_rate(draft_ready, scored_a + scored_b),
            "approval_rate": _safe_rate(approved, draft_ready),
            "send_rate": _safe_rate(sent, approved),
            "reply_rate": _safe_rate(replied, sent),
            "positive_reply_rate": _safe_rate(positive_reply, sent),
            "neutral_reply_rate": _safe_rate(neutral_reply, sent),
            "negative_reply_rate": _safe_rate(negative_reply, sent),
            "opt_out_rate": _safe_rate(opt_out, sent),
            "a_to_positive_rate": _safe_rate(positive_reply, scored_a),
        },
        "first_touch_constraints": {
            "auto_followup_count": 0,
            "messages_sent_after_opt_out": _messages_sent_after_opt_out(dispatch_events),
        },
        "channel_breakdown": _channel_breakdown(dispatch_events),
    }
    return metrics


def _safe_rate(num: int, den: int) -> float:
    if den <= 0:
        return 0.0
    return round(num / den, 4)


def _count_where(rows: list[Any], key: str, value: str) -> int:
    count = 0
    for row in rows:
        if isinstance(row, dict) and str(row.get(key)) == value:
            count += 1
    return count


def _count_status(events: list[Any], accepted: set[str]) -> int:
    count = 0
    for event in events:
        if isinstance(event, dict) and str(event.get("status")) in accepted:
            count += 1
    return count


def _messages_sent_after_opt_out(events: list[Any]) -> int:
    suppressed: set[str] = set()
    violations = 0
    for event in events:
        if not isinstance(event, dict):
            continue
        recipient = str(event.get("recipient", "")).strip().lower()
        status = str(event.get("status", "")).strip().lower()
        if status == "suppressed":
            if recipient:
                suppressed.add(recipient)
            continue
        if status in {"sent", "draft_created"} and recipient and recipient in suppressed:
            violations += 1
    return violations


def _channel_breakdown(events: list[Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        channel = str(event.get("channel_selected", "unknown"))
        out[channel] = out.get(channel, 0) + 1
    return out

