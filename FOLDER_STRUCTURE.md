# Navegador Project - Folder Structure Guide

**Last Updated:** 2026-02-03

This document explains the reorganized folder structure and where to find different types of files.

---

## 📁 Root Directory

The root directory now contains only **core production Python modules** that are actively imported by other files. This preserves all import dependencies without requiring code changes.

### Core Modules (kept in root)
- `agent.py` - Main agent implementation
- `dashboard.py` - Dashboard interface
- `config.py` - Configuration management
- `main.py` - Application entry point
- `detailed_analysis.py` - Detailed analysis module
- `variable_selector.py` - Variable selection logic
- `variable_reviewer.py` - Variable review functionality
- `utility_functions.py` - Common utility functions
- `plotting_utils.py`, `plotting_utils_ses.py` - Plotting utilities
- `ses_analysis.py` - SES analysis module
- `meta_prompting.py` - Meta-prompting functionality
- `intent_classifier.py` - Intent classification
- `cache_manager.py` - Cache management
- `dataset_knowledge.py` - Dataset knowledge base
- `performance_optimization.py` - Performance optimizations
- And other core production modules

---

## 📚 Documentation - [docs/](docs/)

All markdown documentation files:

- `QUICK_START.md` - Quick start guide
- `CLAUDE1_COMPLETE_SUMMARY.md` - Claude1 implementation summary
- `META_PROMPTING_GUIDE.md` - Meta-prompting guide
- `META_PROMPTING_SUMMARY.md` - Meta-prompting summary
- `DEPLOYMENT_SSH_DOCKER_ACR.md` - Deployment guide
- `DOCKER_SANDBOX_STRATEGY.md` - Docker sandbox documentation
- `CREDENTIALS_GUIDE.md` - Credentials management guide
- `SECURITY_NOTICE.md` - Security notices
- `PHASE3_PRIORITY_FIXES.md` - Phase 3 fixes documentation
- `QUICK_FIXES_INTEGRATION_GUIDE.md` - Quick fixes guide
- `SANDBOX_README.md` - Sandbox documentation
- `SES_PLOTTING_INTEGRATION_SUMMARY.md` - SES plotting integration
- `setup_navegador_vm_instructions.md` - VM setup instructions
- `vm_desktop_vscode_setup.md` - VSCode setup guide

---

## 🐳 Docker Configuration - [docker/](docker/)

All Docker-related files:

- `Dockerfile` - Main Dockerfile
- `Dockerfile.claude1` - Claude1 specific Dockerfile
- `docker-compose.claude1.yml` - Docker Compose configuration

---

## ⚙️ Configuration - [config/](config/)

Configuration and dependency files:

- `environment.yml` - Main conda environment
- `environment_linux.yml` - Linux-specific environment
- `environment_min.yml` - Minimal environment
- `environment_working.yml` - Working environment snapshot
- `requirements.txt` - Python dependencies
- `package.json`, `package-lock.json` - Node.js dependencies
- `playwright.config.ts` - Playwright configuration

**Note:** `.env` files remain in root for easy access.

---

## 📓 Notebooks - [notebooks/](notebooks/)

Jupyter notebooks organized by purpose:

### [notebooks/analysis/](notebooks/analysis/)
Analysis notebooks:
- `nav_py13_reporte1.ipynb` - Main report analysis
- `analyze_region_values.ipynb` - Region value analysis
- `ses_table_analysis.ipynb` - SES table analysis

### [notebooks/preprocessing/](notebooks/preprocessing/)
Data preprocessing notebooks:
- `nav_py13_prep_dbf1.ipynb` - Main preprocessing
- `proc_cuest.ipynb` - Survey processing

### [notebooks/experiments/](notebooks/experiments/)
Experimental and test notebooks:
- `Navegador_openai_py13.ipynb` - OpenAI experiments
- `Navegador_gemini_py10.ipynb` - Gemini experiments
- `nav_py13_langchain.ipynb` - Langchain integration
- `test_langchain.ipynb` - Langchain tests
- `test_genai.ipynb` - GenAI tests
- `Semi_Structured_RAG.ipynb` - RAG experiments

---

## 🧪 Tests - [tests/](tests/)

All test files organized by type:

### [tests/unit/](tests/unit/)
Unit tests (~30 files):
- `test_agent_*.py` - Agent tests
- `test_dashboard_*.py` - Dashboard tests
- `test_ses_*.py` - SES analysis tests
- `test_*.py` - Various unit tests

### [tests/integration/](tests/integration/)
Integration tests:
- `test_comprehensive_workflow.py`
- `test_workflow_integration.py`
- `test_detailed_analysis_integration.py`
- `test_agent_workflow_integration.py`

### [tests/performance/](tests/performance/)
Performance benchmarks:
- `benchmark_variable_search.py`
- `test_performance_optimization.py`

### [tests/e2e/](tests/e2e/)
End-to-end tests:
- `demo-todo-app.spec.ts`
- `example.spec.ts`

---

## 🔧 Scripts - [scripts/](scripts/)

Utility scripts organized by purpose:

### [scripts/debug/](scripts/debug/) (~30 files)
Debugging and analysis scripts:
- `debug_*.py` - Various debug scripts
- `analyze_*.py` - Analysis scripts
- `check_*.py` - Verification scripts
- `add_*.py` - Helper scripts for adding functionality
- `enhanced_agent_test.py`, `enhanced_agent_tester.py`
- `create_debug_dashboard.py`
- `demo_ses_plotting.py`
- And more debugging utilities

### [scripts/fixes/](scripts/fixes/) (20 files)
Fix scripts for various issues:
- `fix_*.py` - All fix scripts
- Examples: `fix_agent_state.py`, `fix_dashboard_syntax.py`, etc.

### [scripts/setup/](scripts/setup/)
Setup and credential management:
- `setup_credentials.py`
- `auto_credentials.py`
- `configure_git.py`
- `credentials_manager.py`
- `global_credentials.py`
- `load_credentials.py`
- `secure_credentials.py`

### [scripts/deployment/](scripts/deployment/)
Deployment scripts:
- `deploy_to_existing_vm.sh`
- `run_sandbox.sh`
- `setup_navegador_vm.sh`
- `manage_credentials.sh`
- `analyze_agent.sh`
- `test_agent.sh`
- `test_agent_with_env.sh`
- `test_langsmith.sh`

### [scripts/maintenance/](scripts/maintenance/)
Maintenance utilities:
- `clean_duplicates.py`
- `clean_notebooks.py`
- `convert_pickle_to_json.py`
- `inspect_backups.py`
- `update_pickle_to_json.py`
- `replace_process_agent.py`
- `quick_fixes.py`

---

## 🗄️ Data - [data/](data/)

Data files organized by type:

### [data/encuestas/](data/encuestas/)
Survey data files:
- `answers_sum.json`
- `los_mex_dict.json`

### [data/cache/](data/cache/)
Cache files:
- `llm_cache.json`

### [data/results/](data/results/)
Analysis results and outputs:
- `structured_summary_checkpoint.json`
- `ses_variables_report_*.json`
- `state_construction_*.json`
- Other result files

---

## 📝 Logs - [logs/](logs/)

Application and test logs:
- `agent_analysis.log`
- `agent_test_results.log`
- `test_agent.log`
- `test_agent_tracing.log`

---

## 🗃️ Archive - [archive/](archive/)

Deprecated and backup files:

### [archive/backups/](archive/backups/)
Backup files:
- `*.bak` - Backup files
- `*archive*` - Archived versions
- `*.corrupted` - Corrupted files
- Old dashboard backups with timestamps

### [archive/deprecated/](archive/deprecated/)
Empty and deprecated files (9 files):
- Empty Python files that are no longer used
- Deprecated implementations

---

## 🎯 Finding Files Quickly

### Looking for...

**Documentation?** → Check [docs/](docs/)

**Tests?** → Check [tests/](tests/) (organized by type)

**Need to debug?** → Check [scripts/debug/](scripts/debug/)

**Need to fix something?** → Check [scripts/fixes/](scripts/fixes/)

**Setting up the environment?** → Check [scripts/setup/](scripts/setup/)

**Deploying?** → Check [scripts/deployment/](scripts/deployment/)

**Notebooks?** → Check [notebooks/](notebooks/) (organized by purpose)

**Configuration?** → Check [config/](config/) or root for .env files

**Data files?** → Check [data/](data/)

**Logs?** → Check [logs/](logs/)

**Core code?** → Still in root directory (no changes needed)

---

## ✅ Import Safety

**All core Python modules remain in the root directory** to preserve import statements. No code changes are required - all imports work exactly as before.

Files can still import from root:
```python
from dashboard import create_dashboard
from agent import create_agent
from utility_functions import get_answer
from plotting_utils import create_plot
```

---

## 📊 Statistics

- **Root directory reduced:** ~200 files → ~60 files (70% reduction)
- **Tests organized:** 40+ test files categorized by type
- **Scripts organized:** 50+ scripts categorized by purpose
- **Documentation centralized:** 15 docs in one location
- **Zero broken imports:** All dependencies preserved

---

## 🔄 Maintenance

### Adding New Files

- **New tests** → [tests/](tests/) (in appropriate subfolder)
- **New scripts** → [scripts/](scripts/) (in appropriate subfolder)
- **New docs** → [docs/](docs/)
- **New notebooks** → [notebooks/](notebooks/) (in appropriate subfolder)
- **New core modules** → Root directory (if imported by other files)

### Cleaning Up

Old backups and deprecated files are in [archive/](archive/) and can be deleted periodically to save space.

---

**Questions?** Check the relevant folder's README or the main documentation in [docs/](docs/).
