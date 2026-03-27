"""
Post-SES-Realignment Analysis — WVS Geographic Sweep

Analyzes the realigned WVS geographic sweep (66 countries, Wave 7):
  1. Descriptive stats (significance, signs, magnitudes)
  2. Domain circle network (standard, sign-colored)
  3. Bipartite structure check
  4. SES dominance per bridge
  5. SES-colored circle network
  6. Regional patterns by Inglehart-Welzel cultural zone

Outputs:
  data/results/wvs_domain_circle_network_post_realignment.png
  data/results/wvs_domain_circle_network_ses_colored.png
  data/results/wvs_post_realignment_report.md

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_wvs_post_realignment.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import Wedge
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

RESULTS = ROOT / "data" / "results"

# ─── WVS domain labels ──────────────────────────────────────────────────────
WVS_DOMAIN_LABELS = {
    "WVS_A": "Social\nValues", "WVS_B": "Environ-\nment", "WVS_C": "Work",
    "WVS_D": "Family", "WVS_E": "Politics", "WVS_F": "Religion\n& Morale",
    "WVS_G": "National\nIdentity", "WVS_H": "Security", "WVS_I": "Science\n& Tech",
}

_CMAP24 = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#d37295", "#8cd17d", "#b6992d", "#499894", "#86bcb6",
    "#f1ce63", "#a0cbe8", "#ffbe7d", "#86bcb6", "#e49444",
]

ZONE_COLORS = {
    "Latin America": "#e15759",
    "English-speaking": "#4e79a7",
    "Protestant Europe": "#76b7b2",
    "Catholic Europe": "#b07aa1",
    "Orthodox/ex-Communist": "#9c755f",
    "Confucian": "#edc948",
    "South/Southeast Asian": "#59a14f",
    "African-Islamic": "#f28e2b",
}

SES_COLORS = {
    "escol": "#e15759", "Tam_loc": "#4e79a7",
    "sexo": "#59a14f", "edad": "#edc948",
}
SES_LABELS = {
    "escol": "Education", "Tam_loc": "Urbanization",
    "sexo": "Gender", "edad": "Age/Cohort",
}


# ─── Data loading ────────────────────────────────────────────────────────────

def load_wvs_geographic(path: Path) -> dict:
    """Load WVS geographic sweep. Returns {key: {country, construct_a, construct_b, ...}}."""
    with open(path) as f:
        raw = json.load(f)
    estimates = raw.get("estimates", {})
    out = {}
    for key, v in estimates.items():
        if "dr_gamma" not in v:
            continue
        # Key format: WVS_W7_KAZ::wvs_agg_name|WVS_D::wvs_agg_name|WVS_E
        parts = key.split("::")
        if len(parts) != 3:
            continue
        context = parts[0]  # WVS_W7_KAZ
        country = context.split("_")[-1]  # KAZ

        def to_ca(part):
            if "|" not in part:
                return part
            name, domain = part.rsplit("|", 1)
            name = name.removeprefix("wvs_agg_")
            return f"{domain}|{name}"

        entry = dict(v)
        entry["construct_a"] = to_ca(parts[1])
        entry["construct_b"] = to_ca(parts[2])
        entry["country"] = country
        entry["zone"] = COUNTRY_ZONE.get(country, "Unknown")
        out[key] = entry
    return out


def load_wvs_fingerprints(path: Path) -> dict:
    """Load WVS SES fingerprints."""
    with open(path) as f:
        data = json.load(f)
    fp_raw = data.get("fingerprints", {})
    fp = {}
    for key, item in fp_raw.items():
        # Key: wvs_agg_name → need to find its domain for matching
        fp[key] = {
            "rho_escol": item.get("rho_escol", 0),
            "rho_Tam_loc": item.get("rho_Tam_loc", 0),
            "rho_sexo": item.get("rho_sexo", 0),
            "rho_edad": item.get("rho_edad", 0),
        }
    return fp


# ─── SES dominance ───────────────────────────────────────────────────────────

def compute_ses_dominance(sig_estimates: list[dict], fingerprints: dict) -> list[dict]:
    """Determine dominant SES variable per bridge using fingerprint products."""
    ses_dims = ["rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad"]
    dim_short = {"rho_escol": "escol", "rho_Tam_loc": "Tam_loc",
                 "rho_sexo": "sexo", "rho_edad": "edad"}

    # Build lookup: domain|name → fingerprint key (wvs_agg_name)
    # construct_a format: WVS_D|familial_duty_obligations
    # fingerprint key: wvs_agg_familial_duty_obligations
    def construct_to_fp_key(ca):
        name = ca.split("|", 1)[1] if "|" in ca else ca
        return f"wvs_agg_{name}"

    results = []
    for v in sig_estimates:
        fp_key_a = construct_to_fp_key(v["construct_a"])
        fp_key_b = construct_to_fp_key(v["construct_b"])
        fp_a = fingerprints.get(fp_key_a)
        fp_b = fingerprints.get(fp_key_b)
        if not fp_a or not fp_b:
            results.append({**v, "dominant_ses": "unknown", "ses_contributions": {}})
            continue
        contribs = {dim_short[d]: fp_a[d] * fp_b[d] for d in ses_dims}
        dominant = max(contribs, key=lambda k: abs(contribs[k]))
        results.append({**v, "dominant_ses": dominant, "ses_contributions": contribs})
    return results


# ─── Bipartite structure ─────────────────────────────────────────────────────

def check_bipartite_structure(sig_estimates: list[dict]) -> dict:
    adj = defaultdict(dict)
    nodes = set()
    for v in sig_estimates:
        ca, cb = v["construct_a"], v["construct_b"]
        sign = 1 if v["dr_gamma"] > 0 else -1
        adj[ca][cb] = sign
        adj[cb][ca] = sign
        nodes.add(ca); nodes.add(cb)

    node_list = sorted(nodes)
    n_bal = n_frus = 0
    for i, a in enumerate(node_list):
        for j, b in enumerate(node_list[i+1:], i+1):
            if b not in adj[a]:
                continue
            for c in node_list[j+1:]:
                if c not in adj[a] or c not in adj[b]:
                    continue
                if adj[a][b] * adj[a][c] * adj[b][c] > 0:
                    n_bal += 1
                else:
                    n_frus += 1

    total = n_bal + n_frus
    n_pos = sum(1 for v in sig_estimates if v["dr_gamma"] > 0)
    return {
        "n_nodes": len(nodes), "n_edges": len(sig_estimates),
        "n_pos": n_pos, "n_neg": len(sig_estimates) - n_pos,
        "n_triangles": total, "n_balanced": n_bal, "n_frustrated": n_frus,
        "balance_pct": 100 * n_bal / total if total else 0,
    }


# ─── Geometry (reused) ──────────────────────────────────────────────────────

def domain_angles(domains):
    n = len(domains)
    step = 2 * np.pi / n
    return {d: np.pi / 2 - i * step for i, d in enumerate(sorted(domains))}

def layout_nodes(constructs, dam, n_dom, node_radius=3.4, spread_frac=0.68):
    sector = 2 * np.pi / n_dom
    half = sector * spread_frac / 2
    by_domain = defaultdict(list)
    for c in constructs:
        by_domain[c.split("|")[0]].append(c)
    pos = {}
    for dom, members in by_domain.items():
        center = dam[dom]
        n = len(members)
        angles = [center] if n == 1 else np.linspace(center - half, center + half, n)
        for angle, c in zip(angles, sorted(members)):
            pos[c] = (node_radius * np.cos(angle), node_radius * np.sin(angle))
    return pos

def draw_sector_backgrounds(ax, domains, dam, n_dom, inner_r=2.8, outer_r=4.0, domain_colors=None):
    sector_deg = 360 / n_dom
    half_deg = sector_deg / 2
    for dom in domains:
        angle_deg = np.degrees(dam[dom])
        color = domain_colors.get(dom, "#cccccc")
        ax.add_patch(Wedge((0, 0), outer_r, angle_deg - half_deg, angle_deg + half_deg,
                           width=outer_r - inner_r, facecolor=color, alpha=0.12,
                           edgecolor=color, linewidth=0.4))

def curved_edge(ax, p1, p2, color, alpha, lw, rad=0.25):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-", color=color, alpha=alpha,
                                lw=lw, connectionstyle=f"arc3,rad={rad}"))


# ─── Plot functions ──────────────────────────────────────────────────────────

def _plot_network_base(sig_estimates, all_constructs, title, output_path,
                       edge_color_fn, legend_elements, stats_text):
    """Shared circle network plot logic."""
    constructs = sorted(all_constructs)
    domains = sorted(set(c.split("|")[0] for c in constructs))
    n_dom = len(domains)
    domain_colors = {d: _CMAP24[i % len(_CMAP24)] for i, d in enumerate(domains)}
    node_colors = {c: domain_colors[c.split("|")[0]] for c in constructs}

    sig_nodes = set()
    degree = defaultdict(int)
    for v in sig_estimates:
        sig_nodes.add(v["construct_a"]); sig_nodes.add(v["construct_b"])
        degree[v["construct_a"]] += 1; degree[v["construct_b"]] += 1

    dam = domain_angles(domains)
    pos = layout_nodes(constructs, dam, n_dom)

    fig, ax = plt.subplots(figsize=(22, 22))
    ax.set_aspect("equal"); ax.axis("off")
    lim = 6.5
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    draw_sector_backgrounds(ax, domains, dam, n_dom, 2.7, 4.1, domain_colors)

    g_vals = [abs(v["dr_gamma"]) for v in sig_estimates]
    g_max = max(g_vals) if g_vals else 1.0
    g_min = min(g_vals) if g_vals else 0.0
    g_range = g_max - g_min if g_max > g_min else 1.0

    for v in sorted(sig_estimates, key=lambda x: abs(x["dr_gamma"])):
        ca, cb = v["construct_a"], v["construct_b"]
        if ca not in pos or cb not in pos:
            continue
        color, style = edge_color_fn(v)
        norm_g = (abs(v["dr_gamma"]) - g_min) / g_range
        alpha = 0.15 + 0.55 * norm_g
        lw = 0.4 + 2.6 * norm_g
        if style == "-":
            curved_edge(ax, pos[ca], pos[cb], color, alpha, lw, 0.18)
        else:
            ax.annotate("", xy=pos[cb], xytext=pos[ca],
                        arrowprops=dict(arrowstyle="-", color=color, alpha=alpha,
                                        lw=lw, connectionstyle="arc3,rad=0.18",
                                        linestyle=style))

    for c in constructs:
        x, y = pos[c]
        deg = degree.get(c, 0); is_sig = c in sig_nodes
        size = (40 + min(deg * 14, 200)) if is_sig else 12
        color = node_colors[c] if is_sig else "#cccccc"
        ax.scatter(x, y, s=size, c=color, zorder=5 if is_sig else 3,
                   edgecolors="white" if is_sig else "#aaaaaa",
                   linewidths=0.7 if is_sig else 0.3,
                   alpha=0.92 if is_sig else 0.45)

    deg_threshold = max(5, np.percentile(list(degree.values()) or [0], 70))
    for c in constructs:
        if c in sig_nodes and degree.get(c, 0) >= deg_threshold:
            x, y = pos[c]
            short = c.split("|")[1].replace("_", " ")[:14]
            ax.text(x, y, short, ha="center", va="center", fontsize=4.5, zorder=6,
                    color="white" if degree.get(c, 0) >= 10 else "black",
                    fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=1.2, foreground="black")])

    label_radius = 4.75
    for dom in domains:
        angle = dam[dom]
        lx, ly = label_radius * np.cos(angle), label_radius * np.sin(angle)
        label = WVS_DOMAIN_LABELS.get(dom, dom)
        ha = "left" if lx > 0.3 else ("right" if lx < -0.3 else "center")
        ax.text(lx, ly, f"{dom}\n{label}", ha=ha, va="center", fontsize=8.5,
                fontweight="bold", color=domain_colors[dom],
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")], zorder=6)

    ax.legend(handles=legend_elements, loc="lower left", bbox_to_anchor=(0.01, 0.01),
              fontsize=9, framealpha=0.85)
    ax.text(0, -lim + 0.3, stats_text, ha="center", va="bottom", fontsize=8.5,
            color="#444444", path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])
    ax.set_title(title, fontsize=15, fontweight="bold", pad=16, y=0.98)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Saved: {output_path}")


def plot_standard(sig, constructs, title, path):
    def color_fn(v):
        return ("#d62728" if v["dr_gamma"] > 0 else "#1f77b4"), "-"
    n_pos = sum(1 for v in sig if v["dr_gamma"] > 0)
    legend = [
        mpatches.Patch(facecolor="#d62728", alpha=0.7, label="γ > 0"),
        mpatches.Patch(facecolor="#1f77b4", alpha=0.7, label="γ < 0"),
    ]
    g_max = max(abs(v["dr_gamma"]) for v in sig) if sig else 0
    stats = f"{len(sig)} edges ({n_pos} pos / {len(sig)-n_pos} neg)  |  max |γ| = {g_max:.3f}"
    _plot_network_base(sig, constructs, title, path, color_fn, legend, stats)


def plot_ses_colored(enriched, constructs, title, path):
    def color_fn(v):
        color = SES_COLORS.get(v.get("dominant_ses", ""), "#999999")
        style = "-" if v["dr_gamma"] > 0 else (0, (4, 3))
        return color, style
    dom_counts = Counter(v["dominant_ses"] for v in enriched)
    legend = [mpatches.Patch(facecolor=SES_COLORS[k], alpha=0.8,
                             label=f"{SES_LABELS[k]}  ({k})")
              for k in ["escol", "Tam_loc", "sexo", "edad"]]
    legend.extend([
        plt.Line2D([0], [0], color="grey", lw=1.5, linestyle="-",  label="γ > 0 (solid)"),
        plt.Line2D([0], [0], color="grey", lw=1.5, linestyle="--", label="γ < 0 (dashed)"),
    ])
    dom_str = "  |  ".join(f"{SES_LABELS.get(k,k)}: {n}" for k, n in dom_counts.most_common())
    stats = f"{len(enriched)} edges  |  {dom_str}"
    _plot_network_base(enriched, constructs, title, path, color_fn, legend, stats)


# ─── Regional analysis ──────────────────────────────────────────────────────

def analyze_regional_patterns(all_estimates: dict) -> dict:
    """Per-zone and per-country statistics."""
    by_zone = defaultdict(list)
    by_country = defaultdict(list)

    for v in all_estimates.values():
        country = v.get("country", "?")
        zone = v.get("zone", "Unknown")
        by_country[country].append(v)
        by_zone[zone].append(v)

    zone_stats = {}
    for zone in sorted(by_zone):
        ests = by_zone[zone]
        gammas = [abs(v["dr_gamma"]) for v in ests]
        sig = [v for v in ests if v.get("excl_zero")]
        n_pos = sum(1 for v in sig if v["dr_gamma"] > 0)
        zone_stats[zone] = {
            "n_countries": len(set(v["country"] for v in ests)),
            "n_estimates": len(ests),
            "n_sig": len(sig),
            "sig_pct": 100 * len(sig) / len(ests) if ests else 0,
            "med_abs_gamma": float(np.median(gammas)),
            "mean_abs_gamma": float(np.mean(gammas)),
            "max_abs_gamma": float(np.max(gammas)),
            "pos_pct": 100 * n_pos / len(sig) if sig else 0,
        }

    country_stats = {}
    for country in sorted(by_country):
        ests = by_country[country]
        gammas = [abs(v["dr_gamma"]) for v in ests]
        sig = [v for v in ests if v.get("excl_zero")]
        country_stats[country] = {
            "zone": COUNTRY_ZONE.get(country, "Unknown"),
            "n_estimates": len(ests),
            "n_sig": len(sig),
            "sig_pct": 100 * len(sig) / len(ests) if ests else 0,
            "med_abs_gamma": float(np.median(gammas)),
        }

    return {"zone_stats": zone_stats, "country_stats": country_stats}


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Load geographic sweep
    sweep_path = RESULTS / "wvs_geographic_sweep_w7.json"
    print(f"Loading: {sweep_path.name}")
    all_estimates = load_wvs_geographic(sweep_path)
    print(f"Total estimates: {len(all_estimates):,}")

    # Load WVS fingerprints
    fp_path = RESULTS / "wvs_ses_fingerprints.json"
    fingerprints = load_wvs_fingerprints(fp_path)
    print(f"WVS fingerprints: {len(fingerprints)}")

    # Aggregate across countries: median γ per construct pair
    pair_gammas = defaultdict(list)
    for v in all_estimates.values():
        pair_key = (v["construct_a"], v["construct_b"])
        pair_gammas[pair_key].append(v["dr_gamma"])

    # Build "median-across-countries" aggregate estimates for network plot
    agg_sig = []
    for (ca, cb), gammas in pair_gammas.items():
        med_g = float(np.median(gammas))
        # Count how many countries have this pair significant
        pair_ests = [v for v in all_estimates.values()
                     if v["construct_a"] == ca and v["construct_b"] == cb]
        n_sig = sum(1 for v in pair_ests if v.get("excl_zero"))
        # Consider aggregate-significant if >50% of countries have it significant
        if n_sig > len(pair_ests) * 0.5:
            agg_sig.append({
                "construct_a": ca, "construct_b": cb,
                "dr_gamma": med_g,
                "n_countries_sig": n_sig,
                "n_countries_total": len(pair_ests),
                "excl_zero": True,
            })

    print(f"Aggregate significant pairs (>50% countries): {len(agg_sig)}")

    # Get all constructs
    all_constructs = set()
    for v in all_estimates.values():
        all_constructs.add(v["construct_a"])
        all_constructs.add(v["construct_b"])
    print(f"Constructs: {len(all_constructs)}")

    # All significant (per-country)
    all_sig = [v for v in all_estimates.values() if v.get("excl_zero")]

    # ── 1. Descriptive stats ─────────────────────────────────────────────
    gammas = [v["dr_gamma"] for v in all_sig]
    abs_gammas = [abs(g) for g in gammas]
    n_pos = sum(1 for g in gammas if g > 0)
    n_neg = len(gammas) - n_pos
    print(f"\n{'='*60}")
    print("WVS GEOGRAPHIC POST-REALIGNMENT DESCRIPTIVES")
    print(f"{'='*60}")
    print(f"Total estimates: {len(all_estimates):,}")
    print(f"Significant: {len(all_sig):,} ({100*len(all_sig)/len(all_estimates):.1f}%)")
    print(f"Sign: {n_pos:,} pos ({100*n_pos/len(all_sig):.0f}%) / {n_neg:,} neg ({100*n_neg/len(all_sig):.0f}%)")
    print(f"|γ| med={np.median(abs_gammas):.4f}  mean={np.mean(abs_gammas):.4f}  max={max(abs_gammas):.4f}")
    print(f"\nTop 5 by median |γ| across countries:")
    top_pairs = sorted(pair_gammas.items(), key=lambda x: abs(np.median(x[1])), reverse=True)[:5]
    for (ca, cb), gs in top_pairs:
        print(f"  med γ={np.median(gs):+.4f} (n={len(gs)})  {ca} × {cb}")

    # ── 2. Standard circle network (aggregate) ───────────────────────────
    print(f"\nPlotting standard circle network (aggregate)...")
    plot_standard(
        agg_sig, all_constructs,
        title=("WVS Geographic — Aggregate Construct Network (Post-Realignment)\n"
               "Edges significant in >50% of 66 countries  |  median γ across countries"),
        path=RESULTS / "wvs_domain_circle_network_post_realignment.png",
    )

    # ── 3. Bipartite structure ───────────────────────────────────────────
    print(f"\nChecking bipartite structure (aggregate)...")
    bp = check_bipartite_structure(agg_sig)
    print(f"Nodes: {bp['n_nodes']}  Edges: {bp['n_edges']}")
    print(f"Sign: {bp['n_pos']} pos / {bp['n_neg']} neg")
    print(f"Triangles: {bp['n_triangles']} ({bp['n_balanced']} balanced / {bp['n_frustrated']} frustrated)")
    print(f"Structural balance: {bp['balance_pct']:.1f}%")

    # ── 4. SES dominance ─────────────────────────────────────────────────
    print(f"\nComputing SES dominance (aggregate)...")
    enriched = compute_ses_dominance(agg_sig, fingerprints)
    dom_counts = Counter(v["dominant_ses"] for v in enriched)
    print("Dominant SES dimension:")
    for dim, cnt in dom_counts.most_common():
        print(f"  {SES_LABELS.get(dim, dim)}: {cnt} ({100*cnt/len(enriched):.1f}%)")

    # ── 5. SES-colored network ───────────────────────────────────────────
    print(f"\nPlotting SES-colored circle network...")
    plot_ses_colored(
        enriched, all_constructs,
        title=("WVS Geographic — Network by Dominant SES Dimension\n"
               "Edge color = primary SES driver  |  solid = γ>0, dashed = γ<0"),
        path=RESULTS / "wvs_domain_circle_network_ses_colored.png",
    )

    # ── 6. Regional patterns ─────────────────────────────────────────────
    print(f"\nAnalyzing regional patterns...")
    regional = analyze_regional_patterns(all_estimates)

    print(f"\n{'Zone':<25s} {'Countries':>9} {'Estimates':>10} {'Sig%':>6} {'Med|γ|':>8} {'Pos%':>6}")
    print("-" * 70)
    for zone in sorted(regional["zone_stats"], key=lambda z: -regional["zone_stats"][z]["med_abs_gamma"]):
        s = regional["zone_stats"][zone]
        print(f"{zone:<25s} {s['n_countries']:>9} {s['n_estimates']:>10,} "
              f"{s['sig_pct']:>5.1f}% {s['med_abs_gamma']:>7.4f} {s['pos_pct']:>5.0f}%")

    # Per-zone SES dominance
    print(f"\nSES dominance by zone:")
    for zone in sorted(CULTURAL_ZONES):
        zone_sig = [v for v in all_sig if v.get("zone") == zone]
        if not zone_sig:
            continue
        zone_enriched = compute_ses_dominance(zone_sig, fingerprints)
        zdc = Counter(v["dominant_ses"] for v in zone_enriched)
        top = zdc.most_common(2)
        top_str = ", ".join(f"{SES_LABELS.get(d,d)} {100*c/len(zone_enriched):.0f}%"
                            for d, c in top)
        print(f"  {zone:<25s}: {top_str}")

    # Top/bottom countries by significance rate
    cs = regional["country_stats"]
    by_sig = sorted(cs.items(), key=lambda x: -x[1]["sig_pct"])
    print(f"\nTop 5 countries by sig%:")
    for c, s in by_sig[:5]:
        print(f"  {c} ({s['zone'][:12]}): {s['sig_pct']:.1f}% sig, med|γ|={s['med_abs_gamma']:.4f}")
    print(f"Bottom 5:")
    for c, s in by_sig[-5:]:
        print(f"  {c} ({s['zone'][:12]}): {s['sig_pct']:.1f}% sig, med|γ|={s['med_abs_gamma']:.4f}")

    # ── 7. Write report ──────────────────────────────────────────────────
    report_path = RESULTS / "wvs_post_realignment_report.md"
    with open(report_path, "w") as f:
        f.write("# WVS Geographic Post-Realignment Analysis\n\n")
        f.write("## Global Descriptives\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Countries | 66 |\n")
        f.write(f"| Total estimates | {len(all_estimates):,} |\n")
        f.write(f"| Significant | {len(all_sig):,} ({100*len(all_sig)/len(all_estimates):.1f}%) |\n")
        f.write(f"| Sign split | {n_pos:,} pos / {n_neg:,} neg ({100*n_pos/len(all_sig):.0f}%/{100*n_neg/len(all_sig):.0f}%) |\n")
        f.write(f"| Med \\|γ\\| | {np.median(abs_gammas):.4f} |\n")
        f.write(f"| Max \\|γ\\| | {max(abs_gammas):.4f} |\n\n")

        f.write("## Aggregate Network (>50% countries significant)\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Edges | {len(agg_sig)} |\n")
        f.write(f"| Nodes connected | {bp['n_nodes']} |\n")
        f.write(f"| Structural balance | {bp['balance_pct']:.1f}% |\n\n")

        f.write("## SES Dominance (aggregate)\n\n")
        f.write(f"| SES Dimension | Count | % |\n|---|---|---|\n")
        for dim in ["escol", "Tam_loc", "sexo", "edad"]:
            cnt = dom_counts.get(dim, 0)
            f.write(f"| {SES_LABELS[dim]} | {cnt} | {100*cnt/len(enriched):.1f}% |\n")

        f.write(f"\n## Regional Patterns by Cultural Zone\n\n")
        f.write(f"| Zone | Countries | Sig% | Med \\|γ\\| | Pos% |\n")
        f.write(f"|------|-----------|------|----------|------|\n")
        for zone in sorted(regional["zone_stats"],
                           key=lambda z: -regional["zone_stats"][z]["med_abs_gamma"]):
            s = regional["zone_stats"][zone]
            f.write(f"| {zone} | {s['n_countries']} | {s['sig_pct']:.1f}% | "
                    f"{s['med_abs_gamma']:.4f} | {s['pos_pct']:.0f}% |\n")

        f.write(f"\n## Top 10 Aggregate Bridges\n\n")
        f.write(f"| Med γ | Dominant SES | Construct A | Construct B |\n")
        f.write(f"|-------|-------------|-------------|-------------|\n")
        for v in sorted(enriched, key=lambda x: abs(x["dr_gamma"]), reverse=True)[:10]:
            f.write(f"| {v['dr_gamma']:+.4f} | {v.get('dominant_ses','?')} | "
                    f"{v['construct_a']} | {v['construct_b']} |\n")

    print(f"\nReport: {report_path}")
    print("Done.")


if __name__ == "__main__":
    main()
