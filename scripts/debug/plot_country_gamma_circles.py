"""
Country circle networks: actual γ values (not anomalies).

Same layout as anomaly circles but edges show raw γ values.
Red = positive γ, blue = negative, intensity = |γ|.
Bottom-right legend: summary stats per country.

Generates TWO plots:
  1. country_gamma_circles.png — top 20 + bottom 5 by mean |γ| (actual values)
  2. country_anomaly_circles_v2.png — same countries, anomaly view (with legend)

Run:
  conda run -n nvg_py13_env python scripts/debug/plot_country_gamma_circles.py
"""
import json, sys, numpy as np
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

SWEEP_PATH = ROOT / 'data/results/wvs_geographic_sweep_w7.json'
OUT = ROOT / 'data/results'

ZONE_COLORS = {
    "Latin America": "#e41a1c", "English-speaking": "#377eb8",
    "Protestant Europe": "#4daf4a", "Catholic Europe": "#984ea3",
    "Orthodox/ex-Communist": "#ff7f00", "Confucian": "#a65628",
    "South/Southeast Asian": "#f781bf", "African-Islamic": "#999999",
}
WVS_DOMAIN_LABELS = {
    "WVS_A": "Social\nValues", "WVS_B": "Environ.", "WVS_C": "Work",
    "WVS_D": "Family", "WVS_E": "Politics", "WVS_F": "Religion\n/Morality",
    "WVS_G": "Identity", "WVS_H": "Security", "WVS_I": "Science\n/Tech",
}
_CMAP9 = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
           "#edc948", "#b07aa1", "#ff9da7", "#9c755f"]

def construct_domain(key):
    return key.split("|")[1] if "|" in key else "UNK"

# --- Load ---
print("Loading...")
with open(SWEEP_PATH) as f:
    data = json.load(f)
estimates = data.get("estimates", {})

# --- Collect per country ---
country_sig_edges = defaultdict(list)     # country → [(va, vb, gamma)]
country_all_gammas = defaultdict(list)    # country → [all gamma values]
pair_country_gamma = defaultdict(dict)
pair_global_gammas = defaultdict(list)
all_constructs = set()

for key, est in estimates.items():
    if "dr_gamma" not in est:
        continue
    parts = key.split("::")
    if len(parts) != 3:
        continue
    country = parts[0].split("_")[2]
    va, vb = parts[1], parts[2]
    g = est["dr_gamma"]
    pid = tuple(sorted([va, vb]))
    pair_country_gamma[pid][country] = g
    pair_global_gammas[pid].append(g)
    country_all_gammas[country].append(g)
    if est.get("excl_zero"):
        country_sig_edges[country].append((va, vb, g))
    all_constructs.add(va)
    all_constructs.add(vb)

pair_global_mean = {pid: np.mean(gs) for pid, gs in pair_global_gammas.items()}
all_constructs = sorted(all_constructs)
domains = sorted(set(construct_domain(c) for c in all_constructs))
n_dom = len(domains)
domain_colors = {d: _CMAP9[i % len(_CMAP9)] for i, d in enumerate(domains)}

# --- Layout ---
by_dom = defaultdict(list)
for c in all_constructs:
    by_dom[construct_domain(c)].append(c)
sector = 2 * np.pi / n_dom
spread = 0.68
half_s = sector * spread / 2
dam = {d: np.pi/2 - i * sector for i, d in enumerate(sorted(by_dom.keys()))}
radius = 3.4
pos = {}
for dom, members in by_dom.items():
    center = dam[dom]
    n = len(members)
    angles = np.linspace(center - half_s, center + half_s, n) if n > 1 else [center]
    for angle, c in zip(angles, sorted(members)):
        pos[c] = (radius * np.cos(angle), radius * np.sin(angle))

# --- Country stats ---
country_stats = {}
for country in country_all_gammas:
    gs = country_all_gammas[country]
    sig = country_sig_edges[country]
    anoms = []
    for pid, cg in pair_country_gamma.items():
        if country in cg:
            anoms.append(abs(cg[country] - pair_global_mean[pid]))
    country_stats[country] = {
        "n_sig": len(sig),
        "n_total": len(gs),
        "pct_sig": 100 * len(sig) / max(len(gs), 1),
        "med_abs_gamma": np.median(np.abs(gs)),
        "mean_abs_gamma": np.mean(np.abs(gs)),
        "max_abs_gamma": np.max(np.abs(gs)),
        "mean_anom": np.mean(anoms) if anoms else 0,
    }

# --- Select countries: top/bottom by mean |γ| ---
sorted_by_gamma = sorted(country_stats.keys(), key=lambda c: -country_stats[c]["med_abs_gamma"])
sorted_by_anom = sorted(country_stats.keys(), key=lambda c: -country_stats[c]["mean_anom"])

# Use top 20 by |γ| + bottom 5 + MEX if not already in
selected_gamma = sorted_by_gamma[:20] + sorted_by_gamma[-5:]
if "MEX" not in selected_gamma:
    selected_gamma.append("MEX")

selected_anom = sorted_by_anom[:20] + sorted_by_anom[-5:]
if "MEX" not in selected_anom:
    selected_anom.append("MEX")


def draw_circle_panel(ax, country, edges, mode="actual"):
    """Draw one country's circle network.
    mode='actual': edges colored by γ sign/magnitude
    mode='anomaly': edges colored by deviation from global mean
    """
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-5.8, 5.8)
    ax.set_ylim(-5.8, 5.8)

    # Sector backgrounds
    sector_deg = 360 / n_dom
    half_deg = sector_deg / 2
    for dom in domains:
        angle_deg = np.degrees(dam[dom])
        w = Wedge((0, 0), 4.1, angle_deg - half_deg, angle_deg + half_deg,
                  width=1.3, facecolor=domain_colors[dom], alpha=0.06,
                  edgecolor=domain_colors[dom], linewidth=0.3)
        ax.add_patch(w)

    if not edges:
        return

    gamma_max = max(abs(e[2]) for e in edges)
    for va, vb, g in sorted(edges, key=lambda x: abs(x[2])):
        if va not in pos or vb not in pos:
            continue

        if mode == "actual":
            value = g
            vmax = gamma_max
        else:
            pid = tuple(sorted([va, vb]))
            value = g - pair_global_mean.get(pid, 0)
            vmax = gamma_max  # scale to same range

        strength = min(abs(value) / max(vmax, 0.001), 1.0)
        color = "#d73027" if value > 0 else "#4575b4"
        alpha = 0.15 + 0.55 * strength
        lw = 0.4 + 3.0 * strength
        ax.plot([pos[va][0], pos[vb][0]], [pos[va][1], pos[vb][1]],
                color=color, alpha=alpha, lw=lw, solid_capstyle='round')

    # Nodes
    for c in all_constructs:
        dom = construct_domain(c)
        ax.plot(pos[c][0], pos[c][1], 'o', color=domain_colors[dom],
                markersize=3, markeredgecolor='white', markeredgewidth=0.3, zorder=5)

    # Domain labels
    for dom in domains:
        angle = dam[dom]
        lx, ly = 4.6 * np.cos(angle), 4.6 * np.sin(angle)
        label = WVS_DOMAIN_LABELS.get(dom, dom)
        ax.text(lx, ly, label, ha='center', va='center', fontsize=5.5,
                fontweight='bold', color=domain_colors[dom], alpha=0.7)

    # Stats legend box
    cs = country_stats[country]
    zone = COUNTRY_ZONE.get(country, "?")
    rank_gamma = sorted_by_gamma.index(country) + 1
    rank_anom = sorted_by_anom.index(country) + 1
    legend_text = (
        f"Sig: {cs['n_sig']}/{cs['n_total']} ({cs['pct_sig']:.0f}%)\n"
        f"Med|γ|: {cs['med_abs_gamma']:.4f}\n"
        f"Max|γ|: {cs['max_abs_gamma']:.4f}\n"
        f"Mean|anom|: {cs['mean_anom']:.4f}\n"
        f"|γ| rank: {rank_gamma}/66\n"
        f"Anom rank: {rank_anom}/66"
    )
    ax.text(0.98, 0.02, legend_text, transform=ax.transAxes, fontsize=6,
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85),
            family='monospace')


def make_plot(selected, mode, filename, title):
    n_sel = len(selected)
    ncols = 5
    nrows = (n_sel + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(8 * ncols, 8 * nrows))
    axes = axes.flatten()

    for ci, country in enumerate(selected):
        ax = axes[ci]
        edges = country_sig_edges.get(country, [])
        draw_circle_panel(ax, country, edges, mode=mode)

        zone = COUNTRY_ZONE.get(country, "?")
        zone_color = ZONE_COLORS.get(zone, "#333")
        cs = country_stats[country]

        if mode == "actual":
            subtitle = f"med|γ|={cs['med_abs_gamma']:.4f}"
        else:
            subtitle = f"mean|anom|={cs['mean_anom']:.4f}"

        ax.set_title(f"{country} ({zone[:15]})\n{subtitle}",
                     fontsize=10, fontweight='bold', color=zone_color)

    for i in range(n_sel, len(axes)):
        axes[i].set_visible(False)

    color_label = "red = positive γ, blue = negative" if mode == "actual" \
        else "red = stronger than global, blue = weaker"
    fig.suptitle(f"{title}\n{color_label}",
                 fontsize=16, y=1.01)
    fig.tight_layout()
    fig.savefig(OUT / filename, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {filename}")


# --- Plot 1: Actual γ values ---
make_plot(selected_gamma, "actual", "country_gamma_circles.png",
          "Country SES Bridge Networks — Actual γ Values\n"
          "Top 20 by median |γ| + bottom 5 + MEX")

# --- Plot 2: Anomalies (with legend) ---
make_plot(selected_anom, "anomaly", "country_anomaly_circles_v2.png",
          "Country SES Bridge Anomalies — Deviation from Global Mean\n"
          "Top 20 most anomalous + bottom 5 + MEX")

print("\nDone.")
