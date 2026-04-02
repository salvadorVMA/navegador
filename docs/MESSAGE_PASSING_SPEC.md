# Message Passing on WVS Belief Networks
## Technical Specification — Mathematics, Design, Pitfalls, Interpretation

---

## 0. Scope and Prerequisites

This document specifies five propagation stages on the WVS construct networks:

| Stage | Method | Scope | Status |
|-------|--------|-------|--------|
| 1 | Belief Propagation (Potts MRF) | Within-country, all 66 | Full |
| 2 | Spectral Diffusion (heat kernel) | Within-country, all 66 | Full |
| 3 | Personalized PageRank | Within-country, all 66 | Full |
| 4 | Multilayer Message Passing | Regional subsets only | Scoped |
| 5 | Temporal Dynamics + Forecast | Mexico W3-W7 only | Descriptive + constrained forecast |
| ~~6~~ | ~~Curvature-Weighted Dynamics~~ | — | Dropped (κ ≈ 1.0 everywhere) |

### Data assets

| Asset | Path | Shape | Notes |
|-------|------|-------|-------|
| Weight matrices (W7) | `data/tda/matrices/{ALPHA3}.csv` | 55×55 | Signed γ values; empty cells = missing pair |
| Distance matrices | `data/tda/matrices/{ALPHA3}_distance.csv` | 55×55 | 1 - \|γ\| |
| Temporal weights (MEX) | `data/tda/temporal/MEX_W{n}.csv` | 52×52 | Sparse: W3=14%, W7=72% fill |
| Spectral features | `data/tda/spectral/spectral_features.json` | 66 entries | Fiedler, entropy, radius per country |
| GW transport (top 50) | `data/tda/alignment/gw_transport_top50.json` | 55×55 per pair | Only 50/2145 pairs stored |
| GW distance matrix | `data/tda/alignment/gw_distance_matrix.csv` | 66×66 | Full pairwise |
| Spectral distance matrix | `data/tda/spectral/spectral_distance_matrix.csv` | 66×66 | |
| Mediator scores | `data/tda/floyd_warshall/mediator_scores.json` | 66×55 | Top mediator per country |
| Ricci curvature | `data/tda/ricci/ricci_summary.json` | 66 entries | Mean κ = 0.9992 |
| Manifest | `data/tda/matrices/manifest.json` | — | 55 constructs, 8 cultural zones, 66 countries |

### Key data constraints

**Temporal sparsity.** Construct coverage grows across waves:

| Wave | Year | Constructs present | Fill rate |
|------|------|--------------------|-----------|
| W3 | 1996 | 23/52 | 14.2% |
| W4 | 2001 | 24/52 | 15.7% |
| W5 | 2007 | 28/52 | 21.2% |
| W6 | 2012 | 41/52 | 48.7% |
| W7 | 2018 | 49/52 | 72.4% |

**20 constructs** are present in all 5 waves — these form the forecast universe.

**Missing values.** Weight matrices have empty cells where the DR bridge could
not be estimated (insufficient data, K<3 after binning, or pair timeout). These
are structural zeros, not zero-weight edges. All algorithms must distinguish
"no edge" from "zero-weight edge."

---

## Stage 1: Within-Network Belief Propagation

### 1.1 Mathematical Motivation

The construct network for a single country encodes a **Markov random field
(MRF)**: a joint distribution over belief states where conditional independence
mirrors graph structure. Each construct i is conditionally independent of all
non-neighbors given its Markov blanket (direct neighbors).

The joint distribution factorizes as:

$$P(\mathbf{x}) \propto \prod_{i \in V} \phi_i(x_i)
\prod_{(i,j) \in E} \psi_{ij}(x_i, x_j)$$

**Node potential** φᵢ(xᵢ) is the prior marginal of construct i — the empirical
response distribution over the 5-bin quantile categories. For a construct
measured in Mexico W7, this might be φ(x=1) = 0.20, φ(x=2) = 0.20, ...,
φ(x=5) = 0.20 (uniform by construction if using equal-frequency quantile
binning), or a non-uniform distribution if using fixed-width bins.

**Edge potential** ψᵢⱼ(xᵢ, xⱼ) encodes how compatible states xᵢ and xⱼ are,
given the empirical weight wᵢⱼ (= γ from the DR bridge). For ordinal data on
a 5-point scale, the **Potts model** is appropriate:

$$\psi_{ij}(x_i, x_j) = \begin{cases}
\exp(\beta |w_{ij}|) & \text{if } x_i = x_j \text{ and } w_{ij} > 0 \\
\exp(\beta |w_{ij}|) & \text{if } x_i \neq x_j \text{ and } w_{ij} < 0 \\
1 & \text{otherwise}
\end{cases}$$

Positive γ: agreement favored (concordant SES-mediated covariation).
Negative γ: disagreement favored (discordant covariation).
The inverse temperature β controls coupling strength — higher β makes the
network more deterministic.

**Belief propagation** computes approximate marginal posteriors by passing
messages between neighbors. Message from i to j at iteration t:

$$m_{i \to j}^{(t+1)}(x_j) = \sum_{x_i} \psi_{ij}(x_i, x_j)\, \phi_i(x_i)
\prod_{k \in \mathcal{N}(i) \setminus j} m_{k \to i}^{(t)}(x_i)$$

After convergence, the belief at node i is:

$$b_i(x_i) \propto \phi_i(x_i) \prod_{k \in \mathcal{N}(i)} m_{k \to i}(x_i)$$

The **lift** — KL divergence from prior to posterior — ranks how much evidence
at one construct shifts the distribution at each other construct.

### 1.2 Design Choices

**Why Potts over Gaussian.** The Gaussian potential ψ(xᵢ, xⱼ) =
exp(-(xᵢ - wᵢⱼxⱼ)²/2σ²) treats ordinal categories as continuous, imposing
equal inter-category distances. This is empirically false for Likert-type items:
the distance between "strongly agree" and "agree" is not the same as between
"agree" and "neutral." The Potts model avoids this by operating on category
identity, not magnitude. The cost: Potts cannot model the graded structure of
ordinal data (it treats category 1 and category 5 as equally "different" from
category 3). For 5-bin constructs this is acceptable — the bins are quantile
cuts, not semantic anchors.

**β = 2.0.** This is a moderate coupling. At β = 0, edges have no effect and
posteriors equal priors. At β → ∞, the model is deterministic (hard constraints).
β = 2.0 produces noticeable but not overwhelming shifts in posteriors for edge
weights in the observed range (|γ| typically 0.01–0.10). Sensitivity analysis
should sweep β ∈ {0.5, 1.0, 2.0, 4.0} and report which constructs' rankings
are β-stable.

**Damping = 0.5.** Message update is a 50/50 blend of new and old messages.
Without damping, loopy BP on dense graphs oscillates and fails to converge.
At 0.5 damping, convergence is typical within 50–100 iterations for networks
with density ≈ 23%.

**n_states = 5.** Matches the Julia DR bridge binning pipeline: construct
scores are rank-normalized then quantile-cut into 5 bins. Using the same
discretization ensures consistency between the γ estimates (which were computed
on 5-bin data) and the BP potentials.

**Node priors — two strategies:**

| Strategy | Source | When to use |
|----------|--------|-------------|
| Empirical marginals | WVS microdata via `wvs_loader.py` | Preferred; reflects actual response distribution |
| Uniform (1/5 each) | No data needed | Fallback; justified if bins are equal-frequency quantile cuts |

If constructs were binned by equal-frequency quantile cuts (as in the Julia
pipeline), the marginal distribution is uniform by construction — the two
strategies are equivalent. If fixed-width binning was used, empirical marginals
are necessary.

### 1.3 Pitfalls

**Loopy BP convergence.** The WVS construct networks are highly cyclic (density
23%, diameter 4, clustering 0.531). Loopy BP is an approximation that may not
converge or may converge to incorrect marginals. Mitigation: damping (0.5),
iteration cap (200), monitor max message change per iteration. If the final
max change exceeds 1e-4, flag the country as non-converged and treat results
as soft rather than exact.

*Expected convergence rate:* >90% of countries should converge. The high density
actually helps — in very dense graphs, BP's variational approximation (Bethe
free energy) becomes more accurate because the locally tree-like assumption
fails equally everywhere, producing a systematic but uniform bias.

**Edge weights are not sufficient statistics.** The γ value captures the
monotonic strength of the SES-mediated covariation, but BP requires a full
conditional p(xⱼ | xᵢ). The Potts model uses γ only to set the coupling
strength, not the conditional shape. This means BP captures "how strongly
coupled" but not "in what pattern." For example, a U-shaped relationship
(xᵢ = 1 and xᵢ = 5 both push xⱼ high) would have γ ≈ 0 and be invisible
to BP. The TDA sweep found NMI universally low, so non-monotonic patterns
are rare — but they would be missed.

**Directed edges.** The γ-surface is symmetric (γ(A,B) = γ(B,A) by definition
of Goodman-Kruskal γ), so the weight matrices are symmetric. This is ideal
for MRFs, which require undirected graphs. No symmetrization needed.

**Interpretation boundary.** BP answers "given this evidence, what does the
joint distribution imply about other constructs?" It does NOT answer "if we
intervene to change construct A, what happens to B?" The distinction is
observational (conditioning) vs. causal (intervention). BP is purely
observational — it computes statistical implications, not causal effects.

### 1.4 Interpretation Guidelines

**Lift (KL divergence from prior to posterior):**
- KL > 0.1: strong implication — knowing the evidence construct substantially
  shifts the target distribution
- KL ∈ [0.01, 0.1]: moderate implication — detectable shift
- KL < 0.01: negligible — the evidence construct tells us almost nothing about
  the target

**Reading a scenario output:** "Given that a Mexican respondent scores at
the top quintile of institutional trust, the constructs most shifted are
[list]. Their posterior distributions shift toward [direction], implying that
high institutional trust co-occurs with [interpretation]."

**What lifts reveal about network structure:**
- Constructs with high mutual lift are in the same "belief community" — they
  constrain each other
- Constructs with zero lift from a high-degree evidence node are SES-independent
  of it — they exist in a different region of the belief space
- The lift profile of an evidence node is its "influence fingerprint" — two
  evidence nodes with similar lift profiles play similar structural roles

**β sensitivity:** If a construct's ranking changes dramatically with β, it
means its position depends on coupling strength — it's a "weakly coupled"
belief. If ranking is β-stable, the construct's position is structurally
determined regardless of coupling intensity.

### 1.5 Output Specification

**File:** `data/tda/message_passing/{ALPHA3}_bp.json`

```json
{
  "country": "MEX",
  "config": {
    "potential_type": "potts",
    "beta": 2.0,
    "damping": 0.5,
    "max_iter": 200,
    "n_states": 5,
    "prior_source": "uniform"
  },
  "convergence": {
    "converged": true,
    "iterations": 67,
    "final_max_change": 2.3e-7
  },
  "scenarios": {
    "institutional_trust|WVS_E": {
      "evidence_state": 4,
      "converged": true,
      "top_affected": [
        {
          "construct": "confidence_in_domestic_institutions|WVS_E",
          "kl_from_prior": 0.142,
          "modal_state": 4,
          "posterior": [0.08, 0.12, 0.18, 0.28, 0.34]
        }
      ]
    }
  },
  "lift_matrix": "55x55 mean KL across evidence states (symmetric)",
  "beta_sensitivity": {
    "stable_constructs": ["list of constructs whose top-10 ranking is stable across beta"],
    "sensitive_constructs": ["list of constructs whose ranking shifts by >10 places"]
  }
}
```

---

## Stage 2: Spectral Diffusion

### 2.1 Mathematical Motivation

The graph Laplacian L = D - W (degree matrix minus weighted adjacency) is the
central operator of network dynamics. Its eigendecomposition reveals the
**natural modes of belief variation** in a country.

For the normalized Laplacian:

$$\mathcal{L} = D^{-1/2} L D^{-1/2} = I - D^{-1/2} W D^{-1/2}$$

The eigendecomposition L = UΛUᵀ gives:
- **Eigenvalues** λ₀ ≤ λ₁ ≤ ... ≤ λ₅₄: diffusion rates
- **Eigenvectors** u₀, u₁, ..., u₅₄: spatial modes of variation

The heat equation on the graph:

$$\frac{d\mathbf{x}}{dt} = -L\mathbf{x}(t) \quad \Rightarrow \quad
\mathbf{x}(t) = e^{-Lt}\mathbf{x}(0) = \sum_{k} e^{-\lambda_k t}
\langle \mathbf{x}(0), \mathbf{u}_k \rangle\, \mathbf{u}_k$$

Each eigenvector uₖ is a pattern of belief variation across constructs. Each
eigenvalue λₖ is its decay rate. Small λ = slow decay = large-scale, persistent
patterns. Large λ = fast decay = local, transient patterns.

**Fiedler vector** (u₁, first non-trivial eigenvector): the slowest non-trivial
diffusion mode. It partitions constructs into two groups that vary most
independently — the principal axis of belief variation. Constructs with opposite
signs in u₁ are the ones that most reliably move in opposite directions.

**Heat kernel** H(t) = exp(-Lt): the (i,j) entry gives the amount of diffused
signal arriving at j from an initial impulse at i after time t.

**Diffusion distance** at time t:

$$D_t(i,j)^2 = \sum_k e^{-2\lambda_k t}(u_k(i) - u_k(j))^2$$

This is a multi-scale metric: at small t it is geodesic-like; at large t it
collapses to global community structure.

**Diffusion map**: embed constructs using scaled eigenvectors
(e^{-λ₁t}u₁, e^{-λ₂t}u₂, e^{-λ₃t}u₃). Constructs close in diffusion space
are dynamically similar — they receive similar information from any diffusing
signal.

### 2.2 Design Choices

**Symmetrization.** The weight matrices are already symmetric (γ(A,B) = γ(B,A)),
but numerical precision may introduce asymmetries at the 1e-15 level. Enforce
symmetry via W_sym = (|W| + |W|ᵀ)/2 before computing L.

**Absolute values.** The Laplacian requires non-negative edge weights. Use |wᵢⱼ|
(absolute γ) — this discards sign information. Sign information is preserved in
Stage 1 (BP, via Potts model) and Stage 3 (PPR, via directed structure). The
spectral analysis captures the **strength** of coupling regardless of direction.

**Normalized vs unnormalized Laplacian.** Normalized is preferred because
construct degrees vary (some constructs have many significant bridges, others
few). The unnormalized Laplacian would be dominated by high-degree nodes.
Normalization ensures equal representation.

**Diffusion time sweep.** t is a free parameter with no canonical value. The
characteristic time scale of the network is 1/λ₁ (inverse Fiedler value).
For WVS networks, λ₁ ≈ 0.70, so the characteristic time is ~1.4. Sweep:

| t | Scale | What it captures |
|---|-------|------------------|
| 0.01 | Ultra-local | Direct neighbors only |
| 0.1 | Local | 2-hop neighborhood |
| 0.5 | Meso | Community-level structure |
| 1.0 | Characteristic | The Fiedler mode dominates |
| 5.0 | Global | Only the slowest modes survive |
| 10.0 | Near-equilibrium | Almost uniform — all constructs equally reached |

### 2.3 Pitfalls

**Absolute values discard sign.** By using |γ|, the Laplacian treats positive
and negative bridges identically — both are "connections." This means the
spectral analysis cannot distinguish co-elevation (γ > 0) from
counter-variation (γ < 0). The Fiedler partition may not align with the γ sign
partition (52% pos / 48% neg). If it doesn't, that's informative: the spectral
structure is organized by coupling strength, not coupling direction.

**Disconnected components.** If β₀ > 1 (multiple connected components), L has
multiple zero eigenvalues and diffusion does not cross component boundaries.
The TDA found all 66 countries have n_components = 1 in the spectral features
— every country's network is connected. However, 22 constructs are isolated in
the aggregate network (SES magnitude too small). These would appear as weakly
connected nodes with small eigenvector loadings.

**Linear dynamics.** The heat equation is linear — it models small perturbations
around equilibrium. Real belief dynamics are nonlinear (threshold effects,
social pressure, normative cascades). The heat equation is an approximation
valid for "what happens if one construct shifts slightly?" For large shocks
(e.g., a revolution), nonlinear models would be needed.

**Comparison across countries.** Eigenvalues are comparable across countries
(they measure diffusion rates on normalized Laplacians with the same number of
nodes). Eigenvectors are NOT directly comparable — they can be sign-flipped or
rotated. To compare Fiedler partitions across countries, use the Rand index
(agreement between the two binary partitions), not eigenvector correlation.

### 2.4 Interpretation Guidelines

**Fiedler value (algebraic connectivity):**
- High λ₁ (e.g., 0.80): well-connected network — beliefs propagate quickly
  across all constructs. Hard to have isolated belief clusters.
- Low λ₁ (e.g., 0.60): more modular — some belief communities are weakly
  connected, beliefs propagate slowly between them.
- Observed range: 0.60–0.89 across 66 countries. Most are well-connected.

**Fiedler partition interpretation:** The positive-side and negative-side
constructs form the two groups that vary most independently in this country.
Compare against WVS domains:
- If the partition separates WVS domains (e.g., all religion constructs on one
  side, all politics on the other), the principal axis is thematic.
- If it cuts across domains (religion and politics mixed on both sides), the
  principal axis is structural (SES geometry, not content).

Given that the network's sign structure corresponds to the PC1 of SES
fingerprint space (cosmopolitan-education vs. tradition-locality axis, 78%
variance explained), the Fiedler partition likely aligns with this axis.

**Diffusion map:** The 3D embedding places constructs in "dynamic similarity
space." Clusters in this space are groups of constructs that respond identically
to any perturbation — they are dynamically fungible. Outliers are constructs
with unique dynamic profiles.

**Scale sweep interpretation:** If a construct receives signal quickly (high
value at small t) but not at large t, it's a local neighbor of the evidence
node. If it receives signal only at large t, it's globally connected but not
locally. If it receives signal at all scales, it's a hub.

### 2.5 Output Specification

**File:** `data/tda/message_passing/{ALPHA3}_spectral.json`

```json
{
  "country": "MEX",
  "eigenvalues": [0.0, 0.702, 0.715, ...],
  "fiedler_value": 0.702,
  "fiedler_partition": {
    "positive": ["construct_a", "construct_b", ...],
    "negative": ["construct_c", "construct_d", ...],
    "ranked_by_loading": ["construct_x", ...]
  },
  "diffusion_map_3d": {
    "construct_a": [0.12, -0.05, 0.03],
    ...
  },
  "scale_sweep": {
    "0.01": {"evidence_construct": "...", "top_reached": [...]},
    ...
  }
}
```

**File:** `data/tda/message_passing/fiedler_comparison.json`

```json
{
  "rand_index_matrix": "66x66 pairwise Rand index of Fiedler partitions",
  "mean_within_zone": {"Latin America": 0.82, ...},
  "mean_across_zone": 0.61
}
```

---

## Stage 3: Personalized PageRank Influence Mapping

### 3.1 Mathematical Motivation

Personalized PageRank (PPR) answers: "what is the steady-state influence of
node i on the rest of the network under continuous random restarts?"

Define the transition matrix P = D⁻¹|W| (row-normalized absolute adjacency).
The PPR vector seeded at node i satisfies:

$$\pi^{(i)} = \alpha\, e_i + (1 - \alpha)\, P^\top \pi^{(i)}$$

Solving: π^(i) = α(I - (1-α)Pᵀ)⁻¹ eᵢ

The scalar πⱼ^(i) measures steady-state probability mass at j from a random
walker that starts at i, follows weighted edges, and teleports back to i with
probability α at each step.

The full PPR matrix Π (55×55), with column i = π^(i), gives pairwise influence.
Πⱼᵢ = influence of i on j.

**Hub score** of i = Σⱼ Πⱼᵢ: total outgoing influence (how broadly i reaches).
**Sink score** of j = Σᵢ Πⱼᵢ: total incoming influence (how influenced j is).
**Asymmetry** = Πⱼᵢ - Πᵢⱼ: positive means i dominates j in influence.

### 3.2 Design Choices

**Why PPR over eigenvector centrality.** Eigenvector centrality gives one score
per node (the leading eigenvector of W). PPR gives a full i→j influence matrix
— richer information. Eigenvector centrality is the limit of PPR as α → 0
(pure random walk, no restarts). PPR with α > 0 localizes influence, answering
"where does i's influence concentrate?" rather than just "how central is i?"

**α = 0.20 (default).** This means 20% restart probability — the random walker
returns to the seed every 5 steps on average. For a network with diameter 4,
this means the walker typically explores 2-3 hops before restarting. This
captures local and medium-range influence. Sensitivity sweep at
α ∈ {0.10, 0.15, 0.20, 0.30, 0.50}:

| α | Mean walk length | Interpretation |
|---|------------------|----------------|
| 0.10 | ~10 steps | Global influence — walker reaches most of the network |
| 0.20 | ~5 steps | Medium-range — 2-3 hops |
| 0.50 | ~2 steps | Very local — mostly direct neighbors |

**Absolute values for transition matrix.** P uses |wᵢⱼ| because the transition
matrix must be non-negative (probabilities). Sign information is not used in
PPR. This means PPR measures "how much influence flows between i and j"
regardless of whether that influence is concordant or discordant. The sign
of the influence (does i push j in the same or opposite direction?) must be
read from the original weight matrix, not from PPR.

**Power iteration.** For 55×55 matrices, direct matrix inversion
α(I - (1-α)Pᵀ)⁻¹ is faster than power iteration. But power iteration is
numerically more stable and trivially parallelizable across seed nodes.
Expected convergence: <100 iterations at tol=1e-8.

### 3.3 Pitfalls

**PPR conflates reach with proximity.** A construct directly connected to many
others will have high PPR regardless of edge strength. Weighting by |γ| (which
we do) partially corrects this, but does not fully separate influence from
degree centrality. Compare PPR hub scores against raw degree — constructs where
PPR rank >> degree rank are influential beyond their direct connections.

**Influence ≠ causation.** PPR measures structural coupling, not causal effect.
High Πⱼᵢ means i and j are structurally coupled through the SES-mediated
network — it does not mean changing i causes j to change. The causal
interpretation requires the DR bridge's CIA assumption (conditional independence
given SES) to hold, and even then γ measures association, not intervention
effects.

**α sensitivity as a diagnostic.** If a construct's hub ranking is stable across
α values, its influence is structurally robust — it's a genuine hub. If its
ranking is α-sensitive (high at small α, low at large α), its influence comes
from long-range global connectivity, not local importance. The converse (high
at large α, low at small α) means it's locally central but globally peripheral.

**Stationarity.** PPR assumes the random walk has a stationary distribution.
This requires the graph to be connected (for undirected) or strongly connected
(for directed). All 66 countries have n_components = 1, so stationarity is
guaranteed. The teleportation parameter α also ensures convergence even for
weakly connected graphs.

### 3.4 Interpretation Guidelines

**Hub score ranking:**
- Top hubs are **belief drivers** — constructs whose state constrains the
  broadest set of other beliefs. Shifts in these constructs propagate widely.
  Practical implication: these are the constructs where a public opinion
  campaign would have the largest multiplier effect.
- Bottom hubs are **belief peripherals** — constructs that exist independently
  of the network. Shifting them has minimal downstream effect.

**Sink score ranking:**
- Top sinks are **belief consequences** — constructs most determined by the
  rest of the network. They are downstream of many influences.
- Low sinks are **belief sources** — they influence others but are not
  themselves influenced.

**Asymmetry matrix:**
- Πⱼᵢ >> Πᵢⱼ: i is upstream of j (i influences j more than j influences i)
- Πⱼᵢ ≈ Πᵢⱼ: symmetric relationship (mutual influence)
- The most asymmetric pairs reveal the network's causal hierarchy — which
  constructs are "driving" vs "driven"

**Cross-country hub comparison:**
- Universal hubs (top-10 in >50 countries): these constructs are structurally
  central in the SES belief network regardless of cultural context. They likely
  correspond to constructs with high SES magnitude (ses_magnitude from
  fingerprints).
- Culturally specific hubs (top-10 in one zone only): these are constructs
  whose structural importance varies by cultural context. Compare against
  mediator scores from Floyd-Warshall — constructs that are top mediators
  in specific countries (gender_role_traditionalism in MEX/BRA,
  science_skepticism in USA/JPN) may also be culturally specific hubs.

**Scenario interface ("what if X shifts by 1σ?"):**
The implied shift at construct j is proportional to Πⱼᵢ × shift_magnitude.
This is a first-order linear approximation. For small shifts (<0.5σ), this
is reasonable. For large shifts, the linear model breaks down — nonlinear
dynamics (threshold effects, cascades) would need Stage 5's temporal model.

### 3.5 Output Specification

**File:** `data/tda/message_passing/{ALPHA3}_ppr.json`

```json
{
  "country": "MEX",
  "config": {"alpha": 0.20, "tol": 1e-8, "max_iter": 500},
  "hub_scores": {"construct_a": 1.42, ...},
  "sink_scores": {"construct_a": 1.38, ...},
  "hub_ranking": ["construct_x", "construct_y", ...],
  "sink_ranking": ["construct_z", ...],
  "alpha_sensitivity": {
    "0.10": {"hub_ranking": [...]},
    "0.20": {"hub_ranking": [...]},
    ...
  },
  "alpha_stable_hubs": ["constructs in top-10 at all alpha values"],
  "alpha_sensitive_hubs": ["constructs with >10 rank shift across alpha"]
}
```

**File:** `data/tda/message_passing/ppr_hub_comparison.json`

```json
{
  "hub_rank_matrix": "55x66 — construct × country hub rank",
  "universal_hubs": ["constructs in top-10 for >50 countries"],
  "zone_specific_hubs": {
    "Latin America": ["constructs in top-10 for LatAm but not globally"],
    ...
  }
}
```

---

## Stage 4: Multilayer Message Passing — Regional Scope

### 4.1 Mathematical Motivation

A single country's construct network is Layer 1. The inter-country network is
Layer 2. The **Gromov-Wasserstein transport plan** T^(c₁,c₂) maps constructs
in country c₁ to constructs in c₂ based on structural equivalence — constructs
that play the same role in their respective networks.

The effective cross-country influence of construct i in c₁ on construct j in c₂:

$$\Pi^{(c_1 \to c_2)}_{ij} = \omega_{c_1 c_2} \cdot
\sum_k T^{(c_1,c_2)}_{ik}\, \Pi^{(c_2)}_{kj}$$

where:
- T^(c₁,c₂)ᵢₖ = transport plan: probability that construct i in c₁ corresponds
  to construct k in c₂
- Π^(c₂)ₖⱼ = within-country PPR: influence of k on j within c₂
- ωc₁c₂ = inter-country coupling strength (function of spectral distance)

In matrix form: Π^(c₁→c₂) = ω · Π^(c₂) · T · Π^(c₁)

The chain is: i influences its neighbors in c₁ (Π^(c₁)) → the signal
transfers to structurally equivalent constructs in c₂ (T) → the transferred
signal propagates within c₂ (Π^(c₂)).

### 4.2 Why Full 66-Country Multilayer Is Infeasible

Three compounding problems:

**Problem 1: Near-uniform transport plans.** The GW self-match rate is 3.1%
(mean). For a 55-construct network, random matching would give 1/55 = 1.8%.
The observed 3.1% is only marginally above chance. This means the transport
plans are close to the uniform matrix T = 1/55 · **11**ᵀ — every construct in
c₁ maps roughly equally to every construct in c₂.

Propagating through a near-uniform T smears the signal:

$$\Pi^{(c_1 \to c_2)} \approx \frac{\omega}{55} \cdot \Pi^{(c_2)} \cdot
\mathbf{1}\mathbf{1}^\top \cdot \Pi^{(c_1)}$$

The rank-1 term **11**ᵀ · Π^(c₁) = column sums of Π^(c₁) — a single scalar
per source construct. All target constructs receive the same signal regardless
of their identity. The multilayer propagation degenerates to:
"everything in c₁ affects everything in c₂ equally, scaled by hub score."

**Problem 2: Storage.** Only 50/2,145 transport plans are stored (the 50
most/least similar pairs from the GW analysis). The remaining 2,095 would need
recomputation. Each is a 55×55 matrix.

**Problem 3: Interpretive opacity.** 66 countries × 55 constructs = 3,630 nodes.
The supra-graph PPR output is a 3,630 × 3,630 matrix — 13M entries. No one can
interpret this.

### 4.3 Why Regional Aggregation Works

Within a cultural zone, countries share more structural similarity (spectral
zone coherence p = 0.001 from TDA). The GW transport plans within zones are
sharper because:

- Countries in the same zone have similar Fiedler partitions → constructs
  occupy more consistent structural positions → GW maps are more concentrated
- The spectral distances within zones are smaller → coupling ω is stronger →
  cross-country signal is not attenuated to noise level
- Within-zone self-match rates are typically 2-3× above the global mean

Concretely for Latin America (13 countries):
- 78 within-zone pairs (vs 2,145 total)
- 715 supra-nodes (vs 3,630)
- Results are interpretable: "institutional trust in MEX influences democratic
  values in BRA through the transport coupling"

### 4.4 Design Choices

**Coupling function ω(c₁, c₂).** Three options to test:

| Type | Formula | Properties |
|------|---------|------------|
| Inverse | ω = 1/(d + ε) | Strong coupling at short distance; diverges at d→0 |
| Gaussian | ω = exp(-d²/2σ²) | Smooth; σ controls range |
| Binary | ω = 1 if d < threshold, else 0 | Sparse; cleanest interpretation |

Start with Gaussian (σ = median within-zone spectral distance). Binary as a
sensitivity check.

**GW transport plan normalization.** The raw transport plan T has rows summing
to uniform mass (1/55). Normalize rows to sum to 1 for probabilistic
interpretation: T_norm[i,:] = T[i,:] / Σⱼ T[i,j]. After normalization,
T_norm[i,j] = "probability that construct i in c₁ corresponds to construct j
in c₂."

**Regional subsets:**

| Zone | Countries | Supra-nodes | Pairs |
|------|-----------|-------------|-------|
| Latin America | 13 | 715 | 78 |
| Confucian | 8 | 440 | 28 |
| English-speaking | 6 | 330 | 15 |
| African-Islamic | 14 | 770 | 91 |

Start with Latin America (most relevant to the project's Mexican focus), then
Confucian (most structurally distinct from LatAm for contrast).

### 4.5 Pitfalls

**Structural equivalence ≠ semantic equivalence.** GW maps constructs by
structural role, not by content. Two constructs are "equivalent" if they have
the same pattern of connections — but this ignores what the constructs actually
measure. Always validate transport alignments against construct names: does the
GW plan map "institutional trust" in MEX to "institutional trust" in BRA
(semantic match) or to "civic dishonesty tolerance" (structural match but
semantic mismatch)?

**Coupling ω is a modeling choice.** Results can be sensitive to the functional
form and parameters. Report results for all three coupling types. If
conclusions change with ω, the multilayer finding is fragile and depends on
assumptions rather than data.

**Missing transport plans.** For within-zone pairs not in the top-50 file,
recompute via Julia `tda_gromov_wasserstein.jl`. This is fast (<10s for 78
pairs) but requires the distance matrices to exist for all countries in the
zone. They do (confirmed: all 66 countries have distance matrices).

### 4.6 Interpretation Guidelines

**Belief corridors:** Country pairs × constructs with the highest cross-country
PPR scores. These are pathways where a belief shift in one country would most
efficiently propagate to another.

Questions this answers:
- "If institutional trust rises in Mexico, what moves in Brazil?" → read the
  cross-influence vector Π^(MEX→BRA)[:,institutional_trust]
- "Which constructs are globally influential — not just within their country
  but across borders?" → constructs with high within-country hub score AND
  strong GW alignment to hubs in neighboring countries
- "Are there constructs with no cross-border equivalent?" → constructs with
  diffuse transport plans (no single dominant mapping). These are the most
  culturally specific beliefs.
- "Which country pairs form belief corridors?" → pairs with high ω AND
  concentrated transport plans. Test: compare corridors against geographic
  proximity, trade relationships, or migration patterns.

### 4.7 Output Specification

**File:** `data/tda/message_passing/{zone}_multilayer.json`

```json
{
  "zone": "Latin America",
  "countries": ["ARG", "BOL", ...],
  "coupling_type": "gaussian",
  "coupling_sigma": 0.025,
  "cross_country_influence": {
    "MEX->BRA": {
      "omega": 1.42,
      "top_corridors": [
        {
          "source_construct": "institutional_trust|WVS_E",
          "target_construct": "democratic_values|WVS_E",
          "influence": 0.034,
          "transport_concentration": 0.45
        }
      ]
    }
  },
  "global_hubs": ["constructs with high cross-country influence sum"],
  "culturally_specific": ["constructs with diffuse transport plans"]
}
```

---

## Stage 5: Temporal Dynamics — Descriptive + Constrained Forecast

### 5.1 Data Reality

Mexico has 5 WVS waves (W3=1996, W4=2001, W5=2007, W6=2012, W7=2018). The
temporal weight matrices are 52×52 but sparsely filled in early waves:

| Wave | Year | Constructs present | Empty rows | Fill rate |
|------|------|--------------------|------------|-----------|
| W3 | 1996 | 23 | 29 | 14.2% |
| W4 | 2001 | 24 | 28 | 15.7% |
| W5 | 2007 | 28 | 24 | 21.2% |
| W6 | 2012 | 41 | 11 | 48.7% |
| W7 | 2018 | 49 | 3 | 72.4% |

**20 constructs** are present in all 5 waves (the "temporal core"):

| Construct | Domain |
|-----------|--------|
| autocracy_support | WVS_E |
| child_qualities_autonomy_self_expression | WVS_A |
| child_qualities_conformity_tradition | WVS_A |
| child_qualities_prosocial_diligence | WVS_A |
| civic_dishonesty_tolerance | WVS_F |
| confidence_in_civil_society_organizations | WVS_E |
| confidence_in_domestic_institutions | WVS_E |
| confidence_in_international_organizations | WVS_E |
| economic_ideology | WVS_E |
| gender_role_traditionalism | WVS_D |
| importance_of_life_domains | WVS_A |
| job_scarcity_gender_discrimination | WVS_C |
| job_scarcity_nativist_preference | WVS_C |
| life_autonomy_morality_permissiveness | WVS_F |
| postmaterialist_values | WVS_E |
| religious_practice_and_self_identification | WVS_F |
| sexual_and_reproductive_morality_permissiveness | WVS_F |
| social_intolerance_outgroups | WVS_A |
| societal_change_attitudes | WVS_E |
| subjective_wellbeing | WVS_A |

The descriptive analyses (5a-5c) run on whatever constructs are present in each
wave pair. The forecast (5d) runs only on the 20-construct temporal core, where
all 4 transitions are observed.

### 5.2 Descriptive Analyses

#### 5a. Velocity Field

For each wave, the **network-implied velocity** at construct i:

$$\Delta x_i = \sum_{j \in \mathcal{N}(i)} w_{ij}(x_j - x_i)$$

This is the discrete Laplacian applied to the belief state: v = -L·x. It
measures how much the network "wants" each construct to move, and in which
direction.

- v_i > 0: construct i is below its network-implied value — the network pulls
  it upward
- v_i < 0: construct i is above its network-implied value — the network pulls
  it downward
- v_i ≈ 0: construct i is at network equilibrium — consistent with its neighbors

**Interpretation:** Constructs with large |v_i| are under **network tension** —
their current state disagrees with the SES-mediated pattern of their neighbors.
These are the constructs most "due for" a shift if the network dynamics operate.

#### 5b. Distance from Equilibrium

The network-implied equilibrium is the null space of L — for a connected graph,
this is the weighted consensus state:

$$x^*_i = \frac{\sum_j d_j x_j}{\sum_j d_j} \quad \forall i$$

The L2 distance ||x - x*|| measures how far the actual belief state is from
this consensus.

**Interpretation:**
- Decreasing distance across waves: Mexico's beliefs are converging toward
  SES-network consistency — the structural forces are winning
- Increasing distance: exogenous forces (economic crises, political events,
  generational turnover) are pushing beliefs away from the network attractor
- Stable distance: beliefs are in dynamic equilibrium — exogenous forces and
  network forces balance

#### 5c. Residual Analysis

For consecutive wave pairs, the one-step prediction and residual:

$$\hat{x}(t+1) = A(t) \cdot x(t), \quad r(t) = x(t+1) - \hat{x}(t+1)$$

where A(t) = D⁻¹|W(t)| is the row-normalized adjacency at wave t.

Constructs with large |r_i| changed for reasons the network cannot explain.

**Interpretation:** The residual separates:
- **Network-predicted evolution** (small |r|): the construct moved as the SES
  structure implied. These are the "easy" dynamics — structurally driven.
- **Unexplained shifts** (large |r|): the construct moved independently of or
  against network forces. These are exogenous shocks — historical events,
  policy changes, generational effects.

Cross-reference with Mexican history:
- W3→W4 (1996→2001): Zedillo presidency, NAFTA effects, peso crisis aftermath
- W4→W5 (2001→2007): Fox presidency (first non-PRI), 9/11 aftermath
- W5→W6 (2007→2012): Calderón drug war, 2008 financial crisis
- W6→W7 (2012→2018): Peña Nieto, Ayotzinapa (2014), Trump election (2016)

### 5.3 Constrained Forecast

#### Why a 1-parameter model

The full graph autoregression x̂(t+1) = A(t)·x(t) has 55² = 3,025 effective
parameters (the entries of A), estimated from a single 55-dimensional
observation per transition — hopelessly underdetermined.

But A is not a free parameter — it's estimated from data at each wave. The
model x̂(t+1) = A(t)·x(t) is parameter-free: it uses the observed network
to predict the next belief state. The problem is that this model assumes the
network completely determines the dynamics (α = 1), which is empirically
false — the residuals from 5c show substantial unexplained variation.

The **mixing model** adds one free parameter:

$$\hat{x}(t+1) = \alpha \cdot A(t) \cdot x(t) + (1 - \alpha) \cdot x(t)$$

This is a convex blend of:
- "The network pulls beliefs toward their neighbors" (A·x, weight α)
- "Beliefs stay where they are" (x, weight 1-α, inertia)

The parameter α ∈ [0, 1] controls the mixing strength. At α = 0, beliefs are
purely inertial (next wave = this wave). At α = 1, beliefs are purely
network-driven (next wave = neighbor-average of this wave).

#### Fitting α

Minimize mean squared prediction error across all transitions and constructs:

$$\alpha^* = \arg\min_\alpha \sum_{t \in \text{transitions}} \sum_{i \in \text{core}}
\left[\alpha \cdot (A(t) x(t))_i + (1-\alpha) \cdot x_i(t) - x_i(t+1)\right]^2$$

This is a 1D optimization over N = 4 transitions × 20 constructs = 80
observations (using the temporal core) or up to ~120 observations if using
per-transition construct sets. The optimization is convex (quadratic in α)
and has a closed-form solution:

$$\alpha^* = \frac{\sum_{t,i} (a_i(t) - x_i(t))(x_i(t+1) - x_i(t))}
{\sum_{t,i} (a_i(t) - x_i(t))^2}$$

where a_i(t) = (A(t)·x(t))_i is the network prediction.

**Expected α:** Small (0.05–0.20). Beliefs are mostly inertial; the network
provides a weak directional pull. If α ≈ 0, the network has no predictive
power beyond persistence. If α > 0.5, beliefs are strongly network-driven
(surprising and worth reporting).

#### Forecast

Apply the fitted model forward from the last observed wave:

$$\hat{x}(W8) = \alpha^* \cdot A(W7) \cdot x(W7) + (1-\alpha^*) \cdot x(W7)$$

This assumes:
1. The W7 network structure persists (no structural breaks)
2. The mixing strength α is constant across waves (stationarity)
3. No exogenous shocks between W7 and W8

All three assumptions are questionable. The forecast is explicitly labeled as
"network-implied tendency under structural persistence."

#### Uncertainty Envelope

The 4 historical residual vectors (from 5c) provide an empirical distribution
of prediction error. For each construct i in the temporal core:

- σᵢ = standard deviation of residuals across 4 transitions
- 80% prediction interval: x̂ᵢ(W8) ± 1.28·σᵢ
- Noise-dominated flag: σᵢ > |x̂ᵢ(W8) - xᵢ(W7)| means the predicted shift is
  smaller than the typical historical prediction error

The 80% interval (not 95%) is chosen because with only 4 residuals, the
empirical variance is itself uncertain. An 80% interval with a poorly estimated
σ is more honest than a 95% interval that implies precision we don't have.

**Directional claims:** Constructs where the entire 80% interval lies above
(or below) the current W7 value. For these constructs, the network makes a
directional prediction that exceeds the historical noise floor. These are the
only constructs where the forecast is substantively meaningful.

#### Per-Construct Trend Extrapolation

Independent of the network model, fit a simple OLS trend per construct:

$$x_i(t) = a_i + b_i \cdot t + \epsilon_i(t)$$

fitted from the 5 wave means (t indexed by year). Report:

- Slope bᵢ: direction and rate of change per decade
- R²: how linear the trajectory is (5 points, so R² > 0.7 and p < 0.10 is
  a meaningful threshold)
- Trend-stable constructs: R² > 0.7 — the direction is reliable
- Trend-unstable constructs: R² < 0.3 — no clear direction

**Network-trend comparison:** For each construct, compare:
- Network forecast direction: sign(x̂ᵢ(W8) - xᵢ(W7))
- Trend direction: sign(bᵢ)

| Agreement | Interpretation |
|-----------|----------------|
| Both positive | Network and historical momentum both pull upward — strong directional signal |
| Both negative | Network and momentum both pull downward |
| Network +, trend - | The SES structure at W7 would reverse the historical decline — structural tension |
| Network -, trend + | The SES structure at W7 would reverse the historical rise — structural opposition |

**Trend reversals** (disagreements) are the most substantively interesting
constructs. They indicate that the current network structure is working against
the historical direction of change — a structural tension that either resolves
(the network wins and the trend reverses) or persists (exogenous forces
continue to dominate). These are candidates for deeper qualitative
investigation.

### 5.4 Pitfalls

**4 transitions = very noisy σ.** The standard deviation of 4 residuals has
large estimation error (the standard error of a standard deviation from n=4 is
σ/√(2(n-1)) ≈ 0.41σ). The 80% interval should be treated as approximate, not
precise. Do not over-interpret narrow intervals — they may reflect lucky
residual draws rather than genuine predictability.

**The network changes between waves.** A(t) is itself estimated from data at
wave t. The temporal model uses **estimated regressors** — the network
measurement error propagates into the predictions. This is a standard
errors-in-variables problem. The effect is to bias α toward zero (attenuation
bias) — the true network influence may be stronger than α* suggests.

**Aggregate means, not individual trajectories.** x(t) is the country-level
mean response — not an individual panel. The temporal model describes
population-level dynamics, not individual belief change. The velocity field
describes where the population mean "wants" to go, not where any individual
would go.

**Sparse early waves.** W3 and W4 have only 23-24 constructs. The 20-construct
temporal core is small relative to the full 55-construct network. Network
effects among the missing constructs are invisible. The velocity field and
equilibrium analysis for early waves operate on a different (smaller) effective
network than later waves — they are not directly comparable in magnitude, only
in direction.

**Structural stationarity.** The mixing model assumes α is constant across all
4 transitions. If the network's predictive power changes over time (e.g.,
stronger in recent waves due to more constructs), a single α is a compromise.
As a robustness check: fit α separately for each transition and report the
range. If the per-transition α values span [0.02, 0.40], the stationarity
assumption is violated and the forecast is unreliable.

### 5.5 Interpretation Guidelines

**Velocity field:**
- "At W7, the Mexican belief network pulls institutional trust upward (v=+0.15)
  and religious exclusivism downward (v=-0.22). The constructs under greatest
  network tension are [list]."
- Compare across waves: "Network tension at gender_role_traditionalism
  increased from v=+0.05 (W3) to v=+0.18 (W7), suggesting growing structural
  pressure toward gender liberalization."

**Equilibrium distance:**
- "Mexico's distance from network equilibrium [increased/decreased] from
  [value] in 1996 to [value] in 2018, indicating that Mexican beliefs are
  [converging toward / diverging from] SES-network consistency."

**Residuals:**
- "The largest unexplained shifts between W6 (2012) and W7 (2018) were in
  [constructs]. These shifts coincide with [historical events] and cannot be
  explained by the SES network structure alone."

**Forecast:**
- "Under structural persistence (α*=[value], meaning beliefs are [value]%
  network-driven and [100-value]% inertial), the W7 network implies the
  following directional tendencies for a hypothetical W8:"
- "[N] of 20 temporal-core constructs have prediction intervals excluding their
  current value — the network makes a directional claim above the noise floor."
- "The remaining [20-N] constructs have noise-dominated forecasts — the network
  predicts a direction but the magnitude is smaller than historical error."
- **Always caveat:** "These are network-implied tendencies, not predictions.
  They assume no structural breaks, no exogenous shocks, and constant mixing
  strength. Any of these assumptions may fail."

**Trend reversals:**
- "The network at W7 would pull [construct] upward, but the historical trend
  across 1996-2018 shows decline (b=[slope], R²=[value]). This structural
  tension suggests either the SES structure has recently shifted to favor
  [construct], or that exogenous forces (e.g., [event]) have been pushing
  against the network for decades."

### 5.6 Output Specification

**File:** `data/tda/message_passing/mex_temporal.json`

```json
{
  "data_summary": {
    "waves": [3, 4, 5, 6, 7],
    "years": [1996, 2001, 2007, 2012, 2018],
    "temporal_core": ["20 construct names"],
    "constructs_per_wave": {"W3": 23, "W4": 24, "W5": 28, "W6": 41, "W7": 49}
  },
  "velocity_fields": {
    "W3": {"construct_a": 0.15, "construct_b": -0.08, ...},
    ...
  },
  "equilibrium_distance": {
    "W3": 0.42, "W4": 0.39, "W5": 0.35, "W6": 0.31, "W7": 0.28
  },
  "residuals": {
    "W3_W4": {
      "construct_a": {"predicted": 3.2, "actual": 3.5, "residual": 0.3},
      ...
    },
    ...
  },
  "top_residuals_per_transition": {
    "W3_W4": [{"construct": "...", "residual": 0.45}, ...],
    ...
  },
  "forecast": {
    "model": "mixing",
    "alpha_star": 0.12,
    "alpha_closed_form": true,
    "alpha_fit_rmse": 0.08,
    "alpha_per_transition": {"W3_W4": 0.08, "W4_W5": 0.15, ...},
    "stationarity_range": [0.08, 0.15],
    "n_observations": 80,
    "w8_projection": {
      "autocracy_support|WVS_E": {
        "current_w7": 3.2,
        "network_prediction": 3.18,
        "inertial_prediction": 3.2,
        "forecast_w8": 3.197,
        "shift": -0.003,
        "sigma": 0.22,
        "ci_80": [2.92, 3.48],
        "noise_dominated": true,
        "ci_excludes_current": false
      },
      ...
    },
    "directional_claims": [
      {
        "construct": "...",
        "direction": "up",
        "shift": 0.35,
        "ci_80": [3.10, 3.80],
        "current": 2.95
      }
    ],
    "n_directional_claims": 3,
    "n_noise_dominated": 17
  },
  "trends": {
    "autocracy_support|WVS_E": {
      "slope_per_decade": -0.12,
      "r_squared": 0.85,
      "p_value": 0.03,
      "trend_stable": true,
      "trend_direction": "down",
      "network_direction": "down",
      "agrees": true
    },
    ...
  },
  "trend_reversals": [
    {
      "construct": "...",
      "trend_direction": "up",
      "network_direction": "down",
      "trend_slope": 0.08,
      "trend_r2": 0.72,
      "network_shift": -0.15,
      "interpretation": "structural_opposition"
    }
  ]
}
```

---

## Stage 6: Curvature-Weighted Dynamics — DROPPED

### Reason

The TDA pipeline found Ollivier-Ricci curvature κ uniformly ≈ 1.0 across all
66 countries (mean = 0.9992, min = 0.9887, max = 1.0000). Zero edges have
negative curvature in any country. The curvature-weighted Laplacian
L^κ_{ij} = w_{ij}(1 + κ_{ij}) reduces to L^κ ≈ 2L — a scalar multiple of
the ordinary Laplacian. This multiplies all diffusion rates by 2 without
changing eigenvectors, mode shapes, or any structural property. Stage 6 would
produce identical results to Stage 2 (spectral diffusion) up to a time
rescaling.

The uniform positive curvature is a consequence of the network's high density
(23%) and near-complete subgraph structure. Ollivier-Ricci curvature measures
neighborhood overlap via optimal transport. When every node connects to ~23%
of all others, neighborhoods overlap massively → κ ≈ 1.0 everywhere. The
network has no bottleneck edges (negative curvature) because there are no
sparse bridges — it's a single dense connected component.

This is itself a finding: **WVS belief networks are geometrically flat.** SES-
mediated covariation is pervasive and structurally uniform, not concentrated
in narrow bottleneck pathways between ideological communities. The network does
not have the topological heterogeneity that makes curvature analysis
informative.

---

## Cross-Stage Validation

The five stages produce overlapping but distinct measures. Cross-validation
between stages tests internal consistency:

| Comparison | Expected relationship | If violated |
|------------|----------------------|-------------|
| BP lift vs PPR influence | High correlation (r > 0.7) — both measure "how much i affects j" | BP captures nonlinear coupling that PPR misses (or vice versa) |
| Fiedler partition vs γ sign structure | Alignment with the 52/48 pos/neg split | Spectral structure is organized by strength, not sign |
| PPR hubs vs FW mediators | Moderate correlation — both measure centrality | Mediators are bottlenecks; hubs are influencers. Divergence = distinct structural roles |
| Velocity direction vs residual direction | Anti-correlation — large velocity should predict residual sign | Network forces partially explain belief change |
| Forecast direction vs trend direction | Agreement for ~60-70% of constructs | Trend reversals identify structural tension |
| Within-country hubs vs cross-country corridors (Stage 3 vs 4) | Hubs should anchor corridors | If peripheral constructs create corridors, it's via structural equivalence, not influence |

---

## Execution Plan

### Phase A: Core engine (Stages 1-3), single country proof-of-concept

| Step | Task | Input | Output |
|------|------|-------|--------|
| A1 | Load MEX W7 weight matrix, parse construct labels | `matrices/MEX.csv` | 55×55 numpy array |
| A2 | Compute node priors (uniform or empirical) | `wvs_loader.py` | 55×5 prior array |
| A3 | Run BP: all 55 scenarios, β sensitivity sweep | A1, A2 | `MEX_bp.json` |
| A4 | Run spectral: eigendecomposition, Fiedler, diffusion map, scale sweep | A1 | `MEX_spectral.json` |
| A5 | Run PPR: full matrix, hub/sink scores, α sweep | A1 | `MEX_ppr.json` |
| A6 | Cross-validate: BP lift vs PPR, Fiedler vs sign structure | A3-A5 | Validation report |

### Phase A-batch: Scale to 66 countries

| Step | Task |
|------|------|
| A7 | Batch-run Stages 1-3 for all 66 countries |
| A8 | Cross-country Fiedler comparison (66×66 Rand index) |
| A9 | Cross-country hub comparison (55×66 rank matrix) |
| A10 | Identify universal vs zone-specific hubs |

### Phase B: Temporal dynamics (Stage 5)

| Step | Task | Input | Output |
|------|------|-------|--------|
| B1 | Load temporal weight matrices (MEX W3-W7) | `temporal/MEX_W{n}.csv` | 5 × 52×52 arrays |
| B2 | Compute mean construct responses per wave | `wvs_loader.py` | 5 × 52 vectors |
| B3 | Velocity field per wave | B1, B2 | Velocity vectors |
| B4 | Equilibrium distance per wave | B1, B2 | 5 scalars |
| B5 | Residual analysis (4 transitions) | B1, B2 | Residual vectors + ranking |
| B6 | Fit α* on 20-construct temporal core | B1, B2 | α*, per-transition α, RMSE |
| B7 | Generate W8 projection + uncertainty envelope | B6, B5 | Forecast + 80% intervals |
| B8 | Per-construct linear trends + network-trend comparison | B2, B7 | Trend reversals |

### Phase C: Regional multilayer (Stage 4)

| Step | Task |
|------|------|
| C1 | Identify missing GW transport plans for Latin America (13 countries, 78 pairs) |
| C2 | Recompute missing plans via Julia `tda_gromov_wasserstein.jl` |
| C3 | Build supra-adjacency for Latin America (715×715) |
| C4 | Run supra-graph PPR with 3 coupling functions |
| C5 | Extract belief corridors; validate against γ sign consensus |
| C6 | Repeat C1-C5 for Confucian zone; compare |

### Dependencies

```
wvs_loader.py (empirical marginals + mean responses)
    │
    ├──► Phase A (A1-A6) → Phase A-batch (A7-A10)
    │         │
    │         ├──► Phase B (B1-B8)
    │         │
    │         └──► Phase C (C1-C6) ← Julia GW recomputation
    │
    └──► Validation report (cross-stage)
```

### Effort Estimate

| Phase | Scripts | Compute time | Development |
|-------|---------|-------------|-------------|
| A (proof-of-concept) | 3 | <1 min | 1 day |
| A-batch | +batch wrapper | <10 min | 2-3 hours |
| B | 1 | <1 min | half day |
| C | 1 + Julia | <5 min | 1 day |
| **Total** | **5 + wrapper** | **<20 min** | **~3 days** |
