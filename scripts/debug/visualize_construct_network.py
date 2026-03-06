"""Construct network visualization — within-domain and cross-domain associations.

Builds the network from pre-computed data:
  - Within-domain edges: data/results/construct_network.json (from previous run)
  - Cross-domain edges: data/results/dr_sweep_results.json (full 276-pair sweep)
  - Causal direction: data/results/causal_direction_map.json (1361 construct pairs)

Outputs:
  - data/results/construct_network.json  — updated edge list with causal info
  - data/results/construct_network.html  — interactive Plotly network

Usage:
    python scripts/debug/visualize_construct_network.py [--gamma-threshold 0.05] [--recompute-within]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts' / 'debug'))

OUTPUT_JSON = ROOT / 'data' / 'results' / 'construct_network.json'
OUTPUT_HTML = ROOT / 'data' / 'results' / 'construct_network.html'
DR_SWEEP_PATH = ROOT / 'data' / 'results' / 'dr_sweep_results.json'
CAUSAL_MAP_PATH = ROOT / 'data' / 'results' / 'causal_direction_map.json'
EXISTING_NETWORK_PATH = ROOT / 'data' / 'results' / 'construct_network.json'


def _parse_var_id(var_id: str) -> Tuple[str, str]:
    """Parse 'agg_corruption_perception|COR' -> ('COR', 'corruption_perception')."""
    name, domain = var_id.split('|')
    return domain, name.replace('agg_', '')


def _pair_key(dom_a: str, name_a: str, dom_b: str, name_b: str) -> str:
    """Canonical key for a construct pair."""
    a = f'{dom_a}:{name_a}'
    b = f'{dom_b}:{name_b}'
    return '::'.join(sorted([a, b]))


def load_causal_direction_map() -> Dict[str, Dict]:
    """Load the causal direction map."""
    if not CAUSAL_MAP_PATH.exists():
        return {}
    with open(CAUSAL_MAP_PATH) as f:
        data = json.load(f)
    return data.get('pairs', {})


def load_cross_domain_edges(direction_map: Dict) -> List[Dict[str, Any]]:
    """Load cross-domain edges from the full DR sweep results."""
    if not DR_SWEEP_PATH.exists():
        print(f'  WARNING: {DR_SWEEP_PATH} not found')
        return []

    with open(DR_SWEEP_PATH) as f:
        sweep = json.load(f)

    edges = []
    for pair_key_str, pair_data in sweep.get('domain_pairs', {}).items():
        for est in pair_data.get('estimates', []):
            gamma = est.get('dr_gamma')
            if gamma is None:
                continue
            dom_a, name_a = _parse_var_id(est['var_a'])
            dom_b, name_b = _parse_var_id(est['var_b'])

            # Look up causal direction
            ck = _pair_key(dom_a, name_a, dom_b, name_b)
            cm_entry = direction_map.get(ck, {})
            direction = cm_entry.get('direction', 'ambiguous')
            dir_source = cm_entry.get('source', 'none')

            # Determine source/target based on causal direction
            source_dom, source_name = dom_a, name_a
            target_dom, target_name = dom_b, name_b
            if direction == 'causal' and cm_entry.get('cause'):
                cause_str = cm_entry['cause']  # e.g. "COR:corruption_perception"
                cause_dom = cause_str.split(':')[0] if ':' in cause_str else ''
                cause_name = cause_str.split(':')[1] if ':' in cause_str else ''
                if cause_dom == dom_b and cause_name == name_b:
                    source_dom, source_name = dom_b, name_b
                    target_dom, target_name = dom_a, name_a
                    gamma = -gamma  # flip sign when swapping

            edges.append({
                'source': f'{source_dom}:{source_name}',
                'target': f'{target_dom}:{target_name}',
                'source_domain': source_dom,
                'target_domain': target_dom,
                'gamma': round(gamma, 4),
                'cramers_v': round(est.get('dr_v', 0), 4),
                'ks_overlap': round(est.get('dr_ks', 0), 4),
                'cross_domain': True,
                'causal_direction': direction,
                'direction_source': dir_source,
            })

    return edges


def load_within_domain_edges(direction_map: Dict) -> List[Dict[str, Any]]:
    """Load within-domain edges from the existing construct network."""
    if not EXISTING_NETWORK_PATH.exists():
        print(f'  WARNING: {EXISTING_NETWORK_PATH} not found')
        return []

    with open(EXISTING_NETWORK_PATH) as f:
        network = json.load(f)

    edges = []
    for e in network.get('edges', []):
        if e.get('cross_domain', False):
            continue

        source = e['source']  # e.g. "CIE:science_self_efficacy"
        target = e['target']
        source_dom = source.split(':')[0]
        source_name = source.split(':')[1]
        target_dom = target.split(':')[0]
        target_name = target.split(':')[1]

        # Look up causal direction for intra-domain pairs
        ck = _pair_key(source_dom, source_name, target_dom, target_name)
        cm_entry = direction_map.get(ck, {})
        direction = cm_entry.get('direction', 'ambiguous')
        dir_source = cm_entry.get('source', 'none')

        # Orient by causal direction if available
        if direction == 'causal' and cm_entry.get('cause'):
            cause_str = cm_entry['cause']
            if cause_str == target:
                # Swap: target is actually the cause
                source, target = target, source
                source_dom, target_dom = target_dom, source_dom
                source_name, target_name = target_name, source_name
                e_gamma = -e.get('gamma', 0)
            else:
                e_gamma = e.get('gamma', 0)
        else:
            e_gamma = e.get('gamma', 0)

        edges.append({
            'source': source,
            'target': target,
            'source_domain': source_dom,
            'target_domain': target_dom,
            'gamma': round(e_gamma, 4),
            'cramers_v': round(e.get('cramers_v', 0), 4),
            'ks_overlap': round(e.get('ks_overlap', 0), 4),
            'cross_domain': False,
            'causal_direction': direction,
            'direction_source': dir_source,
        })

    return edges


def deduplicate_edges(edges: List[Dict]) -> List[Dict]:
    """Keep strongest edge per construct pair."""
    best = {}
    for e in edges:
        ck = _pair_key(
            e['source'].split(':')[0], e['source'].split(':')[1],
            e['target'].split(':')[0], e['target'].split(':')[1],
        )
        if ck not in best or abs(e['gamma']) > abs(best[ck]['gamma']):
            best[ck] = e
    return list(best.values())


def build_network(edges: List[Dict]) -> Dict[str, Any]:
    """Build network JSON from edges."""
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


def render_plotly_html(network: Dict, output_path: Path, gamma_threshold: float = 0.05) -> None:
    """Render interactive network with Plotly, including directional arrows."""
    import plotly.graph_objects as go

    nodes = network['nodes']
    edges = network['edges']
    domain_colors = network['domain_colors']

    # --- Compute edge weights first ---
    domains = sorted(set(n['domain'] for n in nodes))
    cross_all = [e for e in edges if e['cross_domain']]
    within_all = [e for e in edges if not e['cross_domain']]
    cross_gammas = sorted([abs(e['gamma']) for e in cross_all])
    cross_strong_thresh = np.percentile(cross_gammas, 99) if cross_gammas else 0.5
    cross_strong_thresh = max(cross_strong_thresh, 0.80)

    sig_edges = ([e for e in within_all if abs(e['gamma']) > gamma_threshold]
                 + [e for e in cross_all if abs(e['gamma']) > gamma_threshold])
    strong_edges = ([e for e in within_all if abs(e['gamma']) > 0.15]
                    + [e for e in cross_all if abs(e['gamma']) > cross_strong_thresh])
    causal_edges = [e for e in sig_edges if e.get('causal_direction') == 'causal'
                    and (not e['cross_domain'] or abs(e['gamma']) > cross_strong_thresh)]

    # Node connectivity weights (from strong edges)
    edge_count = {}
    edge_weight = {}
    for e in strong_edges:
        for nid in (e['source'], e['target']):
            edge_count[nid] = edge_count.get(nid, 0) + 1
            edge_weight[nid] = edge_weight.get(nid, 0.0) + abs(e['gamma'])
    max_weight = max(edge_weight.values()) if edge_weight else 1.0

    # --- Layout: 3 concentric rings by connectivity weight ---
    all_node_ids = [n['id'] for n in nodes]
    weights_list = [edge_weight.get(nid, 0) for nid in all_node_ids]
    nonzero_weights = [w for w in weights_list if w > 0]
    p95 = np.percentile(nonzero_weights, 89) if nonzero_weights else 1.0
    p40 = np.percentile(nonzero_weights, 40) if nonzero_weights else 0.5

    inner_ids = set()   # high: top 5% (P95+)
    middle_ids = set()  # medium: 40th-95th percentile
    outer_ids = set()   # low: below 40th or zero weight
    for nid in all_node_ids:
        w = edge_weight.get(nid, 0)
        if w >= p95:
            inner_ids.add(nid)
        elif w >= p40:
            middle_ids.add(nid)
        else:
            outer_ids.add(nid)

    r_inner_ring = 3.0
    r_middle_ring = 6.0
    r_outer_ring = 9.0

    node_pos = {}
    for tier_ids, radius in [(inner_ids, r_inner_ring),
                             (middle_ids, r_middle_ring),
                             (outer_ids, r_outer_ring)]:
        tier_list = sorted(tier_ids, key=lambda nid: -edge_weight.get(nid, 0))
        n_tier = len(tier_list)
        for j, nid in enumerate(tier_list):
            angle = 2 * math.pi * j / max(n_tier, 1)
            # Small jitter to avoid perfect overlap
            r = radius + 0.3 * (j % 3 - 1)
            node_pos[nid] = (r * math.cos(angle), r * math.sin(angle))

    def _xy(nid):
        return node_pos[nid]

    # --- Edge traces ---
    traces = []

    # Weak within-domain edges (grey)
    weak_within = [e for e in sig_edges
                   if abs(e['gamma']) <= 0.15 and not e['cross_domain']]
    x_w, y_w = [], []
    for e in weak_within:
        if e['source'] in node_pos and e['target'] in node_pos:
            x0, y0 = _xy(e['source'])
            x1, y1 = _xy(e['target'])
            x_w += [x0, x1, None]
            y_w += [y0, y1, None]
    traces.append(go.Scatter(
        x=x_w, y=y_w, mode='lines',
        line=dict(width=0.5, color='rgba(180,180,180,0.25)'),
        name=f'Weak within (|g|>{gamma_threshold:.2f})', hoverinfo='none',
    ))

    # Strong within-domain edges (blue)
    strong_within = [e for e in strong_edges if not e['cross_domain']]
    x_sw, y_sw = [], []
    for e in strong_within:
        if e['source'] in node_pos and e['target'] in node_pos:
            x0, y0 = _xy(e['source'])
            x1, y1 = _xy(e['target'])
            x_sw += [x0, x1, None]
            y_sw += [y0, y1, None]
    traces.append(go.Scatter(
        x=x_sw, y=y_sw, mode='lines',
        line=dict(width=2.0, color='rgba(66,133,244,0.6)'),
        name='Strong within-domain (|g|>0.15)', hoverinfo='none',
    ))

    # Strong cross-domain edges (red)
    strong_cross = [e for e in strong_edges if e['cross_domain']]
    x_sc, y_sc = [], []
    for e in strong_cross:
        if e['source'] in node_pos and e['target'] in node_pos:
            x0, y0 = _xy(e['source'])
            x1, y1 = _xy(e['target'])
            x_sc += [x0, x1, None]
            y_sc += [y0, y1, None]
    traces.append(go.Scatter(
        x=x_sc, y=y_sc, mode='lines',
        line=dict(width=1.5, color='rgba(220,50,50,0.5)'),
        name=f'Strong cross-domain (|g|>{cross_strong_thresh:.2f})', hoverinfo='none',
    ))

    # Ring guide annotations
    annotations = []
    for label, r in [('High connectivity', r_inner_ring),
                     ('Medium', r_middle_ring),
                     ('Low', r_outer_ring)]:
        annotations.append(dict(
            x=r + 0.3, y=0, text=f'<i>{label}</i>',
            showarrow=False, font=dict(size=10, color='rgba(120,120,120,0.6)'),
        ))

    # Ring circles as background traces
    for r in [r_inner_ring, r_middle_ring, r_outer_ring]:
        theta = np.linspace(0, 2 * np.pi, 100)
        traces.append(go.Scatter(
            x=(r * np.cos(theta)).tolist(),
            y=(r * np.sin(theta)).tolist(),
            mode='lines', line=dict(width=0.5, color='rgba(200,200,200,0.3)'),
            hoverinfo='none', showlegend=False,
        ))

    # Node trace
    positioned = [n for n in nodes if n['id'] in node_pos]
    node_x = [_xy(n['id'])[0] for n in positioned]
    node_y = [_xy(n['id'])[1] for n in positioned]
    node_colors = [n['color'] for n in positioned]
    # Labels include domain prefix for identification
    node_labels = [f"{n['domain']}:{n['label'][:25]}" for n in positioned]

    # Node sizes: min 10px (outer), max ~45px (inner hub)
    node_sizes = [
        10 + 35 * (edge_weight.get(n['id'], 0) / max_weight)
        for n in positioned
    ]

    # Hover text
    causal_out = {}
    causal_in = {}
    for e in causal_edges:
        causal_out[e['source']] = causal_out.get(e['source'], 0) + 1
        causal_in[e['target']] = causal_in.get(e['target'], 0) + 1

    hover_text = []
    for n in positioned:
        nid = n['id']
        c_out = causal_out.get(nid, 0)
        c_in = causal_in.get(nid, 0)
        n_strong = edge_count.get(nid, 0)
        w = edge_weight.get(nid, 0)
        tier = 'Inner' if nid in inner_ids else ('Middle' if nid in middle_ids else 'Outer')
        causal_str = f'<br>Causes: {c_out} | Effects: {c_in}' if (c_out + c_in) > 0 else ''
        hover_text.append(
            f"<b>{n['label']}</b><br>Domain: {n['domain']} | Ring: {tier}"
            f"<br>Strong connections: {n_strong} (sum |g|={w:.2f}){causal_str}"
        )

    # Plotly Scatter textfont.size doesn't support per-point arrays,
    # so we create separate traces per tier
    base_font = 8
    node_traces_by_tier = []
    for tier_name, tier_set, font_size in [
        ('inner', inner_ids, base_font * 2),
        ('middle', middle_ids, int(base_font * 1.5)),
        ('outer', outer_ids, base_font),
    ]:
        tier_indices = [i for i, n in enumerate(positioned) if n['id'] in tier_set]
        if not tier_indices:
            continue
        node_traces_by_tier.append(go.Scatter(
            x=[node_x[i] for i in tier_indices],
            y=[node_y[i] for i in tier_indices],
            mode='markers+text',
            marker=dict(
                size=[node_sizes[i] for i in tier_indices],
                color=[node_colors[i] for i in tier_indices],
                line=dict(width=1, color='white'),
            ),
            text=[node_labels[i] for i in tier_indices],
            textposition='top center',
            textfont=dict(size=font_size),
            hovertext=[hover_text[i] for i in tier_indices],
            hoverinfo='text',
            name=f'Constructs ({tier_name})', showlegend=False,
        ))

    # Domain color legend — one invisible trace per domain
    domain_legend_traces = []
    for domain in sorted(domain_colors):
        domain_legend_traces.append(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(size=10, color=domain_colors[domain]),
            name=domain, legendgroup='domains',
        ))

    fig = go.Figure(
        data=traces + node_traces_by_tier + domain_legend_traces,
        layout=go.Layout(
            title=dict(
                text=(f'Construct Association Network — {len(nodes)} constructs, '
                      f'{len(strong_edges)} strong edges '
                      f'(inner={len(inner_ids)}, mid={len(middle_ids)}, outer={len(outer_ids)})'),
                font=dict(size=14),
            ),
            showlegend=True,
            hovermode='closest',
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       scaleanchor='x', scaleratio=1),
            width=1600, height=1200,
            plot_bgcolor='white',
        ),
    )

    fig.write_html(str(output_path), include_plotlyjs='cdn')
    print(f'  HTML saved -> {output_path}')


def main(gamma_threshold: float = 0.05, recompute_within: bool = False):
    t0 = time.time()

    # Load causal direction map
    print('Loading causal direction map...', flush=True)
    direction_map = load_causal_direction_map()
    n_causal = sum(1 for v in direction_map.values() if v.get('direction') == 'causal')
    n_intra = sum(1 for k in direction_map
                  if k.split('::')[0].split(':')[0] == k.split('::')[1].split(':')[0])
    print(f'  {len(direction_map)} pairs: {n_causal} causal, '
          f'{len(direction_map) - n_causal} ambiguous/empirical, {n_intra} intra-domain')

    # Load within-domain edges (from existing network or recompute)
    if recompute_within:
        print('\nRecomputing within-domain edges...', flush=True)
        within_edges = _recompute_within_domain_edges(direction_map)
    else:
        print('\nLoading within-domain edges from existing network...', flush=True)
        within_edges = load_within_domain_edges(direction_map)
    print(f'  {len(within_edges)} within-domain edges')

    # Load cross-domain edges from DR sweep
    print('\nLoading cross-domain edges from DR sweep...', flush=True)
    cross_edges = load_cross_domain_edges(direction_map)
    print(f'  {len(cross_edges)} cross-domain edges (raw)')

    # Combine and deduplicate
    all_edges = within_edges + cross_edges
    all_edges = deduplicate_edges(all_edges)
    print(f'\nAfter deduplication: {len(all_edges)} edges')

    # Stats
    within_final = [e for e in all_edges if not e['cross_domain']]
    cross_final = [e for e in all_edges if e['cross_domain']]
    causal_final = [e for e in all_edges if e.get('causal_direction') == 'causal']
    strong = [e for e in all_edges if abs(e['gamma']) > 0.15]
    gammas = [abs(e['gamma']) for e in all_edges]

    print(f'  Within-domain: {len(within_final)} edges'
          f' (mean |g|={np.mean([abs(e["gamma"]) for e in within_final]):.3f})')
    print(f'  Cross-domain:  {len(cross_final)} edges'
          f' (mean |g|={np.mean([abs(e["gamma"]) for e in cross_final]):.3f})')
    print(f'  Causal arrows: {len(causal_final)}')
    print(f'  Strong (|g|>0.15): {len(strong)}')
    print(f'  Gamma distribution: mean={np.mean(gammas):.3f}, '
          f'median={np.median(gammas):.3f}, P90={np.percentile(gammas, 90):.3f}')

    # Build network
    network = build_network(all_edges)
    elapsed = time.time() - t0
    network['metadata'] = {
        'n_nodes': len(network['nodes']),
        'n_edges': len(all_edges),
        'n_within': len(within_final),
        'n_cross': len(cross_final),
        'n_causal_arrows': len(causal_final),
        'n_strong': len(strong),
        'gamma_threshold': gamma_threshold,
        'elapsed_seconds': round(elapsed, 1),
        'sources': {
            'within_domain': str(EXISTING_NETWORK_PATH),
            'cross_domain': str(DR_SWEEP_PATH),
            'causal_direction': str(CAUSAL_MAP_PATH),
        },
    }

    # Save JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(network, f, indent=2)
    print(f'\n  JSON saved -> {OUTPUT_JSON}')

    # Render HTML
    try:
        render_plotly_html(network, OUTPUT_HTML, gamma_threshold=gamma_threshold)
    except ImportError:
        print('  Plotly not available -- skipping HTML render')

    # Top edges table
    edges_sorted = sorted(all_edges, key=lambda e: -abs(e['gamma']))
    print(f'\n=== TOP 30 STRONGEST EDGES ===')
    print(f'{"Source":40} {"Dir":>3} {"Target":40} {"gamma":>7} {"Type":>6} {"Causal":>8}')
    print('-' * 105)
    for e in edges_sorted[:30]:
        s = e['source'].split(':')[1].replace('_', ' ')[:38]
        t = e['target'].split(':')[1].replace('_', ' ')[:38]
        typ = 'CROSS' if e['cross_domain'] else 'within'
        arrow = ' -> ' if e.get('causal_direction') == 'causal' else ' ~  '
        cdir = e.get('causal_direction', '?')
        print(f'{s:40}{arrow}{t:40} {e["gamma"]:+.3f} {typ:>6} {cdir:>8}')

    # Causal chains (intra-domain)
    print(f'\n=== INTRA-DOMAIN CAUSAL CHAINS ===')
    intra_causal = [e for e in all_edges
                    if not e['cross_domain'] and e.get('causal_direction') == 'causal']
    by_domain = {}
    for e in intra_causal:
        d = e['source_domain']
        by_domain.setdefault(d, []).append(e)
    for d in sorted(by_domain):
        print(f'\n  {d}:')
        for e in sorted(by_domain[d], key=lambda x: -abs(x['gamma'])):
            s = e['source'].split(':')[1].replace('_', ' ')
            t = e['target'].split(':')[1].replace('_', ' ')
            print(f'    {s} -> {t}  (g={e["gamma"]:+.3f})')

    print(f'\nDone in {elapsed:.1f}s')


def _recompute_within_domain_edges(direction_map: Dict) -> List[Dict]:
    """Recompute within-domain edges live using DR estimator."""
    import warnings
    warnings.filterwarnings('ignore')

    from dataset_knowledge import los_mex_dict, enc_nom_dict
    from ses_analysis import AnalysisConfig
    from select_bridge_variables_semantic import SemanticVariableSelector
    from ses_regression import DoublyRobustBridgeEstimator

    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get('enc_dict', los_mex_dict.get('enc_dict', {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}
    SemanticVariableSelector.build_aggregates(enc_dict, enc_nom_dict_rev)

    with open(ROOT / 'data' / 'results' / 'semantic_variable_selection.json') as f:
        sel_data = json.load(f)

    edges = []
    from itertools import combinations
    for code, domain_data in sorted(sel_data['domains'].items()):
        title = domain_data.get('survey_title', '')
        v = enc_dict.get(title)
        if not v:
            continue
        df = v['dataframe']

        strats = domain_data.get('variable_strategies', [])
        constructs = []
        for s in strats:
            if s.get('action') == 'skip':
                continue
            name = s.get('construct_name', '')
            col = f'agg_{name}'
            if col in df.columns:
                constructs.append({'name': name, 'col': col, 'domain': code})

        if len(constructs) < 2:
            continue

        for ca, cb in combinations(constructs, 2):
            est = DoublyRobustBridgeEstimator(n_sim=300, n_bootstrap=3, max_categories=5)
            try:
                r = est.estimate(
                    var_id_a=f'{ca["col"]}|{code}',
                    var_id_b=f'{cb["col"]}|{code}',
                    df_a=df, df_b=df, col_a=ca['col'], col_b=cb['col'])
                if not r:
                    continue
            except Exception:
                continue

            ck = _pair_key(code, ca['name'], code, cb['name'])
            cm_entry = direction_map.get(ck, {})
            direction = cm_entry.get('direction', 'ambiguous')
            dir_source = cm_entry.get('source', 'none')

            source, target = f'{code}:{ca["name"]}', f'{code}:{cb["name"]}'
            gamma = r['gamma']
            if direction == 'causal' and cm_entry.get('cause') == target:
                source, target = target, source
                gamma = -gamma

            edges.append({
                'source': source,
                'target': target,
                'source_domain': code,
                'target_domain': code,
                'gamma': round(gamma, 4),
                'cramers_v': round(r.get('cramers_v', 0), 4),
                'ks_overlap': round(r.get('propensity_overlap', 0), 4),
                'cross_domain': False,
                'causal_direction': direction,
                'direction_source': dir_source,
            })
            s = ca['name'][:30]
            t = cb['name'][:30]
            arrow = '->' if direction == 'causal' else '~ '
            print(f'    {code}: {s:30} {arrow} {t:30} g={gamma:+.3f}', flush=True)

    return edges


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gamma-threshold', type=float, default=0.05,
                        help='Minimum |gamma| to display an edge')
    parser.add_argument('--recompute-within', action='store_true',
                        help='Recompute within-domain edges (slow)')
    args = parser.parse_args()
    main(gamma_threshold=args.gamma_threshold, recompute_within=args.recompute_within)
