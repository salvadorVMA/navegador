# Graph Traversal Engine — Specification

## 1. Problem Statement

The navegador project has produced three independent analytical subsystems over
the WVS construct networks:

| Subsystem | What it knows | Scope |
|-----------|--------------|-------|
| **Ontology** (`opinion_ontology.py`) | Graph structure: nodes, edges, paths, camps, fingerprints | los_mex only (93 constructs, 1 country) |
| **Message Passing** (`mp_*.py`) | Propagation dynamics: BP inference, PPR influence, spectral diffusion, temporal forecasting | WVS (55 constructs, 66 countries, 37 temporal) |
| **TDA** (`tda_*.py`) | Structural geometry: spectral distances, Fiedler trajectories, persistent homology, mediator stability | WVS (100 countries, 5 waves, 1996–2018) |

All three derive from the same γ-surface (DR bridge estimates conditioned on 4
SES dimensions), but they never communicate. The ontology operates on los_mex
data structures that don't exist in WVS. Message passing produces per-country
JSONs that no query layer consumes. TDA characterizes cross-context variation
that no propagation model uses.

**The Graph Traversal Engine (GTE)** unifies these three subsystems into a single
query path:

```
event → construct → propagation → projection → forecast → narrative
```

A user describes an event ("trust in science declines in Mexico"), and the engine
returns: what other attitudes shift (propagation), whether this pattern holds
elsewhere (projection), and where it leads over time (forecast).

---

## 2. Design Principles

### 2.1 WVS-First

The ontology was built for los_mex, which has a unique data structure: 26
separate surveys in a single country, where bridge γ measures *cross-survey*
SES-mediated covariation between constructs that were measured on *different
respondent pools*. This created design decisions throughout `opinion_ontology.py`
that don't apply to WVS:

| los_mex (current ontology) | WVS (target) |
|---------------------------|--------------|
| 26 surveys, 1 country | 1 survey per country×wave context |
| Bridge γ = cross-survey (different respondents) | Bridge γ = within-survey (same respondents) |
| Items belong to specific surveys | All items in same questionnaire per wave |
| `_lift_to_construct()` navigates survey boundaries | No survey boundaries to cross |
| Single bridge network (93×93) | Family of networks: one 55×55 per context |
| SES fingerprints = single country | SES fingerprints = per-country |
| Bipartition = one global partition | Bipartition = per-country (or aggregate) |

The GTE builds on WVS. Los_mex becomes a special case that can be revisited
later by treating it as one more "context" in the family.

### 2.2 Three Layers, One Engine

The three subsystems are not alternatives — they answer different questions
about the same graph:

| Layer | Question | Subsystem |
|-------|----------|-----------|
| **Structure** | What is connected to what? | Ontology |
| **Dynamics** | How does signal flow? | Message Passing |
| **Geometry** | How does structure vary across contexts? | TDA |

A query passes through all three layers:

1. **Structure** resolves the query target and provides the graph for the
   requested context (country, wave)
2. **Dynamics** propagates the shock within that context's graph
3. **Geometry** identifies analogous contexts and temporal trajectories

### 2.3 Context-Indexed Graphs

The fundamental data object is a **context**: a (country, wave) pair that
identifies a specific survey administration. Each context has:

- A **construct set** (subset of the 55 WVS constructs present in that wave)
- A **weight matrix** W (signed γ values, 55×55 with structural zeros for
  missing pairs)
- An **SES fingerprint set** (per-construct [ρ_escol, ρ_Tam_loc, ρ_sexo,
  ρ_edad] in that population)
- Pre-computed **message passing outputs** (BP lifts, PPR matrix, spectral
  decomposition)
- Pre-computed **TDA features** (Fiedler value, mediator scores, Betti numbers)

The engine does not recompute γ or message passing at query time — it queries
pre-computed results. This makes queries fast (subsecond) at the cost of being
limited to contexts that have been swept.

### 2.4 Epistemic Honesty

Every output carries explicit uncertainty markers:

- **γ confidence intervals** from DR bootstrap (median CI width = 0.024 at
  construct level)
- **Method consensus** across BP, PPR, and path-based propagation
- **Noise-dominated flags** from temporal forecasting (σ > |predicted shift|)
- **Zone sign flips** — predictions that reverse direction in other cultural
  contexts
- **Causal disclaimer** — γ measures SES-mediated covariation under CIA, not
  causal effects

---

## 3. Query Interface

### 3.1 Query Types

The engine supports four query types, each composable:

#### Type 1: **Shock Propagation** (within-country)

> "If [attitude X] [increases/decreases] in [country], what else shifts?"

Returns: ranked list of affected constructs with direction, magnitude estimate,
and confidence level from multiple propagation methods.

#### Type 2: **Cross-Country Projection**

> "Does this pattern hold in [other country / zone / globally]?"

Returns: analogous countries by spectral similarity, zone-level aggregation,
sign consistency analysis.

#### Type 3: **Temporal Trajectory**

> "Where is [attitude X] heading in [country]?"

Returns: network-implied forecast, historical trend, agreement/disagreement
between network and trend, uncertainty envelope.

#### Type 4: **Pathway Explanation**

> "How are [attitude X] and [attitude Y] connected in [country]?"

Returns: strongest SES-mediated path, intermediate constructs, per-hop γ with
CI, camp membership of endpoints, dominant SES dimension at each hop.

### 3.2 Query Resolution

Every query begins with **anchor resolution**: mapping the user's natural
language to one or more WVS constructs in a specific context.

```
User input
    │
    ▼
LLM parse → (concept, direction, magnitude, country, wave)
    │
    ▼
Construct match → WVS construct key(s) via semantic search
    │
    ▼
Context selection → (country, wave) → load pre-computed graph
    │
    ▼
Dispatch to query type
```

The LLM's role is limited to two parse operations:
1. Extract structured fields from natural language (concept, direction, country)
2. Match concept description to WVS construct labels (semantic similarity)

All propagation, projection, and forecasting is deterministic — no LLM in the
computation loop.

### 3.3 Output Structure

```python
@dataclass
class TraversalResult:
    # Query metadata
    query: str                              # Original natural language
    anchors: list[Anchor]                   # Resolved construct(s)
    context: Context                        # (country, wave)

    # Layer 1: Structure
    graph_summary: GraphSummary             # Fiedler, density, n_constructs
    anchor_profile: ConstructProfile        # Fingerprint, camp, mediator rank

    # Layer 2: Dynamics (per query type)
    propagation: PropagationResult | None   # Type 1: shock effects
    pathway: PathwayResult | None           # Type 4: construct-to-construct

    # Layer 3: Geometry
    projection: ProjectionResult | None     # Type 2: cross-country
    trajectory: TrajectoryResult | None     # Type 3: temporal

    # Synthesis
    predictions: list[Prediction]           # Ranked, with confidence
    caveats: list[str]                      # Epistemic warnings
    narrative: str                          # LLM-generated plain language
```

---

## 4. Data Model

### 4.1 Context

```python
@dataclass
class Context:
    country: str        # ISO Alpha-3 (e.g., "MEX")
    wave: int           # WVS wave number (3–7)
    year: int           # Survey year
    zone: str           # Inglehart-Welzel cultural zone
    n_constructs: int   # Constructs present in this context
```

### 4.2 ContextGraph

The per-context graph replaces the single-network `OntologyQuery`:

```python
@dataclass
class ContextGraph:
    context: Context
    constructs: list[str]                 # Construct keys present
    weight_matrix: np.ndarray             # 55×55 signed γ (NaN = missing)
    fingerprints: dict[str, Fingerprint]  # Per-construct SES correlations
    camps: dict[str, int]                 # Per-construct bipartition (+1/-1)

    # Pre-computed dynamics (loaded from MP outputs)
    bp_lifts: np.ndarray                  # 55×55 mean KL lift matrix
    ppr_matrix: np.ndarray                # 55×55 PPR influence matrix
    hub_scores: dict[str, float]          # PPR hub scores
    sink_scores: dict[str, float]         # PPR sink scores
    spectral: SpectralDecomp              # Eigenvalues, Fiedler partition

    # Pre-computed TDA features
    fiedler_value: float
    mediator_scores: dict[str, float]
    top_mediator: str
    betti_1: int                          # Number of persistent loops
```

### 4.3 GraphFamily

The collection of all context graphs, plus cross-context relationships:

```python
@dataclass
class GraphFamily:
    contexts: dict[tuple[str, int], ContextGraph]  # (country, wave) → graph
    spectral_distances: np.ndarray                  # n_countries × n_countries
    fiedler_heatmap: pd.DataFrame                   # countries × waves
    convergence_metrics: dict                       # Wave transition data
    mediator_stability: dict[str, dict]             # Per-country stability
    zone_trends: pd.DataFrame                       # Zone × wave trends
```

### 4.4 Fingerprint (WVS-adapted)

```python
@dataclass
class Fingerprint:
    rho_escol: float      # Spearman ρ with education
    rho_Tam_loc: float    # Spearman ρ with urbanization
    rho_sexo: float       # Spearman ρ with gender
    rho_edad: float       # Spearman ρ with age/cohort
    ses_magnitude: float  # RMS of 4 ρ values
    dominant_dim: str     # Dimension with highest |ρ|
```

In WVS, fingerprints are **context-specific**: the same construct has different
SES correlations in different countries. The los_mex ontology assumed a single
fingerprint per construct (single country). The GTE stores fingerprints per
(construct, context) pair.

**Implication for camp structure**: The bipartition is also context-specific. A
construct may be in the "cosmopolitan" camp in Mexico but in the "tradition"
camp in Pakistan, if its SES correlations reverse. This is not a bug — it
reflects genuinely different social structures.

### 4.5 Construct Matching Across Contexts

WVS constructs are identified by the same keys across countries within a wave
(e.g., `gender_role_traditionalism|WVS_D`). Cross-wave matching is handled by
the variable equivalence table (`wvs_metadata.py`), which tracks which Q-codes
map to which constructs in each wave.

For WVS↔los_mex matching, the existing `wvs_losmex_construct_map_v2.json`
provides graded matches (48 grade-3, 77 grade-2).

---

## 5. Engine Components

### 5.1 Component 1: ContextResolver

**Responsibility**: Map a query to a concrete (construct, context) pair.

**Input**: Natural language query string.

**Process**:
1. **LLM parse**: Extract (concept_description, direction, magnitude_hint,
   country_hint, wave_hint) from natural language
2. **Country resolution**: Map country name/hint to ISO Alpha-3 code. Default
   to latest wave for that country if wave not specified.
3. **Construct matching**: Semantic search of concept_description against WVS
   construct labels + descriptions. Use cosine similarity against a pre-built
   embedding index of the 55 construct descriptions.
4. **Multi-anchor detection**: If the event affects multiple constructs (e.g.,
   "economic crisis" → employment_precarity + financial_insecurity), return all
   anchors with individual confidence scores.
5. **Magnitude estimation**: Map qualitative hints to quantitative shock
   magnitudes (weak=0.5σ, moderate=1σ, strong=2σ on the construct's empirical
   distribution in that context).

**Output**: `list[Anchor]` where each Anchor has (construct_key, direction,
magnitude, confidence).

**LLM involvement**: Steps 1 and 4 only. Step 3 can be embedding-based (no LLM
call) or LLM-assisted for ambiguous cases.

### 5.2 Component 2: LocalPropagator

**Responsibility**: Compute within-country shock effects using three
complementary methods.

**Input**: Anchor(s) + ContextGraph.

**Process** (three methods, run in parallel):

#### 2a. Belief Propagation Conditional Inference

- Load pre-computed BP lift matrix for this context
- Look up the anchor construct's row in the lift matrix
- Each entry = KL divergence from prior to posterior when anchor is clamped
- Scale by shock magnitude
- **Output**: `{construct: bp_lift}` for all constructs

**What it answers**: "Given this attitude is observed at level X, what does the
joint distribution *imply* about all other attitudes?"

**Character**: Observational — conditioning, not intervention.

#### 2b. PPR Influence Propagation

- Load pre-computed PPR matrix for this context
- Read anchor construct's PPR column
- Scale by shock magnitude
- Apply sign from weight matrix (PPR uses |γ|; restore sign from W)
- **Output**: `{construct: signed_ppr_shift}` for all constructs

**What it answers**: "How much does a perturbation at this node ripple through
the network, and in what direction?"

**Character**: Steady-state random walk — captures transitive influence through
multi-hop paths.

#### 2c. Spectral Diffusion (Heat Kernel)

- Load pre-computed spectral decomposition for this context
- Compute heat kernel response at multiple time scales
  (t ∈ {0.1, 0.5, 1.0, 5.0})
- Source = anchor construct, target = all others
- **Output**: `{construct: {t: heat_amount}}` — multi-scale response profile

**What it answers**: "At what spatial scale does signal from this construct
reach each other construct?"

**Character**: Multi-scale — separates local (direct neighbors) from global
(whole-network) effects.

#### Reconciliation

The three methods probe different aspects of the same graph:

| Method | Probes | Sensitive to |
|--------|--------|-------------|
| BP | Joint distribution (equilibrium) | Edge signs, coupling strength (β) |
| PPR | Transitive influence (steady-state flow) | Path structure, degree distribution |
| Spectral | Scale-dependent diffusion | Eigenstructure, spectral gap |

**Consensus scoring**: For each target construct, count how many methods agree
on direction (all 3 = high, 2/3 = medium, 1/3 or disagreement = low). When all
three agree on direction AND magnitude ranking, confidence is high. When BP and
PPR agree but spectral shows scale-dependent reversal, flag as "scale-sensitive"
— the effect is real at short range but reverses at long range (possible
through frustrated triangles).

### 5.3 Component 3: CrossContextProjector

**Responsibility**: Project within-country results to other countries, zones,
and historical analogues.

**Input**: LocalPropagation result + target scope.

**Process**:

#### 3a. Spectral Neighbor Identification

- Load spectral distance matrix from TDA
- Find N nearest countries to source country
- **Interpretation**: similar eigenvalue spectra → similar network structure →
  similar propagation patterns

#### 3b. Analogical Transfer

For each spectral neighbor:
- Load its ContextGraph
- Check: does the anchor construct exist? What's its hub score? Mediator rank?
- Run the same propagation query on the neighbor's graph
- Compare: do the top-5 affected constructs match? Do signs agree?
- **Output**: per-neighbor propagation results + similarity score

#### 3c. Zone Aggregation

- Group results by cultural zone (8 Inglehart-Welzel zones)
- For each zone: compute zone-mean effect at each target construct
- Identify **sign flips**: constructs where propagation direction reverses
  between zones
- Identify **zone-specific effects**: constructs affected in some zones but not
  others

#### 3d. Historical Analogue Search

- Search temporal data (37 countries, 3-7 waves) for contexts where the anchor
  construct actually shifted in the observed direction between consecutive waves
- For each historical shift: did the predicted downstream constructs also shift
  as expected?
- **Output**: list of (country, wave_from, wave_to, observed_shift,
  downstream_accuracy)

**This is the strongest form of validation**: the model predicts that declining
construct X should be accompanied by rising construct Y; we can check whether
this actually happened somewhere.

### 5.4 Component 4: TemporalProjector

**Responsibility**: Forecast where a construct is heading, given its trajectory
and network dynamics.

**Input**: Anchor construct + country + available waves.

**Process**:

#### 4a. Network Autoregression

- Load temporal dynamics model for this country
- α* = fitted blending parameter (persistence vs. network diffusion)
- Compute forecast: x̂(next) = α*·A·x(current) + (1-α*)·x(current)
- With shock applied to anchor construct
- **Output**: per-construct forecast with 80% CI

#### 4b. Trend Extrapolation

- OLS trend per construct across available waves
- Compare trend direction vs. network forecast direction
- **Trend reversals** = most interesting: network predicts opposite of momentum

#### 4c. Structural Context

- Fiedler trajectory: is network tightening or loosening?
  - Tightening → shocks propagate more broadly in future
  - Loosening → shocks are more contained
- Mediator stability: is the anchor's structural role persistent or shifting?
- β₁ trend: are topological loops appearing or disappearing?
  - Disappearing loops → network becoming more hierarchical → clearer
    propagation pathways

### 5.5 Component 5: NarrativeSynthesizer

**Responsibility**: Combine all results into a structured, human-readable
response with appropriate caveats.

**Input**: All previous component outputs.

**Process**:

1. **Rank predictions** by consensus across methods and cross-country
   consistency
2. **Flag high-confidence predictions**: all methods agree + historical
   analogues confirm + trend agrees
3. **Flag uncertain predictions**: method disagreement, zone sign flips,
   noise-dominated forecasts
4. **Generate narrative** via LLM: translate construct-level results into plain
   language, tailored to audience (general public vs. social scientist)
5. **Attach caveats**: CIA limitation, monotonic-only, sampling noise floor,
   observational-not-causal

**LLM involvement**: Narrative generation only. All rankings, confidence
scores, and predictions are computed deterministically before the LLM sees them.
The LLM's job is translation to natural language, not computation.

---

## 6. Adaptation of Ontology Concepts to WVS

### 6.1 What Transfers Directly

| Concept | los_mex → WVS | Notes |
|---------|---------------|-------|
| Construct keys | `DOMAIN\|name` format | Same naming convention |
| Fingerprint structure | 4D SES vector | Same 4 dimensions |
| Bridge edges | Significant γ pairs | Same estimator |
| Dijkstra path finding | Weight = -log(\|γ\|) | Same algorithm |
| Camp bipartition | Signed Laplacian Fiedler | Same math |

### 6.2 What Changes

#### 6.2a Lifting (item → construct)

**los_mex**: Complex multi-step lift through survey boundaries. Items belong to
specific surveys; constructs aggregate items within a survey; bridges connect
constructs across surveys. The `_lift_to_construct()` cascade handles exact,
approximate, domain_fallback, and no_constructs_in_domain cases.

**WVS**: Simpler. All items are in the same questionnaire per wave. Lifting is
a direct lookup: item Q-code → construct membership (from
`semantic_variable_selection_v4.json` WVS equivalent). No cross-survey
boundaries.

**However**, lifting gains a new dimension: **wave awareness**. Not all items
exist in all waves (W3 has 24 constructs, W7 has 55). The lift must check
whether the target construct exists in the requested wave.

#### 6.2b Bridge Network (single → family)

**los_mex**: One bridge network (93 constructs, 984 edges). One bipartition.
One set of fingerprints.

**WVS**: A family of bridge networks indexed by context (country, wave). Each
context has its own weight matrix, its own bipartition, its own fingerprints.
The engine must load the correct graph for the requested context.

**Aggregate network**: For cross-country queries, the engine can also operate on
an aggregate network (e.g., median γ across all countries in a zone, or across
all countries globally). This is analogous to the los_mex single network but
derived from WVS data. The aggregate captures "typical" SES structuring; per-
country graphs capture local variation.

#### 6.2c Fingerprints (global → contextual)

**los_mex**: One fingerprint per construct, computed from Mexican survey data.

**WVS**: One fingerprint per (construct, context). The same construct has
different SES correlations in different countries. The fingerprint dot product
→ γ sign prediction (99.4% in los_mex) may vary by context.

**Design decision**: Store both per-context fingerprints (for local queries)
and global-median fingerprints (for cross-country comparisons).

#### 6.2d Path Finding

**los_mex**: Dijkstra on the single 93-construct bridge network.

**WVS**: Dijkstra on a context-specific graph. The path from construct A to
construct B may differ by country — different edges may be significant,
different intermediaries may be on the shortest path.

**Cross-country paths**: A new query type not possible in los_mex. "How does
construct A in country X relate to construct B in country Y?" This requires
the multilayer framework (Stage 4 of message passing) — GW transport plans
bridge between country-specific graphs.

---

## 7. Integration Model

### 7.1 How the Three Layers Combine

```
                    ┌─────────────────────┐
                    │   QUERY INPUT        │
                    │   (natural language)  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  CONTEXT RESOLVER     │ ← LLM (parse only)
                    │  construct + country  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────────┐
              │                │                     │
    ┌─────────▼──────┐ ┌──────▼──────────┐ ┌───────▼────────┐
    │  STRUCTURE      │ │  DYNAMICS       │ │  GEOMETRY       │
    │  (Ontology)     │ │  (Msg Passing)  │ │  (TDA)          │
    │                 │ │                 │ │                 │
    │ • Load graph    │ │ • BP inference  │ │ • Spectral dist │
    │ • Fingerprints  │ │ • PPR influence │ │ • Fiedler traj  │
    │ • Camp/bipart   │ │ • Heat diffusion│ │ • Mediator stab │
    │ • Dijkstra path │ │ • Temporal fcst │ │ • Hist analogues│
    └─────────┬──────┘ └──────┬──────────┘ └───────┬────────┘
              │                │                     │
              └────────────────┼─────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  NARRATIVE SYNTHESIS  │ ← LLM (translate only)
                    │  structured output    │
                    └──────────────────────┘
```

### 7.2 What Each Layer Contributes Per Query Type

| Query Type | Structure | Dynamics | Geometry |
|------------|-----------|----------|----------|
| **Shock Propagation** | Graph, fingerprints, camp context | BP + PPR + spectral (primary) | — |
| **Cross-Country** | Graph per neighbor | Propagation per neighbor | Spectral distances, zone patterns (primary) |
| **Temporal** | Graph per wave | Temporal forecast (primary) | Fiedler trajectory, mediator stability |
| **Pathway** | Dijkstra path (primary) | PPR for path validation | — |

### 7.3 Information Flow

The three layers are not pipelines — they cross-inform:

- **Structure → Dynamics**: The graph topology determines what BP/PPR/spectral
  can compute. Isolated constructs (no edges) produce zero propagation.
- **Dynamics → Structure**: PPR hub scores and BP lifts enrich the structural
  profile of each construct (beyond static fingerprint + degree).
- **Geometry → Dynamics**: Spectral distances determine which other countries'
  propagation results are transferable. Fiedler trajectory modulates confidence
  in temporal forecasts.
- **Dynamics → Geometry**: Per-country propagation patterns can be compared
  across countries as a higher-order similarity metric (beyond spectral
  distance). Two countries with similar propagation profiles for the same
  anchor construct are "dynamically similar" even if their spectra differ.

---

## 8. Scope Boundaries

### 8.1 What the Engine Can Do

- Identify which attitudes are SES-coupled to a target attitude in a specific
  country
- Rank these by multiple propagation methods and assess consensus
- Find countries with similar attitude network structure
- Identify where the same shock would produce different effects (sign flips)
- Project forward using network-regularized trends with honest uncertainty
- Enumerate the SES-mediated pathway between any two attitudes
- Identify structural hubs and mediators

### 8.2 What the Engine Cannot Do

- **Causal claims**: γ measures SES-mediated covariation, not causal effects.
  "If we intervene on X, Y changes" is NOT a valid interpretation.
- **Non-monotonic effects**: γ detects only monotonic associations. U-shaped or
  threshold effects are invisible (NMI was universally low, so this is rare).
- **Real-time tracking**: The engine operates on WVS wave data (latest: 2018).
  It cannot track current events.
- **Individual-level prediction**: All estimates are population-level construct
  aggregates. No individual respondent modeling.
- **Events outside the construct space**: Only the 55 WVS constructs (and their
  constituent items) can be queried. Events affecting attitudes not in this set
  are out of scope.
- **Precise magnitude forecasting**: Temporal uncertainty envelopes are wide.
  The engine can identify direction but rarely magnitude.
- **Non-SES-mediated effects**: Direct attitude-to-attitude effects that bypass
  the 4 SES dimensions are invisible to the γ-surface.

### 8.3 Coverage

| Dimension | Available | Notes |
|-----------|-----------|-------|
| Countries | 100 (W3-W7 combined) | 66 in W7 with full MP outputs |
| Waves | 5 (W3=1996, W4=2000, W5=2007, W6=2012, W7=2018) | |
| Constructs | 55 (W7), down to 24 (W3) | Wave-dependent |
| Temporal panels | 37 countries with ≥3 waves | For forecasting |
| Message passing | 66 countries (W7 only) | BP, PPR, spectral |
| TDA | 100 countries × 5 waves | Spectral, Floyd-Warshall, Ricci, PH |

---

## 9. Module Layout

```
navegador/
├── graph_traversal_engine/
│   ├── __init__.py
│   ├── context.py              # Context, ContextGraph, GraphFamily
│   ├── resolver.py             # ContextResolver (LLM parse + construct match)
│   ├── propagator.py           # LocalPropagator (BP + PPR + spectral)
│   ├── projector.py            # CrossContextProjector + TemporalProjector
│   ├── synthesizer.py          # NarrativeSynthesizer (LLM narrative)
│   ├── engine.py               # Main entry point: query → TraversalResult
│   └── data_loader.py          # Load pre-computed MP, TDA, fingerprint data
```

---

## 10. Dependencies

### 10.1 Data Dependencies (pre-computed, read-only at query time)

| Data | Source | Path |
|------|--------|------|
| γ weight matrices | Julia DR sweep | `data/tda/matrices/{ALPHA3}.csv` |
| BP lift matrices | `mp_belief_propagation.py` | `data/tda/message_passing/{ALPHA3}_bp.json` |
| PPR matrices | `mp_ppr_influence.py` | `data/tda/message_passing/{ALPHA3}_ppr.json` |
| Spectral decompositions | `mp_spectral_diffusion.py` | `data/tda/message_passing/{ALPHA3}_spectral.json` |
| Temporal dynamics | `mp_temporal_descriptive.py` | `data/tda/message_passing/{ALPHA3}_temporal.json` |
| Spectral distance matrix | `tda_spectral_distances.jl` | `data/tda/spectral/spectral_distance_matrix.csv` |
| Fiedler heatmap | `tda_allwave_analysis.py` | `data/tda/allwave/convergence/fiedler_heatmap.csv` |
| Mediator stability | `tda_allwave_analysis.py` | `data/tda/allwave/convergence/mediator_stability.json` |
| Floyd-Warshall mediators | `tda_floyd_warshall.jl` | `data/tda/floyd_warshall/mediator_scores.json` |
| Construct manifest | TDA pipeline | `data/tda/matrices/manifest.json` |

### 10.2 New Data to Compute

| Data | What | How |
|------|------|-----|
| WVS per-country fingerprints | 4D SES ρ per construct per country | Spearman ρ from WVS microdata |
| WVS per-country bipartitions | Signed Laplacian Fiedler per country | From weight matrices (fast) |
| Construct embedding index | Semantic search over 55 construct descriptions | Pre-compute once |
| All-wave MP outputs | BP/PPR/spectral for W3-W6 (currently W7 only) | Run existing MP scripts on allwave matrices |

### 10.3 Software Dependencies

- numpy, scipy (matrix operations, eigendecomposition, Dijkstra)
- LangChain / direct API (LLM parse + narrative generation)
- ChromaDB or simple cosine search (construct semantic matching)
- Existing: `wvs_metadata.py`, `wvs_loader.py` (WVS data access)

---

## 11. Performance Requirements

| Operation | Target | Justification |
|-----------|--------|---------------|
| Query resolution | < 2s | LLM API call dominates |
| Local propagation | < 100ms | Pre-computed matrix lookups |
| Cross-country projection (5 neighbors) | < 500ms | 5 × matrix lookups |
| Temporal forecast | < 100ms | Pre-computed model evaluation |
| Narrative generation | < 3s | LLM API call |
| **Total end-to-end** | **< 6s** | Acceptable for interactive use |

All computation-heavy work (DR bridge estimation, message passing, TDA) is done
offline in batch. The engine is a query layer over pre-computed results.
