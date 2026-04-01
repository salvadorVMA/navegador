"""
Merge per-wave geographic sweep JSONs into a unified all-wave γ-surface.

Reads wvs_geographic_sweep_w{1-7}.json and produces a single merged file
with all estimates keyed by context::var_a::var_b.

Output:
  data/results/wvs_all_wave_gamma_surface.json

Run:
  python scripts/debug/merge_wave_sweeps.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "data" / "results"
OUTPUT = RESULTS_DIR / "wvs_all_wave_gamma_surface.json"


def main():
    print("=" * 60)
    print("Merge per-wave geographic sweeps → unified γ-surface")
    print("=" * 60)

    all_estimates = {}
    all_skipped = {}
    wave_stats = {}

    for wave in range(1, 8):
        path = RESULTS_DIR / f"wvs_geographic_sweep_w{wave}.json"
        if not path.exists():
            print(f"  W{wave}: not found — skipping")
            continue

        with open(path) as f:
            data = json.load(f)

        estimates = data.get("estimates", {})
        skipped = data.get("skipped", {})
        n_sig = sum(1 for v in estimates.values() if v.get("excl_zero"))

        all_estimates.update(estimates)
        all_skipped.update(skipped)

        wave_stats[f"W{wave}"] = {
            "n_estimates": len(estimates),
            "n_skipped": len(skipped),
            "n_significant": n_sig,
            "pct_significant": round(100 * n_sig / max(len(estimates), 1), 1),
        }
        print(f"  W{wave}: {len(estimates):,} estimates, {n_sig} sig ({wave_stats[f'W{wave}']['pct_significant']}%)")

    # Count unique countries and construct pairs
    contexts = set()
    pairs = set()
    for key in all_estimates:
        parts = key.split("::")
        contexts.add(parts[0])
        if len(parts) == 3:
            pairs.add("::".join(sorted([parts[1], parts[2]])))

    print(f"\n  Total estimates: {len(all_estimates):,}")
    print(f"  Total skipped: {len(all_skipped):,}")
    print(f"  Unique contexts: {len(contexts)}")
    print(f"  Unique pairs: {len(pairs)}")

    output = {
        "metadata": {
            "description": "Unified WVS γ-surface (all waves × all countries)",
            "waves_included": sorted(wave_stats.keys()),
            "n_estimates": len(all_estimates),
            "n_contexts": len(contexts),
            "n_unique_pairs": len(pairs),
            "wave_stats": wave_stats,
        },
        "estimates": all_estimates,
        "skipped": all_skipped,
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f)
    print(f"\n  Saved: {OUTPUT}")
    print(f"  Size: {OUTPUT.stat().st_size / 1e6:.1f} MB")
    print("Done.")


if __name__ == "__main__":
    main()
