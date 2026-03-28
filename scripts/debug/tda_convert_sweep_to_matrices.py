"""
Phase 0 — Convert γ-surface sweep JSON to per-country weight matrices.

This is the data preparation step for the TDA (Topological Data Analysis) pipeline.
It reads the flat edge-list sweep results and produces one CSV weight matrix per
country, suitable for input to the Julia topology scripts.

Input:
  data/results/wvs_geographic_sweep_w7.json   — 68K pairwise WVS estimates
  data/results/construct_dr_sweep_v5_julia_v4.json — los_mex estimates

Output (to data/tda/matrices/):
  {COUNTRY}.csv          — one 55×55 signed γ weight matrix per country
  {COUNTRY}_distance.csv — distance matrix: d(i,j) = 1 / max(|γ|, ε)
  LOS_MEX.csv            — single los_mex weight matrix
  LOS_MEX_distance.csv   — los_mex distance matrix
  construct_index.json    — canonical ordered list of constructs
  country_coverage.json   — per-country list of present constructs
  manifest.json           — manifest for Julia scripts (paths + metadata)

Distance metric:
  d(i,j) = 1 / max(|γ(i,j)|, 0.001)
  NaN (no estimate) → Inf → sentinel 9999.0 in CSV for Julia compatibility

Run:
  python scripts/debug/tda_convert_sweep_to_matrices.py
"""
from __future__ import annotations

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

# ── Input / Output paths ─────────────────────────────────────────────────────
WVS_SWEEP   = ROOT / "data" / "results" / "wvs_geographic_sweep_w7.json"
LOSMEX_SWEEP = ROOT / "data" / "results" / "construct_dr_sweep_v5_julia_v4.json"
OUTPUT_DIR   = ROOT / "data" / "tda" / "matrices"

# ── Distance conversion parameters ───────────────────────────────────────────
# Epsilon floor prevents division by zero for γ ≈ 0 pairs.
# 0.001 means "maximally unrelated constructs" get distance = 1000 (large but finite).
EPSILON = 0.001
# Sentinel for unreachable pairs (no edge). Must be large but not Inf
# because Julia CSV parsing chokes on Inf.
SENTINEL_DISTANCE = 9999.0


# ── Key parsing ──────────────────────────────────────────────────────────────
# WVS keys: "WVS_W7_KAZ::wvs_agg_X|WVS_D::wvs_agg_Y|WVS_F"
# Los_mex keys: "agg_X|DOM_A::agg_Y|DOM_B"

def parse_wvs_key(full_key: str) -> tuple[str, str, str]:
    """
    Parse WVS sweep key → (alpha3_country_code, construct_a, construct_b).

    Example:
      "WVS_W7_KAZ::wvs_agg_familial_duty|WVS_D::wvs_agg_life_autonomy|WVS_F"
      → ("KAZ", "wvs_agg_familial_duty|WVS_D", "wvs_agg_life_autonomy|WVS_F")
    """
    parts = full_key.split("::")
    # parts[0] = "WVS_W7_KAZ" → extract "KAZ"
    alpha3 = parts[0].split("_")[2]
    return alpha3, parts[1], parts[2]


def parse_losmex_key(full_key: str) -> tuple[str, str]:
    """
    Parse los_mex sweep key → (construct_a, construct_b).

    Example:
      "agg_fiscal_preferences|FED::agg_security|SEG"
      → ("agg_fiscal_preferences|FED", "agg_security|SEG")
    """
    parts = full_key.split("::")
    return parts[0], parts[1]


def construct_short_name(full_name: str) -> str:
    """
    Shorten construct name for display: strip agg_/wvs_agg_ prefix.

    "wvs_agg_familial_duty_obligations|WVS_D" → "familial_duty_obligations|WVS_D"
    "agg_fiscal_preferences|FED"              → "fiscal_preferences|FED"
    """
    name = full_name
    if name.startswith("wvs_agg_"):
        name = name[len("wvs_agg_"):]
    elif name.startswith("agg_"):
        name = name[len("agg_"):]
    return name


# ── Matrix builders ──────────────────────────────────────────────────────────

def gamma_to_distance(gamma: float) -> float:
    """
    Convert γ ∈ [-1, 1] to a positive distance.

    d = 1 / max(|γ|, ε)

    Intuition:
    - |γ| = 0.5 → d = 2.0   (moderately connected)
    - |γ| = 0.1 → d = 10.0  (weakly connected)
    - |γ| = 0.001 → d = 1000 (essentially unrelated)

    We use |γ| because the sign indicates direction of covariation (positive
    vs negative), not strength. Two constructs with γ = -0.5 are just as
    "topologically close" as γ = +0.5 — they're strongly SES-linked either way.
    The sign information is preserved in the weight matrix for sign-aware analyses.
    """
    return 1.0 / max(abs(gamma), EPSILON)


def build_wvs_matrices(
    sweep_path: Path,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], list[str], dict]:
    """
    Read WVS geographic sweep JSON and build per-country weight + distance matrices.

    Returns:
        weight_matrices:   dict[alpha3 → DataFrame (constructs × constructs, values = γ)]
        distance_matrices: dict[alpha3 → DataFrame (constructs × constructs, values = d)]
        construct_index:   canonical list of all constructs (sorted)
        coverage:          dict[alpha3 → list of constructs present in that country]
    """
    with open(sweep_path) as f:
        data = json.load(f)
    estimates = data.get("estimates", {})
    print(f"  Loaded {len(estimates)} WVS estimates")

    # ── Pass 1: collect all constructs and organize by country ────────────
    by_country: dict[str, dict[tuple[str, str], float]] = defaultdict(dict)
    all_constructs: set[str] = set()
    countries: set[str] = set()

    for key, est in estimates.items():
        gamma = est.get("dr_gamma")
        if gamma is None:
            continue
        alpha3, va, vb = parse_wvs_key(key)
        countries.add(alpha3)
        # Use short names for readability in CSV headers
        sa, sb = construct_short_name(va), construct_short_name(vb)
        all_constructs.add(sa)
        all_constructs.add(sb)
        # Store both directions (matrix is symmetric)
        by_country[alpha3][(sa, sb)] = gamma
        by_country[alpha3][(sb, sa)] = gamma

    construct_index = sorted(all_constructs)
    n = len(construct_index)
    idx = {c: i for i, c in enumerate(construct_index)}
    print(f"  {len(countries)} countries, {n} constructs")

    # ── Pass 2: build matrices ────────────────────────────────────────────
    weight_matrices = {}
    distance_matrices = {}
    coverage = {}

    for alpha3 in sorted(countries):
        pairs = by_country[alpha3]

        # Weight matrix (γ values, NaN where no estimate)
        W = np.full((n, n), np.nan)
        np.fill_diagonal(W, 0.0)
        for (sa, sb), gamma in pairs.items():
            i, j = idx[sa], idx[sb]
            W[i, j] = gamma

        # Distance matrix
        D = np.full((n, n), SENTINEL_DISTANCE)
        np.fill_diagonal(D, 0.0)
        for (sa, sb), gamma in pairs.items():
            i, j = idx[sa], idx[sb]
            D[i, j] = gamma_to_distance(gamma)

        weight_matrices[alpha3] = pd.DataFrame(
            W, index=construct_index, columns=construct_index
        )
        distance_matrices[alpha3] = pd.DataFrame(
            D, index=construct_index, columns=construct_index
        )

        # Coverage: which constructs have at least one non-NaN edge
        present = set()
        for sa, sb in pairs:
            present.add(sa)
            present.add(sb)
        coverage[alpha3] = sorted(present)

    return weight_matrices, distance_matrices, construct_index, coverage


def build_losmex_matrices(
    sweep_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """
    Read los_mex construct sweep JSON and build single weight + distance matrix.
    """
    with open(sweep_path) as f:
        data = json.load(f)
    estimates = data.get("estimates", {})
    print(f"  Loaded {len(estimates)} los_mex estimates")

    all_constructs: set[str] = set()
    pairs: dict[tuple[str, str], float] = {}

    for key, est in estimates.items():
        gamma = est.get("dr_gamma")
        if gamma is None:
            continue
        va, vb = parse_losmex_key(key)
        sa, sb = construct_short_name(va), construct_short_name(vb)
        all_constructs.add(sa)
        all_constructs.add(sb)
        pairs[(sa, sb)] = gamma
        pairs[(sb, sa)] = gamma

    construct_index = sorted(all_constructs)
    n = len(construct_index)
    idx = {c: i for i, c in enumerate(construct_index)}
    print(f"  {n} constructs, {len(pairs) // 2} unique pairs")

    W = np.full((n, n), np.nan)
    np.fill_diagonal(W, 0.0)
    D = np.full((n, n), SENTINEL_DISTANCE)
    np.fill_diagonal(D, 0.0)

    for (sa, sb), gamma in pairs.items():
        i, j = idx[sa], idx[sb]
        W[i, j] = gamma
        D[i, j] = gamma_to_distance(gamma)

    W_df = pd.DataFrame(W, index=construct_index, columns=construct_index)
    D_df = pd.DataFrame(D, index=construct_index, columns=construct_index)
    return W_df, D_df, construct_index


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── WVS geographic ────────────────────────────────────────────────────
    print("=" * 60)
    print("PHASE 0 — Convert sweep JSON → per-country matrices")
    print("=" * 60)

    if not WVS_SWEEP.exists():
        print(f"ERROR: {WVS_SWEEP} not found")
        sys.exit(1)

    print("\n[1/3] Building WVS per-country matrices...")
    W_dict, D_dict, wvs_constructs, coverage = build_wvs_matrices(WVS_SWEEP)

    # Save per-country CSVs
    for alpha3, W_df in W_dict.items():
        W_df.to_csv(OUTPUT_DIR / f"{alpha3}.csv")
        D_dict[alpha3].to_csv(OUTPUT_DIR / f"{alpha3}_distance.csv")
    print(f"  Wrote {len(W_dict)} weight + distance CSV pairs")

    # ── Los_mex ───────────────────────────────────────────────────────────
    print("\n[2/3] Building los_mex matrix...")
    if LOSMEX_SWEEP.exists():
        W_lm, D_lm, lm_constructs = build_losmex_matrices(LOSMEX_SWEEP)
        W_lm.to_csv(OUTPUT_DIR / "LOS_MEX.csv")
        D_lm.to_csv(OUTPUT_DIR / "LOS_MEX_distance.csv")
        print(f"  Wrote LOS_MEX.csv ({len(lm_constructs)} constructs)")
    else:
        print(f"  SKIP: {LOSMEX_SWEEP} not found")
        lm_constructs = []

    # ── Metadata files ────────────────────────────────────────────────────
    print("\n[3/3] Writing metadata...")

    # Construct index (canonical ordering for all matrix rows/cols)
    with open(OUTPUT_DIR / "construct_index.json", "w") as f:
        json.dump({"wvs": wvs_constructs, "los_mex": lm_constructs}, f, indent=2)

    # Per-country coverage
    with open(OUTPUT_DIR / "country_coverage.json", "w") as f:
        json.dump(coverage, f, indent=2)

    # Manifest for Julia scripts: list of all countries + paths
    countries = sorted(W_dict.keys())
    manifest = {
        "countries": countries,
        "n_constructs": len(wvs_constructs),
        "construct_index": wvs_constructs,
        "cultural_zones": {
            zone: [c for c in codes if c in countries]
            for zone, codes in CULTURAL_ZONES.items()
        },
        "country_zone": {c: COUNTRY_ZONE.get(c, "Unknown") for c in countries},
        "files": {
            alpha3: {
                "weight": str(OUTPUT_DIR / f"{alpha3}.csv"),
                "distance": str(OUTPUT_DIR / f"{alpha3}_distance.csv"),
            }
            for alpha3 in countries
        },
    }
    if lm_constructs:
        manifest["los_mex"] = {
            "weight": str(OUTPUT_DIR / "LOS_MEX.csv"),
            "distance": str(OUTPUT_DIR / "LOS_MEX_distance.csv"),
            "n_constructs": len(lm_constructs),
        }

    with open(OUTPUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # ── Summary stats ─────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  WVS countries:    {len(countries)}")
    print(f"  WVS constructs:   {len(wvs_constructs)}")
    min_cov = min(len(v) for v in coverage.values())
    max_cov = max(len(v) for v in coverage.values())
    print(f"  Coverage range:   {min_cov}–{max_cov} constructs per country")
    if lm_constructs:
        print(f"  Los_mex constructs: {len(lm_constructs)}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Manifest:         {OUTPUT_DIR / 'manifest.json'}")
    print("Done.")


if __name__ == "__main__":
    main()
