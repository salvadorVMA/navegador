# WVS Integration Status

Last updated: 2026-04-13

This file tracks the implementation state, known issues, data compatibility findings, and next steps for integrating the World Values Survey (WVS) into Navegador's SES bridge framework.

For the full conceptual plan (gamma-surface formulation, anchor questions, cultural zones), see [WVS_INTEGRATION_PLAN.md](WVS_INTEGRATION_PLAN.md).

---

## Phase Status

| Phase | Description | Status | Notes |
|-------|------------|--------|-------|
| 1 | Data Ingestion | **Complete** | `wvs_loader.py`, `wvs_metadata.py` -- loads Wave 7 and time-series CSVs |
| 2 | Anchor Discovery | **Complete** | `wvs_anchor_discovery.py` -- 48 grade-3 + 77 grade-2 matches found |
| 3 | SES Bridge and Gamma Surface | **Complete** | Julia sweeps: geographic (66 countries, 68K est), temporal (MEX 7 waves, 2.3K est), within-survey (MEX W7, 982 est) |
| 4 | Surface Analysis | **Complete** | Post-realignment analysis, country comparison, macro indicators (V-Dem), cross-zone sign flips, all-wave gamma-surface (123K est, 225 contexts) |
| 5 | Ontology and Graph Traversal | **Complete** | Per-country KGs, OntologyQuery for WVS, GTE Phases 1-4, all-wave camps/fingerprints/MP |

**Tests:** 135 WVS unit tests in `tests/unit/test_wvs_integration.py`, 35 ontology readiness tests in `tests/unit/test_wvs_ontology_readiness.py`, 49 GTE tests in `tests/unit/test_graph_traversal_engine.py`.

---

## Module Map

| Module | Purpose |
|--------|---------|
| `wvs_metadata.py` | Constants (`SES_VARS`, `CULTURAL_ZONES`, `DOMAIN_MAP`, `WAVE_LABELS`), parse equivalences XLSX |
| `wvs_loader.py` | `WVSLoader`: load CSVs from zip, sentinel cleaning, SES harmonization, build `wvs_dict` |
| `wvs_ses_bridge.py` | `WVSBridgeEstimator`: cross-dataset gamma, temporal sweep, geographic sweep; `SESHarmonizer` |
| `wvs_anchor_discovery.py` | `WVSAnchorDiscovery`: ChromaDB vector search + LLM grading (0-3) + anchor registry |
| `graph_traversal_engine/` | Full query engine: Structure + Dynamics + Geometry + Narrative (7 modules) |
| `opinion_ontology.py` | `OntologyQuery` with WVS dataset support |
| `scripts/debug/build_wvs_kg_ontology.py` | Build WVS KG + fingerprints from sweep data |
| `scripts/debug/build_wvs_kg_per_wave.py` | Per-wave KG ontologies (W3-W7) |
| `scripts/debug/compute_gte_camps.py` | Fiedler bipartition from weight matrices |
| `scripts/debug/compute_gte_fingerprints.py` | SES fingerprints (slim Time Series loader for W3-W6) |

---

## Sweep Results Summary

### Post-Realignment (2026-03-26)

| Sweep | Contexts | Estimates | Sig% | Med |gamma| | Runtime |
|-------|----------|-----------|------|---------|---------|
| MEX W7 within-survey | 1 | 982 | 40.2% | 0.008 | 10 min |
| Geographic (W7, 66 countries) | 66 | 68,174 | 39.4% | 0.012 | ~14 hr |
| Temporal (MEX, W3-W7) | 5 | 2,334 | 41.5% | 0.013 | 42 min |
| All-wave gamma-surface | 225 | 123,000+ | ~40% | -- | -- |

### SES Dominance

| Dimension | Los_mex | WVS Global |
|-----------|---------|------------|
| Education | 73.2% | 57.8% |
| Age/Cohort | 2.4% | 33.5% |
| Urbanization | 21.2% | 8.0% |
| Gender | 3.3% | 0.5% |

Key insight: Age/cohort is 2.4% of bridges in Mexico but 33.5% globally.

---

## Data Files

### Tracked (committed)
- `data/wvs/F00003844-WVS_Time_Series_List_of_Variables_and_equivalences_1981_2022_v3_1.xlsx` -- variable equivalences
- `data/wvs/F00012255-WVS_TimeSeries_1981_2020_CountrySpecificCodes.xlsx` -- country codes
- `data/wvs/WVS_Countries_in_time_series_1981-2022.xlsx` -- country participation
- `data/wvs/WVS7_Master_Questionnaire_2017-2020_English.pdf` -- Wave 7 questionnaire
- `data/wvs/WVS7_Questionnaire_Mexico_2018_Spanish.pdf` -- Mexico-specific questionnaire
- `data/wvs/F00017184-WVS_Time_Series_1981_2022_Variables_Report_v5.0.pdf` -- variable report
- `data/wvs/wvs_var_forgob.xlsx` -- user's custom variable selection

### Gitignored (must exist locally)
- `data/wvs/F00011356-WVS_Cross-National_Wave_7_csv_v6_0.zip` (~20MB) -- Wave 7 individual-level data
- `data/wvs/F00011931-WVS_Time_Series_1981-2022_csv_v5_0.zip` (~118MB) -- Longitudinal dataset, waves 1-7
- `data/wvs/wvs_mex_dict.json` -- Generated cache (output of `WVSLoader`)

Download from https://www.worldvaluessurvey.org/ -- "WVS Cross-National Wave 7" and "WVS Time-Series".

### In navegador_data repo
- `data/results/wvs_geographic_sweep_w7.json` -- 68K estimates, 29MB
- `data/results/wvs_temporal_sweep_mex.json` -- 2.3K estimates, 31K lines
- `data/results/wvs_all_wave_gamma_surface.json` -- 123K estimates, 49MB
- `data/tda/allwave/matrices/W{3-7}/` -- Per-country per-wave weight/distance CSVs
- `data/gte/` -- Camps and fingerprints
- `data/tda/message_passing/` -- ~310 MP JSON files

---

## Data Compatibility (validated 2026-03-13, SES realigned 2026-03-26)

### SES Variable Alignment

All 4 bridge variables produce identical value ranges after harmonization and realignment:

| SES var | WVS source | los_mex | Post-realignment notes |
|---------|-----------|---------|----------------------|
| sexo | Q260 (direct: 1=M, 2=F) | sexo | Identical |
| edad | Q262 (continuous numeric) | edad (continuous numeric) | Was 7-bin; now continuous age passed to ordered logit |
| escol | Q275 (ISCED 0-8 to 5-level) | escol (1-5) | ISCED 0=1 (Ninguna), 1=2 (Primaria) separated |
| Tam_loc | G_TOWNSIZE (8 to 4-level) | Tam_loc (1-4) | Los_mex reversed: 1=rural, 4=urban (matches WVS) |

### Sentinel handling
- WVS: negative values (-1 to -5) cleaned to NaN by `wvs_loader.clean_sentinels()` at load time
- los_mex: values >= 97 filtered by `ses_regression._is_sentinel()` at estimation time

### Weight columns
- WVS: `W_WEIGHT` (mean=1.0, range 0.63-1.54)
- los_mex: `Pondi2`
- Unified to `bridge_weight` in `wvs_ses_bridge.py` via `_unify_weight_col()`

---

## Critical: Wave 7 vs Time-Series Column Conventions

The Wave 7 CSV and Time-Series CSV use completely different column naming conventions:

| Feature | Wave 7 CSV | Time-Series CSV |
|---------|-----------|----------------|
| Wave ID | `A_WAVE` | `S002VS` |
| Country | `B_COUNTRY_ALPHA` | `COUNTRY_ALPHA` |
| Weight | `W_WEIGHT` | `S017` |
| Sex | `Q260` | `X001` |
| Age | `Q262` | `X003` |
| Education | `Q275` | `X025` / `X025A_01` |
| Town size | `G_TOWNSIZE` | `X049` |
| Attitude variables | Q-codes (`Q1`, `Q71`) | A-codes (`A001`, `E069_11`) |

Handled by: `wvs_loader._normalize_timeseries_columns()` (renames to W7 convention) and `wvs_ses_bridge._resolve_col()` (resolves any column identifier).

---

## Per-Wave Data Coverage (GTE All-Waves)

| Wave | Year | Countries | Constructs | Camps | Fingerprints | BP | Spectral | PPR |
|------|------|-----------|-----------|-------|-------------|----|---------|----|
| W3 | 1996 | 38 | 24 | 38 | 38 | 38 | 38 | 38 |
| W4 | 2000 | 27 | 25 | 27 | 27 | 27 | 27 | 27 |
| W5 | 2007 | 43 | 31 | 43 | 43 | 43 | 43 | 43 |
| W6 | 2012 | 47 | 44 | 47 | 47 | 47 | 47 | 47 |
| W7 | 2018 | 66 | 55 | 66 | 66 | 66 | 66 | 66 |

---

## Mexico Data Summary

| Wave | Period | n (Mexico) | Source |
|------|--------|-----------|--------|
| 1 | 1981-1984 | 1,837 | Time-Series CSV |
| 2 | 1990-1994 | 1,531 | Time-Series CSV |
| 3 | 1995-1998 | 1,510 | Time-Series CSV |
| 4 | 1999-2004 | 1,535 | Time-Series CSV |
| 5 | 2005-2009 | 1,560 | Time-Series CSV |
| 6 | 2010-2014 | 2,000 | Time-Series CSV |
| 7 | 2017-2022 | 1,741 | Wave 7 CSV |
| **Total** | | **11,714** | |

---

## Remaining Work

### Agent Integration (not yet wired)

- Wire `GraphTraversalEngine` + `OntologyQuery` + `BayesianMultiHopPredictor` into `agent.py` as LangGraph tools
- Register WVS in `dataset_knowledge.py`
- Embed WVS questions in `variable_selector.py` ChromaDB
- Dashboard integration: network visualizations + prediction engine + cross-wave comparison

### Full Bayesian Prediction

- Export ordered-logit theta/beta from Julia sweep for `multi_hop_prediction.py`
- Currently derives sigma from CIs; full 200 bootstrap draws/pair (~157 MB) requires Julia modification

---

## Known Issues / Technical Debt

1. **`_resolve_col()` is O(n) per call** -- iterates full equivalences DataFrame (1048 rows). Pre-build lookup dict for sweep scripts.

2. **Time-series data is column-heavy** -- Each wave slice retains all 1046 time-series columns even though most are NaN. Slim loader (`compute_gte_fingerprints.py`) reads only ~240 columns needed.

3. **Income variable excluded** -- WVS has Q288 (income scale, 10 levels) but excluded per v3 optimization (30-40% coverage). Consistent with los_mex treatment.

4. **Cross-wave construct overlap** -- W3=24, W7=55 constructs. Cross-wave comparisons restricted to intersection (~20-24 shared constructs).

5. **Pre-computed BP only for W7** -- Other waves require on-the-fly PPR/spectral (fast: ~3ms for 55-node graph) but lack pre-computed BP lift matrices.
