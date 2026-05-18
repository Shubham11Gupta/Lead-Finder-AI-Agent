"""Web discovery to collect raw evidence for prompt-based extraction."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import SearchConfig


EMAIL_PATTERN = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(slots=True)
class SearchHit:
    query: str
    title: str
    url: str
    snippet: str
    provider: str
    page_excerpt: str | None = None
    page_emails: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "provider": self.provider,
            "page_excerpt": self.page_excerpt,
            "page_emails": self.page_emails or [],
        }


def discover_web_evidence(search_cfg: SearchConfig) -> dict[str, Any]:
    hits: list[SearchHit] = []
    errors: list[str] = []

    for query in search_cfg.queries:
        try:
            if search_cfg.provider == "google_cse":
                hits.extend(_search_google_cse(search_cfg, query))
            elif search_cfg.provider == "serper":
                hits.extend(_search_serper(search_cfg, query))
            else:
                raise ValueError(
                    f"Unsupported search.provider={search_cfg.provider}. Use google_cse or serper."
                )
        except Exception as exc:
            errors.append(f"{query}: {exc}")

    if search_cfg.fetch_page_content:
        _hydrate_page_content(hits, max_pages_per_query=max(0, search_cfg.fetch_pages_per_query))

    evidence_text = _render_evidence_text(hits)
    return {
        "search_provider": search_cfg.provider,
        "query_count": len(search_cfg.queries),
        "hit_count": len(hits),
        "errors": errors,
        "hits": [hit.to_dict() for hit in hits],
        "raw_evidence_text": evidence_text,
    }


def _search_google_cse(search_cfg: SearchConfig, query: str) -> list[SearchHit]:
    if not search_cfg.google_api_key or not search_cfg.google_cse_id:
        raise ValueError("Missing google_api_key or google_cse_id for google_cse search.")

    params = {
        "key": search_cfg.google_api_key,
        "cx": search_cfg.google_cse_id,
        "q": query,
        "num": min(max(search_cfg.max_results_per_query, 1), 10),
        "hl": search_cfg.language,
        "gl": search_cfg.region,
    }
    url = f"https://customsearch.googleapis.com/customsearch/v1?{urlencode(params)}"
    payload = _http_get_json(url)
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []

    hits: list[SearchHit] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        link = _safe_str(item.get("link"))
        if not link:
            continue
        title = _safe_str(item.get("title")) or "untitled"
        snippet = _safe_str(item.get("snippet")) or ""
        hits.append(SearchHit(query=query, title=title, url=link, snippet=snippet, provider="google_cse"))
    return hits


def _search_serper(search_cfg: SearchConfig, query: str) -> list[SearchHit]:
    if not search_cfg.serper_api_key:
        raise ValueError("Missing serper_api_key for serper search.")

    payload = {
        "q": query,
        "gl": search_cfg.region,
        "hl": search_cfg.language,
        "num": min(max(search_cfg.max_results_per_query, 1), 20),
    }
    raw = json.dumps(payload).encode("utf-8")
    req = Request(
        url="https://google.serper.dev/search",
        data=raw,
        method="POST",
        headers={
            "X-API-KEY": search_cfg.serper_api_key,
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=30) as response:  # nosec - fixed endpoint and controlled payload
        parsed = json.loads(response.read().decode("utf-8"))

    organic = parsed.get("organic", [])
    if not isinstance(organic, list):
        return []

    hits: list[SearchHit] = []
    for item in organic:
        if not isinstance(item, dict):
            continue
        link = _safe_str(item.get("link"))
        if not link:
            continue
        title = _safe_str(item.get("title")) or "untitled"
        snippet = _safe_str(item.get("snippet")) or ""
        hits.append(SearchHit(query=query, title=title, url=link, snippet=snippet, provider="serper"))
    return hits


def _hydrate_page_content(hits: list[SearchHit], *, max_pages_per_query: int) -> None:
    if max_pages_per_query <= 0:
        return

    seen_per_query: dict[str, int] = {}
    for hit in hits:
        current = seen_per_query.get(hit.query, 0)
        if current >= max_pages_per_query:
            continue
        seen_per_query[hit.query] = current + 1

        page_text = _fetch_page_text(hit.url)
        if not page_text:
            continue
        cleaned = _clean_text(page_text)
        hit.page_excerpt = cleaned[:500]

        emails = list({match.lower() for match in EMAIL_PATTERN.findall(cleaned)})
        hit.page_emails = emails[:5]


def _render_evidence_text(hits: list[SearchHit]) -> str:
    chunks: list[str] = []
    for idx, hit in enumerate(hits, start=1):
        chunks.append(f"Result {idx}")
        chunks.append(f"Query: {hit.query}")
        chunks.append(f"Provider: {hit.provider}")
        chunks.append(f"Title: {hit.title}")
        chunks.append(f"URL: {hit.url}")
        chunks.append(f"Snippet: {hit.snippet}")
        if hit.page_emails:
            chunks.append(f"Page emails: {', '.join(hit.page_emails)}")
        if hit.page_excerpt:
            chunks.append(f"Page excerpt: {hit.page_excerpt}")
        chunks.append("")
    return "\n".join(chunks).strip()


def _http_get_json(url: str) -> dict[str, Any]:
    req = Request(url=url, method="GET", headers={"User-Agent": "Semipilot/1.0"})
    with urlopen(req, timeout=30) as response:  # nosec - network endpoint is user-configured API
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Search API returned non-object JSON.")
    return parsed


def _fetch_page_text(url: str) -> str | None:
    try:
        req = Request(url=url, method="GET", headers={"User-Agent": "Semipilot/1.0"})
        with urlopen(req, timeout=15) as response:  # nosec - public web URLs from search results
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                return None
            return response.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def _clean_text(html: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", html)
    return WHITESPACE_PATTERN.sub(" ", without_tags).strip()


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None

