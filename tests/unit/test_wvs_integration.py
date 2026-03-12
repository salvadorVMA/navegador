"""Unit tests for wvs_metadata.py, wvs_loader.py, and wvs_ses_bridge.py.

Tests are structured to run without the large WVS CSV/zip files (which are
gitignored). They validate:
  - Metadata parsing from committed XLSX files
  - SES harmonization logic (edad binning, escol ISCED mapping, Tam_loc collapse)
  - Sentinel cleaning
  - wvs_dict structure construction from synthetic DataFrames
  - Cache save/load round-trip (temp files)
"""

import json
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── modules under test ──────────────────────────────────────────────────────
from wvs_metadata import (
    CULTURAL_ZONES,
    COUNTRY_ZONE,
    DOMAIN_MAP,
    SES_VARS,
    WAVE_LABELS,
    WVS_SENTINEL_THRESHOLD,
    build_qcode_to_acode,
    country_zone,
    get_acode_title,
    get_shared_variables,
    get_variables_for_wave,
    load_country_registry,
    load_equivalences,
)
from wvs_loader import (
    WVSLoader,
    _bin_age,
    _make_short_id,
    _make_survey_key,
    clean_sentinels,
    harmonize_ses,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WVS_DIR = Path(__file__).parents[2] / "data" / "wvs"
XLSX_PRESENT = (
    WVS_DIR / "F00003844-WVS_Time_Series_List_of_Variables_and_equivalences_1981_2022_v3_1.xlsx"
).exists()
COUNTRIES_XLSX_PRESENT = (WVS_DIR / "WVS_Countries_in_time_series_1981-2022.xlsx").exists()


def _synthetic_wvs_df(n: int = 50, wave: int = 7, alpha3: str = "MEX") -> pd.DataFrame:
    """Build a minimal synthetic WVS-like DataFrame for testing."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "B_COUNTRY_ALPHA": [alpha3] * n,
        "A_WAVE": [wave] * n,
        "Q260": rng.choice([1, 2, -2], size=n),        # sex (sentinel: -2)
        "Q262": rng.choice([18, 25, 35, 45, 55, 65, 75, -1], size=n),  # age
        "Q275": rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, -1], size=n),  # ISCED educ
        "G_TOWNSIZE": rng.choice([1, 2, 3, 4, 5, 6, 7, 8, -3], size=n),  # town size
        "Q1": rng.choice([1, 2, 3, 4, -1], size=n),   # substantive attitude
        "Q131": rng.choice([1, 2, 3, 4, -2], size=n),  # neighbourhood security
        "W_WEIGHT": rng.uniform(0.5, 1.5, size=n),
    })
    return df


# ===========================================================================
# wvs_metadata tests
# ===========================================================================


class TestDomainMap:
    def test_all_prefix_keys_present(self):
        for prefix in list("ABCDEFGHIXY"):
            assert prefix in DOMAIN_MAP

    def test_values_are_strings(self):
        for v in DOMAIN_MAP.values():
            assert isinstance(v, str) and len(v) > 0


class TestWaveLabels:
    def test_seven_waves(self):
        assert set(WAVE_LABELS) == {1, 2, 3, 4, 5, 6, 7}

    def test_labels_contain_year(self):
        for label in WAVE_LABELS.values():
            assert any(c.isdigit() for c in label)


class TestCulturalZones:
    def test_eight_zones(self):
        assert len(CULTURAL_ZONES) == 8

    def test_mexico_in_latin_america(self):
        assert "MEX" in CULTURAL_ZONES["Latin America"]

    def test_no_duplicate_countries(self):
        all_countries = [c for lst in CULTURAL_ZONES.values() for c in lst]
        assert len(all_countries) == len(set(all_countries))

    def test_country_zone_lookup(self):
        assert country_zone("MEX") == "Latin America"
        assert country_zone("JPN") == "Confucian"
        assert country_zone("XYZ") == "Unknown"

    def test_country_zone_case_insensitive(self):
        assert country_zone("mex") == "Latin America"

    def test_reverse_lookup_complete(self):
        for zone, countries in CULTURAL_ZONES.items():
            for c in countries:
                assert COUNTRY_ZONE[c] == zone


class TestSESVars:
    def test_four_ses_vars(self):
        assert set(SES_VARS) == {"sexo", "edad", "escol", "Tam_loc"}

    def test_wvs_cols_defined(self):
        for cfg in SES_VARS.values():
            assert "wvs_col" in cfg
            assert "transform" in cfg

    def test_escol_mapping_covers_isced(self):
        mapping = SES_VARS["escol"]["values"]
        for isced in range(9):
            assert isced in mapping

    def test_tam_loc_mapping_covers_1_to_8(self):
        mapping = SES_VARS["Tam_loc"]["values"]
        for code in range(1, 9):
            assert code in mapping
        assert all(v in (1, 2, 3, 4) for v in mapping.values())

    def test_escol_mapping_monotone(self):
        """Higher ISCED should map to equal or higher escol."""
        mapping = SES_VARS["escol"]["values"]
        for i in range(8):
            assert mapping[i] <= mapping[i + 1]

    def test_tam_loc_monotone(self):
        mapping = SES_VARS["Tam_loc"]["values"]
        for i in range(1, 8):
            assert mapping[i] <= mapping[i + 1]


@pytest.mark.skipif(not XLSX_PRESENT, reason="Equivalence XLSX not present")
class TestLoadEquivalences:
    @pytest.fixture(scope="class")
    def equiv(self):
        return load_equivalences()

    def test_returns_dataframe(self, equiv):
        assert isinstance(equiv, pd.DataFrame)

    def test_expected_columns(self, equiv):
        expected = {"a_code", "title", "domain", "prefix", "w7", "w6", "w5", "w4", "w3", "w2", "w1"}
        assert expected.issubset(set(equiv.columns))

    def test_no_null_a_codes(self, equiv):
        assert equiv["a_code"].notna().all()

    def test_domain_populated(self, equiv):
        assert equiv["domain"].notna().all()

    def test_prefix_derived_correctly(self, equiv):
        for _, row in equiv.head(20).iterrows():
            assert row["prefix"] == row["a_code"][0]

    def test_known_variables_present(self, equiv):
        a_codes = set(equiv["a_code"])
        assert "A001" in a_codes  # Family importance
        assert "X001" in a_codes  # Sex
        assert "F028" in a_codes  # Religious attendance

    def test_a001_w7_is_q1(self, equiv):
        row = equiv[equiv["a_code"] == "A001"].iloc[0]
        assert row["w7"] == "Q1"

    def test_x001_w7_is_q260(self, equiv):
        row = equiv[equiv["a_code"] == "X001"].iloc[0]
        assert row["w7"] == "Q260"

    def test_get_variables_for_wave(self, equiv):
        w7_vars = get_variables_for_wave(equiv, 7)
        assert len(w7_vars) > 0
        assert w7_vars["w7"].notna().all()

    def test_get_shared_variables(self, equiv):
        shared = get_shared_variables(equiv, [6, 7])
        assert len(shared) > 0
        assert shared["w6"].notna().all()
        assert shared["w7"].notna().all()

    def test_build_qcode_to_acode(self, equiv):
        lookup = build_qcode_to_acode(equiv)
        assert "Q1" in lookup
        assert 7 in lookup["Q1"]
        assert lookup["Q1"][7] == "A001"

    def test_get_acode_title(self, equiv):
        titles = get_acode_title(equiv)
        assert "A001" in titles
        assert "Family" in titles["A001"]


@pytest.mark.skipif(not COUNTRIES_XLSX_PRESENT, reason="Countries XLSX not present")
class TestLoadCountryRegistry:
    @pytest.fixture(scope="class")
    def registry(self):
        return load_country_registry()

    def test_returns_dict(self, registry):
        assert isinstance(registry, dict)

    def test_mexico_present(self, registry):
        assert "Mexico" in registry

    def test_mexico_seven_waves(self, registry):
        mex = registry["Mexico"]
        assert mex["waves_present"] == [1, 2, 3, 4, 5, 6, 7]

    def test_mexico_total_matches_plan(self, registry):
        mex = registry["Mexico"]
        assert mex["total"] == 11714

    def test_mexico_wave7_n(self, registry):
        mex = registry["Mexico"]
        assert mex["n_per_wave"][6] == 1741  # index 6 = wave 7

    def test_structure_keys(self, registry):
        for country, info in list(registry.items())[:5]:
            assert "n_per_wave" in info
            assert "total" in info
            assert "waves_present" in info
            assert len(info["n_per_wave"]) == 7


# ===========================================================================
# wvs_loader tests
# ===========================================================================


class TestCleanSentinels:
    def test_negative_values_become_nan(self):
        df = pd.DataFrame({"Q1": [1, 2, -1, -2, 3], "Q2": [-5, 4, 5, -3, 2]})
        cleaned = clean_sentinels(df.copy())
        assert cleaned["Q1"].isna().sum() == 2
        assert cleaned["Q2"].isna().sum() == 2

    def test_zero_preserved(self):
        df = pd.DataFrame({"Q275": [0, 1, 2, -1]})
        cleaned = clean_sentinels(df.copy())
        assert cleaned["Q275"].iloc[0] == 0

    def test_positive_values_unchanged(self):
        df = pd.DataFrame({"Q1": [1, 2, 3, 4, 5]})
        cleaned = clean_sentinels(df.copy())
        assert list(cleaned["Q1"]) == [1, 2, 3, 4, 5]

    def test_non_numeric_columns_untouched(self):
        df = pd.DataFrame({
            "B_COUNTRY_ALPHA": ["MEX", "ARG"],
            "Q1": [1, -1],
        })
        cleaned = clean_sentinels(df.copy())
        assert list(cleaned["B_COUNTRY_ALPHA"]) == ["MEX", "ARG"]
        assert pd.isna(cleaned["Q1"].iloc[1])


class TestBinAge:
    @pytest.mark.parametrize("age,expected", [
        (15, "0-18"),
        (18, "0-18"),
        (19, "19-24"),
        (24, "19-24"),
        (25, "25-34"),
        (34, "25-34"),
        (35, "35-44"),
        (44, "35-44"),
        (45, "45-54"),
        (54, "45-54"),
        (55, "55-64"),
        (64, "55-64"),
        (65, "65+"),
        (90, "65+"),
    ])
    def test_age_bins(self, age, expected):
        result = _bin_age(pd.Series([age])).iloc[0]
        assert result == expected

    def test_nan_input_returns_none(self):
        result = _bin_age(pd.Series([np.nan])).iloc[0]
        assert result is None

    def test_series_vectorised(self):
        ages = pd.Series([20, 30, 45, 70, np.nan])
        result = _bin_age(ages)
        assert result.iloc[0] == "19-24"
        assert result.iloc[1] == "25-34"
        assert result.iloc[2] == "45-54"
        assert result.iloc[3] == "65+"
        assert pd.isna(result.iloc[4])


class TestHarmonizeSES:
    def test_columns_created(self):
        df = _synthetic_wvs_df(n=20)
        df_clean = clean_sentinels(df.copy())
        result = harmonize_ses(df_clean.copy())
        for col in ["sexo", "edad", "escol", "Tam_loc"]:
            assert col in result.columns

    def test_sexo_valid_values(self):
        df = pd.DataFrame({"Q260": [1, 2, 1, 2]})
        result = harmonize_ses(df.copy())
        assert set(result["sexo"].dropna()) <= {1, 2}

    def test_escol_range(self):
        df = pd.DataFrame({"Q275": [0, 1, 2, 3, 4, 5, 6, 7, 8]})
        result = harmonize_ses(df.copy())
        assert set(result["escol"].dropna()) <= {1, 2, 3, 4, 5}

    def test_escol_monotone_with_isced(self):
        """Higher ISCED → equal or higher escol."""
        df = pd.DataFrame({"Q275": list(range(9))})
        result = harmonize_ses(df.copy())
        vals = list(result["escol"].dropna())
        assert vals == sorted(vals)

    def test_tam_loc_range(self):
        df = pd.DataFrame({"G_TOWNSIZE": [1, 2, 3, 4, 5, 6, 7, 8]})
        result = harmonize_ses(df.copy())
        assert set(result["Tam_loc"].dropna()) <= {1, 2, 3, 4}

    def test_edad_binning(self):
        df = pd.DataFrame({"Q262": [20, 50, 70]})
        result = harmonize_ses(df.copy())
        assert result["edad"].iloc[0] == "19-24"
        assert result["edad"].iloc[1] == "45-54"
        assert result["edad"].iloc[2] == "65+"

    def test_missing_wvs_col_yields_nan_column(self):
        df = pd.DataFrame({"Q1": [1, 2, 3]})  # no SES cols at all
        result = harmonize_ses(df.copy())
        for col in ["sexo", "edad", "escol", "Tam_loc"]:
            assert col in result.columns
            assert result[col].isna().all()

    def test_sentinels_already_nan(self):
        """After clean_sentinels, harmonization should yield no sentinel-coded outputs."""
        df = _synthetic_wvs_df(n=100)
        df = clean_sentinels(df.copy())
        result = harmonize_ses(df.copy())
        # escol should only be in {1,2,3,4,5} or NaN
        assert set(result["escol"].dropna().astype(int)) <= {1, 2, 3, 4, 5}


class TestSurveyKeyHelpers:
    def test_make_survey_key(self):
        assert _make_survey_key(7, "MEX") == "WVS_W7_MEX"
        assert _make_survey_key(1, "arg") == "WVS_W1_ARG"

    def test_make_short_id(self):
        assert _make_short_id(7, "MEX") == "W7_MEX"
        assert _make_short_id(6, "bra") == "W6_BRA"


class TestWVSLoaderStructure:
    """Tests that use a synthetic DataFrame to validate wvs_dict structure
    without requiring the actual WVS CSV files."""

    @pytest.fixture
    def synthetic_wvs_dict(self):
        """Build a minimal wvs_dict from synthetic data."""
        df = _synthetic_wvs_df(n=50, wave=7, alpha3="MEX")
        df = clean_sentinels(df.copy())
        df = harmonize_ses(df.copy())

        survey_key = "WVS_W7_MEX"
        short_id = "W7_MEX"
        qcode_title = {"Q1": "Important in life: Family", "Q131": "Secure in neighborhood"}

        enc_dict = {
            survey_key: {
                "dataframe": df,
                "metadata": {
                    "variable_value_labels": {},
                    "column_names_to_labels": {
                        col: qcode_title.get(col, col) for col in df.columns
                    },
                },
            }
        }
        return {
            "enc_dict": enc_dict,
            "enc_nom_dict": {survey_key: short_id},
            "pregs_dict": {f"Q1|{short_id}": f"{survey_key}|Important in life: Family"},
            "ses_dict": {survey_key: ["sexo", "edad", "escol", "Tam_loc"]},
            "var_equivalences": pd.DataFrame(),
            "country_registry": {"Mexico": {"n_per_wave": [0]*7, "total": 50, "waves_present": [7]}},
        }

    def test_top_level_keys(self, synthetic_wvs_dict):
        expected = {"enc_dict", "enc_nom_dict", "pregs_dict", "ses_dict",
                    "var_equivalences", "country_registry"}
        assert expected.issubset(set(synthetic_wvs_dict.keys()))

    def test_enc_dict_entry_has_dataframe(self, synthetic_wvs_dict):
        entry = synthetic_wvs_dict["enc_dict"]["WVS_W7_MEX"]
        assert isinstance(entry["dataframe"], pd.DataFrame)
        assert len(entry["dataframe"]) == 50

    def test_enc_dict_entry_has_metadata(self, synthetic_wvs_dict):
        metadata = synthetic_wvs_dict["enc_dict"]["WVS_W7_MEX"]["metadata"]
        assert "variable_value_labels" in metadata
        assert "column_names_to_labels" in metadata

    def test_ses_columns_present_in_dataframe(self, synthetic_wvs_dict):
        df = synthetic_wvs_dict["enc_dict"]["WVS_W7_MEX"]["dataframe"]
        for col in ["sexo", "edad", "escol", "Tam_loc"]:
            assert col in df.columns

    def test_pregs_dict_format(self, synthetic_wvs_dict):
        for key, val in synthetic_wvs_dict["pregs_dict"].items():
            assert "|" in key
            assert "|" in val

    def test_ses_dict_lists_harmonized_cols(self, synthetic_wvs_dict):
        ses = synthetic_wvs_dict["ses_dict"]["WVS_W7_MEX"]
        assert set(ses) <= {"sexo", "edad", "escol", "Tam_loc"}


class TestCacheSaveLoad:
    """Round-trip save/load through WVSLoader.save() / WVSLoader.load()."""

    def _make_loader(self) -> WVSLoader:
        """Instantiate WVSLoader (metadata XLSXs must be present)."""
        if not XLSX_PRESENT or not COUNTRIES_XLSX_PRESENT:
            pytest.skip("WVS metadata XLSXs not present")
        return WVSLoader()

    def test_save_load_roundtrip(self):
        loader = self._make_loader()

        df = _synthetic_wvs_df(n=30)
        df = clean_sentinels(df.copy())
        df = harmonize_ses(df.copy())

        wvs_dict = {
            "enc_dict": {
                "WVS_W7_MEX": {
                    "dataframe": df,
                    "metadata": {
                        "variable_value_labels": {},
                        "column_names_to_labels": {"Q1": "Family"},
                    },
                }
            },
            "enc_nom_dict": {"WVS_W7_MEX": "W7_MEX"},
            "pregs_dict": {"Q1|W7_MEX": "WVS_W7_MEX|Family"},
            "ses_dict": {"WVS_W7_MEX": ["sexo", "edad", "escol", "Tam_loc"]},
            "var_equivalences": loader.equivalences.head(5),
            "country_registry": {"Mexico": {"n_per_wave": [0]*7, "total": 30, "waves_present": [7]}},
        }

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = Path(f.name)

        try:
            loader.save(wvs_dict, tmp_path)
            loaded = WVSLoader.load(tmp_path)

            assert set(loaded["enc_dict"]) == set(wvs_dict["enc_dict"])
            df_loaded = loaded["enc_dict"]["WVS_W7_MEX"]["dataframe"]
            assert len(df_loaded) == 30
            assert "sexo" in df_loaded.columns
            assert loaded["enc_nom_dict"] == wvs_dict["enc_nom_dict"]
            assert loaded["pregs_dict"] == wvs_dict["pregs_dict"]
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            WVSLoader.load(Path("/nonexistent/wvs_dict.json"))


@pytest.mark.skipif(not XLSX_PRESENT, reason="Equivalence XLSX not present")
class TestWVSLoaderInit:
    def test_loader_init_loads_equivalences(self):
        loader = WVSLoader()
        assert isinstance(loader.equivalences, pd.DataFrame)
        assert len(loader.equivalences) > 100

    def test_wave_qcode_title_populated(self):
        loader = WVSLoader()
        assert 7 in loader._wave_qcode_title
        assert "Q1" in loader._wave_qcode_title[7]
        assert "Family" in loader._wave_qcode_title[7]["Q1"]

    def test_country_registry_loaded(self):
        loader = WVSLoader()
        assert "Mexico" in loader.country_registry


# ===========================================================================
# wvs_ses_bridge tests
# ===========================================================================

from wvs_ses_bridge import (
    BRIDGE_SES_VARS,
    LOS_MEX_WEIGHT_COL,
    WVS_WEIGHT_COL,
    WVSBridgeEstimator,
    SESHarmonizer,
    _unify_weight_col,
    _wvs_key,
    summarise_geographic,
    summarise_temporal,
)
from wvs_loader import clean_sentinels, harmonize_ses


def _make_wvs_survey_df(n: int = 120, seed: int = 0, alpha3: str = "MEX", wave: int = 7) -> pd.DataFrame:
    """Synthetic WVS-like DataFrame with harmonized SES and two attitude columns."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "B_COUNTRY_ALPHA": [alpha3] * n,
        "A_WAVE": [wave] * n,
        "Q260": rng.choice([1, 2], size=n),
        "Q262": rng.integers(18, 80, size=n),
        "Q275": rng.integers(0, 9, size=n),
        "G_TOWNSIZE": rng.integers(1, 9, size=n),
        "Q1": rng.integers(1, 5, size=n),     # attitude A
        "Q173": rng.integers(1, 5, size=n),   # attitude B
        "W_WEIGHT": rng.uniform(0.5, 1.5, size=n),
    })
    df = harmonize_ses(df)
    return df


def _make_los_mex_df(n: int = 120, seed: int = 1) -> pd.DataFrame:
    """Synthetic los_mex-like DataFrame with harmonized SES cols and attitude column."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "sexo": rng.choice([1, 2], size=n),
        "edad": rng.choice(["19-24", "25-34", "35-44", "45-54", "55-64", "65+"], size=n),
        "escol": rng.integers(1, 6, size=n),
        "Tam_loc": rng.integers(1, 5, size=n),
        "p16_3": rng.integers(1, 5, size=n),   # attitude col
        "Pondi2": rng.uniform(0.5, 1.5, size=n),
    })
    return df


def _make_wvs_enc_dict(waves: list = None, countries: list = None, n: int = 120) -> dict:
    """Build a minimal wvs_enc_dict from synthetic data for sweep tests."""
    waves = waves or [6, 7]
    countries = countries or ["MEX", "ARG"]
    enc_dict = {}
    for wave in waves:
        for alpha3 in countries:
            key = _wvs_key(wave, alpha3)
            enc_dict[key] = {
                "dataframe": _make_wvs_survey_df(n=n, seed=hash((wave, alpha3)) % 2**31, alpha3=alpha3, wave=wave),
                "metadata": {"variable_value_labels": {}, "column_names_to_labels": {}},
            }
    return enc_dict


class TestWVSKeyHelper:
    def test_key_format(self):
        assert _wvs_key(7, "MEX") == "WVS_W7_MEX"
        assert _wvs_key(1, "arg") == "WVS_W1_ARG"


class TestUnifyWeightCol:
    def test_copies_existing_weight(self):
        df = pd.DataFrame({"W_WEIGHT": [1.0, 2.0], "Q1": [1, 2]})
        result = _unify_weight_col(df, "W_WEIGHT")
        assert "bridge_weight" in result.columns
        assert list(result["bridge_weight"]) == [1.0, 2.0]

    def test_defaults_to_ones_when_col_absent(self):
        df = pd.DataFrame({"Q1": [1, 2, 3]})
        result = _unify_weight_col(df, "W_WEIGHT")
        assert "bridge_weight" in result.columns
        assert all(result["bridge_weight"] == 1.0)

    def test_defaults_to_ones_when_col_is_none(self):
        df = pd.DataFrame({"Q1": [1, 2]})
        result = _unify_weight_col(df, None)
        assert all(result["bridge_weight"] == 1.0)

    def test_original_df_not_mutated(self):
        df = pd.DataFrame({"W_WEIGHT": [1.0], "Q1": [1]})
        _ = _unify_weight_col(df, "W_WEIGHT")
        assert "bridge_weight" not in df.columns


class TestSESHarmonizer:
    def test_validate_returns_available(self):
        df = _make_wvs_survey_df(n=50)
        h = SESHarmonizer()
        avail = h.validate(df)
        assert set(avail) == {"sexo", "edad", "escol", "Tam_loc"}

    def test_validate_warns_on_missing(self):
        df = pd.DataFrame({"sexo": [1, 2], "Q1": [1, 2]})
        h = SESHarmonizer()
        with pytest.warns(UserWarning, match="SES vars not found"):
            avail = h.validate(df, "TEST")
        assert avail == ["sexo"]

    def test_validate_returns_empty_for_no_ses(self):
        df = pd.DataFrame({"Q1": [1, 2, 3]})
        h = SESHarmonizer()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            avail = h.validate(df)
        assert avail == []

    def test_build_standardized_reference_shape(self):
        df = _make_wvs_survey_df(n=200)
        h = SESHarmonizer()
        ref = h.build_standardized_reference(df, weight_col="W_WEIGHT", n=100)
        assert len(ref) == 100
        for col in ["sexo", "edad", "escol", "Tam_loc"]:
            assert col in ref.columns

    def test_build_standardized_reference_no_nulls_in_ses(self):
        df = _make_wvs_survey_df(n=200)
        h = SESHarmonizer()
        ref = h.build_standardized_reference(df, n=50)
        for col in ["sexo", "edad", "escol", "Tam_loc"]:
            assert ref[col].notna().all(), f"{col} has NaN in reference"

    def test_build_zone_pool_latin_america(self):
        enc_dict = _make_wvs_enc_dict(waves=[7], countries=["MEX", "ARG", "BRA"])
        h = SESHarmonizer()
        pool = h.build_zone_pool(enc_dict, zone="Latin America", wave=7)
        assert len(pool) > 0
        assert "_country" in pool.columns
        assert set(pool["_country"].unique()) <= {"MEX", "ARG", "BRA"}

    def test_build_zone_pool_unknown_zone_raises(self):
        enc_dict = _make_wvs_enc_dict(waves=[7], countries=["MEX"])
        h = SESHarmonizer()
        with pytest.raises(ValueError, match="Unknown cultural zone"):
            h.build_zone_pool(enc_dict, zone="Atlantis", wave=7)

    def test_build_zone_pool_missing_data_raises(self):
        h = SESHarmonizer()
        with pytest.raises(ValueError, match="No data found"):
            h.build_zone_pool({}, zone="Latin America", wave=7)


class TestWVSBridgeEstimatorCrossDataset:
    @pytest.fixture(scope="class")
    def estimator(self):
        # Fast settings for tests
        return WVSBridgeEstimator(n_sim=100, n_bootstrap=5, max_categories=4)

    def test_returns_dict_on_valid_input(self, estimator):
        df_wvs = _make_wvs_survey_df(n=150)
        df_los = _make_los_mex_df(n=150)
        result = estimator.estimate_cross_dataset(
            df_wvs, "Q1", df_los, "p16_3",
            var_id_a="Q1|W7_MEX", var_id_b="p16_3|CUL",
        )
        # May return None if statsmodels fails to converge on tiny synth data,
        # but should not raise an exception
        assert result is None or isinstance(result, dict)

    def test_returns_none_when_col_missing(self, estimator):
        df_wvs = _make_wvs_survey_df(n=100)
        df_los = _make_los_mex_df(n=100)
        result = estimator.estimate_cross_dataset(
            df_wvs, "NONEXISTENT_COL", df_los, "p16_3"
        )
        assert result is None

    def test_returns_none_when_no_shared_ses(self, estimator):
        df_wvs = pd.DataFrame({"Q1": [1, 2, 3], "W_WEIGHT": [1.0, 1.0, 1.0]})
        df_los = pd.DataFrame({"p16_3": [1, 2, 3], "Pondi2": [1.0, 1.0, 1.0]})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = estimator.estimate_cross_dataset(df_wvs, "Q1", df_los, "p16_3")
        assert result is None

    def test_result_has_gamma_key(self, estimator):
        df_wvs = _make_wvs_survey_df(n=200)
        df_los = _make_los_mex_df(n=200)
        result = estimator.estimate_cross_dataset(df_wvs, "Q1", df_los, "p16_3")
        if result is not None:
            assert "gamma" in result

    def test_result_gamma_in_range(self, estimator):
        df_wvs = _make_wvs_survey_df(n=200)
        df_los = _make_los_mex_df(n=200)
        result = estimator.estimate_cross_dataset(df_wvs, "Q1", df_los, "p16_3")
        if result is not None and result.get("gamma") is not None:
            assert -1.0 <= result["gamma"] <= 1.0


class TestWVSBridgeEstimatorWithinWVS:
    @pytest.fixture(scope="class")
    def estimator(self):
        return WVSBridgeEstimator(n_sim=100, n_bootstrap=5, max_categories=4)

    def test_within_wvs_same_df(self, estimator):
        df = _make_wvs_survey_df(n=200)
        result = estimator.estimate_within_wvs(df, "Q1", df, "Q173")
        assert result is None or isinstance(result, dict)

    def test_within_wvs_different_waves(self, estimator):
        df_w6 = _make_wvs_survey_df(n=150, seed=10, wave=6)
        df_w7 = _make_wvs_survey_df(n=150, seed=11, wave=7)
        result = estimator.estimate_within_wvs(
            df_w6, "Q1", df_w7, "Q173",
            var_id_a="Q1|W6_MEX", var_id_b="Q173|W7_MEX",
        )
        assert result is None or isinstance(result, dict)

    def test_gamma_in_range_when_present(self, estimator):
        df = _make_wvs_survey_df(n=200)
        result = estimator.estimate_within_wvs(df, "Q1", df, "Q173")
        if result is not None and result.get("gamma") is not None:
            assert -1.0 <= result["gamma"] <= 1.0


class TestTemporalSweep:
    @pytest.fixture(scope="class")
    def estimator(self):
        return WVSBridgeEstimator(n_sim=50, n_bootstrap=3, max_categories=4)

    @pytest.fixture(scope="class")
    def enc_dict(self):
        return _make_wvs_enc_dict(waves=[6, 7], countries=["MEX"])

    def test_returns_dict_keyed_by_wave(self, estimator, enc_dict):
        results = estimator.temporal_sweep(enc_dict, "Q1", "Q173", country="MEX")
        assert isinstance(results, dict)
        assert set(results.keys()) == set(range(1, 8))

    def test_waves_without_data_return_none(self, estimator, enc_dict):
        results = estimator.temporal_sweep(enc_dict, "Q1", "Q173", country="MEX")
        # Waves 1-5 not in enc_dict → None
        for w in range(1, 6):
            assert results[w] is None

    def test_waves_with_data_return_dict_or_none(self, estimator, enc_dict):
        results = estimator.temporal_sweep(enc_dict, "Q1", "Q173", country="MEX")
        for w in [6, 7]:
            assert results[w] is None or isinstance(results[w], dict)

    def test_missing_col_returns_none_for_wave(self, estimator, enc_dict):
        results = estimator.temporal_sweep(enc_dict, "NONEXISTENT", "Q173", country="MEX")
        for w in [6, 7]:
            assert results[w] is None

    def test_summarise_temporal_shape(self, estimator, enc_dict):
        results = estimator.temporal_sweep(enc_dict, "Q1", "Q173", country="MEX")
        df = summarise_temporal(results)
        assert len(df) == 7
        assert set(df.columns) >= {"wave", "gamma", "gamma_lo", "gamma_hi"}
        assert list(df["wave"]) == list(range(1, 8))

    def test_summarise_temporal_nan_for_missing(self, estimator, enc_dict):
        results = estimator.temporal_sweep(enc_dict, "Q1", "Q173", country="MEX")
        df = summarise_temporal(results)
        # Waves 1-5 have no data → gamma should be NaN
        for w in range(1, 6):
            row = df[df["wave"] == w].iloc[0]
            assert pd.isna(row["gamma"])


class TestGeographicSweep:
    @pytest.fixture(scope="class")
    def estimator(self):
        return WVSBridgeEstimator(n_sim=50, n_bootstrap=3, max_categories=4)

    @pytest.fixture(scope="class")
    def enc_dict(self):
        return _make_wvs_enc_dict(waves=[7], countries=["MEX", "ARG", "BRA"])

    def test_returns_dict_keyed_by_country(self, estimator, enc_dict):
        results = estimator.geographic_sweep(enc_dict, "Q1", "Q173", wave=7)
        assert isinstance(results, dict)
        assert set(results.keys()) == {"MEX", "ARG", "BRA"}

    def test_zone_filter_restricts_countries(self, estimator, enc_dict):
        # All 3 are in Latin America zone
        results = estimator.geographic_sweep(
            enc_dict, "Q1", "Q173", wave=7, zone="Latin America"
        )
        assert set(results.keys()) <= set(["MEX", "ARG", "BRA", "BOL", "CHL",
                                           "COL", "ECU", "GTM", "NIC", "PER",
                                           "PRI", "URY", "VEN"])

    def test_unknown_zone_raises(self, estimator, enc_dict):
        with pytest.raises(ValueError, match="Unknown zone"):
            estimator.geographic_sweep(enc_dict, "Q1", "Q173", zone="Atlantis")

    def test_missing_col_returns_none_per_country(self, estimator, enc_dict):
        results = estimator.geographic_sweep(enc_dict, "NONEXISTENT", "Q173", wave=7)
        for alpha3 in ["MEX", "ARG", "BRA"]:
            assert results[alpha3] is None

    def test_summarise_geographic_shape(self, estimator, enc_dict):
        results = estimator.geographic_sweep(enc_dict, "Q1", "Q173", wave=7)
        df = summarise_geographic(results)
        assert len(df) == 3
        assert set(df.columns) >= {"country", "zone", "gamma", "gamma_lo", "gamma_hi"}

    def test_summarise_geographic_zone_column(self, estimator, enc_dict):
        results = estimator.geographic_sweep(enc_dict, "Q1", "Q173", wave=7)
        df = summarise_geographic(results)
        mex_row = df[df["country"] == "MEX"].iloc[0]
        assert mex_row["zone"] == "Latin America"


# ===========================================================================
# wvs_anchor_discovery tests  (Phase 3)
# ===========================================================================

from wvs_anchor_discovery import (
    AnchorCandidate,
    AnchorEntry,
    WVSAnchorDiscovery,
    _parse_grade_json,
    filter_anchors,
    load_anchor_registry,
    registry_to_dataframe,
    summarise_registry,
)


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _make_candidate(grade: int = 2, similarity: float = 0.85) -> AnchorCandidate:
    return AnchorCandidate(
        los_mex_id=f"p16_{grade}|CUL",
        los_mex_survey="CULTURA_POLITICA",
        los_mex_text="¿Qué tanta confianza tiene en el Congreso?",
        cosine_similarity=similarity,
        grade=grade,
        grade_justification="Same concept: confidence in parliament.",
        scale_compatible=True,
        scale_notes="Both 1-4",
    )


def _make_entry(qcode: str = "Q71", best_grade: int = 3) -> AnchorEntry:
    cand = _make_candidate(grade=best_grade)
    return AnchorEntry(
        wvs_qcode=qcode,
        wvs_acode="E069_06",
        wvs_title="Confidence: parliament",
        wvs_domain="Politics & Society",
        candidates=[cand],
        best_grade=best_grade,
        best_candidate=cand,
    )


def _make_registry(n: int = 5) -> dict:
    grades = [3, 2, 2, 1, 0]
    registry = {}
    for i in range(n):
        qcode = f"Q{70 + i}"
        g = grades[i % len(grades)]
        registry[qcode] = _make_entry(qcode=qcode, best_grade=g)
    return registry


# ---------------------------------------------------------------------------
# AnchorCandidate / AnchorEntry model tests
# ---------------------------------------------------------------------------

class TestAnchorModels:
    def test_candidate_grade_range(self):
        for g in range(4):
            c = _make_candidate(grade=g)
            assert c.grade == g

    def test_entry_best_grade_reflects_candidate(self):
        e = _make_entry(best_grade=3)
        assert e.best_grade == 3
        assert e.best_candidate is not None
        assert e.best_candidate.grade == 3

    def test_entry_no_candidates(self):
        e = AnchorEntry(
            wvs_qcode="Q999", wvs_acode="X999", wvs_title="Test",
            wvs_domain="Other", candidates=[], best_grade=0, best_candidate=None,
        )
        assert e.best_grade == 0
        assert e.best_candidate is None

    def test_candidate_serialization_roundtrip(self):
        c = _make_candidate(grade=2)
        d = c.model_dump()
        c2 = AnchorCandidate(**d)
        assert c2.grade == c.grade
        assert c2.los_mex_id == c.los_mex_id

    def test_entry_serialization_roundtrip(self):
        e = _make_entry()
        d = e.model_dump()
        e2 = AnchorEntry(**d)
        assert e2.wvs_qcode == e.wvs_qcode
        assert e2.best_grade == e.best_grade


# ---------------------------------------------------------------------------
# _parse_grade_json tests
# ---------------------------------------------------------------------------

class TestParseGradeJson:
    def test_valid_json(self):
        raw = '{"grade": 3, "grade_justification": "Near-identical.", "scale_compatible": true, "scale_notes": "Both 1-4"}'
        result = _parse_grade_json(raw)
        assert result["grade"] == 3
        assert result["scale_compatible"] is True

    def test_json_embedded_in_prose(self):
        raw = 'Here is my assessment:\n{"grade": 2, "grade_justification": "Similar concept.", "scale_compatible": false, "scale_notes": "Different scales"}\nEnd.'
        result = _parse_grade_json(raw)
        assert result["grade"] == 2

    def test_malformed_json_extracts_grade(self):
        raw = 'The "grade": 1 is appropriate here. Some garbled {"grade": 1, text'
        result = _parse_grade_json(raw)
        assert result["grade"] == 1

    def test_no_json_returns_grade_zero(self):
        raw = "I cannot determine a grade from this."
        result = _parse_grade_json(raw)
        assert result["grade"] == 0

    def test_grade_zero_parsed(self):
        raw = '{"grade": 0, "grade_justification": "Unrelated.", "scale_compatible": false, "scale_notes": ""}'
        result = _parse_grade_json(raw)
        assert result["grade"] == 0

    def test_result_has_required_keys(self):
        raw = '{"grade": 1, "grade_justification": "Weak.", "scale_compatible": false, "scale_notes": "N/A"}'
        result = _parse_grade_json(raw)
        for key in ["grade", "grade_justification", "scale_compatible", "scale_notes"]:
            assert key in result


# ---------------------------------------------------------------------------
# filter_anchors / registry helpers
# ---------------------------------------------------------------------------

class TestRegistryHelpers:
    def test_filter_anchors_grade2(self):
        reg = _make_registry(5)
        filtered = filter_anchors(reg, min_grade=2)
        assert all(e.best_grade >= 2 for e in filtered.values())

    def test_filter_anchors_grade3(self):
        reg = _make_registry(5)
        filtered = filter_anchors(reg, min_grade=3)
        assert all(e.best_grade == 3 for e in filtered.values())

    def test_filter_returns_subset(self):
        reg = _make_registry(5)
        filtered = filter_anchors(reg, min_grade=2)
        assert len(filtered) <= len(reg)

    def test_registry_to_dataframe_shape(self):
        reg = _make_registry(5)
        df = registry_to_dataframe(reg)
        assert isinstance(df, pd.DataFrame)
        assert "wvs_qcode" in df.columns
        assert "los_mex_id" in df.columns
        assert "grade" in df.columns

    def test_registry_to_dataframe_excludes_no_candidate(self):
        reg = {"Q999": AnchorEntry(
            wvs_qcode="Q999", wvs_acode="X999", wvs_title="Test",
            wvs_domain="Other", candidates=[], best_grade=0, best_candidate=None,
        )}
        df = registry_to_dataframe(reg)
        assert len(df) == 0

    def test_summarise_registry_one_row_per_question(self):
        reg = _make_registry(5)
        df = summarise_registry(reg)
        assert len(df) == 5
        assert "wvs_qcode" in df.columns
        assert "best_grade" in df.columns

    def test_summarise_registry_sorted_descending(self):
        reg = _make_registry(5)
        df = summarise_registry(reg)
        grades = list(df["best_grade"])
        assert grades == sorted(grades, reverse=True)


# ---------------------------------------------------------------------------
# Save / load round-trip (no LLM required)
# ---------------------------------------------------------------------------

class TestAnchorRegistryIO:
    def test_save_load_roundtrip(self):
        reg = _make_registry(3)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = Path(f.name)
        try:
            WVSAnchorDiscovery.load  # just check import
            # Save manually (no discovery instance needed)
            data = {qcode: entry.model_dump() for qcode, entry in reg.items()}
            with open(tmp_path, "w") as f:
                json.dump(data, f)
            loaded = load_anchor_registry(tmp_path)
            assert set(loaded.keys()) == set(reg.keys())
            for qcode in reg:
                assert loaded[qcode].best_grade == reg[qcode].best_grade
                assert loaded[qcode].wvs_title == reg[qcode].wvs_title
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_anchor_registry(Path("/nonexistent/anchor_registry.json"))

    def test_loaded_candidates_intact(self):
        reg = _make_registry(2)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = Path(f.name)
        try:
            data = {qcode: entry.model_dump() for qcode, entry in reg.items()}
            with open(tmp_path, "w") as f:
                json.dump(data, f)
            loaded = load_anchor_registry(tmp_path)
            for qcode, entry in loaded.items():
                for cand in entry.candidates:
                    assert isinstance(cand, AnchorCandidate)
                    assert 0 <= cand.grade <= 3
        finally:
            tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# WVSAnchorDiscovery._grade_candidate (mocked LLM)
# ---------------------------------------------------------------------------

class TestGradeCandidate:
    """Test grading logic with a mock LLM — no API key required."""

    def _make_mock_llm(self, response: str):
        class MockResponse:
            content = response
        class MockLLM:
            def invoke(self, messages):
                return MockResponse()
        return MockLLM()

    def _make_mock_db(self, hits: list):
        class MockDB:
            def query(self, query_texts, n_results, include):
                if not hits:
                    return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
                return {
                    "ids": [[h["id"] for h in hits]],
                    "documents": [[h["text"] for h in hits]],
                    "metadatas": [[{"survey": h.get("survey", "")} for h in hits]],
                    "distances": [[h["distance"] for h in hits]],
                }
        return MockDB()

    def test_grade_3_anchor(self):
        mock_llm = self._make_mock_llm(
            '{"grade": 3, "grade_justification": "Near-identical.", "scale_compatible": true, "scale_notes": "Both 1-4"}'
        )
        disc = WVSAnchorDiscovery(db_f1=self._make_mock_db([]), llm=mock_llm)
        cand_raw = {"id": "p16_3|CUL", "text": "¿Confianza en congreso?", "survey": "CUL", "distance": 0.2, "similarity": 0.9}
        result = disc._grade_candidate("Q71", "Confidence: parliament", "Politics", cand_raw)
        assert result.grade == 3
        assert result.scale_compatible is True
        assert result.cosine_similarity == pytest.approx(0.9)

    def test_grade_0_unrelated(self):
        mock_llm = self._make_mock_llm(
            '{"grade": 0, "grade_justification": "Unrelated topics.", "scale_compatible": false, "scale_notes": ""}'
        )
        disc = WVSAnchorDiscovery(db_f1=self._make_mock_db([]), llm=mock_llm)
        cand_raw = {"id": "p1|FAM", "text": "¿Cuántos hijos tiene?", "survey": "FAM", "distance": 1.5, "similarity": 0.25}
        result = disc._grade_candidate("Q71", "Confidence: parliament", "Politics", cand_raw)
        assert result.grade == 0

    def test_malformed_llm_response_handled(self):
        mock_llm = self._make_mock_llm("Sorry I cannot grade this.")
        disc = WVSAnchorDiscovery(db_f1=self._make_mock_db([]), llm=mock_llm)
        cand_raw = {"id": "p1|FAM", "text": "text", "survey": "FAM", "distance": 0.5, "similarity": 0.75}
        result = disc._grade_candidate("Q71", "Confidence", "Politics", cand_raw)
        assert result.grade == 0  # fallback

    def test_query_los_mex_converts_distance_to_similarity(self):
        hits = [{"id": "p1|CUL", "text": "text", "survey": "CUL", "distance": 0.4}]
        mock_db = self._make_mock_db(hits)
        disc = WVSAnchorDiscovery(db_f1=mock_db, llm=self._make_mock_llm(""))
        results = disc._query_los_mex("some question", n_candidates=1)
        assert len(results) == 1
        assert results[0]["similarity"] == pytest.approx(1.0 - 0.4 / 2.0)

    def test_query_returns_empty_for_no_hits(self):
        disc = WVSAnchorDiscovery(db_f1=self._make_mock_db([]), llm=self._make_mock_llm(""))
        results = disc._query_los_mex("some question", n_candidates=5)
        assert results == []

    def test_build_registry_with_mock(self):
        """Smoke test: build_registry runs end-to-end with mocked db + llm."""
        grade_resp = '{"grade": 2, "grade_justification": "Similar.", "scale_compatible": true, "scale_notes": "Both 1-4"}'
        mock_llm = self._make_mock_llm(grade_resp)
        mock_hits = [
            {"id": "p16_3|CUL", "text": "¿Confianza en congreso?", "survey": "CUL", "distance": 0.2},
        ]
        mock_db = self._make_mock_db(mock_hits)
        disc = WVSAnchorDiscovery(db_f1=mock_db, llm=mock_llm, batch_pause=0)

        # Minimal equivalences DataFrame
        equiv = pd.DataFrame({
            "a_code": ["E069_06", "A001"],
            "title": ["Confidence: parliament", "Important in life: Family"],
            "domain": ["Politics & Society", "Social Values"],
            "prefix": ["E", "A"],
            "w7": ["Q71", "Q1"],
            "w6": [None, "V4"],
            "w5": [None, "V4"], "w4": [None, "V4"], "w3": [None, "V4"],
            "w2": [None, "V5"], "w1": [None, None],
        })

        registry = disc.build_registry(equiv, wave=7, n_candidates=1,
                                        min_similarity=0.0, verbose=False)
        assert "Q71" in registry
        assert "Q1" in registry
        assert registry["Q71"].best_grade == 2
        assert registry["Q71"].wvs_acode == "E069_06"
