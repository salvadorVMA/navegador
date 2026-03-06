"""
Unit tests for ses_regression.py — SESEncoder, SurveyVarModel,
CrossDatasetBivariateEstimator, ResidualBridgeEstimator,
EcologicalBridgeEstimator.

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
    ResidualBridgeEstimator,
    EcologicalBridgeEstimator,
    SES_REGRESSION_VARS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ses_df(n: int = 400, seed: int = 0) -> pd.DataFrame:
    """Synthetic DataFrame with SES columns and two target variables."""
    rng = np.random.default_rng(seed)

    sexo      = rng.choice(['01', '02'], n)
    edad      = rng.choice(['19-24', '25-34', '35-44', '45-54', '55-64', '65+'], n)
    region    = rng.choice(['01', '02', '03', '04'], n)
    empleo    = rng.choice(['01', '02', '03', '04', '05'], n)
    escol     = rng.choice([1.0, 2.0, 3.0, 4.0, 5.0], n)
    tam_loc   = rng.choice([1.0, 2.0, 3.0, 4.0], n)
    est_civil = rng.choice([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], n)
    weight    = rng.uniform(0.5, 2.5, n).round(4)

    # Nominal target (5 response categories)
    nominal = rng.choice(['1', '2', '3', '4', '5'], n)
    # Ordinal target (Likert)
    ordinal = rng.choice(['mucho', 'bastante', 'poco', 'nada'], n)

    return pd.DataFrame({
        'sexo': sexo,
        'edad': edad,
        'region': region,
        'empleo': empleo,
        'escol': escol,
        'Tam_loc': tam_loc,
        'est_civil': est_civil,
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
        # sexo(1) + edad(1) + region(3) + empleo(4) + escol(1) + Tam_loc(1) + est_civil(6) = 17 columns
        self.assertEqual(X.shape[1], 17)

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
        # simulate_responses normalises to float-or-str for crosstab compatibility;
        # compare using the same normalisation so int 1 == float 1.0 == "1.0" etc.
        def _norm(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return str(v)
        valid_cats = {_norm(c) for c in model._categories}
        self.assertTrue({_norm(r) for r in responses.unique()}.issubset(valid_cats))

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


    def test_estimate_returns_column_profiles(self):
        """estimate() must return column_profiles and top_contrasts dicts."""
        result = self.estimator.estimate(
            var_id_a='p1|AAA',
            var_id_b='p1|BBB',
            df_a=self.df_a,
            df_b=self.df_b,
            col_a='p_nominal',
            col_b='p_nominal',
        )
        self.assertIn('column_profiles', result)
        self.assertIn('top_contrasts', result)

        # column_profiles: nested dict, proportions sum to ~1.0 per column
        cp = result['column_profiles']
        self.assertIsInstance(cp, dict)
        self.assertGreater(len(cp), 0)
        for col_cat, profile in cp.items():
            self.assertIsInstance(profile, dict)
            total = sum(profile.values())
            self.assertAlmostEqual(total, 1.0, places=2,
                                   msg=f"column '{col_cat}' proportions sum to {total}")

        # top_contrasts: at most 3 entries with required keys
        tc = result['top_contrasts']
        self.assertIsInstance(tc, dict)
        self.assertLessEqual(len(tc), 3)
        for cat, info in tc.items():
            for key in ('min_pct', 'max_pct', 'range', 'min_when', 'max_when'):
                self.assertIn(key, info, f"top_contrasts['{cat}'] missing key '{key}'")
            self.assertGreaterEqual(info['range'], 0.0)
            self.assertLessEqual(info['max_pct'], 1.0)
            self.assertGreaterEqual(info['min_pct'], 0.0)


# ---------------------------------------------------------------------------
# Helpers for diagnostics tests
# ---------------------------------------------------------------------------

def _make_noisy_df(n: int = 500, seed: int = 20) -> pd.DataFrame:
    """Pure-noise dataset: target is independent of all SES predictors.

    Expected: pseudo-R² ≈ 0, LLR p-value ≈ large.
    """
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        'sexo'     : rng.choice(['01', '02'], n),
        'edad'     : rng.choice(['19-24', '25-34', '35-44', '45-54'], n),
        'region'   : rng.choice(['01', '02', '03'], n),
        'empleo'   : rng.choice(['01', '02', '03', '04'], n),
        'Pondi2'   : rng.uniform(0.5, 2.0, n),
        'p_target' : rng.choice(['1', '2'], n),   # binary, no SES signal
    })


def _make_signal_df(n: int = 700, seed: int = 30, p_signal: float = 0.90) -> pd.DataFrame:
    """Dataset where *sexo* is a strong predictor of target.

    sexo='01' → p_signal probability of target='1'
    sexo='02' → p_signal probability of target='2'

    Expected: pseudo-R² >> 0, dominant_ses_group == 'sexo'.
    """
    rng = np.random.default_rng(seed)
    sexo = rng.choice(['01', '02'], n)
    age  = rng.choice(['19-24', '25-34', '35-44', '45-54'], n)
    reg  = rng.choice(['01', '02', '03'], n)
    emp  = rng.choice(['01', '02', '03', '04'], n)
    weight = rng.uniform(0.5, 2.0, n)

    target = np.where(
        sexo == '01',
        rng.choice(['1', '2'], n, p=[p_signal, 1 - p_signal]),
        rng.choice(['1', '2'], n, p=[1 - p_signal, p_signal]),
    )
    return pd.DataFrame({
        'sexo': sexo, 'edad': age, 'region': reg,
        'empleo': emp, 'Pondi2': weight, 'p_target': target,
    })


# ---------------------------------------------------------------------------
# Regression diagnostics tests
# ---------------------------------------------------------------------------

class TestSurveyVarModelDiagnostics(unittest.TestCase):
    """
    Tests for SurveyVarModel.diagnostics().

    Covers:
      - Output structure (required keys, types)
      - Pseudo-R² and LLR p-value are in valid numeric ranges
      - t-statistics are finite (not NaN)
      - With injected signal, the correct SES predictor is identified
      - pseudo-R² is higher for signal data than noise data
      - LLR p-value is significant when there is a real SES → outcome relationship
      - Ordinal model also returns diagnostics
      - RuntimeError when model not yet fitted
    """

    SES_VARS = ['sexo', 'edad', 'region', 'empleo']

    def _fit_model(self, df: pd.DataFrame, target: str = 'p_target') -> SurveyVarModel:
        model = SurveyVarModel()
        model.fit(df, target, self.SES_VARS)
        return model

    # --- Structure --------------------------------------------------------

    def test_diagnostics_returns_dict(self):
        model = self._fit_model(_make_noisy_df())
        diag = model.diagnostics()
        self.assertIsInstance(diag, dict)

    def test_diagnostics_has_all_required_keys(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        required = {
            'model_type', 'n_categories', 'pseudo_r2', 'llr_pvalue',
            'coef_table', 'top_predictor', 'dominant_ses_group',
        }
        for key in required:
            self.assertIn(key, diag, f"Missing key: {key}")

    def test_model_type_is_valid_string(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        self.assertIn(diag['model_type'], ('ordered', 'mnlogit'))

    def test_n_categories_matches_target(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        # binary target → 2 categories
        self.assertEqual(diag['n_categories'], 2)

    # --- Pseudo R² --------------------------------------------------------

    def test_pseudo_r2_in_unit_interval(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        r2 = diag['pseudo_r2']
        self.assertTrue(0.0 <= r2 <= 1.0, f"pseudo_r2={r2} outside [0,1]")

    def test_pseudo_r2_near_zero_for_noise(self):
        """Pure-noise data → McFadden R² should be well below 0.10."""
        diag = self._fit_model(_make_noisy_df(n=600)).diagnostics()
        self.assertLess(diag['pseudo_r2'], 0.10,
                        f"Expected R²<0.10 for noise, got {diag['pseudo_r2']:.4f}")

    def test_pseudo_r2_higher_with_signal(self):
        """Model fit on data with a real signal should have higher R² than noise."""
        r2_noise  = self._fit_model(_make_noisy_df(n=600, seed=20)).diagnostics()['pseudo_r2']
        r2_signal = self._fit_model(_make_signal_df(n=700, seed=30)).diagnostics()['pseudo_r2']
        self.assertGreater(r2_signal, r2_noise,
                           f"Signal R²={r2_signal:.4f} should exceed noise R²={r2_noise:.4f}")

    def test_pseudo_r2_substantial_with_strong_signal(self):
        """With 90% correlation between sexo and target, McFadden R² > 0.15."""
        diag = self._fit_model(_make_signal_df(n=700, p_signal=0.90)).diagnostics()
        self.assertGreater(diag['pseudo_r2'], 0.15,
                           f"Expected R²>0.15 for strong signal, got {diag['pseudo_r2']:.4f}")

    # --- LLR p-value ------------------------------------------------------

    def test_llr_pvalue_in_unit_interval(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        pv = diag['llr_pvalue']
        self.assertTrue(0.0 <= pv <= 1.0, f"llr_pvalue={pv} outside [0,1]")

    def test_llr_pvalue_significant_with_strong_signal(self):
        """With strong SES → outcome signal, the LLR test should reject H0."""
        diag = self._fit_model(_make_signal_df(n=700, p_signal=0.90)).diagnostics()
        self.assertLess(diag['llr_pvalue'], 0.01,
                        f"Expected LLR p<0.01 for strong signal, got {diag['llr_pvalue']:.4f}")

    # --- Coefficient table ------------------------------------------------

    def test_coef_table_is_list_of_dicts(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        ct = diag['coef_table']
        self.assertIsInstance(ct, list)
        self.assertGreater(len(ct), 0)
        for row in ct:
            self.assertIsInstance(row, dict)

    def test_coef_table_has_required_row_keys(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        for row in diag['coef_table']:
            for key in ('feature', 'coef', 'std_err', 't_stat', 'p_value', 'abs_t'):
                self.assertIn(key, row, f"coef_table row missing key '{key}'")

    def test_t_stats_are_finite(self):
        """No NaN or inf t-statistics — model convergence check."""
        diag = self._fit_model(_make_noisy_df(n=600)).diagnostics()
        for row in diag['coef_table']:
            self.assertTrue(np.isfinite(row['t_stat']),
                            f"Non-finite t_stat for feature '{row['feature']}'")

    def test_std_errs_are_positive(self):
        """Standard errors must be strictly positive."""
        diag = self._fit_model(_make_signal_df()).diagnostics()
        for row in diag['coef_table']:
            self.assertGreater(row['std_err'], 0.0,
                               f"std_err ≤ 0 for feature '{row['feature']}'")

    def test_p_values_in_unit_interval(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        for row in diag['coef_table']:
            self.assertGreaterEqual(row['p_value'], 0.0)
            self.assertLessEqual(row['p_value'], 1.0)

    def test_abs_t_matches_t_stat(self):
        """abs_t should equal |t_stat| for each row."""
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        for row in diag['coef_table']:
            self.assertAlmostEqual(row['abs_t'], abs(row['t_stat']), places=6,
                                   msg=f"abs_t mismatch for '{row['feature']}'")

    def test_coef_table_sorted_by_abs_t_descending(self):
        """Rows must be sorted largest-|t| first."""
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        abs_ts = [r['abs_t'] for r in diag['coef_table']]
        self.assertEqual(abs_ts, sorted(abs_ts, reverse=True),
                         "coef_table is not sorted by abs_t descending")

    def test_feature_names_are_strings(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        for row in diag['coef_table']:
            self.assertIsInstance(row['feature'], str)

    # --- Top predictor ----------------------------------------------------

    def test_top_predictor_is_string(self):
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        self.assertIsInstance(diag['top_predictor'], str)
        self.assertGreater(len(diag['top_predictor']), 0)

    def test_dominant_ses_group_in_ses_vars(self):
        """dominant_ses_group should be one of the known SES variable roots."""
        diag = self._fit_model(_make_noisy_df()).diagnostics()
        self.assertIn(diag['dominant_ses_group'], self.SES_VARS,
                      f"Unexpected dominant_ses_group: {diag['dominant_ses_group']}")

    def test_top_predictor_is_sexo_with_injected_signal(self):
        """When sexo is the sole strong predictor, dominant_ses_group must be 'sexo'."""
        diag = self._fit_model(_make_signal_df(n=700, p_signal=0.92)).diagnostics()
        self.assertEqual(
            diag['dominant_ses_group'], 'sexo',
            f"Expected dominant_ses_group='sexo', got '{diag['dominant_ses_group']}'. "
            f"Top feature: '{diag['top_predictor']}', "
            f"coef_table: {[(r['feature'], round(r['abs_t'], 2)) for r in diag['coef_table'][:4]]}"
        )

    def test_top_predictor_has_highest_abs_t(self):
        """top_predictor's abs_t should match the first row of coef_table."""
        diag = self._fit_model(_make_signal_df()).diagnostics()
        if diag['coef_table']:
            expected_feat = diag['coef_table'][0]['feature']
            self.assertEqual(diag['top_predictor'], expected_feat)

    # --- Ordinal model ----------------------------------------------------

    def test_diagnostics_ordinal_model(self):
        """diagnostics() must work when the fitted model is OrderedModel."""
        df = _make_ses_df(n=500, seed=5)
        # p_ordinal has 4 Likert-style categories → OrderedModel path
        model = SurveyVarModel()
        model.fit(df, 'p_ordinal', self.SES_VARS)
        diag = model.diagnostics()
        self.assertIn(diag['model_type'], ('ordered', 'mnlogit'))
        self.assertIsInstance(diag['coef_table'], list)
        self.assertGreater(len(diag['coef_table']), 0)
        r2 = diag['pseudo_r2']
        self.assertTrue(0.0 <= r2 <= 1.0 or np.isnan(r2),
                        f"pseudo_r2={r2} out of range for ordinal model")

    # --- Error handling ---------------------------------------------------

    def test_diagnostics_raises_if_not_fitted(self):
        """RuntimeError must be raised on an unfitted model."""
        model = SurveyVarModel()
        with self.assertRaises(RuntimeError):
            model.diagnostics()


# ---------------------------------------------------------------------------
# Fixture: geographic DataFrame for EcologicalBridgeEstimator tests
# ---------------------------------------------------------------------------

def _make_geo_df(n: int = 800, seed: int = 0) -> pd.DataFrame:
    """Synthetic DataFrame with geographic columns (edo, Tam_loc) and targets.

    Uses 10 states × 4 locality sizes = 40 possible cells.
    At n=800 the expected cell size is 20, matching the default min_cell_n.
    """
    rng = np.random.default_rng(seed)
    edo     = rng.integers(1, 11, n).astype(str)          # states 1-10
    tam_loc = rng.choice([1.0, 2.0, 3.0, 4.0], n)
    weight  = rng.uniform(0.5, 2.5, n).round(4)
    nominal = rng.choice(['1', '2', '3', '4', '5'], n)
    ordinal = rng.choice(['mucho', 'bastante', 'poco', 'nada'], n)
    return pd.DataFrame({
        'edo': edo,
        'Tam_loc': tam_loc,
        'Pondi2': weight,
        'p_nominal': nominal,
        'p_ordinal': ordinal,
    })


# ---------------------------------------------------------------------------
# ResidualBridgeEstimator tests
# ---------------------------------------------------------------------------

class TestResidualBridgeEstimator(unittest.TestCase):
    """Tests for ResidualBridgeEstimator.estimate()."""

    def setUp(self):
        self.df_a = _make_ses_df(n=500, seed=50)
        self.df_b = _make_ses_df(n=500, seed=51)
        # Small n_sim and n_cells for test speed
        self.estimator = ResidualBridgeEstimator(n_sim=300, n_cells=8, min_cell_size=5)

    def _run(self):
        return self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b='p_nominal',
        )

    def test_returns_dict(self):
        result = self._run()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_required_keys(self):
        result = self._run()
        for key in ('cramers_v_residual', 'cramers_v_baseline', 'ses_fraction',
                    'stratified_gamma', 'n_cells_used', 'n_simulated', 'method', 'note'):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_method_label(self):
        self.assertEqual(self._run()['method'], 'ses_residual_bridge')

    def test_cramers_v_residual_in_range(self):
        v = self._run()['cramers_v_residual']
        self.assertGreaterEqual(v, 0.0)
        self.assertLessEqual(v, 1.0)

    def test_cramers_v_baseline_in_range(self):
        v = self._run()['cramers_v_baseline']
        self.assertGreaterEqual(v, 0.0)
        self.assertLessEqual(v, 1.0)

    def test_ses_fraction_non_negative(self):
        frac = self._run()['ses_fraction']
        if frac is not None:
            self.assertGreaterEqual(frac, 0.0)

    def test_n_cells_used_positive(self):
        self.assertGreater(self._run()['n_cells_used'], 0)

    def test_n_simulated_positive(self):
        self.assertGreater(self._run()['n_simulated'], 0)

    def test_missing_column_returns_none(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b='nonexistent_col',
        )
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# EcologicalBridgeEstimator tests
# ---------------------------------------------------------------------------

class TestEcologicalBridgeEstimator(unittest.TestCase):
    """Tests for EcologicalBridgeEstimator.estimate()."""

    def setUp(self):
        # Use small min_cell_n and min_merged_cells for test fixture size
        self.df_a = _make_geo_df(n=800, seed=60)
        self.df_b = _make_geo_df(n=800, seed=61)
        self.estimator = EcologicalBridgeEstimator(
            min_cell_n=5, min_merged_cells=10, n_bootstrap=50
        )

    def _run(self, col_b='p_nominal', cell_cols=None):
        return self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b=col_b,
            cell_cols=cell_cols or ['edo', 'Tam_loc'],
        )

    def test_returns_dict(self):
        result = self._run()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_required_keys(self):
        result = self._run()
        for key in ('spearman_rho', 'p_value', 'ci_95', 'n_cells',
                    'cell_cols_used', 'method', 'note'):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_cell_cols_used_is_subset_of_requested(self):
        result = self._run()
        self.assertIsInstance(result['cell_cols_used'], list)
        self.assertGreater(len(result['cell_cols_used']), 0)
        for c in result['cell_cols_used']:
            self.assertIn(c, ['edo', 'Tam_loc'])

    def test_method_label(self):
        self.assertEqual(self._run()['method'], 'ecological_bridge')

    def test_spearman_rho_in_range(self):
        rho = self._run()['spearman_rho']
        self.assertGreaterEqual(rho, -1.0)
        self.assertLessEqual(rho, 1.0)

    def test_p_value_in_range(self):
        p = self._run()['p_value']
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)

    def test_ci_95_is_ordered_pair(self):
        ci = self._run()['ci_95']
        self.assertIsInstance(ci, tuple)
        self.assertEqual(len(ci), 2)
        lo, hi = ci
        if not (np.isnan(lo) or np.isnan(hi)):
            self.assertLessEqual(lo, hi)

    def test_n_cells_positive(self):
        self.assertGreater(self._run()['n_cells'], 0)

    def test_missing_target_column_returns_none(self):
        result = self._run(col_b='nonexistent_col')
        self.assertIsNone(result)

    def test_all_cell_cols_missing_returns_none(self):
        """When none of the requested cell_cols exist in either df, return None."""
        result = self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b='p_nominal',
            cell_cols=['nonexistent_col_a', 'nonexistent_col_b'],
        )
        self.assertIsNone(result)

    def test_partial_cell_cols_degrade_gracefully(self):
        """When one cell_col is absent, the key falls back to the available one."""
        df_a_no_loc = self.df_a.drop(columns=['Tam_loc'])
        df_b_no_loc = self.df_b.drop(columns=['Tam_loc'])
        result = self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=df_a_no_loc, df_b=df_b_no_loc,
            col_a='p_nominal', col_b='p_nominal',
            cell_cols=['edo', 'Tam_loc'],
        )
        # Falls back to 'edo' only (10 cells); with min_merged_cells=10 may pass
        self.assertTrue(result is None or isinstance(result, dict))
        if result is not None:
            self.assertEqual(result['cell_cols_used'], ['edo'])

    def test_demographic_cell_cols(self):
        """cell_cols=['escol', 'edad'] uses the SES fixture directly."""
        ses_est = EcologicalBridgeEstimator(
            min_cell_n=5, min_merged_cells=10, n_bootstrap=20
        )
        # _make_ses_df has escol and edad — 5×7=35 possible cells
        df_a = _make_ses_df(n=600, seed=80)
        df_b = _make_ses_df(n=600, seed=81)
        result = ses_est.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=df_a, df_b=df_b,
            col_a='p_nominal', col_b='p_nominal',
            cell_cols=['escol', 'edad'],
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['method'], 'ecological_bridge')
        self.assertIn('escol', result['cell_cols_used'])
        self.assertIn('edad', result['cell_cols_used'])


# ---------------------------------------------------------------------------
# Bridge comparison tests
# ---------------------------------------------------------------------------

class TestBridgeComparison(unittest.TestCase):
    """
    Cross-method comparison tests.

    Verifies that all three estimators can run on the same variable pair and
    that their outputs have the expected structural relationships.

    Uses the SES fixture (_make_ses_df) for the baseline + residual estimators,
    and the geographic fixture (_make_geo_df) for the ecological estimator.
    Note: EcologicalBridgeEstimator requires geo columns not present in the
    SES fixture, so it is tested separately.
    """

    def setUp(self):
        self.df_a = _make_ses_df(n=500, seed=70)
        self.df_b = _make_ses_df(n=500, seed=71)
        self.df_geo_a = _make_geo_df(n=800, seed=72)
        self.df_geo_b = _make_geo_df(n=800, seed=73)

        self.baseline  = CrossDatasetBivariateEstimator(n_sim=300)
        self.residual  = ResidualBridgeEstimator(n_sim=300, n_cells=8, min_cell_size=5)
        self.ecological = EcologicalBridgeEstimator(
            min_cell_n=5, min_merged_cells=10, n_bootstrap=50
        )

    def _baseline_result(self):
        return self.baseline.estimate(
            'p1|AAA', 'p1|BBB', self.df_a, self.df_b, 'p_nominal', 'p_nominal'
        )

    def _residual_result(self):
        return self.residual.estimate(
            'p1|AAA', 'p1|BBB', self.df_a, self.df_b, 'p_nominal', 'p_nominal'
        )

    def _ecological_result(self):
        return self.ecological.estimate(
            'p1|AAA', 'p1|BBB',
            self.df_geo_a, self.df_geo_b,
            'p_nominal', 'p_nominal',
            cell_cols=['edo', 'Tam_loc'],
        )

    def test_all_three_return_results(self):
        self.assertIsNotNone(self._baseline_result())
        self.assertIsNotNone(self._residual_result())
        self.assertIsNotNone(self._ecological_result())

    def test_method_labels_are_distinct(self):
        labels = {
            self._baseline_result()['method'],
            self._residual_result()['method'],
            self._ecological_result()['method'],
        }
        self.assertEqual(len(labels), 3,
                         "All three methods must have distinct 'method' labels")

    def test_baseline_has_cramers_v(self):
        r = self._baseline_result()
        self.assertIn('cramers_v', r)
        self.assertGreaterEqual(r['cramers_v'], 0.0)

    def test_residual_has_cramers_v_residual(self):
        r = self._residual_result()
        self.assertIn('cramers_v_residual', r)
        self.assertGreaterEqual(r['cramers_v_residual'], 0.0)

    def test_ecological_has_spearman_rho(self):
        r = self._ecological_result()
        self.assertIn('spearman_rho', r)
        self.assertGreaterEqual(r['spearman_rho'], -1.0)
        self.assertLessEqual(r['spearman_rho'], 1.0)

    def test_residual_baseline_v_also_in_range(self):
        """cramers_v_baseline in residual result must match valid V range."""
        r = self._residual_result()
        v_bl = r['cramers_v_baseline']
        self.assertGreaterEqual(v_bl, 0.0)
        self.assertLessEqual(v_bl, 1.0)

    def test_ses_fraction_when_present(self):
        """ses_fraction = V_residual / V_baseline must be >= 0."""
        frac = self._residual_result().get('ses_fraction')
        if frac is not None:
            self.assertGreaterEqual(frac, 0.0)

    def test_ecological_ci_ordered(self):
        ci = self._ecological_result()['ci_95']
        lo, hi = ci
        if not (np.isnan(lo) or np.isnan(hi)):
            self.assertLessEqual(lo, hi)


if __name__ == '__main__':
    unittest.main()
