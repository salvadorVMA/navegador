"""
Test module for SES Analysis functionality.
Uses synthetic mock data so tests run in any environment without requiring
the real los_mex_dict.json file.
"""

import unittest
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt

from ses_analysis import (
    AnalysisConfig,
    SESDataValidator,
    SESAnalyzer,
    SESVisualizer,
    create_analysis_pipeline
)


def _make_mock_survey_df(n=500, seed=42) -> pd.DataFrame:
    """
    Build a synthetic survey DataFrame that mimics the los_mex structure.

    Columns
    -------
    p1, p2, p3   – nominal question variables  (5 coded categories)
    p4           – ordinal question variable    (Likert: mucho/bastante/poco/nada)
    region       – SES: 4 geographic regions
    edad         – SES: age group strings
    empleo       – SES: employment category
    sexo         – SES: 01 / 02
    Pondi2       – survey weight (float)
    """
    rng = np.random.default_rng(seed)

    def cat(choices, size):
        return rng.choice(choices, size=size)

    region_cats = ['01', '02', '03', '04']
    edad_cats   = ['19-24', '25-34', '35-44', '45-54', '55-64', '65+']
    empleo_cats = ['01', '02', '03', '04', '05']
    likert_cats = ['mucho', 'bastante', 'poco', 'nada']
    nominal_cats = ['1', '2', '3', '4', '5']

    df = pd.DataFrame({
        'p1':     cat(nominal_cats, n),
        'p2':     cat(nominal_cats, n),
        'p3':     cat(nominal_cats, n),
        'p4':     cat(likert_cats,  n),   # ordinal
        'region': cat(region_cats,  n),
        'edad':   cat(edad_cats,    n),
        'empleo': cat(empleo_cats,  n),
        'sexo':   cat(['01', '02'], n),
        'Pondi2': rng.uniform(0.5, 2.5,  n).round(4),
    })
    return df


class TestSESAnalysis(unittest.TestCase):
    """Test cases for SES analysis module using synthetic data."""

    def setUp(self):
        """Set up synthetic test data."""
        self.df = _make_mock_survey_df()

        self.target_vars   = ['p1', 'p2', 'p3', 'p4']
        self.available_ses = ['region', 'edad', 'empleo']

        self.ses_labels = {
            '01': 'Norte', '02': 'Centro',
            '03': 'Centro Occidente', '04': 'Sureste'
        }
        self.var_labels = {
            '1': 'Muy de acuerdo', '2': 'De acuerdo',
            '3': 'En desacuerdo', '4': 'Muy en desacuerdo', '5': 'NS/NC'
        }

        self.config = AnalysisConfig(
            residual_categories=['88', '99', 'NS', 'NC'],
            weight_variable='Pondi2'
        )

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _print_analysis_results(self, results):
        if 'statistics' in results:
            for stat, value in results['statistics'].items():
                if isinstance(value, (int, float)):
                    print(f"  {stat}: {value:.4f}")
                else:
                    print(f"  {stat}: {value}")

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_data_validator(self):
        """Test data validation and variable type detection."""
        validator = SESDataValidator()

        # Valid case
        valid, msg = validator.verify_metadata(
            self.df,
            [self.available_ses[0]] + self.target_vars[:2],
            self.ses_labels,
            self.var_labels
        )
        self.assertTrue(valid, msg)

        # Invalid case – missing column
        valid, msg = validator.verify_metadata(
            self.df, ['nonexistent_var'], self.ses_labels, self.var_labels
        )
        self.assertFalse(valid)

        # Variable type detection (second param is var_labels dict, optional)
        var_types = validator.detect_variable_types(self.df)
        self.assertGreater(len(var_types), 0)
        for col in self.target_vars + self.available_ses:
            self.assertIn(col, var_types)
            self.assertIn(var_types[col], ['nominal', 'ordinal', 'interval'])

    def test_ses_analyzer(self):
        """Test single and multiple relationship analysis."""
        analyzer = SESAnalyzer(self.config)
        ses_var    = self.available_ses[0]   # 'region'
        target_var = self.target_vars[0]     # 'p1'

        # --- single relationship ---
        results = analyzer.analyze_single_relationship(
            self.df, target_var, ses_var,
            self.ses_labels, self.var_labels
        )
        self.assertIn('statistics', results)
        self.assertIn('tables',     results)
        self.assertIn('analysis',   results)
        self.assertIn('chi_square', results['statistics'])
        self.assertIn('cramers_v',  results['statistics'])
        self._print_analysis_results(results)

        # --- multiple relationships ---
        multi = analyzer.analyze_multiple_relationships(
            self.df, self.target_vars[:2], ses_var,
            self.ses_labels, self.var_labels
        )
        # Returns dict keyed by target var
        for var in self.target_vars[:2]:
            self.assertIn(var, multi)
            self.assertIn('statistics', multi[var])

    def test_ses_visualizer(self):
        """Test bar and heatmap visualizations."""
        visualizer = SESVisualizer(self.config)
        ses_var    = self.available_ses[0]
        target_var = self.target_vars[0]

        # bar plot
        fig, ax = visualizer.create_relationship_plot(
            self.df, target_var, ses_var,
            title=f"{target_var} vs {ses_var}",
            ses_labels=self.ses_labels,
            var_labels=self.var_labels,
            plot_type='bar'
        )
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)

        # heatmap
        fig, ax = visualizer.create_relationship_plot(
            self.df, target_var, ses_var,
            title=f"{target_var} vs {ses_var} Heatmap",
            ses_labels=self.ses_labels,
            var_labels=self.var_labels,
            plot_type='heatmap'
        )
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        plt.close('all')

    def test_analysis_pipeline(self):
        """Test complete analysis pipeline end-to-end."""
        analyzer, visualizer = create_analysis_pipeline(self.config)
        ses_var    = self.available_ses[0]
        target_var = self.target_vars[0]

        results = analyzer.analyze_single_relationship(
            self.df, target_var, ses_var,
            self.ses_labels, self.var_labels
        )
        self.assertIn('statistics', results)
        self._print_analysis_results(results)

        fig, ax = visualizer.create_relationship_plot(
            self.df, target_var, ses_var,
            title=f"{target_var} vs {ses_var}"
        )
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        plt.close('all')


if __name__ == '__main__':
    unittest.main()
