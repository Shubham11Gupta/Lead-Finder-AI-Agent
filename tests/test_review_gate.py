"""Tests for automated review gate."""

from __future__ import annotations

import unittest

from src.review import review_draft_queue


class TestReviewGate(unittest.TestCase):
    def test_approve_clean_email_draft(self) -> None:
        draft_queue = [
            {
                "lead_id": "lead_1",
                "channel_selected": "email",
                "message_subject": "Quick pilot idea",
                "message_draft": (
                    "Hi team, noticed your recent launch activity. "
                    "We help sample-led D2C trials convert into full-size buyers with feedback loops. "
                    "Would you be open to a 15-minute pilot discussion this week?"
                ),
                "personalization_reason": "Selected recent launch signal.",
            }
        ]
        lead_by_id = {"lead_1": {"category": "beauty", "brand_name": "GlowBrand"}}
        result = review_draft_queue(draft_queue=draft_queue, lead_by_id=lead_by_id)
        self.assertEqual(1, result["review_summary"]["approved_count"])
        self.assertEqual("approve", result["reviews"][0]["decision"])

    def test_reject_prohibited_claim(self) -> None:
        draft_queue = [
            {
                "lead_id": "lead_2",
                "channel_selected": "email",
                "message_subject": "Guaranteed conversion lift",
                "message_draft": (
                    "We guarantee 50% conversion lift with no-risk rollout. "
                    "Can we talk this week?"
                ),
                "personalization_reason": "Selected active ads signal.",
            }
        ]
        lead_by_id = {"lead_2": {"category": "snacks", "brand_name": "CrunchX"}}
        result = review_draft_queue(draft_queue=draft_queue, lead_by_id=lead_by_id)
        self.assertEqual(1, result["review_summary"]["rejected_count"])
        self.assertEqual("reject", result["reviews"][0]["decision"])


if __name__ == "__main__":
    unittest.main()

