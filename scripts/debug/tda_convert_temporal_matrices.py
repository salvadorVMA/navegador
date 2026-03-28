"""
Phase 4 (Temporal) — Convert temporal sweep JSON to per-wave weight matrices.

Reads wvs_temporal_sweep_mex.json and produces one CSV weight/distance matrix
per wave (MEX_W3..MEX_W7), plus temporal metadata.

Input:
  data/results/wvs_temporal_sweep_mex.json

Output (to data/tda/temporal/):
  MEX_W{n}.csv              — weight matrix (γ values)
  MEX_W{n}_distance.csv     — distance matrix (1/|γ|)
  manifest.json             — per-wave metadata + file paths
  temporal_edge_table.csv   — all edges across waves (for trend analysis)

Run:
  python scripts/debug/tda_convert_temporal_matrices.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SWEEP_PATH = ROOT / "data" / "results" / "wvs_temporal_sweep_mex.json"
OUTPUT_DIR = ROOT / "data" / "tda" / "temporal"
EPSILON = 0.001
SENTINEL_DISTANCE = 9999.0

# Wave year mapping (for labeling)
WAVE_YEARS = {3: 1996, 4: 2001, 5: 2007, 6: 2012, 7: 2018}


def parse_key(full_key: str) -> tuple[int, str, str]:
    """Parse 'WVS_W7_MEX::va::vb' → (wave_number, va, vb)."""
    parts = full_key.split("::")
    # WVS_W7_MEX → extract 7
    wave = int(parts[0].split("_")[1][1:])  # "W7" → 7
    return wave, parts[1], parts[2]


def short_name(name: str) -> str:
    if name.startswith("wvs_agg_"):
        return name[len("wvs_agg_"):]
    return name


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Temporal Phase 4 — Convert sweep to per-wave matrices")
    print("=" * 60)

    with open(SWEEP_PATH) as f:
        data = json.load(f)
    estimates = data.get("estimates", {})
    print(f"Total estimates: {len(estimates)}")

    # Organize by wave
    by_wave: dict[int, dict[tuple[str, str], float]] = defaultdict(dict)
    all_constructs: set[str] = set()

    for key, est in estimates.items():
        gamma = est.get("dr_gamma")
        if gamma is None:
            continue
        wave, va, vb = parse_key(key)
        sa, sb = short_name(va), short_name(vb)
        all_constructs.add(sa)
        all_constructs.add(sb)
        by_wave[wave][(sa, sb)] = gamma
        by_wave[wave][(sb, sa)] = gamma

    construct_index = sorted(all_constructs)
    n = len(construct_index)
    idx = {c: i for i, c in enumerate(construct_index)}
    waves = sorted(by_wave.keys())
    print(f"Waves: {waves}, Constructs (union): {n}")

    # Build per-wave matrices
    manifest = {
        "waves": waves,
        "wave_years": {str(w): WAVE_YEARS.get(w, 0) for w in waves},
        "n_constructs": n,
        "construct_index": construct_index,
        "files": {},
    }

    # Also build edge table for trend analysis
    edge_rows = []

    for wave in waves:
        pairs = by_wave[wave]
        W = np.full((n, n), np.nan)
        np.fill_diagonal(W, 0.0)
        D = np.full((n, n), SENTINEL_DISTANCE)
        np.fill_diagonal(D, 0.0)

        for (sa, sb), gamma in pairs.items():
            i, j = idx[sa], idx[sb]
            W[i, j] = gamma
            D[i, j] = 1.0 / max(abs(gamma), EPSILON)

        w_df = pd.DataFrame(W, index=construct_index, columns=construct_index)
        d_df = pd.DataFrame(D, index=construct_index, columns=construct_index)

        w_path = OUTPUT_DIR / f"MEX_W{wave}.csv"
        d_path = OUTPUT_DIR / f"MEX_W{wave}_distance.csv"
        w_df.to_csv(w_path)
        d_df.to_csv(d_path)

        # Coverage for this wave
        present = set()
        for sa, sb in pairs:
            present.add(sa)
            present.add(sb)

        manifest["files"][f"W{wave}"] = {
            "weight": str(w_path),
            "distance": str(d_path),
            "n_pairs": len(pairs) // 2,
            "n_constructs_present": len(present),
            "year": WAVE_YEARS.get(wave, 0),
        }

        # Edge rows for trend table
        seen = set()
        for (sa, sb), gamma in pairs.items():
            pair_key = "::".join(sorted([sa, sb]))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            edge_rows.append({
                "wave": wave,
                "year": WAVE_YEARS.get(wave, 0),
                "construct_a": sa,
                "construct_b": sb,
                "gamma": gamma,
            })

        n_pairs = len(pairs) // 2
        print(f"  W{wave} ({WAVE_YEARS.get(wave, '?')}): {n_pairs} pairs, {len(present)} constructs")

    # Save manifest
    with open(OUTPUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Save edge table
    edge_df = pd.DataFrame(edge_rows)
    edge_df.to_csv(OUTPUT_DIR / "temporal_edge_table.csv", index=False)
    print(f"\nEdge table: {len(edge_df)} rows ({len(edge_df['wave'].unique())} waves)")

    print(f"Output: {OUTPUT_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
