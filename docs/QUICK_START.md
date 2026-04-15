# Navegador - Quick Start

## Prerequisites

- **Python 3.13** via conda (env name: `nvg_py13_env`)
- **Julia 1.12.5** via juliaup (for numeric sweeps)
- API keys: OpenAI and/or Anthropic (set in `.env`)

## Setup

```bash
# 1. Create conda environment (first time only)
conda env create -f config/environment.yml
conda activate nvg_py13_env

# 2. Install Julia (first time only)
curl -fsSL https://install.julialang.org | sh -s -- --yes
export PATH="$HOME/.juliaup/bin:$PATH"

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)

# 4. Install TDA dependencies (optional, for topological analysis)
pip install ripser persim pot
```

## Key Entry Points

### CLI Agent

```bash
conda activate nvg_py13_env
python main.py
```

Interactive conversational interface for querying survey insights.

### Web Dashboard

```bash
conda activate nvg_py13_env
python dashboard.py
# Opens on http://localhost:8050
```

### Graph Traversal Engine

```python
from graph_traversal_engine import GraphTraversalEngine

engine = GraphTraversalEngine(countries=["MEX", "USA", "JPN"])
result = engine.query(
    "gender_role_traditionalism|WVS_D",
    "MEX", wave=7, direction=-1,
)
print(result.narrative)
```

### OntologyQuery (los_mex)

```python
from opinion_ontology import OntologyQuery

oq = OntologyQuery()
neighborhood = oq.get_neighborhood("agg_personal_religiosity")
path = oq.find_path("agg_personal_religiosity", "agg_structural_housing_quality")
```

## Running Tests

```bash
conda activate nvg_py13_env

# All unit tests
python -m pytest tests/unit/ -v

# Specific test suites
python -m pytest tests/unit/test_graph_traversal_engine.py -v    # GTE (49 tests, ~2s)
python -m pytest tests/unit/test_ses_regression.py -v             # Bridge estimators (76 tests)
python -m pytest tests/unit/test_wvs_integration.py -v            # WVS integration (135 tests)
python -m pytest tests/unit/test_bridge_estimators_v2.py -v       # DR/Bayesian/MRP (36 tests)

# Integration tests (require API keys)
python -m pytest tests/integration/ -v
```

## Running Julia Sweeps

```bash
export PATH="$HOME/.juliaup/bin:$PATH"
cd ../navegador_julia_bridge/julia
julia -t 8 --project=. scripts/run_v5_sweep.jl
# ~40-45 min on 8 cores, outputs to navegador/data/results/
```

## Running Pipelines (Prefect)

```bash
conda activate nvg_py13_env

# SES realignment sweep (los_mex + WVS)
python scripts/pipeline/ses_realignment_pipeline.py --all --dry-run   # preview
python scripts/pipeline/ses_realignment_pipeline.py --los-mex         # los_mex only (~40 min)

# TDA pipeline (all waves)
python scripts/pipeline/allwave_tda_pipeline.py --all --skip-gw       # ~6 min

# GTE all-waves (camps + fingerprints + MP)
python scripts/debug/run_gte_allwaves.py --waves 3 4 5 6 7
```

## Project Structure

See `FOLDER_STRUCTURE.md` in the project root for the full directory layout.

## Key Documentation

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Project state, handoff protocol, all module documentation |
| `FOLDER_STRUCTURE.md` | Directory layout guide |
| `docs/PROPAGATOR_PROJECTOR_METHODS.md` | GTE mathematical methods |
| `docs/MESSAGE_PASSING_SPEC.md` | Message passing mathematics |
| `docs/BRIDGE_ESTIMATORS_GUIDE.md` | All 6 bridge estimator methods |
| `docs/WVS_INTEGRATION_PLAN.md` | WVS integration plan |
| `docs/SECURITY_TOOLS.md` | Security scanning procedures |

## Data

- **Los_mex survey data**: `data/encuestas/los_mex_dict.json` (~191MB, Git LFS)
- **WVS data**: Download from https://www.worldvaluessurvey.org/ into `data/wvs/`
- **Large result files**: Separate repo at https://github.com/salvadorVMA/navegador_data
