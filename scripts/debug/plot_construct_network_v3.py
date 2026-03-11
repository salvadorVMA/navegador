"""Construct network v3 — with semantic similarity flags.

Reads dr_sweep_results_v3.json, classifies edges into significance tiers,
marks tautological/high-overlap edges with dashed lines.

Outputs:
  data/results/construct_network_v3.png
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
OUTPUT_PNG = ROOT / 'data' / 'results' / 'construct_network_v3.png'

# ── Semantic similarity flags ──
# Tautological pairs: same concept across domains
TAUTOLOGICAL_PAIRS = {
    frozenset(['agg_digital_and_cultural_capital|EDU', 'agg_digital_access_and_equipment|SOC']),
    frozenset(['agg_science_technology_engagement|CIE', 'agg_digital_literacy_and_internet_engagement|SOC']),
    frozenset(['p14|HAB', 'agg_material_living_standards|POB']),
}

# High-overlap pairs: substantial conceptual overlap
HIGH_OVERLAP_PAIRS = {
    frozenset(['agg_science_technology_engagement|CIE', 'agg_digital_civic_and_political_participation|SOC']),
    frozenset(['agg_education_quality_and_opportunity|NIN', 'agg_material_living_standards|POB']),
    frozenset(['agg_institutional_trust_and_representativeness|FED', 'agg_digital_civic_and_political_participation|SOC']),
    frozenset(['agg_cultural_openness|GLO', 'agg_media_consumption_and_news_habits|SOC']),
    frozenset(['agg_civil_liberties_and_protest_rights|DER', 'agg_cosmopolitan_identity|GLO']),
    frozenset(['agg_cultural_socialization_in_childhood|DEP', 'agg_cultural_openness|GLO']),
}

DOMAIN_FULL_NAMES = {
    'CIE': 'Ciencia y\nTecnologia',
    'COR': 'Corrupcion y\nLegalidad',
    'CUL': 'Cultura\nPolitica',
    'DEP': 'Cultura, Lectura\ny Deporte',
    'DER': 'Derechos\nHumanos',
    'ECO': 'Economia\ny Empleo',
    'EDU': 'Educacion',
    'ENV': 'Envejecimiento',
    'FAM': 'Familia',
    'FED': 'Federalismo',
    'GEN': 'Genero',
    'GLO': 'Globalizacion',
    'HAB': 'Habitabilidad',
    'IDE': 'Identidad\ny Valores',
    'IND': 'Indigenas',
    'JUS': 'Justicia',
    'MED': 'Medio\nAmbiente',
    'MIG': 'Migracion',
    'NIN': 'Ninos y\nJovenes',
    'POB': 'Pobreza',
    'REL': 'Religion',
    'SAL': 'Salud',
    'SEG': 'Seguridad\nPublica',
    'SOC': 'Sociedad de la\nInformacion',
}


# Raw question summaries — replace cryptic pNN names with descriptive labels
RAW_QUESTION_SUMMARIES = {
    'p14': 'p_housing_ownership',
    'p18_1a_1': 'p_indigenous_group_knowledge',
    'p18_1': 'p_purpose_of_reading',
    'p19': 'p_job_value_preference',
    'p1_2': 'p_father_education_level',
    'p23_1': 'p_healthcare_financial_burden',
    'p24': 'p_healthcare_access_choice',
    'p26_1': 'p_child_corporal_punishment',
    'p34': 'p_alcohol_consumption_freq',
    'p52': 'p_national_emotion',
}


def _parse_var(var_id: str):
    """'agg_foo|DOM' -> ('DOM', 'foo') or ('DOM', 'p14')."""
    name, domain = var_id.split('|')
    short = name.replace('agg_', '')
    # Replace raw question codes with descriptive summaries
    if short in RAW_QUESTION_SUMMARIES:
        short = RAW_QUESTION_SUMMARIES[short]
    return domain, short


def get_edge_flag(src_full: str, tgt_full: str) -> str:
    """Return 'tautological', 'overlap', or 'substantive'."""
    pair = frozenset([src_full, tgt_full])
    if pair in TAUTOLOGICAL_PAIRS:
        return 'tautological'
    if pair in HIGH_OVERLAP_PAIRS:
        return 'overlap'
    return 'substantive'


def load_edges():
    """Load significant edges from v3 sweep results."""
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
            dist_from_edge = min(abs(ci_lo), abs(ci_hi))
            frac = dist_from_edge / ci_w
            if frac <= 0.025:
                tier = 'B'
            elif frac <= 0.05:
                tier = 'C'
            else:
                continue

        parts = pair_key.split('::')
        src_full, tgt_full = parts[0], parts[1]
        src_dom, src_name = _parse_var(src_full)
        tgt_dom, tgt_name = _parse_var(tgt_full)
        flag = get_edge_flag(src_full, tgt_full)

        edges.append({
            'source': f'{src_dom}:{src_name}',
            'target': f'{tgt_dom}:{tgt_name}',
            'src_full': src_full,
            'tgt_full': tgt_full,
            'src_dom': src_dom,
            'tgt_dom': tgt_dom,
            'gamma': gamma,
            'ci': [ci_lo, ci_hi],
            'nmi': est.get('dr_nmi', 0),
            'tier': tier,
            'flag': flag,
        })

    return edges


def collect_all_nodes(edges):
    """Get all constructs across 24 domains."""
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

    for e in edges:
        for nid_key in [e['source'], e['target']]:
            if nid_key not in nodes:
                dom, name = nid_key.split(':', 1)
                nodes[nid_key] = {'domain': dom, 'name': name, 'is_raw': not name.startswith('agg_')}

    return nodes


def layout_nodes(nodes, edges):
    """Single-ring domain-clustered layout. All constructs in one circle,
    grouped by domain, with connected nodes slightly inward."""
    connected = set()
    for e in edges:
        connected.add(e['source'])
        connected.add(e['target'])

    domains = sorted(set(n['domain'] for n in nodes.values()))
    n_domains = len(domains)

    domain_nodes = defaultdict(list)
    for nid, info in nodes.items():
        domain_nodes[info['domain']].append(nid)

    # Allocate angular space proportional to node count, with minimum per domain
    total_nodes = sum(len(v) for v in domain_nodes.values())
    # Wider gaps between domains to prevent label overlap
    gap_angle = 2 * math.pi * 0.015  # 1.5% of circle per gap
    usable_angle = 2 * math.pi - gap_angle * n_domains

    positions = {}
    domain_center_angles = {}
    current_angle = 0.0
    r_ring = 12.0  # larger ring for more spacing

    for dom in domains:
        dom_nids = sorted(domain_nodes[dom])
        n_dom = len(dom_nids)
        # Minimum angular span to prevent tiny clusters
        dom_span = max(usable_angle * (n_dom / total_nodes), 0.06)

        conn_in_dom = [n for n in dom_nids if n in connected]
        unconn_in_dom = [n for n in dom_nids if n not in connected]
        ordered = conn_in_dom + unconn_in_dom

        domain_center_angles[dom] = current_angle + dom_span / 2

        for j, nid in enumerate(ordered):
            if n_dom == 1:
                angle = current_angle + dom_span / 2
            else:
                angle = current_angle + dom_span * j / (n_dom - 1)
            # Connected slightly inward, unconnected slightly outward
            r = r_ring - 0.4 if nid in connected else r_ring + 0.4
            r += 0.2 * ((j % 3) - 1)
            positions[nid] = (r * math.cos(angle), r * math.sin(angle))

        current_angle += dom_span + gap_angle

    return positions, connected, domain_center_angles


def render(nodes, edges, positions, connected, domain_center_angles):
    """Render the network with matplotlib."""
    domains = sorted(set(n['domain'] for n in nodes.values()))
    color_palette = [
        '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4',
        '#42d4f4', '#f032e6', '#bcf60c', '#fabebe', '#008080',
        '#e6beff', '#9a6324', '#800000', '#aaffc3', '#808000',
        '#ffd8b1', '#000075', '#a9a9a9', '#ffe119', '#469990',
        '#dcbeff', '#1f77b4', '#ff7f0e', '#2ca02c',
    ]
    domain_color = {d: color_palette[i % len(color_palette)] for i, d in enumerate(domains)}

    fig, ax = plt.subplots(1, 1, figsize=(160, 140))
    ax.set_aspect('equal')
    ax.axis('off')

    # Light background circle per domain cluster
    for dom, center_angle in domain_center_angles.items():
        cx = 12.0 * math.cos(center_angle)
        cy = 12.0 * math.sin(center_angle)
        circle = plt.Circle((cx, cy), 1.8, color=domain_color[dom],
                            alpha=0.06, linewidth=0)
        ax.add_patch(circle)

    # ── Edges ──
    tier_colors = {'A': '#d32f2f', 'B': '#f57c00', 'C': '#fbc02d'}
    tier_widths = {'A': 8.0, 'B': 6.0, 'C': 4.0}

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
            linestyle = (0, (6, 4))
            width *= 1.3
        elif e['flag'] == 'overlap':
            linestyle = (0, (10, 4, 3, 4))
            width *= 1.1
        else:
            linestyle = 'solid'

        ax.plot([x0, x1], [y0, y1], color=color, linewidth=width,
                alpha=alpha, linestyle=linestyle, zorder=1)

    # ── Nodes ──
    for nid, info in nodes.items():
        if nid not in positions:
            continue
        x, y = positions[nid]
        is_conn = nid in connected
        color = domain_color[info['domain']]
        size = 600 if is_conn else 200
        node_alpha = 1.0 if is_conn else 0.35
        edgecolor = 'white' if is_conn else 'none'

        ax.scatter(x, y, s=size, c=color, alpha=node_alpha, edgecolors=edgecolor,
                   linewidths=1.0, zorder=3)

        # Label all nodes — connected in dark text, unconnected in light gray
        label = info['name'].replace('_', ' ')
        if len(label) > 30:
            label = label[:28] + '..'
        if is_conn:
            ax.annotate(label, (x, y), textcoords='offset points',
                        xytext=(10, 10), fontsize=65, alpha=0.85,
                        fontweight='bold' if info.get('is_raw') else 'normal')
        else:
            ax.annotate(label, (x, y), textcoords='offset points',
                        xytext=(8, 8), fontsize=45, color='#b0b0b0',
                        alpha=0.55, fontweight='normal')

    # ── Domain labels ── placed outside the ring, no overlap
    for dom, center_angle in domain_center_angles.items():
        lx = 14.5 * math.cos(center_angle)
        ly = 14.5 * math.sin(center_angle)
        full_name = DOMAIN_FULL_NAMES.get(dom, dom)
        ax.text(lx, ly, full_name, fontsize=90, fontweight='bold',
                color=domain_color[dom], ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=domain_color[dom], alpha=0.85, linewidth=2))

    # ── Legend ──
    legend_elements = [
        mpatches.Patch(facecolor=tier_colors['A'], alpha=0.7, label='Tier A: CI excludes 0'),
        mpatches.Patch(facecolor=tier_colors['B'], alpha=0.7, label='Tier B: 0 within 2.5% of CI edge'),
        mpatches.Patch(facecolor=tier_colors['C'], alpha=0.7, label='Tier C: 0 within 5% of CI edge'),
        plt.Line2D([0], [0], color='gray', linewidth=10.0, linestyle='solid',
                   label='Substantive edge'),
        plt.Line2D([0], [0], color='gray', linewidth=10.0, linestyle=(0, (6, 4)),
                   label='Tautological (same concept)'),
        plt.Line2D([0], [0], color='gray', linewidth=10.0, linestyle=(0, (10, 4, 3, 4)),
                   label='High overlap (caution)'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', fontsize=90,
              framealpha=0.9, title='Edge Classification', title_fontsize=100,
              bbox_to_anchor=(-0.02, -0.02))

    # ── Title ──
    n_taut = sum(1 for e in edges if e['flag'] == 'tautological')
    n_over = sum(1 for e in edges if e['flag'] == 'overlap')
    n_subst = sum(1 for e in edges if e['flag'] == 'substantive')
    n_a = sum(1 for e in edges if e['tier'] == 'A')
    n_b = sum(1 for e in edges if e['tier'] == 'B')
    n_c = sum(1 for e in edges if e['tier'] == 'C')

    ax.set_title(
        f'SES-Mediated Construct Network (v3 DR Bridge)\n'
        f'{len(nodes)} constructs  |  {len(edges)} edges '
        f'({n_a} Tier A + {n_b} Tier B + {n_c} Tier C)  |  '
        f'{n_subst} substantive, {n_over} high-overlap, {n_taut} tautological',
        fontsize=130, fontweight='bold', pad=40
    )

    plt.tight_layout()
    fig.savefig(str(OUTPUT_PNG), dpi=36, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f'Saved -> {OUTPUT_PNG}')


def main():
    print('Loading edges from v3 sweep...', flush=True)
    edges = load_edges()
    print(f'  {len(edges)} significant edges '
          f'({sum(1 for e in edges if e["tier"]=="A")} A, '
          f'{sum(1 for e in edges if e["tier"]=="B")} B, '
          f'{sum(1 for e in edges if e["tier"]=="C")} C)')
    print(f'  Flags: {sum(1 for e in edges if e["flag"]=="tautological")} tautological, '
          f'{sum(1 for e in edges if e["flag"]=="overlap")} overlap, '
          f'{sum(1 for e in edges if e["flag"]=="substantive")} substantive')

    print('Collecting all constructs...', flush=True)
    nodes = collect_all_nodes(edges)
    print(f'  {len(nodes)} nodes across {len(set(n["domain"] for n in nodes.values()))} domains')

    print('Computing layout...', flush=True)
    positions, connected, domain_center_angles = layout_nodes(nodes, edges)
    print(f'  {len(connected)} connected, {len(nodes) - len(connected)} unconnected')

    print('Rendering...', flush=True)
    render(nodes, edges, positions, connected, domain_center_angles)


if __name__ == '__main__':
    main()
