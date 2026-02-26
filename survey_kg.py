"""
Survey Knowledge Graph module for Navegador.

Provides a domain ontology graph that annotates retrieved survey questions
with domain boundaries and comparability rules before they reach the LLM.
This implements the "pre-generation grounding" pattern described in
knowledge_graphs_for_survey_analysis_engine.md.

Ontology structure (three layers):
  Domain  (e.g. IDE, POB, SAL)
    └─ Construct  (e.g. IDE__national_identity)
         └─ Question  (e.g. p5_1|IDE)

Usage:
    from survey_kg import kg
    context = kg.get_kg_context_for_prompt(["p5_1|IDE", "p3_2|POB", "p7_1|SAL"])
    # context is injected into the LLM prompt before analysis

The module lazy-loads the ontology from data/kg_ontology.json at import time.
If the file is missing the KG falls back to a domain-only graph built from
rev_topic_dict (no construct-level detail, but domain grouping still works).
Run scripts/setup/bootstrap_kg_ontology.py once to generate the full ontology.
"""

import json
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import networkx as nx
except ImportError:
    print("ERROR: networkx not installed. Run: pip install networkx>=2.8", file=sys.stderr)
    nx = None  # type: ignore


# ---------------------------------------------------------------------------
# Default path — can be overridden via KG_ONTOLOGY_PATH env variable
# ---------------------------------------------------------------------------
_DEFAULT_ONTOLOGY_PATH = Path(__file__).parent / "data" / "kg_ontology.json"


class SurveyOntologyGraph:
    """
    Domain ontology for the los_mex multi-topic survey analysis engine.

    Prevents LLMs from drawing spurious cross-topic conclusions by annotating
    retrieved questions with domain boundaries and comparability rules.
    """

    def __init__(self) -> None:
        if nx is None:
            raise ImportError("networkx is required. Run: pip install networkx>=2.8")
        self.G: nx.DiGraph = nx.DiGraph()
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Build / populate
    # ------------------------------------------------------------------

    def add_domain(self, domain_id: str, label: str) -> None:
        self.G.add_node(domain_id, node_type="domain", label=label)

    def add_construct(self, construct_id: str, label: str, domain_id: str) -> None:
        self.G.add_node(construct_id, node_type="construct", label=label)
        self.G.add_edge(construct_id, domain_id, relation="belongs_to_domain")

    def add_question(
        self,
        question_id: str,
        text: str,
        construct_id: str,
        scale_type: Optional[str] = None,
    ) -> None:
        self.G.add_node(
            question_id,
            node_type="question",
            text=text,
            scale_type=scale_type,
        )
        self.G.add_edge(question_id, construct_id, relation="measures")

    def add_relationship(
        self,
        source_construct: str,
        target_construct: str,
        relation: str,
        evidence: Optional[str] = None,
        strength: Optional[str] = None,
    ) -> None:
        self.G.add_edge(
            source_construct,
            target_construct,
            relation=relation,
            evidence=evidence,
            strength=strength,
        )

    def build_from_topics(self, rev_topic_dict: Dict[str, str]) -> None:
        """
        Minimal fallback: build a domain-only graph from the topic dictionary.
        Questions will be parented directly to their domain (no construct layer).
        Useful when kg_ontology.json is not yet available.
        """
        for abbrev, label in rev_topic_dict.items():
            self.add_domain(abbrev, label)
        self._loaded = True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_from_json(self, path) -> None:
        """Load ontology from kg_ontology.json into the NetworkX graph."""
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Clear existing graph
        self.G.clear()

        for d in data.get("domains", []):
            self.add_domain(d["id"], d["label"])

        for c in data.get("constructs", []):
            self.add_construct(c["id"], c["label"], c["domain"])

        for q in data.get("questions", []):
            self.add_question(
                q["id"],
                q.get("text", ""),
                q["construct"],
                q.get("scale_type"),
            )

        for r in data.get("relationships", []):
            self.add_relationship(
                r["from"],
                r["to"],
                r["type"],
                r.get("evidence"),
                r.get("strength"),
            )

        n_domains = sum(1 for _, d in self.G.nodes(data=True) if d.get("node_type") == "domain")
        n_constructs = sum(1 for _, d in self.G.nodes(data=True) if d.get("node_type") == "construct")
        n_questions = sum(1 for _, d in self.G.nodes(data=True) if d.get("node_type") == "question")
        n_rels = len(data.get("relationships", []))
        print(
            f"✅ KG loaded: {n_domains} domains, {n_constructs} constructs, "
            f"{n_questions} questions, {n_rels} cross-domain relationships"
        )
        self._loaded = True

    def save_to_json(self, path) -> None:
        """Serialise the graph back to kg_ontology.json."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        domains, constructs, questions, relationships = [], [], [], []

        for node_id, data in self.G.nodes(data=True):
            ntype = data.get("node_type")
            if ntype == "domain":
                domains.append({"id": node_id, "label": data.get("label", node_id)})
            elif ntype == "construct":
                domain = self._get_parent(node_id, "belongs_to_domain")
                constructs.append(
                    {"id": node_id, "label": data.get("label", node_id), "domain": domain or ""}
                )
            elif ntype == "question":
                construct = self._get_parent(node_id, "measures")
                questions.append(
                    {
                        "id": node_id,
                        "text": data.get("text", ""),
                        "construct": construct or "",
                        "scale_type": data.get("scale_type"),
                    }
                )

        for src, tgt, edata in self.G.edges(data=True):
            rel = edata.get("relation", "")
            if rel not in ("belongs_to_domain", "measures"):
                relationships.append(
                    {
                        "from": src,
                        "to": tgt,
                        "type": rel,
                        "evidence": edata.get("evidence"),
                        "strength": edata.get("strength"),
                    }
                )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"domains": domains, "constructs": constructs, "questions": questions, "relationships": relationships},
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"💾 KG saved to {path}")

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_domain(self, node_id: str) -> Optional[str]:
        """Walk up the graph to find the domain for any question or construct node.

        Falls back to parsing the QID string (format: pN_M|TOPIC_ABBREV) when the
        node is not in the graph — this ensures domain-only mode still works.
        """
        if node_id in self.G:
            ntype = self.G.nodes[node_id].get("node_type")
            if ntype == "domain":
                return node_id
            for _, target, data in self.G.out_edges(node_id, data=True):
                rel = data.get("relation", "")
                if rel == "belongs_to_domain":
                    return target
                if rel == "measures":
                    return self.get_domain(target)

        # Pattern-based fallback: extract topic abbreviation from QID (pN_M|TOPIC)
        if "|" in node_id:
            candidate = node_id.split("|")[-1]
            if candidate in self.G and self.G.nodes[candidate].get("node_type") == "domain":
                return candidate

        return None

    def get_construct(self, question_id: str) -> Optional[str]:
        """Return the construct a question measures, or None."""
        return self._get_parent(question_id, "measures")

    def are_comparable(self, q1_id: str, q2_id: str) -> dict:
        """
        Determine whether two questions can be meaningfully compared.

        Returns a dict with:
            comparable: True | "weak" | False
            reason: human-readable explanation for the LLM
            comparison_type: tag for downstream logic
        """
        d1 = self.get_domain(q1_id)
        d2 = self.get_domain(q2_id)
        c1 = self.get_construct(q1_id)
        c2 = self.get_construct(q2_id)

        # Nodes not in graph — cannot determine
        if d1 is None or d2 is None:
            return {
                "comparable": "weak",
                "reason": f"One or both questions not found in the ontology. Cannot determine comparability.",
                "comparison_type": "unknown",
            }

        if d1 == d2:
            if c1 and c2:
                if c1 == c2:
                    return {
                        "comparable": True,
                        "reason": f"Both measure '{self._label(c1)}' within domain '{self._label(d1)}'.",
                        "comparison_type": "direct",
                    }
                if self.G.has_edge(c1, c2) or self.G.has_edge(c2, c1):
                    edge = self.G.edges.get((c1, c2)) or self.G.edges.get((c2, c1))
                    return {
                        "comparable": True,
                        "reason": (
                            f"'{self._label(c1)}' and '{self._label(c2)}' are related "
                            f"via '{edge.get('relation')}' within domain '{self._label(d1)}'."
                        ),
                        "comparison_type": "related_constructs",
                    }
            return {
                "comparable": "weak",
                "reason": (
                    f"Same domain '{self._label(d1)}' but no direct relationship "
                    f"found between their constructs. Compare with caution."
                ),
                "comparison_type": "same_domain_unlinked",
            }
        else:
            # Different domains — look for a cross-domain path through constructs
            if c1 and c2 and self._has_path(c1, c2):
                path_desc = self._path_description(c1, c2)
                return {
                    "comparable": True,
                    "reason": f"Cross-domain link: {path_desc}",
                    "comparison_type": "cross_domain_linked",
                    "caution": "Cross-domain comparison — interpret with care.",
                }
            return {
                "comparable": False,
                "reason": (
                    f"'{self._label(c1 or q1_id)}' (domain: {self._label(d1)}) and "
                    f"'{self._label(c2 or q2_id)}' (domain: {self._label(d2)}) have no known "
                    f"relationship. Do NOT draw causal or correlational conclusions between these."
                ),
                "comparison_type": "incomparable",
            }

    def enrich_retrieved_questions(self, question_ids: List[str]) -> str:
        """
        Generate the KG context block that gets injected into the LLM prompt.

        This is the main public method used by the pipeline.
        """
        if not question_ids:
            return ""

        lines: List[str] = ["=== SURVEY KNOWLEDGE GRAPH CONTEXT ===\n"]

        # Group by domain
        domain_groups: Dict[str, List[str]] = {}
        unknown: List[str] = []
        for qid in question_ids:
            domain = self.get_domain(qid)
            if domain:
                domain_groups.setdefault(domain, []).append(qid)
            else:
                unknown.append(qid)

        lines.append("DOMAIN GROUPINGS:")
        for domain, qids in domain_groups.items():
            lines.append(f"  [{self._label(domain)}]")
            for qid in qids:
                construct = self.get_construct(qid)
                construct_label = self._label(construct) if construct else "—"
                text_snippet = self.G.nodes.get(qid, {}).get("text", "")
                if text_snippet:
                    text_snippet = text_snippet[:80] + ("…" if len(text_snippet) > 80 else "")
                lines.append(f"    • {qid}: construct='{construct_label}' | \"{text_snippet}\"")
        if unknown:
            lines.append(f"  [Unknown domain]: {', '.join(unknown)}")

        # Pairwise comparability
        lines.append("\nCOMPARABILITY BETWEEN RETRIEVED QUESTIONS:")
        seen: set = set()
        any_printed = False
        for i, q1 in enumerate(question_ids):
            for q2 in question_ids[i + 1:]:
                key = tuple(sorted([q1, q2]))
                if key in seen:
                    continue
                seen.add(key)
                comp = self.are_comparable(q1, q2)
                symbol = "✓" if comp["comparable"] is True else ("~" if comp["comparable"] == "weak" else "✗")
                lines.append(f"  {symbol} {q1} ↔ {q2}: {comp['reason']}")
                any_printed = True
        if not any_printed:
            lines.append("  (only one question retrieved — no pairwise comparison needed)")

        # Reasoning rules
        lines.append(
            "\nANALYSIS RULES (apply to your interpretation):\n"
            "  1. Draw causal or correlational conclusions ONLY between ✓ (confirmed) pairs.\n"
            "  2. Treat ~ (weak) pairs with explicit caveats in your analysis.\n"
            "  3. For ✗ (incomparable) pairs: note the domain difference and do NOT imply causation.\n"
            "  4. Always state which survey topic (domain) each data point comes from.\n"
            "=== END KNOWLEDGE GRAPH CONTEXT ===\n"
        )

        return "\n".join(lines)

    def get_kg_context_for_prompt(self, question_ids: List[str]) -> str:
        """
        Safe wrapper around enrich_retrieved_questions.
        Returns an empty string if the KG is not loaded or an error occurs.
        """
        if not self._loaded:
            return ""
        try:
            return self.enrich_retrieved_questions(question_ids)
        except Exception as e:
            warnings.warn(f"KG enrichment failed (non-fatal): {e}")
            return ""

    def summary_stats(self) -> dict:
        """Return a dict with node/edge counts — useful for the notebook."""
        counts: Dict[str, int] = {"domains": 0, "constructs": 0, "questions": 0, "relationships": 0}
        _plural = {"domain": "domains", "construct": "constructs", "question": "questions"}
        for _, data in self.G.nodes(data=True):
            ntype = data.get("node_type")
            key = _plural.get(ntype, "")
            if key:
                counts[key] += 1
        counts["relationships"] = sum(
            1 for _, _, d in self.G.edges(data=True)
            if d.get("relation") not in ("belongs_to_domain", "measures")
        )
        return counts

    def get_topic_questions(self, domain_id: str) -> Dict[str, dict]:
        """Return {question_id: {construct, text}} for all questions in a domain."""
        result = {}
        for node_id, data in self.G.nodes(data=True):
            if data.get("node_type") == "question":
                if self.get_domain(node_id) == domain_id:
                    result[node_id] = {
                        "construct": self.get_construct(node_id),
                        "text": data.get("text", ""),
                    }
        return result

    def get_cross_domain_relationships(self) -> List[dict]:
        """Return all edges between nodes in different domains."""
        result = []
        for src, tgt, edata in self.G.edges(data=True):
            rel = edata.get("relation", "")
            if rel in ("belongs_to_domain", "measures"):
                continue
            d_src = self.get_domain(src)
            d_tgt = self.get_domain(tgt)
            if d_src and d_tgt and d_src != d_tgt:
                result.append(
                    {
                        "from": src,
                        "from_domain": d_src,
                        "to": tgt,
                        "to_domain": d_tgt,
                        "relation": rel,
                        "evidence": edata.get("evidence"),
                        "strength": edata.get("strength"),
                    }
                )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_parent(self, node_id: str, relation: str) -> Optional[str]:
        for _, target, data in self.G.out_edges(node_id, data=True):
            if data.get("relation") == relation:
                return target
        return None

    def _label(self, node_id: Optional[str]) -> str:
        if not node_id:
            return "?"
        return self.G.nodes.get(node_id, {}).get("label", node_id)

    def _has_path(self, src: str, tgt: str) -> bool:
        try:
            nx.shortest_path(self.G, src, tgt)
            return True
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            try:
                nx.shortest_path(self.G, tgt, src)
                return True
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                return False

    def _path_description(self, src: str, tgt: str) -> str:
        try:
            path = nx.shortest_path(self.G, src, tgt)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path = nx.shortest_path(self.G, tgt, src)
        parts = []
        for i in range(len(path) - 1):
            edata = self.G.edges[path[i], path[i + 1]]
            parts.append(f"{self._label(path[i])} --[{edata.get('relation')}]--> {self._label(path[i + 1])}")
        return " → ".join(parts)


# ---------------------------------------------------------------------------
# Module-level singleton — lazy-loaded at import
# ---------------------------------------------------------------------------

kg: Optional[SurveyOntologyGraph] = None
_KG_AVAILABLE: bool = False

def _init_kg() -> None:
    global kg, _KG_AVAILABLE

    if nx is None:
        print("⚠️  survey_kg: networkx not available — KG disabled.", file=sys.stderr)
        return

    import os
    ontology_path = Path(os.environ.get("KG_ONTOLOGY_PATH", _DEFAULT_ONTOLOGY_PATH))

    kg = SurveyOntologyGraph()

    if ontology_path.exists():
        try:
            kg.load_from_json(ontology_path)
            _KG_AVAILABLE = True
        except Exception as e:
            print(f"⚠️  survey_kg: Failed to load {ontology_path}: {e}", file=sys.stderr)
            print("   Falling back to domain-only graph from rev_topic_dict.", file=sys.stderr)
            _fallback_to_topics()
    else:
        print(
            f"⚠️  survey_kg: {ontology_path} not found. "
            "Run scripts/setup/bootstrap_kg_ontology.py to generate it.",
            file=sys.stderr,
        )
        _fallback_to_topics()


def _fallback_to_topics() -> None:
    """Build a minimal domain-only graph from rev_topic_dict."""
    global _KG_AVAILABLE
    try:
        from dataset_knowledge import rev_topic_dict
        if rev_topic_dict:
            kg.build_from_topics(rev_topic_dict)  # type: ignore[union-attr]
            print("ℹ️  survey_kg: domain-only fallback graph loaded.")
            _KG_AVAILABLE = True
    except Exception as e:
        print(f"⚠️  survey_kg: Fallback also failed: {e}", file=sys.stderr)


_init_kg()
