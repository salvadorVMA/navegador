# Message Passing on WVS Belief Networks — Implementation Plan

## Scope

Implement Stages 1-3 (BP, Spectral Diffusion, PPR) as the core within-country
propagation engine. Stage 4 (Multilayer) scoped to regional subsets with
justification below. Stage 5 (Temporal) descriptive-only. Stage 6 (Curvature)
dropped.

---

## Data Inventory (confirmed available)

| Asset | Path | Shape |
|-------|------|-------|
| Weight matrices (W7, 66 countries) | `data/tda/matrices/{ALPHA3}.csv` | 55×55 each |
| Distance matrices | `data/tda/matrices/{ALPHA3}_distance.csv` | 55×55 |
| Temporal weight matrices (MEX W3-W7) | `data/tda/temporal/MEX_W{n}.csv` | variable |
| Spectral distance matrix | `data/tda/spectral/spectral_distance_matrix.csv` | 66×66 |
| GW transport plans (top 50 pairs) | `data/tda/alignment/gw_transport_top50.json` | 55×55 per pair |
| GW distance matrix | `data/tda/alignment/gw_distance_matrix.csv` | 66×66 |
| Construct index | `data/tda/matrices/manifest.json` | 55 constructs, 8 zones |
| Construct-level sweep | `data/results/wvs_geographic_sweep_w7.json` | 68K estimates |

**Not available but needed:**
- Empirical response marginals per construct per country (for node priors in BP).
  Must be computed from WVS microdata via `wvs_loader.py`.
- Full GW transport plans for all 2,145 pairs (only top 50 stored).
  Stage 4 regional subset avoids this — only ~21-28 pairs needed.

---

## Stage 1: Within-Network Belief Propagation

### What it computes

Given hard or soft evidence at one construct (e.g., "this respondent strongly
agrees with institutional trust"), BP computes the implied posterior distribution
over all 54 other constructs. The **lift** (KL divergence from prior to posterior)
ranks which constructs are most constrained by the evidence.

### Implementation

**File:** `scripts/debug/mp_belief_propagation.py`

**Steps:**

1. **Load weight matrix** from `data/tda/matrices/{country}.csv` → 55×55 numpy
   array. Parse construct labels from CSV header row.

2. **Compute empirical marginals** (node priors). Two options:
   - **(a) From microdata** (preferred): Load WVS via `wvs_loader.py`, compute
     per-construct response frequency histograms. Requires binning `agg_*`
     construct scores into 5 categories (use the same `_bin_to_5` quantile cut
     as Julia). Output: `(55, 5)` array of marginal probabilities.
   - **(b) Uniform fallback**: If microdata unavailable for a country, use
     uniform `(55, 5)` priors. Document which countries use fallback.

3. **Instantiate `BeliefPropagator`** with Potts model (correct for ordinal
   constructs), `beta=2.0`, `damping=0.5`, `max_iter=200`.

4. **Run scenarios**: For each construct as evidence node, inject hard evidence
   at each of the 5 states. Collect lift vectors. Output: `(55, 5, 55)` tensor
   of lifts (evidence_construct × evidence_state × target_construct).

5. **Aggregate**: For each evidence construct, compute mean lift across states
   (which targets are most affected regardless of direction). Rank by mean lift.

**Output:** `data/tda/message_passing/{country}_bp_lifts.json`

```json
{
  "country": "MEX",
  "n_constructs": 55,
  "potential_type": "potts",
  "beta": 2.0,
  "convergence_rate": 0.95,
  "scenarios": {
    "institutional_trust|WVS_E": {
      "converged": true,
      "top_affected": [
        {"construct": "...", "mean_kl": 0.42, "modal_shift": [2, 3]},
        ...
      ]
    }
  }
}
```

**Bug fix from review:** The `neighbors` dict construction in the doc has a
variable shadowing error. Fix: use set comprehension with explicit tuple
unpacking (see feasibility review).

### Validation

- For constructs with γ ≈ 0 (SES-independent), BP lift should also be near zero.
  Cross-check against `wvs_geographic_sweep_w7.json`.
- Convergence rate across 66 countries: expect >90% given density=23% and
  damping=0.5. Flag non-converging countries.

### Runtime estimate

55 scenarios × 200 iterations × 55² message updates = ~60M ops per country.
66 countries: <5 minutes total (numpy vectorized).

---

## Stage 2: Spectral Diffusion

### What it computes

Eigendecomposition of the graph Laplacian reveals the **natural modes of belief
variation** in each country. The Fiedler vector (u₂) identifies the principal
axis that splits constructs into two maximally independent groups. The heat
kernel at time t shows how a localized belief shock spreads across the network
at different spatial scales.

### Implementation

**File:** `scripts/debug/mp_spectral_diffusion.py`

**Steps:**

1. **Symmetrize weight matrix**: `W_sym = (|W| + |W|ᵀ) / 2`. The γ-surface
   weights are already symmetric, but numerical precision may introduce tiny
   asymmetries.

2. **Build normalized Laplacian**: L = D^{-1/2}(D-W)D^{-1/2}. Use `scipy.linalg.eigh`
   for full eigendecomposition (55×55 is trivial).

3. **Fiedler analysis**: Extract u₂ (first non-trivial eigenvector). Partition
   constructs into positive/negative groups. This is the country's **principal
   belief axis** — the dimension along which constructs vary most independently.

4. **Diffusion map**: Embed constructs in 3D diffusion space at t=1.0.
   Save coordinates for visualization.

5. **Scale sweep**: Diffuse a unit impulse at each construct across
   t ∈ {0.01, 0.1, 0.5, 1.0, 5.0, 10.0}. Record which constructs receive
   signal at each scale. Short t = local neighborhood; long t = global structure.

6. **Cross-country Fiedler comparison**: Compare Fiedler partitions across
   66 countries. Compute Rand index between each pair of Fiedler partitions.
   Countries with similar Fiedler partitions have the same principal belief axis;
   dissimilar ones are organized along different dimensions.

**Output:**
- `data/tda/message_passing/{country}_spectral.json` — eigenvalues, Fiedler
  partition, diffusion map coordinates
- `data/tda/message_passing/fiedler_comparison.json` — 66×66 Rand index matrix

**Key diagnostic:** Compare Fiedler partition against the sign structure from
the γ-surface (the 52%/48% positive/negative split documented in CLAUDE.md).
If the Fiedler partition aligns with γ sign, it confirms the spectral structure
reflects the SES geometry. If not, the spectral view reveals structure beyond
SES (e.g., cultural or institutional clustering).

### Connection to existing TDA

The spectral features were already computed in `tda_spectral_distances.jl`, but
only the inter-country spectral distance matrix was saved — not the per-country
eigenstructure. This stage extracts the within-country spectral decomposition.
The Fiedler values from the temporal TDA (0.670→0.816→0.726 for Mexico W3→W5→W7)
provide a baseline for validation.

### Runtime estimate

`eigh` on 55×55: <1ms per country. 66 countries + cross-comparison: <10 seconds.

---

## Stage 3: Personalized PageRank Influence Mapping

### What it computes

For each construct i, PPR computes the steady-state probability that a random
walker (with restart probability α back to i) visits each other construct.
This gives the **sphere of influence** of each construct — not just direct
neighbors but the full transitive reach through the network.

Hub scores (sum of outgoing influence) identify **belief drivers**: constructs
whose shifts propagate broadly. Sink scores identify **belief consequences**:
constructs that are downstream of many others.

### Implementation

**File:** `scripts/debug/mp_ppr_influence.py`

**Steps:**

1. **Build transition matrix**: P = D⁻¹|W| (row-normalize absolute weights).

2. **Compute full PPR matrix**: Π (55×55) where column i = PPR vector seeded
   at node i. Power iteration with tol=1e-8 (converges in <100 iterations for
   these dense graphs).

3. **Extract metrics**:
   - Hub scores: Σⱼ Πⱼᵢ (total outgoing influence of i)
   - Sink scores: Σᵢ Πⱼᵢ (total incoming influence on j)
   - Asymmetry: Πⱼᵢ - Πᵢⱼ (directional dominance of each pair)

4. **α sensitivity sweep**: Run at α ∈ {0.10, 0.15, 0.20, 0.30, 0.50}.
   Report hub/sink rankings at each. Identify constructs whose ranking is
   α-stable (robust hubs) vs α-sensitive (proximity-dependent).

5. **Scenario interface**: `influence_of_shift(construct, magnitude)` →
   ranked implied shifts at all other constructs. This is the user-facing
   query: "if institutional trust rises by 1σ, what moves?"

6. **Cross-country hub comparison**: For each construct, compare hub scores
   across 66 countries. Constructs that are universal hubs (top-10 in most
   countries) vs culturally specific hubs (top-10 only in certain zones).

**Output:**
- `data/tda/message_passing/{country}_ppr.json` — hub scores, sink scores,
  asymmetry matrix, α sensitivity
- `data/tda/message_passing/ppr_hub_comparison.json` — construct × country
  hub rank matrix

### Validation

Cross-check hub rankings against TDA mediator scores from
`data/tda/floyd_warshall/mediator_scores.json`. High-mediator constructs
(gender_role_traditionalism for MEX/BRA, science_skepticism for USA/JPN)
should also rank as high PPR hubs. If they diverge, that's informative:
mediator = structural bottleneck; hub = influence reach. A construct can be
a bottleneck without being influential (if it connects small communities).

### Runtime estimate

55 PPR vectors × 100 iterations × 55² matrix-vector: <1 second per country.
5 α values × 66 countries: <5 minutes total.

---

## Stage 4: Multilayer Message Passing — Regional Scope

### Why full 66-country multilayer is infeasible

Three compounding problems make all-country multilayer impractical:

**1. Missing transport plans.** Only 50 of the 2,145 country pairs have stored
GW transport plans (`gw_transport_top50.json`). The remaining 2,095 would need
recomputation. Each GW alignment takes ~0.05s in Julia, so recomputation is
fast (~2 min), but the storage is 2,145 × 55 × 55 × 8 bytes ≈ 53 MB — manageable
but unnecessary if the transport plans are near-uniform (which they are: GW
self-match rate was only 3.1%).

**2. Near-uniform transport plans.** The 3.1% self-match rate means constructs
do NOT occupy stable structural positions across countries. The GW transport
plan for most pairs is close to the uniform 1/55 matrix — it says "every
construct in country A maps a little bit to every construct in country B."
This is not a failure of the algorithm; it reflects that **construct networks
are structurally similar across countries** (spectral zone coherence p=0.001)
but **individual constructs are not pinned to fixed structural roles**.
Propagating through a near-uniform transport plan smears the signal —
multilayer BP degenerates to "everything affects everything equally."

**3. Supra-graph density.** Even with sparse country coupling (k-NN), the
supra-adjacency for 66 countries × 55 constructs = 3,630 nodes with ~23%
internal density produces ~1.5M edges. BP on this graph is tractable
computationally but interpretively opaque — the output is a 3,630-dimensional
posterior that no one can act on.

### Why regional aggregation fixes this

Within a cultural zone, countries share more structural similarity (that's
what zone coherence p=0.001 means). The GW transport plans within zones are
sharper — constructs have more consistent structural roles among culturally
similar countries. This means:

- Transport plans within Latin America (13 countries) are more concentrated
  than random cross-zone pairs → signal propagates meaningfully rather than
  smearing
- 13 countries × 55 constructs = 715 nodes — interpretable output
- Only 78 within-zone pairs need transport plans (computable in <10s)
- Results can be compared across zones: "how does multilayer propagation
  differ between Latin America and Confucian Asia?"

### Implementation

**File:** `scripts/debug/mp_multilayer.py`

**Steps:**

1. **Select regional subset**: Start with Latin America (13 countries: ARG, BOL,
   BRA, CHL, COL, ECU, GTM, MEX, NIC, PER, PRI, URY, VEN). Second run:
   Confucian (8 countries) for contrast.

2. **Compute missing GW transport plans**: For within-zone pairs not in the
   top-50 file, recompute via Julia `tda_gromov_wasserstein.jl` using existing
   distance matrices. Store as `data/tda/message_passing/{zone}_transport.json`.

3. **Build supra-adjacency**: Intra-layer = country weight matrices. Inter-layer =
   transport plans × coupling weight ω. Test three coupling functions:
   - Inverse spectral distance: ω = 1/d
   - Gaussian: ω = exp(-d²/2σ²), sweep σ
   - Binary threshold: ω = 1 if d < median, else 0

4. **Run within-zone PPR** (not full BP — PPR is more stable on dense graphs):
   For each construct in each country, compute PPR on the supra-graph. Extract
   cross-country influence: "institutional trust in MEX → what in BRA?"

5. **Identify belief corridors**: Country pairs × constructs with highest
   cross-country PPR scores. These are the pathways where belief shifts
   transfer most efficiently.

**Output:**
- `data/tda/message_passing/{zone}_multilayer_ppr.json`
- `data/tda/message_passing/{zone}_belief_corridors.json`

### Validation

Compare top belief corridors against the γ-surface cross-zone sign consensus.
Constructs with consistent γ signs within a zone should have strong corridors;
contested constructs (sign flips) should have weak or absent corridors.

### Runtime estimate

Latin America: 13 PPR matrices (55×55) + supra-graph PPR (715×715): <30 seconds.
GW recomputation for missing pairs: <10 seconds in Julia.

---

## Stage 5: Temporal Dynamics — Descriptive + Constrained Forecast

### What we keep

The temporal model provides **3 descriptive analyses** and **1 constrained
forecast** on Mexico W3-W7. No Graph RNN, no learned parameters beyond a
single global mixing coefficient.

**5a. Velocity field per wave:**
For each wave, compute Δxᵢ = Σⱼ wᵢⱼ(xⱼ - xᵢ). This shows which constructs
are being "pulled" by their network neighbors — the direction the network
structure implies beliefs should move. Constructs with large |velocity| are
under tension: their current state disagrees with their neighborhood.

**5b. Distance from equilibrium per wave:**
The network-implied equilibrium (null space of L) is the consensus state.
The L2 distance from actual belief state to equilibrium measures how far
Mexico is from its network-consistent resting point. If distance decreases
across waves, Mexico's beliefs are converging toward network consistency.
If distance increases, exogenous forces (economic, political) are pushing
beliefs away from the network's structural attractor.

**5c. Residual analysis:**
For consecutive wave pairs (W3→W4, W4→W5, W5→W6, W6→W7), compute
x̂(t+1) = A(t)·x(t) and residual = x(t+1) - x̂(t+1). Constructs with
large residuals changed for reasons the network cannot explain — exogenous
shocks. This is the most substantively interesting output: it separates
**network-predicted evolution** (constructs that moved as the network
implied) from **unexplained shifts** (constructs that moved independently).

**5d. Network-regularized forecast (W8 projection):**

The full graph autoregression x̂(t+1) = A(t)·x(t) is underdetermined (55²
parameters from 1 observation per transition). But a **1-parameter model**
that pools information across all 55 constructs is defensible:

$$\hat{x}(t+1) = \alpha \cdot A(t) \cdot x(t) + (1 - \alpha) \cdot x(t)$$

This is a convex blend of "the network pulls beliefs toward their neighbors"
(A·x) and "beliefs stay where they are" (x). The single parameter α ∈ [0,1]
controls the mixing strength — how much the network structure matters relative
to inertia.

**Fitting α:** Minimize mean squared prediction error across all 4 transitions
× 55 constructs = 220 observations:

$$\alpha^* = \arg\min_\alpha \sum_{t} \| \hat{x}^{(\alpha)}(t+1) - x(t+1) \|^2$$

This is a 1D optimization over 220 data points — statistically sound. The
expected α is small (beliefs are mostly inertial, the network provides a
weak directional pull), likely in the range 0.05–0.20.

**Forecast:** Apply x̂(W8) = α*·A(W7)·x(W7) + (1-α*)·x(W7), assuming the
W7 network persists. This is a "network-implied tendency" — where beliefs
would drift if the current SES structure continues to operate.

**Uncertainty envelope:** The 4 historical residual vectors provide an empirical
distribution of prediction error. For each construct i, compute:
- σᵢ = std of residuals across the 4 transitions
- 80% prediction interval: x̂ᵢ(W8) ± 1.28·σᵢ
- Flag constructs where σᵢ > |x̂ᵢ(W8) - xᵢ(W7)| as "forecast dominated by
  noise" (the predicted shift is smaller than the historical error)

**What this can and cannot say:**
- CAN: "the network structure at W7 pulls institutional trust upward and
  religious exclusivism downward, with a mixing strength of α*=0.12"
- CAN: "constructs X, Y, Z have prediction intervals that exclude their
  current value — the network predicts directional change"
- CANNOT: predict magnitude with precision (σᵢ is estimated from 4 points)
- CANNOT: account for structural breaks (network rewiring between waves)
- CANNOT: predict exogenous shocks (which dominate the residuals)

**Supplementary: per-construct trend extrapolation.** As a second forecast
layer independent of the network model, fit a simple linear trend per
construct: xᵢ(t) = aᵢ + bᵢ·t, fit from 5 wave means. Report:
- Slope bᵢ with R² and p-value (from 5-point OLS)
- Constructs with R² > 0.7 and p < 0.10 are trend-stable (the direction is
  reliable even if the magnitude isn't)
- Compare network forecast direction (sign of x̂ᵢ(W8) - xᵢ(W7)) against
  trend direction (sign of bᵢ). Agreement = the network and historical
  momentum point the same way. Disagreement = the network structure at W7
  would reverse the historical trend — these are the most interesting
  constructs, where SES geometry has shifted against the prevailing direction.

### Honest framing

The forecast is explicitly labeled as **"network-implied tendency under
structural persistence"**, not a prediction. It answers: "if nothing changes
about the SES structure of Mexican society except the passage of time, where
do the network dynamics pull beliefs?" The uncertainty envelope shows that
for most constructs, the predicted shift is smaller than historical noise —
the honest answer is "we can identify direction but not magnitude." The
constructs where the interval excludes the current value are the few where
the network makes a directional claim strong enough to rise above the noise
floor.

### Implementation

**File:** `scripts/debug/mp_temporal_descriptive.py`

**Steps:**

1. Load temporal weight matrices from `data/tda/temporal/MEX_W{n}.csv` (5 waves).
2. Load mean construct responses per wave from WVS microdata (compute via
   `wvs_loader.py` if not cached).
3. Compute velocity field, equilibrium distance, and residuals per wave.
4. Rank constructs by residual magnitude across wave transitions.
5. Fit α* via 1D grid search (or `scipy.optimize.minimize_scalar`) over the
   4 transitions.
6. Generate W8 projection: x̂(W8) = α*·A(W7)·x(W7) + (1-α*)·x(W7).
7. Compute per-construct σᵢ from historical residuals; build 80% prediction
   intervals.
8. Fit per-construct linear trends; compare trend direction vs network
   forecast direction.
9. Cross-reference largest residuals with known Mexican historical events
   (1994 peso crisis near W3, 2006 election crisis near W5, etc.).

**Output:** `data/tda/message_passing/mex_temporal_dynamics.json`

```json
{
  "descriptive": {
    "velocity_fields": {"W3": [...], ...},
    "equilibrium_distances": {"W3": 0.42, ...},
    "residuals": {
      "W3_W4": {"construct": "...", "residual": 0.15, ...},
      ...
    }
  },
  "forecast": {
    "alpha_star": 0.12,
    "alpha_fit_rmse": 0.08,
    "w8_projection": {
      "institutional_trust|WVS_E": {
        "current_w7": 3.2,
        "forecast_w8": 3.35,
        "shift": 0.15,
        "sigma": 0.22,
        "ci_80": [3.07, 3.63],
        "noise_dominated": true,
        "trend_slope": 0.04,
        "trend_r2": 0.81,
        "trend_agrees_with_network": true
      },
      ...
    },
    "directional_claims": ["list of constructs where CI excludes current value"],
    "trend_reversals": ["list of constructs where network and trend disagree"]
  }
}
```

### Runtime estimate

5 matrix operations on 55×55 + 1D optimization + 55 linear regressions: <2 seconds.

---

## Stage 6: Curvature-Weighted Dynamics — DROPPED

### Reason

The TDA pipeline found Ollivier-Ricci curvature κ ≈ 1.0 uniformly across all
66 countries and all edges. The curvature-weighted dynamics model modifies edge
influence by the factor (1 + κ). When κ ≈ 1.0 everywhere, this factor ≈ 2.0
uniformly — it multiplies all dynamics by a constant scalar, adding no
information beyond what the flat Laplacian already captures.

The uniformly positive curvature is a consequence of the network's density
(23%) and near-complete subgraph structure. In a network where every node
connects to ~23% of all others, neighborhoods overlap massively → Ollivier-Ricci
curvature (which measures neighborhood overlap via Wasserstein distance) is
uniformly high. There are no bottleneck edges (negative curvature) because
there are no sparse bridges — the network is a single dense connected component
with 22 isolated nodes.

**Forman-Ricci** would show slightly more variation (it's sensitive to degree
differences), but the fundamental issue remains: the network lacks the
topological heterogeneity (communities connected by narrow bridges) that makes
curvature-weighted dynamics informative. This is itself a finding: **WVS belief
networks are geometrically flat**, meaning SES-mediated covariation is
pervasive and structurally uniform rather than concentrated in bottleneck
pathways.

---

## Execution Order

### Phase A: Core engine (Stages 1-3, single country)

1. Write `mp_belief_propagation.py` — BP on MEX W7 as proof-of-concept
2. Write `mp_spectral_diffusion.py` — Fiedler + diffusion map for MEX
3. Write `mp_ppr_influence.py` — PPR + hub/sink analysis for MEX
4. Validate all three against γ-surface and TDA mediator scores
5. Run Stages 1-3 across all 66 countries (batch mode)
6. Cross-country comparisons: Fiedler partition similarity, hub consistency

### Phase B: Temporal dynamics (Stage 5)

7. Write `mp_temporal_descriptive.py` — velocity/equilibrium/residuals for MEX
8. Fit α* and generate W8 network-implied projection with uncertainty envelope
9. Fit per-construct linear trends; identify trend-reversal constructs
10. Cross-reference residuals and forecasts with historical events

### Phase C: Regional multilayer (Stage 4)

11. Compute missing GW transport plans for Latin America (Julia)
12. Write `mp_multilayer.py` — supra-graph PPR for Latin America
13. Extract belief corridors
14. Repeat for Confucian zone, compare

### Dependencies

```
wvs_loader.py (empirical marginals)
    │
    ├──► Phase A: Stages 1-3
    │        │
    │        ├──► Phase B: Stage 5 (needs mean responses from loader)
    │        │
    │        └──► Phase C: Stage 4 (needs within-country PPR from Stage 3)
    │
    └──► Julia GW recomputation (Phase C only)
```

### Estimated total effort

| Phase | Scripts | Runtime (compute) | Wall time (development) |
|-------|---------|-------------------|------------------------|
| A | 3 | <10 min | 1 day |
| B | 1 | <1 min | half day |
| C | 1 + Julia | <5 min | 1 day |
| **Total** | **5** | **<20 min** | **~2 days** |
