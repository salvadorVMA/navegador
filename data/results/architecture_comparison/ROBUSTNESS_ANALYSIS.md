# Robustness Analysis: Why NEW Architecture is "Less Tolerant"

## The Problem Explained

### What "Less Tolerant" Means

**NEW Architecture (analytical_essay):**
```python
# In quantitative_engine.py, line 185-187:
if var_id not in tables:
    print(f"Warning: Variable {var_id} not found in df_tables")
    return None  # ← STRICT: Variable not found = skip it
```

**Behavior:**
- ✅ **Accurate:** Only uses variables that actually exist
- ❌ **Brittle:** Typo in variable code → variable skipped
- ❌ **Fails completely:** All variables wrong → empty report → analysis fails

### Example: The Q5 Case

**Input:** `['p1|CUP', 'p2|CUP', 'p3|CUP', 'p5|CUP']` (wrong code)

**NEW Architecture Response:**
```
Warning: Variable p1|CUP not found in df_tables
Warning: Variable p2|CUP not found in df_tables
Warning: Variable p3|CUP not found in df_tables
Warning: Variable p5|CUP not found in df_tables
[analytical_essay] Quantitative report: 0 variables
❌ FAILED - No valid variables found
```

**OLD Architecture Response:**
```
[Uses ChromaDB semantic search]
[Finds content about "CUP", "political culture", "democracy"]
✅ SUCCESS - Generated analysis with related content
```

---

## Why Each Architecture Behaves This Way

### OLD Architecture: Semantic Robustness

**Technology:** ChromaDB vector database with semantic embeddings

```python
# In detailed_analysis.py (simplified):
# 1. Embed the user query
query_embedding = embed("political culture democracy")

# 2. Find semantically similar content
results = chromadb.query(
    query_embeddings=[query_embedding],
    n_results=100
)
# ✅ Finds documents RELATED to the query even if codes are wrong
```

**Strengths:**
- 🟢 **Fuzzy matching:** Finds related content even with wrong codes
- 🟢 **Exploratory:** Good for "show me anything about X"
- 🟢 **Forgiving:** Typos and mistakes don't break the system

**Weaknesses:**
- 🔴 **Accuracy risk:** Might retrieve wrong but similar-sounding data
- 🔴 **Silent errors:** User doesn't know they got different data than requested
- 🔴 **Unpredictable:** Different runs might return different variables

---

### NEW Architecture: Strict Validation

**Technology:** Direct dictionary lookup in df_tables

```python
# In quantitative_engine.py, line 185:
if var_id not in tables:  # Exact match only!
    return None
```

**Strengths:**
- 🟢 **Guaranteed accuracy:** Only processes requested variables
- 🟢 **Reproducible:** Same input → same output (deterministic)
- 🟢 **Explicit errors:** User knows immediately when codes are wrong
- 🟢 **No hallucination:** Won't analyze wrong data

**Weaknesses:**
- 🔴 **Brittle:** Single typo breaks everything
- 🔴 **User-unfriendly:** No suggestions or autocorrect
- 🔴 **All-or-nothing:** If all variables wrong → complete failure

---

## The Trade-off

This is a **design choice**, not a bug:

| Scenario | OLD (Semantic) | NEW (Strict) | Better Choice |
|----------|----------------|--------------|---------------|
| User knows exact codes | ✅ Works | ✅ Works | NEW (faster, deterministic) |
| User has typo in one code | ✅ Works (semantic fallback) | ⚠️ Partial (skips bad variable) | OLD |
| User has all codes wrong | ✅ Works (finds related) | ❌ Fails | OLD |
| User wants EXACT variables | ⚠️ Might get different data | ✅ Gets exact data | NEW |
| Exploratory analysis | ✅ Great | ❌ Poor | OLD |
| Production/auditable | ⚠️ Unpredictable | ✅ Reproducible | NEW |

---

## How to Make NEW Architecture More Robust

### Solution 1: Fuzzy Matching with Suggestions ⭐ **Recommended**

Add a fallback that suggests corrections when variables are missing:

```python
def find_closest_variable(var_id: str, all_variables: List[str]) -> Optional[str]:
    """
    Find the closest matching variable using fuzzy string matching.

    Example:
        var_id = "p1|CUP"
        all_variables = [..., "p1|CUL", ...]
        → Returns "p1|CUL" (1 character difference)
    """
    from difflib import get_close_matches

    # Extract just the survey code part
    if '|' in var_id:
        var_part, wrong_code = var_id.split('|')

        # Find variables with same question number but different survey codes
        candidates = [v for v in all_variables if v.startswith(f"{var_part}|")]

        if candidates:
            matches = get_close_matches(var_id, candidates, n=1, cutoff=0.6)
            return matches[0] if matches else None

    # Fallback: general fuzzy match
    matches = get_close_matches(var_id, all_variables, n=1, cutoff=0.8)
    return matches[0] if matches else None


def build_quantitative_report_robust(
    selected_variables: List[str],
    auto_correct: bool = True,  # NEW parameter
    df_tables_override: Optional[Dict] = None,
    pregs_dict_override: Optional[Dict] = None
) -> QuantitativeReport:
    """Enhanced version with fuzzy matching."""

    tables = df_tables_override if df_tables_override is not None else _get_df_tables()
    all_var_ids = list(tables.keys())

    variables = []
    corrections = []  # Track what we corrected

    for var_id in selected_variables:
        if var_id in tables:
            # Exact match - process normally
            stats = compute_variable_statistics(var_id, df_tables_override, pregs_dict_override)
            if stats:
                variables.append(stats)

        elif auto_correct:
            # Try fuzzy match
            suggested = find_closest_variable(var_id, all_var_ids)

            if suggested:
                print(f"⚠️  Variable {var_id} not found")
                print(f"   → Using similar variable: {suggested}")
                corrections.append((var_id, suggested))

                stats = compute_variable_statistics(suggested, df_tables_override, pregs_dict_override)
                if stats:
                    variables.append(stats)
            else:
                print(f"❌ Variable {var_id} not found and no close match available")
        else:
            # Strict mode - just skip
            print(f"Warning: Variable {var_id} not found in df_tables")

    # Rest of the function remains the same...
    if not variables:
        error_msg = "No valid variables found for analysis."
        if corrections:
            error_msg += f" Attempted corrections: {corrections}"

        return QuantitativeReport(
            variable_count=0,
            variables=[],
            shape_summary={"consensus": 0, "lean": 0, "polarized": 0, "dispersed": 0},
            divergence_index=0.0,
            overall_narrative=error_msg,
        )

    # ... continue with normal processing
```

**Example Output with Q5 Bug:**
```
⚠️  Variable p1|CUP not found
   → Using similar variable: p1|CUL
⚠️  Variable p2|CUP not found
   → Using similar variable: p2|CUL
⚠️  Variable p3|CUP not found
   → Using similar variable: p3|CUL
⚠️  Variable p5|CUP not found
   → Using similar variable: p5|CUL

✅ Analysis succeeded with 4 corrected variables
```

---

### Solution 2: Survey Code Validation Layer

Add validation BEFORE sending to quantitative engine:

```python
def validate_and_correct_variables(
    variable_ids: List[str],
    available_surveys: Dict[str, str]  # {"CUL": "CULTURA_POLITICA", ...}
) -> Tuple[List[str], List[str]]:
    """
    Validate variable codes and suggest corrections.

    Returns:
        (valid_variables, warnings)
    """
    from difflib import get_close_matches

    valid = []
    warnings = []

    for var_id in variable_ids:
        if '|' not in var_id:
            warnings.append(f"Invalid format: {var_id} (expected 'pX|CODE')")
            continue

        var_part, survey_code = var_id.split('|')

        # Check if survey code exists
        if survey_code not in available_surveys:
            # Find closest survey code
            close_codes = get_close_matches(survey_code, available_surveys.keys(), n=1, cutoff=0.6)

            if close_codes:
                suggested_code = close_codes[0]
                corrected = f"{var_part}|{suggested_code}"
                warnings.append(
                    f"Survey code '{survey_code}' not found. "
                    f"Did you mean '{suggested_code}' ({available_surveys[suggested_code]})? "
                    f"Using {corrected}"
                )
                valid.append(corrected)
            else:
                warnings.append(f"Unknown survey code: {survey_code}")
        else:
            valid.append(var_id)

    return valid, warnings


# Usage in analytical_essay.py:
def generate_analytical_essay_robust(
    selected_variables: List[str],
    user_query: str,
    auto_correct: bool = True,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
    temperature: float = 0.4,
) -> dict:
    """Enhanced with validation."""

    if auto_correct:
        from dataset_knowledge import enc_nom_dict

        # Validate and correct survey codes
        corrected_vars, warnings = validate_and_correct_variables(
            selected_variables,
            {code: name for name, code in enc_nom_dict.items()}
        )

        # Show warnings to user
        for warning in warnings:
            print(f"⚠️  {warning}")

        # Use corrected variables
        selected_variables = corrected_vars

    # Continue with normal processing...
    quant_report = build_quantitative_report(selected_variables)
    # ...
```

**Example Output:**
```
⚠️  Survey code 'CUP' not found. Did you mean 'CUL' (CULTURA_POLITICA)? Using p1|CUL
⚠️  Survey code 'CUP' not found. Did you mean 'CUL' (CULTURA_POLITICA)? Using p2|CUL
...
✅ Proceeding with 4 corrected variables
```

---

### Solution 3: Hybrid Approach ⭐ **Best of Both Worlds**

Combine strict validation with semantic fallback:

```python
def build_quantitative_report_hybrid(
    selected_variables: List[str],
    user_query: str,  # NEW: needed for semantic fallback
    fallback_to_semantic: bool = True,
    min_variables: int = 2,
) -> QuantitativeReport:
    """
    1. Try exact match (strict mode)
    2. If too few variables found, use semantic search as fallback
    3. Return combined results with metadata about what was used
    """

    # Phase 1: Strict matching
    strict_variables = []
    for var_id in selected_variables:
        stats = compute_variable_statistics(var_id)
        if stats:
            strict_variables.append(stats)

    # Check if we have enough
    if len(strict_variables) >= min_variables:
        # Success with strict matching!
        return create_report(strict_variables, source="exact_match")

    # Phase 2: Semantic fallback (if enabled)
    if fallback_to_semantic and user_query:
        print(f"⚠️  Only {len(strict_variables)} exact matches found.")
        print(f"   Falling back to semantic search for query: {user_query}")

        # Use ChromaDB to find related variables
        from variable_selector import retrieve_all_types_simultaneously
        semantic_vars = retrieve_all_types_simultaneously(
            db_f1,
            query_emb=embed(user_query),
            n_results=10
        )

        # Combine: exact matches + semantic matches (avoiding duplicates)
        combined = strict_variables.copy()
        seen_ids = {v.var_id for v in strict_variables}

        for var_id in semantic_vars:
            if var_id not in seen_ids:
                stats = compute_variable_statistics(var_id)
                if stats:
                    combined.append(stats)
                    seen_ids.add(var_id)

        return create_report(
            combined,
            source="hybrid",
            metadata={"exact_matches": len(strict_variables), "semantic_additions": len(combined) - len(strict_variables)}
        )

    # No fallback or not enough variables even with fallback
    return create_empty_report("Insufficient variables for analysis")
```

**Example Output:**
```
⚠️  Only 0 exact matches found.
   Falling back to semantic search for query: democracia instituciones políticas

Found 8 related variables:
  - p1|CUL (exact: No, semantic match: 0.89)
  - p2|CUL (exact: No, semantic match: 0.87)
  - p3|CUL (exact: No, semantic match: 0.92)
  ...

✅ Analysis succeeded with 8 variables (0 exact, 8 semantic)
```

---

## Recommendation: Phased Implementation

### Phase 1: Quick Win (1-2 hours)
Implement **Solution 1 (Fuzzy Matching)** in `quantitative_engine.py`:
- Add `find_closest_variable()` function
- Add `auto_correct` parameter to `build_quantitative_report()`
- Default to `auto_correct=True` for user-friendliness

### Phase 2: Better UX (2-3 hours)
Implement **Solution 2 (Survey Code Validation)**:
- Add validation layer in `analytical_essay.py`
- Provide clear, actionable error messages
- Show corrections to user before processing

### Phase 3: Production-Ready (4-5 hours)
Implement **Solution 3 (Hybrid Approach)**:
- Combine strict + semantic approaches
- Add metadata to reports about data source
- Give users control via `strict_mode` flag

---

## Summary

**"Less Tolerant" means:**
- NEW uses **exact dictionary lookup** (strict)
- OLD uses **semantic search** (fuzzy)

**This is a feature, not a bug:**
- Strict mode = accurate, reproducible, auditable
- Semantic mode = exploratory, forgiving, flexible

**Making NEW more robust doesn't mean:**
- ❌ Removing strict validation
- ❌ Always using semantic fallback
- ❌ Sacrificing accuracy for convenience

**It means:**
- ✅ Adding fuzzy matching for typos
- ✅ Providing helpful error messages
- ✅ Offering fallback options with user consent
- ✅ Being explicit about what data is actually used

The goal: **"Strict by default, helpful when things go wrong"**
