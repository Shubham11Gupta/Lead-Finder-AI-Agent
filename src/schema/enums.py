"""Enumerations for lead schema validation."""

from __future__ import annotations

from enum import StrEnum


class BrandPresenceType(StrEnum):
    WEBSITE_BRAND = "website_brand"
    SOCIAL_FIRST_UNREGISTERED = "social_first_unregistered"


class RegistrationStatus(StrEnum):
    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    UNKNOWN = "unknown"


class Stage(StrEnum):
    PRE_REVENUE = "pre_revenue"
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    UNKNOWN = "unknown"


class ContactChannel(StrEnum):
    EMAIL = "email"
    INSTAGRAM_DM = "instagram_dm"
    WHATSAPP = "whatsapp"


class EmailValiditySignal(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class ContactFormStatus(StrEnum):
    WORKING = "working"
    MISSING = "missing"
    UNKNOWN = "unknown"


class SignalLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class BinarySignal(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class PriorityBucket(StrEnum):
    A = "A"
    B = "B"
    SKIP = "skip"


class OutreachStatus(StrEnum):
    NOT_STARTED = "not_started"
    DRAFT_READY = "draft_ready"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    CLOSED = "closed"


class ResponseStatus(StrEnum):
    NONE = "none"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


def enum_values(enum_type: type[StrEnum]) -> set[str]:
    """Return allowed values for enum validation."""
    return {member.value for member in enum_type}

