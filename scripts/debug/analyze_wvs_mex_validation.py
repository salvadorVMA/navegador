"""
Phase 1.4 — WVS Mexico validation analysis

Compares WVS within-survey γ estimates (same respondents) with los_mex
cross-survey γ estimates (different surveys). Uses the construct cross-map
to match equivalent constructs across the two datasets.

Analysis:
  1. Within-survey γ distribution (WVS MEX W7)
  2. Comparison with los_mex bridge γ (for matched pairs)
  3. Sign agreement test
  4. CI width comparison (within vs cross-survey)

Output:
  data/results/wvs_mex_validation_report.md
  data/results/wvs_mex_validation_stats.json

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_wvs_mex_validation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

WVS_SWEEP   = ROOT / "data" / "results" / "wvs_mex_w7_within_sweep.json"
LOSMEX_SWEEP = ROOT / "data" / "results" / "construct_dr_sweep_v5_julia_v4.json"
CROSS_MAP   = ROOT / "data" / "results" / "wvs_losmex_construct_map.json"
OUTPUT_MD   = ROOT / "data" / "results" / "wvs_mex_validation_report.md"
OUTPUT_JSON = ROOT / "data" / "results" / "wvs_mex_validation_stats.json"


def load_wvs_sweep() -> dict:
    with open(WVS_SWEEP) as f:
        data = json.load(f)
    return data.get("estimates", {})


def load_losmex_sweep() -> dict:
    with open(LOSMEX_SWEEP) as f:
        data = json.load(f)
    return data.get("estimates", {})


def load_cross_map() -> dict:
    with open(CROSS_MAP) as f:
        return json.load(f)


def main():
    if not WVS_SWEEP.exists():
        print(f"ERROR: {WVS_SWEEP} not found. Run Julia sweep first.")
        sys.exit(1)

    wvs_estimates = load_wvs_sweep()
    print(f"WVS within-survey estimates: {len(wvs_estimates)}")

    # ── 1. WVS within-survey γ distribution ──────────────────────────────────
    gammas = []
    ci_widths = []
    n_sig = 0
    for key, est in wvs_estimates.items():
        if "dr_gamma" in est:
            g = est["dr_gamma"]
            gammas.append(g)
            ci_widths.append(est.get("ci_width", 0))
            if est.get("excl_zero", False):
                n_sig += 1

    gammas = np.array(gammas)
    ci_widths = np.array(ci_widths)
    abs_gammas = np.abs(gammas)

    stats = {
        "n_estimates": len(gammas),
        "n_significant": n_sig,
        "pct_significant": round(100 * n_sig / max(len(gammas), 1), 1),
        "median_abs_gamma": round(float(np.median(abs_gammas)), 4),
        "mean_abs_gamma": round(float(np.mean(abs_gammas)), 4),
        "max_abs_gamma": round(float(np.max(abs_gammas)), 4) if len(abs_gammas) else 0,
        "median_ci_width": round(float(np.median(ci_widths)), 4),
        "mean_ci_width": round(float(np.mean(ci_widths)), 4),
        "p10_ci_width": round(float(np.percentile(ci_widths, 10)), 4) if len(ci_widths) else 0,
        "p90_ci_width": round(float(np.percentile(ci_widths, 90)), 4) if len(ci_widths) else 0,
        "n_positive": int(np.sum(gammas > 0)),
        "n_negative": int(np.sum(gammas < 0)),
    }

    print(f"\nWVS within-survey stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # ── 2. Compare with los_mex (if available) ─────────────────────────────
    comparison = {}
    if LOSMEX_SWEEP.exists() and CROSS_MAP.exists():
        lm_estimates = load_losmex_sweep()
        cross_map = load_cross_map()
        print(f"\nlos_mex estimates: {len(lm_estimates)}")
        print(f"Cross-map entries: {len(cross_map.get('mappings', []))}")

        # Build WVS construct → los_mex construct lookup
        wvs_to_lm = {}
        for mapping in cross_map.get("mappings", []):
            if mapping.get("best_match") and mapping["best_match"]["score"] >= 0.3:
                wvs_key = mapping["wvs_key"]
                wvs_col = mapping["wvs_col"]
                lm_col = mapping["best_match"]["losmex_col"]
                lm_domain = mapping["best_match"]["losmex_domain"]
                wvs_to_lm[wvs_col] = {
                    "losmex_col": lm_col,
                    "losmex_domain": lm_domain,
                    "match_score": mapping["best_match"]["score"],
                }

        # For each WVS pair, find corresponding los_mex pair
        matched_pairs = []
        for wvs_key, wvs_est in wvs_estimates.items():
            if "dr_gamma" not in wvs_est:
                continue
            # Key format: WVS_W7_MEX::wvs_agg_X|WVS_A::wvs_agg_Y|WVS_B
            parts = wvs_key.split("::")
            if len(parts) != 3:
                continue
            ctx, va, vb = parts
            col_a = va.split("|")[0]
            col_b = vb.split("|")[0]

            # Both must have los_mex matches
            if col_a not in wvs_to_lm or col_b not in wvs_to_lm:
                continue

            lm_a = wvs_to_lm[col_a]
            lm_b = wvs_to_lm[col_b]

            # Find los_mex estimate for this pair
            lm_key = f"{lm_a['losmex_col']}|{lm_a['losmex_domain']}::{lm_b['losmex_col']}|{lm_b['losmex_domain']}"
            lm_key_rev = f"{lm_b['losmex_col']}|{lm_b['losmex_domain']}::{lm_a['losmex_col']}|{lm_a['losmex_domain']}"

            lm_est = lm_estimates.get(lm_key) or lm_estimates.get(lm_key_rev)
            if lm_est and "dr_gamma" in lm_est:
                matched_pairs.append({
                    "wvs_pair": f"{col_a}::{col_b}",
                    "losmex_pair": lm_key,
                    "wvs_gamma": wvs_est["dr_gamma"],
                    "wvs_ci_width": wvs_est.get("ci_width", 0),
                    "wvs_excl_zero": wvs_est.get("excl_zero", False),
                    "losmex_gamma": lm_est["dr_gamma"],
                    "losmex_ci_width": lm_est.get("ci_width", 0),
                    "losmex_excl_zero": lm_est.get("excl_zero", False),
                    "sign_agree": (wvs_est["dr_gamma"] > 0) == (lm_est["dr_gamma"] > 0),
                    "gamma_diff": abs(wvs_est["dr_gamma"] - lm_est["dr_gamma"]),
                    "match_score": min(lm_a["match_score"], lm_b["match_score"]),
                })

        if matched_pairs:
            n_matched = len(matched_pairs)
            sign_agree = sum(1 for p in matched_pairs if p["sign_agree"])
            gamma_diffs = [p["gamma_diff"] for p in matched_pairs]
            wvs_cis = [p["wvs_ci_width"] for p in matched_pairs]
            lm_cis = [p["losmex_ci_width"] for p in matched_pairs]

            comparison = {
                "n_matched_pairs": n_matched,
                "sign_agreement": round(100 * sign_agree / n_matched, 1),
                "median_gamma_diff": round(float(np.median(gamma_diffs)), 4),
                "mean_gamma_diff": round(float(np.mean(gamma_diffs)), 4),
                "median_wvs_ci": round(float(np.median(wvs_cis)), 4),
                "median_losmex_ci": round(float(np.median(lm_cis)), 4),
                "ci_ratio": round(float(np.median(wvs_cis)) / max(float(np.median(lm_cis)), 1e-6), 2),
                "top_matches": sorted(matched_pairs, key=lambda x: -abs(x["wvs_gamma"]))[:10],
            }

            print(f"\n  Matched pairs: {n_matched}")
            print(f"  Sign agreement: {comparison['sign_agreement']}%")
            print(f"  Median γ difference: {comparison['median_gamma_diff']}")
            print(f"  WVS CI width: {comparison['median_wvs_ci']} vs los_mex: {comparison['median_losmex_ci']}")

    # ── 3. Write report ───────────────────────────────────────────────────
    report_lines = [
        "# WVS Mexico W7 — Within-Survey Validation Report",
        "",
        "## 1. Within-Survey γ Distribution",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total estimates | {stats['n_estimates']} |",
        f"| Significant (CI excl 0) | {stats['n_significant']} ({stats['pct_significant']}%) |",
        f"| Median |γ| | {stats['median_abs_gamma']} |",
        f"| Mean |γ| | {stats['mean_abs_gamma']} |",
        f"| Max |γ| | {stats['max_abs_gamma']} |",
        f"| Median CI width | {stats['median_ci_width']} |",
        f"| P10 CI width | {stats['p10_ci_width']} |",
        f"| P90 CI width | {stats['p90_ci_width']} |",
        f"| Positive γ | {stats['n_positive']} |",
        f"| Negative γ | {stats['n_negative']} |",
        "",
    ]

    if comparison:
        report_lines.extend([
            "## 2. Cross-Dataset Validation (WVS vs los_mex)",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Matched pairs | {comparison['n_matched_pairs']} |",
            f"| Sign agreement | {comparison['sign_agreement']}% |",
            f"| Median γ difference | {comparison['median_gamma_diff']} |",
            f"| Median WVS CI width | {comparison['median_wvs_ci']} |",
            f"| Median los_mex CI width | {comparison['median_losmex_ci']} |",
            f"| CI ratio (WVS/los_mex) | {comparison['ci_ratio']} |",
            "",
            "### Top Matched Pairs by |γ|",
            "",
            "| WVS pair | γ_WVS | γ_los_mex | Sign agree | Match score |",
            "|----------|-------|-----------|------------|-------------|",
        ])
        for p in comparison.get("top_matches", []):
            report_lines.append(
                f"| {p['wvs_pair']} | {p['wvs_gamma']:.4f} | {p['losmex_gamma']:.4f} | "
                f"{'Yes' if p['sign_agree'] else 'No'} | {p['match_score']:.3f} |"
            )

    report_lines.extend([
        "",
        "## Key Findings",
        "",
        "Within-survey γ (same respondents) provides tighter CIs than cross-survey",
        "bridges because there is no cross-dataset sampling uncertainty. This serves",
        "as a validation benchmark for the cross-survey bridge methodology.",
        "",
        "---",
        f"*Generated by analyze_wvs_mex_validation.py*",
    ])

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(report_lines))
    print(f"\nReport: {OUTPUT_MD}")

    # Save stats JSON
    output = {"wvs_within_stats": stats, "cross_validation": comparison}
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Stats: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
