"""
Regional anomaly circles: how each zone's γ deviates from global mean.

For each construct pair, compute global mean γ across all 66 countries.
Then per zone, show only pairs where zone mean γ deviates significantly
from global mean. Red = stronger than global, blue = weaker.

This reveals what's DIFFERENT about each zone's SES structure,
not what's shared (which is almost everything).

Run:
  conda run -n nvg_py13_env python scripts/debug/plot_regional_anomaly_circles.py
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

# --- Collect γ per pair per zone ---
pair_zone_gammas = defaultdict(lambda: defaultdict(list))  # pair → zone → [γ values]
pair_global_gammas = defaultdict(list)  # pair → [all γ values]
all_constructs = set()

for key, est in estimates.items():
    if "dr_gamma" not in est:
        continue
    parts = key.split("::")
    if len(parts) != 3:
        continue
    country = parts[0].split("_")[2]
    zone = COUNTRY_ZONE.get(country, "Unknown")
    va, vb = parts[1], parts[2]
    pid = tuple(sorted([va, vb]))
    g = est["dr_gamma"]
    pair_zone_gammas[pid][zone].append(g)
    pair_global_gammas[pid].append(g)
    all_constructs.add(va)
    all_constructs.add(vb)

all_constructs = sorted(all_constructs)
domains = sorted(set(construct_domain(c) for c in all_constructs))
n_dom = len(domains)
domain_colors = {d: _CMAP9[i % len(_CMAP9)] for i, d in enumerate(domains)}

# --- Global mean γ per pair ---
pair_global_mean = {pid: np.mean(gs) for pid, gs in pair_global_gammas.items()}

# --- Per-zone anomaly: zone_mean - global_mean ---
zone_anomalies = {}  # zone → [(pair, anomaly, zone_mean, global_mean)]
for zone in CULTURAL_ZONES:
    anomalies = []
    for pid in pair_global_mean:
        if zone not in pair_zone_gammas[pid]:
            continue
        zone_gs = pair_zone_gammas[pid][zone]
        if len(zone_gs) < 3:
            continue
        zone_mean = np.mean(zone_gs)
        global_mean = pair_global_mean[pid]
        anomaly = zone_mean - global_mean
        anomalies.append((pid, anomaly, zone_mean, global_mean))
    zone_anomalies[zone] = anomalies

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

# --- Plot: 8 panels ---
fig, axes = plt.subplots(2, 4, figsize=(40, 20))
axes = axes.flatten()
zone_names = sorted(CULTURAL_ZONES.keys())

for zi, zone in enumerate(zone_names):
    ax = axes[zi]
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

    anomalies = zone_anomalies.get(zone, [])
    if not anomalies:
        ax.set_title(f"{zone}\nNo data", fontsize=11)
        continue

    # Sort by |anomaly| — draw weakest first
    anomalies.sort(key=lambda x: abs(x[1]))
    anom_max = max(abs(a[1]) for a in anomalies)

    # Only draw pairs with meaningful anomaly (top 50% by |anomaly|)
    median_anom = np.median([abs(a[1]) for a in anomalies])
    drawn = 0

    for pid, anomaly, zone_mean, global_mean in anomalies:
        if abs(anomaly) < median_anom:
            continue
        va, vb = pid
        if va not in pos or vb not in pos:
            continue

        strength = abs(anomaly) / max(anom_max, 0.001)
        # Red = zone stronger than global, Blue = zone weaker
        color = "#d73027" if anomaly > 0 else "#4575b4"
        alpha = 0.15 + 0.6 * strength
        lw = 0.4 + 3.0 * strength
        ax.plot([pos[va][0], pos[vb][0]], [pos[va][1], pos[vb][1]],
                color=color, alpha=alpha, lw=lw, solid_capstyle='round')
        drawn += 1

    # Nodes
    for c in all_constructs:
        dom = construct_domain(c)
        ax.plot(pos[c][0], pos[c][1], 'o', color=domain_colors[dom],
                markersize=3.5, markeredgecolor='white', markeredgewidth=0.3, zorder=5)

    # Domain labels
    for dom in domains:
        angle = dam[dom]
        lx, ly = 4.6 * np.cos(angle), 4.6 * np.sin(angle)
        label = WVS_DOMAIN_LABELS.get(dom, dom)
        ax.text(lx, ly, label, ha='center', va='center', fontsize=6,
                fontweight='bold', color=domain_colors[dom], alpha=0.7)

    # Stats
    n_stronger = sum(1 for _, a, _, _ in anomalies if a > median_anom)
    n_weaker = sum(1 for _, a, _, _ in anomalies if a < -median_anom)
    mean_anom = np.mean([a[1] for a in anomalies])

    ax.set_title(f"{zone}\n"
                 f"{drawn} anomalous bridges | mean anomaly: {mean_anom:+.4f}\n"
                 f"red = stronger than global, blue = weaker",
                 fontsize=10, fontweight='bold',
                 color=ZONE_COLORS.get(zone, 'black'))

fig.suptitle("SES Bridge Anomalies by Cultural Zone\n"
             "How each zone's γ DEVIATES from the 66-country global mean\n"
             "Red = zone has stronger SES bridge than world average | Blue = weaker",
             fontsize=16, y=1.02)
fig.tight_layout()
fig.savefig(OUT / 'regional_anomaly_circles.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"Saved: regional_anomaly_circles.png")

# --- Print top anomalies per zone ---
print(f"\nTop 5 anomalies per zone:")
for zone in zone_names:
    anomalies = zone_anomalies.get(zone, [])
    top = sorted(anomalies, key=lambda x: -abs(x[1]))[:5]
    print(f"\n  {zone}:")
    for pid, anom, zmean, gmean in top:
        va = pid[0].split("|")[0].replace("wvs_agg_", "")
        vb = pid[1].split("|")[0].replace("wvs_agg_", "")
        direction = "STRONGER" if anom > 0 else "WEAKER"
        print(f"    {direction:8s} Δ={anom:+.4f} (zone={zmean:+.4f} vs global={gmean:+.4f}): "
              f"{va[:25]} × {vb[:25]}")

print("\nDone.")
