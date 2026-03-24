"""
Regional circle network plots from WVS geographic sweep.

Plot 1: One circle per cultural zone (8 panels). Constructs on the circle,
         edges = significant γ bridges. Transparent lines create density shadow.

Plot 2: Single circle with all countries coded by zone, edges = similarity
         of their γ-vector (correlation of their bridge profiles).

Run:
  conda run -n nvg_py13_env python scripts/debug/plot_regional_circle_networks.py
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
OUT_DIR = ROOT / 'data/results'

ZONE_COLORS = {
    "Latin America": "#e41a1c", "English-speaking": "#377eb8",
    "Protestant Europe": "#4daf4a", "Catholic Europe": "#984ea3",
    "Orthodox/ex-Communist": "#ff7f00", "Confucian": "#a65628",
    "South/Southeast Asian": "#f781bf", "African-Islamic": "#999999",
}

# WVS domain labels
WVS_DOMAIN_LABELS = {
    "WVS_A": "Social Values", "WVS_B": "Environment", "WVS_C": "Work",
    "WVS_D": "Family", "WVS_E": "Politics", "WVS_F": "Religion/Morality",
    "WVS_G": "Identity", "WVS_H": "Security", "WVS_I": "Science/Tech",
}

_CMAP9 = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
           "#edc948", "#b07aa1", "#ff9da7", "#9c755f"]


def parse_key(full_key):
    """'WVS_W7_MEX::va::vb' → (country, va, vb)"""
    parts = full_key.split("::")
    if len(parts) != 3:
        return None, None, None
    country = parts[0].split("_")[2]
    return country, parts[1], parts[2]


def pair_id(va, vb):
    return "::".join(sorted([va, vb]))


def construct_domain(construct_key):
    """'wvs_agg_foo|WVS_E' → 'WVS_E'"""
    parts = construct_key.split("|")
    return parts[1] if len(parts) > 1 else "UNK"


def construct_short(construct_key):
    """'wvs_agg_foo_bar|WVS_E' → 'foo_bar'"""
    col = construct_key.split("|")[0]
    return col.replace("wvs_agg_", "")


# --- Load data ---
print("Loading sweep data...")
with open(SWEEP_PATH) as f:
    data = json.load(f)
estimates = data.get("estimates", {})
print(f"Estimates: {len(estimates)}")

# --- Organize by country ---
by_country = defaultdict(list)
all_constructs = set()
for key, est in estimates.items():
    if "dr_gamma" not in est:
        continue
    country, va, vb = parse_key(key)
    if not country:
        continue
    if est.get("excl_zero", False):
        by_country[country].append({"va": va, "vb": vb, "gamma": est["dr_gamma"]})
    all_constructs.add(va)
    all_constructs.add(vb)

all_constructs = sorted(all_constructs)
domains = sorted(set(construct_domain(c) for c in all_constructs))
n_dom = len(domains)
domain_colors = {d: _CMAP9[i % len(_CMAP9)] for i, d in enumerate(domains)}

print(f"Countries: {len(by_country)}, Constructs: {len(all_constructs)}, Domains: {n_dom}")

# --- Layout: constructs on circle ---
def compute_layout(constructs, radius=3.4, spread=0.68):
    by_dom = defaultdict(list)
    for c in constructs:
        by_dom[construct_domain(c)].append(c)
    doms = sorted(by_dom.keys())
    n_d = len(doms)
    sector = 2 * np.pi / n_d
    half = sector * spread / 2
    dam = {d: np.pi/2 - i * sector for i, d in enumerate(doms)}
    pos = {}
    for dom, members in by_dom.items():
        center = dam[dom]
        n = len(members)
        angles = np.linspace(center - half, center + half, n) if n > 1 else [center]
        for angle, c in zip(angles, sorted(members)):
            pos[c] = (radius * np.cos(angle), radius * np.sin(angle))
    return pos, dam


# =====================================================================
# PLOT 1: One circle per cultural zone (8 panels)
# =====================================================================
print("\nPlot 1: Regional circle networks...")
fig, axes = plt.subplots(2, 4, figsize=(36, 18))
axes = axes.flatten()

zone_names = sorted(CULTURAL_ZONES.keys())
pos, dam = compute_layout(all_constructs)

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
                  width=1.3, facecolor=domain_colors[dom], alpha=0.08,
                  edgecolor=domain_colors[dom], linewidth=0.3)
        ax.add_patch(w)

    # Collect edges from all countries in this zone
    zone_countries = CULTURAL_ZONES.get(zone, [])
    zone_edges = []
    for c in zone_countries:
        zone_edges.extend(by_country.get(c, []))

    n_edges = len(zone_edges)
    n_countries_with_data = sum(1 for c in zone_countries if c in by_country)

    # Draw edges — transparent to create shadow/density effect
    if zone_edges:
        gamma_max = max(abs(e["gamma"]) for e in zone_edges)
        # High alpha — many overlapping lines create density shadow
        # Each edge clearly visible; overlap builds saturation
        for e in sorted(zone_edges, key=lambda x: abs(x["gamma"])):
            va, vb = e["va"], e["vb"]
            if va not in pos or vb not in pos:
                continue
            g = e["gamma"]
            color = "#d73027" if g > 0 else "#4575b4"
            strength = abs(g) / max(gamma_max, 0.01)
            alpha = 0.15 + 0.45 * strength  # range: 0.15 to 0.60
            lw = 0.5 + 2.5 * strength
            ax.plot([pos[va][0], pos[vb][0]], [pos[va][1], pos[vb][1]],
                    color=color, alpha=alpha, lw=lw, solid_capstyle='round')

    # Draw nodes
    for c in all_constructs:
        if c not in pos:
            continue
        dom = construct_domain(c)
        ax.plot(pos[c][0], pos[c][1], 'o', color=domain_colors[dom],
                markersize=3, markeredgecolor='white', markeredgewidth=0.3, zorder=5)

    # Domain labels on outer ring
    for dom in domains:
        angle = dam[dom]
        lx = 4.6 * np.cos(angle)
        ly = 4.6 * np.sin(angle)
        label = WVS_DOMAIN_LABELS.get(dom, dom)
        ax.text(lx, ly, label, ha='center', va='center', fontsize=5,
                fontweight='bold', color=domain_colors[dom], alpha=0.7)

    # Title
    ax.set_title(f"{zone}\n{n_countries_with_data} countries, {n_edges:,} sig edges",
                 fontsize=11, fontweight='bold', color=ZONE_COLORS.get(zone, 'black'))

fig.suptitle("SES Bridge Networks by Cultural Zone\n"
             "Constructs on circle (colored by domain), edges = significant γ bridges "
             "(red=positive, blue=negative)\n"
             "Line density (shadow) shows strength of SES structuring",
             fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(OUT_DIR / 'regional_circle_networks.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"Saved: regional_circle_networks.png")


# =====================================================================
# PLOT 2: Single circle with all countries, coded by zone
# =====================================================================
print("\nPlot 2: Country circle network...")

# Build country γ-vectors for correlation
country_list = sorted(by_country.keys())
# Get all unique pairs
all_pairs = set()
for c in country_list:
    for e in by_country[c]:
        all_pairs.add(pair_id(e["va"], e["vb"]))
# Also include non-significant pairs (need full γ vectors)
country_gamma_vectors = {}
for key, est in estimates.items():
    if "dr_gamma" not in est:
        continue
    country, va, vb = parse_key(key)
    if not country:
        continue
    if country not in country_gamma_vectors:
        country_gamma_vectors[country] = {}
    pid = pair_id(va, vb)
    country_gamma_vectors[country][pid] = est["dr_gamma"]

# Build matrix: countries × pairs
pair_list = sorted(all_pairs)
pair_idx = {p: i for i, p in enumerate(pair_list)}
country_list = sorted(country_gamma_vectors.keys())
n_c = len(country_list)
n_p = len(pair_list)
gamma_matrix = np.full((n_c, n_p), np.nan)
for ci, c in enumerate(country_list):
    for pid, g in country_gamma_vectors[c].items():
        if pid in pair_idx:
            gamma_matrix[ci, pair_idx[pid]] = g

# Correlation between countries (pairwise, ignoring NaN)
from scipy.stats import pearsonr
corr_matrix = np.zeros((n_c, n_c))
for i in range(n_c):
    for j in range(i+1, n_c):
        valid = np.isfinite(gamma_matrix[i]) & np.isfinite(gamma_matrix[j])
        if valid.sum() > 10:
            r, _ = pearsonr(gamma_matrix[i, valid], gamma_matrix[j, valid])
            corr_matrix[i, j] = r
            corr_matrix[j, i] = r
        else:
            corr_matrix[i, j] = 0
            corr_matrix[j, i] = 0

# Layout: countries on circle, grouped by zone
fig, ax = plt.subplots(figsize=(20, 20))
ax.set_aspect("equal")
ax.axis("off")

# Sort countries by zone then alphabetically
zone_order = sorted(ZONE_COLORS.keys())
sorted_countries = []
zone_starts = {}
for zone in zone_order:
    zone_starts[zone] = len(sorted_countries)
    members = sorted([c for c in country_list if COUNTRY_ZONE.get(c) == zone])
    sorted_countries.extend(members)
# Add any unknowns
unknowns = [c for c in country_list if c not in sorted_countries]
sorted_countries.extend(unknowns)

n_total = len(sorted_countries)
country_pos = {}
country_angles = {}
radius = 4.0
for i, c in enumerate(sorted_countries):
    angle = np.pi/2 - 2*np.pi * i / n_total
    country_pos[c] = (radius * np.cos(angle), radius * np.sin(angle))
    country_angles[c] = angle

# Draw zone arcs
for zone in zone_order:
    members = [c for c in sorted_countries if COUNTRY_ZONE.get(c) == zone]
    if not members:
        continue
    start_angle = country_angles[members[0]]
    end_angle = country_angles[members[-1]]
    # Draw arc background
    mid_angle = (start_angle + end_angle) / 2
    lx = 5.2 * np.cos(mid_angle)
    ly = 5.2 * np.sin(mid_angle)
    ax.text(lx, ly, zone, ha='center', va='center', fontsize=7,
            fontweight='bold', color=ZONE_COLORS[zone], rotation=np.degrees(mid_angle) - 90,
            rotation_mode='anchor')

# Draw edges (high correlation = thick/opaque, low = thin/transparent)
# Only draw top correlations to avoid visual noise
threshold = 0.3  # minimum correlation to draw
edges_drawn = 0
for i in range(n_total):
    for j in range(i+1, n_total):
        ci = country_list.index(sorted_countries[i]) if sorted_countries[i] in country_list else -1
        cj = country_list.index(sorted_countries[j]) if sorted_countries[j] in country_list else -1
        if ci < 0 or cj < 0:
            continue
        r = corr_matrix[ci, cj]
        if abs(r) < threshold:
            continue
        c1 = sorted_countries[i]
        c2 = sorted_countries[j]
        # Color: within-zone edges use zone color; cross-zone = gray
        z1 = COUNTRY_ZONE.get(c1, '')
        z2 = COUNTRY_ZONE.get(c2, '')
        if z1 == z2 and z1 in ZONE_COLORS:
            color = ZONE_COLORS[z1]
        else:
            color = "#888888"
        strength = (abs(r) - threshold) / (1.0 - threshold)
        alpha = 0.12 + 0.5 * strength
        lw = 0.4 + 3.0 * strength
        zorder = 3 if z1 == z2 else 1  # within-zone on top
        ax.plot([country_pos[c1][0], country_pos[c2][0]],
                [country_pos[c1][1], country_pos[c2][1]],
                color=color, alpha=alpha, lw=lw, solid_capstyle='round', zorder=zorder)
        edges_drawn += 1
print(f"  Country edges drawn (r>{threshold}): {edges_drawn}")

# Draw country nodes
for c in sorted_countries:
    if c not in country_pos:
        continue
    zone = COUNTRY_ZONE.get(c, "Unknown")
    color = ZONE_COLORS.get(zone, "#cccccc")
    size = 10 if c == "MEX" else 6
    edge = 'black' if c == 'MEX' else 'white'
    edgew = 1.5 if c == 'MEX' else 0.5
    ax.plot(country_pos[c][0], country_pos[c][1], 'o', color=color,
            markersize=size, markeredgecolor=edge, markeredgewidth=edgew, zorder=5)

    # Labels
    angle = country_angles[c]
    lx = 4.5 * np.cos(angle)
    ly = 4.5 * np.sin(angle)
    rot = np.degrees(angle)
    if rot > 90: rot -= 180
    if rot < -90: rot += 180
    ha = 'left' if -np.pi/2 < angle < np.pi/2 else 'right'
    fw = 'bold' if c == 'MEX' else 'normal'
    fs = 8 if c == 'MEX' else 6
    ax.text(lx, ly, c, ha=ha, va='center', fontsize=fs, fontweight=fw,
            rotation=rot, rotation_mode='anchor',
            color=ZONE_COLORS.get(COUNTRY_ZONE.get(c, ''), '#333333'))

ax.set_xlim(-6.5, 6.5)
ax.set_ylim(-6.5, 6.5)

# Legend
from matplotlib.patches import Patch
legend_patches = [Patch(facecolor=v, label=k) for k, v in ZONE_COLORS.items()]
ax.legend(handles=legend_patches, loc='lower right', fontsize=9, framealpha=0.9)

ax.set_title("Country γ-Structure Similarity Network\n"
             "66 countries on circle (grouped by cultural zone)\n"
             "Edges = Pearson r of γ-bridge profiles (r > 0.3)\n"
             "Colored = within-zone, Gray = cross-zone",
             fontsize=14, y=1.02)

fig.savefig(OUT_DIR / 'country_circle_network.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"Saved: country_circle_network.png")

print("\nDone.")
