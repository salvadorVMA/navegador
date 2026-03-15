"""
Phase 3 — Build WVS Construct Variables

Reads wvs_svs_v1.json (Phase 2) + optional wvs_construct_overrides.json and creates
wvs_agg_* columns in the WVS Mexico Wave 7 DataFrame. Computes Cronbach's alpha
for each multi-item construct.

Same logic as build_construct_variables.py (los_mex), adapted for WVS:
  - Sentinel codes < 0 (not >=97)
  - Output scale: [1, 10] (same)
  - Column prefix: wvs_agg_ (instead of agg_)

Output:
  data/results/wvs_construct_manifest.json  — per-construct metadata
  (wvs_agg_* columns are added in-memory; saved to wvs_construct_cache.pkl for reuse)

Run:
  conda run -n nvg_py13_env python scripts/debug/build_wvs_constructs.py
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_loader import WVSLoader

SVS_PATH       = ROOT / "data" / "results" / "wvs_svs_v1.json"
OVERRIDES_PATH = ROOT / "data" / "results" / "wvs_construct_overrides.json"
MANIFEST_PATH  = ROOT / "data" / "results" / "wvs_construct_manifest.json"
CACHE_PATH     = ROOT / "data" / "results" / "wvs_construct_cache.pkl"

# Output scale
OUT_MIN, OUT_MAX = 1.0, 10.0


# ---------------------------------------------------------------------------
# Sentinel & cleaning
# ---------------------------------------------------------------------------

def _is_wvs_sentinel(v: float) -> bool:
    """WVS sentinel: any negative value."""
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
    scaled = OUT_MIN + (s - s_min) / (s_max - s_min) * (OUT_MAX - OUT_MIN)
    return scaled


# ---------------------------------------------------------------------------
# Reverse-code an item: new_value = (max + min) - value
# ---------------------------------------------------------------------------

def _reverse(s: pd.Series) -> pd.Series:
    s_min, s_max = s.min(), s.max()
    if pd.isna(s_min) or pd.isna(s_max) or s_max == s_min:
        return s
    return (s_max + s_min) - s


# ---------------------------------------------------------------------------
# Overrides loader
# ---------------------------------------------------------------------------

def _load_overrides() -> dict:
    if OVERRIDES_PATH.exists():
        with open(OVERRIDES_PATH) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_wvs_constructs(df: pd.DataFrame, svs: dict, overrides: dict) -> tuple[pd.DataFrame, list]:
    """
    Add wvs_agg_* columns to df. Returns (df_with_agg_cols, manifest_list).

    manifest_list: [{key, column, type, alpha, n_valid, n_items, ...}]
    """
    excluded = set(overrides.get("excluded", {}).keys())
    items_to_drop = overrides.get("items_to_drop", {})
    reverse_overrides = overrides.get("reverse_coded_overrides", {})
    type_overrides = overrides.get("construct_type_overrides", {})

    manifest = []
    n_built = 0
    n_skipped = 0

    for wvs_domain, dom_data in svs.get("domains", {}).items():
        # WVS_E → E, WVS_A → A, etc.
        domain_prefix = wvs_domain.replace("WVS_", "")
        for cluster in dom_data.get("construct_clusters", []):
            cname = cluster.get("name", "")
            key = f"WVS_{domain_prefix}|{cname}"
            agg_col = f"wvs_agg_{cname}"

            if key in excluded:
                manifest.append({"key": key, "column": None, "type": "excluded", "alpha": None, "n_valid": 0})
                n_skipped += 1
                continue

            raw_items = list(cluster.get("question_cluster", []))
            # Apply overrides: drop items
            drop_set = set(items_to_drop.get(key, []))
            items = [i for i in raw_items if i not in drop_set]

            reverse_set = set(cluster.get("reverse_coded_items", []))
            reverse_set |= set(reverse_overrides.get(key, []))

            ctype = type_overrides.get(key) or cluster.get("construct_type", "reflective_scale")

            # Filter to items actually in df
            available = [i for i in items if i in df.columns]
            if not available:
                print(f"  [{key}] SKIP — no items in dataframe")
                manifest.append({"key": key, "column": None, "type": "missing_items", "alpha": None, "n_valid": 0})
                n_skipped += 1
                continue

            # Build cleaned item DataFrame
            sub = pd.DataFrame()
            for col in available:
                cleaned = _clean(df[col])
                if col in reverse_set:
                    cleaned = _reverse(cleaned)
                sub[col] = cleaned

            n_valid = int(sub.dropna(how="all").shape[0])

            if ctype == "formative_index":
                # Binary presence: code==1 → 1, else 0; sum across items
                gateway_items = cluster.get("gateway_items", []) or []
                parts = []
                for col in available:
                    if col in gateway_items:
                        continue
                    s = _clean(df[col])
                    parts.append((s == 1).astype(float))
                if not parts:
                    agg = sub.iloc[:, 0]
                else:
                    agg = pd.concat(parts, axis=1).sum(axis=1, min_count=1)
                agg_scaled = _scale_to_output(agg)
                df[agg_col] = agg_scaled
                alpha = None
                manifest.append({
                    "key": key, "column": agg_col, "type": "formative_index",
                    "alpha": None, "n_valid": n_valid, "n_items": len(available),
                    "items": available, "reverse_coded": [],
                    "validated_index": cluster.get("validated_index"),
                })

            elif ctype == "single_item_tier2" or len(available) == 1:
                col = available[0]
                cleaned = _clean(df[col])
                if col in reverse_set:
                    cleaned = _reverse(cleaned)
                agg_scaled = _scale_to_output(cleaned)
                df[agg_col] = agg_scaled
                manifest.append({
                    "key": key, "column": agg_col, "type": "single_item_tier2",
                    "alpha": None, "n_valid": int(cleaned.notna().sum()), "n_items": 1,
                    "items": available, "reverse_coded": list(reverse_set & set(available)),
                    "validated_index": cluster.get("validated_index"),
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
                agg_scaled = _scale_to_output(agg)
                df[agg_col] = agg_scaled

                manifest.append({
                    "key": key, "column": agg_col, "type": tier,
                    "alpha": round(alpha, 4) if alpha is not None else None,
                    "n_valid": n_valid, "n_items": len(available),
                    "items": available,
                    "reverse_coded": list(reverse_set & set(available)),
                    "validated_index": cluster.get("validated_index"),
                    "notes": cluster.get("notes", ""),
                })

            n_built += 1
            alpha_str = f"α={manifest[-1]['alpha']:.3f}" if manifest[-1].get("alpha") is not None else "formative/single"
            print(f"  [{key}] {agg_col} | {manifest[-1]['type']} | {alpha_str} | N={manifest[-1]['n_valid']}")

    print(f"\nBuilt: {n_built} | Skipped: {n_skipped}")
    return df, manifest


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if not SVS_PATH.exists():
        print(f"ERROR: {SVS_PATH} not found. Run build_wvs_svs.py first.")
        sys.exit(1)

    print("Loading WVS Wave 7 Mexico data...")
    loader = WVSLoader()
    wvs_dict = loader.build_wvs_dict(waves=[7], countries=["MEX"])
    df = wvs_dict["enc_dict"]["WVS_W7_MEX"]["dataframe"].copy()

    print("Loading SVS and overrides...")
    with open(SVS_PATH) as f:
        svs = json.load(f)
    overrides = _load_overrides()

    print(f"Building WVS constructs...")
    df, manifest = build_wvs_constructs(df, svs, overrides)

    # Save manifest
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nManifest: {MANIFEST_PATH}")

    # Cache the enriched DataFrame for downstream scripts
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(df, f)
    print(f"Cache: {CACHE_PATH}")

    # Summary by tier
    from collections import Counter
    tier_counts = Counter(m["type"] for m in manifest)
    print("\nTier summary:")
    for t, n in sorted(tier_counts.items()):
        alphas = [m["alpha"] for m in manifest if m["type"] == t and m["alpha"] is not None]
        alpha_str = f"(mean α={np.mean(alphas):.3f})" if alphas else ""
        print(f"  {t}: {n} {alpha_str}")

    good = [m for m in manifest if m["type"] == "good"]
    print(f"\nGood constructs (α≥0.70): {len(good)}")
    for m in sorted(good, key=lambda x: -(x["alpha"] or 0)):
        val = m.get("validated_index") or ""
        print(f"  {m['key']} α={m['alpha']:.3f} N={m['n_valid']} {('→ ' + val) if val else ''}")


if __name__ == "__main__":
    main()
