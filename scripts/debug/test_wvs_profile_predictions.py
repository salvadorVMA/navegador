#!/usr/bin/env python3
"""
WVS Profile Predictions — 5 SES profiles × 5 scenarios × 6 countries

For each combination, runs DRPredictionEngine to answer:
"Given this person's SES, if they score HIGH on construct A,
 how does our prediction for construct B change?"

Key outputs:
  - Expected value of B at baseline (just SES)
  - Expected value of B when A is high (p75)
  - Direction and magnitude of the shift
  - Whether the shift is positive or negative (and how this varies by country)

Usage:
    python scripts/debug/test_wvs_profile_predictions.py
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data" / "results"
CSV_DIR = Path("/workspaces/navegador_data") / "data" / "julia_bridge_wvs"

COUNTRIES = ["MEX", "USA", "JPN", "DEU", "BRA", "NGA"]

SCENARIOS = [
    {
        "id": "S1", "name": "Autonomy → Participation",
        "col_a": "wvs_agg_child_qualities_autonomy_self_expression",
        "col_b": "wvs_agg_online_political_participation",
        "short_a": "Autonomy values", "short_b": "Online participation",
    },
    {
        "id": "S2", "name": "Participation → Security",
        "col_a": "wvs_agg_online_political_participation",
        "col_b": "wvs_agg_precautionary_security_behaviors",
        "short_a": "Online participation", "short_b": "Security behaviors",
    },
    {
        "id": "S3", "name": "Eco Worry → Trust",
        "col_a": "wvs_agg_socioeconomic_insecurity_worry",
        "col_b": "wvs_agg_confidence_in_domestic_institutions",
        "short_a": "Economic worry", "short_b": "Institutional trust",
    },
    {
        "id": "S4", "name": "Morality → Change",
        "col_a": "wvs_agg_sexual_and_reproductive_morality_permissiveness",
        "col_b": "wvs_agg_societal_change_attitudes",
        "short_a": "Moral permissiveness", "short_b": "Openness to change",
    },
    {
        "id": "S5", "name": "Participation → Immigration",
        "col_a": "wvs_agg_online_political_participation",
        "col_b": "wvs_agg_perceived_negative_effects_of_immigration",
        "short_a": "Online participation", "short_b": "Anti-immigration",
    },
]

PROFILES = [
    {"name": "Young urban educated woman",
     "short": "YoungEduUrb♀",
     "ses": {"sexo": 2, "edad": 25, "escol": 4, "Tam_loc": 4}},
    {"name": "Older rural less-educated man",
     "short": "OldRural♂",
     "ses": {"sexo": 1, "edad": 60, "escol": 2, "Tam_loc": 1}},
    {"name": "Middle-aged urban professional man",
     "short": "MidUrbanPro♂",
     "ses": {"sexo": 1, "edad": 40, "escol": 4, "Tam_loc": 3}},
    {"name": "Young rural woman",
     "short": "YoungRural♀",
     "ses": {"sexo": 2, "edad": 22, "escol": 2, "Tam_loc": 1}},
    {"name": "Older urban educated woman",
     "short": "OldEduUrb♀",
     "ses": {"sexo": 2, "edad": 55, "escol": 4, "Tam_loc": 4}},
]

COUNTRY_COLORS = {
    "MEX": "#e41a1c", "USA": "#377eb8", "JPN": "#4daf4a",
    "DEU": "#ff7f00", "BRA": "#984ea3", "NGA": "#a65628",
}


def _expected_value(probs, cats):
    """Compute E[B] = sum(p_i * v_i)."""
    return sum(p * float(c) for p, c in zip(probs, cats))


def fit_engines(country_dfs, scenarios):
    """Fit all engines (scenario × country). Returns nested dict."""
    from ses_regression import DRPredictionEngine

    engines = {}
    for sc in scenarios:
        engines[sc["id"]] = {}
        for ctry in COUNTRIES:
            df = country_dfs.get(ctry)
            if df is None:
                continue
            col_a, col_b = sc["col_a"], sc["col_b"]
            if col_a not in df.columns or col_b not in df.columns:
                continue
            valid = df[[col_a, col_b]].dropna()
            if len(valid) < 100:
                continue

            try:
                engine = DRPredictionEngine(
                    n_sim=500, n_bootstrap=20, max_categories=5,
                    ses_vars=["sexo", "edad", "escol", "Tam_loc"],
                )
                engine.fit(df, df, col_a, col_b)
                engines[sc["id"]][ctry] = engine
                g = engine._dr_result.get("gamma", 0)
                print(f"    {sc['id']}×{ctry}: γ={g:+.4f}")
            except Exception as e:
                print(f"    {sc['id']}×{ctry}: FAILED ({str(e)[:50]})")
    return engines


def run_predictions(engines, scenarios):
    """Run predict() for all profiles. Returns nested results dict."""
    all_results = {}

    for sc in scenarios:
        sc_results = {}
        for ctry in COUNTRIES:
            engine = engines.get(sc["id"], {}).get(ctry)
            if engine is None:
                continue

            df_a = engine._dr_result  # has gamma etc
            gamma = df_a.get("gamma", 0)
            gamma_ci = df_a.get("gamma_ci_95", (None, None))
            is_sig = gamma_ci[0] is not None and (gamma_ci[0] > 0 or gamma_ci[1] < 0)

            # Get A percentiles for "low" and "high" values
            cats_a = engine._cats_a
            cats_b = engine._cats_b
            # Use lowest and highest actual categories as low/high A
            a_low = cats_a[0] if len(cats_a) > 0 else 1.0
            a_high = cats_a[-1] if len(cats_a) > 1 else cats_a[0]
            # For more spread, pick p25 and p75 from categories
            sorted_cats = sorted(cats_a)
            a_low = sorted_cats[len(sorted_cats) // 4] if len(sorted_cats) >= 4 else sorted_cats[0]
            a_high = sorted_cats[-(len(sorted_cats) // 4 + 1)] if len(sorted_cats) >= 4 else sorted_cats[-1]

            profile_results = {}
            for prof in PROFILES:
                try:
                    pred_lo = engine.predict(prof["ses"], a_value=a_low)
                    pred_hi = engine.predict(prof["ses"], a_value=a_high)

                    baseline_ev = _expected_value(pred_lo["baseline"], cats_b)
                    ev_lo = _expected_value(pred_lo["probabilities"], cats_b)
                    ev_hi = _expected_value(pred_hi["probabilities"], cats_b)
                    shift = ev_hi - ev_lo

                    # Compute mean lift across categories
                    lifts = pred_hi["lift_factors"]
                    # Weighted lift: how much does knowing A=high shift probabilities?
                    # Use the lift for the highest B category as the directional signal
                    lift_top = lifts[-1] if lifts else 1.0
                    lift_bottom = lifts[0] if lifts else 1.0

                    profile_results[prof["short"]] = {
                        "baseline_ev": round(baseline_ev, 3),
                        "ev_a_low": round(ev_lo, 3),
                        "ev_a_high": round(ev_hi, 3),
                        "shift": round(shift, 4),
                        "lift_top_cat": round(lift_top, 4),
                        "lift_bottom_cat": round(lift_bottom, 4),
                        "most_likely_hi": pred_hi["most_likely"],
                        "prob_dist_hi": [round(p, 4) for p in pred_hi["probabilities"]],
                        "prob_dist_lo": [round(p, 4) for p in pred_lo["probabilities"]],
                        "baseline_dist": [round(p, 4) for p in pred_lo["baseline"]],
                    }
                except Exception as e:
                    profile_results[prof["short"]] = {"error": str(e)[:60]}

            sc_results[ctry] = {
                "gamma": round(gamma, 5),
                "gamma_ci": [round(x, 5) if x else None for x in gamma_ci],
                "is_sig": is_sig,
                "cats_b": [float(c) for c in cats_b],
                "profiles": profile_results,
            }

        all_results[sc["id"]] = sc_results
    return all_results


def print_results(all_results, scenarios):
    """Print detailed tables."""
    for sc in scenarios:
        print(f"\n{'=' * 90}")
        print(f"  {sc['id']}: {sc['name']}")
        print(f"  A = {sc['short_a']}  →  B = {sc['short_b']}")
        print(f"{'=' * 90}")

        sc_r = all_results.get(sc["id"], {})
        if not sc_r:
            print("  No results")
            continue

        # Gamma row
        print(f"\n  {'':18}", end="")
        for ctry in COUNTRIES:
            print(f" {ctry:>10}", end="")
        print()

        print(f"  {'γ (bridge)':18}", end="")
        for ctry in COUNTRIES:
            r = sc_r.get(ctry, {})
            g = r.get("gamma", 0)
            sig = "*" if r.get("is_sig") else " "
            print(f" {g:>+8.4f}{sig}", end="")
        print()

        # Per-profile predictions
        for prof in PROFILES:
            pname = prof["short"]
            print(f"\n  ── {prof['name']} ──")
            print(f"  {'':18}", end="")
            for ctry in COUNTRIES:
                print(f" {ctry:>10}", end="")
            print()

            # Baseline E[B|SES]
            print(f"  {'Baseline E[B]':18}", end="")
            for ctry in COUNTRIES:
                r = sc_r.get(ctry, {})
                pr = r.get("profiles", {}).get(pname, {})
                val = pr.get("baseline_ev", None)
                print(f" {val:>10.2f}" if val is not None else f" {'—':>10}", end="")
            print()

            # E[B] when A=high
            print(f"  {'E[B|A=high]':18}", end="")
            for ctry in COUNTRIES:
                r = sc_r.get(ctry, {})
                pr = r.get("profiles", {}).get(pname, {})
                val = pr.get("ev_a_high", None)
                print(f" {val:>10.2f}" if val is not None else f" {'—':>10}", end="")
            print()

            # Shift
            print(f"  {'Shift':18}", end="")
            for ctry in COUNTRIES:
                r = sc_r.get(ctry, {})
                pr = r.get("profiles", {}).get(pname, {})
                shift = pr.get("shift", None)
                if shift is not None:
                    arrow = "↑" if shift > 0.005 else "↓" if shift < -0.005 else "~"
                    print(f" {shift:>+8.3f}{arrow}", end="")
                else:
                    print(f" {'—':>10}", end="")
            print()

            # Lift for top B category
            print(f"  {'Lift(top B cat)':18}", end="")
            for ctry in COUNTRIES:
                r = sc_r.get(ctry, {})
                pr = r.get("profiles", {}).get(pname, {})
                lift = pr.get("lift_top_cat", None)
                if lift is not None:
                    print(f" {lift:>10.3f}", end="")
                else:
                    print(f" {'—':>10}", end="")
            print()


def plot_profile_heatmaps(all_results, scenarios, output_path):
    """One heatmap per scenario: profiles × countries, colored by shift magnitude."""
    n_sc = len(scenarios)
    fig, axes = plt.subplots(n_sc, 1, figsize=(12, 3.5 * n_sc))
    if n_sc == 1:
        axes = [axes]

    prof_names = [p["short"] for p in PROFILES]

    for idx, sc in enumerate(scenarios):
        ax = axes[idx]
        sc_r = all_results.get(sc["id"], {})

        matrix = np.zeros((len(PROFILES), len(COUNTRIES)))
        for pi, prof in enumerate(PROFILES):
            for ci, ctry in enumerate(COUNTRIES):
                r = sc_r.get(ctry, {})
                pr = r.get("profiles", {}).get(prof["short"], {})
                matrix[pi, ci] = pr.get("shift", 0)

        vmax = max(0.02, np.max(np.abs(matrix)))
        im = ax.imshow(matrix, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")

        ax.set_xticks(range(len(COUNTRIES)))
        ax.set_xticklabels(COUNTRIES, fontsize=10, fontweight="bold")
        ax.set_yticks(range(len(PROFILES)))
        ax.set_yticklabels(prof_names, fontsize=8)

        for pi in range(len(PROFILES)):
            for ci in range(len(COUNTRIES)):
                val = matrix[pi, ci]
                if abs(val) < 0.001:
                    txt = "~"
                else:
                    arrow = "↑" if val > 0 else "↓"
                    txt = f"{val:+.3f}\n{arrow}"
                color = "white" if abs(val) > vmax * 0.5 else "black"
                ax.text(ci, pi, txt, ha="center", va="center",
                        fontsize=7, color=color, fontweight="bold")

        plt.colorbar(im, ax=ax, label="E[B] shift", shrink=0.8, pad=0.02)

        # Add gamma annotation at top
        gamma_txt = "  ".join(
            f"{ctry}:{sc_r.get(ctry,{}).get('gamma',0):+.3f}{'*' if sc_r.get(ctry,{}).get('is_sig') else ''}"
            for ctry in COUNTRIES
        )
        ax.set_title(f"{sc['id']}: {sc['name']}    (γ: {gamma_txt})",
                     fontsize=10, fontweight="bold", pad=8)

    fig.suptitle("WVS Prediction Shifts by SES Profile\n"
                 "How much does knowing A=high change our prediction of B? "
                 "(Red=↑, Blue=↓, across countries)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Heatmap: {output_path}")


def plot_profile_bars(all_results, scenarios, output_path):
    """Grouped bar chart: for each scenario, show baseline vs A=high E[B] per profile,
    faceted by country. One row per scenario, one column per country."""
    n_sc = len(scenarios)
    n_ctry = len(COUNTRIES)
    fig, axes = plt.subplots(n_sc, n_ctry, figsize=(3.2 * n_ctry, 2.8 * n_sc),
                              sharex=False, sharey=False)

    profile_colors = ["#e41a1c", "#377eb8", "#4daf4a", "#ff7f00", "#984ea3"]
    prof_shorts = [p["short"] for p in PROFILES]
    x = np.arange(len(PROFILES))
    width = 0.35

    for si, sc in enumerate(scenarios):
        sc_r = all_results.get(sc["id"], {})
        for ci, ctry in enumerate(COUNTRIES):
            ax = axes[si, ci] if n_sc > 1 else axes[ci]
            r = sc_r.get(ctry, {})

            baselines = []
            a_highs = []
            for prof in PROFILES:
                pr = r.get("profiles", {}).get(prof["short"], {})
                baselines.append(pr.get("baseline_ev", 0))
                a_highs.append(pr.get("ev_a_high", 0))

            ax.bar(x - width / 2, baselines, width, label="Baseline",
                   color="#bbbbbb", alpha=0.7, edgecolor="white")
            bar_colors = ["#d62728" if h > b + 0.005 else "#1f77b4" if h < b - 0.005 else "#999999"
                          for b, h in zip(baselines, a_highs)]
            ax.bar(x + width / 2, a_highs, width, label="A=high",
                   color=bar_colors, alpha=0.8, edgecolor="white")

            gamma = r.get("gamma", 0)
            sig = "*" if r.get("is_sig") else ""
            ax.set_title(f"{ctry} γ={gamma:+.3f}{sig}", fontsize=8, fontweight="bold")
            ax.set_xticks(x)
            if si == n_sc - 1:
                ax.set_xticklabels([p["short"][:8] for p in PROFILES],
                                    fontsize=5.5, rotation=45, ha="right")
            else:
                ax.set_xticklabels([])
            ax.tick_params(axis="y", labelsize=6)

            if ci == 0:
                ax.set_ylabel(f"{sc['id']}", fontsize=8, fontweight="bold")

    # Legend at bottom
    legend_handles = [
        mpatches.Patch(color="#bbbbbb", label="E[B|SES] baseline"),
        mpatches.Patch(color="#d62728", label="E[B|A=high, SES] ↑"),
        mpatches.Patch(color="#1f77b4", label="E[B|A=high, SES] ↓"),
        mpatches.Patch(color="#999999", label="E[B|A=high, SES] ~"),
    ]
    fig.legend(handles=legend_handles,
               loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.01))

    fig.suptitle("Profile Predictions: Baseline E[B] vs E[B|A=high]\n"
                 "Grey = SES-only baseline, Colored = knowing A shifts prediction",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Bars: {output_path}")


def main():
    t0 = time.time()
    print("WVS Profile Predictions — 5 profiles × 5 scenarios × 6 countries")
    print("=" * 70)

    # Load data
    print("\nLoading country CSVs...")
    country_dfs = {}
    for ctry in COUNTRIES:
        csv_path = CSV_DIR / f"WVS_W7_{ctry}.csv"
        if csv_path.exists():
            country_dfs[ctry] = pd.read_csv(csv_path)
            print(f"  {ctry}: {country_dfs[ctry].shape[0]} rows")

    # Fit engines
    print("\nFitting prediction engines (30 fits)...")
    t1 = time.time()
    engines = fit_engines(country_dfs, SCENARIOS)
    print(f"  Fitted in {time.time() - t1:.0f}s")

    # Run predictions
    print("\nRunning predictions...")
    all_results = run_predictions(engines, SCENARIOS)

    # Print tables
    print_results(all_results, SCENARIOS)

    # Plots
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)

    plot_profile_heatmaps(all_results, SCENARIOS,
                          DATA / "wvs_profile_prediction_heatmaps.png")
    plot_profile_bars(all_results, SCENARIOS,
                      DATA / "wvs_profile_prediction_bars.png")

    total = time.time() - t0
    print(f"\nDone in {total:.0f}s")


if __name__ == "__main__":
    main()
