"""
Quantitative Engine for Navegador Survey Analysis

Pure computation module that reads df_tables (per-variable frequency distributions)
and produces structured quantitative reports. No LLM calls, no ChromaDB, no network I/O.

The quantitative report is then passed to the LLM for qualitative interpretation
as a dialectical analytical essay.

Key concepts:
- Distribution shape classification: consensus / lean / polarized / dispersed
- HHI (Herfindahl-Hirschman Index): measures response concentration
- Minority opinion detection: flags categories > 15% that aren't the mode
- Divergence index: fraction of variables that are NOT consensus
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field


# Lazy import to avoid loading the full dataset at module level.
# This allows unit tests to mock df_tables and pregs_dict without
# requiring the 191MB data file to be present.
_df_tables = None
_pregs_dict = None

# Bivariate lazy state (loaded on first bivariate call)
_los_mex_preprocessed = None
_enc_nom_dict_rev = None

# SES demographic dimensions used for bivariate breakdowns
SES_DEMOGRAPHIC_VARS = ['sexo', 'edad', 'region', 'empleo']


def _get_df_tables():
    global _df_tables
    if _df_tables is None:
        from dataset_knowledge import df_tables
        _df_tables = df_tables
    return _df_tables


def _get_pregs_dict():
    global _pregs_dict
    if _pregs_dict is None:
        from dataset_knowledge import pregs_dict
        _pregs_dict = pregs_dict
    return _pregs_dict


def _get_los_mex_preprocessed() -> dict:
    """Lazy-load and SES-preprocess los_mex_dict for bivariate analysis."""
    global _los_mex_preprocessed
    if _los_mex_preprocessed is None:
        try:
            from dataset_knowledge import los_mex_dict
            from ses_analysis import AnalysisConfig
            _los_mex_preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
        except Exception as e:
            print(f"[bivariate] Could not load/preprocess los_mex_dict: {e}")
            _los_mex_preprocessed = {}
    return _los_mex_preprocessed


def _get_enc_nom_dict_rev() -> dict:
    """Get reverse mapping survey_code -> survey_name (lazy-loaded)."""
    global _enc_nom_dict_rev
    if _enc_nom_dict_rev is None:
        lmd = _get_los_mex_preprocessed()
        _enc_nom_dict_rev = {v: k for k, v in lmd.get('enc_nom_dict', {}).items()}
    return _enc_nom_dict_rev


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class VariableStatistics(BaseModel):
    """Statistics for a single survey variable, computed from df_tables."""
    var_id: str
    question_text: str
    survey_code: str
    n_categories: int
    frequencies: Dict[str, float]           # category_label -> percentage (0-100)
    modal_response: str
    modal_percentage: float
    runner_up_response: str
    runner_up_percentage: float
    margin: float                           # modal - runner_up (percentage points)
    shape: str                              # consensus | lean | polarized | dispersed
    shape_explanation: str
    minority_opinions: Dict[str, float]     # categories > 15%, excluding mode
    hhi: float                              # Herfindahl-Hirschman Index (0-10000)
    # Phase 2 hook
    bivariate_stats: Optional[Dict[str, Any]] = None


class QuantitativeReport(BaseModel):
    """Aggregated quantitative report for all selected variables."""
    variable_count: int
    variables: List[VariableStatistics]
    shape_summary: Dict[str, int]           # e.g. {"consensus": 2, "polarized": 1}
    divergence_index: float                 # fraction of non-consensus variables
    overall_narrative: str                  # one-sentence characterization
    # Phase 2 hook
    demographic_fault_lines: Optional[Dict[str, Any]] = None
    # Phase 5 hook — cross-dataset simulation-based bivariate
    cross_dataset_bivariate: Optional[Dict[str, Any]] = None


# =============================================================================
# DISTRIBUTION SHAPE CLASSIFICATION
# =============================================================================

def classify_distribution_shape(frequencies: Dict[str, float]) -> Tuple[str, str]:
    """
    Classify the shape of a frequency distribution.

    Rules (applied in order):
    1. consensus:  modal > 65%
    2. lean:       modal between 50% and 65% (inclusive on 50%)
    3. polarized:  top two categories both > 30% and both < 50%
    4. dispersed:  no single category > 40%
    5. lean:       fallback (modal > 40%, doesn't match other criteria)

    Args:
        frequencies: Dict mapping category labels to percentage values (0-100)

    Returns:
        Tuple of (shape_name, human-readable explanation)
    """
    if not frequencies:
        return ("dispersed", "No response data available")

    sorted_values = sorted(frequencies.values(), reverse=True)
    top1 = sorted_values[0]
    top2 = sorted_values[1] if len(sorted_values) > 1 else 0.0

    if top1 > 65:
        return ("consensus", f"Strong consensus: modal response exceeds 65% ({top1:.1f}%)")

    if top1 >= 50:
        return ("lean", f"Leaning toward one view: modal response at {top1:.1f}% (50-65% range)")

    if top1 > 30 and top2 > 30 and top1 < 50 and top2 < 50:
        return ("polarized",
                f"Polarized: top two responses are close ({top1:.1f}% vs {top2:.1f}%), "
                f"opinion is divided")

    if top1 <= 40:
        return ("dispersed",
                f"Dispersed: no single category exceeds 40% (highest: {top1:.1f}%), "
                f"opinions are fragmented")

    # Fallback: modal > 40% but doesn't meet other criteria
    return ("lean", f"Leaning toward one view: modal response at {top1:.1f}%")


# =============================================================================
# CONCENTRATION INDEX
# =============================================================================

def compute_hhi(frequencies: Dict[str, float]) -> float:
    """
    Compute Herfindahl-Hirschman Index from percentage distribution.

    HHI = sum(p_i^2) where p_i are proportions (0-1).
    Result scaled to 0-10000 range (standard HHI scale).

    Reference points:
    - 10000: single category at 100% (perfect concentration)
    - 5000:  two categories at 50% each
    - 2500:  four categories at 25% each
    - 2000:  five categories at 20% each (even distribution)

    Args:
        frequencies: Dict mapping category labels to percentage values (0-100)

    Returns:
        HHI value in 0-10000 range
    """
    if not frequencies:
        return 0.0

    proportions = [v / 100.0 for v in frequencies.values()]
    return sum(p * p for p in proportions) * 10000


# =============================================================================
# PER-VARIABLE STATISTICS
# =============================================================================

def compute_variable_statistics(
    var_id: str,
    df_tables_override: Optional[Dict] = None,
    pregs_dict_override: Optional[Dict] = None
) -> Optional[VariableStatistics]:
    """
    Compute all statistics for a single variable from df_tables.

    Reads df_tables[var_id] which is a pandas DataFrame with:
    - index: response category labels (strings)
    - one column of percentages (weighted, 0-100 scale)

    Args:
        var_id: Variable identifier (e.g., "p5_1|IDE")
        df_tables_override: Optional override for testing (bypasses lazy import)
        pregs_dict_override: Optional override for testing (bypasses lazy import)

    Returns:
        VariableStatistics instance, or None if variable not found
    """
    tables = df_tables_override if df_tables_override is not None else _get_df_tables()
    pregs = pregs_dict_override if pregs_dict_override is not None else _get_pregs_dict()

    if var_id not in tables:
        print(f"Warning: Variable {var_id} not found in df_tables")
        return None

    df = tables[var_id]
    df_clean = df.dropna()

    if df_clean.empty:
        print(f"Warning: Variable {var_id} has no valid data")
        return None

    # Extract frequencies as dict
    values = df_clean.iloc[:, 0]
    frequencies = {str(idx): float(val) for idx, val in values.items()}

    # Sort by value descending
    sorted_freqs = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)

    modal_response = sorted_freqs[0][0]
    modal_percentage = sorted_freqs[0][1]
    runner_up_response = sorted_freqs[1][0] if len(sorted_freqs) > 1 else ""
    runner_up_percentage = sorted_freqs[1][1] if len(sorted_freqs) > 1 else 0.0
    margin = modal_percentage - runner_up_percentage

    # Shape classification
    shape, shape_explanation = classify_distribution_shape(frequencies)

    # Minority opinions: > 15%, excluding mode
    minority_opinions = {
        label: pct for label, pct in frequencies.items()
        if pct > 15.0 and label != modal_response
    }

    # HHI
    hhi = compute_hhi(frequencies)

    # Question text
    question_text = pregs.get(var_id, f"Unknown question ({var_id})")
    survey_code = var_id.split('|')[1] if '|' in var_id else "UNK"

    return VariableStatistics(
        var_id=var_id,
        question_text=question_text,
        survey_code=survey_code,
        n_categories=len(frequencies),
        frequencies=frequencies,
        modal_response=modal_response,
        modal_percentage=modal_percentage,
        runner_up_response=runner_up_response,
        runner_up_percentage=runner_up_percentage,
        margin=margin,
        shape=shape,
        shape_explanation=shape_explanation,
        minority_opinions=minority_opinions,
        hhi=hhi,
    )


# =============================================================================
# FUZZY MATCHING FOR ROBUSTNESS
# =============================================================================

def find_closest_variable(
    var_id: str,
    all_variables: List[str],
    same_survey_code: bool = True
) -> Optional[str]:
    """
    Find the closest matching variable using fuzzy string matching.

    CONSTRAINED: By default, only matches within the same survey code
    to prevent cross-topic substitutions (e.g., p1|MED → p1|FED).

    Args:
        var_id: Variable identifier (e.g., "p1|CUP" - wrong code)
        all_variables: List of all available variable IDs
        same_survey_code: If True, only match within the same survey code (default: True)

    Returns:
        Best match variable ID, or None if no close match found

    Example:
        >>> find_closest_variable("p1|CUP", ["p1|CUL", "p2|CUL", ...])
        "p1|CUL"  # Found match with 1 character difference in survey code
    """
    from difflib import get_close_matches

    if '|' not in var_id:
        matches = get_close_matches(var_id, all_variables, n=1, cutoff=0.8)
        return matches[0] if matches else None

    var_part, survey_code = var_id.split('|', 1)

    if same_survey_code:
        # CONSTRAINED: Only match within the same survey code
        # e.g., p1|MED can match p2|MED or p41|MED, but NOT p1|FED
        candidates = [v for v in all_variables if v.endswith(f"|{survey_code}")]

        if candidates:
            # Among same-code variables, find the closest question number
            matches = get_close_matches(var_id, candidates, n=1, cutoff=0.5)
            if matches:
                return matches[0]

        # If no same-code match, try close survey codes (e.g., CUP → CUL)
        # but ONLY for the same question number
        candidates = [v for v in all_variables if v.startswith(f"{var_part}|")]
        if candidates:
            matches = get_close_matches(var_id, candidates, n=1, cutoff=0.7)
            if matches:
                return matches[0]

        return None
    else:
        # UNCONSTRAINED (legacy behavior): match across any survey code
        candidates = [v for v in all_variables if v.startswith(f"{var_part}|")]
        if candidates:
            matches = get_close_matches(var_id, candidates, n=1, cutoff=0.6)
            if matches:
                return matches[0]

        matches = get_close_matches(var_id, all_variables, n=1, cutoff=0.8)
        return matches[0] if matches else None


# =============================================================================
# RELEVANCE GATE (ChromaDB + Expert Grading)
# =============================================================================

# Lazy-loaded ChromaDB connection
_db_f1 = None


def _get_db_f1():
    """Lazy-load ChromaDB collection for relevance checks."""
    global _db_f1
    if _db_f1 is None:
        from utility_functions import environment_setup, embedding_fun_openai
        _, _db_f1 = environment_setup(embedding_fun_openai)
    return _db_f1


def _build_survey_info_string(var_id: str, db_f1=None) -> str:
    """
    Build a survey information string for a variable using ChromaDB data.

    Retrieves QUESTION, SUMMARY, and IMPLICATIONS from ChromaDB
    (the same data used by the OLD architecture's expert grading system).

    Args:
        var_id: Variable identifier (e.g., "p5_1|IDE")
        db_f1: ChromaDB collection (lazy-loaded if None)

    Returns:
        Formatted string with QUESTION, SUMMARY, and IMPLICATIONS
    """
    if db_f1 is None:
        db_f1 = _get_db_f1()

    pregs = _get_pregs_dict()

    parts = {}

    # Question text from pregs_dict
    question_text = pregs.get(var_id, "")
    if question_text:
        parts["QUESTION"] = question_text

    # Summary and implications from ChromaDB
    for doc_type in ["summary", "implications"]:
        try:
            result = db_f1.get(ids=[f"{var_id}__{doc_type}"])
            if result and result.get('documents') and result['documents'][0]:
                parts[doc_type.upper()] = result['documents'][0]
        except Exception:
            pass

    if not parts:
        return f"Variable {var_id}: No information available"

    return ' '.join(f'{k}: {v}' for k, v in parts.items())


def evaluate_variable_relevance(
    var_id: str,
    user_query: str,
    db_f1=None,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
) -> Tuple[float, str]:
    """
    Evaluate whether a variable is relevant to the user query.

    Uses the same expert grading approach as the OLD architecture's
    variable_selector: retrieves QUESTION + SUMMARY + IMPLICATIONS
    from ChromaDB and asks an LLM to grade relevance 0-3.

    Args:
        var_id: Variable identifier
        user_query: The user's original query
        db_f1: ChromaDB collection (lazy-loaded if None)
        model_name: LLM model for grading (mini for balance of speed and quality)

    Returns:
        Tuple of (grade, explanation) where grade is 0-3
    """
    from variable_selector import (
        create_prompt_grader,
        get_structured_summary_grader_p,
        pattern_format_grader_instrtuctions,
    )

    survey_info = _build_survey_info_string(var_id, db_f1)

    prompt = create_prompt_grader(
        user_query,
        survey_info,
        format_instructions=pattern_format_grader_instrtuctions,
    )

    _, result = get_structured_summary_grader_p(
        prompt,
        model_name=model_name,
        temperature=0.3,
    )

    grade_dict = result.get('GRADE_DICT', {})
    if grade_dict:
        grade = list(grade_dict.keys())[0]
        explanation = list(grade_dict.values())[0]
        return float(grade), str(explanation)

    return 0.0, "Grading failed"


def filter_variables_by_relevance(
    variable_ids: List[str],
    user_query: str,
    model_name: str = 'gpt-4.1-mini-2025-04-14',
    min_grade: float = 1.0,
) -> Tuple[List[str], Dict[str, Tuple[float, str]]]:
    """
    Filter a list of variables by their relevance to the user query.

    Uses ChromaDB + expert grading from the OLD architecture to evaluate
    each variable. Removes variables that score below min_grade.

    Args:
        variable_ids: List of variable IDs to evaluate
        user_query: The user's original query
        model_name: LLM model for grading
        min_grade: Minimum grade to keep (default: 1.0, meaning
                   "some connection" or better)

    Returns:
        Tuple of (filtered_ids, grades_dict) where grades_dict maps
        var_id → (grade, explanation) for all evaluated variables
    """
    db_f1 = _get_db_f1()
    grades = {}
    filtered = []

    print(f"\n=== Relevance Gate: evaluating {len(variable_ids)} variables ===")

    for var_id in variable_ids:
        grade, explanation = evaluate_variable_relevance(
            var_id, user_query, db_f1, model_name
        )
        grades[var_id] = (grade, explanation)

        if grade >= min_grade:
            filtered.append(var_id)
            print(f"  ✅ {var_id}: grade={grade:.0f} — {explanation[:80]}")
        else:
            print(f"  ❌ {var_id}: grade={grade:.0f} (filtered out) — {explanation[:80]}")

    print(f"=== Relevance Gate: {len(filtered)}/{len(variable_ids)} variables passed ===\n")

    return filtered, grades


# =============================================================================
# AGGREGATED REPORT
# =============================================================================

def build_quantitative_report(
    selected_variables: List[str],
    user_query: Optional[str] = None,
    df_tables_override: Optional[Dict] = None,
    pregs_dict_override: Optional[Dict] = None,
    auto_correct: bool = True,
    relevance_filter: bool = True,
) -> QuantitativeReport:
    """
    Build a complete quantitative report for all selected variables.

    ENHANCED:
    - Auto-correction constrained to same survey code (prevents cross-topic subs)
    - Relevance gate using ChromaDB + expert grading (when user_query provided)

    Args:
        selected_variables: List of variable IDs
        user_query: The user's query (enables relevance filtering when provided)
        df_tables_override: Optional override for testing
        pregs_dict_override: Optional override for testing
        auto_correct: If True, attempts to correct typos in variable IDs
        relevance_filter: If True and user_query provided, filters by relevance

    Returns:
        QuantitativeReport instance
    """
    tables = df_tables_override if df_tables_override is not None else _get_df_tables()
    all_var_ids = list(tables.keys())

    # Phase 1: Resolve variable IDs (exact match or constrained auto-correction)
    resolved_ids = []
    corrections = []

    for var_id in selected_variables:
        if var_id in tables:
            resolved_ids.append(var_id)
        elif auto_correct:
            suggested = find_closest_variable(var_id, all_var_ids, same_survey_code=True)
            if suggested:
                print(f"⚠️  Variable '{var_id}' not found")
                print(f"   → Auto-corrected to: '{suggested}' (same survey code)")
                corrections.append((var_id, suggested))
                resolved_ids.append(suggested)
            else:
                print(f"❌ Variable '{var_id}' not found and no same-code match available")
        else:
            print(f"Warning: Variable {var_id} not found in df_tables")

    # Phase 2: Relevance gate (if query provided)
    if user_query and relevance_filter and resolved_ids:
        resolved_ids, relevance_grades = filter_variables_by_relevance(
            resolved_ids, user_query
        )

    # Phase 3: Compute statistics for surviving variables
    variables = []
    for var_id in resolved_ids:
        stats = compute_variable_statistics(var_id, df_tables_override, pregs_dict_override)
        if stats is not None:
            variables.append(stats)

    if not variables:
        return QuantitativeReport(
            variable_count=0,
            variables=[],
            shape_summary={"consensus": 0, "lean": 0, "polarized": 0, "dispersed": 0},
            divergence_index=0.0,
            overall_narrative="No valid variables found for analysis.",
        )

    # Phase 4: Bivariate analysis — demographic breakdowns (non-fatal)
    _enrich_with_bivariate_stats(variables)
    demographic_fault_lines = _compute_demographic_fault_lines(variables)

    # Phase 5: Cross-dataset bivariate simulation (non-fatal, only for cross-survey pairs)
    lmd = _get_los_mex_preprocessed()
    enc_dict_p5 = lmd.get('enc_dict', {})
    enc_nom_dict_rev_p5 = _get_enc_nom_dict_rev()
    cross_dataset_bivariate = _estimate_cross_dataset_pairs(
        variables, enc_dict_p5, enc_nom_dict_rev_p5
    )

    # Shape summary
    shape_counts = {"consensus": 0, "lean": 0, "polarized": 0, "dispersed": 0}
    for v in variables:
        shape_counts[v.shape] = shape_counts.get(v.shape, 0) + 1

    # Divergence index: fraction of variables that are NOT consensus
    n_total = len(variables)
    n_non_consensus = n_total - shape_counts.get("consensus", 0)
    divergence_index = n_non_consensus / n_total if n_total > 0 else 0.0

    # Overall narrative
    narrative = _generate_overall_narrative(shape_counts, n_total, divergence_index)

    return QuantitativeReport(
        variable_count=n_total,
        variables=variables,
        shape_summary=shape_counts,
        divergence_index=divergence_index,
        overall_narrative=narrative,
        demographic_fault_lines=demographic_fault_lines,
        cross_dataset_bivariate=cross_dataset_bivariate,
    )


def _generate_overall_narrative(
    shape_counts: Dict[str, int], n_total: int, divergence_index: float
) -> str:
    """Generate a one-sentence narrative characterizing the overall distribution pattern."""
    n_consensus = shape_counts.get("consensus", 0)
    n_polarized = shape_counts.get("polarized", 0)
    n_dispersed = shape_counts.get("dispersed", 0)
    n_lean = shape_counts.get("lean", 0)

    if divergence_index == 0:
        return (f"All {n_total} variables show strong consensus, indicating broad agreement "
                f"across the topics examined.")

    if divergence_index >= 0.7:
        return (f"Most variables ({n_total - n_consensus} of {n_total}) lack clear consensus, "
                f"suggesting significant fragmentation of opinion across these topics.")

    parts = []
    if n_consensus > 0:
        parts.append(f"{n_consensus} show consensus")
    if n_polarized > 0:
        parts.append(f"{n_polarized} are polarized")
    if n_dispersed > 0:
        parts.append(f"{n_dispersed} show dispersed opinions")
    if n_lean > 0:
        parts.append(f"{n_lean} lean toward one view without strong consensus")

    return (f"Of {n_total} variables analyzed, {', '.join(parts)} "
            f"— a divergence index of {divergence_index:.0%} indicates "
            f"{'moderate' if divergence_index < 0.5 else 'substantial'} variation in opinion.")


# =============================================================================
# LLM REPORT FORMATTING
# =============================================================================

def format_quantitative_report_for_llm(report: QuantitativeReport) -> str:
    """
    Format the quantitative report as a structured text block for LLM consumption.

    The output is designed to be unambiguous and easy for the LLM to cite.

    Args:
        report: QuantitativeReport instance

    Returns:
        Formatted text string
    """
    lines = []

    # Header
    lines.append("=== QUANTITATIVE REPORT ===")
    lines.append(f"Variables analyzed: {report.variable_count}")
    lines.append(f"Divergence index: {report.divergence_index:.0%} of variables show "
                 f"non-consensus distributions")
    shape_parts = [f"{shape}={count}" for shape, count in report.shape_summary.items()
                   if count > 0]
    lines.append(f"Shape summary: {', '.join(shape_parts)}")
    lines.append("")

    # Cross-dataset bivariate estimates FIRST (primary evidence about topic relationships)
    if report.cross_dataset_bivariate:
        lines.append("=== CROSS-DATASET BIVARIATE ASSOCIATIONS ===")
        lines.append("(Simulation-based via SES bridge — primary evidence about topic relationships)")
        for pair_key, est in report.cross_dataset_bivariate.items():
            cv = est.get('cramers_v', 0)
            pv = est.get('p_value', 1)
            strength = (
                'weak' if cv < 0.1
                else 'moderate' if cv < 0.3
                else 'strong'
            )
            sig = "SIGNIFICANT" if pv < 0.05 else "NOT SIGNIFICANT"
            lines.append(
                f"  - {est.get('var_a')} × {est.get('var_b')}: "
                f"V={cv:.3f} ({strength}), p={pv:.3f} ({sig}), n={est.get('n_simulated')}"
            )

            # Cross-tab conditional distribution profiles
            col_profiles = est.get('column_profiles')
            top_contrasts = est.get('top_contrasts')
            if col_profiles:
                var_a = est.get('var_a', '?')
                var_b = est.get('var_b', '?')
                lines.append(
                    f"    How {var_b} responses shift across {var_a} categories:"
                )
                for cond_cat, profile in col_profiles.items():
                    sorted_items = sorted(
                        profile.items(), key=lambda x: x[1], reverse=True
                    )
                    parts = [f"{cat}={pct*100:.1f}%" for cat, pct in sorted_items[:4]]
                    if len(sorted_items) > 4:
                        parts.append("...")
                    lines.append(
                        f"      When {var_a}=\"{cond_cat}\": {', '.join(parts)}"
                    )
                if top_contrasts:
                    top_cat = next(iter(top_contrasts))
                    tc = top_contrasts[top_cat]
                    lines.append(
                        f"    Key contrast: \"{top_cat}\" ranges from "
                        f"{tc['min_pct']*100:.1f}% (when \"{tc['min_when']}\") to "
                        f"{tc['max_pct']*100:.1f}% (when \"{tc['max_when']}\")"
                    )
        lines.append("")

    # Demographic fault lines summary
    if report.demographic_fault_lines:
        lines.append("=== DEMOGRAPHIC FAULT LINES ===")
        lines.append("(Ranked by mean Cramér's V across variables)")
        for ses_var, info in report.demographic_fault_lines.items():
            strength = (
                'weak' if info['mean_cramers_v'] < 0.1
                else 'moderate' if info['mean_cramers_v'] < 0.3
                else 'strong'
            )
            lines.append(
                f"  - {ses_var}: mean V={info['mean_cramers_v']:.2f} ({strength}), "
                f"max V={info['max_cramers_v']:.2f}, "
                f"across {info['n_significant']} variable(s)"
            )
    lines.append("")

    # Per-variable sections
    for i, v in enumerate(report.variables, 1):
        lines.append(f"--- Variable {i}: {v.var_id} ---")
        lines.append(f"Question: \"{v.question_text}\"")
        lines.append(f"Distribution shape: {v.shape.upper()} ({v.shape_explanation})")
        lines.append(f"Modal response: {v.modal_response} ({v.modal_percentage:.1f}%)")
        lines.append(f"Runner-up: {v.runner_up_response} ({v.runner_up_percentage:.1f}%), "
                     f"margin: {v.margin:.1f} pp")
        lines.append(f"HHI: {v.hhi:.0f}")

        lines.append("Full distribution:")
        # Sort by percentage descending for readability
        sorted_freqs = sorted(v.frequencies.items(), key=lambda x: x[1], reverse=True)
        for label, pct in sorted_freqs:
            lines.append(f"  - {label}: {pct:.1f}%")

        if v.minority_opinions:
            minority_parts = [f"{label} ({pct:.1f}%)"
                              for label, pct in v.minority_opinions.items()]
            lines.append(f"Minority opinions (>15%): {', '.join(minority_parts)}")
        else:
            lines.append("Minority opinions (>15%): None")

        # Bivariate demographic breakdown
        if v.bivariate_stats:
            lines.append("Demographic breakdown (p<0.05, sorted by Cramér's V):")
            for ses_var, biv in sorted(
                v.bivariate_stats.items(),
                key=lambda x: x[1].get('cramers_v') or 0,
                reverse=True,
            ):
                cv = biv.get('cramers_v') or 0
                cv_label = (
                    'weak' if cv < 0.1
                    else 'moderate' if cv < 0.3
                    else 'strong'
                )
                leaders_str = _format_bivariate_leaders(biv.get('leaders', {}))
                lines.append(
                    f"  - By {ses_var}: Cramér's V={cv:.2f} ({cv_label}){leaders_str}"
                )
        else:
            lines.append("Demographic breakdown: no significant differences (p≥0.05)")

        lines.append("")

    # Overall
    lines.append("=== OVERALL ===")
    lines.append(report.overall_narrative)

    return "\n".join(lines)


# =============================================================================
# PHASE 2: BIVARIATE / DEMOGRAPHIC ANALYSIS
# =============================================================================

def compute_bivariate_statistics(
    var_id: str,
    demographic_var: str,
    enc_dict: Optional[dict] = None,
    enc_nom_dict_rev: Optional[dict] = None,
) -> Optional[Dict[str, Any]]:
    """
    Compute cross-tabulation statistics between a survey variable and a
    demographic SES variable using SESAnalyzer.

    Uses:
    - SESAnalyzer.analyze_single_relationship() with Pondi2 weights
    - Chi-square test, Cramér's V effect size, leader analysis

    Args:
        var_id: Variable ID (e.g., "p5_1|IDE")
        demographic_var: SES variable name (e.g., "sexo", "region")
        enc_dict: Optional enc_dict override (lazy-loaded if None)
        enc_nom_dict_rev: Optional reverse name mapping (lazy-loaded if None)

    Returns:
        Dict with chi_square, p_value, cramers_v, leaders; or None on failure
    """
    import pandas as pd
    from ses_analysis import SESAnalyzer, AnalysisConfig

    if enc_dict is None:
        lmd = _get_los_mex_preprocessed()
        enc_dict = lmd.get('enc_dict', {})
    if enc_nom_dict_rev is None:
        enc_nom_dict_rev = _get_enc_nom_dict_rev()

    if '|' not in var_id:
        return None

    var_part, survey_code = var_id.split('|', 1)
    survey_name = enc_nom_dict_rev.get(survey_code)
    if not survey_name:
        return None

    survey_data = enc_dict.get(survey_name, {})
    df = survey_data.get('dataframe')
    if not isinstance(df, pd.DataFrame):
        return None

    if var_part not in df.columns or demographic_var not in df.columns:
        return None

    config = AnalysisConfig(weight_variable='Pondi2')
    analyzer = SESAnalyzer(config)
    result = analyzer.analyze_single_relationship(
        df=df,
        target_var=var_part,
        ses_var=demographic_var,
    )

    if 'error' in result:
        return None

    stats = result.get('statistics', {})
    return {
        'chi_square': stats.get('chi_square'),
        'p_value': stats.get('p_value'),
        'cramers_v': stats.get('cramers_v'),
        'degrees_of_freedom': stats.get('degrees_of_freedom'),
        'spearman_correlation': stats.get('spearman_correlation'),
        'leaders': result.get('analysis', {}).get('leaders', {}),
        'demographic_var': demographic_var,
    }


def _enrich_with_bivariate_stats(variables: List) -> None:
    """
    Enrich VariableStatistics objects with bivariate SES breakdowns (in-place).
    Only stores results with p < 0.05. Non-fatal on any failure.
    """
    try:
        lmd = _get_los_mex_preprocessed()
        enc_dict = lmd.get('enc_dict', {})
        enc_nom_dict_rev = _get_enc_nom_dict_rev()

        if not enc_dict:
            return

        print(f"[bivariate] Computing demographic breakdowns for {len(variables)} variable(s)...")
        for var_stats in variables:
            biv_results: Dict[str, Any] = {}
            for ses_var in SES_DEMOGRAPHIC_VARS:
                result = compute_bivariate_statistics(
                    var_stats.var_id, ses_var, enc_dict, enc_nom_dict_rev
                )
                if (result
                        and result.get('p_value') is not None
                        and result['p_value'] < 0.05):
                    biv_results[ses_var] = result
            if biv_results:
                var_stats.bivariate_stats = biv_results

        n_with = sum(1 for v in variables if v.bivariate_stats)
        print(f"[bivariate] Done: {n_with}/{len(variables)} variables have significant breakdowns")
    except Exception as e:
        print(f"[bivariate] Enrichment failed (non-fatal): {e}")


def _compute_demographic_fault_lines(variables: List) -> Optional[Dict[str, Any]]:
    """
    Summarize which SES dimensions show the strongest patterns across all variables.
    Returns a dict sorted by mean Cramér's V (strongest divide first).
    """
    ses_agg: Dict[str, List[float]] = {}
    for var in variables:
        if not var.bivariate_stats:
            continue
        for ses_var, biv in var.bivariate_stats.items():
            cv = float(biv.get('cramers_v') or 0.0)
            ses_agg.setdefault(ses_var, []).append(cv)

    if not ses_agg:
        return None

    fault_lines = {
        ses_var: {
            'mean_cramers_v': round(sum(vals) / len(vals), 3),
            'max_cramers_v': round(max(vals), 3),
            'n_significant': len(vals),
        }
        for ses_var, vals in ses_agg.items()
    }

    return dict(sorted(
        fault_lines.items(),
        key=lambda x: x[1]['mean_cramers_v'],
        reverse=True,
    ))


def _estimate_cross_dataset_pairs(
    variables: List,
    enc_dict: dict,
    enc_nom_dict_rev: dict,
    max_pairs: int = 6,
) -> Optional[Dict[str, Any]]:
    """
    For all pairs of variables from different surveys, estimate bivariate
    association via SES bridge simulation (Phase 5).

    Returns dict keyed by '{var_a_id}::{var_b_id}', or None if no cross-survey
    pairs exist or estimation fails entirely.
    """
    import pandas as pd
    from ses_regression import CrossDatasetBivariateEstimator

    if not enc_dict or len(variables) < 2:
        return None

    # Identify cross-survey pairs
    cross_pairs = []
    for i, va in enumerate(variables):
        for vb in variables[i + 1:]:
            if va.survey_code != vb.survey_code:
                cross_pairs.append((va, vb))
            if len(cross_pairs) >= max_pairs:
                break
        if len(cross_pairs) >= max_pairs:
            break

    if not cross_pairs:
        return None

    print(f"[cross-bivariate] Estimating {len(cross_pairs)} cross-survey pair(s)...")
    estimator = CrossDatasetBivariateEstimator(n_sim=2000)
    results: Dict[str, Any] = {}

    for va, vb in cross_pairs:
        pair_key = f"{va.var_id}::{vb.var_id}"
        try:
            # Resolve DataFrames
            survey_name_a = enc_nom_dict_rev.get(va.survey_code)
            survey_name_b = enc_nom_dict_rev.get(vb.survey_code)
            if not survey_name_a or not survey_name_b:
                continue

            df_a = enc_dict.get(survey_name_a, {}).get('dataframe')
            df_b = enc_dict.get(survey_name_b, {}).get('dataframe')
            if not isinstance(df_a, pd.DataFrame) or not isinstance(df_b, pd.DataFrame):
                continue

            col_a = va.var_id.split('|')[0]
            col_b = vb.var_id.split('|')[0]
            if col_a not in df_a.columns or col_b not in df_b.columns:
                continue

            est = estimator.estimate(
                var_id_a=va.var_id,
                var_id_b=vb.var_id,
                df_a=df_a,
                df_b=df_b,
                col_a=col_a,
                col_b=col_b,
            )
            if est is not None:
                results[pair_key] = est
        except Exception as e:
            print(f"[cross-bivariate] Skipping {pair_key}: {e}")

    if not results:
        return None

    print(f"[cross-bivariate] Done: {len(results)} pair(s) estimated")
    return results


def _format_bivariate_leaders(leaders: Dict[str, Any]) -> str:
    """Format top 2 responses per demographic group as a compact string for LLM."""
    if not leaders:
        return ""
    parts = []
    for group, info in list(leaders.items())[:4]:
        first = info.get('first', {})
        second = info.get('second', {})
        cat1 = first.get('category', '?')
        prop1 = first.get('proportion', 0) * 100
        cat2 = second.get('category', '')
        prop2 = second.get('proportion', 0) * 100
        if cat2:
            parts.append(f"{group}: {cat1}={prop1:.0f}%, {cat2}={prop2:.0f}%")
        else:
            parts.append(f"{group}: {cat1}={prop1:.0f}%")
    return "\n      " + "; ".join(parts) if parts else ""
