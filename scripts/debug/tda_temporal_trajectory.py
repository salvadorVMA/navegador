"""
Phase 6 (Temporal) — Temporal spectral trajectory analysis.

Computes wave-to-wave spectral distances for Mexico (W3-W7), tracks mediator
evolution, detects structural change points, and builds edge confidence scores.

This answers: "Is Mexico's SES-attitude network changing shape over time,
or just rescaling?"

Input:
  data/tda/temporal/spectral_features.json    — per-wave spectra (Phase 5)
  data/tda/temporal/mediators_per_wave.json   — per-wave mediator scores
  data/tda/temporal/temporal_edge_table.csv   — all edges across waves (Phase 4)

Output:
  data/tda/temporal/temporal_trajectory.json  — full trajectory analysis
  data/tda/temporal/edge_confidence.csv       — per-edge temporal confidence

Run:
  python scripts/debug/tda_temporal_trajectory.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TEMPORAL_DIR = ROOT / "data" / "tda" / "temporal"
OUTPUT_DIR = TEMPORAL_DIR


def spectral_distance(s1: list[float], s2: list[float]) -> float:
    """L2 distance between two sorted eigenvalue vectors (padded if needed)."""
    n = max(len(s1), len(s2))
    v1 = np.zeros(n)
    v2 = np.zeros(n)
    v1[:len(s1)] = s1
    v2[:len(s2)] = s2
    return float(np.linalg.norm(v1 - v2))


def main():
    print("=" * 60)
    print("Temporal Phase 6 — Spectral Trajectory Analysis")
    print("=" * 60)

    # ── Load data ─────────────────────────────────────────────────────────
    with open(TEMPORAL_DIR / "spectral_features.json") as f:
        spectra = json.load(f)
    with open(TEMPORAL_DIR / "mediators_per_wave.json") as f:
        mediators = json.load(f)
    edges_df = pd.read_csv(TEMPORAL_DIR / "temporal_edge_table.csv")

    waves = sorted(spectra.keys())  # ["W3", "W4", ...]
    print(f"Waves: {waves}")

    # ── 1. Wave-to-wave spectral distances ────────────────────────────────
    print("\n[1/4] Spectral trajectory...")
    trajectory = []
    for i in range(len(waves) - 1):
        w1, w2 = waves[i], waves[i + 1]
        s1 = spectra[w1]["spectrum"]
        s2 = spectra[w2]["spectrum"]
        d = spectral_distance(s1, s2)
        trajectory.append({
            "from_wave": w1,
            "to_wave": w2,
            "from_year": spectra[w1]["year"],
            "to_year": spectra[w2]["year"],
            "spectral_distance": round(d, 6),
            "years_apart": spectra[w2]["year"] - spectra[w1]["year"],
            "distance_per_year": round(d / max(spectra[w2]["year"] - spectra[w1]["year"], 1), 6),
        })
        print(f"  {w1}({spectra[w1]['year']}) → {w2}({spectra[w2]['year']}): "
              f"d={d:.4f}, rate={d / max(spectra[w2]['year'] - spectra[w1]['year'], 1):.5f}/yr")

    # Also compute W3→W7 total distance
    d_total = spectral_distance(spectra[waves[0]]["spectrum"], spectra[waves[-1]]["spectrum"])
    d_sum = sum(t["spectral_distance"] for t in trajectory)
    print(f"\n  Total (sum of steps): {d_sum:.4f}")
    print(f"  Direct (W{waves[0][1:]}→W{waves[-1][1:]}): {d_total:.4f}")
    print(f"  Ratio (path/direct): {d_sum / max(d_total, 1e-9):.2f}")

    # ── 2. Mediator evolution ─────────────────────────────────────────────
    print("\n[2/4] Mediator evolution...")
    mediator_timeline = {}
    for w in waves:
        top = mediators[w]["top_mediator"]
        score = mediators[w]["top_score"]
        mediator_timeline[w] = {"top_mediator": top, "top_score": score}
        print(f"  {w} ({spectra[w]['year']}): {top} (score={score:.0f})")

    # ── 3. Edge confidence scores ─────────────────────────────────────────
    print("\n[3/4] Computing edge confidence...")

    # Group edges by pair
    edges_df["pair"] = edges_df.apply(
        lambda r: "::".join(sorted([r["construct_a"], r["construct_b"]])), axis=1
    )
    pair_groups = edges_df.groupby("pair")

    confidence_rows = []
    for pair_key, group in pair_groups:
        ca, cb = pair_key.split("::")
        gammas = group.sort_values("wave")
        n_waves = len(gammas)
        n_sig = 0  # would need CI data; approximate from magnitude
        signs = np.sign(gammas["gamma"].values)
        sign_stable = bool(np.all(signs == signs[0])) if len(signs) > 0 else True

        # Trend fit (simple OLS: γ = a + b*year)
        slope, r2 = 0.0, 0.0
        if n_waves >= 3:
            years = gammas["year"].values.astype(float)
            gs = gammas["gamma"].values
            if np.std(years) > 0:
                slope_raw = np.polyfit(years, gs, 1)
                slope = slope_raw[0] * 10  # per decade
                predicted = np.polyval(slope_raw, years)
                ss_res = np.sum((gs - predicted) ** 2)
                ss_tot = np.sum((gs - np.mean(gs)) ** 2)
                r2 = 1 - ss_res / max(ss_tot, 1e-12)

        confidence_rows.append({
            "construct_a": ca,
            "construct_b": cb,
            "n_waves_measured": n_waves,
            "sign_stable": sign_stable,
            "mean_gamma": round(float(gammas["gamma"].mean()), 4),
            "std_gamma": round(float(gammas["gamma"].std()), 4) if n_waves > 1 else 0.0,
            "slope_per_decade": round(slope, 5),
            "trend_r2": round(r2, 3),
            "first_wave": int(gammas["wave"].min()),
            "last_wave": int(gammas["wave"].max()),
            "gamma_range": f"[{gammas['gamma'].min():.4f}, {gammas['gamma'].max():.4f}]",
        })

    conf_df = pd.DataFrame(confidence_rows)
    conf_df.to_csv(OUTPUT_DIR / "edge_confidence.csv", index=False)
    print(f"  {len(conf_df)} unique pairs scored")
    print(f"  Sign-stable: {conf_df['sign_stable'].sum()} ({100 * conf_df['sign_stable'].mean():.0f}%)")
    print(f"  Measured in 3+ waves: {(conf_df['n_waves_measured'] >= 3).sum()}")

    # Top trending pairs
    trending = conf_df[conf_df["n_waves_measured"] >= 3].nlargest(5, "slope_per_decade")
    print("\n  Strongest upward trends (γ/decade):")
    for _, r in trending.iterrows():
        print(f"    {r['construct_a'][:30]} × {r['construct_b'][:30]}: "
              f"+{r['slope_per_decade']:.4f}/dec (R²={r['trend_r2']:.2f})")

    declining = conf_df[conf_df["n_waves_measured"] >= 3].nsmallest(5, "slope_per_decade")
    print("  Strongest downward trends:")
    for _, r in declining.iterrows():
        print(f"    {r['construct_a'][:30]} × {r['construct_b'][:30]}: "
              f"{r['slope_per_decade']:.4f}/dec (R²={r['trend_r2']:.2f})")

    # ── 4. Feature evolution ──────────────────────────────────────────────
    print("\n[4/4] Feature evolution summary...")
    feature_evolution = {}
    for w in waves:
        s = spectra[w]
        feature_evolution[w] = {
            "year": s["year"],
            "fiedler": s["fiedler_value"],
            "spectral_entropy": s["spectral_entropy"],
            "spectral_radius": s["spectral_radius"],
            "n_pairs": s["n_pairs"],
            "n_constructs": s["n_constructs_present"],
            "top_mediator": mediator_timeline[w]["top_mediator"],
        }
        print(f"  {w} ({s['year']}): fiedler={s['fiedler_value']:.4f}, "
              f"entropy={s['spectral_entropy']:.3f}, pairs={s['n_pairs']}")

    # ── Save trajectory ───────────────────────────────────────────────────
    result = {
        "trajectory": trajectory,
        "total_spectral_distance": round(d_total, 6),
        "sum_stepwise_distance": round(d_sum, 6),
        "path_direct_ratio": round(d_sum / max(d_total, 1e-9), 3),
        "mediator_timeline": mediator_timeline,
        "feature_evolution": feature_evolution,
        "edge_confidence_summary": {
            "n_pairs": len(conf_df),
            "n_sign_stable": int(conf_df["sign_stable"].sum()),
            "pct_sign_stable": round(100 * conf_df["sign_stable"].mean(), 1),
            "n_measured_3plus": int((conf_df["n_waves_measured"] >= 3).sum()),
        },
    }

    with open(OUTPUT_DIR / "temporal_trajectory.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n{'─' * 60}")
    print(f"  Trajectory: {OUTPUT_DIR / 'temporal_trajectory.json'}")
    print(f"  Edge confidence: {OUTPUT_DIR / 'edge_confidence.csv'}")
    print("Done.")


if __name__ == "__main__":
    main()
