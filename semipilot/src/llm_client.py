"""Minimal OpenAI Responses API client using stdlib only."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


RESPONSES_URL = "https://api.openai.com/v1/responses"


class OpenAIResponsesClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def run(self, *, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = Request(
            url=RESPONSES_URL,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(req, timeout=120) as response:  # nosec - fixed trusted endpoint
            raw = response.read().decode("utf-8")
        parsed = json.loads(raw)
        return _extract_text(parsed)


def _extract_text(response_json: dict[str, Any]) -> str:
    output = response_json.get("output", [])
    if isinstance(output, list):
        texts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    texts.append(text)
        if texts:
            return "\n".join(texts).strip()

    fallback = response_json.get("output_text")
    if isinstance(fallback, str) and fallback.strip():
        return fallback.strip()
    raise ValueError("Could not extract model text output from response.")

