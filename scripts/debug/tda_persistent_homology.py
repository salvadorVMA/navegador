"""
Phase 4 — Persistent Homology via Ripser

Computes topological features (Betti numbers, persistence diagrams, bottleneck
distances) for each country's construct network using the Vietoris-Rips filtration.

── Mathematical background ────────────────────────────────────────────────────

Persistent homology tracks how topological features are born and die as we sweep
a distance threshold ε from 0 to ∞:

  H₀ (connected components):
    At ε=0, every construct is isolated (55 components).
    As ε increases, edges appear and components merge.
    The "persistence" of a component = ε_death - ε_birth.
    Long-lived H₀ features = well-separated clusters of constructs.

  H₁ (loops / 1-cycles):
    A loop appears when an edge connects two constructs that are already
    connected by a path. It dies when the loop gets "filled in" by a triangle.
    Long-lived H₁ features = robust loops that resist triangulation.
    In our context: three constructs where A↔B and B↔C are strong but A↔C is weak
    (non-transitive SES relationships).

  H₂ (voids / 2-cycles):
    Hollow tetrahedra — four constructs where all faces are triangulated but
    the interior is empty. Rare in practice for n=55 at max_dim=2.

The persistence diagram D = {(birth_i, death_i)} is the complete topological
summary. Points far from the diagonal = robust features; near-diagonal = noise.

Bottleneck distance between two persistence diagrams:
  d_B(D₁, D₂) = inf_γ sup_x ||x - γ(x)||∞
  where γ ranges over all bijections between D₁ and D₂ (including projections
  to the diagonal). This is the "largest difference" between matched features.

References:
  Edelsbrunner & Harer (2010), "Computational Topology: An Introduction"
  Ghrist (2008), "Barcodes: The Persistent Topology of Data", AMS Bull.
  Ripser: Bauer (2021), "Ripser: efficient computation of Vietoris-Rips
    persistence barcodes", JACT.

Input:
  data/tda/matrices/manifest.json      — country list + distance matrix paths
  data/tda/floyd_warshall/*_shortest_paths.csv  — from Phase 1

Output:
  data/tda/persistence/topological_features.csv  — per-country feature table
  data/tda/persistence/bottleneck_distances.csv  — 66×66 pairwise bottleneck
  data/tda/persistence/persistence_data.json     — raw diagram data

Run:
  python scripts/debug/tda_persistent_homology.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from ripser import ripser
from persim import bottleneck

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

MANIFEST_PATH = ROOT / "data" / "tda" / "matrices" / "manifest.json"
FW_DIR        = ROOT / "data" / "tda" / "floyd_warshall"
OUTPUT_DIR    = ROOT / "data" / "tda" / "persistence"

# Persistence features with lifetime < threshold are considered noise.
# 0.05 means only features persisting through >5% of the distance range are kept.
PERSISTENCE_THRESHOLD = 0.05
# Maximum homology dimension to compute (H0, H1, H2)
MAX_DIM = 2


# ── Persistent homology computation ──────────────────────────────────────────

def compute_persistence(D: np.ndarray, max_dim: int = MAX_DIM) -> dict:
    """
    Run Vietoris-Rips persistent homology on a distance matrix.

    The Vietoris-Rips complex at threshold ε includes all simplices (edges,
    triangles, tetrahedra...) whose vertices are pairwise within distance ε.
    Ripser computes this incrementally as ε grows from 0 to max_threshold.

    Parameters:
        D: n×n distance matrix (symmetric, non-negative)
        max_dim: maximum homology dimension (2 = compute H0, H1, H2)

    Returns:
        dict with persistence diagrams, Betti numbers, persistence stats
    """
    # Cap infinite/sentinel distances at a reasonable threshold
    # (prevents ripser from allocating huge memory for distant pairs)
    D_capped = np.copy(D)
    D_capped[D_capped >= 9000] = np.max(D_capped[D_capped < 9000]) * 1.1

    # Normalize to [0, 1] for comparable persistence values across countries
    d_max = np.max(D_capped[D_capped > 0])
    if d_max > 0:
        D_norm = D_capped / d_max
    else:
        D_norm = D_capped

    result = ripser(D_norm, maxdim=max_dim, distance_matrix=True, thresh=1.0)
    dgms = result["dgms"]

    return {
        "dgms": dgms,
        "H0": dgms[0],
        "H1": dgms[1] if len(dgms) > 1 else np.empty((0, 2)),
        "H2": dgms[2] if len(dgms) > 2 else np.empty((0, 2)),
        "d_max": float(d_max),
    }


def significant_features(dgm: np.ndarray, threshold: float = PERSISTENCE_THRESHOLD) -> np.ndarray:
    """
    Filter persistence diagram to keep only features with lifetime > threshold.

    Lifetime = death - birth. Short-lived features are typically topological noise
    (random fluctuations in edge weights). Long-lived features represent genuine
    topological structure (robust clusters, persistent loops).
    """
    if len(dgm) == 0:
        return np.empty((0, 2))
    # Remove infinite features (the one essential H0 component)
    finite = dgm[~np.isinf(dgm).any(axis=1)]
    if len(finite) == 0:
        return np.empty((0, 2))
    lifetimes = finite[:, 1] - finite[:, 0]
    return finite[lifetimes > threshold]


def persistence_entropy(dgm: np.ndarray) -> float:
    """
    Persistence entropy: Shannon entropy of the lifetime distribution.

    H = -Σ pᵢ log(pᵢ)  where pᵢ = lifetime_i / Σ lifetimes

    High entropy = many features with similar lifetimes (complex topology).
    Low entropy = one dominant feature (simple topology).
    Zero entropy = only one feature (trivial).

    This is a single number summarizing the "complexity" of the persistence diagram.
    """
    finite = dgm[~np.isinf(dgm).any(axis=1)]
    if len(finite) == 0:
        return 0.0
    lifetimes = finite[:, 1] - finite[:, 0]
    lifetimes = lifetimes[lifetimes > 0]
    if len(lifetimes) == 0:
        return 0.0
    p = lifetimes / lifetimes.sum()
    return float(-np.sum(p * np.log(p + 1e-12)))


def total_persistence(dgm: np.ndarray, p: int = 1) -> float:
    """
    Total persistence: sum of lifetime^p for all features.

    p=1: total persistence (sum of lifetimes)
    p=2: persistence variance (related to Wasserstein-2 distance)

    Higher total persistence = more topological "content" in the network.
    """
    finite = dgm[~np.isinf(dgm).any(axis=1)]
    if len(finite) == 0:
        return 0.0
    lifetimes = finite[:, 1] - finite[:, 0]
    return float(np.sum(np.abs(lifetimes) ** p))


def max_persistence(dgm: np.ndarray) -> float:
    """Maximum lifetime of any feature (excluding infinite H0)."""
    finite = dgm[~np.isinf(dgm).any(axis=1)]
    if len(finite) == 0:
        return 0.0
    lifetimes = finite[:, 1] - finite[:, 0]
    return float(np.max(lifetimes)) if len(lifetimes) > 0 else 0.0


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TDA Phase 4 — Persistent Homology (Ripser)")
    print("=" * 60)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    countries = manifest["countries"]
    constructs = manifest["construct_index"]
    print(f"Countries: {len(countries)}, Constructs: {len(constructs)}")

    # ── Compute persistence for each country ──────────────────────────────
    print("\n[1/3] Computing persistence diagrams...")
    all_persistence: dict[str, dict] = {}
    feature_rows = []

    for i, alpha3 in enumerate(countries):
        # Use shortest-path distances from Phase 1 (more geometrically meaningful
        # than raw distance matrices — they satisfy the triangle inequality)
        sp_path = FW_DIR / f"{alpha3}_shortest_paths.csv"
        if sp_path.exists():
            D_df = pd.read_csv(sp_path, index_col=0)
            D = D_df.values
        else:
            # Fallback to raw distance matrix
            d_path = Path(manifest["files"][alpha3]["distance"])
            D_df = pd.read_csv(d_path, index_col=0)
            D = D_df.values

        pers = compute_persistence(D)
        all_persistence[alpha3] = pers

        # Extract features
        sig_h0 = significant_features(pers["H0"])
        sig_h1 = significant_features(pers["H1"])
        sig_h2 = significant_features(pers["H2"])

        row = {
            "country": alpha3,
            "zone": COUNTRY_ZONE.get(alpha3, "Unknown"),
            # Betti numbers = count of significant features per dimension
            "betti_0": len(sig_h0),
            "betti_1": len(sig_h1),
            "betti_2": len(sig_h2),
            # Total persistence (sum of lifetimes)
            "total_pers_H0": total_persistence(pers["H0"]),
            "total_pers_H1": total_persistence(pers["H1"]),
            "total_pers_H2": total_persistence(pers["H2"]),
            # Maximum persistence (longest-lived feature)
            "max_pers_H0": max_persistence(pers["H0"]),
            "max_pers_H1": max_persistence(pers["H1"]),
            "max_pers_H2": max_persistence(pers["H2"]),
            # Persistence entropy (complexity measure)
            "entropy_H0": persistence_entropy(pers["H0"]),
            "entropy_H1": persistence_entropy(pers["H1"]),
            # Raw feature counts (before filtering)
            "n_features_H0": len(pers["H0"]),
            "n_features_H1": len(pers["H1"]),
            "n_features_H2": len(pers["H2"]),
        }
        feature_rows.append(row)

        if (i + 1) % 10 == 0 or i == len(countries) - 1:
            print(f"  [{i+1}/{len(countries)}] {alpha3}: "
                  f"β₀={row['betti_0']}, β₁={row['betti_1']}, β₂={row['betti_2']}, "
                  f"H1_pers={row['total_pers_H1']:.3f}")

    # Save feature table
    features_df = pd.DataFrame(feature_rows)
    features_df.to_csv(OUTPUT_DIR / "topological_features.csv", index=False)
    print(f"\n  Feature table: {OUTPUT_DIR / 'topological_features.csv'}")

    # ── Pairwise bottleneck distances ─────────────────────────────────────
    print("\n[2/3] Computing pairwise bottleneck distances (H1)...")
    nc = len(countries)
    D_bottleneck = np.zeros((nc, nc))

    for i in range(nc):
        for j in range(i + 1, nc):
            dgm_i = all_persistence[countries[i]]["H1"]
            dgm_j = all_persistence[countries[j]]["H1"]

            # persim.bottleneck handles empty diagrams gracefully
            d = bottleneck(dgm_i, dgm_j)
            D_bottleneck[i, j] = d
            D_bottleneck[j, i] = d

    bn_df = pd.DataFrame(D_bottleneck, index=countries, columns=countries)
    bn_df.to_csv(OUTPUT_DIR / "bottleneck_distances.csv")
    print(f"  Bottleneck matrix: {OUTPUT_DIR / 'bottleneck_distances.csv'}")

    # ── Save raw persistence data ─────────────────────────────────────────
    print("\n[3/3] Saving persistence data...")
    pers_data = {}
    for alpha3, pers in all_persistence.items():
        pers_data[alpha3] = {
            "H0": pers["H0"].tolist(),
            "H1": pers["H1"].tolist(),
            "H2": pers["H2"].tolist(),
            "d_max": pers["d_max"],
        }
    with open(OUTPUT_DIR / "persistence_data.json", "w") as f:
        json.dump(pers_data, f, indent=2)

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  Countries: {nc}")
    print(f"  Mean β₁ (significant H1 features): {features_df['betti_1'].mean():.1f}")
    print(f"  Max β₁: {features_df['betti_1'].max()} ({features_df.loc[features_df['betti_1'].idxmax(), 'country']})")
    print(f"  Mean total H1 persistence: {features_df['total_pers_H1'].mean():.3f}")

    # Zone-level summary
    print(f"\n  Zone averages (β₁):")
    zone_means = features_df.groupby("zone")["betti_1"].mean().sort_values(ascending=False)
    for zone, val in zone_means.items():
        print(f"    {zone}: {val:.1f}")

    upper = D_bottleneck[np.triu_indices(nc, k=1)]
    print(f"\n  Bottleneck distance range: [{upper.min():.4f}, {upper.max():.4f}]")
    print(f"  Mean bottleneck distance: {upper.mean():.4f}")
    print(f"  Output: {OUTPUT_DIR}")
    print("Done.")


if __name__ == "__main__":
    main()
