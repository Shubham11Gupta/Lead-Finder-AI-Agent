"""Step 16 tests for collection pipeline skeleton."""

from __future__ import annotations

import unittest

from src.collection.pipeline import CollectionPipeline
from src.connectors import MockConnector, RawLeadCandidate


class TestCollectionPipeline(unittest.TestCase):
    def test_pipeline_applies_dedup_and_qualification(self) -> None:
        candidates = [
            RawLeadCandidate(
                source_platform="instagram",
                payload={
                    "brand_name": "Glow Lab",
                    "primary_profile_url": "https://instagram.com/glowlab",
                    "instagram_handle": "glowlab",
                    "category": "beauty",
                    "region": "India",
                },
                evidence_urls=["https://instagram.com/glowlab"],
            ),
            RawLeadCandidate(
                source_platform="google_search",
                payload={
                    "brand_name": "Glow Lab",
                    "primary_profile_url": "https://instagram.com/glowlab",
                    "instagram_handle": "glowlab",
                    "category": "beauty",
                    "region": "India",
                },
                evidence_urls=["https://google.com/search?q=glowlab"],
            ),
            RawLeadCandidate(
                source_platform="instagram",
                payload={
                    "brand_name": "Tech Gadget House",
                    "primary_profile_url": "https://instagram.com/techgadgethouse",
                    "instagram_handle": "techgadgethouse",
                    "category": "electronics",
                    "region": "India",
                },
                evidence_urls=["https://instagram.com/techgadgethouse"],
            ),
            RawLeadCandidate(
                source_platform="website",
                payload={
                    "brand_name": "No Contact Snacks",
                    "primary_profile_url": "https://nocontactsnacks.in",
                    "category": "snacks",
                    "region": "India",
                },
                evidence_urls=["https://nocontactsnacks.in/about"],
            ),
        ]

        pipeline = CollectionPipeline(connectors=[MockConnector("mock", candidates)])
        result = pipeline.run(run_context={"run_id": "run_test_001"})

        self.assertEqual("run_test_001", result.run_id)
        self.assertEqual(4, len(result.raw_discovered_leads))
        self.assertEqual(1, len(result.qualified_leads_ready_for_scoring))

        skip_reasons = result.run_summary.get("skip_reasons", {})
        self.assertEqual(1, skip_reasons.get("duplicate_merged"))
        self.assertEqual(1, skip_reasons.get("non_consumable_category"))
        self.assertEqual(1, skip_reasons.get("no_reachable_channel"))

    def test_pipeline_routes_schema_invalid_records_to_skipped(self) -> None:
        candidates = [
            RawLeadCandidate(
                source_platform="instagram",
                payload={
                    "brand_name": "Invalid Stage Brand",
                    "primary_profile_url": "https://instagram.com/invalidstagebrand",
                    "instagram_handle": "invalidstagebrand",
                    "category": "nutrition",
                    "region": "India",
                    "stage": "series_b",
                },
                evidence_urls=["https://instagram.com/invalidstagebrand"],
            )
        ]

        pipeline = CollectionPipeline(connectors=[MockConnector("mock", candidates)])
        result = pipeline.run(run_context={"run_id": "run_test_002"})

        self.assertEqual(0, len(result.qualified_leads_ready_for_scoring))
        self.assertEqual(1, len(result.skipped_leads))
        self.assertEqual("invalid_schema", result.skipped_leads[0].get("reason"))


if __name__ == "__main__":
    unittest.main()

