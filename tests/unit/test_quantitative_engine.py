"""
Unit tests for the quantitative engine.
Tests pure computation — no LLM calls, no network, no data loading.
Uses override parameters to bypass dataset_knowledge import.
"""

import unittest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import only the pure functions that don't trigger dataset_knowledge import
from quantitative_engine import (
    classify_distribution_shape,
    compute_hhi,
    compute_variable_statistics,
    build_quantitative_report,
    format_quantitative_report_for_llm,
    VariableStatistics,
    QuantitativeReport,
)


def _make_df(data_dict):
    """Create a DataFrame matching df_tables structure."""
    return pd.DataFrame(
        list(data_dict.values()),
        index=list(data_dict.keys()),
        columns=['%']
    )


class TestClassifyDistributionShape(unittest.TestCase):
    """Test classify_distribution_shape function."""

    def test_consensus_strong(self):
        shape, _ = classify_distribution_shape({"Yes": 80.0, "No": 15.0, "DK": 5.0})
        self.assertEqual(shape, "consensus")

    def test_consensus_threshold(self):
        """66% should be consensus (> 65%)."""
        shape, _ = classify_distribution_shape({"Yes": 66.0, "No": 34.0})
        self.assertEqual(shape, "consensus")

    def test_lean_at_exactly_65(self):
        """Exactly 65% is NOT > 65, so it should be lean."""
        shape, _ = classify_distribution_shape({"Yes": 65.0, "No": 35.0})
        self.assertEqual(shape, "lean")

    def test_lean_at_55(self):
        shape, _ = classify_distribution_shape({"Agree": 55.0, "Disagree": 30.0, "Neutral": 15.0})
        self.assertEqual(shape, "lean")

    def test_lean_at_exactly_50(self):
        shape, _ = classify_distribution_shape({"Yes": 50.0, "No": 30.0, "DK": 20.0})
        self.assertEqual(shape, "lean")

    def test_polarized_classic(self):
        shape, _ = classify_distribution_shape({"For": 42.0, "Against": 38.0, "Neutral": 15.0, "DK": 5.0})
        self.assertEqual(shape, "polarized")

    def test_polarized_near_equal(self):
        shape, _ = classify_distribution_shape({"A": 35.0, "B": 35.0, "C": 20.0, "D": 10.0})
        self.assertEqual(shape, "polarized")

    def test_dispersed_four_way(self):
        shape, _ = classify_distribution_shape({"A": 25.0, "B": 25.0, "C": 25.0, "D": 25.0})
        self.assertEqual(shape, "dispersed")

    def test_dispersed_five_way(self):
        shape, _ = classify_distribution_shape({"A": 22.0, "B": 20.0, "C": 20.0, "D": 19.0, "E": 19.0})
        self.assertEqual(shape, "dispersed")

    def test_lean_fallback(self):
        """Modal > 40% but doesn't meet polarized or consensus criteria."""
        shape, _ = classify_distribution_shape({"A": 45.0, "B": 25.0, "C": 20.0, "D": 10.0})
        self.assertEqual(shape, "lean")

    def test_empty_frequencies(self):
        shape, _ = classify_distribution_shape({})
        self.assertEqual(shape, "dispersed")

    def test_single_category(self):
        shape, _ = classify_distribution_shape({"Only": 100.0})
        self.assertEqual(shape, "consensus")

    def test_two_category_even(self):
        """50/50 split: top1=50 >= 50, so lean."""
        shape, _ = classify_distribution_shape({"A": 50.0, "B": 50.0})
        self.assertEqual(shape, "lean")

    def test_explanation_contains_percentage(self):
        _, explanation = classify_distribution_shape({"Yes": 70.0, "No": 30.0})
        self.assertIn("70.0", explanation)


class TestComputeHHI(unittest.TestCase):
    """Test HHI computation."""

    def test_monopoly(self):
        self.assertAlmostEqual(compute_hhi({"Only": 100.0}), 10000.0)

    def test_even_split_two(self):
        self.assertAlmostEqual(compute_hhi({"A": 50.0, "B": 50.0}), 5000.0)

    def test_even_split_four(self):
        self.assertAlmostEqual(compute_hhi({"A": 25.0, "B": 25.0, "C": 25.0, "D": 25.0}), 2500.0)

    def test_even_split_five(self):
        self.assertAlmostEqual(compute_hhi({"A": 20.0, "B": 20.0, "C": 20.0, "D": 20.0, "E": 20.0}), 2000.0)

    def test_empty(self):
        self.assertEqual(compute_hhi({}), 0.0)

    def test_skewed(self):
        hhi_skewed = compute_hhi({"A": 70.0, "B": 20.0, "C": 10.0})
        hhi_even = compute_hhi({"A": 40.0, "B": 30.0, "C": 30.0})
        self.assertGreater(hhi_skewed, hhi_even)


class TestComputeVariableStatistics(unittest.TestCase):
    """Test compute_variable_statistics with override parameters."""

    def test_basic_variable(self):
        mock_tables = {
            'p5_1|IDE': _make_df({
                'Orgullo': 38.3, 'Alegría': 25.0, 'Esperanza': 20.0,
                'Tristeza': 10.0, 'Enojo': 6.7
            })
        }
        mock_pregs = {
            'p5_1|IDE': 'IDENTIDAD_Y_VALORES|¿Cuál emoción asocia con México?'
        }

        result = compute_variable_statistics(
            'p5_1|IDE',
            df_tables_override=mock_tables,
            pregs_dict_override=mock_pregs
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.var_id, 'p5_1|IDE')
        self.assertEqual(result.modal_response, 'Orgullo')
        self.assertAlmostEqual(result.modal_percentage, 38.3)
        self.assertEqual(result.runner_up_response, 'Alegría')
        self.assertAlmostEqual(result.runner_up_percentage, 25.0)
        self.assertAlmostEqual(result.margin, 13.3)
        self.assertEqual(result.n_categories, 5)
        self.assertEqual(result.survey_code, 'IDE')
        self.assertEqual(result.shape, 'dispersed')
        # Minority opinions > 15% excluding mode
        self.assertIn('Alegría', result.minority_opinions)
        self.assertIn('Esperanza', result.minority_opinions)
        self.assertNotIn('Orgullo', result.minority_opinions)

    def test_consensus_variable(self):
        mock_tables = {
            'p1|ABC': _make_df({'Sí': 75.0, 'No': 18.0, 'NS/NC': 7.0})
        }
        mock_pregs = {'p1|ABC': 'SURVEY|¿Apoya usted?'}

        result = compute_variable_statistics(
            'p1|ABC',
            df_tables_override=mock_tables,
            pregs_dict_override=mock_pregs
        )

        self.assertEqual(result.shape, 'consensus')
        self.assertEqual(result.modal_response, 'Sí')
        self.assertIn('No', result.minority_opinions)

    def test_polarized_variable(self):
        mock_tables = {
            'p2|DEF': _make_df({'Tradicional': 47.0, 'Moderno': 41.0, 'Otro': 8.0, 'NS': 4.0})
        }
        mock_pregs = {'p2|DEF': 'EDUCACION|¿Método preferido?'}

        result = compute_variable_statistics(
            'p2|DEF',
            df_tables_override=mock_tables,
            pregs_dict_override=mock_pregs
        )

        self.assertEqual(result.shape, 'polarized')
        self.assertAlmostEqual(result.margin, 6.0)

    def test_nonexistent_variable(self):
        result = compute_variable_statistics(
            'p999|XXX',
            df_tables_override={},
            pregs_dict_override={}
        )
        self.assertIsNone(result)


class TestBuildQuantitativeReport(unittest.TestCase):
    """Test the full report builder."""

    def _make_tables_and_pregs(self):
        """Create test data for two variables: one consensus, one polarized."""
        tables = {
            'p1|ABC': _make_df({'A': 70.0, 'B': 20.0, 'C': 10.0}),
            'p2|DEF': _make_df({'X': 35.0, 'Y': 35.0, 'Z': 20.0, 'W': 10.0}),
        }
        pregs = {
            'p1|ABC': 'SURVEY_A|Question 1',
            'p2|DEF': 'SURVEY_B|Question 2',
        }
        return tables, pregs

    def test_report_shape_summary(self):
        tables, pregs = self._make_tables_and_pregs()

        report = build_quantitative_report(
            ['p1|ABC', 'p2|DEF'],
            df_tables_override=tables,
            pregs_dict_override=pregs
        )

        self.assertEqual(report.variable_count, 2)
        self.assertEqual(report.shape_summary['consensus'], 1)
        self.assertEqual(report.shape_summary['polarized'], 1)
        self.assertAlmostEqual(report.divergence_index, 0.5)

    def test_all_consensus(self):
        tables = {
            'p1|ABC': _make_df({'A': 80.0, 'B': 20.0}),
        }
        pregs = {'p1|ABC': 'SURVEY|Q'}

        report = build_quantitative_report(
            ['p1|ABC'],
            df_tables_override=tables,
            pregs_dict_override=pregs
        )

        self.assertAlmostEqual(report.divergence_index, 0.0)
        self.assertIn("consensus", report.overall_narrative.lower())

    def test_high_divergence(self):
        tables = {
            'p1|A': _make_df({'X': 35.0, 'Y': 35.0, 'Z': 30.0}),
            'p2|A': _make_df({'X': 25.0, 'Y': 25.0, 'Z': 25.0, 'W': 25.0}),
            'p3|A': _make_df({'X': 40.0, 'Y': 35.0, 'Z': 25.0}),
        }
        pregs = {'p1|A': 'S|Q1', 'p2|A': 'S|Q2', 'p3|A': 'S|Q3'}

        report = build_quantitative_report(
            ['p1|A', 'p2|A', 'p3|A'],
            df_tables_override=tables,
            pregs_dict_override=pregs
        )

        # All three are non-consensus
        self.assertAlmostEqual(report.divergence_index, 1.0)

    def test_empty_report(self):
        report = build_quantitative_report(
            ['p999|XXX'],
            df_tables_override={},
            pregs_dict_override={}
        )

        self.assertEqual(report.variable_count, 0)
        self.assertEqual(len(report.variables), 0)
        self.assertAlmostEqual(report.divergence_index, 0.0)


class TestFormatQuantitativeReportForLLM(unittest.TestCase):
    """Test the LLM text formatting."""

    def test_format_includes_all_sections(self):
        tables = {'p1|ABC': _make_df({'A': 60.0, 'B': 25.0, 'C': 15.0})}
        pregs = {'p1|ABC': 'SURVEY|Test Question'}

        report = build_quantitative_report(
            ['p1|ABC'],
            df_tables_override=tables,
            pregs_dict_override=pregs
        )
        text = format_quantitative_report_for_llm(report)

        self.assertIn('QUANTITATIVE REPORT', text)
        self.assertIn('p1|ABC', text)
        self.assertIn('60.0%', text)
        self.assertIn('LEAN', text)
        self.assertIn('HHI', text)
        self.assertIn('OVERALL', text)
        self.assertIn('Minority opinions', text)
        self.assertIn('Full distribution', text)

    def test_format_percentages_are_exact(self):
        tables = {'p1|ABC': _make_df({'Yes': 43.7, 'No': 31.2, 'DK': 25.1})}
        pregs = {'p1|ABC': 'S|Q'}

        report = build_quantitative_report(
            ['p1|ABC'],
            df_tables_override=tables,
            pregs_dict_override=pregs
        )
        text = format_quantitative_report_for_llm(report)

        self.assertIn('43.7%', text)
        self.assertIn('31.2%', text)
        self.assertIn('25.1%', text)

    def test_format_shows_divergence_index(self):
        tables = {
            'p1|A': _make_df({'X': 80.0, 'Y': 20.0}),
            'p2|A': _make_df({'X': 35.0, 'Y': 35.0, 'Z': 30.0}),
        }
        pregs = {'p1|A': 'S|Q1', 'p2|A': 'S|Q2'}

        report = build_quantitative_report(
            ['p1|A', 'p2|A'],
            df_tables_override=tables,
            pregs_dict_override=pregs
        )
        text = format_quantitative_report_for_llm(report)

        self.assertIn('50%', text)  # divergence index


if __name__ == '__main__':
    unittest.main()
