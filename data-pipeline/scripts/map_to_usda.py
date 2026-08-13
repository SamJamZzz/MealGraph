"""
Investigates USDA FoodData Central mapping feasibility for the
curated ingredient list (Phase 1, Step 7).

This is an INVESTIGATION, not a production mapping: it queries FDC
search for a sample of canonical ingredient names and reports match
quality, so we know whether this approach is viable before building
it out for the full ingredient list. Responses are cached locally
(data-pipeline/processed/fdc_cache.json, gitignored) so repeat runs
don't re-hit the API unnecessarily.

Requires FDC_API_KEY in a local .env file (gitignored -- never commit
the key). Get one at https://fdc.nal.usda.gov/api-guide.
"""
import json
import os
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

FDC_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
REQUEST_DELAY_SECONDS = 2.0
SAMPLE_SIZE = 50

# Non-Branded data types: generic reference foods, not specific
# commercial products. A "Branded" top match for e.g. "salt" is one
# manufacturer's product, not representative of salt as an ingredient.
NON_BRANDED_DATA_TYPES = ["Foundation", "SR Legacy", "Survey (FNDDS)"]


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("FDC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "FDC_API_KEY not found. Add it to a local .env file "
            "(FDC_API_KEY=your_key_here) -- see .gitignore, never commit it."
        )
    return api_key


def search_food(query: str, api_key: str, page_size: int = 3, data_types: list | None = None, retries: int = 6) -> list:
    """
    Query FDC search for `query`, returning up to `page_size` simplified
    results. `data_types` optionally restricts results to specific FDC
    dataType values (e.g. ["Foundation", "SR Legacy", "Survey (FNDDS)"]
    to exclude "Branded" -- commercial products, whose nutrition
    profiles don't represent a generic ingredient well).

    Retries on failure: USDA's gateway is unreliable when `dataType`
    is present as a repeated query parameter (requests' default list
    encoding) -- every observed 400 during this investigation happened
    on a data_types-filtered call, never an unfiltered one. Sending it
    as a single comma-joined value instead is both more standard and
    more reliable in practice; retries remain as a safety net.
    """
    params = {"api_key": api_key, "query": query, "pageSize": page_size}
    if data_types:
        params["dataType"] = ",".join(data_types)

    last_error = None
    for attempt in range(retries + 1):
        response = requests.get(FDC_SEARCH_URL, params=params, timeout=10)
        if response.ok:
            data = response.json()
            return [
                {
                    "fdc_id": food.get("fdcId"),
                    "description": food.get("description"),
                    "data_type": food.get("dataType"),
                    "score": food.get("score"),
                }
                for food in data.get("foods", [])
            ]

        # response.raise_for_status()'s message embeds the full request
        # URL, which includes api_key as a query parameter -- never let
        # that reach an exception message, a log, or stdout.
        last_error = f"HTTP {response.status_code} -- {response.text[:300]}"
        if attempt < retries:
            time.sleep(1)

    raise RuntimeError(f"FDC search failed for {query!r} after {retries + 1} attempts: {last_error}")


def load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    return {}


def save_cache(cache_path: Path, cache: dict) -> None:
    cache_path.write_text(json.dumps(cache, indent=2))


def _cache_key(query: str, data_types: list | None = None) -> str:
    """
    Cache key includes the data_types filter -- a filtered and
    unfiltered search for the same query can return different
    results, so they must not collide in the cache.
    """
    suffix = ",".join(data_types) if data_types else "unfiltered"
    return f"{query}::{suffix}"


def investigate_matches(queries: list, api_key: str, cache_path: Path, data_types: list | None = None) -> dict:
    """
    Search FDC for each query, using/populating a local cache.

    Saves the cache after every new (non-cached) result, not just once
    at the end -- USDA's gateway has observed transient failures
    partway through a batch, and without incremental saving, a later
    failure would discard all earlier progress in the same run.
    """
    cache = load_cache(cache_path)
    results = {}

    for query in queries:
        key = _cache_key(query, data_types)
        if key in cache:
            results[query] = cache[key]
            continue

        matches = search_food(query, api_key, data_types=data_types)
        cache[key] = matches
        results[query] = matches
        save_cache(cache_path, cache)
        time.sleep(REQUEST_DELAY_SECONDS)

    return results


def match_quality_summary(results: dict) -> dict:
    """Aggregate stats: match rate, and what data_type the top match came from."""
    matched = sum(1 for matches in results.values() if matches)
    data_types = Counter(
        matches[0]["data_type"] for matches in results.values() if matches
    )

    return {
        "total_queries": len(results),
        "queries_with_a_match": matched,
        "match_rate_pct": round(matched / len(results) * 100, 1) if results else 0,
        "top_match_data_type_distribution": dict(data_types),
    }


def main() -> None:
    api_key = load_api_key()

    base_dir = Path(__file__).resolve().parent
    mapping_path = base_dir.parent / "processed" / "ingredient_mapping_draft.csv"
    cache_path = base_dir.parent / "processed" / "fdc_cache.json"

    mapping_df = pd.read_csv(mapping_path)
    sample = mapping_df["canonical_name"].drop_duplicates().head(SAMPLE_SIZE).tolist()

    print(f"Investigating FDC matches for {len(sample)} ingredients (unfiltered)...")
    unfiltered_results = investigate_matches(sample, api_key, cache_path)

    print(f"Investigating FDC matches for {len(sample)} ingredients (non-Branded only)...")
    filtered_results = investigate_matches(sample, api_key, cache_path, data_types=NON_BRANDED_DATA_TYPES)

    print("\n=== Sample Matches, unfiltered vs. non-Branded (first 15) ===")
    for query in sample[:15]:
        top_unfiltered = unfiltered_results[query][0] if unfiltered_results[query] else None
        top_filtered = filtered_results[query][0] if filtered_results[query] else None
        print(f"{query!r}")
        print(f"    unfiltered:   {top_unfiltered['description'] if top_unfiltered else 'NO MATCH'} "
              f"({top_unfiltered['data_type'] if top_unfiltered else '-'})")
        print(f"    non-Branded:  {top_filtered['description'] if top_filtered else 'NO MATCH'} "
              f"({top_filtered['data_type'] if top_filtered else '-'})")

    print("\n=== Match Quality Summary: unfiltered ===")
    for key, value in match_quality_summary(unfiltered_results).items():
        print(f"{key}: {value}")

    print("\n=== Match Quality Summary: non-Branded only ===")
    for key, value in match_quality_summary(filtered_results).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
