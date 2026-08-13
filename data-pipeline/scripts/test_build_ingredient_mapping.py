"""
Unit tests for build_ingredient_mapping.py.

Run with: python -m unittest data-pipeline/scripts/test_build_ingredient_mapping.py
(from the repo root, with the venv activated)
"""
import unittest

import pandas as pd

from build_ingredient_mapping import add_normalized_ingredients, build_draft_mapping


class AddNormalizedIngredientsTests(unittest.TestCase):
    def test_adds_normalized_column(self):
        df = pd.DataFrame({"ingredients_p": [["chopped onion", "salt"]]})
        result = add_normalized_ingredients(df)
        self.assertEqual(result["ingredients_normalized"].iloc[0], ["onion", "salt"])

    def test_original_column_untouched(self):
        df = pd.DataFrame({"ingredients_p": [["chopped onion"]]})
        result = add_normalized_ingredients(df)
        self.assertEqual(result["ingredients_p"].iloc[0], ["chopped onion"])


class BuildDraftMappingTests(unittest.TestCase):
    def test_sorted_by_frequency_descending(self):
        strings = ["salt", "salt", "salt", "pepper", "pepper", "sugar"]
        mapping = build_draft_mapping(strings, top_n=10)
        self.assertEqual(list(mapping["raw_string"]), ["salt", "pepper", "sugar"])
        self.assertEqual(list(mapping["frequency"]), [3, 2, 1])

    def test_reviewed_defaults_to_false(self):
        mapping = build_draft_mapping(["salt", "pepper"], top_n=10)
        self.assertTrue((mapping["reviewed"] == False).all())  # noqa: E712

    def test_respects_top_n(self):
        strings = ["a", "b", "b", "c", "c", "c"]
        mapping = build_draft_mapping(strings, top_n=2)
        self.assertEqual(len(mapping), 2)
        self.assertEqual(list(mapping["raw_string"]), ["c", "b"])


if __name__ == "__main__":
    unittest.main()
