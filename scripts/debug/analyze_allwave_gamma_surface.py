"""
All-Wave γ-Surface Descriptive Analysis
========================================

Analyzes the unified γ-surface (123K estimates across 7 waves × 225 contexts)
to answer: what constructs retain SES-mediated power, where, and when?

6 Sections:
  1. Coverage map (waves × countries heatmap)
  2. Construct power retention (which pairs are universally significant?)
  3. Geographic persistence (country/zone stability across waves)
  4. Temporal dynamics (global trends, convergence/divergence)
  5. Construct personas (top-20 pair profiles)
  6. Key findings auto-summary

Input:
  data/results/wvs_all_wave_gamma_surface.json

Output:
  data/results/allwave_descriptive_report.md
  data/results/allwave_construct_power.csv
  data/results/allwave_country_trajectories.csv
  data/results/allwave_temporal_trends.csv
  data/results/allwave_coverage_heatmap.png
  data/results/allwave_construct_profiles/*.png

Run:
  python scripts/debug/analyze_allwave_gamma_surface.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

SURFACE_PATH = ROOT / "data" / "results" / "wvs_all_wave_gamma_surface.json"
OUTPUT_DIR   = ROOT / "data" / "results"
PROFILE_DIR  = OUTPUT_DIR / "allwave_construct_profiles"
REPORT_PATH  = OUTPUT_DIR / "allwave_descriptive_report.md"

WAVE_YEARS = {1: 1981, 2: 1990, 3: 1996, 4: 2000, 5: 2007, 6: 2012, 7: 2018}

ZONE_COLORS = {
    "Latin America": "#e74c3c", "English-speaking": "#3498db",
    "Protestant Europe": "#2ecc71", "Catholic Europe": "#9b59b6",
    "Orthodox/ex-Communist": "#f39c12", "Confucian": "#1abc9c",
    "South/Southeast Asian": "#e67e22", "African-Islamic": "#95a5a6",
    "Unknown": "#bdc3c7",
}


# ── Key parsing (reused from analyze_wvs_geographic.py) ──────────────────────

def parse_key(full_key: str) -> tuple[str, str, str]:
    """Parse 'WVS_W7_MEX::va::vb' → (context, va, vb)."""
    parts = full_key.split("::")
    return parts[0], parts[1], parts[2]


def context_to_country_wave(ctx: str) -> tuple[str, int]:
    """'WVS_W7_MEX' → ('MEX', 7)."""
    parts = ctx.split("_")
    return parts[2], int(parts[1][1:])


def pair_id(va: str, vb: str) -> str:
    return "::".join(sorted([va, vb]))


def short_name(name: str) -> str:
    n = name.split("|")[0]
    for prefix in ("wvs_agg_", "agg_"):
        if n.startswith(prefix):
            n = n[len(prefix):]
    return n


# ── Load data ────────────────────────────────────────────────────────────────

def load_surface():
    print("Loading γ-surface...")
    with open(SURFACE_PATH) as f:
        data = json.load(f)
    estimates = data.get("estimates", {})
    print(f"  {len(estimates):,} estimates")
    return estimates


def organize(estimates: dict) -> tuple[dict, dict, dict, dict]:
    """Organize estimates into by_pair, by_country, by_wave, by_context dicts."""
    by_pair = defaultdict(list)       # pair_id → [{gamma, country, wave, excl_zero, ...}]
    by_country = defaultdict(list)    # alpha3 → [estimates]
    by_wave = defaultdict(list)       # wave_int → [estimates]
    by_context = defaultdict(dict)    # (country, wave) → {pair_id: gamma}

    for key, est in estimates.items():
        gamma = est.get("dr_gamma")
        if gamma is None:
            continue
        ctx, va, vb = parse_key(key)
        country, wave = context_to_country_wave(ctx)
        pid = pair_id(va, vb)
        excl = est.get("excl_zero", False)

        record = {
            "gamma": gamma, "country": country, "wave": wave,
            "excl_zero": excl, "ci_width": est.get("ci_width", 0),
            "pair": pid, "va": va, "vb": vb,
        }
        by_pair[pid].append(record)
        by_country[country].append(record)
        by_wave[wave].append(record)
        by_context[(country, wave)][pid] = gamma

    return dict(by_pair), dict(by_country), dict(by_wave), dict(by_context)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Coverage Map
# ══════════════════════════════════════════════════════════════════════════════

def section_1_coverage(by_wave, by_country, report_lines):
    print("\n[1/6] Coverage map...")
    report_lines.append("## 1. Coverage Map\n")

    # Wave × country matrix
    countries = sorted(by_country.keys())
    waves = sorted(by_wave.keys())

    # Build coverage matrix: n_pairs per (wave, country)
    coverage = np.zeros((len(waves), len(countries)))
    sig_rate = np.zeros((len(waves), len(countries)))

    for wi, w in enumerate(waves):
        country_pairs = defaultdict(int)
        country_sig = defaultdict(int)
        for r in by_wave[w]:
            country_pairs[r["country"]] += 1
            if r["excl_zero"]:
                country_sig[r["country"]] += 1
        for ci, c in enumerate(countries):
            n = country_pairs.get(c, 0)
            coverage[wi, ci] = n
            sig_rate[wi, ci] = country_sig.get(c, 0) / max(n, 1) if n > 0 else np.nan

    # Heatmap
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(20, len(countries) * 0.35), 8))

    im1 = ax1.imshow(coverage, aspect="auto", cmap="YlOrRd", interpolation="nearest")
    ax1.set_yticks(range(len(waves)))
    ax1.set_yticklabels([f"W{w} ({WAVE_YEARS.get(w, '')})" for w in waves])
    ax1.set_xticks(range(len(countries)))
    ax1.set_xticklabels(countries, rotation=90, fontsize=6)
    ax1.set_title("Pairs estimated per wave × country", fontsize=12)
    plt.colorbar(im1, ax=ax1, label="n pairs")

    im2 = ax2.imshow(sig_rate, aspect="auto", cmap="RdYlGn", vmin=0, vmax=0.7,
                     interpolation="nearest")
    ax2.set_yticks(range(len(waves)))
    ax2.set_yticklabels([f"W{w}" for w in waves])
    ax2.set_xticks(range(len(countries)))
    ax2.set_xticklabels(countries, rotation=90, fontsize=6)
    ax2.set_title("% significant per wave × country", fontsize=12)
    plt.colorbar(im2, ax=ax2, label="sig %")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "allwave_coverage_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Report table
    report_lines.append("| Wave | Year | Countries | Pairs | Sig | %Sig |")
    report_lines.append("|------|------|-----------|-------|-----|------|")
    for w in waves:
        recs = by_wave[w]
        n_countries = len(set(r["country"] for r in recs))
        n_sig = sum(1 for r in recs if r["excl_zero"])
        pct = 100 * n_sig / max(len(recs), 1)
        report_lines.append(
            f"| W{w} | {WAVE_YEARS.get(w, '')} | {n_countries} | {len(recs):,} | {n_sig:,} | {pct:.1f}% |"
        )
    report_lines.append("")
    print(f"  {len(waves)} waves, {len(countries)} countries")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Construct Power Retention
# ══════════════════════════════════════════════════════════════════════════════

def section_2_power(by_pair, report_lines) -> pd.DataFrame:
    print("\n[2/6] Construct power retention...")
    report_lines.append("## 2. Construct Power Retention\n")

    rows = []
    for pid, records in by_pair.items():
        n_measured = len(records)
        n_sig = sum(1 for r in records if r["excl_zero"])
        gammas = [r["gamma"] for r in records]
        signs = [np.sign(g) for g in gammas if g != 0]
        waves_present = sorted(set(r["wave"] for r in records))
        countries_present = sorted(set(r["country"] for r in records))

        # Majority sign
        if signs:
            majority = 1 if sum(1 for s in signs if s > 0) > len(signs) / 2 else -1
            sign_consist = sum(1 for s in signs if s == majority) / len(signs)
        else:
            majority = 0
            sign_consist = 0

        rows.append({
            "pair": pid,
            "construct_a": short_name(pid.split("::")[0]),
            "construct_b": short_name(pid.split("::")[1]),
            "n_contexts_measured": n_measured,
            "n_contexts_significant": n_sig,
            "retention_rate": round(n_sig / max(n_measured, 1), 3),
            "mean_abs_gamma": round(np.mean(np.abs(gammas)), 4),
            "median_abs_gamma": round(np.median(np.abs(gammas)), 4),
            "sign_consistency": round(sign_consist, 3),
            "majority_sign": int(majority),
            "n_countries": len(countries_present),
            "n_waves": len(waves_present),
            "first_wave": min(waves_present),
            "last_wave": max(waves_present),
        })

    df = pd.DataFrame(rows).sort_values("retention_rate", ascending=False)
    df.to_csv(OUTPUT_DIR / "allwave_construct_power.csv", index=False)

    # Report: top 20
    report_lines.append(f"**{len(df)} unique pairs scored.** Top 20 by retention rate:\n")
    report_lines.append("| Rank | Construct A | Construct B | Retention | Mean|γ| | Sign% | Countries | Waves |")
    report_lines.append("|------|------------|------------|-----------|---------|-------|-----------|-------|")
    for i, (_, r) in enumerate(df.head(20).iterrows()):
        report_lines.append(
            f"| {i+1} | {r['construct_a'][:30]} | {r['construct_b'][:30]} | "
            f"{r['retention_rate']:.0%} | {r['mean_abs_gamma']:.3f} | "
            f"{r['sign_consistency']:.0%} | {r['n_countries']} | {r['n_waves']} |"
        )

    # Summary stats
    high_retention = df[df["retention_rate"] >= 0.5]
    report_lines.append(f"\n- Pairs with ≥50% retention: **{len(high_retention)}**")
    report_lines.append(f"- Pairs measured in 5+ waves: **{len(df[df['n_waves'] >= 5])}**")
    report_lines.append(f"- Median retention rate: **{df['retention_rate'].median():.1%}**")
    report_lines.append(f"- Mean sign consistency: **{df['sign_consistency'].mean():.1%}**\n")

    print(f"  {len(high_retention)} pairs with ≥50% retention")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Geographic Persistence
# ══════════════════════════════════════════════════════════════════════════════

def section_3_geographic(by_country, by_context, report_lines) -> pd.DataFrame:
    print("\n[3/6] Geographic persistence...")
    report_lines.append("## 3. Geographic Persistence\n")

    rows = []
    for country in sorted(by_country.keys()):
        recs = by_country[country]
        waves_present = sorted(set(r["wave"] for r in recs))
        zone = COUNTRY_ZONE.get(country, "Unknown")

        gammas_all = [r["gamma"] for r in recs]
        n_sig = sum(1 for r in recs if r["excl_zero"])

        # Per-wave stats
        per_wave = {}
        for w in waves_present:
            w_recs = [r for r in recs if r["wave"] == w]
            w_gammas = [r["gamma"] for r in w_recs]
            per_wave[w] = {
                "n_pairs": len(w_recs),
                "n_sig": sum(1 for r in w_recs if r["excl_zero"]),
                "median_abs_gamma": float(np.median(np.abs(w_gammas))),
            }

        # Cross-wave stability (Spearman ρ between adjacent waves)
        rho_values = []
        for i in range(len(waves_present) - 1):
            w1, w2 = waves_present[i], waves_present[i + 1]
            ctx1 = by_context.get((country, w1), {})
            ctx2 = by_context.get((country, w2), {})
            shared = set(ctx1.keys()) & set(ctx2.keys())
            if len(shared) >= 10:
                g1 = [ctx1[p] for p in shared]
                g2 = [ctx2[p] for p in shared]
                rho, _ = spearmanr(g1, g2)
                rho_values.append(rho)

        rows.append({
            "country": country,
            "zone": zone,
            "n_waves": len(waves_present),
            "waves": ",".join(str(w) for w in waves_present),
            "n_total_estimates": len(recs),
            "n_significant": n_sig,
            "pct_significant": round(100 * n_sig / max(len(recs), 1), 1),
            "median_abs_gamma": round(np.median(np.abs(gammas_all)), 4),
            "mean_stability_rho": round(np.mean(rho_values), 3) if rho_values else np.nan,
        })

    df = pd.DataFrame(rows).sort_values("mean_stability_rho", ascending=False)
    df.to_csv(OUTPUT_DIR / "allwave_country_trajectories.csv", index=False)

    # Report: zone summary
    zone_df = df.groupby("zone").agg({
        "n_waves": "mean",
        "pct_significant": "mean",
        "median_abs_gamma": "mean",
        "mean_stability_rho": "mean",
        "country": "count",
    }).rename(columns={"country": "n_countries"}).round(3)

    report_lines.append("### Zone summary\n")
    report_lines.append("| Zone | Countries | Avg waves | Avg %sig | Avg med|γ| | Avg stability ρ |")
    report_lines.append("|------|-----------|-----------|----------|-----------|----------------|")
    for zone, r in zone_df.sort_values("median_abs_gamma", ascending=False).iterrows():
        report_lines.append(
            f"| {zone} | {r['n_countries']:.0f} | {r['n_waves']:.1f} | "
            f"{r['pct_significant']:.1f}% | {r['median_abs_gamma']:.4f} | "
            f"{r['mean_stability_rho']:.3f} |"
        )

    # Most/least stable countries
    stable = df.dropna(subset=["mean_stability_rho"])
    if len(stable) > 0:
        report_lines.append(f"\n### Most structurally stable countries (cross-wave Spearman ρ)\n")
        for _, r in stable.head(10).iterrows():
            report_lines.append(f"- **{r['country']}** ({r['zone']}): ρ={r['mean_stability_rho']:.3f}, {r['n_waves']} waves")
        report_lines.append(f"\n### Least stable\n")
        for _, r in stable.tail(5).iterrows():
            report_lines.append(f"- **{r['country']}** ({r['zone']}): ρ={r['mean_stability_rho']:.3f}, {r['n_waves']} waves")
    report_lines.append("")

    print(f"  {len(df)} countries, {len(zone_df)} zones")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Temporal Dynamics
# ══════════════════════════════════════════════════════════════════════════════

def section_4_temporal(by_pair, report_lines) -> pd.DataFrame:
    print("\n[4/6] Temporal dynamics...")
    report_lines.append("## 4. Temporal Dynamics (Global Trends)\n")

    rows = []
    for pid, records in by_pair.items():
        # Need 3+ waves of data across ANY country
        waves_with_data = sorted(set(r["wave"] for r in records))
        if len(waves_with_data) < 3:
            continue

        # Aggregate: mean γ per wave (across all countries in that wave)
        wave_means = {}
        wave_sigs = {}
        for w in waves_with_data:
            w_recs = [r for r in records if r["wave"] == w]
            wave_means[w] = np.mean([r["gamma"] for r in w_recs])
            wave_sigs[w] = np.mean([r["excl_zero"] for r in w_recs])

        # Trend: weighted linear regression mean_γ ~ year
        years = np.array([WAVE_YEARS.get(w, w * 5 + 1975) for w in waves_with_data])
        means = np.array([wave_means[w] for w in waves_with_data])
        abs_means = np.abs(means)

        if np.std(years) > 0 and len(years) >= 3:
            coeffs = np.polyfit(years, abs_means, 1)
            slope = coeffs[0] * 10  # per decade
            predicted = np.polyval(coeffs, years)
            ss_res = np.sum((abs_means - predicted) ** 2)
            ss_tot = np.sum((abs_means - np.mean(abs_means)) ** 2)
            r2 = 1 - ss_res / max(ss_tot, 1e-12)

            # Sign trend (on signed γ)
            sign_coeffs = np.polyfit(years, means, 1)
            sign_slope = sign_coeffs[0] * 10
        else:
            slope, r2, sign_slope = 0, 0, 0

        # Sign stability across all observations
        signs = [np.sign(r["gamma"]) for r in records if r["gamma"] != 0]
        if signs:
            majority = 1 if sum(1 for s in signs if s > 0) > len(signs) / 2 else -1
            sign_stable = sum(1 for s in signs if s == majority) / len(signs) > 0.8
        else:
            sign_stable = True

        rows.append({
            "pair": pid,
            "construct_a": short_name(pid.split("::")[0]),
            "construct_b": short_name(pid.split("::")[1]),
            "n_waves": len(waves_with_data),
            "n_observations": len(records),
            "magnitude_slope_per_decade": round(slope, 5),
            "signed_slope_per_decade": round(sign_slope, 5),
            "trend_r2": round(r2, 3),
            "sign_stable": sign_stable,
            "mean_abs_gamma_earliest": round(abs_means[0], 4),
            "mean_abs_gamma_latest": round(abs_means[-1], 4),
            "change": round(abs_means[-1] - abs_means[0], 4),
        })

    df = pd.DataFrame(rows)
    if len(df) == 0:
        report_lines.append("Insufficient multi-wave data for trend analysis.\n")
        return df

    df = df.sort_values("magnitude_slope_per_decade", ascending=False)
    df.to_csv(OUTPUT_DIR / "allwave_temporal_trends.csv", index=False)

    # Global trend
    global_strengthening = df[df["magnitude_slope_per_decade"] > 0.001]
    global_weakening = df[df["magnitude_slope_per_decade"] < -0.001]
    mean_slope = df["magnitude_slope_per_decade"].mean()
    direction = "strengthening" if mean_slope > 0 else "weakening" if mean_slope < 0 else "stable"

    report_lines.append(f"**{len(df)} pairs** tracked across 3+ waves.\n")
    report_lines.append(f"- Global trend: SES stratification is **{direction}** "
                        f"(mean |γ| slope: {mean_slope:+.4f}/decade)")
    report_lines.append(f"- Strengthening pairs: {len(global_strengthening)}")
    report_lines.append(f"- Weakening pairs: {len(global_weakening)}")

    # Top strengthening
    report_lines.append(f"\n### Top 10 strengthening (|γ| increasing)\n")
    report_lines.append("| Construct A | Construct B | Slope/dec | R² | Waves |")
    report_lines.append("|------------|------------|----------|-----|-------|")
    for _, r in df.head(10).iterrows():
        report_lines.append(
            f"| {r['construct_a'][:28]} | {r['construct_b'][:28]} | "
            f"+{r['magnitude_slope_per_decade']:.4f} | {r['trend_r2']:.2f} | {r['n_waves']} |"
        )

    # Top weakening
    report_lines.append(f"\n### Top 10 weakening (|γ| decreasing)\n")
    report_lines.append("| Construct A | Construct B | Slope/dec | R² | Waves |")
    report_lines.append("|------------|------------|----------|-----|-------|")
    for _, r in df.tail(10).iterrows():
        report_lines.append(
            f"| {r['construct_a'][:28]} | {r['construct_b'][:28]} | "
            f"{r['magnitude_slope_per_decade']:.4f} | {r['trend_r2']:.2f} | {r['n_waves']} |"
        )
    report_lines.append("")

    print(f"  {len(df)} pairs with trends, mean slope {mean_slope:+.5f}/decade")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Construct Personas (top-20 profiles)
# ══════════════════════════════════════════════════════════════════════════════

def section_5_profiles(by_pair, power_df, report_lines):
    print("\n[5/6] Construct profiles (top 20)...")
    report_lines.append("## 5. Construct Profiles (Top 20)\n")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    top20 = power_df.head(20)

    for rank, (_, row) in enumerate(top20.iterrows()):
        pid = row["pair"]
        records = by_pair[pid]
        ca = row["construct_a"][:35]
        cb = row["construct_b"][:35]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

        # ── Panel 1: Geographic (bar by country, SORTED by gamma) ────────
        country_gamma = defaultdict(list)
        for r in records:
            country_gamma[r["country"]].append(r["gamma"])

        # Sort countries by mean gamma (descending) for visual clarity
        country_mean = {c: np.mean(gs) for c, gs in country_gamma.items()}
        countries_sorted = sorted(country_mean.keys(), key=lambda c: country_mean[c], reverse=True)
        mean_gammas = [country_mean[c] for c in countries_sorted]
        colors = [ZONE_COLORS.get(COUNTRY_ZONE.get(c, "Unknown"), "#bdc3c7")
                  for c in countries_sorted]

        ax1.bar(range(len(countries_sorted)), mean_gammas, color=colors, alpha=0.8)
        ax1.set_xticks(range(len(countries_sorted)))
        ax1.set_xticklabels(countries_sorted, rotation=90, fontsize=5)
        ax1.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax1.set_ylabel("Mean γ")
        ax1.set_title(f"Geographic: mean γ per country (sorted)")

        # ── Panel 2: Temporal (line per country, bold zone average) ───────
        wave_country = defaultdict(lambda: defaultdict(list))
        for r in records:
            wave_country[r["wave"]][r["country"]].append(r["gamma"])

        waves_present = sorted(wave_country.keys())
        years = [WAVE_YEARS.get(w, w) for w in waves_present]

        # Per-country lines — visible with zone coloring
        all_countries = set()
        for w in waves_present:
            all_countries.update(wave_country[w].keys())

        # Scale alpha by number of countries: fewer countries → more opaque
        n_c = len(all_countries)
        line_alpha = max(0.6, min(0.8, 8.0 / max(n_c, 1)))
        line_width = max(0.8, min(2.0, 5.0 / max(n_c, 1)))

        for c in all_countries:
            c_years = []
            c_gammas = []
            for w in waves_present:
                if c in wave_country[w]:
                    c_years.append(WAVE_YEARS.get(w, w))
                    c_gammas.append(np.mean(wave_country[w][c]))
            if len(c_years) >= 2:
                zone = COUNTRY_ZONE.get(c, "Unknown")
                ax2.plot(c_years, c_gammas,
                         color=ZONE_COLORS.get(zone, "#bdc3c7"),
                         alpha=line_alpha, linewidth=line_width,
                         marker="o", markersize=2)
            elif len(c_years) == 1:
                # Single-wave: show as dot
                zone = COUNTRY_ZONE.get(c, "Unknown")
                ax2.scatter(c_years, c_gammas,
                            color=ZONE_COLORS.get(zone, "#bdc3c7"),
                            alpha=line_alpha, s=15, zorder=5)

        # Global average bold line
        global_means = [np.mean([np.mean(v) for v in wave_country[w].values()])
                        for w in waves_present]
        ax2.plot(years, global_means, color="black", linewidth=2.5,
                 marker="s", markersize=5, label="Global mean", zorder=10)
        ax2.axhline(0, color="gray", linewidth=0.5, linestyle="--")
        ax2.set_xlabel("Year")
        ax2.set_ylabel("γ")
        ax2.set_title(f"Temporal: γ trajectory ({n_c} countries)")
        ax2.legend(fontsize=8)

        fig.suptitle(f"#{rank+1}: {ca} × {cb}\n"
                     f"Retention={row['retention_rate']:.0%}  |γ|={row['mean_abs_gamma']:.3f}  "
                     f"Sign={row['sign_consistency']:.0%}  Countries={row['n_countries']}  Waves={row['n_waves']}",
                     fontsize=11, fontweight="bold")

        plt.tight_layout()
        safe_name = f"{rank+1:02d}_{ca[:20]}_{cb[:20]}".replace("/", "_").replace(" ", "_")
        plt.savefig(PROFILE_DIR / f"{safe_name}.png", dpi=120, bbox_inches="tight")
        plt.close()

        report_lines.append(f"### #{rank+1}: {ca} × {cb}")
        report_lines.append(f"- Retention: {row['retention_rate']:.0%} ({row['n_contexts_significant']}/{row['n_contexts_measured']})")
        report_lines.append(f"- Mean |γ|: {row['mean_abs_gamma']:.3f}, sign consistency: {row['sign_consistency']:.0%}")
        report_lines.append(f"- Span: W{row['first_wave']}–W{row['last_wave']} across {row['n_countries']} countries")
        report_lines.append(f"- Profile: `allwave_construct_profiles/{safe_name}.png`\n")

    print(f"  {len(top20)} profiles saved")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: Key Findings Summary
# ══════════════════════════════════════════════════════════════════════════════

def section_6_summary(power_df, country_df, trends_df, report_lines):
    print("\n[6/6] Key findings summary...")
    report_lines.append("## 6. Key Findings\n")

    # Universal bridges
    universal = power_df[power_df["retention_rate"] >= 0.6]
    if len(universal) > 0:
        names = [f"{r['construct_a'][:25]} × {r['construct_b'][:25]}"
                 for _, r in universal.head(5).iterrows()]
        report_lines.append(f"**Most universal SES bridges** (≥60% retention): {len(universal)} pairs")
        for n in names:
            report_lines.append(f"  - {n}")
    else:
        report_lines.append("**No pairs reach 60% retention** — SES bridges are context-dependent.")

    # Global trend
    if len(trends_df) > 0:
        mean_slope = trends_df["magnitude_slope_per_decade"].mean()
        direction = "strengthening" if mean_slope > 0.001 else "weakening" if mean_slope < -0.001 else "stable"
        report_lines.append(f"\n**Global SES stratification trend**: {direction} "
                            f"({mean_slope:+.4f} |γ|/decade)")

    # Most stable countries
    stable = country_df.dropna(subset=["mean_stability_rho"])
    if len(stable) > 0:
        top3 = stable.head(3)
        bot3 = stable.tail(3)
        report_lines.append(f"\n**Most structurally stable**: "
                            + ", ".join(f"{r['country']} (ρ={r['mean_stability_rho']:.2f})"
                                        for _, r in top3.iterrows()))
        report_lines.append(f"**Most volatile**: "
                            + ", ".join(f"{r['country']} (ρ={r['mean_stability_rho']:.2f})"
                                        for _, r in bot3.iterrows()))

    # Zone uniqueness
    zone_sig = country_df.groupby("zone")["pct_significant"].mean()
    if len(zone_sig) > 0:
        top_zone = zone_sig.idxmax()
        bot_zone = zone_sig.idxmin()
        report_lines.append(f"\n**Highest SES stratification zone**: {top_zone} ({zone_sig[top_zone]:.1f}% sig)")
        report_lines.append(f"**Lowest SES stratification zone**: {bot_zone} ({zone_sig[bot_zone]:.1f}% sig)")

    # Power gained/lost
    if len(trends_df) > 0:
        gained = trends_df.nlargest(3, "magnitude_slope_per_decade")
        lost = trends_df.nsmallest(3, "magnitude_slope_per_decade")
        report_lines.append(f"\n**Pairs gaining SES power**:")
        for _, r in gained.iterrows():
            report_lines.append(f"  - {r['construct_a'][:25]} × {r['construct_b'][:25]}: "
                                f"+{r['magnitude_slope_per_decade']:.4f}/dec")
        report_lines.append(f"**Pairs losing SES power**:")
        for _, r in lost.iterrows():
            report_lines.append(f"  - {r['construct_a'][:25]} × {r['construct_b'][:25]}: "
                                f"{r['magnitude_slope_per_decade']:.4f}/dec")

    report_lines.append("\n---\n*Generated by analyze_allwave_gamma_surface.py*\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("ALL-WAVE γ-SURFACE DESCRIPTIVE ANALYSIS")
    print("=" * 60)

    estimates = load_surface()
    by_pair, by_country, by_wave, by_context = organize(estimates)
    print(f"  {len(by_pair)} pairs, {len(by_country)} countries, {len(by_wave)} waves")

    report = [
        "# All-Wave γ-Surface Descriptive Analysis\n",
        f"**{len(estimates):,} estimates** across {len(by_country)} countries, "
        f"{len(by_wave)} waves (W{'–W'.join(str(w) for w in sorted(by_wave))}), "
        f"{len(by_pair)} unique pairs.\n",
    ]

    section_1_coverage(by_wave, by_country, report)
    power_df = section_2_power(by_pair, report)
    country_df = section_3_geographic(by_country, by_context, report)
    trends_df = section_4_temporal(by_pair, report)
    section_5_profiles(by_pair, power_df, report)
    section_6_summary(power_df, country_df, trends_df, report)

    # Write report
    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(report))
    print(f"\n{'─' * 60}")
    print(f"  Report: {REPORT_PATH}")
    print(f"  Power:  {OUTPUT_DIR / 'allwave_construct_power.csv'}")
    print(f"  Countries: {OUTPUT_DIR / 'allwave_country_trajectories.csv'}")
    print(f"  Trends: {OUTPUT_DIR / 'allwave_temporal_trends.csv'}")
    print(f"  Heatmap: {OUTPUT_DIR / 'allwave_coverage_heatmap.png'}")
    print(f"  Profiles: {PROFILE_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
