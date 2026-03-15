"""
Phase 5 — WVS Construct Validation Against Validated Indices

For each WVS construct we built, asks:
  1. Does it map to an academically validated WVS index? If yes:
       - Compute the validated index from raw items (or use pre-computed Y001/Y002/Y003)
       - Report Spearman ρ(construct, validated_index) and N
       - Verdict: ρ>0.7 = good convergent validity, 0.5-0.7 = partial, <0.5 = poor
  2. If no validated equivalent: descriptive profile + expectation note
       - Descriptive stats of the construct
       - SES gradient (Spearman ρ with sexo, edad, escol, Tam_loc)
       - Cross-reference to los_mex domain if domain overlap exists

Outputs:
  data/results/wvs_validation_report.md   — main report
  data/results/wvs_validation_report.json — machine-readable

Run:
  conda run -n nvg_py13_env python scripts/debug/wvs_validate_against_indices.py
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_loader import WVSLoader

MANIFEST_PATH  = ROOT / "data" / "results" / "wvs_construct_manifest.json"
CACHE_PATH     = ROOT / "data" / "results" / "wvs_construct_cache.pkl"
OUT_MD         = ROOT / "data" / "results" / "wvs_validation_report.md"
OUT_JSON       = ROOT / "data" / "results" / "wvs_validation_report.json"

# ---------------------------------------------------------------------------
# Pre-computed validated indices from raw WVS items
# Formula references: docs/WVS_VALIDATED_INDICES.md
# ---------------------------------------------------------------------------

def _clean_wvs(df: pd.DataFrame, col: str) -> pd.Series:
    s = pd.to_numeric(df[col], errors="coerce")
    return s.where(s >= 0)


def _scale01(s: pd.Series, lo: float, hi: float) -> pd.Series:
    """Scale value s from [lo, hi] to [0, 1]."""
    return (s - lo) / (hi - lo)


def _compute_validated_indices(df: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Compute all 10 academically validated WVS composite indices from raw items.
    Returns {index_name: pd.Series (continuous, higher = more of construct)}.
    """
    indices: dict[str, pd.Series] = {}

    # ── 1. Post-Materialist (use pre-computed Y001 / Y002) ─────────────────
    for y in ["Y001", "Y002", "Y003"]:
        if y in df.columns:
            s = pd.to_numeric(df[y], errors="coerce")
            indices[y] = s.where(s >= 0)

    # ── 2. EVI — Autonomy (replicate Y003 from raw items if available) ─────
    auto_items = {"Q7": (1, 2), "Q18": (1, 2), "Q20": (1, 2)}  # 1=mentioned (good), 2=not
    auto_parts = []
    for col, (good_val, _) in auto_items.items():
        if col in df.columns:
            s = _clean_wvs(df, col)
            auto_parts.append((s == good_val).astype(float))
    if auto_parts:
        indices["EVI_Autonomy"] = pd.concat(auto_parts, axis=1).mean(axis=1)

    # ── 3. EVI — Equality ──────────────────────────────────────────────────
    eq_map = {
        "Q33": (1, 3),   # "men have more right to job" 1=agree, 3=disagree; higher=egalitarian
        "Q105": (4, 1),  # "men better political leaders" 1=strongly agree, 4=strongly disagree
        "Q106": (4, 1),  # "university more important for boys" 1=agree, 4=disagree
    }
    eq_parts = []
    for col, (lo, hi) in eq_map.items():
        if col in df.columns:
            s = _clean_wvs(df, col)
            if hi > lo:
                eq_parts.append(_scale01(s, lo, hi))
            else:
                eq_parts.append(_scale01(hi - (s - lo), 0, hi - lo))
    if eq_parts:
        indices["EVI_Equality"] = pd.concat(eq_parts, axis=1).mean(axis=1)

    # ── 4. EVI — Choice ────────────────────────────────────────────────────
    choice_items = ["Q182", "Q184", "Q185"]  # homosexuality/abortion/divorce justifiable 1-10
    choice_parts = [_scale01(_clean_wvs(df, c), 1, 10) for c in choice_items if c in df.columns]
    if choice_parts:
        indices["EVI_Choice"] = pd.concat(choice_parts, axis=1).mean(axis=1)

    # ── 5. EVI — Voice ─────────────────────────────────────────────────────
    voice_items = {"Q209": (1, 2), "Q210": (1, 2), "Q211": (1, 2)}  # 1=done, 2=not done
    voice_parts = []
    for col, (done, _) in voice_items.items():
        if col in df.columns:
            s = _clean_wvs(df, col)
            voice_parts.append((s == done).astype(float))
    if voice_parts:
        indices["EVI_Voice"] = pd.concat(voice_parts, axis=1).mean(axis=1)

    # ── 6. EVI — Total ─────────────────────────────────────────────────────
    evi_parts = [indices[k] for k in ["EVI_Autonomy", "EVI_Equality", "EVI_Choice", "EVI_Voice"] if k in indices]
    if len(evi_parts) == 4:
        indices["EVI_Total"] = pd.concat(evi_parts, axis=1).mean(axis=1)

    # ── 7. Religiosity (Norris & Inglehart) ─────────────────────────────────
    rel_specs = [
        ("Q164", 1, 10),   # importance of God 1-10; higher = more religious
        ("Q171", 1, 8),    # attendance 1-8; WVS codes 1=weekly+, 8=never; REVERSE (never=1 in raw)
        ("Q172", 1, 8),    # prayer frequency; same reverse issue
        ("Q6", 1, 4),      # importance of religion 1=very, 4=not at all; REVERSE
    ]
    # For Q171/Q172: 1=more than once a week, 8=never → reverse so higher=more religious
    rel_parts = []
    for col, lo, hi in rel_specs:
        if col in df.columns:
            s = _clean_wvs(df, col)
            if col in ("Q171", "Q172", "Q6"):
                # Reverse: higher raw code = less religious
                rel_parts.append(_scale01(hi - s + lo, 0, hi - lo))
            else:
                rel_parts.append(_scale01(s, lo, hi))
    # Belief in God: Q173 (1=yes, 2=no) → 1=religious
    if "Q173" in df.columns:
        s = _clean_wvs(df, "Q173")
        rel_parts.append((s == 1).astype(float))
    # Life after death: Q174 (1=yes, 2=no)
    if "Q174" in df.columns:
        s = _clean_wvs(df, "Q174")
        rel_parts.append((s == 1).astype(float))
    if rel_parts:
        indices["Religiosity"] = pd.concat(rel_parts, axis=1).mean(axis=1)

    # ── 8. Gender Egalitarianism (Inglehart & Norris) ────────────────────────
    gen_specs = [
        ("Q33", 3, 1),    # men have more right to job: 1=agree, 3=disagree; higher raw=egalitarian
        ("Q105", 4, 1),   # men better leaders: 1=strongly agree, 4=strongly disagree; reverse
        ("Q106", 4, 1),   # boys more important university: reverse
        ("Q107", 4, 1),   # men better executives: reverse
    ]
    gen_parts = []
    for col, hi_raw, lo_raw in gen_specs:
        if col not in df.columns:
            continue
        s = _clean_wvs(df, col)
        # higher hi_raw → more egalitarian
        if hi_raw > lo_raw:
            gen_parts.append(_scale01(s, lo_raw, hi_raw))
        else:
            gen_parts.append(_scale01(hi_raw + (lo_raw - s), 0, lo_raw - hi_raw))
    if gen_parts:
        indices["GenderEgalitarianism"] = pd.concat(gen_parts, axis=1).mean(axis=1)

    # ── 9. Institutional Trust (mean across E069 battery) ────────────────────
    trust_cols = [
        c for c in ["Q64","Q65","Q66","Q67","Q68","Q69","Q70","Q71",
                     "Q74","Q75","Q76","Q77","Q80","Q81","Q82","Q83","Q84"]
        if c in df.columns
    ]
    trust_parts = []
    for col in trust_cols:
        s = _clean_wvs(df, col)
        # 1=great deal, 4=none at all → reverse so higher=more trust
        trust_parts.append(_scale01(5 - s, 0, 3))  # 5-s: 4→1=none, 1→4=great deal
    if trust_parts:
        indices["InstitutionalTrust"] = pd.concat(trust_parts, axis=1).mean(axis=1)

    # ── 10. Self-Expression Values (Inglehart-Welzel X-axis approximation) ───
    se_parts = []
    if "Q57" in df.columns:
        s = _clean_wvs(df, "Q57")  # 1=trust, 2=careful → 1=self-expression
        se_parts.append((s == 1).astype(float))
    if "Q209" in df.columns:  # signed petition: 1=done
        s = _clean_wvs(df, "Q209")
        se_parts.append((s == 1).astype(float))
    if "Q182" in df.columns:  # homosexuality justifiable 1-10
        se_parts.append(_scale01(_clean_wvs(df, "Q182"), 1, 10))
    if "Y001" in df.columns:  # post-materialist (Y001 1-3)
        s = pd.to_numeric(df["Y001"], errors="coerce")
        s = s.where(s >= 0)
        se_parts.append(_scale01(s, 1, 3))
    if se_parts:
        indices["SelfExpressionValues"] = pd.concat(se_parts, axis=1).mean(axis=1)

    # ── 11. Traditional/Secular-Rational (Y-axis approximation) ──────────────
    trad_parts = []
    if "Q164" in df.columns:  # Importance of God 1-10; low=secular
        trad_parts.append(1 - _scale01(_clean_wvs(df, "Q164"), 1, 10))
    if "Q6" in df.columns:    # Importance of religion 1-4 (1=very); low code = more traditional
        s = _clean_wvs(df, "Q6")
        trad_parts.append(1 - _scale01(s, 1, 4))  # secular = low importance
    if "Q45" in df.columns:   # Respect for authority: 1=like, 2=neutral, 3=dislike; dislike=secular
        s = _clean_wvs(df, "Q45")
        trad_parts.append(_scale01(s, 1, 3))  # higher = more secular
    if "Q22" in df.columns:   # Obedience child quality: 1=mentioned (traditional), 2=not
        s = _clean_wvs(df, "Q22")
        trad_parts.append((s == 2).astype(float))  # not mentioned = secular
    if trad_parts:
        indices["SecularRationalValues"] = pd.concat(trad_parts, axis=1).mean(axis=1)

    return indices


# ---------------------------------------------------------------------------
# SES gradient
# ---------------------------------------------------------------------------

SES_VARS_MAP = {"sexo": "Gender (M=1,F=2)", "edad": "Age", "escol": "Education", "Tam_loc": "Town size"}


def _ses_gradient(s: pd.Series, df: pd.DataFrame) -> dict[str, float]:
    """Spearman ρ between construct and each SES variable."""
    result = {}
    for col, label in SES_VARS_MAP.items():
        if col not in df.columns:
            continue
        ses = pd.to_numeric(df[col], errors="coerce")
        valid = pd.concat([s, ses], axis=1).dropna()
        if len(valid) < 30:
            continue
        rho, pval = sp_stats.spearmanr(valid.iloc[:, 0], valid.iloc[:, 1])
        result[col] = {"rho": round(float(rho), 3), "p": round(float(pval), 4)}
    return result


# ---------------------------------------------------------------------------
# Convergent validity check
# ---------------------------------------------------------------------------

def _check_convergent(
    construct_series: pd.Series,
    validated_indices: dict[str, pd.Series],
    validated_names: list[str],
) -> list[dict]:
    """
    For each named validated index, compute Spearman ρ with the construct.
    """
    results = []
    for vname in validated_names:
        if vname not in validated_indices:
            results.append({"index": vname, "available": False})
            continue
        vi = validated_indices[vname]
        valid = pd.concat([construct_series, vi], axis=1).dropna()
        if len(valid) < 30:
            results.append({"index": vname, "available": False, "reason": "N<30"})
            continue
        rho, pval = sp_stats.spearmanr(valid.iloc[:, 0], valid.iloc[:, 1])
        verdict = "good" if abs(rho) > 0.7 else ("partial" if abs(rho) > 0.5 else "poor")
        results.append({
            "index": vname,
            "available": True,
            "rho": round(float(rho), 3),
            "p": round(float(pval), 4),
            "n": len(valid),
            "verdict": verdict,
        })
    return results


# ---------------------------------------------------------------------------
# Map construct validated_index string → index key in our computed dict
# ---------------------------------------------------------------------------

_INDEX_NAME_MAP = {
    # Exact or near-exact matches to keys in _compute_validated_indices output
    "Y001": "Y001",
    "Y002": "Y002",
    "Y003": "Y003",
    "Post-Materialist": "Y001",
    "EVI_Autonomy": "EVI_Autonomy",
    "EVI_Equality": "EVI_Equality",
    "EVI_Choice": "EVI_Choice",
    "EVI_Voice": "EVI_Voice",
    "EVI_Total": "EVI_Total",
    "EVI Autonomy": "EVI_Autonomy",
    "EVI Equality": "EVI_Equality",
    "EVI Choice": "EVI_Choice",
    "EVI Voice": "EVI_Voice",
    "Emancipative Values": "EVI_Total",
    "Religiosity (Norris & Inglehart)": "Religiosity",
    "Religiosity": "Religiosity",
    "Gender Egalitarianism": "GenderEgalitarianism",
    "Confidence in Institutions": "InstitutionalTrust",
    "Institutional Trust": "InstitutionalTrust",
    "Traditional/Secular-Rational": "SecularRationalValues",
    "Survival/Self-Expression": "SelfExpressionValues",
    "Self-Expression": "SelfExpressionValues",
}


def _resolve_index_names(validated_index_str: str | None) -> list[str]:
    if not validated_index_str:
        return []
    keys = []
    for part in [validated_index_str] + validated_index_str.split(";"):
        part = part.strip()
        for src, dst in _INDEX_NAME_MAP.items():
            if src.lower() in part.lower():
                if dst not in keys:
                    keys.append(dst)
    return keys


# ---------------------------------------------------------------------------
# Domain overlap: WVS → los_mex
# ---------------------------------------------------------------------------

_DOMAIN_OVERLAP = {
    "WVS_A": "IDE (Identidad y Valores), FAM",
    "WVS_B": "MED (Medio Ambiente)",
    "WVS_C": "ECO (Economía)",
    "WVS_D": "FAM (Familia), ENV (Envejecimiento)",
    "WVS_E": "CUL (Cultura Política), FED, JUS, COR",
    "WVS_F": "REL (Religión)",
    "WVS_G": "IDE (Identidad), GLO, MIG",
    "WVS_H": "SEG (Seguridad), COR (Corrupción)",
    "WVS_I": "CIE (Ciencia y Tecnología)",
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Load WVS data
    if CACHE_PATH.exists():
        print("Loading WVS data from cache...")
        with open(CACHE_PATH, "rb") as f:
            df = pickle.load(f)
    else:
        print("Loading WVS Wave 7 Mexico data (no cache)...")
        loader = WVSLoader()
        wvs_dict = loader.build_wvs_dict(waves=[7], countries=["MEX"])
        df = wvs_dict["enc_dict"]["WVS_W7_MEX"]["dataframe"]

    with open(MANIFEST_PATH) as f:
        manifest_list = json.load(f)

    manifest = [m for m in manifest_list if m.get("column") and m.get("type") not in ("excluded", "missing_items")]

    print("Computing validated indices...")
    validated_indices = _compute_validated_indices(df)
    print(f"  {len(validated_indices)} validated indices computed: {list(validated_indices.keys())}")

    results = []
    validated_count = 0
    no_equiv_count = 0

    for m in manifest:
        key = m["key"]
        col = m["column"]
        if col not in df.columns:
            continue

        construct_series = pd.to_numeric(df[col], errors="coerce")
        validated_index_str = m.get("validated_index") or ""
        index_keys = _resolve_index_names(validated_index_str)

        # Descriptive stats
        valid_s = construct_series.dropna()
        desc = {
            "mean": round(float(valid_s.mean()), 3) if len(valid_s) > 0 else None,
            "std": round(float(valid_s.std()), 3) if len(valid_s) > 0 else None,
            "skew": round(float(valid_s.skew()), 3) if len(valid_s) > 0 else None,
            "n_valid": len(valid_s),
        }

        # SES gradient
        ses_grad = _ses_gradient(construct_series, df)

        # Convergent validity
        convergent = _check_convergent(construct_series, validated_indices, index_keys)
        has_validated = bool(index_keys)
        if has_validated:
            validated_count += 1
        else:
            no_equiv_count += 1

        results.append({
            "key": key,
            "column": col,
            "type": m.get("type"),
            "alpha": m.get("alpha"),
            "n_items": m.get("n_items"),
            "validated_index": validated_index_str,
            "has_validated_equivalent": has_validated,
            "convergent_validity": convergent,
            "descriptive": desc,
            "ses_gradient": ses_grad,
            "wvs_domain": key.split("|")[0] if "|" in key else "",
        })

    print(f"\n{len(results)} constructs evaluated")
    print(f"  {validated_count} with validated equivalent")
    print(f"  {no_equiv_count} without validated equivalent")

    # Save JSON
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"JSON: {OUT_JSON}")

    # Render markdown report
    _render_md(results, validated_indices, OUT_MD)


def _render_md(results: list[dict], validated_indices: dict, out_path: Path) -> None:
    from datetime import datetime

    lines = [
        "# WVS Construct Validation Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Available Validated Indices (computed from raw items)",
        "",
        "| Index | N_valid | Formula basis |",
        "|-------|---------|---------------|",
    ]
    index_descriptions = {
        "Y001": "WVS pre-computed Post-Materialist 4-item",
        "Y002": "WVS pre-computed Post-Materialist 12-item",
        "Y003": "WVS pre-computed Autonomy sub-index",
        "EVI_Autonomy": "A029+A038+A040 (child qualities, Welzel 2013)",
        "EVI_Equality": "C001+D059+D060 (gender attitudes, Welzel 2013)",
        "EVI_Choice": "F118+F120+F121 (lifestyle tolerance, Welzel 2013)",
        "EVI_Voice": "E025+E026+E027 (political action, Welzel 2013)",
        "EVI_Total": "Mean of 4 EVI sub-indices (Welzel 2013)",
        "Religiosity": "F034+F028+F029+F024+F025+Q6 (Norris & Inglehart 2004)",
        "GenderEgalitarianism": "C001+D059+D060+D061 (Inglehart & Norris 2003)",
        "InstitutionalTrust": "Mean across E069 battery (Newton & Norris 2000)",
        "SecularRationalValues": "F034+Q6+Q45+Q22 (Inglehart-Welzel Y-axis approx.)",
        "SelfExpressionValues": "Q57+Q209+Q182+Y001 (Inglehart-Welzel X-axis approx.)",
    }
    for iname, iseries in validated_indices.items():
        n = int(iseries.notna().sum())
        desc = index_descriptions.get(iname, "")
        lines.append(f"| {iname} | {n} | {desc} |")

    lines += ["", "---", ""]

    # Part 1: Constructs WITH validated equivalents
    with_equiv = [r for r in results if r["has_validated_equivalent"]]
    lines += [
        f"## Part 1: Constructs with Validated Equivalents ({len(with_equiv)})",
        "",
        "Spearman ρ with the closest validated WVS index. Target: ρ > 0.70 (good convergent validity).",
        "",
        "| Construct | Type | α | N_valid | Validated index | ρ | p | Verdict |",
        "|-----------|------|---|---------|-----------------|---|---|---------|",
    ]
    for r in sorted(with_equiv, key=lambda x: x["key"]):
        alpha_str = f"{r['alpha']:.3f}" if r.get("alpha") else "—"
        for cv in r["convergent_validity"]:
            if not cv.get("available"):
                rho_str, p_str, verd = "N/A", "—", "—"
            else:
                rho_str = f"{cv['rho']:+.3f}"
                p_str = f"{cv['p']:.4f}"
                verd = cv.get("verdict", "?")
            lines.append(
                f"| `{r['key']}` | {r['type']} | {alpha_str} | {r['descriptive']['n_valid']} "
                f"| {cv['index']} | {rho_str} | {p_str} | **{verd}** |"
            )

    lines += ["", "### Detailed SES Gradients for Validated Constructs", ""]
    for r in sorted(with_equiv, key=lambda x: x["key"]):
        good_cv = [cv for cv in r["convergent_validity"] if cv.get("verdict") in ("good", "partial")]
        ses = r["ses_gradient"]
        if not ses:
            continue
        lines.append(f"**{r['key']}** (α={r.get('alpha')}, {r['type']})")
        ses_parts = [f"{k}: ρ={v['rho']:+.3f} (p={v['p']:.3f})" for k, v in ses.items()]
        lines.append("  SES: " + " | ".join(ses_parts))
        lines.append("")

    # Part 2: Constructs WITHOUT validated equivalents
    without_equiv = [r for r in results if not r["has_validated_equivalent"]]
    lines += [
        "---",
        "",
        f"## Part 2: Constructs Without Validated Equivalents ({len(without_equiv)})",
        "",
        "These are either novel to WVS-Mexico context or WVS items not covered by major indices.",
        "Profile: descriptive stats + SES gradient + overlap with los_mex domains.",
        "",
    ]

    for r in sorted(without_equiv, key=lambda x: x["key"]):
        d = r["descriptive"]
        ses = r["ses_gradient"]
        wvs_dom = r["wvs_domain"]
        los_mex_overlap = _DOMAIN_OVERLAP.get(wvs_dom, "unknown")
        alpha_str = f"α={r['alpha']:.3f}" if r.get("alpha") else r["type"]

        lines += [
            f"### `{r['key']}` ({alpha_str})",
            "",
            f"**Domain overlap (los_mex):** {los_mex_overlap}",
            f"**Items:** {r.get('n_items', '?')} | N_valid: {d['n_valid']}",
            f"**Descriptive:** mean={d['mean']}, std={d['std']}, skew={d['skew']} (scale 1–10)",
            "",
        ]
        if ses:
            lines.append("**SES gradient:**")
            lines.append("")
            lines.append("| SES variable | Spearman ρ | p-value | Interpretation |")
            lines.append("|---|---|---|---|")
            for ses_col, vals in ses.items():
                rho = vals["rho"]
                pval = vals["p"]
                interp = "strong" if abs(rho) > 0.2 else ("moderate" if abs(rho) > 0.1 else "weak")
                sig = "*" if pval < 0.05 else ""
                lines.append(f"| {ses_col} | {rho:+.3f}{sig} | {pval:.4f} | {interp} |")
            lines.append("")

        # Predict what we'd expect if this connects to the cross-dataset bridge
        lines.append("**Bridge expectation:**")
        if d.get("skew") is not None and abs(d["skew"]) > 1.5:
            lines.append("  - Highly skewed distribution → may need ordinal treatment in bridge")
        if any(abs(v["rho"]) > 0.15 for v in ses.values()):
            lines.append("  - Meaningful SES gradients → likely to show significant DR bridge edges")
        else:
            lines.append("  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)")
        if d.get("std") is not None and d["std"] < 1.0:
            lines.append("  - Very low variance → ceiling/floor effect, CI may be wide")
        lines.append("")

    # Part 3: Summary comparison table
    lines += [
        "---",
        "",
        "## Part 3: Aggregate Validation Performance",
        "",
    ]

    valid_cvs = [
        cv
        for r in with_equiv
        for cv in r["convergent_validity"]
        if cv.get("available")
    ]
    if valid_cvs:
        rhos = [abs(cv["rho"]) for cv in valid_cvs]
        n_good = sum(1 for cv in valid_cvs if cv.get("verdict") == "good")
        n_partial = sum(1 for cv in valid_cvs if cv.get("verdict") == "partial")
        n_poor = sum(1 for cv in valid_cvs if cv.get("verdict") == "poor")
        lines += [
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Constructs with validated equivalent | {len(with_equiv)} |",
            f"| Convergent validity tests | {len(valid_cvs)} |",
            f"| Good (ρ > 0.70) | {n_good} |",
            f"| Partial (0.50–0.70) | {n_partial} |",
            f"| Poor (ρ < 0.50) | {n_poor} |",
            f"| Mean \\|ρ\\| | {np.mean(rhos):.3f} |",
            f"| Median \\|ρ\\| | {np.median(rhos):.3f} |",
            "",
            "**Interpretation**: Mean |ρ| > 0.70 = our LLM clustering replicates academic indices well. "
            "Poor performers should be checked against the coherence review for potential item revision.",
            "",
        ]

    lines += [
        "## Part 4: Constructs With No WVS Equivalent — What to Expect in the DR Bridge",
        "",
        "Constructs without validated equivalents cluster into two groups:",
        "",
        "**Group A — Novel WVS constructs** (items exist in WVS but no published scale):",
        "- Expected: some will show significant DR bridge edges with los_mex (especially if SES gradient is present)",
        "- Validation path: compare to los_mex constructs in the same semantic domain via anchor discovery",
        "",
        "**Group B — Single-item tier2 constructs**:",
        "- Expected: wider CIs in DR bridge sweep (less reliable measurement = more noise)",
        "- These are included for breadth but should be interpreted cautiously",
        "",
        "Key diagnostic: SES gradient ρ with escol (education) is the best predictor of DR bridge significance.",
        "Constructs with |ρ(escol)| > 0.15 are strong candidates for significant bridge edges.",
        "",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report: {out_path}")


if __name__ == "__main__":
    main()
