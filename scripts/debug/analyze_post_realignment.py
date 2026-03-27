"""
Post-SES-Realignment Analysis — Los Mex Construct Network

After realigning Tam_loc (1=rural→4=urban), escol (ISCED boundaries),
and edad (continuous), regenerate:
  1. Domain circle network (standard: edges colored by γ sign)
  2. Bipartite structure check (structural balance)
  3. SES dominance per bridge (which of the 4 SES vars drives each γ)
  4. SES-colored circle network (edges colored by dominant SES variable)

Outputs:
  data/results/domain_circle_network_post_realignment.png
  data/results/domain_circle_network_ses_colored.png
  data/results/post_realignment_report.md

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_post_realignment.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
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

RESULTS = ROOT / "data" / "results"

# ─── Domain labels & colors (reuse from plot_domain_circle_network) ──────────

DOMAIN_LABELS = {
    "CIE": "Ciencia", "COR": "Corrupción", "CUL": "Cultura\nPolítica",
    "DEP": "Deporte /\nLectura", "DER": "Derechos", "ECO": "Economía",
    "EDU": "Educación", "ENV": "Envejecim.", "FAM": "Familia",
    "FED": "Fed. /\nGobierno", "GEN": "Género", "GLO": "Global.",
    "HAB": "Habitación", "IDE": "Identidad", "IND": "Industria",
    "JUS": "Justicia", "MED": "Medio Amb.", "MIG": "Migración",
    "NIN": "Niñez /\nJuventud", "POB": "Pobreza", "REL": "Religión",
    "SAL": "Salud", "SEG": "Seguridad", "SOC": "Sociedad\nDigital",
}

_CMAP24 = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#d37295", "#8cd17d", "#b6992d", "#499894", "#86bcb6",
    "#f1ce63", "#a0cbe8", "#ffbe7d", "#86bcb6", "#e49444",
    "#d4a6c8", "#c5d4e8", "#ff9888", "#a5b8d0",
]

SES_COLORS = {
    "escol":   "#e15759",   # red
    "Tam_loc": "#4e79a7",   # blue
    "sexo":    "#59a14f",   # green
    "edad":    "#edc948",   # gold
}
SES_LABELS = {
    "escol": "Education", "Tam_loc": "Urbanization",
    "sexo": "Gender", "edad": "Age/Cohort",
}


# ─── Data loading ────────────────────────────────────────────────────────────

def load_julia_sweep(path: Path) -> dict:
    """Load Julia sweep JSON and normalize to {key: {construct_a, construct_b, ...}}."""
    with open(path) as f:
        raw = json.load(f)
    estimates = raw.get("estimates", raw)
    out = {}
    for key, v in estimates.items():
        if "::" not in key or "dr_gamma" not in v:
            continue
        part_a, part_b = key.split("::", 1)

        def to_ca(part):
            if "|" not in part:
                return part
            name, domain = part.rsplit("|", 1)
            name = name.removeprefix("agg_")
            return f"{domain}|{name}"

        entry = dict(v)
        entry["construct_a"] = to_ca(part_a)
        entry["construct_b"] = to_ca(part_b)
        if "dr_ci_lo" in v and "dr_ci_hi" in v:
            entry["dr_gamma_ci"] = [v["dr_ci_lo"], v["dr_ci_hi"]]
        out[key] = entry
    return out


def load_fingerprints(path: Path) -> dict:
    """Load SES fingerprints → {construct_key: {rho_escol, rho_Tam_loc, rho_sexo, rho_edad}}.

    The fingerprints JSON has top-level keys: metadata, constructs, items, domains.
    `constructs` is a dict keyed by "DOMAIN|construct_name" → {rho_escol, ...}.
    """
    with open(path) as f:
        data = json.load(f)
    constructs = data.get("constructs", {})
    fp = {}
    for key, item in constructs.items():
        fp[key] = {
            "rho_escol":   item.get("rho_escol", 0),
            "rho_Tam_loc": item.get("rho_Tam_loc", 0),
            "rho_sexo":    item.get("rho_sexo", 0),
            "rho_edad":    item.get("rho_edad", 0),
        }
    return fp


# ─── SES dominance per bridge ────────────────────────────────────────────────

def compute_ses_dominance(sig_estimates: list[dict], fingerprints: dict) -> list[dict]:
    """
    For each significant bridge, determine which SES variable dominates.

    The dominant SES dimension is the one whose fingerprint components
    contribute most to the bridge γ. For a pair (A, B), the bridge γ
    is predicted by dot(fingerprint_A, fingerprint_B). The contribution
    of each SES dimension d is: rho_d(A) × rho_d(B). The dimension
    with the largest |contribution| is the dominant driver.
    """
    ses_dims = ["rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad"]
    dim_short = {"rho_escol": "escol", "rho_Tam_loc": "Tam_loc",
                 "rho_sexo": "sexo", "rho_edad": "edad"}
    results = []
    for v in sig_estimates:
        ca, cb = v["construct_a"], v["construct_b"]
        fp_a = fingerprints.get(ca)
        fp_b = fingerprints.get(cb)
        if not fp_a or not fp_b:
            results.append({**v, "dominant_ses": "unknown", "ses_contributions": {}})
            continue

        contribs = {}
        for d in ses_dims:
            contribs[dim_short[d]] = fp_a[d] * fp_b[d]

        dominant = max(contribs, key=lambda k: abs(contribs[k]))
        results.append({**v, "dominant_ses": dominant, "ses_contributions": contribs})

    return results


# ─── Bipartite / structural balance ──────────────────────────────────────────

def check_bipartite_structure(sig_estimates: list[dict]) -> dict:
    """
    Check structural balance: count balanced vs frustrated triangles.

    A triangle is balanced if the product of its 3 edge signs is positive
    (all positive, or one positive + two negative). A frustrated triangle
    has negative product (two positive + one negative, or all negative).

    94% balanced = strong two-camp bipartition.
    """
    # Build adjacency with signs
    adj = defaultdict(dict)
    nodes = set()
    for v in sig_estimates:
        ca, cb = v["construct_a"], v["construct_b"]
        g = v["dr_gamma"]
        sign = 1 if g > 0 else -1
        adj[ca][cb] = sign
        adj[cb][ca] = sign
        nodes.add(ca)
        nodes.add(cb)

    # Count triangles
    node_list = sorted(nodes)
    n_balanced = 0
    n_frustrated = 0
    for i, a in enumerate(node_list):
        for j, b in enumerate(node_list[i+1:], i+1):
            if b not in adj[a]:
                continue
            for c in node_list[j+1:]:
                if c not in adj[a] or c not in adj[b]:
                    continue
                product = adj[a][b] * adj[a][c] * adj[b][c]
                if product > 0:
                    n_balanced += 1
                else:
                    n_frustrated += 1

    total = n_balanced + n_frustrated
    pct = 100 * n_balanced / total if total else 0

    # Sign split
    n_pos = sum(1 for v in sig_estimates if v["dr_gamma"] > 0)
    n_neg = len(sig_estimates) - n_pos

    return {
        "n_nodes": len(nodes),
        "n_edges": len(sig_estimates),
        "n_pos": n_pos,
        "n_neg": n_neg,
        "sign_split": f"{100*n_pos/len(sig_estimates):.0f}% pos / {100*n_neg/len(sig_estimates):.0f}% neg",
        "n_triangles": total,
        "n_balanced": n_balanced,
        "n_frustrated": n_frustrated,
        "balance_pct": pct,
    }


# ─── Geometry (reused from plot_domain_circle_network) ───────────────────────

def domain_angles(domains):
    n = len(domains)
    step = 2 * np.pi / n
    return {d: np.pi / 2 - i * step for i, d in enumerate(sorted(domains))}


def layout_nodes(constructs, domain_angle_map, n_domains, node_radius=3.4, spread_frac=0.68):
    sector = 2 * np.pi / n_domains
    half = sector * spread_frac / 2
    by_domain = defaultdict(list)
    for c in constructs:
        by_domain[c.split("|")[0]].append(c)
    pos = {}
    for dom, members in by_domain.items():
        center = domain_angle_map[dom]
        n = len(members)
        angles = [center] if n == 1 else np.linspace(center - half, center + half, n)
        for angle, c in zip(angles, sorted(members)):
            pos[c] = (node_radius * np.cos(angle), node_radius * np.sin(angle))
    return pos


def draw_sector_backgrounds(ax, domains, dam, n_domains, inner_r=2.8, outer_r=4.0, domain_colors=None):
    sector_deg = 360 / n_domains
    half_deg = sector_deg / 2
    for dom in domains:
        angle_deg = np.degrees(dam[dom])
        color = domain_colors.get(dom, "#cccccc")
        w = Wedge((0, 0), outer_r, angle_deg - half_deg, angle_deg + half_deg,
                  width=outer_r - inner_r, facecolor=color, alpha=0.12,
                  edgecolor=color, linewidth=0.4)
        ax.add_patch(w)


def curved_edge(ax, p1, p2, color, alpha, lw, rad=0.25):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-", color=color, alpha=alpha,
                                lw=lw, connectionstyle=f"arc3,rad={rad}"))


# ─── Plot: standard circle network ──────────────────────────────────────────

def plot_standard_network(sig_estimates, all_constructs, title, output_path):
    """Domain circle network with edges colored by γ sign (red=pos, blue=neg)."""
    constructs = sorted(all_constructs)
    domains = sorted(set(c.split("|")[0] for c in constructs))
    n_dom = len(domains)
    domain_colors = {d: _CMAP24[i % len(_CMAP24)] for i, d in enumerate(domains)}
    node_colors = {c: domain_colors[c.split("|")[0]] for c in constructs}

    sig_nodes = set()
    degree = defaultdict(int)
    for v in sig_estimates:
        sig_nodes.add(v["construct_a"])
        sig_nodes.add(v["construct_b"])
        degree[v["construct_a"]] += 1
        degree[v["construct_b"]] += 1

    dam = domain_angles(domains)
    pos = layout_nodes(constructs, dam, n_dom)

    fig, ax = plt.subplots(figsize=(22, 22))
    ax.set_aspect("equal"); ax.axis("off")
    lim = 6.5
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)

    draw_sector_backgrounds(ax, domains, dam, n_dom, inner_r=2.7, outer_r=4.1,
                            domain_colors=domain_colors)

    gamma_vals = [abs(v["dr_gamma"]) for v in sig_estimates]
    g_max = max(gamma_vals) if gamma_vals else 1.0
    g_min = min(gamma_vals) if gamma_vals else 0.0
    g_range = g_max - g_min if g_max > g_min else 1.0

    for v in sorted(sig_estimates, key=lambda x: abs(x["dr_gamma"])):
        ca, cb = v["construct_a"], v["construct_b"]
        if ca not in pos or cb not in pos:
            continue
        g = v["dr_gamma"]
        color = "#d62728" if g > 0 else "#1f77b4"
        norm_g = (abs(g) - g_min) / g_range
        alpha = 0.15 + 0.55 * norm_g
        lw = 0.4 + 2.6 * norm_g
        curved_edge(ax, pos[ca], pos[cb], color=color, alpha=alpha, lw=lw, rad=0.18)

    for c in constructs:
        x, y = pos[c]
        deg = degree.get(c, 0)
        is_sig = c in sig_nodes
        size = (40 + min(deg * 14, 200)) if is_sig else 12
        color = node_colors[c] if is_sig else "#cccccc"
        alpha = 0.92 if is_sig else 0.45
        ec = "white" if is_sig else "#aaaaaa"
        lw = 0.7 if is_sig else 0.3
        zorder = 5 if is_sig else 3
        ax.scatter(x, y, s=size, c=color, zorder=zorder, edgecolors=ec,
                   linewidths=lw, alpha=alpha)

    deg_threshold = max(5, np.percentile(list(degree.values()) or [0], 70))
    for c in constructs:
        if c in sig_nodes and degree.get(c, 0) >= deg_threshold:
            x, y = pos[c]
            short = c.split("|")[1].replace("_", " ")[:14]
            ax.text(x, y, short, ha="center", va="center", fontsize=4.5, zorder=6,
                    color="white" if degree.get(c, 0) >= 10 else "black",
                    fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=1.2, foreground="black")])

    label_radius = 4.75
    for dom in domains:
        angle = dam[dom]
        lx, ly = label_radius * np.cos(angle), label_radius * np.sin(angle)
        label = DOMAIN_LABELS.get(dom, dom)
        ha = "left" if lx > 0.3 else ("right" if lx < -0.3 else "center")
        ax.text(lx, ly, f"{dom}\n{label}", ha=ha, va="center", fontsize=8.5,
                fontweight="bold", color=domain_colors[dom],
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")], zorder=6)

    legend_elements = [
        mpatches.Patch(facecolor="#d62728", alpha=0.7, label="γ > 0  (positive co-variation)"),
        mpatches.Patch(facecolor="#1f77b4", alpha=0.7, label="γ < 0  (negative co-variation)"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", bbox_to_anchor=(0.01, 0.01),
              fontsize=9, framealpha=0.85, title="Edge sign", title_fontsize=9)

    n_with = sum(1 for c in constructs if degree.get(c, 0) > 0)
    n_pos = sum(1 for v in sig_estimates if v["dr_gamma"] > 0)
    n_neg = len(sig_estimates) - n_pos
    stats = (f"{len(sig_estimates)} significant edges ({n_pos} pos / {n_neg} neg)  |  "
             f"{n_with}/{len(constructs)} constructs connected  |  max |γ| = {g_max:.3f}")
    ax.text(0, -lim + 0.3, stats, ha="center", va="bottom", fontsize=9, color="#444444",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

    ax.set_title(title, fontsize=16, fontweight="bold", pad=16, y=0.98)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved: {output_path}")


# ─── Plot: SES-colored circle network ───────────────────────────────────────

def plot_ses_colored_network(enriched_estimates, all_constructs, title, output_path):
    """Domain circle network with edges colored by dominant SES variable."""
    constructs = sorted(all_constructs)
    domains = sorted(set(c.split("|")[0] for c in constructs))
    n_dom = len(domains)
    domain_colors = {d: _CMAP24[i % len(_CMAP24)] for i, d in enumerate(domains)}
    node_colors = {c: domain_colors[c.split("|")[0]] for c in constructs}

    sig_nodes = set()
    degree = defaultdict(int)
    for v in enriched_estimates:
        sig_nodes.add(v["construct_a"])
        sig_nodes.add(v["construct_b"])
        degree[v["construct_a"]] += 1
        degree[v["construct_b"]] += 1

    dam = domain_angles(domains)
    pos = layout_nodes(constructs, dam, n_dom)

    fig, ax = plt.subplots(figsize=(22, 22))
    ax.set_aspect("equal"); ax.axis("off")
    lim = 6.5
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)

    draw_sector_backgrounds(ax, domains, dam, n_dom, inner_r=2.7, outer_r=4.1,
                            domain_colors=domain_colors)

    gamma_vals = [abs(v["dr_gamma"]) for v in enriched_estimates]
    g_max = max(gamma_vals) if gamma_vals else 1.0
    g_min = min(gamma_vals) if gamma_vals else 0.0
    g_range = g_max - g_min if g_max > g_min else 1.0

    for v in sorted(enriched_estimates, key=lambda x: abs(x["dr_gamma"])):
        ca, cb = v["construct_a"], v["construct_b"]
        if ca not in pos or cb not in pos:
            continue
        g = v["dr_gamma"]
        dom_ses = v.get("dominant_ses", "unknown")
        color = SES_COLORS.get(dom_ses, "#999999")
        norm_g = (abs(g) - g_min) / g_range
        alpha = 0.20 + 0.55 * norm_g
        lw = 0.4 + 2.6 * norm_g
        # Dashed for negative γ, solid for positive
        style = "-" if g > 0 else (0, (4, 3))
        ax.annotate("", xy=pos[cb], xytext=pos[ca],
                     arrowprops=dict(arrowstyle="-", color=color, alpha=alpha,
                                     lw=lw, connectionstyle="arc3,rad=0.18",
                                     linestyle=style))

    for c in constructs:
        x, y = pos[c]
        deg = degree.get(c, 0)
        is_sig = c in sig_nodes
        size = (40 + min(deg * 14, 200)) if is_sig else 12
        color = node_colors[c] if is_sig else "#cccccc"
        alpha = 0.92 if is_sig else 0.45
        ec = "white" if is_sig else "#aaaaaa"
        lw = 0.7 if is_sig else 0.3
        zorder = 5 if is_sig else 3
        ax.scatter(x, y, s=size, c=color, zorder=zorder, edgecolors=ec,
                   linewidths=lw, alpha=alpha)

    deg_threshold = max(5, np.percentile(list(degree.values()) or [0], 70))
    for c in constructs:
        if c in sig_nodes and degree.get(c, 0) >= deg_threshold:
            x, y = pos[c]
            short = c.split("|")[1].replace("_", " ")[:14]
            ax.text(x, y, short, ha="center", va="center", fontsize=4.5, zorder=6,
                    color="white" if degree.get(c, 0) >= 10 else "black",
                    fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=1.2, foreground="black")])

    label_radius = 4.75
    for dom in domains:
        angle = dam[dom]
        lx, ly = label_radius * np.cos(angle), label_radius * np.sin(angle)
        label = DOMAIN_LABELS.get(dom, dom)
        ha = "left" if lx > 0.3 else ("right" if lx < -0.3 else "center")
        ax.text(lx, ly, f"{dom}\n{label}", ha=ha, va="center", fontsize=8.5,
                fontweight="bold", color=domain_colors[dom],
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")], zorder=6)

    # SES legend
    legend_elements = [
        mpatches.Patch(facecolor=SES_COLORS[k], alpha=0.8,
                       label=f"{SES_LABELS[k]}  ({k})")
        for k in ["escol", "Tam_loc", "sexo", "edad"]
    ]
    legend_elements.extend([
        plt.Line2D([0], [0], color="grey", lw=1.5, linestyle="-",  label="γ > 0 (solid)"),
        plt.Line2D([0], [0], color="grey", lw=1.5, linestyle="--", label="γ < 0 (dashed)"),
    ])
    ax.legend(handles=legend_elements, loc="lower left", bbox_to_anchor=(0.01, 0.01),
              fontsize=9, framealpha=0.85, title="Dominant SES dimension", title_fontsize=9)

    # SES dominance counts
    dom_counts = Counter(v["dominant_ses"] for v in enriched_estimates)
    dom_str = "  |  ".join(f"{SES_LABELS.get(k,k)}: {n}" for k, n in dom_counts.most_common())
    n_with = sum(1 for c in constructs if degree.get(c, 0) > 0)
    stats = (f"{len(enriched_estimates)} edges  |  {dom_str}  |  "
             f"{n_with}/{len(constructs)} connected  |  max |γ| = {g_max:.3f}")
    ax.text(0, -lim + 0.3, stats, ha="center", va="bottom", fontsize=8.5, color="#444444",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

    ax.set_title(title, fontsize=15, fontweight="bold", pad=16, y=0.98)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved: {output_path}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Load sweep
    sweep_path = RESULTS / "construct_dr_sweep_v5_julia_v4.json"
    print(f"Loading sweep: {sweep_path.name}")
    estimates = load_julia_sweep(sweep_path)

    # Load fingerprints
    fp_path = RESULTS / "ses_fingerprints.json"
    print(f"Loading fingerprints: {fp_path.name}")
    fingerprints = load_fingerprints(fp_path)

    # Load manifest for full construct list
    manifest_path = RESULTS / "construct_variable_manifest.json"
    all_constructs = set()
    if manifest_path.exists():
        with open(manifest_path) as f:
            for entry in json.load(f):
                if "key" in entry:
                    all_constructs.add(entry["key"])
    for v in estimates.values():
        all_constructs.add(v["construct_a"])
        all_constructs.add(v["construct_b"])
    print(f"Constructs: {len(all_constructs)}")

    # Filter significant
    sig = [v for v in estimates.values()
           if v.get("excl_zero") and "dr_gamma" in v]
    print(f"Significant edges: {len(sig)}")

    # ── 1. Descriptive stats ─────────────────────────────────────────────
    gammas = [v["dr_gamma"] for v in sig]
    abs_gammas = [abs(g) for g in gammas]
    n_pos = sum(1 for g in gammas if g > 0)
    n_neg = len(gammas) - n_pos
    print(f"\n{'='*60}")
    print("POST-REALIGNMENT LOS_MEX NETWORK DESCRIPTIVES")
    print(f"{'='*60}")
    print(f"Significant edges: {len(sig)}")
    print(f"Sign split: {n_pos} pos ({100*n_pos/len(sig):.0f}%) / {n_neg} neg ({100*n_neg/len(sig):.0f}%)")
    print(f"|γ| median={np.median(abs_gammas):.4f}  mean={np.mean(abs_gammas):.4f}  max={max(abs_gammas):.4f}")
    print(f"Top 5 by |γ|:")
    for v in sorted(sig, key=lambda x: abs(x["dr_gamma"]), reverse=True)[:5]:
        print(f"  γ={v['dr_gamma']:+.4f}  {v['construct_a']} × {v['construct_b']}")

    # ── 2. Standard circle network ───────────────────────────────────────
    print(f"\nPlotting standard circle network...")
    plot_standard_network(
        sig, all_constructs,
        title=("SES Bridge — Los Mex Construct Network (Post-Realignment)\n"
               "Significant DR γ pairs (CI excludes zero)  |  Tam_loc corrected, continuous edad"),
        output_path=RESULTS / "domain_circle_network_post_realignment.png",
    )

    # ── 3. Bipartite structure ───────────────────────────────────────────
    print(f"\nChecking bipartite structure...")
    bp = check_bipartite_structure(sig)
    print(f"Nodes: {bp['n_nodes']}  Edges: {bp['n_edges']}")
    print(f"Sign split: {bp['sign_split']}")
    print(f"Triangles: {bp['n_triangles']} ({bp['n_balanced']} balanced / {bp['n_frustrated']} frustrated)")
    print(f"Structural balance: {bp['balance_pct']:.1f}%")

    # ── 4. SES dominance per bridge ──────────────────────────────────────
    print(f"\nComputing SES dominance per bridge...")
    enriched = compute_ses_dominance(sig, fingerprints)
    dom_counts = Counter(v["dominant_ses"] for v in enriched)
    print("Dominant SES dimension distribution:")
    for dim, cnt in dom_counts.most_common():
        pct = 100 * cnt / len(enriched)
        label = SES_LABELS.get(dim, dim)
        print(f"  {label} ({dim}): {cnt} ({pct:.1f}%)")

    # Per-SES-dimension stats
    print("\nMedian |γ| by dominant SES dimension:")
    for dim in ["escol", "Tam_loc", "sexo", "edad"]:
        vals = [abs(v["dr_gamma"]) for v in enriched if v["dominant_ses"] == dim]
        if vals:
            print(f"  {SES_LABELS[dim]:15s}: med |γ|={np.median(vals):.4f}  n={len(vals)}")

    # ── 5. SES-colored circle network ────────────────────────────────────
    print(f"\nPlotting SES-colored circle network...")
    plot_ses_colored_network(
        enriched, all_constructs,
        title=("SES Bridge — Los Mex Network by Dominant SES Dimension\n"
               "Edge color = primary SES driver  |  solid = γ>0, dashed = γ<0"),
        output_path=RESULTS / "domain_circle_network_ses_colored.png",
    )

    # ── 6. Write report ──────────────────────────────────────────────────
    report_path = RESULTS / "post_realignment_report.md"
    with open(report_path, "w") as f:
        f.write("# Post-SES-Realignment Analysis — Los Mex\n\n")
        f.write("## Realignment Changes\n\n")
        f.write("1. **Tam_loc**: reversed to 1=rural → 4=urban (matching WVS)\n")
        f.write("2. **Escol**: WVS ISCED boundaries realigned to Mexican levels\n")
        f.write("3. **Edad**: continuous numeric age (no 7-bin discretization)\n\n")

        f.write("## Network Descriptives\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Significant edges | {len(sig)} |\n")
        f.write(f"| Sign split | {n_pos} pos / {n_neg} neg ({100*n_pos/len(sig):.0f}%/{100*n_neg/len(sig):.0f}%) |\n")
        f.write(f"| Med \\|γ\\| | {np.median(abs_gammas):.4f} |\n")
        f.write(f"| Mean \\|γ\\| | {np.mean(abs_gammas):.4f} |\n")
        f.write(f"| Max \\|γ\\| | {max(abs_gammas):.4f} |\n")
        f.write(f"| Constructs connected | {bp['n_nodes']} |\n\n")

        f.write("## Bipartite Structure\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Triangles | {bp['n_triangles']} |\n")
        f.write(f"| Balanced | {bp['n_balanced']} ({bp['balance_pct']:.1f}%) |\n")
        f.write(f"| Frustrated | {bp['n_frustrated']} ({100-bp['balance_pct']:.1f}%) |\n\n")

        f.write("## SES Dominance per Bridge\n\n")
        f.write(f"| SES Dimension | Count | % | Med \\|γ\\| |\n")
        f.write(f"|--------------|-------|---|----------|\n")
        for dim in ["escol", "Tam_loc", "sexo", "edad"]:
            cnt = dom_counts.get(dim, 0)
            pct = 100 * cnt / len(enriched) if enriched else 0
            vals = [abs(v["dr_gamma"]) for v in enriched if v["dominant_ses"] == dim]
            med = np.median(vals) if vals else 0
            f.write(f"| {SES_LABELS[dim]} ({dim}) | {cnt} | {pct:.1f}% | {med:.4f} |\n")
        unk = dom_counts.get("unknown", 0)
        if unk:
            f.write(f"| Unknown | {unk} | {100*unk/len(enriched):.1f}% | — |\n")

        f.write(f"\n## Top 10 Bridges by |γ|\n\n")
        f.write(f"| γ | Dominant SES | Construct A | Construct B |\n")
        f.write(f"|---|------------|-------------|-------------|\n")
        for v in sorted(enriched, key=lambda x: abs(x["dr_gamma"]), reverse=True)[:10]:
            f.write(f"| {v['dr_gamma']:+.4f} | {v['dominant_ses']} | {v['construct_a']} | {v['construct_b']} |\n")

        f.write(f"\n## Output Files\n\n")
        f.write(f"- `domain_circle_network_post_realignment.png` — standard network (sign-colored)\n")
        f.write(f"- `domain_circle_network_ses_colored.png` — network colored by dominant SES\n")
        f.write(f"- `post_realignment_report.md` — this report\n")

    print(f"\nReport: {report_path}")
    print("Done.")


if __name__ == "__main__":
    main()
