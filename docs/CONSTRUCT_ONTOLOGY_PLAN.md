# Construct Ontology for Navegador — Development Plan

**Date:** 2026-03-04
**Branch:** `feature/bivariate-analysis`
**Author:** Planning document (LLM-assisted)

---

## 1. Vision

The current knowledge graph in `survey_kg.py` organizes nodes by *survey topic*: 24 domain nodes (CIE, COR, CUL, ..., SOC), each connected to the variable nodes drawn from that survey. This topology reflects the accident of data collection, not the latent structure of Mexican public opinion.

The goal is a **construct-level ontology** where nodes represent psychological and sociological constructs — "institutional trust," "perceived discrimination," "economic insecurity," "cultural participation" — and empirical edges encode Goodman-Kruskal γ estimates from the bridge estimators. Survey domains become provenance metadata rather than the primary organizing principle.

The payoff for LLM inference is direct: when a user asks about religious attitudes, the system can retrieve not just REL variables but every construct empirically linked to REL through positive γ — e.g., institutional trust (JUS, COR), family values (FAM, GEN), or community identity (IDE, SOC) — weighted by the strength and reliability of the empirical association.

---

## 2. Construct Identification

### Step 1 — Content analysis of bridge questions

The sweep uses the top-entropy question per domain as the bridge variable (72 questions total: 24 domains × ~3 variable pairs, though pairs are drawn from the 9-pair enumeration). Each question gets a provisional construct label assigned by the following pipeline:

1. Extract question text and response labels from `los_mex_dict.json`.
2. Prompt an LLM (Claude Sonnet) with the question text and response set to propose 1–3 latent construct labels using a fixed taxonomy.
3. Human review and disambiguation pass.

### Step 2 — Seed from existing KG construct nodes

`data/kg_ontology.json` already contains concept-level nodes such as `IDE__national_identity`, `SEG__perceived_threats`, and `SOC__digital_access`. These become the initial seed vocabulary. The LLM labeling step in Step 1 is constrained to map onto these seeds first before proposing new labels.

### Step 3 — CFA / bifactor alignment

Some questions load on domain-specific factors; others load on a general cross-domain factor. For example, items asking about trust in the church, courts, police, and federal government load on a general "institutional trust" factor spanning REL, JUS, SEG, COR, and CUL. A bifactor model (Schmid & Leiman, 1957) decomposes each item's variance into a general factor and a domain-specific residual. Items with high general-factor loadings and low residuals are candidates for cross-domain construct nodes.

Practical implementation: use polychoric correlations (or the bridge γ matrix itself as a proxy correlation matrix) and fit a bifactor structure via the `factor_analyzer` Python package.

### Step 4 — IRT-based cross-survey equating

Several surveys use 0–10 trust or agreement scales. Questions measuring "the same construct" across surveys can be placed on a common latent metric using IRT equating (concurrent calibration or test characteristic curve methods). This allows γ edges to be complemented by scale-metric information, improving interpretability for LLM summaries.

---

## 3. Ontology Structure

```
Domain (24 nodes)
  └── Construct (estimated 40–60 nodes)
        └── Question (bridge variable, ~72 total)
              └── Response category (labeled codes)
```

**Construct node schema:**

```json
{
  "id": "TRUST__institutional",
  "label": "Institutional Trust",
  "definition": "Generalized confidence in formal institutions (legal, political, religious).",
  "example_questions": ["COR_P14", "JUS_P07", "REL_P22", "SEG_P11"],
  "domains": ["COR", "JUS", "REL", "SEG", "CUL"],
  "skos_broader": "http://www.w3.org/2004/02/skos/core#Concept",
  "skos_exactMatch": "https://dbpedia.org/page/Institutional_trust"
}
```

**Empirical edge schema:**

```json
{
  "source": "TRUST__institutional",
  "target": "SECURITY__perceived_threats",
  "ensemble_gamma": 0.18,
  "gamma_ci_95": [0.09, 0.27],
  "n_estimates": 9,
  "estimators_ci_exclude_zero": 3,
  "p_ci_excludes_zero": 0.75
}
```

**Inclusion threshold:** |ensemble γ| > 0.05 AND at least 2 of 4 CI-bearing estimators (Bayesian, MRP, Doubly Robust, Residual) have 95% CIs that exclude zero.

---

## 4. Implementation Plan

### Phase 1 — Construct taxonomy (weeks 1–2)

- Extract all 72 bridge question texts and response sets from the JSON data.
- Run LLM-assisted labeling with seed vocabulary from `kg_ontology.json`.
- Produce a `data/construct_taxonomy.json` mapping each question ID to a construct label and domain.
- Human review pass; resolve ambiguous or multi-loading questions.

### Phase 2 — Update `survey_kg.py` (week 2)

- Add `ConstructNode` dataclass alongside existing `DomainNode` and `VariableNode`.
- Add `add_construct()` and `link_question_to_construct()` methods to `SurveyKnowledgeGraph`.
- Populate construct nodes from `construct_taxonomy.json` at load time.
- The domain → construct edge is a `CONTAINS` relation; construct → question is a `MEASURES` relation.

### Phase 3 — Empirical edge weights (week 3, post-sweep)

- Parse `data/results/bridge_comparison_results.json` to compute per-domain-pair ensemble γ.
- Ensemble method: median of the 6 estimator point estimates; CI from the union of Bayesian + MRP + DR intervals.
- Write `data/results/construct_edges.json` using the edge schema above.
- Load edges into the KG via `SurveyKnowledgeGraph.load_empirical_edges()`.

### Phase 4 — `ConstructOntology` class (week 3)

New file: `construct_ontology.py`

```python
class ConstructOntology:
    def __init__(self, kg: SurveyKnowledgeGraph, edges_path: str): ...
    def related_constructs(self, query: str, top_k: int = 5) -> list[dict]: ...
    def community_detection(self) -> dict[str, list[str]]: ...
    def export_skos(self, path: str) -> None: ...
```

`related_constructs()` pipeline:
1. Embed the user query with the same embedding model used in `variable_selector.py`.
2. Find matching construct nodes by cosine similarity.
3. Expand via γ-weighted graph traversal (BFS with edge weight threshold 0.05).
4. Return ranked list of construct IDs, labels, example questions, and γ to the query construct.

`community_detection()` runs the Louvain algorithm (via `networkx` + `python-louvain`) on the γ-weighted graph to surface natural construct clusters (expected 4–7 clusters: trust/institutions, identity/culture, security/risk, economic/social, health/welfare, etc.).

### Phase 5 — LLM inference integration (week 4)

- Wire `ConstructOntology.related_constructs()` into the `agent.py` tool list.
- Update `analytical_essay.py` to annotate which constructs are empirically linked, with γ and CI surfaced inline.
- Update `quantitative_engine.py` to include the construct graph neighborhood in the report header.

---

## 5. Technical Specifications

| Concern | Decision |
|---------|----------|
| File | `construct_ontology.py` (new) + additions to `survey_kg.py` |
| Storage format | `data/construct_taxonomy.json` (JSON-LD compatible); `data/results/construct_edges.json` |
| Export format | SKOS Turtle (`.ttl`) via `rdflib` for portability and LOD compatibility |
| Graph library | `networkx` (already in environment) |
| Community detection | Louvain via `python-louvain` (`community` package) |
| Edge threshold | ensemble |γ| > 0.05 AND ≥ 2/4 CI-bearing estimators exclude zero |
| Embedding model | Reuse model from `variable_selector.py` (no new dependency) |

---

## 6. Example Construct Cluster: Institutional Trust

The following four construct nodes are expected to form a tight cluster based on prior theoretical grounding and anticipated γ ranges from the bridge sweep.

| Construct ID | Label | Anchor Questions | Domains | Expected γ (inter-construct) |
|---|---|---|---|---|
| `TRUST__institutional` | Institutional Trust | Confianza en gobierno, SCJN, iglesia | COR, JUS, REL, SEG | — (hub) |
| `SECURITY__state_efficacy` | State Efficacy | Policía resuelve crimen, Estado protege | SEG, JUS | 0.15–0.25 |
| `CORRUPTION__perception` | Corruption Perception | Corrupción en gobierno, impunidad | COR, JUS | 0.20–0.35 |
| `IDENTITY__civic` | Civic Identity | Orgullo nacional, participación cívica | IDE, SOC, CUL | 0.08–0.18 |

Edges among these four nodes (where they exist in the sweep results) anchor the "legitimacy and governance" community in the Louvain partition.

---

## 7. KG Limitations to Address

The current `SurveyKnowledgeGraph` in `survey_kg.py` has:

- `DomainNode` (24 nodes) connected to `VariableNode` via `CONTAINS` edges
- `ConceptNode` (sparse) connected to variables via `RELATES_TO` edges
- No cross-domain empirical edges; all edges are definitional

**Changes required:**

1. Add `ConstructNode` as an intermediate node type between `DomainNode` and `VariableNode`.
2. Replace or supplement `ConceptNode` with `ConstructNode` where the concept has empirical grounding.
3. Add directed `EMPIRICAL_GAMMA` edges between construct nodes (weighted, with CI metadata).
4. Add a `gamma_weighted_subgraph()` method returning a `networkx.Graph` for community detection and traversal.
5. Deprecate the current flat domain → variable structure in favor of domain → construct → variable.

---

## 8. Key References

- Borsboom, D., & Cramer, A. O. J. (2013). Network analysis: An integrative approach to the structure of psychopathology. *Annual Review of Clinical Psychology, 9*, 91–121.
- Epskamp, S., Borsboom, D., & Fried, E. I. (2018). Estimating psychological networks and their accuracy. *Behavior Research Methods, 50*(1), 195–212.
- Goodman, L. A., & Kruskal, W. H. (1954). Measures of association for cross classifications. *JASA, 49*(268), 732–764.
- Miles, A., & Bechhofer, J. (2009). *SKOS simple knowledge organization system reference*. W3C Recommendation.
- Park, D. K., Gelman, A., & Bafumi, J. (2004). Bayesian multilevel estimation with poststratification. *Political Analysis, 12*(4), 375–385.
- Schmid, J., & Leiman, J. M. (1957). The development of hierarchical factor solutions. *Psychometrika, 22*(1), 53–61.
- DDI Alliance (2014). *DDI-Lifecycle 3.2 specification*. https://ddialliance.org/
