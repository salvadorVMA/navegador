"""Interactive 3D scatter of SES signatures — top 3 variance dimensions.

Opens in browser via Plotly. Rotate, zoom, hover for country details.
"""
import numpy as np, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import plotly.graph_objects as go
from wvs_metadata import COUNTRY_ZONE

results = json.load(open(ROOT / 'data/results/ses_signatures_all.json'))
dims = ['escol', 'Tam_loc', 'sexo', 'edad']
dim_labels = {'escol': 'Education', 'Tam_loc': 'Urbanization', 'sexo': 'Gender', 'edad': 'Age/Cohort'}
countries = sorted(results.keys())
matrix = np.array([[results[c][d] for d in dims] for c in countries])

# Find top 3 variance dimensions
variances = matrix.var(axis=0)
top3_idx = np.argsort(variances)[::-1][:3]
top3_dims = [dims[i] for i in top3_idx]
top3_labels = [dim_labels[d] for d in top3_dims]
print(f"Top 3 by variance: {top3_labels}")
for i, d in enumerate(top3_dims):
    print(f"  {dim_labels[d]}: var={variances[top3_idx[i]]:.6f}")

ZONE_COLORS = {
    "Latin America": "#e41a1c", "English-speaking": "#377eb8",
    "Protestant Europe": "#4daf4a", "Catholic Europe": "#984ea3",
    "Orthodox/ex-Communist": "#ff7f00", "Confucian": "#a65628",
    "South/Southeast Asian": "#f781bf", "African-Islamic": "#999999",
}

fig = go.Figure()

# Plot each zone as a separate trace (for legend toggling)
for zone, color in ZONE_COLORS.items():
    zone_countries = [c for c in countries if COUNTRY_ZONE.get(c) == zone]
    if not zone_countries:
        continue
    zone_idx = [countries.index(c) for c in zone_countries]
    x = matrix[zone_idx, top3_idx[0]]
    y = matrix[zone_idx, top3_idx[1]]
    z = matrix[zone_idx, top3_idx[2]]

    # Hover text with full 4D signature
    hover = []
    for c in zone_countries:
        s = results[c]
        hover.append(f"<b>{c}</b> ({zone})<br>"
                     f"Education: {s['escol']:.4f}<br>"
                     f"Urbanization: {s['Tam_loc']:.4f}<br>"
                     f"Gender: {s['sexo']:.4f}<br>"
                     f"Age: {s['edad']:.4f}<br>"
                     f"Total: {sum(s.values()):.4f}")

    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers+text',
        marker=dict(size=6, color=color, opacity=0.8,
                    line=dict(width=0.5, color='black')),
        text=zone_countries,
        textposition='top center',
        textfont=dict(size=8),
        hovertext=hover,
        hoverinfo='text',
        name=zone,
    ))

# Highlight MEX and los_mex
for c, symbol, size in [('MEX', 'diamond', 12), ('los_mex', 'x', 14)]:
    if c not in results:
        continue
    ci = countries.index(c)
    s = results[c]
    hover = (f"<b>{c}</b><br>"
             f"Education: {s['escol']:.4f}<br>"
             f"Urbanization: {s['Tam_loc']:.4f}<br>"
             f"Gender: {s['sexo']:.4f}<br>"
             f"Age: {s['edad']:.4f}<br>"
             f"Total: {sum(s.values()):.4f}")
    fig.add_trace(go.Scatter3d(
        x=[matrix[ci, top3_idx[0]]],
        y=[matrix[ci, top3_idx[1]]],
        z=[matrix[ci, top3_idx[2]]],
        mode='markers+text',
        marker=dict(size=size, color='red', symbol=symbol,
                    line=dict(width=2, color='black')),
        text=[c],
        textposition='top center',
        textfont=dict(size=11, color='red'),
        hovertext=[hover],
        hoverinfo='text',
        name=c,
    ))

fig.update_layout(
    title=dict(
        text=(f"SES Signature Space — 66 Countries + los_mex<br>"
              f"<sub>Top 3 dimensions by variance: {top3_labels[0]}, {top3_labels[1]}, {top3_labels[2]}</sub>"),
        font=dict(size=16),
    ),
    scene=dict(
        xaxis_title=f"Mean |ρ| {top3_labels[0]}",
        yaxis_title=f"Mean |ρ| {top3_labels[1]}",
        zaxis_title=f"Mean |ρ| {top3_labels[2]}",
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
    ),
    width=1000,
    height=800,
    legend=dict(itemsizing='constant', font=dict(size=10)),
    margin=dict(l=0, r=0, b=0, t=80),
)

out_html = ROOT / 'data' / 'results' / 'ses_signature_3d.html'
fig.write_html(str(out_html), include_plotlyjs=True)
print(f"Saved: {out_html}")

# Also open in browser
import webbrowser
webbrowser.open(f"file://{out_html}")
print("Opened in browser.")
