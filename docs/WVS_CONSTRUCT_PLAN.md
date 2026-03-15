# WVS Construct Discovery Plan

## Status baseline (2026-03-13)

Already built (other Claude instance, 135 unit tests passing):
- `wvs_loader.py` — loads Wave 7 + Time Series CSVs, filters to Mexico, harmonizes SES, caches
- `wvs_metadata.py` — DOMAIN_MAP, CULTURAL_ZONES, SES_VARS harmonization config, load_equivalences()
- `wvs_ses_bridge.py` — WVSBridgeEstimator wrapping DoublyRobustBridgeEstimator; temporal_sweep(), geographic_sweep()
- `wvs_anchor_discovery.py` — ChromaDB-based anchor question discovery pipeline

**This plan covers only what remains: construct discovery, validation, and comparison to los_mex.**

---

## Phase 1: WVS Variable Inventory

### 1.1 What we're working with

| Source | Records | Notes |
|--------|---------|-------|
| Wave 7 CSV (Mexico) | 1,741 respondents | Primary for construct building |
| Time Series CSV (Mexico) | 11,714 across 7 waves | For temporal validation |
| Y-prefix derived indices | 37 | Team-validated scales — use as gold standard |
| Wave 7 Spanish questionnaire | PDF | Source of question text for LLM prompts |
| Variable equivalences XLSX | 1,048 vars | A-code ↔ Q-code mapping |

### 1.2 Variable scope for construct discovery

Focus on **substantive Wave 7 Q-codes** (excluding SES/admin/derived):

| WVS Domain | Prefix | Wave 7 vars | Priority | Overlapping los_mex domains |
|------------|--------|-------------|----------|-----------------------------|
| Social Values | A | 60 | High | IDE (identidad y valores) |
| Work/Employment | C | 18 | Medium | ECO |
| Family | D | 18 | High | FAM, ENV |
| Politics & Society | E | 134 | Very High | CUL, FED, JUS, COR |
| Religion & Morale | F | 36 | Very High | REL |
| National Identity | G | 25 | High | IDE, GLO, MIG |
| Security | H | 28 | High | SEG, COR |
| Science & Tech | I | 2 | Low | CIE, SOC |
| **Total substantive** | | **~321** | | |
| SES/Demographics | X | 29 | Excluded (bridge vars) | |
| Derived Indices | Y | 37 | Validation only | |

### 1.3 Exclusion rules

Exclude from construct discovery:
- All X-prefix (SES variables — used for bridge, not constructs)
- All Y-prefix (pre-built team indices — use as validation, not building blocks)
- Admin columns: `A_WAVE`, `A_YEAR`, `B_COUNTRY`, `N_REGION_*`, `W_WEIGHT`, `PWGHT`
- Items with N_valid (Mexico Wave 7) < 200 after sentinel removal

### 1.4 Output

Script: `scripts/debug/wvs_variable_inventory.py`
Output: `data/results/wvs_variable_inventory.md`
Content: per-variable name, question text (from equivalences title), N_valid Mexico W7, existing Y-index membership

---

## Phase 2: WVS SVS — LLM Construct Clustering

### 2.1 Goal

Produce `data/results/wvs_svs_v1.json` — same schema as `semantic_variable_selection_v4.json` — using the same 3-step LLM pipeline applied to los_mex.

### 2.2 Input format difference

los_mex had thematic surveys (26 separate questionnaires). WVS is one omnibus questionnaire. Strategy: **treat WVS domain prefixes as the thematic grouping unit** (A, C, D, E, F, G, H, I), processing one domain at a time.

### 2.3 LLM pipeline (adapting los_mex SVS v4 approach)

**Step 1 — Construct clustering per domain**

For each WVS domain, feed LLM:
- Domain name + description
- All Q-codes with Spanish question text + answer scale (from PDF / equivalences)
- N_valid for each item (Mexico Wave 7)

LLM outputs: construct clusters (name + description + list of Q-codes + reverse_coded_items)

Prompt template mirrors SVS v4 step 1. Key differences:
- Use WVS Q-code as item identifier (not los_mex `p1_2` style)
- Items have 4-10 answer options instead of los_mex's 2-7
- Some WVS items have country-specific skip patterns — flag low-N items

**Step 2 — Research review**

Same as SVS v4 step 2: feed construct list back to LLM for:
- Coherence check (is this construct meaningful in Mexico?)
- Cross-reference with academic literature (WVS Y-indices, Welzel/Inglehart scales)
- Flag constructs that map onto validated Y-prefix indices → mark for direct comparison

**Step 3 — Variable strategy**

Same as SVS v4 step 3: for each construct, determine:
- `construct_type`: reflective_scale | single_item_tier2 | formative_index
- `gateway_items`: items that route respondents to sub-batteries (WVS uses many)
- `reverse_coded_items`: items where high score = low construct

### 2.4 Expected output structure

```json
{
  "version": "wvs_v1",
  "source": "WVS Wave 7 (Mexico, 2018)",
  "domains": {
    "WVS_E": {
      "survey_name": "Politics & Society",
      "construct_clusters": [
        {
          "name": "institutional_trust",
          "description": "Trust in major political and social institutions",
          "question_cluster": ["Q65", "Q69", "Q71", "Q72", "Q73"],
          "reverse_coded_items": [],
          "gateway_items": [],
          "construct_type": "reflective_scale"
        }
      ]
    }
  }
}
```

### 2.5 Domain keys

Use 3-character keys prefixed with `WVS_` to distinguish from los_mex domain codes:
`WVS_A`, `WVS_C`, `WVS_D`, `WVS_E`, `WVS_F`, `WVS_G`, `WVS_H`, `WVS_I`

---

## Phase 3: Build WVS Construct Variables

### 3.1 Script: `scripts/debug/build_wvs_constructs.py`

Adapts `build_construct_variables.py` for WVS. Key differences:

| Aspect | los_mex | WVS |
|--------|---------|-----|
| Sentinel detection | `>= 97 or < 0` | `< 0` only |
| Item scale | Varies (2-7 categories) | Varies (2-10 categories) |
| Output scale | [1, 10] | [1, 10] (same) |
| Survey dataframe key | `enc_dict[survey_name]` | `wvs_enc_dict['WVS_W7_MEX']` |
| Column prefix | `agg_` | `wvs_agg_` |
| Reverse coding | Max - value + Min | Same |

The script reads `wvs_svs_v1.json` and builds `wvs_agg_*` columns in the Mexico Wave 7 dataframe.

### 3.2 Output

- `data/results/wvs_construct_manifest.json` — per-construct metadata: key, column, n_valid, alpha, type
- `data/results/build_wvs_constructs.log` — build log with alpha values and warnings

### 3.3 Quality thresholds (same as los_mex)

| Tier | Condition |
|------|-----------|
| good | α ≥ 0.70 |
| questionable | α 0.50–0.69 |
| tier3_caveat | α < 0.50 |
| single_item_tier2 | 1 item (use directly) |
| formative_index | additive count |

**WVS constructs are expected to score better** — WVS is purpose-built for cross-national scale validation. Target: 40-50% "good" tier vs los_mex's 16%.

---

## Phase 4: Semantic Coherence Review (LLM)

### 4.1 Script: `scripts/debug/wvs_semantic_coherence_review.py`

Adapts `semantic_coherence_review.py` for WVS. Changes:
- Uses `wvs_svs_v1.json` and `wvs_overrides.json` (if needed) instead of SVS v4 + v5_overrides
- Item text comes from WVS equivalences XLSX `title` column + Spanish questionnaire PDF
- Same LLM: `claude-haiku-4-5-20251001` — fast, cheap, good at item-level judgments
- Same output schema: COHERENT / MIXED / INCOHERENT per construct, FLAG/OK per item
- Same caching mechanism

### 4.2 Output

- `data/results/wvs_semantic_coherence_v1.md` — per-construct report
- `data/results/wvs_semantic_coherence_v1.json` — machine-readable

### 4.3 Override file: `data/results/wvs_construct_overrides.json`

Same structure as `construct_v5_overrides.json`:
```json
{
  "excluded": {"WVS_I|tech_attitudes": "Only 2 items, both bridge to CIE"},
  "items_to_drop": {"WVS_E|institutional_trust": ["Q68"]},
  "reverse_coded_overrides": {},
  "construct_type_overrides": {}
}
```

---

## Phase 5: Academically Validated WVS Indices

### 5.1 Y-prefix derived indices (team-built, in WVS data)

The WVS team pre-computes 37 derived indices (Y001–Y037). These are the **ground truth** for comparison. Key ones relevant to our domains:

| Y-code | Name | Domain | Reference |
|--------|------|--------|-----------|
| Y001 | Post-Materialist values (4-item) | A, E | Inglehart (1977) |
| Y002 | Post-Materialist values (12-item) | A, E | Inglehart (1997) |
| Y003 | Autonomy index | A | Welzel (2013) |
| Y010 | Religiosity index | F | Various |
| Y011 | Emancipative Values Index | A, D, E | Welzel (2013) |
| Y012 | Secular values | F, A | Inglehart & Welzel (2005) |
| Y020–Y024 | Sub-indices of emancipative values | A, D, E | Welzel (2013) |

**Action**: Run `wvs_variable_inventory.py` to dump all Y-index values and their constituent Q-codes. Compare to our LLM-discovered construct clusters.

### 5.2 Key academic references

Full bibliography with complete item codes: **`docs/WVS_VALIDATED_INDICES.md`**

Summary of 18 validated indices found (all with Wave 7 Q-code ↔ A-code cross-walk):

| Domain | Validated index | Key reference | Relevant WVS items |
|--------|----------------|---------------|--------------------|
| A (Social) | Traditional/Secular-Rational | Inglehart & Welzel (2005) | F034, A006, E018, A042 |
| A (Social) | Survival/Self-Expression | Inglehart & Welzel (2005) | A165, E025, F118 |
| A (Social) | Post-Materialist (Y001/Y002) | Inglehart (1971, 1977) | E001–E004 |
| A (Social) | Emancipative Values (EVI) | Welzel (2013) | A029, A038, A040 |
| A+D+E | EVI sub-indices (Autonomy/Equality/Choice/Voice) | Welzel (2013) | 12 items across 4 domains |
| C+D (Work/Family) | Gender Egalitarianism | Inglehart & Norris (2003) | C001, D059, D060, D061 |
| E (Politics) | Confidence in Institutions | Newton & Norris (2000) | E069_01–E069_63 |
| E (Politics) | Political Trust | Zmerli & Newton (2008) | E069_05/06/17, A165 |
| E (Politics) | Autocracy Support | Foa & Mounk (2016) | E114, E115, E123 |
| F (Religion) | Religiosity composite | Norris & Inglehart (2004) | F028, F029, F034, F024, F025 |
| A (Social) | Social Capital | Bjørnskov (2006) | A165, A098–A106, E025–E027 |
| A (Social) | Subjective Well-Being | Inglehart et al. (2008) | A008 (Q46), A170 (Q49) |
| B (Environment) | Environmental Concern | Knight (2016) | B001–B004 |

**Key insight**: Our LLM construct clustering will have direct academic comparators for most domains. EVI (12 items) and Confidence in Institutions (14+ institutions) provide the richest validation targets.

### 5.3 Comparison method

For each WVS construct we build, check:
1. **Does it map to a Y-index?** If yes: compute Spearman ρ(wvs_agg_*, Y_index). Target ρ > 0.7 for convergent validity.
2. **Is the construct named in an academic paper?** If yes: note the reference in manifest.
3. **Divergences**: constructs we find that have no academic equivalent → novel contributions or noise.

Script: `scripts/debug/wvs_validate_against_yindex.py`
Output: `data/results/wvs_yindex_validation.md`

---

## Phase 6: Cross-Dataset Comparison (WVS ↔ los_mex)

### 6.1 Within-WVS DR sweep (Mexico Wave 7)

Run `sweep_construct_dr.py` equivalent on WVS constructs:
- All pairs of `wvs_agg_*` columns within Mexico Wave 7 dataset
- Expected: fewer pairs (WVS constructs per domain 4-8 vs los_mex's 4-8), but richer construct quality
- N per dataset = 1,741 — slightly larger than los_mex's ~1,200. CI widths should be comparable.

Script: `scripts/debug/sweep_wvs_construct_dr.py` (adapt sweep_construct_dr.py)
Output: `data/results/wvs_construct_dr_sweep.json`

### 6.2 Cross-dataset bridge sweep (WVS Mexico × los_mex)

Use `WVSBridgeEstimator.estimate_cross_dataset()` (already implemented in wvs_ses_bridge.py):
- For each anchor pair (WVS construct, los_mex construct) with semantic overlap ≥ threshold
- Run doubly robust estimation using shared SES space (sexo/edad/escol/Tam_loc harmonized)

**Anchor pair discovery**: `wvs_anchor_discovery.py` already has ChromaDB pipeline for this. Adapt to work at construct-level (compare `wvs_agg_*` descriptions to `agg_*` descriptions).

### 6.3 Temporal sweep (Mexico, 7 waves)

For constructs that are stable across waves (questions in waves 5-7 minimum):
- Run `WVSBridgeEstimator.temporal_sweep()` to get γ(wave) for Mexico
- Expected: captures value change 2005→2018 (waves 5-7)
- Compare to known trends: rising secularization, declining institutional trust post-2010

**Wave coverage**: Temporal sweep is feasible ONLY for items with equivalences in target waves.
From the inventory (Phase 1):
- A domain: 18/56 items in all 7 waves (social values, child qualities)
- E domain: 19/132 items in all 7 waves (politics — core trust battery stable since Wave 1)
- F domain: 15/33 items in all 7 waves (religion — core practice items stable)
- C/D/G/H: 0-1 items in all 7 waves

Strategy: constructs where ALL items are in at least waves 3-7 → full sweep for Mexico.
For items available only in Wave 7 → skip temporal sweep (document in manifest).
The time-series CSV (11,714 Mexico respondents across 7 waves) provides the longitudinal data.
`WVSBridgeEstimator.temporal_sweep()` handles this; filter by construct's `wave_coverage` in manifest.

Output: `data/results/wvs_temporal_sweep_mex.json` + line plots

### 6.4 Network integration

Combine los_mex construct network (construct_network.png) with WVS constructs:
- Nodes: all WVS constructs + all los_mex constructs
- Edges: (1) within-los_mex significant pairs [existing], (2) within-WVS significant pairs [new], (3) cross-dataset significant anchor pairs [new]
- Color code: los_mex blue, WVS green, cross-dataset edges orange
- Output: `data/results/combined_construct_network.png`

---

## Implementation order

| Step | Script | Input | Output | Prerequisite |
|------|--------|-------|--------|--------------|
| 1 | `wvs_variable_inventory.py` | WVS W7 CSV + equivalences XLSX | `wvs_variable_inventory.md` | wvs_loader.py works |
| 2 | Manual / LLM | Inventory + PDF | `wvs_svs_v1.json` | Step 1 |
| 3 | `build_wvs_constructs.py` | `wvs_svs_v1.json` | `wvs_agg_*` columns, manifest | Step 2 |
| 4 | `wvs_semantic_coherence_review.py` | manifest + equivalences | `wvs_semantic_coherence_v1.md` | Step 3 |
| 5 | `wvs_validate_against_yindex.py` | `wvs_agg_*` + Y-indices | `wvs_yindex_validation.md` | Step 3 |
| 6 | `sweep_wvs_construct_dr.py` | `wvs_agg_*` | `wvs_construct_dr_sweep.json` | Step 3 |
| 7 | `wvs_anchor_discovery.py` (construct-level) | both manifests + ChromaDB | `wvs_anchor_pairs.json` | Steps 3,4 |
| 8 | Cross-dataset sweep | anchor pairs + WVSBridgeEstimator | `wvs_cross_dataset_sweep.json` | Steps 6,7 |
| 9 | Combined network plot | steps 1+6+8 | `combined_construct_network.png` | Steps 6,8 |

---

## Notes on WVS construct quality expectations

WVS questionnaire design advantages over los_mex thematic surveys:
1. **Purpose-built scales**: Many WVS batteries are explicitly designed as multi-item scales (e.g., E069 trust battery has 12+ institutions). los_mex sometimes has isolated items that were never meant to be aggregated.
2. **Consistent answer formats**: WVS uses standardized 1-4 and 1-10 scales. los_mex uses survey-specific varying scales (2-7 categories).
3. **Prior validation**: WVS constructs have been validated across 100+ countries over 40 years. Internal consistency is structurally better.
4. **Academic precedent**: Researchers routinely build scales from WVS batteries (see §5.2). Our LLM search can be cross-validated against published usage.

Expected outcomes:
- WVS constructs: 40-60% "good" tier (α ≥ 0.70) vs los_mex 16%
- More overlap between LLM-discovered clusters and Y-prefix validated indices
- Tighter CI widths in DR sweep (larger N + better construct reliability)

---

## Open questions to resolve before implementation

1. **wvs_loader.py status**: Does `wvs_enc_dict` currently expose Mexico Wave 7 with the Q-code columns as-is, or are they already mapped to A-codes? This affects which column names `build_wvs_constructs.py` should expect.

2. **Spanish question text source**: The equivalences XLSX has English `title` column. The Spanish questionnaire PDF is available (`WVS7_Questionnaire_Mexico_2018_Spanish.pdf`) but needs parsing. For the LLM construct clustering, we want Spanish text. Options:
   - Parse PDF with pdfminer/pypdf2 → map Q-codes to Spanish text
   - Use English text from equivalences (faster, loses nuance)
   - Use Google Translate on equivalences titles (cheapest)

3. **Gateway items in WVS**: WVS has filter/routing questions (e.g., Q96 "Do you belong to a religion?" gates Q98-Q101). The `wvs_variable_inventory.py` script should flag these — their N_valid will be systematically lower for non-religious respondents, not random missingness.

4. **Country pooling for temporal sweep**: Mexico alone gives N≈1,500-2,000 per wave. For Latin America pooling (N≈8,000-15,000 per wave), SES-reference must be standardized. The `WVSBridgeEstimator.geographic_sweep()` handles this but needs the standardized reference population defined.
