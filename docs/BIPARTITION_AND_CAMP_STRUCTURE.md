# Bipartition and Camp Structure

## The Problem

The SES bridge network is a signed graph: 71 constructs connected by 984 edges, each carrying a Goodman-Kruskal γ that is either positive (SES co-elevates both attitudes) or negative (SES pushes them in opposite directions).  The sign split is nearly even — 52% positive, 48% negative.

Without structure, this is an undifferentiated cloud of 984 numbers.  An agent asked "why do these two attitudes co-vary?" can report the γ value but cannot explain *why* it is positive or negative.  The answer, for 99.4% of pairs, reduces to a single bit: whether the two constructs are on the same or opposite side of a dominant sociodemographic axis.  That bit is the camp assignment.  Without it, every explanation is ad hoc.  With it, explanations generalise.

### Three concrete failure modes without bipartition

1. **Sign of a path result is unpredictable to the caller.**  `find_path("CIE|scientific_curiosity", "REL|personal_religiosity")` returns `signal_chain = -0.0042`.  The sign is negative — but nothing in the output tells the caller *why*.  Camp membership answers this: they are in opposite camps, so SES pushes them in opposite directions.

2. **Dijkstra routes on |γ| and silently crosses camp boundaries.**  Two paths between the same endpoints can have opposite signs but similar strength.  Dijkstra picks the stronger one without regard to sign.  Without camp metadata, the caller cannot predict whether the returned path will indicate co-elevation or counter-variation.

3. **The 6% frustrated triangles are invisible.**  These are the genuinely complex nodes — constructs whose SES profile straddles both camps.  Bridge paths through them carry higher interpretive uncertainty.  Without bipartition, there is no way to identify or flag them.

---

## The Structure: What Bipartition Is

Harary and Cartwright's structural balance theorem (1956) states that a signed graph with perfect balance can be partitioned into exactly two sets where:

- All within-set edges are positive (same camp → SES co-elevates)
- All between-set edges are negative (opposite camps → SES counter-varies)

This network is 94% balanced (94% of its 8,283 triangles satisfy the sign-product rule).  The bipartition is therefore empirically real, not an artifact.  The two camps correspond to the two halves of the dominant principal axis (PC1, 78% of fingerprint variance):

| Camp | Label | Elevated by | Examples |
|------|-------|-------------|----------|
| +1 | **Cosmopolitan** | Education, urbanisation | Scientific curiosity, digital capital, political engagement, cultural consumption |
| -1 | **Tradition** | Rural residence, older age | Religiosity, traditional gender roles, community attachment, fatalism |

The bipartition is the *discrete shadow* of a continuous underlying geometry.  PC1 of the 4D fingerprint space is nearly collinear (effective dimensionality ≈ 1.5D), and the sign of a construct's PC1 projection determines its camp.  The fingerprint dot product `f_A · f_B` predicts bridge sign at 99.4% accuracy because two constructs whose SES profiles point in the same 4D direction are co-elevated by the same sociodemographic position (γ > 0), while constructs pointing in opposite directions are counter-varied (γ < 0).

---

## Method: Signed Laplacian and Fiedler Vector

### Mathematical foundation

For an unsigned graph with adjacency matrix **A** (non-negative weights), the graph Laplacian is:

```
L = D - A       where D_ii = Σ_j A_ij
```

Its quadratic form measures disagreement across edges:

```
x^T L x  =  Σ_{(i,j)∈E}  A_ij (x_i - x_j)²
```

This is always ≥ 0.  The minimum is 0, achieved by the constant vector **1** (assign everyone the same value — zero disagreement).  The second-smallest eigenvector, the **Fiedler vector**, gives the smoothest non-trivial partition: the assignment of real numbers to nodes that changes least across edges, subject to orthogonality to the trivial solution.

### Extension to signed graphs

The **balanced (signed) Laplacian** replaces A with the signed adjacency A_s (where entries can be negative) and D with D_{|A|} (degree computed from absolute weights):

```
L_s = D_{|A|} - A_s       where D_ii = Σ_j |A_ij|
```

The quadratic form becomes:

```
x^T L_s x  =  Σ_{(i,j)∈E}  |A_ij| (x_i - sign(A_ij) · x_j)²
```

For a **positive edge** (γ > 0, sign = +1):  the term is `|γ| (x_i - x_j)²`, minimised when x_i = x_j.  Positive edges want endpoints to agree.

For a **negative edge** (γ < 0, sign = -1):  the term is `|γ| (x_i + x_j)²`, minimised when x_i = -x_j.  Negative edges want endpoints to disagree.

The Fiedler vector of L_s solves:

```
minimise  Σ_{(i,j)}  |γ_ij| (x_i - sign(γ_ij) · x_j)²
subject to  |x| = 1
```

The sign of each component gives the camp assignment.  The magnitude gives the confidence — how far the node sits from the bipartition boundary.

### Eigenvalue interpretation

- λ₁ = 0:  perfectly balanced graph.  A bipartition exists with zero frustration.
- λ₁ > 0 (small):  nearly balanced.  The Fiedler vector gives the best approximate bipartition, with frustrated edges contributing residual cost.
- λ₁ large:  heavily frustrated.  No meaningful bipartition exists.

For this network (94% balance), λ₁ is small and positive.  The bipartition is meaningful but not perfect — the 6% frustrated triangles are the residual.

### Fiedler magnitude as confidence

A node deep inside one camp — all positive edges to same-camp nodes, all negative edges to opposite-camp nodes — receives a large |fiedler_i|.  A node straddling the boundary — some edges pulling it each way — receives a small |fiedler_i|.

Because this network has near-zero modularity (Q = 0.089), most nodes sit close to the boundary.  Fiedler confidence values are therefore typically low (observed: ~0.003).  This is not a failure — it accurately reflects the continuous-gradient structure of the graph.  There are not two sharply separated clusters; there is a single axis with a zero-crossing, and the bipartition discretises it at that crossing.

### Orientation

The eigenvector is defined only up to sign: v and -v are both valid Fiedler vectors.  The labels +1 and -1 are arbitrary until pinned to a semantic reference.

We orient by comparing the median ρ_escol of nodes in each candidate camp.  The camp with higher median education correlation gets +1 (cosmopolitan).  This choice is:

- Data-driven (not hardcoded to a specific construct)
- Robust to outliers (median, not mean, with n=71)
- Semantically grounded (education is the dimension that most cleanly separates the two halves of PC1)
- Idempotent (running it twice gives the same result)

---

## Why This Method Over Alternatives

### PC1 of fingerprint vectors

The most obvious alternative: project each construct's 4D fingerprint onto the first principal component; sign of projection = camp.  This gives a nearly identical result (the topology report confirms it), and is simpler.

**Why the Laplacian is superior:**  PC1 operates on node attributes (fingerprints).  The Laplacian operates on edge structure (bridge γ values).  These are related — `sign(f_A · f_B) ≈ sign(γ_AB)` at 99.4% — but not identical.  The 0.6% of cases where the fingerprint inner product gets the sign wrong are exactly the cases where the Laplacian gives a different, more trustworthy answer.  The Laplacian bipartition is authoritative over the bridge data; the PC1 bipartition is a prediction about what the bridges should look like.

### Greedy label propagation

Start with random labels, flip nodes to reduce frustrated edges, iterate.  Fast and intuitive.

**Why inferior:**  Non-deterministic.  Can get stuck in local minima.  For a dense graph (23% edge density), the landscape has many local optima.  The Laplacian gives the global optimum in one eigendecomposition.

### Spectral clustering (unsigned)

Ignore signs, cluster by connectivity.

**Why inapplicable:**  The partition exists only because of signs.  The graph has near-zero modularity — unsigned spectral clustering finds no meaningful partition.

### SDP relaxation (Goemans-Williamson)

The theoretically optimal MAX-CUT relaxation.

**Why overkill:**  For 71 nodes with 94% balance, the Fiedler vector is already near-optimal.  SDP solvers add heavy dependencies (CVXPY, Mosek) for negligible improvement.

---

## Frustrated Triangles

### Definition

A triangle (u, v, w) with edges γ_uv, γ_uw, γ_vw is **frustrated** when:

```
sign(γ_uv) × sign(γ_uw) × sign(γ_vw)  <  0
```

The four possible sign combinations:

| Signs | Product | Status | Meaning |
|-------|---------|--------|---------|
| (+, +, +) | +1 | Balanced | All three in the same camp |
| (+, −, −) | +1 | Balanced | Two in one camp, one in the other |
| (+, +, −) | −1 | **Frustrated** | A co-varies with B and C, but B counter-varies with C |
| (−, −, −) | −1 | **Frustrated** | All three counter-vary — no consistent assignment |

### Per-node frustrated ratio

For each construct, we count how many of its triangles are frustrated and report the ratio.  A high ratio means the construct straddles the bipartition boundary: its SES profile is partially aligned with each camp in proportions that prevent consistent assignment.

The 6% global frustration rate is far below the 50% expected from random sign assignment, confirming that the sign structure is real.  But those 493 frustrated triangles are not randomly distributed — they cluster around specific constructs where SES creates genuinely non-transitive patterns.

### Why per-node rather than global

A global frustration index (6%) describes the graph.  Per-node ratios describe individual constructs.  The `is_boundary` flag uses both Fiedler confidence *and* frustrated ratio because they capture different failure modes:

- Low Fiedler confidence, low frustration:  the construct is weakly connected (few edges), so the Laplacian has little evidence.
- High Fiedler confidence, high frustration:  the construct is firmly placed in one camp by most of its edges, but has several surprising edges that contradict the placement.

Both types of boundary node carry higher interpretive uncertainty in bridge paths.

---

## Scale Coding Dependency

The bipartition depends entirely on the correctness of the scale coding pipeline.  The dependency chain:

```
Survey scale direction (which end of the Likert scale = "more")
    ↓
Reverse-coding of items
    ↓
Construct aggregate sign direction (does agg_* increasing = more of the concept?)
    ↓
SES fingerprint ρ signs
    ↓
Bridge γ signs
    ↓
Triangle sign products
    ↓
Bipartition
```

A single miscoded construct flips all its fingerprint ρ signs, which flips all its bridge γ signs (the scale direction audit on 2026-03-18 flipped 265 of 984 edges for 37 constructs), which changes which triangles are frustrated, which shifts the bipartition.

The scale audit (2026-03-18) detected 37 constructs with inverted scales using keyword matching against value-1 labels ("Mucho", "Muy de acuerdo", "Siempre", etc.).  65 reverse-coded items were added, all constructs rebuilt, fingerprints recomputed, and bridge γ signs patched.  The current `kg_ontology_v2.json` reflects the corrected state.

**Residual risk:**  The 6% frustrated triangles could be genuine (non-transitive SES structuring), residual scale errors missed by the audit, artifacts of the ρ→γ scaling approximation (1.14 factor), or statistical boundary cases.  The bipartition API flags this risk through the `is_boundary` qualifier — constructs with low confidence or high frustration should be treated with appropriate epistemic caution.

---

## Implementation in the Ontology

### Load-time computation

At `OntologyQuery.__init__`, after loading bridge edges and fingerprint data:

1. **`_compute_empty_domains()`** — identifies domains with items but no L1 constructs (JUE, CON).  These are structural deadends: items from these domains cannot be lifted to a bridge-capable anchor.

2. **`_compute_bipartition()`** — builds the signed adjacency matrix from `_bridges`, computes the signed Laplacian, extracts the Fiedler vector, orients via median ρ_escol, assigns camp (+1/-1) and confidence to all 93 constructs (71 connected + 22 isolated with fingerprint-based fallback at confidence=0.0).

3. **`_compute_frustrated_ratio()`** (called from within `_compute_bipartition`) — enumerates triangles per node using adjacency sets, computes per-node frustrated ratio and total triangle count.

### Public API

| Method | Input | Output | Purpose |
|--------|-------|--------|---------|
| `get_camp(key)` | Any L0/L1/L2 key | camp_id, camp_name, confidence, frustrated_ratio, is_boundary, narrative | Camp membership for any survey item or construct |
| `get_frustrated_nodes(min_ratio)` | Threshold (default 0.10) | Sorted list of boundary constructs | Identify interpretively uncertain nodes |

### Lift resolution update

`_lift_to_construct` now distinguishes:

| lift_type | Meaning |
|-----------|---------|
| `exact` | Key is an L1 construct, or an item with an exact parent construct |
| `approximate` | Orphan item lifted via candidate_construct (ρ→γ approximation) |
| `domain_fallback` | Item/domain with constructs available but no direct match |
| `no_constructs_in_domain` | Item in a domain that has zero L1 constructs (JUE, CON) — structural deadend, not a bad input |
| `none` | Unresolvable key |

---

## Implementation in Graph Traversal

### Dijkstra enhancements

`find_path` now includes:

| New field | Type | Source |
|-----------|------|--------|
| `camp_a` | `{camp_id, camp_name, confidence}` | Fiedler bipartition of anchor_a |
| `camp_b` | `{camp_id, camp_name, confidence}` | Fiedler bipartition of anchor_b |
| `expected_sign` | +1 / -1 / None | `camp_a.id × camp_b.id` — predicted bridge sign from camp membership |
| `expected_sign_note` | str | Human-readable: "positive (both cosmopolitan)" or "negative (cosmopolitan × tradition)" |
| `signal_chain_confidence` | "high" / "medium" / "low" | Based on lift types of both endpoints |
| `sign_matches_prediction` | bool / None | Whether the direct edge sign matches the camp prediction |

### Sign-consistent routing

`find_path(key_a, key_b, prefer_sign_consistent=True)` adds a soft penalty (0.3 in log-space, ≈26% reduction in effective |γ|) each time consecutive edges flip sign.  This nudges Dijkstra toward all-positive or all-negative paths, which are narratively simpler to explain.

The penalty is additive, not a hard filter.  A sign-consistent path will only be chosen if it is not dramatically weaker than the sign-inconsistent alternative.  This prevents the router from taking a weak but sign-consistent path when a strong sign-crossing path exists.

### Narrative updates

`_path_narrative` now appends a camp context line:

- Same camp: `"Camp: both endpoints are in the cosmopolitan camp — positive bridge signal expected."`
- Opposite camps: `"Camp: cosmopolitan → tradition (opposite camps) — negative bridge signal expected."`
- Sign mismatch: `"WARNING: observed signal sign contradicts camp prediction — path likely crosses camp boundary at an intermediate node."`

---

## What Follows: Integration Plan

### Phase 1: Agent pipeline wiring (immediate)

The ontology is not yet called from the agent pipeline.  The integration point is after `variable_selector.py` returns `(col_name, survey_name)`:

```python
item_key = f"{col}|{enc_nom_dict[survey_name]}"
lift = ontology._lift_to_construct(item_key)
camp = ontology.get_camp(item_key)
```

This gives the agent camp membership and bridge context for any variable it selects, before generating analysis.  The `lift_type` tells the agent how trustworthy the lift is; `no_constructs_in_domain` tells it to avoid bridge-based reasoning entirely for JUE/CON items.

The wiring is a single integration call at the point where `variable_selector.py` resolves a user query to concrete survey columns.  No new module is needed — `OntologyQuery` is instantiated once (the JSON files load in ~0.3s) and queried per variable.

### Phase 2: Camp-aware analysis narratives

The analytical essay pipeline (`analytical_essay.py`) generates two-step LLM output: reasoning outline, then essay.  Camp membership should enter the reasoning outline as structured context, not as a constraint on the essay output.

Concretely, when the essay concerns two variables:

- Same camp: the reasoning outline includes "X and Y are both in the cosmopolitan camp — they are co-elevated by the same sociodemographic profile (education, urbanisation).  The SES bridge predicts positive co-variation."
- Opposite camps: "X (cosmopolitan) and Y (tradition) are counter-varied by SES — the same sociodemographic position that elevates X suppresses Y."
- Boundary node involved: "X sits on the camp boundary (frustrated_ratio={ratio}) — the SES direction is ambiguous and the bridge prediction carries lower confidence."

The LLM can then use or override this framing based on the actual data distributions.  Camp membership informs but does not dictate the narrative.

### Phase 3: Boundary-aware path interpretation

When `find_path` crosses a frustrated node, the narrative should flag this:

- Identify which intermediate node has high frustrated_ratio
- Note that the prediction chain passes through an interpretively uncertain construct
- Recommend checking the direct bridge (if it exists) rather than trusting the multi-hop chain
- If `sign_matches_prediction` is False, explicitly state that the path crosses the camp boundary and explain what this means for the relationship

This is a narrative-layer change: the `find_path` output already contains the data (`frustrated_ratio` per node is in `_frustrated_ratio`, camp info is in the output dict).  The change is in `_path_narrative`, which should look up intermediate nodes' boundary status and inject a caveat when warranted.

### Phase 4: Camp visualization in dashboard

The dashboard (`dashboard.py`) can colour-code the construct network by camp membership:

- Cosmopolitan nodes in one colour, tradition in another
- Boundary nodes (is_boundary=True) in a distinct style (e.g., lighter shade, dashed border)
- Edge colour by sign (positive = within-camp, negative = between-camp)
- Frustrated nodes highlighted with a marker or annotation

The existing `plot_domain_circle_network.py` already renders the construct network.  Adding camp colouring requires reading `get_camp()` for each node at render time and mapping camp_id to a colour scale.  The Fiedler confidence can modulate opacity: high-confidence nodes are fully opaque, boundary nodes are translucent.

### Phase 5: Exploratory graph queries for los_mex

With bipartition in place, the ontology supports a set of structured queries over the los_mex attitude space that were not previously possible:

**5a. Camp census.**  List all constructs by camp, sorted by Fiedler confidence.  This gives a complete map of which attitudes Mexican SES pushes in which direction.  The census is the reference table for any downstream analysis that needs to know "is this attitude cosmopolitan or traditional?"

**5b. Cross-camp bridge leaders.**  Filter bridges to those connecting opposite camps (γ < 0 expected).  Rank by |γ|.  These are the strongest SES-mediated tensions in Mexican opinion — pairs where the same sociodemographic position that elevates one attitude suppresses the other.

**5c. Within-camp bridge leaders.**  Filter bridges to same-camp pairs (γ > 0 expected).  Rank by |γ|.  These are the strongest SES-mediated reinforcements — attitude clusters that move together under sociodemographic stratification.

**5d. Frustrated node deep-dives.**  For each construct with frustrated_ratio > 0.10, extract its triangle list, identify which triangles are frustrated, and report which SES dimension is responsible for the inconsistency (compare fingerprint dot products of the frustrated edges vs. the balanced edges).  This produces a per-node diagnostic of *why* the construct straddles camps.

**5e. Neighbourhood exploration with camp context.**  `get_neighborhood` already returns a construct's bridge neighbours.  With camp metadata, the neighbourhood can be partitioned into same-camp neighbours (reinforcing) and opposite-camp neighbours (tensioning).  The ratio of reinforcing to tensioning edges characterises whether a construct is a camp hub (mostly same-camp links) or a camp bridge (mostly cross-camp links).

These queries operate entirely on the los_mex bridge data (`kg_ontology_v2.json` + `ses_fingerprints.json`) and require no WVS data or external dependencies.

---

## Summary

The bipartition is not a graph-theoretic nicety.  It is the geometric structure of Mexican sociodemographic opinion: a single dominant axis with education-driven cosmopolitanism on one end and age/locality-driven traditionalism on the other.  The signed Laplacian Fiedler vector is the theoretically optimal method for recovering this structure from the bridge data.  Its low confidence values accurately reflect the continuous-gradient nature of the underlying SES geometry — this is a bipartition of a gradient, not of two clusters.

The implementation adds camp metadata to every ontology query and graph traversal result, enabling the agent to explain *why* attitudes co-vary or diverge in terms of the dominant sociodemographic axis, rather than reporting γ values without structural context.
