"""
All-Wave TDA Synthesis — Cross-wave and cross-country analysis
==============================================================

Reads the per-wave and per-country TDA outputs produced by the allwave
pipeline and computes cross-mode synthesis metrics:

  1. Fiedler evolution heatmap (countries × waves)
  2. Global convergence/divergence (spectral distance trends)
  3. Zone temporal trends (zone-mean Fiedler/entropy per wave)
  4. Multi-country spectral trajectories
  5. Mediator stability across waves

Input:
  data/tda/allwave/per_wave/W{n}/spectral/spectral_features.json
  data/tda/allwave/per_wave/W{n}/floyd_warshall/mediator_scores.json
  data/tda/allwave/per_wave/W{n}/spectral/spectral_distance_matrix.csv
  data/tda/allwave/temporal/{ALPHA3}/spectral_features.json
  data/tda/allwave/matrices/global_manifest.json

Output (to data/tda/allwave/convergence/):
  fiedler_heatmap.csv           — countries × waves Fiedler values
  entropy_heatmap.csv           — countries × waves spectral entropy
  convergence_metrics.json      — per-wave-pair convergence statistics
  zone_temporal_trends.csv      — zone-mean features per wave
  mediator_stability.json       — per-country top mediator across waves
  allwave_tda_report.md         — summary report
  fiedler_heatmap.png           — visualization
  zone_trends.png               — zone-level temporal plots
  spectral_trajectories.png     — multi-country Fiedler trajectories

Run:
  python scripts/debug/tda_allwave_analysis.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

ALLWAVE_DIR = ROOT / "data" / "tda" / "allwave"
OUTPUT_DIR  = ALLWAVE_DIR / "convergence"

WAVE_YEARS = {1: 1981, 2: 1990, 3: 1996, 4: 2000, 5: 2007, 6: 2012, 7: 2018}

ZONE_COLORS = {
    "Latin America": "#e74c3c", "English-speaking": "#3498db",
    "Protestant Europe": "#2ecc71", "Catholic Europe": "#9b59b6",
    "Orthodox/ex-Communist": "#f39c12", "Confucian": "#1abc9c",
    "South/Southeast Asian": "#e67e22", "African-Islamic": "#95a5a6",
    "Unknown": "#bdc3c7",
}


# ═══════════════════════════════════════════════════════════════════════════
# 1. FIEDLER EVOLUTION HEATMAP
# ═══════════════════════════════════════════════════════════════════════════

def build_feature_heatmaps() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build countries × waves matrices of Fiedler values and spectral entropy.

    Sources: per-wave geographic spectral_features.json files.
    """
    rows_fiedler = []
    rows_entropy = []

    per_wave_dir = ALLWAVE_DIR / "per_wave"
    if not per_wave_dir.exists():
        print("  WARN: per_wave dir not found, skipping heatmaps")
        return pd.DataFrame(), pd.DataFrame()

    for wave_dir in sorted(per_wave_dir.iterdir()):
        if not wave_dir.is_dir():
            continue
        wave_label = wave_dir.name  # "W3", "W5", etc.
        wave_num = int(wave_label[1:])

        spec_feat_path = wave_dir / "spectral" / "spectral_features.json"
        if not spec_feat_path.exists():
            continue

        with open(spec_feat_path) as f:
            features = json.load(f)

        # features is typically: {country: {fiedler, spectral_gap, entropy, ...}}
        for country, feat in features.items():
            if isinstance(feat, dict):
                fiedler = feat.get("fiedler", feat.get("fiedler_value"))
                entropy = feat.get("spectral_entropy", feat.get("entropy"))
                if fiedler is not None:
                    rows_fiedler.append({
                        "country": country, "wave": wave_num,
                        "year": WAVE_YEARS.get(wave_num, 0),
                        "fiedler": fiedler,
                    })
                if entropy is not None:
                    rows_entropy.append({
                        "country": country, "wave": wave_num,
                        "year": WAVE_YEARS.get(wave_num, 0),
                        "entropy": entropy,
                    })

    # Also check temporal directories for additional data
    temporal_dir = ALLWAVE_DIR / "temporal"
    if temporal_dir.exists():
        for country_dir in sorted(temporal_dir.iterdir()):
            if not country_dir.is_dir():
                continue
            alpha3 = country_dir.name
            spec_path = country_dir / "spectral_features.json"
            if not spec_path.exists():
                continue
            with open(spec_path) as f:
                features = json.load(f)

            for wave_key, feat in features.items():
                if not isinstance(feat, dict):
                    continue
                try:
                    wave_num = int(wave_key.replace("W", ""))
                except ValueError:
                    continue
                fiedler = feat.get("fiedler", feat.get("fiedler_value"))
                entropy = feat.get("spectral_entropy", feat.get("entropy"))
                if fiedler is not None:
                    rows_fiedler.append({
                        "country": alpha3, "wave": wave_num,
                        "year": WAVE_YEARS.get(wave_num, 0),
                        "fiedler": fiedler,
                    })
                if entropy is not None:
                    rows_entropy.append({
                        "country": alpha3, "wave": wave_num,
                        "year": WAVE_YEARS.get(wave_num, 0),
                        "entropy": entropy,
                    })

    df_f = pd.DataFrame(rows_fiedler).drop_duplicates(subset=["country", "wave"])
    df_e = pd.DataFrame(rows_entropy).drop_duplicates(subset=["country", "wave"])

    # Pivot to heatmap format
    if not df_f.empty:
        heatmap_f = df_f.pivot(index="country", columns="wave", values="fiedler")
        heatmap_f.to_csv(OUTPUT_DIR / "fiedler_heatmap.csv")
        print(f"  Fiedler heatmap: {heatmap_f.shape[0]} countries × {heatmap_f.shape[1]} waves")
    else:
        heatmap_f = pd.DataFrame()

    if not df_e.empty:
        heatmap_e = df_e.pivot(index="country", columns="wave", values="entropy")
        heatmap_e.to_csv(OUTPUT_DIR / "entropy_heatmap.csv")
        print(f"  Entropy heatmap: {heatmap_e.shape[0]} countries × {heatmap_e.shape[1]} waves")
    else:
        heatmap_e = pd.DataFrame()

    return heatmap_f, heatmap_e


def plot_fiedler_heatmap(heatmap: pd.DataFrame):
    """Visualize the Fiedler evolution heatmap, sorted by cultural zone."""
    if heatmap.empty:
        return

    # Sort countries by zone then alphabetically
    zone_order = list(ZONE_COLORS.keys())
    heatmap["zone"] = heatmap.index.map(lambda c: COUNTRY_ZONE.get(c, "Unknown"))
    heatmap["zone_rank"] = heatmap["zone"].map(
        lambda z: zone_order.index(z) if z in zone_order else len(zone_order)
    )
    heatmap = heatmap.sort_values(["zone_rank", heatmap.index.name or "country"])
    zones_col = heatmap.pop("zone")
    heatmap.pop("zone_rank")

    fig, ax = plt.subplots(figsize=(10, max(8, len(heatmap) * 0.25)))
    im = ax.imshow(heatmap.values, aspect="auto", cmap="viridis",
                   interpolation="nearest")
    ax.set_yticks(range(len(heatmap)))
    ax.set_yticklabels([f"{c} ({zones_col.iloc[i][:3]})"
                        for i, c in enumerate(heatmap.index)], fontsize=6)
    ax.set_xticks(range(len(heatmap.columns)))
    ax.set_xticklabels([f"W{w}\n{WAVE_YEARS.get(w, '')}" for w in heatmap.columns])
    ax.set_title("Fiedler Value (Algebraic Connectivity) by Country × Wave")
    plt.colorbar(im, ax=ax, label="Fiedler value")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "fiedler_heatmap.png", dpi=150)
    plt.close()
    print(f"  Saved fiedler_heatmap.png")


# ═══════════════════════════════════════════════════════════════════════════
# 2. CONVERGENCE / DIVERGENCE
# ═══════════════════════════════════════════════════════════════════════════

def compute_convergence() -> dict:
    """
    For consecutive wave pairs, compute mean spectral distance between
    countries present in both waves. Decreasing = convergence.
    """
    per_wave_dir = ALLWAVE_DIR / "per_wave"
    if not per_wave_dir.exists():
        return {}

    # Load spectral distance matrices per wave
    spec_matrices = {}
    spec_keys = {}
    for wave_dir in sorted(per_wave_dir.iterdir()):
        if not wave_dir.is_dir():
            continue
        wave_num = int(wave_dir.name[1:])
        sdm_path = wave_dir / "spectral" / "spectral_distance_matrix.csv"
        if not sdm_path.exists():
            continue
        df = pd.read_csv(sdm_path, index_col=0)
        spec_matrices[wave_num] = df.values
        spec_keys[wave_num] = list(df.columns)

    waves = sorted(spec_matrices.keys())
    if len(waves) < 2:
        return {}

    metrics = {}
    for i in range(len(waves) - 1):
        w1, w2 = waves[i], waves[i + 1]
        keys1 = set(spec_keys[w1])
        keys2 = set(spec_keys[w2])
        shared = sorted(keys1 & keys2)

        if len(shared) < 3:
            continue

        # Extract spectral distances for shared countries in wave w2
        # (within-wave distances between shared countries)
        idx2 = [spec_keys[w2].index(c) for c in shared]
        D2 = spec_matrices[w2][np.ix_(idx2, idx2)]
        upper2 = D2[np.triu_indices_from(D2, k=1)]

        idx1 = [spec_keys[w1].index(c) for c in shared]
        D1 = spec_matrices[w1][np.ix_(idx1, idx1)]
        upper1 = D1[np.triu_indices_from(D1, k=1)]

        metrics[f"W{w1}→W{w2}"] = {
            "wave_from": w1, "wave_to": w2,
            "year_from": WAVE_YEARS.get(w1, 0),
            "year_to": WAVE_YEARS.get(w2, 0),
            "shared_countries": len(shared),
            "mean_dist_from": float(np.mean(upper1)),
            "mean_dist_to": float(np.mean(upper2)),
            "delta": float(np.mean(upper2) - np.mean(upper1)),
            "interpretation": "converging" if np.mean(upper2) < np.mean(upper1) else "diverging",
        }

    with open(OUTPUT_DIR / "convergence_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Convergence: {len(metrics)} wave transitions analyzed")
    return metrics


# ═══════════════════════════════════════════════════════════════════════════
# 3. ZONE TEMPORAL TRENDS
# ═══════════════════════════════════════════════════════════════════════════

def compute_zone_trends(heatmap_f: pd.DataFrame, heatmap_e: pd.DataFrame):
    """Group Fiedler/entropy by cultural zone, compute zone-mean per wave."""
    if heatmap_f.empty:
        return pd.DataFrame()

    rows = []
    for wave in heatmap_f.columns:
        for zone in ZONE_COLORS:
            zone_countries = [c for c in heatmap_f.index
                              if COUNTRY_ZONE.get(c) == zone
                              and pd.notna(heatmap_f.loc[c, wave])]
            if not zone_countries:
                continue
            fiedler_vals = [heatmap_f.loc[c, wave] for c in zone_countries]
            row = {
                "wave": wave,
                "year": WAVE_YEARS.get(wave, 0),
                "zone": zone,
                "n_countries": len(zone_countries),
                "mean_fiedler": float(np.mean(fiedler_vals)),
                "std_fiedler": float(np.std(fiedler_vals)),
            }
            if not heatmap_e.empty and wave in heatmap_e.columns:
                entropy_vals = [heatmap_e.loc[c, wave] for c in zone_countries
                                if c in heatmap_e.index and pd.notna(heatmap_e.loc[c, wave])]
                if entropy_vals:
                    row["mean_entropy"] = float(np.mean(entropy_vals))
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(OUTPUT_DIR / "zone_temporal_trends.csv", index=False)
        print(f"  Zone trends: {len(df)} zone-wave combinations")
        plot_zone_trends(df)
    return df


def plot_zone_trends(df: pd.DataFrame):
    """Plot zone-mean Fiedler values over time."""
    fig, ax = plt.subplots(figsize=(10, 6))
    for zone in df["zone"].unique():
        zdf = df[df["zone"] == zone].sort_values("wave")
        color = ZONE_COLORS.get(zone, "#999999")
        ax.plot(zdf["year"], zdf["mean_fiedler"], "o-",
                color=color, label=zone, linewidth=2, markersize=6)
        ax.fill_between(
            zdf["year"],
            zdf["mean_fiedler"] - zdf["std_fiedler"],
            zdf["mean_fiedler"] + zdf["std_fiedler"],
            alpha=0.15, color=color,
        )
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean Fiedler Value")
    ax.set_title("Algebraic Connectivity by Cultural Zone Over Time")
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "zone_trends.png", dpi=150)
    plt.close()
    print(f"  Saved zone_trends.png")


# ═══════════════════════════════════════════════════════════════════════════
# 4. MULTI-COUNTRY SPECTRAL TRAJECTORIES
# ═══════════════════════════════════════════════════════════════════════════

def plot_spectral_trajectories(heatmap_f: pd.DataFrame):
    """
    Plot Fiedler evolution for countries with 4+ waves.
    Highlights the 5 richest-data countries (BRA, CHL, IND, MEX, NGA).
    """
    if heatmap_f.empty:
        return

    # Countries with 4+ non-NaN waves
    coverage = heatmap_f.notna().sum(axis=1)
    rich_countries = coverage[coverage >= 4].index.tolist()

    if not rich_countries:
        rich_countries = coverage[coverage >= 3].index.tolist()
    if not rich_countries:
        return

    # Highlight specific countries
    highlight = {"MEX", "BRA", "IND", "CHL", "NGA"}
    highlight_present = [c for c in rich_countries if c in highlight]
    others = [c for c in rich_countries if c not in highlight]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Background: other countries in gray
    for c in others:
        vals = heatmap_f.loc[c].dropna()
        years = [WAVE_YEARS.get(w, w) for w in vals.index]
        ax.plot(years, vals.values, "-", color="#cccccc", alpha=0.4, linewidth=1)

    # Foreground: highlighted countries
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12"]
    for i, c in enumerate(highlight_present):
        vals = heatmap_f.loc[c].dropna()
        years = [WAVE_YEARS.get(w, w) for w in vals.index]
        color = colors[i % len(colors)]
        zone = COUNTRY_ZONE.get(c, "Unknown")
        ax.plot(years, vals.values, "o-", color=color,
                label=f"{c} ({zone})", linewidth=2.5, markersize=8)

    ax.set_xlabel("Year")
    ax.set_ylabel("Fiedler Value")
    ax.set_title(f"Spectral Trajectories — {len(rich_countries)} Countries with 4+ Waves")
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "spectral_trajectories.png", dpi=150)
    plt.close()
    print(f"  Saved spectral_trajectories.png ({len(rich_countries)} countries)")


# ═══════════════════════════════════════════════════════════════════════════
# 5. MEDIATOR STABILITY
# ═══════════════════════════════════════════════════════════════════════════

def compute_mediator_stability() -> dict:
    """
    For countries with mediator scores in multiple waves, track whether the
    top mediator construct stays the same or changes.
    """
    mediators_by_country: dict[str, dict[int, str]] = defaultdict(dict)

    per_wave_dir = ALLWAVE_DIR / "per_wave"
    if not per_wave_dir.exists():
        return {}

    for wave_dir in sorted(per_wave_dir.iterdir()):
        if not wave_dir.is_dir():
            continue
        wave_num = int(wave_dir.name[1:])
        med_path = wave_dir / "floyd_warshall" / "mediator_scores.json"
        if not med_path.exists():
            continue
        with open(med_path) as f:
            med_data = json.load(f)

        for country, info in med_data.items():
            if isinstance(info, dict):
                top_med = info.get("top_mediator", info.get("top_construct"))
                if top_med:
                    mediators_by_country[country][wave_num] = top_med

    # Compute stability for countries with 3+ waves
    stability = {}
    for country, wave_meds in mediators_by_country.items():
        if len(wave_meds) < 3:
            continue
        waves_sorted = sorted(wave_meds.keys())
        top_meds = [wave_meds[w] for w in waves_sorted]
        most_common = max(set(top_meds), key=top_meds.count)
        n_same = top_meds.count(most_common)

        stability[country] = {
            "waves": waves_sorted,
            "top_mediators": {str(w): m for w, m in wave_meds.items()},
            "most_common": most_common,
            "stability_rate": n_same / len(top_meds),
            "zone": COUNTRY_ZONE.get(country, "Unknown"),
        }

    with open(OUTPUT_DIR / "mediator_stability.json", "w") as f:
        json.dump(stability, f, indent=2)
    print(f"  Mediator stability: {len(stability)} countries with 3+ waves")
    return stability


# ═══════════════════════════════════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════════════════════════════════

def write_report(
    heatmap_f: pd.DataFrame,
    convergence: dict,
    zone_trends: pd.DataFrame,
    mediator_stability: dict,
):
    """Write a summary markdown report."""
    lines = [
        "# All-Wave TDA Synthesis Report",
        "",
        f"**Source**: {ALLWAVE_DIR}",
        "",
    ]

    # Fiedler summary
    if not heatmap_f.empty:
        coverage = heatmap_f.notna().sum(axis=1)
        lines.append("## 1. Fiedler Evolution")
        lines.append(f"- Countries: {len(heatmap_f)}")
        lines.append(f"- Waves: {list(heatmap_f.columns)}")
        lines.append(f"- Countries with 4+ waves: {(coverage >= 4).sum()}")
        lines.append(f"- Countries with 3+ waves: {(coverage >= 3).sum()}")
        global_mean = heatmap_f.mean()
        for w in heatmap_f.columns:
            lines.append(f"  - W{w} ({WAVE_YEARS.get(w, '?')}): "
                         f"mean Fiedler = {global_mean[w]:.3f}")
        lines.append("")

    # Convergence
    if convergence:
        lines.append("## 2. Convergence / Divergence")
        for label, m in convergence.items():
            lines.append(f"- **{label}** ({m['year_from']}→{m['year_to']}): "
                         f"Δ = {m['delta']:+.4f} ({m['interpretation']}), "
                         f"{m['shared_countries']} shared countries")
        lines.append("")

    # Zone trends
    if not zone_trends.empty:
        lines.append("## 3. Zone Temporal Trends")
        latest_wave = zone_trends["wave"].max()
        latest = zone_trends[zone_trends["wave"] == latest_wave].sort_values(
            "mean_fiedler", ascending=False
        )
        for _, row in latest.iterrows():
            lines.append(f"- {row['zone']}: Fiedler = {row['mean_fiedler']:.3f} "
                         f"(n={row['n_countries']})")
        lines.append("")

    # Mediator stability
    if mediator_stability:
        lines.append("## 4. Mediator Stability")
        sorted_stab = sorted(mediator_stability.items(),
                              key=lambda x: x[1]["stability_rate"], reverse=True)
        lines.append("### Most stable (same top mediator across waves)")
        for country, info in sorted_stab[:10]:
            lines.append(f"- **{country}** ({info['zone']}): "
                         f"{info['most_common']} "
                         f"({info['stability_rate']:.0%} of {len(info['waves'])} waves)")
        if len(sorted_stab) > 10:
            lines.append(f"\n### Least stable")
            for country, info in sorted_stab[-5:]:
                lines.append(f"- **{country}** ({info['zone']}): "
                             f"{info['stability_rate']:.0%} stability")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by tda_allwave_analysis.py*")

    report = "\n".join(lines)
    with open(OUTPUT_DIR / "allwave_tda_report.md", "w") as f:
        f.write(report)
    print(f"  Report: {OUTPUT_DIR / 'allwave_tda_report.md'}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ALL-WAVE TDA SYNTHESIS")
    print("=" * 60)

    # 1. Feature heatmaps
    print("\n[1/5] Building feature heatmaps...")
    heatmap_f, heatmap_e = build_feature_heatmaps()
    if not heatmap_f.empty:
        plot_fiedler_heatmap(heatmap_f.copy())

    # 2. Convergence
    print("\n[2/5] Computing convergence/divergence...")
    convergence = compute_convergence()

    # 3. Zone trends
    print("\n[3/5] Computing zone temporal trends...")
    zone_trends = compute_zone_trends(heatmap_f, heatmap_e)

    # 4. Spectral trajectories
    print("\n[4/5] Plotting spectral trajectories...")
    plot_spectral_trajectories(heatmap_f)

    # 5. Mediator stability
    print("\n[5/5] Computing mediator stability...")
    mediator_stability = compute_mediator_stability()

    # Report
    print("\nWriting report...")
    write_report(heatmap_f, convergence, zone_trends, mediator_stability)

    print(f"\n{'═' * 60}")
    print(f"Output: {OUTPUT_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
