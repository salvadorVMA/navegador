"""
visualize_kg.py — Visual display of the Survey Knowledge Graph ontology.

Generates a multi-panel figure showing:
  Panel A — Domain network: 26 survey domains as bubbles sized by question
             count, cross-domain edges coloured by relationship type.
  Panel B — Intra-domain construct web: for the 6 most construct-rich
             domains, shows constructs as nodes and their relationships.
  Panel C — Relationship-type breakdown (horizontal bar chart).
  Panel D — Domain statistics table (questions / constructs per domain).

Usage:
    python scripts/debug/visualize_kg.py
    # Reads data/kg_ontology.json (works on feature/knowledge-graph branch
    # or wherever the ontology file exists). Writes kg_network.png to the
    # same directory as this script.

    Optionally pass a path to the ontology:
    python scripts/debug/visualize_kg.py /path/to/kg_ontology.json
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import networkx as nx
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY = ROOT / "data" / "kg_ontology.json"
OUTPUT = Path(__file__).resolve().parent / "kg_network.png"

def load_ontology(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ── Colour palette ─────────────────────────────────────────────────────────
# 26 domains → assign from a qualitative colourmap
def domain_colours(domain_ids):
    cmap = plt.get_cmap("tab20")
    cmap2 = plt.get_cmap("tab20b")
    colours = [cmap(i % 20) for i in range(20)] + [cmap2(i % 20) for i in range(6)]
    return {d: colours[i] for i, d in enumerate(domain_ids)}

RTYPE_COLOUR = {
    "predicts":          "#e74c3c",
    "influences":        "#e67e22",
    "correlates_with":   "#3498db",
    "is_part_of":        "#27ae60",
    "enables":           "#9b59b6",
    "negatively_affects":"#1abc9c",
}

# ── Build NetworkX graph from ontology dict ────────────────────────────────
def build_graph(data: dict) -> nx.DiGraph:
    G = nx.DiGraph()
    for d in data["domains"]:
        G.add_node(d["id"], node_type="domain", label=d["label"])
    for c in data["constructs"]:
        G.add_node(c["id"], node_type="construct", label=c["label"], domain=c["domain"])
        G.add_edge(c["id"], c["domain"], relation="belongs_to_domain")
    for q in data["questions"]:
        G.add_node(q["id"], node_type="question",
                   text=q.get("text", ""), domain=q.get("construct", "").split("__")[0])
        G.add_edge(q["id"], q["construct"], relation="measures")
    for r in data["relationships"]:
        G.add_edge(r["from"], r["to"],
                   relation=r["type"],
                   evidence=r.get("evidence"),
                   strength=r.get("strength"))
    return G

# ── Aggregate stats ────────────────────────────────────────────────────────
def compute_stats(data: dict):
    cdom = {c["id"]: c["domain"] for c in data["constructs"]}
    q_per_domain  = Counter(cdom.get(q["construct"], "?") for q in data["questions"])
    c_per_domain  = Counter(c["domain"] for c in data["constructs"])
    rels          = data["relationships"]
    rtype_counts  = Counter(r["type"] for r in rels)

    cross, intra  = [], []
    for r in rels:
        d_from = cdom.get(r["from"], "?")
        d_to   = cdom.get(r["to"],   "?")
        (cross if d_from != d_to else intra).append(r)

    return q_per_domain, c_per_domain, rtype_counts, cross, intra, cdom

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel A — Domain bubble network                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def draw_domain_network(ax, data, q_per_domain, c_per_domain, d_colours, cross_rels, cdom):
    domain_ids = [d["id"] for d in data["domains"]]
    domain_label = {d["id"]: d["label"] for d in data["domains"]}

    # Circular layout for domains
    n = len(domain_ids)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    # nudge a few to reduce label overlap
    pos = {d: (np.cos(a), np.sin(a)) for d, a in zip(domain_ids, angles)}

    # Draw cross-domain edges first (under bubbles)
    drawn_pairs = set()
    for r in cross_rels:
        d_from = cdom.get(r["from"], "?")
        d_to   = cdom.get(r["to"],   "?")
        if d_from not in pos or d_to not in pos:
            continue
        pair = tuple(sorted([d_from, d_to]))
        colour = RTYPE_COLOUR.get(r["type"], "#888888")
        style  = "dashed" if r.get("strength") == "moderate" else "solid"
        if pair not in drawn_pairs:
            x_vals = [pos[d_from][0], pos[d_to][0]]
            y_vals = [pos[d_from][1], pos[d_to][1]]
            ax.plot(x_vals, y_vals, color=colour, linewidth=1.8,
                    linestyle=style, alpha=0.75, zorder=1)
            drawn_pairs.add(pair)

    # Bubbles sized by question count
    q_max = max(q_per_domain.values()) if q_per_domain else 1
    for d in domain_ids:
        x, y   = pos[d]
        q      = q_per_domain.get(d, 0)
        c      = c_per_domain.get(d, 0)
        size   = 350 + 1800 * (q / q_max)          # bubble area
        colour = d_colours[d]
        ax.scatter(x, y, s=size, color=colour, alpha=0.88,
                   edgecolors="white", linewidths=1.5, zorder=2)
        # Abbreviation inside bubble
        ax.text(x, y, d, ha="center", va="center",
                fontsize=6.5, fontweight="bold", color="white", zorder=3)

    # Labels outside bubbles (radially placed)
    for d in domain_ids:
        x, y = pos[d]
        r_label = 1.19
        lx, ly = x * r_label, y * r_label
        ha = "left" if x >= -0.1 else "right"
        short = domain_label[d].replace("y ", "& ").title()
        if len(short) > 22:
            short = short[:20] + "…"
        ax.text(lx, ly, short, ha=ha, va="center",
                fontsize=5.5, color="#333333", zorder=4)

    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.55, 1.55)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("A — Domain Network\n(bubble size ∝ questions; edges = cross-domain links)",
                 fontsize=9, pad=6, fontweight="bold")

    # Small legend: cross-domain edge colours
    legend_items = [
        mlines.Line2D([], [], color=RTYPE_COLOUR[t], linewidth=1.8, label=t.replace("_", " "))
        for t in RTYPE_COLOUR if t in {r["type"] for r in cross_rels}
    ]
    if legend_items:
        ax.legend(handles=legend_items, loc="lower left", fontsize=5.5,
                  framealpha=0.8, title="Edge type", title_fontsize=5.5)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel B — Intra-domain construct web (top 6 richest domains)           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def draw_construct_web(ax, data, c_per_domain, d_colours, intra_rels, cdom):
    top6 = [d for d, _ in c_per_domain.most_common(6)]
    domain_label = {d["id"]: d["label"] for d in data["domains"]}
    constructs = [c for c in data["constructs"] if c["domain"] in top6]
    c_label = {c["id"]: c["label"] for c in constructs}
    c_domain = {c["id"]: c["domain"] for c in constructs}

    G = nx.DiGraph()
    for c in constructs:
        G.add_node(c["id"], domain=c["domain"])
    for r in intra_rels:
        if r["from"] in G and r["to"] in G:
            G.add_edge(r["from"], r["to"], relation=r["type"])

    if not G.nodes:
        ax.text(0.5, 0.5, "No construct data", transform=ax.transAxes, ha="center")
        return

    # Arrange top6 domains in a 3×2 grid; spring-layout within each cell
    grid = [(col, row) for row in range(2) for col in range(3)]   # (col, row)
    domain_list = top6[:6]
    cell_w, cell_h = 1.0 / 3, 1.0 / 2
    margin = 0.08

    pos = {}
    rng = np.random.default_rng(42)

    for idx, dom in enumerate(domain_list):
        col, row = grid[idx]
        nodes_in = [n for n in G.nodes if c_domain.get(n) == dom]
        sub = G.subgraph(nodes_in)

        # Spring layout within a unit square, then scale to cell
        if len(nodes_in) == 1:
            local_pos = {nodes_in[0]: (0.5, 0.5)}
        else:
            local_pos = nx.spring_layout(sub, seed=idx * 7 + 1, k=1.2, iterations=80)
            # Normalise to [0,1]²
            xs = np.array([p[0] for p in local_pos.values()])
            ys = np.array([p[1] for p in local_pos.values()])
            xr, yr = np.ptp(xs) or 1, np.ptp(ys) or 1
            local_pos = {n: ((p[0] - xs.min()) / xr, (p[1] - ys.min()) / yr)
                         for n, p in local_pos.items()}

        # Map to global axes coordinates
        x0 = col * cell_w + margin * cell_w
        y0 = (1 - (row + 1) * cell_h) + margin * cell_h
        w  = cell_w * (1 - 2 * margin)
        h  = cell_h * (1 - 2 * margin)
        for n, (lx, ly) in local_pos.items():
            pos[n] = (x0 + lx * w, y0 + ly * h)

    # Draw light background rects per cell
    for idx, dom in enumerate(domain_list):
        col, row = grid[idx]
        colour = d_colours.get(dom, (0.9, 0.9, 0.9, 1))
        rect = mpatches.FancyBboxPatch(
            (col * cell_w + 0.005, (1 - (row + 1) * cell_h) + 0.005),
            cell_w - 0.01, cell_h - 0.01,
            boxstyle="round,pad=0.01",
            linewidth=0.8,
            edgecolor=colour[:3] + (0.6,) if isinstance(colour, tuple) else colour,
            facecolor=colour[:3] + (0.08,) if isinstance(colour, tuple) else colour,
            transform=ax.transAxes, zorder=0,
        )
        ax.add_patch(rect)
        # Domain label in top-left of cell
        short_lbl = domain_label.get(dom, dom).title()
        if len(short_lbl) > 20:
            short_lbl = short_lbl[:18] + "…"
        ax.text(col * cell_w + 0.015, 1 - row * cell_h - 0.03,
                f"{dom}: {short_lbl}",
                transform=ax.transAxes, fontsize=6, fontweight="bold",
                color=colour[:3] if isinstance(colour, tuple) else "black",
                va="top", ha="left", zorder=5)

    # Colour nodes by domain
    node_list = list(G.nodes)
    node_colours = [d_colours.get(c_domain.get(n, ""), (0.8, 0.8, 0.8, 1)) for n in node_list]

    nx.draw_networkx_nodes(G, pos, nodelist=node_list, ax=ax,
                           node_color=node_colours, node_size=55, alpha=0.90)

    # Edge colours by type
    edge_colours = [RTYPE_COLOUR.get(G.edges[e].get("relation", ""), "#aaaaaa")
                    for e in G.edges]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colours,
                           arrows=True, arrowsize=7,
                           width=1.3, alpha=0.70,
                           connectionstyle="arc3,rad=0.15")

    # Node labels (shortened)
    labels = {}
    for n in node_list:
        lbl = c_label.get(n, n).split("__")[-1].replace("_", " ")
        short = lbl if len(lbl) <= 16 else lbl[:14] + "…"
        labels[n] = short
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=4.3, font_color="#111111")

    # Edge-type legend (bottom)
    used_types = {G.edges[e].get("relation", "") for e in G.edges}
    legend_lines = [
        mlines.Line2D([], [], color=RTYPE_COLOUR.get(t, "#aaa"),
                      linewidth=1.5, label=t.replace("_", " "))
        for t in RTYPE_COLOUR if t in used_types
    ]
    if legend_lines:
        ax.legend(handles=legend_lines, loc="lower center",
                  fontsize=5.5, ncol=len(legend_lines),
                  framealpha=0.9, title="Relationship type", title_fontsize=5.5,
                  bbox_to_anchor=(0.5, -0.02))

    ax.set_title("B — Intra-Domain Construct Web\n(top 6 richest domains; each cell = one domain)",
                 fontsize=9, pad=6, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.05, 1.02)
    ax.axis("off")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel C — Relationship type bar chart                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def draw_rtype_chart(ax, rtype_counts, intra_count, cross_count):
    types  = list(rtype_counts.keys())
    counts = list(rtype_counts.values())
    colours= [RTYPE_COLOUR.get(t, "#999999") for t in types]

    bars = ax.barh(types, counts, color=colours, edgecolor="white", linewidth=0.5, height=0.6)
    for bar, val in zip(bars, counts):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=8, color="#333333")

    ax.set_xlabel("Number of relationships", fontsize=8)
    ax.set_xlim(0, max(counts) * 1.2)
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)

    # Intra / cross annotation
    ax.text(0.98, 0.04,
            f"Intra-domain: {intra_count}\nCross-domain:  {cross_count}\nTotal:  {intra_count+cross_count}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color="#555555",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#f5f5f5", edgecolor="#cccccc"))

    ax.set_title("C — Relationship Types", fontsize=9, pad=6, fontweight="bold")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  Panel D — Domain statistics table                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def draw_stats_table(ax, data, q_per_domain, c_per_domain, d_colours):
    domain_label = {d["id"]: d["label"] for d in data["domains"]}
    rows = sorted(domain_label.keys(), key=lambda d: -q_per_domain.get(d, 0))

    col_labels = ["ID", "Survey Topic", "Constructs", "Questions"]
    cell_data  = []
    cell_colours = []

    for d in rows:
        label = domain_label[d].title()
        if len(label) > 38:
            label = label[:36] + "…"
        q = q_per_domain.get(d, 0)
        c = c_per_domain.get(d, 0)
        cell_data.append([d, label, str(c), str(q)])
        base = d_colours.get(d, (0.9, 0.9, 0.9, 1.0))
        # Lighten for readability
        light = tuple(min(1.0, v + 0.45) for v in base[:3]) + (0.35,)
        cell_colours.append([light, "white", "white", "white"])

    table = ax.table(
        cellText=cell_data,
        colLabels=col_labels,
        cellColours=cell_colours,
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(6.8)
    table.scale(1, 1.18)

    # Header style
    for j in range(len(col_labels)):
        table[0, j].set_facecolor("#2c3e50")
        table[0, j].set_text_props(color="white", fontweight="bold")

    ax.axis("off")
    ax.set_title("D — Domain Statistics", fontsize=9, pad=6, fontweight="bold")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    ontology_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ONTOLOGY
    if not ontology_path.exists():
        print(f"ERROR: ontology file not found at {ontology_path}")
        print("  Run on the feature/knowledge-graph branch, or pass the path as argument.")
        sys.exit(1)

    print(f"Loading ontology from {ontology_path} …")
    data = load_ontology(ontology_path)

    q_per_domain, c_per_domain, rtype_counts, cross_rels, intra_rels, cdom = compute_stats(data)

    domain_ids = [d["id"] for d in data["domains"]]
    d_colours  = domain_colours(domain_ids)

    # ── Figure layout ──────────────────────────────────────────────────────
    fig = plt.figure(figsize=(22, 20), facecolor="#fafafa")
    fig.suptitle(
        "Survey Knowledge Graph — los_mex Ontology\n"
        f"{len(data['domains'])} domains · {len(data['constructs'])} constructs · "
        f"{len(data['questions'])} questions · {len(data['relationships'])} relationships",
        fontsize=14, fontweight="bold", color="#2c3e50", y=0.985,
    )

    # Grid: 2×2
    gs = fig.add_gridspec(
        2, 2,
        width_ratios=[1.05, 0.95],
        height_ratios=[1.1, 0.9],
        hspace=0.10,
        wspace=0.08,
        left=0.03, right=0.97,
        top=0.95,  bottom=0.03,
    )

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    print("Drawing domain network …")
    draw_domain_network(ax_a, data, q_per_domain, c_per_domain, d_colours, cross_rels, cdom)

    print("Drawing construct web …")
    draw_construct_web(ax_b, data, c_per_domain, d_colours, intra_rels, cdom)

    print("Drawing relationship chart …")
    draw_rtype_chart(ax_c, rtype_counts, len(intra_rels), len(cross_rels))

    print("Drawing statistics table …")
    draw_stats_table(ax_d, data, q_per_domain, c_per_domain, d_colours)

    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"\n✅  Saved to {OUTPUT}")

    # Print text summary
    print("\n── Text Summary ─────────────────────────────────────────────────")
    print(f"  Domains:       {len(data['domains'])}")
    print(f"  Constructs:    {len(data['constructs'])}")
    print(f"  Questions:     {len(data['questions'])}")
    print(f"  Relationships: {len(data['relationships'])}")
    print(f"    Intra-domain: {len(intra_rels)}")
    print(f"    Cross-domain: {len(cross_rels)}")
    print(f"\n  By relationship type:")
    for t, n in rtype_counts.most_common():
        bar = "█" * (n // 2)
        print(f"    {t:<20} {n:>3}  {bar}")
    print(f"\n  Top 5 domains by construct count:")
    for d, n in c_per_domain.most_common(5):
        lbl = next(x["label"] for x in data["domains"] if x["id"] == d)
        print(f"    {d}: {lbl}  ({n} constructs, {q_per_domain.get(d,0)} questions)")
    print(f"\n  Cross-domain links ({len(cross_rels)}):")
    for r in cross_rels:
        df = cdom.get(r["from"], "?")
        dt = cdom.get(r["to"],   "?")
        print(f"    {df} → {dt}  [{r['type']}]  ({r.get('strength','?')} strength)")
    print("─────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
