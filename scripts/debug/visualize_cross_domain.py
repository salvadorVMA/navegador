"""
visualize_cross_domain.py — Unified cross-domain construct graph visualization.

Merges KG ontology (domain boundaries, constructs, LLM-proposed links) with
empirical bivariate evidence (SES bridge simulation Cramér's V estimates)
into a 4-panel figure.

  Panel A — Domain Association Heatmap (24×24)
  Panel B — Cross-Domain Construct Network
  Panel C — Evidence Convergence Table
  Panel D — Top-20 Strongest Pairs Bar Chart

Usage:
    python scripts/debug/visualize_cross_domain.py
    python scripts/debug/visualize_cross_domain.py --sweep /path/to/sweep.json --ontology /path/to/kg_ontology.json

Inputs:
  - data/kg_ontology.json          (KG ontology from knowledge-graph branch)
  - data/cross_domain_sweep.json   (bivariate sweep results)

Output:
  - scripts/debug/cross_domain_network.png
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY = ROOT / "data" / "kg_ontology.json"
DEFAULT_SWEEP = ROOT / "data" / "cross_domain_sweep.json"
OUTPUT = Path(__file__).resolve().parent / "cross_domain_network.png"


# ── Load data ──────────────────────────────────────────────────────────────

def load_ontology(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_sweep(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── Colour palettes ───────────────────────────────────────────────────────

def domain_colours(domain_ids):
    cmap = plt.get_cmap("tab20")
    cmap2 = plt.get_cmap("tab20b")
    colours = [cmap(i % 20) for i in range(20)] + [cmap2(i % 20) for i in range(10)]
    return {d: colours[i] for i, d in enumerate(sorted(domain_ids))}

RTYPE_COLOUR = {
    "predicts":          "#e74c3c",
    "influences":        "#e67e22",
    "correlates_with":   "#3498db",
    "is_part_of":        "#27ae60",
    "enables":           "#9b59b6",
    "negatively_affects":"#1abc9c",
}

STATUS_COLOUR = {
    "CONFIRMED":    "#27ae60",
    "KG ONLY":      "#3498db",
    "DATA ONLY":    "#e67e22",
    "CONTRADICTED": "#e74c3c",
    "TOP UNLINKED": "#8e44ad",
}


# ── Analysis helpers ───────────────────────────────────────────────────────

def get_kg_cross_domain_links(ontology: dict) -> Dict[Tuple[str,str], dict]:
    """Extract KG-proposed cross-domain links as {(domA, domB): relationship_info}."""
    cdom = {c["id"]: c["domain"] for c in ontology["constructs"]}
    links = {}
    for r in ontology["relationships"]:
        d_from = cdom.get(r["from"], "?")
        d_to = cdom.get(r["to"], "?")
        if d_from != d_to and d_from != "?" and d_to != "?":
            pair = tuple(sorted([d_from, d_to]))
            links[pair] = {
                "type": r["type"],
                "from_construct": r["from"],
                "to_construct": r["to"],
                "strength": r.get("strength", ""),
                "evidence": r.get("evidence", ""),
            }
    return links


def get_sweep_domain_pairs(sweep: dict) -> Dict[Tuple[str,str], dict]:
    """Extract sweep results as {(domA, domB): pair_summary}."""
    pairs = {}
    for key, data in sweep.get("domain_pairs", {}).items():
        da, db = data["domain_a"], data["domain_b"]
        pair = tuple(sorted([da, db]))
        pairs[pair] = data
    return pairs


def build_convergence_status(
    kg_links: Dict[Tuple[str,str], dict],
    sweep_pairs: Dict[Tuple[str,str], dict],
    v_threshold: float = 0.08,
) -> List[dict]:
    """Classify each evidence pair into a convergence status."""
    all_pairs = sorted(set(kg_links.keys()) | set(sweep_pairs.keys()))
    rows = []
    for pair in all_pairs:
        has_kg = pair in kg_links
        has_data = pair in sweep_pairs and sweep_pairs[pair].get("mean_v") is not None

        mean_v = sweep_pairs[pair]["mean_v"] if has_data else None
        max_v = sweep_pairs[pair]["max_v"] if has_data else None
        n_sig = sweep_pairs[pair]["n_significant"] if has_data else 0
        n_total = sweep_pairs[pair]["n_total"] if has_data else 0
        kg_type = kg_links[pair]["type"] if has_kg else None

        if has_kg and has_data:
            if mean_v >= v_threshold and n_sig > 0:
                status = "CONFIRMED"
            else:
                status = "CONTRADICTED"
        elif has_kg:
            status = "KG ONLY"
        else:
            status = "DATA ONLY"

        rows.append({
            "pair": pair,
            "domain_a": pair[0],
            "domain_b": pair[1],
            "has_kg": has_kg,
            "kg_type": kg_type,
            "has_data": has_data,
            "mean_v": mean_v,
            "max_v": max_v,
            "n_sig": n_sig,
            "n_total": n_total,
            "status": status,
        })

    return rows


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel A — Domain Association Heatmap                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def draw_heatmap(ax, domains, sweep_pairs, kg_links, c_per_domain, domain_label):
    n = len(domains)
    matrix = np.full((n, n), np.nan)
    idx = {d: i for i, d in enumerate(domains)}

    # Fill with mean Cramér's V
    for (da, db), data in sweep_pairs.items():
        if da in idx and db in idx and data.get("mean_v") is not None:
            i, j = idx[da], idx[db]
            matrix[i, j] = data["mean_v"]
            matrix[j, i] = data["mean_v"]

    # Diagonal: zero (coloured separately)
    for d in domains:
        i = idx[d]
        matrix[i, i] = 0

    # Mask NaN for colourmap
    masked = np.ma.masked_invalid(matrix)
    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("#f0f0f0")

    im = ax.imshow(masked, cmap=cmap, vmin=0, vmax=0.25, aspect="equal",
                   interpolation="nearest")

    # Diagonal overlay — blue shading for construct count
    max_c = max(c_per_domain.values()) if c_per_domain else 1
    for d in domains:
        i = idx[d]
        c = c_per_domain.get(d, 0)
        intensity = min(1.0, c / max_c)
        rect = mpatches.Rectangle(
            (i - 0.5, i - 0.5), 1, 1,
            facecolor=(0.2, 0.4, 0.8, 0.15 + 0.55 * intensity),
            edgecolor="none", zorder=2,
        )
        ax.add_patch(rect)
        ax.text(i, i, str(c), ha="center", va="center",
                fontsize=5, color="white" if intensity > 0.5 else "#2c3e50",
                fontweight="bold", zorder=3)

    # Annotate off-diagonal cells with V values
    for (da, db), data in sweep_pairs.items():
        if da in idx and db in idx and data.get("mean_v") is not None:
            i, j = idx[da], idx[db]
            v = data["mean_v"]
            if v >= 0.05:
                colour = "white" if v > 0.15 else "#333333"
                txt = f"{v:.2f}"[1:]  # e.g. ".09"
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=3.8, color=colour, zorder=3)
                ax.text(i, j, txt, ha="center", va="center",
                        fontsize=3.8, color=colour, zorder=3)

    # Diamond markers for KG-proposed links
    for (da, db), info in kg_links.items():
        if da in idx and db in idx:
            i, j = idx[da], idx[db]
            ax.plot(j, i, marker="D", markersize=7, markerfacecolor="none",
                    markeredgecolor="#2c3e50", markeredgewidth=1.5, zorder=4)
            ax.plot(i, j, marker="D", markersize=7, markerfacecolor="none",
                    markeredgecolor="#2c3e50", markeredgewidth=1.5, zorder=4)

    # Axis labels
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(domains, fontsize=5.5, rotation=90)
    ax.set_yticklabels(domains, fontsize=5.5)
    ax.tick_params(length=0)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("Mean Cramér's V", fontsize=7)
    cbar.ax.tick_params(labelsize=6)

    # Legend
    diamond = mlines.Line2D([], [], marker="D", markersize=6, markerfacecolor="none",
                             markeredgecolor="#2c3e50", markeredgewidth=1.5,
                             linestyle="none", label="KG-proposed link")
    gray_patch = mpatches.Patch(facecolor="#f0f0f0", edgecolor="#cccccc", label="Not estimated")
    ax.legend(handles=[diamond, gray_patch], loc="lower left", fontsize=5.5,
              framealpha=0.9)

    ax.set_title("A — Domain Association Heatmap\n(cell = mean V; ◆ = KG link; diagonal = construct count)",
                 fontsize=9, pad=8, fontweight="bold")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel B — Cross-Domain Construct Network                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def draw_construct_network(ax, ontology, sweep_pairs, kg_links, d_colours):
    cdom = {c["id"]: c["domain"] for c in ontology["constructs"]}
    c_label = {c["id"]: c["label"] for c in ontology["constructs"]}
    q_to_c = {q["id"]: q["construct"] for q in ontology["questions"]}

    # Build edges from empirical data (variable -> construct -> aggregate)
    empirical_edges: Dict[Tuple[str,str], List[float]] = defaultdict(list)
    for (da, db), data in sweep_pairs.items():
        if data.get("mean_v") is None:
            continue
        for est in data.get("estimates", []):
            if "cramers_v" not in est:
                continue
            ca = q_to_c.get(est["var_a"])
            cb = q_to_c.get(est["var_b"])
            if ca and cb and ca != cb:
                edge_key = tuple(sorted([ca, cb]))
                empirical_edges[edge_key].append(est["cramers_v"])

    # Build edges from KG
    kg_edges = {}
    for (da, db), info in kg_links.items():
        fc = info["from_construct"]
        tc = info["to_construct"]
        if fc and tc:
            edge_key = tuple(sorted([fc, tc]))
            kg_edges[edge_key] = info["type"]

    # Collect top edges (top 40 by mean V + all KG edges)
    top_empirical = sorted(empirical_edges.items(),
                           key=lambda x: -np.mean(x[1]))[:40]
    top_emp_keys = {k for k, _ in top_empirical}

    involved = set()
    for ca, cb in top_emp_keys | set(kg_edges.keys()):
        if ca in cdom and cb in cdom:
            involved.add(ca)
            involved.add(cb)

    if not involved:
        ax.text(0.5, 0.5, "No cross-domain construct edges found",
                transform=ax.transAxes, ha="center", fontsize=10)
        ax.axis("off")
        return

    G = nx.Graph()
    for c in involved:
        G.add_node(c, domain=cdom.get(c, "?"))

    # Empirical edges
    for (ca, cb), vs in top_empirical:
        if ca in G and cb in G:
            G.add_edge(ca, cb, source="empirical", mean_v=float(np.mean(vs)),
                       n_pairs=len(vs))

    # KG edges
    for (ca, cb), rtype in kg_edges.items():
        if ca in G and cb in G:
            if G.has_edge(ca, cb):
                G.edges[ca, cb]["kg_type"] = rtype
                G.edges[ca, cb]["source"] = "both"
            else:
                G.add_edge(ca, cb, source="kg", kg_type=rtype, mean_v=0)

    if not G.nodes:
        ax.text(0.5, 0.5, "No constructs to display",
                transform=ax.transAxes, ha="center", fontsize=10)
        ax.axis("off")
        return

    pos = nx.kamada_kawai_layout(G, weight=None)

    node_list = list(G.nodes)
    node_colors = [d_colours.get(G.nodes[n].get("domain", ""), (0.7, 0.7, 0.7, 1))
                   for n in node_list]
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=node_list,
                           node_color=node_colors, node_size=50, alpha=0.85)

    for u, v, edata in G.edges(data=True):
        src = edata.get("source", "empirical")
        mean_v = edata.get("mean_v", 0)
        x_vals = [pos[u][0], pos[v][0]]
        y_vals = [pos[u][1], pos[v][1]]

        if src == "both":
            ax.plot(x_vals, y_vals, color="#27ae60", linewidth=1.5 + 8 * mean_v,
                    alpha=0.8, zorder=1, solid_capstyle="round")
        elif src == "kg":
            colour = RTYPE_COLOUR.get(edata.get("kg_type", ""), "#3498db")
            ax.plot(x_vals, y_vals, color=colour, linewidth=1.2,
                    linestyle="dashed", alpha=0.7, zorder=1)
        else:
            ax.plot(x_vals, y_vals, color="#e67e22",
                    linewidth=0.5 + 6 * mean_v, alpha=0.5, zorder=1)

    labels = {}
    for n in node_list:
        lbl = c_label.get(n, n)
        if "__" in lbl:
            lbl = lbl.split("__", 1)[-1]
        lbl = lbl.replace("_", " ")
        labels[n] = lbl[:16] + "…" if len(lbl) > 16 else lbl
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=4, font_color="#222222")

    legend_items = [
        mlines.Line2D([], [], color="#27ae60", linewidth=2, label="Confirmed (KG + data)"),
        mlines.Line2D([], [], color="#e67e22", linewidth=1.5, label="Data only"),
        mlines.Line2D([], [], color="#3498db", linewidth=1.2, linestyle="dashed",
                      label="KG only"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=5.5,
              framealpha=0.9, title="Edge source", title_fontsize=5.5)

    ax.set_title("B — Cross-Domain Construct Network\n(top 40 empirical edges + all KG edges; width ∝ V)",
                 fontsize=9, pad=8, fontweight="bold")
    ax.axis("off")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel C — Evidence Convergence Table                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def draw_convergence_table(ax, convergence_rows, domain_label):
    order = {"CONFIRMED": 0, "CONTRADICTED": 1, "KG ONLY": 2, "DATA ONLY": 3}
    rows = sorted(convergence_rows,
                  key=lambda r: (order.get(r["status"], 9), -(r["mean_v"] or 0)))

    kg_rows = [r for r in rows if r["has_kg"]]
    data_rows = sorted([r for r in rows if not r["has_kg"] and r["has_data"]],
                        key=lambda r: -(r["mean_v"] or 0))[:15]
    display_rows = kg_rows + data_rows

    col_labels = ["Domain A", "Domain B", "Status", "KG Type", "Mean V", "Max V", "Sig/Total"]
    cell_data = []
    cell_colours = []

    for r in display_rows:
        da_lbl = r["domain_a"]
        db_lbl = r["domain_b"]
        status = r["status"]
        kg_type = r.get("kg_type") or "—"
        mean_v = f"{r['mean_v']:.3f}" if r["mean_v"] is not None else "—"
        max_v = f"{r['max_v']:.3f}" if r["max_v"] is not None else "—"
        sig = f"{r['n_sig']}/{r['n_total']}" if r["n_total"] else "—"

        cell_data.append([da_lbl, db_lbl, status, kg_type, mean_v, max_v, sig])

        sc = STATUS_COLOUR.get(status, "#cccccc")
        rgb = mcolors.to_rgb(sc)
        light = tuple(min(1.0, c + 0.55) for c in rgb)
        cell_colours.append(["white", "white", light, "white", "white", "white", "white"])

    if not cell_data:
        ax.text(0.5, 0.5, "No convergence data", transform=ax.transAxes, ha="center")
        ax.axis("off")
        return

    table = ax.table(
        cellText=cell_data,
        colLabels=col_labels,
        cellColours=cell_colours,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(6)
    table.scale(1, 1.15)

    for j in range(len(col_labels)):
        table[0, j].set_facecolor("#2c3e50")
        table[0, j].set_text_props(color="white", fontweight="bold")

    legend_patches = [
        mpatches.Patch(facecolor=STATUS_COLOUR[s], label=s, alpha=0.85)
        for s in ["CONFIRMED", "CONTRADICTED", "KG ONLY", "DATA ONLY"]
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=5.5,
              framealpha=0.9, ncol=2, title="Status", title_fontsize=5.5)

    ax.axis("off")
    ax.set_title("C — Evidence Convergence\n(all KG links + top 15 data-only pairs by V)",
                 fontsize=9, pad=8, fontweight="bold")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel D — Top-20 Strongest Pairs Bar Chart                             ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def draw_top_pairs_chart(ax, sweep_pairs, kg_links, domain_label):
    ranked = sorted(
        [(pair, data) for pair, data in sweep_pairs.items()
         if data.get("mean_v") is not None],
        key=lambda x: -x[1]["mean_v"]
    )[:20]

    if not ranked:
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center")
        ax.axis("off")
        return

    labels = []
    values = []
    colours = []
    for pair, data in reversed(ranked):
        da, db = pair
        labels.append(f"{da} × {db}")
        values.append(data["mean_v"])
        has_kg = pair in kg_links
        colours.append("#27ae60" if has_kg else "#e67e22")

    y_pos = range(len(labels))
    bars = ax.barh(y_pos, values, color=colours, edgecolor="white", linewidth=0.5, height=0.7)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.003, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=6.5, color="#333333")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.set_xlabel("Mean Cramér's V", fontsize=8)
    ax.set_xlim(0, max(values) * 1.25 if values else 0.3)
    ax.tick_params(axis="x", labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)

    legend_items = [
        mpatches.Patch(facecolor="#27ae60", label="KG link confirmed"),
        mpatches.Patch(facecolor="#e67e22", label="Empirical only (no KG link)"),
    ]
    ax.legend(handles=legend_items, loc="lower right", fontsize=6,
              framealpha=0.9)

    ax.axvline(x=0.10, color="#999999", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.text(0.10, len(labels) - 0.3, "  weak", fontsize=5, color="#999999")
    ax.axvline(x=0.20, color="#999999", linestyle=":", linewidth=0.8, alpha=0.6)
    ax.text(0.20, len(labels) - 0.3, "  moderate", fontsize=5, color="#999999")

    ax.set_title("D — Top 20 Strongest Domain Pairs\n(green = KG link exists; orange = data only)",
                 fontsize=9, pad=8, fontweight="bold")


# ── Main ───────────────────────────────────────────────────────────────────

def main(ontology_path: Path, sweep_path: Path) -> None:
    print(f"Loading ontology from {ontology_path} …")
    ontology = load_ontology(ontology_path)

    print(f"Loading sweep from {sweep_path} …")
    sweep = load_sweep(sweep_path)

    domain_label = {d["id"]: d["label"] for d in ontology["domains"]}
    c_per_domain = Counter(c["domain"] for c in ontology["constructs"])
    domains = sorted(d["id"] for d in ontology["domains"]
                     if d["id"] not in ("JUE", "CON"))

    d_colours = domain_colours(domains)

    kg_links = get_kg_cross_domain_links(ontology)
    sweep_pairs = get_sweep_domain_pairs(sweep)
    convergence = build_convergence_status(kg_links, sweep_pairs)

    # ── Figure layout ──────────────────────────────────────────────────
    fig = plt.figure(figsize=(22, 24), facecolor="#fafafa")

    meta = sweep.get("metadata", {})
    fig.suptitle(
        "Cross-Domain Association Landscape — los_mex Survey\n"
        f"{meta.get('n_domains', '?')} domains · "
        f"{meta.get('n_pairs_with_results', '?')}/{meta.get('n_pairs_attempted', '?')} pairs estimated · "
        f"{meta.get('n_estimates_total', '?')} bivariate estimates · "
        f"{len(kg_links)} KG-proposed links",
        fontsize=14, fontweight="bold", color="#2c3e50", y=0.985,
    )

    gs = fig.add_gridspec(
        2, 2,
        width_ratios=[1.1, 0.9],
        height_ratios=[1.0, 1.0],
        hspace=0.12,
        wspace=0.10,
        left=0.04, right=0.96,
        top=0.95, bottom=0.03,
    )

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    print("Drawing heatmap …")
    draw_heatmap(ax_a, domains, sweep_pairs, kg_links, c_per_domain, domain_label)

    print("Drawing construct network …")
    draw_construct_network(ax_b, ontology, sweep_pairs, kg_links, d_colours)

    print("Drawing convergence table …")
    draw_convergence_table(ax_c, convergence, domain_label)

    print("Drawing top pairs chart …")
    draw_top_pairs_chart(ax_d, sweep_pairs, kg_links, domain_label)

    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"\n✅  Saved to {OUTPUT}")

    # ── Text summary ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("CROSS-DOMAIN ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"  Sweep: {meta.get('n_pairs_with_results')}/{meta.get('n_pairs_attempted')} pairs, "
          f"{meta.get('n_estimates_total')} estimates in {meta.get('elapsed_seconds', '?')}s")

    statuses = Counter(r["status"] for r in convergence)
    print(f"\n  Convergence status:")
    for s in ["CONFIRMED", "CONTRADICTED", "KG ONLY", "DATA ONLY"]:
        print(f"    {s:<15} {statuses.get(s, 0)}")

    ranked = sorted(
        [(p, d) for p, d in sweep_pairs.items() if d.get("mean_v") is not None],
        key=lambda x: -x[1]["mean_v"]
    )
    print(f"\n  Top 10 strongest domain pairs:")
    for pair, data in ranked[:10]:
        da, db = pair
        kg_tag = " [KG]" if pair in kg_links else ""
        print(f"    {da} × {db}: V={data['mean_v']:.3f}  "
              f"(max={data['max_v']:.3f}, sig={data['n_significant']}/{data['n_total']})"
              f"{kg_tag}")

    print(f"\n  Bottom 5 weakest:")
    for pair, data in ranked[-5:]:
        da, db = pair
        print(f"    {da} × {db}: V={data['mean_v']:.3f}")

    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-domain construct graph visualization")
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY,
                        help="Path to kg_ontology.json")
    parser.add_argument("--sweep", type=Path, default=DEFAULT_SWEEP,
                        help="Path to cross_domain_sweep.json")
    args = parser.parse_args()
    main(args.ontology, args.sweep)
