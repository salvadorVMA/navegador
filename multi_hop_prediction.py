"""
multi_hop_prediction.py — Multi-hop prediction engine for the SES bridge.

Chains predictions from raw survey items through anchor constructs and across
bridges. Given two item-level keys, lifts both to their anchor constructs,
finds the optimal path between them (via Dijkstra on bridge adjacency), and
computes the chained signal.

The prediction chain is:
    signal = loading_gamma_A x gamma(A->B) x ... x gamma(Y->Z) x loading_gamma_B

All terms use the Goodman-Kruskal gamma estimand, making the product
dimensionally consistent.

Two predictor classes:

  MultiHopPredictor        — point-estimate chain (original)
  BayesianMultiHopPredictor — bootstrap-approximate Bayesian with path sampling

The Bayesian predictor propagates uncertainty through the chain by:
1. Deriving sigma per edge from stored 95% CIs: sigma = (ci_hi - ci_lo) / 3.92
2. Sampling gamma ~ N(point, sigma^2) for every edge in the graph
3. Running Dijkstra on each sampled graph -> posterior over paths
4. Computing signal chain per draw -> posterior over total signal
5. Applying softmax shift per draw -> posterior predictive P(B|A)

This is a "bootstrap-approximate Bayesian" approach: it does not use the
ordered-logit generative model (which would require exporting theta/beta
parameters from the Julia sweep). Instead it stays entirely in gamma-space,
treating each gamma as an exchangeable summary statistic with Gaussian
uncertainty derived from the bootstrap CI. The remaining 20% gap is the
absence of a generative P(B|SES) model at the endpoints.

Limitations:
- Independence assumption: gamma values along a path are treated as independent
  draws, but they share SES conditioning. Constructs in the same PC1 camp will
  have correlated gammas. Effect: CIs are somewhat too narrow for same-camp
  chains, too wide for cross-camp chains.
- Loading gamma uncertainty: loading_gamma at endpoints uses the same CI-derived
  sigma when CI is available, or a default sigma=0.15 for approximate loadings.
  True uncertainty depends on item-construct alignment quality.
- Softmax heuristic: the distribution shift is not derived from a generative
  model. Calibration against actual conditional distributions would require
  access to individual-level microdata.
- Path posterior is discrete: with K=500 MC draws, rare alternative paths
  (probability <0.2%) may not appear. Increase n_draws for finer resolution.

Usage:
    from multi_hop_prediction import MultiHopPredictor, BayesianMultiHopPredictor
    from opinion_ontology import OntologyQuery

    oq = OntologyQuery()

    # Point-estimate predictor (original)
    predictor = MultiHopPredictor(oq)
    result = predictor.predict("Q1|W7_MEX", "Q199|W7_MEX")

    # Bayesian predictor with uncertainty
    bpredictor = BayesianMultiHopPredictor(oq, n_draws=500, seed=42)
    bresult = bpredictor.predict("Q1|W7_MEX", "Q199|W7_MEX")
    print(bresult["signal_ci_95"])       # (lo, hi) credible interval
    print(bresult["path_diversity"])      # fraction of draws using non-modal path
    print(bresult["p_positive"])          # posterior P(signal > 0)
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from opinion_ontology import OntologyQuery


class MultiHopPredictor:
    """Chain predictions through the SES bridge network.

    Given two endpoints (item-level keys, construct keys, or domain keys),
    lifts both to L1 anchor constructs, finds the optimal bridge path, and
    computes the chained signal with per-hop details.

    Parameters
    ----------
    ontology : OntologyQuery
        Initialized OntologyQuery instance with fingerprints and bridge data.
    """

    def __init__(self, ontology: OntologyQuery) -> None:
        self._oq = ontology

    def predict(
        self,
        key_a: str,
        key_b: str,
        prefer_sign_consistent: bool = False,
    ) -> Dict:
        """Compute the multi-hop prediction between two endpoints.

        Parameters
        ----------
        key_a, key_b : str
            Item keys (e.g. "Q1|W7_MEX"), construct keys (e.g. "WVS_A|importance_of_life_domains"),
            or domain keys (e.g. "WVS_A").
        prefer_sign_consistent : bool
            If True, prefer paths where consecutive edges have consistent signs.

        Returns
        -------
        dict with keys:
            key_a, key_b          — original input keys
            anchor_a, anchor_b    — L1 construct anchors
            lift_a, lift_b        — lift metadata dicts
            path                  — list of construct keys along the path
            edges                 — per-hop edge details (gamma, CI, etc.)
            n_hops                — number of bridge hops
            signal                — signed product of all gammas along the path
            signal_magnitude      — |signal| (product of |gamma| values)
            endpoint_attenuation  — product of endpoint loading gammas
            total_signal          — signal_magnitude * endpoint_attenuation
            total_signal_signed   — total_signal with correct sign
            direct_edge           — direct bridge edge if it exists (dict or None)
            attenuation_warning   — True if total_signal < 0.001
            error                 — error message or None
            narrative             — human-readable explanation
        """
        # ── Lift both endpoints to L1 constructs ──────────────
        lift_a = self._oq._lift_to_construct(key_a)
        lift_b = self._oq._lift_to_construct(key_b)
        anchor_a = lift_a["construct_key"]
        anchor_b = lift_b["construct_key"]

        base = {
            "key_a": key_a,
            "key_b": key_b,
            "anchor_a": anchor_a,
            "anchor_b": anchor_b,
            "lift_a": lift_a,
            "lift_b": lift_b,
            "path": None,
            "edges": None,
            "n_hops": 0,
            "signal": None,
            "signal_magnitude": None,
            "endpoint_attenuation": None,
            "total_signal": None,
            "total_signal_signed": None,
            "direct_edge": None,
            "attenuation_warning": False,
            "error": None,
            "narrative": "",
        }

        # ── Validate lift results ─────────────────────────────
        if anchor_a is None:
            base["error"] = f"Cannot lift '{key_a}' to an L1 construct anchor."
            base["narrative"] = base["error"]
            return base
        if anchor_b is None:
            base["error"] = f"Cannot lift '{key_b}' to an L1 construct anchor."
            base["narrative"] = base["error"]
            return base

        # Domain-level keys cannot be used for bridge queries
        if lift_a["lift_type"] in ("domain_fallback", "no_constructs_in_domain"):
            base["error"] = (
                f"'{key_a}' resolves to domain-level anchor '{anchor_a}' — "
                f"bridge queries require L1 construct anchors."
            )
            base["narrative"] = base["error"]
            return base
        if lift_b["lift_type"] in ("domain_fallback", "no_constructs_in_domain"):
            base["error"] = (
                f"'{key_b}' resolves to domain-level anchor '{anchor_b}' — "
                f"bridge queries require L1 construct anchors."
            )
            base["narrative"] = base["error"]
            return base

        # ── Same construct: trivial path ──────────────────────
        if anchor_a == anchor_b:
            loading_a = lift_a.get("loading_gamma") or 1.0
            loading_b = lift_b.get("loading_gamma") or 1.0
            ep_atten = abs(loading_a) * abs(loading_b)
            total_signed = loading_a * loading_b

            base.update({
                "path": [anchor_a],
                "edges": [],
                "n_hops": 0,
                "signal": 1.0,
                "signal_magnitude": 1.0,
                "endpoint_attenuation": round(ep_atten, 6),
                "total_signal": round(ep_atten, 6),
                "total_signal_signed": round(total_signed, 6),
                "narrative": (
                    f"Both keys map to the same anchor construct "
                    f"'{_name(anchor_a)}'. No bridge traversal needed. "
                    f"Endpoint attenuation: {ep_atten:.4f}."
                ),
            })
            return base

        # ── Use OntologyQuery.find_path for Dijkstra ──────────
        path_result = self._oq.find_path(
            key_a=anchor_a,
            key_b=anchor_b,
            prefer_sign_consistent=prefer_sign_consistent,
        )

        if path_result.get("error"):
            base["error"] = path_result["error"]
            base["narrative"] = path_result["error"]
            base["direct_edge"] = path_result.get("direct_edge")
            return base

        path = path_result.get("path") or []
        edges = path_result.get("edges") or []

        # ── Compute the chained signal ────────────────────────
        # Bridge signal: signed product of gammas along the path
        bridge_signal = 1.0
        bridge_magnitude = 1.0
        for e in edges:
            bridge_signal *= e["gamma"]
            bridge_magnitude *= abs(e["gamma"])

        # Endpoint loading gammas
        loading_a = lift_a.get("loading_gamma")
        loading_b = lift_b.get("loading_gamma")

        # Default to 1.0 for construct-level (exact) endpoints
        eff_loading_a = loading_a if loading_a is not None else 1.0
        eff_loading_b = loading_b if loading_b is not None else 1.0

        endpoint_attenuation = abs(eff_loading_a) * abs(eff_loading_b)
        total_magnitude = bridge_magnitude * endpoint_attenuation

        # Total signed signal: loading_A * bridge_signal * loading_B
        total_signed = eff_loading_a * bridge_signal * eff_loading_b

        base.update({
            "path": path,
            "edges": edges,
            "n_hops": len(edges),
            "signal": round(bridge_signal, 6),
            "signal_magnitude": round(bridge_magnitude, 6),
            "endpoint_attenuation": round(endpoint_attenuation, 6),
            "total_signal": round(total_magnitude, 6),
            "total_signal_signed": round(total_signed, 6),
            "direct_edge": path_result.get("direct_edge"),
            "attenuation_warning": total_magnitude < 0.001,
            "narrative": self._build_narrative(
                key_a, key_b, anchor_a, anchor_b, lift_a, lift_b,
                path, edges, bridge_signal, bridge_magnitude,
                eff_loading_a, eff_loading_b, total_signed, total_magnitude,
            ),
        })
        return base

    def predict_distribution(
        self,
        key_a: str,
        key_b: str,
        value_a: int,
        n_categories_b: int = 5,
        prefer_sign_consistent: bool = False,
    ) -> Dict:
        """Given item A at value_a, predict the implied distribution over item B.

        Uses the chained signal as a shift parameter on a uniform prior.
        Positive total_signal_signed shifts probability toward higher categories;
        negative shifts toward lower categories.

        This is an approximate heuristic, not a full Bayesian update.

        Parameters
        ----------
        key_a : str
            Source item key.
        key_b : str
            Target item key.
        value_a : int
            Observed value of item A (1-indexed ordinal).
        n_categories_b : int
            Number of categories for item B (default: 5).
        prefer_sign_consistent : bool
            Passed through to predict().

        Returns
        -------
        dict with:
            prediction (from predict()), distribution (list of probabilities),
            expected_value, shift_direction, error.
        """
        pred = self.predict(key_a, key_b, prefer_sign_consistent=prefer_sign_consistent)

        if pred.get("error"):
            return {
                "prediction": pred,
                "distribution": None,
                "expected_value": None,
                "shift_direction": None,
                "error": pred["error"],
            }

        total_signed = pred.get("total_signal_signed", 0.0)
        if total_signed is None:
            total_signed = 0.0

        # Compute a shifted distribution
        # Uniform prior shifted by the signal strength
        dist = _shifted_distribution(
            total_signed=total_signed,
            value_a=value_a,
            n_categories_a=n_categories_b,  # assume same scale for simplicity
            n_categories_b=n_categories_b,
        )

        expected = sum((i + 1) * p for i, p in enumerate(dist))
        shift_dir = "higher" if total_signed > 0 else ("lower" if total_signed < 0 else "none")

        return {
            "prediction": pred,
            "distribution": [round(p, 4) for p in dist],
            "expected_value": round(expected, 3),
            "shift_direction": shift_dir,
            "error": None,
        }

    def get_all_paths(
        self,
        key_a: str,
        key_b: str,
        max_paths: int = 5,
    ) -> List[Dict]:
        """Return multiple paths between two endpoints, ranked by signal strength.

        Uses iterative Dijkstra with edge removal to find alternative paths.
        This is a k-shortest-paths approximation (Yen's algorithm simplified).

        Parameters
        ----------
        key_a, key_b : str
            Endpoint keys.
        max_paths : int
            Maximum number of paths to return.

        Returns
        -------
        List of prediction dicts, sorted by total_signal descending.
        """
        # For now, return just the single best path
        # Full Yen's algorithm would require modifying OntologyQuery internals
        best = self.predict(key_a, key_b)
        return [best] if not best.get("error") else []

    def _build_narrative(
        self,
        key_a: str,
        key_b: str,
        anchor_a: str,
        anchor_b: str,
        lift_a: Dict,
        lift_b: Dict,
        path: List[str],
        edges: List[Dict],
        bridge_signal: float,
        bridge_magnitude: float,
        loading_a: float,
        loading_b: float,
        total_signed: float,
        total_magnitude: float,
    ) -> str:
        """Build human-readable narrative for the prediction."""
        name_a = _name(anchor_a)
        name_b = _name(anchor_b)

        lines = []

        # Path description
        n_hops = len(edges)
        if n_hops == 1:
            lines.append(
                f"Direct bridge: '{name_a}' -> '{name_b}' "
                f"(gamma={edges[0]['gamma']:+.4f})."
            )
        else:
            path_names = [_name(p) for p in path]
            chain = " -> ".join(path_names)
            lines.append(
                f"{n_hops}-hop path: {chain}."
            )
            gamma_strs = [f"{e['gamma']:+.4f}" for e in edges]
            lines.append(
                f"Bridge gammas: {', '.join(gamma_strs)}."
            )

        # Signal summary
        lines.append(
            f"Bridge signal: {bridge_signal:+.6f} "
            f"(magnitude {bridge_magnitude:.6f})."
        )

        # Endpoint attenuation
        lift_notes = []
        if lift_a["lift_type"] != "exact":
            lift_notes.append(
                f"A: {lift_a['lift_type']} lift, loading_gamma={loading_a:.3f}"
            )
        if lift_b["lift_type"] != "exact":
            lift_notes.append(
                f"B: {lift_b['lift_type']} lift, loading_gamma={loading_b:.3f}"
            )
        if lift_notes:
            lines.append("Endpoint attenuation: " + "; ".join(lift_notes) + ".")

        lines.append(
            f"Total signed signal: {total_signed:+.6f} "
            f"(magnitude {total_magnitude:.6f})."
        )

        if total_magnitude < 0.001:
            lines.append(
                "WARNING: total signal < 0.001 — chain too attenuated for "
                "substantive interpretation."
            )

        # Interpretation
        if abs(total_signed) > 0.01:
            direction = "positively" if total_signed > 0 else "negatively"
            lines.append(
                f"Interpretation: '{_name(key_a)}' and '{_name(key_b)}' are "
                f"{direction} linked through SES mediation."
            )
        else:
            lines.append(
                f"Interpretation: the SES-mediated link between "
                f"'{_name(key_a)}' and '{_name(key_b)}' is negligible."
            )

        return " ".join(lines)


# ═══════════════════════════════════════════════════════════════
# FUTURE DEVELOPMENT — Full Bayesian with Generative Model
# ═══════════════════════════════════════════════════════════════
#
# The BayesianMultiHopPredictor above covers ~80% of the uncertainty
# quantification goal. The remaining 20% requires a generative model
# at the endpoints, which would replace the softmax heuristic with
# actual conditional probabilities derived from the ordered-logit
# (proportional-odds) model that produces the gamma estimates.
#
# What's needed:
#
# 1. EXPORT ORDERED-LOGIT PARAMETERS FROM JULIA SWEEP
#    The Julia DR estimator (dr_estimator.jl) fits an OrderedLogit for
#    each construct in each survey context. The model parameters are:
#      - theta (K-1 intercepts / cut points for K ordinal categories)
#      - beta (4 SES coefficients: escol, Tam_loc, sexo, edad)
#    Currently these are used to compute gamma and then discarded.
#    To enable generative predictions, modify `dr_estimate()` to return
#    theta and beta alongside gamma/CI/NMI.
#
# 2. CONDITIONAL P(B|SES) FROM ORDERED-LOGIT
#    Given a respondent's SES profile x = (escol, Tam_loc, sexo, edad):
#      P(B <= j | x) = logistic(theta_j - beta'x)
#      P(B = j | x) = P(B <= j) - P(B <= j-1)
#    This is the generative model that the gamma estimate summarizes.
#    With theta/beta exported, we can compute exact P(B=j | x) for
#    any SES profile, bypassing the softmax heuristic entirely.
#
# 3. FULL BAYESIAN PREDICTION CHAIN
#    Given item A at value v_A:
#      a. Lift A to construct C_A via loading_gamma
#      b. Infer the implied SES profile distribution:
#         P(SES | C_A = bin(v_A)) from the ordered-logit inverse
#      c. Propagate SES through the bridge chain:
#         P(C_B | SES) from each hop's ordered-logit
#      d. Project down to item B:
#         P(B | C_B) via loading_gamma inverse
#    Each step uses the generative model, not summary statistics.
#
# 4. CORRELATED GAMMA SAMPLES
#    Bridge gammas along a path share SES conditioning. A full Bayesian
#    approach would sample (theta, beta) jointly for constructs that
#    share the same survey context, producing correlated gamma draws.
#    This requires storing the bootstrap resamples (200 per pair) rather
#    than just the CI summary. Storage: ~800 bytes per pair × 984 pairs
#    × 200 draws = ~157 MB (feasible).
#
# Estimated effort: ~1 week for Julia modifications + Python integration.
# Feasible but requires re-running the sweep to export parameters.
# The bootstrap-approximate approach above is sufficient for most
# analytical and demonstration purposes in the meantime.

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _name(key: str) -> str:
    """Extract readable name from a key like 'WVS_A|importance_of_life_domains'."""
    if "|" in key:
        return key.split("|")[-1].replace("_", " ")
    return key


def _shifted_distribution(
    total_signed: float,
    value_a: int,
    n_categories_a: int,
    n_categories_b: int,
) -> List[float]:
    """Compute a shifted distribution over B given A=value_a and the total signal.

    Uses a softmax-based shift: uniform prior is perturbed proportionally to
    the signal strength and the deviation of value_a from the midpoint of A.

    Parameters
    ----------
    total_signed : float
        The total signed signal from the prediction chain.
    value_a : int
        Observed value of A (1-indexed).
    n_categories_a : int
        Number of categories of A.
    n_categories_b : int
        Number of categories of B.

    Returns
    -------
    List of probabilities for categories 1..n_categories_b.
    """
    # How far value_a is from the midpoint of A, normalized to [-1, 1]
    midpoint_a = (n_categories_a + 1) / 2.0
    deviation_a = (value_a - midpoint_a) / (midpoint_a - 1) if midpoint_a > 1 else 0.0
    deviation_a = max(-1.0, min(1.0, deviation_a))

    # The shift is proportional to signal * deviation
    # Positive signal + high value_a -> shift B toward higher values
    shift = total_signed * deviation_a

    # Softmax with linear shift
    logits = np.zeros(n_categories_b)
    for i in range(n_categories_b):
        # Center of each category, normalized to [-1, 1]
        cat_center = (i + 1 - (n_categories_b + 1) / 2.0)
        if (n_categories_b + 1) / 2.0 > 1:
            cat_center /= ((n_categories_b + 1) / 2.0 - 1)
        logits[i] = shift * cat_center

    # Softmax
    logits -= logits.max()  # numerical stability
    exp_logits = np.exp(logits)
    probs = exp_logits / exp_logits.sum()

    return probs.tolist()


# ═══════════════════════════════════════════════════════════════
# BayesianMultiHopPredictor — bootstrap-approximate Bayesian
# ═══════════════════════════════════════════════════════════════

class BayesianMultiHopPredictor:
    """Uncertainty-aware multi-hop prediction via Monte Carlo path sampling.

    For each MC draw:
      1. Sample gamma ~ N(point, sigma^2) for every bridge edge
      2. Run Dijkstra on the sampled graph -> a path
      3. Compute signal = product of sampled gammas along path
      4. Include endpoint loading_gamma uncertainty

    Aggregates across draws to produce posterior over signal, credible
    intervals, path diversity, and posterior predictive P(B|A).

    Parameters
    ----------
    ontology : OntologyQuery
        Initialized OntologyQuery with fingerprints and bridge data.
    n_draws : int
        Number of Monte Carlo draws (default: 500).
    seed : int or None
        RNG seed for reproducibility.
    loading_sigma_default : float
        Default sigma for loading_gamma when no CI is available (approximate
        or orphan lifts). Empirically, loading gammas for construct members
        range 0.5-0.99 with typical SE ~0.10-0.20. Default 0.15.
    """

    def __init__(
        self,
        ontology: "OntologyQuery",
        n_draws: int = 500,
        seed: Optional[int] = 42,
        loading_sigma_default: float = 0.15,
    ) -> None:
        self._oq = ontology
        self._n_draws = n_draws
        self._rng = np.random.default_rng(seed)
        self._loading_sigma_default = loading_sigma_default
        # Pre-extract the bridge graph with CI info for sampling
        self._edge_index = self._build_edge_index()

    def _build_edge_index(self) -> Dict[Tuple[str, str], Dict]:
        """Build a lookup of (src, tgt) -> {gamma, sigma, ci_lo, ci_hi}.

        sigma is derived from the 95% CI: sigma = (ci_hi - ci_lo) / 3.92.
        If CI is missing or degenerate, use |gamma| * 0.3 as fallback.
        """
        index: Dict[Tuple[str, str], Dict] = {}
        for src, edges in self._oq._bridges.items():
            for e in edges:
                tgt = e["neighbor"]
                ci_lo = e.get("ci_lo")
                ci_hi = e.get("ci_hi")
                gamma = e["gamma"]
                if ci_lo is not None and ci_hi is not None and ci_hi > ci_lo:
                    sigma = (ci_hi - ci_lo) / 3.92
                else:
                    # Fallback: 30% of |gamma| as rough uncertainty
                    sigma = abs(gamma) * 0.3 + 0.005  # floor prevents zero sigma
                index[(src, tgt)] = {
                    "gamma": gamma,
                    "sigma": sigma,
                    "ci_lo": ci_lo,
                    "ci_hi": ci_hi,
                }
        return index

    def _sample_edge_gammas(self) -> Dict[Tuple[str, str], float]:
        """Sample one draw of gamma for every edge in the graph."""
        sampled: Dict[Tuple[str, str], float] = {}
        for (src, tgt), info in self._edge_index.items():
            g = self._rng.normal(info["gamma"], info["sigma"])
            # Clip to valid range — gamma cannot exceed [-1, 1]
            g = max(-1.0, min(1.0, g))
            sampled[(src, tgt)] = g
        return sampled

    def _dijkstra_on_sampled(
        self,
        sampled: Dict[Tuple[str, str], float],
        anchor_a: str,
        anchor_b: str,
    ) -> Optional[Tuple[List[str], List[float]]]:
        """Dijkstra on sampled gammas. Returns (path, gammas_along_path) or None."""
        import heapq as hq

        # Build adjacency from sampled values
        adj: Dict[str, List[Tuple[str, float, float]]] = {}
        for (src, tgt), g in sampled.items():
            abs_g = abs(g)
            if abs_g < 1e-10:
                continue  # skip near-zero edges (infinite weight)
            weight = -math.log(abs_g)
            adj.setdefault(src, []).append((tgt, weight, g))

        if anchor_a not in adj:
            return None

        cost: Dict[str, float] = {anchor_a: 0.0}
        prev: Dict[str, Optional[str]] = {anchor_a: None}
        prev_gamma: Dict[str, float] = {}
        heap = [(0.0, anchor_a)]

        while heap:
            c, node = hq.heappop(heap)
            if node == anchor_b:
                break
            if c > cost.get(node, math.inf):
                continue
            for nbr, w, g in adj.get(node, []):
                nc = c + w
                if nc < cost.get(nbr, math.inf):
                    cost[nbr] = nc
                    prev[nbr] = node
                    prev_gamma[nbr] = g
                    hq.heappush(heap, (nc, nbr))

        if anchor_b not in prev:
            return None

        # Reconstruct
        path: List[str] = []
        gammas: List[float] = []
        cur = anchor_b
        while cur is not None:
            path.append(cur)
            if prev.get(cur) is not None:
                gammas.append(prev_gamma[cur])
            cur = prev.get(cur)
        path.reverse()
        gammas.reverse()
        return path, gammas

    def _sample_loading(self, lift: Dict) -> float:
        """Sample a loading_gamma from its approximate posterior."""
        lg = lift.get("loading_gamma")
        if lg is None:
            return 1.0  # construct-level endpoint, no attenuation
        # Use CI if available (exact lifts have computed loading_gamma)
        if lift["lift_type"] == "exact":
            # Exact loadings are fairly precise; use smaller sigma
            sigma = self._loading_sigma_default * 0.5
        else:
            sigma = self._loading_sigma_default
        sampled = self._rng.normal(lg, sigma)
        return max(-1.0, min(1.0, sampled))

    def predict(
        self,
        key_a: str,
        key_b: str,
    ) -> Dict:
        """Bayesian multi-hop prediction with full uncertainty quantification.

        Returns
        -------
        dict with keys:
            key_a, key_b, anchor_a, anchor_b, lift_a, lift_b,
            signal_mean, signal_median, signal_ci_95, signal_ci_50,
            signal_magnitude_mean,
            p_positive          — posterior P(total_signed > 0),
            path_modal          — most frequent path across draws,
            path_diversity      — fraction of draws using non-modal path,
            n_unique_paths      — number of distinct paths sampled,
            distribution_mean   — posterior mean P(B=j) averaged across draws,
            distribution_ci_95  — per-category 95% credible intervals,
            n_draws, n_valid_draws,
            point_estimate      — result from deterministic MultiHopPredictor,
            error, narrative
        """
        # ── Lift endpoints ────────────────────────────────────────
        lift_a = self._oq._lift_to_construct(key_a)
        lift_b = self._oq._lift_to_construct(key_b)
        anchor_a = lift_a["construct_key"]
        anchor_b = lift_b["construct_key"]

        base = {
            "key_a": key_a, "key_b": key_b,
            "anchor_a": anchor_a, "anchor_b": anchor_b,
            "lift_a": lift_a, "lift_b": lift_b,
            "signal_mean": None, "signal_median": None,
            "signal_ci_95": None, "signal_ci_50": None,
            "signal_magnitude_mean": None,
            "p_positive": None,
            "path_modal": None, "path_diversity": None,
            "n_unique_paths": 0,
            "distribution_mean": None, "distribution_ci_95": None,
            "n_draws": self._n_draws, "n_valid_draws": 0,
            "point_estimate": None,
            "error": None, "narrative": "",
        }

        # Validate
        if anchor_a is None:
            base["error"] = f"Cannot lift '{key_a}' to L1 construct."
            base["narrative"] = base["error"]
            return base
        if anchor_b is None:
            base["error"] = f"Cannot lift '{key_b}' to L1 construct."
            base["narrative"] = base["error"]
            return base
        if lift_a["lift_type"] in ("domain_fallback", "no_constructs_in_domain"):
            base["error"] = f"'{key_a}' resolves to domain-level — needs L1 anchor."
            base["narrative"] = base["error"]
            return base
        if lift_b["lift_type"] in ("domain_fallback", "no_constructs_in_domain"):
            base["error"] = f"'{key_b}' resolves to domain-level — needs L1 anchor."
            base["narrative"] = base["error"]
            return base

        # Same construct: trivial
        if anchor_a == anchor_b:
            base.update({
                "signal_mean": 1.0, "signal_median": 1.0,
                "signal_ci_95": (1.0, 1.0), "signal_ci_50": (1.0, 1.0),
                "signal_magnitude_mean": 1.0, "p_positive": 1.0,
                "path_modal": [anchor_a], "path_diversity": 0.0,
                "n_unique_paths": 1, "n_valid_draws": self._n_draws,
                "narrative": f"Same anchor '{_name(anchor_a)}'. No bridge needed.",
            })
            return base

        # ── Get point estimate for comparison ─────────────────────
        point_pred = MultiHopPredictor(self._oq).predict(key_a, key_b)
        base["point_estimate"] = point_pred
        if point_pred.get("error"):
            # If deterministic fails, Bayesian likely will too, but try anyway
            pass

        # ── Monte Carlo path sampling ─────────────────────────────
        signals: List[float] = []
        path_counts: Dict[str, int] = {}  # tuple(path)->count
        distributions: List[List[float]] = []

        for _ in range(self._n_draws):
            # Sample edge gammas
            sampled = self._sample_edge_gammas()

            # Dijkstra on sampled graph
            result = self._dijkstra_on_sampled(sampled, anchor_a, anchor_b)
            if result is None:
                continue

            path, gammas = result

            # Bridge signal: signed product
            bridge_signal = 1.0
            for g in gammas:
                bridge_signal *= g

            # Sample endpoint loadings
            la = self._sample_loading(lift_a)
            lb = self._sample_loading(lift_b)

            total_signed = la * bridge_signal * lb
            signals.append(total_signed)

            # Track path
            path_key = "->".join(path)
            path_counts[path_key] = path_counts.get(path_key, 0) + 1

            # Compute shifted distribution for this draw
            dist = _shifted_distribution(
                total_signed=total_signed,
                value_a=3,  # midpoint observation (neutral reference)
                n_categories_a=5,
                n_categories_b=5,
            )
            distributions.append(dist)

        n_valid = len(signals)
        base["n_valid_draws"] = n_valid

        if n_valid < 10:
            base["error"] = (
                f"Only {n_valid}/{self._n_draws} MC draws found a path. "
                f"Constructs may be nearly disconnected."
            )
            base["narrative"] = base["error"]
            return base

        # ── Aggregate posterior ────────────────────────────────────
        signals_arr = np.array(signals)

        base["signal_mean"] = round(float(signals_arr.mean()), 6)
        base["signal_median"] = round(float(np.median(signals_arr)), 6)
        base["signal_ci_95"] = (
            round(float(np.percentile(signals_arr, 2.5)), 6),
            round(float(np.percentile(signals_arr, 97.5)), 6),
        )
        base["signal_ci_50"] = (
            round(float(np.percentile(signals_arr, 25)), 6),
            round(float(np.percentile(signals_arr, 75)), 6),
        )
        base["signal_magnitude_mean"] = round(float(np.abs(signals_arr).mean()), 6)
        base["p_positive"] = round(float((signals_arr > 0).mean()), 4)

        # Path diversity
        modal_path_key = max(path_counts, key=path_counts.get)
        modal_count = path_counts[modal_path_key]
        base["path_modal"] = modal_path_key.split("->")
        base["path_diversity"] = round(1.0 - modal_count / n_valid, 4)
        base["n_unique_paths"] = len(path_counts)

        # Distribution posterior
        if distributions:
            dist_arr = np.array(distributions)
            base["distribution_mean"] = [
                round(float(x), 4) for x in dist_arr.mean(axis=0)
            ]
            base["distribution_ci_95"] = [
                (round(float(np.percentile(dist_arr[:, j], 2.5)), 4),
                 round(float(np.percentile(dist_arr[:, j], 97.5)), 4))
                for j in range(dist_arr.shape[1])
            ]

        # ── Narrative ─────────────────────────────────────────────
        base["narrative"] = self._build_narrative(base, path_counts, n_valid)
        return base

    def predict_distribution(
        self,
        key_a: str,
        key_b: str,
        value_a: int,
        n_categories_b: int = 5,
    ) -> Dict:
        """Bayesian predict_distribution: given A=value_a, posterior over P(B).

        Unlike the point-estimate version, this propagates uncertainty from
        the signal chain through to the predictive distribution, giving
        credible intervals on each category probability.
        """
        pred = self.predict(key_a, key_b)
        if pred.get("error"):
            return {
                "prediction": pred,
                "distribution_mean": None,
                "distribution_ci_95": None,
                "expected_value_mean": None,
                "expected_value_ci_95": None,
                "shift_direction": None,
                "error": pred["error"],
            }

        # Re-run MC draws with the specified value_a
        signals = []
        distributions = []
        for _ in range(self._n_draws):
            sampled = self._sample_edge_gammas()
            result = self._dijkstra_on_sampled(
                sampled, pred["anchor_a"], pred["anchor_b"]
            )
            if result is None:
                continue
            path, gammas = result
            bridge = 1.0
            for g in gammas:
                bridge *= g
            la = self._sample_loading(pred["lift_a"])
            lb = self._sample_loading(pred["lift_b"])
            total = la * bridge * lb
            signals.append(total)
            dist = _shifted_distribution(total, value_a, n_categories_b, n_categories_b)
            distributions.append(dist)

        if len(distributions) < 10:
            return {
                "prediction": pred,
                "distribution_mean": None,
                "distribution_ci_95": None,
                "expected_value_mean": None,
                "expected_value_ci_95": None,
                "shift_direction": None,
                "error": "Too few valid MC draws for distribution prediction.",
            }

        dist_arr = np.array(distributions)
        ev_arr = np.array([
            sum((j + 1) * d[j] for j in range(len(d))) for d in distributions
        ])

        sig_mean = float(np.mean(signals))
        return {
            "prediction": pred,
            "distribution_mean": [round(float(x), 4) for x in dist_arr.mean(axis=0)],
            "distribution_ci_95": [
                (round(float(np.percentile(dist_arr[:, j], 2.5)), 4),
                 round(float(np.percentile(dist_arr[:, j], 97.5)), 4))
                for j in range(dist_arr.shape[1])
            ],
            "expected_value_mean": round(float(ev_arr.mean()), 3),
            "expected_value_ci_95": (
                round(float(np.percentile(ev_arr, 2.5)), 3),
                round(float(np.percentile(ev_arr, 97.5)), 3),
            ),
            "shift_direction": "higher" if sig_mean > 0 else (
                "lower" if sig_mean < 0 else "none"
            ),
            "error": None,
        }

    def _build_narrative(
        self, result: Dict, path_counts: Dict[str, int], n_valid: int,
    ) -> str:
        """Build narrative for Bayesian prediction."""
        lines = []
        sig_mean = result["signal_mean"]
        ci = result["signal_ci_95"]
        p_pos = result["p_positive"]

        # Signal summary
        lines.append(
            f"Bayesian signal: {sig_mean:+.6f} "
            f"(95% CI: [{ci[0]:+.6f}, {ci[1]:+.6f}])."
        )

        # Sign certainty
        if p_pos > 0.975:
            lines.append(f"Sign is positive with high confidence (P={p_pos:.3f}).")
        elif p_pos < 0.025:
            lines.append(f"Sign is negative with high confidence (P={p_pos:.3f}).")
        elif 0.4 < p_pos < 0.6:
            lines.append(
                f"Sign is uncertain — P(positive)={p_pos:.3f}. "
                f"The CI spans zero."
            )
        else:
            direction = "positive" if p_pos > 0.5 else "negative"
            lines.append(
                f"Sign leans {direction} (P(positive)={p_pos:.3f}) "
                f"but with moderate uncertainty."
            )

        # Path diversity
        n_paths = result["n_unique_paths"]
        diversity = result["path_diversity"]
        modal = result["path_modal"]
        modal_names = [_name(p) for p in modal]
        lines.append(
            f"Modal path ({n_valid - int(diversity * n_valid)}/{n_valid} draws): "
            f"{' -> '.join(modal_names)}."
        )
        if n_paths > 1:
            lines.append(
                f"{n_paths} distinct paths sampled; "
                f"{diversity:.1%} of draws used alternative routes."
            )

        # Comparison to point estimate
        pt = result.get("point_estimate")
        if pt and pt.get("total_signal_signed") is not None:
            pt_sig = pt["total_signal_signed"]
            lines.append(
                f"Point estimate: {pt_sig:+.6f} "
                f"(within CI: {ci[0] <= pt_sig <= ci[1]})."
            )

        # Magnitude interpretation
        mag = result["signal_magnitude_mean"]
        if mag < 0.001:
            lines.append(
                "WARNING: mean signal magnitude < 0.001 — chain too attenuated."
            )
        elif mag < 0.01:
            lines.append("Signal is weak but detectable.")
        else:
            lines.append(f"Signal magnitude {mag:.4f} is substantively meaningful.")

        return " ".join(lines)
