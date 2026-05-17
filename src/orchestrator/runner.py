"""One-command automated pipeline runner."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from src.collection.pipeline import CollectionPipeline
from src.connectors import InstagramFileConnector, SerperConnector, SourceConnector
from src.outreach.engine import OutreachDraftEngine
from src.reply import classify_reply
from src.scoring.engine import ScoringEngine
from src.sender import SmtpEmailSender
from src.shared.json_io import read_json_file, write_json_file


EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")


@dataclass(slots=True)
class PipelinePaths:
    run_dir: Path
    collection_json: Path
    scoring_json: Path
    outreach_json: Path
    send_results_json: Path
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
    write_json_file(paths.collection_json, collection.to_dict())

    enriched = _enrich_emails(collection.qualified_leads_ready_for_scoring, timeout_seconds=12)
    scoring = ScoringEngine().run(enriched, run_context={"run_id": run_id})
    write_json_file(paths.scoring_json, scoring.to_dict())

    outreach = OutreachDraftEngine().run(
        scoring.scored_leads,
        run_context={
            "run_id": run_id,
            "sender_name": config.get("outreach", {}).get("sender_name", "Trio&Buy Team"),
            "sender_company": config.get("outreach", {}).get("sender_company", "Trio&Buy"),
        },
    )
    write_json_file(paths.outreach_json, outreach.to_dict())

    send_results = _auto_send_email_drafts(
        drafts=outreach.draft_queue,
        leads=scoring.scored_leads,
        config=config,
    )
    write_json_file(paths.send_results_json, {"run_id": run_id, "results": send_results})

    reply_samples = config.get("inbound_replies", [])
    classified_replies = _classify_inbound_replies(reply_samples)

    summary = {
        "run_id": run_id,
        "collection_summary": collection.run_summary,
        "scoring_summary": scoring.scoring_run_summary,
        "outreach_summary": outreach.outreach_run_summary,
        "send_summary": _send_summary(send_results),
        "reply_classification_count": len(classified_replies),
        "paths": {
            "run_dir": str(paths.run_dir),
            "collection_json": str(paths.collection_json),
            "scoring_json": str(paths.scoring_json),
            "outreach_json": str(paths.outreach_json),
            "send_results_json": str(paths.send_results_json),
        },
    }
    write_json_file(paths.final_summary_json, summary)
    return summary


def _build_connectors(config: dict[str, Any]) -> list[SourceConnector]:
    sources = config.get("sources", {})
    connectors: list[SourceConnector] = []
    if bool(sources.get("serper_enabled", True)):
        connectors.append(
            SerperConnector(
                api_key=sources.get("serper_api_key"),
            )
        )
    instagram_input_path = sources.get("instagram_input_path")
    if isinstance(instagram_input_path, str) and instagram_input_path.strip():
        connectors.append(InstagramFileConnector(instagram_input_path))
    if not connectors:
        raise ValueError("No connectors enabled. Configure at least one source connector.")
    return connectors


def _build_paths(*, config: dict[str, Any], run_id: str) -> PipelinePaths:
    root = Path(config.get("run_output_dir", "runs"))
    run_dir = root / run_id
    return PipelinePaths(
        run_dir=run_dir,
        collection_json=run_dir / "01_collection_output.json",
        scoring_json=run_dir / "02_scoring_output.json",
        outreach_json=run_dir / "03_outreach_output.json",
        send_results_json=run_dir / "04_send_results.json",
        final_summary_json=run_dir / "05_run_summary.json",
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
        with urlopen(req, timeout=timeout_seconds) as response:  # nosec - user configured public URLs
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text" not in content_type and "json" not in content_type and "html" not in content_type:
                return None
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def _auto_send_email_drafts(
    *,
    drafts: list[dict[str, Any]],
    leads: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    send_cfg = config.get("send", {})
    if not bool(send_cfg.get("enabled", False)):
        return []

    sender = SmtpEmailSender(
        host=str(send_cfg["smtp_host"]),
        port=int(send_cfg["smtp_port"]),
        username=str(send_cfg["smtp_username"]),
        password=str(send_cfg["smtp_password"]),
        from_email=str(send_cfg["from_email"]),
        from_name=str(send_cfg.get("from_name", "Trio&Buy Team")),
        use_starttls=bool(send_cfg.get("use_starttls", True)),
        use_ssl=bool(send_cfg.get("use_ssl", False)),
    )
    lead_by_id = {str(item.get("lead_id")): item for item in leads}
    suppression = set(_load_suppression_list(config))
    send_results: list[dict[str, Any]] = []

    for draft in drafts:
        if draft.get("channel_selected") != "email":
            continue
        lead_id = str(draft.get("lead_id"))
        lead = lead_by_id.get(lead_id, {})
        to_email = _norm(lead.get("founder_or_growth_email"))
        if not to_email:
            send_results.append({"lead_id": lead_id, "status": "skipped", "reason": "missing_email"})
            continue
        if to_email in suppression:
            send_results.append({"lead_id": lead_id, "status": "skipped", "reason": "suppressed"})
            continue
        subject = _norm(draft.get("message_subject")) or str(send_cfg.get("default_subject", "Quick idea for your brand"))
        body = str(draft.get("message_draft") or "")
        result = sender.send(lead_id=lead_id, to_email=to_email, subject=subject, body=body)
        send_results.append(result.to_dict())
    return send_results


def _load_suppression_list(config: dict[str, Any]) -> list[str]:
    raw_path = config.get("suppression_file", "data/suppression_list.json")
    data = read_json_file(Path(raw_path), default={"suppressed_emails": []})
    items = data.get("suppressed_emails", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        return []
    return [item.strip().lower() for item in items if isinstance(item, str) and item.strip()]


def _classify_inbound_replies(reply_samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in reply_samples:
        if not isinstance(item, dict):
            continue
        lead_id = str(item.get("lead_id", "unknown_lead"))
        reply_text = str(item.get("reply_text", ""))
        results.append(classify_reply(lead_id=lead_id, reply_text=reply_text))
    return results


def _send_summary(send_results: list[dict[str, Any]]) -> dict[str, int]:
    sent = 0
    failed = 0
    skipped = 0
    for item in send_results:
        status = item.get("status")
        if status == "sent":
            sent += 1
        elif status == "failed":
            failed += 1
        else:
            skipped += 1
    return {"sent": sent, "failed": failed, "skipped": skipped}


def _norm(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None

