"""
Build construct variables from v4 SVS into survey DataFrames.

Reads semantic_variable_selection_v4.json and creates one numeric column
per construct in each survey DataFrame. Handles:
  - Good/questionable constructs: mean of items (with reverse coding)
  - Tier 2 constructs (alpha 0.3-0.4): single best item
  - Formative indices: additive count of gateway items
  - Sentinel filtering before aggregation

Output columns are named `agg_{construct_name}` and scaled to [1, 10].

Usage:
    # As module:
    from build_construct_variables import build_v4_constructs
    enc_dict = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    # Standalone sanity check:
    python scripts/debug/build_construct_variables.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V4_SVS_PATH = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"
FIXES_PATH = ROOT / "data" / "results" / "construct_structural_fixes.json"


def _is_sentinel(v: float) -> bool:
    return v >= 97 or v < 0


def _clean_series(series: pd.Series) -> pd.Series:
    """Convert to numeric, replace sentinels with NaN."""
    s = pd.to_numeric(series, errors="coerce")
    s = s.where(~s.apply(lambda v: _is_sentinel(v) if pd.notna(v) else False))
    return s


def build_v4_constructs(
    enc_dict: dict,
    enc_nom_dict_rev: dict,
    svs_path: Path = V4_SVS_PATH,
    fixes_path: Path = FIXES_PATH,
    alpha_tier2_threshold: float = 0.4,
) -> Tuple[dict, List[dict]]:
    """
    Build construct variables from v4 SVS into enc_dict DataFrames.

    Parameters
    ----------
    enc_dict : dict
        {survey_name: {"dataframe": pd.DataFrame, ...}}. Modified in-place.
    enc_nom_dict_rev : dict
        {domain_code: survey_name} mapping.
    svs_path : Path
        Path to semantic_variable_selection_v4.json.
    fixes_path : Path
        Path to construct_structural_fixes.json (for alpha/tier info).

    Returns
    -------
    enc_dict : dict
        Modified in-place with new agg_* columns.
    manifest : list[dict]
        Per-construct metadata: column name, type, alpha, n_valid, etc.
    """
    with open(svs_path) as f:
        svs = json.load(f)

    # Load final stats for tier classification
    stats = {}
    if fixes_path.exists():
        with open(fixes_path) as f:
            fixes = json.load(f)
        stats = fixes.get("final_stats", {})

    manifest = []
    n_built = 0

    for domain, dom_data in svs.get("domains", {}).items():
        survey_name = enc_nom_dict_rev.get(domain)
        if not survey_name or survey_name not in enc_dict:
            continue
        df = enc_dict[survey_name].get("dataframe")
        if not isinstance(df, pd.DataFrame):
            continue

        for cluster in dom_data.get("construct_clusters", []):
            cname = cluster["name"]
            key = f"{domain}|{cname}"
            construct_type = cluster.get("construct_type", "reflective_scale")
            reverse_items = cluster.get("reverse_coded_items", [])

            qids_raw = cluster.get("question_cluster", [])
            qids_bare = [q.split("|")[0] if "|" in q else q for q in qids_raw]
            cols = [q for q in qids_bare if q in df.columns]

            if not cols:
                manifest.append({
                    "key": key, "column": None, "type": "no_columns",
                    "alpha": None, "n_valid": 0,
                })
                continue

            agg_col = f"agg_{cname}"
            st = stats.get(key, {})
            alpha = st.get("alpha")

            # ── Formative index: additive count of gateway items ──
            if construct_type == "formative_index":
                gateway = cluster.get("gateway_items", [])
                gateway_cols = [g for g in gateway if g in df.columns]
                if not gateway_cols:
                    gateway_cols = cols  # fallback

                # Binary recode + sum
                sub = pd.DataFrame(index=df.index)
                for col in gateway_cols:
                    s = _clean_series(df[col])
                    if s.dropna().nunique() <= 2:
                        sub[col] = (s == 1).astype(float)
                        sub.loc[s.isna(), col] = np.nan
                    else:
                        mn, mx = s.min(), s.max()
                        if mx > mn:
                            sub[col] = (s - mn) / (mx - mn)
                        else:
                            sub[col] = 0.0

                raw = sub.sum(axis=1, min_count=1)
                n_valid = int(raw.dropna().shape[0])

                # Scale to [1, 10]
                lo, hi = raw.min(), raw.max()
                if pd.notna(lo) and pd.notna(hi) and hi > lo:
                    scaled = 1.0 + 9.0 * (raw - lo) / (hi - lo)
                else:
                    scaled = raw * 0.0 + 5.0

                df[agg_col] = np.nan
                df.loc[scaled.dropna().index, agg_col] = scaled.dropna().astype(float)
                n_built += 1

                manifest.append({
                    "key": key, "column": agg_col, "var_id": f"{agg_col}|{domain}",
                    "type": "formative_index", "alpha": alpha,
                    "n_items": len(gateway_cols), "n_valid": n_valid,
                    "gateway_items": gateway_cols,
                })
                continue

            # ── Tier 2 (alpha < threshold): single best item ──
            if alpha is not None and alpha < alpha_tier2_threshold and len(cols) >= 2:
                # Pick item with highest item-total correlation
                sub = pd.DataFrame()
                for col in cols:
                    sub[col] = _clean_series(df[col])
                clean = sub.dropna()

                if len(clean) >= 10 and len(cols) >= 2:
                    best_col = None
                    best_r = -999
                    for col in cols:
                        others = [c for c in cols if c != col]
                        if not others:
                            continue
                        total = clean[others].sum(axis=1)
                        r = clean[col].corr(total, method="spearman")
                        if pd.notna(r) and r > best_r:
                            best_r = r
                            best_col = col
                    if best_col is None:
                        best_col = cols[0]
                else:
                    best_col = cols[0]

                # Use the single item directly (already ordinal)
                s = _clean_series(df[best_col])
                n_valid = int(s.dropna().shape[0])

                # Scale to [1, 10]
                lo, hi = s.min(), s.max()
                if pd.notna(lo) and pd.notna(hi) and hi > lo:
                    scaled = 1.0 + 9.0 * (s - lo) / (hi - lo)
                else:
                    scaled = s * 0.0 + 5.0

                df[agg_col] = np.nan
                df.loc[scaled.dropna().index, agg_col] = scaled.dropna().astype(float)
                n_built += 1

                manifest.append({
                    "key": key, "column": agg_col, "var_id": f"{agg_col}|{domain}",
                    "type": "single_item_tier2", "alpha": alpha,
                    "selected_item": best_col, "item_total_r": round(best_r, 3) if best_r > -999 else None,
                    "n_valid": n_valid,
                })
                continue

            # ── Standard aggregation (mean of items, with reverse coding) ──
            sub = pd.DataFrame()
            for col in cols:
                sub[col] = _clean_series(df[col])

            # Apply reverse coding
            if reverse_items:
                for col in reverse_items:
                    if col in sub.columns:
                        s = sub[col]
                        mx = s.max()
                        mn = s.min()
                        if pd.notna(mx) and pd.notna(mn) and mx > mn:
                            sub[col] = mx + mn - s

            clean = sub.dropna()
            if len(clean) < 10:
                # Try pairwise: use mean with min_count
                raw = sub.mean(axis=1, skipna=True)
                # Only keep rows with at least half the items
                min_count = max(1, len(cols) // 2)
                valid_mask = sub.notna().sum(axis=1) >= min_count
                raw = raw.where(valid_mask)
            else:
                raw = clean.mean(axis=1)

            n_valid = int(raw.dropna().shape[0])

            if n_valid < 10:
                manifest.append({
                    "key": key, "column": None, "type": "insufficient_data",
                    "alpha": alpha, "n_valid": n_valid,
                })
                continue

            # Scale to [1, 10]
            lo, hi = raw.min(), raw.max()
            if pd.notna(lo) and pd.notna(hi) and hi > lo:
                scaled = 1.0 + 9.0 * (raw - lo) / (hi - lo)
            else:
                scaled = raw * 0.0 + 5.0

            df[agg_col] = np.nan
            df.loc[scaled.dropna().index, agg_col] = scaled.dropna().astype(float)
            n_built += 1

            tier = "good" if alpha and alpha >= 0.7 else (
                "questionable" if alpha and alpha >= 0.5 else "tier3_caveat")

            manifest.append({
                "key": key, "column": agg_col, "var_id": f"{agg_col}|{domain}",
                "type": tier, "alpha": alpha,
                "n_items": len(cols), "n_valid": n_valid,
                "reverse_coded": reverse_items if reverse_items else None,
            })

    print(f"  build_v4_constructs: {n_built} columns built across "
          f"{len(svs.get('domains', {}))} domains")

    return enc_dict, manifest


# ═══════════════════════════════════════════════════════════════════
# SANITY CHECK (standalone)
# ═══════════════════════════════════════════════════════════════════

def sanity_check(enc_dict: dict, manifest: list, enc_nom_dict_rev: dict):
    """Verify built variables: distributions, coverage, cross-domain pairs."""
    print("\n═══ SANITY CHECK ═══\n")

    # 1. Per-construct stats
    by_type = {}
    valid_constructs = []
    for m in manifest:
        t = m["type"]
        by_type[t] = by_type.get(t, 0) + 1
        if m.get("column"):
            valid_constructs.append(m)

    print(f"Built constructs by type:")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")

    # 2. Check distributions
    print(f"\nDistribution check ({len(valid_constructs)} constructs):")
    degenerate = []
    low_n = []
    for m in valid_constructs:
        domain = m["key"].split("|")[0]
        survey_name = enc_nom_dict_rev.get(domain)
        if not survey_name or survey_name not in enc_dict:
            continue
        df = enc_dict[survey_name]["dataframe"]
        col = m["column"]
        if col not in df.columns:
            continue
        s = df[col].dropna()
        n = len(s)
        nunique = s.nunique()
        std = s.std()

        if nunique <= 2:
            degenerate.append((m["key"], col, n, nunique))
        if n < 50:
            low_n.append((m["key"], col, n))

    if degenerate:
        print(f"  WARNING: {len(degenerate)} constructs with <=2 unique values:")
        for key, col, n, nu in degenerate:
            print(f"    {key}: {col} (n={n}, unique={nu})")
    else:
        print(f"  All constructs have >2 unique values")

    if low_n:
        print(f"  WARNING: {len(low_n)} constructs with <50 valid rows:")
        for key, col, n in low_n:
            print(f"    {key}: {col} (n={n})")
    else:
        print(f"  All constructs have >=50 valid rows")

    # 3. Cross-domain pair coverage
    # Count how many pairs are possible
    domains = set()
    constructs_per_domain = {}
    for m in valid_constructs:
        dom = m["key"].split("|")[0]
        domains.add(dom)
        constructs_per_domain.setdefault(dom, []).append(m)

    n_domains = len(domains)
    n_cross_pairs = 0
    for i, d1 in enumerate(sorted(domains)):
        for d2 in sorted(domains):
            if d1 >= d2:
                continue
            n1 = len(constructs_per_domain.get(d1, []))
            n2 = len(constructs_per_domain.get(d2, []))
            n_cross_pairs += n1 * n2

    print(f"\nCross-domain pair coverage:")
    print(f"  {n_domains} domains with built variables")
    print(f"  {sum(len(v) for v in constructs_per_domain.values())} total constructs")
    print(f"  {n_cross_pairs} cross-domain construct pairs")
    print(f"  {len(domains) * (len(domains) - 1) // 2} domain pairs")

    # Per-domain counts
    print(f"\n  Per domain:")
    for dom in sorted(constructs_per_domain):
        cs = constructs_per_domain[dom]
        types = {}
        for c in cs:
            types[c["type"]] = types.get(c["type"], 0) + 1
        type_str = ", ".join(f"{n}{t[0].upper()}" for t, n in sorted(types.items()))
        print(f"    {dom}: {len(cs)} constructs ({type_str})")

    return n_cross_pairs


if __name__ == "__main__":
    from dataset_knowledge import enc_dict, enc_nom_dict

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    print("Building v4 construct variables...")
    enc_dict, manifest = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    n_pairs = sanity_check(enc_dict, manifest, enc_nom_dict_rev)

    # Save manifest
    out = ROOT / "data" / "results" / "construct_variable_manifest.json"
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nManifest saved: {out.name}")
