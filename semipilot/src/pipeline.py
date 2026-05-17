"""Prompt-first semipilot workflow automation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .llm_client import OpenAIResponsesClient
from .models import SemipilotConfig
from .prompt_utils import load_prompt, parse_json_from_text


def run_semipilot(config: SemipilotConfig) -> dict[str, Any]:
    run_id = datetime.now(tz=timezone.utc).strftime("semipilot_%Y%m%d_%H%M%S")
    run_dir = config.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    prompts = _load_prompt_pack(config.prompts_dir)
    client = OpenAIResponsesClient(api_key=config.openai_api_key, model=config.model)
    system_prompt = prompts["system"]

    raw_evidence = config.raw_evidence_path.read_text(encoding="utf-8")
    _write_text(run_dir / "00_raw_evidence.txt", raw_evidence)

    collection_input = _compose_collection_prompt(prompts["collection"], raw_evidence)
    collection_text = client.run(system_prompt=system_prompt, user_prompt=collection_input)
    collection_json = parse_json_from_text(collection_text)
    _write_json(run_dir / "01_collection_output.json", collection_json)

    scoring_input = _compose_scoring_prompt(prompts["scoring"], collection_json)
    scoring_text = client.run(system_prompt=system_prompt, user_prompt=scoring_input)
    scoring_json = parse_json_from_text(scoring_text)
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

    reply_results: dict[str, Any] = {"reply_results": []}
    if config.run_reply_classification and config.replies_path and config.replies_path.exists():
        replies_json = json.loads(config.replies_path.read_text(encoding="utf-8"))
        reply_input = _compose_reply_prompt(prompts["reply"], replies_json)
        reply_text = client.run(system_prompt=system_prompt, user_prompt=reply_input)
        reply_results = parse_json_from_text(reply_text)
    _write_json(run_dir / "05_reply_results.json", reply_results)

    summary = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "collection_count": len(collection_json.get("leads", [])),
        "scored_count": len(scoring_json.get("scored_leads", [])),
        "draft_count": len(outreach_json.get("draft_queue", [])),
        "review_count": len(review_results.get("reviews", [])),
        "reply_count": len(reply_results.get("reply_results", [])),
        "files": [
            "00_raw_evidence.txt",
            "01_collection_output.json",
            "02_scoring_output.json",
            "03_outreach_drafts.json",
            "04_review_results.json",
            "05_reply_results.json",
        ],
    }
    _write_json(run_dir / "06_summary.json", summary)
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

