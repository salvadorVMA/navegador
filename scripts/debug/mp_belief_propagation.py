"""
Loopy Belief Propagation on Potts MRF for WVS Construct Networks
================================================================

Stage 1 of the message-passing framework.

What this computes
------------------
Given a weighted graph of 55 WVS constructs (edges = DR bridge gamma values),
we model each construct as a discrete random variable with K=5 states
(corresponding to the equal-frequency quintile bins used in the Julia DR
pipeline).  The joint distribution is a **Potts Markov Random Field**:

    P(x) ~ prod_i phi_i(x_i) * prod_{(i,j)} psi_{ij}(x_i, x_j)

where phi_i is the node potential (prior or evidence) and psi_{ij} is the
edge potential encoding how gamma sign and magnitude shape joint preferences.

Why Potts?
----------
The Potts model is a natural choice because:

1. **Ordinal constructs in quintile bins** -- each construct score is
   discretized into 5 ordered categories by the Julia pipeline
   (rank-normalize -> qcut -> 5 equal-frequency bins).

2. **Signed edges map to agreement/disagreement** -- positive gamma means
   "people who score high on A also score high on B" (agreement), negative
   gamma means the opposite (disagreement).  The Potts potential captures
   this with:
     - gamma > 0: exp(beta * |gamma|) when x_i == x_j, 1.0 otherwise
     - gamma < 0: exp(beta * |gamma|) when x_i != x_j, 1.0 otherwise

3. **beta controls coupling strength** -- higher beta amplifies the
   influence of gamma magnitudes.  beta=2.0 is a reasonable default; the
   beta-sweep option lets you check sensitivity.

Loopy BP (sum-product) iterates message-passing updates until convergence.
On tree graphs, BP gives exact marginals; on loopy graphs (like our dense
construct networks), it gives approximate marginals.  Damping (default 0.5)
stabilizes convergence on dense graphs.

Evidence injection
------------------
To ask "if construct X is clamped to the top quintile (state 4), how do
beliefs at all other constructs change?", we inject hard evidence at node X
(one-hot distribution on state 4) and run BP.  The resulting belief shift
(measured as KL divergence from prior to posterior) is the "lift" -- how
much information propagates from X to each other construct through the
SES-mediated network.

Running all 55 constructs as evidence nodes produces a 55x55 lift matrix,
revealing which constructs are most influential (high mean row lift) and
which are most responsive (high mean column lift).

Output
------
Per-country JSON in data/tda/message_passing/{COUNTRY}_bp.json:
  - lift_matrix: 55x55 KL-divergence lift values
  - top_influencers: top-5 constructs by mean lift (most broadcast power)
  - convergence_rate: fraction of runs that converged
  - beta_stability: (if --beta-sweep) which constructs' top-10 rankings
    are stable across beta values

Usage
-----
    python scripts/debug/mp_belief_propagation.py --country MEX
    python scripts/debug/mp_belief_propagation.py --all --beta-sweep
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

# ── Project paths ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import (  # noqa: E402
    adjacency_mask,
    get_output_dir,
    load_manifest,
    load_weight_matrix,
    save_json,
)


# ═════════════════════════════════════════════════════════════════════════════
# BeliefPropagator — Loopy BP on a signed Potts MRF
# ═════════════════════════════════════════════════════════════════════════════

class BeliefPropagator:
    """
    Loopy Belief Propagation on a Potts Markov Random Field.

    Parameters
    ----------
    W : (k, k) ndarray
        Signed weight matrix.  NaN = no edge; 0.0 = no edge.
        Positive = agreement-favoring; negative = disagreement-favoring.
    construct_labels : list[str]
        Human-readable label for each of the k nodes.
    n_states : int
        Number of discrete states per node (quintile bins, default 5).
    beta : float
        Inverse temperature / coupling strength.  Scales the influence of
        edge weights on the Potts potential.  Higher = stronger coupling.
    damping : float
        Damping coefficient in [0, 1).  The BP message update is:
            m_new = damping * m_old + (1 - damping) * m_computed
        0.5 is a safe default for dense graphs.
    max_iter : int
        Maximum number of BP iterations before declaring non-convergence.
    tol : float
        Convergence threshold: max absolute change across all messages.
    """

    def __init__(
        self,
        W: np.ndarray,
        construct_labels: list[str],
        n_states: int = 5,
        beta: float = 2.0,
        damping: float = 0.5,
        max_iter: int = 200,
        tol: float = 1e-4,
    ):
        self.W = W
        self.labels = construct_labels
        self.k = W.shape[0]
        self.n_states = n_states
        self.beta = beta
        self.damping = damping
        self.max_iter = max_iter
        self.tol = tol

        # ── Build adjacency from the weight matrix ──────────────────────────
        # mask[i,j] = True iff there is a real edge (not NaN, not zero)
        mask = adjacency_mask(W)

        # Neighbor sets: for each node i, the set of adjacent node indices.
        # Using set comprehension for O(1) membership tests during message
        # passing (we need "neighbors of i excluding j" frequently).
        self.nbrs: dict[int, set[int]] = {
            i: {j for j in range(self.k) if mask[i, j]}
            for i in range(self.k)
        }

        # ── Precompute Potts edge potentials ────────────────────────────────
        # For each real edge (i,j), psi[(i,j)] is an (n_states, n_states)
        # array encoding how the two nodes prefer to align.
        #
        # Potts model:
        #   - Positive weight (gamma > 0): agreement is favored.
        #     psi[xi, xj] = exp(beta * |w|) if xi == xj, else 1.0
        #     Interpretation: same-state pairs get a multiplicative boost.
        #
        #   - Negative weight (gamma < 0): disagreement is favored.
        #     psi[xi, xj] = exp(beta * |w|) if xi != xj, else 1.0
        #     Interpretation: different-state pairs get the boost.
        #
        # The magnitude |w| modulates how strong the preference is.
        # beta amplifies all couplings uniformly (inverse temperature).
        self.psi: dict[tuple[int, int], np.ndarray] = {}

        for i in range(self.k):
            for j in self.nbrs[i]:
                w_ij = W[i, j]
                # Skip if somehow NaN slipped through (defensive)
                if np.isnan(w_ij):
                    continue

                pot = np.ones((n_states, n_states), dtype=np.float64)
                coupling = np.exp(beta * abs(w_ij))

                if w_ij > 0:
                    # Agreement: boost diagonal (xi == xj)
                    np.fill_diagonal(pot, coupling)
                else:
                    # Disagreement: boost off-diagonal (xi != xj)
                    pot[:, :] = coupling
                    np.fill_diagonal(pot, 1.0)

                self.psi[(i, j)] = pot

    # ─────────────────────────────────────────────────────────────────────────
    # run() — Main loopy BP loop
    # ─────────────────────────────────────────────────────────────────────────

    def run(
        self,
        evidence: dict[int, np.ndarray] | None = None,
    ) -> tuple[np.ndarray, bool, int, float]:
        """
        Run loopy belief propagation.

        Parameters
        ----------
        evidence : dict mapping node index -> observed distribution
            Each value is a length-n_states array (probability distribution).
            Hard evidence = one-hot vector (e.g., [0, 0, 0, 0, 1] for state 4).
            Soft evidence = any valid distribution over states.
            Nodes not in the dict get uniform priors.

        Returns
        -------
        beliefs : (k, n_states) array
            Approximate marginal distribution at each node.
        converged : bool
            Whether BP converged within max_iter iterations.
        iters_used : int
            Number of iterations actually performed.
        max_change : float
            Final maximum absolute change across all messages.
        """
        k = self.k
        S = self.n_states
        evidence = evidence or {}

        # ── Node potentials (priors) ────────────────────────────────────────
        # phi[i] is the local prior at node i.  Uniform by default.
        # Evidence nodes get their observed distribution as the prior,
        # which effectively clamps the BP to respect those observations.
        phi = np.full((k, S), 1.0 / S, dtype=np.float64)
        for node_idx, obs in evidence.items():
            # Normalize the evidence distribution (defensive)
            obs_arr = np.asarray(obs, dtype=np.float64)
            obs_arr = obs_arr / (obs_arr.sum() + 1e-30)
            phi[node_idx] = obs_arr

        # ── Initialize messages to uniform ──────────────────────────────────
        # messages[(i, j)] is the message FROM node i TO node j.
        # Shape: (n_states,) — a distribution over j's states.
        # Initial value: uniform, meaning "i has no information for j yet".
        messages: dict[tuple[int, int], np.ndarray] = {}
        for i in range(k):
            for j in self.nbrs[i]:
                messages[(i, j)] = np.full(S, 1.0 / S, dtype=np.float64)

        # ── Iterative message passing ───────────────────────────────────────
        # At each iteration, every directed edge (i -> j) updates its
        # message using the sum-product rule:
        #
        #   m_{i->j}(x_j) = sum_{x_i} [ psi_{ij}(x_i, x_j)
        #                                * phi_i(x_i)
        #                                * prod_{k in N(i)\j} m_{k->i}(x_i) ]
        #
        # This is the core BP equation.  Intuitively:
        # - For each possible state x_i of node i...
        # - Multiply: (1) the edge potential (does x_i agree/disagree with x_j?),
        #             (2) i's local prior, and
        #             (3) all incoming messages to i EXCEPT from j
        #               (to avoid double-counting j's own information).
        # - Sum over all x_i to marginalize out i's state.
        # - The result tells j what states are favored from i's perspective.

        converged = False
        max_change = float("inf")

        for iteration in range(1, self.max_iter + 1):
            max_change = 0.0

            for i in range(k):
                for j in self.nbrs[i]:
                    # Skip edges with no precomputed potential (defensive)
                    if (i, j) not in self.psi:
                        continue

                    psi_ij = self.psi[(i, j)]  # (S, S)

                    # ── Compute incoming product at node i, excluding j ─────
                    # Start with phi_i (local prior / evidence)
                    incoming = phi[i].copy()  # (S,)

                    for nb in self.nbrs[i]:
                        if nb != j:
                            incoming *= messages[(nb, i)]

                    # ── Sum-product: marginalize over x_i ───────────────────
                    # m_new[x_j] = sum_{x_i} psi_ij[x_i, x_j] * incoming[x_i]
                    # This is a matrix-vector product: psi_ij.T @ incoming
                    m_computed = psi_ij.T @ incoming  # (S,)

                    # ── Normalize to valid probability distribution ──────────
                    m_sum = m_computed.sum()
                    if m_sum > 0:
                        m_computed /= m_sum
                    else:
                        # Degenerate case: fall back to uniform
                        m_computed[:] = 1.0 / S

                    # ── Damped update ───────────────────────────────────────
                    # Mixing old and new messages prevents oscillation on
                    # loopy graphs.  damping=0.5 means equal weight to old
                    # and new, which is conservative but stable.
                    m_old = messages[(i, j)]
                    m_new = self.damping * m_old + (1.0 - self.damping) * m_computed

                    # ── Track convergence ───────────────────────────────────
                    change = np.max(np.abs(m_new - m_old))
                    if change > max_change:
                        max_change = change

                    messages[(i, j)] = m_new

            # ── Check convergence ───────────────────────────────────────────
            if max_change < self.tol:
                converged = True
                break

        # ── Compute final beliefs ───────────────────────────────────────────
        # Belief at node i = normalized product of local potential and all
        # incoming messages.  This is the approximate marginal P(x_i).
        beliefs = np.zeros((k, S), dtype=np.float64)
        for i in range(k):
            b = phi[i].copy()
            for nb in self.nbrs[i]:
                b *= messages[(nb, i)]
            b_sum = b.sum()
            if b_sum > 0:
                b /= b_sum
            else:
                b[:] = 1.0 / S
            beliefs[i] = b

        return beliefs, converged, iteration, max_change

    # ─────────────────────────────────────────────────────────────────────────
    # compute_lift() — KL divergence from prior to posterior
    # ─────────────────────────────────────────────────────────────────────────

    def compute_lift(self, beliefs: np.ndarray) -> np.ndarray:
        """
        Compute per-node "lift" as KL(posterior || prior).

        KL divergence measures how much the posterior beliefs diverge from
        the uniform prior.  Higher lift = more information gained from the
        network's message passing.

        KL(P || Q) = sum_x P(x) * log(P(x) / Q(x))

        With uniform prior Q(x) = 1/S, this simplifies to:
            KL = log(S) + sum_x P(x) * log(P(x))
           = log(S) - H(P)
        where H(P) is the entropy of the posterior.  Max lift = log(S)
        (posterior is a delta function).  Zero lift = posterior is still
        uniform (no information gained).

        Parameters
        ----------
        beliefs : (k, n_states) array
            Posterior beliefs from BP.

        Returns
        -------
        lift : (k,) array
            KL divergence at each node.  Non-negative.
        """
        S = self.n_states
        prior = 1.0 / S  # uniform prior for each state

        # KL = sum_x post(x) * log(post(x) / prior)
        # Add small epsilon to avoid log(0)
        eps = 1e-12
        log_ratio = np.log((beliefs + eps) / prior)
        kl = np.sum(beliefs * log_ratio, axis=1)  # (k,)

        # Clamp to non-negative (numerical noise can produce tiny negatives)
        return np.maximum(kl, 0.0)


# ═════════════════════════════════════════════════════════════════════════════
# run_country() — Full BP analysis for one country
# ═════════════════════════════════════════════════════════════════════════════

def run_country(
    country: str,
    beta: float = 2.0,
    betas_sweep: list[float] | None = None,
) -> dict:
    """
    Run belief propagation for one country.

    For each of k constructs, inject hard evidence at state=4 (top quintile)
    and measure how beliefs shift across the entire network.  This produces
    a k x k lift matrix.

    If betas_sweep is provided, repeat the full analysis at each beta value
    and identify which constructs' top-10 influence rankings are stable
    (appear in the top-10 at every beta).

    Parameters
    ----------
    country : str
        Three-letter country code (e.g., "MEX").
    beta : float
        Default coupling strength for the main run.
    betas_sweep : list[float] or None
        If provided, run BP at each beta and report ranking stability.

    Returns
    -------
    results : dict
        Serializable dict with lift_matrix, top_influencers, convergence
        stats, and optionally beta_stability.
    """
    # ── Load data ───────────────────────────────────────────────────────────
    W, labels = load_weight_matrix(country)
    k = W.shape[0]

    print(f"\n{'='*60}")
    print(f"  Belief Propagation: {country}")
    print(f"  {k} constructs, beta={beta}, damping=0.5")
    print(f"{'='*60}")

    # ── Count real edges ────────────────────────────────────────────────────
    mask = adjacency_mask(W)
    n_edges = mask.sum() // 2  # undirected
    print(f"  edges: {n_edges}")

    # ── Main run at default beta ────────────────────────────────────────────
    lift_matrix, convergence_flags = _run_all_evidence(W, labels, k, beta)

    n_converged = sum(convergence_flags)
    convergence_rate = n_converged / k
    print(f"  convergence: {n_converged}/{k} ({convergence_rate:.1%})")

    # ── Top influencers by mean lift ────────────────────────────────────────
    # Mean lift across all columns (how much does clamping construct i
    # affect the rest of the network on average?)
    mean_lift = np.nanmean(lift_matrix, axis=1)  # (k,)
    top_idx = np.argsort(mean_lift)[::-1][:5]
    top_influencers = [
        {"rank": rank + 1, "construct": labels[idx], "mean_lift": float(mean_lift[idx])}
        for rank, idx in enumerate(top_idx)
    ]

    print(f"\n  Top-5 most influential constructs (mean KL lift):")
    for entry in top_influencers:
        print(f"    {entry['rank']}. {entry['construct']}: {entry['mean_lift']:.4f}")

    # ── Build results dict ──────────────────────────────────────────────────
    results = {
        "country": country,
        "beta": beta,
        "n_constructs": k,
        "n_edges": int(n_edges),
        "convergence_rate": convergence_rate,
        "lift_matrix": lift_matrix,
        "construct_labels": labels,
        "top_influencers": top_influencers,
        "mean_lift_per_construct": mean_lift,
    }

    # ── Beta sweep (sensitivity analysis) ───────────────────────────────────
    # Running at multiple beta values lets us check whether the top
    # influencers are robust to the coupling strength hyperparameter.
    # A construct that stays in the top-10 across all betas is genuinely
    # central, not an artifact of a particular beta choice.
    if betas_sweep:
        print(f"\n  Beta sweep: {betas_sweep}")
        top10_per_beta: dict[float, set[str]] = {}

        for b in betas_sweep:
            lm_b, _ = _run_all_evidence(W, labels, k, b)
            ml_b = np.nanmean(lm_b, axis=1)
            top10_idx = np.argsort(ml_b)[::-1][:10]
            top10_per_beta[b] = {labels[idx] for idx in top10_idx}
            print(f"    beta={b}: top-10 = {[labels[idx] for idx in top10_idx[:5]]}...")

        # Stable constructs: appear in top-10 at ALL beta values
        stable = set.intersection(*top10_per_beta.values())
        print(f"\n  Beta-stable top-10 constructs ({len(stable)}):")
        for name in sorted(stable):
            print(f"    - {name}")

        results["beta_sweep"] = {
            "betas": betas_sweep,
            "top10_per_beta": {
                str(b): sorted(names) for b, names in top10_per_beta.items()
            },
            "stable_constructs": sorted(stable),
        }

    return results


def _run_all_evidence(
    W: np.ndarray,
    labels: list[str],
    k: int,
    beta: float,
) -> tuple[np.ndarray, list[bool]]:
    """
    Run BP once per construct as evidence node; return lift matrix and
    convergence flags.

    For each construct i in 0..k-1:
      1. Create evidence dict: node i clamped to state 4 (top quintile)
      2. Run BP to convergence
      3. Compute KL-divergence lift at every node
      4. Store as row i of the lift matrix

    The evidence state is 4 (0-indexed) = the 5th quintile = top 20%.
    This asks: "if we know this construct is in the top quintile, how does
    that information propagate through the network?"

    Parameters
    ----------
    W : (k, k) weight matrix
    labels : construct names
    k : number of constructs
    beta : coupling strength

    Returns
    -------
    lift_matrix : (k, k) array
        lift_matrix[i, j] = KL lift at node j when node i is clamped.
    convergence_flags : list[bool]
        Whether BP converged for each evidence node.
    """
    bp = BeliefPropagator(W, labels, n_states=5, beta=beta)

    lift_matrix = np.zeros((k, k), dtype=np.float64)
    convergence_flags: list[bool] = []

    for i in range(k):
        # Hard evidence: one-hot on state 4 (top quintile, 0-indexed)
        evidence_dist = np.zeros(5, dtype=np.float64)
        evidence_dist[4] = 1.0
        evidence = {i: evidence_dist}

        beliefs, converged, iters, max_change = bp.run(evidence=evidence)
        lift = bp.compute_lift(beliefs)

        lift_matrix[i, :] = lift
        convergence_flags.append(converged)

    return lift_matrix, convergence_flags


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Loopy Belief Propagation on Potts MRF for WVS construct networks",
    )
    parser.add_argument(
        "--country",
        default="MEX",
        help="Three-letter country code (default: MEX)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run BP for all 66 countries in the manifest",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=2.0,
        help="Coupling strength / inverse temperature (default: 2.0)",
    )
    parser.add_argument(
        "--beta-sweep",
        action="store_true",
        help="Run sensitivity analysis at beta = {0.5, 1.0, 2.0, 4.0}",
    )
    args = parser.parse_args()

    betas_sweep = [0.5, 1.0, 2.0, 4.0] if args.beta_sweep else None
    out_dir = get_output_dir()

    t0 = time.time()

    if args.all:
        # ── Run all countries ───────────────────────────────────────────────
        manifest = load_manifest()
        countries = sorted(manifest["countries"])
        print(f"Running BP for {len(countries)} countries...")

        all_summaries = []
        for country in countries:
            try:
                results = run_country(country, beta=args.beta, betas_sweep=betas_sweep)
                save_json(results, out_dir / f"{country}_bp.json")
                all_summaries.append({
                    "country": country,
                    "convergence_rate": results["convergence_rate"],
                    "top_influencer": results["top_influencers"][0]["construct"],
                    "top_mean_lift": results["top_influencers"][0]["mean_lift"],
                })
            except Exception as e:
                print(f"  ERROR {country}: {e}")
                all_summaries.append({"country": country, "error": str(e)})

        # ── Cross-country summary ───────────────────────────────────────────
        elapsed = time.time() - t0
        print(f"\n{'='*60}")
        print(f"  All-country BP complete in {elapsed:.1f}s")
        print(f"{'='*60}")

        ok = [s for s in all_summaries if "error" not in s]
        if ok:
            avg_conv = np.mean([s["convergence_rate"] for s in ok])
            print(f"  Mean convergence rate: {avg_conv:.1%}")

            # Most common top influencer across countries
            from collections import Counter
            top_counts = Counter(s["top_influencer"] for s in ok)
            most_common = top_counts.most_common(3)
            print(f"  Most common top influencer:")
            for name, count in most_common:
                print(f"    {name}: {count}/{len(ok)} countries")

        save_json({"summaries": all_summaries, "elapsed_s": elapsed}, out_dir / "bp_all_summary.json")

    else:
        # ── Single country ──────────────────────────────────────────────────
        results = run_country(args.country, beta=args.beta, betas_sweep=betas_sweep)
        save_json(results, out_dir / f"{args.country}_bp.json")

        elapsed = time.time() - t0
        print(f"\n  Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
