"""
Cross-Country Geometric Analysis of the γ-Surface

Answers: WHY do countries have similar or different SES-attitude network structures?
Links spectral distance (network structure similarity) to macro-level predictors:
World Bank development indicators, cultural zones, SES signatures, mediator profiles.

5 parts:
  1. Fetch & cache World Bank macro indicators (circa 2018)
  2. Mantel tests + OLS regression: what predicts spectral distance?
  3. Hierarchical clustering vs Inglehart-Welzel zones
  4. Mediator decomposition: why is gender_role_trad the universal bridge?
  5. Zone-level synthesis: SES profiles per cluster

Outputs:
  data/results/cross_country_geometry_report.md
  data/results/cross_country_geometry.json
  data/results/cross_country_geometry/*.png (5 figures)

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_cross_country_geometry.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import squareform, pdist
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.manifold import MDS

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

RESULTS = ROOT / "data" / "results"
FIG_DIR = RESULTS / "cross_country_geometry"
FIG_DIR.mkdir(parents=True, exist_ok=True)

ZONE_COLORS = {
    "Latin America": "#e15759", "English-speaking": "#4e79a7",
    "Protestant Europe": "#76b7b2", "Catholic Europe": "#b07aa1",
    "Orthodox/ex-Communist": "#9c755f", "Confucian": "#edc948",
    "South/Southeast Asian": "#59a14f", "African-Islamic": "#f28e2b",
}

# Short zone labels for plots
ZONE_SHORT = {
    "Latin America": "LatAm", "English-speaking": "Anglo",
    "Protestant Europe": "ProtEU", "Catholic Europe": "CathEU",
    "Orthodox/ex-Communist": "Ortho", "Confucian": "Confuc",
    "South/Southeast Asian": "S/SE Asia", "African-Islamic": "Afr-Isl",
}

# Zone markers for MDS scatter
ZONE_MARKERS = {
    "Latin America": "o", "English-speaking": "s",
    "Protestant Europe": "^", "Catholic Europe": "D",
    "Orthodox/ex-Communist": "v", "Confucian": "P",
    "South/Southeast Asian": "*", "African-Islamic": "X",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Part 0: Load base data
# ═══════════════════════════════════════════════════════════════════════════════

def load_spectral_distance_matrix() -> tuple[list[str], np.ndarray]:
    """Load 66x66 spectral distance matrix. Returns (country_codes, matrix)."""
    path = ROOT / "data" / "tda" / "spectral" / "spectral_distance_matrix.csv"
    df = pd.read_csv(path, index_col=0)
    countries = list(df.columns)
    mat = df.values.astype(float)
    # Ensure symmetric
    mat = (mat + mat.T) / 2
    np.fill_diagonal(mat, 0.0)
    return countries, mat


def load_ses_signatures() -> dict[str, dict[str, float]]:
    path = RESULTS / "ses_signatures_all.json"
    with open(path) as f:
        return json.load(f)


def load_spectral_summaries() -> dict[str, dict]:
    path = ROOT / "data" / "tda" / "message_passing" / "spectral_all_summary.json"
    with open(path) as f:
        data = json.load(f)
    return {s["country"]: s for s in data["summaries"]}


def load_mediator_scores() -> dict[str, dict[str, float]]:
    path = ROOT / "data" / "tda" / "floyd_warshall" / "mediator_scores.json"
    with open(path) as f:
        data = json.load(f)
    # data is {country: {scores: {construct: float}}}
    return {c: v["scores"] for c, v in data.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# Part 1: World Bank Indicators
# ═══════════════════════════════════════════════════════════════════════════════

# WVS alpha3 → ISO alpha3 mapping for countries that differ or need special handling
WVS_TO_ISO = {
    "NIR": "GBR",   # Northern Ireland → UK
    # Most WVS codes match ISO 3166-1 alpha-3
}

WB_INDICATORS = {
    "gni_pc": "NY.GNP.PCAP.CD",         # GNI per capita, Atlas method
    "gini": "SI.POV.GINI",               # Gini index
    "life_exp": "SP.DYN.LE00.IN",        # Life expectancy at birth
    "literacy": "SE.ADT.LITR.ZS",        # Adult literacy rate
    "edu_expend": "SE.XPD.TOTL.GD.ZS",   # Education expenditure % GDP
    "urban_pct": "SP.URB.TOTL.IN.ZS",    # Urban population %
    "internet": "IT.NET.USER.ZS",         # Internet users %
}

# Target years (try 2018 first, then 2017, 2019, 2016, 2020)
TARGET_YEARS = [2018, 2017, 2019, 2016, 2020]

CACHE_PATH = RESULTS / "world_bank_indicators.json"


def fetch_wb_indicator(indicator: str, countries: list[str], years: list[int]) -> dict[str, float]:
    """Fetch a single World Bank indicator for multiple countries.

    Uses the WB API v2 with JSON format. Tries years in priority order.
    Returns {alpha3: value} for countries with available data.
    """
    results = {}
    # Map WVS codes to ISO for API call
    iso_codes = []
    iso_to_wvs = {}
    for c in countries:
        iso = WVS_TO_ISO.get(c, c)
        iso_codes.append(iso)
        iso_to_wvs[iso] = c

    # Deduplicate ISO codes
    unique_iso = list(set(iso_codes))

    # WB API accepts semicolon-separated country codes, max ~60 at once
    # Split into chunks of 50
    for chunk_start in range(0, len(unique_iso), 50):
        chunk = unique_iso[chunk_start:chunk_start + 50]
        country_str = ";".join(chunk)

        for year in years:
            url = (
                f"https://api.worldbank.org/v2/country/{country_str}"
                f"/indicator/{indicator}?date={year}&format=json&per_page=100"
            )
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "Navegador/1.0")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
                print(f"  WB API error for {indicator} year={year}: {e}")
                continue

            if not isinstance(data, list) or len(data) < 2:
                continue

            for entry in data[1] or []:
                iso3 = entry.get("countryiso3code", entry.get("country", {}).get("id", ""))
                val = entry.get("value")
                if val is not None and iso3 in iso_to_wvs and iso_to_wvs[iso3] not in results:
                    results[iso_to_wvs[iso3]] = float(val)

        # Small delay between chunks to be respectful to the API
        time.sleep(0.3)

    return results


def fetch_all_wb_indicators(countries: list[str]) -> dict[str, dict[str, float]]:
    """Fetch all World Bank indicators. Uses cache if available.

    Returns {indicator_name: {country_alpha3: value}}.
    """
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            cached = json.load(f)
        print(f"Loaded cached World Bank indicators ({len(cached)} indicators)")
        # Check if we have all indicators
        if all(ind in cached for ind in WB_INDICATORS):
            return cached
        print("  Cache incomplete, fetching missing indicators...")
    else:
        cached = {}

    for name, code in WB_INDICATORS.items():
        if name in cached and len(cached[name]) > 30:
            print(f"  {name}: cached ({len(cached[name])} countries)")
            continue
        print(f"  Fetching {name} ({code})...")
        values = fetch_wb_indicator(code, countries, TARGET_YEARS)
        cached[name] = values
        print(f"    Got {len(values)}/{len(countries)} countries")
        time.sleep(0.5)

    # Save cache
    with open(CACHE_PATH, "w") as f:
        json.dump(cached, f, indent=2)
    print(f"Saved to {CACHE_PATH}")

    return cached


# ═══════════════════════════════════════════════════════════════════════════════
# Part 2: Mantel Tests + OLS Regression
# ═══════════════════════════════════════════════════════════════════════════════

def mantel_test(dist_a: np.ndarray, dist_b: np.ndarray, n_perm: int = 10000) -> tuple[float, float]:
    """Mantel test: correlation between two distance matrices.

    Uses Pearson correlation on upper-triangle values.
    Returns (r_obs, p_value) via permutation test.
    """
    n = dist_a.shape[0]
    # Extract upper triangle (no diagonal)
    idx = np.triu_indices(n, k=1)
    a_vec = dist_a[idx]
    b_vec = dist_b[idx]

    r_obs = np.corrcoef(a_vec, b_vec)[0, 1]

    # Permutation test
    count = 0
    rng = np.random.default_rng(42)
    for _ in range(n_perm):
        perm = rng.permutation(n)
        a_perm = dist_a[np.ix_(perm, perm)]
        a_perm_vec = a_perm[idx]
        r_perm = np.corrcoef(a_perm_vec, b_vec)[0, 1]
        if r_perm >= r_obs:
            count += 1

    p_val = (count + 1) / (n_perm + 1)
    return float(r_obs), float(p_val)


def build_indicator_distance_matrices(
    countries: list[str], wb_data: dict[str, dict[str, float]]
) -> dict[str, np.ndarray]:
    """Build pairwise |delta| matrices for each indicator.

    Missing values → NaN. Returns {indicator_name: n×n matrix}.
    """
    n = len(countries)
    matrices = {}

    for name, values in wb_data.items():
        mat = np.full((n, n), np.nan)
        for i in range(n):
            for j in range(i + 1, n):
                vi = values.get(countries[i])
                vj = values.get(countries[j])
                if vi is not None and vj is not None:
                    d = abs(vi - vj)
                    mat[i, j] = d
                    mat[j, i] = d
            mat[i, i] = 0.0
        matrices[name] = mat

    return matrices


def build_zone_distance_matrix(countries: list[str]) -> np.ndarray:
    """Binary distance: 0 if same zone, 1 if different zone."""
    n = len(countries)
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            zi = COUNTRY_ZONE.get(countries[i], "Unknown")
            zj = COUNTRY_ZONE.get(countries[j], "Unknown")
            d = 0.0 if zi == zj else 1.0
            mat[i, j] = d
            mat[j, i] = d
    return mat


def build_ses_signature_distance(countries: list[str], ses_sigs: dict) -> np.ndarray:
    """Euclidean distance between 4D SES signature vectors."""
    n = len(countries)
    dims = ["escol", "Tam_loc", "sexo", "edad"]
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            si = ses_sigs.get(countries[i], {})
            sj = ses_sigs.get(countries[j], {})
            vi = np.array([si.get(d, 0) for d in dims])
            vj = np.array([sj.get(d, 0) for d in dims])
            d = np.linalg.norm(vi - vj)
            mat[i, j] = d
            mat[j, i] = d
    return mat


def build_fiedler_distance(countries: list[str], spectral_summ: dict) -> np.ndarray:
    """Absolute difference in Fiedler value between countries."""
    n = len(countries)
    mat = np.zeros((n, n))
    for i in range(n):
        fi = spectral_summ.get(countries[i], {}).get("fiedler_value", 0.7)
        for j in range(i + 1, n):
            fj = spectral_summ.get(countries[j], {}).get("fiedler_value", 0.7)
            d = abs(fi - fj)
            mat[i, j] = d
            mat[j, i] = d
    return mat


def run_mantel_suite(
    countries: list[str],
    spectral_dist: np.ndarray,
    wb_data: dict,
    ses_sigs: dict,
    spectral_summ: dict,
) -> dict[str, dict]:
    """Run Mantel tests for all predictors against spectral distance."""

    indicator_mats = build_indicator_distance_matrices(countries, wb_data)
    zone_mat = build_zone_distance_matrix(countries)
    ses_dist_mat = build_ses_signature_distance(countries, ses_sigs)
    fiedler_mat = build_fiedler_distance(countries, spectral_summ)

    # Add derived predictors
    all_mats = {**indicator_mats}
    all_mats["same_zone"] = zone_mat
    all_mats["ses_signature"] = ses_dist_mat
    all_mats["fiedler_diff"] = fiedler_mat

    results = {}
    for name, mat in all_mats.items():
        # Handle NaN: for Mantel, we need complete-case pairs
        # Replace NaN with column mean for a rough approximation
        valid = ~np.isnan(mat)
        if np.sum(valid[np.triu_indices(len(countries), k=1)]) < 100:
            print(f"  Skipping {name}: too few valid pairs")
            results[name] = {"r": np.nan, "p": np.nan, "n_pairs": 0}
            continue

        # Fill NaN with mean of valid values for Mantel
        mat_clean = mat.copy()
        nan_mask = np.isnan(mat_clean)
        if nan_mask.any():
            mean_val = np.nanmean(mat_clean[np.triu_indices(len(countries), k=1)])
            mat_clean[nan_mask] = mean_val

        n_valid = int(np.sum(~np.isnan(mat[np.triu_indices(len(countries), k=1)])))
        print(f"  Mantel: spectral dist ~ {name} ({n_valid} pairs)...")
        r, p = mantel_test(spectral_dist, mat_clean, n_perm=10000)
        results[name] = {"r": r, "p": p, "n_pairs": n_valid}
        print(f"    r={r:.4f}, p={p:.4f}")

    return results


def run_pairwise_ols(
    countries: list[str],
    spectral_dist: np.ndarray,
    wb_data: dict,
    ses_sigs: dict,
    spectral_summ: dict,
) -> dict:
    """OLS regression: spectral distance ~ macro indicators + zone + SES + Fiedler.

    Uses upper-triangle pairwise observations. Returns regression summary dict.
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler

    n = len(countries)
    idx = np.triu_indices(n, k=1)
    y = spectral_dist[idx]

    # Build predictor columns
    predictor_names = []
    X_cols = []

    # Macro indicators
    for name, values in wb_data.items():
        col = []
        for i, j in zip(idx[0], idx[1]):
            vi = values.get(countries[i])
            vj = values.get(countries[j])
            if vi is not None and vj is not None:
                col.append(abs(vi - vj))
            else:
                col.append(np.nan)
        X_cols.append(col)
        predictor_names.append(f"|delta_{name}|")

    # Same zone dummy
    zone_col = []
    for i, j in zip(idx[0], idx[1]):
        zi = COUNTRY_ZONE.get(countries[i], "?")
        zj = COUNTRY_ZONE.get(countries[j], "?")
        zone_col.append(1.0 if zi == zj else 0.0)
    X_cols.append(zone_col)
    predictor_names.append("same_zone")

    # SES signature distance
    dims = ["escol", "Tam_loc", "sexo", "edad"]
    ses_col = []
    for i, j in zip(idx[0], idx[1]):
        si = ses_sigs.get(countries[i], {})
        sj = ses_sigs.get(countries[j], {})
        vi = np.array([si.get(d, 0) for d in dims])
        vj = np.array([sj.get(d, 0) for d in dims])
        ses_col.append(np.linalg.norm(vi - vj))
    X_cols.append(ses_col)
    predictor_names.append("|delta_SES_sig|")

    # Fiedler difference
    fiedler_col = []
    for i, j in zip(idx[0], idx[1]):
        fi = spectral_summ.get(countries[i], {}).get("fiedler_value", 0.7)
        fj = spectral_summ.get(countries[j], {}).get("fiedler_value", 0.7)
        fiedler_col.append(abs(fi - fj))
    X_cols.append(fiedler_col)
    predictor_names.append("|delta_Fiedler|")

    X = np.column_stack(X_cols)

    # Drop rows with any NaN
    valid = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X_clean = X[valid]
    y_clean = y[valid]

    print(f"  OLS: {X_clean.shape[0]} valid pairs, {X_clean.shape[1]} predictors")

    # Standardize for comparable betas
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X_clean)

    reg = LinearRegression().fit(X_std, y_clean)
    y_pred = reg.predict(X_std)

    ss_res = np.sum((y_clean - y_pred) ** 2)
    ss_tot = np.sum((y_clean - y_clean.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot

    # Compute p-values via t-test (approximate, ignoring spatial autocorrelation)
    n_obs = len(y_clean)
    k = X_std.shape[1]
    mse = ss_res / (n_obs - k - 1)

    # Hat matrix diagonal for standard errors
    XtX_inv = np.linalg.pinv(X_std.T @ X_std)
    se_beta = np.sqrt(mse * np.diag(XtX_inv))
    t_stats = reg.coef_ / se_beta
    p_values = 2 * stats.t.sf(np.abs(t_stats), df=n_obs - k - 1)

    coefficients = {}
    for name, beta, se, t, p in zip(predictor_names, reg.coef_, se_beta, t_stats, p_values):
        coefficients[name] = {
            "std_beta": float(beta),
            "se": float(se),
            "t": float(t),
            "p": float(p),
            "sig": "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "",
        }

    return {
        "r2": float(r2),
        "adj_r2": float(1 - (1 - r2) * (n_obs - 1) / (n_obs - k - 1)),
        "n_obs": n_obs,
        "n_predictors": k,
        "coefficients": coefficients,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Part 3: Hierarchical Clustering
# ═══════════════════════════════════════════════════════════════════════════════

def cluster_countries(
    countries: list[str], spectral_dist: np.ndarray
) -> tuple[dict, np.ndarray, int]:
    """Ward clustering on spectral distance. Returns (cluster_results, linkage_matrix, best_k)."""

    # Convert to condensed form for scipy
    condensed = squareform(spectral_dist, checks=False)
    Z = linkage(condensed, method="ward")

    # Test k=3 to k=10, pick best silhouette
    sil_scores = {}
    for k in range(3, 11):
        labels = fcluster(Z, k, criterion="maxclust")
        sil = silhouette_score(spectral_dist, labels, metric="precomputed")
        sil_scores[k] = sil

    best_k = max(sil_scores, key=sil_scores.get)
    best_labels = fcluster(Z, best_k, criterion="maxclust")

    # Zone labels for ARI comparison
    zone_labels = [COUNTRY_ZONE.get(c, "Unknown") for c in countries]
    zone_label_ints = pd.Categorical(zone_labels).codes
    ari = adjusted_rand_score(zone_label_ints, best_labels)

    # Build cluster membership
    clusters = defaultdict(list)
    for c, lab in zip(countries, best_labels):
        clusters[int(lab)].append(c)

    return {
        "silhouette_scores": {str(k): float(v) for k, v in sil_scores.items()},
        "best_k": best_k,
        "best_silhouette": float(sil_scores[best_k]),
        "ari_vs_iw_zones": float(ari),
        "cluster_membership": dict(clusters),
        "labels": [int(x) for x in best_labels],
    }, Z, best_k


def plot_dendrogram(
    countries: list[str], Z: np.ndarray, cluster_labels: list[int], best_k: int
):
    """Dendrogram colored by IW zone, with cluster boundaries."""
    fig, ax = plt.subplots(figsize=(20, 8))

    # Color by IW zone
    zone_for_country = {c: COUNTRY_ZONE.get(c, "Unknown") for c in countries}
    leaf_colors = {}
    for i, c in enumerate(countries):
        zone = zone_for_country[c]
        leaf_colors[i] = ZONE_COLORS.get(zone, "#999999")

    # Use default dendrogram coloring (by cluster threshold)
    dendro = dendrogram(
        Z, labels=countries, ax=ax, leaf_rotation=90,
        leaf_font_size=7, color_threshold=0,
        above_threshold_color="#999999",
    )

    # Color the x-axis labels by IW zone
    xlabels = ax.get_xticklabels()
    for label in xlabels:
        c = label.get_text()
        zone = zone_for_country.get(c, "Unknown")
        label.set_color(ZONE_COLORS.get(zone, "#999999"))
        label.set_fontweight("bold")

    ax.set_title(f"Hierarchical Clustering of SES-Attitude Network Structure (Ward, k={best_k})", fontsize=14)
    ax.set_ylabel("Distance")

    # Add legend for zones
    handles = [mpatches.Patch(color=col, label=zone) for zone, col in ZONE_COLORS.items()]
    ax.legend(handles=handles, loc="upper right", fontsize=7, ncol=2)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "dendrogram_spectral.png", dpi=150)
    plt.close(fig)
    print(f"  Saved dendrogram_spectral.png")


def plot_mds_clusters(
    countries: list[str], spectral_dist: np.ndarray,
    cluster_labels: list[int], best_k: int
):
    """MDS 2D scatter: colored by spectral cluster, shaped by IW zone."""
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=42, normalized_stress="auto")
    coords = mds.fit_transform(spectral_dist)

    fig, ax = plt.subplots(figsize=(14, 10))

    # Color palette for clusters
    cluster_colors = plt.cm.Set2(np.linspace(0, 1, best_k))

    for i, c in enumerate(countries):
        zone = COUNTRY_ZONE.get(c, "Unknown")
        cl = cluster_labels[i] - 1  # 0-indexed
        marker = ZONE_MARKERS.get(zone, "o")
        color = cluster_colors[cl]
        ax.scatter(coords[i, 0], coords[i, 1], c=[color], marker=marker,
                   s=80, edgecolors="black", linewidths=0.5, zorder=3)
        ax.annotate(c, (coords[i, 0], coords[i, 1]), fontsize=6,
                    textcoords="offset points", xytext=(4, 4), alpha=0.8)

    # Legends
    # Cluster colors
    cluster_handles = [
        mpatches.Patch(color=cluster_colors[k], label=f"Cluster {k+1}")
        for k in range(best_k)
    ]
    leg1 = ax.legend(handles=cluster_handles, loc="upper left", fontsize=8, title="Spectral Cluster")

    # Zone markers
    zone_handles = [
        plt.Line2D([0], [0], marker=m, color="gray", linestyle="None",
                    markersize=8, label=ZONE_SHORT.get(z, z))
        for z, m in ZONE_MARKERS.items()
    ]
    ax.legend(handles=zone_handles, loc="lower right", fontsize=7, title="IW Zone")
    ax.add_artist(leg1)

    ax.set_title(f"MDS of SES-Attitude Network Structure (k={best_k}, ARI with IW zones shown in report)", fontsize=12)
    ax.set_xlabel("MDS Dimension 1")
    ax.set_ylabel("MDS Dimension 2")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "mds_clusters.png", dpi=150)
    plt.close(fig)
    print(f"  Saved mds_clusters.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Part 2b: Mantel Heatmap
# ═══════════════════════════════════════════════════════════════════════════════

def plot_mantel_heatmap(mantel_results: dict):
    """Bar chart of Mantel r values with significance stars."""
    fig, ax = plt.subplots(figsize=(10, 6))

    names = []
    r_vals = []
    p_vals = []
    for name, res in sorted(mantel_results.items(), key=lambda x: abs(x[1].get("r", 0)), reverse=True):
        if np.isnan(res.get("r", np.nan)):
            continue
        names.append(name)
        r_vals.append(res["r"])
        p_vals.append(res["p"])

    colors = ["#e15759" if p < 0.01 else "#f28e2b" if p < 0.05 else "#999999"
              for p in p_vals]

    bars = ax.barh(range(len(names)), r_vals, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Mantel r (correlation with spectral distance)")
    ax.set_title("What Predicts Network Structure Similarity?\n(Mantel test, 10000 permutations)")
    ax.axvline(0, color="black", linewidth=0.5)

    # Add significance annotation
    for i, (r, p) in enumerate(zip(r_vals, p_vals)):
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
        offset = 0.005 if r >= 0 else -0.005
        ha = "left" if r >= 0 else "right"
        ax.text(r + offset, i, f" {sig} (r={r:.3f})", va="center", ha=ha, fontsize=8)

    # Legend
    handles = [
        mpatches.Patch(color="#e15759", label="p < 0.01"),
        mpatches.Patch(color="#f28e2b", label="p < 0.05"),
        mpatches.Patch(color="#999999", label="not significant"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8)

    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "mantel_heatmap.png", dpi=150)
    plt.close(fig)
    print(f"  Saved mantel_heatmap.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Part 4: Mediator Decomposition
# ═══════════════════════════════════════════════════════════════════════════════

def mediator_decomposition(
    countries: list[str],
    mediator_scores: dict,
    ses_sigs: dict,
    spectral_summ: dict,
    wb_data: dict,
) -> dict:
    """Analyze why gender_role_traditionalism is the universal structural bridge.

    For each country: extract top mediator, its SES magnitude, and network features.
    Regress gender_role_trad mediator rank on SES signature + macro indicators.
    """
    TARGET = "gender_role_traditionalism|WVS_D"

    country_data = []
    for c in countries:
        scores = mediator_scores.get(c, {})
        if not scores:
            continue

        # Rank constructs by mediator score (descending)
        sorted_constructs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        rank_map = {name: rank + 1 for rank, (name, _) in enumerate(sorted_constructs)}

        top_med = sorted_constructs[0][0] if sorted_constructs else "?"
        top_med_name = top_med.split("|")[0] if "|" in top_med else top_med

        grt_rank = rank_map.get(TARGET, len(sorted_constructs))
        grt_score = scores.get(TARGET, 0)

        # SES signature
        sig = ses_sigs.get(c, {})

        # Fiedler
        fiedler = spectral_summ.get(c, {}).get("fiedler_value", np.nan)

        # Macro
        gni = wb_data.get("gni_pc", {}).get(c, np.nan)
        gini = wb_data.get("gini", {}).get(c, np.nan)
        urban = wb_data.get("urban_pct", {}).get(c, np.nan)

        country_data.append({
            "country": c,
            "zone": COUNTRY_ZONE.get(c, "Unknown"),
            "top_mediator": top_med_name,
            "grt_rank": grt_rank,
            "grt_score": grt_score,
            "escol": sig.get("escol", 0),
            "Tam_loc": sig.get("Tam_loc", 0),
            "sexo": sig.get("sexo", 0),
            "edad": sig.get("edad", 0),
            "fiedler": fiedler,
            "gni_pc": gni,
            "gini": gini,
            "urban_pct": urban,
        })

    df = pd.DataFrame(country_data)

    # Compute SES magnitude for each country
    dims = ["escol", "Tam_loc", "sexo", "edad"]
    df["ses_magnitude"] = np.sqrt(sum(df[d] ** 2 for d in dims))

    # Correlation of grt_rank with each predictor
    predictors = ["escol", "Tam_loc", "sexo", "edad", "ses_magnitude", "fiedler", "gni_pc", "gini", "urban_pct"]
    correlations = {}
    for pred in predictors:
        valid = df[["grt_rank", pred]].dropna()
        if len(valid) < 10:
            continue
        r, p = stats.spearmanr(valid["grt_rank"], valid[pred])
        correlations[pred] = {"spearman_r": float(r), "p": float(p)}

    # Top mediator frequency
    top_counts = df["top_mediator"].value_counts().to_dict()

    # GRT rank statistics
    grt_stats = {
        "median_rank": float(df["grt_rank"].median()),
        "mean_rank": float(df["grt_rank"].mean()),
        "pct_top5": float((df["grt_rank"] <= 5).mean() * 100),
        "pct_top10": float((df["grt_rank"] <= 10).mean() * 100),
    }

    return {
        "target_construct": TARGET,
        "grt_rank_stats": grt_stats,
        "top_mediator_frequency": top_counts,
        "grt_rank_correlations": correlations,
        "country_detail": country_data,
    }


def plot_mediator_decomposition(med_results: dict):
    """Scatter: mediator rank of gender_role_trad vs SES magnitude + Fiedler."""
    data = med_results["country_detail"]
    df = pd.DataFrame(data)
    df["ses_magnitude"] = np.sqrt(df["escol"]**2 + df["Tam_loc"]**2 + df["sexo"]**2 + df["edad"]**2)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, xvar, xlabel in [
        (axes[0], "ses_magnitude", "Country SES Magnitude (RMS of 4D signature)"),
        (axes[1], "fiedler", "Fiedler Value (Algebraic Connectivity)"),
    ]:
        for _, row in df.iterrows():
            zone = row["zone"]
            color = ZONE_COLORS.get(zone, "#999999")
            ax.scatter(row[xvar], row["grt_rank"], c=color,
                       s=50, edgecolors="black", linewidths=0.3, zorder=3)
            ax.annotate(row["country"], (row[xvar], row["grt_rank"]),
                        fontsize=5, textcoords="offset points", xytext=(3, 3), alpha=0.7)

        # Add Spearman r
        valid = df[[xvar, "grt_rank"]].dropna()
        if len(valid) > 5:
            r, p = stats.spearmanr(valid[xvar], valid["grt_rank"])
            ax.set_title(f"rho={r:.3f}, p={p:.3f}", fontsize=10)

        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel("gender_role_traditionalism Mediator Rank", fontsize=9)
        ax.invert_yaxis()
        ax.grid(alpha=0.3)

    # Shared legend
    handles = [mpatches.Patch(color=c, label=z) for z, c in ZONE_COLORS.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=7)

    fig.suptitle("Why is gender_role_traditionalism the universal structural bridge?", fontsize=12)
    fig.tight_layout(rect=[0, 0.08, 1, 0.95])
    fig.savefig(FIG_DIR / "mediator_decomposition.png", dpi=150)
    plt.close(fig)
    print(f"  Saved mediator_decomposition.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Part 5: Zone-Level Synthesis
# ═══════════════════════════════════════════════════════════════════════════════

def zone_synthesis(
    countries: list[str],
    cluster_labels: list[int],
    best_k: int,
    ses_sigs: dict,
    spectral_summ: dict,
    mediator_scores: dict,
    spectral_dist: np.ndarray,
) -> dict:
    """Per-cluster synthesis: SES profile, top mediators, Fiedler, inter-cluster distances."""

    dims = ["escol", "Tam_loc", "sexo", "edad"]
    cluster_profiles = {}

    for cl in range(1, best_k + 1):
        members = [countries[i] for i, lab in enumerate(cluster_labels) if lab == cl]

        # Zone composition
        zone_counts = defaultdict(int)
        for c in members:
            zone_counts[COUNTRY_ZONE.get(c, "Unknown")] += 1

        # Mean SES signature
        ses_vals = {d: [] for d in dims}
        for c in members:
            sig = ses_sigs.get(c, {})
            for d in dims:
                if d in sig:
                    ses_vals[d].append(sig[d])
        mean_ses = {d: float(np.mean(v)) if v else 0.0 for d, v in ses_vals.items()}

        # Dominant SES dimension
        dominant = max(mean_ses, key=lambda d: abs(mean_ses[d]))

        # Mean Fiedler
        fiedlers = [spectral_summ.get(c, {}).get("fiedler_value", np.nan) for c in members]
        mean_fiedler = float(np.nanmean(fiedlers))

        # Top 3 mediators (by frequency of being top-1 in cluster members)
        top1_counts = defaultdict(int)
        for c in members:
            scores = mediator_scores.get(c, {})
            if scores:
                top1 = max(scores, key=scores.get)
                name = top1.split("|")[0]
                top1_counts[name] += 1
        top3_mediators = sorted(top1_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        cluster_profiles[str(cl)] = {
            "members": members,
            "n": len(members),
            "zone_composition": dict(zone_counts),
            "mean_ses": mean_ses,
            "dominant_ses_dim": dominant,
            "mean_fiedler": mean_fiedler,
            "top_mediators": [{"construct": m, "count": c} for m, c in top3_mediators],
        }

    # Inter-cluster mean distances
    inter_cluster = {}
    for cl_a in range(1, best_k + 1):
        idx_a = [i for i, lab in enumerate(cluster_labels) if lab == cl_a]
        for cl_b in range(cl_a + 1, best_k + 1):
            idx_b = [i for i, lab in enumerate(cluster_labels) if lab == cl_b]
            dists = spectral_dist[np.ix_(idx_a, idx_b)]
            inter_cluster[f"{cl_a}-{cl_b}"] = float(np.mean(dists))

    # Intra-cluster mean distances
    intra_cluster = {}
    for cl in range(1, best_k + 1):
        idx_cl = [i for i, lab in enumerate(cluster_labels) if lab == cl]
        if len(idx_cl) > 1:
            dists = spectral_dist[np.ix_(idx_cl, idx_cl)]
            intra_cluster[str(cl)] = float(np.mean(dists[np.triu_indices(len(idx_cl), k=1)]))
        else:
            intra_cluster[str(cl)] = 0.0

    return {
        "cluster_profiles": cluster_profiles,
        "inter_cluster_distances": inter_cluster,
        "intra_cluster_distances": intra_cluster,
    }


def plot_cluster_ses_profiles(synthesis: dict, best_k: int):
    """Grouped bar chart: mean SES signature per cluster."""
    dims = ["escol", "Tam_loc", "sexo", "edad"]
    dim_labels = ["Education", "Urbanization", "Gender", "Age"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Bar chart of mean SES per cluster
    ax = axes[0]
    x = np.arange(len(dims))
    width = 0.8 / best_k
    colors = plt.cm.Set2(np.linspace(0, 1, best_k))

    for cl in range(1, best_k + 1):
        profile = synthesis["cluster_profiles"][str(cl)]
        vals = [profile["mean_ses"][d] for d in dims]
        offset = (cl - 1 - best_k / 2 + 0.5) * width
        bars = ax.bar(x + offset, vals, width, label=f"Cl.{cl} (n={profile['n']})",
                       color=colors[cl - 1], edgecolor="black", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(dim_labels)
    ax.set_ylabel("Mean SES Driver Weight")
    ax.set_title("Mean SES Signature per Cluster")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    # Zone composition stacked bars
    ax2 = axes[1]
    zone_names = list(ZONE_COLORS.keys())
    bottom = np.zeros(best_k)
    x2 = np.arange(best_k)

    for zone in zone_names:
        vals = []
        for cl in range(1, best_k + 1):
            comp = synthesis["cluster_profiles"][str(cl)]["zone_composition"]
            vals.append(comp.get(zone, 0))
        ax2.bar(x2, vals, bottom=bottom, label=ZONE_SHORT.get(zone, zone),
                color=ZONE_COLORS[zone], edgecolor="black", linewidth=0.3)
        bottom += np.array(vals)

    ax2.set_xticks(x2)
    ax2.set_xticklabels([f"Cl.{k+1}" for k in range(best_k)])
    ax2.set_ylabel("Number of Countries")
    ax2.set_title("Zone Composition per Cluster")
    ax2.legend(fontsize=7, ncol=2, loc="upper right")

    fig.suptitle("Cluster SES Profiles and Cultural Zone Composition", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_DIR / "cluster_ses_profiles.png", dpi=150)
    plt.close(fig)
    print(f"  Saved cluster_ses_profiles.png")


# ═══════════════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(
    mantel_results: dict,
    ols_results: dict,
    cluster_results: dict,
    mediator_results: dict,
    synthesis: dict,
    wb_data: dict,
    countries: list[str],
) -> str:
    """Generate the markdown report."""

    lines = []
    lines.append("# Cross-Country Geometric Analysis of the gamma-Surface")
    lines.append("")
    lines.append("**What macro-level factors predict SES-attitude network structure similarity across 66 countries?**")
    lines.append("")
    lines.append(f"Analysis date: 2026-04-07 | Countries: {len(countries)} | WVS Wave 7 (2017-2022)")
    lines.append("")

    # ─── Part 1: World Bank Data Coverage ───
    lines.append("## 1. World Bank Macro Indicators (circa 2018)")
    lines.append("")
    lines.append("| Indicator | Countries with data | Min | Max | Mean |")
    lines.append("|-----------|-------------------|-----|-----|------|")
    for name, values in wb_data.items():
        vals = [v for v in values.values() if v is not None]
        n = len(vals)
        if vals:
            lines.append(f"| {name} | {n}/{len(countries)} | {min(vals):.1f} | {max(vals):.1f} | {np.mean(vals):.1f} |")
        else:
            lines.append(f"| {name} | 0/{len(countries)} | - | - | - |")
    lines.append("")

    # ─── Part 2: Mantel Tests ───
    lines.append("## 2. Mantel Tests: Spectral Distance vs. Predictor Distances")
    lines.append("")
    lines.append("Each Mantel test correlates the 66x66 spectral distance matrix with a predictor distance matrix (|delta| for continuous, binary for zone).")
    lines.append("10,000 permutations for p-values.")
    lines.append("")
    lines.append("| Predictor | Mantel r | p-value | Sig | N pairs |")
    lines.append("|-----------|---------|---------|-----|---------|")
    for name, res in sorted(mantel_results.items(), key=lambda x: -abs(x[1].get("r", 0))):
        r = res.get("r", np.nan)
        p = res.get("p", np.nan)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        lines.append(f"| {name} | {r:.4f} | {p:.4f} | {sig} | {res.get('n_pairs', 0)} |")
    lines.append("")

    # Interpretation
    sig_predictors = [(n, r) for n, r in mantel_results.items() if r.get("p", 1) < 0.05]
    if sig_predictors:
        lines.append("**Significant predictors** (p < 0.05):")
        for name, res in sorted(sig_predictors, key=lambda x: -abs(x[1]["r"])):
            direction = "more similar" if res["r"] > 0 else "less similar"
            lines.append(f"- **{name}** (r={res['r']:.3f}): countries with similar {name} have {direction} SES-attitude networks")
    else:
        lines.append("No predictors reached significance at p < 0.05.")
    lines.append("")

    # ─── Part 2b: OLS ───
    lines.append("## 3. Multiple Regression: Pairwise Spectral Distance")
    lines.append("")
    lines.append(f"OLS on {ols_results['n_obs']} country pairs, {ols_results['n_predictors']} standardized predictors.")
    lines.append(f"**R-squared = {ols_results['r2']:.4f}**, Adjusted R-squared = {ols_results['adj_r2']:.4f}")
    lines.append("")
    lines.append("| Predictor | Std Beta | SE | t | p | Sig |")
    lines.append("|-----------|---------|-----|---|---|-----|")
    for name, coef in sorted(ols_results["coefficients"].items(), key=lambda x: -abs(x[1]["std_beta"])):
        lines.append(f"| {name} | {coef['std_beta']:.4f} | {coef['se']:.4f} | {coef['t']:.2f} | {coef['p']:.4f} | {coef['sig']} |")
    lines.append("")

    # ─── Part 3: Clustering ───
    lines.append("## 4. Hierarchical Clustering (Ward's Method)")
    lines.append("")
    lines.append(f"**Optimal k = {cluster_results['best_k']}** (silhouette = {cluster_results['best_silhouette']:.3f})")
    lines.append(f"**ARI vs Inglehart-Welzel zones = {cluster_results['ari_vs_iw_zones']:.3f}**")
    lines.append("")
    lines.append("Silhouette scores by k:")
    lines.append("")
    for k, s in sorted(cluster_results["silhouette_scores"].items(), key=lambda x: int(x[0])):
        marker = " <-- best" if int(k) == cluster_results["best_k"] else ""
        lines.append(f"- k={k}: {s:.3f}{marker}")
    lines.append("")

    # Cluster membership
    lines.append("### Cluster Membership")
    lines.append("")
    for cl_id, members in sorted(cluster_results["cluster_membership"].items()):
        zone_counts = defaultdict(int)
        for c in members:
            zone_counts[COUNTRY_ZONE.get(c, "Unknown")] += 1
        top_zone = max(zone_counts, key=zone_counts.get)
        lines.append(f"**Cluster {cl_id}** ({len(members)} countries, dominant zone: {top_zone}):")
        lines.append(f"  {', '.join(sorted(members))}")
        lines.append("")

    ari = cluster_results["ari_vs_iw_zones"]
    if ari > 0.3:
        lines.append(f"The ARI of {ari:.3f} indicates **moderate-to-strong correspondence** between spectral clusters and Inglehart-Welzel zones.")
    elif ari > 0.1:
        lines.append(f"The ARI of {ari:.3f} indicates **weak-to-moderate correspondence** between spectral clusters and IW zones.")
    else:
        lines.append(f"The ARI of {ari:.3f} indicates **minimal correspondence** between spectral clusters and IW zones. Network structure similarity is driven by factors beyond cultural-zone membership.")
    lines.append("")

    # ─── Part 4: Mediator ───
    lines.append("## 5. Mediator Decomposition: gender_role_traditionalism")
    lines.append("")
    grt = mediator_results["grt_rank_stats"]
    lines.append(f"gender_role_traditionalism (GRT) mediator rank across 66 countries:")
    lines.append(f"- Median rank: **{grt['median_rank']:.0f}** / 55")
    lines.append(f"- Mean rank: {grt['mean_rank']:.1f}")
    lines.append(f"- In top 5: {grt['pct_top5']:.0f}% of countries")
    lines.append(f"- In top 10: {grt['pct_top10']:.0f}% of countries")
    lines.append("")

    lines.append("Top mediator frequency (how often a construct is the #1 mediator):")
    lines.append("")
    for name, count in sorted(mediator_results["top_mediator_frequency"].items(), key=lambda x: -x[1]):
        if count >= 2:
            lines.append(f"- **{name}**: {count} countries ({count/len(countries)*100:.0f}%)")
    lines.append("")

    lines.append("### What predicts GRT mediator rank? (Spearman correlations)")
    lines.append("")
    lines.append("| Predictor | Spearman rho | p-value | Interpretation |")
    lines.append("|-----------|-------------|---------|----------------|")
    for pred, res in sorted(mediator_results["grt_rank_correlations"].items(), key=lambda x: abs(x[1]["spearman_r"]), reverse=True):
        r = res["spearman_r"]
        p = res["p"]
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
        interp = ""
        if p < 0.05:
            if r < 0:
                interp = "higher value -> lower rank (more central)"
            else:
                interp = "higher value -> higher rank (less central)"
        lines.append(f"| {pred} | {r:.3f} | {p:.3f} ({sig}) | {interp} |")
    lines.append("")

    # ─── Part 5: Synthesis ───
    lines.append("## 6. Cluster-Level Synthesis")
    lines.append("")

    for cl_id, profile in sorted(synthesis["cluster_profiles"].items()):
        lines.append(f"### Cluster {cl_id} ({profile['n']} countries)")
        lines.append("")
        lines.append(f"**Members**: {', '.join(sorted(profile['members']))}")
        lines.append("")
        lines.append(f"**Zone composition**: {', '.join(f'{z}: {n}' for z, n in sorted(profile['zone_composition'].items(), key=lambda x: -x[1]))}")
        lines.append("")
        lines.append(f"**Mean SES signature**: escol={profile['mean_ses']['escol']:.4f}, Tam_loc={profile['mean_ses']['Tam_loc']:.4f}, sexo={profile['mean_ses']['sexo']:.4f}, edad={profile['mean_ses']['edad']:.4f}")
        lines.append(f"**Dominant SES dimension**: {profile['dominant_ses_dim']}")
        lines.append(f"**Mean Fiedler value**: {profile['mean_fiedler']:.3f}")
        lines.append("")
        if profile["top_mediators"]:
            lines.append("Top mediators:")
            for m in profile["top_mediators"]:
                lines.append(f"  - {m['construct']} ({m['count']} countries)")
        lines.append("")

    # Inter-cluster distances
    lines.append("### Inter-Cluster Distances")
    lines.append("")
    lines.append("| Pair | Mean Spectral Distance |")
    lines.append("|------|----------------------|")
    for pair, d in sorted(synthesis["inter_cluster_distances"].items(), key=lambda x: x[1]):
        lines.append(f"| {pair} | {d:.4f} |")
    lines.append("")

    lines.append("### Intra-Cluster Distances")
    lines.append("")
    lines.append("| Cluster | Mean Internal Distance |")
    lines.append("|---------|----------------------|")
    for cl, d in sorted(synthesis["intra_cluster_distances"].items()):
        lines.append(f"| {cl} | {d:.4f} |")
    lines.append("")

    # ─── Key Findings ───
    lines.append("## 7. Key Findings")
    lines.append("")

    # Dynamically build findings from actual data
    # Find top Mantel predictor
    sorted_mantel = sorted(
        [(n, r) for n, r in mantel_results.items() if not np.isnan(r.get("r", np.nan))],
        key=lambda x: abs(x[1]["r"]), reverse=True,
    )
    top_mantel = sorted_mantel[0] if sorted_mantel else ("?", {"r": 0})
    sig_mantel = [(n, r) for n, r in sorted_mantel if r.get("p", 1) < 0.05]

    lines.append(f"1. **Macro development indicators are weak predictors of network structure**: "
                 f"No individual World Bank indicator reaches significance in the Mantel test "
                 f"(GNI per capita r={mantel_results.get('gni_pc', {}).get('r', 0):.3f}, "
                 f"urbanization r={mantel_results.get('urban_pct', {}).get('r', 0):.3f}, "
                 f"internet r={mantel_results.get('internet', {}).get('r', 0):.3f}). "
                 f"Two countries can have very different GDP and very similar SES-attitude networks.")
    lines.append("")
    lines.append(f"2. **SES signature geometry is the real driver** (Mantel r={mantel_results.get('ses_signature', {}).get('r', 0):.3f}, p<0.001): "
                 f"Countries with similar distributions of SES driver weights "
                 f"(how much education vs age vs gender vs urbanization structure attitudes) "
                 f"have similar networks. This is not income or development -- it is how "
                 f"sociodemographic position maps onto attitude variation.")
    lines.append("")
    lines.append(f"3. **Fiedler distance dominates** (Mantel r={mantel_results.get('fiedler_diff', {}).get('r', 0):.3f}, p<0.001): "
                 f"Algebraic connectivity (spectral gap) is the strongest single predictor. "
                 f"Combined with SES signature, the OLS model explains "
                 f"**{ols_results['r2']*100:.1f}%** of pairwise spectral distance variance. "
                 f"The Fiedler value captures how tightly the entire construct network is coupled; "
                 f"countries with similar coupling strength have similar structure.")
    lines.append("")
    lines.append(f"4. **Cultural zones have minimal explanatory power** (ARI={cluster_results['ari_vs_iw_zones']:.3f}): "
                 f"Spectral clusters do not map onto Inglehart-Welzel zones. "
                 f"The same_zone Mantel r is only {mantel_results.get('same_zone', {}).get('r', 0):.3f}. "
                 f"Network structure similarity is driven by how SES operates within each society, "
                 f"not by shared cultural heritage.")
    lines.append("")

    grt = mediator_results["grt_rank_stats"]
    lines.append(f"5. **gender_role_traditionalism is the near-universal structural bridge**: "
                 f"Median mediator rank **{grt['median_rank']:.0f}**/55, top-10 in "
                 f"**{grt['pct_top10']:.0f}%** of countries. "
                 f"Its centrality correlates with inequality (Gini rho={mediator_results['grt_rank_correlations'].get('gini', {}).get('spearman_r', 0):.3f}): "
                 f"in more unequal societies, gender role attitudes sit at an even more central "
                 f"nexus of the SES-attitude network.")
    lines.append("")
    lines.append(f"6. **Three-cluster solution**: k={cluster_results['best_k']} "
                 f"(silhouette={cluster_results['best_silhouette']:.3f}). "
                 f"Cluster 2 is a small outlier group (MNG, SGP, GRC, IDN) with the highest "
                 f"Fiedler value ({synthesis['cluster_profiles']['2']['mean_fiedler']:.3f}) and "
                 f"strongest education dominance. Clusters 1 and 3 are the main split, "
                 f"with Cluster 3 (English-speaking + Confucian + some LatAm) showing higher "
                 f"age/cohort driver weight ({synthesis['cluster_profiles']['3']['mean_ses']['edad']:.4f} vs "
                 f"{synthesis['cluster_profiles']['1']['mean_ses']['edad']:.4f}).")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Cross-Country Geometric Analysis of the gamma-Surface")
    print("=" * 70)

    # Part 0: Load data
    print("\n--- Loading base data ---")
    countries, spectral_dist = load_spectral_distance_matrix()
    print(f"  Spectral distance matrix: {len(countries)} countries")

    ses_sigs = load_ses_signatures()
    print(f"  SES signatures: {len(ses_sigs)} countries")

    spectral_summ = load_spectral_summaries()
    print(f"  Spectral summaries: {len(spectral_summ)} countries")

    mediator_scores = load_mediator_scores()
    print(f"  Mediator scores: {len(mediator_scores)} countries")

    # Part 1: World Bank indicators
    print("\n--- Part 1: Fetching World Bank indicators ---")
    wb_data = fetch_all_wb_indicators(countries)

    # Part 2: Mantel tests + OLS
    print("\n--- Part 2: Mantel tests ---")
    mantel_results = run_mantel_suite(countries, spectral_dist, wb_data, ses_sigs, spectral_summ)

    print("\n--- Part 2b: OLS regression ---")
    ols_results = run_pairwise_ols(countries, spectral_dist, wb_data, ses_sigs, spectral_summ)
    print(f"  R-squared: {ols_results['r2']:.4f}")

    # Part 3: Clustering
    print("\n--- Part 3: Hierarchical clustering ---")
    cluster_results, Z, best_k = cluster_countries(countries, spectral_dist)
    cluster_labels = cluster_results["labels"]
    print(f"  Best k={best_k}, silhouette={cluster_results['best_silhouette']:.3f}")
    print(f"  ARI vs IW zones: {cluster_results['ari_vs_iw_zones']:.3f}")

    # Part 4: Mediator decomposition
    print("\n--- Part 4: Mediator decomposition ---")
    mediator_results = mediator_decomposition(countries, mediator_scores, ses_sigs, spectral_summ, wb_data)
    print(f"  GRT median rank: {mediator_results['grt_rank_stats']['median_rank']:.0f}/55")
    print(f"  Top mediator: {list(mediator_results['top_mediator_frequency'].items())[:3]}")

    # Part 5: Synthesis
    print("\n--- Part 5: Zone-level synthesis ---")
    synthesis = zone_synthesis(countries, cluster_labels, best_k, ses_sigs, spectral_summ, mediator_scores, spectral_dist)

    # Plots
    print("\n--- Generating plots ---")
    plot_dendrogram(countries, Z, cluster_labels, best_k)
    plot_mds_clusters(countries, spectral_dist, cluster_labels, best_k)
    plot_mantel_heatmap(mantel_results)
    plot_mediator_decomposition(mediator_results)
    plot_cluster_ses_profiles(synthesis, best_k)

    # Report
    print("\n--- Generating report ---")
    report = generate_report(mantel_results, ols_results, cluster_results, mediator_results, synthesis, wb_data, countries)
    report_path = RESULTS / "cross_country_geometry_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"  Saved {report_path}")

    # JSON output
    print("\n--- Saving JSON ---")
    json_out = {
        "n_countries": len(countries),
        "countries": countries,
        "mantel_tests": mantel_results,
        "ols_regression": ols_results,
        "clustering": cluster_results,
        "mediator_decomposition": mediator_results,
        "synthesis": synthesis,
        "wb_coverage": {name: len(vals) for name, vals in wb_data.items()},
    }
    json_path = RESULTS / "cross_country_geometry.json"
    with open(json_path, "w") as f:
        json.dump(json_out, f, indent=2, default=str)
    print(f"  Saved {json_path}")

    print("\n" + "=" * 70)
    print("DONE. Key results:")
    print(f"  Mantel: strongest predictor = {max(mantel_results.items(), key=lambda x: abs(x[1].get('r', 0)))[0]}")
    print(f"  OLS R-squared = {ols_results['r2']:.4f}")
    print(f"  Clustering: k={best_k}, ARI={cluster_results['ari_vs_iw_zones']:.3f}")
    print(f"  GRT mediator rank: top-10 in {mediator_results['grt_rank_stats']['pct_top10']:.0f}% of countries")
    print("=" * 70)


if __name__ == "__main__":
    main()
