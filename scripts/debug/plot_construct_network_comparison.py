"""Two-panel construct network: Theory (left) vs Empirical (right).

Left panel:  Cross-domain theoretical edges from causal_direction_map.json
             (derived from per-domain literature reviews in step2_research_review)
Right panel: Empirically observed edges from v3 DR bridge estimation
Both panels share identical node layout and domain markers.

Outputs:
  data/results/construct_network_comparison.png
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SWEEP_PATH = ROOT / 'data' / 'results' / 'dr_sweep_results_v3.json'
SVS_PATH = ROOT / 'data' / 'results' / 'semantic_variable_selection.json'
CAUSAL_MAP_PATH = ROOT / 'data' / 'results' / 'causal_direction_map.json'
OUTPUT_PNG = ROOT / 'data' / 'results' / 'construct_network_comparison.png'

# ── Semantic similarity flags ──
TAUTOLOGICAL_PAIRS = {
    frozenset(['agg_digital_and_cultural_capital|EDU', 'agg_digital_access_and_equipment|SOC']),
    frozenset(['agg_science_technology_engagement|CIE', 'agg_digital_literacy_and_internet_engagement|SOC']),
    frozenset(['p14|HAB', 'agg_material_living_standards|POB']),
}
HIGH_OVERLAP_PAIRS = {
    frozenset(['agg_science_technology_engagement|CIE', 'agg_digital_civic_and_political_participation|SOC']),
    frozenset(['agg_education_quality_and_opportunity|NIN', 'agg_material_living_standards|POB']),
    frozenset(['agg_institutional_trust_and_representativeness|FED', 'agg_digital_civic_and_political_participation|SOC']),
    frozenset(['agg_cultural_openness|GLO', 'agg_media_consumption_and_news_habits|SOC']),
    frozenset(['agg_civil_liberties_and_protest_rights|DER', 'agg_cosmopolitan_identity|GLO']),
    frozenset(['agg_cultural_socialization_in_childhood|DEP', 'agg_cultural_openness|GLO']),
}

DOMAIN_FULL_NAMES = {
    'CIE': 'Ciencia y\nTecnologia', 'COR': 'Corrupcion y\nLegalidad',
    'CUL': 'Cultura\nPolitica', 'DEP': 'Cultura, Lectura\ny Deporte',
    'DER': 'Derechos\nHumanos', 'ECO': 'Economia\ny Empleo',
    'EDU': 'Educacion', 'ENV': 'Envejecimiento',
    'FAM': 'Familia', 'FED': 'Federalismo',
    'GEN': 'Genero', 'GLO': 'Globalizacion',
    'HAB': 'Habitabilidad', 'IDE': 'Identidad\ny Valores',
    'IND': 'Indigenas', 'JUS': 'Justicia',
    'MED': 'Medio\nAmbiente', 'MIG': 'Migracion',
    'NIN': 'Ninos y\nJovenes', 'POB': 'Pobreza',
    'REL': 'Religion', 'SAL': 'Salud',
    'SEG': 'Seguridad\nPublica', 'SOC': 'Sociedad de la\nInformacion',
}

RAW_QUESTION_SUMMARIES = {
    'p14': 'p_housing_ownership', 'p18_1a_1': 'p_indigenous_group_knowledge',
    'p18_1': 'p_purpose_of_reading', 'p19': 'p_job_value_preference',
    'p1_2': 'p_father_education_level', 'p23_1': 'p_healthcare_financial_burden',
    'p24': 'p_healthcare_access_choice', 'p26_1': 'p_child_corporal_punishment',
    'p34': 'p_alcohol_consumption_freq', 'p52': 'p_national_emotion',
}


def _parse_var(var_id: str):
    name, domain = var_id.split('|')
    short = name.replace('agg_', '')
    if short in RAW_QUESTION_SUMMARIES:
        short = RAW_QUESTION_SUMMARIES[short]
    return domain, short


def get_edge_flag(src_full, tgt_full):
    pair = frozenset([src_full, tgt_full])
    if pair in TAUTOLOGICAL_PAIRS:
        return 'tautological'
    if pair in HIGH_OVERLAP_PAIRS:
        return 'overlap'
    return 'substantive'


def load_empirical_edges():
    with open(SWEEP_PATH) as f:
        data = json.load(f)

    edges = []
    for pair_key, est in data['estimates'].items():
        ci_lo, ci_hi = est['dr_gamma_ci']
        gamma = est['dr_gamma']
        ci_w = ci_hi - ci_lo
        if ci_w <= 0:
            continue
        if ci_lo > 0 or ci_hi < 0:
            tier = 'A'
        else:
            dist = min(abs(ci_lo), abs(ci_hi))
            frac = dist / ci_w
            if frac <= 0.025:
                tier = 'B'
            elif frac <= 0.05:
                tier = 'C'
            else:
                continue

        parts = pair_key.split('::')
        src_dom, src_name = _parse_var(parts[0])
        tgt_dom, tgt_name = _parse_var(parts[1])
        flag = get_edge_flag(parts[0], parts[1])

        edges.append({
            'source': f'{src_dom}:{src_name}',
            'target': f'{tgt_dom}:{tgt_name}',
            'gamma': gamma, 'tier': tier, 'flag': flag,
        })
    return edges


def load_theoretical_edges():
    """Load cross-domain theoretical edges from causal_direction_map.json."""
    with open(CAUSAL_MAP_PATH) as f:
        cm = json.load(f)

    edges = []
    for pair_key, info in cm['pairs'].items():
        if info['source'] != 'theoretical':
            continue
        parts = pair_key.split('::')
        dom_a = parts[0].split(':')[0]
        dom_b = parts[1].split(':')[0]
        if dom_a == dom_b:
            continue  # only cross-domain

        edges.append({
            'source': parts[0],  # e.g. 'CIE:science_self_efficacy'
            'target': parts[1],
            'direction': info['direction'],
            'cause': info.get('cause'),
        })
    return edges


def collect_all_nodes(empirical_edges):
    with open(SVS_PATH) as f:
        svs = json.load(f)
    nodes = {}
    for domain_code, domain_data in svs['domains'].items():
        for cluster in domain_data.get('construct_clusters', []):
            name = cluster['name']
            nid = f'{domain_code}:{name}'
            nodes[nid] = {'domain': domain_code, 'name': name, 'is_raw': False}
        strats = domain_data.get('variable_strategies', [])
        for s in strats:
            if s.get('action') in ('use_single', 'singleton'):
                col = s.get('bridge_column', '')
                if col and not col.startswith('agg_'):
                    display_name = RAW_QUESTION_SUMMARIES.get(col, col)
                    nid = f'{domain_code}:{display_name}'
                    if nid not in nodes:
                        nodes[nid] = {'domain': domain_code, 'name': display_name, 'is_raw': True}
    for e in empirical_edges:
        for nid_key in [e['source'], e['target']]:
            if nid_key not in nodes:
                dom, name = nid_key.split(':', 1)
                nodes[nid_key] = {'domain': dom, 'name': name, 'is_raw': not name.startswith('agg_')}
    return nodes


def layout_nodes(nodes, empirical_edges):
    connected_emp = set()
    for e in empirical_edges:
        connected_emp.add(e['source'])
        connected_emp.add(e['target'])

    domains = sorted(set(n['domain'] for n in nodes.values()))
    n_domains = len(domains)
    domain_nodes = defaultdict(list)
    for nid, info in nodes.items():
        domain_nodes[info['domain']].append(nid)

    total_nodes = sum(len(v) for v in domain_nodes.values())
    gap_angle = 2 * math.pi * 0.015
    usable_angle = 2 * math.pi - gap_angle * n_domains

    positions = {}
    domain_center_angles = {}
    current_angle = 0.0
    r_ring = 12.0

    for dom in domains:
        dom_nids = sorted(domain_nodes[dom])
        n_dom = len(dom_nids)
        dom_span = max(usable_angle * (n_dom / total_nodes), 0.06)
        conn = [n for n in dom_nids if n in connected_emp]
        unconn = [n for n in dom_nids if n not in connected_emp]
        ordered = conn + unconn
        domain_center_angles[dom] = current_angle + dom_span / 2
        for j, nid in enumerate(ordered):
            angle = current_angle + dom_span / 2 if n_dom == 1 else \
                    current_angle + dom_span * j / (n_dom - 1)
            r = r_ring - 0.4 if nid in connected_emp else r_ring + 0.4
            r += 0.2 * ((j % 3) - 1)
            positions[nid] = (r * math.cos(angle), r * math.sin(angle))
        current_angle += dom_span + gap_angle

    return positions, connected_emp, domain_center_angles


def draw_base(ax, nodes, positions, connected_emp, domain_center_angles, domain_color):
    for dom, ca in domain_center_angles.items():
        cx, cy = 12.0 * math.cos(ca), 12.0 * math.sin(ca)
        ax.add_patch(plt.Circle((cx, cy), 1.8, color=domain_color[dom],
                                alpha=0.06, linewidth=0))

    for nid, info in nodes.items():
        if nid not in positions:
            continue
        x, y = positions[nid]
        is_conn = nid in connected_emp
        color = domain_color[info['domain']]
        ax.scatter(x, y, s=400 if is_conn else 120, c=color,
                   alpha=1.0 if is_conn else 0.35,
                   edgecolors='white' if is_conn else 'none',
                   linewidths=0.8, zorder=3)

        label = info['name'].replace('_', ' ')
        if len(label) > 30:
            label = label[:28] + '..'
        if is_conn:
            ax.annotate(label, (x, y), textcoords='offset points',
                        xytext=(8, 8), fontsize=38, alpha=0.85,
                        fontweight='bold' if info.get('is_raw') else 'normal')
        else:
            ax.annotate(label, (x, y), textcoords='offset points',
                        xytext=(6, 6), fontsize=26, color='#b0b0b0',
                        alpha=0.55)

    for dom, ca in domain_center_angles.items():
        lx, ly = 14.5 * math.cos(ca), 14.5 * math.sin(ca)
        ax.text(lx, ly, DOMAIN_FULL_NAMES.get(dom, dom), fontsize=55,
                fontweight='bold', color=domain_color[dom],
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=domain_color[dom], alpha=0.85, linewidth=2))
    ax.set_aspect('equal')
    ax.axis('off')


def draw_empirical_edges(ax, edges, positions):
    tier_colors = {'A': '#d32f2f', 'B': '#f57c00', 'C': '#fbc02d'}
    tier_widths = {'A': 6.0, 'B': 4.5, 'C': 3.0}
    for e in sorted(edges, key=lambda x: abs(x['gamma'])):
        src, tgt = e['source'], e['target']
        if src not in positions or tgt not in positions:
            continue
        x0, y0 = positions[src]
        x1, y1 = positions[tgt]
        color = tier_colors[e['tier']]
        width = tier_widths[e['tier']]
        alpha = min(0.3 + abs(e['gamma']) * 3, 0.85)
        if e['flag'] == 'tautological':
            ls = (0, (6, 4)); width *= 1.3
        elif e['flag'] == 'overlap':
            ls = (0, (10, 4, 3, 4)); width *= 1.1
        else:
            ls = 'solid'
        ax.plot([x0, x1], [y0, y1], color=color, linewidth=width,
                alpha=alpha, linestyle=ls, zorder=1)


def _node_to_full_id(node_key: str) -> str:
    """Convert 'DOM:short_name' → 'agg_short_name|DOM' or 'pNN|DOM' for flag lookup."""
    dom, name = node_key.split(':', 1)
    # Reverse the RAW_QUESTION_SUMMARIES to recover original pNN codes
    rev_raw = {v: k for k, v in RAW_QUESTION_SUMMARIES.items()}
    if name in rev_raw:
        return f'{rev_raw[name]}|{dom}'
    return f'agg_{name}|{dom}'


def _get_theory_edge_flag(src: str, tgt: str) -> str:
    """Check whether a theoretical edge is tautological / high-overlap."""
    pair = frozenset([_node_to_full_id(src), _node_to_full_id(tgt)])
    if pair in TAUTOLOGICAL_PAIRS:
        return 'tautological'
    if pair in HIGH_OVERLAP_PAIRS:
        return 'overlap'
    return 'substantive'


def draw_theoretical_edges(ax, theory_edges, positions, empirical_set):
    for e in theory_edges:
        src, tgt = e['source'], e['target']
        if src not in positions or tgt not in positions:
            continue
        x0, y0 = positions[src]
        x1, y1 = positions[tgt]

        pair = frozenset([src, tgt])
        confirmed = pair in empirical_set

        if confirmed:
            flag = _get_theory_edge_flag(src, tgt)
            if flag == 'tautological':
                color, width, alpha, ls = '#d32f2f', 6.0, 0.7, (0, (6, 4))
            elif flag == 'overlap':
                color, width, alpha, ls = '#f57c00', 6.0, 0.7, (0, (10, 4, 3, 4))
            else:
                color, width, alpha, ls = '#2e7d32', 6.0, 0.7, 'solid'
        else:
            color, width, alpha, ls = '#1565c0', 3.5, 0.25, (0, (8, 5))

        ax.plot([x0, x1], [y0, y1], color=color, linewidth=width,
                alpha=alpha, linestyle=ls, zorder=1)


def render(nodes, empirical_edges, theory_edges,
           positions, connected_emp, domain_center_angles):
    domains = sorted(set(n['domain'] for n in nodes.values()))
    palette = [
        '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
        '#42d4f4', '#f032e6', '#bcf60c', '#fabebe', '#008080',
        '#e6beff', '#9a6324', '#800000', '#aaffc3', '#808000',
        '#ffd8b1', '#000075', '#a9a9a9', '#ffe119', '#469990',
        '#dcbeff', '#1f77b4', '#ff7f0e', '#2ca02c',
    ]
    domain_color = {d: palette[i % len(palette)] for i, d in enumerate(domains)}

    fig, (ax_t, ax_e) = plt.subplots(1, 2, figsize=(260, 130))

    # Empirical pair set for confirmation checking
    empirical_set = set()
    for e in empirical_edges:
        empirical_set.add(frozenset([e['source'], e['target']]))

    # ── Left: Theory ──
    draw_base(ax_t, nodes, positions, connected_emp, domain_center_angles, domain_color)
    draw_theoretical_edges(ax_t, theory_edges, positions, empirical_set)

    n_resolvable = sum(1 for e in theory_edges
                       if e['source'] in positions and e['target'] in positions)
    n_confirmed = sum(1 for e in theory_edges
                      if e['source'] in positions and e['target'] in positions
                      and frozenset([e['source'], e['target']]) in empirical_set)
    n_unconfirmed = n_resolvable - n_confirmed

    ax_t.set_title(
        f'Theoretical Predictions (Per-Domain Literature Reviews)\n'
        f'{n_resolvable} cross-domain predicted edges  |  '
        f'{n_confirmed} empirically confirmed  |  {n_unconfirmed} not confirmed',
        fontsize=85, fontweight='bold', pad=30)

    # Count confirmed by flag type
    n_conf_taut = sum(1 for e in theory_edges
                      if e['source'] in positions and e['target'] in positions
                      and frozenset([e['source'], e['target']]) in empirical_set
                      and _get_theory_edge_flag(e['source'], e['target']) == 'tautological')
    n_conf_over = sum(1 for e in theory_edges
                      if e['source'] in positions and e['target'] in positions
                      and frozenset([e['source'], e['target']]) in empirical_set
                      and _get_theory_edge_flag(e['source'], e['target']) == 'overlap')
    n_conf_subst = n_confirmed - n_conf_taut - n_conf_over

    theory_legend = [
        plt.Line2D([0], [0], color='#2e7d32', linewidth=8.0, linestyle='solid',
                   label=f'Confirmed — substantive ({n_conf_subst})'),
        plt.Line2D([0], [0], color='#f57c00', linewidth=8.0, linestyle=(0, (10, 4, 3, 4)),
                   label=f'Confirmed — high overlap ({n_conf_over})'),
        plt.Line2D([0], [0], color='#d32f2f', linewidth=8.0, linestyle=(0, (6, 4)),
                   label=f'Confirmed — tautological ({n_conf_taut})'),
        plt.Line2D([0], [0], color='#1565c0', linewidth=5.0, linestyle=(0, (8, 5)),
                   label=f'Not confirmed ({n_unconfirmed})'),
    ]
    ax_t.legend(handles=theory_legend, loc='lower left', fontsize=70,
                framealpha=0.9, title='Theory Status', title_fontsize=80,
                bbox_to_anchor=(0.0, 0.0))

    # ── Right: Empirical ──
    draw_base(ax_e, nodes, positions, connected_emp, domain_center_angles, domain_color)
    draw_empirical_edges(ax_e, empirical_edges, positions)

    n_taut = sum(1 for e in empirical_edges if e['flag'] == 'tautological')
    n_over = sum(1 for e in empirical_edges if e['flag'] == 'overlap')
    n_subst = sum(1 for e in empirical_edges if e['flag'] == 'substantive')
    n_a = sum(1 for e in empirical_edges if e['tier'] == 'A')
    n_b = sum(1 for e in empirical_edges if e['tier'] == 'B')
    n_c = sum(1 for e in empirical_edges if e['tier'] == 'C')

    ax_e.set_title(
        f'Empirical Results (v3 DR Bridge)\n'
        f'{len(empirical_edges)} edges ({n_a}A + {n_b}B + {n_c}C)  |  '
        f'{n_subst} substantive, {n_over} overlap, {n_taut} tautological',
        fontsize=85, fontweight='bold', pad=30)

    tc = {'A': '#d32f2f', 'B': '#f57c00', 'C': '#fbc02d'}
    emp_legend = [
        mpatches.Patch(facecolor=tc['A'], alpha=0.7, label='Tier A: CI excludes 0'),
        mpatches.Patch(facecolor=tc['B'], alpha=0.7, label='Tier B: 0 within 2.5%'),
        mpatches.Patch(facecolor=tc['C'], alpha=0.7, label='Tier C: 0 within 5%'),
        plt.Line2D([0], [0], color='gray', linewidth=6.0, linestyle='solid',
                   label='Substantive'),
        plt.Line2D([0], [0], color='gray', linewidth=6.0, linestyle=(0, (6, 4)),
                   label='Tautological'),
        plt.Line2D([0], [0], color='gray', linewidth=6.0, linestyle=(0, (10, 4, 3, 4)),
                   label='High overlap'),
    ]
    ax_e.legend(handles=emp_legend, loc='lower left', fontsize=70,
                framealpha=0.9, title='Edge Classification', title_fontsize=80,
                bbox_to_anchor=(0.0, 0.0))

    fig.suptitle(
        'SES-Mediated Construct Network: Theory vs Empirical Evidence',
        fontsize=120, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(str(OUTPUT_PNG), dpi=28, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f'Saved -> {OUTPUT_PNG}')


def main():
    print('Loading empirical edges...', flush=True)
    emp = load_empirical_edges()
    print(f'  {len(emp)} significant edges')

    print('Loading theoretical edges from causal_direction_map...', flush=True)
    theory = load_theoretical_edges()
    print(f'  {len(theory)} cross-domain theoretical pairs')

    print('Collecting all constructs...', flush=True)
    nodes = collect_all_nodes(emp)
    print(f'  {len(nodes)} nodes across {len(set(n["domain"] for n in nodes.values()))} domains')

    print('Computing shared layout...', flush=True)
    positions, connected_emp, dca = layout_nodes(nodes, emp)

    # Check theoretical edge resolution
    n_ok = sum(1 for e in theory if e['source'] in positions and e['target'] in positions)
    n_miss = len(theory) - n_ok
    print(f'  {n_ok}/{len(theory)} theoretical edges resolvable ({n_miss} have nodes not in sweep)')

    print('Rendering comparison...', flush=True)
    render(nodes, emp, theory, positions, connected_emp, dca)


if __name__ == '__main__':
    main()
