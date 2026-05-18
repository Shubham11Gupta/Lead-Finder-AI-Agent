"""Tests for analytics snapshot calculations."""

from __future__ import annotations

import unittest

from src.analytics import build_daily_metrics_snapshot


class TestAnalyticsMetrics(unittest.TestCase):
    def test_basic_metric_computation(self) -> None:
        collection_result = {"run_summary": {"discovered_count": 10, "qualified_count": 5}}
        scoring_result = {
            "scored_leads": [
                {"priority_bucket": "A"},
                {"priority_bucket": "A"},
                {"priority_bucket": "B"},
            ]
        }
        outreach_result = {"draft_queue": [{}, {}, {}]}
        review_result = {"review_summary": {"approved_count": 2}}
        dispatch_log = {
            "events": [
                {"status": "sent", "channel_selected": "email"},
                {"status": "draft_created", "channel_selected": "email"},
            ]
        }
        reply_result = {"reply_log": [{"reply_type": "positive"}], "summary": {"category_counts": {"positive": 1}}}

        metrics = build_daily_metrics_snapshot(
            collection_result=collection_result,
            scoring_result=scoring_result,
            outreach_result=outreach_result,
            review_result=review_result,
            dispatch_log=dispatch_log,
            reply_result=reply_result,
        )
        self.assertEqual(10, metrics["funnel_counts"]["discovered"])
        self.assertEqual(2, metrics["funnel_counts"]["sent"])
        self.assertEqual(1, metrics["funnel_counts"]["positive_reply"])
        self.assertGreater(metrics["rates"]["qualification_rate"], 0)


if __name__ == "__main__":
    unittest.main()

