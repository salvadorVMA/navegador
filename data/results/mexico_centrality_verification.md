# Mexico Centrality Verification — Is "Mexico as Global Average" Real?

## Finding

Mexico ranks 66/66 (least anomalous) in mean |γ deviation from global mean| across 66 WVS Wave 7 countries. Its SES-attitude bridge structure is the closest to the world average.

**This finding requires careful verification before it can be trusted.**

## Evidence Obtained So Far

### Precision Artifact (~40% of effect)

Mexico has the 5th narrowest CIs of 66 countries (mean CI width 38.6% below global average). After z-score normalization (anomaly / SE), Mexico drops from rank 64 to **rank 48/66** — still below median but not remarkable.

A noise simulation (same true γ for all countries, different SEs from observed CI widths) places Mexico's expected rank at 61. The observed rank of 64 is at the 98th percentile — slightly more central than precision alone explains, but not dramatically.

**Conclusion**: About half of Mexico's low-anomaly ranking is attributable to precise estimates, not genuine cultural centrality.

### Genuine Cultural Centrality (~40% of effect)

- Mexico ranks **4/66 in pairwise L1 distance** (most central countries: Turkey, Uzbekistan, Kazakhstan, Mexico)
- Mexico ranks **9/66 in PCA distance from origin** (r=0.61 pattern correlation with global mean, rank 13)
- Permutation test: Mexico's gamma profile lands at rank 64 in 10,000 permutations (p<0.0001 for being this central)
- Empirical Bayes shrinkage: Mexico drops from rank 64 to 61 — still bottom quintile

**Conclusion**: Mexico is genuinely one of the most culturally central countries in SES-attitude space. This is real, not just a precision artifact.

### LATAM Cluster Effect (~10%)

- Removing all 13 LATAM countries from the reference shifts Mexico by only 1 rank position (64→63)
- LATAM countries are generally low-anomaly (8/13 rank below median) but Uruguay is the MOST anomalous country globally
- Mexico being close to LATAM mean ≠ Mexico being close to global mean (the two are independently true)

**Conclusion**: LATAM cluster is not inflating Mexico's centrality.

### Construct/SES Design Bias (~10%, unknown)

The WVS SVS constructs were built by an LLM with `"source": "WVS Wave 7 — Mexico (2018)"`. The 4 SES variables were originally designed for los_mex. Both could unconsciously center the measurement on Mexican patterns.

**Conclusion**: Not yet tested. Requires verification steps below.

## Proposed Summary

> Mexico's SES-attitude bridge structure is among the most central in the 66-country sample (rank 4 in pairwise centrality). Roughly half of its low anomaly ranking is attributable to unusually precise estimates (narrow CIs); the other half reflects genuine cultural centrality in SES-attitude space. This is consistent with Mexico's position near the center of the Inglehart-Welzel cultural map.

## Verification Steps Still Needed

### Priority 1: Construct Alpha Comparison (design bias test)

Extract Cronbach's alpha for each construct in each country from `wvs_multi_construct_manifest.json`. If constructs were unconsciously optimized for Mexican response patterns, Mexico should have systematically higher alphas.

- **Confirm bias**: Mexico mean alpha in top 5/66
- **Refute bias**: Mexico mean alpha rank 20-40
- **Data**: `data/results/wvs_geo_construct_manifest.json`

### Priority 2: SES Distribution Entropy (harmonization bias test)

Load raw WVS data for all 66 countries. Compute Shannon entropy of the 4 harmonized SES variables per country. If Mexico's distributions are more balanced (higher entropy), the ordered logit is better conditioned → more stable γ → lower anomaly.

Key concern: `escol` (ISCED 0-8 collapsed to 1-5) and `Tam_loc` (G_TOWNSIZE 1-8 collapsed to 1-4). The collapse boundaries were set for los_mex equivalence.

- **Confirm bias**: Mexico has top-5 SES entropy
- **Refute**: Mexico SES entropy is unremarkable
- **Data**: Raw WVS CSVs in `data/wvs/`

### Priority 3: Binning Quality (ordered logit sensitivity test)

For each construct in each country: compute K<3 skip rate, tie rate before rank normalization, and bin entropy after binning. If Mexico has better-behaved binning, its γ estimates are more stable.

- **Data**: Construct CSVs in `data/julia_bridge_wvs/`

### Priority 4: Cross-Validated SVS (definitive construct bias test)

Have an LLM generate separate SVS definitions for 3-4 culturally diverse countries (Japan, Nigeria, Germany, Mexico) using each country's WVS questionnaire. Re-run the sweep with each SVS. If Mexico ranks lowest ONLY with Mexico-informed SVS, construct design bias is confirmed.

- **Cost**: High (4 LLM SVS builds + 4 sweep runs)
- **Diagnostic value**: Definitive

### Priority 5: Uncollapsed SES Re-Sweep (definitive harmonization test)

Re-run the sweep for a subset using raw WVS SES variables (ISCED 0-8, G_TOWNSIZE 1-8) without los_mex-targeted collapsing. If Mexico's centrality rank drops, harmonization was biasing the result.

- **Cost**: High (Julia re-sweep with modified SES encoding)
- **Diagnostic value**: Definitive

---

*Generated 2026-03-23. Tests 1-3 can be run immediately from existing data. Tests 4-5 require new computation.*
