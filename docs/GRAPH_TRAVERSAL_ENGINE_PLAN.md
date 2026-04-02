# Graph Traversal Engine — Implementation Plan

## 0. Conceptual Motivation

### Why This Engine Exists

The navegador project has computed a rich multi-dimensional object: the
**γ-surface** — a function γ(construct_pair, country, wave, SES_reference) that
maps how sociodemographic position structures the covariation of attitudes
across 100 countries and 30 years. Three analytical subsystems have been built
on this surface, each illuminating a different facet:

1. **The Ontology** answers "what is connected to what?" — static graph
   structure, SES fingerprints, camp membership, shortest paths.

2. **Message Passing** answers "how does signal flow?" — equilibrium inference
   (BP), influence propagation (PPR), multi-scale diffusion (heat kernel),
   temporal forecasting.

3. **TDA** answers "how does structure vary?" — spectral distances between
   country networks, Fiedler connectivity trajectories, persistent topological
   features, mediator stability across waves.

These three subsystems speak about the same reality but in different languages.
The engine is a **translator** that chains them into a single query path.

The fundamental intellectual question the engine addresses: **if something
changes in one corner of the attitude landscape, what reverberates, where, and
for how long?** This is not causal prediction — it is structural inference about
the geometry of sociodemographic stratification.

### The Three Layers as Epistemic Modes

Each layer provides a distinct epistemic mode:

**Structure (Ontology)** = the geometry of the graph. It tells you which
constructs are close and which are far, where the camps divide, which SES
dimensions dominate each region of the attitude space. This is the *map*.

**Dynamics (Message Passing)** = the physics on the graph. Given the map, how
does a perturbation propagate? BP treats the network as a probabilistic
graphical model and computes conditional implications. PPR treats it as a flow
network and computes steady-state influence. Spectral diffusion treats it as a
physical medium and computes wave-like propagation at multiple scales. These are
three *physical metaphors* applied to the same map, each revealing different
aspects:

| Metaphor | BP (MRF) | PPR (random walk) | Spectral (heat) |
|----------|----------|-------------------|-----------------|
| Physics | Statistical mechanics | Stochastic process | Diffusion PDE |
| What propagates | Probability mass | Random walkers | Heat / signal |
| Time concept | Equilibrium (no time) | Steady-state (infinite time) | Continuous time t |
| Edge signs | Used (Potts coupling) | Discarded (|γ|) | Discarded (|γ|) |
| Scale sensitivity | No (equilibrium) | Controlled by α | Controlled by t |
| Output | Posterior distributions | Influence matrix | Scale-dependent profiles |

The fact that three different physical metaphors operate on the same graph is a
*feature*: when they agree, the finding is robust to modeling assumptions. When
they disagree, the disagreement itself is informative — it reveals which aspect
of the graph structure (sign structure, degree distribution, spectral gap)
drives the result.

**Geometry (TDA)** = the meta-structure. It tells you how the map itself varies
across contexts. Two countries with small spectral distance have similar maps —
a finding about propagation in one transfers to the other. Fiedler trajectories
tell you whether a country's map is tightening (shocks propagate further over
time) or loosening (shocks become more contained). Persistent homology tells you
whether the map has robust topological features (loops, voids) or is tree-like
(hierarchical). This layer is the *atlas* — a map of maps.

### Why Not Just One Method?

One could argue that PPR alone is sufficient for propagation queries. But each
method has blind spots:

- **BP sees signs, PPR doesn't.** BP uses the Potts model to distinguish
  concordant (γ > 0) from discordant (γ < 0) coupling. PPR uses |γ| and
  discards sign. For a query "if trust increases, does religiosity increase or
  decrease?", PPR tells you religiosity is affected but not the direction. BP
  tells you the direction.

- **Spectral sees scales, BP doesn't.** BP computes a single equilibrium. The
  heat kernel shows how signal spreads at different time scales — a construct
  may be strongly affected at short range (direct neighbor) but weakly at long
  range (the signal dissipates through many hops). This scale structure is
  invisible to BP.

- **PPR sees asymmetry, spectral doesn't.** Even on an undirected graph, PPR
  produces asymmetric influence (Πⱼᵢ ≠ Πᵢⱼ) because degree heterogeneity
  creates directional bias. High-degree nodes influence more than they are
  influenced. The spectral decomposition, being based on the symmetric
  Laplacian, cannot capture this.

Using all three and checking consensus gives a more robust answer than any
single method.

---

## 1. Mathematical Structures

### 1.1 The γ-Surface as a Tensor

The complete γ-surface is a 4-index object:

$$\gamma_{ijcw} = \gamma(\text{construct}_i, \text{construct}_j, \text{country}_c, \text{wave}_w)$$

where:
- $i, j \in \{1, ..., 55\}$ — WVS constructs
- $c \in \{1, ..., 100\}$ — countries
- $w \in \{3, 4, 5, 6, 7\}$ — WVS waves

Each slice $\gamma_{..cw}$ is a 55×55 symmetric matrix — the weight matrix for
context $(c, w)$. The full tensor has ~55² × 100 × 5 ≈ 1.5M entries, of which
~30% are observed (the rest are structural zeros from missing construct pairs or
country-wave combinations).

The engine's three layers operate on different slices and projections of this
tensor:

| Layer | Slice | Operation |
|-------|-------|-----------|
| Structure | $\gamma_{..cw}$ (single context) | Graph construction, paths, camps |
| Dynamics | $\gamma_{..cw}$ (single context) | BP, PPR, spectral on one matrix |
| Geometry | $\gamma_{ijc.}$ or $\gamma_{ij.w}$ | Cross-country or cross-wave comparison |

### 1.2 Context Graph Construction

For context $(c, w)$, the weight matrix is:

$$W^{(c,w)} \in \mathbb{R}^{55 \times 55}, \quad W^{(c,w)}_{ij} = \gamma_{ijcw}$$

with $W_{ij} = \text{NaN}$ for pairs not estimated (missing items, K<3 after
binning, or pair timeout). These are *structural zeros*, not zero-weight edges.

**Adjacency**: An edge $(i, j)$ exists in context $(c, w)$ if $W_{ij}$ is
non-NaN and the 95% CI from the DR bootstrap excludes zero
($\text{excl\_zero} = \text{true}$).

**Distance**: For path-finding, edge distance is $d_{ij} = -\log|\gamma_{ij}|$.
This transforms the product of |γ| values along a path into a sum of costs
(Dijkstra minimizes additive cost ≡ maximizes multiplicative |γ| product).

**Signal chain**: The predicted signal attenuation along a path
$i \to k_1 \to k_2 \to \cdots \to j$ is:

$$\text{signal} = \prod_{\text{edges}} |\gamma_{\text{edge}}|$$

For a typical 2-hop path with |γ| ≈ 0.05 per edge, signal ≈ 0.0025 — heavy
attenuation. The engine flags paths with signal < 0.001 as "attenuation
warning."

### 1.3 SES Fingerprint Geometry

Each construct $i$ in context $(c, w)$ carries a 4D fingerprint vector:

$$\mathbf{f}^{(c,w)}_i = (\rho^{\text{escol}}_i, \rho^{\text{Tam\_loc}}_i, \rho^{\text{sexo}}_i, \rho^{\text{edad}}_i)$$

where each component is the Spearman rank correlation between the construct
score and the SES dimension in the specific (country, wave) population.

**Fingerprint dot product → γ sign prediction**: In los_mex,
$\text{sign}(\mathbf{f}_i \cdot \mathbf{f}_j)$ predicts $\text{sign}(\gamma_{ij})$
at 99.4% accuracy. This is a geometric consequence: two constructs whose SES
profiles point in the same 4D direction are co-elevated by the same
sociodemographic position → γ > 0. Two constructs pointing in opposite
directions are counter-elevated → γ < 0.

**Context dependence**: The fingerprint of construct $i$ may differ across
countries. If $\rho^{\text{escol}}_i > 0$ in Mexico but $\rho^{\text{escol}}_i < 0$
in Pakistan, the construct has opposite SES gradients in the two populations.
This is not an error — it reflects genuine social structure differences.

**Camp bipartition**: The signed Laplacian of $W^{(c,w)}$:

$$L_s = D_{|W|} - W$$

where $D_{|W|}$ is the diagonal degree matrix of absolute weights. The Fiedler
vector (second-smallest eigenvector of $L_s$) bipartitions constructs into two
camps. The partition is oriented so that camp +1 has higher median $\rho_{\text{escol}}$
("cosmopolitan": elevated by education and urbanization) and camp -1 has higher
median $\rho_{\text{edad}}$ ("tradition": elevated by older age and rural
residence).

The bipartition is **context-specific**. The engine computes it per (country,
wave) rather than assuming a single global partition.

### 1.4 Propagation Mathematics

#### 1.4a Belief Propagation (Potts MRF)

The joint distribution over construct states $\mathbf{x} = (x_1, ..., x_{55})$,
$x_i \in \{1, 2, 3, 4, 5\}$ (five quintile bins):

$$P(\mathbf{x}) \propto \prod_{i} \phi_i(x_i) \prod_{(i,j) \in E} \psi_{ij}(x_i, x_j)$$

Node potential: $\phi_i(x_i)$ = empirical marginal (or uniform 1/5).

Edge potential (Potts):
$$\psi_{ij}(x_i, x_j) = \begin{cases}
\exp(\beta |\gamma_{ij}|) & \text{if } (x_i = x_j \wedge \gamma_{ij} > 0) \text{ or } (x_i \neq x_j \wedge \gamma_{ij} < 0) \\
1 & \text{otherwise}
\end{cases}$$

Loopy BP message update (with damping $\lambda = 0.5$):

$$m_{i \to j}^{(t+1)}(x_j) = \lambda \cdot m_{i \to j}^{(t)}(x_j) + (1 - \lambda) \cdot \sum_{x_i} \psi_{ij}(x_i, x_j) \phi_i(x_i) \prod_{k \in \mathcal{N}(i) \setminus j} m_{k \to i}^{(t)}(x_i)$$

Belief at convergence: $b_i(x_i) \propto \phi_i(x_i) \prod_{k \in \mathcal{N}(i)} m_{k \to i}(x_i)$

**Lift** (shock signal): $\text{KL}(b_j \| \phi_j)$ when evidence is clamped at
construct $i$ — measures how much the posterior at $j$ diverges from the prior.

**Pre-computation**: For each context, run all 55 single-evidence scenarios
(clamp each construct at state 4 = top quintile). Store the 55×55 lift matrix.
At query time, look up the anchor's row.

#### 1.4b Personalized PageRank

Transition matrix: $P = D^{-1}|W|$ (row-normalized absolute weights).

PPR vector seeded at node $i$:

$$\boldsymbol{\pi}^{(i)} = \alpha \mathbf{e}_i + (1 - \alpha) P^\top \boldsymbol{\pi}^{(i)}$$

Closed form: $\boldsymbol{\pi}^{(i)} = \alpha (I - (1-\alpha)P^\top)^{-1} \mathbf{e}_i$

Hub score: $h_i = \sum_{j \neq i} \pi^{(i)}_j$ (total outgoing influence).

Sink score: $s_j = \sum_{i \neq j} \pi^{(i)}_j$ (total incoming influence).

Asymmetry: $A_{ij} = \pi^{(i)}_j - \pi^{(j)}_i$ (directional dominance).

**Sign restoration**: PPR uses $|W|$ and produces unsigned influence values. To
predict direction of effect, multiply by $\text{sign}(\gamma_{ij})$ for direct
neighbors. For multi-hop influence, the sign is determined by the parity of
negative edges along the dominant path (tracked via Dijkstra with sign
accumulation).

#### 1.4c Spectral Diffusion (Heat Kernel)

Normalized Laplacian: $\mathcal{L} = I - D^{-1/2} |W| D^{-1/2}$

Eigendecomposition: $\mathcal{L} = U \Lambda U^\top$ where $\Lambda = \text{diag}(\lambda_0, ..., \lambda_{54})$

Heat kernel: $H(t) = e^{-\mathcal{L}t} = U \, \text{diag}(e^{-\lambda_0 t}, ..., e^{-\lambda_{54} t}) \, U^\top$

Response at construct $j$ from impulse at construct $i$ after time $t$:

$$H(t)_{ji} = \sum_{k=0}^{54} e^{-\lambda_k t} \, u_k(j) \, u_k(i)$$

**Multi-scale profile**: By computing $H(t)_{ji}$ at $t \in \{0.1, 0.5, 1.0, 5.0\}$,
we get a scale-dependent influence profile. Small $t$ captures local (direct
neighbor) effects; large $t$ captures global (whole-network) structure.

**Diffusion distance**: $D_t(i,j)^2 = \sum_k e^{-2\lambda_k t} (u_k(i) - u_k(j))^2$

This is a time-parameterized metric. At the characteristic time
$t^* = 1/\lambda_1$ (inverse Fiedler value, ≈1.4 for WVS networks), the Fiedler
mode dominates and constructs are separated by their camp membership.

### 1.5 Cross-Context Comparison

#### Spectral Distance

For two contexts $(c_1, w)$ and $(c_2, w)$ (same wave, different countries):

$$d_{\text{spectral}}(c_1, c_2) = \|\boldsymbol{\lambda}^{(c_1)} - \boldsymbol{\lambda}^{(c_2)}\|_2$$

where $\boldsymbol{\lambda}^{(c)}$ is the sorted eigenvalue vector of country $c$'s
normalized Laplacian. This measures structural similarity: countries with similar
spectra have similar diffusion dynamics.

**Use in engine**: The spectral distance matrix (66×66 for W7) identifies which
countries are structural neighbors. When projecting propagation results from
Mexico to other countries, the engine prioritizes countries with small spectral
distance to Mexico.

#### Fiedler Trajectory

For a country $c$ across waves $w_1, ..., w_T$:

$$\lambda_1^{(c)}(w_1), \lambda_1^{(c)}(w_2), ..., \lambda_1^{(c)}(w_T)$$

This is the country's **algebraic connectivity trajectory**. Increasing Fiedler
→ tightening network → shocks propagate further. Decreasing → loosening →
shocks are more contained.

**Use in engine**: Modulates confidence in temporal forecasts. If a country's
Fiedler is declining, the network's predictive power is weakening (beliefs are
decoupling from SES structure), and forecasts should carry wider uncertainty.

### 1.6 Temporal Forecasting

Network autoregression (1-parameter):

$$\hat{\mathbf{x}}(w+1) = \alpha^* \cdot A^{(w)} \cdot \mathbf{x}(w) + (1 - \alpha^*) \cdot \mathbf{x}(w)$$

where $A^{(w)} = D^{-1}|W^{(w)}|$ is the row-normalized absolute weight matrix
at wave $w$, and $\mathbf{x}(w)$ is the vector of mean construct responses at
wave $w$.

$\alpha^*$ is fitted by minimizing prediction error across all available
wave transitions:

$$\alpha^* = \arg\min_\alpha \sum_{t=1}^{T-1} \|\hat{\mathbf{x}}^{(\alpha)}(w_{t+1}) - \mathbf{x}(w_{t+1})\|^2$$

This is a 1D optimization over $n_{\text{constructs}} \times (T-1)$ observations.

**Uncertainty**: Per-construct residual standard deviation across wave
transitions → 80% prediction interval: $\hat{x}_i \pm 1.28 \sigma_i$.

**Shock injection**: To forecast the effect of an external shock at construct $i$,
modify $\mathbf{x}(w_{\text{current}})$ by the shock magnitude, then apply the
forecast equation. The network propagates the shock according to its
adjacency structure, blended with persistence.

---

## 2. LLM Involvement

The engine uses LLMs at exactly two points, both at the boundary between human
language and formal structure. All computation is deterministic.

### 2.1 Query Resolution (Input Boundary)

**Where**: `ContextResolver.resolve(query: str) → list[Anchor]`

**LLM task**: Extract structured fields from natural language.

**Prompt structure**:
```
You are parsing a query about attitudes and public opinion.

Available constructs (55 WVS constructs):
{construct_list_with_descriptions}

Available countries: {country_list}
Available waves: W3 (1996), W4 (2000), W5 (2007), W6 (2012), W7 (2018)

Query: "{user_query}"

Extract:
1. concept: What attitude/belief is being discussed?
2. direction: Is it increasing, decreasing, or unspecified?
3. magnitude: weak / moderate / strong / unspecified
4. country: Which country? (default: unspecified)
5. wave: Which time period? (default: latest available)
6. construct_matches: Which of the 55 constructs best match the concept?
   Rank top 3 by relevance, with confidence 0-1.
7. multi_anchor: Does this event affect multiple constructs simultaneously?
   If yes, list all affected constructs.

Return as JSON.
```

**Why LLM here**: Semantic matching between free-text concepts and construct
labels requires natural language understanding. "Trust in scientists" should
match `science_skepticism|WVS_I` (inverted) and
`household_science_cultural_capital|WVS_I`. This is a classification task
where the label space (55 constructs) is small and stable.

**Fallback**: If LLM is unavailable, use cosine similarity between query
embedding and pre-computed construct description embeddings. Lower quality but
functional.

### 2.2 Narrative Synthesis (Output Boundary)

**Where**: `NarrativeSynthesizer.synthesize(result: TraversalResult) → str`

**LLM task**: Translate structured results into natural language.

**Prompt structure**:
```
You are writing a brief analysis of how an attitude shift propagates through
a society's belief network.

Context:
- Country: {country} ({zone} cultural zone)
- Anchor: {construct_name} ({direction})
- Network: {n_constructs} constructs, Fiedler={fiedler_value}

Propagation results (top 10 affected constructs):
{ranked_predictions_with_confidence}

Cross-country findings:
{projection_summary}

Temporal trajectory:
{forecast_summary}

Caveats: {caveats_list}

Write a 3-4 paragraph analysis. Lead with the main finding. Mention the
strongest downstream effects and their SES dimensions. Note where cross-
country patterns agree or diverge. End with the temporal outlook and honest
uncertainty. Do not use causal language ("causes", "leads to"); use
associative language ("co-varies with", "is SES-coupled to", "the network
implies").
```

**Why LLM here**: The structured output contains construct keys, γ values,
confidence levels, and zone names. Translating this into readable prose for
a general audience or a social scientist requires language generation. The
LLM adds no information — it reformats what the engine has already computed.

### 2.3 Where LLMs Are NOT Used

- **Propagation computation**: BP, PPR, and spectral diffusion are deterministic
  matrix operations. No LLM.
- **Cross-country projection**: Spectral distance lookup and zone aggregation
  are deterministic. No LLM.
- **Temporal forecasting**: Network autoregression is a fitted linear model.
  No LLM.
- **Path finding**: Dijkstra is a graph algorithm. No LLM.
- **Confidence scoring**: Method consensus is computed by counting agreements.
  No LLM.
- **Sign prediction**: Fingerprint dot product is a vector operation. No LLM.

This separation is deliberate: the engine's substantive claims are
reproducible and auditable because they come from deterministic algorithms.
The LLM handles only the human-language interface.

---

## 3. WVS Ontology: What Must Be Built

### 3.1 WVS Fingerprints (Per-Country)

**Current state**: WVS fingerprints exist only for Mexico W7
(`wvs_ses_fingerprints.json`). The geographic sweep has γ values for all 66
countries, but per-construct SES correlations (Spearman ρ with each of 4 SES
dimensions) have not been computed per country.

**What to compute**: For each context (country, wave) with WVS microdata
available:
1. Load microdata via `wvs_loader.py`
2. For each construct, compute Spearman ρ against escol, Tam_loc, sexo, edad
3. Store as `{country}_W{wave}_fingerprints.json`

**Use**: Fingerprints enable camp bipartition, sign prediction, SES dimension
identification ("the dominant driver of this association is education"), and
similarity search.

**Fallback for countries without microdata**: Use the γ weight matrix to infer
approximate fingerprints. The fingerprint dot product predicts γ sign at 99.4%
— this constraint, plus the known γ matrix, constrains the fingerprint space.
However, direct computation from microdata is strongly preferred.

### 3.2 WVS Bipartitions (Per-Country)

**Current state**: No per-country bipartitions exist. The los_mex ontology has
one global bipartition.

**What to compute**: For each context with a weight matrix:
1. Build signed Laplacian $L_s = D_{|W|} - W$
2. Compute Fiedler vector
3. Orient by median $\rho_{\text{escol}}$ of candidate camps
4. Assign camps, compute confidence and frustrated triangle ratios

**Cross-country consistency**: Compare Fiedler partitions across countries using
Adjusted Rand Index (already computed in message passing: `fiedler_comparison.json`).
Countries in the same zone should have similar partitions (spectral zone
coherence p=0.001).

### 3.3 WVS Construct Descriptions

**Current state**: Construct labels exist (e.g., `gender_role_traditionalism`),
but no natural-language descriptions optimized for semantic search.

**What to build**: A JSON file mapping each WVS construct key to:
- `label`: human-readable name
- `description`: 1-2 sentence description of what the construct measures
- `example_items`: 2-3 example survey questions
- `domain`: WVS domain code
- `polarity`: "higher = more X" interpretation

This serves as the embedding corpus for construct matching in query resolution.

### 3.4 WVS OntologyQuery Adapter

The existing `OntologyQuery` class assumes los_mex data structures. Rather than
modifying it (which would break los_mex functionality), build a new
`WVSOntologyQuery` class that:

1. Accepts a `context: (country, wave)` parameter
2. Loads the context-specific weight matrix, fingerprints, and bipartition
3. Provides the same API surface: `get_profile()`, `get_similar()`,
   `explain_pair()`, `get_neighbors()`, `get_neighborhood()`, `find_path()`,
   `get_camp()`
4. Adds new methods: `get_cross_country_profile()`,
   `compare_contexts(ctx_a, ctx_b)`

**Key difference**: Every method is context-aware. `find_path("MEX", 7, construct_a, construct_b)`
and `find_path("DEU", 7, construct_a, construct_b)` may return different paths
because the graphs are different.

---

## 4. Integration Architecture

### 4.1 The Query Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                        ENGINE.QUERY()                          │
│                                                                │
│  1. ContextResolver.resolve(query)                             │
│     └─ LLM parse → anchors + context                          │
│                                                                │
│  2. DataLoader.load(context)                                   │
│     └─ Weight matrix + MP outputs + TDA features → ContextGraph│
│                                                                │
│  3. STRUCTURE LAYER                                            │
│     ├─ WVSOntologyQuery(context)                               │
│     │  └─ Fingerprint profile, camp membership, mediator rank  │
│     └─ PathFinder.find_path(anchor_a, anchor_b, context)       │
│        └─ Dijkstra + signal chain + sign accumulation          │
│                                                                │
│  4. DYNAMICS LAYER (parallel)                                  │
│     ├─ BPPropagator.propagate(anchor, context)                 │
│     │  └─ Lift matrix row lookup → conditional inference       │
│     ├─ PPRPropagator.propagate(anchor, context)                │
│     │  └─ PPR column lookup → influence ranking                │
│     └─ SpectralPropagator.propagate(anchor, context)           │
│        └─ Heat kernel at multiple t → scale profile            │
│                                                                │
│  5. GEOMETRY LAYER                                             │
│     ├─ SpectralProjector.project(context, scope)               │
│     │  └─ Spectral neighbors + zone aggregation                │
│     ├─ HistoricalSearch.search(anchor, direction)              │
│     │  └─ Temporal data scan for matching shifts               │
│     └─ TemporalProjector.forecast(anchor, context)             │
│        └─ Network autoregression + trend + Fiedler trajectory  │
│                                                                │
│  6. RECONCILIATION                                             │
│     └─ Consensus scoring across BP/PPR/spectral/cross-country  │
│                                                                │
│  7. NarrativeSynthesizer.synthesize(all_results)               │
│     └─ LLM narrative + structured output                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 How Ontology and Message Passing Integrate

The ontology provides the **structural frame** that message passing operates
within. Specifically:

**Ontology provides to Message Passing:**
- The weight matrix (which edges exist, with what γ)
- Construct membership in camps (for interpreting propagation direction)
- SES fingerprints (for predicting and validating propagation signs)
- Mediator identification (which constructs are structural bridges)

**Message Passing provides to Ontology:**
- Dynamic enrichment: hub scores, sink scores, lift profiles add to the static
  fingerprint
- Propagation-based distance: two constructs may be structurally far (many
  hops on Dijkstra) but dynamically close (high PPR influence due to degree
  structure). This creates a second distance metric on the construct space.
- Temporal dynamics: the ontology is static; message passing adds a time
  dimension through the forecast model

**Integration point — path validation**: When the ontology finds a Dijkstra
path A → B → C (strongest γ chain), message passing validates it:
- Does BP show high lift from A to C? (If yes, the path carries conditional
  inference.)
- Does PPR show A as upstream of C? (If yes, the influence flows in the
  expected direction.)
- Does spectral diffusion reach C from A at the appropriate time scale?
  (If only at large t, the path is indirect; if at small t, it's direct.)

If Dijkstra says "the path goes through B" but PPR says "A influences C
directly without B", then B is on the *shortest* path but not the *dominant*
influence path — the signal takes a parallel route through degree-weighted
shortcuts.

### 4.3 How TDA Adds Up

TDA operates at a higher level of abstraction than ontology or message
passing. It characterizes the **landscape of graphs** rather than individual
graphs.

**TDA provides:**

1. **Transfer validity**: Spectral distance tells you whether propagation
   results from country A are likely to hold in country B. Small spectral
   distance → similar network dynamics → high transfer validity.

2. **Temporal confidence modulation**: The Fiedler trajectory tells you whether
   the network structure that propagation relies on is stable or changing. A
   stable Fiedler trajectory (like India's, ~0.72 for 20 years) means the
   network structure is reliable; a declining trajectory (like Germany's,
   0.82→0.70) means the structure is loosening and predictions from earlier
   waves may not hold.

3. **Topological context**: β₁ (persistent loops) tells you whether the network
   has redundant pathways. Networks with loops (early waves, some countries)
   have multiple propagation routes → more robust signal transmission.
   Tree-like networks (later waves, trend toward β₁=0) have single pathways →
   mediator constructs become more critical.

4. **Convergence/divergence**: The cross-wave spectral distance trends tell you
   whether countries are becoming more similar (converging) or more different
   (diverging) in their attitude network structure. During convergent periods,
   cross-country projection is more reliable; during divergent periods, it's
   less reliable.

5. **Mediator stability**: The persistence of top mediators across waves tells
   you which structural bridges are "load-bearing" vs. transient. A mediator
   that persists across 4/5 waves (like gender_role_traditionalism in most
   countries) is a fundamental feature of the SES-attitude geometry; one that
   appears only once is likely a statistical artifact.

**TDA does NOT provide:**
- Within-country propagation (that's message passing)
- Construct-level detail (that's ontology)
- Causal direction (none of the layers do)

### 4.4 The Role of Path Finding

Path finding (Dijkstra on the γ-weighted graph) serves a specific purpose that
neither BP nor PPR can substitute:

**Mechanistic explanation.** BP tells you "A implies C." PPR tells you "A
influences C." But neither tells you *through what*. Dijkstra tells you "A
connects to C via B, with γ(A,B) = 0.08 and γ(B,C) = 0.05, meaning the
association is mediated by the education dimension at both hops."

This is critical for narrative synthesis. A social scientist doesn't just want
to know that trust in science co-varies with democratic satisfaction — they want
to know that it does so *through* institutional trust and political engagement,
each hop dominated by the education SES dimension. The path provides the
explanatory story.

**Path finding is the ontology's primary contribution** to query types 1 and 4.
For query type 2 (cross-country), paths matter less (the question is about
whether the *pattern* transfers, not the specific path). For query type 3
(temporal), paths are static (they don't change across waves unless the
weight matrix changes, which it does — different waves have different paths,
which is itself an interesting finding).

---

## 5. Implementation Phases

### Phase 0: WVS Data Foundation

**Goal**: Compute the per-country data that the WVS ontology needs but doesn't
yet have.

| Task | Input | Output | Effort |
|------|-------|--------|--------|
| Per-country fingerprints (W7, 66 countries) | WVS microdata | `data/gte/fingerprints/W7/{ALPHA3}.json` | Medium |
| Per-country bipartitions (W7, 66 countries) | Weight matrices | `data/gte/camps/W7/{ALPHA3}.json` | Light |
| Construct description corpus | Manual + WVS codebook | `data/gte/construct_descriptions.json` | Light |
| Construct embedding index | Description corpus | `data/gte/construct_embeddings.npz` | Light |

**Dependencies**: `wvs_loader.py` (for microdata access), weight matrices
(already computed in `data/tda/matrices/`).

### Phase 1: Structure Layer (WVS Ontology)

**Goal**: `WVSOntologyQuery` class with full API surface.

| Task | Description | Effort |
|------|-------------|--------|
| `context.py` | Context, ContextGraph, GraphFamily dataclasses | Light |
| `data_loader.py` | Load weight matrices + MP outputs + TDA features | Medium |
| `wvs_ontology.py` | Context-aware profile, similarity, paths, camps | Medium |
| Unit tests | Port los_mex ontology tests to WVS context | Medium |

**Key API**:
```python
oq = WVSOntologyQuery(country="MEX", wave=7)
oq.get_profile("gender_role_traditionalism|WVS_D")
oq.find_path("institutional_trust|WVS_E", "science_skepticism|WVS_I")
oq.get_camp("personal_religiosity|WVS_A")
oq.get_neighborhood("democratic_aspiration|WVS_E", min_abs_gamma=0.02)
```

### Phase 2: Dynamics Layer (Propagator)

**Goal**: Unified propagation interface consuming pre-computed MP outputs.

| Task | Description | Effort |
|------|-------------|--------|
| `propagator.py` | BPPropagator, PPRPropagator, SpectralPropagator | Medium |
| Consensus scoring | Method agreement computation | Light |
| Sign restoration | PPR sign from weight matrix signs | Light |
| Unit tests | Verify against raw MP JSON outputs | Light |

**Key API**:
```python
prop = LocalPropagator(context_graph)
result = prop.propagate(
    anchor="institutional_trust|WVS_E",
    direction="decrease",
    magnitude=1.0  # σ units
)
# result.bp_effects, result.ppr_effects, result.spectral_effects
# result.consensus (ranked by agreement)
```

### Phase 3: Geometry Layer (Projector)

**Goal**: Cross-context projection using TDA features.

| Task | Description | Effort |
|------|-------------|--------|
| `projector.py` | SpectralProjector, HistoricalSearch, TemporalProjector | Medium |
| Zone aggregation | Group propagation results by zone, identify sign flips | Medium |
| Historical search | Scan temporal data for matching attitude shifts | Medium |
| Temporal forecast with shock | Extend autoregression to accept external shocks | Light |
| Unit tests | Verify spectral neighbor ranking, forecast accuracy | Medium |

**Key API**:
```python
proj = CrossContextProjector(graph_family)
result = proj.project(
    source_context=("MEX", 7),
    propagation_result=prop_result,
    scope="zone"  # or "global", or specific country
)
# result.spectral_neighbors, result.zone_patterns, result.historical_analogues
```

### Phase 4: Query Resolution + Narrative

**Goal**: LLM-powered input parsing and output narrative.

| Task | Description | Effort |
|------|-------------|--------|
| `resolver.py` | LLM query parse + construct matching | Medium |
| `synthesizer.py` | LLM narrative generation | Medium |
| Prompt engineering | Design and test prompts for both LLM touch points | Medium |
| Structured output | Pydantic models for all result types | Light |

### Phase 5: Engine Integration

**Goal**: Single entry point that chains all layers.

| Task | Description | Effort |
|------|-------------|--------|
| `engine.py` | Main `query()` method orchestrating all components | Medium |
| Query type dispatch | Route to correct component combination per query type | Light |
| Caching | Cache ContextGraph objects (heavy to load) | Light |
| Integration tests | End-to-end query → result tests | Medium |

### Phase 6: Agent Integration

**Goal**: Wire into `agent.py` as a tool for the conversational interface.

| Task | Description | Effort |
|------|-------------|--------|
| Tool definition | LangGraph tool wrapping `engine.query()` | Light |
| Prompt update | Add GTE tool to agent system prompt | Light |
| Dashboard widget | Optional: interactive GTE explorer in Dash | Heavy |

---

## 6. Validation Strategy

### 6.1 Internal Consistency

- **BP ↔ PPR agreement**: For each context, compare top-10 affected constructs
  from BP and PPR. Expected: >70% overlap in top-10.
- **PPR ↔ Dijkstra agreement**: PPR's top influence target should be reachable
  via a short, high-γ Dijkstra path. If PPR ranks a construct highly but
  Dijkstra shows a long, attenuated path, investigate (likely degree-mediated
  shortcut).
- **Fingerprint → sign consistency**: Verify that fingerprint dot product
  predicts γ sign at >95% accuracy per country (known to be 99.4% in los_mex).

### 6.2 Cross-Method Validation

- **BP vs. PPR vs. spectral disagreement cases**: Catalog the constructs where
  the three methods disagree. These are structurally interesting: they reveal
  where the choice of physical metaphor matters.
- **PPR hub ↔ Floyd-Warshall mediator**: Compare PPR hub rankings against TDA
  mediator scores. Both measure structural importance but differently (influence
  reach vs. shortest-path bottleneck). Expected: moderate correlation (ρ ≈ 0.5).

### 6.3 Historical Validation

The strongest validation available: **retrospective prediction**.

For each country with ≥3 waves:
1. Use the weight matrix from wave $w$ and mean responses from wave $w$
2. Apply the temporal forecast model to predict wave $w+1$ responses
3. Compare predictions against actual wave $w+1$ observations
4. Track: which constructs are correctly predicted (direction)? What's the
   RMSE? Are high-confidence predictions more accurate?

This tests whether the network structure at one point in time actually predicts
attitude evolution — the core claim of the temporal model.

### 6.4 Cross-Country Validation

For each country pair $(c_1, c_2)$ with small spectral distance:
1. Run propagation on $c_1$ with a given anchor
2. Run propagation on $c_2$ with the same anchor
3. Compare: do the top-5 affected constructs overlap? Do signs agree?
4. Expected: spectral-near countries should have similar propagation patterns.
   If they don't, the spectral distance metric is not predictive of dynamic
   similarity.

---

## 7. Open Questions

### 7.1 Aggregate vs. Per-Country Fingerprints

Should the engine use a global-median fingerprint (one per construct, averaged
across countries) or per-country fingerprints? Arguments:

- **Per-country**: more accurate, captures genuine cross-national variation in
  SES structuring. Needed for per-country bipartitions.
- **Global-median**: more robust (averages out noise), useful for cross-country
  comparisons where a common reference frame is needed.

**Proposed**: compute both. Use per-country for within-country queries, global-
median for cross-country comparisons and as a fallback.

### 7.2 All-Wave Message Passing

Currently, MP outputs (BP, PPR, spectral) exist only for W7 (66 countries).
The allwave TDA pipeline has weight matrices for W3-W7. Should we run MP on
all waves?

- **Pro**: enables per-wave propagation queries, temporal comparison of
  propagation patterns, richer historical validation.
- **Con**: construct sets are much smaller in earlier waves (24 in W3 vs. 55 in
  W7), producing sparser, less reliable propagation results.

**Proposed**: run MP for W5-W7 (where construct coverage is ≥31) and flag W3-W4
as low-coverage contexts with limited propagation reliability.

### 7.3 Multilayer Cross-Country Propagation

Stage 4 of message passing (multilayer GW-coupled propagation) was scoped to
regional subsets due to near-uniform transport plans (3.1% self-match). Should
the engine attempt cross-country propagation?

**Proposed**: defer full multilayer. Instead, use the simpler analogical
transfer approach (Section 5.3): run the same single-country propagation on
spectral neighbors and compare results. This avoids the GW transport plan
problem entirely while still answering "does this pattern hold elsewhere?"

### 7.4 Los_Mex Reintegration

The los_mex ontology has richer item-level detail (6,359 items, orphan loading
approximations, exact loading_gamma values) and domain-specific knowledge
(survey KG relationships). How to bring this back?

**Proposed**: treat los_mex as one more context in the GraphFamily, with its own
weight matrix (the existing 93×93 bridge network) and fingerprints. The 48
grade-3 construct matches from `wvs_losmex_construct_map_v2.json` serve as the
bridge between WVS and los_mex construct spaces. When a user queries about
Mexico, the engine can pull from both WVS (cross-country context) and los_mex
(richer item-level detail).

---

## 8. Summary Table

| Component | Role | Math | LLM? | Data source |
|-----------|------|------|------|-------------|
| ContextResolver | Query → construct + context | Embedding cosine sim | Yes (parse) | Construct descriptions |
| WVSOntologyQuery | Graph structure + paths | Dijkstra, Fiedler, fingerprint geometry | No | Weight matrices, fingerprints |
| BPPropagator | Conditional inference | Potts MRF, loopy BP, KL divergence | No | Pre-computed BP lifts |
| PPRPropagator | Influence flow | Random walk, matrix inversion | No | Pre-computed PPR matrix |
| SpectralPropagator | Multi-scale diffusion | Heat kernel, eigendecomposition | No | Pre-computed spectral decomp |
| CrossContextProjector | Country comparison | Spectral distance, zone aggregation | No | TDA spectral matrix |
| HistoricalSearch | Retrospective validation | OLS trend, residual analysis | No | Temporal sweep data |
| TemporalProjector | Forecast | Network autoregression, 1-param fit | No | Temporal dynamics model |
| NarrativeSynthesizer | Human-readable output | — | Yes (translate) | All previous outputs |
