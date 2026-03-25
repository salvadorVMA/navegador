"""WVS data loader: load Wave 7 and/or time-series CSVs, clean sentinels,
harmonize SES variables, and build a wvs_dict parallel to los_mex_dict.

The WVS zip files are large and gitignored.  This module handles three cases:
  1. Extracted CSV files present in data/wvs/
  2. Zip files present in data/wvs/ — read the CSV directly from the zip
  3. Neither present — raise a helpful FileNotFoundError

wvs_dict structure (mirrors los_mex_dict)
-----------------------------------------
{
    'enc_dict': {
        'WVS_W7_MEX': {
            'dataframe': pd.DataFrame,    # individual-level rows
            'metadata': {
                'variable_value_labels': {},   # var → {code: label}; sparse for WVS
                'column_names_to_labels': {},  # Q-code → A-series title
            },
        },
        ...  # one entry per (wave, country)
    },
    'enc_nom_dict':  {survey_key: short_id},
    'pregs_dict':    {'Q-code|short_id': 'survey_key|title'},
    'ses_dict':      {survey_key: [SES col names]},
    'var_equivalences': pd.DataFrame,   # from wvs_metadata.load_equivalences()
    'country_registry': dict,           # from wvs_metadata.load_country_registry()
}

Usage
-----
    from wvs_loader import WVSLoader
    loader = WVSLoader()
    wvs_dict = loader.build_wvs_dict(
        waves=[7],             # or list of wave numbers 1-7
        countries=['MEX'],     # ISO alpha-3; None = all countries
    )
    # or for the time series:
    wvs_dict = loader.build_wvs_dict(waves=list(range(1, 8)), countries=['MEX'])
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from wvs_metadata import (
    CULTURAL_ZONES,
    DOMAIN_MAP,
    SES_VARS,
    WAVE_LABELS,
    WVS_SENTINEL_THRESHOLD,
    build_qcode_to_acode,
    get_acode_title,
    load_country_registry,
    load_equivalences,
)

# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

_DEFAULT_WVS_DIR = Path(__file__).parent / "data" / "wvs"

# Known zip filenames (may vary by version; check data/wvs/ if not found)
_WAVE7_ZIP_PATTERN = "WVS_Cross-National_Wave_7_csv"
_TIMESERIES_ZIP_PATTERN = "WVS_Time_Series"

# Mexico numeric country code in WVS (B_COUNTRY column)
_MEXICO_COUNTRY_CODE = 484

# WVS Wave 7: column identifying country and wave
_COL_COUNTRY_ALPHA = "B_COUNTRY_ALPHA"
_COL_COUNTRY_NUM = "B_COUNTRY"
_COL_WAVE = "A_WAVE"

# Time-series CSV uses different column names from Wave 7
_TS_COL_WAVE = "S002VS"
_TS_COL_COUNTRY_ALPHA = "COUNTRY_ALPHA"
_TS_COL_COUNTRY_NUM = "S003"
_TS_WEIGHT_COL = "S017"

# Time-series SES column names (A-code equivalents of Wave 7 Q-codes)
_TS_SES_RENAMES: dict[str, str] = {
    "X001": "Q260",       # sex
    "X003": "Q262",       # age (continuous)
    "X025": "Q275",       # education ISCED
    "X049": "G_TOWNSIZE", # settlement size
}

# SES column names produced by harmonization
_HARMONIZED_SES_COLS = list(SES_VARS.keys())  # ['sexo', 'edad', 'escol', 'Tam_loc']


# ---------------------------------------------------------------------------
# Internal helpers: file discovery
# ---------------------------------------------------------------------------

def _find_csv_in_zip(zip_path: Path) -> str:
    """Return the name of the first .csv file found inside a zip archive."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if not csv_names:
        raise FileNotFoundError(f"No CSV found inside {zip_path}")
    return csv_names[0]


def _find_wvs_file(wvs_dir: Path, pattern: str) -> Optional[Path]:
    """Find a WVS data file (CSV or zip) matching a filename pattern."""
    for ext in (".csv", ".zip"):
        matches = sorted(wvs_dir.glob(f"*{pattern}*{ext}"))
        if matches:
            return matches[0]
    return None


def _load_csv_from_source(source: Path) -> pd.DataFrame:
    """Load a WVS CSV, handling both direct CSV files and zip archives."""
    if source.suffix.lower() == ".zip":
        csv_name = _find_csv_in_zip(source)
        with zipfile.ZipFile(source, "r") as zf:
            with zf.open(csv_name) as f:
                return pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"), low_memory=False)
    return pd.read_csv(source, low_memory=False)


# ---------------------------------------------------------------------------
# Internal helpers: SES harmonization
# ---------------------------------------------------------------------------

def _bin_age(series: pd.Series) -> pd.Series:
    """Bin continuous WVS age (Q262) into los_mex edad categories.

    Matches ses_analysis.AnalysisConfig.categorize_age exactly:
    <=18 → '0-18', <=24 → '19-24', <=34 → '25-34', <=44 → '35-44',
    <=54 → '45-54', <=64 → '55-64', >64 → '65+'
    """
    def _cat(v):
        if pd.isna(v):
            return None
        v = float(v)
        if v <= 18:
            return "0-18"
        if v <= 24:
            return "19-24"
        if v <= 34:
            return "25-34"
        if v <= 44:
            return "35-44"
        if v <= 54:
            return "45-54"
        if v <= 64:
            return "55-64"
        return "65+"

    return series.apply(_cat)


def _map_values(series: pd.Series, mapping: dict) -> pd.Series:
    """Map integer codes to harmonized values; unmapped → NaN."""
    return series.map(mapping)


def harmonize_ses(df: pd.DataFrame) -> pd.DataFrame:
    """Add harmonized SES columns to a WVS DataFrame.

    Creates columns: sexo, edad, escol, Tam_loc
    matching the encoding used by los_mex SES variables.

    Parameters
    ----------
    df : pd.DataFrame
        WVS individual-level data (already sentinel-cleaned).

    Returns
    -------
    df with new SES columns added (originals preserved).
    """
    new_cols: dict[str, pd.Series] = {}
    for los_mex_col, cfg in SES_VARS.items():
        wvs_col = cfg["wvs_col"]
        if wvs_col not in df.columns:
            new_cols[los_mex_col] = pd.Series(np.nan, index=df.index)
            continue

        src = df[wvs_col]

        if cfg["transform"] == "direct":
            new_cols[los_mex_col] = _map_values(src, cfg["values"])
        elif cfg["transform"] == "bin_age":
            new_cols[los_mex_col] = _bin_age(src)
        elif cfg["transform"] == "continuous_age":
            age = pd.to_numeric(src, errors="coerce")
            new_cols[los_mex_col] = age.where(age.between(15, 100))
        elif cfg["transform"] in ("isced_to_5", "collapse_4"):
            new_cols[los_mex_col] = _map_values(
                src.astype("Int64", errors="ignore"), cfg["values"]
            )

    return pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)


# ---------------------------------------------------------------------------
# Internal helpers: sentinel cleaning
# ---------------------------------------------------------------------------

def clean_sentinels(df: pd.DataFrame) -> pd.DataFrame:
    """Replace WVS sentinel codes (values < 0) with NaN.

    WVS uses: -1=Don't know, -2=No answer, -3=Not applicable,
              -4=Not asked in this country, -5=Missing.
    All are negative; 0 is a valid value in some variables (e.g. Q275 ISCED=0).
    """
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].where(df[num_cols] >= WVS_SENTINEL_THRESHOLD, other=np.nan)
    return df


def _normalize_timeseries_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename time-series CSV columns to match Wave 7 conventions.

    The time-series CSV uses different column names:
        S002VS → A_WAVE, COUNTRY_ALPHA → B_COUNTRY_ALPHA, S003 → B_COUNTRY,
        S017 → W_WEIGHT, X001 → Q260, X003 → Q262, X025 → Q275, X049 → G_TOWNSIZE
    """
    renames: dict[str, str] = {}

    # Administrative columns
    if _TS_COL_WAVE in df.columns and _COL_WAVE not in df.columns:
        renames[_TS_COL_WAVE] = _COL_WAVE
    if _TS_COL_COUNTRY_ALPHA in df.columns and _COL_COUNTRY_ALPHA not in df.columns:
        renames[_TS_COL_COUNTRY_ALPHA] = _COL_COUNTRY_ALPHA
    if _TS_COL_COUNTRY_NUM in df.columns and _COL_COUNTRY_NUM not in df.columns:
        renames[_TS_COL_COUNTRY_NUM] = _COL_COUNTRY_NUM
    if _TS_WEIGHT_COL in df.columns and "W_WEIGHT" not in df.columns:
        renames[_TS_WEIGHT_COL] = "W_WEIGHT"

    # SES columns (A-code → Q-code)
    for ts_col, w7_col in _TS_SES_RENAMES.items():
        if ts_col in df.columns and w7_col not in df.columns:
            renames[ts_col] = w7_col

    if renames:
        df = df.rename(columns=renames)

    return df


# ---------------------------------------------------------------------------
# Internal helpers: metadata construction
# ---------------------------------------------------------------------------

def _build_survey_metadata(
    df: pd.DataFrame,
    qcode_to_title: dict[str, str],
) -> dict:
    """Build the metadata dict for one WVS survey slice.

    Returns
    -------
    {
        'variable_value_labels': {},   # WVS has no universal value labels; sparse
        'column_names_to_labels': {Q-code: title},
    }
    """
    col_labels = {
        col: qcode_to_title.get(col, col)
        for col in df.columns
    }
    return {
        "variable_value_labels": {},   # WVS codebook labels not machine-parseable from XLSX
        "column_names_to_labels": col_labels,
    }


def _make_survey_key(wave: int, alpha3: str) -> str:
    """Canonical enc_dict key: e.g. 'WVS_W7_MEX'."""
    return f"WVS_W{wave}_{alpha3.upper()}"


def _make_short_id(wave: int, alpha3: str) -> str:
    """Short enc_nom_dict identifier: e.g. 'W7M' for Wave 7 Mexico."""
    return f"W{wave}_{alpha3.upper()}"


# ---------------------------------------------------------------------------
# Main loader class
# ---------------------------------------------------------------------------

class WVSLoader:
    """Load WVS data from local files and build a wvs_dict.

    Parameters
    ----------
    wvs_dir : Path, optional
        Directory containing WVS files. Defaults to data/wvs/.
    """

    def __init__(self, wvs_dir: Optional[Path] = None):
        self.wvs_dir = Path(wvs_dir) if wvs_dir else _DEFAULT_WVS_DIR
        self._timeseries_cache: Optional[pd.DataFrame] = None  # lazy-loaded, reused

        # Load metadata (always available — small XLSXs are committed)
        self.equivalences = load_equivalences(
            self.wvs_dir / "F00003844-WVS_Time_Series_List_of_Variables_and_equivalences_1981_2022_v3_1.xlsx"
        )
        self.country_registry = load_country_registry(
            self.wvs_dir / "WVS_Countries_in_time_series_1981-2022.xlsx"
        )

        # Pre-build lookup tables
        self._qcode_to_acode = build_qcode_to_acode(self.equivalences)
        self._acode_title = get_acode_title(self.equivalences)

        # Q-code → title for each wave
        self._wave_qcode_title: dict[int, dict[str, str]] = {}
        for wave in range(1, 8):
            w_col = f"w{wave}"
            self._wave_qcode_title[wave] = {}
            for _, row in self.equivalences.iterrows():
                q = row[w_col]
                if q:
                    self._wave_qcode_title[wave][q] = row["title"]

    # ------------------------------------------------------------------
    # Raw data loading
    # ------------------------------------------------------------------

    def _load_wave7_raw(self) -> pd.DataFrame:
        """Load the Wave 7 cross-national CSV (all countries)."""
        src = _find_wvs_file(self.wvs_dir, _WAVE7_ZIP_PATTERN)
        if src is None:
            raise FileNotFoundError(
                f"WVS Wave 7 data not found in {self.wvs_dir}\n"
                f"Expected a file matching '*{_WAVE7_ZIP_PATTERN}*.csv' or '*.zip'.\n"
                "Download from https://www.worldvaluessurvey.org/WVSDocumentationWV7.jsp"
            )
        return _load_csv_from_source(src)

    def _load_timeseries_raw(self) -> pd.DataFrame:
        """Load the full WVS Time Series CSV (all waves, all countries).

        Caches the result in memory so multiple wave requests don't re-read
        the 1.3GB CSV file.
        """
        if self._timeseries_cache is not None:
            return self._timeseries_cache

        src = _find_wvs_file(self.wvs_dir, _TIMESERIES_ZIP_PATTERN)
        if src is None:
            raise FileNotFoundError(
                f"WVS Time Series data not found in {self.wvs_dir}\n"
                f"Expected a file matching '*{_TIMESERIES_ZIP_PATTERN}*.csv' or '*.zip'.\n"
                "Download from https://www.worldvaluessurvey.org/WVSDocumentationWVL.jsp"
            )
        self._timeseries_cache = _load_csv_from_source(src)
        return self._timeseries_cache

    # ------------------------------------------------------------------
    # Single-wave / single-country slice
    # ------------------------------------------------------------------

    def load_slice(
        self,
        wave: int,
        countries: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Load a cleaned DataFrame for one wave, optionally filtered to countries.

        Parameters
        ----------
        wave : int
            WVS wave number (1–7).
        countries : list[str], optional
            ISO alpha-3 country codes to keep. None = all countries.

        Returns
        -------
        pd.DataFrame
            Cleaned (sentinels → NaN) individual-level data with harmonized
            SES columns (sexo, edad, escol, Tam_loc) appended.
        """
        if wave == 7:
            raw = self._load_wave7_raw()
        else:
            raw = self._load_timeseries_raw()
            raw = _normalize_timeseries_columns(raw)
            raw = raw[raw[_COL_WAVE] == wave].copy()

        if countries is not None:
            countries_upper = [c.upper() for c in countries]
            if _COL_COUNTRY_ALPHA in raw.columns:
                raw = raw[raw[_COL_COUNTRY_ALPHA].isin(countries_upper)].copy()
            else:
                # Fall back to numeric code if alpha column absent (some older files)
                raw = raw[raw[_COL_COUNTRY_NUM].isin(
                    self._alpha3_to_num(countries_upper)
                )].copy()

        raw = clean_sentinels(raw)
        raw = harmonize_ses(raw)
        raw = raw.reset_index(drop=True)
        return raw

    def _alpha3_to_num(self, alpha3_list: list[str]) -> list[int]:
        """Crude fallback: map common alpha-3 codes to WVS numeric codes."""
        # Only used if B_COUNTRY_ALPHA column is absent
        _MAP = {"MEX": 484, "ARG": 32, "BRA": 76, "CHL": 152, "COL": 170,
                "USA": 840, "DEU": 276, "JPN": 392, "CHN": 156, "IND": 356}
        return [_MAP[c] for c in alpha3_list if c in _MAP]

    # ------------------------------------------------------------------
    # wvs_dict builder
    # ------------------------------------------------------------------

    def build_wvs_dict(
        self,
        waves: Optional[list[int]] = None,
        countries: Optional[list[str]] = None,
    ) -> dict:
        """Build a wvs_dict parallel to los_mex_dict.

        Creates one enc_dict entry per (wave, country) combination.

        Parameters
        ----------
        waves : list[int], optional
            Wave numbers to include. Defaults to [7] (Wave 7 only).
        countries : list[str], optional
            ISO alpha-3 codes. None = all countries present in each wave.

        Returns
        -------
        dict with keys: enc_dict, enc_nom_dict, pregs_dict, ses_dict,
                        var_equivalences, country_registry
        """
        if waves is None:
            waves = [7]

        enc_dict: dict = {}
        enc_nom_dict: dict = {}
        pregs_dict: dict = {}
        ses_dict: dict = {}

        for wave in waves:
            print(f"Loading Wave {wave}…")
            try:
                df_wave = self.load_slice(wave, countries=countries)
            except FileNotFoundError as exc:
                print(f"  SKIP Wave {wave}: {exc}")
                continue

            # Determine which countries are in this slice
            if _COL_COUNTRY_ALPHA in df_wave.columns:
                present_countries = sorted(df_wave[_COL_COUNTRY_ALPHA].dropna().unique())
            else:
                present_countries = ["UNKNOWN"]

            # For Wave 7: columns are Q-codes; for time-series: columns are A-codes.
            # Build a unified column→title mapping for this wave.
            qcode_title = self._wave_qcode_title.get(wave, {})
            # Also include A-code→title for time-series columns
            col_title = dict(qcode_title)
            col_title.update(self._acode_title)

            for alpha3 in present_countries:
                alpha3 = str(alpha3).upper()
                if _COL_COUNTRY_ALPHA in df_wave.columns:
                    df_country = df_wave[df_wave[_COL_COUNTRY_ALPHA] == alpha3].copy()
                else:
                    df_country = df_wave.copy()

                if len(df_country) == 0:
                    continue

                survey_key = _make_survey_key(wave, alpha3)
                short_id = _make_short_id(wave, alpha3)

                enc_dict[survey_key] = {
                    "dataframe": df_country,
                    "metadata": _build_survey_metadata(df_country, col_title),
                }
                enc_nom_dict[survey_key] = short_id

                # pregs_dict: one entry per substantive column (Q-code or A-code)
                for col in df_country.columns:
                    if col in col_title:
                        key = f"{col}|{short_id}"
                        pregs_dict[key] = f"{survey_key}|{col_title[col]}"

                # ses_dict: harmonized SES columns available in this survey
                available_ses = [c for c in _HARMONIZED_SES_COLS if c in df_country.columns]
                ses_dict[survey_key] = available_ses

            print(
                f"  Wave {wave}: {len(present_countries)} countries, "
                f"{len(df_wave)} rows total."
            )

        return {
            "enc_dict": enc_dict,
            "enc_nom_dict": enc_nom_dict,
            "pregs_dict": pregs_dict,
            "ses_dict": ses_dict,
            "var_equivalences": self.equivalences,
            "country_registry": self.country_registry,
        }

    # ------------------------------------------------------------------
    # Convenience: Mexico-only time series
    # ------------------------------------------------------------------

    def build_mexico_timeseries(self) -> dict:
        """Build wvs_dict for Mexico across all 7 waves.

        Shortcut for the primary los_mex bridge use case.
        """
        return self.build_wvs_dict(waves=list(range(1, 8)), countries=["MEX"])

    # ------------------------------------------------------------------
    # Cache helpers (JSON)
    # ------------------------------------------------------------------

    def save(self, wvs_dict: dict, path: Path) -> None:
        """Persist wvs_dict to a JSON cache file.

        DataFrames are serialised as record-oriented JSON.  The
        var_equivalences DataFrame and country_registry are also stored.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        serialisable = {
            "enc_dict": {
                key: {
                    "dataframe": val["dataframe"].to_dict(orient="records"),
                    "metadata": val["metadata"],
                }
                for key, val in wvs_dict["enc_dict"].items()
            },
            "enc_nom_dict": wvs_dict["enc_nom_dict"],
            "pregs_dict": wvs_dict["pregs_dict"],
            "ses_dict": wvs_dict["ses_dict"],
            "var_equivalences": wvs_dict["var_equivalences"].to_dict(orient="records"),
            "country_registry": wvs_dict["country_registry"],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serialisable, f, ensure_ascii=False, allow_nan=True)
        print(f"wvs_dict saved to {path}")

    @staticmethod
    def load(path: Path) -> dict:
        """Load a previously saved wvs_dict JSON cache.

        Reconstructs DataFrames from record-oriented JSON.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"WVS cache not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        enc_dict = {}
        for key, val in raw["enc_dict"].items():
            enc_dict[key] = {
                "dataframe": pd.DataFrame(val["dataframe"]),
                "metadata": val["metadata"],
            }

        equivalences = pd.DataFrame(raw.get("var_equivalences", []))

        return {
            "enc_dict": enc_dict,
            "enc_nom_dict": raw["enc_nom_dict"],
            "pregs_dict": raw["pregs_dict"],
            "ses_dict": raw["ses_dict"],
            "var_equivalences": equivalences,
            "country_registry": raw.get("country_registry", {}),
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build and cache WVS data dictionary")
    parser.add_argument(
        "--waves", nargs="+", type=int, default=[7],
        help="Wave numbers to include (default: 7)",
    )
    parser.add_argument(
        "--countries", nargs="+", default=None,
        help="ISO alpha-3 country codes (default: all)",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/wvs/wvs_dict.json"),
        help="Output JSON cache path",
    )
    parser.add_argument(
        "--mexico-ts", action="store_true",
        help="Shortcut: load all 7 waves for Mexico only",
    )
    args = parser.parse_args()

    loader = WVSLoader()
    if args.mexico_ts:
        wvs_dict = loader.build_mexico_timeseries()
    else:
        wvs_dict = loader.build_wvs_dict(waves=args.waves, countries=args.countries)

    loader.save(wvs_dict, args.output)
    print(f"\nDone. Surveys loaded: {list(wvs_dict['enc_dict'].keys())[:10]}")
