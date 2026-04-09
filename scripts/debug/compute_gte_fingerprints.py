"""
Compute GTE per-country SES fingerprints for any WVS wave.

For each (wave, country), computes Spearman ρ between each construct aggregate
and the 4 SES dimensions (escol, Tam_loc, sexo, edad).

For W7: reads pre-built CSVs from julia_bridge_wvs/ (fast path).
For W3-W6: loads raw WVS data via WVSLoader, builds constructs on-the-fly.

Output format matches existing data/gte/fingerprints/*.json.

Usage:
    python scripts/debug/compute_gte_fingerprints.py --wave 5 --all
    python scripts/debug/compute_gte_fingerprints.py --wave 5 --country MEX
    python scripts/debug/compute_gte_fingerprints.py --all-waves
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import (
    GTE_DIR,
    NAVEGADOR_DATA,
    VALID_WAVES,
    load_manifest,
)

SES_DIMS = ["escol", "Tam_loc", "sexo", "edad"]
JULIA_BRIDGE_DIR = NAVEGADOR_DATA / "data" / "julia_bridge_wvs"


# ---------------------------------------------------------------------------
# Fast path: W7 pre-built CSVs
# ---------------------------------------------------------------------------

def _fingerprint_from_csv(csv_path: Path, construct_names: list[str]) -> tuple[dict, int]:
    """Compute fingerprints from a pre-built julia_bridge CSV.

    Returns (constructs_dict, n_respondents).
    """
    df = pd.read_csv(csv_path)
    n_respondents = len(df)
    constructs = {}

    for cname in construct_names:
        col = f"wvs_agg_{cname}"
        if col not in df.columns:
            continue
        rhos = {}
        n_valid = 0
        for dim in SES_DIMS:
            if dim not in df.columns:
                continue
            mask = df[[col, dim]].dropna()
            if len(mask) < 30:
                continue
            rho, _ = spearmanr(mask[col], mask[dim])
            if not math.isnan(rho):
                rhos[f"rho_{dim}"] = round(rho, 6)
            n_valid = max(n_valid, len(mask))

        if not rhos:
            continue

        mag = math.sqrt(sum(v ** 2 for v in rhos.values()) / len(rhos))
        dominant = max(rhos, key=lambda k: abs(rhos[k]))
        constructs[cname] = {
            **{f"rho_{d}": rhos.get(f"rho_{d}", 0.0) for d in SES_DIMS},
            "ses_magnitude": round(mag, 6),
            "dominant_dim": dominant.replace("rho_", ""),
            "n_valid": n_valid,
        }

    return constructs, n_respondents


# ---------------------------------------------------------------------------
# Slow path: W3-W6 via memory-efficient selective column loading
# ---------------------------------------------------------------------------

# Cache for metadata objects (small, reusable)
_meta_cache: dict = {}


def _get_svs_and_overrides():
    """Load SVS construct definitions and overrides."""
    if "svs" in _meta_cache:
        return _meta_cache["svs"], _meta_cache["overrides"]
    svs_path = ROOT / "data" / "results" / "wvs_svs_v1.json"
    overrides_path = ROOT / "data" / "results" / "wvs_construct_overrides.json"
    with open(svs_path) as f:
        svs = json.load(f)
    overrides = {}
    if overrides_path.exists():
        with open(overrides_path) as f:
            overrides = json.load(f)
    _meta_cache["svs"] = svs
    _meta_cache["overrides"] = overrides
    return svs, overrides


def _get_equivalences():
    """Load WVS equivalences table (cached)."""
    if "eq" in _meta_cache:
        return _meta_cache["eq"]
    from wvs_metadata import load_equivalences
    eq = load_equivalences(
        ROOT / "data" / "wvs" /
        "F00003844-WVS_Time_Series_List_of_Variables_and_equivalences_1981_2022_v3_1.xlsx"
    )
    _meta_cache["eq"] = eq
    return eq


def _load_timeseries_slim(needed_acodes: set[str]) -> pd.DataFrame:
    """Load Time Series CSV with only needed columns (~800MB vs 2GB)."""
    import zipfile

    zip_path = ROOT / "data" / "wvs" / "F00011931-WVS_Time_Series_1981-2022_csv_v5_0.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Time Series ZIP not found: {zip_path}")

    zf = zipfile.ZipFile(zip_path)
    fname = zf.namelist()[0]

    # Read header to map column names to indices
    with zf.open(fname) as f:
        header = f.readline().decode("utf-8-sig").strip().replace('"', '').split(",")

    # Always need: wave, country, SES source columns (both Q-code and A-code names)
    meta_cols = {"S002VS", "COUNTRY_ALPHA"}
    # Q-codes (Wave 7 naming) + A-codes (Time Series naming) for SES
    ses_cols = {"Q260", "Q262", "Q275", "G_TOWNSIZE",
                "X001", "X003", "X025A_01", "X049"}
    all_needed = meta_cols | ses_cols | needed_acodes

    usecols = [i for i, c in enumerate(header) if c in all_needed]

    with zf.open(fname) as f:
        df = pd.read_csv(f, usecols=usecols, low_memory=True)

    # Strip quotes from column names if present
    df.columns = [c.strip('"') for c in df.columns]

    # Rename A-code SES columns to Q-code names (harmonize_ses expects Q-codes)
    acode_to_qcode = {"X001": "Q260", "X003": "Q262", "X025A_01": "Q275", "X049": "G_TOWNSIZE"}
    rename = {a: q for a, q in acode_to_qcode.items() if a in df.columns and q not in df.columns}
    if rename:
        df = df.rename(columns=rename)

    return df


def _fingerprint_from_raw(
    wave: int,
    country: str,
    construct_names: list[str],
    ts_df: pd.DataFrame | None = None,
) -> tuple[dict, int]:
    """Build constructs from raw WVS data and compute fingerprints.

    If ts_df is provided, uses it directly (pre-loaded Time Series).
    Otherwise loads from ZIP (slow).

    Returns (constructs_dict, n_respondents).
    """
    from scripts.debug.build_wvs_constructs_multi import (
        build_qcode_resolver,
        build_wvs_constructs_context,
    )
    from wvs_loader import clean_sentinels, harmonize_ses

    eq = _get_equivalences()
    svs, overrides = _get_svs_and_overrides()

    if ts_df is not None:
        # Filter from pre-loaded DataFrame
        df = ts_df.copy()
        if "S002VS" in df.columns:
            df = df[df["S002VS"] == wave].copy()
        if "COUNTRY_ALPHA" in df.columns:
            df = df[df["COUNTRY_ALPHA"] == country].copy()
    else:
        # Fallback: full load via WVSLoader
        from wvs_loader import WVSLoader
        loader = WVSLoader(wvs_dir=ROOT / "data" / "wvs")
        df = loader.load_slice(wave=wave, countries=[country])

    n_respondents = len(df)
    if n_respondents < 50:
        return {}, n_respondents

    # Clean sentinels and harmonize SES
    df = clean_sentinels(df)
    df = harmonize_ses(df)
    df = df.reset_index(drop=True)

    # Build Q-code resolver and construct aggregates
    resolver = build_qcode_resolver(eq, wave, list(df.columns))
    context_label = f"W{wave}_{country}"
    df, manifest_list = build_wvs_constructs_context(
        df, svs, overrides, resolver, context_label=context_label
    )

    # Compute fingerprints for built constructs
    constructs = {}
    construct_set = set(construct_names)
    for entry in manifest_list:
        col = entry.get("column")
        if col is None:
            continue
        cname = col.replace("wvs_agg_", "")
        if cname not in construct_set:
            continue

        rhos = {}
        n_valid = 0
        for dim in SES_DIMS:
            if dim not in df.columns:
                continue
            mask = df[[col, dim]].dropna()
            if len(mask) < 30:
                continue
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                rho, _ = spearmanr(mask[col], mask[dim])
            if not math.isnan(rho):
                rhos[f"rho_{dim}"] = round(rho, 6)
            n_valid = max(n_valid, len(mask))

        if not rhos:
            continue

        mag = math.sqrt(sum(v ** 2 for v in rhos.values()) / len(rhos))
        dominant = max(rhos, key=lambda k: abs(rhos[k]))
        constructs[cname] = {
            **{f"rho_{d}": rhos.get(f"rho_{d}", 0.0) for d in SES_DIMS},
            "ses_magnitude": round(mag, 6),
            "dominant_dim": dominant.replace("rho_", ""),
            "n_valid": n_valid,
        }

    return constructs, n_respondents


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def compute_fingerprints(
    country: str, wave: int, construct_names: list[str],
    ts_df: pd.DataFrame | None = None,
) -> dict:
    """Compute SES fingerprints for one (country, wave) pair."""
    csv_path = JULIA_BRIDGE_DIR / f"WVS_W{wave}_{country}.csv"

    if csv_path.exists():
        constructs, n_resp = _fingerprint_from_csv(csv_path, construct_names)
    else:
        constructs, n_resp = _fingerprint_from_raw(
            wave, country, construct_names, ts_df=ts_df)

    return {
        "country": country,
        "wave": wave,
        "n_constructs": len(constructs),
        "n_respondents": n_resp,
        "constructs": constructs,
    }


def run_wave(wave: int, country: str | None = None,
             ts_df: pd.DataFrame | None = None) -> None:
    """Run fingerprint computation for one wave.

    If ts_df is provided (pre-loaded Time Series), uses it to avoid
    re-reading the 1.3GB CSV. For W7, ts_df is ignored (uses pre-built CSVs).
    """
    manifest = load_manifest(wave=wave)
    countries = [country] if country else sorted(manifest["countries"])

    # Extract construct names from the manifest's construct_index
    # Format in manifest: "construct_name|WVS_X" → extract "construct_name"
    construct_names = [
        label.split("|")[0] for label in manifest.get("construct_index", [])
    ]

    # For non-W7 waves without pre-built CSVs, load Time Series once
    needs_raw = any(
        not (JULIA_BRIDGE_DIR / f"WVS_W{wave}_{c}.csv").exists()
        for c in countries
    )
    if needs_raw and ts_df is None and wave != 7:
        print(f"  Loading Time Series (slim, ~800MB)...")
        t_load = time.time()
        # Collect needed A-codes from SVS
        svs, _ = _get_svs_and_overrides()
        eq = _get_equivalences()
        all_qcodes = set()
        for dom_data in svs.get("domains", {}).values():
            for cluster in dom_data.get("construct_clusters", []):
                all_qcodes.update(cluster.get("question_cluster", []))
        q_to_a = {}
        for _, row in eq.iterrows():
            q7 = row.get("w7")
            a = row.get("a_code")
            if pd.notna(q7) and pd.notna(a):
                q_to_a[q7] = a
        needed_acodes = {q_to_a[q] for q in all_qcodes if q in q_to_a}
        ts_df = _load_timeseries_slim(needed_acodes)
        print(f"  Loaded: {ts_df.shape}, {time.time()-t_load:.1f}s")

    out_dir = GTE_DIR / f"W{wave}" / "fingerprints"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  GTE Fingerprints — Wave {wave} ({len(countries)} countries)")
    print(f"  {len(construct_names)} constructs in manifest")
    print(f"  Output: {out_dir}")
    print(f"{'='*60}")

    t0 = time.time()
    for i, c in enumerate(countries):
        try:
            result = compute_fingerprints(c, wave, construct_names, ts_df=ts_df)
            path = out_dir / f"{c}.json"
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  [{i+1}/{len(countries)}] {c}: "
                  f"{result['n_constructs']} constructs, "
                  f"{result['n_respondents']} respondents")
        except Exception as e:
            print(f"  [{i+1}/{len(countries)}] {c}: ERROR — {e}")

    elapsed = time.time() - t0
    print(f"\n  Done W{wave} in {elapsed:.1f}s")


def main():
    parser = argparse.ArgumentParser(
        description="Compute GTE SES fingerprints from WVS microdata")
    parser.add_argument("--wave", type=int, default=7, choices=VALID_WAVES,
                        help="WVS wave number (default: 7)")
    parser.add_argument("--country", default=None,
                        help="Single country code (default: all)")
    parser.add_argument("--all", action="store_true",
                        help="Run all countries for the specified wave")
    parser.add_argument("--all-waves", action="store_true",
                        help="Run all countries for waves 3-7")
    args = parser.parse_args()

    if args.all_waves:
        for w in VALID_WAVES:
            run_wave(w)
    elif args.all or args.country is None:
        run_wave(args.wave)
    else:
        run_wave(args.wave, country=args.country)


if __name__ == "__main__":
    main()
