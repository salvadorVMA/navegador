# SES Bridge Improvement Plan: Options 3 and 4

*Drafted 2026-02-24 — worktree-knowledge-graph branch*

---

## Context

The baseline SES bridge (`CrossDatasetBivariateEstimator` in `ses_regression.py`) estimates
cross-survey bivariate associations by fitting both variables on shared SES predictors, then
simulating a joint distribution over a synthetic SES population. The 276-pair sweep revealed
extreme compression (V range 0.081–0.116, IQR 0.010) and near-universal significance (93%),
making the bridge useful only as a demographic-saturation score, not as a measure of
conceptual domain associations.

The baseline bridge was extended (2026-02-24) to include `Tam_loc` (locality size, 24/26 surveys)
and `est_civil` (marital status, 26/26 surveys) alongside the original five predictors
(`sexo`, `edad`, `region`, `empleo`, `escol`). Religion was found in only 2/26 surveys and
is excluded. State (`edo`) has 32 raw INEGI codes with no label mapping and risks convergence
failures; excluded for now.

This document describes the development plans for two further improvements:

- **Option 3**: Mantel-Haenszel Residual Bridge — measures domain association *beyond* shared SES
- **Option 4**: Ecological Bridge — measures domain co-variation *across Mexican geography*

---

## Option 3: Mantel-Haenszel Residual Bridge

### Motivation

The baseline bridge V conflates two things:
1. Between-SES-cell variation: domains A and B both vary with demographics, so any two
   SES-stratified variables will appear correlated
2. Within-SES-cell variation: domains A and B co-vary *even among respondents with identical
   demographic profiles* — this is what "conceptual association beyond demographics" looks like

The Mantel-Haenszel approach measures only the second component.

### Algorithm

```
ResidualBridgeEstimator.estimate(var_a, var_b, df_a, df_b):

1. Fit model_a: P(var_a | SES) via OrderedModel / MNLogit
   Fit model_b: P(var_b | SES) via OrderedModel / MNLogit

2. Discretize SES space into K cells:
   - Encode the reference SES population (n_sim=2000) into numeric features via SESEncoder
   - Cluster into K=20–40 groups using KMeans on the feature matrix
   - Assign each synthetic respondent to a cell index k ∈ {0…K-1}

3. For each cell k:
   a. Simulate n_k responses for var_a using model_a (conditional on cell k's SES profile)
   b. Simulate n_k responses for var_b using model_b (conditional on cell k's SES profile)
   c. Build contingency table T_k = crosstab(sim_a_k, sim_b_k)
   d. Record T_k, chi2_k, and n_k

4. Mantel-Haenszel aggregation:
   - MH chi-square: χ²_MH = (Σ_k a_k - E_k)² / Σ_k Var_k
     where a_k, E_k, Var_k follow the standard MH formula for each 2x2 stratum
     (for multi-category variables: use the generalised CMH test, available in
     scipy.stats.chi2_contingency on pooled within-stratum tables)
   - Alternatively: compute a stratum-weighted average V across cells
     V_residual = Σ_k (n_k / N) * V_k

5. Compare:
   - V_baseline = V from standard CrossDatasetBivariateEstimator (between + within)
   - V_residual = V_MH from step 4 (within-SES only)
   - SES_explained = V_baseline - V_residual  (the demographic component)
   - ratio = V_residual / V_baseline  (fraction unexplained by SES)
```

### Implementation

**New class:** `ResidualBridgeEstimator` in `ses_regression.py`

Key parameters:
- `n_sim: int = 2000` — synthetic population size (same as baseline)
- `n_cells: int = 30` — number of SES cells for stratification
- `cell_method: str = 'kmeans'` — how to discretize SES space ('kmeans' or 'quantile')

Dependencies to add: `sklearn.cluster.KMeans` (already available via scikit-learn)

**New fields in output dict:**
```python
{
    'cramers_v': float,           # baseline bridge V (for comparison)
    'cramers_v_residual': float,  # within-SES-cell V (MH-aggregated)
    'ses_fraction': float,        # V_baseline / V_residual ratio
    'n_cells_used': int,          # K cells with n_k >= min_cell_size
    'method': 'ses_residual_bridge',
}
```

### Expected behaviour

- V_residual will be smaller than V_baseline for all pairs (since it removes the SES component)
- The *spread* of V_residual should be larger than baseline V, enabling domain differentiation
- Domain pairs where V_residual ≈ V_baseline: association is NOT demographically mediated
  (e.g., conceptually linked domains like RELIGION × LAICIDAD)
- Domain pairs where V_residual << V_baseline: association is almost entirely SES-driven

### Caveats

- Within-cell simulation still uses the same SES models — within-cell variation reflects
  model noise and residual heterogeneity, not a direct measure of latent conceptual association
- Small cells (n_k < 10) will produce unstable within-cell V; exclude from MH aggregation
- K is a tuning parameter; K too small → cells still SES-heterogeneous; K too large → sparse cells

### Comparison with baseline

Run both estimators on the same 276 pairs. Produce a comparison report:

| Domain pair | V_baseline | V_residual | SES fraction | Δ interpretation |
|-------------|-----------|-----------|-------------|-----------------|
| CIE × POB   | 0.116     | ?         | ?           | …               |
| DEP × SAL   | 0.081     | ?         | ?           | …               |

---

## Option 4: Ecological Bridge

### Motivation

Since surveys share no common respondents, but they *do* share geography (`edo` = Mexican state,
1-32) and locality size (`Tam_loc`), we can link them at the aggregate level. For each
state × locality-size cell, compute the mean (or modal) response to each variable in Survey A
and Survey B, then correlate these cell-level aggregates across geography.

This produces a real (non-simulated) correlation, subject only to the ecological fallacy, and is
immune to the compression problem that affects the SES bridge.

### Algorithm

```
EcologicalBridgeEstimator.estimate(var_a, var_b, df_a, df_b):

1. Define geographic cells:
   - Cell key = (edo, Tam_loc_bin) where Tam_loc_bin ∈ {1,2,3,4}
   - Maximum cells: 32 states × 4 locality sizes = 128 cells
   - Filter to cells with n ≥ min_cell_n in BOTH surveys (e.g., min_cell_n = 20)

2. Aggregate var_a within Survey A cells:
   - For each cell (s, t): compute weighted mean of var_a (using Pondi2)
     If var_a is categorical, use the weighted modal category, or
     convert to numeric (rank-based or ordinal encoding)
   - Result: Series of length = number of cells with coverage in Survey A

3. Aggregate var_b within Survey B cells:
   - Same as above for Survey B

4. Merge on cell key (inner join → cells present in both surveys)
   - Result: DataFrame with columns [cell_key, agg_a, agg_b, n_a, n_b]
   - Minimum overlap: require ≥ 30 merged cells for a reliable estimate

5. Compute association on merged cell-level data:
   - Weighted Spearman ρ (weight = geometric mean of n_a and n_b per cell)
   - Optionally: weighted Pearson r if both aggregates are continuous/ordinal
   - Convert to Cramér's V equivalent for comparability:
     V_eco = |ρ| (Spearman ρ serves as a standardised effect size directly)

6. Bootstrap CI: resample cells with replacement 500 times to get SE and 95% CI
```

### Implementation

**New class:** `EcologicalBridgeEstimator` in `ses_regression.py`

Key parameters:
- `min_cell_n: int = 20` — minimum respondents per cell per survey
- `min_merged_cells: int = 30` — minimum overlapping cells for a valid estimate
- `agg_method: str = 'mean'` — aggregation method ('mean', 'mode', 'rank_mean')
- `n_bootstrap: int = 500`

Dependencies: only `scipy.stats` (already available)

**New fields in output dict:**
```python
{
    'spearman_rho': float,        # primary effect size
    'spearman_p': float,
    'ci_95': Tuple[float, float], # bootstrap 95% CI
    'n_cells': int,               # number of merged cells used
    'method': 'ecological_bridge',
}
```

### Expected behaviour

- V_eco will span a much wider range than V_baseline (0 to 0.5+), enabling genuine domain
  differentiation
- High V_eco: domains co-vary geographically — states that score high on domain A also score
  high on domain B (e.g., POBREZA × EDUCACION likely high)
- Low V_eco: domains are geographically independent (e.g., DEPORTES × LAICIDAD likely near 0)
- Comparing V_eco with V_baseline and V_residual gives a triangulated picture:
  - High V_baseline + High V_eco: association has both demographic and geographic components
  - High V_baseline + Low V_eco: association is purely demographic, not geographic
  - Low V_baseline + High V_eco: geographic pattern not explained by demographics

### Key limitation

The ecological bridge is subject to the **ecological fallacy**: cell-level correlations can
diverge from individual-level correlations. A state that scores high on poverty AND high on
religiosity does not necessarily mean that poor individuals are more religious.

### Caveats

- Cell coverage: small states (e.g., Colima, Baja California Sur) combined with rural locality
  sizes may produce cells with n < 20 — these are excluded
- Some surveys may not have enough geographic spread (all respondents in urban areas)
- `edo` has no value labels in the JSON — use raw INEGI codes 1-32 as cell keys
- Survey B may have been fielded only in certain states — check coverage before reporting

---

## Comparison Framework

### Running all three methods

A comparison sweep script should:

```
for each domain pair (domain_a, domain_b):
    for each (var_a, var_b) in top-K cross-pair variable combos:
        result_baseline  = CrossDatasetBivariateEstimator().estimate(...)
        result_residual  = ResidualBridgeEstimator().estimate(...)
        result_ecological = EcologicalBridgeEstimator().estimate(...)
        record all three V values
```

Suggested script: `scripts/debug/sweep_bridge_comparison.py`
Output: `data/results/bridge_comparison_report.md` and
        `data/results/bridge_comparison_results.json`

### Interpretation matrix

| V_baseline | V_residual | V_eco | Interpretation |
|-----------|-----------|-------|---------------|
| High | High | High | Strong association: demographic + geographic + conceptual |
| High | Low | High | Geographically real but fully SES-mediated |
| High | Low | Low | Pure SES confounding, no geographic/conceptual signal |
| Low | Low | High | Geographic pattern not captured by demographics |
| Low | Low | Low | Domains are genuinely independent across all dimensions |
| High | High | Low | Demographic + conceptual, but geographically uniform |

---

## Implementation Priority

| Step | Task | Effort | Status |
|------|------|--------|--------|
| A | Expand SES bridge: add Tam_loc, est_civil | Low | **Done (2026-02-24)** |
| B | Run baseline sweep with expanded predictors | Low | In progress |
| C | Implement `ResidualBridgeEstimator` | Medium | Planned |
| D | Implement `EcologicalBridgeEstimator` | Medium | Planned |
| E | Sweep all three methods on 276 pairs | Low | Planned |
| F | Write comparison report | Low | Planned |

---

## Files Affected

| File | Change |
|------|--------|
| `ses_regression.py` | Add `ResidualBridgeEstimator`, `EcologicalBridgeEstimator` classes |
| `ses_analysis.py` | Already updated: Tam_loc and est_civil normalization in `preprocess_survey_data` |
| `scripts/debug/sweep_cross_domain.py` | May need `--method` flag to select estimator |
| `scripts/debug/sweep_bridge_comparison.py` | New: runs all three methods in one pass |
| `data/results/bridge_comparison_report.md` | New: comparison output |
