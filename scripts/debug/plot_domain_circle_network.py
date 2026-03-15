"""
Domain-Circle Network Plot — WVS DR Sweep

Domains arranged evenly around a circle. Constructs nested within their
domain's arc sector. Significant edges (CI excludes zero) drawn between
constructs; positive γ = warm orange, negative γ = cool blue.

Outputs:
  data/results/domain_circle_network_v4.png           (los_mex construct sweep)
  data/results/domain_circle_network_v5.png           (los_mex variable sweep)
  data/results/domain_circle_network_v5_julia.png     (Julia v2 construct sweep)
  data/results/domain_circle_network_v5_julia_v4.png  (Julia v4: rank-norm + K<3 guard)

Run:
  conda run -n nvg_py13_env python scripts/debug/plot_domain_circle_network.py
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

ROOT = Path(__file__).resolve().parents[2]

# ─── Full domain labels ───────────────────────────────────────────────────────
DOMAIN_LABELS = {
    "CIE": "Ciencia",
    "COR": "Corrupción",
    "CUL": "Cultura\nPolítica",
    "DEP": "Deporte /\nLectura",
    "DER": "Derechos",
    "ECO": "Economía",
    "EDU": "Educación",
    "ENV": "Envejecim.",
    "FAM": "Familia",
    "FED": "Fed. /\nGobierno",
    "GEN": "Género",
    "GLO": "Global.",
    "HAB": "Habitación",
    "IDE": "Identidad",
    "IND": "Industria",
    "JUS": "Justicia",
    "MED": "Medio Amb.",
    "MIG": "Migración",
    "NIN": "Niñez /\nJuventud",
    "POB": "Pobreza",
    "REL": "Religión",
    "SAL": "Salud",
    "SEG": "Seguridad",
    "SOC": "Sociedad\nDigital",
}

# 24 visually distinct colors (tab20 + tab20b extended)
_CMAP24 = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#d37295", "#8cd17d", "#b6992d", "#499894", "#86bcb6",
    "#f1ce63", "#a0cbe8", "#ffbe7d", "#86bcb6", "#e49444",
    "#d4a6c8", "#c5d4e8", "#ff9888", "#a5b8d0",
]

# ─── Geometry helpers ─────────────────────────────────────────────────────────

def domain_angles(domains: list[str]) -> dict[str, float]:
    """Return {domain: center_angle_radians} evenly spaced, starting at top."""
    n = len(domains)
    step = 2 * np.pi / n
    # Start at top (π/2) and go clockwise (subtract angle)
    return {d: np.pi / 2 - i * step for i, d in enumerate(sorted(domains))}


def layout_nodes(
    constructs: list[str],
    domain_angle_map: dict[str, float],
    n_domains: int,
    node_radius: float = 3.4,
    spread_frac: float = 0.68,
) -> dict[str, tuple[float, float]]:
    """
    Spread constructs within their domain's angular sector.
    Returns {construct: (x, y)}.
    """
    sector = 2 * np.pi / n_domains
    half = sector * spread_frac / 2

    # Group by domain
    by_domain: dict[str, list[str]] = defaultdict(list)
    for c in constructs:
        by_domain[c.split("|")[0]].append(c)

    pos = {}
    for dom, members in by_domain.items():
        center = domain_angle_map[dom]
        n = len(members)
        if n == 1:
            angles = [center]
        else:
            angles = np.linspace(center - half, center + half, n)
        for angle, c in zip(angles, sorted(members)):
            pos[c] = (node_radius * np.cos(angle), node_radius * np.sin(angle))
    return pos


def draw_sector_backgrounds(
    ax, domains: list[str], domain_angle_map: dict[str, float],
    n_domains: int, inner_r: float = 2.8, outer_r: float = 4.0,
    domain_colors: dict[str, str] = None,
):
    """Shade the angular sector for each domain."""
    sector_deg = 360 / n_domains
    half_deg = sector_deg / 2
    for dom in domains:
        angle_rad = domain_angle_map[dom]
        angle_deg = np.degrees(angle_rad)
        color = domain_colors.get(dom, "#cccccc")
        w = Wedge(
            center=(0, 0),
            r=outer_r,
            theta1=angle_deg - half_deg,
            theta2=angle_deg + half_deg,
            width=outer_r - inner_r,
            facecolor=color,
            alpha=0.12,
            edgecolor=color,
            linewidth=0.4,
        )
        ax.add_patch(w)


def curved_edge(
    ax, p1: tuple, p2: tuple,
    color: str, alpha: float, lw: float,
    rad: float = 0.25,
):
    """Draw a curved edge between two (x, y) positions."""
    style = f"arc3,rad={rad}"
    ax.annotate(
        "",
        xy=p2, xytext=p1,
        arrowprops=dict(
            arrowstyle="-",
            color=color,
            alpha=alpha,
            lw=lw,
            connectionstyle=style,
        ),
    )


# ─── Main plotting function ───────────────────────────────────────────────────

def plot_network(
    estimates: dict,
    title: str,
    output_path: Path,
    manifest_constructs: list[str] | None = None,  # full construct list from manifest
    gamma_thresh: float = 0.0,   # extra absolute γ threshold (0 = any sig pair)
    figsize: tuple = (22, 22),
):
    # ── Filter significant pairs ──────────────────────────────────────────
    sig = []
    for k, v in estimates.items():
        g = v.get("dr_gamma")
        if g is None:
            continue
        # Prefer excl_zero flag (Julia sets this from full-precision floats;
        # JSON serialization can round CI endpoints to ±0.0000 falsely)
        if "excl_zero" in v:
            is_sig = bool(v["excl_zero"])
        else:
            ci = v.get("dr_gamma_ci")
            if not ci or ci[0] is None or ci[1] is None:
                continue
            is_sig = (ci[0] > 0 or ci[1] < 0)
        if is_sig and abs(g) >= gamma_thresh:
            sig.append(v)

    # ── Build node set — ALL constructs (manifest + estimates) ────────────
    constructs = set()
    if manifest_constructs:
        constructs.update(manifest_constructs)
    # Always add anything in estimates so nothing is missing
    for v in estimates.values():
        ca, cb = v.get("construct_a"), v.get("construct_b")
        if ca: constructs.add(ca)
        if cb: constructs.add(cb)

    # Significant node set (for highlighting)
    sig_nodes: set[str] = set()
    for v in sig:
        sig_nodes.add(v["construct_a"])
        sig_nodes.add(v["construct_b"])

    if not constructs:
        print(f"No constructs found for {title}")
        return

    constructs = sorted(constructs)
    domains = sorted(set(c.split("|")[0] for c in constructs))
    n_dom = len(domains)

    domain_colors = {d: _CMAP24[i % len(_CMAP24)] for i, d in enumerate(domains)}
    node_colors   = {c: domain_colors[c.split("|")[0]] for c in constructs}

    # ── Degree (significant edges only) ──────────────────────────────────
    degree: dict[str, int] = defaultdict(int)
    for v in sig:
        degree[v["construct_a"]] += 1
        degree[v["construct_b"]] += 1

    # ── Layout ────────────────────────────────────────────────────────────
    dam = domain_angles(domains)
    pos = layout_nodes(constructs, dam, n_dom, node_radius=3.4)

    # ── Figure ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect("equal")
    ax.axis("off")

    lim = 6.5
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    # ── Sector backgrounds ────────────────────────────────────────────────
    draw_sector_backgrounds(ax, domains, dam, n_dom,
                            inner_r=2.7, outer_r=4.1,
                            domain_colors=domain_colors)

    # ── Edges ─────────────────────────────────────────────────────────────
    gamma_vals = [abs(v["dr_gamma"]) for v in sig]
    g_max = max(gamma_vals) if gamma_vals else 1.0
    g_min = min(gamma_vals) if gamma_vals else 0.0
    g_range = g_max - g_min if g_max > g_min else 1.0

    for v in sorted(sig, key=lambda x: abs(x["dr_gamma"])):  # draw weakest first
        ca, cb = v["construct_a"], v["construct_b"]
        if ca not in pos or cb not in pos:
            continue
        g = v["dr_gamma"]
        abs_g = abs(g)
        # Color: orange-red = positive γ, steel-blue = negative γ
        color = "#d62728" if g > 0 else "#1f77b4"
        # Alpha and line width scaled to |γ|
        norm_g = (abs_g - g_min) / g_range
        alpha = 0.15 + 0.55 * norm_g
        lw    = 0.4  + 2.6  * norm_g
        # Curvature: slight inward curve
        curved_edge(ax, pos[ca], pos[cb], color=color, alpha=alpha, lw=lw, rad=0.18)

    # ── Nodes ─────────────────────────────────────────────────────────────
    # Draw non-significant nodes first (background layer), then significant on top
    for c in constructs:
        x, y = pos[c]
        deg = degree.get(c, 0)
        is_sig = c in sig_nodes
        if is_sig:
            # Highlighted: domain color, size ∝ degree
            size = 40 + min(deg * 14, 200)
            color = node_colors[c]
            alpha = 0.92
            ec = "white"
            lw = 0.7
            zorder = 5
        else:
            # Dimmed: small grey circle
            size = 12
            color = "#cccccc"
            alpha = 0.45
            ec = "#aaaaaa"
            lw = 0.3
            zorder = 3
        ax.scatter(x, y, s=size, c=color, zorder=zorder,
                   edgecolors=ec, linewidths=lw, alpha=alpha)

    # Short construct labels for high-degree significant nodes only
    deg_threshold = max(5, np.percentile(list(degree.values()) or [0], 70))
    for c in constructs:
        if c in sig_nodes and degree.get(c, 0) >= deg_threshold:
            x, y = pos[c]
            short = c.split("|")[1].replace("_", " ")
            short = short[:14]
            ax.text(x, y, short, ha="center", va="center",
                    fontsize=4.5, zorder=6,
                    color="white" if degree.get(c, 0) >= 10 else "black",
                    fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=1.2, foreground="black")])

    # ── Domain labels (outer ring) ────────────────────────────────────────
    label_radius = 4.75
    for dom in domains:
        angle = dam[dom]
        lx = label_radius * np.cos(angle)
        ly = label_radius * np.sin(angle)
        label = DOMAIN_LABELS.get(dom, dom)
        color = domain_colors[dom]

        ha = "center"
        if lx > 0.3:   ha = "left"
        elif lx < -0.3: ha = "right"

        ax.text(
            lx, ly, f"{dom}\n{label}",
            ha=ha, va="center",
            fontsize=8.5, fontweight="bold",
            color=color,
            path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
            zorder=6,
        )

    # ── Legend ────────────────────────────────────────────────────────────
    legend_elements = [
        mpatches.Patch(facecolor="#d62728", alpha=0.7, label="γ > 0  (positive co-variation)"),
        mpatches.Patch(facecolor="#1f77b4", alpha=0.7, label="γ < 0  (negative co-variation)"),
        plt.scatter([], [], s=30,  c="grey", alpha=0.6, label="Low-degree node"),
        plt.scatter([], [], s=140, c="grey", alpha=0.6, label="High-degree node"),
    ]
    ax.legend(handles=legend_elements, loc="lower left",
              bbox_to_anchor=(0.01, 0.01),
              fontsize=9, framealpha=0.85,
              title="Edge sign / Node degree", title_fontsize=9)

    # ── Stats annotation ──────────────────────────────────────────────────
    n_constructs_with_edges = sum(1 for c in constructs if degree.get(c, 0) > 0)
    stats_text = (
        f"{len(sig)} significant edges  |  "
        f"{n_constructs_with_edges}/{len(constructs)} constructs connected  |  "
        f"max |γ| = {g_max:.3f}"
    )
    ax.text(0, -lim + 0.3, stats_text, ha="center", va="bottom",
            fontsize=9, color="#444444",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

    # ── Title ──────────────────────────────────────────────────────────────
    ax.set_title(title, fontsize=16, fontweight="bold", pad=16, y=0.98)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved: {output_path}")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    # Load full construct list from manifest (v4 construct sweep)
    manifest_path = ROOT / "data" / "results" / "construct_variable_manifest.json"
    manifest_constructs: list[str] = []
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest_data = json.load(f)
        manifest_constructs = [entry["key"] for entry in manifest_data if "key" in entry]
        print(f"Manifest: {len(manifest_constructs)} constructs loaded")

    # V4 — construct-level sweep (los_mex)
    v4_path = ROOT / "data" / "results" / "construct_dr_sweep.json"
    with open(v4_path) as f:
        raw4 = json.load(f)
    e4 = raw4.get("estimates", raw4)

    plot_network(
        estimates=e4,
        title=(
            "SES Bridge — Los Mex Construct Network (V4)\n"
            "Significant DR γ pairs (CI excludes zero)  |  domains as sectors"
        ),
        output_path=ROOT / "data" / "results" / "domain_circle_network_v4.png",
        manifest_constructs=manifest_constructs,
    )

    # V5 — variable-level sweep (los_mex)
    v5_path = ROOT / "data" / "results" / "construct_dr_sweep_v5.json"
    with open(v5_path) as f:
        raw5 = json.load(f)
    e5 = raw5.get("estimates", raw5)

    # V5 uses variable keys (not construct manifest) — pass None to use estimates only
    plot_network(
        estimates=e5,
        title=(
            "SES Bridge — Los Mex Variable Network (V5)\n"
            "Significant DR γ pairs (CI excludes zero)  |  domains as sectors"
        ),
        output_path=ROOT / "data" / "results" / "domain_circle_network_v5.png",
        manifest_constructs=None,
    )

    # V5 Julia v2 — construct-level sweep (Julia NewtonTrustRegion + qcut binning)
    v5j_path = ROOT / "data" / "results" / "construct_dr_sweep_v5_julia_v2.json"
    with open(v5j_path) as f:
        raw5j = json.load(f)
    e5j_raw = raw5j.get("estimates", raw5j)
    e5j = normalize_julia_estimates(e5j_raw)

    plot_network(
        estimates=e5j,
        title=(
            "SES Bridge — Los Mex Construct Network (Julia v2)\n"
            "Significant DR γ pairs (CI excludes zero)  |  NewtonTrustRegion + qcut binning"
        ),
        output_path=ROOT / "data" / "results" / "domain_circle_network_v5_julia.png",
        manifest_constructs=manifest_constructs,
    )

    # V5 Julia v4 — rank-norm + K<3 guard (final calibrated sweep)
    v5j4_path = ROOT / "data" / "results" / "construct_dr_sweep_v5_julia_v4.json"
    with open(v5j4_path) as f:
        raw5j4 = json.load(f)
    e5j4_raw = raw5j4.get("estimates", raw5j4)
    e5j4 = normalize_julia_estimates(e5j4_raw)

    plot_network(
        estimates=e5j4,
        title=(
            "SES Bridge — Los Mex Construct Network (Julia v4)\n"
            "Significant DR γ pairs (CI excludes zero)  |  rank-norm + K<3 guard"
        ),
        output_path=ROOT / "data" / "results" / "domain_circle_network_v5_julia_v4.png",
        manifest_constructs=manifest_constructs,
    )


def normalize_julia_estimates(raw: dict) -> dict:
    """
    Convert Julia sweep output format to the format expected by plot_network.

    Julia keys: "agg_{construct}|{DOMAIN}::{agg_{construct}|{DOMAIN}"
    Julia fields: dr_ci_lo, dr_ci_hi, excl_zero  (no construct_a/b, no dr_gamma_ci list)

    Returns estimates dict with construct_a, construct_b, dr_gamma_ci added.
    """
    out = {}
    for key, v in raw.items():
        if "::" not in key:
            continue
        part_a, part_b = key.split("::", 1)

        def to_ca(part: str) -> str:
            # "agg_construct_name|DOMAIN" → "DOMAIN|construct_name"
            if "|" not in part:
                return part
            name, domain = part.rsplit("|", 1)
            name = name.removeprefix("agg_")
            return f"{domain}|{name}"

        entry = dict(v)
        entry["construct_a"] = to_ca(part_a)
        entry["construct_b"] = to_ca(part_b)

        lo = v.get("dr_ci_lo")
        hi = v.get("dr_ci_hi")
        if lo is not None and hi is not None:
            entry["dr_gamma_ci"] = [lo, hi]

        out[key] = entry
    return out


if __name__ == "__main__":
    main()
