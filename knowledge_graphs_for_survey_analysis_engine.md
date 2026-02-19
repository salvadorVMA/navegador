# Knowledge Graphs for Grounding LLM Interpretation in Multi-Survey Analysis

## The Problem

You have an agentic analysis engine where user queries trigger semantic search across multiple, topically distinct surveys. The retrieved questions — semantically similar but contextually unrelated — are passed to LLMs that then draw spurious associations, compare incomparable metrics, and fabricate causal narratives across unrelated datasets. The LLM has no model of **what the survey objects are** or **how they logically relate to each other**.

What you need is a **domain ontology graph** — a structured representation of the real-world objects that survey questions measure, the relationships between those objects, and crucially, the **boundaries** between conceptual domains. When the LLM receives retrieved questions about "customer satisfaction with delivery speed" (from a logistics survey) and "patient satisfaction with wait times" (from a healthcare survey), the graph should make explicit that these measure **different constructs in different domains**, even though they share the word "satisfaction."

---

## How Knowledge Graphs Solve This

### The Core Abstraction: Triples

A knowledge graph (KG) is a directed labeled graph where the fundamental unit is a **triple**: `(subject, predicate, object)`. Each triple is a fact.

```
(delivery_speed, is_a, logistics_metric)
(patient_wait_time, is_a, healthcare_metric)
(logistics_metric, belongs_to_domain, logistics)
(healthcare_metric, belongs_to_domain, healthcare)
(delivery_speed, NOT_comparable_to, patient_wait_time)
```

For your survey engine, you need two layers of graph:

**Layer 1 — The Object Ontology (what things exist and how they relate):**
```
(customer_satisfaction, is_composed_of, product_quality)
(customer_satisfaction, is_composed_of, delivery_experience)
(customer_satisfaction, is_influenced_by, price_perception)
(delivery_experience, is_measured_by, Q7_delivery_rating)
(product_quality, correlates_with, repurchase_intent)
(employee_engagement, belongs_to_domain, HR_survey)
(customer_satisfaction, belongs_to_domain, CX_survey)
(employee_engagement, DOES_NOT_CAUSE, customer_satisfaction)  # unless proven
```

**Layer 2 — The Survey-to-Object Mapping (which questions measure which objects):**
```
(Q7_delivery_rating, measures, delivery_experience)
(Q7_delivery_rating, source_survey, "2024 CX Survey")
(Q7_delivery_rating, scale_type, likert_5)
(Q12_engagement_score, measures, employee_engagement)
(Q12_engagement_score, source_survey, "2024 HR Pulse")
(Q12_engagement_score, scale_type, likert_7)
```

This structure lets you do something powerful at retrieval time: before passing results to the LLM, you can **annotate them with graph context** that constrains interpretation.

### Three Integration Patterns

The research literature (Agrawal et al., NAACL 2024; Pan et al., 2024) identifies three main approaches for combining KGs with LLMs:

**1. Pre-generation grounding (inject graph context into the prompt)**

This is the most practical for your case. Before the LLM analyzes retrieved questions, you query the KG to extract:
- What domain each question belongs to
- What construct each question measures  
- What relationships exist (or don't) between the constructs
- Whether the scales are comparable

You serialize this as structured context in the prompt. The LLM then reasons within these constraints.

**2. Graph-guided retrieval (use the graph to improve what gets retrieved)**

Instead of pure semantic search, you use the KG to filter or re-rank results. If a user asks about "drivers of customer loyalty," you first identify the relevant subgraph (customer_loyalty ← satisfaction ← product_quality, delivery_experience, price_perception), then retrieve only questions that map to nodes in that subgraph. This prevents the healthcare satisfaction questions from ever reaching the LLM.

**3. Post-generation validation (check LLM claims against the graph)**

After the LLM produces its analysis, you extract its claims as triples and verify them against the KG. If the LLM says "employee engagement drives customer satisfaction," you check whether that edge exists in the graph. If not, you flag it as unsubstantiated or loop back for correction.

### Think-on-Graph (ToG) — The Most Relevant Research Paradigm

The **Think-on-Graph** framework (Sun et al., ICLR 2024) is particularly relevant to your architecture. ToG treats the LLM as an agent that iteratively explores a knowledge graph using beam search to discover reasoning paths before generating an answer. The process alternates between:

1. **Exploration** — the LLM examines neighboring nodes/edges in the KG
2. **Reasoning** — the LLM evaluates which paths are most promising
3. **Evaluation** — the LLM decides if it has enough evidence to answer

The key insight is that the LLM never reasons in a vacuum — every reasoning step is anchored to a graph traversal. This is directly applicable to your survey engine: when analyzing cross-survey results, the LLM should "walk" the ontology graph to determine which comparisons are valid before making claims.

The successor, **Think-on-Graph 2.0** (Ma et al., 2024), extends this by coupling graph retrieval with unstructured document retrieval, creating a hybrid that leverages KG structure for precise navigation while using document context to fill in details the graph might lack.

---

## Architecture for Your Multi-Survey Engine

### Recommended Design

```
┌─────────────────────────────────────────────────────┐
│                   USER QUERY                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              SEMANTIC SEARCH (existing)               │
│     Returns questions from multiple surveys           │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│           GRAPH-BASED CONTEXT ENRICHMENT              │
│                                                       │
│  For each retrieved question:                         │
│  1. Look up its node in the KG                        │
│  2. Get its domain, construct, scale, survey source   │
│  3. Find relationships to OTHER retrieved questions    │
│  4. Identify which comparisons are valid/invalid      │
│  5. Extract the relevant subgraph as context          │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│            LLM ANALYSIS WITH CONSTRAINTS              │
│                                                       │
│  Prompt includes:                                     │
│  - Retrieved data (as before)                         │
│  - Graph context (domain boundaries, relationships)   │
│  - Explicit rules ("only compare within same domain   │
│    unless cross-domain link exists in the graph")     │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│          POST-GENERATION VALIDATION (optional)        │
│                                                       │
│  Extract claims → verify against KG → flag or revise  │
└──────────────────────────────────────────────────────┘
```

### Building the Ontology Graph

For your case, the graph should NOT be auto-generated from question text (that would reproduce the same confusion). Instead, it should be **curated or semi-curated** based on domain expertise:

**Step 1 — Define your domains and constructs:**
```python
# Core ontology (you define this based on your survey portfolio)
domains = {
    "customer_experience": ["satisfaction", "loyalty", "NPS", "effort"],
    "employee_engagement": ["motivation", "belonging", "manager_trust"],
    "market_research": ["brand_awareness", "purchase_intent", "price_sensitivity"],
    "healthcare_quality": ["patient_satisfaction", "care_outcomes", "wait_times"]
}
```

**Step 2 — Map questions to constructs (LLM-assisted, human-verified):**

Use an LLM to propose mappings from your survey questions to these constructs, then review them. This is where tools like KGGen can help bootstrap the process, but the final ontology should be validated.

**Step 3 — Define valid cross-domain relationships:**

This is the critical part. Most cross-domain relationships should be absent (meaning "no known relationship"), and the few that exist should be explicitly stated:
```python
cross_domain_links = [
    ("employee_engagement", "influences", "customer_satisfaction", 
     {"evidence": "Service-profit chain literature", "strength": "moderate"}),
    ("brand_awareness", "drives", "purchase_intent",
     {"evidence": "Marketing funnel", "strength": "strong"}),
]
# Absence of a link = "do not infer a relationship"
```

---

## Python Tools — Open Source Ecosystem

### For Graph Storage and Querying

| Tool | Best For | Install | Notes |
|------|----------|---------|-------|
| **NetworkX** | Prototyping, small graphs (<10K nodes) | `pip install networkx` | In-memory, no persistence, but dead simple. Good starting point. |
| **Neo4j Community Edition** | Production, complex queries | `pip install neo4j` | Free graph database with Cypher query language. Best if you need persistence and complex traversals. Neo4j also publishes `neo4j-graphrag-python` for integrated KG+LLM workflows. |
| **RDFLib** | Formal ontologies, SPARQL queries | `pip install rdflib` | If you want OWL reasoning (class hierarchies, inference). Heavier but more formal. |
| **igraph** | Large graph analytics | `pip install igraph` | Faster than NetworkX for large graphs. C-based. |
| **Kuzu** | Embedded graph DB | `pip install kuzu` | SQLite-like embedded graph database — no server needed, fast, good for medium-scale deployment. |

### For KG Construction from Text

| Tool | What It Does | Install |
|------|-------------|---------|
| **KGGen** | State-of-the-art text-to-KG extraction with entity clustering. NeurIPS 2025 paper. Uses LLMs for extraction, then clusters to reduce sparsity. Outperforms Microsoft GraphRAG on information retention. | `pip install kg-gen` |
| **Microsoft GraphRAG** | End-to-end pipeline: text → KG → community detection → multi-level summaries → LLM-grounded Q&A | `pip install graphrag` |
| **LlamaIndex PropertyGraphIndex** | Extracts entities and relations from text chunks, stores in Neo4j or in-memory, with built-in retrieval. Supports schema-guided extraction. | `pip install llama-index llama-index-graph-stores-neo4j` |
| **LangChain GraphCypherQAChain** | Translates natural language queries into Cypher queries against a Neo4j graph, then feeds results to an LLM. | `pip install langchain langchain-community` |

### For LLM + KG Integration (Reasoning)

| Tool / Framework | Approach | Source |
|------------------|----------|--------|
| **Think-on-Graph (ToG)** | LLM agent iteratively explores KG via beam search. Training-free, plug-and-play. | github.com/GasolSun36/ToG (Apache 2.0) |
| **Reasoning on Graphs (RoG)** | Planning-retrieval-reasoning: generates relation paths grounded by KGs as faithful plans, then retrieves and reasons. | github (open source) |
| **LightRAG** | Lightweight graph-based RAG alternative to Microsoft GraphRAG. Simpler architecture, faster. | github.com/HKUDS/LightRAG |
| **nano-graphrag** | Minimal reimplementation of GraphRAG for easy customization. Good for understanding the internals and adapting. | github.com/gusye1234/nano-graphrag |
| **Neo4j GraphRAG Python** | Official Neo4j package for building GraphRAG pipelines. End-to-end from unstructured text to KG creation to retrieval. | `pip install neo4j-graphrag` |

### For Ontology / Causal Structure

| Tool | Purpose | Install |
|------|---------|---------|
| **Owlready2** | Python OWL ontology library with reasoning. Define formal class hierarchies, property restrictions, and run inference. | `pip install owlready2` |
| **DoWhy** | Causal inference — build causal DAGs, estimate causal effects, run robustness checks. Could validate whether cross-survey causal claims hold. | `pip install dowhy` |
| **CausalNex** | Bayesian network structure learning + inference. Can discover causal structure from survey response data. | `pip install causalnex` |

---

## Practical Implementation: NetworkX Prototype

Here's a working prototype of the graph-enrichment layer you'd insert between semantic search and LLM analysis:

```python
import networkx as nx
from typing import List, Dict, Optional
import json

class SurveyOntologyGraph:
    """
    Domain ontology for multi-survey analysis.
    Prevents LLMs from drawing spurious cross-domain conclusions.
    """
    
    def __init__(self):
        self.G = nx.DiGraph()
    
    # ── Build the ontology ──────────────────────────────
    
    def add_domain(self, domain_id: str, label: str):
        self.G.add_node(domain_id, type="domain", label=label)
    
    def add_construct(self, construct_id: str, label: str, domain_id: str):
        self.G.add_node(construct_id, type="construct", label=label)
        self.G.add_edge(construct_id, domain_id, relation="belongs_to_domain")
    
    def add_question(self, question_id: str, text: str, 
                     construct_id: str, survey_name: str,
                     scale_type: str = None, scale_range: tuple = None):
        self.G.add_node(question_id, type="question", text=text,
                        survey=survey_name, scale_type=scale_type,
                        scale_range=scale_range)
        self.G.add_edge(question_id, construct_id, relation="measures")
    
    def add_relationship(self, source_construct: str, target_construct: str,
                         relation: str, evidence: str = None, 
                         strength: str = None):
        self.G.add_edge(source_construct, target_construct,
                        relation=relation, evidence=evidence, 
                        strength=strength)
    
    # ── Query the ontology ──────────────────────────────
    
    def get_domain(self, node_id: str) -> Optional[str]:
        """Walk up to find the domain for any node."""
        if self.G.nodes[node_id].get("type") == "domain":
            return node_id
        for _, target, data in self.G.out_edges(node_id, data=True):
            if data["relation"] == "belongs_to_domain":
                return target
            if data["relation"] == "measures":
                return self.get_domain(target)
        return None
    
    def are_comparable(self, q1_id: str, q2_id: str) -> dict:
        """
        Determine if two questions can be meaningfully compared.
        Returns reasoning for the LLM.
        """
        d1 = self.get_domain(q1_id)
        d2 = self.get_domain(q2_id)
        
        # Get constructs
        c1 = self._get_construct(q1_id)
        c2 = self._get_construct(q2_id)
        
        # Check scale compatibility
        n1 = self.G.nodes[q1_id]
        n2 = self.G.nodes[q2_id]
        scales_match = (n1.get("scale_type") == n2.get("scale_type") and
                        n1.get("scale_range") == n2.get("scale_range"))
        
        # Same domain?
        if d1 == d2:
            # Check if constructs are related
            if c1 == c2:
                return {"comparable": True, 
                        "reason": f"Both measure '{c1}' in domain '{d1}'",
                        "comparison_type": "direct"}
            elif self.G.has_edge(c1, c2) or self.G.has_edge(c2, c1):
                edge_data = (self.G.edges.get((c1, c2)) or 
                             self.G.edges.get((c2, c1)))
                return {"comparable": True,
                        "reason": f"'{c1}' and '{c2}' are related "
                                  f"via '{edge_data.get('relation')}'",
                        "comparison_type": "related_constructs",
                        "scales_compatible": scales_match}
            else:
                return {"comparable": "weak",
                        "reason": f"Same domain '{d1}' but no direct "
                                  f"relationship between '{c1}' and '{c2}'",
                        "comparison_type": "same_domain_unlinked"}
        else:
            # Different domains — check for cross-domain links
            if self._has_path(c1, c2):
                path = self._get_path_description(c1, c2)
                return {"comparable": True,
                        "reason": f"Cross-domain link exists: {path}",
                        "comparison_type": "cross_domain_linked",
                        "caution": "Cross-domain comparison — "
                                   "interpret with care"}
            else:
                return {"comparable": False,
                        "reason": f"'{c1}' (domain: {d1}) and "
                                  f"'{c2}' (domain: {d2}) have no known "
                                  f"relationship. Do NOT draw conclusions "
                                  f"from patterns between these.",
                        "comparison_type": "incomparable"}
    
    def enrich_retrieved_questions(self, question_ids: List[str]) -> str:
        """
        Generate structured context for the LLM prompt.
        This is the key function — it produces the constraint text
        that gets injected before analysis.
        """
        context_parts = []
        
        # Group by domain
        domain_groups = {}
        for qid in question_ids:
            domain = self.get_domain(qid)
            domain_groups.setdefault(domain, []).append(qid)
        
        context_parts.append("=== SURVEY CONTEXT (from knowledge graph) ===\n")
        
        # Describe domain groupings
        context_parts.append("DOMAIN GROUPINGS:")
        for domain, qids in domain_groups.items():
            dlabel = self.G.nodes[domain]["label"] if domain else "Unknown"
            context_parts.append(f"  Domain: {dlabel}")
            for qid in qids:
                node = self.G.nodes[qid]
                construct = self._get_construct(qid)
                context_parts.append(
                    f"    - {qid}: measures '{construct}' "
                    f"| survey: {node.get('survey')} "
                    f"| scale: {node.get('scale_type')} "
                    f"{node.get('scale_range', '')}"
                )
        
        # Describe valid relationships
        context_parts.append("\nVALID RELATIONSHIPS BETWEEN THESE QUESTIONS:")
        comparisons_made = set()
        for i, q1 in enumerate(question_ids):
            for q2 in question_ids[i+1:]:
                key = tuple(sorted([q1, q2]))
                if key not in comparisons_made:
                    comparisons_made.add(key)
                    comp = self.are_comparable(q1, q2)
                    if comp["comparable"] is True:
                        context_parts.append(f"  ✓ {q1} ↔ {q2}: {comp['reason']}")
                    elif comp["comparable"] == "weak":
                        context_parts.append(f"  ~ {q1} ↔ {q2}: {comp['reason']}")
                    else:
                        context_parts.append(f"  ✗ {q1} ↔ {q2}: {comp['reason']}")
        
        # Add reasoning constraints
        context_parts.append("\nANALYSIS RULES:")
        context_parts.append(
            "- Only draw causal or correlational conclusions between "
            "questions marked ✓ or ~"
        )
        context_parts.append(
            "- Questions marked ✗ are from unrelated domains. "
            "Patterns between them are coincidental unless you have "
            "explicit evidence otherwise."
        )
        context_parts.append(
            "- When comparing scores, note scale differences. "
            "A 4/5 and a 4/7 are NOT equivalent."
        )
        context_parts.append(
            "- Always state which survey each data point comes from."
        )
        
        return "\n".join(context_parts)
    
    # ── Internal helpers ────────────────────────────────
    
    def _get_construct(self, question_id: str) -> Optional[str]:
        for _, target, data in self.G.out_edges(question_id, data=True):
            if data["relation"] == "measures":
                return target
        return None
    
    def _has_path(self, source: str, target: str) -> bool:
        try:
            nx.shortest_path(self.G, source, target)
            return True
        except nx.NetworkXNoPath:
            try:
                nx.shortest_path(self.G, target, source)
                return True
            except nx.NetworkXNoPath:
                return False
    
    def _get_path_description(self, source: str, target: str) -> str:
        try:
            path = nx.shortest_path(self.G, source, target)
        except nx.NetworkXNoPath:
            path = nx.shortest_path(self.G, target, source)
        
        parts = []
        for i in range(len(path) - 1):
            edge_data = self.G.edges[path[i], path[i+1]]
            parts.append(f"{path[i]} --[{edge_data['relation']}]--> {path[i+1]}")
        return " → ".join(parts)


# ══════════════════════════════════════════════════════
#  USAGE EXAMPLE
# ══════════════════════════════════════════════════════

def build_example_ontology():
    g = SurveyOntologyGraph()
    
    # Domains
    g.add_domain("cx_domain", "Customer Experience")
    g.add_domain("hr_domain", "Employee & HR")
    g.add_domain("health_domain", "Healthcare Quality")
    
    # Constructs — CX
    g.add_construct("satisfaction", "Customer Satisfaction", "cx_domain")
    g.add_construct("delivery_exp", "Delivery Experience", "cx_domain")
    g.add_construct("loyalty", "Customer Loyalty", "cx_domain")
    g.add_relationship("delivery_exp", "satisfaction", "contributes_to",
                       evidence="CX driver analysis 2024", strength="strong")
    g.add_relationship("satisfaction", "loyalty", "drives",
                       evidence="NPS correlation study", strength="moderate")
    
    # Constructs — HR
    g.add_construct("engagement", "Employee Engagement", "hr_domain")
    g.add_construct("manager_trust", "Manager Trust", "hr_domain")
    g.add_relationship("manager_trust", "engagement", "influences",
                       evidence="Gallup Q12 framework", strength="strong")
    
    # Constructs — Healthcare
    g.add_construct("patient_sat", "Patient Satisfaction", "health_domain")
    g.add_construct("wait_times", "Wait Time Experience", "health_domain")
    g.add_relationship("wait_times", "patient_sat", "negatively_affects",
                       evidence="HCAHPS analysis", strength="strong")
    
    # Cross-domain link (only where evidence exists)
    g.add_relationship("engagement", "satisfaction", "influences",
                       evidence="Service-profit chain (Heskett 1994)",
                       strength="moderate")
    
    # Questions — CX Survey
    g.add_question("CX_Q1", "Rate your satisfaction with delivery speed",
                   "delivery_exp", "2024 CX Survey", "likert", (1, 5))
    g.add_question("CX_Q2", "How likely are you to recommend us?",
                   "loyalty", "2024 CX Survey", "nps", (0, 10))
    g.add_question("CX_Q3", "Overall satisfaction with our service",
                   "satisfaction", "2024 CX Survey", "likert", (1, 5))
    
    # Questions — HR Survey
    g.add_question("HR_Q1", "I feel motivated to go beyond requirements",
                   "engagement", "2024 Employee Pulse", "likert", (1, 7))
    g.add_question("HR_Q2", "I trust my direct manager",
                   "manager_trust", "2024 Employee Pulse", "likert", (1, 7))
    
    # Questions — Healthcare Survey
    g.add_question("HC_Q1", "Satisfaction with your care experience",
                   "patient_sat", "Patient Experience 2024", "likert", (1, 5))
    g.add_question("HC_Q2", "How would you rate the wait time?",
                   "wait_times", "Patient Experience 2024", "likert", (1, 5))
    
    return g


# Simulate what happens when semantic search returns mixed results
if __name__ == "__main__":
    g = build_example_ontology()
    
    # Semantic search returns these (all about "satisfaction" — different domains!)
    retrieved = ["CX_Q3", "HC_Q1", "HR_Q1", "CX_Q1"]
    
    context = g.enrich_retrieved_questions(retrieved)
    print(context)
```

### Example Output

When the semantic search returns satisfaction-related questions from three different surveys, the enrichment layer produces:

```
=== SURVEY CONTEXT (from knowledge graph) ===

DOMAIN GROUPINGS:
  Domain: Customer Experience
    - CX_Q3: measures 'satisfaction' | survey: 2024 CX Survey | scale: likert (1, 5)
    - CX_Q1: measures 'delivery_exp' | survey: 2024 CX Survey | scale: likert (1, 5)
  Domain: Healthcare Quality
    - HC_Q1: measures 'patient_sat' | survey: Patient Experience 2024 | scale: likert (1, 5)
  Domain: Employee & HR
    - HR_Q1: measures 'engagement' | survey: 2024 Employee Pulse | scale: likert (1, 7)

VALID RELATIONSHIPS BETWEEN THESE QUESTIONS:
  ✓ CX_Q3 ↔ CX_Q1: 'delivery_exp' and 'satisfaction' are related via 'contributes_to'
  ✗ CX_Q3 ↔ HC_Q1: 'satisfaction' (domain: cx_domain) and 'patient_sat' (domain: health_domain) have no known relationship.
  ✓ CX_Q3 ↔ HR_Q1: Cross-domain link exists: engagement --[influences]--> satisfaction
  ✗ HC_Q1 ↔ HR_Q1: 'patient_sat' (domain: health_domain) and 'engagement' (domain: hr_domain) have no known relationship.
  ✗ HC_Q1 ↔ CX_Q1: 'patient_sat' (domain: health_domain) and 'delivery_exp' (domain: cx_domain) have no known relationship.
  ✓ HR_Q1 ↔ CX_Q1: Cross-domain link exists: engagement --[influences]--> satisfaction --[contributes_to (reverse path)]

ANALYSIS RULES:
- Only draw causal or correlational conclusions between questions marked ✓ or ~
- Questions marked ✗ are from unrelated domains. Patterns between them are coincidental.
- When comparing scores, note scale differences. A 4/5 and a 4/7 are NOT equivalent.
- Always state which survey each data point comes from.
```

This context block gets prepended to the LLM's analysis prompt, and it fundamentally changes how the model reasons about the data.

---

## Scaling Up: Neo4j + LlamaIndex for Production

For production with many surveys and thousands of questions, move from NetworkX to Neo4j:

```python
from neo4j import GraphDatabase

# Store the same ontology in Neo4j
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    # Create domain
    session.run("""
        MERGE (d:Domain {id: 'cx_domain', label: 'Customer Experience'})
    """)
    
    # Create construct linked to domain
    session.run("""
        MERGE (c:Construct {id: 'satisfaction', label: 'Customer Satisfaction'})
        MERGE (d:Domain {id: 'cx_domain'})
        MERGE (c)-[:BELONGS_TO_DOMAIN]->(d)
    """)
    
    # Create question linked to construct and survey
    session.run("""
        MERGE (q:Question {id: 'CX_Q3', text: 'Overall satisfaction', 
                           scale: 'likert', scale_min: 1, scale_max: 5})
        MERGE (s:Survey {name: '2024 CX Survey'})
        MERGE (c:Construct {id: 'satisfaction'})
        MERGE (q)-[:MEASURES]->(c)
        MERGE (q)-[:FROM_SURVEY]->(s)
    """)
    
    # Query: "What can I compare CX_Q3 with?"
    result = session.run("""
        MATCH (q1:Question {id: 'CX_Q3'})-[:MEASURES]->(c1:Construct)
        MATCH (q2:Question)-[:MEASURES]->(c2:Construct)
        WHERE q1 <> q2
        OPTIONAL MATCH path = (c1)-[r*1..3]-(c2)
        RETURN q2.id, q2.text, c2.id, 
               CASE WHEN path IS NOT NULL THEN true ELSE false END as related,
               [rel in relationships(path) | type(rel)] as relationship_chain
    """)
```

### Using LlamaIndex with Schema-Guided Extraction

LlamaIndex's `PropertyGraphIndex` lets you define a schema so the KG extraction respects your ontology:

```python
from llama_index.core.indices.property_graph import PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

graph_store = Neo4jPropertyGraphStore(
    username="neo4j", password="password",
    url="bolt://localhost:7687"
)

# Define valid entity and relation types
index = PropertyGraphIndex.from_documents(
    documents,
    graph_store=graph_store,
    allowed_entity_types=["Domain", "Construct", "Question", "Survey"],
    allowed_relation_types=[
        "MEASURES", "BELONGS_TO_DOMAIN", "CONTRIBUTES_TO",
        "DRIVES", "INFLUENCES", "FROM_SURVEY"
    ],
)
```

---

## Semi-Automated Ontology Bootstrap

You don't want to manually tag thousands of questions. Here's a hybrid approach:

**Step 1:** Use an LLM to propose the ontology from your survey instruments:

```python
prompt = """
Given these survey questions, identify:
1. The real-world CONSTRUCTS each question measures
2. The DOMAIN each construct belongs to
3. Causal or logical RELATIONSHIPS between constructs

Questions:
{questions}

Return as JSON with format:
{
  "domains": [{"id": "...", "label": "..."}],
  "constructs": [{"id": "...", "label": "...", "domain": "..."}],
  "questions": [{"id": "...", "construct": "..."}],
  "relationships": [{"from": "...", "to": "...", "type": "...", "evidence": "..."}]
}
"""
```

**Step 2:** Human review (this is where your domain expertise is critical)

**Step 3:** Lock the ontology and use it as a constraint for all future analysis

---

## Key Recommendations

1. **Start with NetworkX** — prototype the enrichment layer, validate that it improves LLM output quality, then migrate to Neo4j for production.

2. **The ontology should be curated, not auto-generated.** Auto-extraction tools (KGGen, GraphRAG) are great for building KGs from documents, but for your use case the ontology defines what's *valid to compare* — that requires human judgment.

3. **Use KGGen or GraphRAG for the object-level detail** within each survey, but layer your curated cross-survey ontology on top.

4. **The enrichment context is the most important piece.** Even without a full graph database, simply injecting domain/construct metadata and comparability flags into the prompt will dramatically reduce spurious cross-survey reasoning.

5. **Consider Think-on-Graph for complex queries** where the LLM needs to traverse multiple relationships to determine if a comparison is valid.

6. **Add DoWhy/CausalNex** if you need to validate causal claims against data, not just against the ontology structure.

---

## References and Further Reading

- Agrawal et al. (2024). "Can Knowledge Graphs Reduce Hallucinations in LLMs? A Survey." NAACL 2024.
- Sun et al. (2024). "Think-on-Graph: Deep and Responsible Reasoning of LLM on Knowledge Graph." ICLR 2024.
- Ma et al. (2024). "Think-on-Graph 2.0: Deep and Interpretable LLM Reasoning with Knowledge Graph-guided Retrieval." arXiv:2407.10805.
- Mo et al. (2025). "KGGen: Extracting Knowledge Graphs from Plain Text with Language Models." NeurIPS 2025.
- Pan et al. (2024). "Unifying Large Language Models and Knowledge Graphs: A Roadmap." TKDE 2024.
- GitHub curated list: github.com/zjukg/KG-LLM-Papers — comprehensive collection of KG+LLM integration papers.
- Neo4j GraphRAG Python: neo4j.com/docs/neo4j-graphrag-python/current/
