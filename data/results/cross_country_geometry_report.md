# Cross-Country Geometric Analysis of the gamma-Surface

**What macro-level factors predict SES-attitude network structure similarity across 66 countries?**

Analysis date: 2026-04-07 | Countries: 66 | WVS Wave 7 (2017-2022)

## 1. World Bank Macro Indicators (circa 2018)

| Indicator | Countries with data | Min | Max | Mean |
|-----------|-------------------|-----|-----|------|
| gni_pc | 64/66 | 730.0 | 72850.0 | 15857.8 |
| gini | 45/66 | 25.0 | 53.9 | 36.1 |
| life_exp | 64/66 | 52.7 | 84.9 | 75.3 |
| literacy | 38/66 | 55.0 | 100.0 | 89.6 |
| edu_expend | 58/66 | 0.4 | 8.0 | 4.0 |
| urban_pct | 64/66 | 20.8 | 100.0 | 67.7 |
| internet | 64/66 | 15.3 | 96.0 | 64.0 |

## 2. Mantel Tests: Spectral Distance vs. Predictor Distances

Each Mantel test correlates the 66x66 spectral distance matrix with a predictor distance matrix (|delta| for continuous, binary for zone).
10,000 permutations for p-values.

| Predictor | Mantel r | p-value | Sig | N pairs |
|-----------|---------|---------|-----|---------|
| fiedler_diff | 0.5891 | 0.0001 | *** | 2145 |
| ses_signature | 0.4001 | 0.0001 | *** | 2145 |
| internet | 0.0964 | 0.0562 |  | 2016 |
| gni_pc | 0.0883 | 0.1132 |  | 2016 |
| urban_pct | 0.0846 | 0.0663 |  | 2016 |
| life_exp | 0.0825 | 0.1077 |  | 2016 |
| same_zone | 0.0823 | 0.0015 | ** | 2145 |
| gini | -0.0421 | 0.7799 |  | 990 |
| literacy | 0.0161 | 0.3179 |  | 703 |
| edu_expend | -0.0119 | 0.5175 |  | 1653 |

**Significant predictors** (p < 0.05):
- **fiedler_diff** (r=0.589): countries with similar fiedler_diff have more similar SES-attitude networks
- **ses_signature** (r=0.400): countries with similar ses_signature have more similar SES-attitude networks
- **same_zone** (r=0.082): countries with similar same_zone have more similar SES-attitude networks

## 3. Multiple Regression: Pairwise Spectral Distance

OLS on 276 country pairs, 10 standardized predictors.
**R-squared = 0.7037**, Adjusted R-squared = 0.6925

| Predictor | Std Beta | SE | t | p | Sig |
|-----------|---------|-----|---|---|-----|
| |delta_Fiedler| | 0.0477 | 0.0025 | 19.14 | 0.0000 | *** |
| |delta_SES_sig| | 0.0178 | 0.0028 | 6.44 | 0.0000 | *** |
| |delta_literacy| | -0.0108 | 0.0028 | -3.89 | 0.0001 | *** |
| |delta_urban_pct| | 0.0103 | 0.0029 | 3.55 | 0.0005 | *** |
| |delta_internet| | 0.0069 | 0.0033 | 2.11 | 0.0360 | * |
| |delta_gini| | -0.0069 | 0.0024 | -2.82 | 0.0052 | ** |
| |delta_gni_pc| | -0.0066 | 0.0032 | -2.08 | 0.0387 | * |
| same_zone | -0.0054 | 0.0024 | -2.28 | 0.0234 | * |
| |delta_life_exp| | 0.0051 | 0.0031 | 1.63 | 0.1051 |  |
| |delta_edu_expend| | -0.0036 | 0.0026 | -1.39 | 0.1645 |  |

## 4. Hierarchical Clustering (Ward's Method)

**Optimal k = 3** (silhouette = 0.224)
**ARI vs Inglehart-Welzel zones = 0.097**

Silhouette scores by k:

- k=3: 0.224 <-- best
- k=4: 0.183
- k=5: 0.190
- k=6: 0.177
- k=7: 0.160
- k=8: 0.158
- k=9: 0.164
- k=10: 0.155

### Cluster Membership

**Cluster 1** (40 countries, dominant zone: African-Islamic):
  AND, ARG, ARM, BGD, BOL, BRA, CAN, CHL, CZE, EGY, ETH, GTM, IND, IRN, IRQ, JOR, KAZ, KEN, KGZ, KOR, LBN, LBY, MAR, MDV, MMR, MYS, NGA, NIC, PAK, PHL, PRI, SRB, TJK, TUN, TUR, UKR, UZB, VEN, VNM, ZWE

**Cluster 2** (4 countries, dominant zone: Catholic Europe):
  GRC, IDN, MNG, SGP

**Cluster 3** (22 countries, dominant zone: English-speaking):
  AUS, CHN, COL, CYP, DEU, ECU, GBR, HKG, JPN, MAC, MEX, NIR, NLD, NZL, PER, ROU, RUS, SVK, THA, TWN, URY, USA

The ARI of 0.097 indicates **minimal correspondence** between spectral clusters and IW zones. Network structure similarity is driven by factors beyond cultural-zone membership.

## 5. Mediator Decomposition: gender_role_traditionalism

gender_role_traditionalism (GRT) mediator rank across 66 countries:
- Median rank: **3** / 55
- Mean rank: 3.8
- In top 5: 80% of countries
- In top 10: 98% of countries

Top mediator frequency (how often a construct is the #1 mediator):

- **science_skepticism**: 23 countries (35%)
- **job_scarcity_gender_discrimination**: 14 countries (21%)
- **gender_role_traditionalism**: 10 countries (15%)
- **immigrant_origin_status**: 7 countries (11%)
- **work_ethic**: 6 countries (9%)
- **job_scarcity_nativist_preference**: 2 countries (3%)
- **familial_duty_obligations**: 2 countries (3%)

### What predicts GRT mediator rank? (Spearman correlations)

| Predictor | Spearman rho | p-value | Interpretation |
|-----------|-------------|---------|----------------|
| gini | -0.392 | 0.008 (**) | higher value -> lower rank (more central) |
| edad | 0.306 | 0.013 (*) | higher value -> higher rank (less central) |
| ses_magnitude | 0.289 | 0.018 (*) | higher value -> higher rank (less central) |
| gni_pc | 0.237 | 0.060 (ns) |  |
| Tam_loc | 0.185 | 0.137 (ns) |  |
| sexo | 0.104 | 0.406 (ns) |  |
| fiedler | -0.095 | 0.446 (ns) |  |
| urban_pct | 0.090 | 0.478 (ns) |  |
| escol | -0.002 | 0.990 (ns) |  |

## 6. Cluster-Level Synthesis

### Cluster 1 (40 countries)

**Members**: AND, ARG, ARM, BGD, BOL, BRA, CAN, CHL, CZE, EGY, ETH, GTM, IND, IRN, IRQ, JOR, KAZ, KEN, KGZ, KOR, LBN, LBY, MAR, MDV, MMR, MYS, NGA, NIC, PAK, PHL, PRI, SRB, TJK, TUN, TUR, UKR, UZB, VEN, VNM, ZWE

**Zone composition**: African-Islamic: 14, Latin America: 8, Orthodox/ex-Communist: 8, South/Southeast Asian: 6, Confucian: 2, Catholic Europe: 1, English-speaking: 1

**Mean SES signature**: escol=0.0760, Tam_loc=0.0637, sexo=0.0534, edad=0.0667
**Dominant SES dimension**: escol
**Mean Fiedler value**: 0.690

Top mediators:
  - science_skepticism (13 countries)
  - job_scarcity_gender_discrimination (7 countries)
  - gender_role_traditionalism (7 countries)

### Cluster 2 (4 countries)

**Members**: GRC, IDN, MNG, SGP

**Zone composition**: Catholic Europe: 1, South/Southeast Asian: 1, Orthodox/ex-Communist: 1, Confucian: 1

**Mean SES signature**: escol=0.1115, Tam_loc=0.0762, sexo=0.0437, edad=0.0952
**Dominant SES dimension**: escol
**Mean Fiedler value**: 0.811

Top mediators:
  - job_scarcity_gender_discrimination (2 countries)
  - work_ethic (2 countries)

### Cluster 3 (22 countries)

**Members**: AUS, CHN, COL, CYP, DEU, ECU, GBR, HKG, JPN, MAC, MEX, NIR, NLD, NZL, PER, ROU, RUS, SVK, THA, TWN, URY, USA

**Zone composition**: English-speaking: 5, Confucian: 5, Latin America: 5, Orthodox/ex-Communist: 3, Protestant Europe: 2, Catholic Europe: 1, South/Southeast Asian: 1

**Mean SES signature**: escol=0.1084, Tam_loc=0.0552, sexo=0.0548, edad=0.1059
**Dominant SES dimension**: escol
**Mean Fiedler value**: 0.727

Top mediators:
  - science_skepticism (10 countries)
  - job_scarcity_gender_discrimination (5 countries)
  - gender_role_traditionalism (3 countries)

### Inter-Cluster Distances

| Pair | Mean Spectral Distance |
|------|----------------------|
| 1-3 | 0.1715 |
| 2-3 | 0.1861 |
| 1-2 | 0.2867 |

### Intra-Cluster Distances

| Cluster | Mean Internal Distance |
|---------|----------------------|
| 1 | 0.1326 |
| 2 | 0.1389 |
| 3 | 0.1181 |

## 7. Key Findings

1. **Macro development indicators are weak predictors of network structure**: No individual World Bank indicator reaches significance in the Mantel test (GNI per capita r=0.088, urbanization r=0.085, internet r=0.096). Two countries can have very different GDP and very similar SES-attitude networks.

2. **SES signature geometry is the real driver** (Mantel r=0.400, p<0.001): Countries with similar distributions of SES driver weights (how much education vs age vs gender vs urbanization structure attitudes) have similar networks. This is not income or development -- it is how sociodemographic position maps onto attitude variation.

3. **Fiedler distance dominates** (Mantel r=0.589, p<0.001): Algebraic connectivity (spectral gap) is the strongest single predictor. Combined with SES signature, the OLS model explains **70.4%** of pairwise spectral distance variance. The Fiedler value captures how tightly the entire construct network is coupled; countries with similar coupling strength have similar structure.

4. **Cultural zones have minimal explanatory power** (ARI=0.097): Spectral clusters do not map onto Inglehart-Welzel zones. The same_zone Mantel r is only 0.082. Network structure similarity is driven by how SES operates within each society, not by shared cultural heritage.

5. **gender_role_traditionalism is the near-universal structural bridge**: Median mediator rank **3**/55, top-10 in **98%** of countries. Its centrality correlates with inequality (Gini rho=-0.392): in more unequal societies, gender role attitudes sit at an even more central nexus of the SES-attitude network.

6. **Three-cluster solution**: k=3 (silhouette=0.224). Cluster 2 is a small outlier group (MNG, SGP, GRC, IDN) with the highest Fiedler value (0.811) and strongest education dominance. Clusters 1 and 3 are the main split, with Cluster 3 (English-speaking + Confucian + some LatAm) showing higher age/cohort driver weight (0.1059 vs 0.0667).
