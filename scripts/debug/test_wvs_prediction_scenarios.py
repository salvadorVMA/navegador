#!/usr/bin/env python3
"""
WVS Prediction Engine Test — 5 Scenarios × 6 Countries

Runs DRPredictionEngine.fit() + predict() on real WVS data for 5 theoretically
grounded construct pairs across MEX, USA, JPN, DEU, BRA, NGA.

Outputs:
  Console:  Per-scenario comparison tables
  PNG:      data/results/wvs_prediction_scenarios_heatmap.png
            data/results/wvs_prediction_scenario_circles.png

Usage:
    python scripts/debug/test_wvs_prediction_scenarios.py
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
NAVEGADOR_DATA = Path("/workspaces/navegador_data") / "data" / "results"

COUNTRIES = ["MEX", "USA", "JPN", "DEU", "BRA", "NGA"]

SCENARIOS = [
    {
        "id": "S1", "name": "Autonomy → Political Participation",
        "col_a": "wvs_agg_child_qualities_autonomy_self_expression",
        "col_b": "wvs_agg_online_political_participation",
        "theory": "Emancipative child-rearing values predict digital civic engagement",
        "expected": "Universally positive, strongest in Germany",
    },
    {
        "id": "S2", "name": "Participation → Security Behaviors",
        "col_a": "wvs_agg_online_political_participation",
        "col_b": "wvs_agg_precautionary_security_behaviors",
        "theory": "Does political engagement increase or decrease security anxiety?",
        "expected": "SIGN FLIP: positive in MEX/NGA, negative in JPN/DEU",
    },
    {
        "id": "S3", "name": "Economic Worry → Institutional Trust",
        "col_a": "wvs_agg_socioeconomic_insecurity_worry",
        "col_b": "wvs_agg_confidence_in_domestic_institutions",
        "theory": "Economic anxiety erodes institutional legitimacy",
        "expected": "Universally negative (worry → distrust)",
    },
    {
        "id": "S4", "name": "Moral Permissiveness → Societal Change",
        "col_a": "wvs_agg_sexual_and_reproductive_morality_permissiveness",
        "col_b": "wvs_agg_societal_change_attitudes",
        "theory": "Moral permissiveness predicts openness to societal change",
        "expected": "SIGN FLIP: negative in advanced economies, neutral/positive in developing",
    },
    {
        "id": "S5", "name": "Participation → Anti-Immigration",
        "col_a": "wvs_agg_online_political_participation",
        "col_b": "wvs_agg_perceived_negative_effects_of_immigration",
        "theory": "Digital political engagement and anti-immigrant attitudes",
        "expected": "Sig ALL 6, FLIP: JPN positive vs DEU negative",
    },
]

PROFILES = {
    "Young urban edu F":  {"sexo": 2, "edad": 25, "escol": 4, "Tam_loc": 4},
    "Older rural M":      {"sexo": 1, "edad": 60, "escol": 2, "Tam_loc": 1},
    "Median urban M":     {"sexo": 1, "edad": 38, "escol": 3, "Tam_loc": 3},
    "Young rural F":      {"sexo": 2, "edad": 22, "escol": 2, "Tam_loc": 1},
}


# ─── Run Scenarios ────────────────────────────────────────────────────

def run_scenario(scenario, country_dfs):
    """Run one scenario across all countries. Returns dict of results."""
    from ses_regression import DRPredictionEngine

    col_a = scenario["col_a"]
    col_b = scenario["col_b"]
    results = {}

    for ctry in COUNTRIES:
        df = country_dfs.get(ctry)
        if df is None or col_a not in df.columns or col_b not in df.columns:
            results[ctry] = {"status": "MISSING"}
            continue

        # Check enough non-NaN data
        valid = df[[col_a, col_b]].dropna()
        if len(valid) < 100:
            results[ctry] = {"status": "TOO_FEW", "n": len(valid)}
            continue

        try:
            engine = DRPredictionEngine(
                n_sim=500, n_bootstrap=20, max_categories=5,
                ses_vars=["sexo", "edad", "escol", "Tam_loc"],
            )
            engine.fit(df, df, col_a, col_b)
            gamma = engine._dr_result.get("gamma", 0)
            gamma_ci = engine._dr_result.get("gamma_ci_95", (None, None))

            # Compute percentiles for A values
            a_vals = df[col_a].dropna()
            a_p25 = float(np.percentile(a_vals, 25))
            a_p75 = float(np.percentile(a_vals, 75))

            # Predictions per profile
            predictions = {}
            for pname, ses in PROFILES.items():
                pred_low = engine.predict(ses, a_value=a_p25)
                pred_high = engine.predict(ses, a_value=a_p75)
                # Compute mean predicted B for low vs high A
                cats = pred_low["categories"]
                cat_vals = [float(c) for c in cats]
                mean_b_low = sum(p * v for p, v in zip(pred_low["probabilities"], cat_vals))
                mean_b_high = sum(p * v for p, v in zip(pred_high["probabilities"], cat_vals))
                predictions[pname] = {
                    "mean_b_low_a": round(mean_b_low, 3),
                    "mean_b_high_a": round(mean_b_high, 3),
                    "shift": round(mean_b_high - mean_b_low, 4),
                    "lift_high": pred_high["lift_factors"],
                    "most_likely_high": pred_high["most_likely"],
                }

            results[ctry] = {
                "status": "OK",
                "gamma": round(gamma, 5),
                "gamma_ci": [round(x, 5) if x else None for x in gamma_ci],
                "n": len(valid),
                "predictions": predictions,
                "a_p25": a_p25, "a_p75": a_p75,
            }
        except Exception as e:
            results[ctry] = {"status": "ERROR", "error": str(e)[:80]}

    return results


def print_scenario(scenario, results):
    """Print formatted table for one scenario."""
    print(f"\n{'=' * 75}")
    print(f"  {scenario['id']}: {scenario['name']}")
    print(f"  {scenario['theory']}")
    print(f"  Expected: {scenario['expected']}")
    print(f"{'=' * 75}")

    # Gamma comparison
    print(f"\n  {'Country':<6} {'n':>5} {'γ':>8} {'CI':>22} {'Sig':>4}")
    print(f"  {'─' * 52}")
    for ctry in COUNTRIES:
        r = results.get(ctry, {})
        if r.get("status") != "OK":
            print(f"  {ctry:<6} {r.get('status', '?'):>40}")
            continue
        g = r["gamma"]
        ci = r["gamma_ci"]
        ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci[0] is not None else "[N/A]"
        sig = "***" if ci[0] is not None and (ci[0] > 0 or ci[1] < 0) else ""
        print(f"  {ctry:<6} {r['n']:>5} {g:>+8.4f} {ci_str:>22} {sig:>4}")

    # Prediction shift for one profile (Young urban edu F)
    pname = "Young urban edu F"
    print(f"\n  Prediction shift (A_p25 → A_p75) for '{pname}':")
    print(f"  {'Country':<6} {'E[B|A_low]':>12} {'E[B|A_high]':>13} {'Shift':>8} {'Direction':>12}")
    print(f"  {'─' * 55}")
    for ctry in COUNTRIES:
        r = results.get(ctry, {})
        if r.get("status") != "OK":
            continue
        pred = r["predictions"].get(pname, {})
        shift = pred.get("shift", 0)
        direction = "↑" if shift > 0.01 else "↓" if shift < -0.01 else "~"
        print(f"  {ctry:<6} {pred.get('mean_b_low_a', 0):>12.3f} "
              f"{pred.get('mean_b_high_a', 0):>13.3f} "
              f"{shift:>+8.4f} {direction:>12}")


# ─── Visualizations ───────────────────────────────────────────────────

def plot_heatmap(all_results, output_path):
    """5×6 heatmap: scenarios vs countries, colored by gamma."""
    fig, ax = plt.subplots(figsize=(10, 6))

    matrix = np.zeros((len(SCENARIOS), len(COUNTRIES)))
    sig_mask = np.zeros_like(matrix, dtype=bool)

    for i, sc in enumerate(SCENARIOS):
        res = all_results[sc["id"]]
        for j, ctry in enumerate(COUNTRIES):
            r = res.get(ctry, {})
            if r.get("status") == "OK":
                matrix[i, j] = r["gamma"]
                ci = r.get("gamma_ci", [None, None])
                if ci[0] is not None and (ci[0] > 0 or ci[1] < 0):
                    sig_mask[i, j] = True

    vmax = max(0.05, np.max(np.abs(matrix)))
    im = ax.imshow(matrix, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")

    ax.set_xticks(range(len(COUNTRIES)))
    ax.set_xticklabels(COUNTRIES, fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(SCENARIOS)))
    ax.set_yticklabels([f"{s['id']}: {s['name'][:35]}" for s in SCENARIOS],
                       fontsize=9)

    # Annotate cells
    for i in range(len(SCENARIOS)):
        for j in range(len(COUNTRIES)):
            g = matrix[i, j]
            if abs(g) < 0.001:
                txt = "—"
            else:
                txt = f"{g:+.3f}"
            if sig_mask[i, j]:
                txt += "*"
            color = "white" if abs(g) > vmax * 0.6 else "black"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    fontweight="bold" if sig_mask[i, j] else "normal", color=color)

    plt.colorbar(im, ax=ax, label="Goodman-Kruskal γ", shrink=0.8)
    ax.set_title("WVS Prediction Scenarios — γ Across Countries (Wave 7)\n"
                 "Red = positive co-variation, Blue = negative, * = CI excludes zero",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Heatmap: {output_path}")


COUNTRY_COLORS = {
    "MEX": "#e41a1c",  # red
    "USA": "#377eb8",  # blue
    "JPN": "#4daf4a",  # green
    "DEU": "#ff7f00",  # orange
    "BRA": "#984ea3",  # purple
    "NGA": "#a65628",  # brown
}


def plot_scenario_circles(mex_oq, all_results, manifest, output_path):
    """5 circle plots, each showing one edge per country (color = country,
    solid = positive γ, dashed = negative γ, width ∝ |γ|)."""
    from demo_wvs_ontology import _canonical_layout, DOMAIN_COLORS, WVS_DOMAIN_LABELS

    pos, domains, dam = _canonical_layout(manifest)
    col_to_key = {c["column"]: c["key"] for c in manifest}
    n_dom = len(domains)

    fig, axes = plt.subplots(1, 5, figsize=(45, 9))

    for idx, sc in enumerate(SCENARIOS):
        ax = axes[idx]
        lim = 5.2
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)

        # Sector backgrounds
        sector_deg = 360 / n_dom
        half_deg = sector_deg / 2
        from matplotlib.patches import Wedge
        for dom in domains:
            angle_deg = np.degrees(dam[dom])
            color = DOMAIN_COLORS.get(dom, "#ccc")
            w = Wedge((0, 0), 4.1, angle_deg - half_deg, angle_deg + half_deg,
                      width=1.4, facecolor=color, alpha=0.07, edgecolor=color, linewidth=0.2)
            ax.add_patch(w)

        # Background edges (Mexico network, very faint)
        seen = set()
        for src, edges in mex_oq._bridges.items():
            for e in edges:
                pair = tuple(sorted([src, e["neighbor"]]))
                if pair in seen:
                    continue
                seen.add(pair)
                if src in pos and e["neighbor"] in pos:
                    c = "#d62728" if e["gamma"] > 0 else "#1f77b4"
                    ax.annotate("", xy=pos[e["neighbor"]], xytext=pos[src],
                                arrowprops=dict(arrowstyle="-", color=c,
                                                alpha=0.04, lw=0.2,
                                                connectionstyle="arc3,rad=0.2"))

        # All nodes small
        for c in pos:
            x, y = pos[c]
            dom = c.split("|")[0]
            ax.scatter(x, y, s=8, c=DOMAIN_COLORS.get(dom, "#ccc"),
                       alpha=0.25, edgecolors="white", linewidths=0.15, zorder=3)

        key_a = col_to_key.get(sc["col_a"])
        key_b = col_to_key.get(sc["col_b"])

        if key_a not in pos or key_b not in pos:
            continue

        # Draw one edge per country, fanned with different curvatures
        rad_values = [-0.30, -0.15, 0.0, 0.15, 0.30, 0.45]
        sc_results = all_results[sc["id"]]

        # Find max |gamma| for width scaling
        all_gammas = [abs(sc_results[c].get("gamma", 0))
                      for c in COUNTRIES if sc_results.get(c, {}).get("status") == "OK"]
        g_max = max(all_gammas) if all_gammas else 0.05

        title_parts = []
        for ci, ctry in enumerate(COUNTRIES):
            r = sc_results.get(ctry, {})
            if r.get("status") != "OK":
                continue

            gamma = r["gamma"]
            gc = r.get("gamma_ci", [None, None])
            is_sig = gc[0] is not None and (gc[0] > 0 or gc[1] < 0)
            color = COUNTRY_COLORS[ctry]
            lw = 1.0 + 4.0 * (abs(gamma) / max(g_max, 0.01))
            alpha = 0.9 if is_sig else 0.45
            linestyle = "-" if gamma >= 0 else "--"
            rad = rad_values[ci % len(rad_values)]

            ax.annotate(
                "", xy=pos[key_b], xytext=pos[key_a],
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=color,
                    alpha=alpha,
                    lw=lw,
                    linestyle=linestyle,
                    mutation_scale=12,
                    connectionstyle=f"arc3,rad={rad}",
                ),
                zorder=7,
            )

            sig_mark = "*" if is_sig else ""
            title_parts.append(f"{ctry}:{gamma:+.3f}{sig_mark}")

        # Enlarge endpoints
        for key in [key_a, key_b]:
            x, y = pos[key]
            dom = key.split("|")[0]
            ax.scatter(x, y, s=250, c=DOMAIN_COLORS.get(dom, "#ccc"),
                       alpha=0.95, edgecolors="black", linewidths=1.5, zorder=10)
            short = key.split("|")[1].replace("_", " ")
            if len(short) > 22:
                short = short[:19] + "..."
            # Place label outside the circle
            cx, cy = pos[key]
            offset_y = 0.40 if cy >= 0 else -0.40
            va = "bottom" if cy >= 0 else "top"
            ax.text(cx, cy + offset_y, short, ha="center", va=va,
                    fontsize=5.5, fontweight="bold", zorder=11,
                    path_effects=[pe.withStroke(linewidth=2, foreground="white")])

        # Domain labels (compact)
        for dom in domains:
            angle = dam[dom]
            lx = 4.6 * np.cos(angle)
            ly = 4.6 * np.sin(angle)
            ha = "left" if lx > 0.3 else "right" if lx < -0.3 else "center"
            ax.text(lx, ly, WVS_DOMAIN_LABELS.get(dom, dom),
                    ha=ha, va="center", fontsize=5, fontweight="bold",
                    color=DOMAIN_COLORS.get(dom, "#444"), zorder=6,
                    path_effects=[pe.withStroke(linewidth=1, foreground="white")])

        # Scenario title with per-country gammas
        ax.set_title(f"{sc['id']}: {sc['name'][:35]}\n" + "  ".join(title_parts),
                     fontsize=6.5, fontweight="bold", pad=6)

    # Shared legend
    legend_elements = []
    for ctry in COUNTRIES:
        legend_elements.append(
            mpatches.Patch(facecolor=COUNTRY_COLORS[ctry], label=ctry))
    legend_elements.append(plt.Line2D([0], [0], color="grey", lw=2, linestyle="-",
                                       label="γ > 0 (solid)"))
    legend_elements.append(plt.Line2D([0], [0], color="grey", lw=2, linestyle="--",
                                       label="γ < 0 (dashed)"))
    fig.legend(handles=legend_elements, loc="lower center", ncol=8,
               fontsize=8, framealpha=0.9, bbox_to_anchor=(0.5, 0.0))

    fig.suptitle("Prediction Scenarios — Cross-Country Edge Comparison\n"
                 "Color = country, solid = positive γ, dashed = negative γ, "
                 "width ∝ |γ|, faded = not significant",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0.06, 1, 0.90])
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Circles: {output_path}")


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("WVS Prediction Scenarios — 5 × 6 Countries")
    print("=" * 60)

    # Load DataFrames
    print("\nLoading country CSVs...")
    country_dfs = {}
    for ctry in COUNTRIES:
        csv_path = CSV_DIR / f"WVS_W7_{ctry}.csv"
        if csv_path.exists():
            country_dfs[ctry] = pd.read_csv(csv_path)
            print(f"  {ctry}: {country_dfs[ctry].shape[0]} rows")
        else:
            print(f"  {ctry}: MISSING")

    # Load manifest for circle plots
    manifest = json.load(open(DATA / "wvs_construct_manifest.json"))

    # Build Mexico OntologyQuery for circle plots
    geo = json.load(open(NAVEGADOR_DATA / "wvs_geographic_sweep_w7.json"))
    wvs_fp = json.load(open(DATA / "wvs_ses_fingerprints.json"))["fingerprints"]

    sys.path.insert(0, str(ROOT / "scripts" / "debug"))
    from demo_wvs_ontology import build_country_kg, build_country_fp
    from opinion_ontology import OntologyQuery

    fp_v2 = build_country_fp(manifest, wvs_fp)
    fp_path = DATA / "_tmp_pred_fp.json"
    with open(fp_path, "w") as f:
        json.dump(fp_v2, f)
    mex_kg = build_country_kg("MEX", geo["estimates"], manifest, wvs_fp)
    mex_kg_path = DATA / "_tmp_pred_kg_mex.json"
    with open(mex_kg_path, "w") as f:
        json.dump(mex_kg, f)
    mex_oq = OntologyQuery(fp_path=fp_path, kg_path=mex_kg_path, dataset="wvs_mex")

    # Run scenarios
    all_results = {}
    for sc in SCENARIOS:
        print(f"\n--- {sc['id']}: {sc['name']} ---")
        t1 = time.time()
        results = run_scenario(sc, country_dfs)
        elapsed = time.time() - t1
        all_results[sc["id"]] = results
        print_scenario(sc, results)
        ok = sum(1 for r in results.values() if r.get("status") == "OK")
        print(f"\n  ({ok}/{len(COUNTRIES)} countries, {elapsed:.1f}s)")

    # Visualizations
    print("\n" + "=" * 60)
    print("GENERATING VISUALIZATIONS")
    print("=" * 60)

    plot_heatmap(all_results, DATA / "wvs_prediction_scenarios_heatmap.png")
    plot_scenario_circles(mex_oq, all_results, manifest,
                          DATA / "wvs_prediction_scenario_circles.png")

    # Cleanup
    for f in DATA.glob("_tmp_pred_*"):
        f.unlink()

    total = time.time() - t0
    print(f"\nDone in {total:.0f}s")


if __name__ == "__main__":
    main()
