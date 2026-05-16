"""Mock connector for local development and tests."""

from __future__ import annotations

from typing import Any, Mapping

from .base import RawLeadCandidate, SourceConnector


class MockConnector(SourceConnector):
    """A deterministic connector used for tests and local dry-runs."""

    def __init__(self, name: str, candidates: list[RawLeadCandidate]) -> None:
        self.name = name
        self._candidates = list(candidates)

    def discover(self, run_context: Mapping[str, Any] | None = None) -> list[RawLeadCandidate]:
        return list(self._candidates)

