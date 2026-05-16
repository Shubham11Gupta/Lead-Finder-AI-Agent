"""Internet discovery connector using Serper web search API."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import RawLeadCandidate, SourceConnector


SERPER_ENDPOINT = "https://google.serper.dev/search"


@dataclass(slots=True)
class SearchQuery:
    query: str
    category: str | None = None
    region: str | None = None


class SerperConnector(SourceConnector):
    """Discover lead candidates from internet search results."""

    def __init__(
        self,
        *,
        name: str = "serper",
        api_key: str | None = None,
        http_post: Callable[[str, dict[str, Any], str], dict[str, Any]] | None = None,
    ) -> None:
        self.name = name
        self._api_key = api_key
        self._http_post = http_post or _default_http_post

    def discover(self, run_context: Mapping[str, Any] | None = None) -> list[RawLeadCandidate]:
        run_context = run_context or {}
        api_key = self._resolve_api_key(run_context)
        queries = _parse_queries(run_context.get("serper_queries"))
        if not queries:
            raise ValueError("No search queries configured. Provide `serper_queries` in run_context.")

        gl = str(run_context.get("serper_gl", "in"))
        hl = str(run_context.get("serper_hl", "en"))
        num = int(run_context.get("serper_num", 10))
        default_region = str(run_context.get("default_region", "India"))

        candidates: list[RawLeadCandidate] = []
        seen_links: set[str] = set()

        for q in queries:
            payload = {"q": q.query, "gl": gl, "hl": hl, "num": num}
            response = self._http_post(SERPER_ENDPOINT, payload, api_key)
            organic = response.get("organic", [])
            if not isinstance(organic, list):
                continue

            for item in organic:
                if not isinstance(item, dict):
                    continue
                link = item.get("link")
                title = item.get("title")
                snippet = item.get("snippet")
                if not isinstance(link, str) or not link.strip():
                    continue
                clean_link = link.strip()
                if clean_link in seen_links:
                    continue
                seen_links.add(clean_link)

                brand_name = _infer_brand_name(title=title, link=clean_link)
                category = q.category or _infer_category_from_query(q.query)
                region = q.region or default_region

                instagram_handle = _extract_instagram_handle(clean_link)
                contact_channels = ["instagram_dm"] if instagram_handle else []
                website_url = clean_link if not instagram_handle else None

                lead_payload = {
                    "brand_name": brand_name,
                    "primary_profile_url": clean_link,
                    "website_url": website_url,
                    "instagram_handle": instagram_handle,
                    "contact_channels_available": contact_channels,
                    "category": category or "unknown",
                    "region": region,
                    "stage": "unknown",
                    "registration_status": "unknown",
                    "brand_presence_type": "website_brand" if website_url else "social_first_unregistered",
                    "email_validity_signal": "unknown",
                    "contact_form_status": "unknown",
                    "ugc_review_depth_signal": "unknown",
                    "paid_ads_signal": "unknown",
                    "public_review_request_signal": "unknown",
                    "new_digital_presence_signal": "unknown",
                    "social_presence_signal": "unknown",
                    "sampling_feasibility": "unknown",
                    "shipping_capability": "unknown",
                    "margin_viability_signal": "unknown",
                    "outreach_status": "not_started",
                    "response_status": "none",
                    "contact_source": self.name,
                    "source_urls": [clean_link],
                    "notes": snippet if isinstance(snippet, str) else None,
                }

                candidates.append(
                    RawLeadCandidate(
                        source_platform=self.name,
                        payload=lead_payload,
                        evidence_urls=[clean_link],
                    )
                )

        return candidates

    def _resolve_api_key(self, run_context: Mapping[str, Any]) -> str:
        from_context = run_context.get("serper_api_key")
        if isinstance(from_context, str) and from_context.strip():
            return from_context.strip()
        if self._api_key and self._api_key.strip():
            return self._api_key.strip()
        from_env = os.getenv("SERPER_API_KEY", "").strip()
        if from_env:
            return from_env
        raise ValueError("SERPER API key is missing. Set SERPER_API_KEY or pass `serper_api_key`.")


def _parse_queries(raw: Any) -> list[SearchQuery]:
    if raw is None:
        return []
    queries: list[SearchQuery] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                queries.append(SearchQuery(query=item.strip()))
            elif isinstance(item, dict):
                query = item.get("query")
                if isinstance(query, str) and query.strip():
                    queries.append(
                        SearchQuery(
                            query=query.strip(),
                            category=_to_opt_str(item.get("category")),
                            region=_to_opt_str(item.get("region")),
                        )
                    )
    elif isinstance(raw, str) and raw.strip():
        queries.append(SearchQuery(query=raw.strip()))
    return queries


def _to_opt_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _default_http_post(url: str, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        url=url,
        data=body,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=20) as response:  # nosec - controlled endpoint + payload
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Invalid API response format.")
    return parsed


def _infer_brand_name(*, title: Any, link: str) -> str:
    if isinstance(title, str) and title.strip():
        cleaned = title.split("|")[0].split("-")[0].strip()
        if cleaned:
            return cleaned
    parsed = urlparse(link)
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    root = host.split(".")[0]
    return root or "unknown_brand"


def _extract_instagram_handle(link: str) -> str | None:
    parsed = urlparse(link)
    host = (parsed.netloc or "").lower()
    if "instagram.com" not in host:
        return None
    segments = [segment for segment in parsed.path.split("/") if segment]
    if not segments:
        return None
    return segments[0].lstrip("@")


def _infer_category_from_query(query: str) -> str | None:
    lowered = query.lower()
    if "beauty" in lowered or "personal care" in lowered:
        return "beauty"
    if "nutrition" in lowered or "supplement" in lowered:
        return "nutrition"
    if "snack" in lowered or "food" in lowered:
        return "snacks"
    if "pet" in lowered:
        return "pet care"
    if "health" in lowered:
        return "health care"
    return None

