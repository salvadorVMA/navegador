# Survey Knowledge Graph: End-to-End Construction & Reasoning Pipeline

## Overview

This document describes a complete pipeline for:
1. **Extracting real-world objects** from 2K+ survey questions across multiple surveys
2. **Resolving and deduplicating** those objects into canonical entities
3. **Discovering relationships** between objects (including distant, cross-survey ones)
4. **Detecting communities** to identify latent constructs
5. **Building a NetworkX knowledge graph** with the full ontology
6. **Enriching LLM prompts** with graph context to prevent spurious reasoning
7. **Think-on-Graph (ToG) reasoning** for complex analytical queries

All code uses Python with NetworkX, and LLM calls are abstracted behind a simple
interface so you can plug in OpenAI, Anthropic, or any provider.

---

## Dependencies

```bash
pip install networkx numpy scikit-learn
pip install openai  # or anthropic, or litellm for multi-provider
# Optional but recommended:
pip install leidenalg igraph  # Better community detection than Louvain
pip install sentence-transformers  # For embedding-based similarity
```

---

## Part 1: LLM Interface

All LLM calls go through a single abstraction. Replace the internals with your
preferred provider.

```python
# llm_client.py

import json
import time
from typing import List, Dict, Any, Optional


class LLMClient:
    """
    Thin wrapper around your LLM provider.
    Replace the _call method with your actual API call.
    Handles retries, JSON parsing, and batching.
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514", 
                 api_key: str = None,
                 max_retries: int = 3,
                 retry_delay: float = 2.0):
        self.model = model
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _call(self, system_prompt: str, user_prompt: str, 
              temperature: float = 0.0) -> str:
        """
        Replace this with your actual LLM API call.
        Should return the raw text response.
        """
        # --- Example with Anthropic ---
        # import anthropic
        # client = anthropic.Anthropic(api_key=self.api_key)
        # response = client.messages.create(
        #     model=self.model,
        #     max_tokens=4096,
        #     temperature=temperature,
        #     system=system_prompt,
        #     messages=[{"role": "user", "content": user_prompt}]
        # )
        # return response.content[0].text

        # --- Example with OpenAI ---
        # from openai import OpenAI
        # client = OpenAI(api_key=self.api_key)
        # response = client.chat.completions.create(
        #     model=self.model,
        #     temperature=temperature,
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ]
        # )
        # return response.choices[0].message.content

        raise NotImplementedError("Implement _call with your LLM provider")

    def call_json(self, system_prompt: str, user_prompt: str,
                  temperature: float = 0.0) -> Any:
        """Call LLM and parse response as JSON with retries."""
        for attempt in range(self.max_retries):
            try:
                raw = self._call(system_prompt, user_prompt, temperature)
                # Strip markdown fences if present
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    cleaned = cleaned.rsplit("```", 1)[0]
                return json.loads(cleaned)
            except (json.JSONDecodeError, Exception) as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise ValueError(
                        f"Failed to get valid JSON after {self.max_retries} "
                        f"attempts. Last error: {e}\nLast response: {raw[:500]}"
                    )

    def call_text(self, system_prompt: str, user_prompt: str,
                  temperature: float = 0.0) -> str:
        """Call LLM and return raw text."""
        for attempt in range(self.max_retries):
            try:
                return self._call(system_prompt, user_prompt, temperature)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
```

---

## Part 2: Object Extraction (Pass 1)

The core idea: instead of comparing questions pairwise (combinatorial explosion),
extract the real-world **object** each question is about. Questions that map to the
same object become connected through the object, regardless of how far apart they
are in the surveys or how different their wording is.

```python
# object_extraction.py

from typing import List, Dict, Tuple
import json


# ── Prompts ─────────────────────────────────────────────

OBJECT_EXTRACTION_SYSTEM = """You are an expert in survey methodology and 
psychometrics. Your task is to identify the real-world OBJECT or CONSTRUCT 
that each survey question is measuring or asking about.

Rules:
- Be SPECIFIC. "satisfaction" is too vague. "satisfaction_with_delivery_speed" 
  is better.
- Use snake_case for object IDs.
- An object is the THING IN THE WORLD the question refers to, not the question 
  itself.
- Distinguish between similar but different objects. "trust_in_manager" and 
  "trust_in_organization" are different objects.
- For demographic/SES questions, prefix with "demo_" (e.g., "demo_household_income").
- For behavioral questions, prefix with "behavior_" (e.g., "behavior_exercise_frequency").
- For attitudinal/perceptual questions, use descriptive names 
  (e.g., "perceived_workload", "job_satisfaction").

Return ONLY valid JSON."""

OBJECT_EXTRACTION_USER = """For each question below, identify the real-world 
object or construct it measures. Also identify the object TYPE.

Valid types:
- "attitude": Subjective perception, opinion, or feeling
- "behavior": Observable action or frequency
- "outcome": Result or consequence measure
- "demographic": Personal characteristic or SES variable
- "experience": Description of a specific experience or event
- "knowledge": Factual knowledge or awareness

Survey: {survey_name}
Questions:
{questions_block}

Return JSON array:
[
  {{
    "question_id": "...",
    "object_id": "short_snake_case_name",
    "object_label": "Human readable name",
    "object_type": "attitude|behavior|outcome|demographic|experience|knowledge",
    "reasoning": "Brief explanation of why this object"
  }},
  ...
]"""


# ── Extraction Logic ────────────────────────────────────

def format_questions_block(questions: List[Dict]) -> str:
    """Format questions for the prompt."""
    lines = []
    for q in questions:
        lines.append(f"- [{q['id']}] {q['text']}")
        if q.get('response_options'):
            lines.append(f"  Options: {q['response_options']}")
        if q.get('scale'):
            lines.append(f"  Scale: {q['scale']}")
    return "\n".join(lines)


def extract_objects_from_survey(
    llm: 'LLMClient',
    survey_name: str,
    questions: List[Dict],
    batch_size: int = 25
) -> List[Dict]:
    """
    Extract objects from all questions in a survey.
    
    Args:
        llm: LLMClient instance
        survey_name: Name of the survey
        questions: List of dicts with at minimum 'id' and 'text' keys.
                   Optional: 'response_options', 'scale', 'section'
        batch_size: Questions per LLM call (20-30 is optimal)
    
    Returns:
        List of extraction results, one per question.
    """
    all_results = []

    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        block = format_questions_block(batch)

        prompt = OBJECT_EXTRACTION_USER.format(
            survey_name=survey_name,
            questions_block=block
        )

        results = llm.call_json(OBJECT_EXTRACTION_SYSTEM, prompt)

        # Attach survey metadata
        for r in results:
            r['survey_name'] = survey_name
            # Find the original question to carry forward metadata
            orig = next((q for q in batch if q['id'] == r['question_id']), None)
            if orig:
                r['question_text'] = orig['text']
                r['scale'] = orig.get('scale')
                r['response_options'] = orig.get('response_options')

        all_results.extend(results)
        print(f"  Extracted {len(results)} objects from batch "
              f"{i//batch_size + 1}/{-(-len(questions)//batch_size)}")

    return all_results


def extract_all_surveys(
    llm: 'LLMClient',
    surveys: Dict[str, List[Dict]],
    batch_size: int = 25
) -> List[Dict]:
    """
    Process all surveys.
    
    Args:
        surveys: Dict mapping survey_name -> list of question dicts
    
    Returns:
        Combined list of all extraction results.
    """
    all_extractions = []
    for survey_name, questions in surveys.items():
        print(f"\nProcessing survey: {survey_name} ({len(questions)} questions)")
        results = extract_objects_from_survey(
            llm, survey_name, questions, batch_size
        )
        all_extractions.extend(results)
    
    print(f"\nTotal extractions: {len(all_extractions)}")
    return all_extractions
```

---

## Part 3: Entity Resolution (Pass 2)

The LLM won't produce identical object IDs every time. "manager_feedback",
"supervisory_feedback", "feedback_from_supervisor" might all refer to the same 
construct. This pass clusters and deduplicates them.

```python
# entity_resolution.py

from typing import List, Dict, Set, Tuple
from collections import defaultdict


# ── Prompts ─────────────────────────────────────────────

ENTITY_RESOLUTION_SYSTEM = """You are an expert in survey methodology. Your task 
is to identify which object labels refer to the SAME underlying concept and should 
be merged.

Rules:
- Only merge objects that truly refer to the same concept.
- "trust_in_manager" and "trust_in_organization" are DIFFERENT — do not merge.
- "manager_feedback" and "supervisory_feedback" are the SAME — merge them.
- For each cluster, pick the most descriptive canonical name.
- Preserve type distinctions: a behavior and an attitude about the same topic 
  are different objects (e.g., "exercise_frequency" vs "motivation_to_exercise").

Return ONLY valid JSON."""

ENTITY_RESOLUTION_USER = """Below are object labels extracted from survey questions.
Group objects that refer to the SAME real-world concept into clusters.
Objects that are unique should be in their own cluster.

Objects:
{objects_block}

Return JSON:
{{
  "clusters": [
    {{
      "canonical_id": "best_snake_case_name",
      "canonical_label": "Best human-readable label",
      "canonical_type": "attitude|behavior|outcome|demographic|experience|knowledge",
      "members": ["original_id_1", "original_id_2", ...],
      "reasoning": "Why these are the same concept"
    }},
    ...
  ]
}}"""


# ── Resolution Logic ────────────────────────────────────

def resolve_entities(
    llm: 'LLMClient',
    extractions: List[Dict],
    batch_size: int = 80
) -> Tuple[Dict[str, str], List[Dict]]:
    """
    Cluster and deduplicate extracted objects.
    
    Uses two strategies:
    1. Group by exact object_id match (trivial dedup)
    2. LLM-based semantic dedup for different IDs that mean the same thing
    
    Args:
        llm: LLMClient instance
        extractions: Output from extract_all_surveys()
        batch_size: Objects per LLM resolution call
    
    Returns:
        Tuple of:
        - mapping: Dict[original_object_id -> canonical_object_id]
        - canonical_objects: List of canonical object definitions
    """
    # Step 1: Collect unique objects with their metadata
    unique_objects = {}
    for ext in extractions:
        oid = ext['object_id']
        if oid not in unique_objects:
            unique_objects[oid] = {
                'id': oid,
                'label': ext['object_label'],
                'type': ext['object_type'],
                'example_questions': []
            }
        unique_objects[oid]['example_questions'].append(
            f"[{ext['question_id']}] {ext.get('question_text', '')}"
        )

    print(f"Unique raw objects: {len(unique_objects)}")

    # Step 2: LLM-based semantic resolution in batches
    object_list = list(unique_objects.values())
    all_clusters = []

    for i in range(0, len(object_list), batch_size):
        batch = object_list[i:i + batch_size]
        
        # Format with example questions to help LLM judge equivalence
        lines = []
        for obj in batch:
            examples = "; ".join(obj['example_questions'][:3])
            lines.append(
                f"- {obj['id']} ({obj['type']}): \"{obj['label']}\" "
                f"— Examples: {examples}"
            )
        objects_block = "\n".join(lines)

        prompt = ENTITY_RESOLUTION_USER.format(objects_block=objects_block)
        result = llm.call_json(ENTITY_RESOLUTION_SYSTEM, prompt)
        all_clusters.extend(result['clusters'])
        
        print(f"  Resolved batch {i//batch_size + 1}: "
              f"{len(batch)} objects -> {len(result['clusters'])} clusters")

    # Step 3: Build the mapping
    mapping = {}  # original_id -> canonical_id
    canonical_objects = []

    for cluster in all_clusters:
        canonical = {
            'id': cluster['canonical_id'],
            'label': cluster['canonical_label'],
            'type': cluster['canonical_type'],
            'source_ids': cluster['members']
        }
        canonical_objects.append(canonical)
        for member in cluster['members']:
            mapping[member] = cluster['canonical_id']

    # Verify completeness — every original object should be mapped
    unmapped = set(unique_objects.keys()) - set(mapping.keys())
    if unmapped:
        print(f"WARNING: {len(unmapped)} objects not mapped: {unmapped}")
        # Map unmapped to themselves
        for oid in unmapped:
            mapping[oid] = oid
            canonical_objects.append({
                'id': oid,
                'label': unique_objects[oid]['label'],
                'type': unique_objects[oid]['type'],
                'source_ids': [oid]
            })

    print(f"Canonical objects: {len(canonical_objects)} "
          f"(from {len(unique_objects)} raw)")
    return mapping, canonical_objects
```

---

## Part 4: Relationship Discovery (Pass 3)

This is where distant, non-obvious relationships get found. We work at the
**object level**, not the question level. If you have 150 canonical objects,
this is tractable. We use domain-aware batching to make it efficient.

```python
# relationship_discovery.py

from typing import List, Dict, Tuple
from itertools import combinations


# ── Prompts ─────────────────────────────────────────────

RELATIONSHIP_SYSTEM = """You are an expert in survey methodology, psychometrics, 
and social/behavioral science. Your task is to identify REAL relationships between 
measured constructs.

CRITICAL RULES:
- Only identify relationships that are well-established in the relevant literature 
  or are logically necessary.
- Do NOT invent relationships just because two constructs sound related.
- "No relationship" is a valid and common answer. Most pairs have NO relationship.
- Be specific about relationship types and direction.
- If a relationship is theoretically plausible but not well-established, mark it 
  as "hypothesized" rather than "established".

Valid relationship types:
- "causes": A is a direct cause of B (strong evidence)
- "contributes_to": A is one factor among many that influences B
- "is_component_of": A is a sub-dimension or facet of B
- "correlates_with": A and B co-vary but causal direction is unclear
- "moderates": A changes the strength/direction of another relationship
- "mediates": A transmits the effect of something else onto B
- "is_prerequisite_for": A must exist/occur before B can
- "contradicts": A and B are inversely related by nature
- "hypothesized": Plausible theoretical link, not yet established

Return ONLY valid JSON."""

RELATIONSHIP_WITHIN_DOMAIN = """Identify relationships between these constructs, 
which are all measured within related surveys.

Constructs:
{constructs_block}

For EACH pair that has a relationship, return it. Skip pairs with no relationship.

Return JSON:
{{
  "relationships": [
    {{
      "source": "construct_id_a",
      "target": "construct_id_b",
      "relation": "causes|contributes_to|is_component_of|correlates_with|moderates|mediates|is_prerequisite_for|contradicts|hypothesized",
      "direction": "a_to_b|b_to_a|bidirectional",
      "strength": "strong|moderate|weak",
      "evidence": "Brief theoretical or empirical basis",
      "established": true|false
    }},
    ...
  ]
}}

If NO relationships exist between any pair, return: {{"relationships": []}}"""

RELATIONSHIP_CROSS_DOMAIN = """These constructs come from DIFFERENT survey domains.
Most will have NO cross-domain relationship. Only identify relationships that are 
well-established in interdisciplinary research.

Domain A constructs:
{domain_a_block}

Domain B constructs:
{domain_b_block}

Be VERY conservative. Cross-domain relationships are rare and should have strong 
theoretical backing.

Return JSON (same format as before):
{{
  "relationships": [...]
}}"""

MODERATOR_IDENTIFICATION = """These are demographic/SES variables collected in surveys.
Identify which measured constructs they are likely to MODERATE (i.e., the demographic 
variable changes the relationship between other constructs).

Demographic variables:
{demographics_block}

Measured constructs:
{constructs_block}

Return JSON:
{{
  "moderations": [
    {{
      "moderator": "demo_variable_id",
      "relationship": ["construct_a", "construct_b"],
      "description": "How the demographic moderates this relationship",
      "evidence": "Brief basis"
    }},
    ...
  ]
}}"""


# ── Discovery Logic ─────────────────────────────────────

def format_constructs(constructs: List[Dict]) -> str:
    """Format constructs for prompts, including example questions."""
    lines = []
    for c in constructs:
        line = f"- {c['id']} ({c['type']}): \"{c['label']}\""
        if c.get('example_questions'):
            examples = "; ".join(c['example_questions'][:2])
            line += f" — e.g.: {examples}"
        lines.append(line)
    return "\n".join(lines)


def discover_relationships(
    llm: 'LLMClient',
    canonical_objects: List[Dict],
    domain_assignments: Dict[str, str] = None,
    batch_size: int = 30
) -> List[Dict]:
    """
    Discover relationships between canonical objects.
    
    Strategy:
    1. Within-domain: Check all pairs within each domain
    2. Cross-domain: Check pairs across domains (conservative)
    3. Moderators: Identify demographic moderating effects
    
    Args:
        llm: LLMClient instance
        canonical_objects: Output from entity resolution
        domain_assignments: Optional dict mapping object_id -> domain_name.
                           If None, all objects are treated as one domain.
        batch_size: Constructs per LLM call
    
    Returns:
        List of relationship dicts
    """
    all_relationships = []

    # Separate demographics from substantive constructs
    demographics = [c for c in canonical_objects if c['type'] == 'demographic']
    substantive = [c for c in canonical_objects if c['type'] != 'demographic']

    # ── Step 1: Within-domain relationships ─────────────
    if domain_assignments:
        domains = {}
        for obj in substantive:
            domain = domain_assignments.get(obj['id'], 'unassigned')
            domains.setdefault(domain, []).append(obj)
    else:
        domains = {'all': substantive}

    for domain_name, objects in domains.items():
        print(f"\n  Within-domain relationships: {domain_name} "
              f"({len(objects)} constructs)")
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            block = format_constructs(batch)
            prompt = RELATIONSHIP_WITHIN_DOMAIN.format(constructs_block=block)
            
            result = llm.call_json(RELATIONSHIP_SYSTEM, prompt)
            rels = result.get('relationships', [])
            
            for r in rels:
                r['domain_context'] = domain_name
                r['cross_domain'] = False
            
            all_relationships.extend(rels)
            print(f"    Batch {i//batch_size + 1}: found {len(rels)} relationships")

    # ── Step 2: Cross-domain relationships ──────────────
    if domain_assignments and len(domains) > 1:
        domain_names = list(domains.keys())
        for d1, d2 in combinations(domain_names, 2):
            print(f"\n  Cross-domain: {d1} × {d2}")
            
            block_a = format_constructs(domains[d1])
            block_b = format_constructs(domains[d2])
            
            prompt = RELATIONSHIP_CROSS_DOMAIN.format(
                domain_a_block=block_a,
                domain_b_block=block_b
            )
            
            result = llm.call_json(RELATIONSHIP_SYSTEM, prompt)
            rels = result.get('relationships', [])
            
            for r in rels:
                r['domain_context'] = f"{d1} × {d2}"
                r['cross_domain'] = True
            
            all_relationships.extend(rels)
            print(f"    Found {len(rels)} cross-domain relationships")

    # ── Step 3: Moderator identification ────────────────
    if demographics and substantive:
        print(f"\n  Identifying moderating effects "
              f"({len(demographics)} demographics × "
              f"{len(substantive)} constructs)")
        
        demo_block = format_constructs(demographics)
        
        # Batch the substantive constructs
        for i in range(0, len(substantive), batch_size):
            batch = substantive[i:i + batch_size]
            constr_block = format_constructs(batch)
            
            prompt = MODERATOR_IDENTIFICATION.format(
                demographics_block=demo_block,
                constructs_block=constr_block
            )
            
            result = llm.call_json(RELATIONSHIP_SYSTEM, prompt)
            
            for mod in result.get('moderations', []):
                all_relationships.append({
                    'source': mod['moderator'],
                    'target': f"{mod['relationship'][0]}↔{mod['relationship'][1]}",
                    'relation': 'moderates',
                    'direction': 'moderator',
                    'strength': 'variable',
                    'evidence': mod.get('evidence', ''),
                    'established': True,
                    'cross_domain': False,
                    'moderated_pair': mod['relationship']
                })
        
        print(f"    Found {sum(1 for r in all_relationships if r['relation'] == 'moderates')} moderating effects")

    print(f"\nTotal relationships discovered: {len(all_relationships)}")
    return all_relationships
```

---

## Part 5: Community Detection (Construct Discovery)

Now we build an intermediate graph from the objects and relationships, run 
community detection, and let the LLM name the discovered communities. These 
communities become your high-level **constructs**.

```python
# community_detection.py

import networkx as nx
from typing import List, Dict, Tuple, Set
from collections import defaultdict


# ── Prompts ─────────────────────────────────────────────

COMMUNITY_NAMING_SYSTEM = """You are an expert in survey methodology and 
psychometrics. Your task is to identify the higher-order CONSTRUCT that unifies 
a group of related measured objects.

A construct is an abstract concept like "Employee Engagement", "Customer Loyalty", 
"Workplace Safety Climate", "Health-Related Quality of Life", etc.

Rules:
- The name should be a standard term from the relevant field if one exists.
- Be specific enough to distinguish from other constructs.
- Identify the DOMAIN this construct belongs to.

Return ONLY valid JSON."""

COMMUNITY_NAMING_USER = """These measured objects have been identified as forming 
a coherent group (community) based on their inter-relationships.

Objects in this community:
{objects_block}

Example survey questions that measure these objects:
{questions_block}

Name and describe the higher-order construct that unifies these objects.

Return JSON:
{{
  "construct_id": "snake_case_name",
  "construct_label": "Human Readable Name",
  "domain": "The broad domain (e.g., HR, Customer Experience, Healthcare, etc.)",
  "definition": "1-2 sentence definition of this construct",
  "sub_dimensions": ["list", "of", "the", "objects", "that", "compose", "it"],
  "confidence": "high|medium|low"
}}"""


# ── Community Detection ─────────────────────────────────

def build_object_graph(
    canonical_objects: List[Dict],
    relationships: List[Dict]
) -> nx.Graph:
    """
    Build an undirected weighted graph of objects for community detection.
    
    Edge weights encode relationship strength:
    - is_component_of: 1.0 (strongest — these MUST be in the same community)
    - causes/contributes_to: 0.7
    - correlates_with: 0.5
    - moderates: 0.3
    - hypothesized: 0.2
    """
    G = nx.Graph()

    # Add all objects as nodes
    for obj in canonical_objects:
        G.add_node(obj['id'], **obj)

    # Relationship type -> weight
    weight_map = {
        'is_component_of': 1.0,
        'causes': 0.7,
        'contributes_to': 0.7,
        'mediates': 0.6,
        'is_prerequisite_for': 0.6,
        'correlates_with': 0.5,
        'contradicts': 0.4,
        'moderates': 0.3,
        'hypothesized': 0.2,
    }

    for rel in relationships:
        src = rel['source']
        tgt = rel['target']
        
        # Skip moderator edges for community detection (they connect 
        # demographics to relationships, not to objects)
        if rel['relation'] == 'moderates':
            continue
            
        if src in G and tgt in G:
            weight = weight_map.get(rel['relation'], 0.3)
            
            # Reduce weight for cross-domain relationships
            if rel.get('cross_domain'):
                weight *= 0.5
            
            # Add or update edge (take max weight if multiple relations)
            if G.has_edge(src, tgt):
                G[src][tgt]['weight'] = max(G[src][tgt]['weight'], weight)
                G[src][tgt]['relations'].append(rel['relation'])
            else:
                G.add_edge(src, tgt, weight=weight, relations=[rel['relation']])

    return G


def detect_communities(
    G: nx.Graph,
    resolution: float = 1.0,
    method: str = 'louvain'
) -> List[Set[str]]:
    """
    Run community detection on the object graph.
    
    Args:
        G: Object graph from build_object_graph()
        resolution: Controls granularity. Higher = more, smaller communities.
                    Start with 1.0, adjust based on results.
                    - 0.5: Broad constructs (fewer communities)
                    - 1.0: Default
                    - 2.0: Fine-grained sub-constructs
        method: 'louvain' (built into NetworkX) or 'leiden' (requires igraph)
    
    Returns:
        List of sets, each set containing object IDs in one community.
    """
    if method == 'leiden':
        try:
            import igraph as ig
            import leidenalg
            
            # Convert NetworkX to igraph
            ig_graph = ig.Graph.from_networkx(G)
            weights = ig_graph.es['weight'] if 'weight' in ig_graph.es.attributes() else None
            
            partition = leidenalg.find_partition(
                ig_graph,
                leidenalg.RBConfigurationVertexPartition,
                weights=weights,
                resolution_parameter=resolution
            )
            
            # Convert back to sets of NetworkX node IDs
            node_names = list(G.nodes())
            communities = []
            for community in partition:
                communities.append({node_names[i] for i in community})
            
            return communities
            
        except ImportError:
            print("leidenalg not installed, falling back to Louvain")
            method = 'louvain'

    if method == 'louvain':
        from networkx.algorithms.community import louvain_communities
        return louvain_communities(G, weight='weight', resolution=resolution)

    raise ValueError(f"Unknown method: {method}")


def name_communities(
    llm: 'LLMClient',
    communities: List[Set[str]],
    canonical_objects: List[Dict],
    extractions: List[Dict],
    object_mapping: Dict[str, str]
) -> List[Dict]:
    """
    Use LLM to name and describe each community (= construct).
    
    Args:
        communities: Output from detect_communities()
        canonical_objects: Canonical object list
        extractions: Original extractions (for example questions)
        object_mapping: original_object_id -> canonical_id
    
    Returns:
        List of construct definitions, one per community.
    """
    # Build lookup structures
    obj_lookup = {obj['id']: obj for obj in canonical_objects}
    
    # Map canonical objects to example questions
    obj_questions = defaultdict(list)
    for ext in extractions:
        canonical = object_mapping.get(ext['object_id'], ext['object_id'])
        obj_questions[canonical].append(
            f"[{ext['question_id']}] {ext.get('question_text', '')}"
        )

    constructs = []
    for i, community in enumerate(communities):
        print(f"  Naming community {i + 1}/{len(communities)} "
              f"({len(community)} objects)")
        
        # Get objects in this community
        objs = [obj_lookup[oid] for oid in community if oid in obj_lookup]
        if not objs:
            continue
        
        # Format objects
        obj_lines = []
        for obj in objs:
            obj_lines.append(f"- {obj['id']} ({obj['type']}): \"{obj['label']}\"")
        
        # Gather example questions
        q_lines = []
        for obj in objs:
            questions = obj_questions.get(obj['id'], [])[:3]
            for q in questions:
                q_lines.append(f"  {q}")
        
        prompt = COMMUNITY_NAMING_USER.format(
            objects_block="\n".join(obj_lines),
            questions_block="\n".join(q_lines[:15])  # Cap at 15 examples
        )
        
        result = llm.call_json(COMMUNITY_NAMING_SYSTEM, prompt)
        result['member_objects'] = list(community)
        result['community_index'] = i
        constructs.append(result)

    return constructs
```

---

## Part 6: Build the Final Knowledge Graph

Assemble everything into a single NetworkX DiGraph that serves as the ontology.

```python
# knowledge_graph.py

import networkx as nx
import json
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


class SurveyKnowledgeGraph:
    """
    The complete knowledge graph for multi-survey analysis.
    
    Node types:
    - domain: High-level survey domain
    - construct: Discovered construct (from community detection)
    - object: Canonical measured object
    - question: Individual survey question
    - survey: Source survey
    
    Edge types:
    - belongs_to_domain: construct -> domain
    - is_component_of: object -> construct
    - measures: question -> object
    - from_survey: question -> survey
    - causes / contributes_to / correlates_with / etc.: object -> object
    - moderates: demographic -> relationship
    """

    def __init__(self):
        self.G = nx.DiGraph()

    # ── Construction ────────────────────────────────────

    def build_from_pipeline(
        self,
        extractions: List[Dict],
        object_mapping: Dict[str, str],
        canonical_objects: List[Dict],
        relationships: List[Dict],
        constructs: List[Dict],
        surveys: Dict[str, List[Dict]]
    ):
        """
        Build the complete graph from pipeline outputs.
        """
        # 1. Add survey nodes
        for survey_name in surveys:
            self.G.add_node(
                f"survey:{survey_name}",
                type='survey',
                label=survey_name
            )

        # 2. Add domain nodes (from construct discovery)
        domains_seen = set()
        for construct in constructs:
            domain = construct.get('domain', 'Unknown')
            domain_id = f"domain:{domain.lower().replace(' ', '_')}"
            if domain_id not in domains_seen:
                self.G.add_node(domain_id, type='domain', label=domain)
                domains_seen.add(domain_id)

        # 3. Add construct nodes
        for construct in constructs:
            cid = f"construct:{construct['construct_id']}"
            domain_id = f"domain:{construct['domain'].lower().replace(' ', '_')}"
            
            self.G.add_node(cid,
                type='construct',
                label=construct['construct_label'],
                definition=construct.get('definition', ''),
                confidence=construct.get('confidence', 'medium')
            )
            self.G.add_edge(cid, domain_id, relation='belongs_to_domain')

        # 4. Add canonical object nodes and link to constructs
        obj_to_construct = {}
        for construct in constructs:
            for member_id in construct.get('member_objects', []):
                obj_to_construct[member_id] = construct['construct_id']

        for obj in canonical_objects:
            oid = f"object:{obj['id']}"
            self.G.add_node(oid,
                type='object',
                label=obj['label'],
                object_type=obj['type']
            )
            
            # Link to construct
            construct_id = obj_to_construct.get(obj['id'])
            if construct_id:
                self.G.add_edge(
                    oid, f"construct:{construct_id}",
                    relation='is_component_of'
                )

        # 5. Add question nodes and link to objects and surveys
        for ext in extractions:
            qid = f"question:{ext['question_id']}"
            canonical_obj = object_mapping.get(ext['object_id'], ext['object_id'])
            oid = f"object:{canonical_obj}"
            survey_id = f"survey:{ext['survey_name']}"

            self.G.add_node(qid,
                type='question',
                label=ext.get('question_text', ''),
                scale=ext.get('scale'),
                response_options=ext.get('response_options')
            )
            self.G.add_edge(qid, oid, relation='measures')
            self.G.add_edge(qid, survey_id, relation='from_survey')

        # 6. Add inter-object relationships
        for rel in relationships:
            src = f"object:{rel['source']}"
            tgt = f"object:{rel['target']}"
            
            if src in self.G and tgt in self.G:
                self.G.add_edge(src, tgt,
                    relation=rel['relation'],
                    strength=rel.get('strength', 'unknown'),
                    evidence=rel.get('evidence', ''),
                    established=rel.get('established', False),
                    cross_domain=rel.get('cross_domain', False)
                )

        print(f"Knowledge Graph built:")
        print(f"  Nodes: {self.G.number_of_nodes()}")
        print(f"  Edges: {self.G.number_of_edges()}")
        print(f"  Domains: {sum(1 for _, d in self.G.nodes(data=True) if d.get('type') == 'domain')}")
        print(f"  Constructs: {sum(1 for _, d in self.G.nodes(data=True) if d.get('type') == 'construct')}")
        print(f"  Objects: {sum(1 for _, d in self.G.nodes(data=True) if d.get('type') == 'object')}")
        print(f"  Questions: {sum(1 for _, d in self.G.nodes(data=True) if d.get('type') == 'question')}")

    # ── Querying ────────────────────────────────────────

    def get_question_context(self, question_id: str) -> Dict:
        """Get full context for a question: object, construct, domain, survey."""
        qid = question_id if question_id.startswith("question:") else f"question:{question_id}"
        
        if qid not in self.G:
            return {"error": f"Question {question_id} not found in graph"}

        context = {"question": dict(self.G.nodes[qid])}
        
        # Walk up: question -> object -> construct -> domain
        for _, obj_id, data in self.G.out_edges(qid, data=True):
            if data['relation'] == 'measures':
                context['object'] = {
                    'id': obj_id, **dict(self.G.nodes[obj_id])
                }
                # object -> construct
                for _, con_id, cdata in self.G.out_edges(obj_id, data=True):
                    if cdata['relation'] == 'is_component_of':
                        context['construct'] = {
                            'id': con_id, **dict(self.G.nodes[con_id])
                        }
                        # construct -> domain
                        for _, dom_id, ddata in self.G.out_edges(con_id, data=True):
                            if ddata['relation'] == 'belongs_to_domain':
                                context['domain'] = {
                                    'id': dom_id, **dict(self.G.nodes[dom_id])
                                }
            elif data['relation'] == 'from_survey':
                context['survey'] = {
                    'id': obj_id, **dict(self.G.nodes[obj_id])
                }

        return context

    def get_object_relationships(self, object_id: str) -> List[Dict]:
        """Get all relationships for an object."""
        oid = object_id if object_id.startswith("object:") else f"object:{object_id}"
        
        relationships = []
        # Outgoing
        for _, target, data in self.G.out_edges(oid, data=True):
            if self.G.nodes[target].get('type') == 'object':
                relationships.append({
                    'source': oid,
                    'target': target,
                    'direction': 'outgoing',
                    **data
                })
        # Incoming
        for source, _, data in self.G.in_edges(oid, data=True):
            if self.G.nodes[source].get('type') == 'object':
                relationships.append({
                    'source': source,
                    'target': oid,
                    'direction': 'incoming',
                    **data
                })
        return relationships

    def get_subgraph_for_questions(
        self, 
        question_ids: List[str],
        max_hops: int = 2
    ) -> nx.DiGraph:
        """
        Extract the relevant subgraph for a set of retrieved questions.
        Includes objects, constructs, domains, and relationships between them.
        """
        relevant_nodes = set()

        for qid in question_ids:
            qid_full = qid if qid.startswith("question:") else f"question:{qid}"
            if qid_full not in self.G:
                continue
            
            # BFS up to max_hops
            visited = {qid_full}
            frontier = {qid_full}
            for _ in range(max_hops):
                next_frontier = set()
                for node in frontier:
                    # Successors
                    for succ in self.G.successors(node):
                        if succ not in visited:
                            visited.add(succ)
                            next_frontier.add(succ)
                    # Predecessors
                    for pred in self.G.predecessors(node):
                        if pred not in visited:
                            visited.add(pred)
                            next_frontier.add(pred)
                frontier = next_frontier
            
            relevant_nodes.update(visited)

        return self.G.subgraph(relevant_nodes).copy()

    def are_comparable(self, q1_id: str, q2_id: str) -> Dict:
        """Determine if two questions can be meaningfully compared."""
        ctx1 = self.get_question_context(q1_id)
        ctx2 = self.get_question_context(q2_id)
        
        if 'error' in ctx1 or 'error' in ctx2:
            return {"comparable": "unknown", "reason": "Question not in graph"}
        
        d1 = ctx1.get('domain', {}).get('id')
        d2 = ctx2.get('domain', {}).get('id')
        o1 = ctx1.get('object', {}).get('id')
        o2 = ctx2.get('object', {}).get('id')
        
        # Same object
        if o1 == o2:
            return {
                "comparable": True,
                "type": "same_object",
                "reason": f"Both measure {ctx1['object']['label']}"
            }
        
        # Same domain, check for relationship
        if d1 == d2:
            rels = self._find_path(o1, o2, max_hops=3)
            if rels:
                return {
                    "comparable": True,
                    "type": "related_objects",
                    "reason": f"Same domain, connected via: {rels}"
                }
            return {
                "comparable": "weak",
                "type": "same_domain_unlinked",
                "reason": f"Same domain ({ctx1['domain']['label']}) "
                          f"but no direct relationship found"
            }
        
        # Different domains
        rels = self._find_path(o1, o2, max_hops=4)
        if rels:
            return {
                "comparable": True,
                "type": "cross_domain_linked",
                "reason": f"Cross-domain link: {rels}",
                "caution": True
            }
        
        return {
            "comparable": False,
            "type": "incomparable",
            "reason": (
                f"Different domains ({ctx1.get('domain', {}).get('label')} vs "
                f"{ctx2.get('domain', {}).get('label')}) with no known relationship"
            )
        }

    def _find_path(self, source: str, target: str, max_hops: int = 3) -> Optional[str]:
        """Find a path between two nodes, return description or None."""
        # Only traverse object-level relationships
        object_graph = nx.DiGraph()
        for u, v, data in self.G.edges(data=True):
            if (self.G.nodes.get(u, {}).get('type') == 'object' and 
                self.G.nodes.get(v, {}).get('type') == 'object'):
                object_graph.add_edge(u, v, **data)

        # Try directed
        try:
            path = nx.shortest_path(object_graph, source, target)
            if len(path) - 1 <= max_hops:
                return self._describe_path(path)
        except nx.NetworkXNoPath:
            pass
        
        # Try undirected
        undirected = object_graph.to_undirected()
        try:
            path = nx.shortest_path(undirected, source, target)
            if len(path) - 1 <= max_hops:
                return self._describe_path(path)
        except nx.NetworkXNoPath:
            pass
        
        return None

    def _describe_path(self, path: List[str]) -> str:
        """Describe a path in human-readable form."""
        parts = []
        for i in range(len(path) - 1):
            edge = self.G.edges.get((path[i], path[i + 1]), {})
            rel = edge.get('relation', '?')
            label_a = self.G.nodes[path[i]].get('label', path[i])
            label_b = self.G.nodes[path[i + 1]].get('label', path[i + 1])
            parts.append(f"{label_a} --[{rel}]--> {label_b}")
        return " → ".join(parts)

    # ── Enrichment for LLM Prompts ──────────────────────

    def enrich_for_llm(self, question_ids: List[str]) -> str:
        """
        Generate the structured context block that gets injected into the 
        LLM analysis prompt. This is the key integration point.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("KNOWLEDGE GRAPH CONTEXT")
        lines.append("Use this to constrain your analysis.")
        lines.append("=" * 60)

        # Group questions by domain
        domain_groups = defaultdict(list)
        contexts = {}
        for qid in question_ids:
            ctx = self.get_question_context(qid)
            contexts[qid] = ctx
            domain = ctx.get('domain', {}).get('label', 'Unknown')
            domain_groups[domain].append(qid)

        # Section 1: Domain groupings
        lines.append("\n--- DOMAIN GROUPINGS ---")
        for domain, qids in domain_groups.items():
            lines.append(f"\n[{domain}]")
            for qid in qids:
                ctx = contexts[qid]
                obj_label = ctx.get('object', {}).get('label', '?')
                construct = ctx.get('construct', {}).get('label', '?')
                survey = ctx.get('survey', {}).get('label', '?')
                scale = ctx.get('question', {}).get('scale', '?')
                lines.append(
                    f"  {qid}: measures '{obj_label}' "
                    f"(construct: {construct}) | survey: {survey} | scale: {scale}"
                )

        # Section 2: Valid relationships
        lines.append("\n--- RELATIONSHIPS ---")
        compared = set()
        for i, q1 in enumerate(question_ids):
            for q2 in question_ids[i + 1:]:
                key = tuple(sorted([q1, q2]))
                if key in compared:
                    continue
                compared.add(key)
                
                comp = self.are_comparable(q1, q2)
                if comp['comparable'] is True:
                    symbol = "✓" if not comp.get('caution') else "⚠"
                    lines.append(f"  {symbol} {q1} ↔ {q2}: {comp['reason']}")
                elif comp['comparable'] == 'weak':
                    lines.append(f"  ~ {q1} ↔ {q2}: {comp['reason']}")
                else:
                    lines.append(f"  ✗ {q1} ↔ {q2}: {comp['reason']}")

        # Section 3: Rules
        lines.append("\n--- ANALYSIS CONSTRAINTS ---")
        lines.append("1. Only draw conclusions between items marked ✓ or ⚠")
        lines.append("2. Items marked ✗ are UNRELATED. Shared patterns are coincidental.")
        lines.append("3. Items marked ⚠ are cross-domain. Interpret with caution.")
        lines.append("4. Check scale types before comparing numeric values.")
        lines.append("5. Always attribute data to its source survey.")
        lines.append("6. State explicitly when a relationship is hypothesized vs established.")
        lines.append("=" * 60)

        return "\n".join(lines)

    # ── Serialization ───────────────────────────────────

    def save(self, filepath: str):
        """Save graph to JSON for persistence."""
        data = nx.node_link_data(self.G)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, filepath: str):
        """Load graph from JSON."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.G = nx.node_link_graph(data, directed=True)
```

---

## Part 7: Think-on-Graph (ToG) Reasoning

This implements the ToG paradigm adapted for survey analysis. When a user asks
a complex analytical question, the LLM doesn't just get a flat context dump —
it **actively explores the knowledge graph** step by step, using beam search to
find the most relevant reasoning paths before generating its answer.

This is particularly useful for questions like:
- "What drives the decline in satisfaction among younger demographics?"
- "Are there common factors across surveys that explain low scores?"
- "How might employee engagement relate to customer outcomes?"

```python
# think_on_graph.py

import networkx as nx
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import json


@dataclass
class ReasoningPath:
    """A single reasoning path through the knowledge graph."""
    nodes: List[str] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)
    score: float = 0.0
    description: str = ""

    def to_text(self, G: nx.DiGraph) -> str:
        """Serialize path to text for LLM consumption."""
        if not self.nodes:
            return "(empty path)"
        parts = []
        for i, node in enumerate(self.nodes):
            node_data = G.nodes.get(node, {})
            label = node_data.get('label', node)
            ntype = node_data.get('type', '?')
            parts.append(f"[{ntype}] {label}")
            if i < len(self.edges):
                rel = self.edges[i].get('relation', '?')
                parts.append(f"  --({rel})-->")
        return "\n    ".join(parts)


class ThinkOnGraph:
    """
    Think-on-Graph reasoning adapted for survey knowledge graphs.
    
    The LLM acts as an agent that:
    1. Identifies starting entities from the user query
    2. Explores neighboring nodes/edges in the KG (beam search)
    3. Scores and prunes reasoning paths
    4. Evaluates if enough evidence has been gathered
    5. Generates a grounded answer using the discovered paths
    
    Reference: Sun et al., "Think-on-Graph" (ICLR 2024)
    """

    def __init__(
        self,
        kg: 'SurveyKnowledgeGraph',
        llm: 'LLMClient',
        beam_width: int = 3,
        max_depth: int = 4,
        min_paths: int = 2
    ):
        """
        Args:
            kg: The survey knowledge graph
            llm: LLM client for reasoning
            beam_width: Number of paths to maintain at each step (N in paper)
            max_depth: Maximum reasoning depth (D_max in paper)
            min_paths: Minimum paths before attempting to answer
        """
        self.kg = kg
        self.llm = llm
        self.beam_width = beam_width
        self.max_depth = max_depth
        self.min_paths = min_paths

    def reason(
        self, 
        query: str, 
        retrieved_questions: List[str] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Main reasoning loop.
        
        Args:
            query: The user's analytical question
            retrieved_questions: Optional list of question IDs from 
                                 semantic search
            verbose: Print reasoning steps
        
        Returns:
            Dict with 'answer', 'reasoning_paths', 'evidence', 'confidence'
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"ToG REASONING: {query}")
            print(f"{'='*60}")

        # ── Step 1: Identify starting entities ──────────
        start_entities = self._identify_start_entities(
            query, retrieved_questions
        )
        
        if verbose:
            print(f"\nStarting entities: {start_entities}")

        # ── Step 2: Initialize paths ────────────────────
        paths = []
        for entity in start_entities:
            paths.append(ReasoningPath(
                nodes=[entity],
                edges=[],
                score=1.0
            ))

        # ── Step 3: Iterative exploration + reasoning ───
        for depth in range(self.max_depth):
            if verbose:
                print(f"\n--- Depth {depth + 1}/{self.max_depth} ---")
                print(f"Active paths: {len(paths)}")

            # Explore: expand each path with neighboring edges
            candidate_paths = self._explore(paths, verbose)

            if not candidate_paths:
                if verbose:
                    print("No further expansion possible.")
                break

            # Reason: score and prune candidates
            paths = self._prune(query, candidate_paths, verbose)

            # Evaluate: check if we have enough to answer
            if depth >= 1:  # At least 2 hops before evaluating
                sufficient = self._evaluate_sufficiency(query, paths, verbose)
                if sufficient:
                    if verbose:
                        print("\nSufficient evidence gathered.")
                    break

        # ── Step 4: Generate grounded answer ────────────
        answer = self._generate_answer(query, paths, retrieved_questions, verbose)

        return answer

    # ── Internal Steps ──────────────────────────────────

    def _identify_start_entities(
        self,
        query: str,
        retrieved_questions: List[str] = None
    ) -> List[str]:
        """
        Step 1: Identify which KG nodes are relevant starting points.
        Uses both the query and any retrieved questions.
        """
        # Collect candidate nodes
        candidates = []
        
        # From retrieved questions: get their objects and constructs
        if retrieved_questions:
            for qid in retrieved_questions:
                ctx = self.kg.get_question_context(qid)
                if 'object' in ctx:
                    candidates.append(ctx['object']['id'])
                if 'construct' in ctx:
                    candidates.append(ctx['construct']['id'])

        # Also: ask LLM to identify entities from the query text
        all_objects = [
            {"id": n, "label": d.get('label', n), "type": d.get('type', '?')}
            for n, d in self.kg.G.nodes(data=True)
            if d.get('type') in ('object', 'construct')
        ]
        
        # Format a manageable subset for the LLM
        obj_lines = [f"- {o['id']}: {o['label']} ({o['type']})" 
                     for o in all_objects[:200]]  # Cap for context length
        
        result = self.llm.call_json(
            system_prompt="""You identify which entities in a knowledge graph 
            are relevant to a user query about survey data. Return the IDs 
            of the most relevant entities (max 5). Return ONLY valid JSON.""",
            user_prompt=f"""Query: {query}

Available entities:
{chr(10).join(obj_lines)}

Return JSON: {{"entities": ["entity_id_1", "entity_id_2", ...]}}"""
        )

        llm_entities = result.get('entities', [])
        
        # Merge and deduplicate, prioritizing LLM-identified ones
        all_starts = list(dict.fromkeys(llm_entities + candidates))
        
        # Validate they exist in the graph
        valid = [e for e in all_starts if e in self.kg.G]
        
        return valid[:self.beam_width * 2]  # Don't start with too many

    def _explore(
        self,
        paths: List[ReasoningPath],
        verbose: bool = False
    ) -> List[ReasoningPath]:
        """
        Step 2a: Expand each active path by one hop.
        For each path's current endpoint, find all neighboring 
        nodes via object-level relationships.
        """
        expanded = []

        for path in paths:
            current_node = path.nodes[-1]
            
            # Get neighbors (both directions)
            neighbors = []
            
            # Outgoing edges
            for _, target, data in self.kg.G.out_edges(current_node, data=True):
                target_type = self.kg.G.nodes.get(target, {}).get('type', '')
                # Only traverse object and construct level edges
                if target_type in ('object', 'construct') and target not in path.nodes:
                    neighbors.append((target, data, 'outgoing'))
            
            # Incoming edges
            for source, _, data in self.kg.G.in_edges(current_node, data=True):
                source_type = self.kg.G.nodes.get(source, {}).get('type', '')
                if source_type in ('object', 'construct') and source not in path.nodes:
                    neighbors.append((source, data, 'incoming'))

            for neighbor, edge_data, direction in neighbors:
                new_path = ReasoningPath(
                    nodes=path.nodes + [neighbor],
                    edges=path.edges + [dict(edge_data)],
                    score=path.score  # Will be updated in prune step
                )
                expanded.append(new_path)

            if verbose and neighbors:
                print(f"  Expanded '{current_node}': "
                      f"{len(neighbors)} new branches")

        return expanded

    def _prune(
        self,
        query: str,
        candidate_paths: List[ReasoningPath],
        verbose: bool = False
    ) -> List[ReasoningPath]:
        """
        Step 2b: Use LLM to score paths by relevance to query, 
        keep top beam_width paths.
        """
        if len(candidate_paths) <= self.beam_width:
            return candidate_paths

        # Format paths for LLM evaluation
        path_descriptions = []
        for i, path in enumerate(candidate_paths):
            desc = path.to_text(self.kg.G)
            last_edge = path.edges[-1] if path.edges else {}
            evidence = last_edge.get('evidence', 'none')
            path_descriptions.append(
                f"Path {i}: {desc}\n"
                f"    (evidence: {evidence})"
            )

        result = self.llm.call_json(
            system_prompt="""You evaluate reasoning paths in a knowledge graph 
for their relevance to answering a survey analysis query. Score each path 
0.0-1.0 for relevance. Return ONLY valid JSON.""",
            user_prompt=f"""Query: {query}

Candidate reasoning paths:
{chr(10).join(path_descriptions)}

Score each path's relevance to the query (0.0 = irrelevant, 1.0 = essential).

Return JSON: {{"scores": [0.0, 0.8, ...]}}  (one score per path, same order)"""
        )

        scores = result.get('scores', [0.5] * len(candidate_paths))

        # Assign scores and sort
        for path, score in zip(candidate_paths, scores):
            path.score = score

        candidate_paths.sort(key=lambda p: p.score, reverse=True)
        pruned = candidate_paths[:self.beam_width]

        if verbose:
            print(f"  Pruned {len(candidate_paths)} candidates "
                  f"to top {len(pruned)}")
            for p in pruned:
                last_node = p.nodes[-1]
                label = self.kg.G.nodes.get(last_node, {}).get('label', last_node)
                print(f"    Score {p.score:.2f}: ...→ {label}")

        return pruned

    def _evaluate_sufficiency(
        self,
        query: str,
        paths: List[ReasoningPath],
        verbose: bool = False
    ) -> bool:
        """
        Step 3: Ask LLM if the discovered paths provide enough 
        evidence to answer the query.
        """
        if len(paths) < self.min_paths:
            return False

        path_texts = []
        for i, path in enumerate(paths):
            path_texts.append(f"Path {i} (score {path.score:.2f}):\n"
                            f"    {path.to_text(self.kg.G)}")

        result = self.llm.call_json(
            system_prompt="""You evaluate whether gathered evidence from a 
knowledge graph is sufficient to answer an analytical query about survey data. 
Return ONLY valid JSON.""",
            user_prompt=f"""Query: {query}

Discovered reasoning paths:
{chr(10).join(path_texts)}

Is this evidence sufficient to provide a well-grounded answer?

Return JSON: 
{{
  "sufficient": true|false, 
  "reasoning": "Why or why not",
  "missing": "What additional information would help (if insufficient)"
}}"""
        )

        sufficient = result.get('sufficient', False)
        
        if verbose:
            status = "SUFFICIENT" if sufficient else "INSUFFICIENT"
            print(f"  Evidence evaluation: {status}")
            print(f"    Reasoning: {result.get('reasoning', '?')}")
            if not sufficient:
                print(f"    Missing: {result.get('missing', '?')}")

        return sufficient

    def _generate_answer(
        self,
        query: str,
        paths: List[ReasoningPath],
        retrieved_questions: List[str] = None,
        verbose: bool = False
    ) -> Dict:
        """
        Step 4: Generate the final answer grounded in reasoning paths.
        """
        # Compile evidence from paths
        path_texts = []
        for i, path in enumerate(paths):
            path_texts.append(
                f"Path {i} (relevance: {path.score:.2f}):\n"
                f"    {path.to_text(self.kg.G)}"
            )

        # Also include the enrichment context for any retrieved questions
        enrichment = ""
        if retrieved_questions:
            enrichment = self.kg.enrich_for_llm(retrieved_questions)

        answer_result = self.llm.call_json(
            system_prompt="""You are an expert survey analyst. Generate an 
analytical answer GROUNDED in the knowledge graph evidence provided. 

RULES:
- Only make claims supported by the reasoning paths.
- Distinguish between established relationships and hypothesized ones.
- If evidence is insufficient, say so explicitly.
- Cite which paths support each claim.
- Note when comparisons cross domain boundaries.

Return ONLY valid JSON.""",
            user_prompt=f"""Query: {query}

REASONING PATHS (from knowledge graph exploration):
{chr(10).join(path_texts)}

{enrichment if enrichment else ""}

Generate a grounded analytical response.

Return JSON:
{{
  "answer": "Your analytical response as a coherent paragraph/paragraphs",
  "key_findings": [
    {{
      "finding": "Specific finding",
      "supporting_paths": [0, 2],
      "confidence": "high|medium|low",
      "established": true|false
    }},
    ...
  ],
  "caveats": ["Any limitations or cautions"],
  "suggested_follow_up": ["Questions worth investigating further"]
}}"""
        )

        # Attach the raw paths for traceability
        answer_result['reasoning_paths'] = [
            {
                'nodes': p.nodes,
                'edges': p.edges,
                'score': p.score,
                'text': p.to_text(self.kg.G)
            }
            for p in paths
        ]

        if verbose:
            print(f"\n{'='*60}")
            print("ANSWER:")
            print(answer_result.get('answer', 'No answer generated'))
            print(f"\nKey findings: {len(answer_result.get('key_findings', []))}")
            print(f"Caveats: {len(answer_result.get('caveats', []))}")
            print(f"Reasoning paths used: {len(paths)}")
            print(f"{'='*60}")

        return answer_result
```

---

## Part 8: Putting It All Together

The main orchestration script that runs the full pipeline.

```python
# main.py

import json
from llm_client import LLMClient
from object_extraction import extract_all_surveys
from entity_resolution import resolve_entities
from relationship_discovery import discover_relationships
from community_detection import (
    build_object_graph, detect_communities, name_communities
)
from knowledge_graph import SurveyKnowledgeGraph
from think_on_graph import ThinkOnGraph


def run_pipeline(
    surveys: dict,
    llm: LLMClient,
    resolution: float = 1.0,
    save_intermediates: bool = True,
    output_dir: str = "./kg_output"
):
    """
    End-to-end pipeline: raw surveys → knowledge graph → ready for reasoning.
    
    Args:
        surveys: Dict mapping survey_name -> list of question dicts.
                 Each question dict needs at minimum: {'id': str, 'text': str}
                 Optional keys: 'scale', 'response_options', 'section'
        llm: Configured LLMClient
        resolution: Community detection resolution (0.5=broad, 2.0=fine)
        save_intermediates: Save each step's output to disk
        output_dir: Where to save outputs
    
    Returns:
        Tuple of (SurveyKnowledgeGraph, ThinkOnGraph)
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    # ── Step 1: Extract objects ─────────────────────────
    print("\n" + "="*60)
    print("STEP 1: OBJECT EXTRACTION")
    print("="*60)
    
    extractions = extract_all_surveys(llm, surveys, batch_size=25)
    
    if save_intermediates:
        with open(f"{output_dir}/01_extractions.json", 'w') as f:
            json.dump(extractions, f, indent=2, default=str)

    # ── Step 2: Entity resolution ───────────────────────
    print("\n" + "="*60)
    print("STEP 2: ENTITY RESOLUTION")
    print("="*60)
    
    object_mapping, canonical_objects = resolve_entities(llm, extractions)
    
    if save_intermediates:
        with open(f"{output_dir}/02_mapping.json", 'w') as f:
            json.dump(object_mapping, f, indent=2)
        with open(f"{output_dir}/02_canonical_objects.json", 'w') as f:
            json.dump(canonical_objects, f, indent=2, default=str)

    # ── Step 3: Relationship discovery ──────────────────
    print("\n" + "="*60)
    print("STEP 3: RELATIONSHIP DISCOVERY")
    print("="*60)
    
    # No domain assignments yet — discover_relationships will treat as one pool
    # After community detection, you could re-run with domain info for refinement
    relationships = discover_relationships(
        llm, canonical_objects, domain_assignments=None, batch_size=30
    )
    
    if save_intermediates:
        with open(f"{output_dir}/03_relationships.json", 'w') as f:
            json.dump(relationships, f, indent=2, default=str)

    # ── Step 4: Community detection ─────────────────────
    print("\n" + "="*60)
    print("STEP 4: COMMUNITY DETECTION")
    print("="*60)
    
    object_graph = build_object_graph(canonical_objects, relationships)
    print(f"Object graph: {object_graph.number_of_nodes()} nodes, "
          f"{object_graph.number_of_edges()} edges")
    
    communities = detect_communities(
        object_graph, resolution=resolution, method='louvain'
    )
    print(f"Detected {len(communities)} communities")
    
    # Name the communities
    constructs = name_communities(
        llm, communities, canonical_objects, extractions, object_mapping
    )
    
    if save_intermediates:
        with open(f"{output_dir}/04_constructs.json", 'w') as f:
            json.dump(constructs, f, indent=2, default=str)

    # ── Step 5: Build knowledge graph ───────────────────
    print("\n" + "="*60)
    print("STEP 5: BUILD KNOWLEDGE GRAPH")
    print("="*60)
    
    kg = SurveyKnowledgeGraph()
    kg.build_from_pipeline(
        extractions=extractions,
        object_mapping=object_mapping,
        canonical_objects=canonical_objects,
        relationships=relationships,
        constructs=constructs,
        surveys=surveys
    )
    
    kg.save(f"{output_dir}/knowledge_graph.json")
    print(f"\nKnowledge graph saved to {output_dir}/knowledge_graph.json")

    # ── Step 6: Initialize Think-on-Graph ───────────────
    tog = ThinkOnGraph(
        kg=kg,
        llm=llm,
        beam_width=3,
        max_depth=4,
        min_paths=2
    )

    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"\nUsage:")
    print(f"  # Enrich retrieved questions for LLM analysis:")
    print(f"  context = kg.enrich_for_llm(['Q1', 'Q2', 'Q3'])")
    print(f"")
    print(f"  # Complex reasoning with Think-on-Graph:")
    print(f"  result = tog.reason(")
    print(f"      'What factors drive satisfaction among younger users?',")
    print(f"      retrieved_questions=['CX_Q1', 'CX_Q3', 'HR_Q1']")
    print(f"  )")
    
    return kg, tog


# ── Example Usage ───────────────────────────────────────

if __name__ == "__main__":
    # Example: Define your surveys as dicts
    surveys = {
        "2024 Customer Experience Survey": [
            {"id": "CX_Q1", "text": "Rate your overall satisfaction with our service",
             "scale": "likert_1_5"},
            {"id": "CX_Q2", "text": "How likely are you to recommend us to a friend?",
             "scale": "nps_0_10"},
            {"id": "CX_Q3", "text": "Rate your satisfaction with delivery speed",
             "scale": "likert_1_5"},
            # ... 77 more questions
        ],
        "2024 Employee Pulse": [
            {"id": "HR_Q1", "text": "I feel motivated to go beyond what is required",
             "scale": "likert_1_7"},
            {"id": "HR_Q2", "text": "I trust my direct manager",
             "scale": "likert_1_7"},
            {"id": "HR_Q3", "text": "I have the resources I need to do my job well",
             "scale": "likert_1_7"},
            # ... 77 more questions
            {"id": "HR_Q78", "text": "What is your highest level of education?",
             "scale": "categorical",
             "response_options": "High school, Bachelor's, Master's, Doctorate"},
            {"id": "HR_Q79", "text": "What is your annual household income range?",
             "scale": "categorical",
             "response_options": "<30K, 30-60K, 60-100K, 100K+"},
        ],
        # ... more surveys
    }

    # Configure LLM
    llm = LLMClient(model="claude-sonnet-4-20250514")

    # Run full pipeline
    kg, tog = run_pipeline(
        surveys=surveys,
        llm=llm,
        resolution=1.0,
        save_intermediates=True,
        output_dir="./kg_output"
    )

    # ── Example 1: Simple enrichment ────────────────────
    # Semantic search returned these questions from different surveys
    retrieved = ["CX_Q1", "CX_Q3", "HR_Q1", "HR_Q2"]
    context = kg.enrich_for_llm(retrieved)
    print(context)
    # → Pass this as prefix to your analysis LLM prompt

    # ── Example 2: Think-on-Graph reasoning ─────────────
    result = tog.reason(
        query="What factors might explain declining satisfaction "
              "scores among younger demographics?",
        retrieved_questions=["CX_Q1", "CX_Q3"],
        verbose=True
    )
    print("\nAnswer:", result['answer'])
    print("\nKey findings:")
    for f in result.get('key_findings', []):
        print(f"  [{f['confidence']}] {f['finding']}")

    # ── Example 3: Cross-survey question ────────────────
    result = tog.reason(
        query="Is there evidence that employee engagement "
              "affects customer-facing outcomes in our data?",
        verbose=True
    )
```

---

## Summary of Pipeline Flow

```
INPUT: Raw surveys (2K+ questions as dicts)
  │
  ▼
STEP 1: Object Extraction  [~80 LLM calls]
  │  For each question: "What object does this measure?"
  │  Output: List of (question_id, object_id, object_type)
  │
  ▼
STEP 2: Entity Resolution  [~15 LLM calls]
  │  Cluster synonymous objects into canonical entities
  │  Output: Mapping (raw_object → canonical_object)
  │
  ▼
STEP 3: Relationship Discovery  [~40 LLM calls]
  │  Between canonical objects: what relates to what?
  │  Within-domain, cross-domain, and moderator identification
  │  Output: List of typed, directed relationships
  │
  ▼
STEP 4: Community Detection  [~5 LLM calls for naming]
  │  Louvain/Leiden on the object graph
  │  LLM names each community as a high-level construct
  │  Output: Constructs with member objects and domain labels
  │
  ▼
STEP 5: Knowledge Graph Assembly  [0 LLM calls]
  │  Assemble all layers into a single NetworkX DiGraph
  │  Save to JSON for persistence
  │  Output: SurveyKnowledgeGraph instance
  │
  ▼
READY FOR USE:
  ├─ kg.enrich_for_llm(question_ids)     → Prompt context injection
  ├─ kg.are_comparable(q1, q2)           → Pairwise comparability check
  ├─ kg.get_subgraph_for_questions(ids)  → Relevant subgraph extraction
  └─ tog.reason(query, questions)        → Full Think-on-Graph reasoning
```

Estimated total LLM calls for 2K questions: **~140 calls** (vs ~2M for pairwise).

---

## Notes for Implementation

1. **Persist intermediates.** Each step saves its output. If entity resolution
   needs tweaking, you don't re-run extraction. The pipeline is resumable.

2. **Human review checkpoint.** After Step 4, review the constructs and 
   relationships before building the final graph. This is where domain 
   expertise matters most. The LLM proposes, you validate.

3. **Resolution tuning.** Run community detection at multiple resolutions
   (0.5, 1.0, 1.5, 2.0) and compare the resulting constructs. Pick the
   granularity that matches your analytical needs.

4. **Incremental updates.** When new surveys arrive, run Steps 1-2 for the 
   new questions only, then re-run Steps 3-5 on the full set. The graph 
   evolves without full reconstruction.

5. **The LLMClient is a placeholder.** Implement `_call()` with your provider.
   The pipeline works with any model that can return JSON reliably.

6. **Think-on-Graph costs.** Each ToG reasoning call makes ~8-15 LLM calls
   (entity identification + depth × (explore + prune + evaluate) + generation).
   This is appropriate for complex analytical queries, not for every user 
   question. Use simple `enrich_for_llm()` for routine analysis and reserve 
   ToG for deep reasoning tasks.
