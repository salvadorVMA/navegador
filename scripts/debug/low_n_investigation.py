"""
Stream 4 — Low-N Investigation

For constructs with low n_valid, determines why:
  - Is it a skip/routing pattern (prior question filters respondents)?
  - Is it a small sub-population question (migrants, religious, partnered, etc.)?
  - Is it a data quality issue (high non-response)?
  - Should it be removed from the bridge?

Target constructs (n_valid flagged as suspicious):
  SOC|digital_technology_access_and_ownership  (N=255)
  MIG|transnational_social_ties                 (N=360)
  SOC|internet_engagement_and_digital_literacy  (N=364)
  DEP|reading_engagement_and_literacy           (N=483)
  JUS|legal_self_efficacy_and_access            (N=635)
  GEN|intimate_partner_power_dynamics           (N=637)
  REL|religious_socialization                   (N=847)

Output: data/results/construct_low_n_investigation.md
Run:    python scripts/debug/low_n_investigation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))

OUT = ROOT / "data" / "results" / "construct_low_n_investigation.md"

TARGETS = [
    ("SOC|digital_technology_access_and_ownership", 255),
    ("MIG|transnational_social_ties", 360),
    ("SOC|internet_engagement_and_digital_literacy", 364),
    ("DEP|reading_engagement_and_literacy", 483),
    ("JUS|legal_self_efficacy_and_access", 635),
    ("GEN|intimate_partner_power_dynamics", 637),
    ("REL|religious_socialization", 847),
]

# Threshold: constructs with N < this are at risk for DR bridge reliability
N_THRESHOLD_REMOVE = 400
N_THRESHOLD_CAUTION = 600


def _is_sentinel(v: float) -> bool:
    return v >= 97 or v < 0


def _clean(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return s.where(~s.apply(lambda v: _is_sentinel(v) if pd.notna(v) else False))


def find_routing_candidates(df: pd.DataFrame, items: list[str], top_k: int = 10) -> list[dict]:
    """
    Find columns that best predict whether ALL items in the construct have a valid response.
    Strategy: compute the binary indicator (1=all items valid, 0=otherwise), then find
    columns with highest correlation to this indicator.
    Returns top_k candidates sorted by abs(correlation).
    """
    # Build validity mask
    sub = pd.DataFrame()
    for col in items:
        if col in df.columns:
            sub[col] = _clean(df[col])
    if sub.empty:
        return []
    valid_mask = sub.notna().all(axis=1).astype(float)
    frac_valid = valid_mask.mean()

    if frac_valid < 0.01 or frac_valid > 0.99:
        return []

    candidates = []
    # Only scan numeric columns that are NOT the items themselves
    scan_cols = [c for c in df.columns if c not in items]
    for col in scan_cols:
        try:
            s = pd.to_numeric(df[col], errors="coerce")
            if s.dropna().nunique() < 2 or s.dropna().nunique() > 20:
                continue
            # Use point-biserial correlation (Pearson between binary and continuous)
            paired = pd.DataFrame({"mask": valid_mask, "col": s}).dropna()
            if len(paired) < 30:
                continue
            r = paired["mask"].corr(paired["col"])
            if abs(r) > 0.15:
                candidates.append({"col": col, "r": r, "n": len(paired)})
        except Exception:
            continue

    candidates.sort(key=lambda x: -abs(x["r"]))
    return candidates[:top_k]


def describe_routing_col(df: pd.DataFrame, col: str, vvl: dict, valid_mask: pd.Series) -> str:
    """Show value distribution of a routing candidate, split by valid/invalid."""
    label_map = {}
    for k, v in vvl.get(col, {}).items():
        try:
            label_map[float(k)] = str(v).strip()
        except (ValueError, TypeError):
            pass

    s = pd.to_numeric(df[col], errors="coerce")
    lines = []
    for code in sorted(s.dropna().unique()):
        mask_code = s == code
        n_valid_here = int((mask_code & valid_mask.astype(bool)).sum())
        n_code = int(mask_code.sum())
        pct = n_valid_here / n_code if n_code > 0 else 0
        label = label_map.get(code, str(int(code) if code == int(code) else code))
        lines.append(f"  code={int(code) if code == int(code) else code} ({label}): "
                     f"n={n_code}, {n_valid_here} have construct ({pct:.0%})")
    return "\n".join(lines) if lines else "  _(no data)_"


def item_coverage_table(df: pd.DataFrame, items: list[str], vvl: dict) -> str:
    n_total = len(df)
    lines = ["| item | n_valid | pct_valid | n_sentinel | n_nan |",
             "|------|---------|-----------|------------|-------|"]
    for item in items:
        if item not in df.columns:
            lines.append(f"| `{item}` | — | — | — | — |")
            continue
        s = pd.to_numeric(df[item], errors="coerce")
        n_nan = int(s.isna().sum())
        n_sentinel = int(s.apply(
            lambda v: _is_sentinel(v) if pd.notna(v) else False
        ).sum())
        n_valid = n_total - n_nan - n_sentinel
        pct = n_valid / n_total
        lines.append(f"| `{item}` | {n_valid} | {pct:.1%} | {n_sentinel} | {n_nan} |")
    return "\n".join(lines)


def main():
    print("Loading data...")
    from dataset_knowledge import enc_dict, enc_nom_dict

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    svs_path = ROOT / "data" / "results" / "semantic_variable_selection_v4.json"
    manifest_path = ROOT / "data" / "results" / "construct_variable_manifest.json"

    with open(svs_path) as f:
        svs = json.load(f)
    with open(manifest_path) as f:
        manifest_list = json.load(f)

    manifest = {m["key"]: m for m in manifest_list if m.get("key")}

    # SVS item lookup
    svs_items: dict[str, list[str]] = {}
    for domain, dom_data in svs.get("domains", {}).items():
        for cluster in dom_data.get("construct_clusters", []):
            key = f"{domain}|{cluster['name']}"
            raw = cluster.get("question_cluster", [])
            svs_items[key] = [q.split("|")[0] for q in raw]

    out_lines: list[str] = []
    out_lines.append("# Low-N Construct Investigation — Stream 4\n\n")
    out_lines.append(
        "For each construct with suspiciously low `n_valid`, diagnoses whether the cause is:\n"
        "- Skip/routing patterns (prior question filters respondents)\n"
        "- Sub-population design (migrants, religious, partnered, etc.)\n"
        "- High non-response / data quality\n\n"
        f"**Risk thresholds**: N < {N_THRESHOLD_REMOVE} → flag for removal; "
        f"N < {N_THRESHOLD_CAUTION} → caution.\n\n"
    )
    out_lines.append("---\n\n")

    for ckey, expected_n in TARGETS:
        domain = ckey.split("|")[0]
        survey_name = enc_nom_dict_rev.get(domain)
        m = manifest.get(ckey, {})
        items = svs_items.get(ckey, [])

        print(f"  Processing {ckey} (expected N≈{expected_n})...")
        out_lines.append(f"## {ckey}\n\n")
        out_lines.append(f"**Expected n_valid**: {expected_n}  |  **Alpha**: {m.get('alpha', 'N/A')}  |  **Type**: {m.get('type', '?')}\n\n")

        # Risk flag
        if expected_n < N_THRESHOLD_REMOVE:
            out_lines.append(
                f"> ⚠️ **REMOVAL CANDIDATE** — N={expected_n} < {N_THRESHOLD_REMOVE}. "
                "DR bridge estimates may be unreliable. Recommend removal unless routing is explainable.\n\n"
            )
        elif expected_n < N_THRESHOLD_CAUTION:
            out_lines.append(
                f"> ⚠️ **CAUTION** — N={expected_n} < {N_THRESHOLD_CAUTION}. "
                "CI widths will be inflated. Review routing before keeping.\n\n"
            )

        if not survey_name or survey_name not in enc_dict:
            out_lines.append(f"_Survey not found for domain {domain}_\n\n---\n\n")
            continue

        df = enc_dict[survey_name].get("dataframe")
        metadata = enc_dict[survey_name].get("metadata", {})
        vvl = metadata.get("variable_value_labels", {})
        col_labels = metadata.get("column_names_to_labels", {})
        n_total = len(df) if isinstance(df, pd.DataFrame) else 0

        out_lines.append(f"**Survey**: `{survey_name}` | **Total rows**: {n_total}\n\n")
        out_lines.append(f"**Items**: {items}\n\n")

        if not isinstance(df, pd.DataFrame) or not items:
            out_lines.append("_DataFrame or items not available_\n\n---\n\n")
            continue

        # Per-item coverage
        out_lines.append("### Per-Item Coverage\n\n")
        out_lines.append(item_coverage_table(df, items, vvl) + "\n\n")

        # Routing investigation
        available_items = [it for it in items if it in df.columns]
        if not available_items:
            out_lines.append("_No items found in dataframe_\n\n---\n\n")
            continue

        sub = pd.DataFrame()
        for col in available_items:
            sub[col] = _clean(df[col])
        valid_mask = sub.notna().all(axis=1)
        pct_valid_all = valid_mask.mean()

        out_lines.append(
            f"**Rows with ALL items valid**: {valid_mask.sum()} / {n_total} "
            f"({pct_valid_all:.1%})\n\n"
        )

        # Classify missingness pattern
        all_miss = sub.isna().all(axis=1)
        any_miss = sub.isna().any(axis=1)
        n_all_miss = all_miss.sum()
        n_partial = (any_miss & ~all_miss).sum()
        out_lines.append(
            f"**Missingness pattern**: {n_all_miss} rows ALL items missing "
            f"({n_all_miss/n_total:.1%}), {n_partial} rows partially missing\n\n"
        )

        if n_all_miss / n_total > 0.10:
            out_lines.append(
                "> Pattern: **block missingness** — large fraction has ALL items missing. "
                "Strongly suggests skip/routing (respondents skipped entire battery).\n\n"
            )
        elif n_partial / n_total > 0.10:
            out_lines.append(
                "> Pattern: **scattered missingness** — high partial missingness. "
                "May indicate item-level non-response rather than routing.\n\n"
            )
        else:
            out_lines.append(
                "> Pattern: missingness is low and uniform — N reduction likely due to "
                "survey sub-population design.\n\n"
            )

        # Find routing candidates
        out_lines.append("### Routing Candidate Analysis\n\n")
        candidates = find_routing_candidates(df, available_items, top_k=8)
        if candidates:
            out_lines.append(
                f"Top {len(candidates)} columns most correlated with having valid construct responses "
                f"(|r| > 0.15):\n\n"
            )
            for cand in candidates:
                col_name = cand["col"]
                label = col_labels.get(col_name, "")
                label_str = f" — *{label}*" if label else ""
                out_lines.append(f"**`{col_name}`{label_str}** (r={cand['r']:+.3f}, n={cand['n']})\n\n")
                out_lines.append(describe_routing_col(df, col_name, vvl, valid_mask) + "\n\n")
        else:
            out_lines.append(
                "_No strong routing candidates found (no column with |r| > 0.15 with construct validity)._\n\n"
                "This suggests the low N is due to survey design (sub-population), not routing.\n\n"
            )

        # Recommendation
        out_lines.append("### Recommendation\n\n")
        if expected_n < N_THRESHOLD_REMOVE:
            out_lines.append(
                f"**Remove from bridge** — N={expected_n} is below the minimum for reliable DR estimation. "
                "Even if routing is explainable, bootstrap CIs will be unreliably wide. "
                "Mark construct as `excluded_low_n` in SVS v4.\n\n"
            )
        elif candidates and abs(candidates[0]["r"]) > 0.5:
            out_lines.append(
                f"**Keep with annotation** — Strong routing pattern detected via `{candidates[0]['col']}` "
                f"(r={candidates[0]['r']:+.3f}). Construct measures a sub-population. "
                "γ estimates are conditional on that sub-population. "
                "Add routing note to `significant_constructs.md`.\n\n"
            )
        elif pct_valid_all < 0.35:
            out_lines.append(
                f"**Review before keeping** — {pct_valid_all:.0%} rows valid but no clear routing detected. "
                "Check questionnaire PDF for routing instructions, or consider dropping lowest-coverage item.\n\n"
            )
        else:
            out_lines.append(
                f"**Keep with caution** — N={expected_n}, no strong routing detected. "
                "Sub-population design likely. Note in documentation.\n\n"
            )

        out_lines.append("---\n\n")

    with open(OUT, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"\nDone — written to {OUT}")


if __name__ == "__main__":
    main()
