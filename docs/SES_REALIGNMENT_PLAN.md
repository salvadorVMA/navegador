# SES Variable Realignment: los_mex ↔ WVS Harmonization

## Problem Statement

Cross-study fingerprint comparison (2026-03-25) revealed that WVS and los_mex SES fingerprints for **conceptually identical constructs** are nearly orthogonal:

- **Median cosine similarity: 0.195** (should be ~0.8+ for equivalent constructs)
- **Dominant dimension agreement: 13%** (6/46 grade-3 pairs)
- **41% of pairs have negative cosine** (opposite SES profiles)

Three coding mismatches were identified as root causes.

## Root Cause Analysis

### 1. Tam_loc REVERSED SCALE (critical)

| | los_mex (original) | WVS (after harmonize_ses) |
|---|---|---|
| Value 1 | ≥100,000 inhabitants (urban) | <5,000 inhabitants (rural) |
| Value 4 | <2,500 inhabitants (rural) | ≥100,000 inhabitants (urban) |
| Direction | 1=urban → 4=rural | 1=rural → 4=urban |

**Impact**: All ρ(construct, Tam_loc) have **opposite signs** between studies. Urbanization appears as 0% dominant in WVS but 23% in los_mex — the reversal masks the signal entirely.

**Evidence**: WVS Tam_loc distribution shows 29% at value 1 (rural in WVS), while los_mex shows 52% at value 1 (urban in los_mex). Same country, same respondent pool — the difference is purely the coding direction.

### 2. Escol BOUNDARY MISMATCH (significant)

| Bridge level | WVS (ISCED mapping) | los_mex (Mexican system) |
|---|---|---|
| 1 | No formal + **Primary** (ISCED 0-1) | **Ninguna** (no school) |
| 2 | Lower secondary (ISCED 2) | **Primaria** (primary school) |
| 3 | Upper secondary + post-sec (ISCED 3-4) | **Secundaria** (middle school) |
| 4 | Short-cycle tertiary (ISCED 5) | **Preparatoria** (high school) |
| 5 | Bachelor's + Master's + Doctoral (ISCED 6-8) | **Universidad/Posgrado** |

**Impact**: WVS level 1 contains 28% of respondents (includes all primary school graduates); los_mex level 1 has only 7-12% (no school at all). A primary school graduate is escol=1 in WVS but escol=2 in los_mex. The ordinal ranks carry different populations.

### 3. Edad UNNECESSARY BINNING (resolution loss)

| | WVS | los_mex |
|---|---|---|
| Raw data | Q262: continuous age 18-90+ | sd2: continuous age 15-97 (24/26 surveys) |
| Current transform | `_bin_age()` → 7 string bins | `categorize_age()` → 7 string bins |
| Information loss | 72+ unique ages → 7 bins (10:1 compression) | ~65 unique ages → 7 bins |

**Impact**: The ordered logit handles continuous predictors natively. Binning discards within-bin variance and creates artificial tie structure that inflates Goodman-Kruskal γ (tied pairs excluded from denominator).

**Key finding**: sd2 (raw continuous age) is present in **24/26** los_mex surveys as a numeric variable (range 8-97, ~65 unique values). Only JUEGOS_DE_AZAR and CULTURA_CONSTITUCIONAL have pre-binned edad (ordinal 1-6).

## Fixes Applied (2026-03-25)

### Fix 1: Reverse los_mex Tam_loc → 1=rural, 4=urban

**File**: `ses_analysis.py`, `preprocess_survey_data()`

```python
s = 5.0 - s  # Reverse: 1=urban→4=rural becomes 1=rural→4=urban (WVS convention)
```

The natural ordinal direction is small→large. WVS already uses this. All downstream fingerprints, bridge estimates, and ontology edges will reflect the corrected direction.

### Fix 2: Realign WVS escol to Mexican education levels

**File**: `wvs_metadata.py`

Old: `{0:1, 1:1, 2:2, 3:3, 4:3, 5:4, 6:5, 7:5, 8:5}`
New: `{0:1, 1:2, 2:3, 3:4, 4:4, 5:5, 6:5, 7:5, 8:5}`

| Level | ISCED | Mexican equivalent |
|---|---|---|
| 1 | 0 (No formal) | Ninguna |
| 2 | 1 (Primary) | Primaria |
| 3 | 2 (Lower secondary) | Secundaria |
| 4 | 3-4 (Upper secondary + vocational) | Preparatoria |
| 5 | 5-8 (Tertiary) | Universidad/Posgrado |

### Fix 3: Use continuous age from sd2

**Files**: `ses_analysis.py`, `ses_regression.py`, `wvs_metadata.py`, `wvs_loader.py`

- los_mex: `df['edad'] = pd.to_numeric(df['sd2']).where(between(15, 100))`
- WVS: Q262 passed as raw numeric age (new `"continuous_age"` transform)
- SESEncoder: detects continuous edad (>20 unique values) and passes through directly
- JUE/CON surveys: keep pre-binned edad (1-6) — handled as ordinal integers

## Pipeline Re-run Required

After these code changes, the full pipeline must be re-run:

1. **Rebuild constructs**: `python scripts/debug/build_construct_variables.py`
2. **Recompute fingerprints**: `python scripts/debug/compute_ses_fingerprints.py`
3. **Patch ontology**: `python scripts/debug/patch_kg_ontology_bridges.py`
4. **Re-export WVS CSVs**: `python scripts/debug/export_wvs_for_julia.py`
5. **Re-run los_mex sweep** (Julia, ~40 min): `julia -t 8 scripts/run_v5_sweep.jl`
6. **Re-run WVS sweep** (Julia, ~10 hr geographic): `julia -t 8 scripts/run_wvs_geographic_fast.jl`
7. **Rebuild gamma surface & visualizations**

**Julia `ses_encoder.jl` update needed**: The Julia encoder currently expects edad as string categories. With continuous numeric edad, it should pass through directly.

## Expected Outcomes

1. **Tam_loc fingerprints flip sign** for all los_mex constructs → cosine with WVS should improve dramatically
2. **Escol distributions align** → WVS level 1 shrinks from 28% to ~10% (matching los_mex)
3. **Continuous edad** → finer age discrimination in ordered logit, potentially tighter CIs
4. **Cross-study cosine** should improve from 0.195 toward 0.5-0.8
5. **Driver comparison** should show Tam_loc appearing in WVS significant pairs (currently 0%)

## Verification

- 150 unit tests pass (all 3 test files updated for continuous edad + Tam_loc direction)
- Fingerprint sign check after rebuild: ρ_Tam_loc should flip for all los_mex constructs
- Cross-study cosine recomputation is the key metric

## Risk Notes

- Tam_loc reversal is a pure coordinate flip — magnitudes preserved, some bridge γ signs flip
- Escol change affects WVS data only — los_mex escol is unchanged
- Continuous edad changes model structure (ordinal→continuous predictor) — linearity assumption may not hold for nonlinear age effects, but the ordered logit accommodates this better than arbitrary 7-bin discretization
- `_bin_age()` function retained for backward compatibility (imported by WVS tests)
