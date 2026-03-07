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

## Current Branch

`feature/bivariate-analysis` (branched from `Claude1`) — active development branch.

The `worktree-knowledge-graph` worktree has been **merged** into this branch (commit `0f1fb30`). All knowledge-graph and expanded SES-bridge work now lives in the main workspace.

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
- **Causal interpretation**: γ measures "how much shared SES drives monotonic co-variation between attitudes across survey domains." Under CIA (conditional independence given SES), γ captures only SES-mediated association. Pairs with γ ≈ 0 indicate SES-independent or orthogonally-SES-driven attitudes.
- **γ detects monotonic relationships only**: Goodman-Kruskal γ = (C−D)/(C+D) based on concordant/discordant pairs. Cannot detect U-shaped or other non-monotonic SES-attitude relationships.
- **Normalized MI added**: `normalized_mutual_information(joint_table)` computes NMI ∈ [0,1] from the same joint table γ uses — zero additional model fitting. Detects any statistical dependence regardless of shape. Pairs with |γ| ≈ 0 but NMI >> 0 reveal non-monotonic SES structuring (U-shaped, crossover patterns). Sweep log flags these with `NM!`.

### Sweep Scripts

| Script | Purpose |
|--------|---------|
| `scripts/debug/sweep_cross_domain.py` | Original 276-pair baseline sweep |
| `scripts/debug/sweep_bridge_comparison.py` | All 6 methods on 276 pairs |
| `scripts/debug/sweep_dr_highci.py` | v3 DR re-sweep with high bootstrap CIs, per-pair timeout, atomic checkpointing |
| `scripts/debug/test_dr_diagnostic.py` | Per-step SIGALRM diagnostic for DR hang isolation |

### Sweep Results

| Version | SES vars | n_sim | n_bootstrap | Median CI_w | % excl zero | Notes |
|---------|----------|-------|-------------|-------------|-------------|-------|
| v1 | 7 vars | 500 | 10 | ~0.5 | — | Baseline |
| v2 | 10 vars | 500 | 200 | 1.351 | 0% | Row retention crisis (4.8%) |
| v3 (running) | 4 vars (sexo,edad,escol,Tam_loc) | 2000 | 200 | ~0.23 expected | TBD | Optimal config |

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
