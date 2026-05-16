"""Connector interfaces for collection discovery."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class RawLeadCandidate:
    """Raw candidate discovered from a source platform."""

    source_platform: str
    payload: dict[str, Any]
    evidence_urls: list[str] = field(default_factory=list)


class SourceConnector(ABC):
    """Base interface each source connector should implement."""

    name: str

    @abstractmethod
    def discover(self, run_context: Mapping[str, Any] | None = None) -> list[RawLeadCandidate]:
        """
        Discover raw lead candidates.

        Args:
            run_context: Optional metadata (segment, run_id, limits).
        Returns:
            List of raw candidates from this source.
        """
        raise NotImplementedError

