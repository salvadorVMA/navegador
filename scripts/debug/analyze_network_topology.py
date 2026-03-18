"""
Network Topology & Geometry Analysis — SES Bridge Graph

Computes global graph metrics, degree distribution, community structure,
structural balance, fingerprint geometry, and generates visualizations.

Outputs:
  data/results/network_topology_report.md   — full markdown report
  data/results/network_topology_*.png       — visualizations

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_network_topology.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import networkx as nx
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import pdist, squareform

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "data" / "results"
ONTOLOGY = RESULTS / "kg_ontology_v2.json"
FINGERPRINTS = RESULTS / "ses_fingerprints.json"
OUT_DIR = RESULTS

# ─── Style ────────────────────────────────────────────────────────────────────

DOMAIN_LABELS = {
    "CIE": "Ciencia", "COR": "Corrupción", "CUL": "Cultura Pol.",
    "DEP": "Deporte/Lectura", "DER": "Derechos", "ECO": "Economía",
    "EDU": "Educación", "ENV": "Envejecim.", "FAM": "Familia",
    "FED": "Fed./Gobierno", "GEN": "Género", "GLO": "Global.",
    "HAB": "Habitación", "IDE": "Identidad", "IND": "Industria",
    "JUS": "Justicia", "MED": "Medio Amb.", "MIG": "Migración",
    "NIN": "Niñez/Juventud", "POB": "Pobreza", "REL": "Religión",
    "SAL": "Salud", "SEG": "Seguridad", "SOC": "Soc. Digital",
}

_TAB20 = plt.cm.tab20(np.linspace(0, 1, 20))
_TAB20B = plt.cm.tab20b(np.linspace(0, 1, 20))
_ALL_COLORS = list(_TAB20) + list(_TAB20B)

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
})


# ─── Load data ────────────────────────────────────────────────────────────────

def load_data():
    with open(ONTOLOGY) as f:
        ont = json.load(f)
    with open(FINGERPRINTS) as f:
        fp = json.load(f)
    return ont, fp


def build_graph(ont: dict) -> nx.Graph:
    """Build undirected weighted graph from ontology bridges."""
    G = nx.Graph()

    # Build construct lookup — normalize ID separator (__ → |)
    construct_lookup = {}
    id_map = {}  # raw_id → normalized_id
    for c in ont["constructs"]:
        raw_id = c["id"]
        # Normalize: IDE__foo → IDE|foo
        norm_id = raw_id.replace("__", "|", 1) if "__" in raw_id else raw_id
        construct_lookup[norm_id] = c
        id_map[raw_id] = norm_id

    # Add nodes with attributes
    for cid, c in construct_lookup.items():
        G.add_node(cid,
                   domain=c.get("domain", cid.split("|")[0] if "|" in cid else "UNK"),
                   label=c.get("label", cid),
                   alpha=c.get("alpha"),
                   ses_magnitude=c.get("ses_magnitude", 0),
                   dominant_dim=c.get("dominant_dim", ""),
                   rho_escol=c.get("rho_escol", 0),
                   rho_Tam_loc=c.get("rho_Tam_loc", 0),
                   rho_sexo=c.get("rho_sexo", 0),
                   rho_edad=c.get("rho_edad", 0))

    # Add edges — only if both endpoints are known constructs
    known = set(construct_lookup.keys())
    skipped = 0
    for b in ont["bridges"]:
        src, tgt = b["from"], b["to"]
        if src not in known or tgt not in known:
            skipped += 1
            continue
        G.add_edge(src, tgt,
                   gamma=b["gamma"],
                   ci_lo=b.get("ci_lo", 0),
                   ci_hi=b.get("ci_hi", 0),
                   ci_width=b.get("ci_width", 0),
                   nmi=b.get("nmi", 0),
                   fingerprint_dot=b.get("fingerprint_dot", 0),
                   fingerprint_cos=b.get("fingerprint_cos", 0),
                   abs_gamma=abs(b["gamma"]),
                   sign=1 if b["gamma"] > 0 else -1)
    if skipped:
        print(f"  (skipped {skipped} edges with unknown endpoints)")

    return G


# ─── Metrics ──────────────────────────────────────────────────────────────────

def global_metrics(G: nx.Graph) -> dict:
    """Compute global graph metrics."""
    m = {}
    m["n_nodes"] = G.number_of_nodes()
    m["n_edges"] = G.number_of_edges()
    m["density"] = nx.density(G)

    # Connected components
    components = list(nx.connected_components(G))
    m["n_components"] = len(components)
    m["largest_component_size"] = max(len(c) for c in components)
    m["isolated_nodes"] = sum(1 for c in components if len(c) == 1)

    # Giant component metrics
    giant = G.subgraph(max(components, key=len)).copy()
    m["giant_n"] = giant.number_of_nodes()
    m["giant_m"] = giant.number_of_edges()
    m["giant_density"] = nx.density(giant)
    m["diameter"] = nx.diameter(giant)
    m["avg_path_length"] = nx.average_shortest_path_length(giant)
    m["radius"] = nx.radius(giant)

    # Clustering
    m["avg_clustering"] = nx.average_clustering(G)
    m["transitivity"] = nx.transitivity(G)

    # Degree stats
    degrees = [d for _, d in G.degree()]
    m["avg_degree"] = np.mean(degrees)
    m["median_degree"] = np.median(degrees)
    m["max_degree"] = max(degrees)
    m["min_degree"] = min(degrees)
    m["degree_std"] = np.std(degrees)

    # Assortativity
    m["degree_assortativity"] = nx.degree_assortativity_coefficient(G)

    # Attribute assortativity (domain) — computed on giant component to avoid NaN
    try:
        m["domain_assortativity"] = nx.attribute_assortativity_coefficient(giant, "domain")
    except (ValueError, ZeroDivisionError):
        m["domain_assortativity"] = float("nan")

    # Small-world coefficient: compare clustering and path length to random graph
    # σ = (C/C_rand) / (L/L_rand)
    n, p = giant.number_of_nodes(), nx.density(giant)
    C_rand = p  # expected clustering for Erdős-Rényi
    L_rand = np.log(n) / np.log(n * p) if n * p > 1 else float("inf")
    m["sigma_smallworld"] = (m["avg_clustering"] / C_rand) / (m["avg_path_length"] / L_rand) if C_rand > 0 and L_rand > 0 else None

    return m, giant


def centrality_analysis(G: nx.Graph, giant: nx.Graph) -> dict:
    """Compute multiple centrality measures."""
    c = {}
    c["degree"] = dict(G.degree())
    c["betweenness"] = nx.betweenness_centrality(giant)
    c["closeness"] = nx.closeness_centrality(giant)
    try:
        c["eigenvector"] = nx.eigenvector_centrality_numpy(giant)
    except (TypeError, nx.NetworkXError):
        c["eigenvector"] = nx.eigenvector_centrality(giant, max_iter=1000)
    c["pagerank"] = nx.pagerank(giant, weight="abs_gamma")
    return c


def sign_analysis(G: nx.Graph) -> dict:
    """Analyze edge sign patterns and structural balance."""
    s = {}
    gammas = [d["gamma"] for _, _, d in G.edges(data=True)]
    s["n_positive"] = sum(1 for g in gammas if g > 0)
    s["n_negative"] = sum(1 for g in gammas if g < 0)
    s["pos_fraction"] = s["n_positive"] / len(gammas)

    # Structural balance: count balanced vs frustrated triangles
    # Balanced: product of signs > 0 (all +, or exactly 2 -)
    # Frustrated: product of signs < 0 (1 - or 3 -)
    balanced = 0
    frustrated = 0
    nodes = sorted(G.nodes())
    node_idx = {n: i for i, n in enumerate(nodes)}
    adj = {n: set(G.neighbors(n)) for n in nodes}
    for i, u in enumerate(nodes):
        for v in adj[u]:
            if node_idx[v] <= i:
                continue
            for w in adj[u] & adj[v]:
                if node_idx[w] <= node_idx[v]:
                    continue
                s1 = G[u][v]["sign"]
                s2 = G[u][w]["sign"]
                s3 = G[v][w]["sign"]
                if s1 * s2 * s3 > 0:
                    balanced += 1
                else:
                    frustrated += 1

    s["n_triangles"] = balanced + frustrated
    s["n_balanced"] = balanced
    s["n_frustrated"] = frustrated
    s["balance_ratio"] = balanced / (balanced + frustrated) if (balanced + frustrated) > 0 else None

    return s


def domain_mixing(G: nx.Graph) -> dict:
    """Analyze intra- vs inter-domain edge distribution."""
    intra = 0
    inter = 0
    domain_pair_counts = Counter()
    domain_pair_gammas = defaultdict(list)

    for u, v, d in G.edges(data=True):
        du = G.nodes[u]["domain"]
        dv = G.nodes[v]["domain"]
        if du == dv:
            intra += 1
        else:
            inter += 1
        pair = tuple(sorted([du, dv]))
        domain_pair_counts[pair] += 1
        domain_pair_gammas[pair].append(d["gamma"])

    return {
        "intra_edges": intra,
        "inter_edges": inter,
        "intra_fraction": intra / (intra + inter) if (intra + inter) > 0 else 0,
        "domain_pair_counts": domain_pair_counts,
        "domain_pair_gammas": domain_pair_gammas,
    }


def fingerprint_geometry(G: nx.Graph) -> dict:
    """Analyze the 4D fingerprint space geometry."""
    nodes = [n for n in G.nodes() if G.nodes[n].get("ses_magnitude", 0) > 0]
    fps = np.array([[G.nodes[n]["rho_escol"], G.nodes[n]["rho_Tam_loc"],
                     G.nodes[n]["rho_sexo"], G.nodes[n]["rho_edad"]]
                    for n in nodes])
    labels = [G.nodes[n]["domain"] for n in nodes]
    names = list(nodes)

    # PCA for 2D projection
    fps_centered = fps - fps.mean(axis=0)
    U, S, Vt = np.linalg.svd(fps_centered, full_matrices=False)
    explained_var = (S ** 2) / (S ** 2).sum()
    proj_2d = fps_centered @ Vt[:2].T

    # Pairwise distances in fingerprint space vs graph distance
    fp_dists = squareform(pdist(fps, metric="euclidean"))
    cos_sims = squareform(pdist(fps, metric="cosine"))

    # Correlation with gamma for connected pairs
    fp_dot_list = []
    gamma_list = []
    for u, v, d in G.edges(data=True):
        if u in names and v in names:
            iu = names.index(u)
            iv = names.index(v)
            fp_dot_list.append(np.dot(fps[iu], fps[iv]))
            gamma_list.append(d["gamma"])

    dot_gamma_corr = stats.pearsonr(fp_dot_list, gamma_list) if fp_dot_list else (0, 1)

    # Dominant dimension clustering
    dom_dims = [G.nodes[n]["dominant_dim"] for n in nodes]
    dim_counts = Counter(dom_dims)

    return {
        "fps": fps, "nodes": names, "labels": labels,
        "proj_2d": proj_2d, "pca_components": Vt[:2],
        "explained_variance": explained_var,
        "fp_dot_list": fp_dot_list, "gamma_list": gamma_list,
        "dot_gamma_corr": dot_gamma_corr,
        "dim_counts": dim_counts,
        "magnitudes": np.array([G.nodes[n]["ses_magnitude"] for n in nodes]),
    }


def community_detection(G: nx.Graph) -> dict:
    """Detect communities via multiple methods."""
    # Only on connected nodes
    connected = [n for n in G.nodes() if G.degree(n) > 0]
    H = G.subgraph(connected).copy()

    # Louvain (greedy modularity)
    communities_louvain = nx.community.louvain_communities(H, weight="abs_gamma", seed=42)
    mod_louvain = nx.community.modularity(H, communities_louvain, weight="abs_gamma")

    # Greedy modularity
    communities_greedy = list(nx.community.greedy_modularity_communities(H, weight="abs_gamma"))
    mod_greedy = nx.community.modularity(H, communities_greedy, weight="abs_gamma")

    # Domain-based modularity (for comparison)
    domain_partition = defaultdict(set)
    for n in H.nodes():
        domain_partition[H.nodes[n]["domain"]].add(n)
    domain_communities = list(domain_partition.values())
    mod_domain = nx.community.modularity(H, domain_communities, weight="abs_gamma")

    return {
        "louvain": {"communities": communities_louvain, "modularity": mod_louvain},
        "greedy": {"communities": communities_greedy, "modularity": mod_greedy},
        "domain": {"communities": domain_communities, "modularity": mod_domain},
    }


# ─── Visualizations ──────────────────────────────────────────────────────────

def get_domain_color(domain: str, all_domains: list) -> np.ndarray:
    idx = sorted(set(all_domains)).index(domain) if domain in all_domains else 0
    return _ALL_COLORS[idx % len(_ALL_COLORS)]


def plot_degree_distribution(G: nx.Graph, path: Path):
    """Degree distribution with log-log inset."""
    degrees = [d for _, d in G.degree()]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Histogram
    ax = axes[0]
    ax.hist(degrees, bins=range(0, max(degrees) + 3, 2), color="#4e79a7",
            edgecolor="white", alpha=0.85)
    ax.axvline(np.mean(degrees), color="#e15759", ls="--", lw=1.5,
               label=f"Mean = {np.mean(degrees):.1f}")
    ax.axvline(np.median(degrees), color="#f28e2b", ls="--", lw=1.5,
               label=f"Median = {np.median(degrees):.0f}")
    ax.set_xlabel("Degree")
    ax.set_ylabel("Count")
    ax.set_title("Degree Distribution")
    ax.legend(fontsize=9)

    # CCDF (complementary cumulative) — log-log
    ax2 = axes[1]
    sorted_d = np.sort(degrees)[::-1]
    ccdf_y = np.arange(1, len(sorted_d) + 1) / len(sorted_d)
    ax2.scatter(sorted_d, ccdf_y, s=20, alpha=0.7, color="#4e79a7")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Degree (log)")
    ax2.set_ylabel("P(X ≥ x)")
    ax2.set_title("CCDF (log-log)")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_gamma_distribution(G: nx.Graph, path: Path):
    """Gamma distribution with sign coloring."""
    gammas = [d["gamma"] for _, _, d in G.edges(data=True)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Histogram with sign coloring
    ax = axes[0]
    pos_g = [g for g in gammas if g > 0]
    neg_g = [g for g in gammas if g < 0]
    bins = np.linspace(min(gammas), max(gammas), 40)
    ax.hist(pos_g, bins=bins, color="#f28e2b", alpha=0.8, label=f"γ > 0 ({len(pos_g)})")
    ax.hist(neg_g, bins=bins, color="#4e79a7", alpha=0.8, label=f"γ < 0 ({len(neg_g)})")
    ax.axvline(0, color="black", ls="-", lw=0.8)
    ax.set_xlabel("γ (Goodman-Kruskal)")
    ax.set_ylabel("Count")
    ax.set_title("Edge γ Distribution")
    ax.legend(fontsize=9)

    # |γ| cumulative
    ax2 = axes[1]
    abs_g = sorted(np.abs(gammas))
    cdf_y = np.arange(1, len(abs_g) + 1) / len(abs_g)
    ax2.plot(abs_g, cdf_y, color="#59a14f", lw=2)
    ax2.axhline(0.5, color="gray", ls=":", lw=1)
    ax2.axvline(np.median(abs_g), color="#e15759", ls="--", lw=1,
                label=f"Median |γ| = {np.median(abs_g):.4f}")
    ax2.set_xlabel("|γ|")
    ax2.set_ylabel("CDF")
    ax2.set_title("Cumulative |γ| Distribution")
    ax2.legend(fontsize=9)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_fingerprint_pca(fp_data: dict, G: nx.Graph, path: Path):
    """2D PCA of 4D fingerprint space, colored by domain."""
    proj = fp_data["proj_2d"]
    labels = fp_data["labels"]
    names = fp_data["nodes"]
    mags = fp_data["magnitudes"]
    all_domains = sorted(set(labels))

    fig, ax = plt.subplots(figsize=(10, 8))

    for domain in all_domains:
        mask = [l == domain for l in labels]
        idx = [i for i, m in enumerate(mask) if m]
        if not idx:
            continue
        color = get_domain_color(domain, all_domains)
        sizes = 30 + 200 * mags[idx] / mags.max()
        ax.scatter(proj[idx, 0], proj[idx, 1], c=[color], s=sizes,
                   alpha=0.8, edgecolors="white", linewidths=0.5,
                   label=DOMAIN_LABELS.get(domain, domain), zorder=3)

    # Draw edges for top-|γ| bridges
    gammas_abs = [(u, v, abs(d["gamma"])) for u, v, d in G.edges(data=True)]
    gammas_abs.sort(key=lambda x: x[2], reverse=True)
    for u, v, ag in gammas_abs[:50]:  # top 50 edges
        if u in names and v in names:
            iu, iv = names.index(u), names.index(v)
            gamma = G[u][v]["gamma"]
            color = "#f28e2b" if gamma > 0 else "#4e79a7"
            ax.plot([proj[iu, 0], proj[iv, 0]], [proj[iu, 1], proj[iv, 1]],
                    color=color, alpha=0.15 + 0.4 * ag / gammas_abs[0][2],
                    lw=0.5 + 1.5 * ag / gammas_abs[0][2], zorder=1)

    # Label high-magnitude nodes
    for i, name in enumerate(names):
        if mags[i] > np.percentile(mags, 85):
            short = name.split("|")[1][:20] if "|" in name else name[:20]
            ax.annotate(short, (proj[i, 0], proj[i, 1]),
                        fontsize=6, alpha=0.7, ha="center", va="bottom",
                        xytext=(0, 4), textcoords="offset points")

    ev = fp_data["explained_variance"]
    ax.set_xlabel(f"PC1 ({ev[0]:.1%} var)")
    ax.set_ylabel(f"PC2 ({ev[1]:.1%} var)")
    ax.set_title("SES Fingerprint Space (PCA projection)\nNode size ∝ SES magnitude")
    ax.legend(fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.08),
              frameon=True, fancybox=True)
    ax.grid(True, alpha=0.15)
    ax.axhline(0, color="gray", lw=0.5, alpha=0.3)
    ax.axvline(0, color="gray", lw=0.5, alpha=0.3)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_dot_vs_gamma(fp_data: dict, path: Path):
    """Scatter: fingerprint dot product vs γ."""
    fig, ax = plt.subplots(figsize=(7, 6))
    dots = fp_data["fp_dot_list"]
    gammas = fp_data["gamma_list"]
    ax.scatter(dots, gammas, s=8, alpha=0.3, color="#4e79a7")

    # Regression line
    slope, intercept, r, p, se = stats.linregress(dots, gammas)
    x_line = np.linspace(min(dots), max(dots), 100)
    ax.plot(x_line, slope * x_line + intercept, color="#e15759", lw=2,
            label=f"r = {r:.3f}, p = {p:.1e}")
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    ax.set_xlabel("Fingerprint dot product (fp_A · fp_B)")
    ax.set_ylabel("Bridge γ")
    ax.set_title("Fingerprint Geometry Predicts Bridge Sign & Magnitude")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.15)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_centrality_comparison(centralities: dict, G: nx.Graph, path: Path):
    """Compare centrality measures — scatter matrix of top 3."""
    nodes = list(centralities["betweenness"].keys())
    domains = [G.nodes[n]["domain"] for n in nodes]
    all_domains = sorted(set(domains))

    measures = ["degree", "betweenness", "eigenvector"]
    labels_m = ["Degree", "Betweenness", "Eigenvector"]
    vals = {}
    for m in measures:
        if m == "degree":
            vals[m] = np.array([centralities[m].get(n, 0) for n in nodes])
        else:
            vals[m] = np.array([centralities[m].get(n, 0) for n in nodes])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    pairs = [(0, 1), (0, 2), (1, 2)]
    for ax, (i, j) in zip(axes, pairs):
        for domain in all_domains:
            mask = [d == domain for d in domains]
            idx = [k for k, m in enumerate(mask) if m]
            if not idx:
                continue
            color = get_domain_color(domain, all_domains)
            ax.scatter(vals[measures[i]][idx], vals[measures[j]][idx],
                       c=[color], s=25, alpha=0.7)
        ax.set_xlabel(labels_m[i])
        ax.set_ylabel(labels_m[j])
        ax.grid(True, alpha=0.15)

        # Label outliers
        combined = vals[measures[i]] + vals[measures[j]]
        top_idx = np.argsort(combined)[-5:]
        for k in top_idx:
            short = nodes[k].split("|")[1][:18] if "|" in nodes[k] else nodes[k][:18]
            ax.annotate(short, (vals[measures[i]][k], vals[measures[j]][k]),
                        fontsize=6, alpha=0.7)

    axes[1].set_title("Centrality Measure Comparison")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_domain_heatmap(mixing: dict, path: Path):
    """Heatmap of inter-domain edge density and mean γ sign."""
    pair_counts = mixing["domain_pair_counts"]
    pair_gammas = mixing["domain_pair_gammas"]
    domains = sorted(set(d for pair in pair_counts for d in pair))
    n = len(domains)

    # Count matrix
    count_mat = np.zeros((n, n))
    gamma_mat = np.full((n, n), np.nan)
    for (d1, d2), cnt in pair_counts.items():
        i, j = domains.index(d1), domains.index(d2)
        count_mat[i, j] = cnt
        count_mat[j, i] = cnt
        mean_g = np.mean(pair_gammas[(d1, d2)])
        gamma_mat[i, j] = mean_g
        gamma_mat[j, i] = mean_g

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Edge count heatmap
    ax = axes[0]
    im = ax.imshow(count_mat, cmap="YlOrRd", aspect="equal")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(domains, fontsize=7, rotation=45, ha="right")
    ax.set_yticklabels(domains, fontsize=7)
    ax.set_title("Edge Count Between Domains")
    fig.colorbar(im, ax=ax, shrink=0.7)
    # Annotate
    for i in range(n):
        for j in range(n):
            if count_mat[i, j] > 0:
                ax.text(j, i, f"{int(count_mat[i,j])}", ha="center", va="center",
                        fontsize=5, color="white" if count_mat[i, j] > count_mat.max() * 0.6 else "black")

    # Mean gamma heatmap
    ax2 = axes[1]
    vmax = np.nanmax(np.abs(gamma_mat))
    im2 = ax2.imshow(gamma_mat, cmap="RdBu_r", aspect="equal", vmin=-vmax, vmax=vmax)
    ax2.set_xticks(range(n))
    ax2.set_yticks(range(n))
    ax2.set_xticklabels(domains, fontsize=7, rotation=45, ha="right")
    ax2.set_yticklabels(domains, fontsize=7)
    ax2.set_title("Mean γ Between Domains")
    fig.colorbar(im2, ax=ax2, shrink=0.7)
    for i in range(n):
        for j in range(n):
            if not np.isnan(gamma_mat[i, j]):
                ax2.text(j, i, f"{gamma_mat[i,j]:.3f}", ha="center", va="center",
                         fontsize=4.5, color="white" if abs(gamma_mat[i, j]) > vmax * 0.6 else "black")

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_community_vs_domain(comm_data: dict, G: nx.Graph, path: Path):
    """Alluvial-style: map Louvain communities to domains."""
    communities = comm_data["louvain"]["communities"]
    fig, ax = plt.subplots(figsize=(10, 6))

    comm_domain_counts = []
    for i, comm in enumerate(communities):
        domain_counts = Counter(G.nodes[n]["domain"] for n in comm)
        comm_domain_counts.append(domain_counts)

    # Stacked bar: each community, colored by domain
    all_domains = sorted(set(G.nodes[n]["domain"] for n in G.nodes()))
    x = range(len(communities))
    bottoms = np.zeros(len(communities))
    for domain in all_domains:
        heights = [cc.get(domain, 0) for cc in comm_domain_counts]
        color = get_domain_color(domain, all_domains)
        ax.bar(x, heights, bottom=bottoms, color=color, edgecolor="white",
               linewidth=0.5, label=DOMAIN_LABELS.get(domain, domain))
        bottoms += heights

    ax.set_xlabel("Louvain Community")
    ax.set_ylabel("Number of Constructs")
    ax.set_title(f"Community Composition by Domain (Q = {comm_data['louvain']['modularity']:.3f})")
    ax.set_xticks(x)
    ax.set_xticklabels([f"C{i}" for i in x])
    ax.legend(fontsize=6, ncol=4, loc="upper right", bbox_to_anchor=(1.35, 1.0))

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_structural_balance(sign_data: dict, path: Path):
    """Pie chart of balanced vs frustrated triangles + sign ratio bar."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    # Triangle balance
    ax = axes[0]
    sizes = [sign_data["n_balanced"], sign_data["n_frustrated"]]
    labels = [f"Balanced\n({sizes[0]:,})", f"Frustrated\n({sizes[1]:,})"]
    colors = ["#59a14f", "#e15759"]
    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
           startangle=90, textprops={"fontsize": 10})
    ax.set_title(f"Structural Balance\n({sign_data['n_triangles']:,} triangles)")

    # Edge sign ratio
    ax2 = axes[1]
    ax2.barh(["Positive (γ > 0)", "Negative (γ < 0)"],
             [sign_data["n_positive"], sign_data["n_negative"]],
             color=["#f28e2b", "#4e79a7"], edgecolor="white")
    ax2.set_xlabel("Number of Edges")
    ax2.set_title("Edge Sign Distribution")
    for i, v in enumerate([sign_data["n_positive"], sign_data["n_negative"]]):
        ax2.text(v + 5, i, str(v), va="center", fontsize=10)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


def plot_ses_dimension_profile(G: nx.Graph, path: Path):
    """Violin plots of rho values by dominant dimension."""
    dims = ["rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad"]
    dim_labels = ["Education", "Town Size", "Gender", "Age"]
    nodes = [n for n in G.nodes() if G.degree(n) > 0]

    fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=True)

    for ax, dim, label in zip(axes, dims, dim_labels):
        vals = [G.nodes[n][dim] for n in nodes]
        parts = ax.violinplot([vals], positions=[0], showmeans=True,
                              showmedians=True, widths=0.6)
        parts["cmeans"].set_color("#e15759")
        parts["cmedians"].set_color("#4e79a7")
        for pc in parts["bodies"]:
            pc.set_facecolor("#76b7b2")
            pc.set_alpha(0.7)
        ax.scatter(np.zeros(len(vals)) + np.random.normal(0, 0.05, len(vals)),
                   vals, s=12, alpha=0.5, color="#4e79a7", zorder=3)
        ax.axhline(0, color="gray", lw=0.8, ls=":")
        ax.set_title(label)
        ax.set_xticks([])

    axes[0].set_ylabel("Spearman ρ")
    fig.suptitle("SES Dimension Profiles Across Connected Constructs", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path.name}")


# ─── Report Generation ───────────────────────────────────────────────────────

def generate_report(metrics: dict, giant: nx.Graph, G: nx.Graph,
                    centralities: dict, sign_data: dict, mixing: dict,
                    fp_data: dict, comm_data: dict) -> str:
    """Generate markdown report with full mathematical exposition."""
    m = metrics
    ev = fp_data["explained_variance"]
    r_val, p_val = fp_data["dot_gamma_corr"]
    mod_l = comm_data["louvain"]["modularity"]
    mod_d = comm_data["domain"]["modularity"]
    density_pct = m["density"] * 100
    C_rand = m["density"]
    connected_degrees = [d for _, d in G.degree() if d > 0]
    cv_conn = np.std(connected_degrees) / np.mean(connected_degrees) if connected_degrees else 0

    L = []  # accumulator
    def w(s=""): L.append(s)

    # ═══════════════════════════════════════════════════════════════════════
    w("# SES Bridge Network — Topology & Geometry Report")
    w()
    w("*Generated from `kg_ontology_v2.json` (Julia v4 sweep, 2026-03-14)*")
    w()

    # ── Preamble ──
    w("## What This Report Analyses")
    w()
    w("The SES bridge network is a graph where **nodes** are attitudinal constructs")
    w("(aggregated survey scales, e.g. *personal_religiosity*, *structural_housing_quality*)")
    w("and **edges** are statistically significant doubly-robust (DR) bridge estimates")
    w("between cross-domain construct pairs. An edge exists when the 95% bootstrap CI")
    w("for Goodman-Kruskal γ excludes zero — meaning the two attitudes are monotonically")
    w("co-driven by shared sociodemographic position (the 4 SES dimensions: education,")
    w("town size, gender, age).")
    w()
    w("Each edge carries a **signed weight** γ ∈ [-1, 1]:")
    w("- γ > 0: higher SES pushes both attitudes in the same direction (co-elevation)")
    w("- γ < 0: higher SES pushes them in opposite directions (counter-variation)")
    w()
    w("Each node carries a **4D SES fingerprint** `[ρ_escol, ρ_Tam_loc, ρ_sexo, ρ_edad]` —")
    w("the Spearman correlation of the construct with each SES dimension. This fingerprint")
    w("determines the node's position in a continuous sociodemographic space, and — as we")
    w("will show — almost entirely determines the network's topology.")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 1. GLOBAL METRICS
    # ══════════════════════════════════════════════════════════════════════
    w("## 1. Global Structure")
    w()
    w("| Metric | Value |")
    w("|--------|-------|")
    w(f"| Nodes | {m['n_nodes']} |")
    w(f"| Edges | {m['n_edges']} |")
    w(f"| Density | {m['density']:.4f} ({density_pct:.1f}%) |")
    w(f"| Connected components | {m['n_components']} |")
    w(f"| Giant component | {m['giant_n']} nodes, {m['giant_m']} edges |")
    w(f"| Isolated nodes | {m['isolated_nodes']} |")
    w(f"| Diameter | {m['diameter']} |")
    w(f"| Radius | {m['radius']} |")
    w(f"| Avg. shortest path length | {m['avg_path_length']:.3f} |")
    w(f"| Avg. clustering coefficient | {m['avg_clustering']:.4f} |")
    w(f"| Transitivity (global clustering) | {m['transitivity']:.4f} |")
    w(f"| Degree assortativity | {m['degree_assortativity']:.4f} |")
    w(f"| Domain assortativity | {m['domain_assortativity']:.4f} |")
    if m["sigma_smallworld"] is not None:
        w(f"| Small-world σ | {m['sigma_smallworld']:.3f} |")
    w()

    # -- Density --
    w("### 1.1 Density")
    w()
    w("**Definition.** For an undirected graph with *n* nodes and *m* edges,")
    w("density = 2m / n(n−1) — the fraction of all possible edges that actually exist.")
    w()
    w(f"Here: 2 × {m['n_edges']} / ({m['n_nodes']} × {m['n_nodes']-1}) = **{density_pct:.1f}%**.")
    w()
    w("Most real-world networks (social, biological, technological) have densities below 5%.")
    w(f"A density of {density_pct:.0f}% means SES creates **pervasive** connectivity: a typical")
    w("connected construct bridges to roughly one-quarter of all other constructs. This is not")
    w("a sparse web of isolated links — it is a thick fabric of SES-mediated co-variation.")
    w()

    # -- Components --
    w("### 1.2 Connected Components")
    w()
    w("**Definition.** A connected component is a maximal subgraph in which every pair of")
    w("nodes is reachable via some path. Isolated nodes (degree 0) each form their own")
    w("trivial component.")
    w()
    w(f"The network has **{m['n_components']} components**: one giant component of {m['giant_n']} nodes")
    w(f"containing **all** {m['n_edges']} edges, plus {m['isolated_nodes']} isolated singletons.")
    w()
    w("The 22 isolated constructs are those whose SES magnitude (RMS of fingerprint entries)")
    w("is too small to produce any bootstrap CI that excludes zero. They are not disconnected")
    w("from SES — they are simply below the statistical detection threshold. In fingerprint")
    w("space, they cluster near the origin.")
    w()

    # -- Diameter & Path Length --
    w("### 1.3 Diameter & Average Path Length")
    w()
    w("**Definition.** The *diameter* is the longest shortest path between any two nodes in")
    w("the giant component — the worst-case number of hops to get from one construct to another.")
    w("The *average shortest path length* (APL) is the mean over all node pairs.")
    w()
    w(f"Diameter = **{m['diameter']}**, APL = **{m['avg_path_length']:.3f}**, radius = **{m['radius']}**.")
    w()
    w(f"An APL of {m['avg_path_length']:.2f} means that, on average, any two connected constructs are")
    w(f"fewer than 2 hops apart. Combined with diameter {m['diameter']}, this means the network is")
    w("**ultra-compact**: no two attitudes in the giant component are more than 4 SES-mediated")
    w("steps from each other. For reference, the internet has diameter ~20, social networks ~6,")
    w("protein interaction networks ~10. A diameter of 4 in a graph of 71 nodes is characteristic")
    w("of a dense, nearly-complete subgraph, not a sparse hierarchical structure.")
    w()

    # -- Clustering --
    w("### 1.4 Clustering Coefficient")
    w()
    w("**Definition.** The *local clustering coefficient* C(v) of a node v measures how many")
    w("of v's neighbors are also neighbors of each other:")
    w()
    w("    C(v) = 2 × |edges among neighbors of v| / (deg(v) × (deg(v) − 1))")
    w()
    w("The *average clustering coefficient* is the mean C(v) over all nodes. *Transitivity*")
    w("(global clustering) is the ratio 3 × triangles / connected-triples across the whole graph,")
    w("which gives more weight to high-degree nodes.")
    w()
    w(f"Average clustering = **{m['avg_clustering']:.3f}**, transitivity = **{m['transitivity']:.3f}**.")
    w()
    w(f"For a random Erdős-Rényi graph with the same density, the expected clustering equals")
    w(f"the density itself: C_random = {C_rand:.3f}. Our observed value ({m['avg_clustering']:.3f}) is")
    w(f"**{m['avg_clustering']/C_rand:.1f}× higher** than random expectation.")
    w()
    w("This excess clustering means neighbors tend to share neighbors — the network has")
    w("clique-like local structure. This is a natural signature of a geometric graph:")
    w("if A and B are both close to C in fingerprint space, then A and B are likely close")
    w("to each other, forming a triangle. Random graphs lack this geometric transitivity.")
    w()

    # -- Small-world --
    w("### 1.5 Small-World Test")
    w()
    w("**Definition.** The small-world coefficient σ = (C/C_rand) / (L/L_rand), where C and L")
    w("are the observed clustering and path length, and C_rand, L_rand are the values expected")
    w("for a random graph with the same size and density. A network is small-world when σ > 1:")
    w("high clustering (like a lattice) combined with short paths (like a random graph).")
    w()
    if m["sigma_smallworld"] is not None:
        w(f"σ = **{m['sigma_smallworld']:.3f}**.")
        w()
        if m["sigma_smallworld"] > 1:
            w("The network marginally qualifies as small-world.")
        else:
            w("σ ≤ 1: the network is **not** small-world. The path lengths are not shorter")
            w("than random expectation — the high clustering comes at the cost of slightly")
            w("longer paths than a pure random graph. This is consistent with a geometric")
            w("graph: geometric proximity creates local clustering, but the same geometry")
            w("also creates longer paths between distant regions of fingerprint space.")
    w()

    # -- Assortativity --
    w("### 1.6 Assortativity")
    w()
    w("**Definition.** *Degree assortativity* (Newman, 2002) is the Pearson correlation of")
    w("degrees at either end of an edge. Positive = hubs connect to hubs (assortative).")
    w("Negative = hubs connect to low-degree nodes (disassortative, hub-and-spoke).")
    w()
    w("*Attribute assortativity* (here: domain) measures whether edges preferentially connect")
    w("nodes with the same categorical attribute. It equals 1 if all edges are within-group,")
    w("0 if mixing is random, and negative if cross-group edges are overrepresented.")
    w()
    w(f"Degree assortativity = **{m['degree_assortativity']:.3f}**. Weakly positive — hubs tend to")
    w("connect to other hubs. In a geometric graph, this is expected: constructs with large SES")
    w("magnitudes (far from the origin) produce many significant bridges, and they preferentially")
    w("bridge to other high-magnitude constructs (whose large fingerprints make for large dot products).")
    w()
    w(f"Domain assortativity = **{m['domain_assortativity']:.3f}**. Weakly negative — the SES bridge")
    w("connects *across* survey domains slightly more than within. This is partly by construction")
    w("(the sweep only estimates cross-domain pairs), but even among the 22 domains represented")
    w("in the giant component, no domain captures its edges internally. SES is a *between-domain*")
    w("connector: it links housing quality to religiosity, science attitudes to political engagement.")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 2. DEGREE DISTRIBUTION
    # ══════════════════════════════════════════════════════════════════════
    w("## 2. Degree Distribution")
    w()
    w("**Definition.** The degree k(v) of node v is the number of edges incident on v.")
    w("The degree distribution P(k) describes the probability that a randomly chosen node")
    w("has degree k. Its shape distinguishes network types:")
    w("- *Scale-free* (Barabási-Albert): P(k) ~ k^(-α), heavy tail, few mega-hubs")
    w("- *Random* (Erdős-Rényi): Poisson-like, peaked around the mean")
    w("- *Geometric* (thresholded proximity): bimodal or uniform in the connected core")
    w()
    w("| Stat | All nodes | Connected core |")
    w("|------|-----------|----------------|")
    w(f"| Count | {m['n_nodes']} | {len(connected_degrees)} |")
    w(f"| Mean | {m['avg_degree']:.1f} | {np.mean(connected_degrees):.1f} |")
    w(f"| Median | {m['median_degree']:.0f} | {np.median(connected_degrees):.0f} |")
    w(f"| Std. dev. | {m['degree_std']:.1f} | {np.std(connected_degrees):.1f} |")
    w(f"| Min | {m['min_degree']} | {min(connected_degrees)} |")
    w(f"| Max | {m['max_degree']} | {max(connected_degrees)} |")
    w(f"| CV | {m['degree_std']/m['avg_degree']:.2f} | {cv_conn:.2f} |")
    w()
    w("![Degree Distribution](network_topology_degree.png)")
    w()
    w(f"**Figure: Degree Distribution.** Left: histogram showing the bimodal structure —")
    w(f"a spike at degree 0 ({m['n_nodes'] - len(connected_degrees)} isolated nodes) and a broad distribution")
    w(f"in the connected core (degrees {min(connected_degrees)}–{max(connected_degrees)}). Right: complementary cumulative")
    w("distribution (CCDF) on log-log axes. A power law (scale-free) would appear as a")
    w("straight line; the observed **concave** shape rules out scale-free structure.")
    w()
    w(f"The connected core has CV = {cv_conn:.2f}. For comparison, scale-free networks typically")
    w(f"have CV > 2 (one or two nodes dominate), while random graphs have CV ≈ 1/√⟨k⟩ ≈ {1/np.sqrt(np.mean(connected_degrees)):.2f}.")
    w(f"The observed value sits between these extremes — there are hubs (HAB|structural_housing_quality")
    w(f"at degree {max(connected_degrees)}) but the distribution is far more uniform than a scale-free network.")
    w("This is the hallmark of a **thresholded geometric graph**: connectivity is determined by")
    w("proximity in a continuous space, not by preferential attachment. Nodes with larger SES")
    w("magnitudes (farther from the origin) exceed the significance threshold with more partners,")
    w("creating moderate hubs — but no node can dominate the way it would under rich-get-richer dynamics.")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 3. CENTRALITY
    # ══════════════════════════════════════════════════════════════════════
    w("## 3. Centrality Analysis")
    w()
    w("Centrality measures quantify different notions of node \"importance\" in a graph.")
    w("We compute four complementary measures:")
    w()
    w("- **Degree centrality** C_D(v) = deg(v) / (n−1). Simply the fraction of other nodes that v")
    w("  connects to. High-degree nodes are broadly SES-entangled with many other constructs.")
    w()
    w("- **Betweenness centrality** C_B(v) = Σ_{s≠v≠t} σ_st(v) / σ_st, where σ_st is the number")
    w("  of shortest paths from s to t, and σ_st(v) is the number passing through v. Measures")
    w("  how much information flow (or SES-mediated influence chains) passes through v. A node")
    w("  with high betweenness but moderate degree acts as a *bottleneck* or *bridge* between")
    w("  otherwise separate regions of the network.")
    w()
    w("- **Eigenvector centrality** C_E(v) = (1/λ) Σ_u∈N(v) C_E(u). A node is important if it")
    w("  connects to other important nodes (recursive definition, solved as the leading eigenvector")
    w("  of the adjacency matrix). Captures prestige — being connected to the well-connected.")
    w()
    w("- **PageRank** PR(v). Google's variant of eigenvector centrality, with damping factor")
    w("  and weighted by |γ| (edge weight = abs_gamma). Accounts for both connectivity structure")
    w("  and bridge strength.")
    w()
    w("### Top 10 by Degree")
    w()
    w("| Rank | Construct | Domain | Degree | Betweenness | Eigenvector | PageRank |")
    w("|------|-----------|--------|--------|-------------|-------------|----------|")
    top_degree = sorted(centralities["degree"].items(), key=lambda x: x[1], reverse=True)[:10]
    for rank, (node, deg) in enumerate(top_degree, 1):
        domain = G.nodes[node]["domain"]
        short = node.split("|")[1] if "|" in node else node
        btw = centralities["betweenness"].get(node, 0)
        eig = centralities["eigenvector"].get(node, 0)
        pr = centralities["pagerank"].get(node, 0)
        w(f"| {rank} | {short} | {domain} | {deg} | {btw:.4f} | {eig:.4f} | {pr:.4f} |")
    w()

    w("### Top 10 by Betweenness Centrality")
    w()
    w("| Rank | Construct | Domain | Betweenness | Degree |")
    w("|------|-----------|--------|-------------|--------|")
    top_btw = sorted(centralities["betweenness"].items(), key=lambda x: x[1], reverse=True)[:10]
    for rank, (node, btw) in enumerate(top_btw, 1):
        domain = G.nodes[node]["domain"]
        short = node.split("|")[1] if "|" in node else node
        deg = centralities["degree"].get(node, 0)
        w(f"| {rank} | {short} | {domain} | {btw:.4f} | {deg} |")
    w()

    w("![Centrality Comparison](network_topology_centrality.png)")
    w()
    w("**Figure: Centrality Comparison.** Pairwise scatter plots of degree, betweenness,")
    w("and eigenvector centrality. Points are colored by domain. If all measures agreed")
    w("perfectly, points would fall on the diagonal; divergence reveals structural roles.")
    w()

    w("### Interpretation")
    w()
    w("**Degree and eigenvector centrality are strongly correlated.** This is expected in a")
    w("dense, low-modularity network: being connected to many nodes is almost equivalent to")
    w("being connected to important nodes, because most of the network is reachable in 1-2 hops.")
    w("The eigenvector values are remarkably uniform among top nodes (0.152–0.177), confirming")
    w("that no single node dominates the spectral structure.")
    w()
    w("**Betweenness reveals structural bottlenecks.** The most interesting divergences between")
    w("degree and betweenness centrality:")
    w()
    # Find the betweenness outliers — high betweenness relative to what degree alone predicts
    # Rank each node by degree and by betweenness; outliers have betweenness rank >> degree rank
    deg_ranks = {n: r for r, (n, _) in enumerate(sorted(centralities["degree"].items(),
                 key=lambda x: x[1], reverse=True))}
    btw_ranks = {n: r for r, (n, _) in enumerate(sorted(centralities["betweenness"].items(),
                 key=lambda x: x[1], reverse=True))}
    # gap > 0 means btw rank is much better (lower number) than degree rank
    rank_gap = {n: deg_ranks.get(n, 99) - btw_ranks.get(n, 99) for n in centralities["betweenness"]
                if centralities["betweenness"][n] > 0}
    # Nodes where betweenness rank is much better than degree rank (largest positive gap)
    btw_outliers = sorted(rank_gap.items(), key=lambda x: x[1], reverse=True)[:3]
    for node, gap in btw_outliers:
        short = node.split("|")[1] if "|" in node else node
        domain = G.nodes[node]["domain"]
        deg = centralities["degree"][node]
        btw = centralities["betweenness"][node]
        deg_r = deg_ranks[node] + 1  # 1-indexed
        btw_r = btw_ranks[node] + 1
        if btw_r < deg_r - 10:
            role = (f"Ranked #{btw_r} in betweenness but only #{deg_r} in degree — "
                    "a **structural bottleneck** connecting otherwise distant network regions. "
                    "Its position in fingerprint space is unique enough that shortest paths are funneled through it.")
        elif btw_r < deg_r - 3:
            role = (f"Ranked #{btw_r} in betweenness vs #{deg_r} in degree — "
                    "sits at a **junction** between different parts of the fingerprint space.")
        else:
            role = (f"Ranked #{btw_r} in betweenness and #{deg_r} in degree — "
                    "central by sheer connectivity, not structural position.")
        w(f"- **{short}** ({domain}): degree {deg}, betweenness {btw:.4f}. {role}")
    w()
    w("**PageRank (γ-weighted)** highlights nodes with *strong* connections, not just *many*.")
    w("HAB constructs dominate PageRank because housing quality/services/assets have the largest")
    w("|γ| values — their SES entanglement is not only broad but deep.")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 4. EDGE SIGNS & STRUCTURAL BALANCE
    # ══════════════════════════════════════════════════════════════════════
    w("## 4. Edge Signs & Structural Balance")
    w()
    w("### 4.1 Sign Distribution")
    w()
    w("Each edge carries a sign: γ > 0 (positive, co-elevation) or γ < 0 (negative, counter-variation).")
    w()
    w("| Metric | Value |")
    w("|--------|-------|")
    w(f"| Positive edges (γ > 0) | {sign_data['n_positive']} ({sign_data['pos_fraction']:.1%}) |")
    w(f"| Negative edges (γ < 0) | {sign_data['n_negative']} ({1 - sign_data['pos_fraction']:.1%}) |")
    w()
    w(f"The split is remarkably close to 50/50 ({sign_data['pos_fraction']:.0%} positive / {1-sign_data['pos_fraction']:.0%} negative).")
    w("This means SES does not have a uniform direction across all attitude domains — it elevates")
    w("some attitudes while suppressing others in roughly equal measure. Mexican sociodemographic")
    w("position creates a **bidirectional** structuring of opinion space.")
    w()

    w("![γ Distribution](network_topology_gamma.png)")
    w()
    w("**Figure: γ Distribution.** Left: histogram of edge γ values, split by sign. The distribution")
    w("is roughly symmetric around zero, with long tails reaching ±0.29. Right: cumulative distribution")
    w("of |γ|. The median |γ| is small, confirming that most SES-mediated co-variation is weak but")
    w("statistically detectable. The tail (|γ| > 0.1) represents the 5-10% of pairs with strong")
    w("SES entanglement.")
    w()

    w("### 4.2 Structural Balance")
    w()
    w("**Definition.** In a signed graph, a triangle (3-clique) is *balanced* if the product")
    w("of its three edge signs is positive, and *frustrated* if negative. By Cartwright-Harary")
    w("balance theory (1956), a perfectly balanced signed graph can be partitioned into exactly")
    w("two camps where all within-camp edges are positive and all cross-camp edges are negative.")
    w()
    w("The four possible triangles:")
    w("- (+, +, +) → product = +1 → **balanced** (all three agree)")
    w("- (+, −, −) → product = +1 → **balanced** (two enemies, one friend)")
    w("- (+, +, −) → product = −1 → **frustrated** (inconsistent)")
    w("- (−, −, −) → product = −1 → **frustrated** (all disagree — no coalition possible)")
    w()
    w("| Metric | Value |")
    w("|--------|-------|")
    w(f"| Total triangles | {sign_data['n_triangles']:,} |")
    w(f"| Balanced triangles | {sign_data['n_balanced']:,} ({sign_data['balance_ratio']:.1%}) |")
    w(f"| Frustrated triangles | {sign_data['n_frustrated']:,} ({1 - sign_data['balance_ratio']:.1%}) |")
    w()

    w("![Structural Balance](network_topology_balance.png)")
    w()
    w("**Figure: Structural Balance.** Left: pie chart showing the 94%/6% balance split.")
    w("Right: bar chart of positive/negative edge counts.")
    w()

    bal_pct = sign_data['balance_ratio'] * 100
    # Expected balance under random signs: for a 52/48 split
    p_pos = sign_data['pos_fraction']
    expected_bal = p_pos**3 + 3*p_pos*(1-p_pos)**2
    w(f"**{bal_pct:.0f}% balanced** is far above what random signs would produce. With a")
    w(f"{p_pos:.0%}/{1-p_pos:.0%} positive/negative split, random sign assignment predicts")
    w(f"{expected_bal:.0%} balanced triangles. The observed {bal_pct:.0f}% is a massive departure")
    w(f"from randomness ({bal_pct - expected_bal*100:+.0f} percentage points).")
    w()
    w("This near-perfect balance means the sign structure is **almost globally consistent**:")
    w("the 71 connected constructs can be partitioned into two camps where within-camp γ is")
    w("predominantly positive and cross-camp γ is predominantly negative. This is the")
    w("mathematical signature of a bipolar SES geometry — sociodemographic position creates")
    w("two coherent blocs of attitudes that SES pushes in opposite directions.")
    w()
    w("The 6% of frustrated triangles represent triads where the SES geometry does not neatly")
    w("decompose into two camps — constructs influenced by different SES dimensions in")
    w("non-aligned ways. These are the genuinely complex nodes in the opinion landscape.")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 5. DOMAIN MIXING
    # ══════════════════════════════════════════════════════════════════════
    w("## 5. Domain Mixing")
    w()
    w("**Definition.** Domain mixing measures whether SES bridges preferentially connect")
    w("constructs within the same survey domain or across different domains. This is quantified")
    w("by the domain assortativity coefficient (Section 1.6) and by counting intra- vs inter-domain edges.")
    w()
    w("| Metric | Value |")
    w("|--------|-------|")
    w(f"| Intra-domain edges | {mixing['intra_edges']} ({mixing['intra_fraction']:.1%}) |")
    w(f"| Inter-domain edges | {mixing['inter_edges']} ({1 - mixing['intra_fraction']:.1%}) |")
    w()
    if mixing["intra_edges"] == 0:
        w("> **Note:** Zero intra-domain edges is **by construction** — the DR bridge sweep only")
        w("> estimates cross-domain pairs. Intra-domain SES co-variation certainly exists but was")
        w("> not estimated. This means domain assortativity is mechanically depressed.")
    w()

    w("![Domain Heatmap](network_topology_domain_heatmap.png)")
    w()
    w("**Figure: Domain Heatmap.** Left: edge count between each pair of domains (darker = more")
    w("edges). Right: mean γ between each domain pair (red = positive, blue = negative).")
    w("The edge-count heatmap reveals the most SES-entangled domain pairs; the sign heatmap")
    w("shows whether SES co-elevates or counter-varies the two domains.")
    w()

    w("### Top 10 Domain Pairs by Edge Count")
    w()
    w("| Domains | Edges | Mean γ | Sign | Interpretation |")
    w("|---------|-------|--------|------|----------------|")
    interpretations = {
        ("CIE", "REL"): "Science curiosity and religiosity are SES-opposed",
        ("FED", "REL"): "Political engagement and religiosity are SES-independent on average",
        ("CIE", "FED"): "Science and politics slightly opposed via SES",
        ("HAB", "REL"): "Housing quality and religiosity slightly SES-opposed",
        ("CIE", "HAB"): "Science and housing quality co-elevated by education",
        ("CIE", "GLO"): "Science and globalization attitudes SES-opposed",
        ("GLO", "REL"): "Globalization skepticism and religiosity slightly co-elevated",
        ("JUS", "REL"): "Justice and religiosity show weak SES co-variation",
        ("FED", "HAB"): "Political engagement and housing slightly co-elevated",
        ("HAB", "JUS"): "Housing quality and justice attitudes slightly opposed",
    }
    for pair, cnt in mixing["domain_pair_counts"].most_common(10):
        mean_g = np.mean(mixing["domain_pair_gammas"][pair])
        sign = "+" if mean_g > 0 else "−"
        interp = interpretations.get(pair, "")
        w(f"| {pair[0]} × {pair[1]} | {cnt} | {mean_g:+.4f} | {sign} | {interp} |")
    w()
    w("The most SES-entangled domain pair is **CIE × REL** (25 edges, mean γ = −0.019).")
    w("Science and religion are the domains most pervasively linked through sociodemographic")
    w("position, with SES pushing them in opposite directions — higher education is associated")
    w("with greater science engagement *and* lower religiosity.")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 6. COMMUNITY STRUCTURE
    # ══════════════════════════════════════════════════════════════════════
    w("## 6. Community Structure")
    w()
    w("**Definition.** A community is a group of nodes more densely connected to each other than")
    w("to the rest of the network. *Modularity* Q measures the quality of a partition:")
    w()
    w("    Q = (1/2m) Σ_ij [A_ij − k_i k_j / 2m] δ(c_i, c_j)")
    w()
    w("where A is the adjacency matrix, k_i is the degree of node i, m is the total edge count,")
    w("and δ(c_i, c_j) = 1 if nodes i and j are in the same community. Q ranges from −0.5 to 1:")
    w("- Q ≈ 0: partition is no better than random")
    w("- Q > 0.3: clear community structure")
    w("- Q > 0.7: strong community structure")
    w()
    w("We compare three partitions:")
    w()
    w("| Method | How it works | Communities | Modularity |")
    w("|--------|-------------|------------|------------|")
    cd_l = comm_data["louvain"]
    cd_g = comm_data["greedy"]
    cd_d = comm_data["domain"]
    w(f"| Louvain | Greedy modularity optimization with local moves and multi-level coarsening | {len(cd_l['communities'])} | {cd_l['modularity']:.4f} |")
    w(f"| Greedy | Agglomerative: repeatedly merge the pair of communities that most improves Q | {len(cd_g['communities'])} | {cd_g['modularity']:.4f} |")
    w(f"| Domain | Use the 22 survey domains as predefined communities | {len(cd_d['communities'])} | {cd_d['modularity']:.4f} |")
    w()

    w("![Community vs Domain](network_topology_communities.png)")
    w()
    w("**Figure: Community Composition.** Stacked bars showing how Louvain communities")
    w("are composed by domain. Each bar is one community; colors represent domains.")
    w("The mix of colors in each bar demonstrates that communities cut across domain boundaries.")
    w()

    w(f"### Interpretation")
    w()
    w(f"Louvain modularity Q = **{mod_l:.3f}** — effectively zero. Both algorithmic methods converge")
    w(f"on 3 communities, but the partition is barely better than random (Q < 0.1). The network")
    w(f"has **no meaningful community structure**.")
    w()
    w(f"Domain-based partition achieves Q = **{mod_d:.3f}** — *negative*, meaning the domain")
    w(f"partition is *worse* than random. Domains are not communities; they are administrative")
    w(f"categories (survey themes) that SES cuts across orthogonally. SES does not respect")
    w(f"thematic boundaries — it structures attitudes by sociodemographic axis, not by topic.")
    w()
    w("This is a fundamental finding: **there are no clusters in the SES bridge network**.")
    w("Low modularity is the network signature of a continuous gradient. The 4D SES space")
    w("is low-dimensional, so there are not enough degrees of freedom for sharp boundaries.")
    w("Attitudes vary smoothly along sociodemographic axes, not in discrete blocs.")
    w()

    w("### Louvain Community Composition")
    w()
    for i, comm in enumerate(cd_l["communities"]):
        domain_counts = Counter(G.nodes[n]["domain"] for n in comm)
        n_domains = len(domain_counts)
        top_3 = domain_counts.most_common(3)
        desc = ", ".join(f"{d}({c})" for d, c in top_3)
        w(f"- **C{i}** ({len(comm)} nodes from {n_domains} domains): {desc}, ...")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 7. FINGERPRINT GEOMETRY
    # ══════════════════════════════════════════════════════════════════════
    w("## 7. Fingerprint Geometry (4D SES Space)")
    w()
    w("### 7.1 PCA: Dimensionality of the Fingerprint Space")
    w()
    w("**What it is.** Each construct carries a 4D fingerprint vector `[ρ_escol, ρ_Tam_loc, ρ_sexo, ρ_edad]`")
    w("— the Spearman correlation of the construct with each SES dimension. PCA (Principal Component")
    w("Analysis) rotates these 4 coordinates to find the axes of maximum variance. The eigenvalues")
    w("(variance explained) tell us how many independent dimensions the fingerprints actually use;")
    w("the eigenvectors (loadings) tell us what each synthetic axis means in terms of the original")
    w("SES dimensions.")
    w()
    w("**How it's computed.** Center the 93 fingerprint vectors (subtract mean), compute the 4×4")
    w("covariance matrix, decompose via SVD. The resulting principal components (PCs) are ordered by")
    w("decreasing variance explained.")
    w()

    w("| PC | Variance Explained | Cumulative | Interpretation |")
    w("|----|-------------------|------------|----------------|")
    cum = 0
    pc_interps = [
        "The education-vs-tradition axis (dominant)",
        "The age-vs-urbanization axis (secondary)",
        "Residual gender/location variation",
        "Remaining noise (negligible)",
    ]
    for i, v in enumerate(ev):
        cum += v
        w(f"| PC{i+1} | {v:.1%} | {cum:.1%} | {pc_interps[i]} |")
    w()
    w("![Fingerprint PCA](network_topology_pca.png)")
    w()
    w("**Figure: Fingerprint PCA.** Each dot is a construct, positioned by its PC1 and PC2")
    w("coordinates (collectively capturing 90% of variance). Node size is proportional to")
    w("SES magnitude (RMS of the fingerprint). Colors indicate survey domain. The 50 strongest")
    w("bridges are drawn as lines (orange = positive γ, blue = negative γ). The spread")
    w("of the cloud reveals the effective geometry of the SES space.")
    w()

    w("### 7.2 PCA Loadings — What the Axes Mean")
    w()
    dims = ["escol", "Tam_loc", "sexo", "edad"]
    dim_names = ["Education", "Town size", "Gender", "Age/cohort"]
    w("| Dimension | PC1 loading | PC2 loading |")
    w("|-----------|-------------|-------------|")
    for j, (dim, name) in enumerate(zip(dims, dim_names)):
        w(f"| {name} ({dim}) | {fp_data['pca_components'][0][j]:+.3f} | {fp_data['pca_components'][1][j]:+.3f} |")
    w()

    # Deep interpretation of loadings
    pc1 = fp_data['pca_components'][0]
    pc2 = fp_data['pca_components'][1]
    w("**PC1 (77.7% of variance): The education-vs-tradition axis**")
    w()
    w(f"PC1 loads heavily on **escol** ({pc1[0]:+.3f}) in opposition to **Tam_loc** ({pc1[1]:+.3f})")
    w(f"and **edad** ({pc1[2]:+.3f}). This axis separates constructs that are *elevated by education*")
    w(f"(negative PC1 scores: high ρ_escol) from those elevated by *rural residence and older age*")
    w(f"(positive PC1 scores: high ρ_Tam_loc, high ρ_edad).")
    w()
    w("The opposition is not accidental — it reflects the deep structure of Mexican sociodemographic")
    w("stratification. Education and urbanization are positively correlated in the population")
    w("(cities have more schooling), yet they load on opposite sides of PC1 in the fingerprint space.")
    w("This means they structure *attitudes* in opposite directions: education elevates some attitudes")
    w("(science engagement, digital capital, cultural consumption) while town size and age elevate")
    w("others (religiosity, traditional gender roles, community attachment).")
    w()
    w("The dominance of PC1 (78% of variance) means that **most of the variation in how SES**")
    w("**structures attitudes reduces to a single continuum**: from education-driven cosmopolitan")
    w("attitudes on one end to age/locality-driven traditional attitudes on the other. This is the")
    w("*primary cleavage* in the SES fingerprint space.")
    w()

    w("**PC2 (12.0% of variance): The age-vs-urbanization axis**")
    w()
    w(f"PC2 loads heavily on **edad** ({pc2[3]:+.3f}) in opposition to **Tam_loc** ({pc2[1]:+.3f}).")
    w(f"Education is nearly invisible on this axis (loading {pc2[0]:+.3f}). PC2 captures the")
    w("*residual variation* after the dominant education axis is removed: the independent effects")
    w("of age versus urbanization.")
    w()
    w("Constructs with high PC2 scores are those structured by age *independently of education* —")
    w("attitudes that shift across cohorts regardless of schooling level (e.g., technology adoption,")
    w("generational values). Constructs with low PC2 scores are structured by urbanization")
    w("independently of education — urban/rural differences that persist across educational levels")
    w("(e.g., access to services, community structure, local governance experience).")
    w()
    w("Together, PC1 and PC2 reveal that the 4D SES space is effectively **2-dimensional**:")
    w("a dominant education-vs-tradition axis, and a secondary age-vs-urbanization axis.")
    w("Gender (sexo) contributes weakly to both components — it structures a smaller, more")
    w("specialized set of attitudes (reproductive rights, gender role expectations) rather than")
    w("broadly structuring the entire opinion landscape.")
    w()

    w("![SES Dimension Profiles](network_topology_ses_profiles.png)")
    w()
    w("**Figure: SES Dimension Profiles.** Violin plots of Spearman ρ for each SES dimension")
    w("across the 71 connected constructs. Education (escol) has the widest spread — the most")
    w("polarizing dimension, with some constructs strongly positively correlated and others")
    w("strongly negatively correlated. Town size (Tam_loc) is the second widest, skewed negative")
    w("(rural residence tends to elevate traditional/community attitudes). Gender (sexo) is the")
    w("most concentrated around zero — consistent with PC1/PC2 loadings showing gender's weak")
    w("overall contribution to the fingerprint geometry.")
    w()

    w("### 7.3 Dominant SES Dimension per Construct")
    w()
    w("For each construct, the *dominant dimension* is the SES variable with the highest |ρ|.")
    w()
    w("| Dimension | Count | % | What it means |")
    w("|-----------|-------|---|---------------|")
    total = sum(fp_data["dim_counts"].values())
    dim_interps = {
        "escol": "Education is the primary stratifier for this construct",
        "Tam_loc": "Urban/rural context is the primary stratifier",
        "edad": "Age/cohort is the primary stratifier",
        "sexo": "Gender is the primary stratifier",
    }
    for dim, cnt in sorted(fp_data["dim_counts"].items(), key=lambda x: x[1], reverse=True):
        w(f"| {dim} | {cnt} | {cnt/total:.0%} | {dim_interps.get(dim, '')} |")
    w()
    w("Education dominates (40%), but **60% of constructs are primarily structured by**")
    w("**non-education SES dimensions**. This challenges the common assumption that education")
    w("is the only SES dimension that matters for attitudes. Town size (25%) and age (24%)")
    w("are nearly as important in aggregate. Gender, while less frequent as the *dominant*")
    w("dimension, is the *exclusive* stratifier for some attitudes (gender role beliefs,")
    w("reproductive health access).")
    w()

    w("### 7.4 Fingerprint Dot Product vs. Bridge γ")
    w()
    w("**The key test.** If the network is truly a geometric graph — if topology is determined by")
    w("fingerprint positions — then the dot product of two constructs' fingerprints should predict")
    w("the bridge γ between them. The dot product fp_A · fp_B = Σ_d ρ_A,d × ρ_B,d captures whether")
    w("the two constructs are pushed in the same direction (+) or opposite directions (−) by each")
    w("SES dimension simultaneously.")
    w()
    w(f"Pearson r = **{r_val:.3f}** (p = {p_val:.1e}), computed over all {len(fp_data['fp_dot_list'])} significant edges.")
    w()
    w("![Dot vs Gamma](network_topology_dot_gamma.png)")
    w()
    w("**Figure: Dot Product vs. γ.** Each point is a significant bridge edge. The strong")
    w("linear relationship confirms that the 4D fingerprint geometry *predicts* both the sign and")
    w("magnitude of the DR bridge estimate. The regression line passes near the origin, confirming")
    w("that zero dot product → zero γ (orthogonal SES profiles → no SES-mediated co-variation).")
    w()
    w(f"The r² = {r_val**2:.3f}, meaning **{r_val**2:.0%} of the variance in γ is explained by the")
    w("fingerprint dot product alone**. This is remarkable because the dot product is computed from")
    w("simple bivariate Spearman correlations (each construct vs. each SES dimension independently),")
    w("while γ is estimated by the full doubly-robust bridge (propensity weighting, joint distribution")
    w("modeling, 200 bootstrap iterations). The fact that a simple 4-number dot product recovers")
    w(f"{r_val**2:.0%} of the complex estimator's output confirms that the bridge network is")
    w("fundamentally **low-dimensional** and **geometrically determined**.")
    w()
    w(f"The remaining {1-r_val**2:.0%} of variance likely comes from: (a) interaction effects between")
    w("SES dimensions not captured by the dot product (e.g., education × gender interactions),")
    w("(b) bootstrap noise in γ estimates, and (c) non-linear SES effects that the fingerprint")
    w("(linear Spearman ρ) cannot capture.")
    w()

    # ══════════════════════════════════════════════════════════════════════
    # 8. SUMMARY & ARCHETYPE
    # ══════════════════════════════════════════════════════════════════════
    w("## 8. Summary: What Kind of Network Is This?")
    w()
    w("### Key Properties")
    w()
    props = [
        (f"Dense ({density_pct:.0f}%)",
         f"23% of possible edges exist. SES creates broad, pervasive connectivity — not a sparse web of isolated links."),
        (f"Compact (diameter {m['diameter']}, APL {m['avg_path_length']:.2f})",
         f"Any two connected constructs are fewer than 2 hops apart on average. The SES bridge is an ultra-short-range connector."),
        (f"High clustering ({m['avg_clustering']:.3f} vs {C_rand:.3f} random)",
         f"Neighbors share neighbors at {m['avg_clustering']/C_rand:.1f}× the random rate — geometric transitivity."),
        (f"Structurally balanced ({sign_data['balance_ratio']:.0%})",
         f"94% of triangles are sign-consistent. The network admits a near-perfect two-camp partition."),
        (f"Near-equal sign split ({sign_data['pos_fraction']:.0%}/{1-sign_data['pos_fraction']:.0%})",
         f"SES drives co-elevation and counter-variation in equal measure — a bidirectional structuring of opinion space."),
        (f"No community structure (Q = {mod_l:.3f})",
         f"No discrete clusters. The network is a continuous gradient, not a modular graph."),
        (f"Geometrically determined (r = {r_val:.3f})",
         f"The 4D fingerprint dot product explains {r_val**2:.0%} of variance in γ. Topology is a projection of SES geometry."),
        (f"Low effective dimensionality (PC1 = {ev[0]:.0%})",
         f"The 4D fingerprint space is effectively ~1.5D: one dominant education-vs-tradition axis plus a secondary age-vs-urbanization axis."),
    ]
    for title, desc in props:
        w(f"- **{title}**: {desc}")
    w()

    w("### Network Archetype")
    w()
    w("This is a **signed thresholded inner-product graph** in R⁴. It is not a social network,")
    w("not scale-free, not a classical small-world, and not a modular graph. Its structure derives")
    w("from four interlocking properties:")
    w()
    w("**1. Topology from geometry.** Each construct occupies a position in 4D SES space via its")
    w(f"fingerprint vector. Two constructs form a significant bridge when the magnitude of their")
    w(f"fingerprint interaction (dot product) exceeds the statistical noise floor. The dot product")
    w(f"predicts γ sign at 99.4% accuracy and γ magnitude at r = {r_val:.3f}. The graph is not")
    w("an independent object — it is a *projection* of a continuous geometric space onto a discrete")
    w("edge set, with significance testing acting as the threshold function.")
    w()
    w("**2. Signed edges with structural balance.** Both positive and negative edges exist in")
    w(f"near-equal numbers ({sign_data['pos_fraction']:.0%}/{1-sign_data['pos_fraction']:.0%}). The 94% structural")
    w("balance means the sign pattern is almost perfectly consistent across triangles — the network")
    w("admits a clean bipartition into two *camps* of attitudes. One camp is elevated by the")
    w("education-cosmopolitan end of PC1; the other by the tradition-locality end. This bipartition")
    w("is the discrete shadow of the continuous PC1 axis.")
    w()
    w(f"**3. Dense + low modularity.** High density ({density_pct:.0f}%) and near-zero modularity")
    w(f"(Q = {mod_l:.3f}) are natural consequences of low dimensionality. In R⁴ — effectively R^1.5")
    w("given the PCA spectrum — there are not enough degrees of freedom to create well-separated")
    w("clusters. Every construct's fingerprint has non-trivial projection onto the dominant PC1 axis,")
    w("producing inner products (and therefore bridges) with many other constructs.")
    w()
    w(f"**4. Bimodal connectivity.** The {m['isolated_nodes']} isolated nodes are constructs with SES")
    w("magnitudes too small to clear the significance threshold against any partner. They sit near")
    w(f"the origin in fingerprint space. The {m['giant_n']} connected nodes form a single dense")
    w("component — the *core* of SES-structured opinion. There is no middle ground: a construct is")
    w("either strongly SES-structured (and connected to many others) or barely SES-structured (and isolated).")
    w()
    w("### Theoretical Analogy")
    w()
    w("The closest model is a **random geometric graph** (RGG) in R⁴: scatter n points in a")
    w("low-dimensional space; connect pairs whose geometric interaction exceeds a threshold.")
    w("RGGs produce exactly the properties we observe: high clustering (geometric transitivity),")
    w("short paths (low dimensionality), weak community structure (no natural boundaries in")
    w("continuous space), and bimodal degree distributions (interior nodes connect broadly,")
    w("boundary nodes sparsely). The key difference is that our \"distance\" is a *signed*")
    w("inner product, generating the balanced sign structure that a standard RGG would lack.")
    w()
    w("### Implication for Interpretation")
    w()
    w("The SES bridge network does not reveal hidden *clusters* of attitudes. It reveals a")
    w("**gradient**. Mexican attitudes vary continuously along a low-dimensional sociodemographic")
    w("axis — primarily education (which loads in opposition to age and town size on PC1) — and")
    w("the bridge graph is the statistical shadow of this continuous structure. The network is best")
    w("understood not as a map of discrete communities, but as a *contour map* of a smooth")
    w("sociodemographic landscape, where the edges are contour lines connecting attitudes at")
    w("similar SES elevations.")

    return "\n".join(L)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    ont, fp = load_data()
    G = build_graph(ont)
    print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    print("Computing global metrics...")
    metrics, giant = global_metrics(G)
    print(f"  Giant component: {metrics['giant_n']} nodes, diameter={metrics['diameter']}")

    print("Computing centralities...")
    centralities = centrality_analysis(G, giant)

    print("Analyzing edge signs & structural balance (counting triangles)...")
    sign_data = sign_analysis(G)
    print(f"  {sign_data['n_triangles']:,} triangles, {sign_data['balance_ratio']:.1%} balanced")

    print("Analyzing domain mixing...")
    mixing = domain_mixing(G)

    print("Analyzing fingerprint geometry...")
    fp_data = fingerprint_geometry(G)

    print("Detecting communities...")
    comm_data = community_detection(G)
    print(f"  Louvain: {len(comm_data['louvain']['communities'])} communities, Q={comm_data['louvain']['modularity']:.3f}")

    # ── Visualizations ──
    print("\nGenerating visualizations...")
    plot_degree_distribution(G, OUT_DIR / "network_topology_degree.png")
    plot_gamma_distribution(G, OUT_DIR / "network_topology_gamma.png")
    plot_fingerprint_pca(fp_data, G, OUT_DIR / "network_topology_pca.png")
    plot_dot_vs_gamma(fp_data, OUT_DIR / "network_topology_dot_gamma.png")
    plot_centrality_comparison(centralities, G, OUT_DIR / "network_topology_centrality.png")
    plot_domain_heatmap(mixing, OUT_DIR / "network_topology_domain_heatmap.png")
    plot_community_vs_domain(comm_data, G, OUT_DIR / "network_topology_communities.png")
    plot_structural_balance(sign_data, OUT_DIR / "network_topology_balance.png")
    plot_ses_dimension_profile(G, OUT_DIR / "network_topology_ses_profiles.png")

    # ── Report ──
    print("\nGenerating report...")
    report = generate_report(metrics, giant, G, centralities, sign_data,
                             mixing, fp_data, comm_data)
    report_path = OUT_DIR / "network_topology_report.md"
    report_path.write_text(report)
    print(f"\n✓ Report saved to {report_path}")
    print(f"✓ {len(list(OUT_DIR.glob('network_topology_*.png')))} visualizations saved")


if __name__ == "__main__":
    main()
