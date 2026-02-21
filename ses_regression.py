"""
SES Regression Module for Navegador — Simulation-Based Cross-Dataset Bivariate Estimation

Uses SES variables (sexo, edad, region, empleo) as bridge variables to estimate
bivariate associations between survey questions that come from *different* surveys and
therefore never appear together in a single DataFrame.

Approach:
  1. Fit a regression model for each survey variable on SES predictors
     - Ordinal variable  → OrderedModel (proportional odds logistic)
     - Nominal variable  → MNLogit (multinomial logistic)
  2. Draw a reference SES population from the real marginal distribution
     (pooled from both surveys, weighted by Pondi2)
  3. Simulate responses for both variables using their respective models
  4. Compute chi-square + Cramér's V on the simulated joint distribution

Classes:
  SESEncoder                 — String SES codes → numeric feature matrix
  SurveyVarModel             — Fits and simulates one survey variable
  CrossDatasetBivariateEstimator — Orchestrates the two-model simulation
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats.contingency import association


# ---------------------------------------------------------------------------
# SES encoding constants
# ---------------------------------------------------------------------------

# Ordinal mapping for edad (age bins ordered youngest→oldest)
_EDAD_ORDER: Dict[str, int] = {
    '0-18': 0, '19-24': 1, '25-34': 2, '35-44': 3,
    '45-54': 4, '55-64': 5, '65+': 6,
}

# Nominal SES vars get one-hot encoding (first category dropped)
_NOMINAL_SES = ('sexo', 'region', 'empleo')
_ORDINAL_SES = ('edad',)

# SES variables used in regression features
SES_REGRESSION_VARS: List[str] = ['sexo', 'edad', 'region', 'empleo']


# ---------------------------------------------------------------------------
# SESEncoder
# ---------------------------------------------------------------------------

class SESEncoder:
    """
    Converts SES string-coded columns into a numeric feature matrix suitable
    for regression models.

    Encoding scheme:
      sexo   — binary (01→0, 02→1)
      edad   — ordinal int (0-18→0 … 65+→6)
      region — one-hot, drop first (3 dummy columns)
      empleo — one-hot, drop first (4 dummy columns)

    Usage:
      enc = SESEncoder()
      enc.fit(df)          # learns categories from data
      X = enc.transform(df)
    """

    def __init__(self) -> None:
        self._region_cats: List[str] = []
        self._empleo_cats: List[str] = []
        self._fitted = False

    # ------------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> 'SESEncoder':
        """Learn category sets from DataFrame (for one-hot vars)."""
        if 'region' in df.columns:
            self._region_cats = sorted(df['region'].dropna().unique().tolist())
        if 'empleo' in df.columns:
            self._empleo_cats = sorted(df['empleo'].dropna().unique().tolist())
        self._fitted = True
        return self

    # ------------------------------------------------------------------
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return numeric feature DataFrame, one row per input row."""
        if not self._fitted:
            self.fit(df)

        parts: List[pd.Series] = []

        # sexo — binary
        if 'sexo' in df.columns:
            parts.append(
                df['sexo'].map({'01': 0, '02': 1}).rename('sexo')
                .astype(float)
            )

        # edad — ordinal int
        if 'edad' in df.columns:
            parts.append(
                df['edad'].map(_EDAD_ORDER).rename('edad')
                .astype(float)
            )

        # region — one-hot (drop first category to avoid multicollinearity)
        if 'region' in df.columns and len(self._region_cats) > 1:
            for cat in self._region_cats[1:]:           # drop first
                parts.append(
                    (df['region'] == cat).astype(float).rename(f'region_{cat}')
                )

        # empleo — one-hot (drop first category)
        if 'empleo' in df.columns and len(self._empleo_cats) > 1:
            for cat in self._empleo_cats[1:]:           # drop first
                parts.append(
                    (df['empleo'] == cat).astype(float).rename(f'empleo_{cat}')
                )

        if not parts:
            raise ValueError("No SES columns found in DataFrame.")

        X = pd.concat(parts, axis=1)
        return X.fillna(0.0)

    # ------------------------------------------------------------------
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)

    @property
    def feature_names(self) -> List[str]:
        names = []
        names.append('sexo')
        names.append('edad')
        if len(self._region_cats) > 1:
            names.extend(f'region_{c}' for c in self._region_cats[1:])
        if len(self._empleo_cats) > 1:
            names.extend(f'empleo_{c}' for c in self._empleo_cats[1:])
        return names


# ---------------------------------------------------------------------------
# SurveyVarModel
# ---------------------------------------------------------------------------

class SurveyVarModel:
    """
    Fits a regression model for one survey variable regressed on SES features.

    Model selection (delegated to SESDataValidator.detect_variable_types):
      ordinal  → statsmodels OrderedModel (proportional odds logistic)
      nominal  → statsmodels MNLogit (multinomial logistic)

    Usage:
      model = SurveyVarModel()
      model.fit(df, target_col='p1', ses_vars=['sexo','edad','region','empleo'])
      probs = model.predict_proba(ses_feature_df)   # shape (n, n_categories)
      responses = model.simulate_responses(ses_pop_df)
    """

    def __init__(self) -> None:
        self._model_result = None
        self._categories: List[str] = []
        self._encoder: Optional[SESEncoder] = None
        self._var_type: str = 'nominal'
        self._target_col: str = ''

    # ------------------------------------------------------------------
    def fit(
        self,
        df: pd.DataFrame,
        target_col: str,
        ses_vars: List[str],
        weight_col: str = 'Pondi2',
    ) -> 'SurveyVarModel':
        """
        Fit the appropriate regression model.

        Args:
            df:         Survey DataFrame (already SES-preprocessed)
            target_col: Column name of the survey question to model
            ses_vars:   List of SES column names to use as predictors
            weight_col: Survey weight column name
        """
        from statsmodels.discrete.discrete_model import MNLogit
        from statsmodels.miscmodels.ordinal_model import OrderedModel
        from ses_analysis import SESDataValidator

        self._target_col = target_col

        # Detect variable type
        available_ses = [v for v in ses_vars if v in df.columns]
        if not available_ses:
            raise ValueError(f"No SES columns available: {ses_vars}")

        # Build working subset — drop rows with NA in target or SES
        cols_needed = [target_col] + available_ses
        if weight_col in df.columns:
            cols_needed.append(weight_col)
        work = df[cols_needed].dropna().copy()

        if len(work) < 30:
            raise ValueError(
                f"Insufficient data after dropping NAs: {len(work)} rows"
            )

        # Detect ordinal vs nominal using question values/labels
        var_labels = {target_col: target_col}   # no label text, fall back to values
        var_types = SESDataValidator.detect_variable_types(work[[target_col]], var_labels)
        self._var_type = var_types.get(target_col, 'nominal')

        # Ordered categories
        self._categories = sorted(work[target_col].dropna().unique().tolist(),
                                  key=lambda x: str(x))

        if len(self._categories) < 2:
            raise ValueError(f"Variable {target_col} has fewer than 2 categories.")

        # Encode SES features
        self._encoder = SESEncoder()
        X = self._encoder.fit_transform(work[available_ses])

        # Target: map categories to integer codes 0..K-1
        cat_to_int = {c: i for i, c in enumerate(self._categories)}
        y = work[target_col].map(cat_to_int)

        # Add constant for MNLogit; OrderedModel handles intercept internally
        import statsmodels.api as sm

        # Note: we do NOT pass freq_weights — Pondi2 is a probability weight,
        # not a replication count. Weighting is captured by the Pondi2-weighted
        # SES population sample drawn in CrossDatasetBivariateEstimator.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            if self._var_type == 'ordinal' and len(self._categories) > 2:
                self._model_result = OrderedModel(
                    y, X, distr='logit'
                ).fit(method='bfgs', disp=False)
            else:
                Xc = sm.add_constant(X, has_constant='add')
                self._model_result = MNLogit(y, Xc).fit(method='bfgs', disp=False)

        return self

    # ------------------------------------------------------------------
    def predict_proba(self, ses_feature_df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict P(category | SES) for each row in ses_feature_df.

        Args:
            ses_feature_df: Numeric SES feature matrix (from SESEncoder.transform)

        Returns:
            DataFrame of shape (n_rows, n_categories) with columns = category labels
        """
        import statsmodels.api as sm

        if self._model_result is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        if self._var_type == 'ordinal' and len(self._categories) > 2:
            probs = self._model_result.predict(ses_feature_df)
        else:
            Xc = sm.add_constant(ses_feature_df, has_constant='add')
            probs = self._model_result.predict(Xc)

        # probs is ndarray (n, K); wrap with category labels
        probs_arr = np.array(probs)
        if probs_arr.ndim == 1:
            probs_arr = probs_arr.reshape(-1, 1)
        probs_df = pd.DataFrame(
            probs_arr, columns=self._categories[:probs_arr.shape[1]],
            index=ses_feature_df.index,
        )
        # Replace NaN with uniform (numerical fallback), clip negatives, renormalise
        uniform = 1.0 / len(self._categories)
        probs_df = probs_df.fillna(uniform).clip(lower=0.0)
        row_sums = probs_df.sum(axis=1).replace(0, 1.0)
        probs_df = probs_df.div(row_sums, axis=0)
        return probs_df

    # ------------------------------------------------------------------
    def simulate_responses(self, ses_population_df: pd.DataFrame) -> pd.Series:
        """
        Draw one simulated response per row using predicted probabilities.

        Args:
            ses_population_df: DataFrame with SES columns (before encoding)

        Returns:
            pd.Series of simulated category codes, same index as input
        """
        if self._encoder is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X = self._encoder.transform(ses_population_df)
        probs_df = self.predict_proba(X)

        rng = np.random.default_rng(seed=None)
        responses = []
        for _, row in probs_df.iterrows():
            p = row.values.astype(float)
            # Safety: replace NaN, clip negatives, renormalise
            p = np.nan_to_num(p, nan=0.0)
            p = np.clip(p, 0, None)
            total = p.sum()
            if total == 0:
                p = np.ones_like(p) / len(p)
            else:
                p = p / total
            chosen = rng.choice(self._categories, p=p)
            responses.append(chosen)

        return pd.Series(responses, index=ses_population_df.index, name=self._target_col)


# ---------------------------------------------------------------------------
# CrossDatasetBivariateEstimator
# ---------------------------------------------------------------------------

class CrossDatasetBivariateEstimator:
    """
    Estimates pairwise bivariate associations between survey variables that
    come from *different* surveys, using SES as a bridge variable.

    The estimate() method:
      1. Fits SurveyVarModel for var_a using survey A's DataFrame
      2. Fits SurveyVarModel for var_b using survey B's DataFrame
      3. Samples a reference SES population from real marginals (Pondi2-weighted)
      4. Simulates joint (var_a, var_b) responses
      5. Returns chi-square + Cramér's V on the simulated joint distribution
    """

    def __init__(self, n_sim: int = 2000) -> None:
        self.n_sim = n_sim

    # ------------------------------------------------------------------
    def estimate(
        self,
        var_id_a: str,
        var_id_b: str,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        col_a: str,
        col_b: str,
        ses_vars: Optional[List[str]] = None,
        weight_col: str = 'Pondi2',
        var_type_a: Optional[str] = None,
        var_type_b: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate bivariate between col_a (in df_a) and col_b (in df_b).

        Args:
            var_id_a:    Full variable ID for var_a (e.g. 'p1|REL'), used for labelling
            var_id_b:    Full variable ID for var_b (e.g. 'p1|MED'), used for labelling
            df_a:        SES-preprocessed DataFrame containing col_a
            df_b:        SES-preprocessed DataFrame containing col_b
            col_a:       Column name of the target variable in df_a
            col_b:       Column name of the target variable in df_b
            ses_vars:    SES predictor names to use (defaults to SES_REGRESSION_VARS)
            weight_col:  Survey weight column name
            var_type_a:  Optional override for variable type ('ordinal'/'nominal')
            var_type_b:  Optional override for variable type ('ordinal'/'nominal')

        Returns:
            Dict with cramers_v, p_value, chi_square, degrees_of_freedom,
            n_simulated, method, note; or None on failure.
        """
        if ses_vars is None:
            ses_vars = SES_REGRESSION_VARS

        try:
            # --- Fit models ---
            model_a = SurveyVarModel()
            model_a.fit(df_a, col_a, ses_vars, weight_col)

            model_b = SurveyVarModel()
            model_b.fit(df_b, col_b, ses_vars, weight_col)

            # --- Build reference SES population from real marginals ---
            ses_pop = self._sample_ses_population(df_a, df_b, ses_vars, weight_col)
            if len(ses_pop) < 10:
                return None

            # --- Simulate joint responses ---
            sim_a = model_a.simulate_responses(ses_pop)
            sim_b = model_b.simulate_responses(ses_pop)

            # --- Compute bivariate on simulated joint distribution ---
            crosstab = pd.crosstab(sim_a, sim_b)
            if crosstab.shape[0] < 2 or crosstab.shape[1] < 2:
                return None

            chi2, p_value, dof, _ = stats.chi2_contingency(crosstab)
            cv = float(association(crosstab, method='cramer'))

            # --- Column-normalized conditional distributions ---
            # P(var_a_category | var_b_category) for each var_b category
            col_normed = crosstab.div(crosstab.sum(axis=0), axis=1)

            column_profiles = {}
            for col_cat in col_normed.columns:
                column_profiles[str(col_cat)] = {
                    str(row_cat): round(float(col_normed.loc[row_cat, col_cat]), 3)
                    for row_cat in col_normed.index
                }

            # Key contrasts: which var_a categories vary most across var_b
            top_contrasts = {}
            for row_cat in col_normed.index:
                vals = col_normed.loc[row_cat]
                top_contrasts[str(row_cat)] = {
                    'min_pct': round(float(vals.min()), 3),
                    'max_pct': round(float(vals.max()), 3),
                    'range': round(float(vals.max() - vals.min()), 3),
                    'min_when': str(vals.idxmin()),
                    'max_when': str(vals.idxmax()),
                }
            top_contrasts = dict(sorted(
                top_contrasts.items(), key=lambda x: x[1]['range'], reverse=True
            )[:3])

            return {
                'var_a': var_id_a,
                'var_b': var_id_b,
                'method': 'ses_simulation',
                'n_simulated': len(ses_pop),
                'chi_square': float(chi2),
                'p_value': float(p_value),
                'cramers_v': cv,
                'degrees_of_freedom': int(dof),
                'note': 'Cross-dataset estimate via SES bridge simulation',
                'column_profiles': column_profiles,
                'top_contrasts': top_contrasts,
            }

        except Exception as e:
            print(f"[cross-bivariate] Failed for {var_id_a} × {var_id_b}: {e}")
            return None

    # ------------------------------------------------------------------
    def _sample_ses_population(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        ses_vars: List[str],
        weight_col: str,
    ) -> pd.DataFrame:
        """
        Pool SES rows from both surveys and draw n_sim rows with replacement,
        weighted by Pondi2 (real marginal distribution).
        """
        frames = []
        for df in (df_a, df_b):
            available = [v for v in ses_vars if v in df.columns]
            if not available:
                continue
            cols = available + ([weight_col] if weight_col in df.columns else [])
            sub = df[cols].dropna(subset=available).copy()
            if weight_col not in sub.columns:
                sub[weight_col] = 1.0
            frames.append(sub)

        if not frames:
            return pd.DataFrame()

        pool = pd.concat(frames, ignore_index=True)
        weights = pool[weight_col].astype(float).clip(lower=0)
        total_w = weights.sum()
        if total_w == 0:
            weights = pd.Series(np.ones(len(pool)), index=pool.index)
            total_w = float(len(pool))

        probs = (weights / total_w).values
        rng = np.random.default_rng(seed=42)
        idx = rng.choice(len(pool), size=self.n_sim, replace=True, p=probs)
        sample = pool.iloc[idx][ses_vars].reset_index(drop=True)
        return sample
