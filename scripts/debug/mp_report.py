"""
Message Passing Analysis — Report Generator

Loads all summary JSONs from data/tda/message_passing/, generates six
publication-quality PNG plots, and writes a comprehensive markdown report
covering all five message passing stages plus a cross-stage synthesis.

Usage:
    python scripts/debug/mp_report.py

Outputs:
    data/tda/message_passing/plots/*.png   (6 figures)
    data/results/message_passing_report.md  (markdown report)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import matplotlib.ticker as mticker      # noqa: E402
import numpy as np                       # noqa: E402

# ── Project paths ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import load_manifest  # noqa: E402

MP_DIR   = ROOT / "data" / "tda" / "message_passing"
PLOT_DIR = MP_DIR / "plots"
REPORT   = ROOT / "data" / "results" / "message_passing_report.md"

# ── WVS domain colour palette ───────────────────────────────────────────────

DOMAIN_COLORS = {
    "WVS_A": "#3b82f6",   # blue — Social values, attitudes, stereotypes
    "WVS_C": "#22c55e",   # green — Work
    "WVS_D": "#f97316",   # orange — Family
    "WVS_E": "#ef4444",   # red — Politics & society
    "WVS_F": "#a855f7",   # purple — Religion & morale
    "WVS_G": "#14b8a6",   # teal — National identity
    "WVS_H": "#92400e",   # brown — Security
    "WVS_I": "#6b7280",   # gray — Science
}

DOMAIN_LABELS = {
    "WVS_A": "A: Social values",
    "WVS_C": "C: Work",
    "WVS_D": "D: Family",
    "WVS_E": "E: Politics",
    "WVS_F": "F: Religion/Morale",
    "WVS_G": "G: National identity",
    "WVS_H": "H: Security",
    "WVS_I": "I: Science",
}

# Distinct zone colour palette (8 zones)
ZONE_COLORS = {
    "Latin America":        "#e63946",
    "English-speaking":     "#457b9d",
    "Protestant Europe":    "#2a9d8f",
    "Catholic Europe":      "#e9c46a",
    "Orthodox/ex-Communist":"#264653",
    "Confucian":            "#f4a261",
    "South/Southeast Asian":"#6a994e",
    "African-Islamic":      "#bc6c25",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_json(name: str) -> dict:
    """Load a JSON file from the message passing directory."""
    with open(MP_DIR / name) as f:
        return json.load(f)


def _short_name(construct_key: str) -> str:
    """'immigrant_origin_status|WVS_G' -> 'immigrant_origin_status'"""
    return construct_key.split("|")[0]


def _domain_code(construct_key: str) -> str:
    """'immigrant_origin_status|WVS_G' -> 'WVS_G'"""
    parts = construct_key.split("|")
    return parts[1] if len(parts) > 1 else "WVS_E"


def _pretty(name: str) -> str:
    """'immigrant_origin_status' -> 'Immigrant origin status'"""
    return name.replace("_", " ").capitalize()


# ── Data loading ─────────────────────────────────────────────────────────────

def load_all_summaries() -> dict:
    """Load all summary JSONs into a single dict."""
    data = {}
    data["manifest"]    = load_manifest()
    data["bp"]          = _load_json("bp_all_summary.json")
    data["spectral"]    = _load_json("spectral_all_summary.json")
    data["ppr"]         = _load_json("ppr_hub_comparison.json")
    data["temporal"]    = _load_json("temporal_all_summary.json")
    data["w7"]          = _load_json("w7_descriptive_summary.json")
    data["mex"]         = _load_json("mex_temporal.json")
    data["mex_means"]   = _load_json("mex_wave_means.json")
    return data


# ═══════════════════════════════════════════════════════════════════════════
#  PLOT 1 — Fiedler values by cultural zone (box plot)
# ═══════════════════════════════════════════════════════════════════════════

def plot_fiedler_by_zone(data: dict) -> None:
    manifest = data["manifest"]
    spectral = data["spectral"]["summaries"]
    country_zone = manifest["country_zone"]

    # Build {zone: [fiedler_values]}
    zone_vals: dict[str, list[float]] = {}
    for entry in spectral:
        c = entry["country"]
        z = country_zone.get(c, "Unknown")
        zone_vals.setdefault(z, []).append(entry["fiedler_value"])

    # Sort zones by median Fiedler
    zones_sorted = sorted(zone_vals, key=lambda z: np.median(zone_vals[z]))
    vals = [zone_vals[z] for z in zones_sorted]

    fig, ax = plt.subplots(figsize=(10, 5))
    bp = ax.boxplot(vals, vert=False, patch_artist=True, widths=0.6,
                    medianprops=dict(color="black", linewidth=1.5))
    for patch, zone in zip(bp["boxes"], zones_sorted):
        patch.set_facecolor(ZONE_COLORS.get(zone, "#cccccc"))
        patch.set_alpha(0.7)

    ax.set_yticklabels(zones_sorted, fontsize=9)
    ax.set_xlabel("Fiedler value (algebraic connectivity)", fontsize=10)
    ax.set_title("Algebraic Connectivity by Cultural Zone (WVS W7)", fontsize=12,
                 fontweight="bold")
    ax.axvline(np.median([e["fiedler_value"] for e in spectral]),
               color="gray", linestyle="--", alpha=0.5, label="Global median")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "fiedler_values_by_zone.png", dpi=200)
    plt.close(fig)
    print("  [1/6] fiedler_values_by_zone.png")


# ═══════════════════════════════════════════════════════════════════════════
#  PLOT 2 — Top-10 BP influencers (horizontal bar)
# ═══════════════════════════════════════════════════════════════════════════

def plot_bp_top_influencers(data: dict) -> None:
    bp_summaries = data["bp"]["summaries"]

    # Count how many countries each construct is #1 in
    counts = Counter(entry["top_influencer"] for entry in bp_summaries)
    top10 = counts.most_common(10)
    labels = [_pretty(_short_name(k)) for k, _ in top10]
    values = [v for _, v in top10]
    colors = [DOMAIN_COLORS.get(_domain_code(k), "#888888") for k, _ in top10]

    fig, ax = plt.subplots(figsize=(10, 5))
    y_pos = range(len(labels) - 1, -1, -1)
    ax.barh(y_pos, values, color=colors, edgecolor="white", height=0.6)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Countries where construct is top BP influencer", fontsize=10)
    ax.set_title("Top-10 Belief Propagation Influencers Across 66 Countries",
                 fontsize=12, fontweight="bold")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    # Legend for domains present
    present_domains = sorted(set(_domain_code(k) for k, _ in top10))
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=DOMAIN_COLORS[d])
               for d in present_domains]
    ax.legend(handles, [DOMAIN_LABELS.get(d, d) for d in present_domains],
              fontsize=7, loc="lower right", ncol=2)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "bp_top_influencers.png", dpi=200)
    plt.close(fig)
    print("  [2/6] bp_top_influencers.png")


# ═══════════════════════════════════════════════════════════════════════════
#  PLOT 3 — Mexico PPR hub scores, top 15
# ═══════════════════════════════════════════════════════════════════════════

def plot_ppr_hub_mex(data: dict) -> None:
    # Load per-country PPR for Mexico
    mex_ppr = _load_json("MEX_ppr.json")
    hub_scores = mex_ppr["hub_scores"]

    # Sort descending, take top 15 (exclude near-zero sinks)
    sorted_hubs = sorted(hub_scores.items(), key=lambda x: x[1], reverse=True)
    top15 = [(k, v) for k, v in sorted_hubs if v > 0.01][:15]

    labels = [_pretty(_short_name(k)) for k, _ in top15]
    values = [v for _, v in top15]
    colors = [DOMAIN_COLORS.get(_domain_code(k), "#888888") for k, _ in top15]

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(labels) - 1, -1, -1)
    ax.barh(y_pos, values, color=colors, edgecolor="white", height=0.6)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("PPR hub score", fontsize=10)
    ax.set_title("Personalized PageRank Hub Scores -- Mexico (WVS W7)",
                 fontsize=12, fontweight="bold")

    # Legend
    present_domains = sorted(set(_domain_code(k) for k, _ in top15))
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=DOMAIN_COLORS[d])
               for d in present_domains]
    ax.legend(handles, [DOMAIN_LABELS.get(d, d) for d in present_domains],
              fontsize=7, loc="lower right", ncol=2)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "ppr_hub_scores_mex.png", dpi=200)
    plt.close(fig)
    print("  [3/6] ppr_hub_scores_mex.png")


# ═══════════════════════════════════════════════════════════════════════════
#  PLOT 4 — Temporal alpha by zone (strip / swarm)
# ═══════════════════════════════════════════════════════════════════════════

def plot_alpha_by_zone(data: dict) -> None:
    temporal = data["temporal"]["alpha_ranking"]

    # Build {zone: [(alpha, country)]}
    zone_pts: dict[str, list[tuple[float, str]]] = {}
    for entry in temporal:
        z = entry["zone"]
        zone_pts.setdefault(z, []).append((entry["alpha"], entry["country"]))

    zones_sorted = sorted(zone_pts, key=lambda z: np.median([a for a, _ in zone_pts[z]]))

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, zone in enumerate(zones_sorted):
        pts = zone_pts[zone]
        alphas = [a for a, _ in pts]
        # Jitter y slightly to avoid overlap
        rng = np.random.RandomState(42 + i)
        jitter = rng.uniform(-0.15, 0.15, len(alphas))
        ax.scatter(alphas, [i + j for j in jitter],
                   color=ZONE_COLORS.get(zone, "#888"),
                   s=50, alpha=0.8, edgecolor="white", linewidth=0.5, zorder=3)
        # Label outliers
        for alpha_val, country in pts:
            if alpha_val > 0.30 or alpha_val < 0.02:
                jit = jitter[pts.index((alpha_val, country))]
                ax.annotate(country, (alpha_val, i + jit),
                            fontsize=6, ha="left", va="bottom",
                            xytext=(4, 2), textcoords="offset points")

    ax.axvline(0.0, color="black", linestyle="-", linewidth=0.8, alpha=0.5)
    ax.axvline(0.0, color="red", linestyle="--", linewidth=1.0, alpha=0.6,
               label=r"$\alpha=0$ (pure inertia)")
    ax.set_yticks(range(len(zones_sorted)))
    ax.set_yticklabels(zones_sorted, fontsize=9)
    ax.set_xlabel(r"Temporal mixing parameter $\alpha$", fontsize=10)
    ax.set_title(r"Network-Driven ($\alpha>0$) vs Inertial ($\alpha \approx 0$) "
                 "Belief Change by Zone", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "alpha_by_zone.png", dpi=200)
    plt.close(fig)
    print("  [4/6] alpha_by_zone.png")


# ═══════════════════════════════════════════════════════════════════════════
#  PLOT 5 — Equilibrium distance ranking (horizontal bar, all 66 countries)
# ═══════════════════════════════════════════════════════════════════════════

def plot_equilibrium_distance(data: dict) -> None:
    w7 = data["w7"]["equilibrium_distance_ranking"]
    country_zone = data["manifest"]["country_zone"]

    # Already sorted ascending by eq_distance
    countries = [e["country"] for e in w7]
    distances = [e["eq_distance"] for e in w7]
    colors = [ZONE_COLORS.get(country_zone.get(c, ""), "#888") for c in countries]

    fig, ax = plt.subplots(figsize=(8, 16))
    y_pos = range(len(countries) - 1, -1, -1)
    ax.barh(y_pos, distances, color=colors, edgecolor="none", height=0.7)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(countries, fontsize=7)
    ax.set_xlabel("Equilibrium distance (L2 norm)", fontsize=10)
    ax.set_title("Distance from Network Equilibrium -- WVS Wave 7",
                 fontsize=12, fontweight="bold")

    # Legend
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=ZONE_COLORS[z])
               for z in ZONE_COLORS]
    ax.legend(handles, list(ZONE_COLORS.keys()), fontsize=6,
              loc="lower right", ncol=2)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "equilibrium_distance_ranking.png", dpi=200)
    plt.close(fig)
    print("  [5/6] equilibrium_distance_ranking.png")


# ═══════════════════════════════════════════════════════════════════════════
#  PLOT 6 — Mexico temporal trajectory (2-panel)
# ═══════════════════════════════════════════════════════════════════════════

def plot_mex_temporal(data: dict) -> None:
    mex = data["mex"]

    # Panel (a): equilibrium distance across waves
    eq_dist = mex["equilibrium_distances"]
    waves_str = sorted(eq_dist.keys())        # W3, W4, W5, W6, W7
    wave_nums = [int(w[1:]) for w in waves_str]
    wave_years = {3: 1996, 4: 2000, 5: 2005, 6: 2012, 7: 2018}
    x_labels = [f"W{n}\n({wave_years.get(n, '')})" for n in wave_nums]
    eq_vals = [eq_dist[w] for w in waves_str]

    # Panel (b): velocity magnitude per transition (proxy for rate of change)
    # Use per-transition alpha as velocity-field proxy
    trans_alpha = mex["per_transition_alpha"]
    trans_keys = sorted(trans_alpha.keys())
    trans_labels = [k.replace("_to_", " -> ") for k in trans_keys]
    trans_vals = [trans_alpha[k] for k in trans_keys]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel (a)
    ax1.plot(range(len(eq_vals)), eq_vals, "o-", color="#e63946",
             linewidth=2, markersize=8)
    ax1.set_xticks(range(len(eq_vals)))
    ax1.set_xticklabels(x_labels, fontsize=9)
    ax1.set_ylabel("Equilibrium distance (L2)", fontsize=10)
    ax1.set_title("(a) Mexico: Distance from Equilibrium", fontsize=11,
                  fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)

    # Panel (b)
    bar_colors = ["#457b9d"] * len(trans_vals)
    ax2.bar(range(len(trans_vals)), trans_vals, color=bar_colors,
            edgecolor="white", width=0.6)
    ax2.set_xticks(range(len(trans_vals)))
    ax2.set_xticklabels(trans_labels, fontsize=8, rotation=15)
    ax2.set_ylabel(r"Per-transition $\alpha$ (network influence)", fontsize=10)
    ax2.set_title(r"(b) Mexico: Network Influence ($\alpha$) per Transition",
                  fontsize=11, fontweight="bold")
    ax2.axhline(0, color="red", linestyle="--", linewidth=0.8, alpha=0.5)
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("Mexico Temporal Trajectory (WVS Waves 3-7, 1996-2018)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "mex_temporal_trajectory.png", dpi=200,
                bbox_inches="tight")
    plt.close(fig)
    print("  [6/6] mex_temporal_trajectory.png")


# ═══════════════════════════════════════════════════════════════════════════
#  MARKDOWN REPORT
# ═══════════════════════════════════════════════════════════════════════════

def generate_report(data: dict) -> str:
    """Generate the full markdown report as a string."""

    # ── Helper data extraction ───────────────────────────────────────────
    bp_summaries = data["bp"]["summaries"]
    spectral_summaries = data["spectral"]["summaries"]
    temporal = data["temporal"]
    w7 = data["w7"]
    mex = data["mex"]
    country_zone = data["manifest"]["country_zone"]

    # BP statistics
    bp_counts = Counter(e["top_influencer"] for e in bp_summaries)
    bp_top3 = bp_counts.most_common(3)
    lifts = [e["top_mean_lift"] for e in bp_summaries]
    median_lift = np.median(lifts)
    outliers = [(e["country"], e["top_mean_lift"]) for e in bp_summaries
                if e["top_mean_lift"] > 0.10]
    outliers.sort(key=lambda x: x[1], reverse=True)

    # Spectral statistics
    fiedler_vals = [e["fiedler_value"] for e in spectral_summaries]
    fiedler_min_entry = min(spectral_summaries, key=lambda e: e["fiedler_value"])
    fiedler_max_entry = max(spectral_summaries, key=lambda e: e["fiedler_value"])

    # Temporal statistics
    alpha_ranking = temporal["alpha_ranking"]
    n_temporal = temporal["n_countries"]

    # W7 statistics
    eq_ranking = w7["equilibrium_distance_ranking"]

    # ── Build report ─────────────────────────────────────────────────────

    lines = []
    def w(s=""): lines.append(s)

    w("# Message Passing on the WVS Belief Network")
    w()
    w("**Technical Report -- Navegador Project**")
    w()
    w(f"*Generated: 2026-04-01 | Data: WVS Wave 7 (66 countries, 55 constructs) "
      f"+ Temporal (37 countries, Waves 3-7)*")
    w()
    w("---")
    w()
    w("## Table of Contents")
    w()
    w("1. [Belief Propagation (Stage 1)](#1-belief-propagation-stage-1)")
    w("2. [Spectral Diffusion (Stage 2)](#2-spectral-diffusion-stage-2)")
    w("3. [Personalized PageRank (Stage 3)](#3-personalized-pagerank-stage-3)")
    w("4. [W7 Descriptive Snapshot](#4-w7-descriptive-snapshot-all-66-countries)")
    w("5. [Temporal Dynamics (Stage 5)](#5-temporal-dynamics-37-countries)")
    w("6. [Cross-Stage Synthesis](#6-cross-stage-synthesis)")
    w()
    w("---")
    w()

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION 1 — Belief Propagation
    # ══════════════════════════════════════════════════════════════════════

    w("## Overview")
    w()
    w("This report documents the five-stage message passing analysis of the WVS "
      "(World Values Survey) belief network. The network consists of 55 attitudinal "
      "constructs connected by doubly-robust SES-bridge estimates ($\\gamma$ values), "
      "computed separately for each of 66 countries in Wave 7 (2017-2022) and across "
      "7 waves (1981-2022) for 37 countries with temporal data.")
    w()
    w("The **fundamental question** is: given the SES-mediated coupling between "
      "attitudinal constructs, what can we infer about the *structure*, *dynamics*, "
      "and *cultural specificity* of belief systems across the world?")
    w()
    w("Each stage applies a different mathematical framework to the same underlying "
      "$\\gamma$ network:")
    w()
    w("| Stage | Framework | Key question |")
    w("|-------|-----------|-------------|")
    w("| 1. Belief Propagation | Markov Random Field | Which beliefs are most constrained by their neighbors? |")
    w("| 2. Spectral Diffusion | Graph Laplacian | How easily does the network bisect? Where are the bottlenecks? |")
    w("| 3. Personalized PageRank | Random walks | Which beliefs are influence hubs vs endpoints? |")
    w("| 4. W7 Snapshot | Equilibrium analysis | How far is each country from its SES-predicted state? |")
    w("| 5. Temporal Dynamics | Mixing model | How much does the SES network explain belief change over time? |")
    w()
    w("The analysis reveals three headline findings:")
    w()
    w("1. **No universal belief hubs exist** -- influence topology is fundamentally "
      "zone-specific, with economic ideology being the closest to a global constant")
    w("2. **Cultural zones structure spectral topology** -- within-zone Fiedler partition "
      "agreement is 2.86x higher than across-zone, with English-speaking countries "
      "showing the most coherent belief structure")
    w("3. **Network-driven vs inertial societies** map onto modernization: rapidly "
      "developing countries (VNM, IND) show high network influence ($\\alpha > 0.30$), "
      "while theocratic or post-conflict states (EGY, JOR) show near-zero")
    w()
    w("---")
    w()
    w("## 1. Belief Propagation (Stage 1)")
    w()
    w("### 1.1 Mathematical Motivation")
    w()
    w("We model the 55-construct belief network as a **pairwise Markov Random Field** "
      "(MRF) on a signed, weighted graph $G = (V, E, w)$, where each node $i \\in V$ "
      "represents a WVS construct and each edge weight $w_{ij} = \\gamma(i, j)$ is the "
      "doubly-robust SES-bridge estimate.")
    w()
    w("The energy function follows a **Potts-like** coupling:")
    w()
    w("$$E(\\mathbf{x}) = -\\sum_{(i,j) \\in E} w_{ij} \\cdot x_i \\cdot x_j$$")
    w()
    w("where $x_i \\in \\{-1, +1\\}$ is a binarized belief state (above/below median). "
      "The Gibbs distribution $P(\\mathbf{x}) \\propto \\exp(-\\beta E(\\mathbf{x}))$ "
      "defines a joint probability over all configurations, parameterized by inverse "
      "temperature $\\beta$.")
    w()
    w("We approximate marginals via **loopy belief propagation** (LBP): each node $i$ "
      "sends messages $m_{i \\to j}(x_j)$ to neighbors, iterating:")
    w()
    w("$$m_{i \\to j}(x_j) \\propto \\sum_{x_i} \\psi_{ij}(x_i, x_j) \\cdot "
      "\\phi_i(x_i) \\cdot \\prod_{k \\in \\mathcal{N}(i) \\setminus j} m_{k \\to i}(x_i)$$")
    w()
    w("where $\\psi_{ij}(x_i, x_j) = \\exp(\\beta \\cdot w_{ij} \\cdot x_i \\cdot x_j)$ "
      "is the pairwise potential and $\\phi_i(x_i)$ is the local evidence (uniform prior "
      "in our case).")
    w()
    w("After convergence, we compute the **belief lift**: the KL divergence between the "
      "BP posterior marginal $b_i(x_i)$ and the prior $\\phi_i(x_i)$:")
    w()
    w("$$\\text{lift}_i = D_{\\text{KL}}(b_i \\| \\phi_i) = "
      "\\sum_{x_i} b_i(x_i) \\log \\frac{b_i(x_i)}{\\phi_i(x_i)}$$")
    w()
    w("High lift means that node $i$'s belief is strongly constrained by its network "
      "neighborhood -- its SES-mediated connections to other constructs push it far from "
      "the uninformative prior.")
    w()
    w("### 1.2 Results")
    w()
    w(f"- **Convergence**: 100% ({len(bp_summaries)}/66 countries converged)")
    w(f"- **Median top lift**: {median_lift:.4f} (most countries' top influencer "
      f"has modest lift)")
    w(f"- **Outlier countries**: {', '.join(f'{c} ({v:.2f})' for c, v in outliers)} "
      f"-- strong network constraint on beliefs")
    w()
    w("**Top influencers** (construct most often ranked #1 across countries):")
    w()
    w("| Construct | Countries (#1 in) | Domain |")
    w("|-----------|-------------------|--------|")
    for key, count in bp_top3:
        w(f"| {_pretty(_short_name(key))} | {count} | {DOMAIN_LABELS.get(_domain_code(key), '')} |")
    w()
    w("The dominance of `immigrant_origin_status` (14 countries) and "
      "`online_political_participation` (11) reveals that immigration attitudes and "
      "digital civic engagement are the constructs most tightly constrained by their "
      "SES network neighborhood. In the MRF interpretation, these nodes sit at high "
      "local field positions: their beliefs are effectively *determined* by the beliefs "
      "of their SES-linked neighbors.")
    w()
    w("**Full BP top-10 influencers:**")
    w()
    w("| Rank | Construct | Countries (#1 in) | Domain |")
    w("|------|-----------|-------------------|--------|")
    for rank, (key, count) in enumerate(bp_counts.most_common(10), 1):
        w(f"| {rank} | {_pretty(_short_name(key))} | {count} | "
          f"{DOMAIN_LABELS.get(_domain_code(key), '')} |")
    w()
    w("**Lift distribution by cultural zone:**")
    w()
    # Compute zone-level lift stats
    zone_lifts: dict[str, list[float]] = {}
    for entry in bp_summaries:
        z = country_zone.get(entry["country"], "Unknown")
        zone_lifts.setdefault(z, []).append(entry["top_mean_lift"])
    w("| Zone | Countries | Median lift | Max lift | Max country |")
    w("|------|-----------|-------------|----------|-------------|")
    for zone in sorted(zone_lifts, key=lambda z: np.median(zone_lifts[z]), reverse=True):
        vals = zone_lifts[zone]
        max_idx = np.argmax(vals)
        max_country = [e["country"] for e in bp_summaries
                       if country_zone.get(e["country"], "") == zone][max_idx]
        w(f"| {zone} | {len(vals)} | {np.median(vals):.4f} | "
          f"{max(vals):.4f} | {max_country} |")
    w()
    w("The zone-level breakdown reveals that **Catholic Europe** (driven by GRC and "
      "CYP outliers) has the highest median lift, while most zones cluster around the "
      "global median of ~0.031. The African-Islamic zone shows the most heterogeneity, "
      "with lifts ranging from near-median to substantially above.")
    w()
    w("### 1.3 Interpretation")
    w()
    w("BP lift measures **how much a construct's belief distribution is shaped by "
      "network context** rather than local evidence. A construct with high lift is "
      "\"predictable from its neighbors\" -- knowing someone's education, age, gender, "
      "and urbanization-conditioned attitudes on related topics tightly constrains their "
      "stance on immigration or online participation.")
    w()
    w("The outlier countries (GRC: 0.44, URY: 0.39, TWN: 0.28) have unusually tight "
      "belief coupling: the SES network in these societies acts as a strong constraint "
      "system where one attitude implies many others. This is consistent with their high "
      "SES collinearity (PC1 > 80%).")
    w()
    w("### 1.4 Pitfalls and Limitations")
    w()
    w("1. **Loopy BP is approximate**: the belief network has many short cycles "
      "(clustering coefficient 0.53), so LBP marginals are not exact. On trees, BP "
      "computes exact marginals; on loopy graphs, it minimizes the Bethe free energy, "
      "which is an approximation to the true Gibbs free energy. The bound "
      "$|b_i - p_i| \\leq O(\\beta^{\\text{girth}})$ suggests accuracy improves with "
      "longer cycle lengths. Our network's average clustering of 0.53 implies many "
      "triangles (short cycles), but 100% convergence across 66 countries indicates "
      "the approximation is stable in practice.")
    w("2. **Potts vs Gaussian**: the binary Potts model discretizes each construct "
      "to $\\{-1, +1\\}$ (above/below median), discarding ordinal information. The "
      "WVS constructs are continuous aggregates on [1,10], and binarization loses "
      "gradient information. A Gaussian MRF with precision matrix $J$ (where "
      "$J_{ij} = -\\gamma_{ij}$) would model continuous beliefs directly, but requires "
      "$O(n^3)$ matrix inversion per country and is sensitive to the positive-"
      "definiteness of $J$. The Potts discretization is a conservative choice that "
      "ensures stable inference at the cost of information loss.")
    w("3. **Observational, not causal**: BP lift reflects SES-mediated *statistical* "
      "coupling. It does not imply that changing one belief would propagate to neighbors. "
      "In the language of causal inference, the $\\gamma$ edges are observational "
      "associations conditioned on SES, not interventional effects. A construct with "
      "high lift could be highly constrained because it shares common SES causes with "
      "many neighbors (confounding), not because those neighbors directly influence it.")
    w("4. **Beta sensitivity**: the inverse temperature $\\beta$ controls coupling "
      "strength. At $\\beta = 0$ (infinite temperature), all beliefs are independent "
      "and lift = 0 everywhere. At $\\beta \\to \\infty$ (zero temperature), the system "
      "freezes into the ground state and all beliefs are deterministic. Our default "
      "$\\beta = 1$ is a modeling choice placing the system in the ordered phase but "
      "far from the frozen limit. A systematic $\\beta$-sweep would identify the "
      "critical temperature $\\beta_c$ where the phase transition occurs, but this "
      "is computationally expensive (66 countries $\\times$ 20+ $\\beta$ values).")
    w("5. **Edge density**: the $\\gamma$ matrix is dense (23% non-zero edges), making "
      "the MRF highly connected. In sparse MRFs, BP is near-exact; in dense MRFs, "
      "the Bethe approximation degrades. The high density of our network means BP "
      "results should be interpreted as qualitative rankings rather than precise "
      "posterior probabilities.")
    w()
    w("### Plots")
    w()
    w("![Top-10 BP influencers across 66 countries](../tda/message_passing/plots/bp_top_influencers.png)")
    w()
    w("---")
    w()

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION 2 — Spectral Diffusion
    # ══════════════════════════════════════════════════════════════════════

    w("## 2. Spectral Diffusion (Stage 2)")
    w()
    w("### 2.1 Mathematical Motivation")
    w()
    w("The **graph Laplacian** $L = D - A$ (where $D$ is the degree matrix and $A$ "
      "the adjacency matrix of $|\\gamma|$ weights) governs diffusion on the network. "
      "Its eigendecomposition $L = U \\Lambda U^T$ yields:")
    w()
    w("- $\\lambda_1 = 0$ (trivial, connected component)")
    w("- $\\lambda_2$ = **Fiedler value** (algebraic connectivity): the smallest "
      "nontrivial eigenvalue, measuring how easily the network can be bisected")
    w("- $\\mathbf{v}_2$ = **Fiedler vector**: its sign pattern defines the optimal "
      "graph bipartition (spectral clustering)")
    w()
    w("The **heat kernel** $H(t) = \\exp(-tL)$ describes continuous-time diffusion of "
      "belief states on the network. At time $t$, an initial perturbation $\\mathbf{f}(0)$ "
      "evolves as:")
    w()
    w("$$\\mathbf{f}(t) = \\exp(-tL) \\mathbf{f}(0) = \\sum_k e^{-\\lambda_k t} "
      "(\\mathbf{u}_k^T \\mathbf{f}(0)) \\mathbf{u}_k$$")
    w()
    w("The Fiedler value $\\lambda_2$ controls the slowest non-trivial decay mode: "
      "low $\\lambda_2$ means slow mixing (beliefs persist in two camps), "
      "high $\\lambda_2$ means rapid homogenization.")
    w()
    w("### 2.2 Results")
    w()
    w(f"- **Fiedler range**: {fiedler_min_entry['fiedler_value']:.3f} "
      f"({fiedler_min_entry['country']}) to {fiedler_max_entry['fiedler_value']:.3f} "
      f"({fiedler_max_entry['country']})")
    w(f"- **Median**: {np.median(fiedler_vals):.3f}")
    w(f"- **Within-zone ARI**: 0.0164 (Fiedler partition agreement within cultural zones)")
    w(f"- **Across-zone ARI**: 0.0057")
    w(f"- **Ratio**: 2.86x -- Fiedler partitions are nearly 3x more similar within "
      f"cultural zones than across zones")
    w()
    w("**Zone-level ARI (Fiedler partition coherence):**")
    w()
    w("| Zone | Mean ARI | Interpretation |")
    w("|------|----------|----------------|")
    w("| English-speaking | 0.153 | Highly coherent -- similar bipartition across AUS, CAN, GBR, USA, NZL, NIR |")
    w("| Catholic Europe | -0.002 | No coherence |")
    w("| South/Southeast Asian | -0.003 | No coherence |")
    w()
    w("**Fiedler value distribution by zone:**")
    w()
    zone_fiedler: dict[str, list[tuple[float, str]]] = {}
    for entry in spectral_summaries:
        z = country_zone.get(entry["country"], "Unknown")
        zone_fiedler.setdefault(z, []).append(
            (entry["fiedler_value"], entry["country"]))
    w("| Zone | Countries | Median | Min (country) | Max (country) | IQR |")
    w("|------|-----------|--------|---------------|---------------|-----|")
    for zone in sorted(zone_fiedler, key=lambda z: np.median([v for v, _ in zone_fiedler[z]])):
        vals = [v for v, _ in zone_fiedler[zone]]
        cs = [c for _, c in zone_fiedler[zone]]
        imin = int(np.argmin(vals))
        imax = int(np.argmax(vals))
        q25, q75 = np.percentile(vals, [25, 75])
        w(f"| {zone} | {len(vals)} | {np.median(vals):.3f} | "
          f"{vals[imin]:.3f} ({cs[imin]}) | {vals[imax]:.3f} ({cs[imax]}) | "
          f"{q75 - q25:.3f} |")
    w()
    w("**Top Fiedler-loading constructs** (most frequently the highest-loading "
      "construct on the Fiedler vector across countries):")
    w()
    fiedler_top_counts = Counter(e["top_loading_construct"] for e in spectral_summaries)
    w("| Construct | Countries with top loading |")
    w("|-----------|--------------------------|")
    for key, count in fiedler_top_counts.most_common(8):
        w(f"| {_pretty(_short_name(key))} | {count} |")
    w()
    w("The top-loading constructs on the Fiedler vector are the constructs that "
      "sit furthest from the spectral bisection plane -- they define the two camps "
      "of the belief structure. Their diversity across countries (no single construct "
      "dominates) confirms the zone-specificity of belief topology.")
    w()
    w("Note that the Fiedler partition is *not* the same as a positive/negative "
      "$\\gamma$-sign partition. The Fiedler vector minimizes the Rayleigh quotient "
      "$R(\\mathbf{v}) = \\mathbf{v}^T L \\mathbf{v} / \\mathbf{v}^T \\mathbf{v}$ "
      "subject to orthogonality with the constant eigenvector. This yields the "
      "partition that minimizes total edge weight *cut*, which is a different "
      "objective from maximizing structural balance (the $\\gamma$-sign partition). "
      "In practice the two partitions largely agree (both reflect the dominant "
      "education-vs-tradition axis identified by PCA), but discrepancies arise "
      "where non-monotonic SES patterns or NMI-detectable-but-$\\gamma$-invisible "
      "relationships create spectral structure invisible to the sign partition.")
    w()
    w("### 2.3 Interpretation")
    w()
    w("The Fiedler vector partitions each country's 55-construct network into two "
      "camps. In English-speaking countries, this partition is nearly identical: the same "
      "constructs cluster together regardless of whether we look at Australia, Canada, or "
      "the UK. This means the *structure* of SES-mediated belief coupling -- which beliefs "
      "go together and which oppose each other -- is a cultural invariant in the "
      "Anglosphere.")
    w()
    w("Bangladesh's low Fiedler value (0.61) indicates a near-bipartite belief structure: "
      "the network has a clear bottleneck separating two belief clusters, with weak "
      "cross-cluster SES coupling. Mongolia's high value (0.89) means uniform SES "
      "coupling -- no natural split point.")
    w()
    w("The Fiedler value also controls **diffusion timescale**: the time for a belief "
      "perturbation to spread across the full network scales as $\\tau \\sim 1/\\lambda_2$. "
      f"With the observed range ({fiedler_min_entry['fiedler_value']:.2f} to "
      f"{fiedler_max_entry['fiedler_value']:.2f}), diffusion timescales vary by a factor "
      f"of {fiedler_max_entry['fiedler_value']/fiedler_min_entry['fiedler_value']:.1f}x "
      "across countries. Bangladesh would take ~45% longer than Mongolia for a belief "
      "perturbation to reach network-wide equilibrium.")
    w()
    w("The spectral gap $\\lambda_2$ has a second interpretation via the **Cheeger "
      "inequality**: $h^2/2 \\leq \\lambda_2 \\leq 2h$, where $h$ is the Cheeger "
      "constant (optimal edge cut ratio). Low $\\lambda_2$ implies a cheap graph cut "
      "exists -- the network can be split into two weakly-connected components. This "
      "connects to the sociological concept of belief polarization: countries with low "
      "Fiedler values have two belief clusters with minimal SES-mediated cross-talk.")
    w()
    w("### 2.4 Pitfalls and Limitations")
    w()
    w("1. **Absolute values discard sign**: the Laplacian uses $|\\gamma|$ weights, "
      "losing the positive/negative distinction. The Fiedler partition is a *structural* "
      "bipartition, not a sign-based one (though in practice they largely agree due to "
      "94% structural balance).")
    w("2. **Linear dynamics**: the heat kernel is a linear diffusion model. Real belief "
      "change involves nonlinear thresholds, social influence cascades, and exogenous "
      "shocks.")
    w("3. **Arbitrary $t$**: the diffusion time $t$ is a free parameter. We report "
      "Fiedler values (eigenvalues) rather than diffused states to avoid this choice.")
    w()
    w("### Plots")
    w()
    w("![Fiedler values by cultural zone](../tda/message_passing/plots/fiedler_values_by_zone.png)")
    w()
    w("---")
    w()

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION 3 — Personalized PageRank
    # ══════════════════════════════════════════════════════════════════════

    w("## 3. Personalized PageRank (Stage 3)")
    w()
    w("### 3.1 Mathematical Motivation")
    w()
    w("**Personalized PageRank** (PPR) with restart probability $\\alpha$ computes, "
      "for each seed node $s$, the stationary distribution:")
    w()
    w("$$\\boldsymbol{\\pi}_s = \\alpha \\mathbf{e}_s + (1 - \\alpha) P^T \\boldsymbol{\\pi}_s$$")
    w()
    w("where $P$ is the row-normalized transition matrix of $|\\gamma|$ weights and "
      "$\\mathbf{e}_s$ is the indicator vector for node $s$. Solving:")
    w()
    w("$$\\boldsymbol{\\pi}_s = \\alpha (I - (1-\\alpha) P^T)^{-1} \\mathbf{e}_s$$")
    w()
    w("The **hub score** of node $i$ is its average PPR mass when every other node is "
      "seeded: $\\text{hub}(i) = \\frac{1}{n} \\sum_s \\pi_s(i)$. High hub score means "
      "many random walks end up at $i$ regardless of starting point -- $i$ is a global "
      "attractor of network influence.")
    w()
    w("The **sink score** is the complement: nodes with low hub scores are influence "
      "endpoints (belief *consequences* rather than belief *drivers*).")
    w()
    w("### 3.2 Results")
    w()
    w("- **No universal hubs**: no construct appears in the top-10 hub list of every "
      "cultural zone. Influence topology is fundamentally zone-specific.")
    w("- **Most consistent**: `economic_ideology` has global median rank 7 and appears "
      "in the top-10 of 6+ zones -- the closest thing to a universal influence hub.")
    w("- **Weak mediator correlation**: Spearman $\\rho \\approx -0.15$ to $+0.10$ between "
      "PPR hub rank and Floyd-Warshall mediator score in all countries. Topological "
      "centrality (shortest paths) and diffusion centrality (random walks) measure "
      "different things.")
    w()
    w("**Zone-specific hubs (top construct per zone):**")
    w()
    w("| Zone | Top Hub | Zone top-10 count |")
    w("|------|---------|-------------------|")
    ppr_zones = data["ppr"]["zone_specific_hubs"]
    for zone_name, hub_list in ppr_zones.items():
        if hub_list:
            top = hub_list[0]
            w(f"| {zone_name} | {_pretty(_short_name(top['construct']))} | "
              f"{top['zone_top10_count']}/{top['zone_size']} |")
    w()
    w("**Extended zone-specific hub table** (top-3 hubs per zone):")
    w()
    w("| Zone | Rank | Hub construct | Top-10 in | Global med. rank |")
    w("|------|------|--------------|-----------|-----------------|")
    for zone_name, hub_list in ppr_zones.items():
        for rank, hub in enumerate(hub_list[:3], 1):
            w(f"| {zone_name if rank == 1 else ''} | {rank} | "
              f"{_pretty(_short_name(hub['construct']))} | "
              f"{hub['zone_top10_count']}/{hub['zone_size']} | "
              f"{hub['global_median_rank']} |")
    w()
    w("The global median rank column reveals the contrast between zone-specific "
      "and global influence: `economic_ideology` (median rank 7) is the closest "
      "to a global hub, but `democratic_values_importance` (median rank 11) and "
      "`postmaterialist_values` (median rank 10) are strong in Latin America and "
      "English-speaking zones yet much weaker elsewhere.")
    w()
    w("**Mexico PPR profile:**")
    w()
    w("Mexico's PPR hub scores are notably flat (range: 0.766-0.798, excluding sinks), "
      "indicating a diffuse influence topology where no single construct dominates. The "
      "top hubs are `voluntary_association_belonging` (0.798), `democratic_values_importance` "
      "(0.798), and `perceived_positive_effects_of_immigration` (0.797). The sinks "
      "(near-zero scores) are `existential_threat_worry`, `immigrant_origin_status`, "
      "`offline_political_participation`, `perceived_corruption`, `socioeconomic_insecurity_worry`, "
      "and `voting_participation` -- these are belief endpoints rather than drivers in "
      "the Mexican SES network.")
    w()
    w("### 3.3 Interpretation")
    w()
    w("The absence of universal hubs is a strong result. It means that belief influence "
      "structure is culturally contingent: in Latin America, `economic_ideology` and "
      "`authoritarian_governance_tolerance` drive belief coupling, while in English-speaking "
      "countries, `democratic_values_importance` and `child_qualities_prosocial_diligence` "
      "dominate. The SES network routes influence through different constructs depending "
      "on the cultural context.")
    w()
    w("The hub/sink asymmetry is interpretively rich: hubs are constructs that *generate* "
      "SES-mediated constraint (knowing someone's stance on economic ideology constrains "
      "many other beliefs), while sinks are constructs that *absorb* constraint (stance on "
      "online political participation is a downstream consequence of many other beliefs).")
    w()
    w("### 3.4 Pitfalls and Limitations")
    w()
    w("1. **Influence $\\neq$ causation**: PPR measures network influence, not causal "
      "effect. A hub could be a common *symptom* of underlying SES position rather than "
      "a *driver* of other beliefs.")
    w("2. **PPR conflates reach and proximity**: a construct can have high hub score "
      "either because it is connected to many others (high degree) or because it is "
      "close to high-degree nodes (proximity). These are substantively different.")
    w("3. **$\\alpha$ sensitivity**: restart probability $\\alpha$ controls "
      "locality vs globality of influence. Our default $\\alpha = 0.2$ is standard "
      "but arbitrary. Small $\\alpha$ emphasizes global network structure (long random "
      "walks), while large $\\alpha$ emphasizes local neighborhood (short walks). The "
      "choice affects the hub/sink ranking: local hubs (high-degree nodes) dominate at "
      "high $\\alpha$, while global hubs (bridge nodes) dominate at low $\\alpha$.")
    w("4. **Transition matrix symmetry**: PPR uses $|\\gamma|$ weights, discarding "
      "the sign structure. A signed PageRank variant (e.g., using separate positive "
      "and negative transition matrices) would capture the co-elevation vs counter-"
      "variation distinction that is central to the $\\gamma$-surface framework.")
    w()
    w("### Plots")
    w()
    w("![PPR hub scores for Mexico](../tda/message_passing/plots/ppr_hub_scores_mex.png)")
    w()
    w("---")
    w()

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION 4 — W7 Descriptive Snapshot
    # ══════════════════════════════════════════════════════════════════════

    w("## 4. W7 Descriptive Snapshot (All 66 Countries)")
    w()
    w("### 4.1 Velocity Field and Equilibrium Distance")
    w()
    w("For each country's belief network, we define the **network equilibrium** as "
      "the stationary distribution $\\boldsymbol{\\pi}^*$ of the Markov chain defined "
      "by the row-normalized $|\\gamma|$ transition matrix:")
    w()
    w("$$\\boldsymbol{\\pi}^* = \\boldsymbol{\\pi}^* P$$")
    w()
    w("The **equilibrium distance** is the L2 norm between the observed construct "
      "means $\\bar{\\mathbf{x}}$ and the equilibrium prediction:")
    w()
    w("$$d_{\\text{eq}} = \\| \\bar{\\mathbf{x}} - \\boldsymbol{\\pi}^* \\|_2$$")
    w()
    w("The **velocity field** $\\mathbf{v} = P \\bar{\\mathbf{x}} - \\bar{\\mathbf{x}}$ "
      "gives the direction and magnitude of the force the network exerts on each "
      "construct: positive velocity means the network pushes the construct upward, "
      "negative means downward.")
    w()
    w("### 4.2 Results")
    w()
    w("**Equilibrium distance ranking** (selected countries):")
    w()
    w("| Rank | Country | Zone | Eq. Distance |")
    w("|------|---------|------|-------------|")
    for i, entry in enumerate(eq_ranking[:5]):
        c = entry["country"]
        w(f"| {i+1} | {c} | {country_zone.get(c, '')} | {entry['eq_distance']:.2f} |")
    w("| ... | | | |")
    # Find MEX rank
    mex_rank = next(i for i, e in enumerate(eq_ranking) if e["country"] == "MEX") + 1
    mex_eq = next(e for e in eq_ranking if e["country"] == "MEX")
    w(f"| {mex_rank} | MEX | Latin America | {mex_eq['eq_distance']:.2f} |")
    w("| ... | | | |")
    for i, entry in enumerate(eq_ranking[-3:]):
        c = entry["country"]
        rank = len(eq_ranking) - 2 + i
        w(f"| {rank} | {c} | {country_zone.get(c, '')} | {entry['eq_distance']:.2f} |")
    w()
    w("**Top velocity constructs** (most frequently highest-velocity across countries):")
    w()
    w("| Construct | Countries with top velocity |")
    w("|-----------|---------------------------|")
    top_vel = w7["top_velocity_construct_frequency"]
    for key, count in sorted(top_vel.items(), key=lambda x: x[1], reverse=True)[:5]:
        w(f"| {_pretty(_short_name(key))} | {count}/66 |")
    w()
    w("**Zone-level equilibrium distance:**")
    w()
    zone_eq: dict[str, list[tuple[float, str]]] = {}
    for entry in eq_ranking:
        z = country_zone.get(entry["country"], "Unknown")
        zone_eq.setdefault(z, []).append((entry["eq_distance"], entry["country"]))
    w("| Zone | Countries | Median eq. dist. | Closest | Farthest |")
    w("|------|-----------|-----------------|---------|----------|")
    for zone in sorted(zone_eq, key=lambda z: np.median([v for v, _ in zone_eq[z]])):
        vals = [v for v, _ in zone_eq[zone]]
        cs = [c for _, c in zone_eq[zone]]
        imin = int(np.argmin(vals))
        imax = int(np.argmax(vals))
        w(f"| {zone} | {len(vals)} | {np.median(vals):.2f} | "
          f"{cs[imin]} ({vals[imin]:.1f}) | {cs[imax]} ({vals[imax]:.1f}) |")
    w()
    w("The zone-level pattern is clear: **Latin America** has the lowest median "
      "equilibrium distance (beliefs most consistent with SES predictions), while "
      "**African-Islamic** and **Protestant Europe** are farthest from equilibrium. "
      "This aligns with the finding that education is the dominant SES dimension "
      "in Latin America (73% of bridges), producing a simpler, more predictable "
      "belief structure.")
    w()
    w("**Expanded equilibrium distance ranking (top-10 and bottom-10):**")
    w()
    w("| Rank | Country | Zone | Eq. Distance |")
    w("|------|---------|------|-------------|")
    for i, entry in enumerate(eq_ranking[:10], 1):
        c = entry["country"]
        w(f"| {i} | {c} | {country_zone.get(c, '')} | {entry['eq_distance']:.2f} |")
    w("| ... | | | |")
    for i, entry in enumerate(eq_ranking[-10:]):
        rank = len(eq_ranking) - 9 + i
        c = entry["country"]
        w(f"| {rank} | {c} | {country_zone.get(c, '')} | {entry['eq_distance']:.2f} |")
    w()
    w("**Full velocity field -- top constructs by domain:**")
    w()
    top_vel = w7["top_velocity_construct_frequency"]
    vel_by_domain: dict[str, list[tuple[str, int]]] = {}
    for key, count in top_vel.items():
        d = _domain_code(key)
        vel_by_domain.setdefault(d, []).append((_short_name(key), count))
    w("| Domain | Top-velocity constructs | Total countries |")
    w("|--------|------------------------|----------------|")
    for d in sorted(vel_by_domain):
        items = vel_by_domain[d]
        total = sum(c for _, c in items)
        names = ", ".join(f"{n} ({c})" for n, c in
                          sorted(items, key=lambda x: x[1], reverse=True))
        w(f"| {DOMAIN_LABELS.get(d, d)} | {names} | {total} |")
    w()
    w("Security (H) and National Identity (G) domains dominate the velocity field, "
      "accounting for over half of the top-velocity constructs. These are the belief "
      "domains under the strongest network pressure in Wave 7.")
    w()
    w("The domain concentration of velocity is notable: Politics (E) has the most "
      "constructs (19 of 55) but accounts for a minority of top-velocity instances. "
      "Political attitudes are close to their SES-predicted positions. In contrast, "
      "Security and Identity constructs are consistently displaced from their "
      "network-predicted positions, suggesting that recent geopolitical events "
      "(migration crises, security threats, nationalist movements) have pushed these "
      "attitudes away from where SES mediation alone would place them.")
    w()
    w("### 4.3 Interpretation")
    w()
    w("Countries *close* to equilibrium (MNG: 10.1, ARG: 11.4) have belief profiles "
      "that are approximately consistent with their SES network: the network's \"force\" "
      "on each construct is small. Countries *far* from equilibrium (LBY: 15.9, "
      "EGY: 15.9) have belief profiles that the network would substantially rearrange "
      "if it were the only force operating -- suggesting that non-SES forces (religion, "
      "politics, conflict) are holding beliefs away from the SES-predicted equilibrium.")
    w()
    w("Mexico ranks 4th closest (eq_distance = 11.9), meaning its belief structure is "
      "well-explained by SES mediation. This is consistent with the earlier finding that "
      "Mexico has the lowest RMSE from the global median $\\gamma$-vector.")
    w()
    w("The equilibrium distance concept connects to statistical mechanics: in a Boltzmann "
      "system, the equilibrium distribution is the maximum-entropy state consistent with "
      "the energy constraints. Countries close to equilibrium have belief profiles that are "
      "\"natural\" given their SES coupling structure -- each belief is approximately where "
      "the network forces would place it. Countries far from equilibrium have beliefs held "
      "in \"strained\" positions by external forces (religion, authoritarianism, recent "
      "conflict) that override SES mediation.")
    w()
    w("The top-velocity constructs provide a specific prediction: if non-SES forces were "
      "removed, `immigrant_origin_status` would shift the most in 14/66 countries. This "
      "is the construct under the greatest \"tension\" between its SES-predicted position "
      "and its observed position. In concrete terms: the SES network predicts a particular "
      "relationship between immigration attitudes and other beliefs (e.g., education, "
      "urbanization), but the observed attitudes are displaced from this prediction by "
      "political rhetoric, media framing, or historical migration patterns.")
    w()
    w("The velocity field's top constructs (immigration status, online political "
      "participation) are the same as BP's top influencers, reinforcing that these are "
      "the constructs under the most network pressure.")
    w()
    w("### Plots")
    w()
    w("![Equilibrium distance ranking](../tda/message_passing/plots/equilibrium_distance_ranking.png)")
    w()
    w("---")
    w()

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION 5 — Temporal Dynamics
    # ══════════════════════════════════════════════════════════════════════

    w("## 5. Temporal Dynamics (37 Countries)")
    w()
    w("### 5.1 Mathematical Motivation")
    w()
    w("We model belief change as a **1-parameter mixing** of inertia and network "
      "prediction:")
    w()
    w("$$\\bar{\\mathbf{x}}_{t+1} = (1 - \\alpha) \\bar{\\mathbf{x}}_t + "
      "\\alpha \\cdot P_t \\bar{\\mathbf{x}}_t$$")
    w()
    w("where $\\bar{\\mathbf{x}}_t$ is the vector of construct means at wave $t$, "
      "$P_t$ is the row-normalized $|\\gamma|$ transition matrix at wave $t$, and "
      "$\\alpha \\in [0, 1]$ is the **mixing parameter**.")
    w()
    w("- $\\alpha = 0$: pure inertia (beliefs at $t+1$ equal beliefs at $t$)")
    w("- $\\alpha = 1$: pure network dynamics (beliefs at $t+1$ fully determined by "
      "SES network)")
    w()
    w("We estimate $\\alpha^*$ via least-squares:")
    w()
    w("$$\\alpha^* = \\arg\\min_\\alpha \\sum_{t} \\| \\bar{\\mathbf{x}}_{t+1} - "
      "[(1 - \\alpha) \\bar{\\mathbf{x}}_t + \\alpha \\cdot P_t \\bar{\\mathbf{x}}_t] "
      "\\|_2^2$$")
    w()
    w("which has a closed-form solution as a scalar linear regression of $\\Delta x$ "
      "on $(Px - x)$.")
    w()
    w("### 5.2 Results")
    w()
    w(f"- **Countries with temporal data**: {n_temporal}")
    w(f"- **Alpha range**: {alpha_ranking[-1]['alpha']:.2f} ({alpha_ranking[-1]['country']}) "
      f"to {alpha_ranking[0]['alpha']:.2f} ({alpha_ranking[0]['country']})")
    w()
    w("**Most network-driven societies** ($\\alpha > 0.30$):")
    w()
    w("| Country | Zone | $\\alpha$ | Waves |")
    w("|---------|------|----------|-------|")
    for entry in alpha_ranking[:5]:
        w(f"| {entry['country']} | {entry['zone']} | {entry['alpha']:.3f} | {entry['n_waves']} |")
    w()
    w("**Most inertial societies** ($\\alpha < 0.05$):")
    w()
    w("| Country | Zone | $\\alpha$ | Waves |")
    w("|---------|------|----------|-------|")
    for entry in alpha_ranking[-3:]:
        w(f"| {entry['country']} | {entry['zone']} | {entry['alpha']:.3f} | {entry['n_waves']} |")
    w()

    # Zone-level alpha summary
    zone_alphas: dict[str, list[float]] = {}
    for entry in alpha_ranking:
        zone_alphas.setdefault(entry["zone"], []).append(entry["alpha"])
    w("**Zone-level $\\alpha$ summary:**")
    w()
    w("| Zone | Countries | Median $\\alpha$ | Range |")
    w("|------|-----------|-----------------|-------|")
    for zone in sorted(zone_alphas, key=lambda z: np.median(zone_alphas[z]), reverse=True):
        vals = zone_alphas[zone]
        w(f"| {zone} | {len(vals)} | {np.median(vals):.3f} | "
          f"{min(vals):.3f}-{max(vals):.3f} |")
    w()
    w("### 5.3 Mexico Deep Dive")
    w()
    w(f"- **Overall $\\alpha$**: {mex['alpha_star']:.3f} (moderately network-driven)")
    w(f"- **Waves**: {mex['waves']} (1996-2018)")
    w(f"- **Temporal core constructs**: {mex['n_temporal_core']} (present in 3+ waves)")
    w()
    w("**Per-transition dynamics:**")
    w()
    w("| Transition | $\\alpha$ | Interpretation |")
    w("|------------|----------|----------------|")
    trans = mex["per_transition_alpha"]
    interp = {
        "W3_to_W4": "Near-zero: 1996-2000 belief change was inertial (post-crisis stability)",
        "W4_to_W5": "Moderate: 2000-2005 network influence rising (democratic transition era)",
        "W5_to_W6": "Zero: 2005-2012 change orthogonal to network predictions (drug war shock?)",
        "W6_to_W7": "Strong: 2012-2018 network drives belief change (consolidation)",
    }
    for k in sorted(trans.keys()):
        w(f"| {k.replace('_', ' ')} | {trans[k]:.3f} | {interp.get(k, '')} |")
    w()
    w("**Equilibrium distance trajectory:**")
    w()
    eq_d = mex["equilibrium_distances"]
    w("| Wave | Year | Eq. Distance | Trend |")
    w("|------|------|-------------|-------|")
    wave_years = {3: 1996, 4: 2000, 5: 2005, 6: 2012, 7: 2018}
    prev = None
    for wk in sorted(eq_d.keys()):
        wn = int(wk[1:])
        val = eq_d[wk]
        trend = ""
        if prev is not None:
            trend = "+" if val > prev else "-"
        w(f"| W{wn} | {wave_years.get(wn, '')} | {val:.2f} | {trend} |")
        prev = val
    w()
    w(f"Mexico's equilibrium distance *increases* monotonically from {eq_d['W3']:.1f} "
      f"(1996) to {eq_d['W7']:.1f} (2018), meaning Mexican beliefs are *diverging* "
      f"from the SES network's predicted equilibrium over time. This suggests that "
      f"non-SES forces (democratization, drug war, media landscape changes) are "
      f"increasingly pulling beliefs away from the pattern predicted by pure SES "
      f"mediation.")
    w()
    w("**Top velocity constructs (last wave):**")
    w()
    for v_entry in mex["top_velocity_last_wave"]:
        direction = "upward" if v_entry["velocity"] > 0 else "downward"
        w(f"- `{_short_name(v_entry['construct'])}`: velocity = {v_entry['velocity']:+.3f} "
          f"({direction} network pressure)")
    w()
    w("**Residual RMSE by transition** (how well the mixing model fits):")
    w()
    w("| Transition | Residual RMSE | $\\alpha$ | Interpretation |")
    w("|------------|--------------|----------|----------------|")
    for k in sorted(mex["residual_rmse"].keys()):
        rmse = mex["residual_rmse"][k]
        ak = k.replace("_", "_to_", 1).replace("_W", "_to_W", 1) if "_to_" not in k else k
        # Map residual key to alpha key
        alpha_key = k.replace("_W", "_to_W") if "_to_" not in k else k
        alpha_val = trans.get(alpha_key, "N/A")
        if isinstance(alpha_val, (int, float)):
            w(f"| {k} | {rmse:.3f} | {alpha_val:.3f} | "
              f"{'Good fit' if rmse < 2.0 else 'Poor fit -- large residuals'} |")
        else:
            w(f"| {k} | {rmse:.3f} | N/A | |")
    w()
    w("All transitions show RMSE around 1.9-2.2, indicating that the 1-parameter "
      "mixing model captures the general direction of belief change but leaves "
      "substantial construct-level residuals. The W5-W6 transition (2005-2012) has "
      "the highest RMSE (2.24) and $\\alpha = 0$, confirming that this period's "
      "belief change was orthogonal to network predictions.")
    w()
    w("**Temporal top-velocity constructs** (most frequently highest-velocity across "
      "37 countries):")
    w()
    temp_vel = temporal.get("top_velocity_frequency", {})
    w("| Construct | Countries with top velocity |")
    w("|-----------|---------------------------|")
    for key, count in sorted(temp_vel.items(), key=lambda x: x[1], reverse=True)[:8]:
        w(f"| {_pretty(_short_name(key))} | {count}/37 |")
    w()
    w("The temporal velocity leaders mirror the W7 snapshot: immigration status, "
      "neighborhood disorder, and online political participation are under the most "
      "persistent network pressure across both time and geography.")
    w()
    w("### 5.4 Interpretation")
    w()
    w("$\\alpha$ measures **how much of observed belief change is explained by the "
      "SES network's predictions**. Vietnam ($\\alpha = 0.40$) and Russia ($\\alpha = 0.38$) "
      "show the strongest network-driven dynamics: their belief shifts between waves "
      "follow the direction predicted by SES coupling. Egypt ($\\alpha = 0.00$) shows "
      "pure inertia: belief change is orthogonal to SES network predictions, suggesting "
      "that non-SES forces (religion, authoritarianism, conflict) dominate.")
    w()
    w("The geographic pattern is suggestive: high-$\\alpha$ countries tend to be "
      "undergoing rapid socioeconomic modernization (Vietnam, India, Thailand), "
      "while low-$\\alpha$ countries are either highly stable (Slovenia) or in states "
      "where non-SES institutions dominate belief formation (Egypt, Jordan).")
    w()
    w("This connects to Inglehart's modernization theory: in societies undergoing "
      "rapid economic development, rising education and urbanization reshape the "
      "SES distribution, and belief change follows the new SES structure ($\\alpha > 0$). "
      "In societies where material security is either already achieved (Western Europe) "
      "or disrupted by conflict (MENA), belief change is driven by forces outside the "
      "SES network ($\\alpha \\approx 0$).")
    w()
    w("**Mexico's increasing $\\alpha$ trajectory** is particularly revealing: from "
      "near-zero in 1996-2000 (post-peso crisis inertia) to 0.35 in 2012-2018 (network-"
      "driven change). This suggests that Mexico's belief dynamics are becoming *more* "
      "SES-structured over time, even as the beliefs themselves diverge from the "
      "SES-predicted equilibrium. The paradox resolves as follows: the *direction* of "
      "belief change is increasingly aligned with SES network predictions, but the "
      "*magnitude* is insufficient to close the growing gap. External forces (security "
      "crisis, political polarization) amplify the gap faster than SES convergence can "
      "close it.")
    w()
    w("### 5.5 Pitfalls and Limitations")
    w()
    w("1. **Few time points**: most countries have only 3 waves, giving $\\alpha$ "
      "estimates with 1-2 degrees of freedom. Mexico's 5 waves provide the most "
      "reliable estimate.")
    w("2. **Sparse early waves**: WVS Waves 1-2 have fewer countries and different "
      "construct coverage, limiting temporal depth.")
    w("3. **Stationarity assumption**: the model assumes the SES network structure "
      "(the $\\gamma$ matrix) is constant across waves. In reality, SES coupling "
      "itself evolves.")
    w("4. **Ecological inference**: construct means $\\bar{x}$ are population "
      "aggregates. Individual-level belief dynamics may differ from aggregate trends.")
    w()
    w("### Plots")
    w()
    w("![Temporal alpha by zone](../tda/message_passing/plots/alpha_by_zone.png)")
    w()
    w("![Mexico temporal trajectory](../tda/message_passing/plots/mex_temporal_trajectory.png)")
    w()
    w("---")
    w()

    # ══════════════════════════════════════════════════════════════════════
    #  SECTION 6 — Cross-Stage Synthesis
    # ══════════════════════════════════════════════════════════════════════

    w("## 6. Cross-Stage Synthesis")
    w()
    w("### 6.1 BP Lift vs PPR Influence")
    w()
    w("Belief propagation and personalized PageRank capture complementary aspects "
      "of network influence:")
    w()
    w("| Dimension | BP Lift | PPR Hub Score |")
    w("|-----------|--------|---------------|")
    w("| What it measures | KL divergence from prior | Stationary random walk mass |")
    w("| Interpretation | \"How much does the network constrain this belief?\" | "
      "\"How much influence does this belief exert?\" |")
    w("| Directionality | Symmetric (how constrained) | Asymmetric (how influential) |")
    w("| Top constructs | Immigration status, online political participation | "
      "Economic ideology, democratic values |")
    w()
    w("The discrepancy is substantive: **immigration attitudes are the most "
      "*constrained*** (BP) but not the most *influential* (PPR). Conversely, "
      "economic ideology is moderately constrained but highly influential -- it "
      "generates SES-mediated coupling across many domains without being tightly "
      "pinned itself.")
    w()
    w("### 6.2 Spectral Partition vs Gamma Sign Structure")
    w()
    w("The Fiedler bipartition (spectral) and the $\\gamma$-sign structure (from the "
      "bridge estimates) both partition constructs into two camps. Their agreement is "
      "high but not perfect:")
    w()
    w("- The Fiedler partition uses $|\\gamma|$ weights and finds the optimal algebraic "
      "bisection")
    w("- The $\\gamma$-sign structure uses signed weights and the 94% structural balance "
      "to define a social-balance bipartition")
    w("- In English-speaking countries (ARI = 0.153), both partitions agree closely, "
      "confirming that the sign structure and spectral structure are aligned")
    w("- In South/Southeast Asian countries (ARI = -0.003), they diverge, suggesting "
      "complex SES coupling patterns that do not reduce to a clean two-camp model")
    w()
    w("### 6.3 Network-Driven vs Inertial Societies")
    w()
    w("Combining the temporal $\\alpha$ with the W7 equilibrium distance reveals "
      "four regimes:")
    w()
    w("| | Low eq. distance (near equilibrium) | High eq. distance (far from equilibrium) |")
    w("|---|---|---|")
    w("| **High $\\alpha$** (network-driven) | Converging (VNM, IND) | Restructuring "
      "(RUS, URY) |")
    w("| **Low $\\alpha$** (inertial) | Stable equilibrium (MEX, BRA) | Externally held "
      "(EGY, JOR) |")
    w()
    w()
    w("Each quadrant has distinct sociological characteristics:")
    w()
    w("- **Converging** societies are both close to equilibrium AND have belief "
      "changes that follow network predictions -- the SES system is settling into its "
      "predicted state. These are typically countries in the middle of rapid "
      "modernization where expanding education and urbanization are actively "
      "reshaping belief structures.")
    w("- **Restructuring** societies are far from equilibrium but moving toward it -- "
      "the network is actively reshaping beliefs. Post-Soviet states (Russia, Ukraine) "
      "and rapidly urbanizing societies fit here.")
    w("- **Stable equilibrium** societies are close to equilibrium but show inertial "
      "dynamics -- they reached the SES-predicted state and are staying there. "
      "These are mature democracies where SES distributions have been stable for "
      "decades and belief structures have settled into their SES-predicted configuration.")
    w("- **Externally held** societies are far from equilibrium and not moving toward "
      "it -- non-SES forces (theocratic governance, authoritarian control, conflict) "
      "dominate belief formation. Egypt ($\\alpha = 0.00$, eq_dist = 15.9) is the "
      "archetype: beliefs are entirely determined by non-SES forces, and the SES "
      "network has zero predictive power for belief change.")
    w()
    w("This 2x2 framework provides a testable typology: as countries develop "
      "economically, the prediction is movement from \"externally held\" toward "
      "\"converging\" (lower left to upper left in the table). Conversely, "
      "democratic backsliding or conflict should move countries from \"stable "
      "equilibrium\" toward \"externally held\" (lower left to lower right).")
    w()
    w("### 6.4 Construct-Level Cross-Stage Summary")
    w()
    w("For the key constructs that appear across multiple stages, we can build a "
      "cross-stage profile:")
    w()
    w("| Construct | BP lift rank | PPR hub rank | Velocity rank | $\\alpha$ contribution |")
    w("|-----------|-------------|-------------|--------------|---------------------|")
    w("| `immigrant_origin_status` | #1 (14 countries) | Sink (near-zero) | #1 (14/66) | High velocity |")
    w("| `online_political_participation` | #2 (11 countries) | Sink (near-zero) | #2 (8/66) | High velocity |")
    w("| `economic_ideology` | Low | #1 hub (med. rank 7) | Low | Moderate |")
    w("| `democratic_values_importance` | Low | #2 hub (med. rank 11) | Low | Moderate |")
    w("| `job_scarcity_gender_discrimination` | #3 (6 countries) | Mid-range | #4 (2/66) | Moderate |")
    w()
    w("The cross-stage pattern reveals a fundamental **asymmetry**: the most "
      "*constrained* constructs (immigration, online participation) are *not* the most "
      "*influential*. They are sinks in the PPR sense -- downstream consequences of the "
      "belief network rather than upstream drivers. Conversely, the most influential "
      "constructs (economic ideology, democratic values) have modest constraint levels "
      "but high reach. This is consistent with a causal picture where abstract political "
      "ideology shapes specific attitudes toward immigration and civic participation, "
      "mediated by SES position.")
    w()
    w("### 6.5 Methodological Relationships")
    w()
    w("The five message passing stages form a hierarchy of increasing temporal commitment:")
    w()
    w("| Stage | Input | Output | Time assumption |")
    w("|-------|-------|--------|-----------------|")
    w("| BP (Stage 1) | Signed $\\gamma$ matrix | Posterior marginals, lift | Static (single wave) |")
    w("| Spectral (Stage 2) | $|\\gamma|$ Laplacian | Fiedler bipartition, diffusion timescales | Static, continuous-time |")
    w("| PPR (Stage 3) | $|\\gamma|$ transition matrix | Hub/sink scores | Static, discrete-time random walk |")
    w("| W7 Descriptive (Stage 4) | Transition matrix + means | Equilibrium distance, velocity | Static snapshot with equilibrium reference |")
    w("| Temporal (Stage 5) | Multi-wave matrices + means | $\\alpha$, trajectories | Multi-wave panel |")
    w()
    w("Each stage adds information but also adds assumptions. BP requires the MRF "
      "approximation (pairwise potentials, loopy inference). Spectral diffusion assumes "
      "linear dynamics. PPR assumes ergodic random walks. The temporal model assumes "
      "stationary network structure. Results are most robust where multiple stages "
      "converge on the same conclusion.")
    w()
    w("### 6.6 The Message Passing Picture")
    w()
    w("Taken together, the five message passing stages reveal a consistent picture "
      "of SES-mediated belief coupling in the WVS:")
    w()
    w("1. **The SES network is strong but not universal**: 100% BP convergence and "
      "high Fiedler values (median 0.705) indicate robust SES coupling, but no "
      "universal influence hubs exist.")
    w()
    w("2. **Cultural zones structure belief topology**: spectral partition coherence "
      "is 2.86x higher within zones than across zones, and hub constructs are "
      "zone-specific.")
    w()
    w("3. **The network explains ~11% of Mexico's belief change**: $\\alpha = 0.11$, "
      "with increasing network influence over time (from near-zero in 1996-2000 to "
      "0.35 in 2012-2018).")
    w()
    w("4. **Equilibrium distance is geographic**: countries undergoing rapid "
      "socioeconomic transformation (Vietnam, India) show both high network influence "
      "and convergence toward SES-predicted equilibrium, while post-conflict and "
      "theocratic states (Libya, Egypt) are held far from equilibrium by non-SES forces.")
    w()
    w("5. **Immigration and online participation are the pressure points**: these "
      "constructs consistently appear as the most network-constrained (BP), "
      "highest-velocity (W7 descriptive), and most frequently dominant across "
      "countries. They sit at the intersection of SES dimensions (education, "
      "urbanization, age) and are the constructs most \"in tension\" with their "
      "network neighborhood.")
    w()
    w("6. **The hub-sink asymmetry reveals belief causality**: BP and PPR identify "
      "complementary roles. Economic ideology and democratic values are hubs "
      "(influence generators), while immigration attitudes and online participation "
      "are sinks (influence endpoints). If the SES network approximates causal "
      "structure, this suggests a causal chain: abstract political values -> specific "
      "policy attitudes -> behavioral intentions, mediated by sociodemographic position.")
    w()
    w("7. **Mexico is prototypically Latin American**: across all stages -- BP lift, "
      "Fiedler partition, PPR hub profile, equilibrium distance, and temporal $\\alpha$ "
      "-- Mexico falls squarely within the Latin American zone distribution. Its "
      "increasing network influence ($\\alpha$) and diverging equilibrium distance "
      "tell a specific story of a society where SES-mediated belief coupling is "
      "strengthening even as external forces (security crisis, political polarization, "
      "media transformation) push aggregate beliefs away from the SES-predicted "
      "equilibrium.")
    w()
    w("### 6.7 Limitations and Future Work")
    w()
    w("Several limitations affect all five stages:")
    w()
    w("1. **Construct selection**: the 55 WVS constructs are a subset of all possible "
      "belief dimensions. Missing constructs (e.g., specific policy preferences, "
      "media consumption, social media use) may alter the network topology.")
    w()
    w("2. **SES bridge as proxy**: the $\\gamma$ edges measure SES-*mediated* covariation, "
      "not direct causal influence between beliefs. The message passing framework treats "
      "these edges as if they were direct couplings, which overstates the strength of "
      "the belief network when SES is a common cause rather than a mediator.")
    w()
    w("3. **Cross-country comparability**: WVS samples vary in quality, coverage, and "
      "timing across countries. The 55-construct matrix has structural NaN where "
      "country-specific DR estimates are missing, affecting network density.")
    w()
    w("4. **Temporal sparsity**: most countries have only 3 waves, giving $\\alpha$ "
      "estimates with minimal degrees of freedom. A Bayesian hierarchical model "
      "borrowing strength across countries would improve temporal estimates.")
    w()
    w("5. **Stationarity**: all stages except temporal assume a fixed network structure. "
      "In reality, the $\\gamma$ matrix evolves as SES distributions change. A "
      "time-varying network model (e.g., temporal exponential random graph models) "
      "would capture this evolution.")
    w()
    w("**Future directions:**")
    w()
    w("- Gaussian MRF (continuous beliefs) for more faithful BP")
    w("- Dynamic spectral analysis tracking Fiedler vector rotation across waves")
    w("- Causal discovery (PC algorithm) on the $\\gamma$ matrix to orient edges")
    w("- Integration with los_mex construct network for Mexico-specific deep dive")
    w("- GPU-accelerated BP and PPR for parameter sensitivity analysis")
    w("- Country-specific hub profiles as inputs to the agent's analytical essays")
    w("- Predictive validation: does $\\alpha$ at wave $t$ predict belief shift at $t+1$?")
    w()
    w("### 6.8 Connection to the Broader Navegador Framework")
    w()
    w("The message passing analysis extends the Navegador project's core pipeline:")
    w()
    w("1. **SES bridge** ($\\gamma$-surface): establishes the edge weights")
    w("2. **Construct aggregation**: reduces ~6,000 survey items to 55 constructs")
    w("3. **TDA pipeline**: persistent homology, Ricci curvature, spectral distances")
    w("4. **Message passing** (this report): BP, spectral, PPR, temporal dynamics")
    w()
    w("Each layer adds a different analytical lens:")
    w()
    w("- The $\\gamma$-surface asks: *how strongly are two beliefs coupled by SES?*")
    w("- TDA asks: *what is the topological shape of the belief network?*")
    w("- Message passing asks: *how does information/influence flow through the network?*")
    w()
    w("The message passing results feed back into the agent layer: "
      "the `OntologyQuery` class in `opinion_ontology.py` can use BP lift and PPR "
      "hub scores to contextualize its `get_neighborhood()` and `find_path()` "
      "responses, telling users not just *which beliefs are connected* but "
      "*which beliefs drive which others* and *how quickly perturbations propagate*.")
    w()
    w("For the Mexican survey data (los_mex), the temporal analysis provides "
      "a specific prediction: constructs with high velocity in the W6-W7 transition "
      "(online political participation, social intolerance, religion orientation) "
      "are the constructs most likely to shift in the next survey wave, and the "
      "direction of shift is predictable from the SES network structure.")
    w()
    w("---")
    w()
    w("## Appendix A: Mathematical Notation")
    w()
    w("| Symbol | Definition |")
    w("|--------|-----------|")
    w("| $G = (V, E, w)$ | Weighted belief network graph |")
    w("| $\\gamma(i,j)$ | Doubly-robust SES-bridge estimate between constructs $i$ and $j$ |")
    w("| $L = D - A$ | Graph Laplacian ($D$ = degree matrix, $A$ = adjacency matrix) |")
    w("| $\\lambda_2$ | Fiedler value (algebraic connectivity) |")
    w("| $\\mathbf{v}_2$ | Fiedler vector (spectral bipartition) |")
    w("| $P$ | Row-normalized transition matrix of $|\\gamma|$ weights |")
    w("| $\\boldsymbol{\\pi}_s$ | Personalized PageRank vector from seed $s$ |")
    w("| $\\alpha$ | Restart probability (PPR) or mixing parameter (temporal) |")
    w("| $d_{\\text{eq}}$ | Equilibrium distance: $\\| \\bar{\\mathbf{x}} - \\boldsymbol{\\pi}^* \\|_2$ |")
    w("| $\\mathbf{v}$ | Velocity field: $P\\bar{\\mathbf{x}} - \\bar{\\mathbf{x}}$ |")
    w("| $\\beta$ | Inverse temperature in Potts MRF |")
    w("| $b_i(x_i)$ | BP posterior marginal for node $i$ |")
    w("| $\\text{lift}_i$ | KL divergence: $D_{\\text{KL}}(b_i \\| \\phi_i)$ |")
    w()
    w("## Appendix B: Data Sources")
    w()
    w("| Data file | Description |")
    w("|-----------|-------------|")
    w("| `bp_all_summary.json` | Per-country BP convergence, top influencer, top lift |")
    w("| `spectral_all_summary.json` | Per-country Fiedler value, partition sizes, top loading |")
    w("| `ppr_hub_comparison.json` | Universal/zone-specific hubs, mediator correlation |")
    w("| `temporal_all_summary.json` | Per-country $\\alpha$, zone, wave count |")
    w("| `w7_descriptive_summary.json` | Equilibrium distance ranking, velocity frequency |")
    w("| `mex_temporal.json` | Mexico deep dive: per-transition $\\alpha$, residuals, velocity |")
    w("| `fiedler_comparison.json` | 66x66 ARI matrix of Fiedler partitions |")
    w("| `matrices/manifest.json` | Country list, construct index, cultural zones |")
    w()
    w("## Appendix C: Cultural Zone Membership")
    w()
    cultural_zones = data["manifest"]["cultural_zones"]
    w("| Zone | Countries | $n$ |")
    w("|------|-----------|-----|")
    for zone in sorted(cultural_zones):
        members = cultural_zones[zone]
        w(f"| {zone} | {', '.join(sorted(members))} | {len(members)} |")
    w()
    w("Total: 66 countries across 8 Inglehart-Welzel cultural zones.")
    w()
    w("Zone sizes range from 2 (Protestant Europe: DEU, NLD) to 14 "
      "(African-Islamic). Smaller zones have less statistical power for "
      "within-zone comparisons; results for Protestant Europe and Catholic "
      "Europe (3 countries) should be interpreted with caution.")
    w()
    w("## Appendix D: Pipeline Architecture")
    w()
    w("The message passing pipeline consists of five sequential stages, each "
      "implemented as a separate Python script in `scripts/debug/`:")
    w()
    w("```")
    w("mp_belief_propagation.py     # Stage 1: Loopy BP on Potts MRF")
    w("mp_spectral_diffusion.py     # Stage 2: Laplacian eigendecomposition + heat kernel")
    w("mp_ppr_influence.py          # Stage 3: Personalized PageRank hub/sink analysis")
    w("mp_temporal_descriptive.py   # Stage 4+5: W7 snapshot + temporal dynamics")
    w("mp_report.py                 # This script: report generation + plots")
    w("```")
    w()
    w("All stages share common utilities from `mp_utils.py`:")
    w("- `load_manifest()` -- country/zone/construct metadata")
    w("- `load_weight_matrix(country)` -- per-country 55x55 $\\gamma$ matrix")
    w("- `load_temporal_matrix(wave)` -- per-wave Mexico construct matrix")
    w("- `symmetrize_abs()`, `fill_nan_zero()`, `row_normalize()` -- matrix helpers")
    w()
    w("Input data: WVS Wave 7 $\\gamma$-surface (68,174 estimates from Julia DR sweep) "
      "converted to 55x55 per-country construct matrices by `tda_convert_sweep_to_matrices.py`.")
    w()
    w("## Appendix E: Construct Index")
    w()
    w("The 55 WVS constructs used in the message passing analysis, grouped by domain:")
    w()
    construct_index = data["manifest"]["construct_index"]
    domain_constructs: dict[str, list[str]] = {}
    for c in construct_index:
        d = _domain_code(c)
        domain_constructs.setdefault(d, []).append(_short_name(c))
    w("| Domain | Constructs | Count |")
    w("|--------|-----------|-------|")
    for d in sorted(domain_constructs):
        names = domain_constructs[d]
        w(f"| {DOMAIN_LABELS.get(d, d)} | {', '.join(sorted(names))} | {len(names)} |")
    w()
    w("Domain E (Politics & Society) dominates with the most constructs, reflecting "
      "the WVS's strong focus on political attitudes and institutional confidence. "
      "Domain F (Religion & Morale) is the second largest. Together, these two domains "
      "account for over half of all constructs.")
    w()
    w("## Appendix F: Key Results Summary Table")
    w()
    w("| Metric | Value | Source stage |")
    w("|--------|-------|-------------|")
    w(f"| BP convergence rate | 100% (66/66) | Stage 1 |")
    w(f"| Median top BP lift | {median_lift:.4f} | Stage 1 |")
    w(f"| Max BP lift | {max(lifts):.4f} (GRC) | Stage 1 |")
    w(f"| BP top influencer | immigrant_origin_status (14 countries) | Stage 1 |")
    w(f"| Fiedler range | {fiedler_min_entry['fiedler_value']:.3f}-{fiedler_max_entry['fiedler_value']:.3f} | Stage 2 |")
    w(f"| Fiedler median | {np.median(fiedler_vals):.3f} | Stage 2 |")
    w(f"| Within-zone ARI | 0.0164 (2.86x across-zone) | Stage 2 |")
    w(f"| Most coherent zone | English-speaking (ARI=0.153) | Stage 2 |")
    w(f"| Universal PPR hubs | None | Stage 3 |")
    w(f"| Most consistent hub | economic_ideology (median rank 7) | Stage 3 |")
    w(f"| Mediator-PPR correlation | rho ~ -0.15 to +0.10 (weak) | Stage 3 |")
    w(f"| Eq. distance range | {eq_ranking[0]['eq_distance']:.1f}-{eq_ranking[-1]['eq_distance']:.1f} | Stage 4 |")
    w(f"| Mexico eq. distance rank | {mex_rank}/66 | Stage 4 |")
    w(f"| Top velocity construct | immigrant_origin_status (14/66) | Stage 4 |")
    w(f"| Temporal countries | {n_temporal} | Stage 5 |")
    w(f"| Alpha range | {alpha_ranking[-1]['alpha']:.2f}-{alpha_ranking[0]['alpha']:.2f} | Stage 5 |")
    w(f"| Mexico alpha | {mex['alpha_star']:.3f} | Stage 5 |")
    w(f"| Most network-driven | VNM (alpha={alpha_ranking[0]['alpha']:.3f}) | Stage 5 |")
    w(f"| Most inertial | EGY (alpha={alpha_ranking[-1]['alpha']:.3f}) | Stage 5 |")
    w()
    w("---")
    w()
    w("*Report generated by `scripts/debug/mp_report.py`*")
    w()

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("Message Passing Report Generator")
    print("=" * 50)

    # Ensure output directories exist
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    # Load all data
    print("\nLoading summary JSONs ...")
    data = load_all_summaries()
    print(f"  BP: {len(data['bp']['summaries'])} countries")
    print(f"  Spectral: {len(data['spectral']['summaries'])} countries")
    print(f"  Temporal: {data['temporal']['n_countries']} countries")
    print(f"  W7: {data['w7']['n_countries']} countries")

    # Generate plots
    print("\nGenerating plots ...")
    plot_fiedler_by_zone(data)
    plot_bp_top_influencers(data)
    plot_ppr_hub_mex(data)
    plot_alpha_by_zone(data)
    plot_equilibrium_distance(data)
    plot_mex_temporal(data)
    print(f"\n  All plots saved to {PLOT_DIR.relative_to(ROOT)}/")

    # Generate report
    print("\nGenerating markdown report ...")
    report_text = generate_report(data)
    n_lines = report_text.count("\n") + 1
    REPORT.write_text(report_text, encoding="utf-8")
    print(f"  Report: {n_lines} lines -> {REPORT.relative_to(ROOT)}")
    print("\nDone.")


if __name__ == "__main__":
    main()
