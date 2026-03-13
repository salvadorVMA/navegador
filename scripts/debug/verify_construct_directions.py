"""
Pre-sweep construct direction and sentinel audit — V5.

For every built construct, verifies:
  1. Item-aggregate Spearman r > 0 after reverse coding (direction consistency)
  2. No agg_ values outside [1, 10] (scale range)
  3. Sentinel-partial rows per item (how often an agg value is computed despite
     a sentinel in one of its items — informational, not a hard error)
  4. Dominant-code items (>50% at one code after cleaning)
  5. Cardinality mismatch across items (max/min cats > 3×)
  6. Coverage (n_valid < 600)

Output: data/results/construct_direction_audit_v5.md

Usage:
    python scripts/debug/verify_construct_directions.py
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))

V4_SVS_PATH   = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"
V5_OV_PATH    = ROOT / "data" / "results" / "construct_v5_overrides.json"
OUTPUT_PATH   = ROOT / "data" / "results" / "construct_direction_audit_v5.md"

# Flag thresholds
THRESH_DIRECTION = -0.10   # item-agg Spearman r below → FLAG_DIRECTION
THRESH_WEAK      = 0.05    # |r| below this (n_items>1) → FLAG_WEAK
N_VALID_LOW      = 600
DOMINANCE_THRESH = 0.50    # fraction at one code → FLAG_DOMINANCE
CARDINALITY_RATIO = 3.0    # max/min unique values → FLAG_CARDINALITY
SCALE_LO         = 0.999
SCALE_HI         = 10.001

SKIP_TYPES           = {"excluded", "no_columns", "insufficient_data", "no_survey"}
DIRECTION_SKIP_TYPES = {"single_item_tier2", "formative_index"}


# ── Import shared helpers from build_construct_variables ──────────────────────

from build_construct_variables import _clean_series, _load_v5_overrides


# ── Item-list reconstruction ──────────────────────────────────────────────────

def _rebuild_effective_items(
    key: str,
    svs_domains: dict,
    ov: dict,
) -> Tuple[List[str], List[str], Dict[str, List[int]]]:
    """
    Reconstruct (item_cols, reverse_items, col_sentinels) for a construct key,
    mirroring the exact same logic used in build_v4_constructs.

    Handles both SVS v4 constructs and new_constructs from v5 overrides.
    """
    items_to_drop   = {k: set(v) for k, v in ov.get("items_to_drop", {}).items()   if not k.startswith("_")}
    items_to_add    = {k: v      for k, v in ov.get("items_to_add", {}).items()     if not k.startswith("_")}
    sentinel_ov     = {k: v      for k, v in ov.get("item_sentinel_overrides", {}).items() if not k.startswith("_")}
    reverse_ov      = {k: v.get("add", []) for k, v in ov.get("reverse_coded_overrides", {}).items() if not k.startswith("_")}

    domain = key.split("|")[0]
    cname  = key.split("|", 1)[1]

    # ── Try SVS v4 domains first ──
    cluster = None
    dom_data = svs_domains.get(domain, {})
    for cl in dom_data.get("construct_clusters", []):
        if cl["name"] == cname:
            cluster = cl
            break

    if cluster is not None:
        qids_raw  = cluster.get("question_cluster", [])
        qids_bare = [q.split("|")[0] if "|" in q else q for q in qids_raw]
        drop_set  = items_to_drop.get(key, set())
        qids_bare = [q for q in qids_bare if q not in drop_set]
        for extra in items_to_add.get(key, []):
            if extra not in qids_bare:
                qids_bare.append(extra)
        reverse_items = list(cluster.get("reverse_coded_items", []) or [])
        for item in reverse_ov.get(key, []):
            if item not in reverse_items:
                reverse_items.append(item)
        col_sentinels = sentinel_ov.get(key, {})
        return qids_bare, reverse_items, col_sentinels

    # ── Fallback: new_constructs in v5 overrides ──
    for nc in ov.get("new_constructs", []):
        if nc.get("domain") == domain and nc.get("name") == cname:
            qids  = list(nc.get("question_cluster", []))
            rev   = list(nc.get("reverse_coded_items", []) or [])
            for item in reverse_ov.get(key, []):
                if item not in rev:
                    rev.append(item)
            return qids, rev, sentinel_ov.get(key, {})

    return [], [], {}


# ── Per-item audit helpers ────────────────────────────────────────────────────

def _apply_reverse(series: pd.Series) -> pd.Series:
    mx, mn = series.max(), series.min()
    if pd.notna(mx) and pd.notna(mn) and mx > mn:
        return mx + mn - series
    return series


def _compute_item_agg_correlations(
    df: pd.DataFrame,
    cols: List[str],
    reverse_items: List[str],
    col_sentinels: Dict[str, List[int]],
    agg_col: str,
    n_items_total: int,
) -> List[Dict]:
    results = []
    agg = df[agg_col]
    for col in cols:
        if col not in df.columns:
            results.append({"col": col, "r": None, "n_valid_pairs": 0, "flag": "MISSING_COL"})
            continue
        s = _clean_series(df[col], extra_sentinels=col_sentinels.get(col))
        if col in reverse_items:
            s = _apply_reverse(s)
        mask = s.notna() & agg.notna()
        n_pairs = int(mask.sum())
        if n_pairs < 10:
            results.append({"col": col, "r": None, "n_valid_pairs": n_pairs, "flag": "INSUFFICIENT"})
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = float(s[mask].corr(agg[mask], method="spearman"))
        if pd.isna(r):
            results.append({"col": col, "r": None, "n_valid_pairs": n_pairs, "flag": "CONSTANT"})
            continue
        if r < THRESH_DIRECTION:
            flag = "FLAG_DIRECTION"
        elif abs(r) < THRESH_WEAK and n_items_total > 1:
            flag = "FLAG_WEAK"
        else:
            flag = "OK"
        results.append({"col": col, "r": round(r, 4), "n_valid_pairs": n_pairs, "flag": flag})
    return results


def _check_scale_range(agg_series: pd.Series) -> Dict:
    s = agg_series.dropna()
    below = int((s < SCALE_LO).sum())
    above = int((s > SCALE_HI).sum())
    return {"n_below_1": below, "n_above_10": above, "flagged": below > 0 or above > 0}


def _check_residual_sentinels(
    df: pd.DataFrame,
    cols: List[str],
    col_sentinels: Dict[str, List[int]],
    agg_series: pd.Series,
) -> List[Dict]:
    agg_valid_mask = agg_series.notna()
    n_agg_valid = int(agg_valid_mask.sum())
    results = []
    for col in cols:
        if col not in df.columns:
            continue
        raw = pd.to_numeric(df[col], errors="coerce")
        global_sent = raw.apply(lambda v: (v >= 97 or v < 0) if pd.notna(v) else False)
        extras = col_sentinels.get(col, [])
        extra_sent = raw.isin(extras) if extras else pd.Series(False, index=raw.index)
        any_sent = global_sent | extra_sent
        partial = (any_sent & agg_valid_mask).sum()
        pct = float(partial) / n_agg_valid if n_agg_valid > 0 else 0.0
        results.append({
            "col": col,
            "n_sentinel_partial": int(partial),
            "pct_partial": round(pct, 3),
            "flagged": pct > 0.20,
        })
    return results


def _check_dominance(
    df: pd.DataFrame,
    cols: List[str],
    col_sentinels: Dict[str, List[int]],
) -> List[Dict]:
    results = []
    for col in cols:
        if col not in df.columns:
            continue
        s = _clean_series(df[col], extra_sentinels=col_sentinels.get(col)).dropna()
        if len(s) < 10:
            continue
        vc = s.value_counts(normalize=True)
        top_pct = float(vc.max())
        top_code = vc.idxmax()
        results.append({
            "col": col, "top_code": top_code, "top_pct": round(top_pct, 3),
            "n_valid": len(s), "flagged": top_pct > DOMINANCE_THRESH,
        })
    return results


def _check_cardinality(
    df: pd.DataFrame,
    cols: List[str],
    col_sentinels: Dict[str, List[int]],
) -> Dict:
    cats = {}
    for col in cols:
        if col not in df.columns:
            continue
        s = _clean_series(df[col], extra_sentinels=col_sentinels.get(col)).dropna()
        cats[col] = int(s.nunique())
    if len(cats) < 2:
        return {"flagged": False, "cats_per_item": cats}
    mn, mx = min(cats.values()), max(cats.values())
    ratio = mx / max(mn, 1)
    return {
        "cats_per_item": cats,
        "min_cats": mn, "max_cats": mx,
        "ratio": round(ratio, 1),
        "flagged": ratio > CARDINALITY_RATIO,
    }


# ── Main audit loop ───────────────────────────────────────────────────────────

def audit_all_constructs(
    enc_dict: dict,
    enc_nom_dict_rev: dict,
    svs: dict,
    ov: dict,
    manifest_list: List[Dict],
) -> List[Dict]:
    results = []
    for m in manifest_list:
        key    = m.get("key", "")
        ctype  = m.get("type", "")
        column = m.get("column")

        if not column or ctype in SKIP_TYPES:
            continue

        domain = key.split("|")[0]
        survey_name = enc_nom_dict_rev.get(domain)
        if not survey_name or survey_name not in enc_dict:
            continue
        df = enc_dict[survey_name].get("dataframe")
        if not isinstance(df, pd.DataFrame) or column not in df.columns:
            continue

        agg_series = df[column]
        n_valid = int(agg_series.dropna().shape[0])
        items, reverse_items, col_sentinels = _rebuild_effective_items(key, svs.get("domains", {}), ov)
        items_in_df = [c for c in items if c in df.columns]
        n_items = m.get("n_items") or len(items_in_df)

        record: Dict[str, Any] = {
            "key": key, "column": column, "type": ctype,
            "alpha": m.get("alpha"), "n_valid": n_valid, "n_items": n_items,
            "flags": [],
            "item_correlations": [],
            "scale_check": {},
            "sentinel_check": [],
            "dominance_check": [],
            "cardinality_check": {},
        }

        if n_valid < N_VALID_LOW:
            record["flags"].append(f"FLAG_COVERAGE(n={n_valid})")

        sc = _check_scale_range(agg_series)
        record["scale_check"] = sc
        if sc["flagged"]:
            record["flags"].append(f"FLAG_SCALE_RANGE(below={sc['n_below_1']},above={sc['n_above_10']})")

        if ctype not in DIRECTION_SKIP_TYPES and items_in_df:
            corrs = _compute_item_agg_correlations(
                df, items_in_df, reverse_items, col_sentinels, column, n_items
            )
            record["item_correlations"] = corrs
            dir_flags  = [c for c in corrs if c["flag"] == "FLAG_DIRECTION"]
            weak_flags = [c for c in corrs if c["flag"] == "FLAG_WEAK"]
            if dir_flags:
                s = ", ".join(f"{c['col']}(r={c['r']})" for c in dir_flags)
                record["flags"].append(f"FLAG_DIRECTION: {s}")
            if weak_flags:
                s = ", ".join(f"{c['col']}(r={c['r']})" for c in weak_flags if c["r"] is not None)
                if s:
                    record["flags"].append(f"FLAG_WEAK: {s}")

            sent_check = _check_residual_sentinels(df, items_in_df, col_sentinels, agg_series)
            record["sentinel_check"] = sent_check
            sent_flagged = [s for s in sent_check if s["flagged"]]
            if sent_flagged:
                record["flags"].append(f"FLAG_SENTINEL_PARTIAL({len(sent_flagged)} items)")

            dom_check = _check_dominance(df, items_in_df, col_sentinels)
            record["dominance_check"] = dom_check
            dom_flagged = [d for d in dom_check if d["flagged"]]
            if dom_flagged:
                s = ", ".join(f"{d['col']}({d['top_pct']:.0%}@{d['top_code']})" for d in dom_flagged)
                record["flags"].append(f"FLAG_DOMINANCE: {s}")

            card_check = _check_cardinality(df, items_in_df, col_sentinels)
            record["cardinality_check"] = card_check
            if card_check.get("flagged"):
                record["flags"].append(
                    f"FLAG_CARDINALITY(ratio={card_check['ratio']},"
                    f"min={card_check['min_cats']},max={card_check['max_cats']})"
                )

        results.append(record)
    return results


# ── Markdown rendering ────────────────────────────────────────────────────────

def render_markdown(results: List[Dict], path: Path) -> None:
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    n_total    = len(results)
    n_flagged  = sum(1 for r in results if r["flags"])
    cnt = lambda tag: sum(1 for r in results if any(tag in f for f in r["flags"]))

    lines.append(f"# Construct Direction & Sentinel Audit — V5\n\nGenerated: {ts}\n\n")
    lines.append("## Summary\n\n")
    lines.append("| Metric | Count |\n|--------|-------|\n")
    lines.append(f"| Constructs audited | {n_total} |\n")
    lines.append(f"| Constructs with ≥1 flag | {n_flagged} |\n")
    lines.append(f"| FLAG_DIRECTION (item r < −0.10) | {cnt('FLAG_DIRECTION')} |\n")
    lines.append(f"| FLAG_WEAK (\\|r\\| < 0.05) | {cnt('FLAG_WEAK')} |\n")
    lines.append(f"| FLAG_COVERAGE (n < 600) | {cnt('FLAG_COVERAGE')} |\n")
    lines.append(f"| FLAG_SENTINEL_PARTIAL | {cnt('FLAG_SENTINEL_PARTIAL')} |\n")
    lines.append(f"| FLAG_DOMINANCE (>50% one code) | {cnt('FLAG_DOMINANCE')} |\n")
    lines.append(f"| FLAG_CARDINALITY (ratio >3×) | {cnt('FLAG_CARDINALITY')} |\n")
    lines.append(f"| FLAG_SCALE_RANGE | {cnt('FLAG_SCALE_RANGE')} |\n\n")

    lines.append("## All Constructs\n\n")
    lines.append("| Key | Type | α | N | Flags |\n|-----|------|---|---|-------|\n")
    for r in sorted(results, key=lambda x: x["key"]):
        alpha_str = f"{r['alpha']:.3f}" if r["alpha"] is not None else "—"
        flag_str  = "; ".join(r["flags"]) if r["flags"] else "✓"
        lines.append(f"| `{r['key']}` | {r['type']} | {alpha_str} | {r['n_valid']} | {flag_str} |\n")
    lines.append("\n")

    flagged = [r for r in results if r["flags"]]
    if not flagged:
        lines.append("## Flagged Constructs\n\n_None — all constructs pass._\n")
    else:
        lines.append(f"## Flagged Constructs ({len(flagged)})\n\n")
        for r in sorted(flagged, key=lambda x: x["key"]):
            alpha_str = f"{r['alpha']:.3f}" if r["alpha"] is not None else "—"
            lines.append(f"### `{r['key']}`\n\n")
            lines.append(
                f"**Type**: {r['type']}  |  **α**: {alpha_str}  "
                f"|  **N**: {r['n_valid']}  |  **n_items**: {r['n_items']}\n\n"
            )
            lines.append(f"**Flags**: {'; '.join(r['flags'])}\n\n")

            if r["item_correlations"]:
                lines.append("**Item–Aggregate Spearman r** (after reverse coding applied):\n\n")
                lines.append("| Item | r | n_pairs | Status |\n|------|---|---------|--------|\n")
                for c in r["item_correlations"]:
                    r_str = f"{c['r']:.4f}" if c["r"] is not None else "—"
                    lines.append(f"| `{c['col']}` | {r_str} | {c['n_valid_pairs']} | {c['flag']} |\n")
                lines.append("\n")

            sent_flagged = [s for s in r.get("sentinel_check", []) if s["flagged"]]
            if sent_flagged:
                lines.append("**High-sentinel-partial items** (>20% of agg rows had sentinel in raw item):\n\n")
                for s in sent_flagged:
                    lines.append(f"- `{s['col']}`: {s['pct_partial']:.1%} ({s['n_sentinel_partial']} rows)\n")
                lines.append("\n")

            dom_flagged = [d for d in r.get("dominance_check", []) if d["flagged"]]
            if dom_flagged:
                lines.append("**Dominant-code items**:\n\n")
                for d in dom_flagged:
                    lines.append(f"- `{d['col']}`: {d['top_pct']:.1%} at code {d['top_code']} (n={d['n_valid']})\n")
                lines.append("\n")

            card = r.get("cardinality_check", {})
            if card.get("flagged"):
                cats_str = ", ".join(f"`{k}`={v}" for k, v in card.get("cats_per_item", {}).items())
                lines.append(
                    f"**Scale mismatch**: {card['min_cats']}–{card['max_cats']} categories "
                    f"(ratio {card['ratio']}×). {cats_str}\n\n"
                )

            lines.append("---\n\n")

    path.write_text("".join(lines), encoding="utf-8")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading survey data...")
    from dataset_knowledge import enc_dict, enc_nom_dict
    from build_construct_variables import build_v4_constructs

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    print("Building construct variables...")
    enc_dict, manifest_list = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    print("Loading SVS v4 + v5 overrides...")
    with open(V4_SVS_PATH) as f:
        svs = json.load(f)
    with open(V5_OV_PATH) as f:
        ov = json.load(f)

    n_built = sum(1 for m in manifest_list if m.get("column"))
    print(f"Auditing {n_built} built constructs...")
    results = audit_all_constructs(enc_dict, enc_nom_dict_rev, svs, ov, manifest_list)

    print("Rendering report...")
    render_markdown(results, OUTPUT_PATH)

    n_dir  = sum(1 for r in results if any("FLAG_DIRECTION" in f for f in r["flags"]))
    n_flag = sum(1 for r in results if r["flags"])
    print(f"\n{'='*60}")
    print(f"Audit complete: {n_flag}/{len(results)} constructs flagged, "
          f"{n_dir} direction issues.")
    print(f"Report: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
