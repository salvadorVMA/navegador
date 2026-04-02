"""
Phase 0 — Convert all-wave γ-surface JSON to per-context weight matrices.

Generalizes both tda_convert_sweep_to_matrices.py (geographic) and
tda_convert_temporal_matrices.py (temporal) for the unified all-wave surface.

Two output modes:

  Mode A (geographic): For each wave with ≥ min_countries countries, build one
    directory with per-country weight/distance CSVs and a manifest.json.
    Each wave uses its own construct union (W7≈55, W6≈44, earlier fewer).

  Mode B (temporal): For each country with ≥ min_waves waves, build one
    directory with per-wave weight/distance CSVs and a manifest.json.
    Each country uses the construct union across its waves (NaN/sentinel
    for constructs not measured in a given wave).

Input:
  data/results/wvs_all_wave_gamma_surface.json  — 123K estimates, 225 contexts

Output (to data/tda/allwave/):
  matrices/W{n}/                — per-wave subdirectories (Mode A)
    {COUNTRY}.csv               — weight matrix (γ values)
    {COUNTRY}_distance.csv      — distance matrix (1/|γ|)
    manifest.json               — country list + file paths
    construct_index.json        — canonical construct ordering for this wave
  matrices/global_manifest.json — master index across all waves

  temporal/{ALPHA3}/            — per-country subdirectories (Mode B)
    {ALPHA3}_W{n}.csv           — weight matrix for one wave
    {ALPHA3}_W{n}_distance.csv  — distance matrix for one wave
    manifest.json               — wave list + file paths

Run:
  python scripts/debug/tda_convert_allwave_to_matrices.py --mode both
  python scripts/debug/tda_convert_allwave_to_matrices.py --mode geographic --min-countries 10
  python scripts/debug/tda_convert_allwave_to_matrices.py --mode temporal --min-waves 3
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

# ── Input / Output ────────────────────────────────────────────────────────────
SURFACE_PATH = ROOT / "data" / "results" / "wvs_all_wave_gamma_surface.json"
OUTPUT_ROOT  = ROOT / "data" / "tda" / "allwave"

# ── Distance conversion parameters ───────────────────────────────────────────
EPSILON           = 0.001
SENTINEL_DISTANCE = 9999.0

WAVE_YEARS = {1: 1981, 2: 1990, 3: 1996, 4: 2000, 5: 2007, 6: 2012, 7: 2018}


# ── Key parsing ──────────────────────────────────────────────────────────────

def parse_allwave_key(full_key: str) -> tuple[str, int, str, str]:
    """
    Parse all-wave key → (alpha3, wave, construct_a, construct_b).

    Example:
      "WVS_W7_MEX::wvs_agg_X|WVS_D::wvs_agg_Y|WVS_F"
      → ("MEX", 7, "wvs_agg_X|WVS_D", "wvs_agg_Y|WVS_F")
    """
    parts = full_key.split("::")
    ctx_parts = parts[0].split("_")
    alpha3 = ctx_parts[2]
    wave = int(ctx_parts[1][1:])  # "W7" → 7
    return alpha3, wave, parts[1], parts[2]


def construct_short_name(full_name: str) -> str:
    """Strip agg_/wvs_agg_ prefix for display."""
    if full_name.startswith("wvs_agg_"):
        return full_name[len("wvs_agg_"):]
    if full_name.startswith("agg_"):
        return full_name[len("agg_"):]
    return full_name


def gamma_to_distance(gamma: float) -> float:
    """Convert γ ∈ [-1, 1] to positive distance d = 1 / max(|γ|, ε)."""
    return 1.0 / max(abs(gamma), EPSILON)


# ── Data organization ────────────────────────────────────────────────────────

def load_and_organize(surface_path: Path) -> dict:
    """
    Load the all-wave surface and organize estimates by (wave, country).

    Returns dict with:
      by_wave_country:  {(wave, alpha3) → {(ca, cb): gamma}}
      constructs_by_wave: {wave → set of constructs}
      constructs_by_country: {alpha3 → set of constructs}
      waves_by_country: {alpha3 → set of waves}
    """
    print(f"  Loading {surface_path.name}...")
    with open(surface_path) as f:
        data = json.load(f)
    estimates = data.get("estimates", {})
    print(f"  {len(estimates)} estimates loaded")

    by_wave_country: dict[tuple[int, str], dict[tuple[str, str], float]] = defaultdict(dict)
    constructs_by_wave: dict[int, set[str]] = defaultdict(set)
    constructs_by_country: dict[str, set[str]] = defaultdict(set)
    waves_by_country: dict[str, set[int]] = defaultdict(set)

    for key, est in estimates.items():
        gamma = est.get("dr_gamma")
        if gamma is None:
            continue
        alpha3, wave, va, vb = parse_allwave_key(key)
        sa = construct_short_name(va)
        sb = construct_short_name(vb)

        by_wave_country[(wave, alpha3)][(sa, sb)] = gamma
        by_wave_country[(wave, alpha3)][(sb, sa)] = gamma

        constructs_by_wave[wave].add(sa)
        constructs_by_wave[wave].add(sb)
        constructs_by_country[alpha3].add(sa)
        constructs_by_country[alpha3].add(sb)
        waves_by_country[alpha3].add(wave)

    return {
        "by_wave_country": dict(by_wave_country),
        "constructs_by_wave": {w: sorted(cs) for w, cs in constructs_by_wave.items()},
        "constructs_by_country": {c: sorted(cs) for c, cs in constructs_by_country.items()},
        "waves_by_country": {c: sorted(ws) for c, ws in waves_by_country.items()},
    }


def build_matrix(
    pairs: dict[tuple[str, str], float],
    construct_index: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build weight (γ) and distance (1/|γ|) DataFrames for a set of pairs."""
    n = len(construct_index)
    idx = {c: i for i, c in enumerate(construct_index)}

    W = np.full((n, n), np.nan)
    np.fill_diagonal(W, 0.0)
    D = np.full((n, n), SENTINEL_DISTANCE)
    np.fill_diagonal(D, 0.0)

    for (sa, sb), gamma in pairs.items():
        if sa in idx and sb in idx:
            i, j = idx[sa], idx[sb]
            W[i, j] = gamma
            D[i, j] = gamma_to_distance(gamma)

    W_df = pd.DataFrame(W, index=construct_index, columns=construct_index)
    D_df = pd.DataFrame(D, index=construct_index, columns=construct_index)
    return W_df, D_df


# ── Mode A: Per-wave geographic matrices ─────────────────────────────────────

def build_geographic(org: dict, min_countries: int) -> dict:
    """
    Build per-wave geographic matrices.

    For each wave with enough countries, creates a subdirectory with
    per-country weight/distance CSVs and a manifest.json.

    Returns global manifest dict.
    """
    by_wc = org["by_wave_country"]
    constructs_by_wave = org["constructs_by_wave"]

    # Determine which waves have enough countries
    wave_countries: dict[int, list[str]] = defaultdict(list)
    for (wave, alpha3) in by_wc:
        wave_countries[wave].append(alpha3)
    wave_countries = {w: sorted(set(cs)) for w, cs in wave_countries.items()}

    global_manifest = {
        "description": "All-wave geographic TDA matrices",
        "waves": {},
    }

    for wave in sorted(wave_countries):
        countries = wave_countries[wave]
        if len(countries) < min_countries:
            print(f"  W{wave}: {len(countries)} countries < {min_countries} minimum — SKIP")
            continue

        construct_index = constructs_by_wave[wave]
        n_constructs = len(construct_index)
        wave_dir = OUTPUT_ROOT / "matrices" / f"W{wave}"
        wave_dir.mkdir(parents=True, exist_ok=True)

        print(f"  W{wave} ({WAVE_YEARS.get(wave, '?')}): "
              f"{len(countries)} countries, {n_constructs} constructs")

        # Build per-country matrices
        coverage = {}
        for alpha3 in countries:
            pairs = by_wc[(wave, alpha3)]
            W_df, D_df = build_matrix(pairs, construct_index)
            W_df.to_csv(wave_dir / f"{alpha3}.csv")
            D_df.to_csv(wave_dir / f"{alpha3}_distance.csv")

            present = set()
            for sa, sb in pairs:
                present.add(sa)
                present.add(sb)
            coverage[alpha3] = sorted(present)

        # Wave-level manifest (format matches what Julia scripts expect)
        wave_manifest = {
            "countries": countries,
            "n_constructs": n_constructs,
            "construct_index": construct_index,
            "cultural_zones": {
                zone: [c for c in codes if c in countries]
                for zone, codes in CULTURAL_ZONES.items()
            },
            "country_zone": {c: COUNTRY_ZONE.get(c, "Unknown") for c in countries},
            "files": {
                alpha3: {
                    "weight": str(wave_dir / f"{alpha3}.csv"),
                    "distance": str(wave_dir / f"{alpha3}_distance.csv"),
                }
                for alpha3 in countries
            },
        }

        with open(wave_dir / "manifest.json", "w") as f:
            json.dump(wave_manifest, f, indent=2)
        with open(wave_dir / "construct_index.json", "w") as f:
            json.dump(construct_index, f, indent=2)
        with open(wave_dir / "country_coverage.json", "w") as f:
            json.dump(coverage, f, indent=2)

        global_manifest["waves"][f"W{wave}"] = {
            "year": WAVE_YEARS.get(wave, 0),
            "n_countries": len(countries),
            "n_constructs": n_constructs,
            "manifest": str(wave_dir / "manifest.json"),
        }

    return global_manifest


# ── Mode B: Per-country temporal matrices ────────────────────────────────────

def build_temporal(org: dict, min_waves: int) -> dict:
    """
    Build per-country temporal matrices.

    For each country with enough waves, creates a subdirectory with
    per-wave weight/distance CSVs and a manifest.json.

    Returns temporal summary dict.
    """
    by_wc = org["by_wave_country"]
    waves_by_country = org["waves_by_country"]
    constructs_by_country = org["constructs_by_country"]

    temporal_summary = {
        "description": "All-wave temporal TDA matrices",
        "countries": {},
    }

    eligible = {
        c: ws for c, ws in waves_by_country.items()
        if len(ws) >= min_waves
    }
    print(f"  {len(eligible)} countries with {min_waves}+ waves")

    for alpha3 in sorted(eligible):
        waves = eligible[alpha3]
        # Construct union across all this country's waves
        construct_index = constructs_by_country[alpha3]
        n_constructs = len(construct_index)

        country_dir = OUTPUT_ROOT / "temporal" / alpha3
        country_dir.mkdir(parents=True, exist_ok=True)

        wave_info = {}
        for wave in waves:
            pairs = by_wc.get((wave, alpha3), {})
            if not pairs:
                continue
            W_df, D_df = build_matrix(pairs, construct_index)
            w_path = country_dir / f"{alpha3}_W{wave}.csv"
            d_path = country_dir / f"{alpha3}_W{wave}_distance.csv"
            W_df.to_csv(w_path)
            D_df.to_csv(d_path)

            present = set()
            for sa, sb in pairs:
                present.add(sa)
                present.add(sb)

            wave_info[f"W{wave}"] = {
                "weight": str(w_path),
                "distance": str(d_path),
                "n_pairs": len(pairs) // 2,
                "n_constructs_present": len(present),
                "year": WAVE_YEARS.get(wave, 0),
            }

        # Country temporal manifest (format matches tda_temporal_spectral.jl)
        country_manifest = {
            "waves": waves,
            "wave_years": {str(w): WAVE_YEARS.get(w, 0) for w in waves},
            "n_constructs": n_constructs,
            "construct_index": construct_index,
            "files": wave_info,
        }
        with open(country_dir / "manifest.json", "w") as f:
            json.dump(country_manifest, f, indent=2)

        print(f"  {alpha3}: {len(waves)} waves, {n_constructs} constructs "
              f"({', '.join(f'W{w}' for w in waves)})")

        temporal_summary["countries"][alpha3] = {
            "waves": waves,
            "n_constructs": n_constructs,
            "manifest": str(country_dir / "manifest.json"),
            "zone": COUNTRY_ZONE.get(alpha3, "Unknown"),
        }

    return temporal_summary


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert all-wave γ-surface to TDA matrices"
    )
    parser.add_argument(
        "--mode", choices=["geographic", "temporal", "both"],
        default="both", help="Output mode (default: both)"
    )
    parser.add_argument(
        "--min-countries", type=int, default=5,
        help="Minimum countries per wave for geographic mode (default: 5)"
    )
    parser.add_argument(
        "--min-waves", type=int, default=3,
        help="Minimum waves per country for temporal mode (default: 3)"
    )
    args = parser.parse_args()

    if not SURFACE_PATH.exists():
        print(f"ERROR: {SURFACE_PATH} not found")
        sys.exit(1)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 0 — Convert all-wave γ-surface to TDA matrices")
    print("=" * 60)

    # Load and organize all estimates
    org = load_and_organize(SURFACE_PATH)

    # Summary
    waves = sorted(org["constructs_by_wave"].keys())
    countries = sorted(org["waves_by_country"].keys())
    print(f"  Waves: {waves}")
    print(f"  Countries: {len(countries)}")
    for w in waves:
        n_c = sum(1 for c in countries if w in org["waves_by_country"].get(c, []))
        n_const = len(org["constructs_by_wave"][w])
        print(f"    W{w} ({WAVE_YEARS.get(w, '?')}): {n_c} countries, {n_const} constructs")

    global_manifest = {}

    # Mode A: geographic
    if args.mode in ("geographic", "both"):
        print(f"\n{'─' * 60}")
        print("Mode A: Per-wave geographic matrices")
        print(f"{'─' * 60}")
        geo_manifest = build_geographic(org, args.min_countries)
        global_manifest["geographic"] = geo_manifest

    # Mode B: temporal
    if args.mode in ("temporal", "both"):
        print(f"\n{'─' * 60}")
        print("Mode B: Per-country temporal matrices")
        print(f"{'─' * 60}")
        temp_summary = build_temporal(org, args.min_waves)
        global_manifest["temporal"] = temp_summary

    # Save global manifest
    with open(OUTPUT_ROOT / "matrices" / "global_manifest.json", "w") as f:
        json.dump(global_manifest, f, indent=2)

    print(f"\n{'═' * 60}")
    print(f"Output: {OUTPUT_ROOT}")
    print("Done.")


if __name__ == "__main__":
    main()
