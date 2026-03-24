"""
Phase 3.3 — WVS Temporal Analysis (Mexico, 7 waves, 1981-2022)

Analyzes temporal sweep results: γ time series, trend detection,
structural stability, bipartition persistence.

Output:
  data/results/wvs_temporal_report.md
  data/results/wvs_temporal_stats.json

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_wvs_temporal.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import WAVE_LABELS

SWEEP_PATH  = ROOT / "data" / "results" / "wvs_temporal_sweep_mex.json"
OUTPUT_MD   = ROOT / "data" / "results" / "wvs_temporal_report.md"
OUTPUT_JSON = ROOT / "data" / "results" / "wvs_temporal_stats.json"

# Wave midpoint years for regression
WAVE_YEARS = {1: 1982, 2: 1992, 3: 1996, 4: 2001, 5: 2007, 6: 2012, 7: 2018}


def parse_key(full_key: str) -> tuple[str, str, str]:
    """Parse 'WVS_W7_MEX::va::vb' → (context, va, vb)."""
    parts = full_key.split("::")
    return parts[0], parts[1], parts[2]


def pair_id(va: str, vb: str) -> str:
    return "::".join(sorted([va, vb]))


def wave_from_context(ctx: str) -> int:
    """WVS_W3_MEX → 3"""
    return int(ctx.split("_")[1][1:])


def weighted_linreg(years: list[float], gammas: list[float], weights: list[float]):
    """Weighted linear regression: γ = a + b*year. Returns (slope, intercept, r2)."""
    y = np.array(years, dtype=float)
    g = np.array(gammas, dtype=float)
    w = np.array(weights, dtype=float)
    w = w / w.sum()

    y_mean = np.average(y, weights=w)
    g_mean = np.average(g, weights=w)
    cov_yg = np.average((y - y_mean) * (g - g_mean), weights=w)
    var_y = np.average((y - y_mean) ** 2, weights=w)
    var_g = np.average((g - g_mean) ** 2, weights=w)

    if var_y < 1e-12:
        return 0.0, g_mean, 0.0

    slope = cov_yg / var_y
    intercept = g_mean - slope * y_mean
    r2 = (cov_yg ** 2) / (var_y * var_g) if var_g > 1e-12 else 0.0
    return float(slope), float(intercept), float(r2)


def main():
    if not SWEEP_PATH.exists():
        print(f"ERROR: {SWEEP_PATH} not found. Run temporal sweep first.")
        sys.exit(1)

    with open(SWEEP_PATH) as f:
        data = json.load(f)
    estimates = data.get("estimates", {})
    print(f"Total estimates: {len(estimates)}")

    # ── Organize by wave and pair ─────────────────────────────────────────
    by_wave: dict[int, dict] = defaultdict(dict)
    by_pair: dict[str, dict] = defaultdict(dict)  # pair → {wave: gamma}

    for key, est in estimates.items():
        if "dr_gamma" not in est:
            continue
        ctx, va, vb = parse_key(key)
        wave = wave_from_context(ctx)
        pid = pair_id(va, vb)
        by_wave[wave][pid] = est
        by_pair[pid][wave] = {
            "gamma": est["dr_gamma"],
            "ci_width": est.get("ci_width", 0),
            "excl_zero": est.get("excl_zero", False),
        }

    waves = sorted(by_wave.keys())
    print(f"Waves: {waves}")
    print(f"Unique pairs: {len(by_pair)}")

    # ── Per-wave summary ──────────────────────────────────────────────────
    wave_stats = {}
    for w in waves:
        ests = by_wave[w]
        gammas = [e["dr_gamma"] for e in ests.values()]
        n_sig = sum(1 for e in ests.values() if e.get("excl_zero"))
        wave_stats[w] = {
            "n_pairs": len(gammas),
            "n_significant": n_sig,
            "pct_significant": round(100 * n_sig / max(len(gammas), 1), 1),
            "median_abs_gamma": round(float(np.median(np.abs(gammas))), 4) if gammas else 0,
            "mean_abs_gamma": round(float(np.mean(np.abs(gammas))), 4) if gammas else 0,
            "median_ci_width": round(float(np.median([e.get("ci_width", 0) for e in ests.values()])), 4),
            "year": WAVE_YEARS.get(w, 0),
            "label": WAVE_LABELS.get(w, f"Wave {w}"),
        }

    # ── Trend detection for pairs in 3+ waves ────────────────────────────
    trends = {}
    for pid, wave_data in by_pair.items():
        if len(wave_data) < 3:
            continue
        ws = sorted(wave_data.keys())
        years = [float(WAVE_YEARS[w]) for w in ws]
        gammas = [wave_data[w]["gamma"] for w in ws]
        ci_widths = [wave_data[w]["ci_width"] for w in ws]
        weights = [1.0 / max(ciw, 0.001) for ciw in ci_widths]

        slope, intercept, r2 = weighted_linreg(years, gammas, weights)

        trends[pid] = {
            "n_waves": len(ws),
            "waves": ws,
            "gammas": [round(g, 4) for g in gammas],
            "slope_per_decade": round(slope * 10, 5),
            "intercept": round(intercept, 4),
            "r2": round(r2, 4),
            "sign_stable": all(g > 0 for g in gammas) or all(g <= 0 for g in gammas),
        }

    # Strongest trends
    strong_trends = sorted(
        trends.items(),
        key=lambda x: -abs(x[1]["slope_per_decade"])
    )

    # Most stable pairs
    stable_pairs = sorted(
        [(pid, t) for pid, t in trends.items() if t["n_waves"] >= 4],
        key=lambda x: x[1]["r2"]
    )

    # ── Structural stability: rank correlation between adjacent waves ─────
    rank_correlations = []
    for i in range(len(waves) - 1):
        w1, w2 = waves[i], waves[i + 1]
        shared_pairs = set(by_wave[w1].keys()) & set(by_wave[w2].keys())
        if len(shared_pairs) < 10:
            continue
        g1 = [by_wave[w1][p]["dr_gamma"] for p in shared_pairs]
        g2 = [by_wave[w2][p]["dr_gamma"] for p in shared_pairs]
        # Spearman rank correlation
        from scipy.stats import spearmanr
        rho, pval = spearmanr(g1, g2)
        rank_correlations.append({
            "wave_pair": f"W{w1}→W{w2}",
            "n_shared": len(shared_pairs),
            "spearman_rho": round(float(rho), 3),
            "p_value": round(float(pval), 4),
        })

    # ── Write report ──────────────────────────────────────────────────────
    lines = [
        "# WVS Temporal Analysis — Mexico (1981-2022)",
        "",
        "## Wave Summary",
        "",
        "| Wave | Year | Pairs | Sig | %Sig | Med|γ| | Med CI_w |",
        "|------|------|-------|-----|------|--------|----------|",
    ]
    for w in waves:
        ws = wave_stats[w]
        lines.append(f"| W{w} | {ws['year']} | {ws['n_pairs']} | {ws['n_significant']} | "
                     f"{ws['pct_significant']}% | {ws['median_abs_gamma']} | {ws['median_ci_width']} |")

    lines.extend([
        "",
        f"## Pairs with Trends (3+ waves): {len(trends)}",
        "",
        "### Strongest Trends (slope per decade)",
        "",
        "| Pair | Waves | Slope/decade | R² | Sign stable |",
        "|------|-------|-------------|-----|-------------|",
    ])
    for pid, t in strong_trends[:20]:
        lines.append(f"| {pid[:60]} | {t['n_waves']} | {t['slope_per_decade']:+.5f} | "
                     f"{t['r2']:.3f} | {'Yes' if t['sign_stable'] else 'No'} |")

    if rank_correlations:
        lines.extend([
            "",
            "## Structural Stability (γ rank correlation between adjacent waves)",
            "",
            "| Transition | Shared pairs | Spearman ρ | p-value |",
            "|-----------|-------------|-----------|---------|",
        ])
        for rc in rank_correlations:
            lines.append(f"| {rc['wave_pair']} | {rc['n_shared']} | {rc['spearman_rho']} | {rc['p_value']} |")

    lines.extend(["", "---", "*Generated by analyze_wvs_temporal.py*"])

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(lines))
    print(f"Report: {OUTPUT_MD}")

    output = {
        "wave_stats": {str(k): v for k, v in wave_stats.items()},
        "n_trends": len(trends),
        "n_rank_correlations": len(rank_correlations),
        "rank_correlations": rank_correlations,
    }
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Stats: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
