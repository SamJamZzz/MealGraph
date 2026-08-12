"""
Unit tests for parse_recipes.py.

Run with: python -m unittest data-pipeline/scripts/test_parse_recipes.py
(from the repo root, with the venv activated)
"""
import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from parse_recipes import (
    DAILY_VALUES,
    NUTRITION_FIELDS,
    compute_gram_columns,
    expand_nutrition,
    parse_list_string,
    process_recipes,
)


class ParseListStringTests(unittest.TestCase):
    def test_valid_list_string(self):
        self.assertEqual(parse_list_string("['onion', 'garlic']"), ["onion", "garlic"])

    def test_valid_numeric_list_string(self):
        self.assertEqual(parse_list_string("[1.0, 2.0, 3.0]"), [1.0, 2.0, 3.0])

    def test_nan_returns_default(self):
        self.assertEqual(parse_list_string(float("nan")), [])

    def test_nan_with_none_default_falls_back_to_empty_list(self):
        # default=None is documented as "use the standard [] default", not literal None
        self.assertEqual(parse_list_string(float("nan"), default=None), [])

    def test_nan_with_explicit_default(self):
        self.assertEqual(parse_list_string(float("nan"), default="missing"), "missing")

    def test_malformed_string_returns_default(self):
        self.assertEqual(parse_list_string("not a list"), [])

    def test_already_a_list_passes_through(self):
        self.assertEqual(parse_list_string(["a", "b"]), ["a", "b"])

    def test_non_string_non_list_returns_default(self):
        self.assertEqual(parse_list_string(42), [])


class ExpandNutritionTests(unittest.TestCase):
    def test_valid_seven_element_list(self):
        result = expand_nutrition([51.5, 0.0, 13.0, 0.0, 2.0, 0.0, 4.0])
        self.assertEqual(result["calories"], 51.5)
        self.assertEqual(result["protein_pdv"], 2.0)
        self.assertEqual(result["carbohydrates_pdv"], 4.0)

    def test_wrong_length_list_returns_na(self):
        result = expand_nutrition([1.0, 2.0])
        self.assertTrue(all(pd.isna(result[field]) for field in NUTRITION_FIELDS))

    def test_non_list_returns_na(self):
        result = expand_nutrition(None)
        self.assertTrue(all(pd.isna(result[field]) for field in NUTRITION_FIELDS))


class ComputeGramColumnsTests(unittest.TestCase):
    def test_protein_and_saturated_fat_are_exact_conversions(self):
        df = pd.DataFrame({
            "protein_pdv": [100.0],
            "saturated_fat_pdv": [50.0],
            "sodium_pdv": [0.0],
            "total_fat_pdv": [0.0],
            "carbohydrates_pdv": [0.0],
            "sugar_pdv": [0.0],
        })
        result = compute_gram_columns(df)
        self.assertEqual(result["protein_g"].iloc[0], 50.0)
        self.assertEqual(result["saturated_fat_g"].iloc[0], 10.0)

    def test_all_daily_value_columns_are_added(self):
        df = pd.DataFrame({pdv_col: [0.0] for pdv_col, _ in DAILY_VALUES.values()})
        result = compute_gram_columns(df)
        for gram_column in DAILY_VALUES:
            self.assertIn(gram_column, result.columns)


class ProcessRecipesIntegrationTests(unittest.TestCase):
    """Runs the full pipeline against a small synthetic CSV, not the real dataset."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.tmpdir.name) / "sample_recipes.csv"
        self.csv_path.write_text(
            "name,id,minutes,contributor_id,submitted,tags,nutrition,n_steps,steps,"
            "description,ingredients,n_ingredients\n"
            '"test recipe",1,30,123,2020-01-01,'
            '"[\'easy\', \'quick\']","[200.0, 20.0, 10.0, 5.0, 100.0, 40.0, 15.0]",'
            '2,"[\'step one\', \'step two\']","a test recipe",'
            '"[\'egg\', \'flour\']",2\n'
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_row_count_preserved(self):
        df = process_recipes(self.csv_path)
        self.assertEqual(len(df), 1)

    def test_nutrition_columns_present_and_correct(self):
        df = process_recipes(self.csv_path)
        row = df.iloc[0]
        self.assertEqual(row["calories"], 200.0)
        self.assertEqual(row["protein_pdv"], 100.0)
        self.assertTrue(math.isclose(row["protein_g"], 50.0))

    def test_list_columns_parsed(self):
        df = process_recipes(self.csv_path)
        self.assertEqual(df.iloc[0]["ingredients_p"], ["egg", "flour"])


if __name__ == "__main__":
    unittest.main()
