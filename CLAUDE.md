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
| `dashboard.py` | Dash web interface |
| `config.py` | Configuration and path management |
| `detailed_analysis.py` | Analysis pipeline |
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

## Current Branch / Worktree

**Worktree:** `worktree-knowledge-graph`
**Path:** `.claude/worktrees/knowledge-graph/` (relative to main repo root)
**Branched from:** `feature/bivariate-analysis`

This worktree is the active development environment for the **SES bridge / knowledge graph** work.
Always run code and make changes here, not in the main working directory, unless merging back.

**How to load the survey data:** The data file lives in the main repo, not the worktree.
Always pass the path explicitly when running scripts:
```bash
NAVEGADOR_LOS_MEX_DICT_PATH=/workspaces/navegador/data/encuestas/los_mex_dict.json \
  python scripts/debug/sweep_cross_domain.py --workers 1
```
(2-core machine: use `--workers 1` to leave 1 core idle.)

### Key modules in this worktree

| Module | Purpose |
|--------|---------|
| `ses_regression.py` | `CrossDatasetBivariateEstimator` — SES bridge simulation |
| `ses_analysis.py` | `AnalysisConfig.preprocess_survey_data()` — normalises SES columns |
| `scripts/debug/sweep_cross_domain.py` | 276-pair sweep; outputs to `data/results/` |
| `scripts/debug/visualize_cross_domain.py` | Heatmap viz of sweep results |

### SES Bridge — current state (as of 2026-02-24)

**Baseline bridge predictors:** `sexo`, `edad`, `region`, `empleo`, `escol` (5 variables)

**Extended bridge predictors (added 2026-02-24):** `Tam_loc`, `est_civil`
- `Tam_loc`: locality size (1=large urban → 4=rural), ordinal, 24/26 surveys
  (absent: JUEGOS_DE_AZAR, CULTURA_CONSTITUCIONAL — graceful degradation)
- `est_civil`: marital status (nominal one-hot), 26/26 surveys;
  sentinel codes 8/9 → NaN added to `preprocess_survey_data()`
- `religion`: only 2/26 surveys — NOT included as a bridge predictor
- `edo` (state): 32 INEGI codes, no value labels, convergence risk — excluded for now

**Data audit findings:** Complete audit in `data/results/ses_bridge_report.md`.
Additional variables present across all 26 surveys: `ing_ind` (individual income),
`ing_fam` (family income), `Estrato` (stratum, 24/26) — candidates for future extension.

### SES Bridge — improvement plan

Full plan: `docs/SES_BRIDGE_IMPROVEMENT_PLAN.md`

| Option | Description | Status |
|--------|-------------|--------|
| A | Expand predictors (Tam_loc, est_civil) | **Done** |
| B | Run baseline sweep with expanded predictors | In progress |
| C | Option 3: Mantel-Haenszel Residual Bridge | Planned |
| D | Option 4: Ecological Bridge (geo × locality cells) | Planned |
| E | Comparison sweep: all three methods on 276 pairs | Planned |

**Option 3 (Residual bridge):** New class `ResidualBridgeEstimator` in `ses_regression.py`.
Stratifies the synthetic SES population into K≈30 cells (KMeans), computes V within each cell,
aggregates via Mantel-Haenszel. Measures domain association *beyond* shared demographics.

**Option 4 (Ecological bridge):** New class `EcologicalBridgeEstimator` in `ses_regression.py`.
Aggregates survey responses at state × Tam_loc cells (max 128 cells), merges both surveys on
the geographic key, computes weighted Spearman ρ. Measures co-variation *across Mexican geography*.
Subject to ecological fallacy but immune to the SES bridge's compression problem.

### Known data quality rules

- Sentinel codes `>= 97` or `< 0`: filtered by `_is_sentinel()` in `ses_regression.py`
- `est_civil` codes 8 and 9: below sentinel threshold; explicitly remapped → NaN in `preprocess_survey_data()`
- `escol` codes 9, 98, 99: remapped in `preprocess_survey_data()`; JUEGOS_DE_AZAR/CULTURA_CONSTITUCIONAL use 1/3/4/5/6 scale → remapped to 1-5
- `Tam_loc`: clipped to 1–4; values outside range → NaN
- NaN in `df_tables`: conditional/skip-pattern questions — filter and renormalize before LLM

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
