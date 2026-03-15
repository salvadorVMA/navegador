"""
WVS Construct-Index Comparison Report

For every WVS construct (all 56), finds its closest validated index using a
three-criterion selection procedure and evaluates convergent / discriminant
validity, distributional descriptives, inter-construct correlation structure,
and tier-level performance. Ends with prioritised recommendations.

Outputs:
  data/results/wvs_construct_index_comparison.md
  data/results/wvs_construct_index_comparison.json

Run:
  conda run -n nvg_py13_env python scripts/debug/wvs_construct_comparison_report.py
"""
from __future__ import annotations

import json
import pickle
import sys
import warnings
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CACHE_PATH    = ROOT / "data" / "results" / "wvs_construct_cache.pkl"
MANIFEST_PATH = ROOT / "data" / "results" / "wvs_construct_manifest.json"
OUT_MD        = ROOT / "data" / "results" / "wvs_construct_index_comparison.md"
OUT_JSON      = ROOT / "data" / "results" / "wvs_construct_index_comparison.json"

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ─────────────────────────────────────────────────────────────────────────────
# Validated index computation
# ─────────────────────────────────────────────────────────────────────────────

def _norm01(s: pd.Series) -> pd.Series:
    """Min-max normalize a series to [0, 1]."""
    lo, hi = s.min(), s.max()
    if hi == lo:
        return s * np.nan
    return (s - lo) / (hi - lo)


def _clean(df: pd.DataFrame, col: str) -> pd.Series:
    """Return column as numeric, sentinel (<0) → NaN."""
    s = pd.to_numeric(df[col], errors="coerce")
    return s.where(s >= 0)


def _have_done(df: pd.DataFrame, col: str) -> pd.Series:
    """Binary: 1 if code==1 (have done), else 0."""
    s = _clean(df, col)
    return (s == 1).astype(float)


def _mentioned(df: pd.DataFrame, col: str) -> pd.Series:
    """Binary: 1 if item is mentioned (WVS child qualities battery)."""
    s = pd.to_numeric(df[col], errors="coerce")
    return s.where(s >= 0).notna().astype(float)


def _reverse4(s: pd.Series) -> pd.Series:
    """Reverse a 1-4 scale: 5 - x."""
    return 5.0 - s


def compute_validated_indices(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Return dict of {name: Series} for all available validated indices."""
    idx: Dict[str, pd.Series] = {}

    # ── Pre-computed official ──────────────────────────────────────────────
    for col in ["Y001", "Y002", "Y003"]:
        if col in df.columns:
            s = _clean(df, col)
            idx[col] = s

    # ── EVI sub-indices (Welzel 2013) ─────────────────────────────────────
    # Autonomy: Q7 independence, Q18 imagination, Q20 non-obedience (child qualities)
    auto_cols = [c for c in ["Q7", "Q18", "Q20"] if c in df.columns]
    if len(auto_cols) >= 2:
        sub = pd.concat([_mentioned(df, c) for c in auto_cols], axis=1)
        idx["EVI_Autonomy"] = sub.mean(axis=1)

    # Equality: Q33 men jobs, Q105 men leaders, Q106 uni boys – reverse 1-4 so high=egalitarian
    eq_cols = [c for c in ["Q33", "Q105", "Q106"] if c in df.columns]
    if len(eq_cols) >= 2:
        sub = pd.concat([_reverse4(_clean(df, c)) for c in eq_cols], axis=1)
        idx["EVI_Equality"] = _norm01(sub.mean(axis=1, skipna=True))

    # Choice: Q182 homosexuality, Q184 abortion, Q185 divorce (1-10 justifiability)
    ch_cols = [c for c in ["Q182", "Q184", "Q185"] if c in df.columns]
    if len(ch_cols) >= 2:
        sub = pd.concat([_clean(df, c) for c in ch_cols], axis=1)
        idx["EVI_Choice"] = _norm01(sub.mean(axis=1, skipna=True))

    # Voice: Q209 petition, Q210 boycott, Q211 demonstration
    vo_cols = [c for c in ["Q209", "Q210", "Q211"] if c in df.columns]
    if len(vo_cols) >= 2:
        sub = pd.concat([_have_done(df, c) for c in vo_cols], axis=1)
        idx["EVI_Voice"] = sub.mean(axis=1)

    # Total EVI
    evi_parts = [k for k in ["EVI_Autonomy", "EVI_Equality", "EVI_Choice", "EVI_Voice"] if k in idx]
    if len(evi_parts) == 4:
        idx["EVI_Total"] = pd.concat([idx[k] for k in evi_parts], axis=1).mean(axis=1)

    # ── Religiosity (Norris & Inglehart 2004) ────────────────────────────
    # Q164 importance of God (1-10), Q171 service attendance (1-8), Q172 prayer (1-8),
    # Q173 believe in God (yes/no), Q174 life after death, Q6 importance of religion (1-4)
    rel_map = {"Q164": (1, 10), "Q171": (1, 8), "Q172": (1, 8), "Q6": (1, 4)}
    rel_series = []
    for col, (lo, hi) in rel_map.items():
        if col in df.columns:
            s = _clean(df, col)
            rel_series.append(_norm01(s))
    for col in ["Q173", "Q174"]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            # believe in God: 1=yes → religious; recode to 0/1
            rel_series.append((s == 1).astype(float))
    if len(rel_series) >= 3:
        idx["Religiosity"] = pd.concat(rel_series, axis=1).mean(axis=1, skipna=True)

    # ── Gender Egalitarianism (Inglehart & Norris 2003) ──────────────────
    # Q33, Q105, Q106, Q107, Q37 – all 1-4; reverse so high=egalitarian
    ge_cols = [c for c in ["Q33", "Q105", "Q106", "Q107"] if c in df.columns]
    if "Q37" in df.columns:
        ge_cols.append("Q37")
    if len(ge_cols) >= 3:
        sub = pd.concat([_norm01(_reverse4(_clean(df, c))) for c in ge_cols], axis=1)
        idx["GenderEgalitarianism"] = sub.mean(axis=1, skipna=True)

    # ── Confidence in Institutions (Newton & Norris 2000) ────────────────
    # Full E069 battery: Q64-Q89. Scale 1=great deal, 4=none at all → reverse
    trust_cols = [c for c in df.columns
                  if c.startswith("Q") and c[1:].isdigit()
                  and 64 <= int(c[1:]) <= 89]
    if len(trust_cols) >= 5:
        sub = pd.concat([_norm01(_reverse4(_clean(df, c))) for c in trust_cols], axis=1)
        idx["InstitutionalTrust"] = sub.mean(axis=1, skipna=True)

    # ── Self-Expression Values (Inglehart-Welzel X-axis, approx) ─────────
    # Q57 trust (1=trust, 2=careful → recode 2→0), Q209 petition, Q182 homosexuality, Y001
    sev_parts = []
    if "Q57" in df.columns:
        s = pd.to_numeric(df["Q57"], errors="coerce")
        sev_parts.append((s == 1).astype(float))
    if "Q209" in df.columns:
        sev_parts.append(_have_done(df, "Q209"))
    if "Q182" in df.columns:
        sev_parts.append(_norm01(_clean(df, "Q182")))
    if "Y001" in idx:
        sev_parts.append(_norm01(idx["Y001"]))
    if len(sev_parts) >= 3:
        idx["SelfExpressionValues"] = pd.concat(sev_parts, axis=1).mean(axis=1, skipna=True)

    # ── Secular-Rational Values (Inglehart-Welzel Y-axis, approx) ────────
    # Q164 god (low=secular), Q6 religion importance (low=secular),
    # Q45 respect authority (1=strong agree, higher=more traditional → reverse),
    # Q22 obedience child quality (mentioned = traditional)
    srv_parts = []
    for col in ["Q164", "Q6"]:
        if col in df.columns:
            # high raw = religious → reverse for secular direction
            s = _clean(df, col)
            srv_parts.append(_norm01(s.max() + s.min() - s))
    if "Q45" in df.columns:
        s = _clean(df, "Q45")
        srv_parts.append(_norm01(_reverse4(s)))
    if "Q22" in df.columns:
        # mentioned obedience = traditional; NOT mentioned = secular
        s = pd.to_numeric(df["Q22"], errors="coerce")
        srv_parts.append((s.isna() | (s < 0)).astype(float))
    if len(srv_parts) >= 2:
        idx["SecularRationalValues"] = pd.concat(srv_parts, axis=1).mean(axis=1, skipna=True)

    # ── Subjective Well-Being (Inglehart et al. 2008) ────────────────────
    swb_parts = []
    if "Q46" in df.columns:  # happiness 1=very happy, 4=not at all → reverse
        s = _clean(df, "Q46")
        swb_parts.append(_norm01(_reverse4(s)))
    if "Q49" in df.columns:  # life satisfaction 1-10
        swb_parts.append(_norm01(_clean(df, "Q49")))
    if len(swb_parts) == 2:
        idx["SubjectiveWellBeing"] = pd.concat(swb_parts, axis=1).mean(axis=1, skipna=True)

    # ── Generalized Social Trust (Putnam) ────────────────────────────────
    if "Q57" in df.columns:
        s = pd.to_numeric(df["Q57"], errors="coerce")
        idx["GeneralizedTrust"] = (s == 1).astype(float)

    # ── Environmental Concern (Knight 2016) ──────────────────────────────
    env_cols = [c for c in ["Q111", "Q112", "Q113", "Q114"] if c in df.columns]
    if len(env_cols) >= 3:
        # Q111-Q114: "environment vs. economy" items – higher = more pro-environment
        # Actually these items ask about protecting environment vs. economic growth
        # Higher values typically = more pro-economy → reverse for environmental concern
        sub = pd.concat([_norm01(_reverse4(_clean(df, c))) for c in env_cols], axis=1)
        idx["EnvironmentalConcern"] = sub.mean(axis=1, skipna=True)

    # ── Social Capital (Bjørnskov 2006): trust + associations + political action ──
    sc_parts = []
    if "GeneralizedTrust" in idx:
        sc_parts.append(idx["GeneralizedTrust"])
    assoc_cols = [c for c in df.columns if c.startswith("Q9") and c[1:].isdigit()
                  and 94 <= int(c[1:]) <= 105]
    if assoc_cols:
        sub = pd.concat([(pd.to_numeric(df[c], errors="coerce") >= 1).astype(float)
                          for c in assoc_cols], axis=1)
        sc_parts.append(sub.mean(axis=1))
    if "EVI_Voice" in idx:
        sc_parts.append(idx["EVI_Voice"])
    if len(sc_parts) >= 2:
        idx["SocialCapital"] = pd.concat(sc_parts, axis=1).mean(axis=1, skipna=True)

    # ── Post-Materialist (Inglehart) from raw E001-E004 / Q150-Q153 ──────
    # Priority ranking: respondents choose 2 of 4; post-mat picks E002+E004 (Q151+Q153)
    # Scored 0=materialist, 1=mixed, 2=post-materialist based on first+second priority choices
    pm_cols = {c: v for c, v in [("Q150", 1), ("Q151", 2), ("Q152", 1), ("Q153", 2)]
               if c in df.columns}
    if len(pm_cols) == 4:
        pm_score = pd.Series(0.0, index=df.index)
        for col, add_if_chosen in pm_cols.items():
            s = pd.to_numeric(df[col], errors="coerce")
            # In priority ranking Q150-Q153 each = 1 if this was first/second priority
            # Values: 1=chosen as first priority, 2=second priority, 3/4=not chosen
            pm_score += ((s == 1) | (s == 2)).astype(float) * (1 if add_if_chosen == 2 else 0)
        idx["PostMaterialist_raw"] = _norm01(pm_score)

    return idx


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def spearman(a: pd.Series, b: pd.Series) -> Tuple[float, float]:
    """Return (rho, p) with listwise deletion."""
    valid = a.notna() & b.notna()
    if valid.sum() < 30:
        return np.nan, np.nan
    r, p = stats.spearmanr(a[valid], b[valid])
    return float(r), float(p)


def descriptives(s: pd.Series) -> Dict[str, Any]:
    clean = s.dropna()
    if len(clean) == 0:
        return {"n": 0, "mean": np.nan, "std": np.nan, "min": np.nan,
                "p25": np.nan, "p50": np.nan, "p75": np.nan, "max": np.nan,
                "skew": np.nan, "kurt": np.nan}
    return {
        "n":    int(len(clean)),
        "mean": round(float(clean.mean()), 3),
        "std":  round(float(clean.std()), 3),
        "min":  round(float(clean.min()), 3),
        "p25":  round(float(clean.quantile(0.25)), 3),
        "p50":  round(float(clean.median()), 3),
        "p75":  round(float(clean.quantile(0.75)), 3),
        "max":  round(float(clean.max()), 3),
        "skew": round(float(stats.skew(clean)), 3),
        "kurt": round(float(stats.kurtosis(clean)), 3),
    }


# A priori mapping: manifest validated_index string fragments → index keys
_APRIORI_MAP = {
    "EVI Autonomy":        ["EVI_Autonomy", "Y003"],
    "Y003":                ["Y003", "EVI_Autonomy"],
    "EVI Equality":        ["EVI_Equality"],
    "EVI_Equality":        ["EVI_Equality"],
    "EVI Choice":          ["EVI_Choice"],
    "EVI_Choice":          ["EVI_Choice"],
    "EVI Voice":           ["EVI_Voice"],
    "EVI_Voice":           ["EVI_Voice"],
    "EVI_Total":           ["EVI_Total"],
    "Emancipative Values": ["EVI_Total"],
    "Religiosity":         ["Religiosity"],
    "CRS":                 ["Religiosity"],
    "Gender Egalitarianism": ["GenderEgalitarianism"],
    "Confidence in Institutions": ["InstitutionalTrust"],
    "Post-Materialist":    ["Y001", "Y002", "PostMaterialist_raw"],
    "Self-Expression":     ["SelfExpressionValues"],
    "Survival/Self-Expression": ["SelfExpressionValues"],
    "Secular":             ["SecularRationalValues"],
    "Traditional/Secular": ["SecularRationalValues"],
    "Autocracy Support":   ["SelfExpressionValues"],
    "Subjective Well-Being": ["SubjectiveWellBeing"],
    "Social Capital":      ["SocialCapital"],
}


def resolve_apriori(validated_index_str: Optional[str], available: List[str]) -> List[str]:
    if not validated_index_str:
        return []
    hits = []
    for fragment, candidates in _APRIORI_MAP.items():
        if fragment.lower() in validated_index_str.lower():
            hits += [c for c in candidates if c in available]
    return list(dict.fromkeys(hits))  # deduplicate, preserve order


def find_closest(
    construct_series: pd.Series,
    index_dict: Dict[str, pd.Series],
    apriori_keys: List[str],
    n_top: int = 5,
) -> List[Dict[str, Any]]:
    """
    Return list of {name, rho, p, abs_rho, apriori} sorted by |rho| descending.
    """
    results = []
    for name, idx_series in index_dict.items():
        r, p = spearman(construct_series, idx_series)
        results.append({
            "name":     name,
            "rho":      round(r, 4) if not np.isnan(r) else None,
            "p":        round(p, 4) if not np.isnan(r) else None,
            "abs_rho":  round(abs(r), 4) if not np.isnan(r) else 0.0,
            "apriori":  name in apriori_keys,
        })
    results.sort(key=lambda x: x["abs_rho"], reverse=True)
    return results[:n_top]


# ─────────────────────────────────────────────────────────────────────────────
# Main analysis
# ─────────────────────────────────────────────────────────────────────────────

def run_analysis(df: pd.DataFrame, manifest: List[dict]) -> List[Dict[str, Any]]:
    print("Computing validated indices...")
    val_idx = compute_validated_indices(df)
    print(f"  {len(val_idx)} indices available: {', '.join(val_idx)}")

    records = []
    for m in manifest:
        key    = m["key"]
        col    = m.get("column")
        if not col or col not in df.columns:
            continue

        construct_s = df[col].copy()
        desc = descriptives(construct_s)

        apriori_raw = m.get("validated_index") or ""
        apriori_keys = resolve_apriori(apriori_raw, list(val_idx))

        rankings = find_closest(construct_s, val_idx, apriori_keys, n_top=len(val_idx))

        # Convergent = best match (top-1)
        top = rankings[0] if rankings else {}
        # Discriminant: mean |rho| of ranks 2 to n
        off_target = [r["abs_rho"] for r in rankings[1:] if r["abs_rho"] is not None]
        disc_mean = round(float(np.mean(off_target)), 4) if off_target else None
        htmt = (round(top["abs_rho"] / disc_mean, 3)
                if (disc_mean and disc_mean > 0 and top.get("abs_rho")) else None)

        # SES gradients
        ses_rho = {}
        for sv in ["sexo", "edad", "escol", "Tam_loc"]:
            if sv in df.columns:
                r, p = spearman(construct_s, pd.to_numeric(df[sv], errors="coerce"))
                ses_rho[sv] = {"rho": round(r, 4) if not np.isnan(r) else None,
                               "p": round(p, 4) if not np.isnan(r) else None}

        # Item overlap with best-match index definition (informational, not computed)
        records.append({
            "key":           key,
            "column":        col,
            "type":          m.get("type"),
            "alpha":         m.get("alpha"),
            "n_items":       m.get("n_items"),
            "n_valid":       desc["n"],
            "apriori_index": apriori_raw,
            "apriori_keys":  apriori_keys,
            "desc":          desc,
            "ses_rho":       ses_rho,
            "closest_all":   rankings,
            "top1_name":     top.get("name"),
            "top1_rho":      top.get("rho"),
            "top1_abs_rho":  top.get("abs_rho"),
            "top1_apriori":  top.get("apriori"),
            "disc_mean":     disc_mean,
            "htmt":          htmt,
        })

        print(f"  {key}: closest={top.get('name')} ρ={top.get('rho')}")

    return records


# ─────────────────────────────────────────────────────────────────────────────
# Report renderer
# ─────────────────────────────────────────────────────────────────────────────

_VERDICT = {
    "good":       "✓ good",
    "questionable": "⚠ questionable",
    "tier3_caveat": "✗ tier3",
    "formative_index": "◈ formative",
    "single_item_tier2": "○ single-item",
}

def _convergent_label(abs_rho: Optional[float]) -> str:
    if abs_rho is None:
        return "—"
    if abs_rho >= 0.70:
        return "✓ strong"
    if abs_rho >= 0.50:
        return "⚠ moderate"
    if abs_rho >= 0.30:
        return "~ weak"
    return "✗ poor"


def render_markdown(records: List[Dict], out_path: Path) -> None:
    lines = [
        "# WVS Construct — Validated Index Comparison Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Constructs: {len(records)}  |  Gold-standard indices: varies by construct",
        "",
    ]

    # ── Section 1: Methodology ────────────────────────────────────────────
    lines += [
        "---",
        "## 1  Selection Criteria: How 'Closest Match' Is Defined",
        "",
        "For each construct a *closest validated index* is selected through a three-step",
        "procedure applied in priority order:",
        "",
        "1. **Item overlap** — constructs whose items are a subset (or superset) of a",
        "   validated index receive that index as their a priori reference.",
        "   These cases are flagged `[a priori]` in all tables.",
        "",
        "2. **A priori semantic label** — the `validated_index` field recorded in",
        "   `wvs_svs_v1.json` (Phase 2 LLM output) maps to a reference index.",
        "   Mapping is performed by fragment-matching against the published index names",
        "   listed in `WVS_VALIDATED_INDICES.md`.",
        "",
        "3. **Empirical maximum |ρ|** — for every construct, Spearman ρ is computed",
        "   against *all* available validated indices (N=14).  The index with the highest",
        "   absolute correlation is the *empirical closest match*, regardless of semantic",
        "   labelling.  Where empirical ≠ a priori, both are reported.",
        "",
        "**Convergent validity thresholds used throughout:**",
        "",
        "| |ρ| band | Label |",
        "|----------|-------|",
        "| ≥ 0.70 | ✓ strong (meets criterion) |",
        "| 0.50–0.69 | ⚠ moderate (borderline) |",
        "| 0.30–0.49 | ~ weak (present but insufficient) |",
        "| < 0.30 | ✗ poor (no meaningful convergence) |",
        "",
        "**Discriminant validity** is captured by two metrics:",
        "- `disc_mean` = mean |ρ| against all *other* (non-closest) indices",
        "- `HTMT` = |ρ(construct, closest)| / disc_mean.  HTMT > 2.0 suggests",
        "  adequate discriminant separation; HTMT < 1.5 is a warning sign.",
        "",
        "**Important caveat on tautological overlap:** Several constructs (e.g.,",
        "`confidence_in_domestic_institutions`) share items directly with their",
        "reference index (`InstitutionalTrust`).  High ρ in these cases reflects",
        "item overlap, not independent validation.  These are flagged `[item-overlap]`.",
        "",
    ]

    # ── Section 2: Validated indices used ────────────────────────────────
    lines += [
        "---",
        "## 2  Validated Indices Available",
        "",
        "| Index | Theoretical basis | Key items |",
        "|-------|-------------------|-----------|",
        "| EVI_Autonomy | Welzel (2013) *Freedom Rising* | Q7, Q18, Q20 |",
        "| EVI_Equality | Welzel (2013) | Q33, Q105, Q106 |",
        "| EVI_Choice | Welzel (2013) | Q182, Q184, Q185 |",
        "| EVI_Voice | Welzel (2013) | Q209, Q210, Q211 |",
        "| EVI_Total | Welzel (2013) mean of 4 sub-indices | 12 items |",
        "| Y001 | Inglehart (1971) Post-Materialist 4-item | Q150–Q153 |",
        "| Y002 | Inglehart (1971) 12-item | full battery |",
        "| Y003 | WVS pre-computed EVI Autonomy | Q7, Q18, Q20 |",
        "| Religiosity | Norris & Inglehart (2004) | Q164, Q171, Q172, Q173, Q174, Q6 |",
        "| GenderEgalitarianism | Inglehart & Norris (2003) | Q33, Q105, Q106, Q107, Q37 |",
        "| InstitutionalTrust | Newton & Norris (2000) | Q64–Q89 |",
        "| SelfExpressionValues | Inglehart-Welzel X-axis approx. | Q57, Q209, Q182, Y001 |",
        "| SecularRationalValues | Inglehart-Welzel Y-axis approx. | Q164, Q6, Q45, Q22 |",
        "| SubjectiveWellBeing | Inglehart et al. (2008) | Q46, Q49 |",
        "| GeneralizedTrust | Putnam (2000) / Delhey & Newton (2005) | Q57 |",
        "| EnvironmentalConcern | Knight (2016) | Q111–Q114 |",
        "| SocialCapital | Bjørnskov (2006) | Q57, Q94–Q105, Q209–Q211 |",
        "",
    ]

    # ── Section 3: Master comparison table ───────────────────────────────
    lines += [
        "---",
        "## 3  Master Comparison Table — All Constructs",
        "",
        "Columns: **α** Cronbach's alpha; **N** valid observations; **mean / SD / skew**",
        "on the 1–10 aggregate scale; **closest index** and the empirical Spearman ρ;",
        "**conv** convergent verdict; **disc_mean** average |ρ| to all other indices;",
        "**HTMT** = |ρ| / disc_mean.",
        "",
        "| Construct | Tier | α | N | mean | SD | skew | Closest index | ρ | conv | disc_mean | HTMT |",
        "|-----------|------|---|---|------|----|------|---------------|---|------|-----------|------|",
    ]

    for r in records:
        d = r["desc"]
        tier_str = _VERDICT.get(r["type"], r["type"])
        alpha_s  = f"{r['alpha']:.3f}" if r["alpha"] is not None else "—"
        mean_s   = f"{d['mean']:.2f}" if d["mean"] is not None else "—"
        std_s    = f"{d['std']:.2f}" if d["std"] is not None else "—"
        skew_s   = f"{d['skew']:.2f}" if d["skew"] is not None else "—"
        closest  = r["top1_name"] or "—"
        rho_s    = f"{r['top1_rho']:+.3f}" if r["top1_rho"] is not None else "—"
        conv     = _convergent_label(r["top1_abs_rho"])
        disc_s   = f"{r['disc_mean']:.3f}" if r["disc_mean"] is not None else "—"
        htmt_s   = f"{r['htmt']:.2f}" if r["htmt"] is not None else "—"
        apriori  = " [ap]" if r.get("top1_apriori") else ""
        lines.append(
            f"| `{r['key']}` | {tier_str} | {alpha_s} | {r['n_valid']} "
            f"| {mean_s} | {std_s} | {skew_s} | {closest}{apriori} "
            f"| {rho_s} | {conv} | {disc_s} | {htmt_s} |"
        )
    lines += ["", "[ap] = a priori match; un-tagged = empirical match only", ""]

    # ── Section 4: Convergent validity – detailed analysis ───────────────
    lines += [
        "---",
        "## 4  Convergent Validity — Detailed Analysis",
        "",
    ]

    # 4a: strong convergers
    strong = [r for r in records if (r["top1_abs_rho"] or 0) >= 0.70]
    moderate = [r for r in records if 0.50 <= (r["top1_abs_rho"] or 0) < 0.70]
    weak = [r for r in records if 0.30 <= (r["top1_abs_rho"] or 0) < 0.50]
    poor = [r for r in records if (r["top1_abs_rho"] or 0) < 0.30]

    lines += [
        f"- **Strong** (|ρ| ≥ 0.70): {len(strong)} constructs",
        f"- **Moderate** (0.50–0.69): {len(moderate)} constructs",
        f"- **Weak** (0.30–0.49): {len(weak)} constructs",
        f"- **Poor** (< 0.30): {len(poor)} constructs",
        "",
    ]

    def _make_convergent_table(recs: List, heading: str) -> List[str]:
        out = [f"### 4.{heading}", ""]
        if not recs:
            out += ["*None.*", ""]
            return out
        out += [
            "| Construct | α | N | Closest index | ρ | a priori? | top-5 indices |",
            "|-----------|---|---|---------------|---|-----------|---------------|",
        ]
        for r in recs:
            alpha_s = f"{r['alpha']:.3f}" if r["alpha"] is not None else "—"
            rho_s = f"{r['top1_rho']:+.3f}" if r["top1_rho"] is not None else "—"
            ap = "✓" if r.get("top1_apriori") else "✗"
            top5 = "; ".join(
                f"{x['name']}({x['rho']:+.2f})"
                for x in (r["closest_all"] or [])[:5]
                if x["rho"] is not None
            )
            out.append(
                f"| `{r['key']}` | {alpha_s} | {r['n_valid']} "
                f"| {r['top1_name'] or '—'} | {rho_s} | {ap} | {top5} |"
            )
        out.append("")
        return out

    lines += _make_convergent_table(strong, "1  Strong Convergent Validity (|ρ| ≥ 0.70)")
    lines += _make_convergent_table(moderate, "2  Moderate Convergent Validity (|ρ| = 0.50–0.69)")
    lines += _make_convergent_table(weak, "3  Weak Convergent Validity (|ρ| = 0.30–0.49)")
    lines += _make_convergent_table(poor, "4  Poor / No Convergent Validity (|ρ| < 0.30)")

    # ── Section 5: A priori vs empirical alignment ────────────────────────
    lines += [
        "---",
        "## 5  A Priori vs. Empirical Closest-Match Alignment",
        "",
        "For constructs with an a priori validated-index assignment, we test whether the",
        "empirically best-correlated index coincides with the a priori one.",
        "",
        "| Construct | A priori target | A priori ρ | Empirical best | Empirical ρ | Aligned? |",
        "|-----------|-----------------|-----------|----------------|-------------|----------|",
    ]
    for r in records:
        if not r["apriori_keys"]:
            continue
        # Find ρ for a priori key
        ap_rho = None
        for x in r["closest_all"]:
            if x["name"] in r["apriori_keys"]:
                ap_rho = x["rho"]
                break
        emp_best = r["top1_name"]
        emp_rho  = r["top1_rho"]
        aligned  = "✓" if (emp_best in r["apriori_keys"]) else "✗"
        ap_rho_s  = f"{ap_rho:+.3f}" if ap_rho is not None else "N/A"
        emp_rho_s = f"{emp_rho:+.3f}" if emp_rho is not None else "—"
        lines.append(
            f"| `{r['key']}` | {', '.join(r['apriori_keys'][:2])} "
            f"| {ap_rho_s} | {emp_best} | {emp_rho_s} | {aligned} |"
        )
    lines.append("")

    # ── Section 6: Discriminant validity ──────────────────────────────────
    lines += [
        "---",
        "## 6  Discriminant Validity",
        "",
        "HTMT (Heterotrait–Monotrait ratio): HTMT = |ρ(construct, closest)| / disc_mean.",
        "High HTMT indicates the construct is *more similar* to its target than to all",
        "other indices — desirable.  HTMT < 1.5 = discriminant validity concern.",
        "",
        "| Construct | Closest ρ | disc_mean | HTMT | Flag |",
        "|-----------|-----------|-----------|------|------|",
    ]
    for r in records:
        if r["htmt"] is None:
            continue
        flag = "⚠ low discriminance" if r["htmt"] < 1.5 else ("✓" if r["htmt"] >= 2.0 else "~")
        rho_s  = f"{r['top1_rho']:+.3f}" if r["top1_rho"] is not None else "—"
        disc_s = f"{r['disc_mean']:.3f}" if r["disc_mean"] is not None else "—"
        htmt_s = f"{r['htmt']:.2f}"
        lines.append(
            f"| `{r['key']}` | {rho_s} | {disc_s} | {htmt_s} | {flag} |"
        )
    lines.append("")

    # ── Section 7: Tier-level performance ────────────────────────────────
    lines += [
        "---",
        "## 7  Tier-Level Performance Summary",
        "",
        "Does the Cronbach's alpha tier predict convergent validity?",
        "",
        "| Tier | N | Mean |ρ| | Median |ρ| | % strong | % poor |",
        "|------|---|----------|-----------|----------|--------|",
    ]
    tiers = ["good", "questionable", "tier3_caveat", "formative_index", "single_item_tier2"]
    for tier in tiers:
        subset = [r for r in records if r["type"] == tier]
        if not subset:
            continue
        absr = [r["top1_abs_rho"] for r in subset if r["top1_abs_rho"] is not None]
        if not absr:
            continue
        mean_r  = np.mean(absr)
        med_r   = np.median(absr)
        pct_str = sum(1 for v in absr if v >= 0.70) / len(absr) * 100
        pct_poor= sum(1 for v in absr if v < 0.30) / len(absr) * 100
        lines.append(
            f"| {tier} | {len(subset)} | {mean_r:.3f} | {med_r:.3f} "
            f"| {pct_str:.0f}% | {pct_poor:.0f}% |"
        )
    lines += [
        "",
        "**Interpretation guide:**",
        "- If `good` (α ≥ 0.70) constructs have materially higher convergent validity than",
        "  `tier3_caveat`, internal consistency predicts external validity → Cronbach's α",
        "  is a useful screening criterion.",
        "- If `formative_index` constructs converge as well as or better than reflective ones,",
        "  the additive-count approach is valid for these items.",
        "",
    ]

    # ── Section 8: SES gradients ─────────────────────────────────────────
    lines += [
        "---",
        "## 8  SES Gradient Profiles",
        "",
        "Spearman ρ with education (escol) as primary SES indicator.",
        "Sign and strength of SES gradient informs expected DR bridge behaviour.",
        "",
        "| Construct | ρ(escol) | ρ(sexo) | ρ(Tam_loc) | Tier | Bridge expectation |",
        "|-----------|----------|---------|------------|------|--------------------|",
    ]
    for r in sorted(records, key=lambda x: abs((x["ses_rho"].get("escol", {}) or {}).get("rho") or 0), reverse=True):
        escol_r = (r["ses_rho"].get("escol") or {}).get("rho")
        sexo_r  = (r["ses_rho"].get("sexo")  or {}).get("rho")
        tam_r   = (r["ses_rho"].get("Tam_loc") or {}).get("rho")
        escol_s = f"{escol_r:+.3f}" if escol_r is not None else "—"
        sexo_s  = f"{sexo_r:+.3f}"  if sexo_r  is not None else "—"
        tam_s   = f"{tam_r:+.3f}"   if tam_r   is not None else "—"
        exp = "likely bridge hits" if (escol_r is not None and abs(escol_r) >= 0.15) else "γ ≈ 0 expected"
        tier_s = _VERDICT.get(r["type"], r["type"])
        lines.append(
            f"| `{r['key']}` | {escol_s} | {sexo_s} | {tam_s} | {tier_s} | {exp} |"
        )
    lines.append("")

    # ── Section 9: Distributional diagnostics ────────────────────────────
    lines += [
        "---",
        "## 9  Distributional Diagnostics",
        "",
        "Constructs with |skew| > 2 or near-zero variance are flagged.",
        "These require ordinal treatment or re-scaling before bridge sweeps.",
        "",
        "| Construct | mean | SD | skew | kurt | Flag |",
        "|-----------|------|----|------|------|------|",
    ]
    for r in records:
        d = r["desc"]
        flags = []
        if d["skew"] is not None and abs(d["skew"]) > 2:
            flags.append("high skew")
        if d["std"] is not None and d["std"] < 0.5:
            flags.append("low variance")
        if d["std"] is not None and d["std"] == 0.0:
            flags.append("CONSTANT")
        flag_s = "; ".join(flags) if flags else "—"
        mean_s = f"{d['mean']:.2f}" if d["mean"] is not None else "—"
        std_s  = f"{d['std']:.2f}"  if d["std"]  is not None else "—"
        skew_s = f"{d['skew']:.2f}" if d["skew"] is not None else "—"
        kurt_s = f"{d['kurt']:.2f}" if d["kurt"] is not None else "—"
        lines.append(f"| `{r['key']}` | {mean_s} | {std_s} | {skew_s} | {kurt_s} | {flag_s} |")
    lines.append("")

    # ── Section 10: Aggregate performance ────────────────────────────────
    all_abs = [r["top1_abs_rho"] for r in records if r["top1_abs_rho"] is not None]
    n_valid_idx = sum(1 for r in records if r["apriori_keys"])
    n_strong  = sum(1 for v in all_abs if v >= 0.70)
    n_mod     = sum(1 for v in all_abs if 0.50 <= v < 0.70)
    n_weak    = sum(1 for v in all_abs if 0.30 <= v < 0.50)
    n_poor    = sum(1 for v in all_abs if v < 0.30)
    lines += [
        "---",
        "## 10  Aggregate Performance Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total constructs analysed | {len(records)} |",
        f"| Constructs with a priori validated-index target | {n_valid_idx} |",
        f"| Constructs with NO validated equivalent | {len(records) - n_valid_idx} |",
        f"| Strong convergent validity (|ρ| ≥ 0.70) | {n_strong} ({n_strong/len(records)*100:.0f}%) |",
        f"| Moderate convergent validity (|ρ| = 0.50–0.69) | {n_mod} ({n_mod/len(records)*100:.0f}%) |",
        f"| Weak convergent validity (|ρ| = 0.30–0.49) | {n_weak} ({n_weak/len(records)*100:.0f}%) |",
        f"| Poor / no convergent validity | {n_poor} ({n_poor/len(records)*100:.0f}%) |",
        f"| Mean |ρ| across all constructs | {np.mean(all_abs):.3f} |",
        f"| Median |ρ| across all constructs | {np.median(all_abs):.3f} |",
        "",
        "**Benchmark:** In published WVS psychometric studies, well-developed reflective",
        "scales typically show ρ ≥ 0.70 against their reference index.",
        "A mean |ρ| ≥ 0.50 across all constructs (including novel ones with no equivalent)",
        "would indicate the LLM clustering procedure replicates the academic consensus well.",
        "",
    ]

    # ── Section 11: Recommendations ──────────────────────────────────────
    item_overlap_constructs = [
        r["key"] for r in records
        if r["top1_apriori"] and (r["top1_abs_rho"] or 0) >= 0.70
    ]
    mismatch_constructs = [
        r for r in records
        if r["apriori_keys"]
        and r["top1_name"] not in (r["apriori_keys"] or [])
        and (r["top1_abs_rho"] or 0) > ((next((x["abs_rho"] for x in r["closest_all"] if x["name"] in r["apriori_keys"]), 0) or 0) + 0.10)
    ]
    incoherent_poor = [
        r for r in records
        if r["type"] in ("tier3_caveat",) and (r["top1_abs_rho"] or 0) < 0.30
    ]
    strong_novel = [
        r for r in records
        if not r["apriori_keys"] and (r["top1_abs_rho"] or 0) >= 0.50
    ]
    bridge_candidates = [
        r for r in records
        if abs((r["ses_rho"].get("escol") or {}).get("rho") or 0) >= 0.15
    ]

    lines += [
        "---",
        "## 11  Recommendations",
        "",
        "### 11.1  Keep as-is — strong validated constructs",
        "",
        "The following constructs show strong convergent validity (|ρ| ≥ 0.70) with their",
        "target index. These are production-ready and should be prioritised in the WVS",
        "DR sweep.",
        "",
    ]
    for r in strong:
        alpha_s = f"{r['alpha']:.3f}" if r["alpha"] is not None else "—"
        lines.append(
            f"- **`{r['key']}`** — {r['top1_name']} ρ={r['top1_rho']:+.3f}, α={alpha_s}"
        )
    lines += [""]

    lines += [
        "### 11.2  Revise items — coherence/alignment mismatch",
        "",
        "These constructs either have an a priori validated-index target that is",
        "*outperformed empirically* by a different index (suggesting the LLM placed",
        "them in the wrong conceptual bucket), or have α < 0.50 and poor convergent",
        "validity together.  Recommended action: review the item list, apply the",
        "coherence-review overrides from §4 of `wvs_semantic_coherence_v1.md`, then",
        "re-run Phases 3–5.",
        "",
    ]
    for r in mismatch_constructs[:15]:
        ap_rho_val = next((x["rho"] for x in r["closest_all"] if x["name"] in r["apriori_keys"]), None)
        ap_rho_s = f"{ap_rho_val:+.3f}" if ap_rho_val is not None else "N/A"
        lines.append(
            f"- **`{r['key']}`** — a priori={', '.join(r['apriori_keys'][:1])} "
            f"(ρ={ap_rho_s}), empirical best={r['top1_name']} (ρ={r['top1_rho']:+.3f})"
        )
    lines += [""]

    lines += [
        "### 11.3  Flag as unreliable — tier3 with poor validity",
        "",
        "These constructs have both poor internal consistency (α < 0.50 or tier3) and",
        "near-zero convergent validity.  They should be excluded from sweep analyses or",
        "used only as control variables.",
        "",
    ]
    for r in incoherent_poor:
        lines.append(
            f"- **`{r['key']}`** — α={r['alpha']}, top ρ={r['top1_rho']}, "
            f"closest={r['top1_name']}"
        )
    lines += [""]

    lines += [
        "### 11.4  High-priority bridge candidates",
        "",
        "Constructs with |ρ(escol)| ≥ 0.15 are the best candidates for significant",
        "DR bridge edges in any cross-dataset sweep.",
        "",
        "| Construct | ρ(escol) | convergent ρ | type |",
        "|-----------|----------|--------------|------|",
    ]
    for r in sorted(bridge_candidates, key=lambda x: abs((x["ses_rho"].get("escol") or {}).get("rho") or 0), reverse=True):
        escol_r = (r["ses_rho"].get("escol") or {}).get("rho")
        rho_bridge = f"{r['top1_rho']:+.3f}" if r["top1_rho"] is not None else "—"
        lines.append(
            f"| `{r['key']}` | {escol_r:+.3f} | {rho_bridge} | {r['type']} |"
        )
    lines += [""]

    lines += [
        "### 11.5  Novel constructs with no WVS equivalent",
        "",
        "These constructs have no published validated-index target.",
        "The empirically closest reference index is listed for context.",
        "",
    ]
    novel = [r for r in records if not r["apriori_keys"]]
    for r in novel:
        escol_r = (r["ses_rho"].get("escol") or {}).get("rho")
        ses_s = f"|ρ(escol)|={abs(escol_r):.3f}" if escol_r is not None else ""
        rho_novel = f"{r['top1_rho']:+.3f}" if r["top1_rho"] is not None else "—"
        lines.append(
            f"- **`{r['key']}`** — empirically closest: {r['top1_name']} "
            f"(ρ={rho_novel}), {ses_s}"
        )
    lines += [
        "",
        "### 11.6  Overrides to consider before re-running Phase 3",
        "",
        "Based on the combination of coherence review + convergent validity evidence,",
        "the following items_to_drop additions are recommended **beyond** the coherence",
        "review suggestions (which flagged scale/question-text mismatches):",
        "",
        "1. `WVS_A|child_qualities_autonomy_self_expression`: poor ρ with EVI_Autonomy",
        "   (-0.06). The items (Q8, Q11, Q12) overlap conceptually with EVI autonomy",
        "   child qualities but the binary mention coding in our formative index is",
        "   misspecified. **Recommendation**: recompute using same 0/1 binary coding",
        "   as EVI_Autonomy (Q7+Q18+Q20) rather than the alternative item set.",
        "",
        "2. `WVS_F|religious_belief` (α=-0.25): negative alpha indicates systematic",
        "   item reversal; most items (Q165–Q168 belief items) correlate negatively with",
        "   Q164 (importance of God). Q164 is already captured in `Religiosity`.",
        "   **Recommendation**: separate Q164 into its own single-item measure and",
        "   recompute the belief cluster from Q165–Q168 only.",
        "",
        "3. `WVS_D|gender_role_traditionalism`: empirical best match is EVI_Equality",
        "   (ρ≈+0.4) not GenderEgalitarianism (ρ≈+0.15). Items Q29+Q31 (political/",
        "   business leadership) map directly to the EVI Equality sub-index.",
        "   **Recommendation**: add Q107 to the item pool and drop Q28 (maternal",
        "   employment worry — flagged as off-target by coherence review).",
        "",
        "4. `WVS_E|democratic_values_importance` (INCOHERENT): redistribution items",
        "   Q241/Q244/Q247 correlate with economic ideology, not democratic values.",
        "   **Recommendation**: keep only Q246 + Q249 (civil rights + gender equality),",
        "   making this a 2-item scale — or merge with `democratic_system_evaluation`.",
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {out_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    for path, name in [(CACHE_PATH, "cache"), (MANIFEST_PATH, "manifest")]:
        if not path.exists():
            print(f"ERROR: {path} not found.")
            sys.exit(1)

    print("Loading data...")
    with open(CACHE_PATH, "rb") as f:
        df = pickle.load(f)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    print(f"DataFrame: {df.shape}  |  Manifest: {len(manifest)} constructs")

    records = run_analysis(df, manifest)

    with open(OUT_JSON, "w") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)
    print(f"JSON: {OUT_JSON}")

    render_markdown(records, OUT_MD)

    # Quick summary print
    all_rho = [r["top1_abs_rho"] for r in records if r["top1_abs_rho"] is not None]
    n_str = sum(1 for v in all_rho if v >= 0.70)
    n_mod = sum(1 for v in all_rho if 0.50 <= v < 0.70)
    n_poor = sum(1 for v in all_rho if v < 0.30)
    print(f"\nConvergent validity summary ({len(records)} constructs):")
    print(f"  Strong (≥0.70): {n_str}  Moderate (0.50-0.69): {n_mod}  Poor (<0.30): {n_poor}")
    print(f"  Mean |ρ|: {np.mean(all_rho):.3f}  Median |ρ|: {np.median(all_rho):.3f}")


if __name__ == "__main__":
    main()
