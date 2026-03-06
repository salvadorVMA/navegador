"""Construct network visualization — within-domain and cross-domain associations.

Runs DRPredictionEngine on selected domain pairs to build a network of
construct-level associations. Outputs:
  - data/results/construct_network.json  — edge list with DR gamma
  - data/results/construct_network.html  — interactive Plotly network

Usage:
    python scripts/debug/visualize_construct_network.py [--pairs N] [--fast]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts' / 'debug'))

OUTPUT_JSON = ROOT / 'data' / 'results' / 'construct_network.json'
OUTPUT_HTML = ROOT / 'data' / 'results' / 'construct_network.html'


def load_data():
    from dataset_knowledge import los_mex_dict, enc_nom_dict
    from ses_analysis import AnalysisConfig
    from select_bridge_variables_semantic import SemanticVariableSelector

    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get('enc_dict', los_mex_dict.get('enc_dict', {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}
    SemanticVariableSelector.build_aggregates(enc_dict, enc_nom_dict_rev)
    sel = SemanticVariableSelector.load()

    with open(ROOT / 'data' / 'results' / 'semantic_variable_selection.json') as f:
        sel_data = json.load(f)

    return enc_dict, enc_nom_dict_rev, sel, sel_data


def get_df(enc_dict, sel_data, domain_code):
    title = sel_data['domains'].get(domain_code, {}).get('survey_title', '')
    v = enc_dict.get(title)
    return v['dataframe'] if v else None


def get_constructs(sel_data, domain_code) -> List[Dict[str, str]]:
    """Get construct names and their agg column names for a domain."""
    strats = sel_data['domains'].get(domain_code, {}).get('variable_strategies', [])
    constructs = []
    for s in strats:
        if s.get('action') == 'skip':
            continue
        name = s.get('construct_name', '')
        col = f'agg_{name}'
        constructs.append({'name': name, 'col': col, 'domain': domain_code})
    return constructs


def estimate_edge(
    df_a, df_b, construct_a, construct_b, n_sim=500, n_bootstrap=5, max_categories=5,
    direction_map=None,
) -> Optional[Dict[str, Any]]:
    """Estimate DR gamma between two constructs.

    If direction_map is provided and indicates a causal direction, the source/target
    in the returned edge reflect cause→effect ordering.
    """
    from ses_regression import DoublyRobustBridgeEstimator
    from select_bridge_variables_semantic import SemanticVariableSelector

    col_a = construct_a['col']
    col_b = construct_b['col']
    dom_a = construct_a['domain']
    dom_b = construct_b['domain']
    if col_a not in df_a.columns or col_b not in df_b.columns:
        return None

    # Resolve causal direction for cross-domain pairs (construct-level)
    causal_dir = 'within'
    if dom_a != dom_b and direction_map:
        src, tgt, dir_type = SemanticVariableSelector.get_pair_direction(
            dom_a, dom_b, direction_map,
            construct_a=construct_a['name'], construct_b=construct_b['name'])
        causal_dir = dir_type
        # Determine if we need to swap: src might be "DOMAIN:construct" or "DOMAIN"
        src_dom = src.split(':')[0] if ':' in src else src
        if src_dom == dom_b:
            df_a, df_b = df_b, df_a
            col_a, col_b = col_b, col_a
            construct_a, construct_b = construct_b, construct_a
            dom_a, dom_b = dom_b, dom_a

    est = DoublyRobustBridgeEstimator(
        n_sim=n_sim, n_bootstrap=n_bootstrap, max_categories=max_categories)
    try:
        r = est.estimate(
            var_id_a=f"{col_a}|{dom_a}",
            var_id_b=f"{col_b}|{dom_b}",
            df_a=df_a, df_b=df_b, col_a=col_a, col_b=col_b)
        if r:
            return {
                'source': f"{dom_a}:{construct_a['name']}",
                'target': f"{dom_b}:{construct_b['name']}",
                'source_domain': dom_a,
                'target_domain': dom_b,
                'gamma': r['gamma'],
                'cramers_v': r['cramers_v'],
                'ks_overlap': r['propensity_overlap'],
                'cross_domain': dom_a != dom_b,
                'causal_direction': causal_dir,
            }
    except Exception:
        pass
    return None


def build_network(edges: List[Dict], sel_data: dict) -> Dict[str, Any]:
    """Build network JSON from edges."""
    # Nodes: all unique constructs
    node_set = set()
    for e in edges:
        node_set.add(e['source'])
        node_set.add(e['target'])

    nodes = []
    for n in sorted(node_set):
        domain, name = n.split(':', 1)
        nodes.append({
            'id': n,
            'label': name.replace('_', ' ').title(),
            'domain': domain,
        })

    # Domain colors
    domains = sorted(set(n['domain'] for n in nodes))
    colors = [
        '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
        '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
        '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000',
        '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9',
        '#e6beff', '#1f77b4', '#ff7f0e', '#2ca02c',
    ]
    domain_color = {d: colors[i % len(colors)] for i, d in enumerate(domains)}
    for n in nodes:
        n['color'] = domain_color[n['domain']]

    return {
        'nodes': nodes,
        'edges': edges,
        'domain_colors': domain_color,
    }


def render_plotly_html(network: Dict, output_path: Path) -> None:
    """Render interactive network with Plotly."""
    import plotly.graph_objects as go

    nodes = network['nodes']
    edges = network['edges']
    domain_colors = network['domain_colors']

    # Layout: group by domain using a circular arrangement
    domains = sorted(set(n['domain'] for n in nodes))
    domain_idx = {d: i for i, d in enumerate(domains)}

    # Position nodes: domains around a circle, constructs within each domain
    node_pos = {}
    n_domains = len(domains)
    for d in domains:
        d_nodes = [n for n in nodes if n['domain'] == d]
        angle_center = 2 * np.pi * domain_idx[d] / n_domains
        r_domain = 3.0  # radius for domain centers
        cx = r_domain * np.cos(angle_center)
        cy = r_domain * np.sin(angle_center)
        # Spread constructs around domain center
        n_c = len(d_nodes)
        for j, n in enumerate(d_nodes):
            a = angle_center + (j - n_c/2) * 0.15
            r = r_domain + 0.3 * (j % 2) - 0.15
            node_pos[n['id']] = (
                cx + 0.6 * np.cos(a + np.pi/2 * (j % 2)),
                cy + 0.6 * np.sin(a + np.pi/2 * (j % 2)),
            )

    # Filter edges by |gamma| threshold
    sig_edges = [e for e in edges if abs(e['gamma']) > 0.05]
    strong_edges = [e for e in edges if abs(e['gamma']) > 0.15]

    # Edge traces (weak and strong)
    edge_traces = []
    for edge_set, width, opacity, name in [
        (sig_edges, 1.0, 0.3, 'Weak (|g|>0.05)'),
        (strong_edges, 2.5, 0.7, 'Strong (|g|>0.15)'),
    ]:
        x_edges, y_edges = [], []
        for e in edge_set:
            if e['source'] in node_pos and e['target'] in node_pos:
                x0, y0 = node_pos[e['source']]
                x1, y1 = node_pos[e['target']]
                x_edges += [x0, x1, None]
                y_edges += [y0, y1, None]
        color = 'rgba(200,50,50,{})'.format(opacity) if name.startswith('Strong') else 'rgba(150,150,150,{})'.format(opacity)
        edge_traces.append(go.Scatter(
            x=x_edges, y=y_edges, mode='lines',
            line=dict(width=width, color=color),
            name=name, hoverinfo='none',
        ))

    # Cross-domain strong edges highlighted
    cross_strong = [e for e in strong_edges if e['cross_domain']]
    x_cross, y_cross = [], []
    for e in cross_strong:
        if e['source'] in node_pos and e['target'] in node_pos:
            x0, y0 = node_pos[e['source']]
            x1, y1 = node_pos[e['target']]
            x_cross += [x0, x1, None]
            y_cross += [y0, y1, None]
    edge_traces.append(go.Scatter(
        x=x_cross, y=y_cross, mode='lines',
        line=dict(width=3, color='rgba(255,0,0,0.6)'),
        name='Cross-domain strong', hoverinfo='none',
    ))

    # Node trace
    node_x = [node_pos[n['id']][0] for n in nodes if n['id'] in node_pos]
    node_y = [node_pos[n['id']][1] for n in nodes if n['id'] in node_pos]
    node_colors = [n['color'] for n in nodes if n['id'] in node_pos]
    node_labels = [n['label'] for n in nodes if n['id'] in node_pos]
    node_domains = [n['domain'] for n in nodes if n['id'] in node_pos]

    # Count edges per node for sizing
    edge_count = {}
    for e in sig_edges:
        edge_count[e['source']] = edge_count.get(e['source'], 0) + 1
        edge_count[e['target']] = edge_count.get(e['target'], 0) + 1
    node_sizes = [8 + 3 * edge_count.get(n['id'], 0) for n in nodes if n['id'] in node_pos]

    hover_text = [
        f"<b>{label}</b><br>Domain: {dom}<br>Connections: {edge_count.get(nodes[i]['id'], 0)}"
        for i, (label, dom) in enumerate(zip(node_labels, node_domains))
        if nodes[i]['id'] in node_pos
    ]

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        marker=dict(size=node_sizes, color=node_colors,
                    line=dict(width=1, color='white')),
        text=node_labels, textposition='top center',
        textfont=dict(size=7),
        hovertext=hover_text, hoverinfo='text',
        name='Constructs',
    )

    # Domain legend annotations
    annotations = []
    for d in domains:
        d_nodes_in = [n for n in nodes if n['domain'] == d and n['id'] in node_pos]
        if d_nodes_in:
            cx = np.mean([node_pos[n['id']][0] for n in d_nodes_in])
            cy = np.mean([node_pos[n['id']][1] for n in d_nodes_in])
            annotations.append(dict(
                x=cx, y=cy + 0.8, text=f'<b>{d}</b>',
                showarrow=False, font=dict(size=11, color=domain_colors[d]),
            ))

    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title=dict(
                text='Construct Association Network (DR gamma)',
                font=dict(size=16),
            ),
            showlegend=True,
            hovermode='closest',
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            width=1400, height=1000,
            plot_bgcolor='white',
        ),
    )

    fig.write_html(str(output_path), include_plotlyjs='cdn')
    print(f'  HTML saved -> {output_path}')


def main(max_cross_pairs: int = 30, max_within_pairs: int = 24, fast: bool = True):
    t0 = time.time()
    print('Loading data...', flush=True)
    enc_dict, enc_nom_dict_rev, sel, sel_data = load_data()

    # Load causal direction map
    from select_bridge_variables_semantic import SemanticVariableSelector
    direction_map = SemanticVariableSelector.load_causal_direction_map()
    n_causal = sum(1 for v in direction_map.values() if v['direction'] == 'causal')
    print(f'Causal direction map: {n_causal} causal, '
          f'{len(direction_map) - n_causal} ambiguous')

    # Build construct list
    all_constructs = {}  # domain -> list of construct dicts
    for code in sorted(sel_data['domains'].keys()):
        cs = get_constructs(sel_data, code)
        df = get_df(enc_dict, sel_data, code)
        # Only keep constructs that have the column in the dataframe
        if df is not None:
            cs = [c for c in cs if c['col'] in df.columns]
        all_constructs[code] = cs

    n_total = sum(len(v) for v in all_constructs.values())
    print(f'Constructs: {n_total} across {len(all_constructs)} domains')

    n_sim = 300 if fast else 500
    n_boot = 3 if fast else 10
    edges = []

    # --- Within-domain edges (all 5C2 = 10 pairs per domain) ---
    print(f'\n--- Within-domain edges ---', flush=True)
    n_within = 0
    for code, cs in all_constructs.items():
        df = get_df(enc_dict, sel_data, code)
        if df is None or len(cs) < 2:
            continue
        for ca, cb in combinations(cs, 2):
            edge = estimate_edge(df, df, ca, cb, n_sim=n_sim, n_bootstrap=n_boot)
            if edge:
                edges.append(edge)
                g = edge['gamma']
                marker = '*' if abs(g) > 0.15 else ' '
                n_within += 1
                print(f'  {marker} {code}: {ca["name"][:30]:30} x {cb["name"][:30]:30} g={g:+.3f}',
                      flush=True)

    print(f'  Within-domain: {n_within} edges', flush=True)

    # --- Cross-domain edges (top pairs by construct similarity) ---
    print(f'\n--- Cross-domain edges (sampling {max_cross_pairs} pairs) ---', flush=True)
    domain_codes = sorted(all_constructs.keys())
    cross_pairs = list(combinations(domain_codes, 2))
    # Prioritize pairs with clear causal direction, then by construct count
    def pair_priority(p):
        pk = '::'.join(sorted(p))
        info = direction_map.get(pk, {})
        has_dir = 1 if info.get('direction') == 'causal' else 0
        n_constructs = len(all_constructs[p[0]]) * len(all_constructs[p[1]])
        return (-has_dir, -n_constructs)
    cross_pairs.sort(key=pair_priority)

    n_cross = 0
    for da, db in cross_pairs:
        if n_cross >= max_cross_pairs:
            break
        df_a = get_df(enc_dict, sel_data, da)
        df_b = get_df(enc_dict, sel_data, db)
        if df_a is None or df_b is None:
            continue
        cs_a = all_constructs[da]
        cs_b = all_constructs[db]
        if not cs_a or not cs_b:
            continue

        # Pick first construct from each domain (strongest/most representative)
        ca = cs_a[0]
        cb = cs_b[0]
        edge = estimate_edge(df_a, df_b, ca, cb, n_sim=n_sim, n_bootstrap=n_boot,
                             direction_map=direction_map)
        if edge:
            edges.append(edge)
            g = edge['gamma']
            arrow = '→' if edge.get('causal_direction') == 'causal' else '~'
            marker = '*' if abs(g) > 0.15 else ' '
            n_cross += 1
            src_d = edge['source_domain']
            tgt_d = edge['target_domain']
            print(f'  {marker} {src_d}{arrow}{tgt_d}: '
                  f'{edge["source"].split(":")[1][:28]:28} {arrow} '
                  f'{edge["target"].split(":")[1][:28]:28} g={g:+.3f}',
                  flush=True)

    # Also run a few more cross-domain pairs for domains with strong signal
    strong_cross = [e for e in edges if e['cross_domain'] and abs(e['gamma']) > 0.10]
    print(f'\n--- Expanding {len(strong_cross)} strong cross-domain pairs ---', flush=True)
    for se in strong_cross[:10]:
        da = se['source_domain']
        db = se['target_domain']
        df_a = get_df(enc_dict, sel_data, da)
        df_b = get_df(enc_dict, sel_data, db)
        if df_a is None or df_b is None:
            continue
        cs_a = all_constructs[da]
        cs_b = all_constructs[db]
        existing = {(e['source'], e['target']) for e in edges}
        for ca in cs_a[1:3]:
            for cb in cs_b[1:3]:
                key = (f"{ca['domain']}:{ca['name']}", f"{cb['domain']}:{cb['name']}")
                if key in existing:
                    continue
                edge = estimate_edge(df_a, df_b, ca, cb, n_sim=n_sim, n_bootstrap=n_boot,
                                     direction_map=direction_map)
                if edge:
                    edges.append(edge)
                    g = edge['gamma']
                    arrow = '→' if edge.get('causal_direction') == 'causal' else '~'
                    print(f'    {da}{arrow}{db}: {ca["name"][:28]:28} {arrow} {cb["name"][:28]:28} g={g:+.3f}',
                          flush=True)

    elapsed = time.time() - t0
    print(f'\nTotal edges: {len(edges)} ({elapsed:.0f}s)')

    # Summary stats
    gammas = [abs(e['gamma']) for e in edges]
    cross_gammas = [abs(e['gamma']) for e in edges if e['cross_domain']]
    within_gammas = [abs(e['gamma']) for e in edges if not e['cross_domain']]
    print(f'  Within-domain: {len(within_gammas)} edges, mean |g|={np.mean(within_gammas):.3f}' if within_gammas else '')
    print(f'  Cross-domain:  {len(cross_gammas)} edges, mean |g|={np.mean(cross_gammas):.3f}' if cross_gammas else '')
    print(f'  Strong (|g|>0.15): {sum(1 for g in gammas if g > 0.15)}')

    # Save JSON
    network = build_network(edges, sel_data)
    network['metadata'] = {
        'n_edges': len(edges),
        'n_nodes': len(network['nodes']),
        'n_strong': sum(1 for g in gammas if g > 0.15),
        'elapsed_seconds': round(elapsed, 1),
        'n_sim': n_sim,
        'n_bootstrap': n_boot,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(network, f, indent=2)
    print(f'  JSON saved -> {OUTPUT_JSON}')

    # Render HTML
    try:
        render_plotly_html(network, OUTPUT_HTML)
    except ImportError:
        print('  Plotly not available — skipping HTML render')

    # Print top edges
    edges_sorted = sorted(edges, key=lambda e: -abs(e['gamma']))
    print(f'\n=== TOP 20 STRONGEST EDGES ===')
    print(f'{"source":40} {"target":40} {"gamma":>7} {"type":>6}')
    print('-' * 95)
    for e in edges_sorted[:20]:
        s = e['source'].split(':')[1].replace('_',' ')[:38]
        t = e['target'].split(':')[1].replace('_',' ')[:38]
        typ = 'CROSS' if e['cross_domain'] else 'within'
        print(f'{s:40} {t:40} {e["gamma"]:+.3f} {typ:>6}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=int, default=30,
                        help='Max cross-domain pairs to test')
    parser.add_argument('--fast', action='store_true', default=True,
                        help='Fast mode (n_sim=300, n_boot=3)')
    args = parser.parse_args()
    main(max_cross_pairs=args.pairs, fast=args.fast)
