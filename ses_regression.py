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

# Survey sentinel codes: values < 0 (invalid/missing) or >= 97 (no-answer, don't-know, refuse)
# These are never substantive responses and must be excluded from model fitting.
# Common examples: 97=not applicable, 98=don't know, 99=no answer, -1=system missing
_SENTINEL_HIGH = 97.0
_SENTINEL_LOW  = 0.0   # exclusive lower bound (0 itself is valid in some scales)


def _is_sentinel(val) -> bool:
    """Return True if val is a survey no-answer / invalid code.

    Catches:
      - Numeric codes >= 97  (97=N/A, 98=don't know, 99=no answer, 999=…)
      - Numeric codes < 0    (-1=system missing, -9=not conducted, etc.)
    Works on floats, ints, and string-coded numerics ('99', '99.0', '-1').
    Returns False for non-numeric strings (categorical labels like '01', 'Norte').
    """
    try:
        f = float(str(val))
        return f < _SENTINEL_LOW or f >= _SENTINEL_HIGH
    except (TypeError, ValueError):
        return False


def _drop_ses_sentinel_rows(df: pd.DataFrame, ses_vars: List[str]) -> pd.DataFrame:
    """Drop rows where any SES predictor column contains a sentinel code.

    This guards the regression models and the SES population sample against
    responses coded as 'no answer' (99), 'don't know' (98), 'not applicable'
    (97), or any negative invalid code — even when those values are stored as
    strings ('99', '99.0') rather than NaN, which would otherwise pass through
    a bare dropna() call.

    Applied to both SurveyVarModel.fit() and _sample_ses_population() so that
    sentinel-coded respondents are excluded from the bridge regression at every
    stage of the pipeline.
    """
    cols = [v for v in ses_vars if v in df.columns]
    if not cols:
        return df
    keep = pd.Series(True, index=df.index)
    for col in cols:
        sentinel_mask = df[col].apply(_is_sentinel)
        keep &= ~sentinel_mask
    result = df[keep].copy()
    # Also drop any remaining NaN in SES columns (e.g. from failed mappings)
    result = result.dropna(subset=cols)
    return result


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
        """Learn category sets from DataFrame (for one-hot vars).

        Sentinel-coded categories (e.g. region='99', empleo='97') are excluded
        so they never appear as dummy columns in the feature matrix.
        """
        if 'region' in df.columns:
            self._region_cats = sorted(
                c for c in df['region'].dropna().unique()
                if not _is_sentinel(c)
            )
        if 'empleo' in df.columns:
            self._empleo_cats = sorted(
                c for c in df['empleo'].dropna().unique()
                if not _is_sentinel(c)
            )
        self._fitted = True
        return self

    # ------------------------------------------------------------------
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return numeric feature DataFrame, one row per input row.

        Sentinel codes that slipped past upstream filtering will map to NaN
        rather than being silently recoded as the base category (the previous
        fillna(0.0) behaviour).  Callers should ensure _drop_ses_sentinel_rows
        has been applied before transform(); any residual NaN here indicates a
        data quality issue and will propagate visibly rather than silently.
        """
        if not self._fitted:
            self.fit(df)

        parts: List[pd.Series] = []

        # sexo — binary
        # Surveys store sexo either as strings ('01','02') or as floats (1.0, 2.0).
        # Normalise to string first so both forms are handled uniformly.
        if 'sexo' in df.columns:
            parts.append(
                df['sexo'].astype(str).str.strip()
                .map({'01': 0, '1': 0, '1.0': 0, '02': 1, '2': 1, '2.0': 1})
                .rename('sexo').astype(float)
            )

        # edad — ordinal int
        # Most surveys store edad as pre-binned strings ('25-34', '45-54', etc.).
        # FAMILIA and a few others store raw numeric ages (15.0, 47.0, …).
        # Detect the format by attempting string-map first; if >50% map to NaN
        # fall back to numeric age binning.
        if 'edad' in df.columns:
            mapped_edad = df['edad'].map(_EDAD_ORDER)
            if mapped_edad.isna().mean() > 0.5:
                # Numeric raw-age fallback: bin into the same ordinal brackets
                numeric_age = pd.to_numeric(df['edad'], errors='coerce')
                mapped_edad = pd.cut(
                    numeric_age,
                    bins=[-1, 18, 24, 34, 44, 54, 64, 999],
                    labels=[0, 1, 2, 3, 4, 5, 6],
                ).astype(float)
            parts.append(mapped_edad.rename('edad').astype(float))

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
        # Do NOT fillna(0.0) here. Residual NaN means an unmapped / sentinel
        # value slipped through; propagate it so the issue is visible and rows
        # with unknown SES codes are excluded from model fitting rather than
        # silently assigned to the base category.
        return X

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

        # Remove sentinel-coded TARGET values (99=no answer, -1=invalid, etc.)
        sentinel_mask = work[target_col].apply(_is_sentinel)
        if sentinel_mask.any():
            work = work[~sentinel_mask]
            if len(work) < 30:
                raise ValueError(
                    f"Too few non-sentinel rows for {target_col}: {len(work)} "
                    f"(dropped {sentinel_mask.sum()} sentinel-coded rows)"
                )

        # Remove sentinel-coded SES PREDICTOR values.
        # Sentinel codes in predictors (e.g. sexo='99', empleo='97') are string-
        # valued and therefore survive dropna(); they would otherwise be silently
        # mapped to the base category by SESEncoder.transform(). Drop them here
        # before the encoder sees the data.
        work = _drop_ses_sentinel_rows(work, available_ses)
        if len(work) < 30:
            raise ValueError(
                f"Too few rows for {target_col} after SES sentinel filtering: {len(work)}"
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

        # Drop any rows where encoding produced NaN (residual unmapped codes)
        valid_rows = X.notna().all(axis=1)
        if not valid_rows.all():
            X = X[valid_rows]
            work = work.loc[X.index]
            if len(work) < 30:
                raise ValueError(
                    f"Too few rows for {target_col} after SES encoding: {len(work)}"
                )

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

            # Belt-and-suspenders: drop any sentinel-coded categories that slipped
            # through (should not happen after the fit() sentinel filter, but guards
            # against edge cases in the simulation).
            substantive_rows = [
                r for r in col_normed.index if not _is_sentinel(r)
            ]
            substantive_cols = [
                c for c in col_normed.columns if not _is_sentinel(c)
            ]
            if len(substantive_rows) < len(col_normed.index) or len(substantive_cols) < len(col_normed.columns):
                col_normed = col_normed.loc[substantive_rows, substantive_cols]
                # Renormalize columns after dropping sentinel rows
                col_sums = col_normed.sum(axis=0).replace(0, 1.0)
                col_normed = col_normed.div(col_sums, axis=1)

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

        Sentinel-coded SES values (e.g. sexo='99', empleo='97') are dropped
        before pooling so they cannot corrupt the reference SES distribution.
        """
        frames = []
        for df in (df_a, df_b):
            available = [v for v in ses_vars if v in df.columns]
            if not available:
                continue
            cols = available + ([weight_col] if weight_col in df.columns else [])
            sub = df[cols].dropna(subset=available).copy()
            # Drop rows where any SES column is sentinel-coded (e.g. '99', '-1')
            sub = _drop_ses_sentinel_rows(sub, available)
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
