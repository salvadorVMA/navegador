"""Detect empirical construct communities via Louvain at multiple resolutions.

Reads the construct network (construct_network.json) and runs weighted Louvain
community detection at several resolution values. Produces:
  - data/results/construct_communities.json   — community assignments per resolution
  - data/results/construct_communities.html   — single Plotly figure with subplot per resolution

Usage:
    python scripts/debug/detect_construct_communities.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NETWORK_PATH = ROOT / 'data' / 'results' / 'construct_network.json'
OUTPUT_JSON = ROOT / 'data' / 'results' / 'construct_communities.json'
OUTPUT_HTML = ROOT / 'data' / 'results' / 'construct_communities.html'

# Resolution values: low → few large clusters, high → many small clusters
RESOLUTIONS = [0.5, 0.75, 1.0, 1.5, 2.0]


def build_graph(network: dict) -> nx.Graph:
    """Build weighted undirected graph from network edges."""
    G = nx.Graph()
    for n in network['nodes']:
        G.add_node(n['id'], domain=n['domain'], label=n['label'],
                   color=n.get('color', '#999'))

    for e in network['edges']:
        src, tgt = e['source'], e['target']
        w = abs(e.get('gamma', 0))
        if w < 1e-6:
            continue
        if G.has_edge(src, tgt):
            # Keep strongest
            if w > G[src][tgt]['weight']:
                G[src][tgt]['weight'] = w
                G[src][tgt]['cross_domain'] = e.get('cross_domain', False)
        else:
            G.add_edge(src, tgt, weight=w, cross_domain=e.get('cross_domain', False))

    return G


def run_louvain(G: nx.Graph, resolution: float, seed: int = 42) -> list[set]:
    """Run Louvain and return communities sorted by size (largest first)."""
    communities = nx.community.louvain_communities(
        G, weight='weight', resolution=resolution, seed=seed)
    return sorted(communities, key=len, reverse=True)


def community_stats(G: nx.Graph, communities: list[set]) -> list[dict]:
    """Compute stats per community."""
    stats = []
    for i, comm in enumerate(communities):
        nodes = list(comm)
        subG = G.subgraph(nodes)
        internal_edges = subG.edges(data=True)
        gammas = [d['weight'] for _, _, d in internal_edges]
        domains = set(G.nodes[n]['domain'] for n in nodes)

        # Cross-domain edges within this community
        cross_internal = sum(1 for _, _, d in internal_edges if d.get('cross_domain'))

        # Betweenness centrality within subgraph
        if len(nodes) > 2:
            bc = nx.betweenness_centrality(subG, weight='weight')
            bridge_node = max(bc, key=bc.get)
            bridge_score = bc[bridge_node]
        else:
            bridge_node = nodes[0] if nodes else ''
            bridge_score = 0.0

        stats.append({
            'community_id': i,
            'n_constructs': len(nodes),
            'n_domains': len(domains),
            'domains': sorted(domains),
            'constructs': sorted(nodes),
            'n_internal_edges': len(gammas),
            'n_cross_domain_internal': cross_internal,
            'mean_gamma': round(float(np.mean(gammas)), 3) if gammas else 0,
            'max_gamma': round(float(max(gammas)), 3) if gammas else 0,
            'bridge_node': bridge_node,
            'bridge_betweenness': round(bridge_score, 3),
        })
    return stats


def detect_all(network: dict) -> dict:
    """Run community detection at all resolutions."""
    G = build_graph(network)
    print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')

    results = {'resolutions': {}}
    for res in RESOLUTIONS:
        communities = run_louvain(G, resolution=res)
        stats = community_stats(G, communities)

        # Modularity
        partition = []
        for comm in communities:
            partition.append(comm)
        mod = nx.community.modularity(G, partition, weight='weight')

        results['resolutions'][str(res)] = {
            'resolution': res,
            'n_communities': len(communities),
            'modularity': round(mod, 4),
            'communities': stats,
        }

        sizes = [s['n_constructs'] for s in stats]
        print(f'  res={res:.2f}: {len(communities)} communities '
              f'(sizes: {sizes[:8]}{"..." if len(sizes) > 8 else ""}), '
              f'modularity={mod:.4f}')

    return results, G


def render_html(network: dict, results: dict, G: nx.Graph, output_path: Path):
    """Render single HTML with one subplot per resolution."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    n_res = len(RESOLUTIONS)
    cols = min(n_res, 3)
    rows = math.ceil(n_res / cols)

    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f'Resolution={r} ({results["resolutions"][str(r)]["n_communities"]} clusters, '
                        f'Q={results["resolutions"][str(r)]["modularity"]:.3f})'
                        for r in RESOLUTIONS],
        horizontal_spacing=0.03, vertical_spacing=0.08,
    )

    # Use spring layout once (consistent positions across panels)
    pos = nx.spring_layout(G, weight='weight', seed=42, k=2.0 / math.sqrt(G.number_of_nodes()))

    # Community color palette (max ~15 distinct colors)
    comm_colors = [
        '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
        '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990',
        '#dcbeff', '#9A6324', '#800000', '#aaffc3', '#000075',
    ]

    node_ids = list(G.nodes())
    node_x = [pos[n][0] for n in node_ids]
    node_y = [pos[n][1] for n in node_ids]

    # Node sizes by degree weight
    degree_w = dict(G.degree(weight='weight'))
    max_dw = max(degree_w.values()) if degree_w else 1
    node_sizes = [8 + 25 * (degree_w.get(n, 0) / max_dw) for n in node_ids]

    for idx, res in enumerate(RESOLUTIONS):
        row = idx // cols + 1
        col = idx % cols + 1
        res_data = results['resolutions'][str(res)]
        communities = res_data['communities']

        # Build node → community map
        node_comm = {}
        for comm in communities:
            cid = comm['community_id']
            for nid in comm['constructs']:
                node_comm[nid] = cid

        # Color nodes by community
        colors = [comm_colors[node_comm.get(n, 0) % len(comm_colors)] for n in node_ids]

        # Labels
        labels = []
        for n in node_ids:
            domain = G.nodes[n]['domain']
            label = G.nodes[n]['label'][:20]
            cid = node_comm.get(n, '?')
            labels.append(f'{domain}:{label} (C{cid})')

        # Hover text
        hover = []
        for n in node_ids:
            domain = G.nodes[n]['domain']
            label = G.nodes[n]['label']
            cid = node_comm.get(n, '?')
            dw = degree_w.get(n, 0)
            hover.append(f'<b>{label}</b><br>Domain: {domain}<br>'
                         f'Community: {cid}<br>Weighted degree: {dw:.2f}')

        # Edges — color by same/different community
        x_same, y_same = [], []
        x_diff, y_diff = [], []
        for u, v in G.edges():
            if u not in pos or v not in pos:
                continue
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            if node_comm.get(u) == node_comm.get(v):
                x_same += [x0, x1, None]
                y_same += [y0, y1, None]
            else:
                x_diff += [x0, x1, None]
                y_diff += [y0, y1, None]

        # Intra-community edges
        fig.add_trace(go.Scatter(
            x=x_same, y=y_same, mode='lines',
            line=dict(width=0.3, color='rgba(100,100,100,0.15)'),
            hoverinfo='none', showlegend=False,
        ), row=row, col=col)

        # Inter-community edges
        fig.add_trace(go.Scatter(
            x=x_diff, y=y_diff, mode='lines',
            line=dict(width=0.3, color='rgba(220,50,50,0.08)'),
            hoverinfo='none', showlegend=False,
        ), row=row, col=col)

        # Nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode='markers+text',
            marker=dict(size=node_sizes, color=colors,
                        line=dict(width=0.5, color='white')),
            text=[G.nodes[n]['domain'] for n in node_ids],
            textposition='top center',
            textfont=dict(size=6),
            hovertext=hover, hoverinfo='text',
            showlegend=False,
        ), row=row, col=col)

    # Layout
    fig.update_layout(
        title=dict(
            text=f'Louvain Community Detection — {G.number_of_nodes()} constructs, '
                 f'{G.number_of_edges()} edges, {len(RESOLUTIONS)} resolutions',
            font=dict(size=16),
        ),
        width=1800, height=700 * rows,
        plot_bgcolor='white',
        showlegend=False,
    )

    # Remove axes from all subplots
    for i in range(1, n_res + 1):
        suffix = '' if i == 1 else str(i)
        fig.update_layout(**{
            f'xaxis{suffix}': dict(showgrid=False, zeroline=False, showticklabels=False),
            f'yaxis{suffix}': dict(showgrid=False, zeroline=False, showticklabels=False),
        })

    fig.write_html(str(output_path), include_plotlyjs='cdn')
    print(f'\nHTML saved -> {output_path}')


def main():
    with open(NETWORK_PATH) as f:
        network = json.load(f)

    results, G = detect_all(network)

    # Print detailed community info for best modularity
    best_res = max(results['resolutions'].values(), key=lambda x: x['modularity'])
    print(f'\nBest modularity: res={best_res["resolution"]} '
          f'(Q={best_res["modularity"]:.4f}, {best_res["n_communities"]} communities)')
    print(f'\n{"ID":>3} {"Size":>5} {"Domains":>7} {"Mean|γ|":>8} {"Max|γ|":>7} '
          f'{"Cross":>6} {"Bridge Node":40}')
    print('-' * 85)
    for c in best_res['communities']:
        bridge_label = c['bridge_node'].split(':')[1].replace('_', ' ')[:38] if ':' in c['bridge_node'] else ''
        bridge_dom = c['bridge_node'].split(':')[0] if ':' in c['bridge_node'] else ''
        print(f'{c["community_id"]:>3} {c["n_constructs"]:>5} {c["n_domains"]:>7} '
              f'{c["mean_gamma"]:>8.3f} {c["max_gamma"]:>7.3f} '
              f'{c["n_cross_domain_internal"]:>6} {bridge_dom}:{bridge_label}')

    # Print members of top communities
    for c in best_res['communities'][:8]:
        print(f'\n  Community {c["community_id"]} '
              f'(n={c["n_constructs"]}, domains={c["domains"]}):')
        for nid in c['constructs']:
            dom = nid.split(':')[0]
            name = nid.split(':')[1].replace('_', ' ')
            print(f'    {dom:>5}: {name}')

    # Save JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nJSON saved -> {OUTPUT_JSON}')

    # Render HTML
    try:
        render_html(network, results, G, OUTPUT_HTML)
    except ImportError:
        print('Plotly not available — skipping HTML')


if __name__ == '__main__':
    main()
