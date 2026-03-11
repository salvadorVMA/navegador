"""
Plot construct network from DR sweep results.

Shows constructs as nodes and significant γ links as edges,
with three CI-based significance tiers:
  - Tier 1 (p < 0.01 proxy): CI entirely excludes zero by wide margin
  - Tier 2 (p < 0.025): CI excludes zero
  - Tier 3 (p < 0.05 proxy): CI nearly excludes zero (within 5% of width)

Usage:
    python scripts/debug/plot_construct_network.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SWEEP_PATH = ROOT / "data" / "results" / "construct_dr_sweep.json"
MANIFEST_PATH = ROOT / "data" / "results" / "construct_variable_manifest.json"
OUTPUT_PATH = ROOT / "data" / "results" / "construct_network.png"


# Domain color palette (24 domains)
DOMAIN_COLORS = {
    "CIE": "#1f77b4", "COR": "#ff7f0e", "CUL": "#2ca02c", "DEP": "#d62728",
    "DER": "#9467bd", "ECO": "#8c564b", "EDU": "#e377c2", "ENV": "#7f7f7f",
    "FAM": "#bcbd22", "FED": "#17becf", "GEN": "#aec7e8", "GLO": "#ffbb78",
    "HAB": "#98df8a", "IDE": "#ff9896", "IND": "#c5b0d5", "JUS": "#c49c94",
    "MED": "#f7b6d2", "MIG": "#c7c7c7", "NIN": "#dbdb8d", "POB": "#9edae5",
    "REL": "#e41a1c", "SAL": "#377eb8", "SEG": "#4daf4a", "SOC": "#984ea3",
}


def classify_edge(gamma: float, ci: list) -> str | None:
    """Classify edge by CI-based significance tier."""
    ci_lo, ci_hi = ci
    ci_width = ci_hi - ci_lo

    # Tier 1: CI excludes zero (strict)
    if ci_lo > 0 or ci_hi < 0:
        # Sub-classify: how far from zero relative to CI width?
        if gamma > 0:
            margin = ci_lo / ci_width  # fraction of CI above zero
        else:
            margin = -ci_hi / ci_width
        if margin > 0.15:
            return "tier1"  # strong exclusion
        return "tier2"  # just excludes zero

    # Tier 3: nearly excludes zero (within 5% of CI width)
    if gamma > 0:
        gap = -ci_lo  # how far below zero the lower bound is
    else:
        gap = ci_hi   # how far above zero the upper bound is

    if gap <= 0.05 * ci_width:
        return "tier3"

    return None  # not significant


def short_name(construct_key: str) -> str:
    """Shorten construct name for display."""
    parts = construct_key.split("|")
    domain = parts[0]
    name = parts[1] if len(parts) > 1 else parts[0]
    # Abbreviate long names
    name = (name
            .replace("_and_", "&")
            .replace("_or_", "/")
            .replace("institutional_", "inst_")
            .replace("employment_", "empl_")
            .replace("participation_", "partic_")
            .replace("engagement_", "engag_")
            .replace("socialization", "social.")
            .replace("perception", "percep.")
            .replace("preferences", "pref.")
            .replace("satisfaction", "satisf.")
            .replace("evaluation", "eval.")
            .replace("discrimination", "discrim.")
            .replace("vulnerability", "vulner.")
            .replace("victimization", "victim.")
            .replace("reproductive", "reprod.")
            .replace("technology", "tech.")
            .replace("environmental", "environ.")
            .replace("preparation", "prep.")
            )
    # Truncate if still long
    if len(name) > 28:
        name = name[:26] + ".."
    return f"{domain}|{name}"


def main():
    # Load data
    with open(SWEEP_PATH) as f:
        sweep = json.load(f)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    estimates = sweep["estimates"]

    # Build graph
    G = nx.Graph()

    # Collect all constructs that appear in significant edges
    edges_by_tier = {"tier1": [], "tier2": [], "tier3": []}

    for pair_id, est in estimates.items():
        if "dr_gamma" not in est:
            continue
        gamma = est["dr_gamma"]
        ci = est.get("dr_gamma_ci")
        if not ci:
            continue

        tier = classify_edge(gamma, ci)
        if tier is None:
            continue

        ca = est["construct_a"]
        cb = est["construct_b"]
        edges_by_tier[tier].append((ca, cb, gamma, ci))

    # Add nodes and edges
    for tier, edges in edges_by_tier.items():
        for ca, cb, gamma, ci in edges:
            da = ca.split("|")[0]
            db = cb.split("|")[0]
            G.add_node(ca, domain=da)
            G.add_node(cb, domain=db)
            G.add_edge(ca, cb, gamma=gamma, ci=ci, tier=tier)

    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    for tier in ["tier1", "tier2", "tier3"]:
        print(f"  {tier}: {len(edges_by_tier[tier])} edges")

    # Layout
    pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42)

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(22, 18))
    ax.set_facecolor("#fafafa")

    # Draw edges by tier (back to front: tier3 first, tier1 last)
    tier_styles = {
        "tier3": {"alpha": 0.15, "width": 0.6, "style": "dotted",  "label": "Near-significant (5% from CI boundary)"},
        "tier2": {"alpha": 0.35, "width": 1.2, "style": "dashed",  "label": "Significant (CI excludes zero)"},
        "tier1": {"alpha": 0.70, "width": 2.5, "style": "solid",   "label": "Strongly significant (CI well past zero)"},
    }

    for tier in ["tier3", "tier2", "tier1"]:
        style = tier_styles[tier]
        tier_edges = [(u, v) for u, v, d in G.edges(data=True) if d["tier"] == tier]
        if not tier_edges:
            continue

        # Color by sign of gamma
        edge_colors = []
        for u, v in tier_edges:
            g = G[u][v]["gamma"]
            if g > 0:
                edge_colors.append("#2166ac")  # blue = positive
            else:
                edge_colors.append("#b2182b")  # red = negative

        nx.draw_networkx_edges(
            G, pos, edgelist=tier_edges,
            edge_color=edge_colors,
            alpha=style["alpha"],
            width=style["width"],
            style=style["style"],
            ax=ax)

    # Draw nodes
    node_colors = [DOMAIN_COLORS.get(G.nodes[n]["domain"], "#999999") for n in G.nodes()]
    node_sizes = []
    for n in G.nodes():
        degree = G.degree(n)
        node_sizes.append(200 + 40 * degree)

    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.85,
        edgecolors="white",
        linewidths=1.0,
        ax=ax)

    # Labels
    labels = {n: short_name(n) for n in G.nodes()}
    nx.draw_networkx_labels(
        G, pos, labels,
        font_size=6,
        font_weight="bold",
        ax=ax)

    # Legend - tiers
    legend_handles = []
    for tier in ["tier1", "tier2", "tier3"]:
        style = tier_styles[tier]
        legend_handles.append(
            mpatches.Patch(color="#555555", alpha=style["alpha"],
                           label=style["label"]))
    legend_handles.append(
        mpatches.Patch(color="#2166ac", label="Positive γ (concordant)"))
    legend_handles.append(
        mpatches.Patch(color="#b2182b", label="Negative γ (discordant)"))

    # Add domain color legend
    domains_in_graph = sorted(set(G.nodes[n]["domain"] for n in G.nodes()))
    for dom in domains_in_graph:
        legend_handles.append(
            mpatches.Patch(color=DOMAIN_COLORS.get(dom, "#999"),
                           label=f"{dom}", alpha=0.85))

    ax.legend(handles=legend_handles, loc="upper left", fontsize=7,
              ncol=2, framealpha=0.9)

    n_total = sweep["metadata"]["n_total_pairs"]
    n_sig = len(edges_by_tier["tier1"]) + len(edges_by_tier["tier2"])
    n_near = len(edges_by_tier["tier3"])

    ax.set_title(
        f"Construct Network — SES-Mediated γ Links\n"
        f"{G.number_of_nodes()} constructs, {n_sig} significant + {n_near} near-significant edges "
        f"(of {n_total} pairs tested)\n"
        f"DR estimator: n_sim=2000, n_bootstrap=200, SES=[sexo, edad, escol, Tam_loc]",
        fontsize=13, fontweight="bold", pad=15)

    ax.axis("off")
    plt.tight_layout()
    fig.savefig(str(OUTPUT_PATH), dpi=180, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"\nSaved: {OUTPUT_PATH}")
    plt.close()

    # Print edge summary
    print(f"\n{'='*70}")
    print("TIER 1 — Strongly significant edges:")
    print(f"{'='*70}")
    t1 = sorted(edges_by_tier["tier1"], key=lambda x: -abs(x[2]))
    for ca, cb, gamma, ci in t1:
        print(f"  γ={gamma:+.4f} CI=[{ci[0]:+.4f},{ci[1]:+.4f}] | {ca} × {cb}")

    print(f"\n{'='*70}")
    print("TIER 2 — Significant edges (CI just excludes zero):")
    print(f"{'='*70}")
    t2 = sorted(edges_by_tier["tier2"], key=lambda x: -abs(x[2]))
    for ca, cb, gamma, ci in t2:
        print(f"  γ={gamma:+.4f} CI=[{ci[0]:+.4f},{ci[1]:+.4f}] | {ca} × {cb}")

    print(f"\n{'='*70}")
    print("TIER 3 — Near-significant edges:")
    print(f"{'='*70}")
    t3 = sorted(edges_by_tier["tier3"], key=lambda x: -abs(x[2]))
    for ca, cb, gamma, ci in t3[:30]:  # show top 30
        print(f"  γ={gamma:+.4f} CI=[{ci[0]:+.4f},{ci[1]:+.4f}] | {ca} × {cb}")
    if len(t3) > 30:
        print(f"  ... and {len(t3)-30} more")


if __name__ == "__main__":
    main()
