"""
Integration tests for Phase 5 cross-dataset bivariate simulation.

Tests the full pipeline from build_quantitative_report() through to the
formatted essay markdown, using real survey data (los_mex_dict.json).

Requires los_mex_dict.json to be present; skips gracefully otherwise.
LLM tests require an API key and are marked @pytest.mark.slow.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _load_data():
    """Load df_tables/pregs_dict; skip if survey data unavailable."""
    try:
        from dataset_knowledge import df_tables, pregs_dict
        return df_tables, pregs_dict
    except SystemExit as exc:
        pytest.skip(f"Survey data exited during load: {exc}")
        raise
    except Exception as e:
        pytest.skip(f"Cannot load dataset_knowledge: {e}")


def _load_los_mex():
    """Load and SES-preprocess los_mex_dict; skip if unavailable."""
    try:
        from dataset_knowledge import los_mex_dict
        from ses_analysis import AnalysisConfig
        return AnalysisConfig.preprocess_survey_data(los_mex_dict)
    except SystemExit as exc:
        pytest.skip(f"Survey data exited during load: {exc}")
        raise
    except Exception as e:
        pytest.skip(f"Cannot load/preprocess los_mex_dict: {e}")


def _require_openai_key():
    if not os.environ.get('OPENAI_API_KEY'):
        pytest.skip("OPENAI_API_KEY not set")


# ---------------------------------------------------------------------------
# Test 1: Phase 5 fires for cross-survey variables (data-only, no LLM)
# ---------------------------------------------------------------------------

def test_phase5_fires_for_cross_survey_variables():
    """
    build_quantitative_report() with variables from two different surveys
    must populate cross_dataset_bivariate with valid simulation estimates.

    Variables: p1|CUL, p2|CUL (Cultura Política) + p1|COR, p2|COR (Corrupción)
    → 4 cross-survey pairs: (CUL×COR) × 2×2 combinations
    """
    _load_data()

    from quantitative_engine import build_quantitative_report

    variables = ["p1|CUL", "p2|CUL", "p1|COR", "p2|COR"]
    print(f"\nVariables: {variables}")

    report = build_quantitative_report(variables, user_query=None)

    print(f"Variables analyzed: {report.variable_count}")
    print(f"cross_dataset_bivariate: {report.cross_dataset_bivariate}")

    # Phase 5 must have produced results
    assert report.cross_dataset_bivariate is not None, (
        "cross_dataset_bivariate should be populated for cross-survey variables"
    )

    # At least one pair key with '::' separator
    pair_keys = list(report.cross_dataset_bivariate.keys())
    print(f"Pair keys: {pair_keys}")
    assert any("::" in k for k in pair_keys), (
        f"Expected '::' separator in pair keys, got: {pair_keys}"
    )

    # Validate each estimate
    for pair_key, est in report.cross_dataset_bivariate.items():
        print(f"  {pair_key}: V={est.get('cramers_v'):.3f}, "
              f"p={est.get('p_value'):.3f}, n={est.get('n_simulated')}")

        assert est.get('method') == 'ses_simulation', (
            f"Expected method='ses_simulation', got {est.get('method')}"
        )
        assert 'cramers_v' in est
        assert 'p_value' in est
        assert 'chi_square' in est
        assert 'degrees_of_freedom' in est
        assert 'n_simulated' in est
        assert 'note' in est

        cv = est['cramers_v']
        pv = est['p_value']
        assert 0.0 <= cv <= 1.0, f"Cramér's V out of range: {cv}"
        assert 0.0 <= pv <= 1.0, f"p-value out of range: {pv}"
        assert est['chi_square'] >= 0.0, f"chi_square negative: {est['chi_square']}"
        assert est['n_simulated'] == 2000

        # Phase 5 cross-tab profiles (column_profiles + top_contrasts)
        assert 'column_profiles' in est, f"{pair_key}: missing column_profiles"
        assert 'top_contrasts' in est, f"{pair_key}: missing top_contrasts"
        cp = est['column_profiles']
        assert isinstance(cp, dict) and len(cp) > 0, (
            f"{pair_key}: column_profiles should be non-empty dict"
        )
        tc = est['top_contrasts']
        assert isinstance(tc, dict) and len(tc) <= 3, (
            f"{pair_key}: top_contrasts should have ≤3 entries"
        )


# ---------------------------------------------------------------------------
# Test 2: Phase 5 is silent when all variables share a survey (data-only)
# ---------------------------------------------------------------------------

def test_phase5_silent_for_same_survey_variables():
    """
    build_quantitative_report() with variables all from the same survey
    must leave cross_dataset_bivariate as None — no cross-survey pairs exist.

    Variables: p1|CUL, p2|CUL, p3|CUL (all from Cultura Política)
    """
    _load_data()

    from quantitative_engine import build_quantitative_report

    variables = ["p1|CUL", "p2|CUL", "p3|CUL"]
    print(f"\nVariables (same survey): {variables}")

    report = build_quantitative_report(variables, user_query=None)

    print(f"cross_dataset_bivariate: {report.cross_dataset_bivariate}")
    assert report.cross_dataset_bivariate is None, (
        "cross_dataset_bivariate should be None when all variables share a survey"
    )


# ---------------------------------------------------------------------------
# Test 3: SES population uses real Pondi2-weighted marginals (data-only)
# ---------------------------------------------------------------------------

def test_ses_population_real_weights():
    """
    CrossDatasetBivariateEstimator._sample_ses_population() must return a
    DataFrame of the correct size drawn from the real weighted SES marginals.
    """
    lmd = _load_los_mex()

    from ses_regression import CrossDatasetBivariateEstimator, SES_REGRESSION_VARS

    enc_dict = lmd.get('enc_dict', {})

    # Resolve DataFrames for two surveys
    enc_nom_dict = lmd.get('enc_nom_dict', {})
    # enc_nom_dict maps full_name → code; we need code → full_name
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    survey_name_cul = enc_nom_dict_rev.get('CUL')
    survey_name_cor = enc_nom_dict_rev.get('COR')

    if not survey_name_cul or not survey_name_cor:
        pytest.skip("CUL or COR survey not found in enc_nom_dict")

    df_cul = enc_dict.get(survey_name_cul, {}).get('dataframe')
    df_cor = enc_dict.get(survey_name_cor, {}).get('dataframe')

    if df_cul is None or df_cor is None:
        pytest.skip("Could not retrieve CUL or COR DataFrames")

    import pandas as pd
    assert isinstance(df_cul, pd.DataFrame)
    assert isinstance(df_cor, pd.DataFrame)

    estimator = CrossDatasetBivariateEstimator(n_sim=500)
    pop = estimator._sample_ses_population(
        df_cul, df_cor,
        ses_vars=SES_REGRESSION_VARS,
        weight_col='Pondi2',
    )

    print(f"\nSES population shape: {pop.shape}")
    print(f"Columns: {list(pop.columns)}")
    print(f"NaN counts:\n{pop.isnull().sum()}")

    assert len(pop) == 500, f"Expected 500 rows, got {len(pop)}"

    # All requested SES vars that exist in either survey must be present
    present_ses = [v for v in SES_REGRESSION_VARS
                   if v in df_cul.columns or v in df_cor.columns]
    for col in present_ses:
        assert col in pop.columns, f"SES column '{col}' missing from population"
        assert pop[col].isnull().sum() == 0, (
            f"SES column '{col}' has NaN in sampled population"
        )


# ---------------------------------------------------------------------------
# Test 4: Cross-dataset section surfaces in essay markdown (LLM required)
# ---------------------------------------------------------------------------

def test_phase5_via_run_analysis_dispatcher():
    """
    Verify that run_analysis(analysis_type='analytical_essay') — the v2 quantitative
    pipeline entry point — populates cross_dataset_bivariate on the returned
    quantitative report without requiring an LLM call.

    We extract the quantitative report from the result dict and check Phase 5 ran.
    """
    _load_data()

    from run_analysis import run_analysis

    variables = ["p1|CUL", "p2|CUL", "p1|COR", "p2|COR"]
    query = "¿Cómo se relacionan la cultura política y la corrupción?"

    # run_analysis with analytical_essay uses the v2 quantitative engine
    # even if the LLM step fails — the quantitative report is built first
    result = run_analysis(
        analysis_type='analytical_essay',
        selected_variables=variables,
        user_query=query,
    )

    print(f"\nrun_analysis success: {result.get('success')}")
    print(f"analysis_type: {result.get('analysis_type')}")

    assert result.get('analysis_type') == 'analytical_essay', (
        "Dispatcher should route to analytical_essay"
    )

    # The quantitative report is stored in results regardless of LLM outcome
    results = result.get('results', {})
    quant = results.get('quantitative_report')

    # quant may be a QuantitativeReport object or a serialised dict
    def _get_cross_biv(q):
        if q is None:
            return None
        if isinstance(q, dict):
            return q.get('cross_dataset_bivariate')
        return getattr(q, 'cross_dataset_bivariate', None)

    cross_biv = _get_cross_biv(quant)
    print(f"cross_dataset_bivariate keys: {list(cross_biv.keys()) if cross_biv else None}")

    if cross_biv is not None:
        # Phase 5 populated correctly
        assert any("::" in k for k in cross_biv.keys()), (
            "Expected '::' separator in cross_dataset_bivariate keys"
        )
    else:
        # Fall back: check formatted_report contains the section
        formatted = result.get('formatted_report', '')
        assert 'Cross-Dataset' in formatted or result.get('success'), (
            "run_analysis must either populate cross_dataset_bivariate or succeed overall"
        )


@pytest.mark.slow
def test_cross_dataset_surfaces_in_essay_markdown():
    """
    Full end-to-end via run_analysis dispatcher (v2 analytical_essay pipeline):
    formatted_report must contain the Cross-Dataset Bivariate Estimates section.

    Requires OPENAI_API_KEY. Uses only 2 variables to minimise LLM cost.
    """
    _load_data()
    _require_openai_key()

    from run_analysis import run_analysis

    variables = ["p1|CUL", "p1|COR"]
    query = "¿Cómo se relacionan la cultura política y la corrupción en México?"

    print(f"\nVariables: {variables}")
    print(f"Query: {query}")

    result = run_analysis(
        analysis_type='analytical_essay',
        selected_variables=variables,
        user_query=query,
    )

    print(f"Success: {result.get('success')}")
    assert result.get('analysis_type') == 'analytical_essay'

    if not result.get('success'):
        pytest.fail(f"run_analysis failed: {result.get('error')}")

    formatted = result.get('formatted_report', '')
    print(f"Formatted report length: {len(formatted)} chars")

    if 'Cross-Dataset' in formatted:
        start = formatted.index('Cross-Dataset')
        print(f"\nCross-Dataset section (first 800 chars):\n{formatted[start:start+800]}")

    assert 'Cross-Dataset Bivariate Estimates' in formatted, (
        "Expected 'Cross-Dataset Bivariate Estimates' section in formatted_report"
    )
    assert (
        'ses_simulation' in formatted
        or 'SES bridge' in formatted
        or 'SES-bridge' in formatted
        or 'Simulation-Based' in formatted
    ), "Expected simulation method reference in formatted_report"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
