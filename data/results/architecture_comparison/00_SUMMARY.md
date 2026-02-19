# Architecture Comparison Summary

**Generated:** 2026-02-19 21:27:10

**Total Questions Tested:** 5

---

## Overview

This comparison evaluates two analysis architectures:

1. **OLD Architecture:** `detailed_report` - Traditional detailed analysis pipeline
2. **NEW Architecture:** `analytical_essay` - Quantitative engine + dialectical essay

---

## Results Summary

| Question | OLD Success | NEW Success | OLD Latency (ms) | NEW Latency (ms) | Speedup |
|----------|-------------|-------------|------------------|------------------|---------|
| q1_identity | ✅ | ✅ | 412 | 344 | 19.8% |
| q2_environment | ✅ | ✅ | 384 | 18 | 2008.2% |
| q3_poverty | ✅ | ✅ | 448 | 18 | 2347.4% |
| q4_religion | ✅ | ✅ | 281 | 21446 | -98.7% |
| q5_political_culture | ✅ | ✅ | 31566 | 39802 | -20.7% |

---

## Average Metrics

**OLD Average Latency:** 6618 ms

**NEW Average Latency:** 12326 ms

**OLD Success Rate:** 100%

**NEW Success Rate:** 100%

---

## Individual Comparisons

- [q1_identity](./q1_identity_comparison.md)
- [q2_environment](./q2_environment_comparison.md)
- [q3_poverty](./q3_poverty_comparison.md)
- [q4_religion](./q4_religion_comparison.md)
- [q5_political_culture](./q5_political_culture_comparison.md)

---

## Architecture Details


### OLD Architecture: detailed_report

- Uses `detailed_analysis.py`
- Traditional LLM-based analysis pipeline
- May include multiple LLM calls for different aspects
- Integrates ChromaDB for semantic search

### NEW Architecture: analytical_essay

- **Phase 1:** Pure computational quantitative engine (no LLM)
  - Analyzes distribution shapes (consensus/lean/polarized/dispersed)
  - Calculates HHI (concentration index)
  - Identifies minority opinions
  - Computes divergence index

- **Phase 2:** Single LLM call for dialectical essay
  - Structured output: summary, introduction, prevailing view, counterargument, implications
  - Enforces nuance through counterargument >= prevailing view
  - Evidence-grounded with exact percentages from quantitative report

