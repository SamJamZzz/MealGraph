"""
Unit tests for map_to_usda.py.

Network calls are mocked -- tests never hit the real FDC API, per the
project's convention of not depending on external/slow resources in
the test suite (see CONTRIBUTING.md).

Run with: python -m unittest data-pipeline/scripts/test_map_to_usda.py
(from the repo root, with the venv activated)
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from map_to_usda import (
    investigate_matches,
    load_api_key,
    load_cache,
    match_quality_summary,
    save_cache,
    search_food,
)


class LoadApiKeyTests(unittest.TestCase):
    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("map_to_usda.load_dotenv"):  # don't let a real .env leak in
                with self.assertRaises(RuntimeError):
                    load_api_key()

    def test_returns_key_when_present(self):
        with patch.dict(os.environ, {"FDC_API_KEY": "test-key-123"}):
            with patch("map_to_usda.load_dotenv"):
                self.assertEqual(load_api_key(), "test-key-123")


class CacheRoundTripTests(unittest.TestCase):
    def test_save_then_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            save_cache(cache_path, {"salt": [{"fdc_id": 1}]})
            self.assertEqual(load_cache(cache_path), {"salt": [{"fdc_id": 1}]})

    def test_missing_file_returns_empty_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "does_not_exist.json"
            self.assertEqual(load_cache(cache_path), {})


class InvestigateMatchesTests(unittest.TestCase):
    def test_uses_cache_instead_of_calling_search_again(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            cache_path.write_text(json.dumps({"salt::unfiltered": [{"fdc_id": 1, "description": "Salt"}]}))

            with patch("map_to_usda.search_food") as mock_search:
                results = investigate_matches(["salt"], "fake-key", cache_path)

            mock_search.assert_not_called()
            self.assertEqual(results["salt"][0]["description"], "Salt")

    def test_calls_search_for_uncached_query_and_persists_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"

            with patch("map_to_usda.search_food", return_value=[{"fdc_id": 2, "description": "Pepper"}]) as mock_search:
                with patch("map_to_usda.time.sleep"):  # don't actually wait in tests
                    results = investigate_matches(["pepper"], "fake-key", cache_path)

            mock_search.assert_called_once_with("pepper", "fake-key", data_types=None)
            self.assertEqual(results["pepper"][0]["description"], "Pepper")
            self.assertEqual(load_cache(cache_path)["pepper::unfiltered"][0]["description"], "Pepper")

    def test_filtered_and_unfiltered_searches_do_not_collide_in_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"

            with patch("map_to_usda.search_food", side_effect=[
                [{"description": "unfiltered result"}],
                [{"description": "filtered result"}],
            ]):
                with patch("map_to_usda.time.sleep"):
                    unfiltered = investigate_matches(["salt"], "fake-key", cache_path)
                    filtered = investigate_matches(["salt"], "fake-key", cache_path, data_types=["Foundation"])

            self.assertEqual(unfiltered["salt"][0]["description"], "unfiltered result")
            self.assertEqual(filtered["salt"][0]["description"], "filtered result")


class SearchFoodRetryTests(unittest.TestCase):
    """
    USDA's gateway was observed to intermittently return a bare 400
    for a request that succeeds identically on retry -- confirmed
    transient during Step 7's investigation, not a parameter bug.
    """

    def test_succeeds_after_transient_failure(self):
        failing_response = MagicMock(ok=False, status_code=400, text="Bad Request")
        succeeding_response = MagicMock(ok=True)
        succeeding_response.json.return_value = {
            "foods": [{"fdcId": 1, "description": "Salt", "dataType": "SR Legacy", "score": 100}]
        }

        with patch("map_to_usda.requests.get", side_effect=[failing_response, succeeding_response]):
            with patch("map_to_usda.time.sleep"):
                results = search_food("salt", "fake-key")

        self.assertEqual(results[0]["description"], "Salt")

    def test_raises_without_leaking_api_key_after_exhausting_retries(self):
        failing_response = MagicMock(ok=False, status_code=400, text="Bad Request")

        with patch("map_to_usda.requests.get", return_value=failing_response):
            with patch("map_to_usda.time.sleep"):
                with self.assertRaises(RuntimeError) as ctx:
                    search_food("salt", "super-secret-key", retries=1)

        self.assertNotIn("super-secret-key", str(ctx.exception))


class MatchQualitySummaryTests(unittest.TestCase):
    def test_computes_match_rate_and_data_type_distribution(self):
        results = {
            "salt": [{"data_type": "SR Legacy"}],
            "garlic": [{"data_type": "Foundation"}],
            "made_up_thing": [],
        }
        summary = match_quality_summary(results)
        self.assertEqual(summary["total_queries"], 3)
        self.assertEqual(summary["queries_with_a_match"], 2)
        self.assertAlmostEqual(summary["match_rate_pct"], 66.7, places=1)
        self.assertEqual(
            summary["top_match_data_type_distribution"],
            {"SR Legacy": 1, "Foundation": 1},
        )


if __name__ == "__main__":
    unittest.main()
