"""
SES Regression Module for Navegador — Simulation-Based Cross-Dataset Bivariate Estimation

Uses SES variables (sexo, edad, region, empleo, escol) as bridge variables to estimate
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
  SESEncoder                    — String SES codes → numeric feature matrix
  SurveyVarModel                — Fits and simulates one survey variable
  CrossDatasetBivariateEstimator — Baseline: pooled simulation over shared SES pop
  ResidualBridgeEstimator       — Within-SES-cell V (Mantel-Haenszel style)
  EcologicalBridgeEstimator     — Geographic cell-level Spearman ρ (edo × Tam_loc)
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
_NOMINAL_SES = ('sexo', 'region', 'empleo', 'est_civil')
_ORDINAL_SES = ('edad', 'escol', 'Tam_loc')

# ---------------------------------------------------------------------------
# Human-readable labels for one-hot SES category columns.
# Keys are normalised to int (int(float(code))) to handle both '01' and 1.0.
# Source: survey metadata variable_value_labels across all 26 surveys.
# ---------------------------------------------------------------------------

# Region codes 1-4 (raw Region column) → string code '01'-'04' → label
# Verified from survey metadata: 1=Centro, 2=CDMX/Estado de México, 3=Norte, 4=Sur
_REGION_LABEL_MAP: Dict[int, str] = {
    1: 'Centro',
    2: 'CDMX_Edo',   # D.F. y Estado de México
    3: 'Norte',
    4: 'Sur',
}

# Employment status (sd5 / empleo): 1=Empleado … 5=Jubilado
_EMPLEO_LABEL_MAP: Dict[int, str] = {
    1: 'Empleado',
    2: 'Desempleado',
    3: 'Estudiante',
    4: 'Hogar',
    5: 'Jubilado',
}

# Marital status (est_civil): survey metadata confirmed codes 1, 2, 6 in most surveys
_EST_CIVIL_LABEL_MAP: Dict[int, str] = {
    1: 'CasadoUL',    # Casado / Unión libre
    2: 'SepDivVdo',   # Separado / Divorciado / Viudo
    3: 'UnionLibre',  # Unión libre (some surveys split this from Casado)
    4: 'Separado',
    5: 'Divorciado',
    6: 'Soltero',
    7: 'Otro',
}


def _ses_label(label_map: Dict[int, str], code, fallback: str = '') -> str:
    """Return human-readable label for a SES category code.

    Normalises code to int so both string codes ('01', '1') and float codes
    (1.0) all resolve to the same label.
    """
    try:
        key = int(float(str(code).strip()))
    except (ValueError, TypeError):
        return fallback or str(code)
    return label_map.get(key, fallback or str(code))

# SES variables used in regression features.
# Tam_loc and est_civil are included when present (24/26 and 26/26 surveys resp.).
# Surveys missing Tam_loc (JUEGOS_DE_AZAR, CULTURA_CONSTITUCIONAL) degrade
# gracefully: SESEncoder skips any column absent from the DataFrame.
SES_REGRESSION_VARS: List[str] = [
    'sexo', 'edad', 'region', 'empleo', 'escol', 'Tam_loc', 'est_civil',
    'income_quintile', 'empleo_formality', 'region_x_Tam_loc',
]

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
# Category binning — collapse high-cardinality outcome variables
# ---------------------------------------------------------------------------

def bin_categories(
    series: pd.Series,
    max_categories: int = 5,
    var_type: str = 'nominal',
) -> Tuple[pd.Series, Dict]:
    """Collapse high-cardinality target variables into max_categories bins.

    For ordinal variables: equal-width binning into max_categories groups,
    preserving ordinal order.
    For nominal variables: keep the top (max_categories - 1) most frequent
    categories, merge the rest into a single bin.

    Reduces MNLogit parameter count and avoids near-separation in models
    with many sparse categories (Peduzzi et al. 1996; Agresti 2002 §6.5).

    Args:
        series: Target variable Series (sentinels already removed).
        max_categories: Maximum number of output categories (default 5).
        var_type: 'ordinal' or 'nominal'.

    Returns:
        (binned_series, bin_map) where bin_map maps original → binned values.
        If len(unique) <= max_categories, returns series unchanged with
        identity bin_map.
    """
    unique_vals = sorted(series.dropna().unique().tolist(), key=lambda x: str(x))
    if len(unique_vals) <= max_categories:
        bin_map = {v: v for v in unique_vals}
        return series.copy(), bin_map

    if var_type == 'ordinal':
        # Quantile-based binning: equal-frequency groups so every bin has
        # observations. Equal-width fails for skewed continuous scores
        # (e.g. PCA aggregates scaled to [1,10] with mean~9) because most
        # observations pile into one bin, causing near-separation in
        # OrderedModel and singular Hessians.
        numeric = pd.to_numeric(series, errors='coerce').dropna()
        binned_num = pd.qcut(numeric, q=max_categories, labels=False,
                             duplicates='drop') + 1.0
        bin_map = {}
        for orig_val, bin_val in zip(numeric, binned_num):
            bin_map.setdefault(orig_val, bin_val)
        # Ensure all unique original values get a mapping (qcut may drop dupes)
        remaining = sorted([float(v) for v in unique_vals
                            if float(v) not in bin_map])
        if remaining:
            # Map unmapped values to nearest bin by value
            mapped_keys = sorted(bin_map.keys())
            for rv in remaining:
                closest = min(mapped_keys, key=lambda k: abs(k - rv))
                bin_map[rv] = bin_map[closest]
    else:
        # Nominal: keep most frequent categories, merge the rest
        freq = series.value_counts()
        top_cats = freq.head(max_categories - 1).index.tolist()
        bin_map = {}
        for v in unique_vals:
            if v in top_cats:
                bin_map[v] = v
            else:
                bin_map[v] = float(max_categories)  # "other" bin

    binned = series.map(bin_map)
    return binned, bin_map


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
      escol  — ordinal int (1=Ninguna … 5=Universidad/Posgrado)

    Usage:
      enc = SESEncoder()
      enc.fit(df)          # learns categories from data
      X = enc.transform(df)
    """

    def __init__(self) -> None:
        self._region_cats: List[str] = []
        self._empleo_cats: List[str] = []
        self._est_civil_cats: List = []
        self._region_x_tam_cats: List = []
        self._has_tam_loc: bool = False
        self._has_income_quintile: bool = False
        self._has_empleo_formality: bool = False
        self._has_region_x_tam: bool = False
        self._fitted = False

    # ------------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> 'SESEncoder':
        """Learn category sets from DataFrame (for one-hot vars).

        Sentinel-coded categories (e.g. region='99', empleo='97') are excluded
        so they never appear as dummy columns in the feature matrix.
        """
        if 'region' in df.columns:
            self._region_cats = sorted(
                (c for c in df['region'].dropna().unique() if not _is_sentinel(c)),
                key=str,
            )
        if 'empleo' in df.columns:
            self._empleo_cats = sorted(
                (c for c in df['empleo'].dropna().unique() if not _is_sentinel(c)),
                key=str,
            )
        if 'est_civil' in df.columns:
            # est_civil stores numeric codes (1.0, 2.0, 6.0 etc.) after preprocessing.
            # Sort numerically so the dropped first category is consistently the
            # lowest code across surveys.
            self._est_civil_cats = sorted(
                (c for c in df['est_civil'].dropna().unique() if not _is_sentinel(c)),
                key=str,
            )
        self._has_tam_loc = 'Tam_loc' in df.columns
        self._has_income_quintile = 'income_quintile' in df.columns
        self._has_empleo_formality = 'empleo_formality' in df.columns
        if 'region_x_Tam_loc' in df.columns:
            self._has_region_x_tam = True
            self._region_x_tam_cats = sorted(
                (c for c in df['region_x_Tam_loc'].dropna().unique()
                 if not _is_sentinel(c)),
                key=float,
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

        # region — one-hot (drop first category to avoid multicollinearity).
        # Skip when region_x_Tam_loc is present: the interaction encodes all
        # region × Tam_loc combinations, making region and Tam_loc marginals
        # exact linear combinations of the interaction dummies → rank deficiency.
        if ('region' in df.columns and len(self._region_cats) > 1
                and not self._has_region_x_tam):
            for cat in self._region_cats[1:]:           # drop first
                label = _ses_label(_REGION_LABEL_MAP, cat)
                parts.append(
                    (df['region'] == cat).astype(float).rename(f'region_{label}')
                )

        # empleo — one-hot (drop first category)
        if 'empleo' in df.columns and len(self._empleo_cats) > 1:
            for cat in self._empleo_cats[1:]:           # drop first
                label = _ses_label(_EMPLEO_LABEL_MAP, cat)
                parts.append(
                    (df['empleo'] == cat).astype(float).rename(f'empleo_{label}')
                )

        # escol — ordinal int (education grade, 1=Ninguna … 5=Universidad/Posgrado)
        # Already stored as numeric float in all surveys; sentinel rows are removed
        # upstream by _drop_ses_sentinel_rows before transform() is called.
        if 'escol' in df.columns:
            parts.append(
                pd.to_numeric(df['escol'], errors='coerce').rename('escol')
            )

        # Tam_loc — ordinal int (locality size: 1=≥100k urban → 4=rural).
        # Present in 24/26 surveys; absent in JUEGOS_DE_AZAR and CULTURA_CONSTITUCIONAL.
        # Skip when region_x_Tam_loc is present (same collinearity reason as region).
        if 'Tam_loc' in df.columns and not self._has_region_x_tam:
            parts.append(
                pd.to_numeric(df['Tam_loc'], errors='coerce').rename('Tam_loc')
            )

        # est_civil — nominal one-hot (marital status, drop first category).
        # Sentinel codes 8/9/98/99 are remapped to NaN by preprocess_survey_data();
        # any residual sentinels will produce NaN after pd.to_numeric and be excluded.
        if 'est_civil' in df.columns and len(self._est_civil_cats) > 1:
            est_civil_num = pd.to_numeric(df['est_civil'], errors='coerce')
            for cat in self._est_civil_cats[1:]:
                label = _ses_label(_EST_CIVIL_LABEL_MAP, cat)
                parts.append(
                    (est_civil_num == cat).astype(float).rename(f'est_civil_{label}')
                )

        # income_quintile — ordinal 1–5 (sd14: personal income bin).
        # Available in ~23/26 surveys. Stronger SES signal than escol alone.
        if 'income_quintile' in df.columns:
            parts.append(
                pd.to_numeric(df['income_quintile'], errors='coerce')
                .rename('income_quintile')
            )

        # empleo_formality — ordinal 1–4 (sd11: employment formality).
        # 1=formal salaried, 2=self-employed, 3=informal, 4=unpaid/other.
        if 'empleo_formality' in df.columns:
            parts.append(
                pd.to_numeric(df['empleo_formality'], errors='coerce')
                .rename('empleo_formality')
            )

        # region_x_Tam_loc — local fixed effects (one-hot, drop first).
        # 16 cells: 4 regions × 4 locality sizes. Captures geographic-structural
        # confounding invisible to individual-level SES variables.
        if ('region_x_Tam_loc' in df.columns
                and len(self._region_x_tam_cats) > 1):
            rtl_num = pd.to_numeric(df['region_x_Tam_loc'], errors='coerce')
            for cat in self._region_x_tam_cats[1:]:
                parts.append(
                    (rtl_num == cat).astype(float)
                    .rename(f'rtl_{int(cat)}')
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
            names.extend(f'region_{_ses_label(_REGION_LABEL_MAP, c)}'
                         for c in self._region_cats[1:])
        if len(self._empleo_cats) > 1:
            names.extend(f'empleo_{_ses_label(_EMPLEO_LABEL_MAP, c)}'
                         for c in self._empleo_cats[1:])
        names.append('escol')
        if self._has_tam_loc:
            names.append('Tam_loc')
        if len(self._est_civil_cats) > 1:
            names.extend(f'est_civil_{_ses_label(_EST_CIVIL_LABEL_MAP, c)}'
                         for c in self._est_civil_cats[1:])
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
      model.fit(df, target_col='p1', ses_vars=['sexo','edad','region','empleo','escol'])
      probs = model.predict_proba(ses_feature_df)   # shape (n, n_categories)
      responses = model.simulate_responses(ses_pop_df)
    """

    def __init__(self) -> None:
        self._model_result = None
        self._categories: List[str] = []
        self._encoder: Optional[SESEncoder] = None
        self._var_type: str = 'nominal'
        self._target_col: str = ''
        self._bin_map: Optional[Dict] = None

    # ------------------------------------------------------------------
    def fit(
        self,
        df: pd.DataFrame,
        target_col: str,
        ses_vars: List[str],
        weight_col: str = 'Pondi2',
        max_categories: Optional[int] = 5,
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

        # Category binning: collapse high-cardinality targets to improve
        # model conditioning (Peduzzi et al. 1996 EPV rule)
        if max_categories is not None and len(self._categories) > max_categories:
            binned_col, self._bin_map = bin_categories(
                work[target_col], max_categories=max_categories,
                var_type=self._var_type,
            )
            work = work.copy()
            work[target_col] = binned_col
            self._categories = sorted(
                work[target_col].dropna().unique().tolist(),
                key=lambda x: str(x),
            )

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
    def diagnostics(self) -> Dict[str, Any]:
        """
        Return regression diagnostics for the fitted model.

        Exposes per-coefficient statistics (coef, std_err, t-stat, p-value),
        McFadden pseudo-R², and the likelihood-ratio test p-value for overall
        model fit. Works for both OrderedModel and MNLogit results.

        The ``top_predictor`` field names the single feature with the highest
        |t-stat| — i.e. the SES variable doing the most work in the bridge.
        ``dominant_ses_group`` maps that feature back to the root SES variable
        (e.g. ``'empleo_03'`` → ``'empleo'``).

        Returns:
            dict with:
              'model_type'       : 'ordered' or 'mnlogit'
              'n_categories'     : number of outcome categories
              'pseudo_r2'        : McFadden's pseudo-R² ∈ [0, 1] (nan if unavailable)
              'llr_pvalue'       : LR-test p-value vs null model (nan if unavailable)
              'coef_table'       : list of dicts sorted by |t_stat| descending,
                                   each with keys:
                                     feature, coef, std_err, t_stat, p_value, abs_t
              'top_predictor'    : feature name with highest |t_stat|
              'dominant_ses_group': root SES variable for top_predictor

        Raises:
            RuntimeError: if the model has not been fitted yet.
        """
        if self._model_result is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        result = self._model_result
        n_cats = len(self._categories)
        model_type = 'ordered' if (self._var_type == 'ordinal' and n_cats > 2) else 'mnlogit'

        # --- Pseudo R² (McFadden's) ---
        try:
            pseudo_r2 = float(result.prsquared)
            pseudo_r2 = max(0.0, min(1.0, pseudo_r2))
        except Exception:
            pseudo_r2 = float('nan')

        # --- Likelihood-ratio test p-value ---
        try:
            llr_pvalue = float(result.llr_pvalue)
        except Exception:
            llr_pvalue = float('nan')

        # --- Per-coefficient table ---
        rows: List[Dict[str, Any]] = []
        try:
            params  = result.params
            tvals   = result.tvalues
            pvals   = result.pvalues
            bse     = result.bse

            if model_type == 'mnlogit':
                # params / tvals are DataFrames: index=feature_names, columns=class_indices
                # Summarise each feature by taking the class with the highest |t|.
                if hasattr(params, 'index'):
                    feature_names = [n for n in params.index if n != 'const']
                else:
                    feature_names = self._encoder.feature_names if self._encoder else []

                for feat in feature_names:
                    if feat not in params.index:
                        continue
                    t_vec  = np.asarray(tvals.loc[feat], dtype=float)
                    p_vec  = np.asarray(pvals.loc[feat], dtype=float)
                    c_vec  = np.asarray(params.loc[feat], dtype=float)
                    se_vec = np.asarray(bse.loc[feat], dtype=float)
                    best   = int(np.nanargmax(np.abs(t_vec)))
                    rows.append({
                        'feature' : feat,
                        'coef'    : float(np.nanmean(c_vec)),
                        'std_err' : float(np.nanmean(se_vec)),
                        't_stat'  : float(t_vec[best]),
                        'p_value' : float(p_vec[best]),
                        'abs_t'   : float(np.nanmax(np.abs(t_vec))),
                    })

            else:  # ordered logit — params is a Series
                # Last (n_cats - 1) params are threshold intercepts; their index
                # labels contain '/' (e.g. '0/1', '1/2').  Everything else is a
                # predictor coefficient.
                all_idx = list(params.index)
                feature_labels = [l for l in all_idx if '/' not in str(l)]
                for feat in feature_labels:
                    rows.append({
                        'feature' : str(feat),
                        'coef'    : float(params[feat]),
                        'std_err' : float(bse[feat]),
                        't_stat'  : float(tvals[feat]),
                        'p_value' : float(pvals[feat]),
                        'abs_t'   : float(abs(tvals[feat])),
                    })

        except Exception:
            rows = []

        # Sort by |t_stat| descending so callers see dominant predictors first
        rows.sort(key=lambda r: r['abs_t'], reverse=True)

        top_predictor = rows[0]['feature'] if rows else None

        def _ses_group(feat_name: str) -> Optional[str]:
            """Map encoded feature name back to root SES variable."""
            for ses_var in SES_REGRESSION_VARS:
                if feat_name == ses_var or feat_name.startswith(ses_var + '_'):
                    return ses_var
            return feat_name

        dominant_ses_group = _ses_group(top_predictor) if top_predictor else None

        # --- AIC / BIC (available on both MNLogit and OrderedModel results) ---
        try:
            aic = float(result.aic)
        except Exception:
            aic = float('nan')
        try:
            bic = float(result.bic)
        except Exception:
            bic = float('nan')

        return {
            'model_type'        : model_type,
            'n_categories'      : n_cats,
            'pseudo_r2'         : pseudo_r2,
            'llr_pvalue'        : llr_pvalue,
            'aic'               : aic,
            'bic'               : bic,
            'coef_table'        : rows,
            'top_predictor'     : top_predictor,
            'dominant_ses_group': dominant_ses_group,
        }

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
    def held_out_accuracy(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict[str, float]:
        """Compute held-out prediction accuracy metrics.

        Args:
            X_test: Encoded SES feature matrix (from SESEncoder.transform)
            y_test: True category labels for test set

        Returns:
            dict with accuracy, log_loss, mse, mae
        """
        if self._model_result is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        probs_df = self.predict_proba(X_test)

        # Modal prediction accuracy
        modal = probs_df.idxmax(axis=1)
        # Normalise types for comparison
        try:
            modal_f = modal.astype(float)
            y_f = y_test.astype(float)
            accuracy = float((modal_f == y_f).mean())
        except (ValueError, TypeError):
            accuracy = float((modal.astype(str) == y_test.astype(str)).mean())

        # Per-observation probability of true class
        p_true = np.array([
            float(probs_df.at[idx, val])
            if val in probs_df.columns
            else 1.0 / len(self._categories)
            for idx, val in y_test.items()
        ])
        p_true = np.clip(p_true, 1e-10, 1.0)

        log_loss = float(-np.log(p_true).mean())
        mse = float(((1.0 - p_true) ** 2).mean())
        mae = float((1.0 - p_true).mean())

        return {
            'accuracy': round(accuracy, 4),
            'log_loss': round(log_loss, 4),
            'mse': round(mse, 4),
            'mae': round(mae, 4),
        }

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

        # Normalise response values to a single comparable type so that
        # pd.crosstab can sort the index without a "<" str-vs-float error.
        # (Columns from object-dtype survey vars can be a mix of str and float.)
        out = pd.Series(responses, index=ses_population_df.index, name=self._target_col)
        try:
            out = out.astype(float)
        except (ValueError, TypeError):
            out = out.astype(str)
        return out


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

    def __init__(self, n_sim: int = 2000, max_categories: Optional[int] = 5) -> None:
        self.n_sim = n_sim
        self.max_categories = max_categories

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
            model_a.fit(df_a, col_a, ses_vars, weight_col,
                        max_categories=self.max_categories)

            model_b = SurveyVarModel()
            model_b.fit(df_b, col_b, ses_vars, weight_col,
                        max_categories=self.max_categories)

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

            # --- Bridge model diagnostics (for human inspection, not passed to LLM) ---
            diag_a: Optional[Dict[str, Any]] = None
            diag_b: Optional[Dict[str, Any]] = None
            try:
                diag_a = model_a.diagnostics()
            except Exception:
                pass
            try:
                diag_b = model_b.diagnostics()
            except Exception:
                pass

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
                'model_a_diagnostics': diag_a,
                'model_b_diagnostics': diag_b,
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
        available_in_pool = [v for v in ses_vars if v in pool.columns]
        sample = pool.iloc[idx][available_in_pool].reset_index(drop=True)
        return sample


# ---------------------------------------------------------------------------
# Shared helper: rank-encode a categorical Series for ecological aggregation
# ---------------------------------------------------------------------------

def _rank_encode_col(series: pd.Series) -> pd.Series:
    """Map category values to ordinal ranks (1, 2, 3, …) sorted by str().

    Used by EcologicalBridgeEstimator to convert categorical survey responses
    into a numeric scale suitable for computing weighted cell means.
    """
    cats = sorted(series.dropna().unique(), key=str)
    rank_map = {c: float(i + 1) for i, c in enumerate(cats)}
    return series.map(rank_map)


# ---------------------------------------------------------------------------
# ResidualBridgeEstimator
# ---------------------------------------------------------------------------

class ResidualBridgeEstimator:
    """
    Mantel-Haenszel Residual Bridge: within-SES-cell Cramér's V.

    The baseline CrossDatasetBivariateEstimator pools all simulated respondents
    together, so any two SES-correlated variables appear associated even when
    there is no conceptual link.  This estimator removes that confound by:

      1. Fitting the same two SES models as the baseline.
      2. Sampling the same reference SES population.
      3. Discretizing the SES population into K cells (KMeans on encoded features).
      4. Simulating var_a and var_b *within* each cell independently.
      5. Computing Cramér's V within each cell and returning a cell-size-weighted mean.

    Result interpretation:
      V_residual ≈ V_baseline → association is NOT demographically mediated.
      V_residual << V_baseline → association is mostly SES confounding.
      ses_fraction = V_residual / V_baseline (ratio of residual to baseline).

    Output dict keys:
      cramers_v_residual  — weighted-mean within-SES-cell V
      cramers_v_baseline  — baseline V over full SES pop (same run, for comparison)
      ses_fraction        — cramers_v_residual / cramers_v_baseline
      n_cells_used        — number of cells with ≥ min_cell_size respondents
      n_simulated         — total respondents across valid cells
      method              — 'ses_residual_bridge'
    """

    def __init__(self, n_sim: int = 2000, n_cells: int = 30,
                 min_cell_size: int = 5,
                 max_categories: Optional[int] = 5) -> None:
        self.n_sim = n_sim
        self.n_cells = n_cells
        self.min_cell_size = min_cell_size
        self.max_categories = max_categories

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
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate within-SES-cell association between col_a (df_a) and col_b (df_b).

        Returns a dict or None on failure.
        """
        if ses_vars is None:
            ses_vars = SES_REGRESSION_VARS

        if col_a not in df_a.columns or col_b not in df_b.columns:
            return None

        try:
            from scipy.cluster.vq import kmeans2, whiten

            # --- Fit SES models (identical to baseline estimator) ---
            model_a = SurveyVarModel()
            model_a.fit(df_a, col_a, ses_vars, weight_col,
                        max_categories=self.max_categories)

            model_b = SurveyVarModel()
            model_b.fit(df_b, col_b, ses_vars, weight_col,
                        max_categories=self.max_categories)

            # --- Sample reference SES population ---
            _helper = CrossDatasetBivariateEstimator(n_sim=self.n_sim)
            ses_pop = _helper._sample_ses_population(df_a, df_b, ses_vars, weight_col)
            if len(ses_pop) < max(10, self.min_cell_size * 2):
                return None

            # --- Encode SES pop for clustering (fresh encoder, col-mean imputation) ---
            cluster_enc = SESEncoder()
            X_enc = cluster_enc.fit_transform(ses_pop)
            X_arr = X_enc.fillna(X_enc.mean()).values.astype(float)

            # Whiten (standardise columns) for stable KMeans; replace zero-std cols
            col_stds = X_arr.std(axis=0)
            col_stds[col_stds == 0] = 1.0
            X_white = X_arr / col_stds

            # Clamp K so each cell can have >= min_cell_size rows on average
            k = min(self.n_cells, len(ses_pop) // max(self.min_cell_size, 1))
            if k < 2:
                return None

            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                _, cell_labels = kmeans2(X_white, k, minit='points', seed=42)

            # --- Per-cell bias-corrected V + CMH-style stratified gamma ---
            # Uses Bergsma (2013) bias-corrected V instead of classical V,
            # and pools concordance/discordance counts across cells (Mantel &
            # Haenszel 1959; Cochran 1954) for a proper stratified gamma.
            cell_vs: List[float] = []
            cell_ns: List[int] = []
            total_concordant = 0.0
            total_discordant = 0.0
            for cell_k in range(k):
                mask = cell_labels == cell_k
                ses_cell = ses_pop[mask].reset_index(drop=True)
                if len(ses_cell) < self.min_cell_size:
                    continue
                sim_a = model_a.simulate_responses(ses_cell)
                sim_b = model_b.simulate_responses(ses_cell)
                ct = pd.crosstab(sim_a, sim_b)
                if ct.shape[0] < 2 or ct.shape[1] < 2:
                    continue
                ct_arr = ct.values.astype(float)
                # Bias-corrected Cramér's V per cell (Bergsma 2013)
                v_k = bias_corrected_cramers_v(ct_arr)
                cell_vs.append(v_k)
                cell_ns.append(len(ses_cell))
                # Pool concordance/discordance for CMH stratified gamma
                for i in range(ct_arr.shape[0]):
                    for j in range(ct_arr.shape[1]):
                        total_concordant += ct_arr[i, j] * ct_arr[i + 1:, j + 1:].sum()
                        total_discordant += ct_arr[i, j] * ct_arr[i + 1:, :j].sum()

            n_cells_used = len(cell_vs)
            if n_cells_used == 0:
                return None

            total_n = sum(cell_ns)
            v_residual = sum(v * n / total_n for v, n in zip(cell_vs, cell_ns))

            # Stratified gamma (CMH-style pooled concordance/discordance)
            cd_denom = total_concordant + total_discordant
            stratified_gamma = (
                float((total_concordant - total_discordant) / cd_denom)
                if cd_denom > 0 else 0.0
            )

            # Baseline V over full SES pop (same models, same pop — for ses_fraction)
            sim_a_full = model_a.simulate_responses(ses_pop)
            sim_b_full = model_b.simulate_responses(ses_pop)
            ct_full = pd.crosstab(sim_a_full, sim_b_full)
            v_baseline = (
                float(association(ct_full, method='cramer'))
                if ct_full.shape[0] >= 2 and ct_full.shape[1] >= 2
                else float('nan')
            )
            ses_fraction = (
                round(v_residual / v_baseline, 4)
                if v_baseline > 0 and not np.isnan(v_baseline)
                else None
            )

            return {
                'var_a': var_id_a,
                'var_b': var_id_b,
                'method': 'ses_residual_bridge',
                'cramers_v_residual': round(v_residual, 4),
                'cramers_v_baseline': round(v_baseline, 4),
                'ses_fraction': ses_fraction,
                'stratified_gamma': round(stratified_gamma, 4),
                'n_cells_used': n_cells_used,
                'n_simulated': total_n,
                'note': (
                    'Within-SES-cell V (Bergsma 2013 bias-corrected) '
                    'with CMH stratified gamma'
                ),
            }

        except Exception as e:
            print(f"[residual-bridge] Failed for {var_id_a} × {var_id_b}: {e}")
            return None


# ---------------------------------------------------------------------------
# EcologicalBridgeEstimator
# ---------------------------------------------------------------------------

class EcologicalBridgeEstimator:
    """
    Ecological Bridge: cell-level Spearman correlation across shared strata.

    Aggregates each variable within cells defined by one or more shared columns
    (``cell_cols``), merges both surveys on the cell key, and computes weighted
    Spearman ρ with a bootstrap 95% CI.

    The default ``cell_cols=['edo', 'Tam_loc']`` uses geography (up to 128 cells),
    but any columns present in both surveys work.  Recommended alternatives:

      ['escol', 'edad']      — 5×7=35 demographic cells; education and age often
                               explain opinion better than geography, and cells are
                               denser (~57 rows each at n=2000).
      ['region', 'edad']     — 4×7=28 cells; larger but still demographic.
      ['region', 'escol']    — 4×5=20 cells; education within macro-region.

    Columns absent from either survey are silently dropped from the key; if no
    requested column is present in both surveys the method returns None.

    Unlike the SES-bridge simulation this method uses *real* aggregate data
    and is not subject to the compression problem.  It IS subject to the
    ecological fallacy: cell-level correlations can diverge from individual-
    level ones.

    Output dict keys:
      spearman_rho   — weighted Spearman ρ across merged cells
      p_value        — p-value from scipy.stats.spearmanr
      ci_95          — (lower, upper) bootstrap 95% CI
      n_cells        — number of overlapping cells with ≥ min_cell_n in both surveys
      cell_cols_used — list of columns actually used for the cell key
      method         — 'ecological_bridge'
    """

    def __init__(
        self,
        min_cell_n: int = 20,
        min_merged_cells: int = 30,
        n_bootstrap: int = 500,
    ) -> None:
        self.min_cell_n = min_cell_n
        self.min_merged_cells = min_merged_cells
        self.n_bootstrap = n_bootstrap

    # ------------------------------------------------------------------
    def estimate(
        self,
        var_id_a: str,
        var_id_b: str,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        col_a: str,
        col_b: str,
        cell_cols: Optional[List[str]] = None,
        weight_col: str = 'Pondi2',
        ses_vars: Optional[List[str]] = None,  # unused; kept for API parity
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate cell-level correlation between col_a (df_a) and col_b (df_b).

        Args:
            cell_cols: Columns used to define cells (default ['edo', 'Tam_loc']).
                       Any mix of geographic, demographic, or SES columns.
                       Columns absent from either survey are silently dropped.

        Returns a dict or None when coverage is insufficient.
        """
        if cell_cols is None:
            cell_cols = ['edo', 'Tam_loc']

        if col_a not in df_a.columns or col_b not in df_b.columns:
            return None

        # Keep only columns present in both surveys AND with low enough cardinality.
        # Columns like 'edad' may be raw ages (70+ unique values) in some surveys but
        # binned groups ('19-24', etc.) in others — their cell keys never overlap.
        # Skip any col where EITHER survey has more than max_cardinality unique values.
        _MAX_CARDINALITY = 20
        available_cols = [
            c for c in cell_cols
            if c in df_a.columns and c in df_b.columns
            and df_a[c].dropna().nunique() <= _MAX_CARDINALITY
            and df_b[c].dropna().nunique() <= _MAX_CARDINALITY
        ]
        if not available_cols:
            return None

        try:
            # --- Build composite cell key from available columns ---
            def _cell_key(df: pd.DataFrame) -> pd.Series:
                parts = [df[c].astype(str).str.strip() for c in available_cols]
                if len(parts) == 1:
                    return parts[0]
                return parts[0].str.cat(parts[1:], sep='_')

            # --- Rank-encode target variables ---
            enc_a = _rank_encode_col(df_a[col_a])
            enc_b = _rank_encode_col(df_b[col_b])

            # --- Weighted cell aggregation ---
            def _cell_agg(
                df: pd.DataFrame,
                encoded: pd.Series,
                cell_keys: pd.Series,
                wt: str,
            ) -> Tuple[pd.Series, pd.Series]:
                weights = df[wt].astype(float) if wt in df.columns else pd.Series(1.0, index=df.index)
                work = pd.DataFrame({
                    'cell': cell_keys,
                    'val': encoded,
                    'w': weights,
                }).dropna()
                sizes = work.groupby('cell').size()
                valid = sizes[sizes >= self.min_cell_n].index
                work = work[work['cell'].isin(valid)]
                agg = work.groupby('cell').apply(
                    lambda g: (g['val'] * g['w']).sum() / g['w'].sum()
                )
                return agg, work.groupby('cell').size()

            keys_a = _cell_key(df_a)
            keys_b = _cell_key(df_b)
            agg_a, sz_a = _cell_agg(df_a, enc_a, keys_a, weight_col)
            agg_b, sz_b = _cell_agg(df_b, enc_b, keys_b, weight_col)

            # --- Inner join on cell key ---
            merged = pd.DataFrame({'agg_a': agg_a, 'agg_b': agg_b}).dropna()
            if len(merged) < self.min_merged_cells:
                return None

            # Cell weight = geometric mean of cell sizes in both surveys
            merged['w'] = np.sqrt(
                sz_a.reindex(merged.index).fillna(1).values *
                sz_b.reindex(merged.index).fillna(1).values
            )

            # --- Weighted Spearman ρ ---
            # Use scipy; repeat rows by integer weight for a weighted approximation
            int_weights = (merged['w'] / merged['w'].min()).round().clip(1, 20).astype(int)
            expanded_a = merged['agg_a'].repeat(int_weights).values
            expanded_b = merged['agg_b'].repeat(int_weights).values
            rho, p_val = stats.spearmanr(expanded_a, expanded_b)

            # --- Bootstrap 95% CI (resample cells) ---
            rng = np.random.default_rng(seed=42)
            n = len(merged)
            boot_rhos: List[float] = []
            for _ in range(self.n_bootstrap):
                idx = rng.integers(0, n, size=n)
                s = merged.iloc[idx]
                iw = int_weights.iloc[idx]
                ea = s['agg_a'].repeat(iw.values).values
                eb = s['agg_b'].repeat(iw.values).values
                if len(ea) < 4:
                    continue
                r, _ = stats.spearmanr(ea, eb)
                if not np.isnan(r):
                    boot_rhos.append(r)

            ci_95: Tuple[float, float] = (
                (round(float(np.percentile(boot_rhos, 2.5)), 4),
                 round(float(np.percentile(boot_rhos, 97.5)), 4))
                if boot_rhos
                else (float('nan'), float('nan'))
            )

            cell_desc = ' × '.join(available_cols)
            return {
                'var_a': var_id_a,
                'var_b': var_id_b,
                'method': 'ecological_bridge',
                'spearman_rho': round(float(rho), 4),
                'p_value': round(float(p_val), 4),
                'ci_95': ci_95,
                'n_cells': len(merged),
                'cell_cols_used': available_cols,
                'note': f'Cell-level correlation ({cell_desc})',
            }

        except Exception as e:
            print(f"[ecological-bridge] Failed for {var_id_a} × {var_id_b}: {e}")
            return None


# ---------------------------------------------------------------------------
# Goodman-Kruskal gamma (ordinal association measure)
# ---------------------------------------------------------------------------

def goodman_kruskal_gamma(joint_table: np.ndarray) -> float:
    """Compute Goodman-Kruskal γ from a K_a × K_b joint probability table.

    γ = (C - D) / (C + D) where C = concordant pairs, D = discordant pairs.
    γ ∈ [-1, 1]: +1 = perfect positive ordinal association, 0 = independence.
    Appropriate for ordinal × ordinal tables (v3 §2.2).
    """
    K_a, K_b = joint_table.shape
    concordant = discordant = 0.0
    for i in range(K_a):
        for j in range(K_b):
            p_ij = joint_table[i, j]
            concordant += p_ij * joint_table[i + 1:, j + 1:].sum()
            discordant += p_ij * joint_table[i + 1:, :j].sum()
    denom = concordant + discordant
    return float((concordant - discordant) / denom) if denom > 0 else 0.0


def bias_corrected_cramers_v(contingency_table: np.ndarray) -> float:
    """Bergsma (2013) bias-corrected Cramér's V.

    Removes the first-order upward bias of classical V in small tables.
    Formula:
        phi2_c = max(0, chi2/n - (r-1)(c-1)/(n-1))
        r_c = r - (r-1)^2/(n-1)
        c_c = c - (c-1)^2/(n-1)
        V_c = sqrt(phi2_c / (min(r_c, c_c) - 1))

    Reference: Bergsma, W. (2013). "A bias-correction for Cramér's V and
    Tschuprow's T." Journal of the Korean Statistical Society 42(3):323-328.
    DOI: 10.1016/j.jkss.2012.10.002
    """
    n = contingency_table.sum()
    if n <= 1:
        return 0.0
    r, c = contingency_table.shape
    if r < 2 or c < 2:
        return 0.0
    chi2 = stats.chi2_contingency(contingency_table, correction=False)[0]
    phi2_corrected = max(0.0, chi2 / n - (r - 1) * (c - 1) / (n - 1))
    r_corrected = r - (r - 1) ** 2 / (n - 1)
    c_corrected = c - (c - 1) ** 2 / (n - 1)
    denom = min(r_corrected, c_corrected) - 1
    if denom <= 0:
        return 0.0
    return float(np.sqrt(phi2_corrected / denom))


# ---------------------------------------------------------------------------
# BayesianBridgeEstimator
# ---------------------------------------------------------------------------

class BayesianBridgeEstimator:
    """
    Bayesian bridge: Laplace-approximate posterior over the joint table.

    Uses the fitted statsmodels OrderedModel/MNLogit covariance matrix as a
    Gaussian approximation to the posterior.  Draws M coefficient samples,
    propagates each through the CIA joint-table formula, and reports the
    posterior distribution of Goodman-Kruskal γ and Cramér's V.

    This addresses v3 §1.3 (estimation uncertainty) and §4.3 (Bayesian PO):
    the credible interval reflects parameter uncertainty, unlike the baseline's
    single-point chi-square p-value.

    Output dict keys:
      gamma            — posterior mean Goodman-Kruskal γ
      gamma_ci_95      — (lower, upper) 95% credible interval
      cramers_v        — posterior mean Cramér's V (for backward compat)
      cramers_v_ci_95  — 95% CI for V
      joint_table      — posterior mean K_a × K_b joint probability table
      pseudo_r2_a      — McFadden pseudo-R² for variable A model
      pseudo_r2_b      — McFadden pseudo-R² for variable B model
      method           — 'bayesian_bridge'
    """

    def __init__(self, n_sim: int = 2000, n_draws: int = 200,
                 max_categories: Optional[int] = 5) -> None:
        self.n_sim = n_sim
        self.n_draws = n_draws
        self.max_categories = max_categories

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
    ) -> Optional[Dict[str, Any]]:
        if ses_vars is None:
            ses_vars = SES_REGRESSION_VARS
        if col_a not in df_a.columns or col_b not in df_b.columns:
            return None

        try:
            import statsmodels.api as sm

            # Restrict to SES vars present in BOTH surveys so that models and the
            # reference SES population share the exact same feature space.
            available_ses = [v for v in ses_vars
                             if v in df_a.columns and v in df_b.columns]
            if len(available_ses) < 2:
                return None

            # --- Fit models (shared SES features only) ---
            model_a = SurveyVarModel()
            model_a.fit(df_a, col_a, available_ses, weight_col,
                        max_categories=self.max_categories)
            model_b = SurveyVarModel()
            model_b.fit(df_b, col_b, available_ses, weight_col,
                        max_categories=self.max_categories)

            # --- Reference SES population ---
            helper = CrossDatasetBivariateEstimator(n_sim=self.n_sim)
            ses_pop = helper._sample_ses_population(df_a, df_b, available_ses, weight_col)
            if len(ses_pop) < 30:
                return None

            # --- Extract MLE params + covariance for each model ---
            def _draw_proba(model: SurveyVarModel, ses_pop_raw: pd.DataFrame,
                            avail: List[str], rng: np.random.Generator) -> np.ndarray:
                """Draw one posterior sample of P(Y|X) via Laplace approximation.

                Uses the model's own encoder to transform ses_pop_raw, guaranteeing
                that the feature column count exactly matches the model's params.

                MNLogit:    params is (n_feat+1, K-1); cov_params() is (p, p)
                OrderedModel: params is a 1D Series (n_feat + K-1 thresholds);
                              threshold entries have '/' in their index label.
                """
                from scipy.special import expit
                res = model._model_result
                K = len(model._categories)

                is_mnlogit = not (model._var_type == 'ordinal' and K > 2)

                if is_mnlogit:
                    # MNLogit params DataFrame is (n_feat+1, K-1), but
                    # cov_params() is ordered alternative-first:
                    #   [(alt1,const), (alt1,x1), ..., (alt2,const), ...].
                    # Ravel with Fortran (column-major) order to match cov.
                    params_mle = np.asarray(res.params, dtype=float).ravel(order='F')
                else:
                    # OrderedModel: params is 1-D Series, ordering matches cov.
                    params_mle = np.asarray(res.params, dtype=float).ravel()

                try:
                    cov = np.asarray(res.cov_params(), dtype=float)
                    # Guard: use diagonal if cov is not PSD (numerical issues)
                    cov = np.nan_to_num(cov, nan=0.0)
                    cov = (cov + cov.T) / 2.0
                    min_eig = np.linalg.eigvalsh(cov).min()
                    if min_eig < 0:
                        cov += (-min_eig + 1e-6) * np.eye(len(params_mle))

                    # Ledoit-Wolf-style diagonal shrinkage to regularise
                    # ill-conditioned Hessians from near-separation.
                    # Tierney & Kadane (1986): Laplace requires well-conditioned
                    # Hessian; Mansournia et al. (2018): penalized likelihood.
                    alpha = 0.1
                    diag_vals = np.diag(cov)
                    target = np.median(diag_vals[diag_vals > 0]) if (diag_vals > 0).any() else 1.0
                    cov = (1 - alpha) * cov + alpha * target * np.eye(len(params_mle))

                    # Cap extreme BSEs: scale down rows/cols where sqrt(diag) > 10
                    bse_cap = 10.0
                    bse_draw = np.sqrt(np.diag(cov))
                    scale_mask = bse_draw > bse_cap
                    if scale_mask.any():
                        scale = np.ones(len(params_mle))
                        scale[scale_mask] = bse_cap / bse_draw[scale_mask]
                        cov = cov * np.outer(scale, scale)
                except Exception:
                    try:
                        cov = np.diag(np.asarray(res.bse, dtype=float).ravel() ** 2)
                    except Exception:
                        # bse also calls cov_params() internally; fall back to
                        # a small isotropic covariance so draws stay near MLE.
                        p = len(params_mle)
                        cov = np.eye(p) * 0.01

                params_draw = rng.multivariate_normal(params_mle, cov)
                # Re-encode using model's own encoder so columns match params exactly.
                X_encoded = model._encoder.transform(ses_pop_raw[avail]).fillna(0.0)
                X_arr = np.array(X_encoded, dtype=float)

                if not is_mnlogit:
                    # OrderedModel: betas + thresholds. Threshold indices have '/'.
                    idx = res.params.index if hasattr(res.params, 'index') else []
                    thresh_mask = np.array([('/' in str(i)) for i in idx])
                    if thresh_mask.any():
                        betas = params_draw[~thresh_mask]
                        thresholds = np.sort(params_draw[thresh_mask])
                    else:
                        # Fallback: last K-1 entries are thresholds
                        betas = params_draw[:-(K - 1)]
                        thresholds = np.sort(params_draw[-(K - 1):])

                    eta = X_arr @ betas  # (n,)
                    probs = np.zeros((len(X_arr), K))
                    for k in range(K):
                        if k == 0:
                            probs[:, k] = expit(thresholds[0] - eta)
                        elif k == K - 1:
                            probs[:, k] = 1.0 - expit(thresholds[-1] - eta)
                        else:
                            probs[:, k] = (expit(thresholds[k] - eta)
                                           - expit(thresholds[k - 1] - eta))
                else:
                    # MNLogit: params drawn in alternative-first order.
                    # Reshape back to (n_feat+1, K-1) using column-major order
                    # so each column holds one alternative's coefficients.
                    n_rows = np.asarray(res.params, dtype=float).shape[0]
                    n_cols = K - 1
                    params_2d = params_draw.reshape(n_rows, n_cols, order='F')
                    Xc = np.column_stack([np.ones(len(X_arr)), X_arr])
                    eta = Xc @ params_2d  # (n, K-1) for non-reference categories
                    # Softmax: reference class (first category) has eta=0.
                    # Prepend ref eta so the max subtraction is consistent
                    # across ALL K alternatives (avoids inflating the ref).
                    eta_all = np.hstack([np.zeros((len(Xc), 1)), eta])
                    max_eta = eta_all.max(axis=1, keepdims=True)
                    probs = np.exp(eta_all - max_eta)
                    probs /= probs.sum(axis=1, keepdims=True)

                probs = np.nan_to_num(probs, nan=0.0)
                probs = np.clip(probs, 1e-8, 1.0)
                probs /= probs.sum(axis=1, keepdims=True)
                return probs

            # --- Monte Carlo over posterior draws ---
            K_a = len(model_a._categories)
            K_b = len(model_b._categories)
            rng = np.random.default_rng(seed=42)

            gammas = []
            vs = []
            joint_tables = np.zeros((self.n_draws, K_a, K_b))

            for m in range(self.n_draws):
                pa = _draw_proba(model_a, ses_pop, available_ses, rng)  # (n, K_a)
                pb = _draw_proba(model_b, ses_pop, available_ses, rng)  # (n, K_b)
                # Trim to consistent shapes
                pa = pa[:, :K_a]
                pb = pb[:, :K_b]
                # Joint table under CIA
                joint_m = (pa[:, :, None] * pb[:, None, :]).mean(axis=0)
                joint_tables[m] = joint_m
                gammas.append(goodman_kruskal_gamma(joint_m))
                vs.append(float(association(
                    (joint_m * self.n_sim).astype(int).clip(1),
                    method='cramer'
                )))

            gammas = np.array(gammas)
            vs = np.array(vs)
            joint_mean = joint_tables.mean(axis=0)

            # Point estimate: gamma from the mean joint table, NOT mean of
            # per-draw gammas. Averaging per-draw gammas suffers sign
            # cancellation because gamma is a nonlinear function of the table
            # entries (Jensen's inequality). The mean table preserves the
            # MLE's ordinal structure.
            gamma_point = goodman_kruskal_gamma(joint_mean)
            v_point = float(association(
                (joint_mean * self.n_sim).astype(int).clip(1),
                method='cramer'
            ))

            diag_a = model_a.diagnostics()
            diag_b = model_b.diagnostics()

            return {
                'var_a': var_id_a,
                'var_b': var_id_b,
                'method': 'bayesian_bridge',
                'gamma': round(float(gamma_point), 4),
                'gamma_ci_95': (
                    round(float(np.percentile(gammas, 2.5)), 4),
                    round(float(np.percentile(gammas, 97.5)), 4),
                ),
                'cramers_v': round(float(v_point), 4),
                'cramers_v_ci_95': (
                    round(float(np.percentile(vs, 2.5)), 4),
                    round(float(np.percentile(vs, 97.5)), 4),
                ),
                'joint_table': joint_mean.tolist(),
                'pseudo_r2_a': diag_a.get('pseudo_r2'),
                'pseudo_r2_b': diag_b.get('pseudo_r2'),
                'n_draws': self.n_draws,
                'n_simulated': self.n_sim,
                'note': (
                    'Laplace-approximate Bayesian posterior over joint table; '
                    'gamma and V CIs reflect parameter uncertainty'
                ),
            }

        except Exception as e:
            print(f"[bayesian-bridge] Failed for {var_id_a} × {var_id_b}: {e}")
            return None


# ---------------------------------------------------------------------------
# MRPBridgeEstimator
# ---------------------------------------------------------------------------

class MRPBridgeEstimator:
    """
    MRP Bridge: cell-level empirical distributions with partial pooling.

    Defines SES cells from categorical variables (default: escol × edad × sexo),
    computes the empirical P(Y_A|cell) and P(Y_B|cell) within each cell, applies
    shrinkage toward the global marginal, and poststratifies to produce the
    population joint table.

    This implements v3 §5.4: MRP for joint distribution at cell level.
    Shrinkage (James-Stein style) replaces full multilevel modeling — at n≈1000
    with ~70 cells, this gives comparable results without requiring PyMC.

    Output dict keys:
      gamma            — Goodman-Kruskal γ from poststratified joint table
      gamma_ci_95      — 95% bootstrap CI
      cramers_v        — Cramér's V (for comparison)
      joint_table      — K_a × K_b poststratified joint probability table
      n_cells_used     — number of cells with data in both surveys
      mean_cell_n      — average cell size across used cells
      method           — 'mrp_bridge'
    """

    def __init__(
        self,
        cell_cols: Optional[List[str]] = None,
        shrinkage_kappa: float = 10.0,
        min_cell_n: int = 3,
        n_bootstrap: int = 200,
        bin_cell_vars: Optional[Dict[str, int]] = None,
        max_categories: Optional[int] = 5,
    ) -> None:
        self.cell_cols = cell_cols or ['escol', 'edad', 'sexo']
        self.shrinkage_kappa = shrinkage_kappa
        self.min_cell_n = min_cell_n
        self.n_bootstrap = n_bootstrap
        # Default: bin edad (7→3) and escol (5→3) to reduce cell count.
        # With sexo binary: 3×3×2 = 18 cells (vs ~70 without binning).
        self.bin_cell_vars = (bin_cell_vars if bin_cell_vars is not None
                              else {'edad': 3, 'escol': 3})
        self.max_categories = max_categories

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
    ) -> Optional[Dict[str, Any]]:
        if col_a not in df_a.columns or col_b not in df_b.columns:
            return None

        try:
            _MAX_CARD = 20

            # --- Bin cell columns to reduce cell count ---
            def _bin_col(series: pd.Series, n_bins: int) -> pd.Series:
                """Bin a cell column into n_bins groups via equal-width."""
                vals = pd.to_numeric(series, errors='coerce')
                if vals.notna().sum() < 2:
                    return series
                lo, hi = vals.min(), vals.max()
                if lo == hi:
                    return series.fillna(0).astype(int).astype(str)
                edges = np.linspace(lo - 0.5, hi + 0.5, n_bins + 1)
                return pd.cut(vals, bins=edges, labels=[str(i) for i in range(n_bins)],
                              include_lowest=True).astype(str)

            # Apply binning to working copies
            df_a_work = df_a.copy()
            df_b_work = df_b.copy()
            binned_cols_map: Dict[str, str] = {}
            for col_name, n_bins in self.bin_cell_vars.items():
                if col_name in df_a_work.columns and col_name in df_b_work.columns:
                    new_name = f'{col_name}_bin'
                    df_a_work[new_name] = _bin_col(df_a_work[col_name], n_bins)
                    df_b_work[new_name] = _bin_col(df_b_work[col_name], n_bins)
                    binned_cols_map[col_name] = new_name

            # Resolve cell_cols: use binned version if available
            resolved_cols = [binned_cols_map.get(c, c) for c in self.cell_cols]

            available_cols = [
                c for c in resolved_cols
                if c in df_a_work.columns and c in df_b_work.columns
                and df_a_work[c].dropna().nunique() <= _MAX_CARD
                and df_b_work[c].dropna().nunique() <= _MAX_CARD
            ]
            if not available_cols:
                return None

            # --- Build cell keys ---
            def _cell_key(df: pd.DataFrame) -> pd.Series:
                parts = [df[c].astype(str).str.strip() for c in available_cols]
                return parts[0].str.cat(parts[1:], sep='_') if len(parts) > 1 else parts[0]

            # --- Cell-level empirical distributions with shrinkage ---
            def _cell_distributions(
                df: pd.DataFrame, col: str, wt: str,
            ) -> Tuple[Dict[str, np.ndarray], np.ndarray, list, Dict[str, float]]:
                """
                Returns:
                  cell_dists: {cell_key: probability vector} with shrinkage
                  global_dist: global marginal distribution
                  categories: sorted list of non-sentinel category values
                  cell_weights: {cell_key: total weight in cell}
                """
                work = df[[col] + available_cols].copy()
                work['_cell'] = _cell_key(df)
                work['_w'] = df[wt].astype(float) if wt in df.columns else 1.0
                work = work.dropna(subset=[col, '_cell'])
                # Filter sentinels from target
                mask = work[col].apply(lambda v: not _is_sentinel(v))
                work = work[mask]

                cats = sorted(work[col].dropna().unique().tolist(), key=str)
                if len(cats) < 2:
                    return {}, np.array([]), cats, {}
                K = len(cats)
                cat_idx = {c: i for i, c in enumerate(cats)}

                # Global marginal
                global_dist = np.zeros(K)
                for c, i in cat_idx.items():
                    m = work[col] == c
                    global_dist[i] = work.loc[m, '_w'].sum()
                total = global_dist.sum()
                if total > 0:
                    global_dist /= total

                # Per-cell distributions with shrinkage
                cell_dists: Dict[str, np.ndarray] = {}
                cell_weights: Dict[str, float] = {}
                for cell_key, grp in work.groupby('_cell'):
                    n_cell = len(grp)
                    if n_cell < self.min_cell_n:
                        continue
                    emp = np.zeros(K)
                    for c, i in cat_idx.items():
                        m = grp[col] == c
                        emp[i] = grp.loc[m, '_w'].sum()
                    emp_total = emp.sum()
                    if emp_total > 0:
                        emp /= emp_total
                    # Shrinkage: λ = n / (n + κ)
                    lam = n_cell / (n_cell + self.shrinkage_kappa)
                    pooled = lam * emp + (1 - lam) * global_dist
                    pooled_total = pooled.sum()
                    if pooled_total > 0:
                        pooled /= pooled_total
                    cell_dists[cell_key] = pooled
                    cell_weights[cell_key] = emp_total

                return cell_dists, global_dist, cats, cell_weights

            dist_a, global_a, cats_a, wt_a = _cell_distributions(df_a_work, col_a, weight_col)
            dist_b, global_b, cats_b, wt_b = _cell_distributions(df_b_work, col_b, weight_col)

            if len(cats_a) < 2 or len(cats_b) < 2:
                return None

            # --- Overlapping cells ---
            shared_cells = sorted(set(dist_a.keys()) & set(dist_b.keys()))
            if len(shared_cells) < 3:
                return None

            K_a, K_b = len(cats_a), len(cats_b)

            # --- Poststratified joint table ---
            def _compute_joint(cell_list, d_a, d_b, w_a, w_b):
                joint = np.zeros((K_a, K_b))
                total_w = 0.0
                for cell in cell_list:
                    # Cell weight = geometric mean of survey weights
                    cw = np.sqrt(w_a.get(cell, 1.0) * w_b.get(cell, 1.0))
                    joint += cw * np.outer(d_a[cell], d_b[cell])
                    total_w += cw
                if total_w > 0:
                    joint /= total_w
                return joint

            joint_table = _compute_joint(shared_cells, dist_a, dist_b, wt_a, wt_b)
            gamma_point = goodman_kruskal_gamma(joint_table)

            # Convert to integer counts for Cramér's V
            counts = (joint_table * 1000).astype(int).clip(1)
            v_point = float(association(counts, method='cramer'))

            # --- Bootstrap CI ---
            rng = np.random.default_rng(seed=42)
            boot_gammas = []
            for _ in range(self.n_bootstrap):
                boot_cells = rng.choice(shared_cells, size=len(shared_cells), replace=True).tolist()
                jt_b = _compute_joint(boot_cells, dist_a, dist_b, wt_a, wt_b)
                boot_gammas.append(goodman_kruskal_gamma(jt_b))

            boot_gammas = np.array(boot_gammas)
            gamma_ci = (
                round(float(np.percentile(boot_gammas, 2.5)), 4),
                round(float(np.percentile(boot_gammas, 97.5)), 4),
            )

            cell_sizes = [len(df_a_work[_cell_key(df_a_work) == c]) + len(df_b_work[_cell_key(df_b_work) == c])
                          for c in shared_cells]
            mean_cell_n = float(np.mean(cell_sizes)) if cell_sizes else 0.0

            return {
                'var_a': var_id_a,
                'var_b': var_id_b,
                'method': 'mrp_bridge',
                'gamma': round(gamma_point, 4),
                'gamma_ci_95': gamma_ci,
                'cramers_v': round(v_point, 4),
                'joint_table': joint_table.tolist(),
                'n_cells_used': len(shared_cells),
                'mean_cell_n': round(mean_cell_n, 1),
                'cell_cols_used': available_cols,
                'note': (
                    f'MRP with shrinkage (κ={self.shrinkage_kappa}) '
                    f'over {len(shared_cells)} cells ({", ".join(available_cols)})'
                ),
            }

        except Exception as e:
            print(f"[mrp-bridge] Failed for {var_id_a} × {var_id_b}: {e}")
            return None


# ---------------------------------------------------------------------------
# DoublyRobustBridgeEstimator
# ---------------------------------------------------------------------------

class DoublyRobustBridgeEstimator:
    """
    Doubly robust bridge: AIPW-corrected marginals + CIA joint table.

    Combines an outcome model P(Y|X) with a propensity model P(survey=A|X)
    using the augmented IPW formula (v3 §5.2, §7.1).  The DR estimator is
    consistent if EITHER the outcome model OR the propensity model is correct.

    Propensity weights are trimmed at the 95th percentile to guard against
    extreme weights from near-separation (v3 §6 pitfall).

    Output dict keys:
      gamma              — Goodman-Kruskal γ from DR-corrected joint table
      gamma_ci_95        — 95% bootstrap CI
      cramers_v          — Cramér's V
      joint_table        — K_a × K_b joint probability table
      propensity_overlap — Kolmogorov-Smirnov statistic for SES overlap
      max_weight         — maximum trimmed propensity weight
      n_trimmed          — weights trimmed
      method             — 'doubly_robust_bridge'
    """

    def __init__(self, n_sim: int = 2000, n_bootstrap: int = 200,
                 max_categories: Optional[int] = 5,
                 propensity_vars: Optional[List[str]] = None,
                 ks_threshold: float = 0.4) -> None:
        self.n_sim = n_sim
        self.n_bootstrap = n_bootstrap
        self.max_categories = max_categories
        self.propensity_vars = propensity_vars or ['sexo', 'escol', 'edad']
        self.ks_threshold = ks_threshold

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
    ) -> Optional[Dict[str, Any]]:
        if ses_vars is None:
            ses_vars = SES_REGRESSION_VARS
        if col_a not in df_a.columns or col_b not in df_b.columns:
            return None

        try:
            import statsmodels.api as sm

            # --- Restrict to shared SES features ---
            available = [v for v in ses_vars if v in df_a.columns and v in df_b.columns]
            if len(available) < 2:
                return None

            # --- Fit outcome models on shared SES features only ---
            # Using the intersection ensures the feature space matches when we
            # predict model_a on survey B's population (and vice versa).
            model_a = SurveyVarModel()
            model_a.fit(df_a, col_a, available, weight_col,
                        max_categories=self.max_categories)
            model_b = SurveyVarModel()
            model_b.fit(df_b, col_b, available, weight_col,
                        max_categories=self.max_categories)

            cats_a = model_a._categories
            cats_b = model_b._categories
            K_a, K_b = len(cats_a), len(cats_b)

            # --- Encode SES for both surveys ---
            enc = SESEncoder()

            sub_a = _drop_ses_sentinel_rows(
                df_a[[col_a] + [v for v in available if v in df_a.columns]].dropna(), available
            )
            sub_b = _drop_ses_sentinel_rows(
                df_b[[col_b] + [v for v in available if v in df_b.columns]].dropna(), available
            )
            if len(sub_a) < 30 or len(sub_b) < 30:
                return None

            X_a = enc.fit_transform(sub_a[available]).fillna(0.0)
            X_b = enc.transform(sub_b[available]).fillna(0.0)

            # --- Propensity model: P(survey=A | X) ---
            # Use restricted feature set for propensity to avoid near-separation
            # when too many one-hot columns overpower the logistic model.
            # Petersen et al. (2012); Li, Morgan & Zaslavsky (2018).
            prop_avail = [v for v in self.propensity_vars
                          if v in df_a.columns and v in df_b.columns]
            if len(prop_avail) < 1:
                prop_avail = available  # fallback to full features

            prop_enc = SESEncoder()
            Xp_a = prop_enc.fit_transform(sub_a[prop_avail]).fillna(0.0)
            Xp_b = prop_enc.transform(sub_b[prop_avail]).fillna(0.0)
            X_pooled_prop = pd.concat([Xp_a, Xp_b], ignore_index=True)
            delta = np.concatenate([np.ones(len(Xp_a)), np.zeros(len(Xp_b))])
            Xc = sm.add_constant(X_pooled_prop, has_constant='add')
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                prop_model = sm.Logit(delta, Xc).fit(method='bfgs', disp=False)
            prop_all = np.asarray(prop_model.predict(Xc), dtype=float)
            prop_a = prop_all[:len(Xp_a)]
            prop_b = prop_all[len(Xp_a):]

            # KS overlap diagnostic
            ks_stat = float(stats.ks_2samp(prop_a, prop_b).statistic)

            # IPW weights for survey A units: w_i = (1 - π_i) / π_i
            prop_a_clipped = np.clip(prop_a, 0.01, 0.99)
            raw_weights = (1 - prop_a_clipped) / prop_a_clipped
            # Trim extreme weights
            cap = np.percentile(raw_weights, 95)
            n_trimmed = int((raw_weights > cap).sum())
            weights = np.minimum(raw_weights, cap)
            weights /= weights.sum()  # normalise

            # --- AIPW-corrected marginal for var_a in survey B population ---
            def _aipw_marginal(
                model: SurveyVarModel, sub_src: pd.DataFrame, col_src: str,
                sub_tgt: pd.DataFrame, avail: List[str],
                cats: list, w: np.ndarray,
            ) -> np.ndarray:
                """DR-corrected P(Y=k) for the target population.

                Uses model's own encoder to encode sub_src and sub_tgt, guaranteeing
                that feature column count matches model's params regardless of which
                categories appear in the reference encoder's training data.
                """
                K = len(cats)
                # Re-encode using model's own encoder (avoids column count mismatch)
                X_tgt = model._encoder.transform(sub_tgt[avail]).fillna(0.0)
                X_src = model._encoder.transform(sub_src[avail]).fillna(0.0)

                # Outcome model predictions on target
                pred_tgt = model.predict_proba(X_tgt).values  # (n_tgt, K)
                imputed = pred_tgt.mean(axis=0)  # (K,)

                # Outcome model predictions on source (for residual)
                pred_src = model.predict_proba(X_src).values  # (n_src, K)

                # Observed indicators in source
                y_src = sub_src[col_src].values
                indicators = np.zeros((len(y_src), K))
                cat_map = {c: i for i, c in enumerate(cats)}
                for idx, val in enumerate(y_src):
                    if val in cat_map:
                        indicators[idx, cat_map[val]] = 1.0
                    else:
                        try:
                            fval = float(val)
                            if fval in cat_map:
                                indicators[idx, cat_map[fval]] = 1.0
                        except (ValueError, TypeError):
                            pass

                # AIPW correction
                residual = indicators - pred_src  # (n_src, K)
                correction = (residual * w[:, None]).sum(axis=0)
                dr_marginal = imputed + correction
                # Clip and renorm
                dr_marginal = np.clip(dr_marginal, 1e-8, None)
                dr_marginal /= dr_marginal.sum()
                return dr_marginal

            # Marginal of Y_A in B's population (kept for diagnostics)
            marg_a = _aipw_marginal(model_a, sub_a, col_a, sub_b, available, cats_a, weights)

            # For Y_B in A's population, compute reverse propensity
            prop_b_units = np.clip(prop_b, 0.01, 0.99)
            raw_weights_b = prop_b_units / (1 - prop_b_units)
            cap_b = np.percentile(raw_weights_b, 95)
            weights_b = np.minimum(raw_weights_b, cap_b)
            weights_b /= weights_b.sum()

            marg_b = _aipw_marginal(model_b, sub_b, col_b, sub_a, available, cats_b, weights_b)

            # --- Joint table under CIA via individual-level predictions ---
            # Using a shared reference SES population (same as Bayesian),
            # predict P(Y_a|X_i) and P(Y_b|X_i) for each individual and
            # compute mean outer product.  This recovers ordinal association;
            # outer(marg_a, marg_b) would always give gamma ≈ 0 by construction.
            helper = CrossDatasetBivariateEstimator(n_sim=self.n_sim)
            ses_pop = helper._sample_ses_population(df_a, df_b, available, weight_col)
            X_ref_a = model_a._encoder.transform(ses_pop[available]).fillna(0.0)
            X_ref_b = model_b._encoder.transform(ses_pop[available]).fillna(0.0)
            pa_ref = model_a.predict_proba(X_ref_a).values[:, :K_a]
            pb_ref = model_b.predict_proba(X_ref_b).values[:, :K_b]
            joint_table = (pa_ref[:, :, None] * pb_ref[:, None, :]).mean(axis=0)
            joint_table /= joint_table.sum()

            gamma_point = goodman_kruskal_gamma(joint_table)
            counts = (joint_table * 1000).astype(int).clip(1)
            v_point = float(association(counts, method='cramer'))

            # --- Bootstrap CI ---
            rng = np.random.default_rng(seed=42)
            boot_gammas = []
            n_a, n_b = len(sub_a), len(sub_b)
            for _ in range(self.n_bootstrap):
                idx_a = rng.choice(n_a, size=n_a, replace=True)
                idx_b = rng.choice(n_b, size=n_b, replace=True)
                try:
                    # Re-fit on bootstrap samples using shared SES features
                    boot_a_df = sub_a.iloc[idx_a].reset_index(drop=True)
                    boot_b_df = sub_b.iloc[idx_b].reset_index(drop=True)
                    bm_a = SurveyVarModel()
                    bm_a.fit(boot_a_df, col_a, available, weight_col)
                    bm_b = SurveyVarModel()
                    bm_b.fit(boot_b_df, col_b, available, weight_col)

                    # Individual-level CIA on reference population using
                    # each bootstrap model's own encoder.
                    X_ref_a_boot = bm_a._encoder.transform(ses_pop[available]).fillna(0.0)
                    X_ref_b_boot = bm_b._encoder.transform(ses_pop[available]).fillna(0.0)
                    pa_b = bm_a.predict_proba(X_ref_a_boot).values[:, :K_a]
                    pb_b = bm_b.predict_proba(X_ref_b_boot).values[:, :K_b]
                    jt_boot = (pa_b[:, :, None] * pb_b[:, None, :]).mean(axis=0)
                    jt_boot /= jt_boot.sum()
                    boot_gammas.append(goodman_kruskal_gamma(jt_boot))
                except Exception:
                    continue

            if len(boot_gammas) < 10:
                gamma_ci = (gamma_point, gamma_point)
            else:
                boot_gammas = np.array(boot_gammas)
                gamma_ci = (
                    round(float(np.percentile(boot_gammas, 2.5)), 4),
                    round(float(np.percentile(boot_gammas, 97.5)), 4),
                )

            return {
                'var_a': var_id_a,
                'var_b': var_id_b,
                'method': 'doubly_robust_bridge',
                'gamma': round(gamma_point, 4),
                'gamma_ci_95': gamma_ci,
                'cramers_v': round(v_point, 4),
                'joint_table': joint_table.tolist(),
                'propensity_overlap': round(ks_stat, 4),
                'ks_warning': ks_stat > self.ks_threshold,
                'propensity_features': prop_avail,
                'max_weight': round(float(cap), 4),
                'n_trimmed': n_trimmed,
                'n_a': n_a,
                'n_b': n_b,
                'note': (
                    'AIPW doubly-robust correction; joint table from '
                    'DR-corrected marginals under CIA'
                ),
            }

        except Exception as e:
            print(f"[doubly-robust-bridge] Failed for {var_id_a} × {var_id_b}: {e}")
            return None
