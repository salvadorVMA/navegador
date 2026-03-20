"""
Bipartition Analysis — Camp Structure Characterization

Generates diagnostic plots and a summary report for the signed-graph
bipartition of the los_mex construct network.

Outputs (all in data/results/):
  bipartition_network.png          — domain-circle network colored by camp
  bipartition_fiedler_spectrum.png — eigenvalue spectrum + Fiedler vector histogram
  bipartition_pca_camps.png        — fingerprint PCA scatter colored by camp
  bipartition_frustration.png      — frustrated triangle ratio distribution
  bipartition_domain_composition.png — domain bar chart (cosmopolitan vs tradition)
  bipartition_edge_balance.png     — cross-camp vs within-camp edge counts
  bipartition_analysis.json        — full analysis data for the report

Run:
  python scripts/debug/analyze_bipartition.py
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
from matplotlib.patches import FancyArrowPatch, Wedge
import matplotlib.patheffects as pe
import numpy as np
from scipy import stats as sp_stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from opinion_ontology import OntologyQuery

# Import layout helpers from existing plot script
sys.path.insert(0, str(ROOT / "scripts" / "debug"))
from plot_domain_circle_network import (
    DOMAIN_LABELS, _CMAP24, domain_angles, layout_nodes,
    draw_sector_backgrounds, curved_edge, normalize_julia_estimates,
)

RESULTS = ROOT / "data" / "results"

# ─── Camp colors ────────────────────────────────────────────────────────────
CAMP_COLORS = {
    1:  "#2166ac",   # cosmopolitan: deep blue
    -1: "#b2182b",   # tradition: deep red
}
CAMP_COLORS_LIGHT = {
    1:  "#92c5de",   # cosmopolitan light
    -1: "#f4a582",   # tradition light
}
CAMP_NAMES = {1: "Cosmopolitan", -1: "Tradition"}


def collect_data(oq: OntologyQuery) -> dict:
    """Extract all bipartition data from OntologyQuery."""
    constructs = []
    for k in sorted(oq._constructs.keys()):
        fp = oq._constructs[k]
        camp_id = oq._camp.get(k)
        constructs.append({
            "key": k,
            "domain": k.split("|")[0],
            "name": k.split("|")[1] if "|" in k else k,
            "camp_id": camp_id,
            "camp_name": CAMP_NAMES.get(camp_id, "?"),
            "confidence": oq._camp_confidence.get(k, 0.0),
            "frustrated_ratio": oq._frustrated_ratio.get(k, 0.0),
            "n_triangles": oq._n_triangles.get(k, 0),
            "n_bridges": len(oq._bridges.get(k, [])),
            "rho_escol": fp.get("rho_escol", 0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0),
            "rho_sexo": fp.get("rho_sexo", 0),
            "rho_edad": fp.get("rho_edad", 0),
            "ses_magnitude": fp.get("ses_magnitude", 0),
        })

    # Eigenvalue spectrum
    nodes = sorted(k for k in oq._constructs if k in oq._bridges)
    idx = {k: i for i, k in enumerate(nodes)}
    n = len(nodes)
    A = np.zeros((n, n))
    for src in nodes:
        i = idx[src]
        for e in oq._bridges.get(src, []):
            nbr = e["neighbor"]
            if nbr in idx:
                A[i, idx[nbr]] = e["gamma"]
    L_s = np.diag(np.abs(A).sum(axis=1)) - A
    eigenvalues, eigenvectors = np.linalg.eigh(L_s)
    fiedler = eigenvectors[:, 1].copy()

    # Orient Fiedler (same logic as OntologyQuery)
    pos_mask = fiedler > 0
    if pos_mask.any() and (~pos_mask).any():
        escol_pos = np.median([oq._constructs[nodes[i]].get("rho_escol", 0)
                               for i in range(n) if pos_mask[i]])
        escol_neg = np.median([oq._constructs[nodes[i]].get("rho_escol", 0)
                               for i in range(n) if not pos_mask[i]])
        if escol_neg > escol_pos:
            fiedler = -fiedler

    # Edge classification
    edges = []
    seen = set()
    for src in nodes:
        for e in oq._bridges.get(src, []):
            nbr = e["neighbor"]
            if nbr not in idx:
                continue
            pair = tuple(sorted([src, nbr]))
            if pair in seen:
                continue
            seen.add(pair)
            same_camp = oq._camp.get(src) == oq._camp.get(nbr)
            edges.append({
                "from": src, "to": nbr,
                "gamma": e["gamma"],
                "same_camp": same_camp,
                "balanced": (e["gamma"] > 0 and same_camp) or (e["gamma"] < 0 and not same_camp),
            })

    # PCA of fingerprint vectors
    fp_matrix = np.array([
        [oq._constructs[k].get("rho_escol", 0),
         oq._constructs[k].get("rho_Tam_loc", 0),
         oq._constructs[k].get("rho_sexo", 0),
         oq._constructs[k].get("rho_edad", 0)]
        for k in nodes
    ])
    if fp_matrix.shape[0] > 2:
        fp_centered = fp_matrix - fp_matrix.mean(axis=0)
        cov = np.cov(fp_centered.T)
        pca_vals, pca_vecs = np.linalg.eigh(cov)
        # Descending order
        order = np.argsort(-pca_vals)
        pca_vals = pca_vals[order]
        pca_vecs = pca_vecs[:, order]
        pca_proj = fp_centered @ pca_vecs[:, :2]
        pca_var_explained = pca_vals / pca_vals.sum()
    else:
        pca_proj = np.zeros((len(nodes), 2))
        pca_var_explained = np.array([0, 0, 0, 0])
        pca_vecs = np.eye(4)

    return {
        "constructs": constructs,
        "connected_nodes": nodes,
        "eigenvalues": eigenvalues.tolist(),
        "fiedler": {nodes[i]: float(fiedler[i]) for i in range(n)},
        "edges": edges,
        "pca_proj": {nodes[i]: pca_proj[i].tolist() for i in range(n)},
        "pca_var_explained": pca_var_explained.tolist(),
        "pca_loadings": pca_vecs[:, :2].tolist(),
        "n_balanced": sum(1 for e in edges if e["balanced"]),
        "n_frustrated_edges": sum(1 for e in edges if not e["balanced"]),
    }


# ─── Plot 1: Domain circle network with camp coloring ──────────────────────

def plot_camp_network(data: dict, oq: OntologyQuery):
    """Domain-circle network with nodes and edges colored by camp assignment."""

    # Load Julia v4 estimates for edges
    v5j4_path = RESULTS / "construct_dr_sweep_v5_julia_v4.json"
    with open(v5j4_path) as f:
        raw = json.load(f)
    est_raw = raw.get("estimates", raw)
    estimates = normalize_julia_estimates(est_raw)

    # Filter significant
    sig = []
    for k, v in estimates.items():
        g = v.get("dr_gamma")
        if g is None:
            continue
        if "excl_zero" in v:
            is_sig = bool(v["excl_zero"])
        else:
            ci = v.get("dr_gamma_ci")
            if not ci or ci[0] is None or ci[1] is None:
                continue
            is_sig = (ci[0] > 0 or ci[1] < 0)
        if is_sig:
            sig.append(v)

    # Build node set
    manifest_path = RESULTS / "construct_variable_manifest.json"
    manifest_constructs = []
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        manifest_constructs = [e["key"] for e in manifest_data if "key" in e]

    constructs = set(manifest_constructs)
    for v in estimates.values():
        ca, cb = v.get("construct_a"), v.get("construct_b")
        if ca: constructs.add(ca)
        if cb: constructs.add(cb)
    constructs = sorted(constructs)

    sig_nodes = set()
    for v in sig:
        sig_nodes.add(v["construct_a"])
        sig_nodes.add(v["construct_b"])

    domains = sorted(set(c.split("|")[0] for c in constructs))
    domain_colors = {d: _CMAP24[i % len(_CMAP24)] for i, d in enumerate(domains)}
    dam = domain_angles(domains)
    pos = layout_nodes(constructs, dam, len(domains), node_radius=3.4)

    degree = defaultdict(int)
    for v in sig:
        degree[v["construct_a"]] += 1
        degree[v["construct_b"]] += 1

    fig, ax = plt.subplots(figsize=(24, 24))
    ax.set_aspect("equal")
    ax.axis("off")
    lim = 6.5
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    # Sector backgrounds with camp tinting
    draw_sector_backgrounds(ax, domains, dam, len(domains),
                            inner_r=2.7, outer_r=4.1,
                            domain_colors=domain_colors)

    # Edges — colored by balance status
    gamma_vals = [abs(v["dr_gamma"]) for v in sig]
    g_max = max(gamma_vals) if gamma_vals else 1.0
    g_min = min(gamma_vals) if gamma_vals else 0.0
    g_range = g_max - g_min if g_max > g_min else 1.0

    for v in sorted(sig, key=lambda x: abs(x["dr_gamma"])):
        ca, cb = v["construct_a"], v["construct_b"]
        if ca not in pos or cb not in pos:
            continue
        g = v["dr_gamma"]
        abs_g = abs(g)
        camp_a = oq._camp.get(ca)
        camp_b = oq._camp.get(cb)
        same = camp_a == camp_b

        # Balanced = expected sign; frustrated = unexpected sign
        balanced = (g > 0 and same) or (g < 0 and not same)
        if balanced:
            color = "#2166ac" if g < 0 else "#b2182b"  # blue cross-camp, red within
            alpha_base = 0.20
        else:
            # Frustrated edges: gold/warning color
            color = "#ff7f00"
            alpha_base = 0.45

        norm_g = (abs_g - g_min) / g_range
        alpha = alpha_base + 0.50 * norm_g
        lw = 0.5 + 2.5 * norm_g
        curved_edge(ax, pos[ca], pos[cb], color=color, alpha=alpha, lw=lw, rad=0.18)

    # Nodes — colored by camp
    for c in constructs:
        x, y = pos[c]
        deg = degree.get(c, 0)
        is_sig = c in sig_nodes
        camp_id = oq._camp.get(c)
        frust = oq._frustrated_ratio.get(c, 0.0)

        if is_sig:
            size = 50 + min(deg * 14, 220)
            color = CAMP_COLORS.get(camp_id, "#888888")
            if frust >= 0.15:
                ec = "#ff7f00"  # orange border for frustrated
                lw = 2.0
            else:
                ec = "white"
                lw = 0.8
            alpha = 0.92
            zorder = 5
        else:
            size = 15
            color = CAMP_COLORS_LIGHT.get(camp_id, "#cccccc")
            alpha = 0.50
            ec = "#aaaaaa"
            lw = 0.3
            zorder = 3
        ax.scatter(x, y, s=size, c=color, zorder=zorder,
                   edgecolors=ec, linewidths=lw, alpha=alpha)

    # Labels for high-degree nodes
    deg_threshold = max(5, np.percentile(list(degree.values()) or [0], 65))
    for c in constructs:
        if c in sig_nodes and degree.get(c, 0) >= deg_threshold:
            x, y = pos[c]
            short = c.split("|")[1].replace("_", " ")[:16]
            ax.text(x, y, short, ha="center", va="center",
                    fontsize=4.5, zorder=6, color="white", fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=1.2, foreground="black")])

    # Domain labels
    label_radius = 4.75
    for dom in domains:
        angle = dam[dom]
        lx = label_radius * np.cos(angle)
        ly = label_radius * np.sin(angle)
        label = DOMAIN_LABELS.get(dom, dom)
        color = domain_colors[dom]
        ha = "center"
        if lx > 0.3:
            ha = "left"
        elif lx < -0.3:
            ha = "right"
        ax.text(lx, ly, f"{dom}\n{label}", ha=ha, va="center",
                fontsize=8.5, fontweight="bold", color=color,
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
                zorder=6)

    # Legend
    n_balanced = sum(1 for e in data["edges"] if e["balanced"])
    n_frustrated = sum(1 for e in data["edges"] if not e["balanced"])
    legend_elements = [
        mpatches.Patch(facecolor=CAMP_COLORS[1], alpha=0.8,
                       label=f"Cosmopolitan camp ({sum(1 for c in data['constructs'] if c['camp_id']==1)})"),
        mpatches.Patch(facecolor=CAMP_COLORS[-1], alpha=0.8,
                       label=f"Tradition camp ({sum(1 for c in data['constructs'] if c['camp_id']==-1)})"),
        mpatches.Patch(facecolor="#b2182b", alpha=0.5, label=f"γ>0 within-camp ({n_balanced} balanced)"),
        mpatches.Patch(facecolor="#2166ac", alpha=0.5, label="γ<0 cross-camp"),
        mpatches.Patch(facecolor="#ff7f00", alpha=0.6,
                       label=f"Frustrated edge ({n_frustrated})"),
        plt.scatter([], [], s=60, c="#888888", edgecolors="#ff7f00",
                    linewidths=2, label="Boundary node (frustrated ≥15%)"),
    ]
    ax.legend(handles=legend_elements, loc="lower left",
              bbox_to_anchor=(0.01, 0.01), fontsize=9, framealpha=0.88,
              title="Camp Bipartition", title_fontsize=10)

    # Stats
    balance_pct = n_balanced / (n_balanced + n_frustrated) * 100 if (n_balanced + n_frustrated) else 0
    stats_text = (
        f"{len(sig)} significant edges  |  "
        f"balance: {balance_pct:.1f}%  |  "
        f"frustrated edges: {n_frustrated}  |  "
        f"isolated: {sum(1 for c in data['constructs'] if c['n_bridges']==0)}"
    )
    ax.text(0, -lim + 0.3, stats_text, ha="center", va="bottom",
            fontsize=9, color="#444444",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

    ax.set_title(
        "SES Bridge — Camp Bipartition\n"
        "Signed Laplacian Fiedler decomposition  |  los_mex construct network",
        fontsize=16, fontweight="bold", pad=16, y=0.98,
    )

    fig.tight_layout()
    out = RESULTS / "bipartition_network.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved: {out}")


# ─── Plot 2: Eigenvalue spectrum + Fiedler vector ──────────────────────────

def plot_fiedler_spectrum(data: dict):
    eigenvalues = np.array(data["eigenvalues"])
    fiedler_vals = np.array(list(data["fiedler"].values()))
    nodes = list(data["fiedler"].keys())
    camps = [1 if v >= 0 else -1 for v in fiedler_vals]

    fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))

    # Panel A: Eigenvalue spectrum (first 20)
    ax = axes[0]
    n_show = min(20, len(eigenvalues))
    ax.bar(range(n_show), eigenvalues[:n_show], color="#4e79a7", alpha=0.8, width=0.7)
    ax.axhline(eigenvalues[0], color="#e15759", linestyle="--", linewidth=1, alpha=0.7,
               label=f"λ₀ = {eigenvalues[0]:.4f}")
    ax.axhline(eigenvalues[1], color="#59a14f", linestyle="--", linewidth=1, alpha=0.7,
               label=f"λ₁ = {eigenvalues[1]:.4f}")
    ax.set_xlabel("Eigenvalue index", fontsize=11)
    ax.set_ylabel("λ", fontsize=11)
    ax.set_title("Signed Laplacian Eigenvalue Spectrum", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(-0.5, n_show - 0.5)

    # Panel B: Fiedler vector sorted by value
    ax = axes[1]
    order = np.argsort(fiedler_vals)
    sorted_fiedler = fiedler_vals[order]
    sorted_camps = [camps[i] for i in order]
    colors = [CAMP_COLORS[c] for c in sorted_camps]
    ax.bar(range(len(sorted_fiedler)), sorted_fiedler, color=colors, alpha=0.85, width=1.0)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="-")
    ax.set_xlabel("Construct (sorted by Fiedler component)", fontsize=11)
    ax.set_ylabel("Fiedler component", fontsize=11)
    ax.set_title("Fiedler Vector — Camp Assignment", fontsize=12, fontweight="bold")
    # Mark the dominant node
    max_idx = np.argmax(np.abs(sorted_fiedler))
    max_node = nodes[order[max_idx]]
    max_name = max_node.split("|")[1].replace("_", " ") if "|" in max_node else max_node
    ax.annotate(max_name, xy=(max_idx, sorted_fiedler[max_idx]),
                xytext=(max_idx - 15, sorted_fiedler[max_idx] * 0.7),
                fontsize=7.5, arrowprops=dict(arrowstyle="->", color="#333"),
                color="#333")

    # Panel C: Fiedler component distribution (histogram)
    ax = axes[2]
    cosmo_vals = fiedler_vals[fiedler_vals >= 0]
    trad_vals = fiedler_vals[fiedler_vals < 0]
    bins = np.linspace(fiedler_vals.min(), fiedler_vals.max(), 40)
    ax.hist(trad_vals, bins=bins, color=CAMP_COLORS[-1], alpha=0.7,
            label=f"Tradition (n={len(trad_vals)})")
    ax.hist(cosmo_vals, bins=bins, color=CAMP_COLORS[1], alpha=0.7,
            label=f"Cosmopolitan (n={len(cosmo_vals)})")
    ax.axvline(0, color="black", linewidth=1.2, linestyle="--", alpha=0.7)
    ax.set_xlabel("Fiedler component value", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("Fiedler Component Distribution", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    spectral_gap = eigenvalues[1] - eigenvalues[0]
    fig.suptitle(
        f"Signed Laplacian Analysis  |  "
        f"λ₀={eigenvalues[0]:.4f}  λ₁={eigenvalues[1]:.4f}  "
        f"spectral gap={spectral_gap:.4f}  |  "
        f"71 connected / 22 isolated",
        fontsize=11, y=1.02,
    )
    fig.tight_layout()
    out = RESULTS / "bipartition_fiedler_spectrum.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


# ─── Plot 3: PCA scatter with camp coloring ────────────────────────────────

def plot_pca_camps(data: dict, oq: OntologyQuery):
    nodes = data["connected_nodes"]
    pca = data["pca_proj"]
    var_expl = data["pca_var_explained"]
    loadings = np.array(data["pca_loadings"])
    dim_labels = ["escol", "Tam_loc", "sexo", "edad"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Panel A: PCA scatter colored by camp
    ax = axes[0]
    for node in nodes:
        p = pca[node]
        camp_id = oq._camp.get(node)
        frust = oq._frustrated_ratio.get(node, 0.0)
        deg = len(oq._bridges.get(node, []))

        color = CAMP_COLORS.get(camp_id, "#888")
        size = 30 + min(deg * 3, 150)
        ec = "#ff7f00" if frust >= 0.15 else "white"
        lw = 1.5 if frust >= 0.15 else 0.5
        ax.scatter(p[0], p[1], s=size, c=color, edgecolors=ec,
                   linewidths=lw, alpha=0.82, zorder=5)

        if deg >= 25:
            name = node.split("|")[1].replace("_", " ")[:14]
            ax.annotate(name, (p[0], p[1]), fontsize=6.5,
                        xytext=(5, 5), textcoords="offset points",
                        color="#333", fontweight="bold")

    ax.axhline(0, color="#ccc", linewidth=0.5)
    ax.axvline(0, color="#ccc", linewidth=0.5)
    ax.set_xlabel(f"PC1 ({var_expl[0]*100:.1f}% variance)", fontsize=11)
    ax.set_ylabel(f"PC2 ({var_expl[1]*100:.1f}% variance)", fontsize=11)
    ax.set_title("Fingerprint PCA — Camp Coloring", fontsize=12, fontweight="bold")

    legend_elements = [
        mpatches.Patch(facecolor=CAMP_COLORS[1], alpha=0.8, label="Cosmopolitan"),
        mpatches.Patch(facecolor=CAMP_COLORS[-1], alpha=0.8, label="Tradition"),
        plt.scatter([], [], s=50, c="#888", edgecolors="#ff7f00",
                    linewidths=1.5, label="Frustrated (≥15%)"),
    ]
    ax.legend(handles=legend_elements, fontsize=9, loc="lower left")

    # Panel B: PCA loading biplot
    ax = axes[1]
    scale = 3.0
    for i, dim in enumerate(dim_labels):
        ax.arrow(0, 0, loadings[i, 0] * scale, loadings[i, 1] * scale,
                 head_width=0.08, head_length=0.04, fc="#333", ec="#333",
                 alpha=0.8, linewidth=1.5)
        offset_x = 0.15 if loadings[i, 0] >= 0 else -0.15
        offset_y = 0.15 if loadings[i, 1] >= 0 else -0.15
        ax.text(loadings[i, 0] * scale + offset_x,
                loadings[i, 1] * scale + offset_y,
                dim, fontsize=11, fontweight="bold", color="#333",
                ha="center", va="center")

    ax.set_xlim(-scale * 1.3, scale * 1.3)
    ax.set_ylim(-scale * 1.3, scale * 1.3)
    ax.axhline(0, color="#ccc", linewidth=0.5)
    ax.axvline(0, color="#ccc", linewidth=0.5)
    ax.set_xlabel("PC1 loading", fontsize=11)
    ax.set_ylabel("PC2 loading", fontsize=11)
    ax.set_title("PCA Loadings — SES Dimensions", fontsize=12, fontweight="bold")
    ax.set_aspect("equal")

    fig.suptitle(
        f"SES Fingerprint Geometry  |  "
        f"PC1={var_expl[0]*100:.1f}%  PC2={var_expl[1]*100:.1f}%  "
        f"effective dim ≈ {1/sum(v**2 for v in var_expl):.1f}",
        fontsize=11, y=1.02,
    )
    fig.tight_layout()
    out = RESULTS / "bipartition_pca_camps.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


# ─── Plot 4: Frustration distribution ──────────────────────────────────────

def plot_frustration(data: dict, oq: OntologyQuery):
    connected = [c for c in data["constructs"] if c["n_bridges"] > 0]
    ratios = [c["frustrated_ratio"] for c in connected]
    names = [c["name"].replace("_", " ") for c in connected]
    camp_ids = [c["camp_id"] for c in connected]
    n_tri = [c["n_triangles"] for c in connected]

    # Sort by frustrated_ratio descending
    order = np.argsort(ratios)[::-1]

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    # Panel A: Bar chart of frustrated ratio (top 30)
    ax = axes[0]
    n_show = min(30, len(order))
    y_pos = np.arange(n_show)
    bar_ratios = [ratios[order[i]] for i in range(n_show)]
    bar_colors = [CAMP_COLORS.get(camp_ids[order[i]], "#888") for i in range(n_show)]
    bar_names = [names[order[i]][:28] for i in range(n_show)]
    bar_tri = [n_tri[order[i]] for i in range(n_show)]

    bars = ax.barh(y_pos, bar_ratios, color=bar_colors, alpha=0.82, height=0.75)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(bar_names, fontsize=7.5)
    ax.invert_yaxis()
    ax.axvline(0.15, color="#ff7f00", linestyle="--", linewidth=1.2, alpha=0.7,
               label="Boundary threshold (0.15)")
    ax.set_xlabel("Frustrated Triangle Ratio", fontsize=11)
    ax.set_title("Top 30 — Frustrated Triangle Ratio", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    # Annotate triangle counts
    for i in range(n_show):
        ax.text(bar_ratios[i] + 0.01, y_pos[i], f"n={bar_tri[i]}",
                va="center", fontsize=7, color="#666")

    # Panel B: Scatter of frustrated_ratio vs n_triangles
    ax = axes[1]
    for c in connected:
        color = CAMP_COLORS.get(c["camp_id"], "#888")
        size = 20 + min(c["n_bridges"] * 2, 100)
        ax.scatter(c["n_triangles"], c["frustrated_ratio"],
                   s=size, c=color, alpha=0.75, edgecolors="white", linewidths=0.5)
        if c["frustrated_ratio"] >= 0.3 or (c["frustrated_ratio"] >= 0.15 and c["n_triangles"] > 100):
            name = c["name"].replace("_", " ")[:18]
            ax.annotate(name, (c["n_triangles"], c["frustrated_ratio"]),
                        fontsize=6.5, xytext=(5, 3), textcoords="offset points",
                        color="#333")

    ax.axhline(0.15, color="#ff7f00", linestyle="--", linewidth=1, alpha=0.7,
               label="Boundary threshold")
    ax.set_xlabel("Total Triangles", fontsize=11)
    ax.set_ylabel("Frustrated Ratio", fontsize=11)
    ax.set_title("Frustration vs Triangle Count", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    fig.suptitle(
        f"Frustrated Triangles — Boundary Node Identification  |  "
        f"{sum(1 for r in ratios if r >= 0.15)} constructs above threshold",
        fontsize=11, y=1.02,
    )
    fig.tight_layout()
    out = RESULTS / "bipartition_frustration.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


# ─── Plot 5: Domain composition ────────────────────────────────────────────

def plot_domain_composition(data: dict):
    domains = sorted(set(c["domain"] for c in data["constructs"]))
    cosmo_counts = []
    trad_counts = []
    for d in domains:
        cosmo_counts.append(sum(1 for c in data["constructs"]
                                if c["domain"] == d and c["camp_id"] == 1))
        trad_counts.append(sum(1 for c in data["constructs"]
                                if c["domain"] == d and c["camp_id"] == -1))

    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(domains))
    w = 0.38

    bars1 = ax.bar(x - w/2, cosmo_counts, w, color=CAMP_COLORS[1], alpha=0.82,
                   label="Cosmopolitan")
    bars2 = ax.bar(x + w/2, trad_counts, w, color=CAMP_COLORS[-1], alpha=0.82,
                   label="Tradition")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{d}\n{DOMAIN_LABELS.get(d, d)}" for d in domains],
                       fontsize=7.5, ha="center")
    ax.set_ylabel("Number of Constructs", fontsize=11)
    ax.set_title(
        "Camp Composition by Domain\n"
        "Cosmopolitan (education/urbanisation-elevated) vs "
        "Tradition (age/locality-elevated)",
        fontsize=12, fontweight="bold",
    )
    ax.legend(fontsize=10)

    # Highlight pure domains
    for i, d in enumerate(domains):
        if cosmo_counts[i] > 0 and trad_counts[i] == 0:
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.08, color=CAMP_COLORS[1])
        elif trad_counts[i] > 0 and cosmo_counts[i] == 0:
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.08, color=CAMP_COLORS[-1])

    fig.tight_layout()
    out = RESULTS / "bipartition_domain_composition.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


# ─── Plot 6: Edge balance analysis ─────────────────────────────────────────

def plot_edge_balance(data: dict):
    edges = data["edges"]
    pos_within = sum(1 for e in edges if e["gamma"] > 0 and e["same_camp"])
    neg_cross = sum(1 for e in edges if e["gamma"] < 0 and not e["same_camp"])
    neg_within = sum(1 for e in edges if e["gamma"] < 0 and e["same_camp"])
    pos_cross = sum(1 for e in edges if e["gamma"] > 0 and not e["same_camp"])

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panel A: Stacked bar chart of edge types
    ax = axes[0]
    categories = ["Within-camp", "Cross-camp"]
    balanced = [pos_within, neg_cross]
    frustrated = [neg_within, pos_cross]

    x = np.arange(2)
    w = 0.45
    ax.bar(x, balanced, w, color="#59a14f", alpha=0.82, label="Balanced (expected sign)")
    ax.bar(x, frustrated, w, bottom=balanced, color="#ff7f00", alpha=0.82,
           label="Frustrated (unexpected sign)")

    for i in range(2):
        ax.text(x[i], balanced[i]/2, str(balanced[i]), ha="center", va="center",
                fontsize=12, fontweight="bold", color="white")
        if frustrated[i] > 0:
            ax.text(x[i], balanced[i] + frustrated[i]/2, str(frustrated[i]),
                    ha="center", va="center", fontsize=11, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylabel("Edge Count", fontsize=11)
    ax.set_title("Edge Balance by Camp Relationship", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    # Panel B: |γ| distribution for balanced vs frustrated edges
    ax = axes[1]
    bal_gammas = [abs(e["gamma"]) for e in edges if e["balanced"]]
    fru_gammas = [abs(e["gamma"]) for e in edges if not e["balanced"]]

    bins = np.linspace(0, max(abs(e["gamma"]) for e in edges), 35)
    ax.hist(bal_gammas, bins=bins, color="#59a14f", alpha=0.6, label=f"Balanced (n={len(bal_gammas)})")
    ax.hist(fru_gammas, bins=bins, color="#ff7f00", alpha=0.6, label=f"Frustrated (n={len(fru_gammas)})")
    ax.set_xlabel("|γ|", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("|γ| Distribution — Balanced vs Frustrated Edges", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    total = len(edges)
    balance_pct = (pos_within + neg_cross) / total * 100
    fig.suptitle(
        f"Structural Balance Analysis  |  "
        f"{total} edges  |  {balance_pct:.1f}% balanced  |  "
        f"{neg_within + pos_cross} frustrated",
        fontsize=11, y=1.02,
    )
    fig.tight_layout()
    out = RESULTS / "bipartition_edge_balance.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("Loading ontology...")
    oq = OntologyQuery()
    print("Collecting bipartition data...")
    data = collect_data(oq)

    # Save analysis data
    analysis_out = RESULTS / "bipartition_analysis.json"
    with open(analysis_out, "w") as f:
        json.dump({
            "constructs": data["constructs"],
            "eigenvalues": data["eigenvalues"][:20],
            "n_balanced": data["n_balanced"],
            "n_frustrated_edges": data["n_frustrated_edges"],
            "pca_var_explained": data["pca_var_explained"],
            "pca_loadings": data["pca_loadings"],
        }, f, indent=2)
    print(f"Saved: {analysis_out}")

    print("\nGenerating plots...")
    plot_camp_network(data, oq)
    plot_fiedler_spectrum(data)
    plot_pca_camps(data, oq)
    plot_frustration(data, oq)
    plot_domain_composition(data)
    plot_edge_balance(data)

    # Print summary for report
    connected = [c for c in data["constructs"] if c["n_bridges"] > 0]
    isolated = [c for c in data["constructs"] if c["n_bridges"] == 0]
    cosmo = [c for c in data["constructs"] if c["camp_id"] == 1]
    trad = [c for c in data["constructs"] if c["camp_id"] == -1]
    boundary_nodes = [c for c in connected if c["confidence"] < 0.2 or c["frustrated_ratio"] > 0.15]
    pure_cosmo_domains = [d for d in sorted(set(c["domain"] for c in data["constructs"]))
                          if all(c["camp_id"] == 1 for c in data["constructs"] if c["domain"] == d)]
    pure_trad_domains = [d for d in sorted(set(c["domain"] for c in data["constructs"]))
                         if all(c["camp_id"] == -1 for c in data["constructs"] if c["domain"] == d)]

    print(f"\n{'='*60}")
    print(f"BIPARTITION SUMMARY")
    print(f"{'='*60}")
    print(f"Total constructs:     {len(data['constructs'])}")
    print(f"  Cosmopolitan:       {len(cosmo)}")
    print(f"  Tradition:          {len(trad)}")
    print(f"  Connected:          {len(connected)}")
    print(f"  Isolated:           {len(isolated)}")
    print(f"  Boundary (low conf):{len(boundary_nodes)}")
    print(f"\nEdge balance:         {data['n_balanced']}/{data['n_balanced']+data['n_frustrated_edges']} "
          f"({data['n_balanced']/(data['n_balanced']+data['n_frustrated_edges'])*100:.1f}%)")
    print(f"Frustrated edges:     {data['n_frustrated_edges']}")
    print(f"\nSpectral gap:         {data['eigenvalues'][1] - data['eigenvalues'][0]:.6f}")
    print(f"PCA variance:         PC1={data['pca_var_explained'][0]*100:.1f}% "
          f"PC2={data['pca_var_explained'][1]*100:.1f}%")
    print(f"\nPure cosmo domains:   {', '.join(pure_cosmo_domains) or 'none'}")
    print(f"Pure trad domains:    {', '.join(pure_trad_domains) or 'none'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
