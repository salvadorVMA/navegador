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
| `ses_regression.py` | Active | `CrossDatasetBivariateEstimator` — SES-bridge simulation via `OrderedModel`/`MNLogit` to estimate associations between cross-survey variable pairs |
| `ses_analysis.py` | Active | SES preprocessing: create region/edad/empleo from raw vars, normalise escol/Tam_loc/est_civil |
| `survey_kg.py` | Active | Knowledge graph ontology for survey domains (merged from worktree-knowledge-graph) |
| `tool_enhanced_analysis.py` | Updated | Migrated from deprecated `AgentExecutor` to `langgraph.prebuilt.create_react_agent` |

### Recent Work (as of 2026-02-26)

- **Worktree merge**: `worktree-knowledge-graph` merged into `feature/bivariate-analysis`. Brought in `survey_kg.py`, `docs/SES_BRIDGE_IMPROVEMENT_PLAN.md`, 276-pair sweep results, and 7-var SES bridge. Bug fixed in `_sample_ses_population` (indexing pool with `available_in_pool` not full `ses_vars`). Test fixture updated for 7 SES vars; all 47 unit tests pass.
- **Knowledge graph**: `survey_kg.py` defines domain/variable/concept ontology for survey topics.
- **Cross-dataset bivariate pipeline** (Phase 5): SES-bridge simulation estimates Cramér's V between variables from different surveys. Results include conditional distribution profiles and key contrasts.
- **Analytical essay pipeline**: Two-step LLM chain (reasoning outline → essay). Essays lead with data patterns ("25% vs 12%") not statistics recitation.
- **SES bridge predictor expansion**: `SES_REGRESSION_VARS` now 7 variables: `sexo`, `edad`, `region`, `empleo`, `escol`, `Tam_loc`, `est_civil`. `SESEncoder` handles ordinal (`Tam_loc`) and one-hot (`est_civil`). Absent columns degrade gracefully.
- **Regression diagnostics**: `SurveyVarModel.diagnostics()` returns pseudo-R² (McFadden), LLR p-value, per-coefficient table sorted by |t|, `top_predictor`, and `dominant_ses_group`. `estimate()` exposes `model_a_diagnostics` / `model_b_diagnostics` in the return dict.
- **Essay Bridge Diagnostics appendix**: `_format_bridge_diagnostics()` in `analytical_essay.py` appends a human-readable per-variable diagnostics table (R², quality flag, top SES coefficients) AFTER the LLM essay — never in the LLM prompt.
- **Label resolution**: `_get_var_labels` + `_apply_labels_to_estimate` in `quantitative_engine.py` resolve raw numeric codes (e.g. "1.0", "2.0") to human-readable labels in cross-tab profiles before the LLM sees them.
- **Sentinel filtering**: `_is_sentinel()` in `ses_regression.py` and NaN/sentinel filtering in `compute_variable_statistics()` ensure codes like 99 (no-answer) and NaN (not-applicable) are excluded.
- **Sweep scripts**: `scripts/debug/sweep_cross_domain.py` (276-pair sweep with `MAX_ORDINAL_CATEGORIES=15` gate), `scripts/debug/visualize_cross_domain.py`, `scripts/debug/visualize_kg.py`.
- **Test runner**: `scripts/run_tests.sh [unit|essays|all]` — essays run via nohup in background.
- **SES bridge improvement plan**: `docs/SES_BRIDGE_IMPROVEMENT_PLAN.md` — Options C (Residual bridge) and D (Ecological bridge) designed and ready to implement.

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
