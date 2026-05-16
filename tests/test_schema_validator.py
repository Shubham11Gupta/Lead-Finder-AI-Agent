"""Step 15 tests for schema validation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.schema import SchemaValidationError, validate_lead_or_raise, validate_lead_record


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


class TestSchemaValidator(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        payload = load_fixture("lead_valid.json")
        result = validate_lead_record(payload)

        self.assertTrue(result.is_valid)
        self.assertEqual([], result.issues)

    def test_missing_required_field_returns_issue(self) -> None:
        payload = load_fixture("lead_invalid_missing_required.json")
        result = validate_lead_record(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any(i.field == "lead_id" and i.code == "missing_required" for i in result.issues))

    def test_invalid_enum_returns_issue(self) -> None:
        payload = load_fixture("lead_invalid_enum.json")
        result = validate_lead_record(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any(i.field == "stage" and i.code == "invalid_enum" for i in result.issues))

    def test_invalid_datetime_returns_issue(self) -> None:
        payload = load_fixture("lead_invalid_datetime.json")
        result = validate_lead_record(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any(i.field == "last_verified_at" and i.code == "invalid_datetime" for i in result.issues))
        self.assertTrue(any(i.field == "created_at" and i.code == "invalid_datetime" for i in result.issues))

    def test_array_field_type_check(self) -> None:
        payload = load_fixture("lead_valid.json")
        payload["contact_channels_available"] = "email"
        result = validate_lead_record(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(
            any(i.field == "contact_channels_available" and i.code == "invalid_type" for i in result.issues)
        )

    def test_out_of_range_score_returns_issue(self) -> None:
        payload = load_fixture("lead_valid.json")
        payload["final_score"] = 120
        result = validate_lead_record(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any(i.field == "final_score" and i.code == "out_of_range" for i in result.issues))

    def test_validate_or_raise_throws_on_invalid_payload(self) -> None:
        payload = load_fixture("lead_invalid_enum.json")

        with self.assertRaises(SchemaValidationError):
            validate_lead_or_raise(payload)


if __name__ == "__main__":
    unittest.main()

