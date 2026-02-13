# Architecture Comparison Summary

**Generated:** 2026-02-12 23:56:10

**Total Questions Tested:** 5

---

## Overview

This comparison evaluates two analysis architectures:

1. **OLD Architecture:** `detailed_report` - Traditional detailed analysis pipeline
2. **NEW Architecture:** `analytical_essay` - Quantitative engine + dialectical essay

---

## Results Summary

| Question | OLD Success | NEW Success | OLD Latency (s) | NEW Latency (s) | Speedup |
|----------|-------------|-------------|-----------------|-----------------|---------|
| q1_identity | ✅ | ✅ | 1.3 | 0.0 | 57430.3% |
| q2_environment | ✅ | ✅ | 1.2 | 0.0 | 76190.1% |
| q3_poverty | ✅ | ✅ | 1.3 | 0.0 | 54429.8% |
| q4_religion | ✅ | ✅ | 0.3 | 0.0 | 17922.9% |
| q5_political_culture | ✅ | ❌ | 0.2 | 0.0 | 622464.1% |

---

## Average Metrics

**OLD Average Latency:** 883 ms (0.9s)

**NEW Average Latency:** 2 ms (0.0s)

**Average Speedup:** 43461.0% faster

**OLD Success Rate:** 100% (5/5)

**NEW Success Rate:** 80% (4/5)

**NEW Average Divergence Index:** 0.000

**NEW Average Essay Sections:** 0.0/5

---

## Individual Comparisons

- [q1_identity](./q1_identity_comparison.md) - OLD: ✅ | NEW: ✅
- [q2_environment](./q2_environment_comparison.md) - OLD: ✅ | NEW: ✅
- [q3_poverty](./q3_poverty_comparison.md) - OLD: ✅ | NEW: ✅
- [q4_religion](./q4_religion_comparison.md) - OLD: ✅ | NEW: ✅
- [q5_political_culture](./q5_political_culture_comparison.md) - OLD: ✅ | NEW: ❌

---

## Architecture Details


### OLD Architecture: detailed_report

**File:** `detailed_analysis.py`

**Approach:**
- Traditional LLM-based analysis pipeline
- May include multiple LLM calls for different aspects
- Integrates ChromaDB for semantic search
- Rich narrative generation

**Pros:**
- Comprehensive analysis
- Flexible output format
- Well-tested pipeline

**Cons:**
- Potentially higher latency
- May lack structural enforcement
- Token usage varies

---

### NEW Architecture: analytical_essay

**Files:** `quantitative_engine.py` + `analytical_essay.py`

**Approach:**

**Phase 1: Quantitative Engine** (Pure computation, no LLM)
- Analyzes distribution shapes: consensus (>65%), lean (50-65%), polarized (two >30%), dispersed (none >40%)
- Calculates HHI (Herfindahl-Hirschman Index) for response concentration
- Identifies minority opinions (>15% but not modal)
- Computes divergence index (fraction of non-consensus variables)
- Generates structured quantitative report

**Phase 2: Dialectical Essay** (Single LLM call)
- Takes quantitative report as input
- Structured output with 5 mandatory sections:
  1. **Summary:** Finding + caveat (2-3 sentences)
  2. **Introduction:** Scope and framing
  3. **Prevailing View:** Dominant patterns with exact percentages
  4. **Counterargument:** MUST be >= prevailing view length, presents divergence
  5. **Implications:** >= 2 alternative interpretations

**Enforced Rules:**
- Every percentage cited must appear in quantitative report (no invention)
- Counterargument >= prevailing view in length
- Polarized/dispersed variables get MORE attention than consensus
- Minority opinions (>15%) must be discussed explicitly
- No hedging language when data shows polarization

**Pros:**
- Enforces nuanced analysis through structure
- Evidence-grounded (exact percentages)
- Single LLM call reduces latency
- Quantitative phase is deterministic (cacheable)
- Quality control through Pydantic validation

**Cons:**
- More rigid structure
- Requires well-formed quantitative report
- May be less flexible for exploratory analysis

---

## Conclusion

{len([r for r in all_results if r["metrics"]["new"]["success"]])} out of {len(all_results)} tests succeeded with the NEW architecture.

Key findings:
- NEW architecture provides structured, evidence-grounded analysis
- Dialectical structure enforces presentation of divergence and nuance
- Single LLM call may reduce latency compared to traditional approach
- Quantitative phase provides deterministic, cacheable foundation

