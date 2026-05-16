"""Tests for SerperConnector internet discovery behavior."""

from __future__ import annotations

import unittest

from src.connectors import SerperConnector


def fake_serper_response(url: str, payload: dict, api_key: str) -> dict:
    if not api_key:
        raise AssertionError("API key should be provided in tests.")
    query = payload.get("q", "")
    if "beauty" in query.lower():
        return {
            "organic": [
                {
                    "title": "Glow Lab | Official Store",
                    "link": "https://glowlab.in",
                    "snippet": "D2C beauty brand",
                },
                {
                    "title": "Glow Lab Instagram",
                    "link": "https://instagram.com/glowlab",
                    "snippet": "Instagram profile",
                },
            ]
        }
    return {
        "organic": [
            {
                "title": "PetJoy India - Home",
                "link": "https://petjoy.in",
                "snippet": "Pet care products",
            }
        ]
    }


class TestSerperConnector(unittest.TestCase):
    def test_discover_from_query_list(self) -> None:
        connector = SerperConnector(api_key="test-key", http_post=fake_serper_response)
        candidates = connector.discover(
            run_context={
                "serper_queries": [
                    {"query": "d2c beauty india", "category": "beauty", "region": "India"},
                    {"query": "d2c pet care india", "category": "pet care", "region": "India"},
                ]
            }
        )

        self.assertEqual(3, len(candidates))
        first = candidates[0]
        self.assertEqual("serper", first.source_platform)
        self.assertEqual("Glow Lab", first.payload.get("brand_name"))
        self.assertEqual("beauty", first.payload.get("category"))

        ig_candidate = next(c for c in candidates if c.payload.get("instagram_handle") == "glowlab")
        self.assertIn("instagram_dm", ig_candidate.payload.get("contact_channels_available", []))
        self.assertEqual("social_first_unregistered", ig_candidate.payload.get("brand_presence_type"))

    def test_requires_queries(self) -> None:
        connector = SerperConnector(api_key="test-key", http_post=fake_serper_response)
        with self.assertRaises(ValueError):
            connector.discover(run_context={})

    def test_requires_api_key(self) -> None:
        connector = SerperConnector(api_key=None, http_post=fake_serper_response)
        with self.assertRaises(ValueError):
            connector.discover(run_context={"serper_queries": ["d2c beauty india"]})


if __name__ == "__main__":
    unittest.main()

