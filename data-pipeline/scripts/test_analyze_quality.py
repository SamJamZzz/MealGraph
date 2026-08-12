"""
Unit tests for analyze_quality.py.

Run with: python -m unittest data-pipeline/scripts/test_analyze_quality.py
(from the repo root, with the venv activated)
"""
import unittest

import pandas as pd

from analyze_quality import (
    duplicate_ingredient_recipes,
    duplicate_recipe_report,
    missing_value_report,
    outlier_report,
    popularity_report,
    value_frequency,
)


class MissingValueReportTests(unittest.TestCase):
    def test_reports_only_columns_with_missing_values(self):
        df = pd.DataFrame({"a": [1, None, 3], "b": [1, 2, 3]})
        report = missing_value_report(df)
        self.assertEqual(list(report.index), ["a"])
        self.assertEqual(report.loc["a", "missing_count"], 1)

    def test_no_missing_values_returns_empty(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        self.assertTrue(missing_value_report(df).empty)


class DuplicateRecipeReportTests(unittest.TestCase):
    def test_detects_duplicate_ids_and_names(self):
        df = pd.DataFrame({
            "id": [1, 1, 2],
            "name": ["Chili", "chili ", "Soup"],
        })
        report = duplicate_recipe_report(df)
        self.assertEqual(report["duplicate_ids"], 1)
        self.assertEqual(report["duplicate_names"], 1)

    def test_no_duplicates(self):
        df = pd.DataFrame({"id": [1, 2], "name": ["Chili", "Soup"]})
        report = duplicate_recipe_report(df)
        self.assertEqual(report["duplicate_ids"], 0)
        self.assertEqual(report["duplicate_names"], 0)

    def test_handles_list_typed_columns_without_crashing(self):
        # pandas' duplicated() can't hash list values (tags_p/steps_p/
        # ingredients_p) -- this must not raise TypeError.
        df = pd.DataFrame({
            "id": [1, 2],
            "name": ["Chili", "Soup"],
            "ingredients_p": [["egg", "flour"], ["salt"]],
        })
        report = duplicate_recipe_report(df)
        self.assertEqual(report["exact_duplicate_rows"], 0)


class DuplicateIngredientRecipesTests(unittest.TestCase):
    def test_counts_recipes_with_repeated_ingredient(self):
        df = pd.DataFrame({
            "ingredients_p": [["salt", "salt", "pepper"], ["egg", "flour"]]
        })
        self.assertEqual(duplicate_ingredient_recipes(df), 1)


class OutlierReportTests(unittest.TestCase):
    def test_flags_extreme_values(self):
        series = pd.Series([10, 11, 12, 9, 10, 11, 10, 100_000])
        report = outlier_report(series)
        self.assertEqual(report["outlier_count"], 1)
        self.assertEqual(report["max"], 100_000)

    def test_no_outliers_in_tight_distribution(self):
        series = pd.Series([10, 11, 12, 9, 10, 11, 10, 9])
        report = outlier_report(series)
        self.assertEqual(report["outlier_count"], 0)


class ValueFrequencyTests(unittest.TestCase):
    def test_counts_across_lists(self):
        column = pd.Series([["egg", "flour"], ["egg", "milk"], ["egg"]])
        result = value_frequency(column, top_n=2)
        self.assertEqual(result["egg"], 3)
        self.assertEqual(len(result), 2)


class PopularityReportTests(unittest.TestCase):
    def test_zero_interaction_recipes_counted(self):
        recipes_df = pd.DataFrame({"id": [1, 2, 3]})
        interactions_df = pd.DataFrame({
            "recipe_id": [1, 1, 2],
            "rating": [5, 4, 3],
        })
        report = popularity_report(recipes_df, interactions_df)
        self.assertEqual(report["recipes_with_zero_interactions"], 1)


if __name__ == "__main__":
    unittest.main()
