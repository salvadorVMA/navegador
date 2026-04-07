#!/usr/bin/env python3
"""
WVS Ontology Demo — Build, query, and visualize construct ontologies
for Mexico and comparison countries.

Demonstrates all OntologyQuery capabilities on WVS data:
  1. Build per-country KG ontologies from the geographic sweep
  2. Run traversal queries (profile, neighbors, paths, camps)
  3. Visualize the construct network with signed edges and SES coloring
  4. Compare network structure across countries

Usage:
    python scripts/debug/demo_wvs_ontology.py
    python scripts/debug/demo_wvs_ontology.py --countries MEX USA JPN DEU BRA
"""
import argparse
import json
import math
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data" / "results"
NAVEGADOR_DATA = Path("/workspaces/navegador_data") / "data" / "results"

ALL_DIMS = ("rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad")

WVS_DOMAIN_LABELS = {
    "WVS_A": "Values",
    "WVS_B": "Environment",
    "WVS_C": "Work",
    "WVS_D": "Family",
    "WVS_E": "Politics",
    "WVS_F": "Religion",
    "WVS_G": "Identity",
    "WVS_H": "Security",
    "WVS_I": "Science",
}

DOMAIN_COLORS = {
    "WVS_A": "#e15759",  # red
    "WVS_B": "#59a14f",  # green
    "WVS_C": "#f28e2b",  # orange
    "WVS_D": "#b07aa1",  # purple
    "WVS_E": "#4e79a7",  # blue
    "WVS_F": "#9c755f",  # brown
    "WVS_G": "#ff9da7",  # pink
    "WVS_H": "#76b7b2",  # teal-grey
    "WVS_I": "#edc948",  # gold
}


def _fp_vec(fp):
    return np.array([fp.get(d, 0.0) for d in ALL_DIMS])


def _cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ─── Build per-country KG from geographic sweep ──────────────────────

def build_country_kg(country_code, geo_estimates, manifest, wvs_fp_flat):
    """Build a KG dict for a single country from the geographic sweep."""
    col_to_key = {c["column"]: c["key"] for c in manifest}

    # Remap fingerprints to manifest keys
    constructs_fp = {}
    for c in manifest:
        fp = wvs_fp_flat.get(c["column"], {})
        constructs_fp[c["key"]] = fp

    prefix = f"WVS_W7_{country_code}"
    bridges = []

    for sweep_key, v in geo_estimates.items():
        ctx = v.get("context", sweep_key.split("::")[0])
        if ctx != prefix:
            continue
        if not v.get("excl_zero"):
            continue

        parts = sweep_key.split("::")
        if len(parts) != 3:
            continue
        col_a = parts[1].rsplit("|", 1)[0]
        col_b = parts[2].rsplit("|", 1)[0]
        key_a = col_to_key.get(col_a)
        key_b = col_to_key.get(col_b)
        if not key_a or not key_b:
            continue

        fp_a = constructs_fp.get(key_a, {})
        fp_b = constructs_fp.get(key_b, {})
        vec_a, vec_b = _fp_vec(fp_a), _fp_vec(fp_b)
        fp_dot = float(np.dot(vec_a, vec_b))
        fp_cos = _cosine(vec_a, vec_b)

        bridges.append({
            "from": key_a, "to": key_b,
            "gamma": round(v["dr_gamma"], 6),
            "ci_lo": round(v["dr_ci_lo"], 6),
            "ci_hi": round(v["dr_ci_hi"], 6),
            "ci_width": round(v["ci_width"], 6),
            "excl_zero": True,
            "nmi": round(v.get("dr_nmi", 0), 6),
            "fingerprint_dot": round(fp_dot, 6),
            "fingerprint_cos": round(fp_cos, 6),
            "dot_sign_consistent": bool(
                abs(fp_dot) < 1e-8 or abs(v["dr_gamma"]) < 1e-8
                or np.sign(fp_dot) == np.sign(v["dr_gamma"])
            ),
        })

    constructs = []
    for c in manifest:
        key = c["key"]
        fp = constructs_fp.get(key, {})
        constructs.append({
            "id": key,
            "label": key.split("|")[1].replace("_", " ").title(),
            "domain": key.split("|")[0],
            "column": c["column"],
            "type": c.get("type"),
            "alpha": c.get("alpha"),
            "rho_escol": fp.get("rho_escol", 0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0),
            "rho_sexo": fp.get("rho_sexo", 0),
            "rho_edad": fp.get("rho_edad", 0),
            "ses_magnitude": fp.get("ses_magnitude", 0),
            "dominant_dim": fp.get("dominant_dim", "escol"),
            "ses_sign": 1 if fp.get("rho_escol", 0) >= 0 else -1,
            "n_surveys": 1,
        })

    domains = [{"id": d, "label": WVS_DOMAIN_LABELS.get(d, d)}
               for d in sorted({c["key"].split("|")[0] for c in manifest})]

    return {
        "version": "v1_wvs",
        "dataset": f"wvs_w7_{country_code.lower()}",
        "domains": domains,
        "constructs": constructs,
        "relationships": [],
        "bridges": bridges,
    }


def build_country_fp(manifest, wvs_fp_flat):
    """Build OntologyQuery-compatible fingerprint dict."""
    constructs_fp = {}
    for c in manifest:
        fp = wvs_fp_flat.get(c["column"], {})
        constructs_fp[c["key"]] = {
            "rho_escol": fp.get("rho_escol", 0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0),
            "rho_sexo": fp.get("rho_sexo", 0),
            "rho_edad": fp.get("rho_edad", 0),
            "ses_magnitude": fp.get("ses_magnitude", 0),
            "dominant_dim": fp.get("dominant_dim", "escol"),
        }
    return {
        "metadata": {"source": "WVS_W7", "ses_vars": list(ALL_DIMS)},
        "constructs": constructs_fp, "items": {}, "domains": {},
    }


# ─── Circle layout (canonical, shared across countries) ───────────────

def _canonical_layout(manifest):
    """Build a fixed circle layout from the manifest so every country plot
    places constructs at the same position.  Returns (pos, domains, domain_angle_map)."""
    constructs = sorted(c["key"] for c in manifest)
    domains = sorted({c.split("|")[0] for c in constructs})
    n_dom = len(domains)
    step = 2 * np.pi / n_dom
    domain_angle_map = {d: np.pi / 2 - i * step for i, d in enumerate(domains)}

    by_domain = defaultdict(list)
    for c in constructs:
        by_domain[c.split("|")[0]].append(c)

    sector = 2 * np.pi / n_dom
    spread_frac = 0.70
    half = sector * spread_frac / 2
    node_radius = 3.4

    pos = {}
    for dom, members in by_domain.items():
        center = domain_angle_map[dom]
        n = len(members)
        angles = np.linspace(center - half, center + half, n) if n > 1 else [center]
        for angle, c in zip(angles, sorted(members)):
            pos[c] = (node_radius * np.cos(angle), node_radius * np.sin(angle))

    return pos, domains, domain_angle_map


def _draw_circle_network(ax, oq, pos, domains, domain_angle_map,
                         country_code, compact=False):
    """Draw a domain-circle network on the given axes."""
    n_dom = len(domains)
    lim = 5.2 if compact else 6.2
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    # Sector backgrounds
    sector_deg = 360 / n_dom
    half_deg = sector_deg / 2
    inner_r = 2.7
    outer_r = 4.1
    for dom in domains:
        angle_deg = np.degrees(domain_angle_map[dom])
        color = DOMAIN_COLORS.get(dom, "#cccccc")
        from matplotlib.patches import Wedge
        w = Wedge((0, 0), outer_r, angle_deg - half_deg, angle_deg + half_deg,
                  width=outer_r - inner_r, facecolor=color, alpha=0.12,
                  edgecolor=color, linewidth=0.4)
        ax.add_patch(w)

    # Collect edges
    edges = []
    seen = set()
    for src, elist in oq._bridges.items():
        for e in elist:
            pair = tuple(sorted([src, e["neighbor"]]))
            if pair in seen:
                continue
            seen.add(pair)
            if src in pos and e["neighbor"] in pos:
                edges.append((src, e["neighbor"], e["gamma"]))

    # Degree
    degree = defaultdict(int)
    for a, b, g in edges:
        degree[a] += 1
        degree[b] += 1

    sig_nodes = set(degree.keys())

    # Gamma range for scaling
    gammas = [abs(g) for _, _, g in edges]
    g_max = max(gammas) if gammas else 1.0
    g_min = min(gammas) if gammas else 0.0
    g_range = g_max - g_min if g_max > g_min else 1.0

    # Draw edges (weakest first)
    for a, b, g in sorted(edges, key=lambda x: abs(x[2])):
        color = "#d62728" if g > 0 else "#1f77b4"
        norm_g = (abs(g) - g_min) / g_range
        alpha = 0.10 + 0.50 * norm_g
        lw = (0.2 + 1.5 * norm_g) if compact else (0.4 + 2.6 * norm_g)
        rad = 0.20
        ax.annotate("", xy=pos[b], xytext=pos[a],
                     arrowprops=dict(arrowstyle="-", color=color,
                                     alpha=alpha, lw=lw,
                                     connectionstyle=f"arc3,rad={rad}"))

    # Draw nodes — all constructs at fixed positions
    import matplotlib.patheffects as pe
    for c in pos:
        x, y = pos[c]
        dom = c.split("|")[0]
        is_sig = c in sig_nodes
        deg = degree.get(c, 0)
        if is_sig:
            sz = (20 + min(deg * 6, 80)) if compact else (40 + min(deg * 14, 200))
            col = DOMAIN_COLORS.get(dom, "#cccccc")
            al = 0.90
        else:
            sz = 6 if compact else 12
            col = "#cccccc"
            al = 0.40
        ax.scatter(x, y, s=sz, c=col, alpha=al, edgecolors="white",
                   linewidths=0.3 if compact else 0.7, zorder=5 if is_sig else 3)

    # Labels
    if not compact:
        deg_thresh = max(5, np.percentile(list(degree.values()) or [0], 70))
        for c in pos:
            if c in sig_nodes and degree.get(c, 0) >= deg_thresh:
                x, y = pos[c]
                short = c.split("|")[1].replace("_", " ")[:16]
                ax.text(x, y, short, ha="center", va="center",
                        fontsize=4.5, fontweight="bold", zorder=6,
                        color="white",
                        path_effects=[pe.withStroke(linewidth=1.2, foreground="black")])

    # Domain labels (outer ring)
    label_r = 4.7 if not compact else 4.3
    for dom in domains:
        angle = domain_angle_map[dom]
        lx = label_r * np.cos(angle)
        ly = label_r * np.sin(angle)
        label = WVS_DOMAIN_LABELS.get(dom, dom)
        col = DOMAIN_COLORS.get(dom, "#444")
        ha = "center"
        if lx > 0.3: ha = "left"
        elif lx < -0.3: ha = "right"
        fs = 6.5 if compact else 8.5
        ax.text(lx, ly, f"{dom}\n{label}", ha=ha, va="center",
                fontsize=fs, fontweight="bold", color=col, zorder=6,
                path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

    # Stats
    n_pos = sum(1 for _, _, g in edges if g > 0)
    n_neg = sum(1 for _, _, g in edges if g <= 0)
    n_con = len(sig_nodes)
    density = len(edges) / max(1, n_con * (n_con - 1) / 2) if n_con > 1 else 0
    stats = f"{len(edges)} edges ({n_pos}+ / {n_neg}−)  |  {n_con} constructs  |  {density:.0%} density"
    fs = 7 if compact else 9
    ax.text(0, -lim + 0.25, stats, ha="center", va="bottom",
            fontsize=fs, color="#555555",
            path_effects=[pe.withStroke(linewidth=1.2, foreground="white")])


def visualize_country_network(oq, country_code, output_path, manifest, title=None):
    """Full-size circle plot for one country."""
    pos, domains, dam = _canonical_layout(manifest)
    fig, ax = plt.subplots(figsize=(20, 20))
    _draw_circle_network(ax, oq, pos, domains, dam, country_code, compact=False)

    # Legend
    legend = [
        mpatches.Patch(facecolor="#d62728", alpha=0.7, label="γ > 0  (co-elevated by SES)"),
        mpatches.Patch(facecolor="#1f77b4", alpha=0.7, label="γ < 0  (counter-varies)"),
    ]
    ax.legend(handles=legend, loc="lower left", bbox_to_anchor=(0.01, 0.01),
              fontsize=9, framealpha=0.85)

    t = title or f"WVS Construct Network — {country_code} (Wave 7)"
    ax.set_title(t, fontsize=16, fontweight="bold", pad=16, y=0.98)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"  Saved: {output_path}")


def visualize_comparison(country_oqs, output_path, manifest):
    """Small multiples: one circle network per country, identical layout."""
    pos, domains, dam = _canonical_layout(manifest)
    n = len(country_oqs)
    cols = min(3, n)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(8 * cols, 8 * rows))
    if n == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for idx, (code, oq) in enumerate(country_oqs.items()):
        ax = axes[idx]
        _draw_circle_network(ax, oq, pos, domains, dam, code, compact=True)
        ax.set_title(code, fontsize=14, fontweight="bold", pad=8)

    for idx in range(n, len(axes)):
        axes[idx].axis("off")

    fig.suptitle("WVS Construct Networks — Cross-Country Comparison (Wave 7)\n"
                 "Same layout: constructs at identical positions across all panels",
                 fontsize=15, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"  Saved: {output_path}")


# ─── Query Demo ───────────────────────────────────────────────────────

def demo_queries(oq, country_code):
    """Run and print example queries on a country ontology."""
    connected = [k for k in oq._constructs if k in oq._bridges]
    if not connected:
        print(f"  {country_code}: No connected constructs")
        return

    print(f"\n{'─' * 60}")
    print(f"  {country_code} — {len(connected)} connected constructs, "
          f"{sum(len(v) for v in oq._bridges.values()) // 2} edges")
    print(f"{'─' * 60}")

    # 1. Profile
    key = connected[0]
    p = oq.get_profile(key)
    print(f"\n  1. PROFILE: {key}")
    print(f"     Dominant SES dim: {p.get('dominant_dim')}")
    print(f"     SES magnitude: {p.get('ses_magnitude', 0):.4f}")
    print(f"     Narrative: {p.get('narrative', '')[:120]}")

    # 2. Neighbors
    nb = oq.get_neighbors(key, top_n=5)
    print(f"\n  2. NEIGHBORS of {key.split('|')[1][:30]}:")
    for n in nb[:5]:
        name = n["neighbor"].split("|")[1].replace("_", " ")[:35]
        print(f"     γ={n['gamma']:+.4f}  {name}")

    # 3. Path between two distant constructs
    if len(connected) >= 2:
        # Find two constructs in different domains
        domains = {}
        for k in connected:
            d = k.split("|")[0]
            domains.setdefault(d, []).append(k)
        dom_keys = list(domains.keys())
        a = domains[dom_keys[0]][0]
        b = domains[dom_keys[-1]][0] if len(dom_keys) > 1 else connected[-1]

        path = oq.find_path(a, b)
        if not path.get("error"):
            print(f"\n  3. PATH: {a.split('|')[1][:25]} → {b.split('|')[1][:25]}")
            for i, step in enumerate(path["path"]):
                print(f"     [{i}] {step}")
            print(f"     Signal chain: {path['signal_chain']:.6f}")
            print(f"     Expected sign: {path.get('expected_sign_note', 'unknown')}")

    # 4. Camp membership
    camp = oq.get_camp(key)
    print(f"\n  4. CAMP: {key.split('|')[1][:30]}")
    print(f"     Camp: {camp.get('camp_name')} (confidence: {camp.get('confidence', 0):.3f})")

    # 5. Network stats
    camps = Counter()
    for k in connected:
        c = oq.get_camp(k)
        if c.get("camp_id"):
            camps[c["camp_name"]] += 1
    print(f"\n  5. CAMP DISTRIBUTION: {dict(camps)}")


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WVS Ontology Demo")
    parser.add_argument("--countries", nargs="+", default=["MEX", "USA", "JPN", "DEU", "BRA", "NGA"],
                        help="Country codes to compare")
    args = parser.parse_args()

    print("WVS Ontology Demo")
    print("=" * 60)

    # Load shared data
    manifest = json.load(open(DATA / "wvs_construct_manifest.json"))
    wvs_fp = json.load(open(DATA / "wvs_ses_fingerprints.json"))["fingerprints"]

    print("\nLoading geographic sweep (29 MB)...")
    t0 = time.time()
    geo = json.load(open(NAVEGADOR_DATA / "wvs_geographic_sweep_w7.json"))
    print(f"  Loaded in {time.time() - t0:.1f}s ({len(geo['estimates'])} estimates)")

    # Build OntologyQuery per country
    from opinion_ontology import OntologyQuery

    fp_v2 = build_country_fp(manifest, wvs_fp)
    fp_path = DATA / "_tmp_wvs_fp_v2.json"
    with open(fp_path, "w") as f:
        json.dump(fp_v2, f)

    country_oqs = {}
    for code in args.countries:
        kg = build_country_kg(code, geo["estimates"], manifest, wvs_fp)
        n_bridges = len(kg["bridges"])
        if n_bridges == 0:
            print(f"  {code}: 0 bridges, skipping")
            continue

        kg_path = DATA / f"_tmp_wvs_kg_{code.lower()}.json"
        with open(kg_path, "w") as f:
            json.dump(kg, f)

        oq = OntologyQuery(fp_path=fp_path, kg_path=kg_path, dataset=f"wvs_{code}")
        country_oqs[code] = oq
        print(f"  {code}: {n_bridges} bridges, "
              f"{len([k for k in oq._constructs if k in oq._bridges])} connected constructs")

    # ─── Demo Queries ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("QUERY DEMONSTRATIONS")
    print("=" * 60)

    for code, oq in country_oqs.items():
        demo_queries(oq, code)

    # ─── Visualizations ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("VISUALIZATIONS")
    print("=" * 60)

    # Detailed Mexico network
    if "MEX" in country_oqs:
        visualize_country_network(
            country_oqs["MEX"], "MEX",
            DATA / "wvs_ontology_network_mex.png",
            manifest=manifest,
        )

    # Comparison small multiples
    visualize_comparison(
        country_oqs,
        DATA / "wvs_ontology_comparison.png",
        manifest=manifest,
    )

    # ─── Cross-Country Summary ────────────────────────────────
    print("\n" + "=" * 60)
    print("CROSS-COUNTRY NETWORK COMPARISON")
    print("=" * 60)
    print(f"\n{'Country':<8} {'Edges':>6} {'Density':>8} {'Diameter':>9} "
          f"{'Cosmo':>6} {'Trad':>5} {'Balance':>8}")
    print("─" * 60)

    for code, oq in country_oqs.items():
        connected = [k for k in oq._constructs if k in oq._bridges]
        n_edges = sum(len(v) for v in oq._bridges.values()) // 2
        n = len(connected)
        density = n_edges / max(1, n * (n - 1) / 2)

        # Quick BFS diameter
        adj = defaultdict(set)
        for src, edges in oq._bridges.items():
            for e in edges:
                adj[src].add(e["neighbor"])
        diameter = 0
        for start in connected[:10]:
            dist = {start: 0}
            queue = [start]
            i = 0
            while i < len(queue):
                node = queue[i]; i += 1
                for nb in adj[node]:
                    if nb not in dist:
                        dist[nb] = dist[node] + 1
                        queue.append(nb)
            if dist:
                diameter = max(diameter, max(dist.values()))

        camps = Counter()
        for k in connected:
            c = oq.get_camp(k)
            if c.get("camp_name"):
                camps[c["camp_name"]] += 1

        # Balance
        n_bal = n_frust = 0
        seen_edges = {}
        for src, edges in oq._bridges.items():
            for e in edges:
                pair = tuple(sorted([src, e["neighbor"]]))
                seen_edges[pair] = e["gamma"]
        edge_list = list(seen_edges.items())
        node_set = set()
        for (a, b), _ in edge_list:
            node_set.add(a); node_set.add(b)
        for (a, b), g1 in edge_list:
            for (c, d), g2 in edge_list:
                if a == c and b != d:
                    g3 = seen_edges.get(tuple(sorted([b, d])))
                    if g3 is not None:
                        if np.sign(g1) * np.sign(g2) * np.sign(g3) > 0:
                            n_bal += 1
                        else:
                            n_frust += 1
        total_tri = (n_bal + n_frust) // 6  # each triangle counted 6 times
        n_bal //= 6; n_frust //= 6
        balance = n_bal / max(1, n_bal + n_frust)

        print(f"{code:<8} {n_edges:>6} {density:>7.1%} {diameter:>9} "
              f"{camps.get('cosmopolitan', 0):>6} {camps.get('tradition', 0):>5} "
              f"{balance:>7.1%}")

    # Cleanup temp files
    for f in DATA.glob("_tmp_wvs_*"):
        f.unlink()

    print(f"\nDone. Visualizations saved to data/results/")


if __name__ == "__main__":
    main()
