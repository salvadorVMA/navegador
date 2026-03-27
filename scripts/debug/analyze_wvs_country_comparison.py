"""
WVS Country Comparison — Distance from Global Average

For each country, builds a γ-vector (one γ per construct pair), then measures
distance from the global median vector. Produces:
  1. Country ranking by distance from average
  2. Multi-country small-multiples circle plot (top closest + most distant)
  3. Mexico's position relative to all countries

Outputs:
  data/results/wvs_country_distance_from_average.png  (bar chart)
  data/results/wvs_multicountry_circle_plots.png      (small multiples)
  data/results/wvs_country_comparison_report.md

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_wvs_country_comparison.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import Wedge
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

RESULTS = ROOT / "data" / "results"

WVS_DOMAIN_LABELS = {
    "WVS_A": "Social\nValues", "WVS_B": "Environ.", "WVS_C": "Work",
    "WVS_D": "Family", "WVS_E": "Politics", "WVS_F": "Religion",
    "WVS_G": "Nat.\nIdentity", "WVS_H": "Security", "WVS_I": "Sci &\nTech",
}

_CMAP24 = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#d37295", "#8cd17d", "#b6992d", "#499894", "#86bcb6",
    "#f1ce63", "#a0cbe8", "#ffbe7d", "#86bcb6", "#e49444",
]

ZONE_COLORS = {
    "Latin America": "#e15759", "English-speaking": "#4e79a7",
    "Protestant Europe": "#76b7b2", "Catholic Europe": "#b07aa1",
    "Orthodox/ex-Communist": "#9c755f", "Confucian": "#edc948",
    "South/Southeast Asian": "#59a14f", "African-Islamic": "#f28e2b",
}


# ─── Load data ───────────────────────────────────────────────────────────────

def load_wvs_geographic(path: Path) -> dict:
    with open(path) as f:
        raw = json.load(f)
    estimates = raw.get("estimates", {})
    out = {}
    for key, v in estimates.items():
        if "dr_gamma" not in v:
            continue
        parts = key.split("::")
        if len(parts) != 3:
            continue
        context = parts[0]
        country = context.split("_")[-1]

        def to_ca(part):
            if "|" not in part:
                return part
            name, domain = part.rsplit("|", 1)
            name = name.removeprefix("wvs_agg_")
            return f"{domain}|{name}"

        pair_key = f"{to_ca(parts[1])}::{to_ca(parts[2])}"
        entry = dict(v)
        entry["construct_a"] = to_ca(parts[1])
        entry["construct_b"] = to_ca(parts[2])
        entry["country"] = country
        entry["zone"] = COUNTRY_ZONE.get(country, "Unknown")
        entry["pair_key"] = pair_key
        out[key] = entry
    return out


# ─── Build country γ-vectors ─────────────────────────────────────────────────

def build_gamma_vectors(all_estimates: dict) -> tuple[dict, list, np.ndarray]:
    """
    Build a matrix of γ values: rows = countries, columns = construct pairs.

    Returns:
        country_list: ordered list of country codes
        pair_list: ordered list of pair keys
        gamma_matrix: (n_countries × n_pairs) matrix, NaN where pair not estimated
    """
    # Collect all pairs and countries
    by_country_pair = defaultdict(dict)
    all_pairs = set()
    all_countries = set()

    for v in all_estimates.values():
        country = v["country"]
        pair = v["pair_key"]
        by_country_pair[country][pair] = v["dr_gamma"]
        all_pairs.add(pair)
        all_countries.add(country)

    pair_list = sorted(all_pairs)
    country_list = sorted(all_countries)
    pair_idx = {p: i for i, p in enumerate(pair_list)}

    # Build matrix
    n_c = len(country_list)
    n_p = len(pair_list)
    mat = np.full((n_c, n_p), np.nan)
    for ci, country in enumerate(country_list):
        for pair, gamma in by_country_pair[country].items():
            mat[ci, pair_idx[pair]] = gamma

    return country_list, pair_list, mat


def compute_distances(country_list, gamma_matrix):
    """
    Compute each country's distance from the global median γ-vector.

    Uses cosine distance on the γ-vector (treating each pair's γ as a
    coordinate). NaN pairs are excluded pairwise.

    Also computes Euclidean distance on the non-NaN subset.
    """
    # Global median: column-wise median ignoring NaN
    median_vec = np.nanmedian(gamma_matrix, axis=0)

    results = {}
    for ci, country in enumerate(country_list):
        vec = gamma_matrix[ci]
        # Mask where both country and median are non-NaN
        valid = ~np.isnan(vec) & ~np.isnan(median_vec)
        n_valid = valid.sum()
        if n_valid < 10:
            continue

        v = vec[valid]
        m = median_vec[valid]

        # Cosine similarity
        dot = np.dot(v, m)
        norm_v = np.linalg.norm(v)
        norm_m = np.linalg.norm(m)
        cos_sim = dot / (norm_v * norm_m) if norm_v > 0 and norm_m > 0 else 0
        cos_dist = 1 - cos_sim

        # Euclidean distance (normalized by sqrt(n))
        euc = np.sqrt(np.mean((v - m) ** 2))  # RMSE

        # Spearman rank correlation
        from scipy.stats import spearmanr
        rho, _ = spearmanr(v, m)

        results[country] = {
            "cos_sim": cos_sim,
            "cos_dist": cos_dist,
            "rmse": euc,
            "spearman_rho": rho,
            "n_pairs": n_valid,
            "zone": COUNTRY_ZONE.get(country, "Unknown"),
        }

    return results, median_vec


# ─── Circle plot helpers ─────────────────────────────────────────────────────

def domain_angles(domains):
    n = len(domains)
    step = 2 * np.pi / n
    return {d: np.pi / 2 - i * step for i, d in enumerate(sorted(domains))}

def layout_nodes(constructs, dam, n_dom, node_radius=3.4, spread_frac=0.68):
    sector = 2 * np.pi / n_dom
    half = sector * spread_frac / 2
    by_domain = defaultdict(list)
    for c in constructs:
        by_domain[c.split("|")[0]].append(c)
    pos = {}
    for dom, members in by_domain.items():
        center = dam[dom]
        n = len(members)
        angles = [center] if n == 1 else np.linspace(center - half, center + half, n)
        for angle, c in zip(angles, sorted(members)):
            pos[c] = (node_radius * np.cos(angle), node_radius * np.sin(angle))
    return pos


def plot_mini_circle(ax, sig_estimates, all_constructs, country_label,
                     subtitle="", highlight=False):
    """Draw a small circle network in a single axes panel."""
    constructs = sorted(all_constructs)
    domains = sorted(set(c.split("|")[0] for c in constructs))
    n_dom = len(domains)
    domain_colors = {d: _CMAP24[i % len(_CMAP24)] for i, d in enumerate(domains)}

    dam = domain_angles(domains)
    pos = layout_nodes(constructs, dam, n_dom, node_radius=1.0, spread_frac=0.68)

    ax.set_aspect("equal")
    ax.axis("off")
    lim = 1.6
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    if highlight:
        ax.patch.set_facecolor("#fff8e7")
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("#e6a817")
            spine.set_linewidth(3)

    # Sector backgrounds (thin)
    sector_deg = 360 / n_dom
    half_deg = sector_deg / 2
    for dom in domains:
        angle_deg = np.degrees(dam[dom])
        color = domain_colors.get(dom, "#cccccc")
        ax.add_patch(Wedge((0, 0), 1.25, angle_deg - half_deg, angle_deg + half_deg,
                           width=0.4, facecolor=color, alpha=0.10,
                           edgecolor=color, linewidth=0.2))

    # Edges
    if sig_estimates:
        g_max = max(abs(v["dr_gamma"]) for v in sig_estimates)
        g_min = min(abs(v["dr_gamma"]) for v in sig_estimates)
        g_range = g_max - g_min if g_max > g_min else 1.0
    else:
        g_max = g_min = g_range = 1.0

    for v in sorted(sig_estimates, key=lambda x: abs(x["dr_gamma"])):
        ca, cb = v["construct_a"], v["construct_b"]
        if ca not in pos or cb not in pos:
            continue
        g = v["dr_gamma"]
        color = "#d62728" if g > 0 else "#1f77b4"
        norm_g = (abs(g) - g_min) / g_range
        alpha = 0.10 + 0.50 * norm_g
        lw = 0.2 + 1.5 * norm_g
        ax.annotate("", xy=pos[cb], xytext=pos[ca],
                     arrowprops=dict(arrowstyle="-", color=color, alpha=alpha,
                                     lw=lw, connectionstyle="arc3,rad=0.15"))

    # Nodes
    degree = defaultdict(int)
    for v in sig_estimates:
        degree[v["construct_a"]] += 1
        degree[v["construct_b"]] += 1
    sig_nodes = set(degree.keys())

    for c in constructs:
        x, y = pos[c]
        is_sig = c in sig_nodes
        size = (8 + min(degree.get(c, 0) * 3, 30)) if is_sig else 3
        color = domain_colors[c.split("|")[0]] if is_sig else "#cccccc"
        ax.scatter(x, y, s=size, c=color, zorder=5, edgecolors="white",
                   linewidths=0.2, alpha=0.85 if is_sig else 0.3)

    # Title
    n_sig = len(sig_estimates)
    n_pos = sum(1 for v in sig_estimates if v["dr_gamma"] > 0)
    title_color = "#c44e00" if highlight else "black"
    ax.set_title(f"{country_label}\n{n_sig} edges ({n_pos}+/{n_sig-n_pos}−){subtitle}",
                 fontsize=8, fontweight="bold" if highlight else "normal",
                 color=title_color, pad=4)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    sweep_path = RESULTS / "wvs_geographic_sweep_w7.json"
    print(f"Loading: {sweep_path.name}")
    all_estimates = load_wvs_geographic(sweep_path)
    print(f"Total estimates: {len(all_estimates):,}")

    # Build γ-vectors and compute distances
    country_list, pair_list, gamma_matrix = build_gamma_vectors(all_estimates)
    print(f"Countries: {len(country_list)}  Pairs: {len(pair_list)}")

    distances, median_vec = compute_distances(country_list, gamma_matrix)
    print(f"Distances computed for {len(distances)} countries")

    # Rank by cosine similarity (closest = highest cos_sim)
    ranked = sorted(distances.items(), key=lambda x: -x[1]["spearman_rho"])

    # Find Mexico
    mex_rank = next(i for i, (c, _) in enumerate(ranked) if c == "MEX") + 1
    mex_stats = distances["MEX"]

    print(f"\n{'='*60}")
    print("COUNTRY DISTANCE FROM GLOBAL AVERAGE γ-VECTOR")
    print(f"{'='*60}")
    print(f"Mexico rank: {mex_rank}/{len(ranked)} (Spearman ρ = {mex_stats['spearman_rho']:.3f})")
    print(f"\nTop 10 closest to average:")
    for i, (c, s) in enumerate(ranked[:10], 1):
        flag = " ← MEX" if c == "MEX" else ""
        print(f"  {i:2d}. {c} ({s['zone'][:15]:15s})  ρ={s['spearman_rho']:.3f}  "
              f"cos={s['cos_sim']:.3f}  RMSE={s['rmse']:.4f}{flag}")
    print(f"\nBottom 5 (most distant):")
    for i, (c, s) in enumerate(ranked[-5:], len(ranked)-4):
        print(f"  {i:2d}. {c} ({s['zone'][:15]:15s})  ρ={s['spearman_rho']:.3f}  "
              f"cos={s['cos_sim']:.3f}  RMSE={s['rmse']:.4f}")

    # ── Bar chart: distance from average ─────────────────────────────────
    print(f"\nPlotting distance bar chart...")
    fig, ax = plt.subplots(figsize=(16, 10))
    countries_sorted = [c for c, _ in ranked]
    rhos = [distances[c]["spearman_rho"] for c in countries_sorted]
    colors = [ZONE_COLORS.get(COUNTRY_ZONE.get(c, ""), "#999999") for c in countries_sorted]
    bars = ax.barh(range(len(countries_sorted)), rhos, color=colors, edgecolor="white", linewidth=0.3)

    # Highlight Mexico
    mex_idx = countries_sorted.index("MEX")
    bars[mex_idx].set_edgecolor("#c44e00")
    bars[mex_idx].set_linewidth(2.5)

    ax.set_yticks(range(len(countries_sorted)))
    ax.set_yticklabels(countries_sorted, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Spearman ρ with global median γ-vector", fontsize=11)
    ax.set_title("WVS W7 — Country Distance from Global Average SES-Attitude Structure\n"
                 "Higher ρ = more typical SES-attitude pattern",
                 fontsize=13, fontweight="bold")
    ax.axvline(x=mex_stats["spearman_rho"], color="#c44e00", linestyle="--", alpha=0.6, lw=1)
    ax.text(mex_stats["spearman_rho"] + 0.005, mex_idx, f"MEX (rank {mex_rank})",
            va="center", fontsize=8, color="#c44e00", fontweight="bold")

    # Zone legend
    legend_handles = [mpatches.Patch(facecolor=c, label=z)
                      for z, c in sorted(ZONE_COLORS.items())]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=7, framealpha=0.85)

    fig.tight_layout()
    fig.savefig(RESULTS / "wvs_country_distance_from_average.png",
                dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: wvs_country_distance_from_average.png")

    # ── Multi-country small multiples ────────────────────────────────────
    # Show: top 4 closest + MEX (if not in top 4) + bottom 4 most distant
    print(f"\nPlotting multi-country circle plots...")

    show_countries = []
    for c, _ in ranked[:4]:
        show_countries.append(c)
    if "MEX" not in show_countries:
        show_countries.append("MEX")
    # Add median position marker
    show_countries.append("__MEDIAN__")
    for c, _ in ranked[-4:]:
        show_countries.append(c)

    # Prepare per-country significant estimates
    by_country = defaultdict(list)
    for v in all_estimates.values():
        if v.get("excl_zero"):
            by_country[v["country"]].append(v)

    # Median "country" — use aggregate significant pairs
    pair_gammas = defaultdict(list)
    for v in all_estimates.values():
        pair_gammas[v["pair_key"]].append(v)
    median_sig = []
    for pk, ests in pair_gammas.items():
        med_g = float(np.median([e["dr_gamma"] for e in ests]))
        n_sig = sum(1 for e in ests if e.get("excl_zero"))
        if n_sig > len(ests) * 0.5:
            median_sig.append({
                "construct_a": ests[0]["construct_a"],
                "construct_b": ests[0]["construct_b"],
                "dr_gamma": med_g, "excl_zero": True,
            })

    all_constructs = set()
    for v in all_estimates.values():
        all_constructs.add(v["construct_a"])
        all_constructs.add(v["construct_b"])

    n_panels = len(show_countries)
    n_cols = 5
    n_rows = (n_panels + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 5 * n_rows))
    axes_flat = axes.flatten() if n_rows > 1 else (axes if n_cols > 1 else [axes])

    for idx, country in enumerate(show_countries):
        ax = axes_flat[idx]
        if country == "__MEDIAN__":
            plot_mini_circle(ax, median_sig, all_constructs,
                             "MEDIAN", subtitle="\n(>50% countries sig)")
        elif country == "MEX":
            plot_mini_circle(ax, by_country[country], all_constructs,
                             f"MEX (rank {mex_rank})",
                             subtitle=f"\nρ={mex_stats['spearman_rho']:.3f}",
                             highlight=True)
        else:
            rank = next(i for i, (c, _) in enumerate(ranked) if c == country) + 1
            d = distances[country]
            plot_mini_circle(ax, by_country[country], all_constructs,
                             f"{country} (rank {rank})",
                             subtitle=f"\nρ={d['spearman_rho']:.3f}")

    # Hide unused axes
    for idx in range(len(show_countries), len(axes_flat)):
        axes_flat[idx].axis("off")

    fig.suptitle("WVS W7 — SES Bridge Networks: Closest to Average → Most Distant\n"
                 "Red edges = γ>0, Blue = γ<0  |  Mexico highlighted",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(RESULTS / "wvs_multicountry_circle_plots.png",
                dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: wvs_multicountry_circle_plots.png")

    # ── Report ───────────────────────────────────────────────────────────
    report_path = RESULTS / "wvs_country_comparison_report.md"
    with open(report_path, "w") as f:
        f.write("# WVS Country Comparison — Distance from Global Average\n\n")
        f.write("## Method\n\n")
        f.write("For each country, a γ-vector is constructed with one element per construct pair.\n")
        f.write("The global median γ-vector (element-wise median across 66 countries) serves as\n")
        f.write("the reference. Spearman rank correlation measures how well each country's\n")
        f.write("SES-attitude structure matches the global pattern.\n\n")

        f.write(f"## Mexico's Position\n\n")
        f.write(f"- **Rank**: {mex_rank} / {len(ranked)}\n")
        f.write(f"- **Spearman ρ**: {mex_stats['spearman_rho']:.3f}\n")
        f.write(f"- **Cosine similarity**: {mex_stats['cos_sim']:.3f}\n")
        f.write(f"- **RMSE**: {mex_stats['rmse']:.4f}\n\n")

        f.write("## Full Ranking\n\n")
        f.write("| Rank | Country | Zone | Spearman ρ | Cosine sim | RMSE |\n")
        f.write("|------|---------|------|-----------|-----------|------|\n")
        for i, (c, s) in enumerate(ranked, 1):
            flag = " **" if c == "MEX" else ""
            f.write(f"| {i} | {c}{flag} | {s['zone']} | {s['spearman_rho']:.3f} | "
                    f"{s['cos_sim']:.3f} | {s['rmse']:.4f} |\n")

        f.write(f"\n## Output Files\n\n")
        f.write(f"- `wvs_country_distance_from_average.png` — bar chart ranked by ρ\n")
        f.write(f"- `wvs_multicountry_circle_plots.png` — small multiples (closest + MEX + most distant)\n")

    print(f"\nReport: {report_path}")
    print("Done.")


if __name__ == "__main__":
    main()
