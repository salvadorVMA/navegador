# Knowledge Graph Feature Branch — Detailed Description

**Branch:** `feature/knowledge-graph`
**Date:** 2026-02-19
**Base:** `Claude1`

---

## Overview

This feature branch adds a **knowledge graph (KG) subsystem** to the Navegador survey analysis platform. The KG provides domain-boundary grounding that prevents LLMs from drawing spurious cross-domain conclusions when analyzing multi-topic survey data. It also introduces a new thematic essay architecture (v2) and upgrades the data setup pipeline.

---

## Problem Statement

When Navegador's LLM-based analysis engine receives a query spanning multiple survey domains (e.g., "How do religion and politics relate in Mexico?"), it retrieves variables from different surveys and feeds them to the model. Without structural metadata about which domains these variables belong to and whether cross-domain comparisons are methodologically valid, the LLM can hallucinate causal links or conflate unrelated constructs.

---

## What Changed

### 1. Knowledge Graph Core (`survey_kg.py`)

New module implementing a `SurveyOntologyGraph` class built on NetworkX. It:

- Loads a JSON ontology (`data/kg_ontology.json`) defining **domains**, **constructs**, **question-to-construct mappings**, and **cross-domain relationships**
- Determines whether two survey questions are comparable (same construct, related constructs, or unrelated)
- Generates prompt-enrichment context that tells the LLM which domain each variable belongs to and what cross-domain inferences are supported by the ontology
- Falls back gracefully to domain-only context if the full ontology is not bootstrapped
- Exposed as a lazy-loaded singleton (`kg`) with a public `get_kg_context_for_prompt()` method

### 2. KG Ontology Bootstrap (`scripts/setup/bootstrap_kg_ontology.py`)

LLM-assisted script that generates the knowledge graph ontology in two passes:

- **Pass 1:** Annotates each survey question with its construct(s) and confidence scores, parallelized across topics (~$0.10 using cheap models)
- **Pass 2:** Proposes cross-domain relationships (e.g., "economic_situation" in the Economy survey relates to "poverty_perception" in the Poverty survey)
- Outputs `data/kg_ontology.json` (the full ontology) and `data/kg_review_summary.md` (a prioritized human-review checklist)

### 3. KG Integration into Variable Selection (`variable_selector.py`)

After the existing semantic search and ranking pipeline selects the top variables, a new KG enrichment step:

- Calls `survey_kg.get_kg_context_for_prompt()` with the selected variable IDs
- Returns a `kg_context` string alongside the existing `(topic_ids, variables_dict, grade_dict)` tuple
- All return sites updated from 3-tuple to 4-tuple

### 4. KG Context Propagated Through the Analysis Pipeline

The KG context flows through the full chain:

- **`agent.py`**: Stores `kg_context` in `AgentState`, passes it to `run_analysis()`
- **`run_analysis.py`**: Forwards `kg_context` and `model_name` to `run_detailed_analysis()`
- **`detailed_analysis.py`**: Injects `kg_context` into the cross-summary prompt (before the QUERY), threaded through `create_prompt_crosssum()` → `get_structured_summary()` → `_deep_analyzer()` → `run_detailed_analysis()`

### 5. Thematic Essay v2 (`analytical_essay_v2.py`)

New essay architecture that replaces distribution-focused narratives with content-organized thematic essays:

- 5-stage pipeline: quantitative report → format → ChromaDB implications retrieval → thematic synthesis → essay generation
- Thematic synthesis groups variables by content (not by distribution shape), producing substantive findings with nuances
- Registered in `run_analysis.py` as the `"thematic_essay"` analysis type

### 6. Model Parameterization

The analysis pipeline previously hard-coded `gpt-4o-mini-2024-07-18` throughout. Now:

- `model_name` is accepted as a parameter in `run_detailed_analysis()`, `_deep_analyzer()`, `get_structured_summary()`, `batch_process_expert_summaries()`, and `get_transversal_analysis()`
- The agent can pass any model name down the chain

### 7. Quantitative Engine Simplification (`quantitative_engine.py`)

- Removed the `relevance_filter` parameter and `filter_variables_by_relevance()` call from `build_quantitative_report()`. The relevance gate (ChromaDB + expert grading) was redundant with the upstream variable selection pipeline that already performs semantic ranking
- Simplified from 3 phases to 2 phases (resolve → compute)

### 8. ChromaDB Setup Automation (`.devcontainer/fetch-data.sh`)

Extended the Codespace data-fetch script to also set up ChromaDB:

- Tries to download a pre-built ChromaDB archive from `navegador_data` (instant restore)
- Falls back to running `populate_chromadb.py` if the archive is not available (requires `OPENAI_API_KEY`, ~40 minutes)
- Checks if ChromaDB is already populated before doing anything
- Added `OPENAI_API_KEY` to `devcontainer.json` secrets

### 9. ChromaDB Population & Export Scripts

- **`scripts/setup/populate_chromadb.py`**: Populates ChromaDB from `los_mex_dict.json` using OpenAI embeddings, with batch processing and resume support
- **`scripts/setup/export_chromadb.sh`**: Archives the populated ChromaDB for upload to `navegador_data`

### 10. Architecture Comparison Benchmarks

Two comparative test runners with full result sets:

- **`scripts/debug/compare_architectures_final.py`**: Updated to a 2x2 design (architecture x model), with semantic variable selection replacing hard-coded variables. Tests `detailed_report` vs `analytical_essay` across `gpt-4.1-mini` and `gpt-4.1`
- **`scripts/debug/compare_architectures_v2.py`**: Three-way comparison (OLD, NEW v1, NEW v2) across 10 cross-topic questions
- Results stored in `data/results/architecture_comparison_2x2/` and `data/results/architecture_comparison_v2/`

### 11. KG Exploration Notebook (`notebooks/explore_kg.ipynb`)

Interactive Jupyter notebook for inspecting and validating the KG: load stats, visualize the ontology graph, browse constructs per topic, test pairwise comparability, review cross-domain relationships.

### 12. Design Documents

- **`knowledge_graphs_for_survey_analysis_engine.md`**: Comprehensive design doc covering the triple-based abstraction, integration patterns, Think-on-Graph research, and Python ecosystem tools
- **`survey_kg_pipeline_implementation.md`**: End-to-end technical guide for KG construction (object extraction, entity resolution, relationship discovery, community detection)
- **`data/kg_review_summary.md`**: Auto-generated prioritized review checklist for validating the bootstrapped ontology

### 13. Minor Changes

- `variable_reviewer.py`: Updated to unpack the new 4-tuple from `_variable_selector()`
- `analytical_essay.py`: Removed `relevance_filter=True` from `build_quantitative_report()` call
- `config/requirements.txt`: Added `networkx>=2.8`
- Whitespace and formatting cleanup across modified files
- `n_topics` formula in `get_structured_summary()` changed from `min(len // 4, 5)` to `max(4, len // 2)` to avoid thin analyses

---

## New Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `networkx` | >=2.8 | Knowledge graph data structure and traversal |

---

## Files Added

| File | Purpose |
|------|---------|
| `survey_kg.py` | KG core module (ontology graph, prompt enrichment) |
| `analytical_essay_v2.py` | Thematic essay v2 pipeline |
| `scripts/setup/bootstrap_kg_ontology.py` | LLM-assisted ontology generation |
| `scripts/setup/populate_chromadb.py` | ChromaDB population from survey data |
| `scripts/setup/export_chromadb.sh` | ChromaDB archive export |
| `scripts/debug/compare_architectures_v2.py` | Three-way architecture benchmark |
| `data/kg_ontology.json` | Generated knowledge graph ontology (~488KB) |
| `data/kg_review_summary.md` | Ontology review checklist |
| `notebooks/explore_kg.ipynb` | KG exploration notebook |
| `knowledge_graphs_for_survey_analysis_engine.md` | Design document |
| `survey_kg_pipeline_implementation.md` | Implementation guide |
| `docs/KNOWLEDGE_GRAPH_FEATURE.md` | This file |

## Files Modified

| File | Summary |
|------|---------|
| `agent.py` | Added `kg_context` to state, propagated through pipeline |
| `variable_selector.py` | KG enrichment step, 4-tuple return |
| `variable_reviewer.py` | Updated to unpack 4-tuple |
| `detailed_analysis.py` | KG context injection, model parameterization, n_topics formula |
| `analytical_essay.py` | Removed redundant relevance filter |
| `quantitative_engine.py` | Removed relevance_filter parameter |
| `run_analysis.py` | Added thematic_essay type, forward kg_context + model_name |
| `config/requirements.txt` | Added networkx |
| `.devcontainer/devcontainer.json` | Added OPENAI_API_KEY secret |
| `.devcontainer/fetch-data.sh` | ChromaDB setup automation |
| `scripts/debug/compare_architectures_final.py` | Refactored to 2x2 design |
