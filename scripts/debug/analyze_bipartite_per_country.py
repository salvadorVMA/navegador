"""
Per-country bipartite network analysis.

For each of 66 WVS countries:
  B1: Structural balance (% balanced triangles in signed network)
  B2: Camp assignment vs los_mex reference bipartition
  B3: Spectral bipartition (Fiedler vector of signed Laplacian)
  B4: Signed modularity Q
  B5: Balance vs anomaly correlation
  B6: Bipartition PCA (countries in Fiedler-vector space)

Output:
  data/results/bipartite_per_country.json
  data/results/bipartite_per_country_report.md
  data/results/bipartite_fiedler_pca.png
  data/results/bipartite_balance_vs_anomaly.png
  data/results/bipartite_camp_stability.png

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_bipartite_per_country.py
"""
import json, sys, numpy as np
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

SWEEP_PATH = ROOT / 'data/results/wvs_geographic_sweep_w7.json'
LOSMEX_KG = ROOT / 'data/results/kg_ontology_v2.json'
OUT = ROOT / 'data/results'

ZONE_COLORS = {
    "Latin America": "#e41a1c", "English-speaking": "#377eb8",
    "Protestant Europe": "#4daf4a", "Catholic Europe": "#984ea3",
    "Orthodox/ex-Communist": "#ff7f00", "Confucian": "#a65628",
    "South/Southeast Asian": "#f781bf", "African-Islamic": "#999999",
}

# --- Load ---
print("Loading sweep data...")
with open(SWEEP_PATH) as f:
    data = json.load(f)
estimates = data.get("estimates", {})

# --- Build per-country signed adjacency ---
print("Building per-country networks...")
country_edges = defaultdict(list)  # country → [(va, vb, gamma, excl_zero)]
all_constructs = set()

for key, est in estimates.items():
    if "dr_gamma" not in est:
        continue
    parts = key.split("::")
    if len(parts) != 3:
        continue
    country = parts[0].split("_")[2]
    va, vb = parts[1], parts[2]
    country_edges[country].append((va, vb, est["dr_gamma"], est.get("excl_zero", False)))
    all_constructs.add(va)
    all_constructs.add(vb)

all_constructs = sorted(all_constructs)
construct_idx = {c: i for i, c in enumerate(all_constructs)}
N = len(all_constructs)
countries = sorted(country_edges.keys())
print(f"Countries: {len(countries)}, Constructs: {N}")


def analyze_country(country):
    """Compute bipartite metrics for one country."""
    edges = country_edges[country]
    sig_edges = [(va, vb, g) for va, vb, g, sig in edges if sig]

    if len(sig_edges) < 10:
        return country, None

    # Build signed adjacency matrix (sig edges only)
    A = np.zeros((N, N))
    for va, vb, g in sig_edges:
        i, j = construct_idx[va], construct_idx[vb]
        A[i, j] = np.sign(g)
        A[j, i] = np.sign(g)

    # Active nodes (any sig edge)
    active = np.where(np.any(A != 0, axis=1))[0]
    n_active = len(active)
    if n_active < 5:
        return country, None

    A_sub = A[np.ix_(active, active)]

    # --- B1: Structural balance ---
    n_balanced = 0
    n_total = 0
    for i in range(n_active):
        for j in range(i+1, n_active):
            if A_sub[i, j] == 0:
                continue
            for k in range(j+1, n_active):
                if A_sub[i, k] == 0 or A_sub[j, k] == 0:
                    continue
                product = A_sub[i, j] * A_sub[i, k] * A_sub[j, k]
                n_total += 1
                if product > 0:
                    n_balanced += 1
    balance = n_balanced / max(n_total, 1)

    # --- B3: Spectral bipartition (Fiedler vector) ---
    # Signed Laplacian: L = D - A where D_ii = sum |A_ij|
    D = np.diag(np.sum(np.abs(A_sub), axis=1))
    L = D - A_sub
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        # Fiedler vector = eigenvector of 2nd smallest eigenvalue
        fiedler_idx = np.argsort(eigenvalues)[1]
        fiedler = eigenvectors[:, fiedler_idx]
        # Bipartition: sign of Fiedler vector
        camp_labels = np.sign(fiedler)
        camp_labels[camp_labels == 0] = 1
    except:
        fiedler = np.zeros(n_active)
        camp_labels = np.ones(n_active)

    # --- B4: Signed modularity Q ---
    # Q = (1/2m) * sum_ij (A_ij - k_i*k_j/2m) * delta(c_i, c_j)
    m = np.sum(np.abs(A_sub)) / 2
    if m > 0:
        k = np.sum(np.abs(A_sub), axis=1)
        Q = 0
        for i in range(n_active):
            for j in range(n_active):
                if camp_labels[i] == camp_labels[j]:
                    Q += A_sub[i, j] - k[i] * k[j] / (2 * m)
        Q /= (2 * m)
    else:
        Q = 0

    # Map Fiedler back to full construct space
    fiedler_full = np.zeros(N)
    camp_full = np.zeros(N)
    for idx_sub, idx_full in enumerate(active):
        fiedler_full[idx_full] = fiedler[idx_sub]
        camp_full[idx_full] = camp_labels[idx_sub]

    n_pos = int(np.sum(camp_labels > 0))
    n_neg = int(np.sum(camp_labels < 0))
    n_pos_edges = sum(1 for _, _, g in sig_edges if g > 0)
    n_neg_edges = sum(1 for _, _, g in sig_edges if g < 0)

    return country, {
        "n_sig_edges": len(sig_edges),
        "n_active_nodes": n_active,
        "structural_balance": round(balance, 4),
        "n_balanced_triangles": n_balanced,
        "n_total_triangles": n_total,
        "modularity_Q": round(float(Q), 4),
        "camp_sizes": [n_pos, n_neg],
        "n_pos_edges": n_pos_edges,
        "n_neg_edges": n_neg_edges,
        "fiedler_vector": fiedler_full.tolist(),
        "camp_labels": camp_full.tolist(),
    }


# --- Run analysis for all countries ---
print("Analyzing bipartite structure per country...")
with ThreadPoolExecutor(max_workers=8) as pool:
    results_raw = list(pool.map(analyze_country, countries))

results = {c: r for c, r in results_raw if r is not None}
print(f"Analyzed: {len(results)} countries")

# --- B2: Camp assignment vs los_mex reference ---
# Load los_mex bipartition from KG ontology bridges
print("Loading los_mex reference bipartition...")
try:
    with open(LOSMEX_KG) as f:
        kg = json.load(f)
    # Use bridge signs to build los_mex camps
    # Not directly comparable (different constructs), so use WVS MEX as reference
    mex_camps = results.get("MEX", {}).get("camp_labels", [])
except:
    mex_camps = []

if mex_camps and any(c != 0 for c in mex_camps):
    mex_camps = np.array(mex_camps)
    print("Computing camp stability vs Mexico reference...")
    for country, r in results.items():
        if country == "MEX":
            r["camp_agreement_with_mex"] = 1.0
            continue
        c_camps = np.array(r["camp_labels"])
        # Compare on active nodes (both countries have nonzero camp)
        active = (mex_camps != 0) & (c_camps != 0)
        if active.sum() < 5:
            r["camp_agreement_with_mex"] = None
            continue
        agree = np.sum(mex_camps[active] == c_camps[active])
        # Try both orientations (camps are arbitrary +/-)
        agree_flip = np.sum(mex_camps[active] == -c_camps[active])
        best = max(agree, agree_flip)
        r["camp_agreement_with_mex"] = round(best / active.sum(), 4)

# --- B5: Load anomaly data ---
pair_global = defaultdict(list)
for key, est in estimates.items():
    if "dr_gamma" not in est:
        continue
    parts = key.split("::")
    if len(parts) != 3:
        continue
    pid = tuple(sorted([parts[1], parts[2]]))
    pair_global[pid].append(est["dr_gamma"])
pair_mean = {pid: np.mean(gs) for pid, gs in pair_global.items()}

country_mean_anom = {}
for country in results:
    anoms = []
    for va, vb, g, sig in country_edges[country]:
        pid = tuple(sorted([va, vb]))
        if pid in pair_mean:
            anoms.append(abs(g - pair_mean[pid]))
    country_mean_anom[country] = np.mean(anoms) if anoms else 0

# --- Save JSON ---
output = {c: {k: v for k, v in r.items() if k != "fiedler_vector"}
          for c, r in results.items()}
with open(OUT / 'bipartite_per_country.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f"Saved: bipartite_per_country.json")

# --- Report ---
lines = [
    "# Per-Country Bipartite Network Analysis",
    "",
    "## Country Summary",
    "",
    "| Country | Zone | Sig edges | Active | Balance | Q | Camp sizes | MEX agree |",
    "|---------|------|-----------|--------|---------|---|------------|-----------|",
]
for c in sorted(results.keys()):
    r = results[c]
    zone = COUNTRY_ZONE.get(c, "?")[:12]
    camp_agree = r.get("camp_agreement_with_mex")
    ca_str = f"{camp_agree:.2f}" if camp_agree is not None else "—"
    lines.append(
        f"| {c} | {zone} | {r['n_sig_edges']} | {r['n_active_nodes']} | "
        f"{r['structural_balance']:.3f} | {r['modularity_Q']:.3f} | "
        f"{r['camp_sizes'][0]}+{r['camp_sizes'][1]} | {ca_str} |"
    )

# Summary stats
balances = [r["structural_balance"] for r in results.values()]
Qs = [r["modularity_Q"] for r in results.values()]
agrees = [r.get("camp_agreement_with_mex", 0) for r in results.values()
          if r.get("camp_agreement_with_mex") is not None]

lines.extend([
    "",
    "## Summary Statistics",
    "",
    f"- **Structural balance**: median={np.median(balances):.3f}, "
    f"mean={np.mean(balances):.3f}, range=[{np.min(balances):.3f}, {np.max(balances):.3f}]",
    f"- **Modularity Q**: median={np.median(Qs):.3f}, "
    f"mean={np.mean(Qs):.3f}, range=[{np.min(Qs):.3f}, {np.max(Qs):.3f}]",
    f"- **Camp agreement with MEX**: median={np.median(agrees):.3f}, "
    f"mean={np.mean(agrees):.3f}, range=[{np.min(agrees):.3f}, {np.max(agrees):.3f}]" if agrees else "",
    f"- **los_mex reference**: balance=0.940, Q=0.089",
    "",
    "---",
    "*Generated by analyze_bipartite_per_country.py*",
])
with open(OUT / 'bipartite_per_country_report.md', 'w') as f:
    f.write("\n".join(lines))
print(f"Saved: bipartite_per_country_report.md")


# =====================================================================
# PLOTS
# =====================================================================

# --- B5: Balance vs Anomaly ---
fig, ax = plt.subplots(figsize=(10, 8))
for c in results:
    r = results[c]
    zone = COUNTRY_ZONE.get(c, "Unknown")
    color = ZONE_COLORS.get(zone, "#ccc")
    marker = '*' if c == 'MEX' else 'o'
    size = 150 if c == 'MEX' else 50
    ax.scatter(country_mean_anom.get(c, 0), r["structural_balance"],
               c=color, s=size, marker=marker, alpha=0.8,
               edgecolors='black' if c == 'MEX' else 'none', linewidths=1.5, zorder=10 if c == 'MEX' else 2)
    if c in ('MEX', 'USA', 'JPN', 'DEU', 'GBR', 'CHN', 'IND', 'BRA', 'NGA',
             'URY', 'SGP', 'MNG', 'JOR', 'AUS', 'GRC', 'TUR'):
        ax.annotate(c, (country_mean_anom.get(c, 0), r["structural_balance"]),
                   fontsize=7, fontweight='bold' if c == 'MEX' else 'normal')

# Correlation
xs = [country_mean_anom.get(c, 0) for c in results]
ys = [results[c]["structural_balance"] for c in results]
from scipy.stats import spearmanr
rho, pval = spearmanr(xs, ys)
ax.set_xlabel("Mean |anomaly| from global mean", fontsize=12)
ax.set_ylabel("Structural balance (% balanced triangles)", fontsize=12)
ax.set_title(f"Structural Balance vs Anomaly (ρ={rho:.3f}, p={pval:.4f})\n"
             f"los_mex reference: balance=0.94", fontsize=13)
ax.axhline(y=0.94, color='gray', linestyle='--', alpha=0.5, label='los_mex (0.94)')
ax.grid(True, alpha=0.2)
handles = [Patch(facecolor=v, label=k) for k, v in ZONE_COLORS.items()]
ax.legend(handles=handles, fontsize=8, loc='lower left')
fig.tight_layout()
fig.savefig(OUT / 'bipartite_balance_vs_anomaly.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("Saved: bipartite_balance_vs_anomaly.png")

# --- B2: Camp agreement with MEX ---
if agrees:
    fig, ax = plt.subplots(figsize=(14, 6))
    sorted_c = sorted(results.keys(),
                       key=lambda c: -(results[c].get("camp_agreement_with_mex") or 0))
    x = range(len(sorted_c))
    colors = [ZONE_COLORS.get(COUNTRY_ZONE.get(c, ''), '#ccc') for c in sorted_c]
    vals = [results[c].get("camp_agreement_with_mex", 0) or 0 for c in sorted_c]
    bars = ax.bar(x, vals, color=colors, edgecolor='white', linewidth=0.3)
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_c, rotation=90, fontsize=7)
    for tick in ax.get_xticklabels():
        if tick.get_text() == 'MEX':
            tick.set_color('red')
            tick.set_fontweight('bold')
    ax.set_ylabel("Camp agreement with Mexico bipartition", fontsize=11)
    ax.set_title("Bipartition Stability: Agreement with Mexico's Camp Assignment", fontsize=13)
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Chance level')
    ax.grid(axis='y', alpha=0.2)
    handles = [Patch(facecolor=v, label=k) for k, v in ZONE_COLORS.items()]
    ax.legend(handles=handles, fontsize=7, loc='lower left', ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / 'bipartite_camp_stability.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Saved: bipartite_camp_stability.png")

# --- B6: Fiedler PCA ---
fiedler_matrix = []
fiedler_countries = []
for c in sorted(results.keys()):
    fv = results[c].get("fiedler_vector") or np.zeros(N)
    if isinstance(fv, list):
        fv = np.array(fv)
    # Normalize sign (arbitrary in eigenvectors) — align to MEX
    if "MEX" in results and c != "MEX":
        mex_fv = np.array(results["MEX"].get("fiedler_vector", np.zeros(N)))
        if np.dot(fv, mex_fv) < 0:
            fv = -fv
    if np.any(fv != 0):
        fiedler_matrix.append(fv)
        fiedler_countries.append(c)

if len(fiedler_matrix) >= 5:
    from sklearn.decomposition import PCA
    F = np.array(fiedler_matrix)
    pca = PCA(n_components=min(3, len(F)))
    coords = pca.fit_transform(F)

    fig, ax = plt.subplots(figsize=(12, 10))
    for i, c in enumerate(fiedler_countries):
        zone = COUNTRY_ZONE.get(c, "Unknown")
        color = ZONE_COLORS.get(zone, "#ccc")
        marker = '*' if c == 'MEX' else 'o'
        size = 200 if c == 'MEX' else 50
        ax.scatter(coords[i, 0], coords[i, 1], c=color, s=size, marker=marker,
                   alpha=0.8, edgecolors='black' if c == 'MEX' else 'none',
                   linewidths=1.5, zorder=10 if c == 'MEX' else 2)
        if c in ('MEX', 'USA', 'JPN', 'DEU', 'GBR', 'CHN', 'IND', 'BRA', 'NGA',
                 'URY', 'SGP', 'MNG', 'JOR', 'AUS', 'GRC', 'TUR', 'EGY', 'IDN'):
            ax.annotate(c, (coords[i, 0], coords[i, 1]), fontsize=7,
                       fontweight='bold' if c == 'MEX' else 'normal')

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)", fontsize=12)
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)", fontsize=12)
    ax.set_title("Countries in Bipartition Space (PCA of Fiedler Vectors)\n"
                 "Countries with similar bipartitions cluster together", fontsize=13)
    ax.grid(True, alpha=0.2)
    handles = [Patch(facecolor=v, label=k) for k, v in ZONE_COLORS.items()]
    ax.legend(handles=handles, fontsize=8, loc='upper right')
    fig.tight_layout()
    fig.savefig(OUT / 'bipartite_fiedler_pca.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Saved: bipartite_fiedler_pca.png")
    print(f"  Fiedler PCA: PC1={pca.explained_variance_ratio_[0]*100:.1f}%, "
          f"PC2={pca.explained_variance_ratio_[1]*100:.1f}%")

print("\nDone.")
