"""Tests for reply processing and routing."""

from __future__ import annotations

import unittest

from src.reply import process_replies


class TestReplyProcessor(unittest.TestCase):
    def test_opt_out_updates_suppression(self) -> None:
        replies = [
            {
                "lead_id": "lead_1",
                "reply_text": "Please unsubscribe me.",
                "channel_selected": "email",
                "reply_received_at": "2026-05-17T10:00:00+00:00",
            }
        ]
        lead_by_id = {"lead_1": {"founder_or_growth_email": "lead1@example.com"}}
        outbound_by_lead_id = {}
        suppression_registry = {"emails": {}, "instagram_handles": {}, "whatsapp_numbers": {}}

        result = process_replies(
            replies=replies,
            lead_by_id=lead_by_id,
            outbound_by_lead_id=outbound_by_lead_id,
            suppression_registry=suppression_registry,
        )
        self.assertEqual(1, result.summary["total_replies"])
        self.assertIn("lead1@example.com", result.suppression_registry["emails"])

    def test_positive_routes_to_handoff(self) -> None:
        replies = [{"lead_id": "lead_2", "reply_text": "Interested, let's talk.", "channel_selected": "email"}]
        lead_by_id = {"lead_2": {"brand_name": "X", "category": "beauty", "region": "India"}}
        outbound_by_lead_id = {"lead_2": {"message_subject": "Hi", "message_draft": "Body", "channel_selected": "email"}}
        suppression_registry = {"emails": {}, "instagram_handles": {}, "whatsapp_numbers": {}}

        result = process_replies(
            replies=replies,
            lead_by_id=lead_by_id,
            outbound_by_lead_id=outbound_by_lead_id,
            suppression_registry=suppression_registry,
        )
        self.assertEqual(1, len(result.manual_handoff_queue))
        self.assertEqual("positive", result.manual_handoff_queue[0]["reply_type"])


if __name__ == "__main__":
    unittest.main()

