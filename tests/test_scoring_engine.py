"""Tests for scoring engine behavior."""

from __future__ import annotations

import unittest

from src.scoring import ScoringEngine


def make_base_lead() -> dict:
    return {
        "lead_id": "lead_score_001",
        "brand_name": "Score Brand",
        "brand_presence_type": "social_first_unregistered",
        "registration_status": "unknown",
        "category": "beauty",
        "stage": "pre_seed",
        "region": "India",
        "team_size": 12,
        "primary_profile_url": "https://instagram.com/scorebrand",
        "instagram_handle": "scorebrand",
        "contact_channels_available": ["instagram_dm", "email"],
        "founder_or_growth_email": "hello@scorebrand.in",
        "email_validity_signal": "valid",
        "contact_form_status": "working",
        "ugc_review_depth_signal": "low",
        "paid_ads_signal": "high",
        "public_review_request_signal": "yes",
        "new_digital_presence_signal": "yes",
        "social_presence_signal": "high",
        "sampling_feasibility": "yes",
        "shipping_capability": "yes",
        "margin_viability_signal": "high",
        "outreach_status": "not_started",
        "contact_source": "instagram",
        "source_urls": ["https://instagram.com/scorebrand"],
        "last_verified_at": "2026-05-16T12:00:00+05:30",
        "created_at": "2026-05-16T12:00:00+05:30",
        "updated_at": "2026-05-16T12:00:00+05:30",
    }


class TestScoringEngine(unittest.TestCase):
    def test_strong_lead_scores_priority_a(self) -> None:
        lead = make_base_lead()
        lead["launch_recency_days"] = 30

        result = ScoringEngine().run([lead], run_context={"score_run_id": "score_run_test_a"})
        self.assertEqual("score_run_test_a", result.run_id)
        self.assertEqual(1, len(result.scored_leads))
        scored = result.scored_leads[0]

        self.assertEqual("A", scored.get("priority_bucket"))
        self.assertGreaterEqual(scored.get("final_score", 0), 60)
        self.assertEqual([], scored.get("penalties_applied"))

    def test_hard_skip_sampling_not_feasible(self) -> None:
        lead = make_base_lead()
        lead["sampling_feasibility"] = "no"

        result = ScoringEngine().run([lead])
        self.assertEqual(0, len(result.scored_leads))
        self.assertEqual(1, len(result.skipped_scoring))
        self.assertEqual("sampling_not_feasible", result.skipped_scoring[0].get("reason"))

    def test_hard_skip_no_reachable_channel(self) -> None:
        lead = make_base_lead()
        lead["contact_channels_available"] = ["email"]
        lead["email_validity_signal"] = "invalid"
        lead["founder_or_growth_email"] = "bad@scorebrand.in"
        lead["instagram_handle"] = None
        lead["primary_profile_url"] = "https://scorebrand.in"
        lead["whatsapp_business_link_or_number"] = None

        result = ScoringEngine().run([lead])
        self.assertEqual(0, len(result.scored_leads))
        self.assertEqual("no_reachable_channel", result.skipped_scoring[0].get("reason"))

    def test_low_margin_penalty_applied(self) -> None:
        lead = make_base_lead()
        lead["launch_recency_days"] = 30
        lead["margin_viability_signal"] = "low"

        result = ScoringEngine().run([lead])
        scored = result.scored_leads[0]

        self.assertIn("very_low_margin", scored.get("penalties_applied", []))
        self.assertEqual(85, scored.get("final_score"))

    def test_bucket_b_boundary(self) -> None:
        lead = make_base_lead()
        lead["team_size"] = None
        lead["stage"] = "unknown"
        lead["launch_recency_days"] = None
        lead["public_review_request_signal"] = "no"
        lead["new_digital_presence_signal"] = "no"
        lead["paid_ads_signal"] = "low"
        lead["ugc_review_depth_signal"] = "high"
        lead["shipping_capability"] = "no"
        lead["margin_viability_signal"] = "unknown"
        lead["contact_form_status"] = "missing"
        lead["contact_channels_available"] = ["email"]
        lead["instagram_handle"] = None
        lead["primary_profile_url"] = "https://scorebrand.in"
        lead["whatsapp_business_link_or_number"] = None

        result = ScoringEngine().run([lead])
        scored = result.scored_leads[0]

        self.assertEqual(30, scored.get("final_score"))
        self.assertEqual("B", scored.get("priority_bucket"))

    def test_missing_required_scoring_fields(self) -> None:
        lead = make_base_lead()
        del lead["category"]

        result = ScoringEngine().run([lead])
        self.assertEqual(0, len(result.scored_leads))
        self.assertEqual("missing_required_scoring_fields", result.skipped_scoring[0].get("reason"))
        self.assertIn("category", result.skipped_scoring[0].get("missing_fields", []))


if __name__ == "__main__":
    unittest.main()
