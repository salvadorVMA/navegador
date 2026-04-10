"""
opinion_ontology.py — Query layer over the SES fingerprint ontology.

Provides three operations for the agent:

  get_profile(key)            → fingerprint + structured narrative
  get_similar(key, n)         → top-n constructs by fingerprint cosine similarity
  explain_pair(key_a, key_b)  → why these two topics co-vary (or don't)

Lookup hierarchy:
  exact construct key (L1) → nearest item key (L0) → domain key (L2)

All 4 SES dimensions have equal standing:
  escol (education), Tam_loc (urban/rural), sexo (gender), edad (age/cohort)
  None is a "demographic control" subordinate to the others.

Usage:
    from opinion_ontology import OntologyQuery
    oq = OntologyQuery()
    print(oq.get_profile("HAB|structural_housing_quality"))
    print(oq.explain_pair("HAB|structural_housing_quality", "REL|personal_religiosity"))
    print(oq.get_similar("CIE|household_science_cultural_capital", n=5))
"""
from __future__ import annotations

import heapq
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent

_FP_PATH = ROOT / "data" / "results" / "ses_fingerprints.json"
_KG_PATH = ROOT / "data" / "results" / "kg_ontology_v2.json"

_ALL_DIMS = ("escol", "Tam_loc", "sexo", "edad")  # all 4 SES dims, equal standing

_DIM_LABELS = {
    "escol":   "education level",
    "Tam_loc": "urban/rural locality",
    "sexo":    "gender",
    "edad":    "age/cohort",
}
_DIM_DIR = {
    "escol":   ("less educated", "more educated"),
    "Tam_loc": ("rural", "urban"),
    "sexo":    ("female-skewed", "male-skewed"),
    "edad":    ("younger", "older"),
}


class OntologyQuery:
    """Query interface over ses_fingerprints.json and kg_ontology_v2.json."""

    def __init__(
        self,
        fp_path: Path = _FP_PATH,
        kg_path: Path = _KG_PATH,
        dataset: str = "los_mex",
        wave: Optional[int] = None,
        country: Optional[str] = None,
    ) -> None:
        # If wave+country specified for WVS, use per-country KG
        if wave is not None and dataset == "wvs":
            _results = ROOT / "data" / "results"
            if country is not None:
                fp_path = _results / "wvs_kg" / f"W{wave}" / f"{country}_fp.json"
                kg_path = _results / "wvs_kg" / f"W{wave}" / f"{country}_kg.json"
            else:
                # Aggregate per-wave (legacy, country-median)
                fp_path = _results / f"wvs_ses_fingerprints_v2_w{wave}.json"
                kg_path = _results / f"wvs_kg_ontology_w{wave}.json"
        fp_path = Path(fp_path) if not isinstance(fp_path, Path) else fp_path
        kg_path = Path(kg_path) if not isinstance(kg_path, Path) else kg_path
        self._dataset = dataset
        with open(fp_path) as f:
            raw = json.load(f)
        self._constructs: Dict[str, Dict] = raw.get("constructs", {})
        self._items: Dict[str, Dict]      = raw.get("items", {})
        self._domains: Dict[str, Dict]    = raw.get("domains", {})

        # Pre-compute construct vectors for similarity search
        self._vec_keys: List[str] = list(self._constructs.keys())
        self._vec_matrix = self._build_matrix(self._constructs, self._vec_keys)

        # KG relationships index: construct_id → list of {to, type, evidence}
        self._kg_rels: Dict[str, List[Dict]] = {}
        # Bridge adjacency index: construct_id → list of bridge edge dicts (bidirectional)
        self._bridges: Dict[str, List[Dict]] = {}
        if kg_path.exists():
            with open(kg_path) as f:
                kg = json.load(f)
            for rel in kg.get("relationships", []):
                src = rel.get("from", "")
                tgt = rel.get("to", "")
                # Convert DOMAIN__name → DOMAIN|name for lookup
                src_key = src.replace("__", "|", 1)
                tgt_key = tgt.replace("__", "|", 1)
                self._kg_rels.setdefault(src_key, []).append(
                    {"to": tgt_key, "type": rel.get("type"), "evidence": rel.get("evidence")}
                )
                self._kg_rels.setdefault(tgt_key, []).append(
                    {"to": src_key, "type": rel.get("type"), "evidence": rel.get("evidence")}
                )
            for edge in kg.get("bridges", []):
                src = edge["from"]
                tgt = edge["to"]
                fwd = {**edge, "neighbor": tgt}
                rev = {**edge, "neighbor": src}
                self._bridges.setdefault(src, []).append(fwd)
                self._bridges.setdefault(tgt, []).append(rev)

        # Bipartition: signed Laplacian Fiedler vector → camp assignments
        self._camp: Dict[str, int] = {}            # +1 = cosmopolitan, -1 = tradition
        self._camp_confidence: Dict[str, float] = {}  # |fiedler_i| / max, 0–1
        self._frustrated_ratio: Dict[str, float] = {}  # fraction of triangles frustrated
        self._n_triangles: Dict[str, int] = {}         # total triangles per node
        self._empty_domains: set = set()               # domains with items but no constructs
        self._compute_empty_domains()
        self._compute_bipartition()

    # ─────────────────────────────────────────────────────────
    # Bipartition — signed Laplacian Fiedler decomposition
    # ─────────────────────────────────────────────────────────

    def _compute_empty_domains(self) -> None:
        """Identify survey domains that have items but no L1 constructs.

        Domains such as JUE and CON contain items in the fingerprint store
        but were never assigned constructs during the construct-building phase.
        Items from these domains cannot be lifted to a bridge-capable anchor.
        """
        construct_domains = {k.split("|")[0] for k in self._constructs}
        item_domains = {
            v.get("domain", k.split("|")[0] if "|" in k else "")
            for k, v in self._items.items()
        }
        all_referenced = construct_domains | item_domains | set(self._domains.keys())
        self._empty_domains = all_referenced - construct_domains

    def _compute_bipartition(self) -> None:
        """Assign each bridge-connected construct to a camp via the signed Laplacian.

        Computes the Fiedler vector of the balanced Laplacian
            L_s = D_|A| - A_s
        where A_s[i,j] = γ (signed, weighted) and D_|A|[i,i] = Σ_j |γ_ij|.

        The Fiedler vector (second-smallest eigenvector of L_s) bipartitions the
        signed graph: sign(fiedler_i) = camp assignment.  The vector is oriented
        so that camp +1 contains constructs with positive rho_escol (cosmopolitan:
        elevated by education and urbanisation) and camp -1 contains constructs
        with positive rho_edad / rho_Tam_loc (tradition: elevated by rural
        residence and older age).

        Confidence = |fiedler_i| / max|fiedler|: distance from the bipartition
        boundary.  Because this graph has near-zero modularity (Q=0.089), most
        nodes sit close to the boundary — low confidence is the expected, correct
        outcome, not a bug.

        Isolated nodes (no bridge edges) receive a fingerprint-based fallback:
        camp = sign(rho_escol), confidence = 0.0.

        Also calls _compute_frustrated_ratio() to populate triangle statistics.
        """
        connected = sorted(k for k in self._constructs if k in self._bridges)

        if not connected:
            # Fingerprint-only fallback for all constructs
            for k, fp in self._constructs.items():
                self._camp[k] = 1 if fp.get("rho_escol", 0.0) >= 0 else -1
                self._camp_confidence[k] = 0.0
            self._compute_frustrated_ratio({})
            return

        idx = {k: i for i, k in enumerate(connected)}
        n = len(connected)

        # Signed weighted adjacency (undirected — store both directions)
        A = np.zeros((n, n), dtype=float)
        for src in connected:
            i = idx[src]
            for e in self._bridges.get(src, []):
                nbr = e["neighbor"]
                if nbr in idx:
                    A[i, idx[nbr]] = e["gamma"]

        # Signed Laplacian
        L_s = np.diag(np.abs(A).sum(axis=1)) - A

        eigenvalues, eigenvectors = np.linalg.eigh(L_s)
        fiedler = eigenvectors[:, 1].copy()

        # Orient: median rho_escol of positive-fiedler nodes should be higher
        pos_mask = fiedler > 0
        if pos_mask.any() and (~pos_mask).any():
            escol_pos = np.median(
                [self._constructs[connected[i]].get("rho_escol", 0.0)
                 for i in range(n) if pos_mask[i]]
            )
            escol_neg = np.median(
                [self._constructs[connected[i]].get("rho_escol", 0.0)
                 for i in range(n) if not pos_mask[i]]
            )
            if escol_neg > escol_pos:
                fiedler = -fiedler

        fiedler_max = float(np.max(np.abs(fiedler))) or 1.0

        for i, node in enumerate(connected):
            self._camp[node] = 1 if fiedler[i] >= 0 else -1
            self._camp_confidence[node] = float(abs(fiedler[i]) / fiedler_max)

        # Isolated constructs: fingerprint-based fallback
        for k, fp in self._constructs.items():
            if k not in self._camp:
                self._camp[k] = 1 if fp.get("rho_escol", 0.0) >= 0 else -1
                self._camp_confidence[k] = 0.0

        self._compute_frustrated_ratio(idx)

    def _compute_frustrated_ratio(self, idx: Dict[str, int]) -> None:
        """Count frustrated triangles per node.

        A triangle (u, v, w) is frustrated when the product of its three edge
        signs is negative — i.e., the three constructs cannot be consistently
        assigned to two camps.  Nodes with high frustrated_ratio straddle the
        bipartition boundary and carry higher interpretive uncertainty.

        Args:
            idx: node→index map from _compute_bipartition (may be empty for
                 degenerate graphs with no connected constructs).
        """
        if not idx:
            return

        # Signed adjacency lookup: (src, tgt) → sign
        gamma_sign: Dict[Tuple[str, str], int] = {}
        adj_nbrs: Dict[str, set] = {}
        for src in idx:
            adj_nbrs[src] = set()
            for e in self._bridges.get(src, []):
                nbr = e["neighbor"]
                if nbr in idx:
                    adj_nbrs[src].add(nbr)
                    s = 1 if e["gamma"] > 0 else -1
                    gamma_sign[(src, nbr)] = s
                    gamma_sign[(nbr, src)] = s

        for node in idx:
            nbrs = list(adj_nbrs.get(node, set()))
            total = 0
            frustrated = 0
            for a_i, nbr_a in enumerate(nbrs):
                for nbr_b in nbrs[a_i + 1:]:
                    if nbr_b not in adj_nbrs.get(nbr_a, set()):
                        continue
                    total += 1
                    s1 = gamma_sign.get((node, nbr_a), 0)
                    s2 = gamma_sign.get((node, nbr_b), 0)
                    s3 = gamma_sign.get((nbr_a, nbr_b), 0)
                    if s1 * s2 * s3 < 0:
                        frustrated += 1
            self._n_triangles[node] = total
            self._frustrated_ratio[node] = frustrated / total if total > 0 else 0.0

    # ─────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────

    def get_profile(self, key: str) -> Dict:
        """Return fingerprint + structured narrative for a construct, item, or domain."""
        fp, level = self._resolve(key)
        if fp is None:
            return {"error": f"No fingerprint found for '{key}'", "level": None}
        return {
            "key":      key,
            "level":    level,
            "fingerprint": fp,
            "ses_summary":  self._ses_summary(fp),
            "narrative":    self._narrative(key, fp, level),
            "kg_relations": self._kg_rels.get(key, []),
        }

    def get_similar(self, key: str, n: int = 10) -> List[Dict]:
        """Return the n most similar constructs by fingerprint cosine similarity."""
        fp, _ = self._resolve(key)
        if fp is None:
            return []
        query_vec = self._fp_to_vec(fp)
        if query_vec is None:
            return []

        sims = self._cosine_sim_all(query_vec)
        ranked = sorted(
            ((k, s) for k, s in zip(self._vec_keys, sims) if k != key),
            key=lambda x: -x[1],
        )[:n]
        return [
            {
                "key":        k,
                "cosine_sim": round(float(s), 4),
                "shared_dim": self._shared_driver(fp, self._constructs[k]),
                "fingerprint": self._constructs[k],
            }
            for k, s in ranked
        ]

    def explain_pair(self, key_a: str, key_b: str) -> Dict:
        """Explain whether and why two topics co-vary through the sociodemographic structure."""
        fp_a, level_a = self._resolve(key_a)
        fp_b, level_b = self._resolve(key_b)
        if fp_a is None or fp_b is None:
            missing = key_a if fp_a is None else key_b
            return {"error": f"No fingerprint for '{missing}'"}

        vec_a = self._fp_to_vec(fp_a)
        vec_b = self._fp_to_vec(fp_b)
        cos_sim: Optional[float] = None
        if vec_a is not None and vec_b is not None:
            cos_sim = float(np.dot(vec_a, vec_b) /
                            (np.linalg.norm(vec_a) * np.linalg.norm(vec_b) + 1e-12))

        shared = self._shared_driver(fp_a, fp_b)
        kg_links = [r for r in self._kg_rels.get(key_a, []) if r["to"] == key_b]

        return {
            "key_a":        key_a,
            "key_b":        key_b,
            "level_a":      level_a,
            "level_b":      level_b,
            "cosine_sim":   round(cos_sim, 4) if cos_sim is not None else None,
            "covariation":  self._covariation_verdict(cos_sim, fp_a, fp_b),
            "shared_dim":   shared,
            "fingerprint_a": fp_a,
            "fingerprint_b": fp_b,
            "kg_links":     kg_links,
            "narrative":    self._pair_narrative(key_a, key_b, fp_a, fp_b, cos_sim, shared),
        }

    def get_domain_landscape(self, domain: str) -> Dict:
        """Return all construct profiles in a domain, sorted by SES magnitude."""
        constructs = {k: v for k, v in self._constructs.items()
                      if k.startswith(f"{domain}|")}
        domain_fp = self._domains.get(domain)
        ranked = sorted(constructs.items(), key=lambda x: -x[1].get("ses_magnitude", 0))
        return {
            "domain":          domain,
            "domain_fp":       domain_fp,
            "n_constructs":    len(constructs),
            "constructs":      [{"key": k, **v} for k, v in ranked],
            "ses_summary":     self._ses_summary(domain_fp) if domain_fp else None,
        }

    def get_neighbors(
        self,
        key: str,
        min_abs_gamma: float = 0.0,
        top_n: Optional[int] = None,
    ) -> List[Dict]:
        """Return all constructs with a significant bridge edge to key.

        Results are sorted by |gamma| descending.  All edges in _bridges
        already have excl_zero=True (only significant pairs are stored).

        Args:
            key:           L1 construct key, e.g. "FAM|childrens_participation"
            min_abs_gamma: optional lower bound on |gamma| (default: no filter)
            top_n:         if set, return only the top-n strongest edges

        Returns:
            List of dicts with keys: neighbor, gamma, ci_lo, ci_hi, ci_width,
            nmi, fingerprint_cos, shared_dim, neighbor_fp
        """
        edges = self._bridges.get(key, [])
        if min_abs_gamma > 0:
            edges = [e for e in edges if abs(e["gamma"]) >= min_abs_gamma]
        edges = sorted(edges, key=lambda e: -abs(e["gamma"]))
        if top_n is not None:
            edges = edges[:top_n]
        result = []
        for e in edges:
            nbr = e["neighbor"]
            nbr_fp = self._constructs.get(nbr)
            result.append({
                "neighbor":       nbr,
                "gamma":          e["gamma"],
                "ci_lo":          e["ci_lo"],
                "ci_hi":          e["ci_hi"],
                "ci_width":       e["ci_width"],
                "nmi":            e["nmi"],
                "fingerprint_cos": e["fingerprint_cos"],
                "shared_dim":     self._shared_driver(
                                      self._constructs[key] if key in self._constructs else {},
                                      nbr_fp or {}
                                  ),
                "neighbor_fp":    nbr_fp,
            })
        return result

    def get_camp(self, key: str) -> Dict:
        """Return camp membership for any key (L0/L1/L2).

        Camp +1 = cosmopolitan: elevated by education and urbanisation
                  (science, digital capital, political engagement, cultural consumption)
        Camp -1 = tradition: elevated by rural residence and older age
                  (religiosity, traditional gender roles, community attachment)

        A construct is a boundary node if confidence < 0.2 or
        frustrated_ratio > 0.15.  Because the network has near-zero modularity
        (Q=0.089), boundary flags are common and expected — they reflect the
        graph's continuous geometry, not measurement error.

        Returns:
            key, anchor_construct, lift_type, loading_gamma,
            camp_id (+1 / -1 / None), camp_name, confidence (0–1),
            frustrated_ratio, n_triangles, is_boundary, narrative, error.
        """
        lift = self._lift_to_construct(key)
        anchor = lift["construct_key"]
        lift_type = lift["lift_type"]

        base: Dict = {
            "key": key,
            "anchor_construct": anchor,
            "lift_type": lift_type,
            "loading_gamma": lift["loading_gamma"],
            "camp_id": None,
            "camp_name": None,
            "confidence": 0.0,
            "frustrated_ratio": 0.0,
            "n_triangles": 0,
            "is_boundary": False,
            "narrative": "",
            "error": None,
        }

        if anchor is None or lift_type == "none":
            base["error"] = f"No anchor found for '{key}'."
            base["narrative"] = base["error"]
            return base

        if lift_type in ("domain_fallback", "no_constructs_in_domain"):
            base["error"] = (
                f"'{anchor}' is a domain-level key — camp assignment requires "
                f"an L1 construct anchor."
            )
            base["narrative"] = base["error"]
            return base

        camp_id = self._camp.get(anchor)
        if camp_id is None:
            base["error"] = f"Camp not computed for '{anchor}'."
            base["narrative"] = base["error"]
            return base

        confidence = self._camp_confidence.get(anchor, 0.0)
        frust_ratio = self._frustrated_ratio.get(anchor, 0.0)
        n_tri = self._n_triangles.get(anchor, 0)
        is_boundary = confidence < 0.2 or frust_ratio > 0.15

        camp_name = "cosmopolitan" if camp_id == 1 else "tradition"
        _CAMP_DESC = {
            "cosmopolitan": (
                "elevated by education and urbanisation "
                "(science curiosity, digital capital, political engagement)"
            ),
            "tradition": (
                "elevated by rural residence and older age "
                "(religiosity, traditional gender roles, community attachment)"
            ),
        }

        anchor_name = anchor.split("|")[-1].replace("_", " ") if "|" in anchor else anchor
        lift_note = (
            ""
            if lift_type == "exact"
            else (
                f" [approximate lift from '{key}'"
                + (
                    f", loading_γ≈{lift['loading_gamma']:.3f}"
                    if lift["loading_gamma"] is not None
                    else ""
                )
                + "]"
            )
        )
        boundary_note = (
            " This construct sits near the camp boundary — assignment has lower confidence."
            if is_boundary
            else ""
        )

        narrative = (
            f"'{anchor_name}'{lift_note} is assigned to the {camp_name} camp: "
            f"{_CAMP_DESC[camp_name]}. "
            f"Confidence: {confidence:.3f} (Fiedler distance from boundary).{boundary_note} "
            f"Frustrated triangle ratio: {frust_ratio:.3f} ({n_tri} total triangles)."
        )

        base.update({
            "camp_id": camp_id,
            "camp_name": camp_name,
            "confidence": round(confidence, 3),
            "frustrated_ratio": round(frust_ratio, 3),
            "n_triangles": n_tri,
            "is_boundary": is_boundary,
            "narrative": narrative,
        })
        return base

    def get_frustrated_nodes(self, min_frustrated_ratio: float = 0.10) -> List[Dict]:
        """Return constructs with high frustrated triangle ratios, sorted descending.

        Frustrated nodes straddle the camp boundary.  They are not noise —
        they are the constructs where SES creates genuinely non-transitive sign
        patterns, often because their fingerprint sits between the two halves of
        the PC1 axis.  Bridge paths through frustrated nodes carry higher
        interpretive uncertainty.

        Args:
            min_frustrated_ratio: minimum ratio to include (default 0.10).

        Returns:
            List of dicts: construct, camp_id, camp_name, confidence,
            frustrated_ratio, n_triangles, is_boundary.
        """
        results = []
        for node, ratio in self._frustrated_ratio.items():
            if ratio < min_frustrated_ratio:
                continue
            camp_id = self._camp.get(node)
            camp_name = (
                "cosmopolitan" if camp_id == 1
                else "tradition" if camp_id == -1
                else None
            )
            confidence = self._camp_confidence.get(node, 0.0)
            results.append({
                "construct": node,
                "camp_id": camp_id,
                "camp_name": camp_name,
                "confidence": round(confidence, 3),
                "frustrated_ratio": round(ratio, 3),
                "n_triangles": self._n_triangles.get(node, 0),
                "is_boundary": confidence < 0.2 or ratio > 0.15,
            })
        return sorted(results, key=lambda x: -x["frustrated_ratio"])

    def get_network(
        self,
        key: str,
        hops: int = 1,
        min_abs_gamma: float = 0.0,
        top_n_per_node: Optional[int] = None,
    ) -> Dict:
        """BFS subgraph starting from key up to `hops` degrees of separation.

        Args:
            key:             starting L1 construct key
            hops:            number of BFS levels to expand (default: 1 = direct neighbors)
            min_abs_gamma:   prune edges below this |gamma| threshold
            top_n_per_node:  at each node, keep only the top-n edges before expanding

        Returns:
            {
              "root":   key,
              "hops":   hops,
              "nodes":  {key: fingerprint_dict, ...},   # all visited constructs
              "edges":  [{"from", "to", "gamma", "ci_lo", "ci_hi", "nmi", "fingerprint_cos"}, ...]
            }
        """
        visited_nodes: Dict[str, Dict] = {}
        visited_edges: Dict[frozenset, Dict] = {}   # keyed by frozenset({a,b}) to avoid duplicates
        queue = [key]
        current_frontier = {key}

        if key in self._constructs:
            visited_nodes[key] = self._constructs[key]

        for _ in range(hops):
            next_frontier: set = set()
            for node in current_frontier:
                for e in self.get_neighbors(node, min_abs_gamma=min_abs_gamma, top_n=top_n_per_node):
                    nbr = e["neighbor"]
                    edge_id = frozenset({node, nbr})
                    if edge_id not in visited_edges:
                        visited_edges[edge_id] = {
                            "from":           node,
                            "to":             nbr,
                            "gamma":          e["gamma"],
                            "ci_lo":          e["ci_lo"],
                            "ci_hi":          e["ci_hi"],
                            "nmi":            e["nmi"],
                            "fingerprint_cos": e["fingerprint_cos"],
                        }
                    if nbr not in visited_nodes:
                        visited_nodes[nbr] = self._constructs.get(nbr, {})
                        next_frontier.add(nbr)
            current_frontier = next_frontier

        return {
            "root":  key,
            "hops":  hops,
            "nodes": visited_nodes,
            "edges": list(visited_edges.values()),
        }

    # ─────────────────────────────────────────────────────────
    # Item → construct lift
    # ─────────────────────────────────────────────────────────

    def _lift_to_construct(self, key: str) -> Dict:
        """Resolve any key (L0/L1/L2) to the best available L1 anchor construct.

        Returns:
            {
                "construct_key":  str | None,
                "lift_type":      "exact" | "approximate" | "domain_fallback"
                                  | "no_constructs_in_domain" | "none",
                "loading_gamma":  float | None,
                "loading_type":   str | None,
            }

        Priority:
          1. Key is already an L1 construct                → exact, loading_gamma=1.0
          2. L0 item with parent_construct                  → exact, item's loading_gamma
          3. L0 item with candidate_construct               → approximate, candidate_loading_gamma
          4. L0 item in a domain that has constructs        → domain_fallback (no bridge queries)
          5. L0 item in a domain with NO constructs (e.g. JUE, CON)
                                                            → no_constructs_in_domain
          6. Unresolvable                                   → none
        """
        if key in self._constructs:
            return {"construct_key": key, "lift_type": "exact",
                    "loading_gamma": 1.0, "loading_type": "exact"}

        if key in self._items:
            item = self._items[key]
            parent = item.get("parent_construct")
            if parent and parent in self._constructs:
                return {"construct_key": parent, "lift_type": "exact",
                        "loading_gamma": item.get("loading_gamma"),
                        "loading_type": item.get("loading_type", "exact")}
            candidate = item.get("candidate_construct")
            if candidate and candidate in self._constructs:
                return {"construct_key": candidate, "lift_type": "approximate",
                        "loading_gamma": item.get("candidate_loading_gamma"),
                        "loading_type": item.get("loading_type", "approximate")}
            # Domain fallback — distinguish structural deadend from ordinary fallback
            domain = item.get("domain", key.split("|")[0] if "|" in key else key)
            if domain in self._empty_domains:
                return {"construct_key": domain,
                        "lift_type": "no_constructs_in_domain",
                        "loading_gamma": None, "loading_type": item.get("loading_type")}
            if domain in self._domains:
                return {"construct_key": domain, "lift_type": "domain_fallback",
                        "loading_gamma": None, "loading_type": item.get("loading_type")}
            return {"construct_key": None, "lift_type": "none",
                    "loading_gamma": None, "loading_type": None}

        if key in self._domains:
            lt = (
                "no_constructs_in_domain"
                if key in self._empty_domains
                else "domain_fallback"
            )
            return {"construct_key": key, "lift_type": lt,
                    "loading_gamma": None, "loading_type": None}

        # bare domain prefix (e.g. "FAM")
        if "|" not in key and len(key) <= 5 and key in self._domains:
            lt = (
                "no_constructs_in_domain"
                if key in self._empty_domains
                else "domain_fallback"
            )
            return {"construct_key": key, "lift_type": lt,
                    "loading_gamma": None, "loading_type": None}

        return {"construct_key": None, "lift_type": "none",
                "loading_gamma": None, "loading_type": None}

    # ─────────────────────────────────────────────────────────
    # Use-case 1 — neighborhood description
    # ─────────────────────────────────────────────────────────

    def get_neighborhood(
        self,
        key: str,
        min_abs_gamma: float = 0.0,
        top_n: Optional[int] = None,
    ) -> Dict:
        """Describe the SES-mediated attitudinal neighborhood of any item or construct.

        Lifts the input key to an L1 anchor construct, then returns all significant
        bridge neighbors with a neighborhood summary.

        Args:
            key:           L0 item key (e.g. "p3_2|IDE"), L1 construct, or L2 domain
            min_abs_gamma: filter edges below this |gamma| threshold
            top_n:         limit to top-n strongest neighbors

        Returns dict with:
            input_key, anchor_construct, lift_type, loading_gamma,
            neighbors (sorted by |gamma|), neighborhood_summary, narrative, error
        """
        lift = self._lift_to_construct(key)
        anchor = lift["construct_key"]

        if anchor is None:
            return {"input_key": key, "anchor_construct": None,
                    "lift_type": "none", "error": f"No anchor found for '{key}'",
                    "neighbors": [], "neighborhood_summary": {}, "narrative": ""}

        neighbors = self.get_neighbors(anchor, min_abs_gamma=min_abs_gamma, top_n=top_n)

        # Summary statistics
        domain_dist = Counter(n["neighbor"].split("|")[0] for n in neighbors)
        pos = sum(1 for n in neighbors if n["gamma"] > 0)
        neg = sum(1 for n in neighbors if n["gamma"] < 0)
        dim_counter = Counter(n["shared_dim"] for n in neighbors if n["shared_dim"])
        dominant_dim = dim_counter.most_common(1)[0][0] if dim_counter else None
        strongest = max(neighbors, key=lambda n: abs(n["gamma"])) if neighbors else None

        summary = {
            "n_neighbors":        len(neighbors),
            "domain_distribution": dict(domain_dist.most_common()),
            "positive_gamma":     pos,
            "negative_gamma":     neg,
            "dominant_shared_dim": dominant_dim,
            "strongest_edge":     strongest,
        }

        # Narrative
        anchor_name = anchor.split("|")[-1].replace("_", " ") if "|" in anchor else anchor
        lift_note = (
            "" if lift["lift_type"] == "exact"
            else f" [via {lift['lift_type']} lift from '{key}'"
                 + (f", loading_γ={lift['loading_gamma']:.3f}" if lift["loading_gamma"] is not None else "")
                 + "]"
        )
        if not neighbors:
            narrative = (
                f"'{anchor_name}'{lift_note} has no significant SES-mediated bridge "
                f"connections in the current network."
            )
        else:
            s = strongest
            narrative = (
                f"'{anchor_name}'{lift_note} has {len(neighbors)} bridge-connected "
                f"construct(s). Positive co-variation (γ>0): {pos}; "
                f"negative (γ<0): {neg}. "
                f"Primary shared SES dimension: {dominant_dim or 'unknown'}. "
                f"Strongest link: {s['neighbor']} (γ={s['gamma']:+.4f})."
            )

        return {
            "input_key":         key,
            "anchor_construct":  anchor,
            "lift_type":         lift["lift_type"],
            "loading_gamma":     lift["loading_gamma"],
            "neighbors":         neighbors,
            "neighborhood_summary": summary,
            "narrative":         narrative,
            "error":             None,
        }

    # ─────────────────────────────────────────────────────────
    # Use-case 2 — directed path (Dijkstra)
    # ─────────────────────────────────────────────────────────

    def find_path(
        self,
        key_a: str,
        key_b: str,
        prefer_sign_consistent: bool = False,
    ) -> Dict:
        """Find the strongest SES-bridge path between two items or constructs.

        Uses Dijkstra with edge weight = -log(|gamma|), which minimises cumulative
        weight ≡ maximises the product of |gamma| values along the path.
        All bridge edges have excl_zero=True — gamma is never zero.

        Args:
            key_a, key_b: L0/L1/L2 keys for the two endpoints.
            prefer_sign_consistent: if True, add a penalty (0.3 in log-space,
                roughly 26% reduction in effective |γ|) each time consecutive
                edges flip sign.  This nudges the router toward all-positive or
                all-negative paths, which are easier to explain narratively.
                The penalty is soft — it does not prevent crossing if no
                sign-consistent path exists.

        Returns dict with:
            key_a, key_b, anchor_a, anchor_b, lift_a, lift_b,
            camp_a, camp_b,                    ← NEW: camp dicts for each endpoint
            expected_sign (+1/-1/None),        ← NEW: predicted from camp membership
            expected_sign_note,                ← NEW: human-readable prediction
            signal_chain_confidence,           ← NEW: "high"/"medium"/"low"
            sign_matches_prediction (bool),    ← NEW: if direct edge exists
            path, edges, signal_chain, total_cost,
            direct_edge, attenuation_warning, narrative, error
        """
        lift_a = self._lift_to_construct(key_a)
        lift_b = self._lift_to_construct(key_b)
        anchor_a = lift_a["construct_key"]
        anchor_b = lift_b["construct_key"]

        # ── Camp metadata ──────────────────────────────────────
        def _camp_dict(anchor: Optional[str]) -> Dict:
            if anchor is None:
                return {"camp_id": None, "camp_name": None, "confidence": None}
            cid = self._camp.get(anchor)
            return {
                "camp_id": cid,
                "camp_name": "cosmopolitan" if cid == 1
                             else "tradition" if cid == -1
                             else None,
                "confidence": self._camp_confidence.get(anchor),
            }

        camp_a = _camp_dict(anchor_a)
        camp_b = _camp_dict(anchor_b)

        cid_a = camp_a["camp_id"]
        cid_b = camp_b["camp_id"]
        if cid_a is not None and cid_b is not None:
            expected_sign = cid_a * cid_b          # +1 same camp, -1 opposite
            expected_sign_note = (
                f"positive (both in {camp_a['camp_name']} camp)"
                if cid_a == cid_b
                else f"negative ({camp_a['camp_name']} × {camp_b['camp_name']})"
            )
        else:
            expected_sign = None
            expected_sign_note = "unknown (one or both endpoints isolated from bridge network)"

        # Signal-chain confidence from lift types
        lt_a, lt_b = lift_a["lift_type"], lift_b["lift_type"]
        _low = {"no_constructs_in_domain", "domain_fallback", "none"}
        if lt_a == "exact" and lt_b == "exact":
            sig_conf = "high"
        elif lt_a in _low or lt_b in _low:
            sig_conf = "low"
        else:
            sig_conf = "medium"

        base = {
            "key_a": key_a, "key_b": key_b,
            "anchor_a": anchor_a, "anchor_b": anchor_b,
            "lift_a": lift_a, "lift_b": lift_b,
            "camp_a": camp_a, "camp_b": camp_b,
            "expected_sign": expected_sign,
            "expected_sign_note": expected_sign_note,
            "signal_chain_confidence": sig_conf,
            "sign_matches_prediction": None,
            "path": None, "edges": None, "signal_chain": None,
            "total_cost": None, "direct_edge": None,
            "attenuation_warning": False, "narrative": "", "error": None,
        }

        if anchor_a is None or anchor_b is None:
            missing = key_a if anchor_a is None else key_b
            base["error"] = f"No anchor found for '{missing}'"
            base["narrative"] = base["error"]
            return base

        if anchor_a == anchor_b:
            base["path"] = [anchor_a]
            base["edges"] = []
            base["signal_chain"] = 1.0
            base["total_cost"] = 0.0
            name = anchor_a.split("|")[-1].replace("_", " ")
            base["narrative"] = f"Both keys map to the same anchor '{name}' — trivial path."
            return base

        # Check for direct edge (stored regardless of Dijkstra result)
        direct_edges = [e for e in self._bridges.get(anchor_a, [])
                        if e["neighbor"] == anchor_b]
        if direct_edges:
            e = direct_edges[0]
            base["direct_edge"] = {
                "from": anchor_a, "to": anchor_b,
                "gamma": e["gamma"], "ci_lo": e["ci_lo"],
                "ci_hi": e["ci_hi"], "nmi": e["nmi"],
            }

        # Guard: anchors with no bridge connections cannot have a path
        if anchor_a not in self._bridges and anchor_b not in self._bridges:
            base["error"] = f"Both anchors are isolated (no bridge edges)"
            base["narrative"] = base["error"]
            return base
        if anchor_a not in self._bridges:
            base["error"] = f"Anchor '{anchor_a}' has no bridge connections"
            base["narrative"] = base["error"]
            return base
        if anchor_b not in self._bridges:
            base["error"] = f"Anchor '{anchor_b}' has no bridge connections"
            base["narrative"] = base["error"]
            return base

        # Dijkstra: weight = -log(|gamma|); optional sign-consistency penalty
        _SIGN_PENALTY = 0.3   # ≈ 26% reduction in effective |γ| per sign flip
        cost_so_far: Dict[str, float] = {anchor_a: 0.0}
        prev: Dict[str, Optional[str]] = {anchor_a: None}
        prev_sign: Dict[str, int] = {anchor_a: 0}    # last edge sign entering node
        heap: list = [(0.0, anchor_a)]

        while heap:
            cost, node = heapq.heappop(heap)
            if node == anchor_b:
                break
            if cost > cost_so_far.get(node, math.inf):
                continue
            last_sign = prev_sign.get(node, 0)
            for edge in self._bridges.get(node, []):
                nbr = edge["neighbor"]
                edge_sign = 1 if edge["gamma"] > 0 else -1
                weight = -math.log(abs(edge["gamma"]))
                if prefer_sign_consistent and last_sign != 0 and edge_sign != last_sign:
                    weight += _SIGN_PENALTY
                new_cost = cost + weight
                if new_cost < cost_so_far.get(nbr, math.inf):
                    cost_so_far[nbr] = new_cost
                    prev[nbr] = node
                    prev_sign[nbr] = edge_sign
                    heapq.heappush(heap, (new_cost, nbr))

        if anchor_b not in prev:
            base["error"] = "No path found (disconnected components)"
            base["narrative"] = base["error"]
            return base

        # Reconstruct path
        path: List[str] = []
        cur: Optional[str] = anchor_b
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        path.reverse()

        # Build edge list for the path
        path_edges: List[Dict] = []
        for i in range(len(path) - 1):
            src, tgt = path[i], path[i + 1]
            match = next(
                (e for e in self._bridges.get(src, []) if e["neighbor"] == tgt), None
            )
            if match:
                path_edges.append({
                    "from": src, "to": tgt,
                    "gamma": match["gamma"], "ci_lo": match["ci_lo"],
                    "ci_hi": match["ci_hi"], "nmi": match["nmi"],
                    "fingerprint_cos": match["fingerprint_cos"],
                })

        signal_chain = 1.0
        for e in path_edges:
            signal_chain *= abs(e["gamma"])
        total_cost = cost_so_far.get(anchor_b, math.inf)

        # Compare signal sign to camp prediction
        sign_matches: Optional[bool] = None
        if expected_sign is not None and path_edges:
            actual_sign = 1 if signal_chain >= 0 else -1
            # Recompute signed product (signal_chain above used abs)
            signed_product = 1.0
            for e in path_edges:
                signed_product *= e["gamma"]
            actual_sign = 1 if signed_product >= 0 else -1
            sign_matches = actual_sign == expected_sign
        # If direct edge exists, use its sign for the match check
        if expected_sign is not None and base.get("direct_edge"):
            direct_sign = 1 if base["direct_edge"]["gamma"] >= 0 else -1
            sign_matches = direct_sign == expected_sign

        base.update({
            "path":                   path,
            "edges":                  path_edges,
            "signal_chain":           round(signal_chain, 6),
            "total_cost":             round(total_cost, 4),
            "attenuation_warning":    signal_chain < 0.001,
            "sign_matches_prediction": sign_matches,
            "narrative":              self._path_narrative(
                path, path_edges, lift_a, lift_b, signal_chain,
                camp_a["camp_name"], camp_b["camp_name"],
                expected_sign, sign_matches,
            ),
        })
        return base

    # ─────────────────────────────────────────────────────────
    # Resolution (L2 → L1 → L0)
    # ─────────────────────────────────────────────────────────

    def _resolve(self, key: str) -> Tuple[Optional[Dict], Optional[str]]:
        if key in self._constructs:
            return self._constructs[key], "L1_construct"
        if key in self._items:
            return self._items[key], "L0_item"
        if key in self._domains:
            return self._domains[key], "L2_domain"
        # Try domain prefix fallback
        domain = key.split("|")[0] if "|" in key else key
        if domain in self._domains:
            return self._domains[domain], "L2_domain_fallback"
        return None, None

    # ─────────────────────────────────────────────────────────
    # Vector ops
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _fp_to_vec(fp: Dict) -> Optional[np.ndarray]:
        vals = [fp.get(f"rho_{dim}", 0.0) for dim in _ALL_DIMS]
        arr = np.array(vals, dtype=float)
        norm = np.linalg.norm(arr)
        return arr / norm if norm > 1e-9 else None

    @staticmethod
    def _build_matrix(fps: Dict[str, Dict], keys: List[str]) -> np.ndarray:
        rows = []
        for k in keys:
            fp = fps[k]
            vals = [fp.get(f"rho_{dim}", 0.0) for dim in _ALL_DIMS]
            arr = np.array(vals, dtype=float)
            norm = np.linalg.norm(arr)
            rows.append(arr / norm if norm > 1e-9 else arr)
        return np.array(rows) if rows else np.zeros((0, 4))

    def _cosine_sim_all(self, query_vec: np.ndarray) -> np.ndarray:
        return self._vec_matrix @ query_vec  # vectors are pre-normalised

    # ─────────────────────────────────────────────────────────
    # Narrative builders
    # ─────────────────────────────────────────────────────────

    def _path_narrative(
        self,
        path: List[str],
        edges: List[Dict],
        lift_a: Dict,
        lift_b: Dict,
        signal_chain: float,
        camp_name_a: Optional[str] = None,
        camp_name_b: Optional[str] = None,
        expected_sign: Optional[int] = None,
        sign_matches: Optional[bool] = None,
    ) -> str:
        """Human-readable description of a Dijkstra bridge path."""
        if len(path) == 1:
            name = path[0].split("|")[-1].replace("_", " ")
            return f"Both endpoints map to the same anchor '{name}' — no bridge needed."

        name_a = path[0].split("|")[-1].replace("_", " ")
        name_b = path[-1].split("|")[-1].replace("_", " ")

        # Build chain string: A → (dim, γ=+0.08) → B → ...
        chain_parts: List[str] = [name_a]
        for e in edges:
            fp_from = self._constructs.get(e["from"], {})
            fp_to   = self._constructs.get(e["to"], {})
            dim = self._shared_driver(fp_from, fp_to) or "?"
            dim_label = _DIM_LABELS.get(dim, dim)
            chain_parts.append(f"({dim_label}, γ={e['gamma']:+.4f})")
            chain_parts.append(e["to"].split("|")[-1].replace("_", " "))
        chain_str = " → ".join(chain_parts)

        n_hops = len(edges)
        lift_notes: List[str] = []
        for lift in (lift_a, lift_b):
            if lift.get("lift_type") == "approximate":
                lg = lift.get("loading_gamma")
                note = (
                    f"approximate anchor '{lift['construct_key']}'"
                    + (f" (loading_γ≈{lg:.3f})" if lg is not None else "")
                )
                lift_notes.append(note)

        lines = [
            f"'{name_a}' connects to '{name_b}' through SES mediation ({n_hops} hop(s)).",
            f"Signal chain: {signal_chain:.6f} (product of |γ| — attenuation over path).",
            f"Path: {chain_str}.",
        ]
        if lift_notes:
            lines.append("Lift notes: " + "; ".join(lift_notes) + ".")
        if signal_chain < 0.001:
            lines.append(
                "WARNING: signal chain < 0.001 — chain too attenuated for "
                "substantive interpretation."
            )

        # Camp context line
        if camp_name_a and camp_name_b:
            if camp_name_a == camp_name_b:
                camp_line = (
                    f"Camp: both endpoints are in the {camp_name_a} camp — "
                    f"positive bridge signal expected."
                )
            else:
                camp_line = (
                    f"Camp: {camp_name_a} → {camp_name_b} (opposite camps) — "
                    f"negative bridge signal expected."
                )
            if sign_matches is False:
                camp_line += (
                    " WARNING: observed signal sign contradicts camp prediction — "
                    "path likely crosses camp boundary at an intermediate node."
                )
            lines.append(camp_line)

        return " ".join(lines)

    def _ses_summary(self, fp: Optional[Dict]) -> Dict:
        """Return rho for all 4 SES dimensions (all equal standing)."""
        if not fp:
            return {}
        return {dim: fp.get(f"rho_{dim}", 0.0) for dim in _ALL_DIMS}

    def _shared_driver(self, fp_a: Dict, fp_b: Dict) -> Optional[str]:
        """Return the dimension most responsible for (dis-)alignment.

        Uses |rho_a * rho_b| — the dimension with the largest absolute
        cross-product, regardless of whether the association is positive
        (same direction) or negative (opposite direction).
        """
        best_dim, best_score = None, 0.0
        for dim in _ALL_DIMS:
            ra = fp_a.get(f"rho_{dim}", 0.0)
            rb = fp_b.get(f"rho_{dim}", 0.0)
            score = abs(ra * rb)
            if score > best_score:
                best_score = score
                best_dim = dim
        return best_dim if best_score > 1e-6 else None

    @staticmethod
    def _covariation_verdict(cos_sim: Optional[float], fp_a: Dict, fp_b: Dict) -> str:
        if cos_sim is None:
            return "unknown"
        mag_a = fp_a.get("ses_magnitude", 0)
        mag_b = fp_b.get("ses_magnitude", 0)
        if max(mag_a, mag_b) < 0.03:
            return "ses_independent"
        if cos_sim > 0.5:
            return "positive_covariation"
        if cos_sim < -0.5:
            return "negative_covariation"
        if cos_sim > 0.1:
            return "weak_positive"
        if cos_sim < -0.1:
            return "weak_negative"
        return "orthogonal"

    def _narrative(self, key: str, fp: Dict, level: str) -> str:
        name = key.split("|")[-1].replace("_", " ") if "|" in key else key
        mag = fp.get("ses_magnitude", 0)
        dom = fp.get("dominant_dim", "")
        rho_dom = fp.get(f"rho_{dom}", 0)
        dir_label = _DIM_DIR.get(dom, ("low", "high"))
        direction = dir_label[1] if rho_dom > 0 else dir_label[0]

        if mag < 0.02:
            return (f"'{name}' shows negligible sociodemographic stratification "
                    f"(magnitude {mag:.3f}). It varies similarly across all groups.")
        qualifier = "strongly" if mag > 0.15 else ("moderately" if mag > 0.06 else "weakly")
        dim_label = _DIM_LABELS.get(dom, dom)
        return (
            f"'{name}' is {qualifier} stratified by sociodemographic position ({dim_label}): "
            f"more prevalent among the {direction} (ρ={rho_dom:+.3f}, magnitude={mag:.3f}). "
            f"[Source: {level}]"
        )

    def _pair_narrative(
        self,
        key_a: str, key_b: str,
        fp_a: Dict, fp_b: Dict,
        cos_sim: Optional[float],
        shared_dim: Optional[str],
    ) -> str:
        name_a = key_a.split("|")[-1].replace("_", " ") if "|" in key_a else key_a
        name_b = key_b.split("|")[-1].replace("_", " ") if "|" in key_b else key_b
        mag_a = fp_a.get("ses_magnitude", 0)
        mag_b = fp_b.get("ses_magnitude", 0)

        if max(mag_a, mag_b) < 0.02:
            return (f"Both '{name_a}' and '{name_b}' are virtually flat across all "
                    f"sociodemographic groups. Any observed co-variation is not "
                    f"driven by shared SES or demographic structure.")

        verdict = self._covariation_verdict(cos_sim, fp_a, fp_b)
        if verdict == "ses_independent":
            return (f"'{name_a}' and '{name_b}' are functionally independent in SES "
                    f"space (cosine={cos_sim:.3f}). They may co-vary for reasons "
                    f"unrelated to education, locality, gender, or age.")

        dim_label = _DIM_LABELS.get(shared_dim, shared_dim) if shared_dim else "multiple dimensions"
        rho_a = fp_a.get(f"rho_{shared_dim}", 0) if shared_dim else 0
        rho_b = fp_b.get(f"rho_{shared_dim}", 0) if shared_dim else 0

        if verdict in ("positive_covariation", "weak_positive"):
            return (
                f"'{name_a}' and '{name_b}' tend to co-vary positively through shared "
                f"sociodemographic structure (cosine={cos_sim:.3f}). "
                f"The primary driver is {dim_label}: "
                f"ρ_A={rho_a:+.3f}, ρ_B={rho_b:+.3f}. "
                f"Groups with higher {dim_label} tend to score higher on both."
            )
        if verdict in ("negative_covariation", "weak_negative"):
            return (
                f"'{name_a}' and '{name_b}' tend to co-vary negatively through shared "
                f"sociodemographic structure (cosine={cos_sim:.3f}). "
                f"The primary driver is {dim_label}: "
                f"ρ_A={rho_a:+.3f}, ρ_B={rho_b:+.3f}. "
                f"Groups with higher {dim_label} score higher on one and lower on the other."
            )
        return (
            f"'{name_a}' and '{name_b}' have partially aligned sociodemographic profiles "
            f"(cosine={cos_sim:.3f}), but the alignment is weak. "
            f"Any co-variation is likely modest and context-dependent."
        )


# ─────────────────────────────────────────────────────────────
# Quick smoke test
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    oq = OntologyQuery()

    print("─── Profile: HAB|structural_housing_quality ───")
    p = oq.get_profile("HAB|structural_housing_quality")
    print(p["narrative"])
    print("SES:", p["ses_summary"])

    print("\n─── Profile: REL|personal_religiosity ───")
    p2 = oq.get_profile("REL|personal_religiosity")
    print(p2["narrative"])

    print("\n─── Explain pair: HAB|structural_housing_quality × REL|personal_religiosity ───")
    ex = oq.explain_pair("HAB|structural_housing_quality", "REL|personal_religiosity")
    print(ex["narrative"])
    print(f"  cosine_sim={ex['cosine_sim']}  verdict={ex['covariation']}  shared_dim={ex['shared_dim']}")

    print("\n─── Most similar to CIE|household_science_cultural_capital ───")
    for sim in oq.get_similar("CIE|household_science_cultural_capital", n=5):
        print(f"  {sim['key']:55s} cos={sim['cosine_sim']:.3f}  shared={sim['shared_dim']}")

    print("\n─── Domain landscape: REL ───")
    land = oq.get_domain_landscape("REL")
    print(f"  {land['n_constructs']} constructs, domain_mag={land['domain_fp']['ses_magnitude']:.3f}")
    for c in land["constructs"]:
        print(f"  {c['key']:50s} mag={c['ses_magnitude']:.3f}  dom={c['dominant_dim']}")

    print("\n─── Neighbors: FAM|family_cohesion_quality ───")
    for n in oq.get_neighbors("FAM|family_cohesion_quality", top_n=5):
        print(f"  {n['neighbor']:55s} γ={n['gamma']:+.4f}  shared={n['shared_dim']}")

    print("\n─── 2-hop network from FAM|family_cohesion_quality (top 10/node) ───")
    net = oq.get_network("FAM|family_cohesion_quality", hops=2, top_n_per_node=10)
    print(f"  nodes={len(net['nodes'])}  edges={len(net['edges'])}")

    # ── Use-case 1: neighborhood via item key ──────────────────────────
    print("\n─── Use-case 1: get_neighborhood from item key ───")
    item_key = "p3_2|IDE"   # known exact member of IDE|national_identity_pride
    nh = oq.get_neighborhood(item_key)
    print(f"  input:   {item_key}")
    print(f"  anchor:  {nh['anchor_construct']}  lift={nh['lift_type']}  loading_γ={nh['loading_gamma']}")
    print(f"  {nh['narrative']}")

    print("\n─── Use-case 1: get_neighborhood from orphan item ───")
    orphan_key = "loca|IDE"  # orphan item (no parent construct)
    nh2 = oq.get_neighborhood(orphan_key)
    print(f"  input:   {orphan_key}")
    print(f"  anchor:  {nh2['anchor_construct']}  lift={nh2['lift_type']}  loading_γ={nh2['loading_gamma']}")
    print(f"  {nh2['narrative']}")

    # ── Use-case 2: find_path between constructs ───────────────────────
    print("\n─── Use-case 2: find_path between constructs ───")
    fp_result = oq.find_path("FAM|family_cohesion_quality", "FED|political_interest_and_engagement")
    print(f"  path: {' → '.join(fp_result['path'] or [])}")
    print(f"  signal_chain={fp_result['signal_chain']}  hops={len(fp_result['edges'] or [])}")
    print(f"  {fp_result['narrative']}")

    print("\n─── Use-case 2: find_path from item to construct ───")
    fp_result2 = oq.find_path("loca|IDE", "HAB|structural_housing_quality")
    print(f"  anchor_a={fp_result2['anchor_a']}  lift={fp_result2['lift_a']['lift_type']}")
    print(f"  path: {' → '.join(fp_result2['path'] or [])}")
    print(f"  {fp_result2['narrative']}")
