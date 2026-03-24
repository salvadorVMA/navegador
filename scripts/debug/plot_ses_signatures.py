"""Plot SES signatures: 66 WVS countries + los_mex across 4 SES dimensions."""
import numpy as np, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from wvs_metadata import COUNTRY_ZONE

results = json.load(open(ROOT / 'data/results/ses_signatures_all.json'))
dims = ['escol', 'Tam_loc', 'sexo', 'edad']
dim_labels = ['Education', 'Urbanization', 'Gender', 'Age/Cohort']
countries = sorted(results.keys())
matrix = np.array([[results[c][d] for d in dims] for c in countries])

ZONE_COLORS = {
    "Latin America": "#e41a1c", "English-speaking": "#377eb8",
    "Protestant Europe": "#4daf4a", "Catholic Europe": "#984ea3",
    "Orthodox/ex-Communist": "#ff7f00", "Confucian": "#a65628",
    "South/Southeast Asian": "#f781bf", "African-Islamic": "#999999",
}
HIGHLIGHT = ('MEX', 'los_mex')
LABEL_SET = {'MEX','los_mex','USA','JPN','DEU','GBR','CHN','IND','BRA','NGA',
             'EGY','SGP','MNG','JOR','AUS','TUR','CYP','HKG','IDN'}
OUT = ROOT / 'data' / 'results'

# --- Plot 1: 6-panel scatter (all dim pairs) ---
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
for ax, (i, j) in zip(axes.flatten(), [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]):
    for ci, c in enumerate(countries):
        zone = COUNTRY_ZONE.get(c, 'Latin America') if c != 'los_mex' else 'Latin America'
        color = ZONE_COLORS.get(zone, '#cccccc')
        is_hl = c in HIGHLIGHT
        ax.scatter(matrix[ci,i], matrix[ci,j], c=color,
                   s=250 if is_hl else 50, marker='*' if is_hl else 'o',
                   alpha=1.0 if is_hl else 0.7,
                   edgecolors='black' if is_hl else 'none', linewidths=1.5,
                   zorder=10 if is_hl else 2)
        if c in LABEL_SET:
            ax.annotate(c, (matrix[ci,i], matrix[ci,j]), fontsize=7,
                       fontweight='bold' if is_hl else 'normal', ha='left', va='bottom')
    ax.set_xlabel(f'Mean |ρ| {dim_labels[i]}', fontsize=10)
    ax.set_ylabel(f'Mean |ρ| {dim_labels[j]}', fontsize=10)
    ax.grid(True, alpha=0.2)

handles = [Patch(facecolor=v, label=k) for k,v in ZONE_COLORS.items()]
handles.append(plt.Line2D([0],[0], marker='*', color='w', markerfacecolor='#e41a1c',
                           markersize=15, label='MEX / los_mex'))
fig.legend(handles=handles, loc='lower center', ncol=4, fontsize=9, bbox_to_anchor=(0.5,-0.02))
fig.suptitle('SES Signature: Mean |ρ(construct, SES dim)| — 66 Countries + los_mex', fontsize=14, y=1.01)
fig.tight_layout()
fig.savefig(OUT / 'ses_signature_scatter.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('1/3 scatter')

# --- Plot 2: Radar ---
selected = ['MEX','los_mex','USA','DEU','JPN','CHN','IND','BRA','NGA','EGY','SGP','MNG','JOR','GBR','AUS','TUR']
selected = [c for c in selected if c in results]
angles = np.linspace(0, 2*np.pi, 4, endpoint=False).tolist() + [0]
fig, ax = plt.subplots(figsize=(10,10), subplot_kw=dict(polar=True))
cmap = plt.cm.tab20(np.linspace(0,1,len(selected)))
for ci, c in enumerate(selected):
    vals = [results[c][d] for d in dims] + [results[c][dims[0]]]
    lw = 3 if c in HIGHLIGHT else 1.5
    ls = '--' if c == 'los_mex' else '-'
    ax.plot(angles, vals, lw=lw, ls=ls, label=c, color=cmap[ci])
    if c in HIGHLIGHT: ax.fill(angles, vals, alpha=0.1, color=cmap[ci])
ax.set_xticks(angles[:-1])
ax.set_xticklabels(dim_labels, fontsize=12)
ax.set_title('SES Signature Profiles — Mean |ρ(construct, SES dim)|', fontsize=14, y=1.08)
ax.legend(loc='upper right', bbox_to_anchor=(1.35,1.05), fontsize=9)
fig.tight_layout()
fig.savefig(OUT / 'ses_signature_radar.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('2/3 radar')

# --- Plot 3: Stacked bars sorted by total magnitude ---
dim_colors = ['#2166ac','#b2182b','#1b7837','#762a83']
total_mag = [sum(results[c][d] for d in dims) for c in countries]
sort_idx = np.argsort(total_mag)[::-1]
fig, ax = plt.subplots(figsize=(22,8))
x = np.arange(len(countries))
bottom = np.zeros(len(countries))
for di, dim in enumerate(dims):
    vals = [results[countries[i]][dim] for i in sort_idx]
    ax.bar(x, vals, bottom=bottom, label=dim_labels[di], color=dim_colors[di], alpha=0.85)
    bottom += vals
sorted_labels = [countries[i] for i in sort_idx]
ax.set_xticks(x)
ax.set_xticklabels(sorted_labels, rotation=90, fontsize=7)
for tick in ax.get_xticklabels():
    if tick.get_text() in HIGHLIGHT:
        tick.set_color('red'); tick.set_fontweight('bold')
ax.set_ylabel('Mean |ρ(construct, SES dim)|', fontsize=11)
ax.set_title('SES Signature Magnitude by Country — Stacked by Dimension', fontsize=14)
ax.legend(loc='upper right', fontsize=10)
ax.grid(axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / 'ses_signature_bars.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('3/3 bars')
print('Done.')
