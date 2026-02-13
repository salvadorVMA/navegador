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

def find_closest_variable(var_id: str, all_variables: List[str]) -> Optional[str]:
    """
    Find the closest matching variable using fuzzy string matching.

    Useful when a variable ID has a typo, especially in the survey code part.

    Args:
        var_id: Variable identifier (e.g., "p1|CUP" - wrong code)
        all_variables: List of all available variable IDs

    Returns:
        Best match variable ID, or None if no close match found

    Example:
        >>> find_closest_variable("p1|CUP", ["p1|CUL", "p2|CUL", ...])
        "p1|CUL"  # Found match with 1 character difference in survey code
    """
    from difflib import get_close_matches

    if '|' in var_id:
        # Extract question part and survey code
        var_part, _ = var_id.split('|')

        # Strategy 1: Find variables with same question number but different survey code
        # This catches typos like "p1|CUP" → "p1|CUL"
        candidates = [v for v in all_variables if v.startswith(f"{var_part}|")]

        if candidates:
            # Find closest match among candidates
            matches = get_close_matches(var_id, candidates, n=1, cutoff=0.6)
            if matches:
                return matches[0]

    # Strategy 2: Fallback to general fuzzy match across all variables
    # This catches more complex errors
    matches = get_close_matches(var_id, all_variables, n=1, cutoff=0.8)
    return matches[0] if matches else None


# =============================================================================
# AGGREGATED REPORT
# =============================================================================

def build_quantitative_report(
    selected_variables: List[str],
    df_tables_override: Optional[Dict] = None,
    pregs_dict_override: Optional[Dict] = None,
    auto_correct: bool = True  # NEW: Enable fuzzy matching by default
) -> QuantitativeReport:
    """
    Build a complete quantitative report for all selected variables.

    ENHANCED: Now includes auto-correction for typos in variable IDs.

    Computes per-variable statistics, aggregates shape summary,
    calculates divergence index, and generates an overall narrative.

    Args:
        selected_variables: List of variable IDs
        df_tables_override: Optional override for testing
        pregs_dict_override: Optional override for testing
        auto_correct: If True, attempts to correct typos in variable IDs (default: True)

    Returns:
        QuantitativeReport instance
    """
    tables = df_tables_override if df_tables_override is not None else _get_df_tables()
    all_var_ids = list(tables.keys())

    variables = []
    corrections = []  # Track auto-corrections made

    for var_id in selected_variables:
        # Try exact match first
        if var_id in tables:
            stats = compute_variable_statistics(var_id, df_tables_override, pregs_dict_override)
            if stats is not None:
                variables.append(stats)

        elif auto_correct:
            # Try fuzzy matching
            suggested = find_closest_variable(var_id, all_var_ids)

            if suggested:
                print(f"⚠️  Variable '{var_id}' not found")
                print(f"   → Auto-corrected to: '{suggested}'")
                corrections.append((var_id, suggested))

                stats = compute_variable_statistics(suggested, df_tables_override, pregs_dict_override)
                if stats is not None:
                    variables.append(stats)
            else:
                print(f"❌ Variable '{var_id}' not found and no close match available")
        else:
            # Strict mode - just print warning
            print(f"Warning: Variable {var_id} not found in df_tables")

    if not variables:
        return QuantitativeReport(
            variable_count=0,
            variables=[],
            shape_summary={"consensus": 0, "lean": 0, "polarized": 0, "dispersed": 0},
            divergence_index=0.0,
            overall_narrative="No valid variables found for analysis.",
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

        lines.append("")

    # Overall
    lines.append("=== OVERALL ===")
    lines.append(report.overall_narrative)

    return "\n".join(lines)


# =============================================================================
# PHASE 2 HOOK (NOT IMPLEMENTED)
# =============================================================================

def compute_bivariate_statistics(
    var_id: str,
    demographic_var: str,
    enc_dict: dict
) -> Optional[Dict[str, Any]]:
    """
    Phase 2: Compute cross-tabulation statistics between a survey variable
    and a demographic variable using SESAnalyzer.

    Not implemented in Phase 1. Will use:
    - ses_analysis.SESAnalyzer.analyze_single_relationship()
    - Weighted cross-tabs with Pondi2
    - Chi-square, Cramér's V, leader analysis
    """
    raise NotImplementedError("Phase 2: bivariate analysis not yet implemented")
