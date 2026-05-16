"""Tests for InstagramFileConnector."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src.connectors import InstagramFileConnector


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestInstagramFileConnector(unittest.TestCase):
    def test_discovers_from_csv(self) -> None:
        connector = InstagramFileConnector(FIXTURES_DIR / "instagram_candidates.csv")
        candidates = connector.discover()

        self.assertEqual(2, len(candidates))
        first = candidates[0]
        self.assertEqual("instagram", first.source_platform)
        self.assertEqual("Glow Lab", first.payload.get("brand_name"))
        self.assertEqual("glowlab", first.payload.get("instagram_handle"))
        self.assertEqual("https://instagram.com/glowlab", first.payload.get("primary_profile_url"))
        self.assertIn("https://instagram.com/p/example1", first.evidence_urls)

    def test_discovers_from_jsonl(self) -> None:
        connector = InstagramFileConnector(FIXTURES_DIR / "instagram_candidates.jsonl")
        candidates = connector.discover()

        self.assertEqual(2, len(candidates))
        second = candidates[1]
        self.assertEqual("SnackRoot", second.payload.get("brand_name"))
        self.assertEqual("https://instagram.com/snackroot", second.payload.get("primary_profile_url"))

    def test_run_context_path_override(self) -> None:
        connector = InstagramFileConnector(FIXTURES_DIR / "instagram_candidates.csv")
        candidates = connector.discover(
            run_context={"instagram_input_path": str(FIXTURES_DIR / "instagram_candidates.jsonl")}
        )
        self.assertEqual(2, len(candidates))
        self.assertEqual("PetJoy", candidates[0].payload.get("brand_name"))

    def test_missing_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_path = Path(tmp_dir) / "missing.csv"
            connector = InstagramFileConnector(missing_path)
            with self.assertRaises(FileNotFoundError):
                connector.discover()


if __name__ == "__main__":
    unittest.main()

