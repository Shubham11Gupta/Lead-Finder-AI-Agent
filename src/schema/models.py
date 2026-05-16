"""Validation models and error structures for schema checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationIssue:
    field: str
    code: str
    message: str
    expected: str | None = None
    actual: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(slots=True)
class ValidationResult:
    normalized: dict[str, Any]
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "normalized": self.normalized,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class SchemaValidationError(Exception):
    """Raised when `validate_lead_or_raise` sees invalid payload."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        chunks = [f"{issue.field}: {issue.message}" for issue in self.issues]
        return "Schema validation failed: " + "; ".join(chunks)

