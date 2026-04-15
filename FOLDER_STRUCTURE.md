# Navegador Project - Folder Structure Guide

**Last Updated:** 2026-04-13

This document describes the project directory layout. Navegador is an AI-powered survey analysis platform combining LLM agents, doubly-robust SES bridge estimation, knowledge graphs, and topological data analysis across Mexican survey data (los_mex) and the World Values Survey (WVS, 66 countries, 7 waves).

---

## Root Directory — Core Python Modules

Production modules imported by other files. Entry points: `main.py` (CLI), `dashboard.py` (web on port 8050).

### Agent and Interface

| Module | Purpose |
|--------|---------|
| `main.py` | CLI agent entry point |
| `dashboard.py` | Dash web interface |
| `agent.py` | Main agent workflow and orchestration (LangGraph) |
| `agent_conversation.py` | Conversation state management |
| `intent_classifier.py` | User intent classification |
| `tool_enhanced_analysis.py` | LangGraph react agent with tools |

### Analysis Engines

| Module | Purpose |
|--------|---------|
| `analytical_essay.py` | Two-step LLM pipeline: reasoning outline + essay generation |
| `quantitative_engine.py` | Pure-computation report: sentinel filtering, label resolution, cross-dataset bivariate |
| `ses_regression.py` | All 6 bridge estimators (DR, Bayesian, MRP, Ecological, Residual, Simulation) |
| `ses_analysis.py` | SES preprocessing: variable creation, sentinel remapping, ordinal normalization |
| `jax_dr_bridge.py` | JAX GPU bridge (Apple Metal / CUDA / TPU) |
| `jax_backend.py` | JAX backend utilities |

### Knowledge Graph and Ontology

| Module | Purpose |
|--------|---------|
| `survey_kg.py` | Knowledge graph ontology for survey domains |
| `opinion_ontology.py` | `OntologyQuery`: network traversal API (neighborhoods, Dijkstra paths, lift-to-construct) |
| `multi_hop_prediction.py` | `BayesianMultiHopPredictor`: item-to-item prediction chains via construct bridges |

### WVS Integration

| Module | Purpose |
|--------|---------|
| `wvs_metadata.py` | WVS constants, equivalence parsing, cultural zones, SES harmonization config |
| `wvs_loader.py` | `WVSLoader`: load CSVs from zip, sentinel cleaning, SES harmonization, `wvs_dict` |
| `wvs_ses_bridge.py` | `WVSBridgeEstimator`: cross-dataset gamma, temporal/geographic sweeps |
| `wvs_anchor_discovery.py` | ChromaDB vector search + LLM grading for anchor pairs |

### Data and Utilities

| Module | Purpose |
|--------|---------|
| `config.py` | Configuration and path management |
| `dataset_knowledge.py` | Survey data loading and metadata |
| `variable_selector.py` | Query-to-variable semantic matching |
| `cache_manager.py` | LLM response caching |
| `meta_prompting.py` | Prompt optimization system |
| `prompt_integration.py` | Quality scoring |
| `plotting_utils.py` | General plotting utilities |
| `plotting_utils_ses.py` | SES-specific plotting |
| `utils.py` | Common helpers |
| `ordinal_filter.py` | Ordinal variable filtering |
| `detailed_analysis.py` | Legacy analysis pipeline |
| `preprocess_navegador.py` | Data preprocessing |
| `import_los_mex.py` | Los_mex data import |
| `process_summaries.py` | Summary processing |

---

## `graph_traversal_engine/` -- Graph Traversal Engine Package

Query engine over the WVS gamma-surface: Structure + Dynamics + Geometry + Narrative.

| Module | Phase | Purpose |
|--------|-------|---------|
| `__init__.py` | -- | Package exports |
| `context.py` | 1 | Dataclasses: `Context`, `ContextGraph`, `Fingerprint`, `CampAssignment`, `GraphFamily` |
| `data_loader.py` | 1 | Wave-aware loading from navegador_data + wvs_kg fallback |
| `wvs_ontology.py` | 1 | `WVSOntologyQuery`: profiles, neighbors, Dijkstra paths, camps, cross-context comparison |
| `propagator.py` | 2 | BP lift, on-the-fly PPR (power iteration), spectral heat kernel; consensus scoring |
| `projector.py` | 3 | Spectral neighbors, zone aggregation, temporal trajectory, SES geometry, transfer confidence |
| `synthesizer.py` | 4 | `NarrativeSynthesizer`: structured markdown, auto-caveats, optional LLM |
| `engine.py` | All | `GraphTraversalEngine.query()`, `compare_countries()`, `compare_waves()` |

---

## `docs/` -- Documentation

50+ markdown files covering architecture, methods, plans, and findings.

### Active Reference

| File | Purpose |
|------|---------|
| `GRAPH_TRAVERSAL_ENGINE_PLAN.md` | GTE spec (Phases 0-5 design) |
| `GRAPH_TRAVERSAL_ENGINE_SPEC.md` | GTE implementation spec |
| `PROPAGATOR_PROJECTOR_METHODS.md` | Technical methods: BP, PPR, spectral, zones, temporal, SES geometry |
| `MESSAGE_PASSING_SPEC.md` | Mathematical reference: notation, algorithms, convergence |
| `MESSAGE_PASSING_PLAN.md` | MP scoping decisions and plan |
| `wvs_message_passing.md` | MP implementation guide with code fragments |
| `WVS_INTEGRATION_PLAN.md` | Full WVS integration plan with gamma-surface formulation |
| `WVS_INTEGRATION_STATUS.md` | WVS implementation status tracker |
| `WVS_ONTOLOGY_FINDINGS.md` | WVS ontology and cross-country prediction findings |
| `WVS_CONSTRUCT_PLAN.md` | WVS construct design |
| `WVS_GAMMA_SURFACE_PLAN.md` | Gamma-surface computation plan |
| `WVS_VALIDATED_INDICES.md` | WVS validated survey indices |
| `TOPOLOGICAL_ANALYSIS_WVS.md` | TDA pipeline architecture (Julia-accelerated) |
| `ALL_WAVE_SWEEP_PLAN.md` | All-wave (W3-W7) sweep plan |
| `SES_REALIGNMENT_PLAN.md` | SES coding realignment plan + root cause analysis |

### Bridge and SES

| File | Purpose |
|------|---------|
| `BRIDGE_ESTIMATORS_GUIDE.md` | Guide to all 6 bridge estimators |
| `BRIDGE_IMPROVEMENT_PLAN_V2.md` | DR bridge optimization history |
| `BRIDGE_QUESTIONS_CATALOG.md` | Bridge question catalog |
| `DR_BRIDGE_DEVELOPMENT_GUIDE.md` | DR bridge development guide |
| `SES_BRIDGE_IMPROVEMENT_PLAN.md` | SES bridge improvement plan |
| `SES_PLOTTING_INTEGRATION_SUMMARY.md` | SES plotting integration |
| `bridge_regression_review_v2.md` | Bridge regression review v2 |
| `bridge_regression_review_v3.md` | Bridge regression review v3 |

### Knowledge Graph and Ontology

| File | Purpose |
|------|---------|
| `ONTOLOGY_GUIDE.md` | Ontology usage guide |
| `CONSTRUCT_ONTOLOGY_PLAN.md` | Construct ontology design |
| `CONSTRUCT_IDENTIFICATION_AND_VALIDATION.md` | Construct identification methods |
| `ATTITUDE_PREDICTION_ENGINE.md` | Prediction engine design |
| `BIPARTITION_AND_CAMP_STRUCTURE.md` | Bipartition and camp analysis |
| `significant_constructs.md` | Significant construct catalog |
| `SURVEY_QUALITY_CONCERNS.md` | Data quality documentation |

### Agent and Architecture

| File | Purpose |
|------|---------|
| `AGENTIC_ARCHITECTURE_DIAGRAM.md` | Agent architecture diagram |
| `AGENTIC_TOOLS_IMPLEMENTATION_PLAN.md` | Agent tools implementation plan |
| `TOOLS_QUICK_REFERENCE.md` | Tools quick reference |
| `BUSINESS_USE_CASES.md` | Business use cases document |

### Infrastructure and Setup

| File | Purpose |
|------|---------|
| `QUICK_START.md` | Getting started guide |
| `SECURITY_TOOLS.md` | Security scanning tools |
| `SECURITY_NOTICE.md` | Security notices |
| `CREDENTIALS_GUIDE.md` | Credentials management |
| `CODACY_REVISIONS.md` | Codacy code quality findings |
| `setup_navegador_vm_instructions.md` | VM setup instructions |
| `vm_desktop_vscode_setup.md` | VSCode desktop setup |
| `DEPLOYMENT_SSH_DOCKER_ACR.md` | Deployment guide |
| `META_PROMPTING_GUIDE.md` | Prompt optimization guide |
| `META_PROMPTING_SUMMARY.md` | Prompt optimization summary |
| `OPEN_SOURCE_MODELS_PLAN.md` | Open source model integration plan |

### Archived (historical value, no longer active focus)

| File | Purpose |
|------|---------|
| `DOCKER_SANDBOX_STRATEGY.md` | Claude1-era Docker sandbox architecture |
| `SANDBOX_README.md` | Claude1-era sandbox guide |
| `PHASE3_PRIORITY_FIXES.md` | Jan 2026 dashboard reliability fixes |
| `QUICK_FIXES_INTEGRATION_GUIDE.md` | Jan 2026 dashboard quick fixes |
| `CLAUDE1_COMPLETE_SUMMARY.md` | Claude1 implementation summary |

---

## `scripts/` -- Utility and Analysis Scripts

### `scripts/pipeline/` -- Orchestration Pipelines

| Script | Purpose |
|--------|---------|
| `ses_realignment_pipeline.py` | Prefect pipeline: all SES sweeps (los_mex, WVS geographic, temporal) |
| `allwave_tda_pipeline.py` | Prefect pipeline: all-wave TDA (Mode A geographic + Mode B temporal + Phase C synthesis) |
| `tda_pipeline.py` | Prefect pipeline: W7 geographic TDA (7 phases) |
| `temporal_tda_pipeline.py` | Temporal TDA pipeline: Mexico W3-W7 |
| `all_wave_sweep_pipeline.py` | All-wave gamma-surface sweep pipeline |

### `scripts/debug/` -- Analysis, Builds, Sweeps, Visualization (~100+ scripts)

**WVS Analysis:**

| Script | Purpose |
|--------|---------|
| `analyze_wvs_geographic.py` | Geographic analysis by country and cultural zone |
| `analyze_wvs_temporal.py` | Temporal trends, structural stability |
| `analyze_wvs_country_comparison.py` | Country distance from average, multi-country plots |
| `analyze_wvs_mex_validation.py` | MEX within vs cross validation |
| `analyze_wvs_mex_validation_v2.py` | Cross-dataset validation with polarity correction |
| `analyze_wvs_post_realignment.py` | WVS post-realignment descriptives |
| `analyze_allwave_gamma_surface.py` | All-wave gamma-surface analysis |
| `analyze_macro_indicators.py` | V-Dem + World Bank + UNDP indicators vs network metrics |
| `analyze_gte_allwaves.py` | Cross-wave GTE analysis: camps, fingerprints, hubs, 6 plots |

**Los_mex Analysis:**

| Script | Purpose |
|--------|---------|
| `analyze_post_realignment.py` | Los_mex post-realignment descriptives |
| `analyze_network_topology.py` | Network topology and geometry |
| `analyze_item_network.py` | Item-level signal chains |
| `analyze_bipartition.py` | Bipartition analysis |
| `analyze_ses_drivers.py` | SES driver analysis |
| `analyze_sign_flips.py` | Cross-zone sign flip analysis |
| `analyze_cross_country_geometry.py` | Cross-country SES geometry |

**Build Scripts:**

| Script | Purpose |
|--------|---------|
| `build_construct_variables.py` | Build agg_* construct columns from SVS v4 |
| `build_gamma_surface.py` | Unified gamma-surface from 4 sources |
| `build_wvs_constructs.py` | WVS construct builder (single context) |
| `build_wvs_constructs_multi.py` | WVS construct builder (multi-context, any wave x country) |
| `build_wvs_losmex_construct_map.py` | WVS-los_mex construct cross-map v1 (Jaccard) |
| `build_wvs_losmex_construct_map_v2.py` | WVS-los_mex construct cross-map v2 (LLM-graded) |
| `build_wvs_svs.py` | WVS semantic variable selection |
| `build_wvs_kg_ontology.py` | Build WVS KG + fingerprints from sweep data |
| `build_wvs_kg_per_wave.py` | Per-wave KG ontologies |

**Compute Scripts:**

| Script | Purpose |
|--------|---------|
| `compute_ses_fingerprints.py` | L0/L1/L2 SES fingerprints, orphan loading enrichment |
| `compute_wvs_l0_fingerprints.py` | WVS L0 fingerprints |
| `compute_gte_camps.py` | Fiedler bipartition + structural balance from weight matrices |
| `compute_gte_fingerprints.py` | SES Spearman rho from CSVs or raw Time Series ZIP |

**Sweep Scripts:**

| Script | Purpose |
|--------|---------|
| `sweep_construct_dr.py` | Construct-level DR sweep (4979 pairs, atomic checkpointing) |
| `sweep_dr_highci.py` | DR re-sweep with high bootstrap CIs, per-pair timeout |
| `sweep_cross_domain.py` | Original 276-pair baseline sweep |
| `sweep_bridge_comparison.py` | All 6 methods on 276 pairs |
| `sweep_dr_only.py` | DR-only sweep |

**TDA Scripts:**

| Script | Purpose |
|--------|---------|
| `tda_convert_sweep_to_matrices.py` | Phase 0: sweep JSON to per-country weight/distance CSVs |
| `tda_convert_allwave_to_matrices.py` | Phase 0: all-wave to per-wave geographic + per-country temporal CSVs |
| `tda_convert_temporal_matrices.py` | Temporal: per-wave matrices from temporal sweep |
| `tda_persistent_homology.py` | Phase 4: ripser H0/H1/H2 + bottleneck distances |
| `tda_embeddings_and_zones.py` | Phase 5: MDS + zone coherence permutation tests |
| `tda_temporal_trajectory.py` | Temporal: spectral trajectory + edge confidence |
| `tda_allwave_analysis.py` | Phase C: Fiedler heatmaps, convergence, zone trends |
| `tda_allwave_report.py` | 8-figure report generator |

**Message Passing Scripts:**

| Script | Purpose |
|--------|---------|
| `mp_utils.py` | Shared data loading, matrix ops, JSON serialization (wave-aware) |
| `mp_belief_propagation.py` | Loopy BP on Potts MRF (55x55, 5-state ordinal) |
| `mp_spectral_diffusion.py` | Laplacian eigendecomposition, Fiedler partition, heat kernel |
| `mp_ppr_influence.py` | Personalized PageRank, hub/sink/asymmetry analysis |
| `mp_temporal_descriptive.py` | Velocity fields, equilibrium distance, 1-param forecast |
| `mp_report.py` | Generate MP plots and markdown report |

**GTE Scripts:**

| Script | Purpose |
|--------|---------|
| `run_gte_allwaves.py` | Orchestration: camps + fingerprints + MP for any wave set |
| `demo_wvs_ontology.py` | Per-country network builder + circle-layout visualizations |
| `demo_wvs_ontology_capabilities.py` | 10 OntologyQuery operations across 6 countries |
| `diagnostic_wvs_ontology_readiness.py` | 5-section readiness diagnostic |
| `test_wvs_prediction_scenarios.py` | 5 scenarios x 6 countries, DRPredictionEngine |
| `test_wvs_profile_predictions.py` | 5 SES profiles x 5 scenarios x 6 countries |

**Visualization Scripts:**

| Script | Purpose |
|--------|---------|
| `plot_domain_circle_network.py` | Circle-layout network plots (sign/SES colored) |
| `plot_construct_network.py` | Construct network visualization |
| `plot_ses_signatures.py` | Per-country SES signature plots |
| `plot_ses_signature_3d.py` | Interactive 3D Plotly SES signature scatter |
| `plot_country_gamma_circles.py` | Per-country gamma circle plots |
| `plot_regional_circle_networks.py` | Regional circle network plots |
| `visualize_gamma_surface.py` | PCA, heatmaps, ribbon plots, Mexico trajectory |
| `visualize_kg.py` | Knowledge graph visualization |
| `visualize_construct_network.py` | Construct network visualization |
| `visualize_cross_domain.py` | Cross-domain visualization |

**Other Scripts:**

| Script | Purpose |
|--------|---------|
| `audit_scale_direction.py` | Scale inversion audit + RC override generation |
| `patch_kg_ontology_bridges.py` | Recompute fingerprint_cos, flip bridge gamma signs |
| `rebuild_kg_ontology.py` | Rebuild KG ontology |
| `optimize_constructs.py` | Construct optimization |
| `export_constructs_for_julia.py` | CSV exporter for Julia (los_mex) |
| `export_wvs_for_julia.py` | CSV exporter for Julia (WVS, one CSV per context) |
| `merge_wave_sweeps.py` | Merge per-wave sweep results |
| `select_bridge_variables_semantic.py` | Semantic bridge variable selection |

### `scripts/fixes/` -- Bug Fix Scripts (~20 files)

`fix_*.py` scripts for various historical issues.

### `scripts/setup/` -- Setup and Credentials

Credential management: `setup_credentials.py`, `auto_credentials.py`, `credentials_manager.py`, etc.

### `scripts/deployment/` -- Deployment Scripts

Shell scripts: `deploy_to_existing_vm.sh`, `run_sandbox.sh`, `setup_navegador_vm.sh`, etc.

### `scripts/maintenance/` -- Maintenance Utilities

`clean_duplicates.py`, `clean_notebooks.py`, `convert_pickle_to_json.py`, etc.

---

## `tests/` -- Test Suites

### `tests/unit/` (~55 files)

| File | Tests | Coverage |
|------|-------|---------|
| `test_ses_regression.py` | 76 | SESEncoder, SurveyVarModel, CrossDataset, Residual, Ecological |
| `test_bridge_estimators_v2.py` | 36 | GK gamma, Bayesian, MRP, DR estimators |
| `test_bridge_evaluation.py` | 38 | Predictive accuracy, AIC/BIC, gamma recovery, CI calibration |
| `test_wvs_integration.py` | 135 | WVS Phases 1-3 (loader, metadata, SES bridge, anchors) |
| `test_wvs_ontology_readiness.py` | 35 | WVS data integrity + OntologyQuery integration |
| `test_graph_traversal_engine.py` | 49 | GTE Phases 1-4 (structure, propagator, projector, synthesizer) |
| `test_multi_hop_prediction.py` | -- | Multi-hop prediction engine |
| `test_wvs_l0_fingerprints.py` | -- | WVS L0 fingerprint computation |
| `test_quantitative_engine.py` | -- | Quantitative engine |
| `test_ses_analysis.py` | -- | SES analysis preprocessing |
| `test_agent_*.py` | -- | Agent workflow tests (multiple files) |
| `test_dashboard_*.py` | -- | Dashboard tests (multiple files) |

### `tests/integration/` (7 files)

Integration tests: agent workflow, analytical essay, cross-dataset bivariate, tool-enhanced analysis.

### `tests/performance/` (2 files)

Benchmarks: variable search, performance optimization.

### `tests/e2e/` (2 files)

Playwright end-to-end tests.

---

## `data/` -- Data Files

### `data/encuestas/`

- `los_mex_dict.json` (~191MB, Git LFS) -- Mexican survey data dictionary

### `data/wvs/`

- Variable equivalence XLSX files (tracked)
- Country codes and questionnaire PDFs (tracked)
- WVS CSV/ZIP data files (gitignored, symlinked from navegador_data)

### `data/results/`

Analysis outputs: sweep JSONs, KG ontologies, fingerprints, reports, plots.

Key files:
- `kg_ontology_v2.json` -- 93 L1 constructs, 984 bridges
- `ses_fingerprints.json` -- L0/L1/L2 fingerprints with loading gammas
- `wvs_kg_ontology.json` -- WVS KG (56 constructs, 395 bridges)
- `wvs_ses_fingerprints_v2.json` -- WVS OntologyQuery-compatible fingerprints
- `wvs_kg/W{3-7}/` -- Per-country per-wave KGs (221 files)
- Reports: `post_realignment_report.md`, `wvs_post_realignment_report.md`, etc.

### `data/tda/`

TDA pipeline outputs (gitignored, in navegador_data):
- `matrices/` -- Per-country weight/distance CSVs
- `floyd_warshall/`, `ricci/`, `spectral/`, `persistence/`, `embeddings/`, `alignment/`
- `allwave/` -- Per-wave geographic + per-country temporal
- `message_passing/` -- ~310 JSON files (BP, spectral, PPR per country)

### `data/gte/`

GTE pipeline outputs:
- `camps/` -- Per-country bipartition files
- `fingerprints/` -- Per-country SES fingerprint files

### `data/julia_bridge/` and `data/julia_bridge_wvs/`

Pre-built CSVs for Julia sweep engine.

---

## `notebooks/` -- Jupyter Notebooks

| Notebook | Purpose |
|----------|---------|
| `colab_jax_gamma_surface.ipynb` | Colab: JAX gamma-surface (auto-clones both repos) |
| `analysis/nav_py13_reporte1.ipynb` | Main report analysis |
| `analysis/analyze_region_values.ipynb` | Region value analysis |
| `preprocessing/nav_py13_prep_dbf1.ipynb` | Data preprocessing |
| `preprocessing/proc_cuest.ipynb` | Survey processing |
| `experiments/*.ipynb` | LLM experiments (OpenAI, Gemini, LangChain, RAG) |

---

## `config/` -- Configuration

- `environment.yml` -- Main conda environment
- `requirements.txt` -- Python dependencies
- Additional environment YMLs for different platforms

---

## `docker/` -- Docker Configuration

- `Dockerfile`, `Dockerfile.claude1`, `docker-compose.claude1.yml`
- Historical; local Mac + conda is now the primary dev environment.

---

## `archive/deprecated/` -- Deprecated Files

Old dashboard patches and agent fixes no longer in use.

---

## External: Julia Bridge

The Julia numeric engine lives in a separate worktree:

```
../navegador_julia_bridge/julia/
  src/NavegadorBridge.jl     -- Main module
  src/gamma_nmi.jl           -- GK gamma, NMI
  src/ordinal_model.jl       -- Ordered logit
  src/ses_encoder.jl         -- SES encoding (3-pass edad)
  src/dr_estimator.jl        -- DR bridge estimator
  src/sweep.jl               -- Sweep engine (8-thread)
  src/cronbach.jl            -- Cronbach alpha, scale building
  src/wvs_sweep.jl           -- WVS within-survey sweep
  scripts/run_v5_sweep.jl    -- Current sweep script
  scripts/tda_*.jl           -- TDA Julia scripts (Floyd-Warshall, Ricci, spectral, GW)
  test/runtests.jl           -- 66 unit tests
  docs/JULIA_BRIDGE_PRIMER.md
```

## External: navegador_data

Large data files live in a separate repo: `https://github.com/salvadorVMA/navegador_data`

Contains: sweep JSONs (gamma-surface, geographic, temporal), Julia CSVs, TDA outputs, construct manifests.
