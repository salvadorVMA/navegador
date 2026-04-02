"""
Phase 5 — MDS Embeddings + Cultural Zone Coherence Tests

Takes the distance matrices from Phase 3 (spectral) and Phase 4 (bottleneck)
and produces:
  1. 2D MDS embeddings colored by cultural zone
  2. Silhouette scores for cultural zone clustering
  3. Permutation tests for zone coherence (is within-zone distance < between-zone?)
  4. Combined summary of topological + spectral features

── Why MDS? ───────────────────────────────────────────────────────────────────

MDS (Multidimensional Scaling) finds coordinates in R^d that preserve pairwise
distances as well as possible. Unlike PCA (which needs vector input), MDS works
directly from a distance matrix — perfect for spectral/bottleneck distances.

We use classical MDS (Torgersen, 1952) via eigendecomposition of the doubly-
centered distance matrix: B = -½ H D² H where H = I - 11'/n.

Input:
  data/tda/spectral/spectral_distance_matrix.csv    — from Phase 3
  data/tda/persistence/bottleneck_distances.csv      — from Phase 4
  data/tda/persistence/topological_features.csv      — from Phase 4
  data/tda/ricci/ricci_summary.json                  — from Phase 2

Output:
  data/tda/embeddings/mds_spectral_2d.png
  data/tda/embeddings/mds_bottleneck_2d.png
  data/tda/embeddings/zone_coherence.json
  data/tda/embeddings/combined_features.csv

Run:
  python scripts/debug/tda_embeddings_and_zones.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.manifold import MDS
from sklearn.metrics import silhouette_score

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

# Allow env var overrides for allwave pipeline (default: v1 paths)
SPECTRAL_PATH  = Path(os.environ.get("TDA_SPECTRAL_PATH",
                      str(ROOT / "data" / "tda" / "spectral" / "spectral_distance_matrix.csv")))
BOTTLENECK_PATH = Path(os.environ.get("TDA_BOTTLENECK_PATH",
                       str(ROOT / "data" / "tda" / "persistence" / "bottleneck_distances.csv")))
FEATURES_PATH  = Path(os.environ.get("TDA_FEATURES_PATH",
                      str(ROOT / "data" / "tda" / "persistence" / "topological_features.csv")))
RICCI_PATH     = Path(os.environ.get("TDA_RICCI_PATH",
                      str(ROOT / "data" / "tda" / "ricci" / "ricci_summary.json")))
MEDIATOR_PATH  = Path(os.environ.get("TDA_MEDIATOR_PATH",
                      str(ROOT / "data" / "tda" / "floyd_warshall" / "mediator_scores.json")))
SPECTRAL_FEAT  = Path(os.environ.get("TDA_SPECTRAL_FEAT",
                      str(ROOT / "data" / "tda" / "spectral" / "spectral_features.json")))
OUTPUT_DIR     = Path(os.environ.get("TDA_OUTPUT_DIR",
                      str(ROOT / "data" / "tda" / "embeddings")))
MANIFEST_PATH  = Path(os.environ.get("TDA_MANIFEST",
                      str(ROOT / "data" / "tda" / "matrices" / "manifest.json")))

# Zone colors (consistent with existing navegador visualizations)
ZONE_COLORS = {
    "Latin America": "#e74c3c",
    "English-speaking": "#3498db",
    "Protestant Europe": "#2ecc71",
    "Catholic Europe": "#9b59b6",
    "Orthodox/ex-Communist": "#f39c12",
    "Confucian": "#1abc9c",
    "South/Southeast Asian": "#e67e22",
    "African-Islamic": "#95a5a6",
    "Unknown": "#bdc3c7",
}


# ── MDS embedding ─────────────────────────────────────────────────────────────

def mds_embed(
    D: np.ndarray,
    countries: list[str],
    n_components: int = 2,
) -> np.ndarray:
    """
    Classical MDS embedding of a distance matrix into R^d.

    Handles NaN by replacing with median distance (conservative imputation).
    Returns (n, d) coordinate array.
    """
    D_clean = D.copy()
    # Replace NaN with median of valid distances
    valid = D_clean[~np.isnan(D_clean) & (D_clean > 0)]
    if len(valid) > 0:
        D_clean[np.isnan(D_clean)] = np.median(valid)

    mds = MDS(
        n_components=n_components,
        dissimilarity="precomputed",
        random_state=42,
        normalized_stress="auto",
    )
    coords = mds.fit_transform(D_clean)
    return coords


def plot_mds(
    coords: np.ndarray,
    countries: list[str],
    title: str,
    output_path: Path,
):
    """
    Plot 2D MDS embedding with points colored by cultural zone.
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    for zone, zone_countries in CULTURAL_ZONES.items():
        zone_indices = [i for i, c in enumerate(countries) if c in zone_countries]
        if not zone_indices:
            continue
        x = coords[zone_indices, 0]
        y = coords[zone_indices, 1]
        ax.scatter(x, y, c=ZONE_COLORS.get(zone, "#bdc3c7"),
                   label=zone, s=80, alpha=0.8, edgecolors="white", linewidths=0.5)
        for idx in zone_indices:
            ax.annotate(countries[idx], (coords[idx, 0], coords[idx, 1]),
                        fontsize=7, ha="center", va="bottom",
                        textcoords="offset points", xytext=(0, 5))

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("MDS dimension 1")
    ax.set_ylabel("MDS dimension 2")
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path.name}")


# ── Zone coherence tests ─────────────────────────────────────────────────────

def zone_coherence_permutation(
    D: np.ndarray,
    countries: list[str],
    n_permutations: int = 10000,
) -> dict:
    """
    Test whether cultural zones are coherent clusters in distance space.

    Computes the within-zone / between-zone distance ratio and tests whether
    it's significantly smaller than expected by random zone assignment.

    This is similar to PERMANOVA (Anderson 2001) but uses a simpler statistic:
    R = mean(within-zone distances) / mean(between-zone distances)
    R < 1 means zones are more internally coherent than random groupings.

    Also computes silhouette scores (Rousseeuw 1987) using zone labels.
    """
    nc = len(countries)
    zone_labels = [COUNTRY_ZONE.get(c, "Unknown") for c in countries]
    unique_zones = sorted(set(zone_labels))
    zone_idx = {z: i for i, z in enumerate(unique_zones)}
    labels = np.array([zone_idx[z] for z in zone_labels])

    # Handle NaN
    D_clean = D.copy()
    valid = D_clean[~np.isnan(D_clean) & (D_clean > 0)]
    if len(valid) > 0:
        D_clean[np.isnan(D_clean)] = np.median(valid)

    def compute_ratio(lab):
        """Compute within/between distance ratio for given labels."""
        within = []
        between = []
        for i in range(nc):
            for j in range(i + 1, nc):
                if lab[i] == lab[j]:
                    within.append(D_clean[i, j])
                else:
                    between.append(D_clean[i, j])
        if not within or not between:
            return 1.0
        return np.mean(within) / np.mean(between)

    observed_ratio = compute_ratio(labels)

    # Permutation test: shuffle zone labels and recompute ratio
    rng = np.random.default_rng(42)
    null_ratios = np.empty(n_permutations)
    for p in range(n_permutations):
        shuffled = labels.copy()
        rng.shuffle(shuffled)
        null_ratios[p] = compute_ratio(shuffled)

    p_value = float(np.mean(null_ratios <= observed_ratio))

    # Silhouette score (requires at least 2 labels with ≥1 member)
    try:
        sil = float(silhouette_score(D_clean, labels, metric="precomputed"))
    except ValueError:
        sil = 0.0

    # Per-zone within-zone mean distance
    zone_within = {}
    for z in unique_zones:
        z_idx = [i for i, l in enumerate(zone_labels) if l == z]
        if len(z_idx) < 2:
            continue
        dists = [D_clean[i, j] for i in z_idx for j in z_idx if i < j]
        if dists:
            zone_within[z] = {
                "mean_within_dist": round(float(np.mean(dists)), 4),
                "n_countries": len(z_idx),
            }

    return {
        "observed_ratio": round(observed_ratio, 4),
        "p_value": round(p_value, 4),
        "silhouette": round(sil, 4),
        "n_permutations": n_permutations,
        "interpretation": (
            "significant" if p_value < 0.05
            else "marginal" if p_value < 0.10
            else "not significant"
        ),
        "zone_within_distances": zone_within,
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TDA Phase 5 — MDS Embeddings + Zone Coherence")
    print("=" * 60)

    coherence_results = {}

    # ── Spectral distance embedding ───────────────────────────────────────
    if SPECTRAL_PATH.exists():
        print("\n[1/4] Spectral distance embedding...")
        spec_df = pd.read_csv(SPECTRAL_PATH, index_col=0)
        countries_spec = list(spec_df.index)
        D_spec = spec_df.values

        coords = mds_embed(D_spec, countries_spec)
        plot_mds(coords, countries_spec,
                 "MDS of Spectral Distances — WVS Construct Networks (W7)",
                 OUTPUT_DIR / "mds_spectral_2d.png")

        print("  Testing zone coherence (spectral)...")
        coherence_results["spectral"] = zone_coherence_permutation(
            D_spec, countries_spec
        )
        r = coherence_results["spectral"]
        print(f"    Ratio: {r['observed_ratio']:.3f}, "
              f"p={r['p_value']:.4f} ({r['interpretation']}), "
              f"silhouette={r['silhouette']:.3f}")
    else:
        print("  SKIP: spectral distance matrix not found")

    # ── Bottleneck distance embedding ─────────────────────────────────────
    if BOTTLENECK_PATH.exists():
        print("\n[2/4] Bottleneck distance embedding...")
        bn_df = pd.read_csv(BOTTLENECK_PATH, index_col=0)
        countries_bn = list(bn_df.index)
        D_bn = bn_df.values

        coords = mds_embed(D_bn, countries_bn)
        plot_mds(coords, countries_bn,
                 "MDS of Bottleneck Distances (H₁) — WVS Construct Networks (W7)",
                 OUTPUT_DIR / "mds_bottleneck_2d.png")

        print("  Testing zone coherence (bottleneck)...")
        coherence_results["bottleneck"] = zone_coherence_permutation(
            D_bn, countries_bn
        )
        r = coherence_results["bottleneck"]
        print(f"    Ratio: {r['observed_ratio']:.3f}, "
              f"p={r['p_value']:.4f} ({r['interpretation']}), "
              f"silhouette={r['silhouette']:.3f}")
    else:
        print("  SKIP: bottleneck distance matrix not found")

    # ── Combined feature table ────────────────────────────────────────────
    print("\n[3/4] Building combined feature table...")
    combined = None

    if FEATURES_PATH.exists():
        topo_df = pd.read_csv(FEATURES_PATH)
        combined = topo_df.copy()

    # Add Ricci summary features
    if RICCI_PATH.exists():
        with open(RICCI_PATH) as f:
            ricci = json.load(f)
        ricci_rows = []
        for c in combined["country"] if combined is not None else []:
            if c in ricci and "mean" in ricci[c]:
                ricci_rows.append({
                    "country": c,
                    "ricci_mean": ricci[c]["mean"],
                    "ricci_min": ricci[c]["min"],
                    "frac_negative_ricci": ricci[c]["frac_negative"],
                })
            else:
                ricci_rows.append({"country": c})
        if ricci_rows and combined is not None:
            ricci_df = pd.DataFrame(ricci_rows)
            combined = combined.merge(ricci_df, on="country", how="left")

    # Add spectral features
    if SPECTRAL_FEAT.exists():
        with open(SPECTRAL_FEAT) as f:
            spec_feat = json.load(f)
        spec_rows = []
        for c in combined["country"] if combined is not None else []:
            if c in spec_feat:
                spec_rows.append({
                    "country": c,
                    "fiedler_value": spec_feat[c].get("fiedler_value"),
                    "spectral_gap": spec_feat[c].get("spectral_gap"),
                    "spectral_entropy": spec_feat[c].get("spectral_entropy"),
                })
            else:
                spec_rows.append({"country": c})
        if spec_rows and combined is not None:
            spec_df = pd.DataFrame(spec_rows)
            combined = combined.merge(spec_df, on="country", how="left")

    # Add mediator info
    if MEDIATOR_PATH.exists():
        with open(MEDIATOR_PATH) as f:
            mediators = json.load(f)
        med_rows = []
        for c in combined["country"] if combined is not None else []:
            if c in mediators:
                med_rows.append({
                    "country": c,
                    "top_mediator": mediators[c].get("top_mediator"),
                    "top_mediator_score": mediators[c].get("top_score"),
                    "n_triangle_violations": mediators[c].get("n_violations"),
                })
            else:
                med_rows.append({"country": c})
        if med_rows and combined is not None:
            med_df = pd.DataFrame(med_rows)
            combined = combined.merge(med_df, on="country", how="left")

    if combined is not None:
        combined.to_csv(OUTPUT_DIR / "combined_features.csv", index=False)
        print(f"  Combined features: {len(combined)} countries × {len(combined.columns)} features")
    else:
        print("  SKIP: no feature data found")

    # ── Save coherence results ────────────────────────────────────────────
    print("\n[4/4] Saving coherence results...")
    with open(OUTPUT_DIR / "zone_coherence.json", "w") as f:
        json.dump(coherence_results, f, indent=2)

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    for metric, result in coherence_results.items():
        print(f"  {metric}: within/between ratio = {result['observed_ratio']:.3f}, "
              f"p = {result['p_value']:.4f}, silhouette = {result['silhouette']:.3f}")
    print(f"  Output: {OUTPUT_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
