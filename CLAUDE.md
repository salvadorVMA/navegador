# Navegador - AI Survey Analysis Platform

## Overview

Navegador is an AI-powered survey analysis platform that uses Large Language Models (LLMs) and intelligent agent systems to analyze and extract insights from survey data. The project focuses on Mexican survey data ("los_mex") and provides conversational interfaces for querying survey insights.

## Project Goals & Philosophy

Navegador is a **demonstration project** intended to be made publicly accessible on the open internet. It serves as a self-contained showcase of LLM and agentic capabilities applied to highly customized data analysis of survey research. It is intended to be used by a broad range of users, from the general public to social scientists.

**Key principles:**
- **Modularity & Flexibility**: Components should be loosely coupled and easily swappable (e.g., different LLMs, data sources, analysis pipelines)
- **Public-ready**: The codebase is being prepared for open public access and should be clean, well-documented, and self-explanatory
- **Demo-to-production path**: Not production-ready today, but structured so that it can become production-ready with minimal effort
- **Self-contained**: The project should work as a complete, standalone demonstration without external dependencies beyond API keys

## Core Capabilities

- **Multi-LLM Support**: OpenAI GPT, Anthropic Claude, Google Gemini
- **Pattern Identification**: Detect similar/different patterns in survey responses
- **Semantic Variable Selection**: Natural language queries mapped to survey variables
- **Cost Optimization**: ChromaDB + JSON caching for 70% cost reduction
- **Interactive Dashboard**: Web interface for exploration and analysis
- **LangSmith Monitoring**: Tracing and observability for LLM operations

## Architecture

```
User Interface (Dashboard/CLI/Agent)
    ↓
Agent Layer (LangGraph)
    ↓
Processing Layer (LLM Integration, Cache, Analysis)
    ↓
Data Layer (ChromaDB embeddings, JSON files)
```

## Key Entry Points

| Entry Point | Purpose | Command |
|-------------|---------|---------|
| `main.py` | CLI agent interface | `python main.py` |
| `dashboard.py` | Web interface | `python dashboard.py` (port 8050) |
| `agent.py` | Core agent module | Import for programmatic use |

## Project Structure

```
/workspaces/navegador/
├── Core Modules (root)     # agent.py, dashboard.py, config.py, etc.
├── data/encuestas/         # Survey data (JSON, Git LFS)
├── data/results/           # Analysis outputs
├── docs/                   # Documentation
├── notebooks/              # Jupyter notebooks (analysis, preprocessing)
├── tests/                  # Unit, integration, e2e tests
├── scripts/                # Debug, fixes, deployment, setup
├── docker/                 # Container configuration
└── config/                 # Environment and dependencies
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `agent.py` | Main agent workflow and orchestration |
| `analytical_essay.py` | Two-step essay pipeline: reasoning outline + essay generation |
| `quantitative_engine.py` | Pure-computation report with sentinel filtering, label resolution, cross-dataset bivariate |
| `ses_regression.py` | SES-bridge cross-dataset bivariate estimation (OrderedModel / MNLogit) |
| `ses_analysis.py` | SES preprocessing: variable creation, sentinel remapping, ordinal normalisation |
| `survey_kg.py` | Knowledge graph ontology for survey domains (domain/variable/concept nodes) |
| `dashboard.py` | Dash web interface |
| `config.py` | Configuration and path management |
| `detailed_analysis.py` | Legacy analysis pipeline (OLD architecture) |
| `variable_selector.py` | Query-to-variable semantic matching |
| `meta_prompting.py` | Prompt optimization system |
| `cache_manager.py` | LLM response caching |
| `dataset_knowledge.py` | Survey data loading and metadata |

## Tech Stack

- **AI/LLM**: LangChain, LangGraph, LangSmith, OpenAI, Anthropic, Google GenAI
- **Data**: ChromaDB, Pandas, NumPy
- **Web**: Dash, Plotly, Flask
- **Config**: python-dotenv, Pydantic
- **Testing**: pytest, Playwright
- **Deployment**: Docker (Mambaforge base), Conda/Mamba

## Data

- **Survey Dataset**: `data/encuestas/los_mex_dict.json` (~191MB, Git LFS)
- **Format**: JSON dictionary mapping questions to aggregated responses
- **Processing**: ChromaDB embeddings for semantic search

## Active Branches

### `feature/bivariate-analysis` (branched from `Claude1`)

Primary development branch for los_mex SES bridge work, construct-level analysis, and all core modules.

The `worktree-knowledge-graph` worktree has been **merged** into this branch (commit `0f1fb30`). All knowledge-graph and expanded SES-bridge work now lives in the main workspace.

### `wvs` (branched from `feature/bivariate-analysis`)

World Values Survey integration branch. Extends the SES bridge to WVS data, adding time (7 waves, 1981-2022) and geography (66 countries, 8 cultural zones) dimensions. Key additions:
- `data/wvs/` — WVS metadata files (variable equivalences, country codes, questionnaires)
- `docs/WVS_INTEGRATION_PLAN.md` — Full integration plan with γ-surface formulation
- WVS data zips (Wave 7 + Time Series) stored locally but gitignored (138MB)

#### WVS Phase 1 ✅ COMPLETE (2026-03-12)

| Module | Purpose |
|--------|---------|
| `wvs_metadata.py` | Parse equivalence XLSX → a_code/title/domain/wave Q-codes; `CULTURAL_ZONES` (8 IW zones); `SES_VARS` harmonization config; country registry helpers |
| `wvs_loader.py` | `WVSLoader` class: load CSV from zip/file, filter by wave+country, clean sentinels, harmonize SES vars, build `wvs_dict`, JSON cache save/load |
| `tests/unit/test_wvs_integration.py` | 75 tests covering all Phase 1 functionality |

**wvs_dict structure** (mirrors los_mex_dict):
- `enc_dict`: `WVS_W{n}_{ALPHA3}` keys → `{dataframe, metadata}`
- `enc_nom_dict`: `W{n}_{ALPHA3}` short IDs
- `pregs_dict`: `{Q-code|short_id: survey_key|title}`
- `ses_dict`: harmonized SES cols per survey
- `var_equivalences`: equivalence DataFrame
- `country_registry`: wave participation counts

**SES harmonization** (income excluded; 4-var config matching v3 sweep):
- `Q260 → sexo` (direct: 1=M, 2=F)
- `Q262 → edad` (continuous → 7 age bins, matches `ses_analysis.categorize_age`)
- `Q275 → escol` (ISCED 0-8 → 5-level ordinal)
- `G_TOWNSIZE → Tam_loc` (8-level → 4-level collapse)

**CLI:** `python wvs_loader.py --waves 7 --countries MEX ARG --output data/wvs/wvs_dict.json`
**Mexico time series:** `python wvs_loader.py --mexico-ts`

#### WVS Phase 2 ✅ COMPLETE (2026-03-12)

| Module | Purpose |
|--------|---------|
| `wvs_ses_bridge.py` | `SESHarmonizer` (validate SES cols, build standardized/zone-pooled reference populations); `WVSBridgeEstimator` (wraps DR estimator for WVS); `temporal_sweep()`, `geographic_sweep()`; `summarise_temporal()`, `summarise_geographic()` |
| `tests/unit/test_wvs_integration.py` | Extended to 108 tests (33 new Phase 2 tests) |

**Weight unification:** `W_WEIGHT` (WVS) and `Pondi2` (los_mex) both normalised to `bridge_weight` before passing to `DoublyRobustBridgeEstimator`.

**γ-surface API (`WVSBridgeEstimator`):**
- `estimate_cross_dataset(df_wvs, col_wvs, df_los_mex, col_los_mex)` — WVS × los_mex
- `estimate_within_wvs(df_a, col_a, df_b, col_b)` — WVS × WVS (cross-wave or cross-country)
- `temporal_sweep(enc_dict, col_a, col_b, country='MEX')` → `{wave: result}`
- `geographic_sweep(enc_dict, col_a, col_b, wave=7, zone=None)` → `{alpha3: result}`

#### WVS Phase 3 ✅ COMPLETE (2026-03-12)

| Module | Purpose |
|--------|---------|
| `wvs_anchor_discovery.py` | `WVSAnchorDiscovery`: vector search against los_mex ChromaDB → LLM grades 0-3; `AnchorEntry`/`AnchorCandidate` Pydantic models; `filter_anchors()`, `registry_to_dataframe()`, `summarise_registry()`; JSON save/load |
| `tests/unit/test_wvs_integration.py` | Extended to 135 tests (27 new Phase 3 tests, all with mock LLM) |

**Anchor grading scale:** 3=near-identical (direct validation), 2=same concept different wording (thematic), 1=weak overlap, 0=unrelated.

**To run anchor discovery** (requires los_mex ChromaDB + OpenAI API key):
```python
from wvs_anchor_discovery import WVSAnchorDiscovery
from wvs_metadata import load_equivalences
disc = WVSAnchorDiscovery(db_f1=db_f1, llm=llm)
registry = disc.build_registry(load_equivalences(), wave=7, n_candidates=5)
disc.save(registry, Path('data/wvs/anchor_registry.json'))
```

> WVS CSV/zip files are present on local Mac (`data/wvs/`). Not in Codespace.

- **γ-surface concept**: γ(variable_pair, country, wave, SES_reference) — the bridge "travels" across contexts
- **Anchor questions**: Shared questions between WVS and los_mex for bridge validation
- **SES harmonization**: WVS Q260/Q262/Q275/G_TOWNSIZE → los_mex sexo/edad/escol/Tam_loc
- **Mexico in all 7 WVS waves**: 11,714 total respondents (1,741 in Wave 7, fielded 2018)

#### WVS γ-Surface Pipeline ✅ COMPLETE (2026-03-23)

Julia-powered γ-surface across 66 countries and 7 Mexico waves. All computations in Julia 8-thread; Python handles data prep, analysis, and visualization.

**Infrastructure (Phase 0):**

| Module | Purpose |
|--------|---------|
| `scripts/debug/build_wvs_constructs_multi.py` | Multi-context construct builder (any wave×country) |
| `scripts/debug/export_wvs_for_julia.py` | CSV exporter for Julia (one CSV per context, absolute paths) |
| `julia/src/wvs_sweep.jl` | Julia WVS within-survey sweep module |
| `julia/scripts/run_wvs_geographic_fast.jl` | Flat-parallel geographic sweep (all pairs across all countries in one thread pool) |
| `julia/scripts/run_wvs_temporal.jl` | Temporal sweep (Mexico, 7 waves) |

**Sweep Results:**

| Sweep | Contexts | Estimates | Sig% | Med|γ| | Runtime |
|-------|----------|-----------|------|--------|---------|
| MEX W7 within-survey | 1 | 982 | 40.2% | 0.008 | 10 min |
| Geographic (W7, 66 countries) | 66 | 68,174 | 39.3% | 0.012 | 9.7 hr |
| Temporal (MEX, W3-W7) | 5 | 2,334 | 41.5% | 0.013 | 42 min |

**Key findings:**
- SES stratification varies by cultural zone: Catholic/English-speaking (med|γ|=0.026) >> African-Islamic (0.010)
- Mexico PC1=70% (WVS) / 78% (los_mex) — above global median of 61% but not extreme
- Most collinear: Mongolia (90%), Singapore (85%), Taiwan (84%)
- Most multi-dimensional: Jordan (38%), Turkey (46%), India (47%)
- Top 3 cross-country variance dimensions: Age/Cohort > Education > Urbanization (Gender has least variance)
- Temporal structural stability: Spearman ρ = 0.63–0.75 between adjacent Mexico waves (1996–2018)
- Within-survey CIs 29% tighter than cross-survey (0.022 vs 0.031)

**Analysis & Visualization:**

| File | Contents |
|------|----------|
| `scripts/debug/analyze_wvs_mex_validation.py` | Phase 1.4: MEX within vs cross validation |
| `scripts/debug/analyze_wvs_geographic.py` | Geographic analysis by country and cultural zone |
| `scripts/debug/analyze_wvs_temporal.py` | Temporal trends, structural stability |
| `scripts/debug/build_gamma_surface.py` | Unified γ-surface (72,756 entries from 4 sources) |
| `scripts/debug/visualize_gamma_surface.py` | PCA, heatmaps, ribbon plots, Mexico trajectory |
| `scripts/debug/plot_ses_signatures.py` | Per-country SES signatures (scatter, radar, bars) |
| `scripts/debug/plot_ses_signature_3d.py` | Interactive 3D Plotly scatter of SES signatures |
| `scripts/debug/build_wvs_losmex_construct_map.py` | WVS↔los_mex construct cross-map |

**Output files (large JSON data in `navegador_data` repo, reports/code in main repo):**

| File | Contents | Repo |
|------|----------|------|
| `data/results/wvs_mex_w7_within_sweep.json` | MEX W7 within-survey (982 est, 13K lines) | navegador_data |
| `data/results/wvs_geographic_sweep_w7.json` | 66-country geographic (68K est, 900K lines) | navegador_data |
| `data/results/wvs_temporal_sweep_mex.json` | Mexico temporal W3-W7 (2.3K est, 31K lines) | navegador_data |
| `data/results/gamma_surface.json` | Unified γ-surface (72.7K entries, 1M lines) | navegador_data |
| `data/results/ses_signatures_all.json` | Per-country 4D SES signatures (67 countries) | navegador_data |
| `data/results/ses_signature_3d.html` | Interactive 3D Plotly signature scatter | navegador_data |
| `data/results/wvs_geo_construct_manifest.json` | Per-country construct metadata (66 contexts) | navegador_data |
| `data/results/wvs_temporal_construct_manifest.json` | Per-wave construct metadata (7 waves) | navegador_data |
| `data/results/wvs_losmex_construct_map.json` | WVS↔los_mex construct cross-map (v1 Jaccard) | navegador_data |
| `data/results/wvs_losmex_construct_map_v2.json` | WVS↔los_mex construct cross-map (v2 LLM) | main |
| `data/results/wvs_ses_fingerprints.json` | WVS W7 MEX per-construct SES fingerprints | main |
| `data/results/wvs_geographic_report.md` | Geographic analysis report | main |
| `data/results/wvs_temporal_report.md` | Temporal analysis report | main |
| `data/results/wvs_mex_validation_report.md` | MEX validation report | main |
| `data/results/wvs_mex_validation_report_v2.md` | MEX validation report v2 (LLM-matched) | main |
| `data/julia_bridge_wvs/wvs_manifest.json` | Julia CSV manifest (absolute paths, 66+7 contexts) | navegador_data |
| `data/julia_bridge_wvs/WVS_W7_*.csv` | Per-country construct CSVs for Julia | navegador_data |

#### WVS ↔ los_mex Construct Matching & Cross-Study Validation (2026-03-24)

**LLM-based construct matching (v2)** replaces v1 Jaccard/TF-IDF heuristic:

| Module | Purpose |
|--------|---------|
| `scripts/debug/build_wvs_losmex_construct_map_v2.py` | Claude Sonnet 4 semantic grading (0-3 scale) of 56 WVS × 93 los_mex constructs |
| `scripts/debug/analyze_wvs_mex_validation_v2.py` | Cross-dataset validation with polarity correction (needs WVS sweep JSON) |

**Matching results:** 48 grade-3 (near-identical), 77 grade-2 (same concept), 10 reversed-polarity pairs detected. 46/56 WVS constructs (82%) have grade-3 matches. Cache: `data/results/.construct_map_v2_cache/`.

**WVS SES fingerprints** computed from `julia_bridge_wvs/WVS_W7_MEX.csv` (Spearman ρ per construct × 4 SES dims). Saved to `data/results/wvs_ses_fingerprints.json`.

**Cross-study fingerprint comparison (grade-3 pairs):**
- Median cosine similarity: **0.195** (low)
- Dominant dimension agreement: **13%** (6/46)
- 41% of pairs have **negative cosine** (opposite SES profile despite same concept)

**Cross-study driver comparison (significant pairs):**

| Dimension | WVS driver % | los_mex driver % | Delta |
|-----------|-------------|-----------------|-------|
| escol | 59.7% | 65.9% | -6 |
| Tam_loc | 7.6% | 23.0% | **-15** |
| sexo | 0.5% | 4.9% | -4 |
| edad | **32.2%** | 6.3% | **+26** |

**Key finding:** Age is 5× more important in WVS; urbanization is 3× more important in los_mex. Education is stable (~50-65%). Root causes: different age binning (WVS continuous→7 vs los_mex pre-binned), different urbanization classifications (WVS G_TOWNSIZE vs Mexican Tam_loc), and sampling differences (WVS omnibus vs los_mex domain-specific). **SES fingerprints are survey-specific, not construct-specific.**

**Validation sign agreement** (~50%) is a noise-floor artifact: median |γ| = 0.008, CI width = 0.022 → SNR < 1. Among high-magnitude pairs (both constructs SES mag ≥ 0.05), fingerprint dot product predicts γ sign at **98.7% accuracy** (sig pairs). At mag ≥ 0.10: **100%** (12/12).

**navegador_data repo:** `https://github.com/salvadorVMA/navegador_data` — large JSON sweep files, Julia CSVs, construct manifests. Los_mex bridge CSVs also pushed here (`data/julia_bridge/`).

**Colab notebook** (`notebooks/colab_jax_gamma_surface.ipynb`): Auto-clones both repos (navegador + navegador_data), no manual file upload. `DATASET = "los_mex" | "wvs"` toggle.

#### SES Realignment ✅ COMPLETE (2026-03-26)

Cross-study fingerprint comparison revealed WVS and los_mex SES fingerprints were nearly orthogonal (median cosine 0.195) due to 3 coding mismatches. All fixed:

| Fix | File | Change |
|-----|------|--------|
| **Tam_loc reversed** | `ses_analysis.py` | `5 - s` → 1=rural, 4=urban (matching WVS) |
| **Escol boundaries** | `wvs_metadata.py` | ISCED 0→1, 1→2 (Primary separate from Ninguna) |
| **Continuous edad** | `ses_analysis.py`, `ses_regression.py`, `wvs_loader.py`, `julia/src/ses_encoder.jl` | Raw numeric age passed to ordered logit (no 7-bin discretization) |

Julia `ses_encoder.jl`: 3-pass edad encoding — Pass 1: string bins (legacy), Pass 2: continuous (>20 unique values, pass-through), Pass 3: pre-binned (≤20 unique, bin to 7 ranks).

**Prefect pipeline** (`scripts/pipeline/ses_realignment_pipeline.py`): Fully annotated orchestration for all sweeps. Subprocess-based (each task calls existing scripts). Real-time stdout streaming via `Popen` + line-by-line reading.

```bash
# CLI flags (nothing runs by default):
--los-mex          # los_mex path (~40 min)
--wvs-geographic   # WVS 66 countries, W7 (~11-14h)
--wvs-temporal     # WVS Mexico 7 waves (~42 min)
--all              # everything
--fresh            # archive old sweep JSONs before starting (forces full recompute)
--dry-run          # print task graph, no execution
```

Scope-specific build: `build_wvs_constructs_multi.py --scope geographic|temporal` → separate cache/manifest files, no overwrites.

#### Post-Realignment Results (2026-03-26)

**Los_Mex (post-realignment):**

| Metric | Pre | Post |
|--------|-----|------|
| Significant edges | 984 | 879 |
| Med \|γ\| (sig) | 0.024 | 0.030 |
| Structural balance | 94% | **100%** |
| SES dominance: Education | — | 73.2% |
| SES dominance: Urbanization | — | 21.2% |
| SES dominance: Age | — | 2.4% |
| SES dominance: Gender | — | 3.3% |

**WVS Geographic (post-realignment):**

| Metric | Value |
|--------|-------|
| Estimates | 68,174 |
| Significant | 26,870 (39.4%) |
| Aggregate sig (>50% countries) | 206 edges |
| Structural balance (aggregate) | 94.7% |
| SES dominance: Education | 57.8% |
| SES dominance: Age | 33.5% |
| Sign consensus: 22% contested | 326 cross-zone sign flips |

**Key difference los_mex vs WVS**: Age/cohort is 2.4% of bridges in Mexico but **33.5%** globally — cross-national generational value shifts are much larger than within-Mexico variation.

**Country distance from average** (Spearman ρ with global median γ-vector):
- Top 5: ROU (0.732), TWN (0.718), GRC (0.692), NIR (0.687), **MEX (0.669, rank 5)**
- Bottom 5: THA (0.157), KAZ (0.155), UZB (0.141), MNG (0.128), PAK (0.089)
- Mexico has lowest RMSE (0.011) — closest magnitudes to global median

**Cross-zone sign flips**: South/Southeast Asia flips against global consensus on multiple pairs (work ethic, societal change, online participation). English-speaking uniquely decouples family obligation from moral permissiveness.

**Analysis scripts:**

| Script | Purpose |
|--------|---------|
| `scripts/debug/analyze_post_realignment.py` | Los_mex descriptives, circle networks, bipartite, SES dominance |
| `scripts/debug/analyze_wvs_post_realignment.py` | WVS descriptives, aggregate network, regional patterns |
| `scripts/debug/analyze_wvs_country_comparison.py` | Country distance from average, multi-country circle plots |

**Output files:**

| File | Contents |
|------|----------|
| `data/results/domain_circle_network_post_realignment.png` | Los_mex sign-colored network |
| `data/results/domain_circle_network_ses_colored.png` | Los_mex SES-colored network |
| `data/results/wvs_domain_circle_network_post_realignment.png` | WVS aggregate sign-colored network |
| `data/results/wvs_domain_circle_network_ses_colored.png` | WVS aggregate SES-colored network |
| `data/results/wvs_country_distance_from_average.png` | Country ranking bar chart |
| `data/results/wvs_multicountry_circle_plots.png` | Small multiples (closest + MEX + distant) |
| `data/results/post_realignment_report.md` | Los_mex report |
| `data/results/wvs_post_realignment_report.md` | WVS report |
| `data/results/wvs_country_comparison_report.md` | Country comparison report |

**JAX GPU Bridge (`jax_dr_bridge.py`):**
- Manual Cholesky solver bypasses Metal's missing `triangular_solve` XLA op
- Works on Apple Metal GPU for single pairs and point-estimate batches (100× faster)
- Metal crashes on double-vmap (pairs × bootstrap) due to buffer allocator limits
- Colab notebook ready for CUDA/TPU: `notebooks/colab_jax_gamma_surface.ipynb`
- TPU v5e (free Colab tier) has native `triangular_solve` and would complete full 3D surface in ~5-15 min

### Key Modules Added / Significantly Changed

| Module | Status | Purpose |
|--------|--------|---------|
| `analytical_essay.py` | Active | Two-step LLM pipeline: reasoning outline → analytical essay. Entry point: `generate_analytical_essay()` |
| `quantitative_engine.py` | Active | Pure-computation report builder. Handles sentinel/NaN filtering, label resolution for cross-tab profiles and bivariate leaders, SES bridge cross-dataset estimation |
| `ses_regression.py` | Active | All 6 bridge estimators (see table below). `OrderedModel`/`MNLogit` backbone. SES vars: `['sexo', 'edad', 'escol', 'Tam_loc']` |
| `ses_analysis.py` | Active | SES preprocessing: create region/edad/empleo from raw vars, normalise escol/Tam_loc/est_civil |
| `survey_kg.py` | Active | Knowledge graph ontology for survey domains (merged from worktree-knowledge-graph) |
| `tool_enhanced_analysis.py` | Updated | Migrated from deprecated `AgentExecutor` to `langgraph.prebuilt.create_react_agent` |

### Bridge Estimators in ses_regression.py (all 6 active)

| Class | `method` key | Primary output | Notes |
|-------|-------------|----------------|-------|
| `CrossDatasetBivariateEstimator` | `ses_simulation` | `cramers_v`, `p_value`, `column_profiles` | Baseline SES simulation |
| `ResidualBridgeEstimator` | `ses_residual_bridge` | `cramers_v_residual`, `ses_fraction` | Within-cell Mantel-Haenszel |
| `EcologicalBridgeEstimator` | `ecological_bridge` | `spearman_rho`, `ci_95` | Geographic cell Spearman ρ |
| `BayesianBridgeEstimator` | `bayesian_bridge` | `gamma`, `gamma_ci_95`, `cramers_v_ci_95` | Laplace posterior, no PyMC |
| `MRPBridgeEstimator` | `mrp_bridge` | `gamma`, `gamma_ci_95`, `n_cells_used` | James-Stein shrinkage cells |
| `DoublyRobustBridgeEstimator` | `doubly_robust_bridge` | `gamma`, `gamma_ci_95`, `normalized_mi`, `propensity_overlap` | AIPW + propensity weights |

Module-level helpers:
- `goodman_kruskal_gamma(joint_table)` — ordinal γ ∈ [-1,1], detects monotonic association only
- `normalized_mutual_information(joint_table)` — NMI ∈ [0,1], detects any dependence (monotonic, U-shaped, complex). Pairs with |γ| ≈ 0 but NMI >> 0 indicate non-monotonic SES structuring.

SES label maps (verified from survey metadata):
- `_REGION_LABEL_MAP`: `{1:'Centro', 2:'CDMX_Edo', 3:'Norte', 4:'Sur'}`
- `_EMPLEO_LABEL_MAP`: `{1:'Empleado', 2:'Desempleado', 3:'Estudiante', 4:'Hogar', 5:'Jubilado'}`
- `_EST_CIVIL_LABEL_MAP`: `{1:'CasadoUL', 2:'SepDivVdo', 3:'UnionLibre', 4:'Separado', 5:'Divorciado', 6:'Soltero', 7:'Otro'}`

### Test Suites

| File | Tests | Coverage |
|------|-------|---------|
| `tests/unit/test_ses_regression.py` | 76 | `SESEncoder`, `SurveyVarModel`, `CrossDatasetBivariateEstimator`, `ResidualBridgeEstimator`, `EcologicalBridgeEstimator` |
| `tests/unit/test_bridge_estimators_v2.py` | 36 | `goodman_kruskal_gamma`, `BayesianBridgeEstimator`, `MRPBridgeEstimator`, `DoublyRobustBridgeEstimator`, 6-way comparison |
| `tests/unit/test_bridge_evaluation.py` | 38 | Evaluation: predictive accuracy, AIC/BIC, variable selection, gamma recovery, CI calibration, cross-survey robustness |

Run all unit tests (150 total, ~38s):
```bash
python -m pytest tests/unit/test_ses_regression.py tests/unit/test_bridge_estimators_v2.py tests/unit/test_bridge_evaluation.py -v
```

### Recent Work (as of 2026-03-07)

- **DR estimator v3 optimization**: Systematic optimization of `DoublyRobustBridgeEstimator` for tighter bootstrap CIs.
  - **SES variable pruning**: `SES_REGRESSION_VARS` reduced from 10 → 4 vars: `['sexo', 'edad', 'escol', 'Tam_loc']`. Dropped `empleo` (9-20% coverage), `income_quintile` (30-40%), `est_civil`, `empleo_formality`, `region_x_Tam_loc`. Replaced `region` (3 one-hot dummies, causes sparsity) with `Tam_loc` (single ordinal, missing in only 2/26 surveys). Row retention: 4.8% → 99.2%.
  - **Tam_loc vs region**: Empirically tested — Tam_loc produces 28% tighter CIs (median 0.234 vs 0.324) with same row retention and faster runtime.
  - **n_sim increased**: 500 → 2000. Monte Carlo noise now negligible (∝ 1/√n_sim).
  - **maxiter cap**: `SurveyVarModel.fit()` accepts `maxiter` parameter. Bootstrap fits capped at `maxiter=100` to prevent BFGS hangs on ill-conditioned resamples.
  - **Per-pair timeout**: `sweep_dr_highci.py` uses `signal.alarm()` / `SIGALRM` with 120s timeout per pair. Prevents hung BFGS from blocking the sweep.
- **Uncertainty walls identified**: Three noise sources in DR bootstrap CIs:
  1. **Monte Carlo** (n_sim): ∝ 1/√n_sim, negligible at n_sim=2000
  2. **Bootstrap resampling** (n_bootstrap): stabilizes CI endpoints, diminishing returns beyond ~200
  3. **Sampling noise** (n ≈ 1200 per survey): irreducible floor at ~0.2-0.3 CI width. This is the dominant wall.
- **Causal interpretation**: γ measures "how much shared sociodemographic position drives monotonic co-variation between attitudes across survey domains." The 4 SES dimensions — escol (education), Tam_loc (location/urban-rural), sexo (gender), edad (age/cohort) — are treated with equal standing; none is a "demographic control" subordinate to the others. Under CIA (conditional independence given SES), γ captures only SES-mediated association. Pairs with γ ≈ 0 indicate SES-independent or orthogonally-SES-driven attitudes.
- **γ detects monotonic relationships only**: Goodman-Kruskal γ = (C−D)/(C+D) based on concordant/discordant pairs. Cannot detect U-shaped or other non-monotonic SES-attitude relationships.
- **Normalized MI added**: `normalized_mutual_information(joint_table)` computes NMI ∈ [0,1] from the same joint table γ uses — zero additional model fitting. Detects any statistical dependence regardless of shape. Pairs with |γ| ≈ 0 but NMI >> 0 reveal non-monotonic SES structuring (U-shaped, crossover patterns). Sweep log flags these with `NM!`.

### Construct-Level Analysis Pipeline (as of 2026-03-10)

- **Semantic Variable Selection v4**: LLM-assisted 3-step pipeline (construct clusters → research review → variable strategy) for all 24 domains. Outputs `semantic_variable_selection_v4.json` with construct clusters, reverse-coded items, formative indices, gateway items.
- **Construct Variable Builder** (`scripts/debug/build_construct_variables.py`): Reads v4 SVS and creates `agg_{construct_name}` columns in each survey DataFrame, scaled to [1,10]. Handles: reflective scales (mean of items with reverse coding), tier 2 constructs (single best item by item-total correlation), formative indices (additive count of gateway items). Sentinel filtering before aggregation.
- **102 constructs built** across 24 domains: 16 good (α≥0.7), 49 questionable (α 0.5-0.7), 20 tier3_caveat (α<0.5), 12 single_item_tier2, 5 formative_index.
- **Construct Validation** (`scripts/debug/validate_constructs.py`, `optimize_constructs.py`): Structural audit, alpha fixes, optimization log.

### SES Fingerprint & Ontology Pipeline (as of 2026-03-17, extended 2026-03-18)

#### SES Foundation

All bridge estimates are conditioned on 4 sociodemographic (SES) dimensions:

| Variable | Dimension |
|----------|-----------|
| `escol` | Education level |
| `Tam_loc` | Town size / urban-rural axis |
| `sexo` | Gender |
| `edad` | Age / cohort |

All four are SES dimensions with equal standing. Gender and age/cohort structure attitudes, access, and life trajectories in ways inseparable from class in Mexican society. The DR bridge conditions on all 4 simultaneously; γ(A,B) measures covariation mediated by the full sociodemographic position, not education alone.

**Bridge CIA limitation**: γ captures ONLY SES-mediated covariation. It cannot detect: direct A→B links independent of SES, confounders outside the 4-var set, reverse causation, or non-monotonic SES patterns (use NMI for the last).

#### Level Hierarchy (bottom-up)

| Level | Unit | Count | Notes |
|-------|------|-------|-------|
| L0 | Questions (raw survey items) | 6 359 | Use with caution — check `reverse_coded` flag |
| L1 | Constructs (agg_* aggregates) | 93 | Authoritative; signed in conceptual direction |
| L2 | Domains | 24 | Coarse fallback only; averaging cancels within-domain opposing signals |

Lookup priority: **L1 construct → L0 item (rc-checked) → L2 domain (fallback)**

#### SES Fingerprint

Each L1 construct carries a 4D fingerprint vector `[rho_escol, rho_Tam_loc, rho_sexo, rho_edad]`:
- `ses_magnitude` = RMS of the 4 ρ values (overall SES stratification intensity)
- `dominant_dim` = SES dimension with highest |ρ| (may be any of the 4)
- **Bridge sign prediction**: `dot(fingerprint_A, fingerprint_B)` predicts sign of γ(A,B) at **99.4% accuracy** across 984 significant bridges. Two constructs whose SES profiles point in the same 4D direction are co-elevated by the same sociodemographic position → γ > 0.

Distribution of `dominant_dim` across 93 constructs: escol=37, Tam_loc=23, edad=22, sexo=11. More than half are primarily structured by age, location, or gender rather than education — treating those as secondary would misrepresent the SES geometry.

#### Prediction Chain (item → construct → bridge → construct → item)

```
signal = loading_gamma_A × γ(A→B) × loading_gamma_B
```

- `loading_gamma` = γ(raw_item, bin5(agg_construct)): signed, same estimand as Julia DR bridge
- All terms are γ-scale → dimensionally consistent
- Sign travels through the chain: negative loading_gamma = reverse-coded item
- Double negatives cancel correctly (both items RC → positive prediction)
- Bridge γ is the dominant bottleneck; item loadings are typically 0.5–0.99

#### Orphan Item Loading (approximate, 2026-03-18)

5,877 of 6,359 L0 items have no parent construct. For these orphans, `compute_ses_fingerprints.py` now computes:
- `candidate_construct`: L1 construct in same domain with highest fingerprint cosine similarity
- `candidate_loading`: Spearman ρ(item, agg_candidate) from actual survey data
- `candidate_loading_gamma`: `clip(ρ × 1.14, -1, 1)` — approximate γ via empirical scaling factor
- `loading_type`: `"exact"` | `"approximate"` | `"none"` (JUE/CON have no constructs)

**ρ→γ scaling factor (1.14):** Derived from 474 construct-member items with both measurements.
Pearson r(ρ,γ)=0.9765, sign agreement=99.8%, median |γ|/|ρ|=1.14. GK γ exceeds Spearman ρ
because γ excludes tied pairs from its denominator while ρ averages tied ranks — for 5-point
Likert items with ~30–50% ties, this produces ~14% systematic inflation.

Coverage: 482 exact + 5,307 approximate + 570 none (JUE=331, CON=239).

Run: `python scripts/debug/compute_ses_fingerprints.py --enrich-only`

#### OntologyQuery — Network Traversal API (2026-03-18)

`opinion_ontology.OntologyQuery` now supports item-level input and graph traversal:

**`_lift_to_construct(key)`** — resolves any L0/L1/L2 key to an L1 anchor construct:
- exact: item with parent_construct, or L1 construct itself
- approximate: orphan item with candidate_construct (uses candidate_loading_gamma)
- domain_fallback: item/domain with no construct (no bridge queries possible)
- none: unresolvable

**Use-case 1 — `get_neighborhood(key, min_abs_gamma, top_n)`**
Lifts item → anchor construct → `get_neighbors`. Returns neighbors list + summary
(domain distribution, positive/negative γ counts, dominant shared dim, strongest edge)
+ narrative. Flags lift type and loading_gamma in output.

**Use-case 2 — `find_path(key_a, key_b)`**
Dijkstra on bridge adjacency with weight = `-log(|γ|)`, equivalent to maximising the
product of |γ| values along the path (strongest SES-mediated chain).
Returns: path, edges (γ/CI per hop), signal_chain (∏|γᵢ|), total_cost (Σ-log|γᵢ|),
direct_edge (if exists), attenuation_warning (signal_chain < 0.001), narrative.
Both endpoints are lifted via `_lift_to_construct`; lift metadata included in output.

**Integration note:** Current analysis pipelines do not yet call OntologyQuery.
Integration point: after `variable_selector.py` returns `(col_name, survey_name)`,
construct `item_key = f"{col}|{enc_nom_dict[survey_name]}"` then call `_lift_to_construct`.

#### Scale Direction Audit & RC Fix (2026-03-18)

Systematic audit of all 93 constructs detected **37 with scale inversion** (value 1 = positive label, e.g. "Mucho", "Muy de acuerdo", "Siempre", "Muy buena" but item was not reverse-coded). Without RC, higher construct score = LESS of the implied concept.

**Fix pipeline:**
1. `scripts/debug/audit_scale_direction.py` — detects scale-inverted items by checking `variable_value_labels["1.0"]` against positive-intensity keyword patterns; writes `data/results/scale_audit_v1.json`; `--apply` flag writes proposed overrides to `construct_v5_overrides.json`
2. `scripts/debug/build_construct_variables.py` — rebuilds all `agg_*` columns with corrected RC
3. `scripts/debug/compute_ses_fingerprints.py` (full recompute) — recomputes all ρ values and fingerprint vectors
4. `scripts/debug/patch_kg_ontology_bridges.py` — recomputes `fingerprint_cos` and flips bridge γ signs where `sign(cos_new) ≠ sign(γ_old)` (caused by RC'ing exactly one side of the pair); 265/984 edges flipped

**65 new RC items** added across 37 constructs. All construct fingerprints, bridge γ signs, and `fingerprint_cos` values are now correct.

**Detection keywords** (value 1 label containing): mucho/mucha, bastante, muy de acuerdo, totalmente de acuerdo, siempre, excelente, muy buena/bueno, muy satisfecho, muy confiado, mucha confianza, totalmente de acuerdo/cierto/correcto/seguro, de acuerdo, se justifica mucho.

#### Output Files

| File | Contents |
|------|----------|
| `data/results/ses_fingerprints.json` | L0/L1/L2 fingerprints; L0 items include `loading_gamma` (exact) or `candidate_loading_gamma` (approximate) and `loading_type` |
| `data/results/kg_ontology_v2.json` | 93 L1 constructs enriched with fingerprints + 984 bridge edges (γ signs corrected 2026-03-18) |
| `data/results/kg_ontology.json` | Original v1 (stale; 176 old constructs) — do not use |
| `data/results/scale_audit_v1.json` | Per-item scale direction audit; proposed RC overrides |
| `data/results/network_topology_report.md` | Full topology & geometry report (867 lines) — global metrics, PCA, balance, community |

#### Network Topology & Geometry (2026-03-18)

Full analysis in `data/results/network_topology_report.md` (generated by `scripts/debug/analyze_network_topology.py` + `scripts/debug/analyze_item_network.py`).

**Global metrics** (giant component, 71 nodes, 984 edges):

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Density | 23.0% | Pervasive SES connectivity (typical networks <5%) |
| Diameter | 4 | Max 4 SES-mediated hops between any two constructs |
| APL | 1.728 | < 2 hops on average — ultra-compact |
| Avg clustering | 0.531 | 2.3× random expectation (0.230) — geometric transitivity |
| Transitivity | 0.720 | |
| Isolated nodes | 22 | SES-magnitude too small to clear significance threshold |
| Sign split | 52% pos / 48% neg | Co-elevation and counter-variation in near-equal measure |
| Structural balance | 94% | 94% of triangles are sign-consistent; clean two-camp bipartition |
| Modularity Q | 0.089 | No community structure — continuous gradient, not modular |
| σ (small-world) | 0.991 | Not small-world — geometric graph, not sparse random graph |

**PCA of 4D fingerprint space:**
- PC1 = **78% of variance** — education-vs-tradition axis (escol + Tam_loc on one end; sexo + edad on the other)
- PC2 = **12% of variance** — age-vs-urbanization axis
- Effective dimensionality ≈ 1.5D; the 4D space is nearly collinear

**Fingerprint dot product → bridge γ:**
- `dot(fingerprint_A, fingerprint_B)` predicts γ **sign** at 99.4% accuracy
- `dot` predicts γ **magnitude** at r = 0.685 (47% variance explained)
- 53% unexplained: education × gender interactions, bootstrap noise, non-linear SES effects

**Network archetype:** Signed thresholded inner-product graph in R⁴. Not scale-free, not small-world, not modular. Structure is a projection of SES geometry onto a discrete edge set (significance test as threshold). The bipartition of the 94%-balanced sign structure corresponds exactly to the two halves of the PC1 axis (cosmopolitan–education camp vs. tradition–locality camp).

**Item-level signal chains** (from `analyze_item_network.py`):
- 3.9M item→item paths evaluated; 2.4% reach |signal| ≥ 0.01
- Prediction chain: `signal = loading_γ_A × γ_bridge × loading_γ_B`; `loading_γ` = γ(raw item, bin5(agg_construct))
- ρ → γ scaling factor: **1.14** (empirically derived from 474 construct-member items)

### Sweep Scripts

| Script | Purpose |
|--------|---------|
| `scripts/debug/sweep_cross_domain.py` | Original 276-pair baseline sweep |
| `scripts/debug/sweep_bridge_comparison.py` | All 6 methods on 276 pairs |
| `scripts/debug/sweep_dr_highci.py` | v3 DR re-sweep with high bootstrap CIs, per-pair timeout, atomic checkpointing |
| `scripts/debug/sweep_construct_dr.py` | **Construct-level DR sweep**: 4979 cross-domain construct pairs, atomic checkpointing, resume-friendly |
| `scripts/debug/test_dr_diagnostic.py` | Per-step SIGALRM diagnostic for DR hang isolation |

### Sweep Results

| Version | Level | SES vars | n_sim | n_bootstrap | Median CI_w | % excl zero | Notes |
|---------|-------|----------|-------|-------------|-------------|-------------|-------|
| v1 | variable | 7 vars | 500 | 10 | ~0.5 | — | Baseline |
| v2 | variable | 10 vars | 500 | 200 | 1.351 | 0% | Row retention crisis (4.8%) |
| v3 | variable | 4 vars (sexo,edad,escol,Tam_loc) | 2000 | 200 | 0.121 | 2.5% (38/1531) | Optimal config, NMI added |
| v4 | **construct** | 4 vars (sexo,edad,escol,Tam_loc) | 2000 | 200 | 0.024 | 7.2% (360/4979) | Construct-level aggregation |

### V3 Sweep Findings (2026-03-08, variable-level)

- **1531 pairs completed** in 6.6h, 100% success rate
- **Median CI width 0.121** — 91% narrower than v2 (1.351). Mean 0.167, P10=0.048, P90=0.348.
- **38 pairs (2.5%) have CIs excluding zero** — definitive SES-mediated monotonic co-variation.
- **Most γ ≈ 0** (median |γ| = 0.015): most cross-domain attitude pairs are NOT monotonically co-driven by SES. This is itself a substantive finding.
- **NMI universally low** (max 0.037, median 0.0003): no hidden non-monotonic SES patterns. Where SES creates dependence, it's monotonic. Only 1 pair flagged as non-monotonic (|γ| < 0.05 but NMI > 0.02).
- **Top pair**: digital/cultural capital (EDU) × media consumption (γ = +0.576) — higher SES pushes both up.
- **Conclusion**: The SES bridge is well-calibrated. It detects signal where it genuinely exists, and the signal is overwhelmingly monotonic. The estimator is optimal given n ≈ 1200 sampling constraints.

### V4 Construct Sweep Findings (2026-03-10, construct-level)

- **4979 pairs completed** in 11.1h, 0 errors (100% success rate).
- **Median CI width 0.024** — 5x narrower than v3 variable-level (0.121). Construct aggregation dramatically reduces noise.
- **360 pairs (7.2%) have CIs excluding zero** — 3x more discoveries than variable-level sweep.
- **Median |γ| = 0.004**, mean |γ| = 0.008, max |γ| = 0.133.
- **Top hubs**: HAB (housing quality/services) and REL (religiosity) are the most SES-stratified domains.
- **Top pair**: HAB|structural_housing_quality × REL|personal_religiosity (γ=+0.133) — higher SES → better housing AND more religious.
- **Sign patterns**: HAB × REL positive (housing+religiosity co-vary), HAB × SEG negative (better housing → less crime exposure), ECO × REL negative (employment precarity → less religiosity).
- **Network visualization**: 60 constructs with significant links, 140 strongly significant + 220 significant + 125 near-significant edges. Saved as `data/results/construct_network.png`.

### Earlier Work (2026-02-26 to 2026-03-02)

- **6-method bridge suite**: Added `BayesianBridgeEstimator` (Laplace posterior), `MRPBridgeEstimator` (James-Stein shrinkage), `DoublyRobustBridgeEstimator` (AIPW) to `ses_regression.py`. No PyMC/sklearn — uses only scipy/statsmodels/numpy.
- **`goodman_kruskal_gamma()`**: Module-level helper for ordinal association γ ∈ [-1,1].
- **Bug fixes**: BFGS hangs, Bayesian `_draw_proba`, DR propensity cast, SESEncoder mixed-type sort, Ecological cardinality guard.
- **Worktree merge** (2026-02-26): `worktree-knowledge-graph` merged → `survey_kg.py`, expanded SES bridge.
- **Label resolution**: `_get_var_labels` + `_apply_labels_to_estimate` in `quantitative_engine.py`.
- **Sentinel filtering**: `_is_sentinel()` in `ses_regression.py`.

### Known Data Quality Rules

- **Sentinel codes** (`>= 97` or `< 0`): filtered by `_is_sentinel()` in `ses_regression.py`. Must be excluded from all marginal tables, bivariate models, and LLM-facing reports.
- **`est_civil` codes 8 and 9**: below sentinel threshold — explicitly remapped → NaN in `preprocess_survey_data()`.
- **`escol` codes 9, 98, 99**: remapped in `preprocess_survey_data()`; JUEGOS_DE_AZAR/CULTURA_CONSTITUCIONAL use 1/3/4/5/6 scale → remapped to 1–5.
- **`Tam_loc`**: clipped to 1–4; values outside range → NaN.
- **NaN indices** in `df_tables`: represent conditional/skip-pattern questions (not applicable to subgroups). Filter and renormalize before passing to LLM.
- **Label resolution** for cross-tab profiles uses `variable_value_labels` from `enc_dict[survey_name]['metadata']`. Verified to be present in the JSON data structure.
- **`ses_sign` on construct nodes** = sign(rho_escol) only — a single-axis summary. Use the full fingerprint vector (`[rho_escol, rho_Tam_loc, rho_sexo, rho_edad]` in `ses_fingerprints.json`) for SES direction analysis.

## TDA Pipeline (Topological Data Analysis) — 2026-03-27, extended 2026-04-01

Applies persistent homology, Ricci curvature, spectral graph theory, and Gromov-Wasserstein alignment to the WVS construct networks.

### Architecture

Python (ripser, persim, scikit-learn) handles TDA + visualization. Julia handles O(n³) bottlenecks (Floyd-Warshall, Sinkhorn OT, spectral eigendecomposition, GW alignment). Communication via CSV scratch files. All 5 Julia TDA scripts accept CLI args for manifest/output paths (backward-compatible defaults).

### Pipeline Scripts

**v1 (W7 geographic + Mexico temporal):**

| Script | Purpose |
|--------|---------|
| `scripts/pipeline/tda_pipeline.py` | Prefect orchestration (7 phases, `--all`, `--skip-ricci`, `--skip-gw`, `--dry-run`) |
| `scripts/pipeline/temporal_tda_pipeline.py` | Temporal pipeline: Mexico W3-W7 sweep + per-wave TDA |
| `scripts/debug/tda_convert_sweep_to_matrices.py` | Phase 0: sweep JSON → per-country 55×55 CSV weight/distance matrices |
| `scripts/debug/tda_persistent_homology.py` | Phase 4: ripser H0/H1/H2 + bottleneck distances (supports `TDA_*` env var overrides) |
| `scripts/debug/tda_embeddings_and_zones.py` | Phase 5: MDS + zone coherence permutation tests (supports `TDA_*` env var overrides) |
| `scripts/debug/tda_convert_temporal_matrices.py` | Temporal Phase 4: per-wave matrices from temporal sweep |
| `scripts/debug/tda_temporal_trajectory.py` | Temporal Phase 6: spectral trajectory + edge confidence |

**v2 All-wave (W3-W7, 100 countries, 37 temporal):**

| Script | Purpose |
|--------|---------|
| `scripts/pipeline/allwave_tda_pipeline.py` | Prefect orchestration: Mode A (per-wave geographic) + Mode B (per-country temporal) + Phase C (synthesis). Per-task dashboard labels. |
| `scripts/debug/tda_convert_allwave_to_matrices.py` | Phase 0: all-wave γ-surface JSON → per-wave geographic CSVs + per-country temporal CSVs |
| `scripts/debug/tda_allwave_analysis.py` | Phase C: Fiedler heatmaps, convergence/divergence, zone trends, mediator stability |
| `scripts/debug/tda_allwave_report.py` | 8-figure report generator (Fiedler panels, zone trends, convergence, β₁, mediators, spectral heatmaps, MDS trajectories) |

Julia scripts (in `../navegador_julia_bridge/julia/scripts/`):

| Script | Purpose | CLI args |
|--------|---------|----------|
| `tda_floyd_warshall.jl` | Phase 1: APSP + mediator scores | `[manifest] [output_dir]` |
| `tda_ricci_curvature.jl` | Phase 2: Ollivier-Ricci via Sinkhorn OT | `[manifest] [fw_dir] [output_dir]` |
| `tda_spectral_distances.jl` | Phase 3: pairwise Laplacian spectral distances | `[manifest] [output_dir]` |
| `tda_gromov_wasserstein.jl` | Phase 6: all-pair GW alignment | `[manifest] [fw_dir] [output_dir]` |
| `tda_temporal_spectral.jl` | Temporal: per-wave FW + spectral features | `[manifest] [output_dir]` |

`tda_spectral_distances.jl` adapts `MIN_SHARED = min(40, floor(0.7 × n_constructs))` from the manifest, supporting smaller construct sets in earlier waves.

### v1 Findings (WVS W7, 66 countries)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Ricci curvature κ | ≈ 1.0 everywhere | Geometrically flat, no bottleneck edges |
| β₁ (persistent loops) | 0.1 mean, max 2 (BGD) | Nearly tree-like, no robust loops |
| Spectral zone coherence | p=0.001, ratio=0.913 | Cultural zones cluster spectrally |
| Bottleneck zone coherence | p=0.672 | Topological features do NOT separate zones |
| GW self-match rate | 3.1% | Constructs occupy different positions across countries |
| Top mediator (MEX/BRA) | gender_role_traditionalism | Varies by country |
| Top mediator (USA/JPN) | science_skepticism | |

### v2 All-Wave Findings (W3-W7, 100 countries, 1996-2018)

**Algebraic connectivity (Fiedler value) is a near-constant:**

| Wave | Year | Countries | Mean Fiedler |
|------|------|-----------|-------------|
| W3 | 1996 | 38 | 0.723 |
| W4 | 2000 | 27 | 0.713 |
| W5 | 2007 | 43 | 0.724 |
| W6 | 2012 | 47 | 0.701 |
| W7 | 2018 | 66 | 0.710 |

**Convergence oscillates, does not trend:**

| Transition | Δ Spectral Distance | Direction |
|---|---|---|
| W3→W4 | -0.020 | converging |
| W4→W5 | +0.018 | diverging |
| W5→W6 | -0.069 | converging |
| W6→W7 | +0.006 | diverging |

**Persistent loops declining:** β₁ drops from 39% of countries with loops (W3) to 20% (W7). Networks becoming more tree-like.

**Gender role traditionalism is the universal structural bridge:** Top mediator in 20/37 countries (54%), persistent across waves. Science skepticism #2 (10/37, 27%).

**Zone coherence significant only at scale:** Spectral zone coherence significant in W3 (p=0.002) and W7 (p=0.001) but not W4-W6. Bottleneck distances never separate zones.

**Country trajectories (Fiedler):** Mexico peaks at W5 (0.82, 2007) then drops. Germany declines monotonically (0.82→0.70). Chile rises steadily (0.67→0.73). India stable (~0.72).

**Ricci curvature κ ≈ 0 everywhere**, confirmed across all 5 waves.

### All-Wave Pipeline CLI

```bash
# Full run (~6 min with Ricci, skip GW):
python scripts/pipeline/allwave_tda_pipeline.py --all --skip-gw

# Geographic only, specific waves:
python scripts/pipeline/allwave_tda_pipeline.py --geographic --waves 5 6 7 --skip-ricci

# Temporal only, specific countries:
python scripts/pipeline/allwave_tda_pipeline.py --temporal --countries MEX BRA IND

# Dry run:
python scripts/pipeline/allwave_tda_pipeline.py --all --dry-run
```

### TDA Output Files

All TDA outputs in `data/tda/` (gitignored, pushed to `navegador_data`):

**v1 outputs:**

| Directory | Key Files |
|-----------|-----------|
| `matrices/` | manifest.json, per-country weight/distance CSVs |
| `floyd_warshall/` | mediator_scores.json |
| `ricci/` | ricci_summary.json |
| `spectral/` | spectral_distance_matrix.csv, spectral_features.json |
| `persistence/` | topological_features.csv, bottleneck_distances.csv |
| `embeddings/` | zone_coherence.json, mds_*.png, combined_features.csv |
| `alignment/` | gw_distance_matrix.csv, gw_alignment_summary.json |
| `temporal/` | temporal_trajectory.json, edge_confidence.csv |

**v2 all-wave outputs:**

| Directory | Key Files |
|-----------|-----------|
| `allwave/matrices/W{3-7}/` | Per-wave manifest.json + per-country CSVs |
| `allwave/per_wave/W{3-7}/` | floyd_warshall/, ricci/, spectral/, persistence/, embeddings/ per wave |
| `allwave/temporal/{ALPHA3}/` | Per-country spectral_features.json, mediators_per_wave.json (37 countries) |
| `allwave/convergence/` | fiedler_heatmap.csv, convergence_metrics.json, zone_temporal_trends.csv, mediator_stability.json |

**Report:** `data/results/allwave_tda_report.md` + 8 figures in `data/results/allwave_tda_plots/` (gitignored PNGs, regenerate via `tda_allwave_report.py`).

### Python TDA Dependencies

```bash
pip install ripser persim pot
```

Julia packages added: `Graphs`, `Distances` (in julia bridge Project.toml).

## Quick Start

```bash
# Install dependencies
pip install -r config/requirements.txt

# Set environment variables (copy from .env.example)
cp .env.example .env

# Run CLI
python main.py

# Run dashboard
python dashboard.py
```

## Security

The project uses a layered security approach across the editor, CLI, CI, and GitHub platform. All tools are persisted in the devcontainer configuration so they survive Codespace rebuilds.

- **Editor**: SonarLint (real-time code quality and security), Pylint (Python linting)
- **CLI**: Bandit (Python SAST), Safety (dependency vulnerabilities), Semgrep (multi-language static analysis), Gitleaks (secret detection)
- **CI/CD**: GitHub Actions workflow runs Bandit, Gitleaks, Safety, and Codacy on every push/PR plus weekly schedule
- **GitHub Platform**: Dependabot (dependency updates for pip, npm, GitHub Actions), secret scanning (activates when repo goes public)
- **Secrets**: `.env` files are gitignored and never committed. API keys should be managed via Codespace secrets or `.env` files only.

For detailed documentation of each tool, see `docs/SECURITY_TOOLS.md`.

## Documentation

See `docs/` folder for detailed guides:
- `QUICK_START.md` - Getting started
- `CLAUDE1_COMPLETE_SUMMARY.md` - Recent improvements
- `META_PROMPTING_GUIDE.md` - Prompt optimization
- `SANDBOX_README.md` - Docker sandbox usage
- `SECURITY_TOOLS.md` - Security tools and scanning procedures
- `WVS_INTEGRATION_PLAN.md` - World Values Survey integration plan (branch `wvs`)


## Julia Bridge (branch: julia_bridge)

> **Architecture decision (2026-03-14):** Julia is the **primary numeric processing engine** for the DR bridge. All ordered-logit fitting, bootstrap CI estimation, and construct-level sweeps are performed in Julia. Python handles data I/O, LLM calls, visualization, and orchestration. Python's `DoublyRobustBridgeEstimator` remains as a reference implementation and for one-off estimates, but Julia's `run_sweep` is the canonical sweep engine.

### Location

```
../navegador_julia_bridge/julia/
```

The `julia_bridge` branch is a git worktree of this repository.
All Julia source files live in the `julia/` subdirectory of that worktree.

### Module Structure

| File | Purpose |
|------|---------|
| `src/NavegadorBridge.jl` | Main module (all exports) |
| `src/gamma_nmi.jl` | `goodman_kruskal_gamma`, `normalized_mutual_information` |
| `src/cronbach.jl` | `cronbach_alpha`, `scale_to_output`, `reverse_code`, `build_construct_scale` |
| `src/ordinal_model.jl` | `fit_ordered_logit`, `predict_proba`, `fit_logistic`, `predict_logistic` |
| `src/ses_encoder.jl` | `encode_ses`, `drop_sentinel_rows`, `is_sentinel`, `SES_VARS` |
| `src/dr_estimator.jl` | `dr_estimate`, `DRResult`, `_rank_normalize`, `_bin_to_5`, `_find_bin` |
| `src/sweep.jl` | `run_sweep`, `load_checkpoint`, `save_checkpoint` |
| `scripts/run_v5_sweep.jl` | **Current sweep script** — v4 (rank-norm + K<3 guard, 8 threads) |
| `test/runtests.jl` | 66 unit tests (all pass) |
| `examples/demo_dr.jl` | End-to-end demo: 1200 synthetic respondents, 50 bootstrap, ~5s |
| `docs/JULIA_BRIDGE_PRIMER.md` | Full technical primer (Python↔Julia side-by-side) |

### Key Functions

- **`dr_estimate(df_a, col_a, df_b, col_b; ses_vars, n_sim, n_bootstrap, seed)`**
  Main DR bridge estimator. Returns `DRResult` with γ, 95% CI, NMI, Cramér's V,
  and KS propensity overlap. Mirrors `DoublyRobustBridgeEstimator` from `ses_regression.py`.

- **`goodman_kruskal_gamma(joint_table)`** — Goodman-Kruskal γ ∈ [-1, 1]
- **`normalized_mutual_information(joint_table)`** — NMI ∈ [0, 1]
- **`cronbach_alpha(X)`** — Cronbach's α for item matrix
- **`_rank_normalize(v)`** — midrank transform → uniform [1,10] before qcut (v4)

### Binning Pipeline (v4, canonical)

1. **`_rank_normalize`**: Convert raw construct scores to fractional midranks scaled to [1,10].
   Tied observations get average of positional ranks. Guarantees uniform distribution regardless of skew.
2. **`_bin_to_5`**: Equal-frequency quantile cut (qcut) → 5 edges. Applied after rank normalization.
3. **`_find_bin`**: Return integer bin index 1..K via `searchsortedlast`. Fixed K=6 bug (prior versions
   returned edge Float64 values as category labels, producing spurious 6th category).
4. **K<3 guard**: Constructs collapsing to ≤2 categories raise an error → recorded as `skipped` in JSON.

### Julia Sweep Version History

| Version | Binning | Bug status | sig% | Notes |
|---------|---------|------------|------|-------|
| v1 | Raw values, float labels | K=6 bug | ~30%+ | Single-thread, wrong binning |
| v2 | qcut (equal-freq) | K=6 bug present | 24.8% | Newton+LBFGS, K<2 guard only |
| v3 | qcut, integer bin index | K=6 fixed | 18.9% | `searchsortedlast` fix |
| **v4** | **rank-norm → qcut** | **K<3 guard** | **25.4%** | Canonical; 266 degenerate pairs skipped |

**v4 sweep results** (completed 2026-03-14, `construct_dr_sweep_v5_julia_v4.json`):
- 3869 done + 266 skipped (K<3 or error) = 4135 total pairs
- **984/3869 (25.4%) CIs exclude zero**
- Median |γ| = 0.0063, mean |γ| = 0.013, max |γ| = 0.2886
- Network plot: `data/results/domain_circle_network_v5_julia_v4.png`

**Why Julia sig% > Python (25.4% vs 7.2%):**
- Julia |γ| point estimates are ~2× larger (med 0.0063 vs 0.0030)
- CIs only ~1.26× wider → SNR higher → nonlinear more threshold crossings
- Root cause: Newton solver reliably converges on bootstrap resamples where Python BFGS
  hits maxiter=100 cap → Julia has wider, more honest bootstrap distributions
- K=6 bug (v1/v2) added ~5-6% artificial significance; rank normalization is a calibration
  improvement but did not reduce significance rate (K=3 constructs just get skipped)
- Some gap may reflect genuine Python underestimation due to bootstrap underconvergence
- Top hubs in Julia (HAB, REL, CIE, FED) match Python top-4 exactly — core signal confirmed

### How to Run Sweep

```bash
export PATH="$HOME/.juliaup/bin:$PATH"
cd /path/to/navegador_julia_bridge/julia
julia -t 8 --project=. scripts/run_v5_sweep.jl
# Outputs: ../navegador/data/results/construct_dr_sweep_v5_julia_v4.json
# Expected: ~40-45 min (8 threads, 4135 pairs)
```

### How to Run Tests

```bash
export PATH="$HOME/.juliaup/bin:$PATH"
cd /path/to/navegador_julia_bridge/julia
julia --project=. test/runtests.jl
```

Expected: 66 tests pass in ~7 seconds.

### Performance

Realized speedup vs. Python+statsmodels (measured):

| Operation | Python | Julia |
|-----------|--------|-------|
| Single ordered logit fit (n=1200, K=5) | ~0.5s | ~0.01s |
| 200 bootstrap iterations | ~120s | ~4s |
| 4135-pair sweep (n_boot=200, 8 threads) | ~11h (est.) | **~40-45 min** |

### Output Format

```json
{
  "metadata": {"n_sim": 2000, "n_bootstrap": 200, "ses_vars": [...], ...},
  "estimates": {
    "agg_col_a|DOMAIN_A::agg_col_b|DOMAIN_B": {
      "dr_gamma": 0.1332, "dr_ci_lo": 0.0891, "dr_ci_hi": 0.1773,
      "dr_nmi": 0.0087, "dr_v": 0.0621, "ci_width": 0.0882,
      "excl_zero": true, "n_a": 1200, "n_b": 1200
    }
  },
  "skipped": {"agg_col|DOMAIN::agg_col|DOMAIN": "error message", ...}
}
```

Python normalization helper in `scripts/debug/plot_domain_circle_network.py`:
`normalize_julia_estimates()` converts Julia key format → Python `construct_a/b` + `dr_gamma_ci` list.

### Installation

Julia 1.12.5 installed via juliaup. To reinstall:
```bash
curl -fsSL https://install.julialang.org | sh -s -- --yes
export PATH="$HOME/.juliaup/bin:$PATH"
# Then install packages:
julia --project=julia/ -e 'using Pkg; Pkg.add(["DataFrames","CSV","JSON","GLM","Distributions","StatsBase","CategoricalArrays","Optim","ForwardDiff"]); Pkg.add(["LinearAlgebra","Statistics","Random","Dates","Printf","Test"])'
```
