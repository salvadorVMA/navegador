"""
export_constructs_for_julia.py — Export los_mex construct DataFrames to CSV for Julia sweep

Loads the los_mex survey data, builds all agg_* construct columns, then exports
one CSV per domain containing the SES columns + all agg_* columns for that domain.

Also writes a pairs CSV with all v5 sweep pairs in the format expected by Julia's
run_sweep: columns var_a, var_b in "agg_colname|DOMAIN" format.

Outputs (into data/julia_bridge/):
  {DOMAIN}.csv         — one file per domain (SES + agg_* cols)
  v5_pairs.csv         — all 4135 pairs from construct_dr_sweep_v5.json
  manifest.json        — domain → CSV path mapping

Run:
  conda run -n nvg_py13_env python scripts/debug/export_constructs_for_julia.py
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))

import pandas as pd

OUT_DIR = ROOT / "data" / "julia_bridge"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SES_COLS = ["sexo", "edad", "escol", "Tam_loc"]

def load_data():
    """Load los_mex_dict.json and build construct variables."""
    print("Loading dataset_knowledge (may take 10-15s)...")
    t0 = time.time()
    import dataset_knowledge as dk
    enc_dict = dk.enc_dict
    enc_nom_dict = dk.enc_nom_dict
    print(f"  Loaded {len(enc_dict)} surveys in {time.time()-t0:.1f}s")
    return enc_dict, enc_nom_dict

def build_constructs(enc_dict: dict, enc_nom_dict: dict) -> dict:
    """Build agg_* construct columns in each survey DataFrame."""
    print("Building construct variables (v4 SVS)...")
    t0 = time.time()
    from build_construct_variables import build_v4_constructs
    # enc_nom_dict_rev: survey_key -> short_name
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}
    manifest = build_v4_constructs(enc_dict, enc_nom_dict_rev)
    print(f"  {len(manifest)} constructs built in {time.time()-t0:.1f}s")
    return enc_dict, manifest

def get_domain_df(enc_dict: dict, domain: str, agg_cols: list[str]) -> pd.DataFrame | None:
    """
    Merge across all surveys for a domain to get one combined DataFrame.
    Each survey has SES + agg_ columns. We pool all surveys for that domain.
    """
    frames = []
    for survey_key, val in enc_dict.items():
        df = val.get("dataframe")
        if df is None:
            continue
        # Check if this survey has any agg_ columns for this domain
        present_agg = [c for c in agg_cols if c in df.columns]
        if not present_agg:
            continue
        present_ses = [c for c in SES_COLS if c in df.columns]
        keep_cols = present_ses + present_agg
        sub = df[keep_cols].copy()
        frames.append(sub)

    if not frames:
        return None

    # Concatenate all surveys for this domain
    combined = pd.concat(frames, ignore_index=True)
    return combined

def main():
    # ── Load data ──────────────────────────────────────────────────────────
    enc_dict, enc_nom_dict = load_data()
    enc_dict, manifest_list = build_constructs(enc_dict, enc_nom_dict)

    # ── Collect all agg_* columns per domain from v5 pairs ────────────────
    v5_path = ROOT / "data" / "results" / "construct_dr_sweep_v5.json"
    with open(v5_path) as f:
        v5_data = json.load(f)
    v5_estimates = v5_data.get("estimates", v5_data)

    # Extract unique (construct, domain) pairs
    by_domain: dict[str, set[str]] = {}
    pairs: list[tuple[str, str]] = []
    for k in v5_estimates.keys():
        a, b = k.split("::")
        col_a, dom_a = a.rsplit("|", 1)
        col_b, dom_b = b.rsplit("|", 1)
        by_domain.setdefault(dom_a, set()).add(col_a)
        by_domain.setdefault(dom_b, set()).add(col_b)
        pairs.append((a, b))

    print(f"\nDomains: {sorted(by_domain.keys())}")
    print(f"Total pairs: {len(pairs)}")

    # ── Export domain CSVs ─────────────────────────────────────────────────
    manifest = {}
    print("\nExporting domain CSVs...")
    for domain, agg_cols in sorted(by_domain.items()):
        agg_list = sorted(agg_cols)
        df = get_domain_df(enc_dict, domain, agg_list)
        if df is None or len(df) == 0:
            print(f"  {domain}: no data found, skipping")
            continue

        out_path = OUT_DIR / f"{domain}.csv"
        df.to_csv(out_path, index=False)
        manifest[domain] = str(out_path)
        n_agg = sum(1 for c in df.columns if c.startswith("agg_"))
        print(f"  {domain}: {len(df):,} rows, {n_agg} constructs → {out_path.name}")

    # ── Write pairs CSV ───────────────────────────────────────────────────
    pairs_path = OUT_DIR / "v5_pairs.csv"
    pairs_df = pd.DataFrame(pairs, columns=["var_a", "var_b"])
    pairs_df.to_csv(pairs_path, index=False)
    print(f"\nPairs CSV: {pairs_path}  ({len(pairs_df)} rows)")

    # ── Write manifest ─────────────────────────────────────────────────────
    manifest_path = OUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest:  {manifest_path}")
    print(f"\nDone. {len(manifest)} domains exported.")

if __name__ == "__main__":
    main()
