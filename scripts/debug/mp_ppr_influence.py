"""
Personalized PageRank Influence Mapping on WVS Construct Networks
=================================================================

Stage 3 of the message-passing framework.

What this computes
------------------
Given a weighted graph of 55 WVS constructs (edges = |gamma| magnitudes from
the DR bridge), we compute the **Personalized PageRank (PPR)** influence
matrix.  PPR extends standard PageRank by seeding the random walk at a
specific node, producing a distribution over all other nodes that captures
how much influence that seed exerts through the network.

For each seed construct i, the PPR vector pi satisfies:

    pi = alpha * e_i + (1 - alpha) * P^T * pi

where:
  - alpha is the teleportation probability (restart rate): how often the
    walker "resets" back to the seed.  Higher alpha means the walker stays
    closer to the seed (more local influence); lower alpha lets influence
    spread further through multi-hop paths.
  - e_i is the one-hot vector at seed node i
  - P is the row-normalized transition matrix: P[i,j] = |W[i,j]| / sum_j |W[i,j]|
  - P^T transposes the walk direction so that Pi[j,i] measures how much
    influence *from* i reaches j

We solve this via power iteration (fast, guaranteed to converge since
alpha > 0 makes the system contractive).

Computing PPR for every seed produces a (k x k) influence matrix Pi where
Pi[j,i] = influence of construct i on construct j.  This matrix is generally
asymmetric: a construct can be a strong "hub" (influences many others) without
being a "sink" (receiving influence from many others).

From the full PPR matrix, several analyses follow:

1. **Hub scores**.  Column sums of Pi (minus diagonal).  Measures total outward
   influence: how much a construct's "shock" would ripple through the network.
   High hub scores indicate constructs that sit at central positions in the SES
   bridge network — a shift in their SES stratification would propagate widely.

2. **Sink scores**.  Row sums of Pi (minus diagonal).  Measures total inward
   influence: how much a construct is affected by shocks originating elsewhere.
   High sink scores indicate constructs that are downstream of many pathways.

3. **Asymmetry matrix**.  A = Pi - Pi^T.  Positive A[j,i] means construct i
   influences j more than j influences i.  This reveals the *directionality*
   of influence flow, even in an undirected weight graph (directionality
   emerges from asymmetric degree distributions and local topology).

4. **Scenario analysis**.  Given a hypothetical +/- shift at a seed construct,
   the PPR column gives the implied shift at every other construct.  This
   answers: "If religious_belief were to become more SES-stratified by 0.1
   gamma units, which other constructs would be most affected?"

5. **Alpha sensitivity sweep**.  We vary the teleportation parameter alpha
   across [0.10, 0.15, 0.20, 0.30, 0.50] and track how hub rankings change.
   Constructs that are top hubs at *all* alpha values are structurally central
   regardless of the locality/globality balance.  Constructs whose rank
   shifts by >10 are alpha-sensitive — their influence depends on whether
   we measure local vs. global reach.

6. **Cross-country comparison**.  When run with --all, we compute PPR for
   all 66 countries and compare hub rankings.  Universal hubs (top-10 in
   >50 countries) are constructs whose SES centrality is a cross-cultural
   constant.  Zone-specific hubs are central only in certain cultural
   regions, revealing how SES network architecture varies geographically.

Validation
----------
Hub rankings are compared against Floyd-Warshall mediator scores (from the
TDA pipeline Phase 1) via Spearman rank correlation.  High correlation
confirms that PPR-derived influence agrees with shortest-path-based
betweenness.  Discrepancies are informative: PPR counts *all* paths
(weighted by transition probability), while Floyd-Warshall counts only
shortest paths.  Constructs that rank higher in PPR than in mediator scores
sit on many redundant paths — they are "broad conduits" rather than
"narrow bottlenecks."

Output
------
Per-country JSON in data/tda/message_passing/{COUNTRY}_ppr.json:
  - hub_scores: per-construct outward influence
  - sink_scores: per-construct inward influence
  - hub_ranking: constructs sorted by hub score (descending)
  - sink_ranking: constructs sorted by sink score (descending)
  - scenario: implied shifts from a unit shock at the top hub
  - alpha_sensitivity: hub ranking stability across alpha values
  - mediator_correlation: Spearman rho vs Floyd-Warshall mediator scores

Cross-country JSON (with --all):
  - ppr_hub_comparison.json: universal hubs, zone-specific hubs,
    hub rank matrix (55 x 66)

Usage
-----
    python scripts/debug/mp_ppr_influence.py --country MEX
    python scripts/debug/mp_ppr_influence.py --all
    python scripts/debug/mp_ppr_influence.py --country MEX --alpha 0.30
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

# ── Project paths ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import (  # noqa: E402
    fill_nan_zero,
    get_output_dir,
    load_manifest,
    load_mediator_scores,
    load_weight_matrix,
    row_normalize,
    save_json,
)


# ═════════════════════════════════════════════════════════════════════════════
# PPRMapper — Personalized PageRank influence analysis on construct graphs
# ═════════════════════════════════════════════════════════════════════════════

class PPRMapper:
    """
    Personalized PageRank influence mapper for a weighted construct network.

    Builds a transition matrix from the absolute-valued weight matrix and
    computes per-seed PPR vectors via power iteration.  Provides methods for
    hub/sink scoring, asymmetry detection, and scenario analysis.

    Parameters
    ----------
    W : (k, k) ndarray
        Raw weight matrix (may be asymmetric, may contain NaN).
        Absolute values are used; NaN is treated as "no edge" (zero weight).
    construct_labels : list[str]
        Human-readable label for each of the k nodes.
    alpha : float, default 0.20
        Teleportation (restart) probability.  Higher alpha = more local
        influence; lower alpha = influence spreads further through multi-hop
        paths.  The default 0.20 is a standard choice in the literature and
        balances local vs. global reach.
    """

    def __init__(self, W: np.ndarray, construct_labels: list[str],
                 alpha: float = 0.20):
        self.labels = construct_labels
        self.k = W.shape[0]
        self.alpha = alpha

        # ── Step 1: Take absolute values and fill NaN ────────────────────
        # We use |gamma| as edge weights because PPR needs non-negative
        # transition probabilities.  The sign information (positive vs.
        # negative gamma) is not used here — it's captured in the sign-
        # aware analyses (belief propagation, structural balance).
        # NaN means "no edge" — we set these to zero so they contribute
        # nothing to the transition probability.
        W_abs = np.abs(W)
        W_clean = fill_nan_zero(W_abs)

        # Zero out diagonal — self-transitions are meaningless (a construct
        # doesn't influence itself through the SES bridge network).
        np.fill_diagonal(W_clean, 0.0)

        # ── Step 2: Build transition matrix P ────────────────────────────
        # P[i,j] = W_clean[i,j] / sum_j W_clean[i,j]
        # Each row sums to 1.0 (a probability distribution over next steps
        # in the random walk from node i).
        # Isolated nodes (zero row sum) get P[i,:] = 0, so the walker
        # always teleports back to the seed — this is correct behavior
        # (an isolated node has no outward influence).
        self.P = row_normalize(W_clean)

    # ─────────────────────────────────────────────────────────────────────────
    # ppr_vector() — Compute PPR for a single seed via power iteration
    # ─────────────────────────────────────────────────────────────────────────

    def ppr_vector(self, seed: int) -> np.ndarray:
        """
        Compute the Personalized PageRank vector seeded at node `seed`.

        Solves pi = alpha * e_seed + (1 - alpha) * P^T * pi by power
        iteration.  The result pi[j] is the stationary probability that a
        random walker (who restarts at `seed` with probability alpha) is
        found at node j.  Higher pi[j] means node j receives more
        influence from the seed.

        Parameters
        ----------
        seed : int
            Index of the seed node (0-based).

        Returns
        -------
        pi : (k,) ndarray
            PPR distribution over all k nodes.  Sums to 1.0.
        """
        # ── Teleportation vector: 1.0 at the seed, 0 elsewhere ──────────
        e = np.zeros(self.k)
        e[seed] = 1.0

        # ── Initial guess: uniform distribution ─────────────────────────
        # Any starting vector converges; uniform is a safe choice.
        pi = np.ones(self.k) / self.k

        # ── Power iteration ─────────────────────────────────────────────
        # At each step:
        #   pi_new = alpha * e + (1 - alpha) * P^T @ pi_old
        #
        # Why P^T and not P?  P[i,j] is the probability of stepping from
        # i to j.  To compute where probability *flows to* j from all
        # sources, we need column j of P, which is row j of P^T.  So
        # P^T @ pi distributes the current probability mass according
        # to the transition structure.
        #
        # Convergence is guaranteed because the teleportation term (alpha)
        # makes the iteration a contraction mapping.  Rate of convergence
        # is (1-alpha)^t, so for alpha=0.20 we reach machine precision
        # in about -log(1e-8)/log(0.8) ~ 83 iterations — well within
        # our max_iter=500 budget.
        max_iter = 500
        tol = 1e-8

        for _ in range(max_iter):
            pi_new = self.alpha * e + (1.0 - self.alpha) * (self.P.T @ pi)
            # Check L1 convergence (sum of absolute differences)
            if np.abs(pi_new - pi).sum() < tol:
                return pi_new
            pi = pi_new

        # If we exhaust iterations (unlikely with alpha > 0), return
        # the last iterate — it's close enough for practical purposes.
        return pi

    # ─────────────────────────────────────────────────────────────────────────
    # full_ppr_matrix() — PPR from every seed → (k, k) influence matrix
    # ─────────────────────────────────────────────────────────────────────────

    def full_ppr_matrix(self) -> np.ndarray:
        """
        Compute the full PPR influence matrix Pi.

        Pi is (k, k) where column i is the PPR vector seeded at node i:
            Pi[j, i] = influence of construct i on construct j

        This is the core data structure for all downstream analyses.
        Computing it requires k power iterations (one per seed), which is
        O(k^2 * n_iter) — fast for k=55 (a few hundred milliseconds).

        Returns
        -------
        Pi : (k, k) ndarray
            Column i = ppr_vector(i).
        """
        Pi = np.zeros((self.k, self.k))
        for i in range(self.k):
            Pi[:, i] = self.ppr_vector(i)
        return Pi

    # ─────────────────────────────────────────────────────────────────────────
    # hub_scores() — Total outward influence per construct
    # ─────────────────────────────────────────────────────────────────────────

    def hub_scores(self, Pi: np.ndarray) -> np.ndarray:
        """
        Hub score = column sum of Pi, excluding the diagonal.

        Measures total outward influence: a high hub score means that when
        this construct is "shocked" (seeded), the influence spreads widely
        to many other constructs.  The diagonal is excluded because a
        construct's influence on itself is trivially high (it's the seed).

        Parameters
        ----------
        Pi : (k, k) ndarray
            Full PPR matrix from full_ppr_matrix().

        Returns
        -------
        scores : (k,) ndarray
            One score per construct.
        """
        # Column sum = total probability mass that construct i "sends" to
        # all other constructs.  Diagonal is the self-influence (always
        # large due to teleportation), so we subtract it.
        return Pi.sum(axis=0) - np.diag(Pi)

    # ─────────────────────────────────────────────────────────────────────────
    # sink_scores() — Total inward influence per construct
    # ─────────────────────────────────────────────────────────────────────────

    def sink_scores(self, Pi: np.ndarray) -> np.ndarray:
        """
        Sink score = row sum of Pi, excluding the diagonal.

        Measures total inward influence: a high sink score means this
        construct receives substantial influence regardless of which
        construct is the source of a shock.

        Parameters
        ----------
        Pi : (k, k) ndarray
            Full PPR matrix from full_ppr_matrix().

        Returns
        -------
        scores : (k,) ndarray
            One score per construct.
        """
        # Row sum = total probability mass that arrives at construct j
        # across all possible seeds.
        return Pi.sum(axis=1) - np.diag(Pi)

    # ─────────────────────────────────────────────────────────────────────────
    # asymmetry() — Directional influence imbalance
    # ─────────────────────────────────────────────────────────────────────────

    def asymmetry(self, Pi: np.ndarray) -> np.ndarray:
        """
        Asymmetry matrix A = Pi - Pi^T.

        A[j, i] > 0 means construct i influences j more than j influences i.
        Even though the weight matrix is undirected (symmetric |gamma|),
        asymmetry emerges from differences in local degree: a high-degree
        node's influence is "diluted" across many edges, while a low-degree
        node concentrates its influence on fewer neighbors.

        Parameters
        ----------
        Pi : (k, k) ndarray
            Full PPR matrix from full_ppr_matrix().

        Returns
        -------
        A : (k, k) ndarray
            Skew-symmetric matrix (A + A^T = 0).
        """
        return Pi - Pi.T

    # ─────────────────────────────────────────────────────────────────────────
    # scenario() — Implied shifts from a hypothetical shock at one construct
    # ─────────────────────────────────────────────────────────────────────────

    def scenario(self, Pi: np.ndarray, seed_idx: int, magnitude: float,
                 labels: list[str] | None = None) -> list[dict]:
        """
        Compute the implied shift at each construct from a shock at seed_idx.

        The PPR column for the seed gives the relative influence on every
        other construct.  Multiplying by the shock magnitude gives a
        first-order approximation of how much each construct's SES
        stratification would shift.

        This is a linear approximation — it assumes the network structure
        itself doesn't change in response to the shock.  For small
        perturbations (magnitude < 0.1), this is reasonable.

        Parameters
        ----------
        Pi : (k, k) ndarray
            Full PPR matrix.
        seed_idx : int
            Index of the shocked construct.
        magnitude : float
            Size of the hypothetical shock (in gamma units).
        labels : list[str], optional
            Construct labels.  Defaults to self.labels.

        Returns
        -------
        shifts : list[dict]
            Sorted by |shift| descending.  Each dict has:
              - construct: label string
              - shift: implied gamma shift (magnitude * PPR weight)
            The seed construct itself is excluded from the list.
        """
        if labels is None:
            labels = self.labels

        # Implied shift at each construct j = Pi[j, seed_idx] * magnitude
        # This is the PPR probability (influence fraction) times the shock.
        shifts = Pi[:, seed_idx] * magnitude

        # Build list of (construct, shift) dicts, excluding the seed itself
        results = []
        for j in range(self.k):
            if j == seed_idx:
                continue
            results.append({
                "construct": labels[j],
                "shift": float(shifts[j]),
            })

        # Sort by absolute shift (largest impact first)
        results.sort(key=lambda x: abs(x["shift"]), reverse=True)
        return results


# ═════════════════════════════════════════════════════════════════════════════
# alpha_sweep — Sensitivity of hub rankings to the teleportation parameter
# ═════════════════════════════════════════════════════════════════════════════

def alpha_sweep(W: np.ndarray, labels: list[str],
                alphas: list[float] | None = None) -> dict:
    """
    Sweep over teleportation parameter alpha and track hub ranking stability.

    For each alpha value, we build a PPRMapper, compute the full PPR matrix,
    and record the hub ranking (constructs sorted by hub score).  We then
    identify:
      - **alpha-stable** constructs: in the top-10 at *every* alpha value.
        These are structurally central regardless of the locality/globality
        balance — their influence is robust.
      - **alpha-sensitive** constructs: their rank shifts by more than 10
        positions across alpha values.  These are constructs whose apparent
        centrality depends strongly on whether we measure local vs. global
        influence.

    Parameters
    ----------
    W : (k, k) ndarray
        Raw weight matrix.
    labels : list[str]
        Construct labels.
    alphas : list[float], optional
        Alpha values to test.  Default: [0.10, 0.15, 0.20, 0.30, 0.50].

    Returns
    -------
    result : dict
        Keys:
          - per_alpha: {alpha_str: [construct labels in hub-score order]}
          - stable_hubs: list of constructs in top-10 at all alpha values
          - sensitive_constructs: list of {construct, min_rank, max_rank, shift}
    """
    if alphas is None:
        alphas = [0.10, 0.15, 0.20, 0.30, 0.50]

    k = W.shape[0]

    # ── Compute hub ranking at each alpha ────────────────────────────────
    # per_alpha_rankings[alpha_str] = list of construct labels, sorted by
    # hub score (descending).
    per_alpha_rankings: dict[str, list[str]] = {}

    # rank_matrix[i, a] = rank of construct i at alpha_a (0-based)
    rank_matrix = np.zeros((k, len(alphas)), dtype=int)

    for a_idx, alpha in enumerate(alphas):
        mapper = PPRMapper(W, labels, alpha=alpha)
        Pi = mapper.full_ppr_matrix()
        hubs = mapper.hub_scores(Pi)

        # argsort descending → rank order
        order = np.argsort(-hubs)
        ranking = [labels[i] for i in order]
        per_alpha_rankings[f"{alpha:.2f}"] = ranking

        # Record rank of each construct at this alpha
        for rank, idx in enumerate(order):
            rank_matrix[idx, a_idx] = rank

    # ── Alpha-stable hubs ────────────────────────────────────────────────
    # A construct is "stable" if it's in the top-10 at every alpha value.
    # This means max rank <= 9 (0-based) across all alpha columns.
    stable_hubs = []
    for i in range(k):
        if rank_matrix[i].max() <= 9:  # top-10 at every alpha
            stable_hubs.append(labels[i])

    # ── Alpha-sensitive constructs ───────────────────────────────────────
    # Rank shift = max_rank - min_rank across alpha values.
    # Constructs with shift > 10 are sensitive.
    sensitive = []
    for i in range(k):
        min_rank = int(rank_matrix[i].min())
        max_rank = int(rank_matrix[i].max())
        shift = max_rank - min_rank
        if shift > 10:
            sensitive.append({
                "construct": labels[i],
                "min_rank": min_rank + 1,   # 1-based for human readability
                "max_rank": max_rank + 1,
                "rank_shift": shift,
            })

    # Sort sensitive constructs by rank shift (largest first)
    sensitive.sort(key=lambda x: x["rank_shift"], reverse=True)

    return {
        "per_alpha": per_alpha_rankings,
        "stable_hubs": stable_hubs,
        "sensitive_constructs": sensitive,
    }


# ═════════════════════════════════════════════════════════════════════════════
# run_country — Full PPR analysis for a single country
# ═════════════════════════════════════════════════════════════════════════════

def run_country(country: str, alpha: float = 0.20,
                do_alpha_sweep: bool = True, wave: int = 7) -> dict:
    """
    Run the full PPR influence analysis for one country.

    Steps:
      1. Load the 55x55 weight matrix
      2. Build PPRMapper and compute the full influence matrix
      3. Extract hub scores, sink scores, hub/sink rankings
      4. Run scenario analysis (unit shock at the top hub)
      5. Optionally run alpha sensitivity sweep
      6. Validate against Floyd-Warshall mediator scores

    Parameters
    ----------
    country : str
        3-letter country code (e.g., "MEX", "USA").
    alpha : float, default 0.20
        PPR teleportation probability.
    do_alpha_sweep : bool, default True
        Whether to run the alpha sensitivity sweep.

    Returns
    -------
    result : dict
        Full analysis results for this country.
    """
    print(f"\n{'='*70}")
    print(f"  PPR Influence — {country}  (alpha={alpha})")
    print(f"{'='*70}")

    # ── Load data ────────────────────────────────────────────────────────
    W, labels = load_weight_matrix(country, wave=wave)
    k = W.shape[0]
    print(f"  Loaded {k}x{k} weight matrix (W{wave}), {len(labels)} constructs")

    # ── Build mapper and compute full PPR matrix ─────────────────────────
    t0 = time.time()
    mapper = PPRMapper(W, labels, alpha=alpha)
    Pi = mapper.full_ppr_matrix()
    t_ppr = time.time() - t0
    print(f"  Full PPR matrix computed in {t_ppr:.2f}s")

    # ── Hub and sink scores ──────────────────────────────────────────────
    hubs = mapper.hub_scores(Pi)
    sinks = mapper.sink_scores(Pi)

    # Rankings: sort descending by score
    hub_order = np.argsort(-hubs)
    sink_order = np.argsort(-sinks)

    hub_ranking = [
        {"rank": i + 1, "construct": labels[idx], "score": float(hubs[idx])}
        for i, idx in enumerate(hub_order)
    ]
    sink_ranking = [
        {"rank": i + 1, "construct": labels[idx], "score": float(sinks[idx])}
        for i, idx in enumerate(sink_order)
    ]

    # Print top-10 hubs and sinks
    print(f"\n  Top-10 hubs (outward influence):")
    for entry in hub_ranking[:10]:
        print(f"    {entry['rank']:>2}. {entry['construct']:<45s} {entry['score']:.6f}")

    print(f"\n  Top-10 sinks (inward influence):")
    for entry in sink_ranking[:10]:
        print(f"    {entry['rank']:>2}. {entry['construct']:<45s} {entry['score']:.6f}")

    # ── Asymmetry: largest directional imbalances ────────────────────────
    A = mapper.asymmetry(Pi)
    # Find the top-5 most asymmetric pairs (i influences j >> j influences i)
    # We look at the upper triangle to avoid double-counting.
    asym_pairs = []
    for i in range(k):
        for j in range(i + 1, k):
            # A[j,i] > 0 means i→j is stronger than j→i
            val = A[j, i]
            if abs(val) > 0:
                if val > 0:
                    asym_pairs.append((labels[i], labels[j], float(val)))
                else:
                    asym_pairs.append((labels[j], labels[i], float(-val)))
    asym_pairs.sort(key=lambda x: x[2], reverse=True)

    print(f"\n  Top-5 asymmetric influence pairs (A → B more than B → A):")
    for src, tgt, val in asym_pairs[:5]:
        print(f"    {src:<35s} → {tgt:<35s}  delta={val:.6f}")

    # ── Scenario: unit shock at the top hub ──────────────────────────────
    top_hub_idx = int(hub_order[0])
    scenario_shifts = mapper.scenario(Pi, top_hub_idx, magnitude=1.0)

    print(f"\n  Scenario: unit shock at '{labels[top_hub_idx]}'")
    print(f"  Top-5 implied shifts:")
    for entry in scenario_shifts[:5]:
        print(f"    {entry['construct']:<45s} {entry['shift']:+.6f}")

    # ── Alpha sensitivity sweep ──────────────────────────────────────────
    alpha_result = None
    if do_alpha_sweep:
        t0 = time.time()
        alpha_result = alpha_sweep(W, labels)
        t_sweep = time.time() - t0
        print(f"\n  Alpha sweep ({len(alpha_result['per_alpha'])} values) "
              f"in {t_sweep:.2f}s")
        print(f"  Alpha-stable hubs (top-10 at all alphas): "
              f"{alpha_result['stable_hubs']}")
        if alpha_result["sensitive_constructs"]:
            print(f"  Alpha-sensitive constructs "
                  f"(rank shift > 10):")
            for entry in alpha_result["sensitive_constructs"][:5]:
                print(f"    {entry['construct']:<40s} "
                      f"rank {entry['min_rank']}-{entry['max_rank']} "
                      f"(shift={entry['rank_shift']})")
        else:
            print(f"  No alpha-sensitive constructs (all rank shifts <= 10)")

    # ── Validation: compare against Floyd-Warshall mediator scores ───────
    mediator_corr = _validate_against_mediators(country, labels, hubs)

    # ── Assemble results ─────────────────────────────────────────────────
    result = {
        "country": country,
        "alpha": alpha,
        "n_constructs": k,
        "hub_scores": {labels[i]: float(hubs[i]) for i in range(k)},
        "sink_scores": {labels[i]: float(sinks[i]) for i in range(k)},
        "hub_ranking": hub_ranking,
        "sink_ranking": sink_ranking,
        "top_asymmetric_pairs": [
            {"source": src, "target": tgt, "asymmetry": val}
            for src, tgt, val in asym_pairs[:20]
        ],
        "scenario": {
            "seed": labels[top_hub_idx],
            "magnitude": 1.0,
            "shifts": scenario_shifts[:20],  # top-20 for brevity
        },
        "mediator_correlation": mediator_corr,
    }

    if alpha_result is not None:
        result["alpha_sensitivity"] = alpha_result

    return result


# ═════════════════════════════════════════════════════════════════════════════
# Validation against Floyd-Warshall mediator scores
# ═════════════════════════════════════════════════════════════════════════════

def _validate_against_mediators(country: str, labels: list[str],
                                hub_scores: np.ndarray) -> dict:
    """
    Compare PPR hub rankings against Floyd-Warshall mediator scores.

    The mediator scores (from TDA pipeline Phase 1) measure how often each
    construct lies on shortest paths between other constructs.  PPR hub
    scores measure how much influence spreads from each construct through
    *all* paths (weighted by transition probability).

    A high Spearman correlation means both measures agree on which constructs
    are central.  Low correlation reveals constructs that are "broad conduits"
    (high PPR, low mediator — many redundant paths) vs. "narrow bottlenecks"
    (low PPR, high mediator — sole shortest path).

    Parameters
    ----------
    country : str
        3-letter country code.
    labels : list[str]
        Construct labels.
    hub_scores : (k,) ndarray
        PPR hub scores for this country.

    Returns
    -------
    result : dict
        Spearman rho, p-value, and interpretation.
    """
    try:
        all_mediator_scores = load_mediator_scores()
    except FileNotFoundError:
        print(f"\n  [skip] Floyd-Warshall mediator scores not found — "
              f"skipping validation")
        return {"status": "mediator_scores_not_found"}

    # mediator_scores.json structure: {country: {scores: {construct: value}, ...}}
    if country not in all_mediator_scores:
        print(f"\n  [skip] No mediator scores for {country}")
        return {"status": "country_not_in_mediator_scores"}

    country_entry = all_mediator_scores[country]
    # Extract the scores sub-dict (the actual construct → score mapping)
    country_mediators = country_entry.get("scores", country_entry)

    # Align: only compare constructs present in both PPR labels and mediator
    # scores.  They should match (both come from the same weight matrix),
    # but we handle mismatches gracefully.
    ppr_vals = []
    med_vals = []
    matched_labels = []

    for i, label in enumerate(labels):
        if label in country_mediators:
            ppr_vals.append(hub_scores[i])
            med_vals.append(country_mediators[label])
            matched_labels.append(label)

    if len(matched_labels) < 5:
        print(f"\n  [skip] Only {len(matched_labels)} matched constructs — "
              f"too few for correlation")
        return {"status": "too_few_matches", "n_matched": len(matched_labels)}

    # Spearman rank correlation: are the two rankings monotonically related?
    rho, p_value = stats.spearmanr(ppr_vals, med_vals)

    # Interpretation thresholds (conventional):
    #   rho > 0.7: strong agreement
    #   rho 0.4-0.7: moderate — some constructs differ in PPR vs. mediator
    #   rho < 0.4: weak — the two measures capture different aspects
    if rho > 0.7:
        interp = "strong agreement"
    elif rho > 0.4:
        interp = "moderate agreement"
    else:
        interp = "weak agreement — PPR and mediator capture different aspects"

    print(f"\n  Mediator validation ({len(matched_labels)} constructs matched):")
    print(f"    Spearman rho = {rho:.4f}  (p = {p_value:.2e})  [{interp}]")

    return {
        "spearman_rho": float(rho),
        "p_value": float(p_value),
        "n_matched": len(matched_labels),
        "interpretation": interp,
    }


# ═════════════════════════════════════════════════════════════════════════════
# cross_country_comparison — Universal vs. zone-specific hubs across 66 countries
# ═════════════════════════════════════════════════════════════════════════════

def cross_country_comparison(all_results: dict, wave: int = 7) -> dict:
    """
    Compare PPR hub rankings across all countries.

    Builds a (55 x N_countries) matrix of hub ranks and identifies:
      - Universal hubs: constructs in the top-10 in >50 countries.
        These are SES network positions that are structurally central
        regardless of cultural context.
      - Zone-specific hubs: constructs that are top-10 in a majority of
        countries within a cultural zone but not universally.  These
        reveal how SES network architecture varies by cultural region.

    Parameters
    ----------
    all_results : dict
        {country: result_dict} from run_country().

    Returns
    -------
    comparison : dict
        Universal hubs, zone-specific hubs, hub rank matrix.
    """
    # ── Collect all construct labels (union across countries) ─────────
    # In practice all countries use the same 55 constructs, but we handle
    # the general case.
    manifest = load_manifest(wave=wave)
    countries = sorted(all_results.keys())
    n_countries = len(countries)

    # Use construct_index from manifest for canonical ordering
    if "construct_index" in manifest:
        all_labels = manifest["construct_index"]
    else:
        # Fallback: collect from first country's results
        first = next(iter(all_results.values()))
        all_labels = [entry["construct"] for entry in first["hub_ranking"]]

    k = len(all_labels)
    label_to_idx = {lab: i for i, lab in enumerate(all_labels)}

    # ── Build hub rank matrix ────────────────────────────────────────────
    # rank_matrix[i, c] = rank of construct i in country c (1-based)
    # Missing constructs get rank = k (worst possible).
    rank_matrix = np.full((k, n_countries), k, dtype=int)

    for c_idx, country in enumerate(countries):
        result = all_results[country]
        for entry in result["hub_ranking"]:
            label = entry["construct"]
            rank = entry["rank"]  # already 1-based
            if label in label_to_idx:
                rank_matrix[label_to_idx[label], c_idx] = rank

    # ── Universal hubs ───────────────────────────────────────────────────
    # Count how many countries each construct is in the top-10
    top10_counts = (rank_matrix <= 10).sum(axis=1)  # (k,)
    threshold = min(50, int(n_countries * 0.75))  # >50 or >75% of countries

    universal_hubs = []
    for i in range(k):
        if top10_counts[i] > threshold:
            universal_hubs.append({
                "construct": all_labels[i],
                "top10_count": int(top10_counts[i]),
                "median_rank": int(np.median(rank_matrix[i])),
            })
    universal_hubs.sort(key=lambda x: x["top10_count"], reverse=True)

    print(f"\n  Universal hubs (top-10 in >{threshold} of {n_countries} countries):")
    if universal_hubs:
        for entry in universal_hubs:
            print(f"    {entry['construct']:<45s} "
                  f"top-10 in {entry['top10_count']}/{n_countries} countries  "
                  f"(median rank {entry['median_rank']})")
    else:
        print(f"    (none)")

    # ── Zone-specific hubs ───────────────────────────────────────────────
    # For each cultural zone, find constructs that are top-10 in a majority
    # of zone members but are NOT universal hubs.
    cultural_zones = manifest.get("cultural_zones", {})
    universal_set = {h["construct"] for h in universal_hubs}

    zone_hubs: dict[str, list[dict]] = {}
    for zone, zone_countries in cultural_zones.items():
        # Filter to countries we actually have results for
        zone_present = [c for c in zone_countries if c in all_results]
        if len(zone_present) < 3:
            continue  # need at least 3 countries for meaningful zone analysis

        # Get column indices for zone countries
        zone_c_indices = [countries.index(c) for c in zone_present
                          if c in countries]

        # Count top-10 appearances within this zone
        zone_top10 = (rank_matrix[:, zone_c_indices] <= 10).sum(axis=1)
        zone_threshold = len(zone_present) // 2  # majority

        zone_specific = []
        for i in range(k):
            label = all_labels[i]
            if label in universal_set:
                continue  # skip universal hubs
            if zone_top10[i] > zone_threshold:
                zone_specific.append({
                    "construct": label,
                    "zone_top10_count": int(zone_top10[i]),
                    "zone_size": len(zone_present),
                    "global_median_rank": int(np.median(rank_matrix[i])),
                })
        zone_specific.sort(key=lambda x: x["zone_top10_count"], reverse=True)

        if zone_specific:
            zone_hubs[zone] = zone_specific

    if zone_hubs:
        print(f"\n  Zone-specific hubs:")
        for zone, entries in zone_hubs.items():
            print(f"\n    [{zone}]")
            for entry in entries[:5]:
                print(f"      {entry['construct']:<40s} "
                      f"top-10 in {entry['zone_top10_count']}/"
                      f"{entry['zone_size']} zone members  "
                      f"(global median rank {entry['global_median_rank']})")

    # ── Assemble comparison result ───────────────────────────────────────
    return {
        "n_countries": n_countries,
        "n_constructs": k,
        "universal_hubs": universal_hubs,
        "zone_specific_hubs": zone_hubs,
        "hub_rank_matrix": {
            "constructs": all_labels,
            "countries": countries,
            "ranks": rank_matrix.tolist(),
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="PPR influence mapping on WVS construct networks (Stage 3)")
    parser.add_argument("--country", default="MEX",
                        help="3-letter country code (default: MEX)")
    parser.add_argument("--all", action="store_true",
                        help="Run all 66 countries + cross-country comparison")
    parser.add_argument("--alpha", type=float, default=0.20,
                        help="PPR teleportation probability (default: 0.20)")
    parser.add_argument("--wave", type=int, default=7, choices=[3, 4, 5, 6, 7],
                        help="WVS wave number (default: 7)")
    args = parser.parse_args()

    out_dir = get_output_dir(wave=args.wave)

    if args.all:
        # ── All-country mode ─────────────────────────────────────────────
        manifest = load_manifest(wave=args.wave)
        countries = sorted(manifest.get("countries", []))
        print(f"\nRunning PPR influence for {len(countries)} countries "
              f"(W{args.wave}, alpha={args.alpha})")

        all_results = {}
        t_total = time.time()

        for i, country in enumerate(countries):
            print(f"\n[{i+1}/{len(countries)}]", end="")
            try:
                result = run_country(country, alpha=args.alpha,
                                     do_alpha_sweep=True, wave=args.wave)
                all_results[country] = result

                # Save per-country JSON
                save_json(result, out_dir / f"{country}_ppr.json")
            except Exception as e:
                print(f"\n  ERROR for {country}: {e}")
                continue

        t_total = time.time() - t_total
        print(f"\n{'='*70}")
        print(f"  All countries completed in {t_total:.1f}s")
        print(f"{'='*70}")

        # Cross-country comparison
        if len(all_results) > 1:
            print(f"\n  Cross-country comparison "
                  f"({len(all_results)} countries)...")
            comparison = cross_country_comparison(all_results, wave=args.wave)
            save_json(comparison, out_dir / "ppr_hub_comparison.json")

    else:
        # ── Single-country mode ──────────────────────────────────────────
        result = run_country(args.country, alpha=args.alpha,
                             do_alpha_sweep=True, wave=args.wave)
        save_json(result, out_dir / f"{args.country}_ppr.json")


if __name__ == "__main__":
    main()
