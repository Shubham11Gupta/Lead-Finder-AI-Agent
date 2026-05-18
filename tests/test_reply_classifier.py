"""Tests for deterministic reply classification."""

from __future__ import annotations

import unittest

from src.reply import classify_reply


class TestReplyClassifier(unittest.TestCase):
    def test_classify_opt_out(self) -> None:
        result = classify_reply("lead_1", "Please unsubscribe me from this.")
        self.assertEqual("opt_out", result["reply_type"])
        self.assertTrue(result["do_not_contact"])

    def test_classify_positive(self) -> None:
        result = classify_reply("lead_2", "Yes, interested. Share details.")
        self.assertEqual("positive", result["reply_type"])
        self.assertEqual("handoff_required", result["action_taken"])

    def test_interest_plus_opt_out_becomes_neutral(self) -> None:
        result = classify_reply("lead_3", "Interested, but please stop messaging for now.")
        self.assertEqual("neutral", result["reply_type"])
        self.assertFalse(result["do_not_contact"])


if __name__ == "__main__":
    unittest.main()
