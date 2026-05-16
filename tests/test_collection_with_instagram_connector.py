"""Integration-style test for CollectionPipeline with InstagramFileConnector."""

from __future__ import annotations

from pathlib import Path
import unittest

from src.collection import CollectionPipeline
from src.connectors import InstagramFileConnector


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestCollectionWithInstagramConnector(unittest.TestCase):
    def test_pipeline_accepts_real_instagram_connector(self) -> None:
        connector = InstagramFileConnector(FIXTURES_DIR / "instagram_candidates.csv")
        pipeline = CollectionPipeline([connector])

        result = pipeline.run(run_context={"run_id": "run_instagram_connector_test"})

        self.assertEqual("run_instagram_connector_test", result.run_id)
        self.assertEqual(2, len(result.raw_discovered_leads))
        self.assertEqual(2, len(result.qualified_leads_ready_for_scoring))
        self.assertEqual(0, result.run_summary.get("source_error_count"))


if __name__ == "__main__":
    unittest.main()

