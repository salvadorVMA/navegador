"""WVS metadata: variable equivalences, domain taxonomy, cultural zones, country registry.

Parses the WVS XLSX metadata files shipped in data/wvs/ and exposes them as
plain Python structures that the rest of the WVS integration can depend on
without touching CSV/zip data.

Key public API
--------------
load_equivalences(path)   -> pd.DataFrame   (1 row per A-series variable)
load_country_registry(path) -> dict          (country → wave participation counts)
DOMAIN_MAP                -> dict[str, str]  (prefix → domain name)
CULTURAL_ZONES            -> dict[str, list] (zone → list of ISO alpha-3 codes)
WAVE_LABELS               -> dict[int, str]  (wave number → label)
SES_VARS                  -> dict            (harmonized SES config for bridge)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Domain prefix → human-readable domain name (matches WVS codebook sections)
DOMAIN_MAP: dict[str, str] = {
    "A": "Social Values, Attitudes & Stereotypes",
    "B": "Environment",
    "C": "Work & Employment",
    "D": "Family",
    "E": "Politics & Society",
    "F": "Religion & Morale",
    "G": "National Identity",
    "H": "Security",
    "I": "Science & Technology",
    "X": "SES & Demographics",
    "Y": "Derived Indices",
}

#: Wave number → descriptive label
WAVE_LABELS: dict[int, str] = {
    1: "Wave 1 (1981–1984)",
    2: "Wave 2 (1990–1994)",
    3: "Wave 3 (1995–1998)",
    4: "Wave 4 (1999–2004)",
    5: "Wave 5 (2005–2009)",
    6: "Wave 6 (2010–2014)",
    7: "Wave 7 (2017–2022)",
}

#: Wave number → column names in the equivalence XLSX
_WAVE_COL_NAMES: dict[int, str] = {
    7: "WVS7",
    6: "WVS6",
    5: "WVS5",
    4: "WVS4",
    3: "WVS3",
    2: "WVS2",
    1: "WVS1",
}

#: Inglehart-Welzel cultural zones (Wave 7 countries, ISO alpha-3)
# Inglehart-Welzel cultural zones — expanded to cover all WVS waves (W1-W7).
# Based on the Inglehart-Welzel Cultural Map of the World (2020 revision).
# Original W7-only list extended with 34 countries from earlier waves.
#
# Zone assignments follow the standard WVS typology:
#   - Protestant Europe: Nordic + Germanic Protestant-heritage countries
#   - Catholic Europe: Romance + historically Catholic non-Latin-American countries
#   - English-speaking: Anglosphere settler societies
#   - Latin America: Spanish/Portuguese-speaking Americas + Caribbean
#   - Orthodox/ex-Communist: post-Soviet + post-Yugoslav + ex-Warsaw Pact
#   - Confucian: East Asian Confucian-heritage societies
#   - South/Southeast Asian: South + Southeast Asian (non-Confucian)
#   - African-Islamic: Sub-Saharan Africa + MENA Islamic-majority countries
#
# Borderline cases:
#   - TUR: placed in African-Islamic (Islamic-majority, Inglehart maps it there)
#   - CYP: Catholic Europe (Greek Orthodox but EU Mediterranean culture)
#   - ZAF: African-Islamic (Sub-Saharan Africa, diverse but Inglehart groups it here)
#   - TTO: Latin America (Caribbean, English-speaking but Latin cultural sphere)
#   - GEO: Orthodox/ex-Communist (post-Soviet, Orthodox Christian)

CULTURAL_ZONES: dict[str, list[str]] = {
    "Latin America": [
        "ARG", "BOL", "BRA", "CHL", "COL", "DOM", "ECU", "GTM",
        "HTI", "MEX", "NIC", "PER", "PRI", "TTO", "URY", "VEN",
    ],
    "English-speaking": ["AUS", "CAN", "GBR", "NIR", "NZL", "USA"],
    "Protestant Europe": [
        "CHE", "DEU", "EST", "LTU", "LVA", "NLD", "NOR", "SWE",
    ],
    "Catholic Europe": [
        "AND", "CYP", "ESP", "FRA", "GRC", "HUN", "ITA", "POL",
        "SVN",
    ],
    "Orthodox/ex-Communist": [
        "ALB", "ARM", "AZE", "BGR", "BIH", "BLR", "CZE", "GEO",
        "KAZ", "KGZ", "MDA", "MKD", "MNE", "MNG", "ROU", "RUS",
        "SRB", "SVK", "TJK", "UKR", "UZB",
    ],
    "Confucian": ["CHN", "HKG", "JPN", "KOR", "MAC", "SGP", "TWN", "VNM"],
    "South/Southeast Asian": [
        "BGD", "IDN", "IND", "MMR", "MYS", "PAK", "PHL", "THA",
    ],
    "African-Islamic": [
        "BFA", "DZA", "EGY", "ETH", "GHA", "IRN", "IRQ", "JOR",
        "KEN", "KWT", "LBN", "LBY", "MAR", "MDV", "MLI", "NGA",
        "RWA", "SAU", "TUN", "TUR", "YEM", "ZAF", "ZMB", "ZWE",
    ],
}

#: Reverse lookup: alpha-3 → zone name
COUNTRY_ZONE: dict[str, str] = {
    country: zone
    for zone, countries in CULTURAL_ZONES.items()
    for country in countries
}

# ---------------------------------------------------------------------------
# SES harmonization configuration
# ---------------------------------------------------------------------------

# WVS Q-code → los_mex SES variable name, plus transformation details.
# These are the 4 SES vars used throughout the bridge (v3 optimal config).
SES_VARS: dict[str, dict] = {
    "sexo": {
        "wvs_col": "Q260",          # 1=Male, 2=Female — direct match
        "transform": "direct",
        "values": {1: 1, 2: 2},
    },
    "edad": {
        "wvs_col": "Q262",          # continuous age 18–90+
        "transform": "continuous_age",  # pass numeric age directly
        # Q262 is continuous year-of-age. Passed through as-is for the
        # ordered logit (handles continuous predictors natively).
        # Values outside 15-100 → NaN.
    },
    "escol": {
        "wvs_col": "Q275",          # ISCED 0-8
        "transform": "isced_to_5",  # applied via _map_values() in wvs_loader
        # Aligned to Mexican education levels:
        # 0 → 1 (Ninguna), 1 → 2 (Primaria), 2 → 3 (Secundaria),
        # 3-4 → 4 (Preparatoria), 5-8 → 5 (Universidad/Posgrado)
        "values": {0: 1, 1: 2, 2: 3, 3: 4, 4: 4, 5: 5, 6: 5, 7: 5, 8: 5},
    },
    "Tam_loc": {
        "wvs_col": "G_TOWNSIZE",    # 1-8 town size scale
        "transform": "collapse_4",  # collapse 8 → 4 levels
        # 1-2 → 1 (rural), 3-4 → 2 (small), 5-6 → 3 (medium), 7-8 → 4 (large)
        "values": {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4},
    },
}

# WVS sentinel codes (values < 0 → NaN)
WVS_SENTINEL_THRESHOLD = 0  # strictly negative values are sentinels

# ---------------------------------------------------------------------------
# Default file paths (relative to project root)
# ---------------------------------------------------------------------------

_DEFAULT_WVS_DIR = Path(__file__).parent / "data" / "wvs"

_EQUIVALENCE_FILENAME = (
    "F00003844-WVS_Time_Series_List_of_Variables_and_equivalences_1981_2022_v3_1.xlsx"
)
_COUNTRIES_FILENAME = "WVS_Countries_in_time_series_1981-2022.xlsx"


# ---------------------------------------------------------------------------
# Equivalence table
# ---------------------------------------------------------------------------

def load_equivalences(path: Optional[Path] = None) -> pd.DataFrame:
    """Parse the WVS variable equivalences XLSX into a tidy DataFrame.

    Returns one row per A-series variable with columns:
        a_code    : str   — time-series code (e.g. 'A001')
        title     : str   — human-readable question description
        domain    : str   — domain name (from DOMAIN_MAP)
        prefix    : str   — single-letter prefix (e.g. 'A')
        w7, w6, w5, w4, w3, w2, w1 : str|None — Q-code in each wave

    Parameters
    ----------
    path : Path, optional
        Path to the equivalence XLSX. Defaults to data/wvs/<filename>.
    """
    xlsx_path = path or (_DEFAULT_WVS_DIR / _EQUIVALENCE_FILENAME)
    if not xlsx_path.exists():
        raise FileNotFoundError(
            f"WVS equivalence file not found: {xlsx_path}\n"
            "Expected: data/wvs/F00003844-WVS_Time_Series_*.xlsx"
        )

    df = pd.read_excel(xlsx_path, header=0)

    # The file has a blank first column; real columns start at index 1
    # Columns: [blank, Variable, Title, WVS7, WVS6, WVS5, WVS4, WVS3, WVS2, WVS1]
    df = df.iloc[:, 1:]  # drop blank leading column
    df.columns = ["a_code", "title", "w7", "w6", "w5", "w4", "w3", "w2", "w1"]

    # Drop rows without a valid A-series code
    df = df[df["a_code"].notna()].copy()
    df["a_code"] = df["a_code"].astype(str).str.strip()

    # Derive domain prefix (first character of a_code)
    df["prefix"] = df["a_code"].str[0]
    df["domain"] = df["prefix"].map(DOMAIN_MAP).fillna("Other")

    # Normalise wave Q-codes: strip whitespace, convert to str, None if missing
    for w_col in ["w7", "w6", "w5", "w4", "w3", "w2", "w1"]:
        df[w_col] = df[w_col].where(df[w_col].notna(), other=None)
        df[w_col] = df[w_col].apply(
            lambda v: str(v).strip() if v is not None else None
        )

    df = df.reset_index(drop=True)
    return df[["a_code", "title", "domain", "prefix", "w7", "w6", "w5", "w4", "w3", "w2", "w1"]]


def build_qcode_to_acode(equivalences: pd.DataFrame) -> dict[str, dict[int, str]]:
    """Build reverse lookup: Q-code → {wave: A-series code}.

    Useful for translating Wave 7 CSV column names back to stable A-series codes.

    Returns
    -------
    dict mapping Q-code string → dict of {wave_int: a_code}
    """
    lookup: dict[str, dict[int, str]] = {}
    wave_cols = {7: "w7", 6: "w6", 5: "w5", 4: "w4", 3: "w3", 2: "w2", 1: "w1"}
    for _, row in equivalences.iterrows():
        for wave, col in wave_cols.items():
            q = row[col]
            if q:
                lookup.setdefault(q, {})[wave] = row["a_code"]
    return lookup


def get_acode_title(equivalences: pd.DataFrame) -> dict[str, str]:
    """Return {a_code: title} dict for all variables."""
    return dict(zip(equivalences["a_code"], equivalences["title"]))


# ---------------------------------------------------------------------------
# Country registry
# ---------------------------------------------------------------------------

def load_country_registry(path: Optional[Path] = None) -> dict[str, dict]:
    """Parse country participation XLSX into a registry dict.

    Returns
    -------
    dict mapping country name → {
        'n_per_wave': [n_w1, n_w2, n_w3, n_w4, n_w5, n_w6, n_w7],
        'total': int,
        'waves_present': [wave_ints where n > 0],
    }
    """
    xlsx_path = path or (_DEFAULT_WVS_DIR / _COUNTRIES_FILENAME)
    if not xlsx_path.exists():
        raise FileNotFoundError(
            f"WVS countries file not found: {xlsx_path}\n"
            "Expected: data/wvs/WVS_Countries_in_time_series_1981-2022.xlsx"
        )

    df = pd.read_excel(xlsx_path, header=None)

    registry: dict[str, dict] = {}
    for _, row in df.iterrows():
        name = row.iloc[0]
        if not isinstance(name, str) or not name.strip():
            continue
        vals = list(row.iloc[1:8])  # 7 wave columns
        n_per_wave = [int(v) if pd.notna(v) else 0 for v in vals]
        total = int(row.iloc[8]) if pd.notna(row.iloc[8]) else sum(n_per_wave)
        waves_present = [i + 1 for i, n in enumerate(n_per_wave) if n > 0]
        registry[name.strip()] = {
            "n_per_wave": n_per_wave,
            "total": total,
            "waves_present": waves_present,
        }
    return registry


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_variables_for_wave(equivalences: pd.DataFrame, wave: int) -> pd.DataFrame:
    """Return subset of equivalences available in the given wave (Q-code not null)."""
    col = f"w{wave}"
    if col not in equivalences.columns:
        raise ValueError(f"Invalid wave: {wave}. Must be 1-7.")
    return equivalences[equivalences[col].notna()].copy()


def get_shared_variables(equivalences: pd.DataFrame, waves: list[int]) -> pd.DataFrame:
    """Return variables present (non-null Q-code) in ALL specified waves."""
    mask = pd.Series(True, index=equivalences.index)
    for w in waves:
        mask &= equivalences[f"w{w}"].notna()
    return equivalences[mask].copy()


def country_zone(alpha3: str) -> str:
    """Return the Inglehart-Welzel cultural zone for an ISO alpha-3 code, or 'Unknown'."""
    return COUNTRY_ZONE.get(alpha3.upper(), "Unknown")
