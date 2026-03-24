"""
Country anomaly circle: each country's γ deviation from global mean.

Single circle with constructs. For each country, draw its anomalous bridges
(where that country's γ deviates most from the 66-country mean).
Color = zone. Red hue = stronger than global, blue hue = weaker.

Run:
  conda run -n nvg_py13_env python scripts/debug/plot_country_anomaly_circle.py
"""
import json, sys, numpy as np
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Patch
from matplotlib.colors import to_rgba
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
    parts = key.split("|")
    return parts[1] if len(parts) > 1 else "UNK"

# --- Load ---
print("Loading...")
with open(SWEEP_PATH) as f:
    data = json.load(f)
estimates = data.get("estimates", {})

# --- Collect γ per pair per country ---
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
    pid = tuple(sorted([va, vb]))
    g = est["dr_gamma"]
    pair_country_gamma[pid][country] = g
    pair_global_gammas[pid].append(g)
    all_constructs.add(va)
    all_constructs.add(vb)

pair_global_mean = {pid: np.mean(gs) for pid, gs in pair_global_gammas.items()}
all_constructs = sorted(all_constructs)
domains = sorted(set(construct_domain(c) for c in all_constructs))
n_dom = len(domains)
domain_colors = {d: _CMAP9[i % len(_CMAP9)] for i, d in enumerate(domains)}

# --- Per-country anomaly stats ---
country_anomalies = {}
for country in sorted(set(c for pids in pair_country_gamma.values() for c in pids)):
    anoms = []
    for pid, cg in pair_country_gamma.items():
        if country not in cg:
            continue
        anoms.append((pid, cg[country] - pair_global_mean[pid]))
    country_anomalies[country] = anoms

# --- Layout ---
by_dom = defaultdict(list)
for c in all_constructs:
    by_dom[construct_domain(c)].append(c)
sector = 2 * np.pi / n_dom
spread = 0.68
half = sector * spread / 2
dam = {d: np.pi/2 - i * sector for i, d in enumerate(sorted(by_dom.keys()))}
radius = 3.4
pos = {}
for dom, members in by_dom.items():
    center = dam[dom]
    n = len(members)
    angles = np.linspace(center - half, center + half, n) if n > 1 else [center]
    for angle, c in zip(angles, sorted(members)):
        pos[c] = (radius * np.cos(angle), radius * np.sin(angle))

# --- Sort countries by mean |anomaly| ---
country_mean_anom = {}
for country, anoms in country_anomalies.items():
    country_mean_anom[country] = np.mean([abs(a) for _, a in anoms])
sorted_countries = sorted(country_mean_anom.keys(), key=lambda c: -country_mean_anom[c])

# --- Plot: top 20 most anomalous + bottom 5 least ---
selected = sorted_countries[:20] + sorted_countries[-5:]
n_sel = len(selected)
ncols = 5
nrows = (n_sel + ncols - 1) // ncols

fig, axes = plt.subplots(nrows, ncols, figsize=(8 * ncols, 8 * nrows))
axes = axes.flatten()

for ci, country in enumerate(selected):
    ax = axes[ci]
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-5.5, 5.5)
    ax.set_ylim(-5.5, 5.5)

    # Sector backgrounds
    sector_deg = 360 / n_dom
    half_deg = sector_deg / 2
    for dom in domains:
        angle_deg = np.degrees(dam[dom])
        w = Wedge((0, 0), 4.1, angle_deg - half_deg, angle_deg + half_deg,
                  width=1.3, facecolor=domain_colors[dom], alpha=0.06,
                  edgecolor=domain_colors[dom], linewidth=0.3)
        ax.add_patch(w)

    anoms = country_anomalies[country]
    anoms.sort(key=lambda x: abs(x[1]))
    anom_max = max(abs(a) for _, a in anoms) if anoms else 1
    median_anom = np.median([abs(a) for _, a in anoms])

    # Draw only above-median anomalies
    drawn = 0
    for pid, anomaly in anoms:
        if abs(anomaly) < median_anom:
            continue
        va, vb = pid
        if va not in pos or vb not in pos:
            continue
        strength = min(abs(anomaly) / max(anom_max, 0.001), 1.0)
        color = "#d73027" if anomaly > 0 else "#4575b4"
        alpha = 0.2 + 0.6 * strength
        lw = 0.5 + 3.5 * strength
        ax.plot([pos[va][0], pos[vb][0]], [pos[va][1], pos[vb][1]],
                color=color, alpha=alpha, lw=lw, solid_capstyle='round')
        drawn += 1

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
        ax.text(lx, ly, label, ha='center', va='center', fontsize=6,
                fontweight='bold', color=domain_colors[dom], alpha=0.7)

    zone = COUNTRY_ZONE.get(country, "Unknown")
    zone_color = ZONE_COLORS.get(zone, "#333333")
    rank = sorted_countries.index(country) + 1
    mean_a = country_mean_anom[country]
    ax.set_title(f"{country} ({zone[:12]})\n"
                 f"Rank {rank}/66 | mean|anom|={mean_a:.4f} | {drawn} edges\n"
                 f"red = stronger than global, blue = weaker",
                 fontsize=9, fontweight='bold', color=zone_color)

# Hide unused axes
for i in range(n_sel, len(axes)):
    axes[i].set_visible(False)

fig.suptitle("Country γ-Anomalies: Deviation from Global Mean\n"
             "Top 20 most anomalous countries + 5 least anomalous\n"
             "Red = country has stronger SES bridge than world | Blue = weaker",
             fontsize=16, y=1.01)
fig.tight_layout()
fig.savefig(OUT / 'country_anomaly_circles.png', dpi=120, bbox_inches='tight')
plt.close(fig)
print(f"Saved: country_anomaly_circles.png")

# --- Summary table ---
print(f"\n{'Rank':<5} {'Country':<6} {'Zone':<22} {'Mean|anom|':>10}")
print("-" * 48)
for i, c in enumerate(sorted_countries):
    marker = " ← MEX" if c == "MEX" else ""
    if i < 20 or i >= len(sorted_countries) - 5 or c == "MEX":
        print(f"{i+1:<5} {c:<6} {COUNTRY_ZONE.get(c,'?'):<22} {country_mean_anom[c]:>10.4f}{marker}")
    elif i == 20:
        print("  ...")
