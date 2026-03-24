"""
Phase 0A — Multi-context WVS construct builder

Extends build_wvs_constructs.py to handle any (wave, country) combination.
For each context, resolves Q-codes (used in wvs_svs_v1.json for Wave 7) to
actual column names in the DataFrame:
  - Wave 7: Q-codes are column names directly
  - Waves 1-6 (time-series): Q-code → A-code via equivalences table

Outputs:
  data/results/wvs_multi_construct_manifest.json  — per-context metadata
  data/results/wvs_multi_construct_cache.pkl      — {context_key: enriched_df}

Run:
  conda run -n nvg_py13_env python scripts/debug/build_wvs_constructs_multi.py \
      --waves 7 --countries MEX
  conda run -n nvg_py13_env python scripts/debug/build_wvs_constructs_multi.py \
      --waves 1 2 3 4 5 6 7 --countries MEX   # temporal (Mexico all waves)
  conda run -n nvg_py13_env python scripts/debug/build_wvs_constructs_multi.py \
      --waves 7                                 # geographic (Wave 7, all countries)
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_loader import WVSLoader

SVS_PATH       = ROOT / "data" / "results" / "wvs_svs_v1.json"
OVERRIDES_PATH = ROOT / "data" / "results" / "wvs_construct_overrides.json"
MANIFEST_PATH  = ROOT / "data" / "results" / "wvs_multi_construct_manifest.json"
CACHE_PATH     = ROOT / "data" / "results" / "wvs_multi_construct_cache.pkl"

OUT_MIN, OUT_MAX = 1.0, 10.0


# ---------------------------------------------------------------------------
# Sentinel & cleaning (WVS: negative values are sentinels)
# ---------------------------------------------------------------------------

def _is_wvs_sentinel(v: float) -> bool:
    return v < 0


def _clean(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return s.where(~s.apply(lambda v: _is_wvs_sentinel(v) if pd.notna(v) else False))


# ---------------------------------------------------------------------------
# Cronbach's alpha
# ---------------------------------------------------------------------------

def _cronbach_alpha(df_items: pd.DataFrame) -> float | None:
    df_c = df_items.dropna()
    if len(df_c) < 10 or df_items.shape[1] < 2:
        return None
    n_items = df_items.shape[1]
    item_vars = df_c.var(ddof=1)
    total_var = df_c.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return None
    alpha = (n_items / (n_items - 1)) * (1 - item_vars.sum() / total_var)
    return float(np.clip(alpha, -1.0, 1.0))


# ---------------------------------------------------------------------------
# Scale to [1, 10]
# ---------------------------------------------------------------------------

def _scale_to_output(s: pd.Series) -> pd.Series:
    s_min, s_max = s.min(), s.max()
    if s_max == s_min:
        return s.where(s.notna(), np.nan).map(lambda v: OUT_MIN if pd.notna(v) else np.nan)
    return OUT_MIN + (s - s_min) / (s_max - s_min) * (OUT_MAX - OUT_MIN)


def _reverse(s: pd.Series) -> pd.Series:
    s_min, s_max = s.min(), s.max()
    if pd.isna(s_min) or pd.isna(s_max) or s_max == s_min:
        return s
    return (s_max + s_min) - s


# ---------------------------------------------------------------------------
# Q-code → actual column name resolver
# ---------------------------------------------------------------------------

def build_qcode_resolver(equivalences: pd.DataFrame, wave: int, df_columns: list[str]) -> dict[str, str]:
    """Build a mapping from SVS Q-codes (Wave 7) to actual column names in the DataFrame.

    For Wave 7: Q-codes are column names directly.
    For waves 1-6: Q-code → A-code via equivalences table.

    Returns {q_code: actual_column_name} for all resolvable Q-codes.
    """
    col_set = set(df_columns)
    resolver = {}

    if wave == 7:
        # Wave 7: Q-codes are the actual column names
        for qc in col_set:
            resolver[qc] = qc
        return resolver

    # Waves 1-6: time-series CSV uses A-codes
    # SVS Q-codes are from Wave 7 → look up their A-code equivalents
    wave_col = f"w{wave}"
    for _, row in equivalences.iterrows():
        q7_code = row.get("w7")
        a_code = row.get("a_code")
        wave_present = row.get(wave_col)

        if not q7_code or pd.isna(q7_code):
            continue

        # The question must exist in this wave
        if not wave_present or pd.isna(wave_present):
            continue

        # In time-series CSV, column name is the A-code
        if a_code and a_code in col_set:
            resolver[q7_code] = a_code

    return resolver


# ---------------------------------------------------------------------------
# Core builder (single context)
# ---------------------------------------------------------------------------

def build_wvs_constructs_context(
    df: pd.DataFrame,
    svs: dict,
    overrides: dict,
    resolver: dict[str, str],
    context_label: str = "",
) -> tuple[pd.DataFrame, list[dict]]:
    """Add wvs_agg_* columns to df for one context. Returns (df, manifest_list)."""
    excluded = set(overrides.get("excluded", {}).keys())
    items_to_drop = overrides.get("items_to_drop", {})
    reverse_overrides = overrides.get("reverse_coded_overrides", {})
    type_overrides = overrides.get("construct_type_overrides", {})

    manifest = []
    n_built = 0
    n_skipped = 0

    for wvs_domain, dom_data in svs.get("domains", {}).items():
        domain_prefix = wvs_domain.replace("WVS_", "")
        for cluster in dom_data.get("construct_clusters", []):
            cname = cluster.get("name", "")
            key = f"WVS_{domain_prefix}|{cname}"
            agg_col = f"wvs_agg_{cname}"

            if key in excluded:
                manifest.append({"key": key, "column": None, "type": "excluded",
                                 "alpha": None, "n_valid": 0})
                n_skipped += 1
                continue

            raw_items = list(cluster.get("question_cluster", []))
            drop_set = set(items_to_drop.get(key, []))
            items = [i for i in raw_items if i not in drop_set]

            reverse_set = set(cluster.get("reverse_coded_items", []))
            reverse_set |= set(reverse_overrides.get(key, []))

            ctype = type_overrides.get(key) or cluster.get("construct_type", "reflective_scale")

            # Resolve Q-codes to actual column names in this context
            resolved = [(qc, resolver[qc]) for qc in items if qc in resolver]
            available_qcodes = [qc for qc, _ in resolved]
            available_cols = [col for _, col in resolved]

            if not available_cols:
                manifest.append({"key": key, "column": None, "type": "missing_items",
                                 "alpha": None, "n_valid": 0, "n_items": 0, "items": []})
                n_skipped += 1
                continue

            # Build cleaned item DataFrame (using actual column names)
            sub = pd.DataFrame()
            for qc, col in resolved:
                cleaned = _clean(df[col])
                if qc in reverse_set:
                    cleaned = _reverse(cleaned)
                sub[col] = cleaned

            n_valid = int(sub.dropna(how="all").shape[0])

            if ctype == "formative_index":
                gateway_items = set(cluster.get("gateway_items", []) or [])
                # Resolve gateway items too
                gateway_cols = {resolver.get(g, g) for g in gateway_items}
                parts = []
                for qc, col in resolved:
                    if col in gateway_cols:
                        continue
                    s = _clean(df[col])
                    parts.append((s == 1).astype(float))
                if not parts:
                    agg = sub.iloc[:, 0]
                else:
                    agg = pd.concat(parts, axis=1).sum(axis=1, min_count=1)
                df[agg_col] = _scale_to_output(agg)
                alpha = None
                manifest.append({
                    "key": key, "column": agg_col, "type": "formative_index",
                    "alpha": None, "n_valid": n_valid,
                    "n_items": len(available_cols), "items": available_qcodes,
                    "resolved_cols": available_cols,
                })

            elif ctype == "single_item_tier2" or len(available_cols) == 1:
                qc, col = resolved[0]
                cleaned = _clean(df[col])
                if qc in reverse_set:
                    cleaned = _reverse(cleaned)
                df[agg_col] = _scale_to_output(cleaned)
                manifest.append({
                    "key": key, "column": agg_col, "type": "single_item_tier2",
                    "alpha": None, "n_valid": int(cleaned.notna().sum()),
                    "n_items": 1, "items": available_qcodes,
                    "resolved_cols": available_cols,
                })

            else:  # reflective_scale
                alpha = _cronbach_alpha(sub)
                if alpha is None or np.isnan(alpha):
                    tier = "tier3_caveat"
                elif alpha >= 0.70:
                    tier = "good"
                elif alpha >= 0.50:
                    tier = "questionable"
                else:
                    tier = "tier3_caveat"

                agg = sub.mean(axis=1, skipna=True)
                df[agg_col] = _scale_to_output(agg)
                manifest.append({
                    "key": key, "column": agg_col, "type": tier,
                    "alpha": round(alpha, 4) if alpha is not None else None,
                    "n_valid": n_valid,
                    "n_items": len(available_cols), "items": available_qcodes,
                    "resolved_cols": available_cols,
                })

            n_built += 1

    return df, manifest


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-context WVS construct builder")
    parser.add_argument("--waves", nargs="+", type=int, default=[7],
                        help="WVS waves to process (default: 7)")
    parser.add_argument("--countries", nargs="*", default=None,
                        help="ISO alpha-3 codes (default: all countries in each wave)")
    parser.add_argument("--manifest-path", type=str, default=str(MANIFEST_PATH))
    parser.add_argument("--cache-path", type=str, default=str(CACHE_PATH))
    args = parser.parse_args()

    if not SVS_PATH.exists():
        print(f"ERROR: {SVS_PATH} not found. Run build_wvs_svs.py first.")
        sys.exit(1)

    with open(SVS_PATH) as f:
        svs = json.load(f)
    overrides = json.load(open(OVERRIDES_PATH)) if OVERRIDES_PATH.exists() else {}

    print(f"Loading WVS data (waves={args.waves}, countries={args.countries})...")
    t0 = time.time()
    loader = WVSLoader()
    wvs_dict = loader.build_wvs_dict(waves=args.waves, countries=args.countries)
    print(f"  Loaded in {time.time()-t0:.1f}s")

    enc_dict = wvs_dict["enc_dict"]
    all_manifests: dict[str, list[dict]] = {}
    all_dfs: dict[str, pd.DataFrame] = {}

    for context_key, ctx_data in sorted(enc_dict.items()):
        df = ctx_data["dataframe"].copy()
        # Parse wave from key: WVS_W7_MEX → 7
        wave = int(context_key.split("_")[1][1:])
        alpha3 = context_key.split("_")[2]

        print(f"\n{'='*60}")
        print(f"Context: {context_key} (wave={wave}, country={alpha3}, n={len(df)})")

        resolver = build_qcode_resolver(loader.equivalences, wave, list(df.columns))
        n_resolved = sum(1 for qc in _all_svs_qcodes(svs) if qc in resolver)
        n_total_qc = len(_all_svs_qcodes(svs))
        print(f"  Q-code resolution: {n_resolved}/{n_total_qc} items available")

        df, ctx_manifest = build_wvs_constructs_context(
            df, svs, overrides, resolver, context_label=context_key
        )

        built = [m for m in ctx_manifest if m.get("column")]
        skipped = [m for m in ctx_manifest if not m.get("column")]
        print(f"  Built: {len(built)} constructs | Skipped: {len(skipped)}")

        # Tier summary
        from collections import Counter
        tier_counts = Counter(m["type"] for m in ctx_manifest if m.get("column"))
        for t, n in sorted(tier_counts.items()):
            print(f"    {t}: {n}")

        all_manifests[context_key] = ctx_manifest
        all_dfs[context_key] = df

    # Save manifest
    manifest_path = Path(args.manifest_path)
    with open(manifest_path, "w") as f:
        json.dump(all_manifests, f, ensure_ascii=False, indent=2)
    print(f"\nManifest: {manifest_path}")

    # Save cache
    cache_path = Path(args.cache_path)
    with open(cache_path, "wb") as f:
        pickle.dump(all_dfs, f)
    print(f"Cache: {cache_path} ({len(all_dfs)} contexts)")

    # Summary table
    print(f"\n{'='*60}")
    print(f"{'Context':<20} {'Built':>6} {'Skipped':>8} {'N_resp':>8}")
    print(f"{'-'*20} {'-'*6} {'-'*8} {'-'*8}")
    for ctx in sorted(all_manifests.keys()):
        m = all_manifests[ctx]
        built = sum(1 for x in m if x.get("column"))
        skip = sum(1 for x in m if not x.get("column"))
        n = len(all_dfs[ctx])
        print(f"{ctx:<20} {built:>6} {skip:>8} {n:>8}")


def _all_svs_qcodes(svs: dict) -> set[str]:
    """Extract all Q-codes referenced in the SVS."""
    qcodes = set()
    for dom_data in svs.get("domains", {}).values():
        for cluster in dom_data.get("construct_clusters", []):
            qcodes.update(cluster.get("question_cluster", []))
    return qcodes


if __name__ == "__main__":
    main()
