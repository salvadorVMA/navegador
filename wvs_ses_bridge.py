"""WVS SES bridge: cross-dataset γ estimation between WVS and los_mex.

Wraps the existing DoublyRobustBridgeEstimator (ses_regression.py) to handle
WVS-specific conventions (weight column, harmonized SES vars) and provides
convenience methods for the γ-surface:

    γ(variable_pair, country, wave, SES_reference) → [-1, +1]

Main classes
------------
SESHarmonizer
    Validates SES column availability, builds reference populations
    (local / standardized / zone-pooled).

WVSBridgeEstimator
    Wraps DoublyRobustBridgeEstimator for WVS contexts.
    Methods:
        estimate_cross_dataset()  — WVS variable × los_mex variable
        estimate_within_wvs()     — WVS variable × WVS variable
        temporal_sweep()          — γ(wave) for Mexico across all 7 waves
        geographic_sweep()        — γ(country) across Wave 7 countries

Usage
-----
    from wvs_ses_bridge import WVSBridgeEstimator
    estimator = WVSBridgeEstimator(n_sim=2000, n_bootstrap=50)

    # Cross-dataset: WVS trust-in-parliament × los_mex political trust
    result = estimator.estimate_cross_dataset(
        df_wvs=wvs_enc_dict['WVS_W7_MEX']['dataframe'], col_wvs='Q71',
        df_los_mex=enc_dict['CULTURA_POLITICA']['dataframe'], col_los_mex='p16_3',
    )
    # result: {'gamma': 0.35, 'gamma_ci_95': [0.12, 0.58], ...}

    # Temporal sweep: γ(wave) for religiosity × trust-in-church in Mexico
    γ_by_wave = estimator.temporal_sweep(
        wvs_enc_dict, col_a='Q173', col_b='Q76', country='MEX'
    )
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ses_regression import (
    DoublyRobustBridgeEstimator,
    SES_REGRESSION_VARS,
)
from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WVS_WEIGHT_COL = "W_WEIGHT"
LOS_MEX_WEIGHT_COL = "Pondi2"

# Unified weight column name used internally when combining datasets
_BRIDGE_WEIGHT_COL = "bridge_weight"

# The 4-var SES config (matches v3 sweep and wvs_loader.harmonize_ses)
BRIDGE_SES_VARS: List[str] = SES_REGRESSION_VARS  # ['sexo', 'edad', 'escol', 'Tam_loc']

# enc_dict key pattern: WVS_W{wave}_{ALPHA3}
def _wvs_key(wave: int, alpha3: str) -> str:
    return f"WVS_W{wave}_{alpha3.upper()}"


# ---------------------------------------------------------------------------
# SESHarmonizer
# ---------------------------------------------------------------------------

class SESHarmonizer:
    """Validate and manage SES variables for WVS ↔ los_mex bridge estimation.

    Handles three reference population modes:
        local       — pool df_a + df_b (default; each dataset contributes equally)
        standardized — use a fixed external reference (e.g. MEX Wave 7 SES)
        zone_pooled  — merge all country DataFrames in a cultural zone
    """

    SES_VARS = BRIDGE_SES_VARS

    def validate(self, df: pd.DataFrame, label: str = "") -> List[str]:
        """Return SES vars present in df; warn about missing ones.

        Parameters
        ----------
        df : pd.DataFrame
        label : str
            Human label for warning messages (e.g. 'WVS_W7_MEX').

        Returns
        -------
        list of available SES column names.
        """
        available = [v for v in self.SES_VARS if v in df.columns]
        missing = [v for v in self.SES_VARS if v not in df.columns]
        if missing:
            warnings.warn(
                f"SESHarmonizer [{label}]: SES vars not found: {missing}. "
                f"Available: {available}. "
                "Run wvs_loader.harmonize_ses() on WVS data before bridging.",
                stacklevel=2,
            )
        return available

    def build_standardized_reference(
        self,
        df: pd.DataFrame,
        weight_col: Optional[str] = None,
        n: int = 5000,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Sample SES rows from df to use as a fixed reference population.

        Use this when you want γ to reflect structural P(Y|SES) differences
        across contexts without confounding by SES composition shifts.

        Parameters
        ----------
        df : pd.DataFrame
            Source dataset whose SES distribution becomes the reference.
        weight_col : str, optional
            Weight column for sampling. If None, uniform sampling.
        n : int
            Number of rows to draw (with replacement).
        seed : int
            Random state for reproducibility.

        Returns
        -------
        pd.DataFrame with only SES columns (and bridge_weight), ready to
        pass as an override reference population.
        """
        available = self.validate(df, "standardized_reference")
        if not available:
            raise ValueError("No SES columns available to build reference population.")

        ses_df = df[available].dropna(subset=available)
        if weight_col and weight_col in df.columns:
            w = df.loc[ses_df.index, weight_col].fillna(1.0)
            w = w / w.sum()
        else:
            w = None

        rng = np.random.default_rng(seed)
        idx = rng.choice(len(ses_df), size=n, replace=True, p=w)
        ref = ses_df.iloc[idx].copy().reset_index(drop=True)
        ref[_BRIDGE_WEIGHT_COL] = 1.0
        return ref

    def build_zone_pool(
        self,
        wvs_enc_dict: dict,
        zone: str,
        wave: int = 7,
    ) -> pd.DataFrame:
        """Pool SES rows from all countries in a cultural zone for one wave.

        Parameters
        ----------
        wvs_enc_dict : dict
            The enc_dict portion of a wvs_dict.
        zone : str
            Inglehart-Welzel zone name (from wvs_metadata.CULTURAL_ZONES).
        wave : int
            WVS wave number.

        Returns
        -------
        Concatenated DataFrame of SES rows from all zone countries.
        """
        if zone not in CULTURAL_ZONES:
            raise ValueError(
                f"Unknown cultural zone: '{zone}'. "
                f"Valid zones: {list(CULTURAL_ZONES.keys())}"
            )

        parts = []
        for alpha3 in CULTURAL_ZONES[zone]:
            key = _wvs_key(wave, alpha3)
            if key not in wvs_enc_dict:
                continue
            df = wvs_enc_dict[key]["dataframe"]
            available = self.validate(df, key)
            if len(available) >= 2:
                sub = df[available + [WVS_WEIGHT_COL]].copy() if WVS_WEIGHT_COL in df.columns else df[available].copy()
                sub["_country"] = alpha3
                parts.append(sub)

        if not parts:
            raise ValueError(
                f"No data found for zone '{zone}' wave {wave} in wvs_enc_dict."
            )
        return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------
# Weight column unification
# ---------------------------------------------------------------------------

def _unify_weight_col(df: pd.DataFrame, original_col: Optional[str]) -> pd.DataFrame:
    """Add _BRIDGE_WEIGHT_COL to df, copying from original_col or defaulting to 1.0."""
    df = df.copy()
    if original_col and original_col in df.columns:
        df[_BRIDGE_WEIGHT_COL] = df[original_col].fillna(1.0)
    else:
        df[_BRIDGE_WEIGHT_COL] = 1.0
    return df


# ---------------------------------------------------------------------------
# WVSBridgeEstimator
# ---------------------------------------------------------------------------

class WVSBridgeEstimator:
    """Compute γ between WVS variables and/or los_mex variables.

    Wraps DoublyRobustBridgeEstimator with WVS-aware defaults:
        - weight_col handled per-dataset (W_WEIGHT for WVS, Pondi2 for los_mex)
        - SES vars default to 4-var BRIDGE_SES_VARS
        - Graceful handling of missing weight or SES columns

    Parameters
    ----------
    n_sim : int
        Monte Carlo draws for CIA simulation (default 2000).
    n_bootstrap : int
        Bootstrap samples for CI estimation (default 50 for sweeps, 200 for precision).
    max_categories : int
        Maximum categories for outcome variable (default 5).
    """

    def __init__(
        self,
        n_sim: int = 2000,
        n_bootstrap: int = 50,
        max_categories: int = 5,
    ):
        self._dr = DoublyRobustBridgeEstimator(
            n_sim=n_sim,
            n_bootstrap=n_bootstrap,
            max_categories=max_categories,
        )
        self._harmonizer = SESHarmonizer()

    def _prep(self, df: pd.DataFrame, weight_col: Optional[str]) -> pd.DataFrame:
        """Unify weight column and return cleaned copy."""
        return _unify_weight_col(df, weight_col)

    def estimate_cross_dataset(
        self,
        df_wvs: pd.DataFrame,
        col_wvs: str,
        df_los_mex: pd.DataFrame,
        col_los_mex: str,
        var_id_a: str = "",
        var_id_b: str = "",
        ses_vars: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Estimate γ between a WVS variable and a los_mex variable.

        The two DataFrames must already have harmonized SES columns
        (sexo, edad, escol, Tam_loc) — WVS data must be processed by
        wvs_loader.harmonize_ses() first.

        Parameters
        ----------
        df_wvs : pd.DataFrame
            WVS individual-level data (sentinel-cleaned, SES harmonized).
        col_wvs : str
            Attitude column in df_wvs (e.g. 'Q71').
        df_los_mex : pd.DataFrame
            los_mex individual-level data.
        col_los_mex : str
            Attitude column in df_los_mex.
        var_id_a, var_id_b : str
            Human-readable IDs for logging (e.g. 'Q71|W7_MEX', 'p16_3|CUL').
        ses_vars : list, optional
            Override SES variable list. Defaults to BRIDGE_SES_VARS.

        Returns
        -------
        dict with keys from DoublyRobustBridgeEstimator, or None on failure.
        """
        ses = ses_vars or BRIDGE_SES_VARS

        df_a = self._prep(df_wvs, WVS_WEIGHT_COL)
        df_b = self._prep(df_los_mex, LOS_MEX_WEIGHT_COL)

        avail_a = self._harmonizer.validate(df_a, var_id_a or "WVS")
        avail_b = self._harmonizer.validate(df_b, var_id_b or "los_mex")
        shared_ses = [v for v in ses if v in avail_a and v in avail_b]

        if len(shared_ses) < 2:
            warnings.warn(
                f"estimate_cross_dataset: fewer than 2 shared SES vars "
                f"({shared_ses}). Skipping pair ({var_id_a}, {var_id_b})."
            )
            return None

        return self._dr.estimate(
            var_id_a=var_id_a or col_wvs,
            var_id_b=var_id_b or col_los_mex,
            df_a=df_a,
            df_b=df_b,
            col_a=col_wvs,
            col_b=col_los_mex,
            ses_vars=shared_ses,
            weight_col=_BRIDGE_WEIGHT_COL,
        )

    def estimate_within_wvs(
        self,
        df_a: pd.DataFrame,
        col_a: str,
        df_b: pd.DataFrame,
        col_b: str,
        var_id_a: str = "",
        var_id_b: str = "",
        ses_vars: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Estimate γ between two WVS variables (same or different waves/countries).

        Used for:
        - Within-wave, within-country: standard bivariate γ
        - Cross-wave (temporal bridge): df_a from wave_i, df_b from wave_j
        - Cross-country (geographic bridge): df_a from country_A, df_b from country_B

        Both DataFrames must have harmonized SES columns.
        """
        ses = ses_vars or BRIDGE_SES_VARS

        df_a = self._prep(df_a, WVS_WEIGHT_COL)
        df_b = self._prep(df_b, WVS_WEIGHT_COL)

        avail_a = self._harmonizer.validate(df_a, var_id_a or "WVS_A")
        avail_b = self._harmonizer.validate(df_b, var_id_b or "WVS_B")
        shared_ses = [v for v in ses if v in avail_a and v in avail_b]

        if len(shared_ses) < 2:
            warnings.warn(
                f"estimate_within_wvs: fewer than 2 shared SES vars ({shared_ses})."
            )
            return None

        return self._dr.estimate(
            var_id_a=var_id_a or col_a,
            var_id_b=var_id_b or col_b,
            df_a=df_a,
            df_b=df_b,
            col_a=col_a,
            col_b=col_b,
            ses_vars=shared_ses,
            weight_col=_BRIDGE_WEIGHT_COL,
        )

    # ------------------------------------------------------------------
    # Temporal sweep: γ(wave) for Mexico
    # ------------------------------------------------------------------

    def temporal_sweep(
        self,
        wvs_enc_dict: dict,
        col_a: str,
        col_b: str,
        country: str = "MEX",
        ses_vars: Optional[List[str]] = None,
    ) -> Dict[int, Optional[Dict[str, Any]]]:
        """Compute γ(wave) for a variable pair within one country across all waves.

        Runs estimate_within_wvs() for each wave where both col_a and col_b
        exist in the country's enc_dict entry.

        Parameters
        ----------
        wvs_enc_dict : dict
            The enc_dict portion of a wvs_dict.
        col_a, col_b : str
            WVS Q-code column names (must be present after harmonization).
        country : str
            ISO alpha-3 country code (default 'MEX').
        ses_vars : list, optional
            Override SES vars.

        Returns
        -------
        dict mapping wave_int → estimate dict (or None if wave unavailable).

        Example
        -------
        γ_waves = estimator.temporal_sweep(wvs_enc_dict, 'Q6', 'Q173', country='MEX')
        # {1: None, 2: None, ..., 6: {'gamma': 0.22, ...}, 7: {'gamma': 0.28, ...}}
        """
        results: Dict[int, Optional[Dict[str, Any]]] = {}
        for wave in range(1, 8):
            key = _wvs_key(wave, country)
            if key not in wvs_enc_dict:
                results[wave] = None
                continue

            df = wvs_enc_dict[key]["dataframe"]
            if col_a not in df.columns or col_b not in df.columns:
                results[wave] = None
                continue

            result = self.estimate_within_wvs(
                df_a=df, col_a=col_a,
                df_b=df, col_b=col_b,
                var_id_a=f"{col_a}|W{wave}_{country}",
                var_id_b=f"{col_b}|W{wave}_{country}",
                ses_vars=ses_vars,
            )
            results[wave] = result

        return results

    # ------------------------------------------------------------------
    # Geographic sweep: γ(country) in Wave 7
    # ------------------------------------------------------------------

    def geographic_sweep(
        self,
        wvs_enc_dict: dict,
        col_a: str,
        col_b: str,
        wave: int = 7,
        zone: Optional[str] = None,
        ses_vars: Optional[List[str]] = None,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Compute γ(country) for a variable pair across countries in one wave.

        Parameters
        ----------
        wvs_enc_dict : dict
            The enc_dict portion of a wvs_dict.
        col_a, col_b : str
            WVS Q-code column names.
        wave : int
            WVS wave number (default 7).
        zone : str, optional
            Restrict to one Inglehart-Welzel cultural zone. None = all countries.
        ses_vars : list, optional
            Override SES vars.

        Returns
        -------
        dict mapping alpha3 → estimate dict (or None if data unavailable).

        Example
        -------
        γ_countries = estimator.geographic_sweep(
            wvs_enc_dict, 'Q71', 'Q173', zone='Latin America'
        )
        """
        if zone is not None:
            if zone not in CULTURAL_ZONES:
                raise ValueError(f"Unknown zone: '{zone}'")
            target_countries = CULTURAL_ZONES[zone]
        else:
            # All countries present in enc_dict for this wave
            prefix = f"WVS_W{wave}_"
            target_countries = [
                k[len(prefix):] for k in wvs_enc_dict if k.startswith(prefix)
            ]

        results: Dict[str, Optional[Dict[str, Any]]] = {}
        for alpha3 in target_countries:
            key = _wvs_key(wave, alpha3)
            if key not in wvs_enc_dict:
                results[alpha3] = None
                continue

            df = wvs_enc_dict[key]["dataframe"]
            if col_a not in df.columns or col_b not in df.columns:
                results[alpha3] = None
                continue

            result = self.estimate_within_wvs(
                df_a=df, col_a=col_a,
                df_b=df, col_b=col_b,
                var_id_a=f"{col_a}|W{wave}_{alpha3}",
                var_id_b=f"{col_b}|W{wave}_{alpha3}",
                ses_vars=ses_vars,
            )
            results[alpha3] = result

        return results


# ---------------------------------------------------------------------------
# Convenience: summarise γ-surface results
# ---------------------------------------------------------------------------

def summarise_temporal(γ_by_wave: Dict[int, Optional[Dict]]) -> pd.DataFrame:
    """Convert temporal_sweep output to a tidy DataFrame.

    Returns columns: wave, gamma, gamma_lo, gamma_hi, n_obs, converged
    """
    rows = []
    for wave, res in sorted(γ_by_wave.items()):
        if res is None:
            rows.append({"wave": wave, "gamma": np.nan, "gamma_lo": np.nan,
                         "gamma_hi": np.nan, "n_obs": 0, "converged": False})
        else:
            ci = res.get("gamma_ci_95", [np.nan, np.nan])
            rows.append({
                "wave": wave,
                "gamma": res.get("gamma", np.nan),
                "gamma_lo": ci[0] if len(ci) > 0 else np.nan,
                "gamma_hi": ci[1] if len(ci) > 1 else np.nan,
                "n_obs": res.get("n_obs", np.nan),
                "converged": res.get("converged", True),
            })
    return pd.DataFrame(rows)


def summarise_geographic(
    γ_by_country: Dict[str, Optional[Dict]],
) -> pd.DataFrame:
    """Convert geographic_sweep output to a tidy DataFrame.

    Returns columns: country, zone, gamma, gamma_lo, gamma_hi, n_obs, converged
    """
    rows = []
    for alpha3, res in sorted(γ_by_country.items()):
        zone = COUNTRY_ZONE.get(alpha3, "Unknown")
        if res is None:
            rows.append({"country": alpha3, "zone": zone, "gamma": np.nan,
                         "gamma_lo": np.nan, "gamma_hi": np.nan,
                         "n_obs": 0, "converged": False})
        else:
            ci = res.get("gamma_ci_95", [np.nan, np.nan])
            rows.append({
                "country": alpha3,
                "zone": zone,
                "gamma": res.get("gamma", np.nan),
                "gamma_lo": ci[0] if len(ci) > 0 else np.nan,
                "gamma_hi": ci[1] if len(ci) > 1 else np.nan,
                "n_obs": res.get("n_obs", np.nan),
                "converged": res.get("converged", True),
            })
    return pd.DataFrame(rows)
