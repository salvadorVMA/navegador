# WVS Bridge Exploration Plan — Julia-Powered γ-Surface

## Context

The los_mex bridge methodology produces γ(construct_A, construct_B | SES) — measuring SES-mediated covariation between attitude constructs across different surveys. The Julia v4 sweep found 984/3869 significant bridges (25.4%) with median CI width 0.024, revealing a 94%-balanced bipartition along a PC1 education-vs-tradition axis.

WVS offers a fundamentally different test bed: a single well-designed survey instrument fielded across ~60 countries and 7 waves (1981–2022). This lets us ask three questions:
1. **Mexico validation** — Does γ within a single survey (same respondents) replicate the cross-survey los_mex bridge? How much tighter?
2. **Geographic generalization** — Does the bipartition structure hold globally? How do cultural zones differ?
3. **Temporal stability** — Are bridge relations stable from 1981 to 2022?

All bridge computations in Julia (30× faster than Python).

---

## Phase 0: Infrastructure

### 0A. Multi-context WVS construct builder
**New file:** `scripts/debug/build_wvs_constructs_multi.py`

- Extends existing `build_wvs_constructs.py` to handle any (wave, country) combo
- For each context, resolves Q-codes to actual column names via equivalences table (Wave 7 uses Q-codes, earlier waves use different codes — `wvs_ses_bridge._resolve_col()` already handles this)
- Checks per-construct item availability per context; falls back to single-item if <2 items available
- Outputs: enriched wvs_dict with `wvs_agg_*` columns + per-context manifest (construct availability, alpha)
- **Key concern:** construct availability drops in earlier waves (Wave 7: ~56, Wave 1-4: ~15-25 constructs)

### 0B. WVS CSV exporter for Julia
**New file:** `scripts/debug/export_wvs_for_julia.py`

Output structure:
```
data/julia_bridge_wvs/
  WVS_W7_MEX.csv       # rows=respondents, cols=SES vars + wvs_agg_* constructs
  WVS_W7_ARG.csv
  WVS_W1_MEX.csv       # temporal
  ...
  wvs_pairs.csv        # all cross-domain construct pairs
  wvs_manifest.json    # per-context: {csv_path, n_rows, constructs_available}
```

One CSV per (wave, country) — not per domain — because WVS respondents answer all domains in one survey. Follows pattern of existing `export_constructs_for_julia.py`.

### 0C. Julia WVS sweep module
**New file:** `julia/src/wvs_sweep.jl`

```julia
function run_wvs_sweep(csv_dir, pairs_path, manifest_path;
    output_path, ses_vars, n_sim=2000, n_bootstrap=200,
    contexts=String[], sweep_type=:within)
```

Three modes:
- `:within` — γ for all pairs within each context CSV (same respondents). Core use case.
- `:cross_context` — γ across two context CSVs (e.g., W3_MEX vs W7_MEX, or MEX vs ARG)
- `:cross_dataset` — γ between WVS context CSV and los_mex domain CSV

The existing `dr_estimate(df_a, col_a, df_b, col_b)` is context-agnostic — no changes needed to core estimator.

### 0D. Julia module update
**Modified:** `julia/src/NavegadorBridge.jl` — add `include("wvs_sweep.jl")`, export new functions.

---

## Phase 1: Mexico Validation

**Goal:** Can the bridge be replicated within WVS-Mexico?

### Step 1.1: WVS-MEX within-survey sweep (Julia, `:within`)
- 56 constructs, ~1200-1500 cross-domain pairs
- Within-survey = same respondents → "gold standard" (no cross-dataset uncertainty)
- **Expected:** ~15 min Julia runtime
- **Output:** `data/results/wvs_mex_w7_within_sweep.json`

### Step 1.2: Construct cross-map
**New file:** `scripts/debug/build_wvs_losmex_construct_map.py`
- Match WVS constructs to los_mex constructs via: (a) SES fingerprint cosine >0.8, (b) anchor discovery grade-3 shared items, (c) semantic equivalence
- **Output:** `data/results/wvs_losmex_construct_map.json`

### Step 1.3: Cross-dataset validation (Julia, `:cross_dataset`)
- For matched pairs, estimate γ(WVS_MEX, los_mex)
- Compare three values per matched pair: γ_within_wvs, γ_cross_dataset, γ_within_losmex

### Step 1.4: Validation analysis
**New file:** `scripts/debug/analyze_wvs_mex_validation.py`
- Scatter: γ_within_wvs vs γ_within_losmex for matched pairs
- Distribution of |γ_within − γ_cross|
- Sign agreement test (benchmark: 99.4% from fingerprint dot product)
- Key question: should WVS within-survey γ become the "golden truth"?
- **Output:** `data/results/wvs_mex_validation_report.md` + plots

---

## Phase 2: Geographic Sweep (Wave 7, ~60 Countries)

### Step 2.1: Build constructs for all W7 countries
- Run `build_wvs_constructs_multi.py` with waves=[7], countries=all
- Track per-country construct availability (~40-50 of 56 per country)

### Step 2.2: Export ~60 CSVs, run per-country sweep (Julia)
- ~60 countries × ~1200 pairs × 4s/pair / 8 threads ≈ **~10 hours**
- Checkpointed and resumable
- **Output:** `data/results/wvs_geographic_sweep_w7.json` — `{country: {pair: result}}`

### Step 2.3: Geographic analysis
**New file:** `scripts/debug/analyze_wvs_geographic.py`
- Per-pair γ stability across countries (mean, SD, range)
- Cultural zone aggregation (8 Inglehart-Welzel zones) — ANOVA: between-zone vs within-zone variance
- Mexico in Latin American context
- Bipartition generalization: does PC1 education-vs-tradition persist globally?
- **Output:** `data/results/wvs_geographic_report.md` + heatmap (countries × pairs)

---

## Phase 3: Temporal Sweep (Mexico, 7 Waves, 1981–2022)

### Step 3.1: Build constructs for MEX across all waves
- Item availability varies dramatically; only "classic" WVS items span all 7 waves
- Manifest records per-wave construct availability

### Step 3.2: Export 7 CSVs, run per-wave sweep (Julia)
- 7 waves × ~800 pairs avg × 4s/pair / 8 threads ≈ **~50 min**
- N per wave: W1=1,837, W2=1,531, W3=2,364, W4=1,535, W5=2,000, W6=2,000, W7=1,741
- **Output:** `data/results/wvs_temporal_sweep_mex.json` — `{wave: {pair: result}}`

### Step 3.3: Temporal analysis
**New file:** `scripts/debug/analyze_wvs_temporal.py`
- γ time series for pairs available in 3+ waves (ribbon plots with CIs)
- Trend detection: weighted linear regression of γ vs year (weight = 1/CI_width)
- Structural stability: rank correlation of γ vectors between adjacent waves
- Camp evolution: does the bipartition persist from 1981 to 2022?
- **Output:** `data/results/wvs_temporal_report.md` + ribbon plots

---

## Phase 4: 3D γ-Surface Analysis

### Step 4.1: Build unified γ-surface
**New file:** `scripts/debug/build_gamma_surface.py`

Combine all sweep outputs:
```python
gamma_surface[(construct_pair, country, wave)] = {gamma, ci_lo, ci_hi, n, excl_zero}
```

### Step 4.2: Dimensionality reduction
- Matrix: countries × construct-pairs (values = γ) for Wave 7
- PCA/UMAP → map countries into "attitude structure" space
- Compare to Inglehart-Welzel cultural map

### Step 4.3: Visualization
**New file:** `scripts/debug/visualize_gamma_surface.py`
1. Country map in PCA space (colored by cultural zone)
2. Heatmap: construct-pairs × countries with dendrogram clustering
3. Domain circle network per country (extend existing viz)
4. Temporal ribbon plots for selected pairs (1981–2022)
5. Mexico temporal trajectory in PCA space

---

## Execution Sequence

```
[Upload WVS CSVs]
    ↓
[Phase 0: Infrastructure — 0A→0B→0C/0D]
    ↓
[Phase 1: Mexico validation — validates methodology]
    ↓
[Phase 2 + Phase 3 — independent, can run in parallel]
    ↓
[Phase 4: 3D analysis — combines all results]
```

## Verification

- **Unit tests:** Extend `tests/unit/test_wvs_integration.py` (currently 135 tests) for multi-context construct builder and CSV exporter
- **Julia tests:** Add WVS sweep tests to `julia/test/runtests.jl`
- **Spot-check:** Run Phase 1 first (Mexico only, ~15 min) — compare a handful of pairs manually against Python `WVSBridgeEstimator` output
- **Cross-validate:** For Mexico W7, Julia `:within` mode γ should closely match Python `wvs_ses_bridge.estimate_within_wvs()` on same pairs

## Key Files to Modify/Create

| File | Action | Phase |
|------|--------|-------|
| `scripts/debug/build_wvs_constructs_multi.py` | Create | 0A |
| `scripts/debug/export_wvs_for_julia.py` | Create | 0B |
| `julia/src/wvs_sweep.jl` | Create | 0C |
| `julia/src/NavegadorBridge.jl` | Modify | 0D |
| `scripts/debug/build_wvs_losmex_construct_map.py` | Create | 1.2 |
| `julia/scripts/run_wvs_mex_validation.jl` | Create | 1.1/1.3 |
| `scripts/debug/analyze_wvs_mex_validation.py` | Create | 1.4 |
| `julia/scripts/run_wvs_geographic.jl` | Create | 2.2 |
| `scripts/debug/analyze_wvs_geographic.py` | Create | 2.3 |
| `julia/scripts/run_wvs_temporal.jl` | Create | 3.2 |
| `scripts/debug/analyze_wvs_temporal.py` | Create | 3.3 |
| `scripts/debug/build_gamma_surface.py` | Create | 4.1 |
| `scripts/debug/visualize_gamma_surface.py` | Create | 4.3 |

## Prerequisite

WVS CSV/zip files must be uploaded to `data/wvs/` before any execution:
- `F00011356-WVS_Cross-National_Wave_7_csv_v6_0.zip` (~20MB)
- `F00011931-WVS_Time_Series_1981-2022_csv_v5_0.zip` (~118MB)
