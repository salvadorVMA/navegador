"""
Propagator -- Phase 2 dynamics layer for the Graph Traversal Engine.

Three complementary propagation methods that answer: "If construct A shifts,
what happens to other constructs according to the SES-conditioned network?"

Methods:
  1. Belief Propagation (BP): Information-theoretic -- how much does knowing
     A's value tell us about B's distribution? Uses pre-computed BP lift matrix.
  2. Personalized PageRank (PPR): Structural influence -- how much network
     traffic flows from A to B? Computed on-the-fly from the weight matrix.
  3. Spectral Heat Kernel: Multi-scale diffusion -- at what time scale does
     a signal at A reach B? Computed on-the-fly via eigendecomposition.

All methods produce unsigned magnitudes. Signs are restored via Dijkstra
path-sign accumulation from wvs_ontology.find_path().

The consensus scorer reconciles the three rankings into a single prediction.

IMPORTANT: This is NOT causal. gamma measures SES-conditioned monotonic
covariation. "A increases => B increases" means "people in higher SES
positions tend to score higher on both A and B."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from graph_traversal_engine.context import ContextGraph, Fingerprint
from graph_traversal_engine.wvs_ontology import WVSOntologyQuery


# -- Result containers ---------------------------------------------------------

@dataclass
class PropagationEffect:
    """One construct's predicted effect from a single propagation method."""
    construct: str
    magnitude: float        # Predicted shift magnitude (method-specific units)
    direction: int          # +1 (co-movement) or -1 (counter-movement)
    confidence: float       # 0-1 method-specific confidence
    rank: int               # Rank among all constructs for this method


@dataclass
class ConsensusEffect:
    """A construct's consensus-ranked effect across all three methods."""
    construct: str
    direction: int
    bp_rank: Optional[int]          # Rank in BP (None if BP unavailable)
    ppr_rank: Optional[int]         # Rank in PPR
    spectral_rank: Optional[int]    # Rank in spectral at characteristic time t*
    agreement_score: float          # 0-1: fraction of methods in top-N
    confidence: str                 # "high" (3/3), "medium" (2/3), "low" (1/3)
    mean_magnitude: float           # Average normalized magnitude across methods


@dataclass
class PropagationResult:
    """Combined result from all three propagation methods."""
    anchor: str
    anchor_direction: int           # +1 (increase) or -1 (decrease)
    context_str: str
    bp_effects: list[PropagationEffect]
    ppr_effects: list[PropagationEffect]
    spectral_effects: dict[float, list[PropagationEffect]]  # t -> effects
    consensus: list[ConsensusEffect]
    method_agreement: dict[str, float]  # Pairwise rank correlation
    n_present: int                      # Constructs with data in this context


# -- Propagator ----------------------------------------------------------------

# Default time scales for spectral diffusion (log-spaced).
# t* = 1/lambda_2 is the characteristic time; we sample around it.
_DEFAULT_TIME_SCALES = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

# Consensus top-N threshold: a construct must be in top-N of a method
# to count toward agreement.
_CONSENSUS_TOP_N = 10


class Propagator:
    """
    Multi-method signal propagator on a single context graph.

    Computes BP, PPR, and spectral diffusion effects from an anchor construct,
    then builds a consensus ranking.

    Usage:
        oq = WVSOntologyQuery(family, "MEX", 7)
        prop = Propagator(oq)
        result = prop.propagate("gender_role_traditionalism|WVS_D", direction=-1)
        for eff in result.consensus[:5]:
            print(f"  {eff.construct}: dir={eff.direction}, agreement={eff.agreement_score:.0%}")
    """

    def __init__(self, oq: WVSOntologyQuery) -> None:
        self._oq = oq
        self._graph: ContextGraph = oq.graph
        self._constructs = self._graph.constructs
        self._n = len(self._constructs)

        # Precompute clean weight matrix (NaN -> 0) and absolute version
        W = self._graph.weight_matrix.copy()
        W = np.nan_to_num(W, nan=0.0)
        self._W = W
        self._W_abs = np.abs(W)

        # Precompute sign matrix for direction restoration
        self._sign_matrix = np.sign(W)

        # Cache eigendecomposition (computed lazily)
        self._eigen_cache: Optional[tuple[np.ndarray, np.ndarray]] = None

    # -- BP propagation --------------------------------------------------------

    def _bp_propagate(
        self, anchor_idx: int, direction: int
    ) -> list[PropagationEffect]:
        """
        Use pre-computed BP lift matrix to rank constructs by information gain.

        BP lift[i,j] = KL divergence at j when i is clamped (unsigned, >= 0).
        Sign is restored from the weight matrix sign(gamma[anchor, target]).
        For non-adjacent targets, sign comes from Dijkstra path sign.
        """
        lift = self._graph.bp_lift_matrix
        if lift is None:
            return []

        row = lift[anchor_idx]
        if row.max() < 1e-10:
            return []

        # Normalize to [0, 1] for confidence
        max_lift = row.max()
        effects = []
        for j in range(self._n):
            if j == anchor_idx:
                continue
            mag = float(row[j])
            if mag < 1e-10:
                continue

            # Restore sign
            edge_sign = self._get_path_sign(anchor_idx, j)
            effects.append(PropagationEffect(
                construct=self._constructs[j],
                magnitude=mag,
                direction=direction * edge_sign,
                confidence=mag / max_lift,
                rank=0,
            ))

        effects.sort(key=lambda e: e.magnitude, reverse=True)
        for i, e in enumerate(effects):
            e.rank = i + 1
        return effects

    # -- PPR propagation -------------------------------------------------------

    def _ppr_propagate(
        self, anchor_idx: int, direction: int, alpha: float = 0.2
    ) -> list[PropagationEffect]:
        """
        Compute Personalized PageRank seeded at anchor.

        PPR models a random walker starting at anchor, following edges
        with probability proportional to |gamma|, teleporting back with
        probability alpha. The stationary distribution measures structural
        influence from the anchor.

        alpha = 0.2 balances local structure (high alpha) with global reach
        (low alpha). For a 55-node network, this produces meaningful rankings
        with ~5-hop effective reach.
        """
        W_abs = self._W_abs
        row_sums = W_abs.sum(axis=1)
        row_sums[row_sums < 1e-10] = 1.0  # Avoid division by zero for isolated nodes
        P = W_abs / row_sums[:, None]  # Row-stochastic transition matrix

        n = self._n
        e_anchor = np.zeros(n)
        e_anchor[anchor_idx] = 1.0
        pi = e_anchor.copy()

        for _ in range(100):
            pi_new = alpha * e_anchor + (1 - alpha) * P.T @ pi
            if np.max(np.abs(pi_new - pi)) < 1e-8:
                break
            pi = pi_new

        # Remove self and normalize for confidence
        pi[anchor_idx] = 0.0
        max_pi = pi.max()
        if max_pi < 1e-10:
            return []

        effects = []
        for j in range(n):
            if j == anchor_idx or pi[j] < 1e-10:
                continue
            edge_sign = self._get_path_sign(anchor_idx, j)
            effects.append(PropagationEffect(
                construct=self._constructs[j],
                magnitude=float(pi[j]),
                direction=direction * edge_sign,
                confidence=float(pi[j] / max_pi),
                rank=0,
            ))

        effects.sort(key=lambda e: e.magnitude, reverse=True)
        for i, e in enumerate(effects):
            e.rank = i + 1
        return effects

    # -- Spectral heat kernel propagation --------------------------------------

    def _get_eigen(self) -> tuple[np.ndarray, np.ndarray]:
        """Compute or return cached eigendecomposition of normalized Laplacian."""
        if self._eigen_cache is not None:
            return self._eigen_cache

        W_abs = self._W_abs
        D = W_abs.sum(axis=1)
        D_safe = np.where(D > 1e-10, D, 1.0)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(D_safe))

        L_norm = np.eye(self._n) - D_inv_sqrt @ W_abs @ D_inv_sqrt
        # Symmetrize to avoid numerical asymmetry
        L_norm = (L_norm + L_norm.T) / 2

        eigenvalues, eigenvectors = np.linalg.eigh(L_norm)
        # Clamp small negative eigenvalues from numerical error
        eigenvalues = np.maximum(eigenvalues, 0.0)

        self._eigen_cache = (eigenvalues, eigenvectors)
        return eigenvalues, eigenvectors

    def _spectral_propagate(
        self, anchor_idx: int, direction: int,
        time_scales: Optional[list[float]] = None,
    ) -> dict[float, list[PropagationEffect]]:
        """
        Compute heat kernel diffusion response at multiple time scales.

        H(t) = V * diag(exp(-lambda_i * t)) * V^T

        At short t, only immediate neighbors respond (local structure).
        At t ~ 1/lambda_2 (Fiedler), signal crosses the bipartition boundary.
        At large t, signal equilibrates (no information).

        Returns: {t: [PropagationEffect, ...]} for each time scale.
        """
        if time_scales is None:
            time_scales = _DEFAULT_TIME_SCALES

        eigenvalues, eigenvectors = self._get_eigen()

        results = {}
        for t in time_scales:
            # Heat kernel row for anchor
            heat_weights = np.exp(-eigenvalues * t)
            # H(t)[anchor, j] = sum_k V[anchor,k] * exp(-lam_k*t) * V[j,k]
            h_row = (eigenvectors[anchor_idx, :] * heat_weights) @ eigenvectors.T

            # Remove self, normalize
            h_row[anchor_idx] = 0.0
            max_h = np.abs(h_row).max()
            if max_h < 1e-10:
                results[t] = []
                continue

            effects = []
            for j in range(self._n):
                if j == anchor_idx:
                    continue
                mag = abs(float(h_row[j]))
                if mag < 1e-10:
                    continue
                edge_sign = self._get_path_sign(anchor_idx, j)
                effects.append(PropagationEffect(
                    construct=self._constructs[j],
                    magnitude=mag,
                    direction=direction * edge_sign,
                    confidence=mag / max_h,
                    rank=0,
                ))

            effects.sort(key=lambda e: e.magnitude, reverse=True)
            for i, e in enumerate(effects):
                e.rank = i + 1
            results[t] = effects

        return results

    # -- Sign restoration helper -----------------------------------------------

    def _get_path_sign(self, src_idx: int, tgt_idx: int) -> int:
        """
        Get the sign of the path from src to tgt.

        For direct neighbors, use sign(gamma). For non-adjacent nodes,
        use the Dijkstra path sign (product of edge signs along shortest path).
        """
        # Direct edge?
        gamma = self._W[src_idx, tgt_idx]
        if abs(gamma) > 1e-10:
            return 1 if gamma > 0 else -1

        # Dijkstra path sign (cached via WVSOntologyQuery)
        src_key = self._constructs[src_idx]
        tgt_key = self._constructs[tgt_idx]
        try:
            path = self._oq.find_path(src_key, tgt_key)
            if path.path_sign != 0:
                return path.path_sign
        except (ValueError, IndexError):
            pass

        # No path: assume positive (unknown)
        return 1

    # -- Consensus scoring -----------------------------------------------------

    def _build_consensus(
        self,
        bp: list[PropagationEffect],
        ppr: list[PropagationEffect],
        spectral: dict[float, list[PropagationEffect]],
    ) -> list[ConsensusEffect]:
        """
        Build consensus ranking across the three methods.

        For each construct, check if it appears in top-N of each method.
        Agreement score = fraction of available methods ranking it in top-N.
        Final ranking by agreement score, then by mean rank.

        Spectral uses the time scale closest to t* = 1/lambda_2 (Fiedler).
        """
        # Choose characteristic time scale for spectral
        eigenvalues, _ = self._get_eigen()
        lambda_2 = eigenvalues[1] if len(eigenvalues) > 1 else 1.0
        t_star = 1.0 / max(lambda_2, 1e-6)
        # Pick closest available time scale
        spectral_at_tstar = []
        if spectral:
            closest_t = min(spectral.keys(), key=lambda t: abs(t - t_star))
            spectral_at_tstar = spectral[closest_t]

        # Build rank lookups
        def _rank_dict(effects: list[PropagationEffect]) -> dict[str, int]:
            return {e.construct: e.rank for e in effects}

        def _dir_dict(effects: list[PropagationEffect]) -> dict[str, int]:
            return {e.construct: e.direction for e in effects}

        def _mag_dict(effects: list[PropagationEffect]) -> dict[str, float]:
            # Normalize magnitudes to [0, 1]
            if not effects:
                return {}
            max_m = max(e.magnitude for e in effects) or 1.0
            return {e.construct: e.magnitude / max_m for e in effects}

        bp_ranks = _rank_dict(bp)
        ppr_ranks = _rank_dict(ppr)
        spec_ranks = _rank_dict(spectral_at_tstar)

        bp_dirs = _dir_dict(bp)
        ppr_dirs = _dir_dict(ppr)
        spec_dirs = _dir_dict(spectral_at_tstar)

        bp_mags = _mag_dict(bp)
        ppr_mags = _mag_dict(ppr)
        spec_mags = _mag_dict(spectral_at_tstar)

        # All constructs that appear in any method
        all_constructs = set(bp_ranks) | set(ppr_ranks) | set(spec_ranks)

        # Count available methods (BP may be missing for non-W7 contexts)
        n_methods = sum([bool(bp), bool(ppr), bool(spectral_at_tstar)])
        if n_methods == 0:
            return []

        top_n = _CONSENSUS_TOP_N
        consensus = []
        for key in all_constructs:
            bp_r = bp_ranks.get(key)
            ppr_r = ppr_ranks.get(key)
            spec_r = spec_ranks.get(key)

            # Agreement: fraction of methods placing this in top-N
            in_top = 0
            available = 0
            if bp:
                available += 1
                if bp_r is not None and bp_r <= top_n:
                    in_top += 1
            if ppr:
                available += 1
                if ppr_r is not None and ppr_r <= top_n:
                    in_top += 1
            if spectral_at_tstar:
                available += 1
                if spec_r is not None and spec_r <= top_n:
                    in_top += 1

            agreement = in_top / available if available > 0 else 0.0

            # Direction: majority vote
            dirs = [d for d in [bp_dirs.get(key), ppr_dirs.get(key), spec_dirs.get(key)] if d is not None]
            direction = 1 if sum(dirs) >= 0 else -1

            # Mean normalized magnitude
            mags = [m for m in [bp_mags.get(key), ppr_mags.get(key), spec_mags.get(key)] if m is not None]
            mean_mag = sum(mags) / len(mags) if mags else 0.0

            if agreement >= 1 / available if available > 0 else False:
                confidence = "high" if in_top == available else ("medium" if in_top >= 2 else "low")
            else:
                confidence = "low"

            consensus.append(ConsensusEffect(
                construct=key,
                direction=direction,
                bp_rank=bp_r,
                ppr_rank=ppr_r,
                spectral_rank=spec_r,
                agreement_score=agreement,
                confidence=confidence,
                mean_magnitude=mean_mag,
            ))

        # Sort: agreement desc, then mean_magnitude desc, then mean_rank asc
        def _sort_key(e: ConsensusEffect):
            ranks = [r for r in [e.bp_rank, e.ppr_rank, e.spectral_rank] if r is not None]
            mean_rank = sum(ranks) / len(ranks) if ranks else 999
            return (-e.agreement_score, -e.mean_magnitude, mean_rank)

        consensus.sort(key=_sort_key)
        return consensus

    def _compute_method_agreement(
        self,
        bp: list[PropagationEffect],
        ppr: list[PropagationEffect],
        spectral_at_tstar: list[PropagationEffect],
    ) -> dict[str, float]:
        """Pairwise Spearman rank correlation between methods."""
        def _rank_vec(effects: list[PropagationEffect], constructs: list[str]) -> np.ndarray:
            rank_map = {e.construct: e.rank for e in effects}
            return np.array([rank_map.get(c, len(constructs) + 1) for c in constructs])

        # Use constructs present in at least 2 methods
        all_c = sorted(
            set(e.construct for e in bp)
            | set(e.construct for e in ppr)
            | set(e.construct for e in spectral_at_tstar)
        )

        if len(all_c) < 3:
            return {}

        result = {}
        pairs = [("bp_ppr", bp, ppr), ("bp_spectral", bp, spectral_at_tstar),
                 ("ppr_spectral", ppr, spectral_at_tstar)]
        for name, a, b in pairs:
            if not a or not b:
                continue
            va = _rank_vec(a, all_c)
            vb = _rank_vec(b, all_c)
            # Spearman = Pearson on ranks
            corr = np.corrcoef(va, vb)[0, 1]
            result[name] = round(float(corr), 4) if not np.isnan(corr) else 0.0

        return result

    # -- Main entry point ------------------------------------------------------

    def propagate(
        self,
        anchor: str,
        direction: int = 1,
        alpha_ppr: float = 0.2,
        time_scales: Optional[list[float]] = None,
    ) -> PropagationResult:
        """
        Run all three propagation methods from anchor and build consensus.

        Args:
            anchor: Construct key (name|WVS_X format)
            direction: +1 (increasing) or -1 (decreasing)
            alpha_ppr: PPR teleport probability (default 0.2)
            time_scales: Spectral diffusion time points (default: 6 log-spaced)

        Returns:
            PropagationResult with per-method rankings and consensus.
        """
        idx = self._graph.construct_index(anchor)
        if idx < 0:
            raise ValueError(f"Construct not found in context: {anchor}")

        # Run three methods
        bp_effects = self._bp_propagate(idx, direction)
        ppr_effects = self._ppr_propagate(idx, direction, alpha_ppr)
        spectral_effects = self._spectral_propagate(idx, direction, time_scales)

        # Choose spectral at t* for consensus
        eigenvalues, _ = self._get_eigen()
        lambda_2 = eigenvalues[1] if len(eigenvalues) > 1 else 1.0
        t_star = 1.0 / max(lambda_2, 1e-6)
        closest_t = min(spectral_effects.keys(), key=lambda t: abs(t - t_star)) if spectral_effects else 1.0
        spec_at_tstar = spectral_effects.get(closest_t, [])

        # Build consensus
        consensus = self._build_consensus(bp_effects, ppr_effects, spectral_effects)

        # Method agreement
        agreement = self._compute_method_agreement(bp_effects, ppr_effects, spec_at_tstar)

        return PropagationResult(
            anchor=anchor,
            anchor_direction=direction,
            context_str=self._oq.context,
            bp_effects=bp_effects,
            ppr_effects=ppr_effects,
            spectral_effects=spectral_effects,
            consensus=consensus,
            method_agreement=agreement,
            n_present=len(self._graph.present_constructs),
        )
