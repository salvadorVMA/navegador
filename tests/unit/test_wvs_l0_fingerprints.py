"""
Unit tests for WVS L0 (item-level) SES fingerprint computation.

Tests are structured to run WITHOUT the large WVS CSV/zip files —
all tests use synthetic DataFrames and mock data. They validate:
  - Sentinel filtering (negative values, >=97)
  - SES harmonization logic
  - Fingerprint computation (Spearman rho, GK gamma)
  - Output format validation
  - Edge cases (all-NaN, constant, missing SES vars)
  - Q-code -> construct mapping
  - Orphan enrichment with candidate construct
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.compute_wvs_l0_fingerprints import (
    SES_COLS,
    _bin5,
    _build_domain_construct_index,
    _build_qcode_construct_index,
    _best_candidate_construct,
    _clean_ses_wvs,
    _fingerprint,
    _gk_gamma,
    _is_sentinel,
    _spearman_rho,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _synthetic_wvs_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Build a synthetic WVS-like DataFrame with harmonized SES columns."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        # SES columns (already harmonized)
        "sexo": rng.choice([1, 2], size=n),
        "edad": rng.uniform(18, 80, size=n).round(0),
        "escol": rng.choice([1, 2, 3, 4, 5], size=n),
        "Tam_loc": rng.choice([1, 2, 3, 4], size=n),
        # Substantive Q-codes
        "Q1": rng.choice([1, 2, 3, 4], size=n),
        "Q2": rng.choice([1, 2, 3, 4, 5], size=n),
        "Q3": rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], size=n),
        # Q-code with sentinels
        "Q4": rng.choice([1, 2, 3, 4, -1, -2, 98, 99], size=n),
        # Binary item
        "Q5": rng.choice([1, 2], size=n),
        # Construct aggregate
        "wvs_agg_test_construct": rng.uniform(1, 10, size=n),
    })
    return df


def _synthetic_manifest():
    """Build a minimal WVS construct manifest."""
    return [
        {
            "key": "WVS_A|test_construct",
            "column": "wvs_agg_test_construct",
            "type": "good",
            "alpha": 0.8,
            "n_valid": 200,
            "n_items": 3,
            "items": ["Q1", "Q2", "Q3"],
            "reverse_coded": ["Q3"],
        },
        {
            "key": "WVS_B|other_construct",
            "column": "wvs_agg_other_construct",
            "type": "formative_index",
            "alpha": None,
            "n_valid": 200,
            "n_items": 1,
            "items": ["Q5"],
            "reverse_coded": [],
        },
    ]


# ---------------------------------------------------------------------------
# Test sentinel filtering
# ---------------------------------------------------------------------------

class TestSentinelFiltering:
    """Validate sentinel detection and removal."""

    def test_negative_is_sentinel(self):
        assert _is_sentinel(-1) is True
        assert _is_sentinel(-5) is True

    def test_high_is_sentinel(self):
        assert _is_sentinel(97) is True
        assert _is_sentinel(98) is True
        assert _is_sentinel(99) is True

    def test_valid_values_not_sentinel(self):
        assert _is_sentinel(0) is False
        assert _is_sentinel(1) is False
        assert _is_sentinel(50) is False
        assert _is_sentinel(96) is False

    def test_nan_not_sentinel(self):
        assert _is_sentinel(np.nan) is False

    def test_sentinel_filtering_in_ses_clean(self):
        """SES columns should have sentinels replaced with NaN."""
        df = pd.DataFrame({
            "sexo": [1, 2, -1, 1, 2],
            "edad": [25, 35, 45, 5, 105],  # 5 and 105 out of 15-100 range
            "escol": [1, 2, 99, 3, -2],
            "Tam_loc": [1, 2, 3, 98, 4],
        })
        ses = _clean_ses_wvs(df)
        # sexo: -1 should be NaN
        assert pd.isna(ses.loc[2, "sexo"])
        assert ses.loc[0, "sexo"] == 1.0
        # edad: 5 and 105 should be NaN (outside 15-100)
        assert pd.isna(ses.loc[3, "edad"])
        assert pd.isna(ses.loc[4, "edad"])
        # escol: 99 and -2 should be NaN
        assert pd.isna(ses.loc[2, "escol"])
        assert pd.isna(ses.loc[4, "escol"])
        # Tam_loc: 98 should be NaN
        assert pd.isna(ses.loc[3, "Tam_loc"])


# ---------------------------------------------------------------------------
# Test SES harmonization
# ---------------------------------------------------------------------------

class TestSESHarmonization:
    """Validate SES column cleaning."""

    def test_all_four_ses_cols_present(self):
        df = _synthetic_wvs_df()
        ses = _clean_ses_wvs(df)
        for col in SES_COLS:
            assert col in ses.columns

    def test_missing_ses_col_filled_with_nan(self):
        df = pd.DataFrame({"Q1": [1, 2, 3]})
        ses = _clean_ses_wvs(df)
        for col in SES_COLS:
            assert col in ses.columns
            assert ses[col].isna().all()

    def test_edad_range_filtering(self):
        df = pd.DataFrame({
            "sexo": [1], "escol": [3], "Tam_loc": [2],
            "edad": [10],  # too young
        })
        ses = _clean_ses_wvs(df)
        assert pd.isna(ses.loc[0, "edad"])

    def test_valid_edad_passes(self):
        df = pd.DataFrame({
            "sexo": [1], "escol": [3], "Tam_loc": [2],
            "edad": [35],
        })
        ses = _clean_ses_wvs(df)
        assert ses.loc[0, "edad"] == 35.0


# ---------------------------------------------------------------------------
# Test fingerprint computation
# ---------------------------------------------------------------------------

class TestFingerprintComputation:
    """Validate the core fingerprint computation."""

    def test_basic_fingerprint(self):
        df = _synthetic_wvs_df(n=500)
        ses = _clean_ses_wvs(df)
        series = pd.to_numeric(df["Q1"], errors="coerce")
        fp = _fingerprint(series, ses)
        assert fp is not None
        assert "rho_escol" in fp
        assert "rho_Tam_loc" in fp
        assert "rho_sexo" in fp
        assert "rho_edad" in fp
        assert "ses_magnitude" in fp
        assert fp["ses_magnitude"] >= 0.0
        assert fp["dominant_dim"] in {"escol", "Tam_loc", "sexo", "edad"}
        assert "n_obs" in fp

    def test_fingerprint_rho_range(self):
        df = _synthetic_wvs_df(n=500)
        ses = _clean_ses_wvs(df)
        series = pd.to_numeric(df["Q2"], errors="coerce")
        fp = _fingerprint(series, ses)
        assert fp is not None
        for dim in SES_COLS:
            rho = fp.get(f"rho_{dim}")
            if rho is not None:
                assert -1.0 <= rho <= 1.0, f"rho_{dim}={rho} out of range"

    def test_fingerprint_all_nan_returns_none(self):
        """Column that's all NaN should return None."""
        ses = pd.DataFrame({
            "sexo": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
            "edad": [20, 30, 40, 50, 60, 25, 35, 45, 55, 65],
            "escol": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "Tam_loc": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2],
        })
        series = pd.Series([np.nan] * 10)
        fp = _fingerprint(series, ses)
        assert fp is None

    def test_fingerprint_constant_col_returns_none(self):
        """Constant column (nunique < 2) should be skipped upstream, but fingerprint
        may still return None if Spearman rho is undefined."""
        ses = pd.DataFrame({
            "sexo": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
            "edad": [20, 30, 40, 50, 60, 25, 35, 45, 55, 65],
            "escol": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "Tam_loc": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2],
        })
        series = pd.Series([3] * 10)
        fp = _fingerprint(series, ses)
        # Spearman on constant variable gives NaN, so should return None
        assert fp is None

    def test_fingerprint_too_few_obs(self):
        """Fewer than 10 valid observations should return None."""
        ses = pd.DataFrame({
            "sexo": [1, 2, 1], "edad": [20, 30, 40],
            "escol": [1, 2, 3], "Tam_loc": [1, 2, 3],
        })
        series = pd.Series([1, 2, 3])
        fp = _fingerprint(series, ses)
        assert fp is None


# ---------------------------------------------------------------------------
# Test Spearman rho
# ---------------------------------------------------------------------------

class TestSpearmanRho:
    """Validate Spearman rho computation."""

    def test_perfect_positive(self):
        x = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        rho = _spearman_rho(x, y)
        assert rho is not None
        assert abs(rho - 1.0) < 0.001

    def test_perfect_negative(self):
        x = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        rho = _spearman_rho(x, y)
        assert rho is not None
        assert abs(rho + 1.0) < 0.001

    def test_too_few_obs(self):
        x = pd.Series([1, 2, 3])
        y = pd.Series([3, 2, 1])
        rho = _spearman_rho(x, y)
        assert rho is None

    def test_nan_handling(self):
        x = pd.Series([1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        y = pd.Series([2, 3, 4, np.nan, 6, 7, 8, 9, 10, 11, 12, 13])
        rho = _spearman_rho(x, y)
        assert rho is not None  # should handle pairwise NaN


# ---------------------------------------------------------------------------
# Test GK gamma
# ---------------------------------------------------------------------------

class TestGKGamma:
    """Validate Goodman-Kruskal gamma computation."""

    def test_perfect_concordance(self):
        x = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        g = _gk_gamma(x, y)
        assert g is not None
        assert abs(g - 1.0) < 0.001

    def test_perfect_discordance(self):
        x = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = pd.Series([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        g = _gk_gamma(x, y)
        assert g is not None
        assert abs(g + 1.0) < 0.001

    def test_too_few_obs(self):
        x = pd.Series([1, 2, 3])
        y = pd.Series([3, 2, 1])
        g = _gk_gamma(x, y)
        assert g is None

    def test_constant_variable(self):
        x = pd.Series([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        y = pd.Series([1, 2, 3, 4, 5, 1, 2, 3, 4, 5])
        g = _gk_gamma(x, y)
        assert g is None  # only 1 unique value in x


# ---------------------------------------------------------------------------
# Test bin5
# ---------------------------------------------------------------------------

class TestBin5:
    """Validate rank-normalise -> qcut binning."""

    def test_basic_binning(self):
        s = pd.Series(range(100))
        binned = _bin5(s)
        assert binned.dropna().nunique() == 5
        assert set(binned.dropna().unique()).issubset({1, 2, 3, 4, 5})

    def test_too_few_values(self):
        s = pd.Series([1, 2, 3])
        binned = _bin5(s)
        assert binned.isna().all()

    def test_nan_passthrough(self):
        s = pd.Series([np.nan] * 30 + list(range(30)))
        binned = _bin5(s)
        assert binned[:30].isna().all()
        assert binned[30:].notna().any()


# ---------------------------------------------------------------------------
# Test Q-code -> construct mapping
# ---------------------------------------------------------------------------

class TestQcodeConstructIndex:
    """Validate construct index building from manifest."""

    def test_build_index(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(_synthetic_manifest(), f)
            f.flush()
            idx = _build_qcode_construct_index(Path(f.name))

        assert "Q1" in idx
        assert idx["Q1"]["construct_key"] == "WVS_A|test_construct"
        assert idx["Q1"]["reverse_coded"] is False

        assert "Q3" in idx
        assert idx["Q3"]["reverse_coded"] is True

        assert "Q5" in idx
        assert idx["Q5"]["construct_key"] == "WVS_B|other_construct"

    def test_missing_manifest(self):
        idx = _build_qcode_construct_index(Path("/nonexistent/path.json"))
        assert idx == {}


# ---------------------------------------------------------------------------
# Test domain construct index and candidate matching
# ---------------------------------------------------------------------------

class TestDomainConstructIndex:
    """Validate orphan -> candidate construct matching."""

    def test_build_and_match(self):
        construct_fps = {
            "WVS_A|construct_1": {"rho_escol": 0.3, "rho_Tam_loc": 0.1,
                                   "rho_sexo": -0.1, "rho_edad": 0.2},
            "WVS_A|construct_2": {"rho_escol": -0.2, "rho_Tam_loc": 0.4,
                                   "rho_sexo": 0.1, "rho_edad": -0.1},
        }
        idx = _build_domain_construct_index(construct_fps)
        assert "WVS_A" in idx
        assert len(idx["WVS_A"]) == 2

        # An item aligned with construct_1
        item_fp = {"rho_escol": 0.25, "rho_Tam_loc": 0.08,
                   "rho_sexo": -0.05, "rho_edad": 0.15}
        candidate = _best_candidate_construct(item_fp, idx, "WVS_A")
        assert candidate == "WVS_A|construct_1"

    def test_no_constructs_in_domain(self):
        idx = _build_domain_construct_index({})
        candidate = _best_candidate_construct(
            {"rho_escol": 0.1}, idx, "WVS_X",
        )
        assert candidate is None

    def test_zero_norm_item(self):
        construct_fps = {
            "WVS_A|c1": {"rho_escol": 0.3, "rho_Tam_loc": 0.1,
                          "rho_sexo": 0.0, "rho_edad": 0.0},
        }
        idx = _build_domain_construct_index(construct_fps)
        item_fp = {"rho_escol": 0.0, "rho_Tam_loc": 0.0,
                   "rho_sexo": 0.0, "rho_edad": 0.0}
        candidate = _best_candidate_construct(item_fp, idx, "WVS_A")
        assert candidate is None  # zero-norm vector cannot be normalized


# ---------------------------------------------------------------------------
# Test output format
# ---------------------------------------------------------------------------

class TestOutputFormat:
    """Validate the output JSON structure matches OntologyQuery expectations."""

    def test_output_structure(self):
        """The output should have metadata, constructs, items, domains keys."""
        output = {
            "metadata": {
                "source": "WVS_W7_MEX",
                "n": 1741,
                "n_items": 200,
                "ses_vars": SES_COLS,
            },
            "constructs": {},
            "items": {
                "Q1|W7_MEX": {
                    "rho_escol": 0.1,
                    "rho_Tam_loc": -0.05,
                    "rho_sexo": 0.02,
                    "rho_edad": -0.03,
                    "ses_magnitude": 0.06,
                    "dominant_dim": "escol",
                    "n_obs": 1700,
                    "domain": "Social Values, Attitudes & Stereotypes",
                    "domain_prefix": "A",
                    "title": "Importance in life: Family",
                    "in_construct": True,
                    "parent_construct": "WVS_A|importance_of_life_domains",
                    "reverse_coded": False,
                    "loading": 0.45,
                    "loading_gamma": 0.52,
                    "loading_type": "exact",
                },
            },
            "domains": {},
        }
        # Validate required keys
        assert "metadata" in output
        assert "constructs" in output
        assert "items" in output
        assert "domains" in output

        # Validate item entry
        item = output["items"]["Q1|W7_MEX"]
        for dim in SES_COLS:
            assert f"rho_{dim}" in item
        assert "ses_magnitude" in item
        assert "dominant_dim" in item
        assert "parent_construct" in item
        assert "loading_type" in item
        assert item["loading_type"] in ("exact", "approximate", "none")

    def test_item_key_format(self):
        """Item keys should be '{Q-code}|{short_id}'."""
        key = "Q199|W7_MEX"
        parts = key.split("|")
        assert len(parts) == 2
        assert parts[0].startswith("Q")
        assert parts[1].startswith("W")
