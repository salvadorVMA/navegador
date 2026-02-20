"""
Unit tests for ses_regression.py — SESEncoder, SurveyVarModel,
CrossDatasetBivariateEstimator.

All tests use synthetic data so the 191 MB los_mex_dict.json is not required.
"""

import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, '/workspaces/navegador')

from ses_regression import (
    SESEncoder,
    SurveyVarModel,
    CrossDatasetBivariateEstimator,
    SES_REGRESSION_VARS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ses_df(n: int = 400, seed: int = 0) -> pd.DataFrame:
    """Synthetic DataFrame with SES columns and two target variables."""
    rng = np.random.default_rng(seed)

    sexo   = rng.choice(['01', '02'], n)
    edad   = rng.choice(['19-24', '25-34', '35-44', '45-54', '55-64', '65+'], n)
    region = rng.choice(['01', '02', '03', '04'], n)
    empleo = rng.choice(['01', '02', '03', '04', '05'], n)
    weight = rng.uniform(0.5, 2.5, n).round(4)

    # Nominal target (5 response categories)
    nominal = rng.choice(['1', '2', '3', '4', '5'], n)
    # Ordinal target (Likert)
    ordinal = rng.choice(['mucho', 'bastante', 'poco', 'nada'], n)

    return pd.DataFrame({
        'sexo': sexo,
        'edad': edad,
        'region': region,
        'empleo': empleo,
        'Pondi2': weight,
        'p_nominal': nominal,
        'p_ordinal': ordinal,
    })


# ---------------------------------------------------------------------------
# SESEncoder tests
# ---------------------------------------------------------------------------

class TestSESEncoder(unittest.TestCase):

    def setUp(self):
        self.df = _make_ses_df(n=200, seed=1)
        self.enc = SESEncoder()

    def test_fit_transform_shape(self):
        X = self.enc.fit_transform(self.df)
        self.assertEqual(len(X), len(self.df))
        # sexo(1) + edad(1) + region(3) + empleo(4) = 9 columns
        self.assertEqual(X.shape[1], 9)

    def test_no_nans_in_output(self):
        X = self.enc.fit_transform(self.df)
        self.assertFalse(X.isnull().any().any())

    def test_sexo_binary(self):
        X = self.enc.fit_transform(self.df)
        self.assertIn('sexo', X.columns)
        self.assertTrue(X['sexo'].isin([0.0, 1.0]).all())

    def test_edad_ordinal_range(self):
        X = self.enc.fit_transform(self.df)
        self.assertIn('edad', X.columns)
        self.assertTrue((X['edad'] >= 0).all())
        self.assertTrue((X['edad'] <= 6).all())

    def test_region_one_hot_columns(self):
        X = self.enc.fit_transform(self.df)
        region_cols = [c for c in X.columns if c.startswith('region_')]
        # 4 categories → 3 dummies (drop first)
        self.assertEqual(len(region_cols), 3)

    def test_empleo_one_hot_columns(self):
        X = self.enc.fit_transform(self.df)
        empleo_cols = [c for c in X.columns if c.startswith('empleo_')]
        # 5 categories → 4 dummies (drop first)
        self.assertEqual(len(empleo_cols), 4)

    def test_transform_subset_of_ses_vars(self):
        """Should work even if some SES columns are absent from the DataFrame."""
        df_partial = self.df[['sexo', 'edad', 'Pondi2', 'p_nominal']].copy()
        enc = SESEncoder()
        X = enc.fit_transform(df_partial)
        # Only sexo + edad available
        self.assertIn('sexo', X.columns)
        self.assertIn('edad', X.columns)
        region_cols = [c for c in X.columns if c.startswith('region_')]
        self.assertEqual(len(region_cols), 0)


# ---------------------------------------------------------------------------
# SurveyVarModel tests
# ---------------------------------------------------------------------------

class TestSurveyVarModel(unittest.TestCase):

    def setUp(self):
        self.df = _make_ses_df(n=400, seed=2)
        self.ses_vars = ['sexo', 'edad', 'region', 'empleo']

    def test_fit_nominal(self):
        model = SurveyVarModel()
        model.fit(self.df, 'p_nominal', self.ses_vars)
        self.assertIsNotNone(model._model_result)
        self.assertEqual(len(model._categories), 5)

    def test_fit_ordinal(self):
        """Ordinal variable should fit without error."""
        # Inject ordinal-pattern values so detect_variable_types picks 'ordinal'
        df = self.df.copy()
        df['p_likert'] = df['p_ordinal']  # values like 'mucho','bastante' are ordinal
        model = SurveyVarModel()
        model.fit(df, 'p_likert', self.ses_vars)
        self.assertIsNotNone(model._model_result)

    def test_predict_proba_shape(self):
        model = SurveyVarModel()
        model.fit(self.df, 'p_nominal', self.ses_vars)
        # Use the model's own encoder to guarantee feature compatibility
        X = model._encoder.transform(self.df.head(50)[self.ses_vars])
        probs = model.predict_proba(X)
        self.assertEqual(probs.shape, (50, 5))

    def test_predict_proba_sums_to_one(self):
        model = SurveyVarModel()
        model.fit(self.df, 'p_nominal', self.ses_vars)
        X = model._encoder.transform(self.df.head(20)[self.ses_vars])
        probs = model.predict_proba(X)
        row_sums = probs.sum(axis=1)
        np.testing.assert_allclose(row_sums.values, np.ones(20), atol=1e-6)

    def test_simulate_responses_length(self):
        model = SurveyVarModel()
        model.fit(self.df, 'p_nominal', self.ses_vars)
        # simulate_responses accepts raw SES df (encoding happens internally)
        sim_pop = self.df[self.ses_vars].copy()
        responses = model.simulate_responses(sim_pop)
        self.assertEqual(len(responses), len(sim_pop))

    def test_simulate_responses_valid_categories(self):
        model = SurveyVarModel()
        model.fit(self.df, 'p_nominal', self.ses_vars)
        sim_pop = self.df[self.ses_vars].copy()
        responses = model.simulate_responses(sim_pop)
        valid_cats = set(model._categories)
        self.assertTrue(set(responses.unique()).issubset(valid_cats))

    def test_insufficient_data_raises(self):
        model = SurveyVarModel()
        tiny = self.df.head(10)
        with self.assertRaises(ValueError):
            model.fit(tiny, 'p_nominal', self.ses_vars)


# ---------------------------------------------------------------------------
# CrossDatasetBivariateEstimator tests
# ---------------------------------------------------------------------------

class TestCrossDatasetBivariateEstimator(unittest.TestCase):

    def setUp(self):
        self.df_a = _make_ses_df(n=400, seed=3)
        self.df_b = _make_ses_df(n=400, seed=4)
        self.estimator = CrossDatasetBivariateEstimator(n_sim=500)

    def test_estimate_returns_dict(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='p_nominal',
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_estimate_has_required_keys(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='p_nominal',
        )
        for key in ('cramers_v', 'p_value', 'chi_square', 'degrees_of_freedom',
                    'n_simulated', 'method', 'note'):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_cramers_v_in_range(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='p_nominal',
        )
        self.assertGreaterEqual(result['cramers_v'], 0.0)
        self.assertLessEqual(result['cramers_v'], 1.0)

    def test_p_value_in_range(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='p_nominal',
        )
        self.assertGreaterEqual(result['p_value'], 0.0)
        self.assertLessEqual(result['p_value'], 1.0)

    def test_n_simulated(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='p_nominal',
        )
        self.assertEqual(result['n_simulated'], 500)

    def test_method_label(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='p_nominal',
        )
        self.assertEqual(result['method'], 'ses_simulation')

    def test_missing_column_returns_none(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='nonexistent_col',
        )
        self.assertIsNone(result)

    def test_ses_population_sampling(self):
        """Reference population should have correct size and only SES columns."""
        pop = self.estimator._sample_ses_population(
            self.df_a, self.df_b,
            ses_vars=['sexo', 'edad', 'region', 'empleo'],
            weight_col='Pondi2',
        )
        self.assertEqual(len(pop), 500)
        for col in ['sexo', 'edad', 'region', 'empleo']:
            self.assertIn(col, pop.columns)


if __name__ == '__main__':
    unittest.main()
