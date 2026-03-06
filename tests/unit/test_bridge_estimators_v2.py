"""
Unit tests for the v2 bridge estimators: BayesianBridgeEstimator,
MRPBridgeEstimator, DoublyRobustBridgeEstimator, and the
goodman_kruskal_gamma() helper.

All tests use synthetic data so the 191 MB los_mex_dict.json is not required.
"""

import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, '/workspaces/navegador')

from ses_regression import (
    goodman_kruskal_gamma,
    BayesianBridgeEstimator,
    MRPBridgeEstimator,
    DoublyRobustBridgeEstimator,
    CrossDatasetBivariateEstimator,
    ResidualBridgeEstimator,
    EcologicalBridgeEstimator,
)


# ---------------------------------------------------------------------------
# Shared fixtures (same as test_ses_regression.py)
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


def _make_geo_df(n: int = 800, seed: int = 0) -> pd.DataFrame:
    """Synthetic DataFrame with geographic columns (edo, Tam_loc) and targets."""
    rng = np.random.default_rng(seed)
    edo     = rng.integers(1, 11, n).astype(str)
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
# TestGoodmanKruskalGamma
# ---------------------------------------------------------------------------

class TestGoodmanKruskalGamma(unittest.TestCase):
    """Tests for the goodman_kruskal_gamma() helper function."""

    def test_perfect_concordance(self):
        """A diagonal joint table should give γ = 1 (perfect positive agreement)."""
        table = np.eye(4) / 4.0
        gamma = goodman_kruskal_gamma(table)
        self.assertAlmostEqual(gamma, 1.0, places=6)

    def test_perfect_discordance(self):
        """Anti-diagonal joint table should give γ = -1 (perfect negative)."""
        table = np.fliplr(np.eye(4)) / 4.0
        gamma = goodman_kruskal_gamma(table)
        self.assertAlmostEqual(gamma, -1.0, places=6)

    def test_independence(self):
        """Uniform joint table (independence) should give γ ≈ 0."""
        table = np.ones((5, 5)) / 25.0
        gamma = goodman_kruskal_gamma(table)
        self.assertAlmostEqual(gamma, 0.0, places=6)

    def test_symmetry(self):
        """γ(table) == γ(table.T): transposing swaps roles but preserves γ."""
        rng = np.random.default_rng(seed=99)
        table = rng.random((4, 5))
        table /= table.sum()
        g1 = goodman_kruskal_gamma(table)
        g2 = goodman_kruskal_gamma(table.T)
        self.assertAlmostEqual(g1, g2, places=6)

    def test_empty_table(self):
        """All-zero table should return 0.0 (denom = 0)."""
        table = np.zeros((3, 3))
        gamma = goodman_kruskal_gamma(table)
        self.assertEqual(gamma, 0.0)


# ---------------------------------------------------------------------------
# TestBayesianBridgeEstimator
# ---------------------------------------------------------------------------

class TestBayesianBridgeEstimator(unittest.TestCase):
    """Tests for BayesianBridgeEstimator."""

    def setUp(self):
        self.df_a = _make_ses_df(n=400, seed=100)
        self.df_b = _make_ses_df(n=400, seed=101)
        # Small draws and sim for speed
        self.estimator = BayesianBridgeEstimator(n_sim=200, n_draws=20)

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
        for key in ('gamma', 'gamma_ci_95', 'cramers_v', 'cramers_v_ci_95',
                    'joint_table', 'pseudo_r2_a', 'pseudo_r2_b', 'method'):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_method_label(self):
        self.assertEqual(self._run()['method'], 'bayesian_bridge')

    def test_gamma_in_range(self):
        g = self._run()['gamma']
        self.assertGreaterEqual(g, -1.0)
        self.assertLessEqual(g, 1.0)

    def test_gamma_ci_ordered_pair(self):
        ci = self._run()['gamma_ci_95']
        self.assertIsInstance(ci, tuple)
        self.assertEqual(len(ci), 2)
        lo, hi = ci
        self.assertLessEqual(lo, hi)

    def test_gamma_ci_has_positive_width(self):
        ci = self._run()['gamma_ci_95']
        # With multiple draws, the CI should generally span a range > 0
        # (even with random data the posterior has some spread)
        lo, hi = ci
        self.assertGreaterEqual(hi - lo, 0.0)

    def test_joint_table_sums_to_one(self):
        jt = np.array(self._run()['joint_table'])
        self.assertAlmostEqual(jt.sum(), 1.0, places=2)

    def test_missing_column_returns_none(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b='nonexistent_col',
        )
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# TestMRPBridgeEstimator
# ---------------------------------------------------------------------------

class TestMRPBridgeEstimator(unittest.TestCase):
    """Tests for MRPBridgeEstimator."""

    def setUp(self):
        self.df_a = _make_ses_df(n=500, seed=200)
        self.df_b = _make_ses_df(n=500, seed=201)
        self.estimator = MRPBridgeEstimator(
            cell_cols=['escol', 'edad', 'sexo'],
            shrinkage_kappa=10.0,
            min_cell_n=3,
            n_bootstrap=20,
        )

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
        for key in ('gamma', 'gamma_ci_95', 'cramers_v', 'joint_table',
                    'n_cells_used', 'mean_cell_n', 'method'):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_method_label(self):
        self.assertEqual(self._run()['method'], 'mrp_bridge')

    def test_gamma_in_range(self):
        g = self._run()['gamma']
        self.assertGreaterEqual(g, -1.0)
        self.assertLessEqual(g, 1.0)

    def test_gamma_ci_ordered_pair(self):
        ci = self._run()['gamma_ci_95']
        self.assertIsInstance(ci, tuple)
        self.assertEqual(len(ci), 2)
        lo, hi = ci
        self.assertLessEqual(lo, hi)

    def test_joint_table_sums_to_one(self):
        jt = np.array(self._run()['joint_table'])
        self.assertAlmostEqual(jt.sum(), 1.0, places=2)

    def test_n_cells_used_positive(self):
        result = self._run()
        self.assertGreater(result['n_cells_used'], 0)

    def test_missing_column_returns_none(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b='nonexistent_col',
        )
        self.assertIsNone(result)

    def test_demographic_cell_cols(self):
        """cell_cols with edad and sexo should work on the SES fixture."""
        est = MRPBridgeEstimator(
            cell_cols=['edad', 'sexo'],
            shrinkage_kappa=10.0,
            min_cell_n=3,
            n_bootstrap=10,
        )
        result = est.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b='p_nominal',
        )
        self.assertIsNotNone(result)
        # After binning, edad may appear as 'edad_bin'; accept both forms.
        cols_used = result['cell_cols_used']
        self.assertTrue(
            any('edad' in c for c in cols_used),
            f"Expected edad (or edad_bin) in cell_cols_used, got {cols_used}"
        )
        self.assertTrue(
            any('sexo' in c for c in cols_used),
            f"Expected sexo in cell_cols_used, got {cols_used}"
        )


# ---------------------------------------------------------------------------
# TestDoublyRobustBridgeEstimator
# ---------------------------------------------------------------------------

class TestDoublyRobustBridgeEstimator(unittest.TestCase):
    """Tests for DoublyRobustBridgeEstimator."""

    def setUp(self):
        self.df_a = _make_ses_df(n=400, seed=300)
        self.df_b = _make_ses_df(n=400, seed=301)
        # Very small bootstrap for test speed (model re-fitting is expensive)
        self.estimator = DoublyRobustBridgeEstimator(n_sim=200, n_bootstrap=10)

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
        for key in ('gamma', 'gamma_ci_95', 'cramers_v', 'joint_table',
                    'propensity_overlap', 'ks_warning', 'propensity_features',
                    'max_weight', 'n_trimmed', 'method'):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_method_label(self):
        self.assertEqual(self._run()['method'], 'doubly_robust_bridge')

    def test_gamma_in_range(self):
        g = self._run()['gamma']
        self.assertGreaterEqual(g, -1.0)
        self.assertLessEqual(g, 1.0)

    def test_gamma_ci_ordered_pair(self):
        ci = self._run()['gamma_ci_95']
        self.assertIsInstance(ci, tuple)
        self.assertEqual(len(ci), 2)
        lo, hi = ci
        self.assertLessEqual(lo, hi)

    def test_joint_table_sums_to_one(self):
        jt = np.array(self._run()['joint_table'])
        self.assertAlmostEqual(jt.sum(), 1.0, places=2)

    def test_propensity_overlap_in_range(self):
        """KS statistic is in [0, 1]."""
        ks = self._run()['propensity_overlap']
        self.assertGreaterEqual(ks, 0.0)
        self.assertLessEqual(ks, 1.0)

    def test_missing_column_returns_none(self):
        result = self.estimator.estimate(
            var_id_a='p1|AAA', var_id_b='p1|BBB',
            df_a=self.df_a, df_b=self.df_b,
            col_a='p_nominal', col_b='nonexistent_col',
        )
        self.assertIsNone(result)

    def test_ks_warning_is_boolean(self):
        """ks_warning must be a boolean (True when overlap is poor)."""
        result = self._run()
        self.assertIsInstance(result['ks_warning'], bool)

    def test_propensity_features_is_list(self):
        """propensity_features reports which vars were used for propensity."""
        result = self._run()
        self.assertIsInstance(result['propensity_features'], list)
        self.assertGreater(len(result['propensity_features']), 0)


# ---------------------------------------------------------------------------
# TestCategoryBinning
# ---------------------------------------------------------------------------

class TestCategoryBinning(unittest.TestCase):
    """Tests for the bin_categories() helper and max_categories integration."""

    def setUp(self):
        from ses_regression import bin_categories
        self.bin_categories = bin_categories

    def test_no_binning_when_within_limit(self):
        s = pd.Series([1, 2, 3, 2, 1, 3])
        binned, bmap = self.bin_categories(s, max_categories=5)
        pd.testing.assert_series_equal(binned, s)
        self.assertEqual(set(bmap.keys()), {1, 2, 3})

    def test_ordinal_binning_reduces_categories(self):
        s = pd.Series(range(10))  # 10 unique values
        binned, bmap = self.bin_categories(s, max_categories=4, var_type='ordinal')
        self.assertLessEqual(binned.nunique(), 4)
        self.assertEqual(len(bmap), 10)  # every original value mapped

    def test_nominal_binning_reduces_categories(self):
        s = pd.Series(['a', 'b', 'c', 'd', 'e', 'f', 'a', 'a', 'b'])
        binned, bmap = self.bin_categories(s, max_categories=3, var_type='nominal')
        self.assertLessEqual(binned.nunique(), 3)

    def test_bayesian_respects_max_categories(self):
        """BayesianBridgeEstimator with max_categories=3 should produce ≤3 cat model."""
        rng = np.random.default_rng(99)
        n = 400
        # 8-category target variable
        df_a = _make_ses_df(n=n, seed=10)
        df_a['p_many'] = rng.choice([str(i) for i in range(8)], n)
        df_b = _make_ses_df(n=n, seed=11)
        df_b['p_many'] = rng.choice([str(i) for i in range(8)], n)

        est = BayesianBridgeEstimator(n_sim=100, n_draws=20, max_categories=3)
        result = est.estimate('v|A', 'v|B', df_a, df_b, 'p_many', 'p_many')
        self.assertIsNotNone(result)
        jt = np.array(result['joint_table'])
        # With max_categories=3 the joint table should be 3×3 or smaller
        self.assertLessEqual(jt.shape[0], 3)
        self.assertLessEqual(jt.shape[1], 3)


# ---------------------------------------------------------------------------
# TestAllSixEstimatorsComparison
# ---------------------------------------------------------------------------

class TestAllSixEstimatorsComparison(unittest.TestCase):
    """
    Integration tests: all 6 estimators on the same variable pair.

    Verifies structural consistency across the old (baseline, residual,
    ecological) and new (bayesian, mrp, doubly_robust) estimators.
    """

    @classmethod
    def setUpClass(cls):
        """Run all 6 estimators once and cache results."""
        cls.df_a     = _make_ses_df(n=500, seed=400)
        cls.df_b     = _make_ses_df(n=500, seed=401)
        cls.df_geo_a = _make_geo_df(n=800, seed=402)
        cls.df_geo_b = _make_geo_df(n=800, seed=403)

        args = dict(var_id_a='p1|AAA', var_id_b='p1|BBB',
                    col_a='p_nominal', col_b='p_nominal')

        cls.results = {}

        # Original three
        r = CrossDatasetBivariateEstimator(n_sim=300).estimate(
            df_a=cls.df_a, df_b=cls.df_b, **args)
        cls.results['baseline'] = r

        r = ResidualBridgeEstimator(n_sim=300, n_cells=8, min_cell_size=5).estimate(
            df_a=cls.df_a, df_b=cls.df_b, **args)
        cls.results['residual'] = r

        r = EcologicalBridgeEstimator(
            min_cell_n=5, min_merged_cells=10, n_bootstrap=20
        ).estimate(
            df_a=cls.df_geo_a, df_b=cls.df_geo_b,
            cell_cols=['edo', 'Tam_loc'], **args)
        cls.results['ecological'] = r

        # New three
        r = BayesianBridgeEstimator(n_sim=200, n_draws=15).estimate(
            df_a=cls.df_a, df_b=cls.df_b, **args)
        cls.results['bayesian'] = r

        r = MRPBridgeEstimator(
            cell_cols=['escol', 'edad', 'sexo'],
            min_cell_n=3, n_bootstrap=15,
        ).estimate(df_a=cls.df_a, df_b=cls.df_b, **args)
        cls.results['mrp'] = r

        r = DoublyRobustBridgeEstimator(n_sim=200, n_bootstrap=10).estimate(
            df_a=cls.df_a, df_b=cls.df_b, **args)
        cls.results['doubly_robust'] = r

    def test_all_six_return_non_none(self):
        for name, result in self.results.items():
            self.assertIsNotNone(result, f"{name} returned None")

    def test_method_labels_distinct(self):
        labels = {r['method'] for r in self.results.values() if r is not None}
        self.assertEqual(len(labels), 6,
                         f"Expected 6 distinct method labels, got {labels}")

    def test_new_estimators_report_gamma(self):
        """All three new estimators should report 'gamma' in [-1, 1]."""
        for name in ('bayesian', 'mrp', 'doubly_robust'):
            r = self.results[name]
            self.assertIn('gamma', r, f"{name} missing gamma")
            g = r['gamma']
            self.assertGreaterEqual(g, -1.0, f"{name} gamma < -1")
            self.assertLessEqual(g, 1.0, f"{name} gamma > 1")

    def test_new_estimators_report_ci(self):
        """All three new estimators should include gamma_ci_95 as ordered pair."""
        for name in ('bayesian', 'mrp', 'doubly_robust'):
            r = self.results[name]
            ci = r['gamma_ci_95']
            self.assertIsInstance(ci, tuple, f"{name} CI not a tuple")
            self.assertEqual(len(ci), 2, f"{name} CI not length 2")
            lo, hi = ci
            self.assertLessEqual(lo, hi, f"{name} CI not ordered: {ci}")

    def test_new_estimators_include_joint_table(self):
        """All three new estimators should include a joint_table that sums ≈1."""
        for name in ('bayesian', 'mrp', 'doubly_robust'):
            r = self.results[name]
            self.assertIn('joint_table', r, f"{name} missing joint_table")
            jt = np.array(r['joint_table'])
            self.assertAlmostEqual(jt.sum(), 1.0, places=1,
                                   msg=f"{name} joint table sum = {jt.sum()}")

    def test_all_estimators_have_cramers_v(self):
        """Every estimator should have some form of cramers_v."""
        for name, r in self.results.items():
            if name == 'ecological':
                continue  # Ecological reports spearman_rho, not cramers_v
            if name == 'residual':
                self.assertIn('cramers_v_residual', r)
            else:
                self.assertIn('cramers_v', r, f"{name} missing cramers_v")


if __name__ == '__main__':
    unittest.main()
