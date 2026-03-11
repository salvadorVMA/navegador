# Construct Identification and Validation Strategy

**Date:** 2026-03-09 (updated)
**Branch:** `feature/bivariate-analysis`
**Status:** Active development

---

## 1. Overview

Navegador maps ~2,400 survey questions from 24 thematic domains of the "Los Mexicanos" survey series into latent **constructs** — coherent groups of questions that measure a single underlying dimension (e.g., "institutional trust," "personal religiosity," "gender role attitudes"). These constructs serve as the atomic units for the bridge estimator network, replacing raw questions with psychometrically grounded variables.

This document describes the construct identification pipeline, its validation methodology, known weaknesses, and the optimization strategies applied.

---

## 2. Pipeline Architecture (5-Step LLM Pipeline)

The construct identification pipeline lives in `scripts/debug/select_bridge_variables_semantic.py` and runs per domain.

### Step 0 — Question Summarization (Claude Haiku)

**Input:** Raw Spanish question text from `los_mex_dict.json`
**Output:** English summary + metadata per question
**Cost:** ~$0.10 per domain

Each question gets a structured English summary capturing: the question's topic, response format, and measurement intent. Summaries are cached in `.semantic_selection_cache/{DOMAIN}_step0_summaries.json`.

### Step 1 — Construct Clustering (Claude Sonnet)

**Input:** All question summaries for a domain + original Spanish text (v2)
**Output:** 5+ construct clusters, each with a name, description, and list of question IDs
**Cost:** ~$0.20 per domain

The LLM groups questions into conceptually coherent clusters. Each cluster should measure a single latent dimension.

**v1 limitation (fixed in v2):** Step 1 originally received only English summaries from Step 0. The Haiku summaries lost nuance from the original Spanish, leading to ~90% of constructs being incorrectly specified. See Section 4.

**v2 fix:** Step 1 now receives both `[ES]` original Spanish and `[EN]` English summary for each question. The prompt explicitly instructs: *"Use the ORIGINAL SPANISH to understand what each question truly asks."*

### Step 1b — Statistical Validation Gate (Local)

**Input:** Proposed clusters from Step 1 + survey DataFrame
**Output:** Cronbach's alpha per cluster, stat_flag annotation

Added in v2. Computes Cronbach's alpha immediately after clustering to flag statistically incoherent clusters early. Informational only — does not reject clusters.

### Step 2 — Research Review (Claude Opus)

**Input:** Each construct cluster
**Output:** Academic validation, causal relationships, data availability notes
**Cost:** ~$0.50 per domain

### Step 3 — Variable Strategy (Claude Sonnet)

**Input:** Validated constructs
**Output:** Aggregation strategy (mean, sum, single-item) per construct
**Cost:** ~$0.15 per domain

### Step 4 — Variable Building (Local)

**Input:** Strategy specifications + survey DataFrames
**Output:** Aggregated construct variables in the data pipeline

---

## 3. Validation Methodology

Validation is implemented in `scripts/debug/validate_constructs.py` with three complementary phases.

### Phase A — Semantic Validation (LLM)

Each construct is audited by Claude Sonnet against its actual survey questions. The LLM evaluates:

| Dimension | Scale | What it measures |
|-----------|-------|------------------|
| `name_accuracy` | 1-5 | Does the name describe what these questions collectively measure? |
| `description_accuracy` | 1-5 | Does the description match the actual questions? |
| `internal_coherence` | 1-5 | Do all questions belong together as measures of one construct? |

Additional outputs: outlier questions, suggested renames, summary accuracy flags, and a verdict (`valid`, `needs_rename`, `needs_restructure`).

### Phase B — Cross-Construct Misassignment (LLM)

All constructs within each domain are reviewed together to identify:
- Questions assigned to the wrong sibling construct
- Orphan questions that don't fit any existing construct
- Domain-level structural issues

### Phase C — Statistical Diagnostics (Local)

Pure computation, no LLM calls. Per construct:

| Metric | Purpose | Threshold |
|--------|---------|-----------|
| **Cronbach's alpha (alpha)** | Internal consistency | >= 0.7 good, >= 0.5 questionable, < 0.5 poor |
| **Mean inter-item Spearman r** | Pairwise correlation strength | >= 0.3 for "good" verdict |
| **PCA variance explained** | Dimensionality | PC1 ratio indicates unidimensionality |
| **Item-total correlation** | Per-item fit | Low r_item_total = misfit item |
| **alpha_if_dropped** | Item pruning guide | Shows alpha improvement from dropping each item |

**Sentinel filtering:** Values >= 97 or < 0 are excluded before all computations.

---

## 4. Root Cause Analysis: Why v1 Constructs Failed

### The Problem

v1 constructs had a mean alpha of ~0.25. Only 5/125 constructs (4%) reached alpha >= 0.7. LLM validation revealed that construct names and descriptions frequently didn't match the actual survey questions.

### Root Cause

**Step 0 (Haiku) summaries degraded question meaning.** Spanish questions were summarized into English by Claude Haiku, which lost nuance, conflated distinct concepts, and occasionally mistranslated. Step 1 (Sonnet) then clustered based on these degraded summaries, not the original questions.

Example: A question about "pride in being Mexican" was summarized as "national sentiment," which got clustered with questions about "flag respect" and "anthem knowledge" — measuring national symbols knowledge, not emotional attachment.

### The Fix (v2)

Step 1 now receives both original Spanish text and English summaries. The prompt includes:

> *"Use the ORIGINAL SPANISH to understand what each question truly asks — the English summary may lose nuance."*

Additionally, Step 1b (statistical validation gate) was added to flag incoherent clusters immediately.

---

## 5. v2 Rebuild Results

All 24 domains were fully rebuilt with the v2 pipeline.

| Metric | v1 | v2 | Change |
|--------|-----|-----|--------|
| Total constructs | 125 | 120 | -5 |
| Good (alpha >= 0.7) | 5 (4%) | 11 (9%) | +120% |
| Questionable (0.5-0.7) | ~15 | 25 (21%) | +67% |
| Poor (alpha < 0.5) | ~105 | 78 (65%) | -26% |
| Mean alpha | ~0.25 | 0.378 | +0.13 |
| Median alpha | ~0.22 | 0.389 | +0.17 |

**Best v2 constructs:**
- FED|legal_uniformity_preference: alpha = 0.948
- FED|perceived_representativeness: alpha = 0.916
- REL|supernatural_beliefs: alpha = 0.900
- CUL|authoritarian_predisposition: alpha = 0.766
- SAL|financial_burden_of_healthcare: alpha = 0.741

While v2 was a significant improvement, 78 constructs (65%) remained statistically poor. Two optimization strategies were developed.

---

## 6. Optimization Strategies

### Strategy 1 — Iterative Item Pruning (Free, Instant)

**Script:** `scripts/debug/optimize_constructs.py --prune-only`

For each poor construct, iteratively drops the worst-fitting item (lowest item-total correlation / highest alpha_if_dropped) until:
- alpha reaches the target (0.5), OR
- only 3 items remain (minimum viable cluster), OR
- no further drop improves alpha

**Rationale:** Many constructs contain 1-2 misfit items that drag down alpha. A question about "frequency of church attendance" in a "personal religiosity" cluster measuring beliefs (not behavior) drops alpha from 0.73 to -0.17. Removing it instantly rescues the construct.

**Results (v2 -> v3 pruning):**

| Metric | v2 | v3 (pruned) | Change |
|--------|-----|-------------|--------|
| Good (alpha >= 0.7) | 11 | 15 | +4 |
| Questionable (0.5-0.7) | 25 | 50 | +25 |
| Poor (alpha < 0.5) | 78 | 55 | -23 |
| Mean alpha | 0.378 | 0.503 | +0.125 |
| Median alpha | 0.389 | 0.511 | +0.122 |

**68 constructs improved**, 29 reached the alpha >= 0.5 target.

**Top rescues:**
| Construct | Before | After | Items dropped |
|-----------|--------|-------|---------------|
| REL\|personal_religiosity | -0.167 | 0.732 | 1 (p18) |
| CUL\|democratic_legitimacy_support | 0.031 | 0.567 | 2 |
| ENV\|assessment_of_older_adult_wellbeing | -0.002 | 0.532 | 5 |
| SAL\|functional_health_status | 0.262 | 0.723 | 1 (p7) |
| DEP\|reading_engagement_and_literacy | 0.138 | 0.623 | 3 |

### Strategy 2 — LLM Re-exploration of Unused Questions

**Script:** `scripts/debug/optimize_constructs.py --reexplore-only`

For the ~55 constructs still poor after pruning, an LLM (Claude Sonnet) reviews all **unused** questions in the same domain and suggests:
1. Questions to **add** that measure the same dimension
2. Current items to **remove** that are clearly misfit
3. Optional name/description updates

**Safeguard:** Every LLM suggestion is statistically verified before application — the change is only applied if Cronbach's alpha actually improves. This prevents LLM hallucination from degrading constructs.

**Key design decisions:**
- Each domain has 14-80 unused questions (median ~30) available for re-exploration
- Both Spanish and English text are provided to the LLM
- Confidence levels (high/medium/low) are logged for audit
- Changes that don't improve alpha are logged but not applied

**Results:**
- 49 constructs sent to LLM for re-exploration (those still poor after pruning)
- 5 LLM suggestions passed statistical verification and were applied
- 44 LLM suggestions were rejected (alpha didn't improve after verification)
- The safeguard prevented any degradation from hallucinated suggestions

**Insight:** Strategy 2's low hit rate (10%) is expected — constructs that survive pruning but remain poor likely have fundamental issues: the domain's available questions simply don't measure a coherent single dimension. The high rejection rate validates the statistical verification safeguard.

### Combined Results (Strategy 1 + Strategy 2)

| Metric | v2 | v3 (combined) | Change |
|--------|-----|---------------|--------|
| Good (alpha >= 0.7) | 11 (9%) | 15 (13%) | +4 |
| Questionable (0.5-0.7) | 25 (21%) | 52 (43%) | +27 |
| Poor (alpha < 0.5) | 78 (65%) | 53 (44%) | -25 |
| Mean alpha | 0.378 | 0.506 | +0.128 |
| Median alpha | 0.389 | 0.516 | +0.127 |
| Degradations | — | 0 | zero |

The majority of improvement came from Strategy 1 (item pruning). Strategy 2 contributed marginally but served as validation that the remaining poor constructs are genuinely irreducible with available questions.

---

## 7. Data Quality Rules

All statistical computations enforce these rules:

| Rule | Implementation |
|------|---------------|
| Sentinel codes (>= 97 or < 0) | Filtered to NaN by `_is_sentinel()` |
| est_civil codes 8, 9 | Remapped to NaN in preprocessing |
| escol codes 9, 98, 99 | Remapped in `preprocess_survey_data()` |
| Tam_loc outside 1-4 | Clipped; out-of-range -> NaN |
| NaN indices in df_tables | Represent skip patterns; filtered before analysis |
| Minimum sample size | 10 valid rows required for any statistic |
| Minimum items | 2 items required for alpha; 3 minimum after pruning |

---

## 8. File Reference

| File | Purpose |
|------|---------|
| `scripts/debug/select_bridge_variables_semantic.py` | 5-step LLM construct pipeline |
| `scripts/debug/validate_constructs.py` | 3-phase validation (semantic + statistical) |
| `scripts/debug/optimize_constructs.py` | Strategy 1 (pruning) + Strategy 2 (re-exploration) |
| `data/results/semantic_variable_selection.json` | v2 constructs (current baseline) |
| `data/results/semantic_variable_selection_v3.json` | v3 constructs (post-optimization) |
| `data/results/semantic_variable_selection_v4.json` | v4 constructs (structural fixes + tier 1 removed) |
| `data/results/construct_validation_report.json` | Phase A/B/C validation results |
| `data/results/construct_optimization_log.json` | Detailed pruning + re-exploration log |
| `data/results/construct_structural_audit.json` | Per-item structural diagnosis |
| `data/results/construct_structural_fixes.json` | Fix application log (reverse coding, categorical removal, etc.) |
| `data/results/.semantic_selection_cache/` | Intermediate pipeline outputs |

---

## 9. Structural Fixes (v4)

After v3 optimization, a structural audit identified six issue categories across 53 constructs: skip-pattern funnels, categorical codes treated as ordinal, mixed binary/ordinal formats, low-coverage conditional items, negative correlations requiring reverse coding, and near-zero inter-item correlations.

### Fixes Applied

| Fix | Constructs affected | Result |
|-----|-------------------|--------|
| Reverse coding | 3 (POB\|subjective_economic_wellbeing +0.115, SOC\|media_trust +0.024, MED\|env_governance +0.024) | alpha gains verified |
| Remove categorical items | 2 (CUL\|democratic_legitimacy +0.015, DEP\|cultural_identity rescued from None to 0.415) | categorical response codes removed |
| Remove low-coverage items | 4 (SOC\|digital_tech_access +0.234, ECO\|human_capital +0.120, EDU\|perceived_ed_quality +0.166) | row coverage restored |
| Formative indices | 5 (SEG\|crime_victimization, COR\|reporting, HAB\|housing_tenure, ECO\|job_search, EDU\|school_env) | reclassified as additive indices |

### Tier 1 Removed (18 constructs)

The following constructs were permanently removed (alpha < 0.3, mean inter-item r near zero, no structural fix available):

| Domain | Construct | alpha | mean_r | Reason |
|--------|-----------|-------|--------|--------|
| POB | perceived_social_inequality_and_discrimination | -0.073 | -0.054 | Items inversely correlated |
| SAL | financial_burden_of_healthcare | -0.036 | 0.003 | 33 valid rows, zero correlation |
| DEP | sports_engagement_and_media_consumption | 0.099 | 0.039 | Categorical + skip pattern, 2 items left |
| HAB | housing_problem_perception | 0.229 | 0.091 | Unrelated items |
| GLO | cosmopolitan_identity | 0.235 | 0.073 | Unrelated items |
| GLO | cultural_openness_to_foreign_influence | 0.236 | 0.099 | Unrelated items |
| GEN | gender_equality_in_public_life | 0.239 | 0.081 | Unrelated items |
| POB | poverty_attribution_and_definition | 0.252 | 0.091 | Unrelated items |
| IND | indigenous_cultural_integration_vs_autonomy | 0.264 | 0.108 | Mixed format, weak |
| COR | institutional_trust_and_efficacy | 0.293 | 0.071 | Near-zero correlations |
| ENV | support_for_elder_friendly_public_policy | 0.296 | 0.063 | Near-zero correlations |
| MIG | perceived_conditions_outcomes_mexican_emigration | 0.302 | 0.043 | Near-zero correlations |
| ENV | perceived_elder_abuse_and_mistreatment | 0.307 | 0.071 | Near-zero correlations |
| EDU | educational_inclusion_equity | 0.310 | 0.045 | Near-zero correlations |
| IDE | social_trust_and_civic_cooperation | 0.317 | 0.112 | Negative pairs, unfixable |
| IND | stereotyping_and_social_image_of_indigenous_people | 0.319 | 0.114 | Only categorical items remain |
| NIN | perceived_child_and_adolescent_violence_exposure | 0.324 | 0.060 | Near-zero correlations |
| MED | environmental_governance_attitudes | 0.325 | 0.108 | Even after reverse coding |

### Remaining Construct Tiers

- **Tier 3 (keep with caveat):** 18 constructs with alpha 0.4-0.5. Usable for group-level exploratory bridge analysis with reliability disclaimer.
- **Tier 2 (demoted):** 14 constructs with alpha 0.3-0.4. Individual items may serve as single-item bridge variables rather than aggregated scales.

### v4 Final Summary

| Metric | v2 | v3 | v4 |
|--------|-----|-----|-----|
| Total constructs | 120 | 120 | 102 (+ 5 formative) |
| Good (alpha >= 0.7) | 11 | 15 | 16 |
| Questionable (0.5-0.7) | 25 | 52 | 49 |
| Poor (alpha < 0.5) | 78 | 53 | 32 |
| Formative index | 0 | 0 | 5 |
| Removed | 0 | 0 | 18 |
| Mean alpha | 0.378 | 0.506 | 0.508 |

---

## 10. Limitations and Future Work

### Current Limitations

1. **Cronbach's alpha assumes tau-equivalence** — items must have equal factor loadings for alpha to be an accurate reliability estimate. For congeneric items (unequal loadings), McDonald's omega would be more appropriate. Alpha underestimates reliability for congeneric measures.

2. **Single survey sample** — all statistics are computed on a single survey wave per domain (n ~ 1,200). Cross-validation across survey waves is not yet implemented.

3. **LLM-dependent clustering** — construct boundaries depend on LLM judgment, which may vary across runs. Step 1b (statistical gate) mitigates but does not eliminate this.

4. **Item pruning reduces cluster size** — some constructs are pruned to 3 items, the minimum. Three-item scales have higher sampling variability and are more sensitive to individual item characteristics.

5. **Tier 2/3 constructs in bridge analysis** — constructs with alpha 0.3-0.5 introduce measurement noise that attenuates gamma estimates. Bridge results involving these constructs should be interpreted with wider uncertainty bands.

### Future Directions

- **CFA/bifactor models** (per CONSTRUCT_ONTOLOGY_PLAN.md) for cross-domain constructs
- **McDonald's omega** as a supplementary reliability measure
- **IRT-based equating** for constructs measured across multiple surveys
- **Tier 2 single-item bridge variables** as alternatives to weak aggregated scales
- **Human expert review** of the ~20 highest-impact constructs
