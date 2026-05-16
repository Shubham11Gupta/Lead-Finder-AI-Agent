"""Tests for outreach draft generation engine."""

from __future__ import annotations

import unittest

from src.outreach import OutreachDraftEngine


def make_scored_lead() -> dict:
    return {
        "lead_id": "lead_outreach_001",
        "brand_name": "Glow Lab",
        "category": "beauty",
        "stage": "pre_seed",
        "region": "India",
        "priority_bucket": "A",
        "outreach_status": "not_started",
        "contact_channels_available": ["email", "instagram_dm", "whatsapp"],
        "founder_or_growth_email": "founder@glowlab.in",
        "email_validity_signal": "valid",
        "instagram_handle": "glowlab",
        "primary_profile_url": "https://instagram.com/glowlab",
        "whatsapp_business_link_or_number": "+919999999999",
        "paid_ads_signal": "high",
        "ugc_review_depth_signal": "low",
        "public_review_request_signal": "yes",
        "new_digital_presence_signal": "yes",
        "sampling_feasibility": "yes",
        "social_presence_signal": "high",
        "contact_form_status": "working",
        "response_status": "none",
        "launch_recency_days": 30,
    }


class TestOutreachEngine(unittest.TestCase):
    def test_generates_email_draft_for_priority_lead(self) -> None:
        lead = make_scored_lead()
        lead["persona"] = "founder"
        result = OutreachDraftEngine().run(
            [lead],
            run_context={
                "outreach_run_id": "outreach_run_test_001",
                "sender_name": "Shubham",
                "sender_company": "Trio&Buy",
            },
        )

        self.assertEqual("outreach_run_test_001", result.run_id)
        self.assertEqual(1, len(result.draft_queue))
        draft = result.draft_queue[0]

        self.assertEqual("email", draft.get("channel_selected"))
        self.assertEqual("pending_review", draft.get("review_status"))
        self.assertEqual("not_sent", draft.get("send_status"))
        self.assertEqual("T1", draft.get("template_id"))
        self.assertIn("Trio Box", draft.get("message_draft", ""))

    def test_skips_non_priority_lead(self) -> None:
        lead = make_scored_lead()
        lead["priority_bucket"] = "skip"
        result = OutreachDraftEngine().run([lead])

        self.assertEqual(0, len(result.draft_queue))
        self.assertEqual(1, len(result.skipped_outreach))
        self.assertEqual("not_priority_bucket", result.skipped_outreach[0].get("reason"))

    def test_skips_if_outreach_already_started(self) -> None:
        lead = make_scored_lead()
        lead["outreach_status"] = "sent"
        result = OutreachDraftEngine().run([lead])

        self.assertEqual(0, len(result.draft_queue))
        self.assertEqual("outreach_already_started", result.skipped_outreach[0].get("reason"))

    def test_falls_back_to_instagram_when_email_not_valid(self) -> None:
        lead = make_scored_lead()
        lead["email_validity_signal"] = "invalid"
        result = OutreachDraftEngine().run([lead])

        self.assertEqual(1, len(result.draft_queue))
        draft = result.draft_queue[0]
        self.assertEqual("instagram_dm", draft.get("channel_selected"))
        self.assertIn(draft.get("template_id"), {"T2", "T4"})

    def test_skips_when_no_reachable_channel(self) -> None:
        lead = make_scored_lead()
        lead["contact_channels_available"] = ["email"]
        lead["email_validity_signal"] = "invalid"
        lead["instagram_handle"] = None
        lead["primary_profile_url"] = "https://example.com"
        lead["whatsapp_business_link_or_number"] = None

        result = OutreachDraftEngine().run([lead])
        self.assertEqual(0, len(result.draft_queue))
        self.assertEqual("no_reachable_channel", result.skipped_outreach[0].get("reason"))


if __name__ == "__main__":
    unittest.main()
