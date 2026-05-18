"""Tests for suppression manager behavior."""

from __future__ import annotations

import unittest

from src.suppression import add_opt_out_to_suppression, is_lead_suppressed, load_suppression_registry


class TestSuppressionManager(unittest.TestCase):
    def test_legacy_registry_normalization(self) -> None:
        registry = load_suppression_registry("tests/fixtures/suppression_legacy.json")
        self.assertIn("blocked@example.com", registry["emails"])

    def test_add_and_detect_suppression(self) -> None:
        registry = {"emails": {}, "instagram_handles": {}, "whatsapp_numbers": {}}
        lead = {
            "founder_or_growth_email": "brand@example.com",
            "instagram_handle": "brandhandle",
            "whatsapp_business_link_or_number": "+911234567890",
        }
        updated = add_opt_out_to_suppression(lead=lead, registry=registry)
        suppressed, by = is_lead_suppressed(lead, updated)
        self.assertTrue(suppressed)
        self.assertEqual("email", by)


if __name__ == "__main__":
    unittest.main()

