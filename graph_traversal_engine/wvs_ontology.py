"""
WVSOntologyQuery -- context-aware structure layer for the Graph Traversal Engine.

Provides the same query surface as opinion_ontology.OntologyQuery but indexed
by (country, wave) context. Every method operates on a specific country's
graph: fingerprints, bipartitions, edges, and paths are all context-specific.

Key differences from los_mex OntologyQuery:
  - No item-level lifting (WVS constructs are direct; no cross-survey boundaries)
  - Every query is context-bound (country, wave)
  - Bipartition, fingerprints, and paths differ per country
  - Cross-country comparison methods added
  - Construct-set intersection for cross-wave comparisons
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Optional

import numpy as np

from graph_traversal_engine.context import (
    CampAssignment,
    ContextGraph,
    Fingerprint,
    GraphFamily,
)


# -- Helper: SES dimension labels ----------------------------------------------

_SES_DIMS = ["escol", "Tam_loc", "sexo", "edad"]
_SES_LABELS = {
    "escol": "education",
    "Tam_loc": "urbanization",
    "sexo": "gender",
    "edad": "age/cohort",
}


def _shared_driver(fp_a: Fingerprint, fp_b: Fingerprint) -> Optional[str]:
    """
    Identify the SES dimension that most strongly co-drives two constructs.

    Returns the dimension with max |rho_a * rho_b| -- the dimension where both
    constructs are most jointly stratified.
    """
    va, vb = fp_a.to_vec(), fp_b.to_vec()
    products = np.abs(va * vb)
    if products.max() < 1e-10:
        return None
    return _SES_DIMS[int(np.argmax(products))]


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# -- Result containers ---------------------------------------------------------

@dataclass
class ConstructProfile:
    """Full profile of a construct in a specific context."""
    key: str
    context_str: str
    fingerprint: Optional[Fingerprint]
    camp: Optional[CampAssignment]
    degree: int                     # Number of significant edges
    hub_rank: Optional[int]         # PPR hub ranking (1-based)
    mediator_rank: Optional[int]    # Floyd-Warshall mediator ranking
    ses_summary: dict[str, float]   # {dim: rho} for all 4 dims


@dataclass
class EdgeInfo:
    """Information about one edge in a path or neighborhood."""
    source: str
    target: str
    gamma: float
    ci_width: Optional[float]
    dominant_dim: Optional[str]
    fingerprint_cos: float


@dataclass
class PathResult:
    """Result of Dijkstra path finding between two constructs."""
    source: str
    target: str
    context_str: str
    path: list[str]               # Ordered construct keys
    edges: list[EdgeInfo]         # Per-hop edge data
    total_cost: float             # Sum of -log(|gamma|) along path
    signal_chain: float           # Product of |gamma| along path
    direct_edge: Optional[float]  # gamma if direct edge exists
    attenuation_warning: bool     # signal_chain < 0.001
    path_sign: int                # Product of sign(gamma) along path


# -- Main Class ----------------------------------------------------------------

class WVSOntologyQuery:
    """
    Context-aware query interface over the WVS construct network.

    Instantiate with a country code (and optionally wave) to query that
    country's specific graph structure. All results reflect the local
    SES geometry of the specified context.

    Usage:
        oq = WVSOntologyQuery(family, country="MEX", wave=7)
        oq.get_profile("gender_role_traditionalism|WVS_D")
        oq.get_neighbors("institutional_trust|WVS_E", min_abs_gamma=0.02)
        oq.find_path("institutional_trust|WVS_E", "science_skepticism|WVS_I")
    """

    def __init__(
        self,
        family: GraphFamily,
        country: str,
        wave: int = 7,
    ) -> None:
        self._family = family
        self._country = country
        self._wave = wave

        graph = family.get(country, wave)
        if graph is None:
            raise ValueError(
                f"No context graph for ({country}, W{wave}). "
                f"Available: {family.countries(wave)[:10]}..."
            )
        self._graph: ContextGraph = graph
        self._constructs = graph.constructs
        self._n = len(self._constructs)

        # Pre-compute fingerprint vector matrix for similarity queries
        self._fp_vecs: dict[str, np.ndarray] = {}
        for key in self._constructs:
            fp = graph.fingerprints.get(key)
            if fp:
                v = fp.to_unit_vec()
                if v is not None:
                    self._fp_vecs[key] = v

    @property
    def context(self) -> str:
        return str(self._graph.context)

    @property
    def graph(self) -> ContextGraph:
        return self._graph

    # -- Profile Queries -------------------------------------------------------

    def get_profile(self, key: str) -> ConstructProfile:
        """
        Full profile of a construct in this context: fingerprint, camp,
        degree, hub rank, and SES summary.
        """
        fp = self._graph.fingerprints.get(key)
        camp = self._graph.camps.get(key)
        neighbors = self._graph.get_significant_neighbors(key)
        degree = len(neighbors)

        # Hub ranking from PPR
        hub_rank = None
        if self._graph.ppr_hub_scores:
            sorted_hubs = sorted(
                self._graph.ppr_hub_scores.items(),
                key=lambda x: x[1], reverse=True
            )
            for rank, (k, _) in enumerate(sorted_hubs, 1):
                if k == key:
                    hub_rank = rank
                    break

        ses_summary = {}
        if fp:
            ses_summary = {d: getattr(fp, f"rho_{d}") for d in _SES_DIMS}

        return ConstructProfile(
            key=key,
            context_str=self.context,
            fingerprint=fp,
            camp=camp,
            degree=degree,
            hub_rank=hub_rank,
            mediator_rank=None,
            ses_summary=ses_summary,
        )

    # -- Similarity Queries ----------------------------------------------------

    def get_similar(
        self, key: str, n: int = 10
    ) -> list[tuple[str, float, Optional[str]]]:
        """
        Find constructs with similar SES fingerprints in this context.

        Returns list of (construct_key, cosine_similarity, shared_driver).
        """
        if key not in self._fp_vecs:
            return []

        query_vec = self._fp_vecs[key]
        results = []
        for other_key, other_vec in self._fp_vecs.items():
            if other_key == key:
                continue
            sim = float(np.dot(query_vec, other_vec))
            fp_other = self._graph.fingerprints.get(other_key)
            fp_self = self._graph.fingerprints.get(key)
            driver = _shared_driver(fp_self, fp_other) if fp_self and fp_other else None
            results.append((other_key, sim, driver))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n]

    # -- Neighbor / Edge Queries -----------------------------------------------

    def get_neighbors(
        self,
        key: str,
        min_abs_gamma: float = 0.0,
        top_n: Optional[int] = None,
    ) -> list[EdgeInfo]:
        """Get significant neighbors with edge metadata, sorted by |gamma|."""
        raw = self._graph.get_significant_neighbors(key, min_abs_gamma)
        if top_n:
            raw = raw[:top_n]

        fp_source = self._graph.fingerprints.get(key)
        edges = []
        for neighbor_key, gamma in raw:
            fp_target = self._graph.fingerprints.get(neighbor_key)
            driver = None
            fp_cos = 0.0
            if fp_source and fp_target:
                driver = _shared_driver(fp_source, fp_target)
                fp_cos = _cosine_sim(fp_source.to_vec(), fp_target.to_vec())

            edges.append(EdgeInfo(
                source=key,
                target=neighbor_key,
                gamma=gamma,
                ci_width=None,
                dominant_dim=driver,
                fingerprint_cos=fp_cos,
            ))
        return edges

    def get_neighborhood(
        self,
        key: str,
        min_abs_gamma: float = 0.0,
        top_n: Optional[int] = None,
    ) -> dict:
        """Rich neighborhood summary: neighbors + domain distribution + camp split."""
        edges = self.get_neighbors(key, min_abs_gamma, top_n)
        if not edges:
            return {
                "key": key,
                "context": self.context,
                "neighbors": [],
                "summary": {"n_neighbors": 0},
            }

        domain_counts: dict[str, int] = {}
        n_positive = n_negative = 0
        for e in edges:
            domain = e.target.split("|")[-1] if "|" in e.target else "?"
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            if e.gamma > 0:
                n_positive += 1
            else:
                n_negative += 1

        strongest = max(edges, key=lambda e: abs(e.gamma))

        return {
            "key": key,
            "context": self.context,
            "neighbors": [
                {
                    "key": e.target,
                    "gamma": e.gamma,
                    "dominant_dim": e.dominant_dim,
                    "fingerprint_cos": e.fingerprint_cos,
                }
                for e in edges
            ],
            "summary": {
                "n_neighbors": len(edges),
                "n_positive": n_positive,
                "n_negative": n_negative,
                "domain_distribution": domain_counts,
                "strongest_edge": {
                    "key": strongest.target,
                    "gamma": strongest.gamma,
                    "dominant_dim": strongest.dominant_dim,
                },
            },
        }

    # -- Camp Queries ----------------------------------------------------------

    def get_camp(self, key: str) -> Optional[CampAssignment]:
        """Return camp assignment for a construct in this context."""
        return self._graph.camps.get(key)

    def get_camp_members(self, camp_id: int) -> list[str]:
        """Return all constructs in a given camp (+1 or -1)."""
        return [k for k, c in self._graph.camps.items() if c.camp_id == camp_id]

    def get_frustrated_nodes(
        self, min_frustrated_ratio: float = 0.10
    ) -> list[tuple[str, CampAssignment]]:
        """Return constructs at the bipartition boundary."""
        return [
            (k, c) for k, c in self._graph.camps.items()
            if c.frustrated_ratio >= min_frustrated_ratio
        ]

    # -- Path Finding ----------------------------------------------------------

    def find_path(self, key_a: str, key_b: str) -> PathResult:
        """
        Find strongest SES-mediated path between two constructs via Dijkstra.

        Edge weight = -log(|gamma|). Minimizing total weight = maximizing the
        product of |gamma| along the path (strongest SES-mediated chain).
        """
        W = self._graph.weight_matrix
        idx_a = self._graph.construct_index(key_a)
        idx_b = self._graph.construct_index(key_b)

        if idx_a < 0:
            raise ValueError(f"Construct not found: {key_a}")
        if idx_b < 0:
            raise ValueError(f"Construct not found: {key_b}")

        n = self._n
        dist = np.full(n, np.inf)
        prev = np.full(n, -1, dtype=int)
        dist[idx_a] = 0.0
        visited = set()
        pq = [(0.0, idx_a)]

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            if u == idx_b:
                break

            for v in range(n):
                if v == u or v in visited:
                    continue
                gamma = W[u, v]
                if np.isnan(gamma) or abs(gamma) < 1e-10:
                    continue
                edge_cost = -np.log(abs(gamma))
                new_dist = dist[u] + edge_cost
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        if dist[idx_b] == np.inf:
            return PathResult(
                source=key_a, target=key_b, context_str=self.context,
                path=[], edges=[], total_cost=np.inf, signal_chain=0.0,
                direct_edge=self._graph.get_edge(key_a, key_b),
                attenuation_warning=True, path_sign=0,
            )

        path_indices = []
        current = idx_b
        while current != -1:
            path_indices.append(current)
            current = prev[current]
        path_indices.reverse()

        path_keys = [self._constructs[i] for i in path_indices]

        edges = []
        signal_chain = 1.0
        path_sign = 1
        for hop in range(len(path_indices) - 1):
            u, v = path_indices[hop], path_indices[hop + 1]
            gamma = float(W[u, v])
            signal_chain *= abs(gamma)
            path_sign *= 1 if gamma > 0 else -1

            key_u = self._constructs[u]
            key_v = self._constructs[v]
            fp_u = self._graph.fingerprints.get(key_u)
            fp_v = self._graph.fingerprints.get(key_v)
            driver = _shared_driver(fp_u, fp_v) if fp_u and fp_v else None
            fp_cos = _cosine_sim(fp_u.to_vec(), fp_v.to_vec()) if fp_u and fp_v else 0.0

            edges.append(EdgeInfo(
                source=key_u, target=key_v,
                gamma=gamma, ci_width=None,
                dominant_dim=driver, fingerprint_cos=fp_cos,
            ))

        return PathResult(
            source=key_a, target=key_b, context_str=self.context,
            path=path_keys, edges=edges,
            total_cost=float(dist[idx_b]),
            signal_chain=signal_chain,
            direct_edge=self._graph.get_edge(key_a, key_b),
            attenuation_warning=signal_chain < 0.001,
            path_sign=path_sign,
        )

    # -- Cross-Context Comparison (construct-set intersection aware) -----------

    def compare_with(
        self, other_country: str, key: str, other_wave: Optional[int] = None,
    ) -> dict:
        """
        Compare a construct's profile across two contexts.

        When comparing across waves (different construct sets), restricts
        neighbor analysis to the shared construct intersection.
        """
        wave = other_wave if other_wave is not None else self._wave
        other_graph = self._family.get(other_country, wave)
        if other_graph is None:
            return {"error": f"No graph for {other_country} W{wave}"}

        fp_self = self._graph.fingerprints.get(key)
        fp_other = other_graph.fingerprints.get(key)

        camp_self = self._graph.camps.get(key)
        camp_other = other_graph.camps.get(key)

        fp_cos = 0.0
        if fp_self and fp_other:
            fp_cos = _cosine_sim(fp_self.to_vec(), fp_other.to_vec())

        # Restrict to shared constructs when comparing across waves
        present_self = set(self._graph.present_constructs)
        present_other = set(other_graph.present_constructs)
        shared_universe = present_self & present_other

        neighbors_self = {
            k for k, g in self._graph.get_significant_neighbors(key)
            if k in shared_universe
        }
        neighbors_other = {
            k for k, g in other_graph.get_significant_neighbors(key)
            if k in shared_universe
        }
        shared = neighbors_self & neighbors_other
        union = neighbors_self | neighbors_other
        jaccard = len(shared) / len(union) if union else 0.0

        sign_agree = 0
        for nk in shared:
            g_self = self._graph.get_edge(key, nk)
            g_other = other_graph.get_edge(key, nk)
            if g_self is not None and g_other is not None:
                if np.sign(g_self) == np.sign(g_other):
                    sign_agree += 1
        sign_agreement = sign_agree / len(shared) if shared else 0.0

        return {
            "construct": key,
            "context_a": self.context,
            "context_b": str(other_graph.context),
            "fingerprint_cosine": round(fp_cos, 4),
            "camp_a": camp_self.camp_name if camp_self else None,
            "camp_b": camp_other.camp_name if camp_other else None,
            "camp_agreement": (
                camp_self is not None and camp_other is not None
                and camp_self.camp_id == camp_other.camp_id
            ),
            "n_shared_constructs": len(shared_universe),
            "n_neighbors_a": len(neighbors_self),
            "n_neighbors_b": len(neighbors_other),
            "n_shared_neighbors": len(shared),
            "neighbor_jaccard": round(jaccard, 4),
            "sign_agreement": round(sign_agreement, 4),
        }

    def explain_pair(self, key_a: str, key_b: str) -> dict:
        """
        Explain the relationship between two constructs in this context.

        Combines fingerprint geometry, direct edge, path, and camp membership.
        """
        fp_a = self._graph.fingerprints.get(key_a)
        fp_b = self._graph.fingerprints.get(key_b)

        fp_cos = 0.0
        driver = None
        if fp_a and fp_b:
            fp_cos = _cosine_sim(fp_a.to_vec(), fp_b.to_vec())
            driver = _shared_driver(fp_a, fp_b)

        direct_gamma = self._graph.get_edge(key_a, key_b)

        camp_a = self._graph.camps.get(key_a)
        camp_b = self._graph.camps.get(key_b)
        same_camp = (camp_a and camp_b and camp_a.camp_id == camp_b.camp_id)

        expected_sign = None
        if fp_a and fp_b:
            dot = float(np.dot(fp_a.to_vec(), fp_b.to_vec()))
            expected_sign = 1 if dot > 0 else (-1 if dot < 0 else 0)

        try:
            path_result = self.find_path(key_a, key_b)
        except ValueError:
            path_result = None

        return {
            "key_a": key_a,
            "key_b": key_b,
            "context": self.context,
            "fingerprint_cosine": round(fp_cos, 4),
            "shared_driver": _SES_LABELS.get(driver, driver) if driver else None,
            "direct_gamma": direct_gamma,
            "expected_sign": expected_sign,
            "sign_consistent": (
                direct_gamma is not None and expected_sign is not None
                and np.sign(direct_gamma) == expected_sign
            ),
            "same_camp": same_camp,
            "camp_a": camp_a.camp_name if camp_a else None,
            "camp_b": camp_b.camp_name if camp_b else None,
            "path_length": len(path_result.path) - 1 if path_result and path_result.path else None,
            "signal_chain": path_result.signal_chain if path_result else None,
            "path_sign": path_result.path_sign if path_result else None,
        }
