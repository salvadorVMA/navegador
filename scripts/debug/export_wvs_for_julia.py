"""
Phase 0B — Export WVS construct DataFrames to CSV for Julia sweep

Reads wvs_multi_construct_cache.pkl (from build_wvs_constructs_multi.py)
and exports one CSV per (wave, country) context containing SES vars + wvs_agg_* columns.

Also writes a pairs CSV (all cross-domain construct pairs) and manifest JSON.

For within-survey sweeps, both constructs come from the same CSV — unlike los_mex
where each domain is a separate survey.

Output structure:
  data/julia_bridge_wvs/
    WVS_W7_MEX.csv          # one file per context
    WVS_W7_ARG.csv
    WVS_W1_MEX.csv           # temporal
    ...
    wvs_pairs.csv             # all cross-domain construct pairs
    wvs_manifest.json         # {context_key: {csv_path, n_rows, constructs}}

Run:
  conda run -n nvg_py13_env python scripts/debug/export_wvs_for_julia.py
  conda run -n nvg_py13_env python scripts/debug/export_wvs_for_julia.py --cache /path/to/cache.pkl
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from itertools import combinations
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DEFAULT_CACHE = ROOT / "data" / "results" / "wvs_multi_construct_cache.pkl"
DEFAULT_MANIFEST_IN = ROOT / "data" / "results" / "wvs_multi_construct_manifest.json"
OUT_DIR = ROOT / "data" / "julia_bridge_wvs"

SES_COLS = ["sexo", "edad", "escol", "Tam_loc"]
AGG_PREFIX = "wvs_agg_"


def load_cache(path: Path) -> dict[str, pd.DataFrame]:
    with open(path, "rb") as f:
        return pickle.load(f)


def load_manifest(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def get_domain_for_construct(key: str) -> str:
    """Extract domain from construct key: WVS_A|name → WVS_A"""
    return key.split("|")[0]


def build_cross_domain_pairs(manifest_entries: list[dict]) -> list[tuple[str, str]]:
    """Build all cross-domain construct pairs from a manifest.

    Same logic as los_mex sweep: only pairs where domain_a != domain_b.
    Returns list of (col_a|domain_a, col_b|domain_b) tuples.
    """
    # Collect built constructs with their domain
    constructs = []
    for m in manifest_entries:
        if not m.get("column"):
            continue
        domain = get_domain_for_construct(m["key"])
        constructs.append((m["column"], domain))

    # All cross-domain pairs
    pairs = []
    for (col_a, dom_a), (col_b, dom_b) in combinations(constructs, 2):
        if dom_a != dom_b:
            pairs.append((f"{col_a}|{dom_a}", f"{col_b}|{dom_b}"))
    return pairs


def main():
    parser = argparse.ArgumentParser(description="Export WVS constructs for Julia sweep")
    parser.add_argument("--cache", type=str, default=str(DEFAULT_CACHE))
    parser.add_argument("--manifest", type=str, default=str(DEFAULT_MANIFEST_IN))
    parser.add_argument("--out-dir", type=str, default=str(OUT_DIR))
    args = parser.parse_args()

    cache_path = Path(args.cache)
    manifest_path = Path(args.manifest)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading cache: {cache_path}")
    dfs = load_cache(cache_path)
    print(f"Loading manifest: {manifest_path}")
    manifest_data = load_manifest(manifest_path)

    julia_manifest = {}
    all_pairs_set = set()

    for context_key in sorted(dfs.keys()):
        df = dfs[context_key]
        ctx_manifest = manifest_data.get(context_key, [])

        # Select SES + wvs_agg_* columns
        ses_present = [c for c in SES_COLS if c in df.columns]
        agg_cols = sorted([c for c in df.columns if c.startswith(AGG_PREFIX)])

        if not agg_cols:
            print(f"  {context_key}: no constructs, skipping")
            continue

        keep = ses_present + agg_cols
        out_df = df[keep].copy()

        # Export CSV
        csv_path = out_dir / f"{context_key}.csv"
        out_df.to_csv(csv_path, index=False)

        # Build pairs for this context
        pairs = build_cross_domain_pairs(ctx_manifest)
        all_pairs_set.update(pairs)

        julia_manifest[context_key] = {
            "csv_path": str(csv_path.resolve()),
            "n_rows": len(out_df),
            "n_constructs": len(agg_cols),
            "constructs": agg_cols,
        }
        print(f"  {context_key}: {len(out_df):,} rows, {len(agg_cols)} constructs, "
              f"{len(pairs)} pairs → {csv_path.name}")

    # Write pairs CSV (union of all pairs across contexts)
    pairs_list = sorted(all_pairs_set)
    pairs_path = out_dir / "wvs_pairs.csv"
    pairs_df = pd.DataFrame(pairs_list, columns=["var_a", "var_b"])
    pairs_df.to_csv(pairs_path, index=False)
    print(f"\nPairs CSV: {pairs_path} ({len(pairs_df)} pairs)")

    # Write manifest
    manifest_out = out_dir / "wvs_manifest.json"
    with open(manifest_out, "w") as f:
        json.dump(julia_manifest, f, indent=2)
    print(f"Manifest:  {manifest_out}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Exported {len(julia_manifest)} contexts to {out_dir}")
    print(f"Total unique pairs: {len(pairs_list)}")


if __name__ == "__main__":
    main()
