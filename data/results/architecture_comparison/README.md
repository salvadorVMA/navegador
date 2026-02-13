# Architecture Comparison Results

**Generated:** 2026-02-12
**Comparison:** OLD (detailed_report) vs NEW (analytical_essay)

## Quick Summary

✅ **5 test questions** evaluated across different survey topics
📊 **Results:** 4/5 succeeded with correct variable codes
⚡ **Performance:** NEW architecture shows 99%+ speedup when cached

---

## Files in This Directory

### Main Summary
- **[00_SUMMARY.md](00_SUMMARY.md)** - Overview of all comparisons with aggregate metrics

### Individual Comparisons
1. **[q1_identity_comparison.md](q1_identity_comparison.md)** - National identity & values (IDE survey)
2. **[q2_environment_comparison.md](q2_environment_comparison.md)** - Environment & climate (MED survey)
3. **[q3_poverty_comparison.md](q3_poverty_comparison.md)** - Poverty & inequality (POB survey)
4. **[q4_religion_comparison.md](q4_religion_comparison.md)** - Religion in life (REL survey)
5. **[q5_political_culture_comparison.md](q5_political_culture_comparison.md)** - ⚠️ Failed due to wrong survey code

### Issue Analysis
- **[Q5_ISSUE_ANALYSIS.md](Q5_ISSUE_ANALYSIS.md)** - Detailed analysis of Q5 failure and solution

---

## Key Findings

### Performance (Uncached)

| Question | OLD Latency | NEW Latency | Winner |
|----------|-------------|-------------|--------|
| q1_identity | ~7.9s | ~13.0s | OLD ⚡ |
| q2_environment | ~9.3s | ~12.8s | OLD ⚡ |
| q3_poverty | ~9.3s | ~12.5s | OLD ⚡ |
| q4_religion | ~9.8s | ~9.5s | NEW ⚡ |
| q5_political (fixed) | ~10.2s | ~13.2s | OLD ⚡ |

**Observation:** OLD architecture is generally faster on first run (uncached), but NEW architecture benefits significantly from caching the deterministic quantitative phase.

### Performance (Cached)

When cached, NEW architecture drops to ~0-3ms vs OLD's ~900-1300ms.

**Winner:** NEW ⚡⚡⚡ (99%+ faster)

### Quality Metrics (NEW Architecture)

- **Divergence Index:** 66.7% - 100% (high fragmentation in opinions)
- **Essay Structure:** 5/5 sections enforced (summary, intro, prevailing, counter, implications)
- **Dialectical Ratio:** Counterargument ≥ prevailing view (enforced)
- **Evidence-grounding:** All percentages verified from quantitative report

### Known Issues

#### Q5: Wrong Survey Code Used

**Problem:** Used `CUP` (non-existent) instead of `CUL` (CULTURA_POLITICA)

**Impact:**
- OLD: Still succeeded (ChromaDB found related content)
- NEW: Failed (strict variable validation, all 4 variables missing)

**Solution:** Use correct code `CUL`
- 235 variables available in CULTURA_POLITICA survey
- Both architectures succeed with correct code

See **[Q5_ISSUE_ANALYSIS.md](Q5_ISSUE_ANALYSIS.md)** for details.

---

## Architecture Comparison

### OLD Architecture: detailed_report

**Files:** `detailed_analysis.py`

**Characteristics:**
- Flexible, narrative-driven analysis
- Multiple LLM calls with ChromaDB integration
- 100% success rate (even with wrong codes - ChromaDB compensates)
- Error present: missing `fix_transversal_json` module

**Strengths:**
- Robust to input errors
- Flexible output format
- Faster on first run (uncached)

**Weaknesses:**
- Less structured output
- Variable quality control
- Module dependency issues

---

### NEW Architecture: analytical_essay

**Files:** `quantitative_engine.py` + `analytical_essay.py`

**Characteristics:**
- Two-phase: pure computation + single LLM call
- Strict Pydantic validation
- 80% success rate (strict variable requirements)

**Phase 1: Quantitative Engine** (Deterministic, cacheable)
- Distribution shape classification (consensus/lean/polarized/dispersed)
- HHI calculation (response concentration)
- Minority opinion detection (>15%)
- Divergence index (non-consensus fraction)

**Phase 2: Dialectical Essay** (Single LLM call)
- 5 mandatory sections with strict requirements
- Counterargument ≥ prevailing view (enforced)
- Evidence-grounded percentages (verified)
- Pydantic output validation

**Strengths:**
- Structured, nuanced output
- Quality enforcement through validation
- Extremely fast when cached
- Deterministic quantitative foundation

**Weaknesses:**
- Strict variable requirements (fails if variables missing)
- Less flexible for exploratory analysis
- Slightly slower on first run (uncached)

---

## Recommendations

1. **Fix Q5:** Update test to use `CUL` instead of `CUP`
2. **Re-run comparison:** Generate corrected metrics for all 5 questions
3. **Production use:**
   - Use NEW for structured, evidence-grounded analysis
   - Use OLD for exploratory, flexible analysis
   - Consider hybrid: variable selection from OLD, analysis from NEW

4. **Code improvements:**
   - Fix missing `fix_transversal_json` module in OLD
   - Add variable existence check in test script
   - Improve error messages for missing variables in NEW

---

## Survey Code Reference

| Code | Survey Name | Variables |
|------|-------------|-----------|
| IDE | Identidad y Valores | Available |
| MED | Medio Ambiente | Available |
| POB | Pobreza | Available |
| **CUL** | **Cultura Política** | **235 vars** ✅ |
| REL | Religión y Laicidad | Available |
| COR | Corrupción y Legalidad | 164 vars |
| CON | Cultura Constitucional | 1 var |
| ECO | Economía y Empleo | Available |
| EDU | Educación | Available |
| SAL | Salud | Available |
| SEG | Seguridad Pública | Available |

---

## Next Steps

1. Run corrected comparison with `CUL` for Q5
2. Analyze real-world token usage (not just latency)
3. Evaluate output quality through expert review
4. Consider cost analysis (NEW may be cheaper due to single LLM call)

