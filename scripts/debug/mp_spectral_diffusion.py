"""
Spectral Analysis & Heat Diffusion on WVS Construct Networks
=============================================================

Stage 2 of the message-passing framework.

What this computes
------------------
Given a weighted graph of 55 WVS constructs (edges = |gamma| magnitudes from
the DR bridge), we build the **normalized graph Laplacian** and perform its
full eigendecomposition.  The eigenvalues and eigenvectors encode the
network's geometry in a basis-free way:

  L = D^{-1/2} (D - W) D^{-1/2}

where D is the diagonal degree matrix and W is the symmetrized |gamma|
weight matrix.  Eigenvalues lambda_0 <= lambda_1 <= ... <= lambda_{k-1}
capture connectivity at different scales, and eigenvectors define a spectral
embedding of the constructs.

From this decomposition, several analyses follow:

1. **Fiedler partition** (algebraic connectivity).  The second-smallest
   eigenvalue (lambda_1, the "Fiedler value") measures how well-connected
   the graph is.  The corresponding eigenvector (Fiedler vector) provides an
   optimal bipartition: constructs are split into two groups by the sign of
   their Fiedler vector loading.  In our signed gamma networks, this
   typically separates the "cosmopolitan-education" camp from the
   "tradition-locality" camp identified in the SES fingerprint PCA.

2. **Diffusion maps**.  Exponentially weighting eigenvectors by their
   eigenvalue at time t produces a diffusion-map embedding:
     coord_i(t) = (exp(-lambda_1*t)*u_1(i), exp(-lambda_2*t)*u_2(i), ...)
   At small t, fine-grained local structure is visible; at large t, only
   the global partition survives.  This gives a 3D embedding for visualization.

3. **Heat kernel**.  H(t) = U diag(exp(-lambda*t)) U^T is the matrix of
   heat diffusion probabilities.  H(t)[i,j] measures how much "heat"
   (influence, information) diffuses from construct i to construct j in
   time t.  Diagonal entries H(t)[i,i] measure heat retention (isolated
   constructs retain more heat).

4. **Scale sweep**.  For a chosen source construct, we track where heat
   flows at different time scales (t = 0.01 to 10.0).  At small t, only
   direct neighbors receive heat; at large t, heat spreads network-wide.
   The transition reveals the multi-scale structure of construct influence.

5. **Diffusion distance**.  D_t(i,j)^2 = sum_k exp(-2*lambda_k*t) *
   (u_k(i) - u_k(j))^2.  This is a time-parameterized distance metric
   that respects graph geometry: nearby constructs in diffusion distance
   are connected by many short paths, not just one.

6. **Fiedler comparison** (cross-country).  When run with --all, we compute
   the Fiedler partition for all 66 countries and measure pairwise agreement
   using the Adjusted Rand Index.  Countries in the same cultural zone
   should have more similar partitions than countries across zones.

Validation
----------
The computed Fiedler value is compared against the value stored in
spectral_features.json (from the TDA pipeline Phase 3).  A large discrepancy
would indicate a bug in our Laplacian construction or eigendecomposition.

Output
------
Per-country JSON in data/tda/message_passing/{COUNTRY}_spectral.json:
  - fiedler_partition: two groups of constructs + Fiedler value
  - diffusion_map_3d: 3D coordinates per construct at t=1.0
  - scale_sweep: per-time-scale top-5 heat recipients from source
  - fiedler_validation: comparison with spectral_features.json

Cross-country JSON (with --all):
  - fiedler_comparison.json: 66x66 Adjusted Rand Index matrix +
    within-zone vs across-zone mean ARI

Usage
-----
    python scripts/debug/mp_spectral_diffusion.py --country MEX
    python scripts/debug/mp_spectral_diffusion.py --all
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import scipy.linalg

# ── Project paths ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import (  # noqa: E402
    fill_nan_zero,
    get_output_dir,
    load_manifest,
    load_spectral_features,
    load_weight_matrix,
    save_json,
    symmetrize_abs,
)


# ═════════════════════════════════════════════════════════════════════════════
# SpectralAnalyzer — Eigendecomposition + heat diffusion on construct graphs
# ═════════════════════════════════════════════════════════════════════════════

class SpectralAnalyzer:
    """
    Spectral analysis of a weighted construct network.

    Builds the normalized graph Laplacian from a symmetrized |gamma| weight
    matrix and computes its full eigendecomposition.  Provides methods for
    Fiedler partitioning, diffusion maps, heat kernels, and diffusion
    distances.

    Parameters
    ----------
    W : (k, k) ndarray
        Raw weight matrix (may be asymmetric, may contain NaN).
        Absolute values are taken and symmetrized.
    construct_labels : list[str]
        Human-readable label for each of the k nodes.
    """

    def __init__(self, W: np.ndarray, construct_labels: list[str]):
        self.labels = construct_labels
        self.k = W.shape[0]

        # ── Step 1: Symmetrize and clean ──────────────────────────────────
        # symmetrize_abs computes (|W| + |W|^T) / 2, propagating NaN.
        # fill_nan_zero replaces NaN (structural "no edge") with 0.0 so
        # the Laplacian is well-defined.
        W_sym = symmetrize_abs(W)
        W_clean = fill_nan_zero(W_sym)

        # Zero out diagonal — self-loops have no meaning in our framework
        # (a construct doesn't "bridge" to itself via SES).
        np.fill_diagonal(W_clean, 0.0)

        self.W_clean = W_clean

        # ── Step 2: Degree matrix D ───────────────────────────────────────
        # d_i = sum of edge weights incident to node i.
        # This measures how "connected" each construct is in the SES network.
        d = W_clean.sum(axis=1)  # (k,)

        # Handle isolated nodes (zero degree) by adding a tiny epsilon.
        # Without this, D^{-1/2} would contain inf, and the normalized
        # Laplacian would be undefined.  The epsilon (1e-12) is small
        # enough that it doesn't affect non-isolated nodes.
        d_safe = d.copy()
        d_safe[d_safe == 0] = 1e-12

        # D^{-1/2}: inverse square root of degree, as a diagonal matrix.
        # This normalizes the Laplacian so that eigenvalues lie in [0, 2]
        # regardless of the graph's overall weight scale.
        D_inv_sqrt = np.diag(1.0 / np.sqrt(d_safe))

        # ── Step 3: Normalized Laplacian ──────────────────────────────────
        # L = D^{-1/2} (D - W) D^{-1/2}
        #   = I - D^{-1/2} W D^{-1/2}
        #
        # Properties:
        #   - Symmetric positive semi-definite
        #   - Smallest eigenvalue = 0 (for each connected component)
        #   - Eigenvalues in [0, 2]
        #   - Eigenvectors are orthonormal (since L is symmetric)
        D_diag = np.diag(d)
        self.L = D_inv_sqrt @ (D_diag - W_clean) @ D_inv_sqrt

        # ── Step 4: Full eigendecomposition ───────────────────────────────
        # scipy.linalg.eigh returns eigenvalues in ascending order and
        # corresponding orthonormal eigenvectors as columns of U.
        # Using eigh (not eig) because L is symmetric — this guarantees
        # real eigenvalues and is numerically more stable.
        eigenvalues, U = scipy.linalg.eigh(self.L)

        # ── Step 5: Clip tiny negative eigenvalues ────────────────────────
        # Due to floating-point arithmetic, the smallest eigenvalue(s) may
        # be very slightly negative (e.g., -1e-15) instead of exactly 0.
        # Clipping to 0 prevents issues with sqrt and exp downstream.
        eigenvalues = np.clip(eigenvalues, 0.0, None)

        self.eigenvalues = eigenvalues  # (k,) ascending
        self.U = U                      # (k, k) columns are eigenvectors

    # ─────────────────────────────────────────────────────────────────────────
    # fiedler_partition() — Algebraic connectivity bipartition
    # ─────────────────────────────────────────────────────────────────────────

    def fiedler_partition(self) -> dict:
        """
        Extract the Fiedler vector and partition constructs by sign.

        The Fiedler vector is the eigenvector corresponding to the smallest
        non-trivial eigenvalue (lambda_1 > 0).  It provides the optimal
        spectral bipartition: constructs with positive loading form one
        group, those with negative loading form the other.

        In our SES construct networks, this typically separates:
          - Positive group: cosmopolitan/education-aligned constructs
          - Negative group: tradition/locality-aligned constructs
        (though the sign assignment is arbitrary — what matters is the split).

        Returns
        -------
        dict with keys:
          - fiedler_value: float — algebraic connectivity (smaller = more
            "cuttable" the graph is)
          - fiedler_index: int — index of the Fiedler eigenvalue
          - positive_group: list[str] — constructs with positive loading
          - negative_group: list[str] — constructs with negative loading
          - ranked_by_abs_loading: list[dict] — all constructs ranked by
            absolute Fiedler loading (highest = most central to the split)
        """
        # Find the first non-trivial eigenvalue.
        # Eigenvalue 0 corresponds to the constant vector (connected component
        # membership).  We skip eigenvalues below 1e-8 to handle numerical
        # zeros from multiple connected components.
        fiedler_idx = None
        for idx, lam in enumerate(self.eigenvalues):
            if lam > 1e-8:
                fiedler_idx = idx
                break

        # Fallback: if all eigenvalues are near zero (fully disconnected
        # graph), use index 1.  This shouldn't happen with our dense
        # construct networks, but is defensive.
        if fiedler_idx is None:
            fiedler_idx = min(1, self.k - 1)

        fiedler_value = float(self.eigenvalues[fiedler_idx])
        fiedler_vec = self.U[:, fiedler_idx]  # (k,)

        # Partition by sign of Fiedler vector.
        positive_group = [
            self.labels[i] for i in range(self.k) if fiedler_vec[i] >= 0
        ]
        negative_group = [
            self.labels[i] for i in range(self.k) if fiedler_vec[i] < 0
        ]

        # Rank all constructs by absolute Fiedler loading.
        # High |loading| = the construct is far from the partition boundary
        # and strongly identifies with one side of the spectral split.
        abs_loadings = np.abs(fiedler_vec)
        ranked_idx = np.argsort(abs_loadings)[::-1]  # descending
        ranked_by_abs_loading = [
            {
                "construct": self.labels[i],
                "loading": float(fiedler_vec[i]),
                "abs_loading": float(abs_loadings[i]),
                "group": "positive" if fiedler_vec[i] >= 0 else "negative",
            }
            for i in ranked_idx
        ]

        return {
            "fiedler_value": fiedler_value,
            "fiedler_index": int(fiedler_idx),
            "positive_group": positive_group,
            "negative_group": negative_group,
            "ranked_by_abs_loading": ranked_by_abs_loading,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # diffusion_map_3d() — 3D embedding from diffusion coordinates
    # ─────────────────────────────────────────────────────────────────────────

    def diffusion_map_3d(self, t: float = 1.0) -> dict:
        """
        Compute a 3D diffusion map embedding at time scale t.

        Diffusion maps embed each node into R^d using the first d non-trivial
        eigenvectors, weighted by exp(-lambda * t):

            coord_i = (exp(-lam_1*t) * u_1(i),
                       exp(-lam_2*t) * u_2(i),
                       exp(-lam_3*t) * u_3(i))

        The time parameter t controls the scale of the embedding:
          - Small t (e.g., 0.1): fine-grained local structure emphasized
          - Large t (e.g., 10.0): only global partition visible (all
            non-trivial eigenvalues are damped to near-zero except the
            smallest few)

        We use the first 3 non-trivial eigenvectors (indices 1, 2, 3 by
        default) for a 3D embedding suitable for visualization.

        Parameters
        ----------
        t : float
            Diffusion time scale (default 1.0).

        Returns
        -------
        dict mapping construct label -> [x, y, z] coordinates.
        """
        # Identify the first 3 non-trivial eigenvectors.
        # We skip eigenvalue indices where lambda <= 1e-8 (trivial / zero).
        non_trivial_idx = [
            i for i, lam in enumerate(self.eigenvalues) if lam > 1e-8
        ]

        # If fewer than 3 non-trivial eigenvectors exist (very fragmented
        # graph), pad with zeros.
        use_idx = non_trivial_idx[:3]
        while len(use_idx) < 3:
            # Append the next available index (even if trivial)
            next_idx = use_idx[-1] + 1 if use_idx else 1
            if next_idx < self.k:
                use_idx.append(next_idx)
            else:
                use_idx.append(use_idx[-1])  # repeat last (degenerate)

        # Compute diffusion coordinates.
        # Each axis is scaled by exp(-lambda_j * t): at large t, high-frequency
        # eigenvectors (large lambda) are exponentially damped, and the
        # embedding collapses onto the low-frequency global structure.
        coords = np.zeros((self.k, 3), dtype=np.float64)
        for dim, eigvec_idx in enumerate(use_idx):
            lam = self.eigenvalues[eigvec_idx]
            scale = np.exp(-lam * t)
            coords[:, dim] = scale * self.U[:, eigvec_idx]

        # Build label -> [x, y, z] mapping
        return {
            self.labels[i]: coords[i].tolist()
            for i in range(self.k)
        }

    # ─────────────────────────────────────────────────────────────────────────
    # heat_kernel() — Full heat diffusion matrix at time t
    # ─────────────────────────────────────────────────────────────────────────

    def heat_kernel(self, t: float) -> np.ndarray:
        """
        Compute the heat kernel matrix H(t).

        H(t) = U @ diag(exp(-lambda * t)) @ U^T

        H(t)[i,j] is the amount of "heat" that diffuses from node i to
        node j in time t, starting from a unit heat source at i.

        Physical intuition: imagine placing a unit of heat at one construct
        and letting it diffuse along the weighted edges.  At t=0, all heat
        is at the source.  As t increases, heat spreads to neighbors, then
        to neighbors-of-neighbors, weighted by edge strength.  At t -> inf,
        heat equilibrates to the stationary distribution (proportional to
        node degree).

        Properties:
          - H(0) = I (identity — no diffusion yet)
          - H(t) is symmetric and positive semi-definite
          - Rows sum to 1 (heat is conserved in the normalized Laplacian)
          - Diagonal entries decrease with t (heat leaves the source)

        Parameters
        ----------
        t : float
            Diffusion time.

        Returns
        -------
        H : (k, k) ndarray
            Heat kernel matrix.
        """
        # diag(exp(-lambda * t)): exponential decay of each eigenmode.
        # Low-frequency modes (small lambda) persist; high-frequency modes
        # (large lambda) decay rapidly.  This is why the heat kernel
        # naturally smooths the signal — it acts as a low-pass filter on
        # the graph spectrum.
        exp_diag = np.diag(np.exp(-self.eigenvalues * t))
        H = self.U @ exp_diag @ self.U.T
        return H

    # ─────────────────────────────────────────────────────────────────────────
    # scale_sweep() — Multi-scale heat diffusion from a source construct
    # ─────────────────────────────────────────────────────────────────────────

    def scale_sweep(
        self,
        source_idx: int,
        t_values: list[float],
    ) -> dict:
        """
        Track heat diffusion from a source construct at multiple time scales.

        For each time t, compute the heat kernel row for the source node
        and report the top-5 constructs that receive the most heat.  This
        reveals the multi-scale structure of construct influence:

          - t=0.01: only immediate neighbors (strongest direct edges)
          - t=0.1:  local neighborhood (2-hop reach)
          - t=1.0:  intermediate scale (community-level diffusion)
          - t=10.0: global equilibrium (heat distributed by degree)

        Parameters
        ----------
        source_idx : int
            Index of the source construct in the weight matrix.
        t_values : list[float]
            Diffusion time scales to evaluate.

        Returns
        -------
        dict keyed by t value (as string), each containing:
          - source_retention: fraction of heat remaining at source
          - top_5: list of dicts with construct name and heat received
        """
        results = {}

        for t in t_values:
            # Compute heat kernel at time t
            H = self.heat_kernel(t)

            # Extract the source row: how heat from source_idx distributes
            heat_row = H[source_idx, :]  # (k,)

            # Source retention: how much heat stays at the source.
            # High retention = the source is relatively isolated.
            source_retention = float(heat_row[source_idx])

            # Top-5 recipients (excluding self).
            # We mask the source node to find the top destinations.
            heat_others = heat_row.copy()
            heat_others[source_idx] = -np.inf  # exclude self from ranking
            top5_idx = np.argsort(heat_others)[::-1][:5]

            top_5 = [
                {
                    "construct": self.labels[idx],
                    "heat": float(heat_row[idx]),
                }
                for idx in top5_idx
            ]

            results[str(t)] = {
                "source_retention": source_retention,
                "top_5": top_5,
            }

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # diffusion_distance() — Pairwise diffusion distances at time t
    # ─────────────────────────────────────────────────────────────────────────

    def diffusion_distance(self, t: float) -> np.ndarray:
        """
        Compute the pairwise diffusion distance matrix at time t.

        D_t(i,j)^2 = sum_k exp(-2*lambda_k*t) * (u_k(i) - u_k(j))^2

        Diffusion distance captures connectivity through ALL paths, not
        just the shortest one.  Two constructs that are connected by many
        moderate-weight paths will have smaller diffusion distance than
        two connected by a single strong path.

        The time parameter t controls the scale:
          - Small t: distance reflects local edge structure
          - Large t: distance reflects global topology (communities)

        Unlike Euclidean distance in the weight matrix, diffusion distance
        respects the manifold structure of the graph and is robust to noise
        in individual edge weights.

        Parameters
        ----------
        t : float
            Diffusion time scale.

        Returns
        -------
        D : (k, k) ndarray
            Pairwise diffusion distance matrix (symmetric, non-negative,
            zero diagonal).
        """
        # Compute the diffusion coordinates: each node gets a k-dimensional
        # coordinate vector with entries exp(-lambda_j * t) * u_j(i).
        # The diffusion distance is then just the Euclidean distance in
        # this coordinate space.
        #
        # We include ALL eigenvectors (not just the first few) for an
        # exact computation.  The exponential weighting naturally downweights
        # high-frequency components, so including them doesn't add noise.
        weights = np.exp(-self.eigenvalues * t)  # (k,)

        # D_t(i,j)^2 = sum_m w_m^2 * (U[i,m] - U[j,m])^2
        #            = sum_m exp(-2*lam_m*t) * (U[i,m] - U[j,m])^2
        #
        # Efficient vectorized computation using broadcasting:
        # weighted_U[i, m] = exp(-lam_m * t) * U[i, m]
        weighted_U = self.U * weights[np.newaxis, :]  # (k, k)

        # Pairwise squared Euclidean distance in the weighted eigenvector space.
        # D^2[i,j] = ||weighted_U[i] - weighted_U[j]||^2
        #          = sum_m (weighted_U[i,m] - weighted_U[j,m])^2
        #
        # Expand: ||a - b||^2 = ||a||^2 + ||b||^2 - 2*a.b
        sq_norms = np.sum(weighted_U ** 2, axis=1)  # (k,)
        D_sq = (
            sq_norms[:, np.newaxis]
            + sq_norms[np.newaxis, :]
            - 2.0 * weighted_U @ weighted_U.T
        )

        # Clamp to non-negative (numerical noise can produce tiny negatives)
        D_sq = np.maximum(D_sq, 0.0)

        return np.sqrt(D_sq)


# ═════════════════════════════════════════════════════════════════════════════
# fiedler_comparison() — Cross-country Fiedler partition agreement
# ═════════════════════════════════════════════════════════════════════════════

def fiedler_comparison(
    all_partitions: dict[str, dict],
    manifest: dict,
) -> dict:
    """
    Compare Fiedler partitions across countries using Adjusted Rand Index.

    The Adjusted Rand Index (ARI) measures agreement between two
    partitions, corrected for chance:
      - ARI = 1.0: perfect agreement (identical partitions)
      - ARI = 0.0: chance-level agreement
      - ARI < 0.0: less agreement than expected by chance

    We compute the 66x66 ARI matrix and then test whether within-zone
    pairs (same cultural zone) have higher ARI than across-zone pairs.
    This tests the hypothesis that cultural zones share similar spectral
    structure in their SES construct networks.

    Parameters
    ----------
    all_partitions : dict[str, dict]
        country -> fiedler_partition() output (must contain positive_group
        and negative_group).
    manifest : dict
        Manifest with cultural_zones mapping.

    Returns
    -------
    dict with:
      - rand_matrix: 66x66 ARI values
      - countries: ordered list of country codes
      - mean_within_zone: mean ARI for pairs in the same cultural zone
      - mean_across_zone: mean ARI for pairs in different cultural zones
      - zone_ari_breakdown: per-zone mean ARI
    """
    from sklearn.metrics import adjusted_rand_score

    countries = sorted(all_partitions.keys())
    n = len(countries)

    # ── Build label vectors for ARI ───────────────────────────────────────
    # For each country, convert the Fiedler partition into a label vector:
    # each construct gets label 1 (positive group) or 0 (negative group).
    # ARI then measures how much two countries agree on which constructs
    # belong together.
    #
    # We need a shared construct ordering.  Use the construct_index from
    # the manifest (all countries share the same 55 constructs).
    construct_index = manifest.get("construct_index", [])

    label_vectors: dict[str, list[int]] = {}
    for country in countries:
        part = all_partitions[country]
        pos_set = set(part["positive_group"])
        # Assign 1 to positive group, 0 to negative group
        labels = [1 if c in pos_set else 0 for c in construct_index]
        label_vectors[country] = labels

    # ── Pairwise ARI matrix ───────────────────────────────────────────────
    rand_matrix = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i, n):
            if i == j:
                rand_matrix[i, j] = 1.0
            else:
                ari = adjusted_rand_score(
                    label_vectors[countries[i]],
                    label_vectors[countries[j]],
                )
                rand_matrix[i, j] = ari
                rand_matrix[j, i] = ari

    # ── Within-zone vs across-zone ARI ────────────────────────────────────
    # cultural_zones maps zone_name -> list of country codes.
    cultural_zones = manifest.get("cultural_zones", {})

    # Build country -> zone lookup
    country_to_zone: dict[str, str] = {}
    for zone_name, zone_countries in cultural_zones.items():
        for c in zone_countries:
            country_to_zone[c] = zone_name

    within_aris: list[float] = []
    across_aris: list[float] = []

    for i in range(n):
        for j in range(i + 1, n):
            c_i = countries[i]
            c_j = countries[j]
            ari_val = rand_matrix[i, j]

            zone_i = country_to_zone.get(c_i, "unknown")
            zone_j = country_to_zone.get(c_j, "unknown")

            if zone_i == zone_j and zone_i != "unknown":
                within_aris.append(ari_val)
            else:
                across_aris.append(ari_val)

    mean_within = float(np.mean(within_aris)) if within_aris else 0.0
    mean_across = float(np.mean(across_aris)) if across_aris else 0.0

    # ── Per-zone breakdown ────────────────────────────────────────────────
    zone_ari_breakdown: dict[str, dict] = {}
    for zone_name, zone_countries in cultural_zones.items():
        # Filter to countries we actually have partitions for
        zone_in_data = [c for c in zone_countries if c in set(countries)]
        if len(zone_in_data) < 2:
            continue

        zone_pairs: list[float] = []
        for ii in range(len(zone_in_data)):
            for jj in range(ii + 1, len(zone_in_data)):
                ci_idx = countries.index(zone_in_data[ii])
                cj_idx = countries.index(zone_in_data[jj])
                zone_pairs.append(rand_matrix[ci_idx, cj_idx])

        zone_ari_breakdown[zone_name] = {
            "n_countries": len(zone_in_data),
            "n_pairs": len(zone_pairs),
            "mean_ari": float(np.mean(zone_pairs)),
            "std_ari": float(np.std(zone_pairs)),
        }

    print(f"\n  Fiedler comparison ({n} countries):")
    print(f"    Mean within-zone ARI:  {mean_within:.4f}")
    print(f"    Mean across-zone ARI:  {mean_across:.4f}")
    print(f"    Ratio (within/across): {mean_within / mean_across:.2f}x"
          if mean_across > 0 else "    (no across-zone pairs)")
    for zone_name, info in sorted(zone_ari_breakdown.items()):
        print(f"    {zone_name}: mean ARI = {info['mean_ari']:.4f} "
              f"({info['n_countries']} countries, {info['n_pairs']} pairs)")

    return {
        "rand_matrix": rand_matrix,
        "countries": countries,
        "mean_within_zone": mean_within,
        "mean_across_zone": mean_across,
        "n_within_pairs": len(within_aris),
        "n_across_pairs": len(across_aris),
        "zone_ari_breakdown": zone_ari_breakdown,
    }


# ═════════════════════════════════════════════════════════════════════════════
# run_country() — Full spectral analysis for one country
# ═════════════════════════════════════════════════════════════════════════════

def run_country(country: str) -> dict:
    """
    Run complete spectral analysis for one country.

    Steps:
      1. Load the 55x55 weight matrix
      2. Construct SpectralAnalyzer (Laplacian + eigendecomposition)
      3. Compute Fiedler partition
      4. Compute 3D diffusion map at t=1.0
      5. Run scale sweep from the top Fiedler-loading construct
      6. Validate Fiedler value against spectral_features.json

    Parameters
    ----------
    country : str
        Three-letter country code (e.g., "MEX").

    Returns
    -------
    results : dict
        Serializable dict with all spectral analysis outputs.
    """
    # ── Load data ─────────────────────────────────────────────────────────
    W, labels = load_weight_matrix(country)
    k = W.shape[0]

    print(f"\n{'='*60}")
    print(f"  Spectral Analysis: {country}")
    print(f"  {k} constructs")
    print(f"{'='*60}")

    # ── Build spectral analyzer ───────────────────────────────────────────
    sa = SpectralAnalyzer(W, labels)

    # Print eigenvalue summary
    print(f"  Eigenvalue range: [{sa.eigenvalues[0]:.6f}, "
          f"{sa.eigenvalues[-1]:.6f}]")
    n_zero = np.sum(sa.eigenvalues < 1e-8)
    print(f"  Near-zero eigenvalues: {n_zero} (connected components)")

    # ── Fiedler partition ─────────────────────────────────────────────────
    fiedler = sa.fiedler_partition()
    print(f"\n  Fiedler value (algebraic connectivity): "
          f"{fiedler['fiedler_value']:.6f}")
    print(f"  Partition: {len(fiedler['positive_group'])} positive, "
          f"{len(fiedler['negative_group'])} negative")

    # Show top-3 constructs by Fiedler loading (most central to the split)
    print(f"  Top-3 by |Fiedler loading|:")
    for entry in fiedler["ranked_by_abs_loading"][:3]:
        sign = "+" if entry["loading"] > 0 else "-"
        print(f"    {sign} {entry['construct']}: {entry['loading']:.4f}")

    # ── Diffusion map 3D at t=1.0 ─────────────────────────────────────────
    diffusion_map = sa.diffusion_map_3d(t=1.0)
    print(f"\n  Diffusion map: 3D embedding at t=1.0 "
          f"({len(diffusion_map)} constructs)")

    # ── Scale sweep ───────────────────────────────────────────────────────
    # Use the construct with highest absolute Fiedler loading as source.
    # This is the construct most central to the spectral bipartition,
    # so its heat diffusion pattern is most informative about the
    # network's multi-scale structure.
    top_construct = fiedler["ranked_by_abs_loading"][0]["construct"]
    source_idx = labels.index(top_construct)

    t_values = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0]
    scale_sweep_result = sa.scale_sweep(source_idx, t_values)

    print(f"\n  Scale sweep from '{top_construct}' (idx {source_idx}):")
    for t_str, info in scale_sweep_result.items():
        top1 = info["top_5"][0]
        print(f"    t={t_str}: retention={info['source_retention']:.4f}, "
              f"top recipient={top1['construct']} ({top1['heat']:.4f})")

    # ── Validation: compare Fiedler value with spectral_features.json ────
    validation = _validate_fiedler(country, fiedler["fiedler_value"])

    # ── Assemble results ──────────────────────────────────────────────────
    results = {
        "country": country,
        "n_constructs": k,
        "eigenvalue_summary": {
            "min": float(sa.eigenvalues[0]),
            "max": float(sa.eigenvalues[-1]),
            "fiedler": fiedler["fiedler_value"],
            "n_near_zero": int(n_zero),
            "all_eigenvalues": sa.eigenvalues.tolist(),
        },
        "fiedler_partition": fiedler,
        "diffusion_map_3d": diffusion_map,
        "scale_sweep": {
            "source_construct": top_construct,
            "source_index": source_idx,
            "t_values": t_values,
            "results": scale_sweep_result,
        },
        "construct_labels": labels,
        "fiedler_validation": validation,
    }

    return results


def _validate_fiedler(country: str, computed_fiedler: float) -> dict:
    """
    Compare our computed Fiedler value against spectral_features.json.

    The TDA pipeline (Phase 3, Julia) computes spectral features including
    the Fiedler value.  We compare our Python-computed value against it
    to catch bugs in the Laplacian construction or eigendecomposition.

    A small discrepancy is expected due to:
      - Different symmetrization (we use |W|; Julia may use signed W)
      - Different NaN handling
      - Floating-point differences between Julia and Python/scipy

    Parameters
    ----------
    country : str
        Country code.
    computed_fiedler : float
        Fiedler value from our SpectralAnalyzer.

    Returns
    -------
    dict with computed, reference, difference, and match status.
    """
    try:
        spectral_features = load_spectral_features()
    except FileNotFoundError:
        print(f"  [validation] spectral_features.json not found — skipping")
        return {"status": "file_not_found"}

    if country not in spectral_features:
        print(f"  [validation] {country} not in spectral_features.json — skipping")
        return {"status": "country_not_found"}

    reference = spectral_features[country]["fiedler_value"]
    diff = abs(computed_fiedler - reference)
    relative_diff = diff / max(abs(reference), 1e-10)

    # Threshold for "close enough": 5% relative difference.
    # We expect some discrepancy because our symmetrization takes |W|
    # while the TDA pipeline may use signed weights.
    is_close = relative_diff < 0.05

    status = "match" if is_close else "mismatch"
    print(f"\n  [validation] Fiedler value comparison:")
    print(f"    Computed:  {computed_fiedler:.6f}")
    print(f"    Reference: {reference:.6f}")
    print(f"    Diff:      {diff:.6f} ({relative_diff:.1%} relative)")
    print(f"    Status:    {status}")

    return {
        "status": status,
        "computed": computed_fiedler,
        "reference": reference,
        "absolute_difference": diff,
        "relative_difference": relative_diff,
    }


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Spectral analysis and heat diffusion on WVS construct networks",
    )
    parser.add_argument(
        "--country",
        default="MEX",
        help="Three-letter country code (default: MEX)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run spectral analysis for all 66 countries + Fiedler comparison",
    )
    args = parser.parse_args()

    out_dir = get_output_dir()
    t0 = time.time()

    if args.all:
        # ── Run all countries ─────────────────────────────────────────────
        manifest = load_manifest()
        countries = sorted(manifest["countries"])
        print(f"Running spectral analysis for {len(countries)} countries...")

        all_partitions: dict[str, dict] = {}
        all_summaries: list[dict] = []

        for country in countries:
            try:
                results = run_country(country)
                save_json(results, out_dir / f"{country}_spectral.json")

                # Store partition for cross-country comparison
                all_partitions[country] = results["fiedler_partition"]

                all_summaries.append({
                    "country": country,
                    "fiedler_value": results["fiedler_partition"]["fiedler_value"],
                    "n_positive": len(results["fiedler_partition"]["positive_group"]),
                    "n_negative": len(results["fiedler_partition"]["negative_group"]),
                    "top_loading_construct": (
                        results["fiedler_partition"]["ranked_by_abs_loading"][0]["construct"]
                    ),
                })
            except Exception as e:
                print(f"  ERROR {country}: {e}")
                all_summaries.append({"country": country, "error": str(e)})

        # ── Fiedler comparison across countries ───────────────────────────
        if len(all_partitions) >= 2:
            comparison = fiedler_comparison(all_partitions, manifest)
            save_json(comparison, out_dir / "fiedler_comparison.json")

        # ── Cross-country summary ─────────────────────────────────────────
        elapsed = time.time() - t0
        print(f"\n{'='*60}")
        print(f"  All-country spectral analysis complete in {elapsed:.1f}s")
        print(f"{'='*60}")

        ok = [s for s in all_summaries if "error" not in s]
        if ok:
            fiedler_vals = [s["fiedler_value"] for s in ok]
            print(f"  Fiedler value: median={np.median(fiedler_vals):.4f}, "
                  f"range=[{min(fiedler_vals):.4f}, {max(fiedler_vals):.4f}]")

        save_json(
            {"summaries": all_summaries, "elapsed_s": elapsed},
            out_dir / "spectral_all_summary.json",
        )

    else:
        # ── Single country ────────────────────────────────────────────────
        results = run_country(args.country)
        save_json(results, out_dir / f"{args.country}_spectral.json")

        elapsed = time.time() - t0
        print(f"\n  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
