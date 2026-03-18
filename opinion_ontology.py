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

import json
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
    ) -> None:
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
