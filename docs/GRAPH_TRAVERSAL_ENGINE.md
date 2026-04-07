# Graph Traversal Engine — Architecture & User Manual

## Overview

The Graph Traversal Engine (GTE) is a context-aware query layer over the WVS
γ-surface. It unifies three analytical subsystems — ontology (graph structure),
message passing (propagation dynamics), and TDA (cross-context geometry) — into
a single query interface indexed by (country, wave).

**Current status: Phase 1 (Structure Layer) complete.** Phase 2 (Dynamics) and
Phase 3 (Geometry) are planned.

---

## Architecture

### Three-Layer Design

```
                    ┌─────────────────────┐
                    │   QUERY INPUT        │
                    │   (natural language)  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────────┐
              │                │                     │
    ┌─────────▼──────┐ ┌──────▼──────────┐ ┌───────▼────────┐
    │  STRUCTURE      │ │  DYNAMICS       │ │  GEOMETRY       │
    │  (Phase 1) ✅   │ │  (Phase 2)      │ │  (Phase 3)      │
    │                 │ │                 │ │                 │
    │ • Fingerprints  │ │ • BP inference  │ │ • Spectral dist │
    │ • Camps/bipart  │ │ • PPR influence │ │ • Fiedler traj  │
    │ • Dijkstra path │ │ • Heat diffusion│ │ • Hist analogues│
    │ • Neighborhoods │ │ • Temporal fcst │ │ • Convergence   │
    └─────────┬──────┘ └──────┬──────────┘ └───────┬────────┘
              │                │                     │
              └────────────────┼─────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  NARRATIVE SYNTHESIS  │
                    └──────────────────────┘
```

### What Each Layer Does

| Layer | Question | Status |
|-------|----------|--------|
| **Structure** | What is connected to what, and why? | ✅ Phase 1 |
| **Dynamics** | How does signal flow through the network? | Planned (Phase 2) |
| **Geometry** | How does structure vary across countries and time? | Planned (Phase 3) |

### Key Design Decisions

1. **Context-indexed.** Every query is bound to a (country, wave) context. The
   same construct has different fingerprints, camp membership, and paths in
   different countries. This is not a bug — it reflects genuinely different
   social structures.

2. **Pre-computed.** No DR bootstrap or message passing at query time. The
   engine reads pre-computed results from the γ-surface sweeps, TDA pipeline,
   and message passing framework. Queries are subsecond.

3. **LLM at the boundary only.** All computation (paths, fingerprints,
   consensus) is deterministic. LLMs are used only to parse natural language
   queries (input) and generate narrative summaries (output). This makes every
   substantive claim auditable and reproducible.

4. **Significant edges only.** The ontology operates exclusively on edges where
   the 95% CI from the DR bootstrap excludes zero. Non-significant pairs are
   treated as absent, not zero-weight.

---

## Module Structure

```
graph_traversal_engine/
├── __init__.py              # Public exports
├── context.py               # Context, ContextGraph, GraphFamily, Fingerprint, CampAssignment
├── data_loader.py           # Load weight matrices, fingerprints, camps, MP, TDA
└── wvs_ontology.py          # WVSOntologyQuery: the main query interface
```

### Data Dependencies

| Data | Source | Path |
|------|--------|------|
| Weight matrices (55×55 γ) | Julia DR sweep | `data/tda/matrices/{ALPHA3}.csv` |
| SES fingerprints (4D ρ) | Phase 0 script | `data/gte/fingerprints/{ALPHA3}.json` |
| Camp bipartitions | Phase 0 script | `data/gte/camps/{ALPHA3}.json` |
| Construct descriptions | Phase 0 script | `data/gte/construct_descriptions.json` |
| BP lift matrices | Message passing | `data/tda/message_passing/{ALPHA3}_bp.json` |
| PPR hub/sink scores | Message passing | `data/tda/message_passing/{ALPHA3}_ppr.json` |
| Spectral eigenvalues | Message passing | `data/tda/message_passing/{ALPHA3}_spectral.json` |
| Spectral distance matrix | TDA pipeline | `data/tda/spectral/spectral_distance_matrix.csv` |
| Fiedler heatmap | TDA pipeline | `data/tda/allwave/convergence/fiedler_heatmap.csv` |
| Mediator stability | TDA pipeline | `data/tda/allwave/convergence/mediator_stability.json` |

### Phase 0 Scripts

| Script | Purpose | Runtime |
|--------|---------|---------|
| `scripts/debug/compute_wvs_country_fingerprints.py` | Compute per-country fingerprints + bipartitions | ~10s (66 countries) |
| `scripts/debug/build_construct_corpus.py` | Extract construct descriptions for semantic search | <1s |

---

## Data Model

### Context

A (country, wave) pair identifying a specific WVS survey administration.
66 countries in W7, up to 100 across W3–W7.

### Fingerprint

A 4D vector per construct per context:

```
[ρ_escol, ρ_Tam_loc, ρ_sexo, ρ_edad]
```

Each component is Spearman ρ between the construct score and one SES dimension
in that country's population. The fingerprint captures *how* a construct is
sociodemographically stratified.

**Key properties:**
- `ses_magnitude` = RMS of 4 ρ values (overall stratification intensity)
- `dominant_dim` = dimension with highest |ρ|
- `dot(fp_a, fp_b)` predicts sign of γ(A,B) at >85% accuracy

### CampAssignment

Each construct is assigned to one of two camps via the signed Laplacian's
Fiedler vector:
- **+1 = cosmopolitan**: higher median ρ_escol (education-elevated)
- **-1 = tradition**: higher median ρ_edad (age/rural-elevated)

Camp membership is context-specific. A construct may switch camps between
countries if its SES correlations reverse.

### ContextGraph

The per-context graph containing:
- 55×55 weight matrix (signed γ, NaN = missing/non-significant)
- Per-construct fingerprints and camp assignments
- Pre-computed dynamics (BP, PPR, spectral — when available)
- TDA features (Fiedler value, top mediator, Betti numbers)

### GraphFamily

The collection of all context graphs plus cross-context data:
- Spectral distance matrix (66×66 country pairwise distances)
- Fiedler heatmap (country × wave)
- Mediator stability across waves
- Construct description corpus

---

## User Manual

### Setup

```python
import sys
sys.path.insert(0, '/path/to/navegador')

from graph_traversal_engine.data_loader import load_graph_family
from graph_traversal_engine.wvs_ontology import WVSOntologyQuery
```

### Loading Data

```python
# Load all 66 countries (W7)
family = load_graph_family()

# Load specific countries (faster)
family = load_graph_family(countries=["MEX", "USA", "JPN"])

# Load without message passing outputs (fastest, structure only)
family = load_graph_family(countries=["MEX"], load_mp=False)
```

### Creating a Query Object

```python
oq = WVSOntologyQuery(family, country="MEX", wave=7)
print(oq.context)  # "MEX_W7"
```

Each `WVSOntologyQuery` is bound to one country. To compare countries, create
multiple query objects or use `compare_with()`.

### API Reference

#### `get_profile(key) → ConstructProfile`

Full profile of a construct in this context.

```python
profile = oq.get_profile("gender_role_traditionalism|WVS_D")

profile.fingerprint      # Fingerprint(rho_escol=0.137, rho_edad=-0.169, ...)
profile.camp             # CampAssignment(camp_name="cosmopolitan", ...)
profile.degree           # 46 (number of significant edges)
profile.ses_summary      # {"escol": 0.137, "Tam_loc": -0.021, "sexo": 0.060, "edad": -0.169}
```

**What it tells you:** How this attitude is sociodemographically structured in
this country. Which SES dimensions matter, which camp it belongs to, and how
connected it is.

#### `get_neighbors(key, min_abs_gamma=0.0, top_n=None) → list[EdgeInfo]`

Significant neighbors sorted by |γ|.

```python
edges = oq.get_neighbors("gender_role_traditionalism|WVS_D", min_abs_gamma=0.01, top_n=5)

for e in edges:
    print(f"{e.target}: γ={e.gamma:+.4f}, dim={e.dominant_dim}, cos={e.fingerprint_cos:+.3f}")
```

Output:
```
political_information_sources|WVS_E: γ=+0.046, dim=escol, cos=+0.849
online_political_participation|WVS_E: γ=+0.037, dim=escol, cos=+0.656
sexual_and_reproductive_morality|WVS_F: γ=+0.036, dim=edad, cos=+0.815
```

**What it tells you:** Which other attitudes co-vary with this one through
shared SES position, and *why* (the dominant_dim and fingerprint_cos explain the
mechanism).

#### `get_neighborhood(key, min_abs_gamma=0.0, top_n=None) → dict`

Rich neighborhood summary with domain distribution and strongest edge.

```python
nh = oq.get_neighborhood("gender_role_traditionalism|WVS_D", min_abs_gamma=0.01)

nh["summary"]["n_neighbors"]          # 46
nh["summary"]["n_positive"]           # 38
nh["summary"]["n_negative"]           # 8
nh["summary"]["domain_distribution"]  # {"WVS_E": 15, "WVS_F": 7, ...}
nh["summary"]["strongest_edge"]       # {"key": "...", "gamma": 0.046}
```

#### `get_similar(key, n=10) → list[tuple[str, float, str]]`

Constructs with the most similar SES fingerprint (cosine similarity).

```python
similar = oq.get_similar("gender_role_traditionalism|WVS_D", n=3)
# [("social_intolerance_outgroups|WVS_A", 0.974, "edad"),
#  ("work_ethic|WVS_C", 0.889, "edad"),
#  ...]
```

**What it tells you:** Which attitudes are driven by the same sociodemographic
forces, regardless of whether they share a direct bridge edge.

#### `get_camp(key) → CampAssignment`

Camp membership and boundary information.

```python
camp = oq.get_camp("gender_role_traditionalism|WVS_D")
camp.camp_name       # "cosmopolitan"
camp.confidence      # 0.02 (very close to boundary)
camp.frustrated_ratio  # fraction of sign-inconsistent triangles
camp.is_boundary     # True if frustrated_ratio > 0.10
```

#### `get_camp_members(camp_id) → list[str]`

```python
cosmopolitan = oq.get_camp_members(+1)
tradition = oq.get_camp_members(-1)
```

#### `find_path(key_a, key_b) → PathResult`

Dijkstra shortest path maximizing the product of |γ| along the chain.

```python
path = oq.find_path(
    "gender_role_traditionalism|WVS_D",
    "science_skepticism|WVS_I"
)

path.path          # ["gender_role_trad...", "science_skepticism..."]
path.signal_chain  # 0.0104 (product of |γ| along path)
path.path_sign     # -1 (opposing: higher on one → lower on other)
path.edges[0].gamma          # -0.0104
path.edges[0].dominant_dim   # "edad"
path.direct_edge             # -0.0104 (direct connection exists)
path.attenuation_warning     # False (signal > 0.001)
```

**What it tells you:** The strongest SES-mediated chain connecting two
attitudes. The path_sign tells you the expected direction of co-variation.
Each hop's dominant_dim tells you which SES dimension carries the association.

#### `explain_pair(key_a, key_b) → dict`

All-in-one explanation combining fingerprint geometry, direct edge, path,
and camp membership.

```python
result = oq.explain_pair(
    "gender_role_traditionalism|WVS_D",
    "religious_belief|WVS_F"
)

result["fingerprint_cosine"]  # -0.897 (opposing SES profiles)
result["shared_driver"]       # "age/cohort"
result["direct_gamma"]        # -0.031 (negative bridge)
result["expected_sign"]       # -1 (from fingerprint dot product)
result["sign_consistent"]     # True (actual matches expected)
result["same_camp"]           # False (different camps)
result["path_length"]         # 1 (directly connected)
result["signal_chain"]        # 0.031
```

#### `compare_with(other_country, key) → dict`

Compare a construct's profile and network position across two countries.

```python
comp = oq.compare_with("PAK", "gender_role_traditionalism|WVS_D")

comp["fingerprint_cosine"]    # 0.20 (nearly orthogonal SES profiles)
comp["camp_agreement"]        # True (both cosmopolitan)
comp["neighbor_jaccard"]      # 0.86 (86% shared neighbors)
comp["sign_agreement"]        # 0.49 (coin flip — signs scrambled)
```

**What it tells you:** Two countries can share the same topology (which
constructs connect) but have completely different SES geometry (how and why).
Mexico and Pakistan share 86% of neighbors for this construct, but the γ signs
agree only 49% of the time — the SES mechanisms driving the connections are
fundamentally different.

### GraphFamily Methods

```python
# Spectral neighbors: countries with most similar network structure
family.spectral_neighbors("MEX", n=5)
# [("JPN", 0.073), ("SVK", 0.074), ("DEU", 0.077), ...]

# List countries available for a wave
family.countries(wave=7)  # ["AND", "ARG", "ARM", ...]

# Get a specific context graph
graph = family.get("MEX", 7)
graph.fiedler_value           # 0.058
graph.structural_balance      # 0.667
graph.n_significant_edges     # 982
```

---

## Construct Key Format

All construct keys follow the format `{name}|{domain}`:

```
gender_role_traditionalism|WVS_D
science_skepticism|WVS_I
democratic_values_importance|WVS_E
personal_religiosity|WVS_F
```

The 55 W7 constructs span 8 WVS domains:

| Domain | Name | # Constructs |
|--------|------|-------------|
| WVS_A | Social Values, Attitudes & Stereotypes | 9 |
| WVS_C | Work & Employment | 3 |
| WVS_D | Family | 3 |
| WVS_E | Politics & Society | 18 |
| WVS_F | Religion & Morale | 8 |
| WVS_G | National Identity | 5 |
| WVS_H | Security | 9 |
| WVS_I | Science & Technology | 1 |

---

## Examples

### Example 1: Why do gender attitudes and religiosity co-vary in Mexico?

```python
oq = WVSOntologyQuery(family, country="MEX")
result = oq.explain_pair(
    "gender_role_traditionalism|WVS_D",
    "religious_belief|WVS_F"
)
```

**Finding:** Fingerprint cosine = -0.90. These two attitudes have *opposing*
SES profiles. The shared driver is age/cohort. In Mexico, the same generational
shift that pushes toward gender egalitarianism also pushes away from religious
belief — producing a negative γ = -0.031. They're in different camps
(cosmopolitan vs. tradition), and the sign is consistent with the fingerprint
prediction.

### Example 2: Does gender traditionalism mean the same thing in different countries?

```python
for country in ["MEX", "USA", "JPN", "DEU", "PAK"]:
    oq_c = WVSOntologyQuery(family, country=country)
    p = oq_c.get_profile("gender_role_traditionalism|WVS_D")
    print(f"{country}: dominant={p.fingerprint.dominant_dim}, camp={p.camp.camp_name}")
```

| Country | Dominant dim | Camp |
|---------|-------------|------|
| MEX | edad (age) | cosmopolitan |
| USA | sexo (gender) | **tradition** |
| JPN | edad (age) | cosmopolitan |
| DEU | sexo (gender) | cosmopolitan |
| PAK | sexo (gender) | cosmopolitan |

**Finding:** The construct is *age-driven* in Mexico and Japan but
*gender-driven* in the US, Germany, and Pakistan. The US is the only country
where it falls in the tradition camp. Same survey question, fundamentally
different social meaning depending on context.

### Example 3: Whose attitude network looks most like Mexico's?

```python
for c, d in family.spectral_neighbors("MEX", n=5):
    print(f"{c} ({family.country_zones[c]}): {d:.4f}")
```

```
JPN (Confucian):              0.0727
SVK (Orthodox/ex-Communist):  0.0742
DEU (Protestant Europe):      0.0765
NZL (English-speaking):       0.0784
RUS (Orthodox/ex-Communist):  0.0801
```

**Finding:** Mexico's nearest structural neighbor is Japan — not Brazil, not
any other Latin American country. This is spectral distance (eigenvalue
similarity of the network Laplacian), meaning the two countries have similar
*diffusion dynamics*. A perturbation in Mexico's attitude network would ripple
through in a pattern more similar to Japan than to geographically or culturally
closer countries.

---

## Interpretation Guide

### What γ Measures

γ is Goodman-Kruskal gamma: a measure of monotonic association between two
ordinal variables, conditioned on 4 SES dimensions (education, urbanization,
gender, age) via a doubly-robust bridge estimator.

**γ > 0**: The same SES position that elevates construct A also elevates B.
**γ < 0**: The same SES position that elevates A suppresses B.
**γ ≈ 0**: The two constructs are independently SES-structured (or not
structured at all).

### What γ Does NOT Measure

- **Causation.** γ = SES-mediated covariation, not causal effect.
- **Non-monotonic effects.** U-shaped relationships are invisible.
- **Direct attitude-to-attitude links.** Only SES-mediated associations.
- **Individual-level prediction.** All estimates are population-level.

### Reading Fingerprint Cosine

| Cosine | Interpretation |
|--------|---------------|
| > +0.8 | Same SES gradient → expect γ > 0 (co-elevated) |
| +0.3 to +0.8 | Partially aligned SES profiles |
| -0.3 to +0.3 | Orthogonal — SES-independent or different dims dominate |
| < -0.8 | Opposing SES gradient → expect γ < 0 (counter-elevated) |

### Reading Camp Membership

The bipartition divides constructs into two groups that tend to have opposite
SES gradients. Within a camp, most γ values are positive (co-elevated). Between
camps, most are negative (counter-elevated).

Camp assignment is context-specific. Structural balance (fraction of
sign-consistent triangles) ranges from 62% to 100% across countries. Higher
balance = cleaner two-camp structure.

---

## Known Limitations

1. **W7 only.** Per-country fingerprints and bipartitions are computed for W7
   (2018) only. Earlier waves have smaller construct sets (24–42) and no
   per-country fingerprints yet.

2. **No propagation yet.** The structure layer tells you *what* is connected but
   not *how signal flows*. BP/PPR/spectral propagation is Phase 2.

3. **No temporal forecasting.** Trajectories and shock injection are Phase 3.

4. **55 constructs.** Events outside this vocabulary produce forced best-matches.
   No confidence threshold yet on construct matching quality.

5. **Bipartition stability.** Some countries have low structural balance (62%),
   meaning the two-camp model is a poor fit. The engine does not yet flag when
   bipartition-based reasoning is unreliable.

---

## Further Steps

### Phase 2: Dynamics Layer (Propagator)

**Goal:** Unified propagation interface consuming pre-computed MP outputs.

| Component | What it does |
|-----------|-------------|
| BPPropagator | Load BP lift matrix → conditional inference from clamped evidence |
| PPRPropagator | Load PPR matrix → steady-state influence ranking with sign restoration |
| SpectralPropagator | Load spectral decomposition → multi-scale heat kernel response |
| Consensus scoring | Count method agreement on direction (3/3 = high, 2/3 = medium) |

**Key question to resolve:** PPR output currently stores hub/sink scores but
not the full 55×55 PPR matrix. Either recompute and cache, or add matrix output
to `mp_ppr_influence.py`.

### Phase 3: Geometry Layer (Projector)

**Goal:** Cross-context projection using TDA features.

| Component | What it does |
|-----------|-------------|
| SpectralProjector | Find structurally similar countries via spectral distance |
| HistoricalSearch | Scan temporal data for past instances of predicted shifts |
| TemporalProjector | Network autoregression forecast with shock injection |
| Zone aggregation | Group results by cultural zone, identify sign flips |

**Key question to resolve:** All-wave MP (running BP/PPR/spectral on W3–W6)
would enable per-wave propagation queries. Worth the compute for W5–W7 (≥31
constructs); W3–W4 may be too sparse to be reliable.

### Phase 4: Query Resolution + Narrative

**Goal:** LLM-powered input parsing and output narrative.

- ContextResolver: natural language → (construct, direction, country, wave)
- NarrativeSynthesizer: structured results → plain-language analysis
- Construct embedding index for semantic matching (pre-compute once)

### Phase 5: Agent Integration

**Goal:** Wire GTE into `agent.py` as a LangGraph tool.

- Tool definition wrapping `engine.query()`
- System prompt update with GTE tool description
- Optional: interactive GTE explorer in the Dash dashboard

---

## Test Suite

65 unit tests covering all Phase 0 + Phase 1 functionality:

```bash
python -m pytest tests/unit/test_graph_traversal_engine.py -v
```

Tests include:
- Context dataclasses and Fingerprint operations
- Data loading (weight matrices, fingerprints, camps, MP, TDA)
- WVSOntologyQuery: profiles, neighbors, paths, camps, cross-country
- Fingerprint sign prediction validation (>85% accuracy per country)
- Phase 0 output file integrity checks

Runtime: ~0.7s.
