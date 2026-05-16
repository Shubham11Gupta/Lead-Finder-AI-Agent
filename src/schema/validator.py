"""Lead schema validator for Step 14 (Python foundation)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from .enums import (
    BinarySignal,
    BrandPresenceType,
    ContactChannel,
    ContactFormStatus,
    EmailValiditySignal,
    OutreachStatus,
    PriorityBucket,
    RegistrationStatus,
    ResponseStatus,
    SignalLevel,
    Stage,
    enum_values,
)
from .models import SchemaValidationError, ValidationIssue, ValidationResult


REQUIRED_STRING_FIELDS = {
    "lead_id",
    "brand_name",
    "category",
    "region",
    "primary_profile_url",
    "contact_source",
}

OPTIONAL_STRING_FIELDS = {
    "website_url",
    "instagram_handle",
    "whatsapp_business_link_or_number",
    "founder_or_growth_email",
    "notes",
}

REQUIRED_ENUM_FIELDS: dict[str, set[str]] = {
    "brand_presence_type": enum_values(BrandPresenceType),
    "registration_status": enum_values(RegistrationStatus),
    "stage": enum_values(Stage),
    "email_validity_signal": enum_values(EmailValiditySignal),
    "contact_form_status": enum_values(ContactFormStatus),
    "ugc_review_depth_signal": enum_values(SignalLevel),
    "paid_ads_signal": enum_values(SignalLevel),
    "public_review_request_signal": enum_values(BinarySignal),
    "new_digital_presence_signal": enum_values(BinarySignal),
    "social_presence_signal": enum_values(SignalLevel),
    "sampling_feasibility": enum_values(BinarySignal),
    "shipping_capability": enum_values(BinarySignal),
    "margin_viability_signal": enum_values(SignalLevel),
    "outreach_status": enum_values(OutreachStatus),
}

OPTIONAL_ENUM_FIELDS: dict[str, set[str]] = {
    "priority_bucket": enum_values(PriorityBucket),
    "response_status": enum_values(ResponseStatus),
}

REQUIRED_ARRAY_ENUM_FIELDS: dict[str, set[str]] = {
    "contact_channels_available": enum_values(ContactChannel),
}

OPTIONAL_ARRAY_STRING_FIELDS = {"penalties_applied", "source_urls"}

REQUIRED_DATETIME_FIELDS = {"last_verified_at", "created_at", "updated_at"}
OPTIONAL_DATETIME_FIELDS = {"scored_at", "last_outreach_at"}

OPTIONAL_NUMBER_OR_STRING_FIELDS = {"team_size", "launch_recency_days"}

OPTIONAL_RANGED_NUMBER_FIELDS: dict[str, tuple[float, float]] = {
    "icp_fit_score": (0, 40),
    "need_intent_score": (0, 35),
    "operational_feasibility_score": (0, 15),
    "reachability_score": (0, 10),
    "final_score": (0, 100),
}

REQUIRED_FIELDS = (
    REQUIRED_STRING_FIELDS
    | set(REQUIRED_ENUM_FIELDS)
    | set(REQUIRED_ARRAY_ENUM_FIELDS)
    | REQUIRED_DATETIME_FIELDS
)


def validate_lead_record(record: Mapping[str, Any]) -> ValidationResult:
    """
    Validate a lead payload against `docs/lead-data-schema.md`.

    Returns:
        ValidationResult with `is_valid`, `issues`, and `normalized` payload copy.
    """
    issues: list[ValidationIssue] = []

    if not isinstance(record, Mapping):
        issues.append(
            ValidationIssue(
                field="root",
                code="invalid_type",
                message="Lead payload must be a mapping/dictionary.",
                expected="mapping",
                actual=type(record).__name__,
            )
        )
        return ValidationResult(normalized={}, issues=issues)

    normalized = dict(record)

    _validate_required_fields(normalized, issues)
    _validate_string_fields(normalized, issues)
    _validate_enum_fields(normalized, issues)
    _validate_array_fields(normalized, issues)
    _validate_number_or_string_fields(normalized, issues)
    _validate_ranged_numbers(normalized, issues)
    _validate_datetime_fields(normalized, issues)

    return ValidationResult(normalized=normalized, issues=issues)


def validate_lead_or_raise(record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate record and raise SchemaValidationError if invalid."""
    result = validate_lead_record(record)
    if not result.is_valid:
        raise SchemaValidationError(result.issues)
    return result.normalized


def _validate_required_fields(record: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for field in sorted(REQUIRED_FIELDS):
        if field not in record:
            _add_issue(
                issues,
                field=field,
                code="missing_required",
                message=f"Missing required field: '{field}'.",
            )


def _validate_string_fields(record: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for field in REQUIRED_STRING_FIELDS | OPTIONAL_STRING_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, str):
            _add_issue(
                issues,
                field=field,
                code="invalid_type",
                message=f"Field '{field}' must be a string.",
                expected="string",
                actual=type(value).__name__,
            )
            continue
        if value.strip() == "":
            _add_issue(
                issues,
                field=field,
                code="empty_string",
                message=f"Field '{field}' cannot be empty.",
            )
            continue
        record[field] = value.strip()


def _validate_enum_fields(record: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for field, allowed in {**REQUIRED_ENUM_FIELDS, **OPTIONAL_ENUM_FIELDS}.items():
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, str):
            _add_issue(
                issues,
                field=field,
                code="invalid_type",
                message=f"Field '{field}' must be a string enum value.",
                expected=f"one of {sorted(allowed)}",
                actual=type(value).__name__,
            )
            continue
        if value not in allowed:
            _add_issue(
                issues,
                field=field,
                code="invalid_enum",
                message=f"Field '{field}' has invalid enum value.",
                expected=f"one of {sorted(allowed)}",
                actual=value,
            )


def _validate_array_fields(record: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for field, allowed in REQUIRED_ARRAY_ENUM_FIELDS.items():
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, list):
            _add_issue(
                issues,
                field=field,
                code="invalid_type",
                message=f"Field '{field}' must be an array/list.",
                expected="array",
                actual=type(value).__name__,
            )
            continue
        if len(value) == 0:
            _add_issue(
                issues,
                field=field,
                code="empty_array",
                message=f"Field '{field}' cannot be an empty array.",
            )
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                _add_issue(
                    issues,
                    field=f"{field}[{idx}]",
                    code="invalid_type",
                    message=f"Array item in '{field}' must be a string enum value.",
                    expected=f"one of {sorted(allowed)}",
                    actual=type(item).__name__,
                )
                continue
            if item not in allowed:
                _add_issue(
                    issues,
                    field=f"{field}[{idx}]",
                    code="invalid_enum",
                    message=f"Array item in '{field}' has invalid enum value.",
                    expected=f"one of {sorted(allowed)}",
                    actual=item,
                )

    for field in OPTIONAL_ARRAY_STRING_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if not isinstance(value, list):
            _add_issue(
                issues,
                field=field,
                code="invalid_type",
                message=f"Field '{field}' must be an array/list.",
                expected="array",
                actual=type(value).__name__,
            )
            continue
        for idx, item in enumerate(value):
            if not isinstance(item, str):
                _add_issue(
                    issues,
                    field=f"{field}[{idx}]",
                    code="invalid_type",
                    message=f"Array item in '{field}' must be a string.",
                    expected="string",
                    actual=type(item).__name__,
                )
                continue
            if item.strip() == "":
                _add_issue(
                    issues,
                    field=f"{field}[{idx}]",
                    code="empty_string",
                    message=f"Array item in '{field}' cannot be empty.",
                )


def _validate_number_or_string_fields(record: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for field in OPTIONAL_NUMBER_OR_STRING_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if isinstance(value, str):
            if value.strip() == "":
                _add_issue(
                    issues,
                    field=field,
                    code="empty_string",
                    message=f"Field '{field}' cannot be an empty string.",
                )
            else:
                record[field] = value.strip()
            continue
        if not _is_number(value):
            _add_issue(
                issues,
                field=field,
                code="invalid_type",
                message=f"Field '{field}' must be a number or string.",
                expected="number|string",
                actual=type(value).__name__,
            )


def _validate_ranged_numbers(record: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for field, (min_value, max_value) in OPTIONAL_RANGED_NUMBER_FIELDS.items():
        if field not in record:
            continue
        value = record[field]
        if not _is_number(value):
            _add_issue(
                issues,
                field=field,
                code="invalid_type",
                message=f"Field '{field}' must be a number.",
                expected="number",
                actual=type(value).__name__,
            )
            continue
        numeric_value = float(value)
        if not (min_value <= numeric_value <= max_value):
            _add_issue(
                issues,
                field=field,
                code="out_of_range",
                message=f"Field '{field}' must be between {min_value} and {max_value}.",
                expected=f"{min_value}..{max_value}",
                actual=value,
            )


def _validate_datetime_fields(record: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for field in REQUIRED_DATETIME_FIELDS | OPTIONAL_DATETIME_FIELDS:
        if field not in record:
            continue
        value = record[field]
        parsed = _parse_iso_datetime(value)
        if parsed is None:
            _add_issue(
                issues,
                field=field,
                code="invalid_datetime",
                message=f"Field '{field}' must be a valid ISO-8601 datetime.",
                expected="ISO-8601 datetime string",
                actual=value,
            )
            continue
        # Keep normalized datetimes in ISO format for consistency.
        record[field] = parsed.isoformat()


def _parse_iso_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if raw == "":
        return None

    # Python fromisoformat handles offsets but not trailing 'Z' directly.
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _add_issue(
    issues: list[ValidationIssue],
    *,
    field: str,
    code: str,
    message: str,
    expected: str | None = None,
    actual: Any | None = None,
) -> None:
    issues.append(
        ValidationIssue(
            field=field,
            code=code,
            message=message,
            expected=expected,
            actual=actual,
        )
    )

