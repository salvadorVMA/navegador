"""
Integration tests for the analytical essay pipeline.

Tests the full flow from run_analysis dispatch to essay output.
Requires the survey data file (los_mex_dict.json) to be present.
LLM tests require an API key and are marked with @pytest.mark.slow.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def _load_data():
    """Try to load dataset_knowledge. Returns (df_tables, pregs_dict) or calls pytest.skip."""
    try:
        from dataset_knowledge import df_tables, pregs_dict
        return df_tables, pregs_dict
    except SystemExit as exc:
        pytest.skip(f"Survey data file not available (dataset_knowledge exited): {exc}")
        raise  # unreachable, but satisfies linter S5754
    except Exception as e:
        pytest.skip(f"Cannot load data: {e}")


def _require_openai_key():
    """Skip test if OPENAI_API_KEY is not set."""
    if not os.environ.get('OPENAI_API_KEY'):
        pytest.skip("No OPENAI_API_KEY set")


def test_quantitative_report_with_real_data():
    """
    Test that the quantitative engine can compute statistics from real df_tables.
    Requires los_mex_dict.json to be loaded.
    """
    df_tables, _ = _load_data()

    from quantitative_engine import (
        build_quantitative_report,
        format_quantitative_report_for_llm,
    )

    # Pick a few known variable IDs from the data
    sample_vars = list(df_tables.keys())[:5]
    print(f"Sample variables: {sample_vars}")

    report = build_quantitative_report(sample_vars)
    print(f"Variables analyzed: {report.variable_count}")
    print(f"Shape summary: {report.shape_summary}")
    print(f"Divergence index: {report.divergence_index:.1%}")
    print(f"Overall narrative: {report.overall_narrative}")

    # Verify structure
    assert report.variable_count > 0, "Should have at least one variable"
    assert len(report.variables) == report.variable_count
    assert sum(report.shape_summary.values()) == report.variable_count

    for v in report.variables:
        assert v.modal_percentage > 0, f"{v.var_id}: modal should be > 0"
        assert v.n_categories > 0, f"{v.var_id}: should have categories"
        assert v.shape in ('consensus', 'lean', 'polarized', 'dispersed')
        assert v.hhi > 0, f"{v.var_id}: HHI should be > 0"
        print(f"  {v.var_id}: {v.shape} (modal={v.modal_response} {v.modal_percentage:.1f}%, "
              f"margin={v.margin:.1f}pp, HHI={v.hhi:.0f})")

    # Test LLM format
    text = format_quantitative_report_for_llm(report)
    assert 'QUANTITATIVE REPORT' in text
    assert 'OVERALL' in text
    print(f"\nFormatted report length: {len(text)} chars")
    print(f"First 500 chars:\n{text[:500]}")


def test_analytical_essay_end_to_end():
    """
    Test the full analytical essay pipeline including LLM call.
    Requires API key and real data.
    """
    df_tables, _ = _load_data()
    _require_openai_key()

    from analytical_essay import generate_analytical_essay

    # Pick a few variables
    sample_vars = list(df_tables.keys())[:5]
    user_query = "¿Qué piensan los mexicanos sobre su identidad nacional?"

    print(f"Variables: {sample_vars}")
    print(f"Query: {user_query}")

    result = generate_analytical_essay(
        selected_variables=sample_vars,
        user_query=user_query,
    )

    print(f"\nSuccess: {result.get('success')}")

    if result.get('success'):
        essay = result['essay']
        print(f"Essay sections: {list(essay.keys())}")

        # Check all sections present (data-driven structure)
        for section in ['summary', 'data_landscape', 'evidence', 'complications', 'implications']:
            assert section in essay, f"Missing section: {section}"
            assert len(essay[section]) > 0, f"Empty section: {section}"
            print(f"  {section}: {len(essay[section])} chars")

        # Print formatted report excerpt
        formatted = result.get('formatted_report', '')
        print(f"\nFormatted report ({len(formatted)} chars):")
        print(formatted[:1500])
        print("...")

        # Print metadata
        metadata = result.get('metadata', {})
        print(f"\nMetadata: {metadata}")
    else:
        print(f"ERROR: {result.get('error')}")
        pytest.fail(f"Essay generation failed: {result.get('error')}")


def test_run_analysis_dispatcher():
    """
    Test that run_analysis correctly dispatches 'analytical_essay' type.
    Requires API key and real data.
    """
    df_tables, _ = _load_data()
    _require_openai_key()

    from run_analysis import run_analysis

    sample_vars = list(df_tables.keys())[:3]

    result = run_analysis(
        analysis_type='analytical_essay',
        selected_variables=sample_vars,
        user_query="What do Mexicans think about community attachment?"
    )

    print(f"Success: {result.get('success')}")
    print(f"Analysis type: {result.get('analysis_type')}")
    assert result.get('analysis_type') == 'analytical_essay'

    if result.get('success'):
        assert 'formatted_report' in result
        assert len(result['formatted_report']) > 100
        print(f"Report length: {len(result['formatted_report'])} chars")
    else:
        print(f"Error: {result.get('error')}")
        pytest.fail(f"Dispatcher failed: {result.get('error')}")


def test_comparison_detailed_vs_essay():
    """
    Compare output structure between detailed_report and analytical_essay.
    """
    df_tables, _ = _load_data()
    _require_openai_key()

    from run_analysis import run_analysis

    sample_vars = list(df_tables.keys())[:3]
    query = "¿Qué opinan los mexicanos sobre la democracia?"

    for analysis_type in ["detailed_report", "analytical_essay"]:
        print(f"\n--- {analysis_type.upper()} ---")
        result = run_analysis(
            analysis_type=analysis_type,
            selected_variables=sample_vars,
            user_query=query
        )

        print(f"Success: {result.get('success')}")
        if result.get('success'):
            results = result.get('results', {})
            sections = results.get('report_sections', {})
            print(f"Report sections: {list(sections.keys())}")
            print(f"Formatted report length: {len(result.get('formatted_report', ''))}")
        else:
            print(f"Error: {result.get('error')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
