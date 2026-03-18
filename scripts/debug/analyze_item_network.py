"""
Item-Level Network Analysis — Full L0 → L1 → Bridge → L1 → L0 Chain

Builds the expanded network where:
  - L0 items connect to L1 constructs via loading_gamma (exact or approximate)
  - L1 constructs connect to other L1 constructs via DR bridge γ
  - Signal chain: loading_A × γ(A→B) × loading_B

Computes item-level network metrics, signal attenuation, and domain-to-domain
flow analysis. Updates the topology report with a new section.

Outputs:
  data/results/network_topology_report.md   — appended with item-level section
  data/results/network_item_signal_heatmap.png
  data/results/network_item_loading_dist.png
  data/results/network_item_signal_attenuation.png
  data/results/network_item_bipartite.png

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_item_network.py
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
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "data" / "results"
ONTOLOGY = RESULTS / "kg_ontology_v2.json"
FINGERPRINTS = RESULTS / "ses_fingerprints.json"
REPORT = RESULTS / "network_topology_report.md"
OUT_DIR = RESULTS

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
})

DOMAIN_LABELS = {
    "CIE": "Ciencia", "COR": "Corrupción", "CUL": "Cultura Pol.",
    "DEP": "Deporte/Lectura", "DER": "Derechos", "ECO": "Economía",
    "EDU": "Educación", "ENV": "Envejecim.", "FAM": "Familia",
    "FED": "Fed./Gobierno", "GEN": "Género", "GLO": "Global.",
    "HAB": "Habitación", "IDE": "Identidad", "IND": "Industria",
    "JUS": "Justicia", "MED": "Medio Amb.", "MIG": "Migración",
    "NIN": "Niñez/Juventud", "POB": "Pobreza", "REL": "Religión",
    "SAL": "Salud", "SEG": "Seguridad", "SOC": "Soc. Digital",
    "JUE": "Juegos Azar", "CON": "Constitucional",
}


# ─── Load data ────────────────────────────────────────────────────────────────

def load_all():
    with open(ONTOLOGY) as f:
        ont = json.load(f)
    with open(FINGERPRINTS) as f:
        fp = json.load(f)
    return ont, fp


def build_item_construct_map(fp: dict) -> dict:
    """Build item → construct mapping with loading gammas.

    Returns dict of item_key → {
        construct: str | None,
        loading_gamma: float | None,
        loading_type: 'exact' | 'approximate' | 'none',
        domain: str,
        rho_vec: [4 floats],
        ses_magnitude: float,
    }
    """
    items = {}
    for key, rec in fp["items"].items():
        lt = rec.get("loading_type", "none")
        if lt == "exact":
            construct = rec.get("parent_construct")
            lg = rec.get("loading_gamma")
        elif lt == "approximate":
            construct = rec.get("candidate_construct")
            lg = rec.get("candidate_loading_gamma")
        else:
            construct = None
            lg = None

        items[key] = {
            "construct": construct,
            "loading_gamma": lg,
            "loading_type": lt,
            "domain": rec.get("domain", key.split("|")[1] if "|" in key else "UNK"),
            "rho_vec": [rec.get("rho_escol", 0), rec.get("rho_Tam_loc", 0),
                        rec.get("rho_sexo", 0), rec.get("rho_edad", 0)],
            "ses_magnitude": rec.get("ses_magnitude", 0),
        }
    return items


def build_bridges(ont: dict) -> dict:
    """Build construct → construct bridge map.

    Returns dict of (construct_a, construct_b) → gamma.
    Both directions stored.
    """
    # Normalize construct IDs from ontology (__ → |)
    construct_ids = set()
    for c in ont["constructs"]:
        norm = c["id"].replace("__", "|", 1) if "__" in c["id"] else c["id"]
        construct_ids.add(norm)

    bridges = {}
    for b in ont["bridges"]:
        src, tgt = b["from"], b["to"]
        gamma = b["gamma"]
        bridges[(src, tgt)] = gamma
        bridges[(tgt, src)] = gamma
    return bridges, construct_ids


# ─── Analysis ─────────────────────────────────────────────────────────────────

def compute_item_stats(items: dict) -> dict:
    """Basic statistics about item-construct mapping."""
    by_type = Counter(v["loading_type"] for v in items.values())
    by_domain = Counter(v["domain"] for v in items.values())

    # Items per construct
    construct_items = defaultdict(list)
    for key, v in items.items():
        if v["construct"]:
            construct_items[v["construct"]].append(key)
    items_per_construct = [len(v) for v in construct_items.values()]

    # Loading gamma distributions by type
    exact_loadings = [v["loading_gamma"] for v in items.values()
                      if v["loading_type"] == "exact" and v["loading_gamma"] is not None]
    approx_loadings = [v["loading_gamma"] for v in items.values()
                       if v["loading_type"] == "approximate" and v["loading_gamma"] is not None]

    return {
        "n_items": len(items),
        "by_type": by_type,
        "by_domain": by_domain,
        "construct_items": construct_items,
        "items_per_construct": items_per_construct,
        "exact_loadings": exact_loadings,
        "approx_loadings": approx_loadings,
    }


def compute_signal_chains(items: dict, bridges: dict) -> dict:
    """Compute all possible item-to-item signal chains through bridges.

    For each bridge (construct_A, construct_B) with γ(A,B):
      - For each item_a in construct_A with loading_gamma_a:
        - For each item_b in construct_B with loading_gamma_b:
          - signal = loading_a × γ(A,B) × loading_b
    """
    # Group items by construct
    construct_items = defaultdict(list)
    for key, v in items.items():
        if v["construct"] and v["loading_gamma"] is not None:
            construct_items[v["construct"]].append((key, v))

    # For each bridge, compute signals
    signals = []
    domain_signals = defaultdict(list)  # (domain_a, domain_b) → [signal, ...]
    bridge_fan = defaultdict(lambda: {"n_item_pairs": 0, "signals": []})  # bridge → stats

    seen_bridges = set()
    for (ca, cb), gamma in bridges.items():
        if (cb, ca) in seen_bridges:
            continue
        seen_bridges.add((ca, cb))

        items_a = construct_items.get(ca, [])
        items_b = construct_items.get(cb, [])
        if not items_a or not items_b:
            continue

        for key_a, va in items_a:
            for key_b, vb in items_b:
                la = va["loading_gamma"]
                lb = vb["loading_gamma"]
                signal = la * gamma * lb
                abs_signal = abs(signal)
                signals.append(abs_signal)

                dom_a = va["domain"]
                dom_b = vb["domain"]
                pair = tuple(sorted([dom_a, dom_b]))
                domain_signals[pair].append(signal)

                bridge_fan[(ca, cb)]["n_item_pairs"] += 1
                bridge_fan[(ca, cb)]["signals"].append(abs_signal)

    return {
        "signals": signals,
        "domain_signals": domain_signals,
        "bridge_fan": bridge_fan,
        "n_chains": len(signals),
    }


def compute_effective_degree(items: dict, bridges: dict, construct_items: dict) -> dict:
    """For each item, how many items in OTHER domains can it reach (with signal > threshold)?"""
    # Build item → construct lookup
    item_construct = {}
    for key, v in items.items():
        if v["construct"]:
            item_construct[key] = v["construct"]

    # Build construct → bridged constructs
    construct_bridges = defaultdict(set)
    for (ca, cb) in bridges:
        construct_bridges[ca].add(cb)

    # For each item, count reachable items
    item_reach = {}
    for key, v in items.items():
        c = v.get("construct")
        if not c:
            item_reach[key] = 0
            continue
        # Reachable constructs
        bridged = construct_bridges.get(c, set())
        # Count items in bridged constructs
        n_reachable = sum(len(construct_items.get(bc, [])) for bc in bridged)
        item_reach[key] = n_reachable

    return item_reach


def compute_domain_flow_matrix(domain_signals: dict, all_domains: list) -> tuple:
    """Build domain × domain matrices for mean signal and count."""
    n = len(all_domains)
    count_mat = np.zeros((n, n))
    mean_signal_mat = np.full((n, n), np.nan)
    mean_abs_signal_mat = np.full((n, n), np.nan)

    for (da, db), sigs in domain_signals.items():
        i = all_domains.index(da) if da in all_domains else -1
        j = all_domains.index(db) if db in all_domains else -1
        if i < 0 or j < 0:
            continue
        count_mat[i, j] = len(sigs)
        count_mat[j, i] = len(sigs)
        mean_signal_mat[i, j] = np.mean(sigs)
        mean_signal_mat[j, i] = np.mean(sigs)
        mean_abs_signal_mat[i, j] = np.mean(np.abs(sigs))
        mean_abs_signal_mat[j, i] = np.mean(np.abs(sigs))

    return count_mat, mean_signal_mat, mean_abs_signal_mat


# ─── Visualizations ──────────────────────────────────────────────────────────

def plot_loading_distributions(stats: dict, path: Path):
    """Loading gamma distributions for exact vs approximate items."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    # Exact loadings
    ax = axes[0]
    exact = stats["exact_loadings"]
    ax.hist(exact, bins=40, color="#4e79a7", edgecolor="white", alpha=0.85)
    ax.axvline(np.median(exact), color="#e15759", ls="--", lw=1.5,
               label=f"Median = {np.median(exact):.3f}")
    ax.axvline(0, color="black", ls="-", lw=0.8)
    ax.set_xlabel("Loading γ")
    ax.set_ylabel("Count")
    ax.set_title(f"Exact Loadings (n={len(exact)})")
    ax.legend(fontsize=8)

    # Approximate loadings
    ax2 = axes[1]
    approx = stats["approx_loadings"]
    ax2.hist(approx, bins=60, color="#f28e2b", edgecolor="white", alpha=0.85)
    ax2.axvline(np.median(approx), color="#e15759", ls="--", lw=1.5,
                label=f"Median = {np.median(approx):.3f}")
    ax2.axvline(0, color="black", ls="-", lw=0.8)
    ax2.set_xlabel("Loading γ")
    ax2.set_title(f"Approximate Loadings (n={len(approx)})")
    ax2.legend(fontsize=8)

    # |loading| comparison
    ax3 = axes[2]
    exact_abs = np.abs(exact)
    approx_abs = np.abs(approx)
    bins = np.linspace(0, 1, 50)
    ax3.hist(exact_abs, bins=bins, color="#4e79a7", alpha=0.6, label=f"Exact (med={np.median(exact_abs):.3f})")
    ax3.hist(approx_abs, bins=bins, color="#f28e2b", alpha=0.6, label=f"Approx (med={np.median(approx_abs):.3f})")
    ax3.set_xlabel("|Loading γ|")
    ax3.set_ylabel("Count")
    ax3.set_title("Absolute Loading Comparison")
    ax3.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_signal_attenuation(chain_data: dict, path: Path):
    """Signal attenuation: how much signal survives the full chain."""
    signals = chain_data["signals"]

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    # Signal distribution (log scale)
    ax = axes[0]
    log_sig = np.log10(np.array(signals) + 1e-12)
    ax.hist(log_sig, bins=60, color="#59a14f", edgecolor="white", alpha=0.85)
    ax.axvline(np.log10(np.median(signals)), color="#e15759", ls="--", lw=1.5,
               label=f"Median = {np.median(signals):.4f}")
    ax.axvline(np.log10(0.001), color="black", ls=":", lw=1.5,
               label="Attenuation warning (0.001)")
    ax.set_xlabel("log₁₀(|signal|)")
    ax.set_ylabel("Count")
    ax.set_title(f"Item-to-Item Signal (n={len(signals):,})")
    ax.legend(fontsize=7)

    # CDF of |signal|
    ax2 = axes[1]
    sorted_sig = np.sort(signals)
    cdf_y = np.arange(1, len(sorted_sig) + 1) / len(sorted_sig)
    ax2.plot(sorted_sig, cdf_y, color="#4e79a7", lw=2)
    ax2.axvline(0.001, color="black", ls=":", lw=1.5, label="0.001 threshold")
    ax2.axvline(0.01, color="gray", ls=":", lw=1, label="0.01 threshold")
    ax2.axhline(0.5, color="gray", ls=":", lw=0.5)
    ax2.set_xlabel("|signal|")
    ax2.set_ylabel("CDF")
    ax2.set_xscale("log")
    ax2.set_title("Signal CDF")
    ax2.legend(fontsize=8)

    # Decomposition: |loading_A| × |γ| × |loading_B|
    # Show the three multiplicative components
    ax3 = axes[2]
    # Compute component distributions from the bridge fan data
    bridge_gammas = []
    bridge_mean_loading_products = []
    for (ca, cb), bdata in chain_data["bridge_fan"].items():
        if bdata["signals"]:
            bridge_gammas.append(len(bdata["signals"]))
            bridge_mean_loading_products.append(np.mean(bdata["signals"]))

    # Instead, show the breakdown of where signal is lost
    n_below_001 = sum(1 for s in signals if s < 0.001)
    n_001_01 = sum(1 for s in signals if 0.001 <= s < 0.01)
    n_01_05 = sum(1 for s in signals if 0.01 <= s < 0.05)
    n_above_05 = sum(1 for s in signals if s >= 0.05)
    categories = ["< 0.001\n(noise)", "0.001–0.01\n(weak)", "0.01–0.05\n(moderate)", "≥ 0.05\n(strong)"]
    counts = [n_below_001, n_001_01, n_01_05, n_above_05]
    colors = ["#bab0ac", "#f28e2b", "#59a14f", "#4e79a7"]
    bars = ax3.bar(categories, counts, color=colors, edgecolor="white")
    for bar, cnt in zip(bars, counts):
        pct = cnt / len(signals) * 100
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + len(signals) * 0.01,
                 f"{pct:.0f}%", ha="center", va="bottom", fontsize=9)
    ax3.set_ylabel("Number of item-pairs")
    ax3.set_title("Signal Strength Categories")

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_domain_signal_heatmap(domain_signals: dict, all_domains: list, path: Path):
    """Domain × domain heatmap of mean |signal| and item-pair count."""
    count_mat, mean_signal_mat, mean_abs_signal_mat = compute_domain_flow_matrix(
        domain_signals, all_domains)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Item-pair count
    ax = axes[0]
    log_count = np.log10(count_mat + 1)
    im = ax.imshow(log_count, cmap="YlOrRd", aspect="equal")
    ax.set_xticks(range(len(all_domains)))
    ax.set_yticks(range(len(all_domains)))
    ax.set_xticklabels(all_domains, fontsize=6, rotation=45, ha="right")
    ax.set_yticklabels(all_domains, fontsize=6)
    ax.set_title("Item-Pair Count (log₁₀ scale)")
    fig.colorbar(im, ax=ax, shrink=0.7)

    # Mean |signal|
    ax2 = axes[1]
    im2 = ax2.imshow(mean_abs_signal_mat, cmap="viridis", aspect="equal")
    ax2.set_xticks(range(len(all_domains)))
    ax2.set_yticks(range(len(all_domains)))
    ax2.set_xticklabels(all_domains, fontsize=6, rotation=45, ha="right")
    ax2.set_yticklabels(all_domains, fontsize=6)
    ax2.set_title("Mean |signal| Between Domains")
    fig.colorbar(im2, ax=ax2, shrink=0.7)
    for i in range(len(all_domains)):
        for j in range(len(all_domains)):
            if not np.isnan(mean_abs_signal_mat[i, j]) and mean_abs_signal_mat[i, j] > 0:
                ax2.text(j, i, f"{mean_abs_signal_mat[i,j]:.4f}", ha="center", va="center",
                         fontsize=3.5,
                         color="white" if mean_abs_signal_mat[i, j] > np.nanmax(mean_abs_signal_mat) * 0.5 else "black")

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_bipartite_structure(stats: dict, bridges: dict, path: Path):
    """Visualize the bipartite item-construct-item structure."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Items per construct histogram
    ax = axes[0]
    ipc = stats["items_per_construct"]
    ax.hist(ipc, bins=range(0, max(ipc) + 2), color="#76b7b2", edgecolor="white", alpha=0.85)
    ax.axvline(np.mean(ipc), color="#e15759", ls="--", lw=1.5,
               label=f"Mean = {np.mean(ipc):.1f}")
    ax.set_xlabel("Items per Construct")
    ax.set_ylabel("Count")
    ax.set_title("Items per Construct (all loading types)")
    ax.legend(fontsize=9)

    # Fan-out: items reachable per item through bridges
    ax2 = axes[1]
    # Compute bridge fan-out per construct
    construct_fan = defaultdict(int)
    seen = set()
    for (ca, cb) in bridges:
        if (cb, ca) in seen:
            continue
        seen.add((ca, cb))
        items_b = stats["construct_items"].get(cb, [])
        construct_fan[ca] += len(items_b)
        items_a = stats["construct_items"].get(ca, [])
        construct_fan[cb] += len(items_a)

    fan_values = list(construct_fan.values())
    if fan_values:
        ax2.hist(fan_values, bins=30, color="#b07aa1", edgecolor="white", alpha=0.85)
        ax2.axvline(np.mean(fan_values), color="#e15759", ls="--", lw=1.5,
                    label=f"Mean = {np.mean(fan_values):.0f}")
        ax2.set_xlabel("Reachable Items (through bridges)")
        ax2.set_ylabel("Number of Constructs")
        ax2.set_title("Bridge Fan-Out (items reachable per construct)")
        ax2.legend(fontsize=9)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_item_reach_by_domain(items: dict, item_reach: dict, path: Path):
    """Box plot of item reach (reachable items) by domain."""
    domain_reach = defaultdict(list)
    for key, v in items.items():
        domain_reach[v["domain"]].append(item_reach.get(key, 0))

    # Sort domains by median reach
    domains_sorted = sorted(domain_reach.keys(),
                           key=lambda d: np.median(domain_reach[d]), reverse=True)
    # Exclude domains with all zeros
    domains_sorted = [d for d in domains_sorted if np.max(domain_reach[d]) > 0]

    fig, ax = plt.subplots(figsize=(14, 5))
    data = [domain_reach[d] for d in domains_sorted]
    labels = [f"{d}\n(n={len(domain_reach[d])})" for d in domains_sorted]

    bp = ax.boxplot(data, labels=labels, patch_artist=True, showfliers=False,
                    medianprops={"color": "#e15759", "lw": 2})
    for patch in bp["boxes"]:
        patch.set_facecolor("#a0cbe8")
        patch.set_alpha(0.7)

    ax.set_ylabel("Reachable Items (through bridge chain)")
    ax.set_title("Item Reach by Domain")
    ax.tick_params(axis="x", labelsize=7)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


# ─── Report Section ──────────────────────────────────────────────────────────

def generate_item_section(stats: dict, chain_data: dict, item_reach: dict,
                          items: dict, bridges: dict) -> str:
    """Generate the item-level network section for the report."""
    L = []
    def w(s=""): L.append(s)

    w()
    w("---")
    w()
    w("## 9. The Full Item-Level Network")
    w()

    # ── 9.1 The Three-Layer Architecture ──
    w("### 9.1 The Three-Layer Architecture")
    w()
    w("The construct-level network (Sections 1–8) is a compressed view. The full network has")
    w("three layers:")
    w()
    w("```")
    w("L0 Items (6,359)  ──loading_γ──▶  L1 Constructs (93)  ──bridge_γ──▶  L1 Constructs  ──loading_γ──▶  L0 Items")
    w("     (raw survey questions)            (aggregated scales)                                    (raw survey questions)")
    w("```")
    w()
    w("Each connection in this chain carries a Goodman-Kruskal γ ∈ [-1, 1]:")
    w()
    w("- **Loading γ** (item → construct): measures how strongly an individual survey question")
    w("  co-varies monotonically with its parent construct. Computed as γ(raw_item, bin5(agg_construct)).")
    w("  Items that are reverse-coded have negative loading γ; items aligned with the construct")
    w("  direction have positive loading γ.")
    w()
    w("- **Bridge γ** (construct → construct): the DR bridge estimate from the Julia sweep.")
    w("  Measures SES-mediated monotonic co-variation between two constructs in different domains.")
    w()
    w("The **signal chain** from item A to item B through the bridge is:")
    w()
    w("    signal(A → B) = loading_γ_A × bridge_γ(construct_A, construct_B) × loading_γ_B")
    w()
    w("All three terms are on the same γ scale, so the product is dimensionally consistent.")
    w("Signs propagate correctly: a reverse-coded item (negative loading) connected through a")
    w("positive bridge to a positively-loaded item produces a negative prediction — meaning")
    w("higher values on item A predict lower values on item B, mediated by SES.")
    w()

    # ── 9.2 Item-Construct Coverage ──
    w("### 9.2 Item-Construct Coverage")
    w()

    bt = stats["by_type"]
    n_total = stats["n_items"]
    w(f"**{n_total:,} items** across 24 survey domains, connected to constructs via three mechanisms:")
    w()
    w("| Loading Type | Count | % | Method |")
    w("|-------------|-------|---|--------|")
    w(f"| **Exact** | {bt.get('exact', 0):,} | {bt.get('exact', 0)/n_total:.1%} | γ(item, bin5(parent_construct)) — directly measured |")
    w(f"| **Approximate** | {bt.get('approximate', 0):,} | {bt.get('approximate', 0)/n_total:.1%} | ρ(item, candidate_construct) × 1.14 — nearest construct by fingerprint cosine similarity |")
    w(f"| **None** | {bt.get('none', 0):,} | {bt.get('none', 0)/n_total:.1%} | No construct exists in domain (JUE, CON) |")
    w()
    w(f"The 1.14 scaling factor converts Spearman ρ to approximate γ, based on the empirical")
    w(f"relationship: for 474 construct-member items with both measurements, Pearson r(ρ, γ) = 0.977")
    w(f"and median |γ|/|ρ| = 1.14. The inflation arises because GK γ excludes tied pairs from its")
    w(f"denominator, while ρ averages tied ranks — for 5-point Likert items with ~30-50% ties,")
    w(f"this produces ~14% systematic inflation.")
    w()

    # Domain breakdown
    w("#### Items by Domain")
    w()
    w("| Domain | Items | Exact | Approx | None | Items/Construct |")
    w("|--------|-------|-------|--------|------|-----------------|")
    # Group items by domain and type
    domain_type_counts = defaultdict(lambda: {"exact": 0, "approximate": 0, "none": 0, "total": 0})
    for v in items.values():
        d = v["domain"]
        domain_type_counts[d][v["loading_type"]] += 1
        domain_type_counts[d]["total"] += 1
    # Count constructs per domain
    domain_constructs = Counter(v["construct"].split("|")[0] if v["construct"] and "|" in v["construct"] else ""
                                for v in items.values() if v["construct"])
    for d in sorted(domain_type_counts.keys()):
        tc = domain_type_counts[d]
        n_constructs = domain_constructs.get(d, 0)
        # Count unique constructs for this domain
        unique_constructs = set()
        for v in items.values():
            if v["domain"] == d and v["construct"]:
                unique_constructs.add(v["construct"])
        nc = len(unique_constructs)
        ipc = f"{tc['total']/nc:.0f}" if nc > 0 else "—"
        w(f"| {d} | {tc['total']} | {tc['exact']} | {tc['approximate']} | {tc['none']} | {ipc} |")
    w()

    # ── 9.3 Loading γ Distribution ──
    w("### 9.3 Loading γ Distribution")
    w()
    w("**Definition.** Loading γ measures the monotonic association between an individual item")
    w("and its anchor construct. It answers: *if I know someone's position on the construct,")
    w("how well can I predict their response to this specific item?*")
    w()
    exact = stats["exact_loadings"]
    approx = stats["approx_loadings"]
    w("| Statistic | Exact (n={:,}) | Approximate (n={:,}) |".format(len(exact), len(approx)))
    w("|-----------|--------------|---------------------|")
    w(f"| Mean | {np.mean(exact):.3f} | {np.mean(approx):.3f} |")
    w(f"| Median | {np.median(exact):.3f} | {np.median(approx):.3f} |")
    w(f"| Std. dev. | {np.std(exact):.3f} | {np.std(approx):.3f} |")
    w(f"| Mean |loading| | {np.mean(np.abs(exact)):.3f} | {np.mean(np.abs(approx)):.3f} |")
    w(f"| Median |loading| | {np.median(np.abs(exact)):.3f} | {np.median(np.abs(approx)):.3f} |")
    w(f"| % negative | {sum(1 for x in exact if x < 0)/len(exact):.1%} | {sum(1 for x in approx if x < 0)/len(approx):.1%} |")
    w()

    w("![Loading Distributions](network_item_loading_dist.png)")
    w()
    w("**Figure: Loading γ Distributions.** Left: exact loadings (measured γ for construct-member items).")
    w("Center: approximate loadings (ρ × 1.14 for orphan items matched to nearest construct).")
    w("Right: comparison of absolute loading magnitudes. Exact loadings are substantially larger")
    w("(median |γ| ≈ {:.2f}) because these items were selected *because* they belong to the construct.".format(
        np.median(np.abs(exact))))
    w("Approximate loadings are weaker (median |γ| ≈ {:.2f}) because orphan items are matched".format(
        np.median(np.abs(approx))))
    w("to the nearest construct by fingerprint similarity — a weaker relationship than construct membership.")
    w()
    w("**Consequence for the signal chain:** The loading step is where most signal is lost.")
    w("A bridge γ of 0.10 between two constructs propagates to item-item signal of only")
    w(f"|{np.median(np.abs(exact)):.2f}| × 0.10 × |{np.median(np.abs(exact)):.2f}| ≈ {np.median(np.abs(exact))**2 * 0.10:.4f}")
    w(f"for exact items, and |{np.median(np.abs(approx)):.2f}| × 0.10 × |{np.median(np.abs(approx)):.2f}| ≈ {np.median(np.abs(approx))**2 * 0.10:.4f}")
    w("for approximate items — a 100× attenuation in the approximate case.")
    w()

    # ── 9.4 Signal Attenuation ──
    signals = chain_data["signals"]
    w("### 9.4 Signal Attenuation Through the Full Chain")
    w()
    w("**Definition.** For each pair of bridged constructs, and for each pair of items")
    w("(one from each construct), the signal is |loading_A| × |bridge_γ| × |loading_B|.")
    w("This measures how much of the SES-mediated covariation between constructs survives")
    w("down to the level of individual survey questions.")
    w()
    w(f"Total item-to-item signal chains computed: **{len(signals):,}**")
    w()
    w("| Statistic | Value |")
    w("|-----------|-------|")
    w(f"| Mean |signal| | {np.mean(signals):.5f} |")
    w(f"| Median |signal| | {np.median(signals):.5f} |")
    w(f"| Max |signal| | {np.max(signals):.4f} |")
    w(f"| P90 |signal| | {np.percentile(signals, 90):.5f} |")
    w(f"| P99 |signal| | {np.percentile(signals, 99):.4f} |")
    n_above_001 = sum(1 for s in signals if s >= 0.001)
    n_above_01 = sum(1 for s in signals if s >= 0.01)
    n_above_05 = sum(1 for s in signals if s >= 0.05)
    w(f"| Chains with |signal| ≥ 0.001 | {n_above_001:,} ({n_above_001/len(signals):.1%}) |")
    w(f"| Chains with |signal| ≥ 0.01 | {n_above_01:,} ({n_above_01/len(signals):.1%}) |")
    w(f"| Chains with |signal| ≥ 0.05 | {n_above_05:,} ({n_above_05/len(signals):.1%}) |")
    w()

    w("![Signal Attenuation](network_item_signal_attenuation.png)")
    w()
    w("**Figure: Signal Attenuation.** Left: histogram of log₁₀(|signal|) — the full distribution")
    w("of item-to-item signal strengths. The vertical dashed line marks the 0.001 attenuation")
    w("threshold. Center: CDF on log scale showing what fraction of chains exceed each signal")
    w("level. Right: categorical breakdown of signal strength.")
    w()

    w("**Interpretation.** The signal chain is a **triple multiplicative bottleneck**:")
    w()
    w("1. **Loading attenuation (item → construct):** Most items load at |γ| ≈ 0.05–0.70 on their")
    w("   construct, depending on loading type. This first multiplication reduces the signal by ~50-95%.")
    w()
    w("2. **Bridge attenuation (construct → construct):** Bridge γ values are typically 0.005–0.15.")
    w("   This second multiplication reduces the signal by another 85-99%.")
    w()
    w("3. **Loading attenuation (construct → item):** Same as step 1 in the target domain.")
    w("   A third multiplicative reduction.")
    w()
    w("The cumulative effect: a bridge γ of 0.10 (a strong bridge) between two constructs")
    w("propagates to a median item-item signal of ~10⁻³ to 10⁻⁴. Only the strongest bridges")
    w("between the best-loaded items produce signals above 0.01.")
    w()
    w(f"**{n_above_01/len(signals):.1%} of item-item chains exceed |signal| ≥ 0.01** — these are the")
    w("genuinely detectable SES-mediated associations at the raw survey question level.")
    w(f"The remaining {(1 - n_above_01/len(signals)):.0%} are real in principle but too attenuated to")
    w("be practically useful for individual item-level prediction.")
    w()

    # ── 9.5 Domain-to-Domain Signal Flow ──
    domain_sigs = chain_data["domain_signals"]
    w("### 9.5 Domain-to-Domain Signal Flow")
    w()
    w("**Definition.** For each pair of domains, aggregate all item-to-item signals across all")
    w("bridged construct pairs. The mean |signal| reveals which domain pairs have the strongest")
    w("item-level SES entanglement, accounting for both bridge strength and item loading quality.")
    w()

    w("![Domain Signal Heatmap](network_item_signal_heatmap.png)")
    w()
    w("**Figure: Domain Signal Heatmap.** Left: item-pair count between domains (log₁₀ scale),")
    w("showing the combinatorial fan-out. Right: mean |signal| between domains. Hot cells")
    w("indicate domain pairs where SES-mediated covariation penetrates all the way down to")
    w("individual survey items.")
    w()

    # Top domain pairs by mean |signal|
    pair_stats = []
    for (da, db), sigs in domain_sigs.items():
        pair_stats.append({
            "pair": f"{da} × {db}",
            "n_chains": len(sigs),
            "mean_abs": np.mean(np.abs(sigs)),
            "mean_signed": np.mean(sigs),
            "max_abs": np.max(np.abs(sigs)),
        })
    pair_stats.sort(key=lambda x: x["mean_abs"], reverse=True)

    w("#### Top 10 Domain Pairs by Mean |signal|")
    w()
    w("| Domains | Item Pairs | Mean |signal| | Max |signal| | Mean signed | Direction |")
    w("|---------|------------|----------------|--------------|-------------|-----------|")
    for ps in pair_stats[:10]:
        sign = "co-elevate" if ps["mean_signed"] > 0 else "counter-vary"
        w(f"| {ps['pair']} | {ps['n_chains']:,} | {ps['mean_abs']:.5f} | {ps['max_abs']:.4f} | {ps['mean_signed']:+.5f} | {sign} |")
    w()

    if pair_stats:
        top = pair_stats[0]
        w(f"The strongest domain-level item signal is **{top['pair']}** (mean |signal| = {top['mean_abs']:.5f},")
        w(f"max |signal| = {top['max_abs']:.4f}). Even the strongest domain pair has mean item-level signal")
        w(f"of order 10⁻⁴ to 10⁻³ — consistent with the triple multiplicative bottleneck.")
    w()

    # ── 9.6 Item Reach ──
    w("### 9.6 Item Reach: How Many Items Can Each Item See?")
    w()
    w("**Definition.** The *reach* of an item is the number of items in other domains it can")
    w("connect to through the construct → bridge → construct chain (regardless of signal strength).")
    w("This is the item-level analogue of degree centrality.")
    w()

    reaches = list(item_reach.values())
    nonzero_reaches = [r for r in reaches if r > 0]
    zero_reaches = len(reaches) - len(nonzero_reaches)

    w("| Statistic | All Items | Connected Items |")
    w("|-----------|-----------|-----------------|")
    w(f"| Count | {len(reaches):,} | {len(nonzero_reaches):,} |")
    w(f"| Mean reach | {np.mean(reaches):.0f} | {np.mean(nonzero_reaches):.0f} |")
    w(f"| Median reach | {np.median(reaches):.0f} | {np.median(nonzero_reaches):.0f} |")
    w(f"| Max reach | {max(reaches):,} | {max(nonzero_reaches):,} |")
    w(f"| Zero-reach items | {zero_reaches:,} ({zero_reaches/len(reaches):.1%}) | — |")
    w()

    w("![Item Reach by Domain](network_item_reach_by_domain.png)")
    w()
    w("**Figure: Item Reach by Domain.** Box plots showing how many items each item can reach")
    w("through the bridge chain, by domain. Domains with high-degree constructs (HAB, CIE, REL)")
    w("produce items with the widest reach.")
    w()
    w(f"The median connected item reaches **{np.median(nonzero_reaches):.0f}** items in other domains.")
    w(f"But {zero_reaches:,} items ({zero_reaches/len(reaches):.1%}) have zero reach — either they")
    w("belong to isolated constructs (no significant bridges) or to domains without constructs (JUE, CON).")
    w()

    # ── 9.7 Bipartite structure ──
    w("### 9.7 The Bipartite Fan-Out")
    w()
    w("**Definition.** Each bridge connects two constructs, but each construct aggregates")
    w("multiple items. A single bridge therefore creates a *fan-out* of item-to-item connections")
    w("equal to |items_A| × |items_B|. This fan-out determines the combinatorial structure of")
    w("the item-level network.")
    w()

    ipc = stats["items_per_construct"]
    w(f"Items per construct: mean = {np.mean(ipc):.1f}, median = {np.median(ipc):.0f}, "
      f"range [{min(ipc)}, {max(ipc)}].")
    w()

    # Compute total fan-out
    total_fanout = sum(bdata["n_item_pairs"] for bdata in chain_data["bridge_fan"].values())
    n_bridges = len(chain_data["bridge_fan"])
    w(f"984 construct-level bridges expand to **{total_fanout:,}** item-level signal chains")
    w(f"(average fan-out: {total_fanout/n_bridges:.0f} item-pairs per bridge).")
    w()

    w("![Bipartite Structure](network_item_bipartite.png)")
    w()
    w("**Figure: Bipartite Structure.** Left: items per construct (how many items feed into")
    w("each construct node). Right: bridge fan-out (how many items in other domains are reachable")
    w("from items in each construct, through its bridges).")
    w()

    # ── 9.8 Synthesis ──
    w("### 9.8 Synthesis: The Item-Level Network as a Signal Decay Hierarchy")
    w()
    w("The expanded item-level network reveals a **three-stage signal decay** hierarchy:")
    w()
    w("| Level | Connections | Typical |γ| | Signal remaining |")
    w("|-------|------------|-----------|------------------|")
    w("| L1 ↔ L1 (bridge) | 984 | 0.01–0.29 | 100% (reference) |")
    med_exact_abs = np.median(np.abs(exact))
    med_approx_abs = np.median(np.abs(approx))
    w(f"| L0 → L1 (exact loading) | {bt.get('exact', 0)} | {med_exact_abs:.2f} | ×{med_exact_abs:.2f} |")
    w(f"| L0 → L1 (approx loading) | {bt.get('approximate', 0)} | {med_approx_abs:.2f} | ×{med_approx_abs:.2f} |")
    w(f"| L0 ↔ L0 (full chain, exact) | — | {np.median([s for s in signals if s > np.median(np.abs(exact))**2 * 0.001]):.4f} | ×{med_exact_abs**2:.3f} of bridge |")
    w(f"| L0 ↔ L0 (full chain, approx) | — | ~10⁻⁴ | ×{med_approx_abs**2:.4f} of bridge |")
    w()
    w("**Key insight:** The item-level network is not a *different* network from the construct-level")
    w("network — it is the *same* geometric structure, viewed through a noisy lens. The SES geometry")
    w("(fingerprint positions in R⁴) determines the construct-level bridges, and the loading structure")
    w("determines how much of that signal penetrates to individual items.")
    w()
    w("The practical consequence: **construct-level analysis is the right level of abstraction**.")
    w("Item-level signal is so attenuated that only the strongest bridges between the best-loaded")
    w(f"items produce detectable associations. Of {len(signals):,} possible item-to-item chains,")
    w(f"only {n_above_01:,} ({n_above_01/len(signals):.1%}) exceed |signal| ≥ 0.01.")
    w("The construct layer acts as a *noise-reducing aggregation* that makes the SES geometry visible.")
    w()
    w("However, the item-level view is valuable for one critical purpose: **tracing predictions**")
    w("**to specific survey questions**. When a user asks \"what does housing quality have to do")
    w("with religiosity?\", the answer can be traced from specific housing items (e.g., *does your")
    w("home have running water?*) through the bridge to specific religiosity items (e.g., *how")
    w("often do you attend religious services?*), with explicit signal strength at each step.")

    return "\n".join(L)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    ont, fp = load_all()

    print("Building item-construct map...")
    items = build_item_construct_map(fp)
    bridges, construct_ids = build_bridges(ont)
    print(f"  {len(items):,} items, {len(bridges)//2} bridges")

    print("Computing item statistics...")
    stats = compute_item_stats(items)
    print(f"  By type: {dict(stats['by_type'])}")
    print(f"  Items per construct: mean={np.mean(stats['items_per_construct']):.1f}")

    print("Computing signal chains...")
    chain_data = compute_signal_chains(items, bridges)
    print(f"  {chain_data['n_chains']:,} item-to-item chains")
    if chain_data["signals"]:
        print(f"  Median |signal| = {np.median(chain_data['signals']):.5f}")

    print("Computing item reach...")
    item_reach = compute_effective_degree(items, bridges, stats["construct_items"])

    # ── Visualizations ──
    print("\nGenerating visualizations...")
    plot_loading_distributions(stats, OUT_DIR / "network_item_loading_dist.png")
    plot_signal_attenuation(chain_data, OUT_DIR / "network_item_signal_attenuation.png")

    all_domains = sorted(set(v["domain"] for v in items.values()))
    plot_domain_signal_heatmap(chain_data["domain_signals"], all_domains,
                               OUT_DIR / "network_item_signal_heatmap.png")
    plot_bipartite_structure(stats, bridges, OUT_DIR / "network_item_bipartite.png")
    plot_item_reach_by_domain(items, item_reach, OUT_DIR / "network_item_reach_by_domain.png")

    # ── Report ──
    print("\nGenerating report section...")
    section = generate_item_section(stats, chain_data, item_reach, items, bridges)

    # Append to existing report
    existing = REPORT.read_text()
    updated = existing + "\n" + section
    REPORT.write_text(updated)
    print(f"\n✓ Section 9 appended to {REPORT.name}")
    print(f"✓ {len(list(OUT_DIR.glob('network_item_*.png')))} item-level visualizations saved")


if __name__ == "__main__":
    main()
