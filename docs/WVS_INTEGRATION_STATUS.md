# WVS Integration Status

Last updated: 2026-03-13

This file tracks the implementation state, known issues, data compatibility findings, and next steps for integrating the World Values Survey (WVS) into Navegador's SES bridge framework. It is intended to be read by any Claude instance continuing this work.

For the full conceptual plan (γ-surface formulation, anchor questions, cultural zones), see [WVS_INTEGRATION_PLAN.md](WVS_INTEGRATION_PLAN.md).

---

## Phase Status

| Phase | Description | Status | Notes |
|-------|------------|--------|-------|
| 1 | Data Ingestion | **Complete** | `wvs_loader.py`, `wvs_metadata.py` — loads Wave 7 and time-series CSVs |
| 2 | Anchor Discovery | Code exists, **not run on real data** | `wvs_anchor_discovery.py` — needs ChromaDB embeddings + LLM API calls |
| 3 | SES Bridge & γ Surface | Code exists, **not run on real data** | `wvs_ses_bridge.py` — WVSBridgeEstimator, temporal/geographic sweeps |
| 4 | Surface Analysis | **Not started** | Temporal gradients, geographic gradients, compositional decomposition |
| 5 | Agent Integration | **Not started** | dataset_knowledge.py, variable_selector.py, survey_kg.py, analytical_essay.py |

**Tests:** 135 unit tests in `tests/unit/test_wvs_integration.py`, all passing (synthetic data, no API calls).

---

## Module Map

| Module | Lines | Purpose |
|--------|-------|---------|
| `wvs_metadata.py` | 282 | Constants (`SES_VARS`, `CULTURAL_ZONES`, `DOMAIN_MAP`, `WAVE_LABELS`), parse equivalences XLSX |
| `wvs_loader.py` | ~570 | `WVSLoader`: load CSVs from zip, sentinel cleaning, SES harmonization, build `wvs_dict` |
| `wvs_ses_bridge.py` | ~560 | `WVSBridgeEstimator`: cross-dataset γ, temporal sweep, geographic sweep; `SESHarmonizer`; `_resolve_col()` |
| `wvs_anchor_discovery.py` | 454 | `WVSAnchorDiscovery`: ChromaDB vector search → LLM grading (0-3) → anchor registry |
| `tests/unit/test_wvs_integration.py` | 1153 | 135 tests covering all phases (synthetic data) |

---

## Data Files

### Tracked (committed)
- `data/wvs/F00003844-WVS_Time_Series_List_of_Variables_and_equivalences_1981_2022_v3_1.xlsx` — variable equivalences
- `data/wvs/F00012255-WVS_TimeSeries_1981_2020_CountrySpecificCodes.xlsx` — country codes
- `data/wvs/WVS_Countries_in_time_series_1981-2022.xlsx` — country participation
- `data/wvs/WVS7_Master_Questionnaire_2017-2020_English.pdf` — Wave 7 questionnaire
- `data/wvs/WVS7_Questionnaire_Mexico_2018_Spanish.pdf` — Mexico-specific questionnaire
- `data/wvs/F00017184-WVS_Time_Series_1981_2022_Variables_Report_v5.0.pdf` — variable report
- `data/wvs/wvs_var_forgob.xlsx` — user's custom variable selection

### Gitignored (must exist locally)
- `data/wvs/F00011356-WVS_Cross-National_Wave_7_csv_v6_0.zip` (~20MB) — Wave 7 individual-level data
- `data/wvs/F00011931-WVS_Time_Series_1981-2022_csv_v5_0.zip` (~118MB) — Longitudinal dataset, waves 1-7
- `data/wvs/wvs_mex_dict.json` — Generated cache (output of `WVSLoader`)

Download from https://www.worldvaluessurvey.org/ — "WVS Cross-National Wave 7" and "WVS Time-Series".

---

## Data Compatibility (validated 2026-03-13)

### SES Variable Alignment

All 4 bridge variables produce **identical value ranges** in WVS and los_mex after harmonization:

| SES var | WVS (Wave 7) | WVS (Time-Series) | los_mex | Values | Coverage |
|---------|-------------|-------------------|---------|--------|----------|
| sexo | Q260 | X001 | sexo | {1, 2} | 100% both |
| edad | Q262 → binned | X003 → binned | edad | {'0-18','19-24','25-34','35-44','45-54','55-64','65+'} | 99.9% WVS, 100% los_mex |
| escol | Q275 (ISCED 0-8) → 5-level | X025 → 5-level | escol (1-5) | {1.0, 2.0, 3.0, 4.0, 5.0} | 99.5% WVS, 100% los_mex |
| Tam_loc | G_TOWNSIZE (1-8) → 4-level | X049 → 4-level | Tam_loc (1-4) | {1.0, 2.0, 3.0, 4.0} | 99.0% WVS, varies los_mex |

### Minor dtype difference
- `sexo`: WVS produces `int64`, los_mex produces `float64`
- **Not a problem**: `SESEncoder` in `ses_regression.py` casts to `str` internally (line 323: `df['sexo'].astype(str).str.strip()`)

### Sentinel handling
- WVS: negative values (-1 to -5) → cleaned to NaN by `wvs_loader.clean_sentinels()` at load time
- los_mex: values ≥ 97 → filtered by `ses_regression._is_sentinel()` at estimation time
- Both approaches work correctly; no cross-contamination

### Weight columns
- WVS: `W_WEIGHT` (mean=1.0, range 0.63-1.54)
- los_mex: `Pondi2`
- Unified to `bridge_weight` in `wvs_ses_bridge.py` via `_unify_weight_col()`

---

## Critical: Wave 7 vs Time-Series Column Conventions

The Wave 7 CSV and Time-Series CSV use **completely different column naming conventions**:

| Feature | Wave 7 CSV | Time-Series CSV |
|---------|-----------|----------------|
| Wave ID | `A_WAVE` | `S002VS` |
| Country | `B_COUNTRY_ALPHA` | `COUNTRY_ALPHA` |
| Country (numeric) | `B_COUNTRY` | `S003` |
| Weight | `W_WEIGHT` | `S017` |
| Sex | `Q260` | `X001` |
| Age | `Q262` | `X003` |
| Education | `Q275` | `X025` |
| Town size | `G_TOWNSIZE` | `X049` |
| Attitude variables | Q-codes (`Q1`, `Q71`, `Q173`) | A-codes (`A001`, `E069_11`, `F034`) |

### How this is handled

1. **`wvs_loader._normalize_timeseries_columns()`** — renames administrative and SES columns from time-series convention to Wave 7 convention before any processing
2. **`wvs_ses_bridge._resolve_col()`** — resolves any column identifier (Q-code or A-code) to the actual column name present in a DataFrame, using the equivalences table

### Q-code collision warning
Q-codes are **NOT unique across variables** — different WVS variables can have the same Q-code in different waves (e.g., `Q173` means "Religious person" in Wave 7 but could mean something else in Wave 4). The resolver prioritizes Wave 7 Q-code matches to avoid mismatches. When calling `temporal_sweep()` or `geographic_sweep()`, always pass `equivalences=wvs_dict['var_equivalences']`.

---

## Performance Notes

- **Wave 7 only:** ~4s to load (20MB zip, 1741 rows × 617 cols)
- **Time-series CSV:** ~47s to load first time (118MB zip → 1.3GB uncompressed)
- **All 7 Mexico waves:** ~52s with caching (was 279s without caching)
- **Caching:** `WVSLoader._timeseries_cache` holds the full time-series DataFrame in memory after first load. Reuse the same `WVSLoader` instance when loading multiple waves.

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

All 7 waves have all 4 SES variables successfully harmonized.

---

## Next Steps

### Immediate (Phase 3 validation)

1. **Run pilot WVS×los_mex cross-dataset bridge** — Pick a known-strong pair (e.g., WVS Q71 "Confidence: Government" × los_mex p16_3|CUL trust item). Verify `WVSBridgeEstimator.estimate_cross_dataset()` produces sensible γ with reasonable CIs. Use `n_bootstrap=50` for speed.

2. **Run pilot temporal sweep** — Pick a variable pair present across multiple Mexico waves (e.g., A008 "Feeling of happiness" × F034 "Religious person" — present in all 7 waves). Verify `temporal_sweep()` with `equivalences=wvs_dict['var_equivalences']` resolves columns correctly across waves and produces γ(t).

3. **Validate SES bridge calibration** — Compare WVS Mexico Wave 7 SES marginals (P(escol), P(edad), etc.) with los_mex marginals. If systematically different, the bridge may need calibration correction.

### Phase 2 (Anchor Discovery — requires API access)

4. **Embed WVS question texts in ChromaDB** — Extract Spanish text from `WVS7_Questionnaire_Mexico_2018_Spanish.pdf`, embed alongside los_mex questions in the existing ChromaDB collection.

5. **Run anchor matching sweep** — For each WVS question, find nearest los_mex neighbors. LLM-grade (0-3) the top candidates.

6. **Build anchor registry** — Curated JSON of Grade 2-3 anchor pairs with scale harmonization notes.

### Phase 3 (Full γ-surface)

7. **WVS×los_mex sweep** — Run `DoublyRobustBridgeEstimator` on all cross-dataset pairs (WVS Wave 7 × 26 los_mex surveys). Use sweep script pattern from `scripts/debug/sweep_dr_highci.py` (atomic checkpointing, per-pair timeout).

8. **Temporal sweep** — γ(variable_pair, MEX, wave_i, local) for all 7 waves for key variable pairs. Requires ~20 core variables present across all waves (see Section 8.1 of `WVS_INTEGRATION_PLAN.md`).

9. **Geographic sweep** — γ(variable_pair, country_j, wave7, local) for Latin American countries. Requires loading multi-country Wave 7 data.

### Phase 4 (Surface Analysis)

10. **Temporal gradients** — Detect variable pairs with steepest Δγ across waves.
11. **Compositional vs structural decomposition** — Compare local-reference γ with standardized-reference γ.
12. **γ-profile rankings** — Spearman ρ on γ-rankings across countries.

### Phase 5 (Agent Integration)

13. **Register WVS in `dataset_knowledge.py`** — Add WVS surveys to `enc_dict`, `enc_nom_dict`, `pregs_dict`.
14. **Embed WVS questions in `variable_selector.py`** — ChromaDB collection alongside los_mex.
15. **Extend `survey_kg.py`** — Add WVS domain nodes with cross-links to los_mex domains.
16. **Update `analytical_essay.py`** — Handle WVS data in essay generation pipeline.

---

## Known Issues / Technical Debt

1. **`_resolve_col()` is O(n) per call** — iterates the full equivalences DataFrame (1048 rows) for each resolution. For sweep scripts with thousands of pairs, pre-build a lookup dict instead. Not a problem for single-pair estimation.

2. **Time-series data is column-heavy** — Each wave slice retains all 1046 time-series columns even though most are NaN for that wave (~836 A-code columns, ~200 valid per wave). Consider dropping all-NaN columns per slice in `load_slice()`.

3. **No `wvs_mex_dict.json` cache generated yet** — The `WVSLoader.save()` / `WVSLoader.load()` methods exist but haven't been used. Generating and caching the processed dict would avoid the ~52s load time on subsequent runs.

4. **Anchor discovery not yet run** — The `wvs_anchor_discovery.py` module needs ChromaDB with los_mex embeddings and LLM API access. The 13 candidate anchor pairs in the integration plan are hand-identified; the systematic pipeline hasn't been executed.

5. **Cross-country SES harmonization assumptions** — The ISCED→5-level education mapping assumes all countries' education systems map similarly. The integration plan recommends using the coarser 3-group recoding (X025R/Q275R) for cross-country comparisons.

6. **Income variable excluded** — WVS has Q288 (income scale, 10 levels) but it was excluded from the bridge per v3 optimization (30-40% coverage, causes row loss). This is consistent with los_mex treatment.
