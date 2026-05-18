"""Prompt-first semipilot workflow automation."""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .gmail_drafts import GmailDraftClient
from .llm_client import OpenAIResponsesClient
from .models import SemipilotConfig
from .prompt_utils import load_prompt, parse_json_from_text
from .web_discovery import discover_web_evidence


def run_semipilot(config: SemipilotConfig) -> dict[str, Any]:
    run_id = datetime.now(tz=timezone.utc).strftime("semipilot_%Y%m%d_%H%M%S")
    run_dir = config.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    prompts = _load_prompt_pack(config.prompts_dir)
    client = OpenAIResponsesClient(api_key=config.openai_api_key, model=config.model)
    system_prompt = prompts["system"]

    search_report = _resolve_evidence(config)
    raw_evidence = search_report["raw_evidence_text"]
    _write_json(run_dir / "00_search_report.json", search_report)
    _write_text(run_dir / "00_raw_evidence.txt", raw_evidence)

    collection_input = _compose_collection_prompt(prompts["collection"], raw_evidence)
    collection_text = client.run(system_prompt=system_prompt, user_prompt=collection_input)
    collection_json = parse_json_from_text(collection_text)
    collection_json = _normalize_collection_leads(
        collection_json,
        source_name=str(search_report.get("search_provider")),
        domain_email_map=_domain_email_map_from_search_report(search_report),
    )
    _write_json(run_dir / "01_collection_output.json", collection_json)

    scoring_input = _compose_scoring_prompt(prompts["scoring"], collection_json)
    scoring_text = client.run(system_prompt=system_prompt, user_prompt=scoring_input)
    scoring_json = parse_json_from_text(scoring_text)
    scoring_json = _merge_collection_fields_into_scored(scoring_json, collection_json)
    _write_json(run_dir / "02_scoring_output.json", scoring_json)

    outreach_input = _compose_outreach_prompt(
        prompts["outreach"],
        scoring_json,
        sender_name=config.sender_name,
        sender_company=config.sender_company,
    )
    outreach_text = client.run(system_prompt=system_prompt, user_prompt=outreach_input)
    outreach_json = parse_json_from_text(outreach_text)
    _write_json(run_dir / "03_outreach_drafts.json", outreach_json)

    review_results = _run_review_gate(
        client=client,
        system_prompt=system_prompt,
        review_prompt=prompts["review"],
        outreach_json=outreach_json,
        evidence_json=collection_json,
    )
    _write_json(run_dir / "04_review_results.json", review_results)

    gmail_draft_results = _create_gmail_drafts_if_enabled(
        config=config,
        outreach_json=outreach_json,
        review_results=review_results,
        scored_json=scoring_json,
    )
    _write_json(run_dir / "05_gmail_draft_results.json", gmail_draft_results)

    reply_results: dict[str, Any] = {"reply_results": []}
    if config.run_reply_classification and config.replies_path and config.replies_path.exists():
        replies_json = json.loads(config.replies_path.read_text(encoding="utf-8"))
        reply_input = _compose_reply_prompt(prompts["reply"], replies_json)
        reply_text = client.run(system_prompt=system_prompt, user_prompt=reply_input)
        reply_results = parse_json_from_text(reply_text)
    _write_json(run_dir / "06_reply_results.json", reply_results)

    summary = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "search_provider": search_report.get("search_provider"),
        "search_hit_count": int(search_report.get("hit_count", 0)),
        "collection_count": len(collection_json.get("leads", [])),
        "scored_count": len(scoring_json.get("scored_leads", [])),
        "draft_count": len(outreach_json.get("draft_queue", [])),
        "review_count": len(review_results.get("reviews", [])),
        "gmail_draft_count": len(gmail_draft_results.get("results", [])),
        "reply_count": len(reply_results.get("reply_results", [])),
        "files": [
            "00_search_report.json",
            "00_raw_evidence.txt",
            "01_collection_output.json",
            "02_scoring_output.json",
            "03_outreach_drafts.json",
            "04_review_results.json",
            "05_gmail_draft_results.json",
            "06_reply_results.json",
        ],
    }
    _write_json(run_dir / "07_summary.json", summary)
    return summary


def _load_prompt_pack(prompts_dir: Path) -> dict[str, str]:
    return {
        "system": load_prompt(prompts_dir / "00_system_role_prompt.md"),
        "collection": load_prompt(prompts_dir / "01_collection_extraction_prompt.md"),
        "scoring": load_prompt(prompts_dir / "02_scoring_prompt.md"),
        "outreach": load_prompt(prompts_dir / "03_outreach_draft_prompt.md"),
        "review": load_prompt(prompts_dir / "04_review_gate_prompt.md"),
        "reply": load_prompt(prompts_dir / "05_reply_classification_prompt.md"),
    }


def _compose_collection_prompt(template: str, raw_evidence: str) -> str:
    return f"{template}\n\nINPUT_EVIDENCE:\n```text\n{raw_evidence}\n```"


def _compose_scoring_prompt(template: str, collection_json: dict[str, Any]) -> str:
    leads = collection_json.get("leads", [])
    leads_json = json.dumps(leads, indent=2, ensure_ascii=True)
    return f"{template}\n\nINPUT_LEADS_JSON:\n```json\n{leads_json}\n```"


def _compose_outreach_prompt(
    template: str,
    scoring_json: dict[str, Any],
    *,
    sender_name: str,
    sender_company: str,
) -> str:
    scored = scoring_json.get("scored_leads", [])
    input_payload = {
        "sender_name": sender_name,
        "sender_company": sender_company,
        "scored_leads": scored,
    }
    rendered = json.dumps(input_payload, indent=2, ensure_ascii=True)
    return f"{template}\n\nINPUT_SCORED_LEADS_JSON:\n```json\n{rendered}\n```"


def _resolve_evidence(config: SemipilotConfig) -> dict[str, Any]:
    if config.search.provider == "manual_file":
        if not config.raw_evidence_path or not config.raw_evidence_path.exists():
            raise FileNotFoundError("search.provider=manual_file requires `raw_evidence_path` to exist.")
        return {
            "search_provider": "manual_file",
            "query_count": 0,
            "hit_count": 0,
            "errors": [],
            "hits": [],
            "raw_evidence_text": config.raw_evidence_path.read_text(encoding="utf-8"),
        }
    return discover_web_evidence(config.search)


def _run_review_gate(
    *,
    client: OpenAIResponsesClient,
    system_prompt: str,
    review_prompt: str,
    outreach_json: dict[str, Any],
    evidence_json: dict[str, Any],
) -> dict[str, Any]:
    leads_by_id = {str(item.get("lead_id")): item for item in evidence_json.get("leads", []) if isinstance(item, dict)}
    reviews: list[dict[str, Any]] = []
    for draft in outreach_json.get("draft_queue", []):
        if not isinstance(draft, dict):
            continue
        lead_id = str(draft.get("lead_id"))
        evidence = leads_by_id.get(lead_id, {})
        composed = (
            f"{review_prompt}\n\nINPUT_DRAFT_JSON:\n```json\n"
            f"{json.dumps(draft, indent=2, ensure_ascii=True)}\n```\n\nINPUT_EVIDENCE_JSON:\n```json\n"
            f"{json.dumps(evidence, indent=2, ensure_ascii=True)}\n```"
        )
        text = client.run(system_prompt=system_prompt, user_prompt=composed)
        output = parse_json_from_text(text)
        output["lead_id"] = lead_id
        reviews.append(output)
    return {"reviews": reviews}


def _compose_reply_prompt(template: str, replies_json: Any) -> str:
    rendered = json.dumps(replies_json, indent=2, ensure_ascii=True)
    return f"{template}\n\nINPUT_REPLIES_JSON:\n```json\n{rendered}\n```"


def _merge_collection_fields_into_scored(scoring_json: dict[str, Any], collection_json: dict[str, Any]) -> dict[str, Any]:
    leads_by_id = {
        str(item.get("lead_id")): item
        for item in collection_json.get("leads", [])
        if isinstance(item, dict) and isinstance(item.get("lead_id"), str)
    }
    scored = scoring_json.get("scored_leads", [])
    if not isinstance(scored, list):
        return scoring_json

    merged: list[dict[str, Any]] = []
    for item in scored:
        if not isinstance(item, dict):
            continue
        lead_id = str(item.get("lead_id", ""))
        merged_item = dict(leads_by_id.get(lead_id, {}))
        merged_item.update(item)
        merged.append(merged_item)
    scoring_json["scored_leads"] = merged
    return scoring_json


def _normalize_collection_leads(
    collection_json: dict[str, Any],
    *,
    source_name: str,
    domain_email_map: dict[str, str],
) -> dict[str, Any]:
    leads = collection_json.get("leads", [])
    if not isinstance(leads, list):
        collection_json["leads"] = []
        return collection_json

    normalized: list[dict[str, Any]] = []
    for lead in leads:
        if not isinstance(lead, dict):
            continue
        lead_copy = dict(lead)
        brand = _safe_str(lead_copy.get("brand_name")) or "unknown_brand"
        primary_url = _safe_str(lead_copy.get("primary_profile_url")) or "unknown"
        region = _safe_str(lead_copy.get("region")) or "India"
        source_urls = _as_str_list(lead_copy.get("source_urls"))
        website_url = _safe_str(lead_copy.get("website_url"))

        email = _safe_str(lead_copy.get("founder_or_growth_email"))
        if not email:
            email = _extract_email_from_lead_text(lead_copy)
        if not email:
            email = _email_from_domain_map(source_urls=source_urls, domain_email_map=domain_email_map)

        channels = _as_str_list(lead_copy.get("contact_channels_available"))
        channels = [item.lower() for item in channels if item.lower() in {"email", "instagram_dm", "whatsapp"}]
        if email and "email" not in channels:
            channels.append("email")

        normalized_lead = {
            "lead_id": _safe_str(lead_copy.get("lead_id")) or _make_lead_id(brand=brand, primary_url=primary_url, region=region),
            "brand_name": brand,
            "primary_profile_url": primary_url,
            "instagram_handle": _normalize_unknown(lead_copy.get("instagram_handle")),
            "website_url": _normalize_unknown(website_url),
            "whatsapp_business_link_or_number": _normalize_unknown(lead_copy.get("whatsapp_business_link_or_number")),
            "contact_channels_available": channels,
            "category": _normalize_unknown(lead_copy.get("category")),
            "stage": _normalize_stage(lead_copy.get("stage")),
            "team_size": _normalize_team_size(lead_copy.get("team_size")),
            "region": region,
            "launch_recency_days": _normalize_number_or_unknown(lead_copy.get("launch_recency_days")),
            "ugc_review_depth_signal": _normalize_signal_level(lead_copy.get("ugc_review_depth_signal")),
            "paid_ads_signal": _normalize_signal_level(lead_copy.get("paid_ads_signal")),
            "public_review_request_signal": _normalize_binary(lead_copy.get("public_review_request_signal")),
            "new_digital_presence_signal": _normalize_binary(lead_copy.get("new_digital_presence_signal")),
            "social_presence_signal": _normalize_signal_level(lead_copy.get("social_presence_signal")),
            "sampling_feasibility": _normalize_binary(lead_copy.get("sampling_feasibility")),
            "shipping_capability": _normalize_binary(lead_copy.get("shipping_capability")),
            "margin_viability_signal": _normalize_signal_level(lead_copy.get("margin_viability_signal")),
            "founder_or_growth_email": _normalize_unknown(email),
            "email_validity_signal": "valid" if email else "unknown",
            "contact_form_status": _normalize_contact_form(lead_copy.get("contact_form_status")),
            "brand_presence_type": _normalize_brand_presence(lead_copy.get("brand_presence_type"), website_url=website_url),
            "registration_status": _normalize_registration_status(lead_copy.get("registration_status")),
            "contact_source": _safe_str(lead_copy.get("contact_source")) or source_name,
            "source_urls": source_urls or ([primary_url] if primary_url != "unknown" else []),
            "evidence_notes": _safe_str(lead_copy.get("evidence_notes")) or "",
            "outreach_status": _safe_str(lead_copy.get("outreach_status")) or "not_started",
            "response_status": _safe_str(lead_copy.get("response_status")) or "none",
        }
        normalized.append(normalized_lead)

    collection_json["leads"] = normalized
    return collection_json


def _create_gmail_drafts_if_enabled(
    *,
    config: SemipilotConfig,
    outreach_json: dict[str, Any],
    review_results: dict[str, Any],
    scored_json: dict[str, Any],
) -> dict[str, Any]:
    if not config.gmail_drafts.enabled:
        return {"enabled": False, "results": []}

    review_decisions = _review_decisions_by_lead(review_results)
    scored_by_id = {
        str(item.get("lead_id")): item
        for item in scored_json.get("scored_leads", [])
        if isinstance(item, dict) and isinstance(item.get("lead_id"), str)
    }
    client = GmailDraftClient(config.gmail_drafts)
    results: list[dict[str, Any]] = []

    for draft in outreach_json.get("draft_queue", []):
        if not isinstance(draft, dict):
            continue
        lead_id = str(draft.get("lead_id"))
        if config.gmail_drafts.only_review_approved:
            decision = review_decisions.get(lead_id)
            if decision != "approve":
                continue

        lead = scored_by_id.get(lead_id, {})
        recipient = _best_email_from_lead(lead)
        if not recipient:
            results.append(
                {
                    "lead_id": lead_id,
                    "recipient": "",
                    "status": "skipped",
                    "draft_id": None,
                    "error": "missing_email",
                }
            )
            continue

        subject = _safe_str(draft.get("message_subject")) or config.gmail_drafts.subject_fallback
        body = _safe_str(draft.get("message_draft")) or ""
        try:
            draft_id = client.create_draft(to_email=recipient, subject=subject, body=body)
            results.append(
                {
                    "lead_id": lead_id,
                    "recipient": recipient,
                    "status": "created",
                    "draft_id": draft_id,
                    "error": None,
                }
            )
        except Exception as exc:  # pragma: no cover - network dependent
            results.append(
                {
                    "lead_id": lead_id,
                    "recipient": recipient,
                    "status": "failed",
                    "draft_id": None,
                    "error": str(exc),
                }
            )

    return {"enabled": True, "results": results}


def _review_decisions_by_lead(review_results: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    reviews = review_results.get("reviews", [])
    if not isinstance(reviews, list):
        return output
    for item in reviews:
        if not isinstance(item, dict):
            continue
        lead_id = item.get("lead_id")
        decision = item.get("decision")
        if isinstance(lead_id, str) and isinstance(decision, str):
            output[lead_id] = decision
    return output


def _best_email_from_lead(lead: dict[str, Any]) -> str | None:
    email = _safe_str(lead.get("founder_or_growth_email"))
    if email and "@" in email and email.lower() != "unknown":
        return email
    return None


def _extract_email_from_lead_text(lead: dict[str, Any]) -> str | None:
    chunks: list[str] = []
    for key in ("evidence_notes", "notes"):
        value = _safe_str(lead.get(key))
        if value:
            chunks.append(value)
    for value in _as_str_list(lead.get("source_urls")):
        chunks.append(value)
    text = "\n".join(chunks)
    match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
    if not match:
        return None
    return match.group(1).lower()


def _domain_email_map_from_search_report(search_report: dict[str, Any]) -> dict[str, str]:
    output: dict[str, str] = {}
    hits = search_report.get("hits", [])
    if not isinstance(hits, list):
        return output
    for item in hits:
        if not isinstance(item, dict):
            continue
        url = _safe_str(item.get("url"))
        emails = item.get("page_emails")
        if not url or not isinstance(emails, list):
            continue
        domain = _domain_from_url(url)
        if not domain:
            continue
        for email in emails:
            if isinstance(email, str) and "@" in email:
                output[domain] = email.lower()
                break
    return output


def _email_from_domain_map(*, source_urls: list[str], domain_email_map: dict[str, str]) -> str | None:
    for url in source_urls:
        domain = _domain_from_url(url)
        if domain and domain in domain_email_map:
            return domain_email_map[domain]
    return None


def _domain_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = parsed.netloc.strip().lower()
    if not host:
        return None
    return host[4:] if host.startswith("www.") else host


def _make_lead_id(*, brand: str, primary_url: str, region: str) -> str:
    seed = f"{brand.lower()}|{primary_url.lower()}|{region.lower()}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"lead_{digest}"


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    output.append(cleaned)
        return output
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    return []


def _normalize_unknown(value: Any) -> str:
    text = _safe_str(value)
    return text if text else "unknown"


def _normalize_stage(value: Any) -> str:
    allowed = {"pre_revenue", "pre_seed", "seed", "series_a", "unknown"}
    text = (_safe_str(value) or "unknown").lower()
    return text if text in allowed else "unknown"


def _normalize_team_size(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(int(value))
    text = _safe_str(value)
    return text if text else "unknown"


def _normalize_number_or_unknown(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = _safe_str(value)
    return text if text else "unknown"


def _normalize_signal_level(value: Any) -> str:
    allowed = {"high", "medium", "low", "unknown"}
    text = (_safe_str(value) or "unknown").lower()
    return text if text in allowed else "unknown"


def _normalize_binary(value: Any) -> str:
    allowed = {"yes", "no", "unknown"}
    text = (_safe_str(value) or "unknown").lower()
    return text if text in allowed else "unknown"


def _normalize_contact_form(value: Any) -> str:
    allowed = {"working", "missing", "unknown"}
    text = (_safe_str(value) or "unknown").lower()
    return text if text in allowed else "unknown"


def _normalize_brand_presence(value: Any, *, website_url: str | None) -> str:
    text = (_safe_str(value) or "").lower()
    allowed = {"website_brand", "social_first_unregistered"}
    if text in allowed:
        return text
    return "website_brand" if website_url and website_url.lower() != "unknown" else "social_first_unregistered"


def _normalize_registration_status(value: Any) -> str:
    allowed = {"registered", "unregistered", "unknown"}
    text = (_safe_str(value) or "unknown").lower()
    return text if text in allowed else "unknown"


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
