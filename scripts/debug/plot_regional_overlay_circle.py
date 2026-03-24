"""
Single circle with ALL regional edges overlaid — lines colored by cultural zone.

All 8 zones' significant γ bridges on one construct circle. Each zone's edges
use its zone color regardless of γ sign. The overlay shows which zones
have dense SES structuring and where their patterns overlap or diverge.

Run:
  conda run -n nvg_py13_env python scripts/debug/plot_regional_overlay_circle.py
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
OUT = ROOT / 'data/results/regional_overlay_circle.png'

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

# --- Organize sig edges by zone ---
zone_edges = defaultdict(list)
all_constructs = set()
for key, est in estimates.items():
    if "dr_gamma" not in est or not est.get("excl_zero"):
        continue
    parts = key.split("::")
    if len(parts) != 3:
        continue
    country = parts[0].split("_")[2]
    zone = COUNTRY_ZONE.get(country, "Unknown")
    va, vb = parts[1], parts[2]
    zone_edges[zone].append({"va": va, "vb": vb, "gamma": est["dr_gamma"]})
    all_constructs.add(va)
    all_constructs.add(vb)

all_constructs = sorted(all_constructs)
domains = sorted(set(construct_domain(c) for c in all_constructs))
n_dom = len(domains)
domain_colors = {d: _CMAP9[i % len(_CMAP9)] for i, d in enumerate(domains)}

for z in sorted(zone_edges):
    print(f"  {z}: {len(zone_edges[z]):,} sig edges")

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

# --- Plot ---
fig, ax = plt.subplots(figsize=(28, 28))
ax.set_aspect("equal")
ax.axis("off")
ax.set_xlim(-7, 7)
ax.set_ylim(-7, 7)

# Sector backgrounds
sector_deg = 360 / n_dom
half_deg = sector_deg / 2
for dom in domains:
    angle_deg = np.degrees(dam[dom])
    w = Wedge((0, 0), 4.1, angle_deg - half_deg, angle_deg + half_deg,
              width=1.3, facecolor=domain_colors[dom], alpha=0.06,
              edgecolor=domain_colors[dom], linewidth=0.3)
    ax.add_patch(w)

# --- Find universal bridges (significant in 40+ countries) ---
from collections import Counter as Ctr
pair_sig_count = Ctr()
for zone, edges in zone_edges.items():
    for e in edges:
        pid = tuple(sorted([e["va"], e["vb"]]))
        pair_sig_count[pid] += 1
UNIVERSAL_THRESH = 40
universal_pairs = {pid for pid, cnt in pair_sig_count.items() if cnt >= UNIVERSAL_THRESH}
print(f"  Universal bridges (sig in {UNIVERSAL_THRESH}+ countries): {len(universal_pairs)}")

# --- Draw country lines: alpha=0.03, colored by zone ---
zone_order = sorted(zone_edges.keys(), key=lambda z: len(zone_edges[z]))
for zone in zone_order:
    edges = zone_edges[zone]
    color = ZONE_COLORS.get(zone, "#cccccc")
    for e in edges:
        va, vb = e["va"], e["vb"]
        if va not in pos or vb not in pos:
            continue
        ax.plot([pos[va][0], pos[vb][0]], [pos[va][1], pos[vb][1]],
                color=color, alpha=0.03, lw=0.5, solid_capstyle='round')

# --- Draw universal bridges on top: thick gray ---
for pid in universal_pairs:
    va, vb = pid
    if va not in pos or vb not in pos:
        continue
    cnt = pair_sig_count[pid]
    strength = (cnt - UNIVERSAL_THRESH) / (66 - UNIVERSAL_THRESH)
    lw = 1.5 + 3.0 * strength
    alpha = 0.3 + 0.4 * strength
    ax.plot([pos[va][0], pos[vb][0]], [pos[va][1], pos[vb][1]],
            color='#333333', alpha=alpha, lw=lw, solid_capstyle='round', zorder=4)

# Nodes + construct labels
for c in all_constructs:
    dom = construct_domain(c)
    ax.plot(pos[c][0], pos[c][1], 'o', color=domain_colors[dom],
            markersize=6, markeredgecolor='white', markeredgewidth=0.5, zorder=10)

    # Construct name label — radially outward from circle
    x, y = pos[c]
    angle = np.arctan2(y, x)
    lx = (radius + 0.45) * np.cos(angle)
    ly = (radius + 0.45) * np.sin(angle)
    rot = np.degrees(angle)
    if rot > 90: rot -= 180
    if rot < -90: rot += 180
    ha = 'left' if -np.pi/2 < angle < np.pi/2 else 'right'
    short_name = c.split("|")[0].replace("wvs_agg_", "").replace("_", " ")
    # Truncate long names
    if len(short_name) > 25:
        short_name = short_name[:23] + ".."
    ax.text(lx, ly, short_name, ha=ha, va='center', fontsize=5.5,
            rotation=rot, rotation_mode='anchor', color=domain_colors[dom], alpha=0.85)

# Domain labels on outer ring
for dom in domains:
    angle = dam[dom]
    lx, ly = 5.8 * np.cos(angle), 5.8 * np.sin(angle)
    label = WVS_DOMAIN_LABELS.get(dom, dom)
    ax.text(lx, ly, label, ha='center', va='center', fontsize=11,
            fontweight='bold', color=domain_colors[dom])

# Zone legend
zone_patches = [Patch(facecolor=v, label=f"{k} ({len(zone_edges.get(k,[])):,})")
                for k, v in ZONE_COLORS.items()]
ax.legend(handles=zone_patches, loc='lower right', fontsize=10, framealpha=0.9,
          title="Cultural Zone (sig edges)", title_fontsize=11)

ax.set_title("Global SES Bridge Network — 66 Countries, Colored by Cultural Zone\n"
             "Each significant γ bridge drawn once per country at α=0.05\n"
             "Density (saturation) = how many countries share that bridge",
             fontsize=15, y=1.01)

fig.savefig(OUT, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nSaved: {OUT}")
