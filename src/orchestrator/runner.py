"""One-command automated pipeline runner."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from src.analytics import build_daily_metrics_snapshot
from src.collection.pipeline import CollectionPipeline
from src.connectors import InstagramFileConnector, SerperConnector, SourceConnector
from src.outreach.engine import OutreachDraftEngine
from src.reply import process_replies
from src.review import review_draft_queue
from src.scoring.engine import ScoringEngine
from src.sender import GmailDraftSender, SmtpEmailSender
from src.shared.json_io import read_json_file, write_json_file
from src.suppression import is_lead_suppressed, load_suppression_registry, save_suppression_registry


EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")


@dataclass(slots=True)
class PipelinePaths:
    run_dir: Path
    collection_json: Path
    scoring_json: Path
    outreach_json: Path
    review_json: Path
    dispatch_log_json: Path
    reply_log_json: Path
    handoff_queue_json: Path
    suppression_snapshot_json: Path
    metrics_snapshot_json: Path
    final_summary_json: Path


def run_pipeline(config_path: str | Path) -> dict[str, Any]:
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    run_id = _run_id()
    paths = _build_paths(config=config, run_id=run_id)
    paths.run_dir.mkdir(parents=True, exist_ok=True)

    connectors = _build_connectors(config)
    collection = CollectionPipeline(connectors=connectors).run(
        run_context={
            "run_id": run_id,
            "default_region": config.get("default_region", "India"),
            "serper_queries": config.get("sources", {}).get("serper_queries", []),
            "serper_gl": config.get("sources", {}).get("serper_gl", "in"),
            "serper_hl": config.get("sources", {}).get("serper_hl", "en"),
            "serper_num": config.get("sources", {}).get("serper_num", 10),
            "serper_api_key": config.get("sources", {}).get("serper_api_key"),
            "instagram_input_path": config.get("sources", {}).get("instagram_input_path"),
        },
        existing_leads=[],
    )
    collection_dict = collection.to_dict()
    write_json_file(paths.collection_json, collection_dict)

    enriched = _enrich_emails(collection.qualified_leads_ready_for_scoring, timeout_seconds=12)
    scoring = ScoringEngine().run(enriched, run_context={"run_id": run_id})
    scoring_dict = scoring.to_dict()
    write_json_file(paths.scoring_json, scoring_dict)

    outreach = OutreachDraftEngine().run(
        scoring.scored_leads,
        run_context={
            "run_id": run_id,
            "sender_name": config.get("outreach", {}).get("sender_name", "Trio&Buy Team"),
            "sender_company": config.get("outreach", {}).get("sender_company", "Trio&Buy"),
        },
    )
    outreach_dict = outreach.to_dict()
    write_json_file(paths.outreach_json, outreach_dict)

    lead_by_id = {str(item.get("lead_id")): item for item in scoring.scored_leads}
    review_result = review_draft_queue(draft_queue=outreach.draft_queue, lead_by_id=lead_by_id)
    write_json_file(paths.review_json, review_result)

    suppression_file = config.get("suppression_file", "data/suppression_list.json")
    suppression_registry = load_suppression_registry(suppression_file)

    dispatch_log = _dispatch_approved_drafts(
        review_result=review_result,
        lead_by_id=lead_by_id,
        config=config,
        suppression_registry=suppression_registry,
    )
    write_json_file(paths.dispatch_log_json, dispatch_log)

    replies = _load_reply_intake(config)
    outbound_by_lead_id = _outbound_index(dispatch_log.get("events", []), review_result.get("approved_drafts", []))
    reply_result = process_replies(
        replies=replies,
        lead_by_id=lead_by_id,
        outbound_by_lead_id=outbound_by_lead_id,
        suppression_registry=suppression_registry,
    )
    suppression_registry = reply_result.suppression_registry
    save_suppression_registry(suppression_file, suppression_registry)

    write_json_file(paths.reply_log_json, {"reply_log": reply_result.reply_log, "summary": reply_result.summary})
    write_json_file(paths.handoff_queue_json, {"manual_handoff_queue": reply_result.manual_handoff_queue})
    write_json_file(paths.suppression_snapshot_json, suppression_registry)

    metrics = build_daily_metrics_snapshot(
        collection_result=collection_dict,
        scoring_result=scoring_dict,
        outreach_result=outreach_dict,
        review_result=review_result,
        dispatch_log=dispatch_log,
        reply_result={"reply_log": reply_result.reply_log, "summary": reply_result.summary},
    )
    write_json_file(paths.metrics_snapshot_json, metrics)

    summary = {
        "run_id": run_id,
        "collection_summary": collection.run_summary,
        "scoring_summary": scoring.scoring_run_summary,
        "outreach_summary": outreach.outreach_run_summary,
        "review_summary": review_result.get("review_summary", {}),
        "dispatch_summary": dispatch_log.get("summary", {}),
        "reply_summary": reply_result.summary,
        "metrics_snapshot": metrics,
        "paths": {
            "run_dir": str(paths.run_dir),
            "collection_json": str(paths.collection_json),
            "scoring_json": str(paths.scoring_json),
            "outreach_json": str(paths.outreach_json),
            "review_json": str(paths.review_json),
            "dispatch_log_json": str(paths.dispatch_log_json),
            "reply_log_json": str(paths.reply_log_json),
            "handoff_queue_json": str(paths.handoff_queue_json),
            "suppression_snapshot_json": str(paths.suppression_snapshot_json),
            "metrics_snapshot_json": str(paths.metrics_snapshot_json),
        },
    }
    write_json_file(paths.final_summary_json, summary)
    return summary


def _build_connectors(config: dict[str, Any]) -> list[SourceConnector]:
    sources = config.get("sources", {})
    connectors: list[SourceConnector] = []

    if bool(sources.get("serper_enabled", True)):
        connectors.append(SerperConnector(api_key=sources.get("serper_api_key")))
    instagram_input_path = sources.get("instagram_input_path")
    if isinstance(instagram_input_path, str) and instagram_input_path.strip():
        connectors.append(InstagramFileConnector(instagram_input_path))

    if not connectors:
        raise ValueError("No connectors enabled. Configure Serper and/or Instagram file connector.")
    return connectors


def _build_paths(*, config: dict[str, Any], run_id: str) -> PipelinePaths:
    root = Path(config.get("run_output_dir", "runs"))
    run_dir = root / run_id
    return PipelinePaths(
        run_dir=run_dir,
        collection_json=run_dir / "01_collection_output.json",
        scoring_json=run_dir / "02_scoring_output.json",
        outreach_json=run_dir / "03_outreach_output.json",
        review_json=run_dir / "04_review_output.json",
        dispatch_log_json=run_dir / "05_dispatch_log.json",
        reply_log_json=run_dir / "06_reply_log.json",
        handoff_queue_json=run_dir / "07_manual_handoff_queue.json",
        suppression_snapshot_json=run_dir / "08_suppression_snapshot.json",
        metrics_snapshot_json=run_dir / "09_daily_metrics_snapshot.json",
        final_summary_json=run_dir / "10_run_summary.json",
    )


def _run_id() -> str:
    return datetime.now(tz=timezone.utc).strftime("run_%Y%m%d_%H%M%S")


def _enrich_emails(leads: list[dict[str, Any]], *, timeout_seconds: int) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for lead in leads:
        lead_copy = dict(lead)
        email = _norm(lead_copy.get("founder_or_growth_email"))
        if not email:
            candidate = _discover_email_from_urls(lead_copy, timeout_seconds=timeout_seconds)
            if candidate:
                lead_copy["founder_or_growth_email"] = candidate
                lead_copy["email_validity_signal"] = "valid"
                channels = lead_copy.get("contact_channels_available")
                if isinstance(channels, list) and "email" not in channels:
                    channels.append("email")
        enriched.append(lead_copy)
    return enriched


def _discover_email_from_urls(lead: dict[str, Any], *, timeout_seconds: int) -> str | None:
    urls: list[str] = []
    primary = lead.get("primary_profile_url")
    website = lead.get("website_url")
    if isinstance(primary, str) and primary.strip():
        urls.append(primary.strip())
    if isinstance(website, str) and website.strip() and website.strip() not in urls:
        urls.append(website.strip())
    source_urls = lead.get("source_urls")
    if isinstance(source_urls, list):
        for value in source_urls:
            if isinstance(value, str) and value.strip() and value.strip() not in urls:
                urls.append(value.strip())

    for url in urls[:3]:
        body = _fetch_text(url, timeout_seconds=timeout_seconds)
        if not body:
            continue
        match = EMAIL_PATTERN.search(body)
        if match:
            email = match.group(1).lower()
            if not email.endswith((".png", ".jpg", ".jpeg")):
                return email
    return None


def _fetch_text(url: str, *, timeout_seconds: int) -> str | None:
    try:
        req = Request(url=url, headers={"User-Agent": "LeadFinderAgent/1.0"})
        with urlopen(req, timeout=timeout_seconds) as response:  # nosec - public URLs discovered from search
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text" not in content_type and "json" not in content_type and "html" not in content_type:
                return None
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def _dispatch_approved_drafts(
    *,
    review_result: dict[str, Any],
    lead_by_id: dict[str, dict[str, Any]],
    config: dict[str, Any],
    suppression_registry: dict[str, Any],
) -> dict[str, Any]:
    approved_drafts = review_result.get("approved_drafts", [])
    if not isinstance(approved_drafts, list):
        approved_drafts = []

    delivery_cfg = config.get("delivery", {})
    mode = str(delivery_cfg.get("mode", "none"))
    history_path = Path(str(config.get("outreach_history_file", "data/outreach_messages_log.json")))
    history = read_json_file(history_path, default={"events": []})
    history_events = history.get("events", []) if isinstance(history, dict) else []
    if not isinstance(history_events, list):
        history_events = []

    smtp_sender = _build_smtp_sender(config) if mode == "smtp_send" else None
    gmail_sender = _build_gmail_draft_sender(config) if mode == "gmail_draft" else None
    if mode == "smtp_send" and smtp_sender is None:
        mode = "none"
    if mode == "gmail_draft" and gmail_sender is None:
        mode = "none"

    events: list[dict[str, Any]] = []
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    manual_queue_count = 0

    for draft in approved_drafts:
        if not isinstance(draft, dict):
            continue
        lead_id = str(draft.get("lead_id"))
        channel = str(draft.get("channel_selected", "email"))
        lead = lead_by_id.get(lead_id, {})
        duplicate_key = _idempotency_key(lead_id=lead_id, channel=channel, body=str(draft.get("message_draft", "")))
        if _already_dispatched(history_events, duplicate_key):
            events.append(
                {
                    "lead_id": lead_id,
                    "channel_selected": channel,
                    "status": "skipped",
                    "reason": "duplicate_dispatch",
                    "idempotency_key": duplicate_key,
                }
            )
            skipped_count += 1
            continue
        if _already_contacted_today(history_events, lead_id):
            events.append(
                {
                    "lead_id": lead_id,
                    "channel_selected": channel,
                    "status": "skipped",
                    "reason": "same_day_contact_block",
                    "idempotency_key": duplicate_key,
                }
            )
            skipped_count += 1
            continue

        suppressed, suppressed_by = is_lead_suppressed(lead, suppression_registry)
        if suppressed:
            events.append(
                {
                    "lead_id": lead_id,
                    "channel_selected": channel,
                    "status": "suppressed",
                    "reason": f"suppressed_by_{suppressed_by}",
                    "recipient": _best_recipient(lead, channel),
                    "idempotency_key": duplicate_key,
                }
            )
            skipped_count += 1
            continue

        subject = _norm(draft.get("message_subject")) or str(
            config.get("send", {}).get("default_subject", "Quick idea for your brand")
        )
        body = str(draft.get("message_draft", ""))

        if channel != "email":
            events.append(
                {
                    "lead_id": lead_id,
                    "channel_selected": channel,
                    "status": "manual_channel_queue",
                    "reason": "adapter_not_configured",
                    "recipient": _best_recipient(lead, channel),
                    "message_subject": subject,
                    "message_draft": body,
                    "created_at": datetime.now(tz=timezone.utc).isoformat(),
                    "idempotency_key": duplicate_key,
                }
            )
            manual_queue_count += 1
            continue

        to_email = _norm(lead.get("founder_or_growth_email"))
        if not to_email:
            events.append(
                {
                    "lead_id": lead_id,
                    "channel_selected": channel,
                    "status": "skipped",
                    "reason": "missing_email",
                    "idempotency_key": duplicate_key,
                }
            )
            skipped_count += 1
            continue

        if mode == "none":
            events.append(
                {
                    "lead_id": lead_id,
                    "channel_selected": channel,
                    "status": "queued_not_dispatched",
                    "recipient": to_email,
                    "message_subject": subject,
                    "message_draft": body,
                    "created_at": datetime.now(tz=timezone.utc).isoformat(),
                    "idempotency_key": duplicate_key,
                }
            )
            skipped_count += 1
            continue

        if mode == "smtp_send" and smtp_sender is not None:
            result = smtp_sender.send(lead_id=lead_id, to_email=to_email, subject=subject, body=body).to_dict()
            result["channel_selected"] = channel
            result["idempotency_key"] = duplicate_key
            events.append(result)
            if result.get("status") == "sent":
                sent_count += 1
            else:
                failed_count += 1
            continue

        if mode == "gmail_draft" and gmail_sender is not None:
            result = gmail_sender.create_draft(
                lead_id=lead_id,
                to_email=to_email,
                subject=subject,
                body=body,
                from_email=_norm(config.get("send", {}).get("from_email")),
            ).to_dict()
            result["channel_selected"] = channel
            result["idempotency_key"] = duplicate_key
            result["created_at"] = datetime.now(tz=timezone.utc).isoformat()
            events.append(result)
            if result.get("status") == "draft_created":
                sent_count += 1
            else:
                failed_count += 1
            continue

        events.append(
            {
                "lead_id": lead_id,
                "channel_selected": channel,
                "status": "failed",
                "reason": f"unsupported_delivery_mode_{mode}",
                "idempotency_key": duplicate_key,
            }
        )
        failed_count += 1

    combined_history = history_events + events
    write_json_file(history_path, {"events": combined_history})
    return {
        "events": events,
        "summary": {
            "mode": mode,
            "input_count": len(approved_drafts),
            "sent_or_drafted_count": sent_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "manual_channel_queue_count": manual_queue_count,
        },
    }


def _build_smtp_sender(config: dict[str, Any]) -> SmtpEmailSender | None:
    send_cfg = config.get("send", {})
    required = ("smtp_host", "smtp_port", "smtp_username", "smtp_password", "from_email")
    if not all(key in send_cfg and str(send_cfg[key]).strip() for key in required):
        return None
    return SmtpEmailSender(
        host=str(send_cfg["smtp_host"]),
        port=int(send_cfg["smtp_port"]),
        username=str(send_cfg["smtp_username"]),
        password=str(send_cfg["smtp_password"]),
        from_email=str(send_cfg["from_email"]),
        from_name=str(send_cfg.get("from_name", "Trio&Buy Team")),
        use_starttls=bool(send_cfg.get("use_starttls", True)),
        use_ssl=bool(send_cfg.get("use_ssl", False)),
    )


def _build_gmail_draft_sender(config: dict[str, Any]) -> GmailDraftSender | None:
    gmail_cfg = config.get("gmail_drafts", {})
    enabled = bool(gmail_cfg.get("enabled", False))
    if not enabled:
        return None
    return GmailDraftSender(
        user_id=str(gmail_cfg.get("user_id", "me")),
        oauth_client_id=_norm(gmail_cfg.get("oauth_client_id")),
        oauth_client_secret=_norm(gmail_cfg.get("oauth_client_secret")),
        oauth_refresh_token=_norm(gmail_cfg.get("oauth_refresh_token")),
        oauth_access_token=_norm(gmail_cfg.get("oauth_access_token")),
    )


def _idempotency_key(*, lead_id: str, channel: str, body: str) -> str:
    seed = f"{lead_id}|{channel}|{body.strip()}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return digest


def _already_dispatched(history_events: list[dict[str, Any]], key: str) -> bool:
    for event in history_events:
        if not isinstance(event, dict):
            continue
        if str(event.get("idempotency_key")) == key and str(event.get("status")) in {
            "sent",
            "draft_created",
            "queued_not_dispatched",
            "manual_channel_queue",
        }:
            return True
    return False


def _already_contacted_today(history_events: list[dict[str, Any]], lead_id: str) -> bool:
    today = datetime.now(tz=timezone.utc).date().isoformat()
    for event in history_events:
        if not isinstance(event, dict):
            continue
        if str(event.get("lead_id")) != lead_id:
            continue
        ts = _norm(event.get("sent_at")) or _norm(event.get("created_at"))
        if not ts:
            continue
        if ts[:10] == today and str(event.get("status")) in {
            "sent",
            "draft_created",
            "queued_not_dispatched",
            "manual_channel_queue",
        }:
            return True
    return False


def _load_reply_intake(config: dict[str, Any]) -> list[dict[str, Any]]:
    path_value = config.get("reply_intake_file")
    if isinstance(path_value, str) and path_value.strip():
        path = Path(path_value)
        if path.exists():
            payload = read_json_file(path, default=[])
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
    inline = config.get("inbound_replies", [])
    if isinstance(inline, list):
        return [item for item in inline if isinstance(item, dict)]
    return []


def _outbound_index(events: list[dict[str, Any]], approved_drafts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_lead: dict[str, dict[str, Any]] = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        lead_id = event.get("lead_id")
        if isinstance(lead_id, str):
            by_lead[lead_id] = event
    for draft in approved_drafts:
        if not isinstance(draft, dict):
            continue
        lead_id = draft.get("lead_id")
        if isinstance(lead_id, str) and lead_id not in by_lead:
            by_lead[lead_id] = draft
    return by_lead


def _best_recipient(lead: dict[str, Any], channel: str) -> str:
    if channel == "email":
        return _norm(lead.get("founder_or_growth_email")) or ""
    if channel == "instagram_dm":
        return _norm(lead.get("instagram_handle")) or ""
    if channel == "whatsapp":
        return _norm(lead.get("whatsapp_business_link_or_number")) or ""
    return ""


def _norm(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None
