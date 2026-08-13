# USDA FoodData Central mapping — investigation (Phase 1, Step 7)

**Status:** investigated with live API calls against the top 50 most frequent canonical ingredient names, 2026-08-12. `map_to_usda.py`.

## Headline result: coverage is excellent, top-1 relevance is not

**100% match rate** on the top 50 ingredients, both unfiltered and filtered to non-Branded data types (Foundation/SR Legacy/Survey (FNDDS)). FDC search finds *something* for every common ingredient tested.

But match rate alone overstates how usable this is:

- **Unfiltered search defaults heavily to `Branded`** (39/50 top matches) — specific commercial products, not generic reference foods. A "Branded" top match for `"salt"` is one manufacturer's product, not representative of salt as an ingredient.
- **Filtering to non-Branded types fixes that, but surfaces a different problem**: naive top-1 relevance ranking on short, generic queries is unreliable. Examples from the real run:
  - `'salt'` → *"Pecans, salted"* — wrong food entirely.
  - `'pepper'` → *"Pepper steak"* — a prepared dish, not an ingredient.
  - `'garlic cloves'` → *"Spices, cloves, ground"* — conflated "garlic cloves" with "cloves" the spice.
  - vs. `'all-purpose flour'` → *"Flour, wheat, all-purpose, enriched, bleached"* — exactly right.
  - vs. `'brown sugar'` → *"Sugar, brown"* — exactly right.

There's no obvious pattern separating the good matches from the bad ones (multi-word queries aren't uniformly better — `"garlic cloves"` still failed). **Conclusion: automated top-1 matching is not reliable enough to use unreviewed**, for either filtered or unfiltered search.

## Recommendation

Coverage isn't the blocker — relevance is. When it's time to actually populate `canonical_ingredients.fdc_id` (from the schema design), the same approach already chosen for ingredient-name curation applies here: **hand-review matches for the head of the frequency distribution rather than trusting automated top-1 matching**, using non-Branded-filtered search results as *candidates* to review, not answers to accept. This is consistent with the project's existing principle of not letting an unreviewed automated process be the source of truth for data that downstream nutrition claims depend on.

## API reliability findings (relevant to any future implementation)

- **USDA's gateway returns intermittent bare `400 Bad Request` (nginx, no JSON body) for requests that succeed identically on retry.** Confirmed not rate-limiting (`X-RateLimit-Remaining` stayed above 3,300 of 3,600 throughout this investigation) and not a deterministic parameter problem (the exact same request failed and succeeded across repeated attempts). A production implementation needs retry logic with backoff; this investigation's `search_food()` retries up to 6 times.
- **Prefer a single comma-joined `dataType` value over passing a list to `requests`** (which encodes as repeated `dataType=X&dataType=Y` query keys) — the comma-joined form failed less often in testing, though the gateway's underlying flakiness wasn't fully eliminated either way.
- **Cache API responses locally and save incrementally**, not just once at the end of a batch — a mid-batch failure previously discarded all progress from that run before this was fixed.

## Security note

While debugging a request failure during this investigation, the FDC API key was briefly exposed in a raised exception's message (`response.raise_for_status()` embeds the full request URL, including `api_key`, into its error text). This was caught and fixed — errors are now constructed from `response.status_code`/`response.text` only, never the URL. **Recommend rotating the key** at https://fdc.nal.usda.gov/api-guide as a precaution; this is a low-stakes credential (free API, no payment or personal data attached), but the key did appear in this session's output.
