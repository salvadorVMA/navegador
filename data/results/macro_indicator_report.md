# Macro-Indicator Analysis: What Predicts SES-Attitude Network Structure?

## Overview

This analysis tests whether country-level macro indicators predict variation
in SES-attitude network properties across 66 WVS Wave 7 countries.

**Macro indicators tested:**
- V-Dem Electoral Democracy (v2x_polyarchy)
- V-Dem Liberal Democracy (v2x_libdem)
- V-Dem Egalitarian Democracy (v2x_egaldem)
- V-Dem Participatory Democracy (v2x_partipdem)
- V-Dem Deliberative Democracy (v2x_delibdem)
- V-Dem PC1 (PCA composite of all 5 V-Dem indices)
- GNI per capita (log-transformed, World Bank 2018)
- Gini coefficient (World Bank, latest near 2018)
- Urban population % (World Bank 2018)
- Mean years of schooling (UNDP HDR 2018)
- Human Development Index (UNDP 2018)

**Network properties predicted:**
- Significance rate (% of construct pairs with CI excluding zero)
- Median |gamma| (SES-mediated association strength)
- Spearman rho with global median (typicality)
- Fiedler value (algebraic connectivity from TDA pipeline)
- Spectral entropy and radius
- SES magnitude (RMS of 4D SES signature)

**V-Dem coverage:** 61/66 countries (AND, HKG, MAC, NIR, PRI lack V-Dem entries)

## 1. Bivariate Correlations (Spearman)

| Macro Indicator | Network Metric | rho | p-value | n | Sig |
|-----------------|---------------|-----|---------|---|-----|
| hdi | spearman_rho_with_median | +0.637 | 0.0000 | 64 | *** |
| log_gni_pc | spearman_rho_with_median | +0.596 | 0.0000 | 66 | *** |
| hdi | median_abs_gamma | +0.597 | 0.0000 | 64 | *** |
| hdi | sig_pct | +0.592 | 0.0000 | 64 | *** |
| hdi | ses_magnitude | +0.591 | 0.0000 | 64 | *** |
| v2x_egaldem | median_abs_gamma | +0.592 | 0.0000 | 61 | *** |
| v2x_egaldem | spearman_rho_with_median | +0.589 | 0.0000 | 61 | *** |
| v2x_egaldem | ses_magnitude | +0.587 | 0.0000 | 61 | *** |
| vdem_pc1 | median_abs_gamma | +0.575 | 0.0000 | 61 | *** |
| v2x_delibdem | median_abs_gamma | +0.574 | 0.0000 | 61 | *** |
| v2x_egaldem | sig_pct | +0.574 | 0.0000 | 61 | *** |
| log_gni_pc | median_abs_gamma | +0.555 | 0.0000 | 66 | *** |
| mean_yrs_school | ses_magnitude | +0.554 | 0.0000 | 66 | *** |
| v2x_delibdem | spearman_rho_with_median | +0.572 | 0.0000 | 61 | *** |
| v2x_libdem | median_abs_gamma | +0.572 | 0.0000 | 61 | *** |
| mean_yrs_school | median_abs_gamma | +0.549 | 0.0000 | 66 | *** |
| v2x_delibdem | sig_pct | +0.568 | 0.0000 | 61 | *** |
| v2x_polyarchy | median_abs_gamma | +0.560 | 0.0000 | 61 | *** |
| log_gni_pc | sig_pct | +0.541 | 0.0000 | 66 | *** |
| vdem_pc1 | spearman_rho_with_median | +0.559 | 0.0000 | 61 | *** |
| vdem_pc1 | ses_magnitude | +0.557 | 0.0000 | 61 | *** |
| vdem_pc1 | sig_pct | +0.557 | 0.0000 | 61 | *** |
| log_gni_pc | ses_magnitude | +0.536 | 0.0000 | 66 | *** |
| v2x_libdem | ses_magnitude | +0.554 | 0.0000 | 61 | *** |
| v2x_polyarchy | spearman_rho_with_median | +0.553 | 0.0000 | 61 | *** |
| v2x_libdem | spearman_rho_with_median | +0.552 | 0.0000 | 61 | *** |
| v2x_delibdem | ses_magnitude | +0.552 | 0.0000 | 61 | *** |
| v2x_libdem | sig_pct | +0.551 | 0.0000 | 61 | *** |
| v2x_polyarchy | ses_magnitude | +0.546 | 0.0000 | 61 | *** |
| v2x_partipdem | median_abs_gamma | +0.545 | 0.0000 | 61 | *** |
| v2x_polyarchy | sig_pct | +0.542 | 0.0000 | 61 | *** |
| v2x_partipdem | ses_magnitude | +0.531 | 0.0000 | 61 | *** |
| v2x_partipdem | sig_pct | +0.530 | 0.0000 | 61 | *** |
| v2x_partipdem | spearman_rho_with_median | +0.522 | 0.0000 | 61 | *** |
| hdi | spectral_radius | -0.499 | 0.0000 | 64 | *** |
| mean_yrs_school | spearman_rho_with_median | +0.484 | 0.0000 | 66 | *** |
| hdi | spectral_entropy | +0.486 | 0.0000 | 64 | *** |
| urban_pct | spearman_rho_with_median | +0.467 | 0.0001 | 66 | *** |
| mean_yrs_school | sig_pct | +0.461 | 0.0001 | 66 | *** |
| log_gni_pc | spectral_entropy | +0.453 | 0.0001 | 66 | *** |
| mean_yrs_school | spectral_radius | -0.419 | 0.0005 | 66 | *** |
| log_gni_pc | spectral_radius | -0.409 | 0.0007 | 66 | *** |
| v2x_egaldem | spectral_entropy | +0.403 | 0.0013 | 61 | ** |
| v2x_libdem | spectral_entropy | +0.380 | 0.0025 | 61 | ** |
| v2x_delibdem | spectral_entropy | +0.379 | 0.0026 | 61 | ** |
| vdem_pc1 | spectral_entropy | +0.379 | 0.0026 | 61 | ** |
| v2x_egaldem | spectral_radius | -0.368 | 0.0035 | 61 | ** |
| v2x_polyarchy | spectral_entropy | +0.364 | 0.0040 | 61 | ** |
| urban_pct | median_abs_gamma | +0.348 | 0.0042 | 66 | ** |
| v2x_libdem | spectral_radius | -0.345 | 0.0064 | 61 | ** |
| v2x_delibdem | spectral_radius | -0.342 | 0.0070 | 61 | ** |
| vdem_pc1 | spectral_radius | -0.341 | 0.0072 | 61 | ** |
| gini | fiedler_value | +0.349 | 0.0073 | 58 | ** |
| urban_pct | sig_pct | +0.321 | 0.0086 | 66 | ** |
| mean_yrs_school | spectral_entropy | +0.317 | 0.0095 | 66 | ** |
| v2x_polyarchy | spectral_radius | -0.329 | 0.0096 | 61 | ** |
| v2x_partipdem | spectral_entropy | +0.321 | 0.0116 | 61 | * |
| urban_pct | ses_magnitude | +0.308 | 0.0119 | 66 | * |
| urban_pct | spectral_radius | -0.271 | 0.0275 | 66 | * |
| gini | pos_pct | +0.287 | 0.0292 | 58 | * |
| urban_pct | spectral_entropy | +0.258 | 0.0365 | 66 | * |
| v2x_partipdem | spectral_radius | -0.268 | 0.0370 | 61 | * |
| gini | median_abs_gamma | -0.244 | 0.0649 | 58 |  |
| gini | ses_magnitude | -0.186 | 0.1615 | 58 |  |
| gini | spectral_entropy | +0.176 | 0.1858 | 58 |  |
| hdi | fiedler_value | +0.128 | 0.3141 | 64 |  |
| gini | spearman_rho_with_median | +0.125 | 0.3515 | 58 |  |
| log_gni_pc | fiedler_value | +0.112 | 0.3711 | 66 |  |
| urban_pct | pos_pct | -0.106 | 0.3952 | 66 |  |
| v2x_egaldem | pos_pct | +0.108 | 0.4078 | 61 |  |
| v2x_partipdem | pos_pct | +0.105 | 0.4208 | 61 |  |
| v2x_polyarchy | pos_pct | +0.104 | 0.4256 | 61 |  |
| vdem_pc1 | pos_pct | +0.096 | 0.4626 | 61 |  |
| v2x_libdem | pos_pct | +0.094 | 0.4704 | 61 |  |
| mean_yrs_school | pos_pct | +0.090 | 0.4728 | 66 |  |
| v2x_delibdem | pos_pct | +0.093 | 0.4760 | 61 |  |
| log_gni_pc | pos_pct | -0.078 | 0.5310 | 66 |  |
| urban_pct | fiedler_value | +0.077 | 0.5400 | 66 |  |
| gini | spectral_radius | +0.059 | 0.6611 | 58 |  |
| gini | sig_pct | -0.045 | 0.7385 | 58 |  |
| v2x_egaldem | fiedler_value | +0.034 | 0.7938 | 61 |  |
| v2x_libdem | fiedler_value | +0.030 | 0.8195 | 61 |  |
| vdem_pc1 | fiedler_value | +0.027 | 0.8350 | 61 |  |
| v2x_delibdem | fiedler_value | +0.027 | 0.8379 | 61 |  |
| v2x_polyarchy | fiedler_value | +0.026 | 0.8418 | 61 |  |
| v2x_partipdem | fiedler_value | -0.012 | 0.9244 | 61 |  |
| mean_yrs_school | fiedler_value | +0.011 | 0.9275 | 66 |  |
| hdi | pos_pct | -0.004 | 0.9721 | 64 |  |

### Democracy-Specific Findings

- **median_abs_gamma**: rho = +0.560 (p=0.0000, ***)
- **spearman_rho_with_median**: rho = +0.553 (p=0.0000, ***)
- **ses_magnitude**: rho = +0.546 (p=0.0000, ***)
- **sig_pct**: rho = +0.542 (p=0.0000, ***)
- **spectral_entropy**: rho = +0.364 (p=0.0040, **)
- **spectral_radius**: rho = -0.329 (p=0.0096, **)
- **pos_pct**: rho = +0.104 (p=0.4256, ns)
- **fiedler_value**: rho = +0.026 (p=0.8418, ns)

## 2. Mantel Tests (gamma-vector distance)

Tests whether countries with similar macro indicators also have similar
SES-attitude networks (measured by gamma-vector cosine distance).

| Indicator | Mantel rho | p-value | n | Sig |
|-----------|-----------|---------|---|-----|
| v2x_polyarchy | +0.211 | 0.0001 | 61 | *** |
| v2x_partipdem | +0.183 | 0.0001 | 61 | *** |
| vdem_pc1 | +0.168 | 0.0002 | 61 | *** |
| urban_pct | +0.201 | 0.0002 | 61 | *** |
| mean_yrs_school | +0.182 | 0.0002 | 61 | *** |
| hdi | +0.223 | 0.0002 | 61 | *** |
| log_gni_pc | +0.201 | 0.0004 | 61 | *** |
| v2x_libdem | +0.156 | 0.0006 | 61 | *** |
| v2x_delibdem | +0.150 | 0.0010 | 61 | ** |
| v2x_egaldem | +0.134 | 0.0040 | 61 | ** |

## 3. OLS Regression Models


### Outcome: sig_pct

**Model: baseline** (n=58, R2=0.355, adj_R2=0.307)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +22.4809 | 14.3066 | +1.57 | 0.1220 |
| log_gni_pc | +8.0070 | 2.7079 | +2.96 | 0.0046** |
| gini | +0.0529 | 0.2891 | +0.18 | 0.8555 |
| urban_pct | -0.0523 | 0.1396 | -0.37 | 0.7096 |
| mean_yrs_school | +0.3045 | 1.0260 | +0.30 | 0.7678 |

**Model: full_with_vdem** (n=56, R2=0.405, adj_R2=0.345)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +19.7770 | 14.9153 | +1.33 | 0.1909 |
| log_gni_pc | +5.9018 | 3.0150 | +1.96 | 0.0559 |
| gini | +0.0342 | 0.3039 | +0.11 | 0.9107 |
| urban_pct | -0.0882 | 0.1379 | -0.64 | 0.5253 |
| mean_yrs_school | +0.3705 | 1.0114 | +0.37 | 0.7157 |
| v2x_polyarchy | +17.7058 | 9.5883 | +1.85 | 0.0707 |

**Model: democracy_only** (n=61, R2=0.297, adj_R2=0.285)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +22.4272 | 3.8746 | +5.79 | 0.0000*** |
| v2x_polyarchy | +33.2967 | 6.6663 | +4.99 | 0.0000*** |

**V-Dem increment:** Delta R2 = +0.049 (from 0.355 to 0.405)


### Outcome: median_abs_gamma

**Model: baseline** (n=58, R2=0.371, adj_R2=0.323)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.0124 | 0.0073 | +1.70 | 0.0951 |
| log_gni_pc | +0.0040 | 0.0014 | +2.87 | 0.0058** |
| gini | -0.0002 | 0.0001 | -1.17 | 0.2484 |
| urban_pct | -0.0000 | 0.0001 | -0.18 | 0.8574 |
| mean_yrs_school | +0.0001 | 0.0005 | +0.16 | 0.8756 |

**Model: full_with_vdem** (n=56, R2=0.418, adj_R2=0.360)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.0098 | 0.0073 | +1.35 | 0.1837 |
| log_gni_pc | +0.0022 | 0.0015 | +1.49 | 0.1428 |
| gini | -0.0001 | 0.0001 | -1.01 | 0.3181 |
| urban_pct | -0.0000 | 0.0001 | -0.38 | 0.7077 |
| mean_yrs_school | +0.0001 | 0.0005 | +0.14 | 0.8877 |
| v2x_polyarchy | +0.0113 | 0.0047 | +2.40 | 0.0200* |

**Model: democracy_only** (n=61, R2=0.339, adj_R2=0.328)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.0048 | 0.0018 | +2.69 | 0.0092** |
| v2x_polyarchy | +0.0170 | 0.0031 | +5.50 | 0.0000*** |

**V-Dem increment:** Delta R2 = +0.047 (from 0.371 to 0.418)


### Outcome: spearman_rho_with_median

**Model: baseline** (n=58, R2=0.384, adj_R2=0.338)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | -0.0298 | 0.1625 | -0.18 | 0.8551 |
| log_gni_pc | +0.0636 | 0.0307 | +2.07 | 0.0435* |
| gini | +0.0047 | 0.0033 | +1.42 | 0.1615 |
| urban_pct | +0.0006 | 0.0016 | +0.39 | 0.7015 |
| mean_yrs_school | +0.0124 | 0.0117 | +1.06 | 0.2923 |

**Model: full_with_vdem** (n=56, R2=0.417, adj_R2=0.359)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | -0.1186 | 0.1695 | -0.70 | 0.4873 |
| log_gni_pc | +0.0397 | 0.0343 | +1.16 | 0.2525 |
| gini | +0.0060 | 0.0035 | +1.74 | 0.0885 |
| urban_pct | +0.0003 | 0.0016 | +0.21 | 0.8366 |
| mean_yrs_school | +0.0133 | 0.0115 | +1.16 | 0.2514 |
| v2x_polyarchy | +0.1819 | 0.1089 | +1.67 | 0.1012 |

**Model: democracy_only** (n=61, R2=0.326, adj_R2=0.314)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.2125 | 0.0430 | +4.94 | 0.0000*** |
| v2x_polyarchy | +0.3949 | 0.0740 | +5.34 | 0.0000*** |

**V-Dem increment:** Delta R2 = +0.032 (from 0.384 to 0.417)


### Outcome: fiedler_value

**Model: baseline** (n=58, R2=0.076, adj_R2=0.006)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.6072 | 0.0533 | +11.38 | 0.0000*** |
| log_gni_pc | -0.0015 | 0.0101 | -0.15 | 0.8839 |
| gini | +0.0021 | 0.0011 | +1.97 | 0.0545 |
| urban_pct | -0.0001 | 0.0005 | -0.15 | 0.8805 |
| mean_yrs_school | +0.0033 | 0.0038 | +0.86 | 0.3941 |

**Model: full_with_vdem** (n=56, R2=0.059, adj_R2=-0.036)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.6159 | 0.0580 | +10.62 | 0.0000*** |
| log_gni_pc | -0.0052 | 0.0117 | -0.44 | 0.6604 |
| gini | +0.0018 | 0.0012 | +1.56 | 0.1259 |
| urban_pct | -0.0001 | 0.0005 | -0.20 | 0.8417 |
| mean_yrs_school | +0.0031 | 0.0039 | +0.79 | 0.4331 |
| v2x_polyarchy | +0.0225 | 0.0373 | +0.60 | 0.5480 |

**Model: democracy_only** (n=61, R2=0.005, adj_R2=-0.012)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.7017 | 0.0140 | +50.06 | 0.0000*** |
| v2x_polyarchy | +0.0128 | 0.0241 | +0.53 | 0.5970 |

**V-Dem increment:** Delta R2 = -0.017 (from 0.076 to 0.059)


### Outcome: ses_magnitude

**Model: baseline** (n=58, R2=0.356, adj_R2=0.307)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.0650 | 0.0169 | +3.85 | 0.0003*** |
| log_gni_pc | +0.0093 | 0.0032 | +2.91 | 0.0053** |
| gini | -0.0002 | 0.0003 | -0.58 | 0.5639 |
| urban_pct | -0.0001 | 0.0002 | -0.67 | 0.5047 |
| mean_yrs_school | +0.0007 | 0.0012 | +0.54 | 0.5887 |

**Model: full_with_vdem** (n=56, R2=0.401, adj_R2=0.341)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.0610 | 0.0171 | +3.57 | 0.0008*** |
| log_gni_pc | +0.0050 | 0.0034 | +1.46 | 0.1519 |
| gini | -0.0002 | 0.0003 | -0.57 | 0.5734 |
| urban_pct | -0.0001 | 0.0002 | -0.90 | 0.3729 |
| mean_yrs_school | +0.0006 | 0.0012 | +0.52 | 0.6024 |
| v2x_polyarchy | +0.0271 | 0.0110 | +2.47 | 0.0169* |

**Model: democracy_only** (n=61, R2=0.332, adj_R2=0.320)

| Predictor | Coef | SE | t | p |
|-----------|------|-----|---|---|
| const | +0.0542 | 0.0042 | +12.82 | 0.0000*** |
| v2x_polyarchy | +0.0394 | 0.0073 | +5.41 | 0.0000*** |

**V-Dem increment:** Delta R2 = +0.045 (from 0.356 to 0.401)


## V-Dem PCA Composite

PC1 explains **98.6%** of the variance across all 5 V-Dem indices.

PC1 loadings:

| Index | Loading |
|-------|--------|
| v2x_polyarchy | +0.4592 |
| v2x_libdem | +0.4937 |
| v2x_egaldem | +0.4246 |
| v2x_partipdem | +0.3256 |
| v2x_delibdem | +0.5090 |


## 4. Interaction Models (Democracy x Macro Indicators)

### Statistical Methodology

- **OLS coefficients**: t = beta / SE(beta), p-value from t-distribution with (n - k - 1) degrees of freedom. Assumes: normally distributed errors, homoscedasticity, no perfect multicollinearity.
- **Mantel test**: permutation-based p-value (9999 random permutations of distance matrix rows/columns). No distributional assumptions.
- **Spearman rho**: exact or asymptotic p-value for null hypothesis of rho = 0, computed via scipy.stats.spearmanr.
- **Interaction terms**: Continuous predictors are mean-centered before computing interactions to reduce multicollinearity between main effects and interaction terms.
- **Delta R2**: R2(interaction model) - R2(additive-only model with same main-effect predictors but no interaction terms).


### Outcome: fiedler_value

| Model | n | R2 | R2_add | Delta_R2 | Interaction | Coef | p | Sig |
|-------|---|----|----|------|------------|------|---|-----|
| A_gni_x_demo | 61 | 0.104 | 0.005 | +0.099 | log_gni_pc_x_v2x_polyarchy | -0.0601 | 0.0150 | * |
| B_educ_x_demo | 61 | 0.059 | 0.006 | +0.053 | mean_yrs_school_x_v2x_polyarchy | -0.0197 | 0.0790 |  |
| C_gini_x_demo | 56 | 0.047 | 0.046 | +0.001 | gini_x_v2x_polyarchy | -0.0012 | 0.8127 |  |
| D_urban_x_demo | 61 | 0.042 | 0.008 | +0.034 | urban_pct_x_v2x_polyarchy | -0.0020 | 0.1631 |  |
| E_full_interactions | 56 | 0.137 | 0.059 | +0.078 | log_gni_pc_x_v2x_polyarchy | -0.0594 | 0.0436 | * |
| E_full_interactions | 56 | 0.137 | 0.059 | +0.078 | gini_x_v2x_polyarchy | -0.0025 | 0.6250 |  |


### Outcome: median_abs_gamma

| Model | n | R2 | R2_add | Delta_R2 | Interaction | Coef | p | Sig |
|-------|---|----|----|------|------------|------|---|-----|
| A_gni_x_demo | 61 | 0.438 | 0.413 | +0.025 | log_gni_pc_x_v2x_polyarchy | +0.0047 | 0.1203 |  |
| B_educ_x_demo | 61 | 0.384 | 0.371 | +0.013 | mean_yrs_school_x_v2x_polyarchy | +0.0015 | 0.2776 |  |
| C_gini_x_demo | 56 | 0.375 | 0.375 | +0.000 | gini_x_v2x_polyarchy | -0.0000 | 0.9728 |  |
| D_urban_x_demo | 61 | 0.381 | 0.350 | +0.031 | urban_pct_x_v2x_polyarchy | +0.0003 | 0.0954 |  |
| E_full_interactions | 56 | 0.447 | 0.418 | +0.030 | log_gni_pc_x_v2x_polyarchy | +0.0058 | 0.1229 |  |
| E_full_interactions | 56 | 0.447 | 0.418 | +0.030 | gini_x_v2x_polyarchy | +0.0003 | 0.6208 |  |


### Outcome: ses_magnitude

| Model | n | R2 | R2_add | Delta_R2 | Interaction | Coef | p | Sig |
|-------|---|----|----|------|------------|------|---|-----|
| A_gni_x_demo | 61 | 0.409 | 0.396 | +0.013 | log_gni_pc_x_v2x_polyarchy | +0.0080 | 0.2718 |  |
| B_educ_x_demo | 61 | 0.385 | 0.366 | +0.018 | mean_yrs_school_x_v2x_polyarchy | +0.0043 | 0.1979 |  |
| C_gini_x_demo | 56 | 0.355 | 0.355 | +0.000 | gini_x_v2x_polyarchy | -0.0002 | 0.8887 |  |
| D_urban_x_demo | 61 | 0.355 | 0.335 | +0.020 | urban_pct_x_v2x_polyarchy | +0.0006 | 0.1899 |  |
| E_full_interactions | 56 | 0.412 | 0.401 | +0.011 | log_gni_pc_x_v2x_polyarchy | +0.0080 | 0.3650 |  |
| E_full_interactions | 56 | 0.412 | 0.401 | +0.011 | gini_x_v2x_polyarchy | +0.0006 | 0.7097 |  |


### Outcome: sig_pct

| Model | n | R2 | R2_add | Delta_R2 | Interaction | Coef | p | Sig |
|-------|---|----|----|------|------------|------|---|-----|
| A_gni_x_demo | 61 | 0.409 | 0.409 | +0.000 | log_gni_pc_x_v2x_polyarchy | +0.5036 | 0.9376 |  |
| B_educ_x_demo | 61 | 0.353 | 0.334 | +0.018 | mean_yrs_school_x_v2x_polyarchy | +3.8104 | 0.2089 |  |
| C_gini_x_demo | 56 | 0.332 | 0.325 | +0.007 | gini_x_v2x_polyarchy | -1.0218 | 0.4519 |  |
| D_urban_x_demo | 61 | 0.319 | 0.316 | +0.003 | urban_pct_x_v2x_polyarchy | +0.2131 | 0.5927 |  |
| E_full_interactions | 56 | 0.408 | 0.405 | +0.003 | log_gni_pc_x_v2x_polyarchy | +2.9108 | 0.7063 |  |
| E_full_interactions | 56 | 0.408 | 0.405 | +0.003 | gini_x_v2x_polyarchy | -0.3746 | 0.7855 |  |


### Outcome: spearman_rho_with_median

| Model | n | R2 | R2_add | Delta_R2 | Interaction | Coef | p | Sig |
|-------|---|----|----|------|------------|------|---|-----|
| A_gni_x_demo | 61 | 0.415 | 0.407 | +0.009 | log_gni_pc_x_v2x_polyarchy | -0.0658 | 0.3663 |  |
| B_educ_x_demo | 61 | 0.374 | 0.374 | +0.000 | mean_yrs_school_x_v2x_polyarchy | -0.0048 | 0.8851 |  |
| C_gini_x_demo | 56 | 0.322 | 0.322 | +0.000 | gini_x_v2x_polyarchy | -0.0027 | 0.8637 |  |
| D_urban_x_demo | 61 | 0.377 | 0.374 | +0.003 | urban_pct_x_v2x_polyarchy | +0.0021 | 0.6289 |  |
| E_full_interactions | 56 | 0.420 | 0.417 | +0.003 | log_gni_pc_x_v2x_polyarchy | -0.0447 | 0.6105 |  |
| E_full_interactions | 56 | 0.420 | 0.417 | +0.003 | gini_x_v2x_polyarchy | +0.0012 | 0.9373 |  |


## 5. Key Findings

### Significant Democracy-Network Relationships

- v2x_egaldem x median_abs_gamma: rho = +0.592 (p = 0.0000)
- v2x_egaldem x spearman_rho_with_median: rho = +0.589 (p = 0.0000)
- v2x_egaldem x ses_magnitude: rho = +0.587 (p = 0.0000)
- v2x_egaldem x sig_pct: rho = +0.574 (p = 0.0000)
- v2x_libdem x median_abs_gamma: rho = +0.572 (p = 0.0000)
- v2x_polyarchy x median_abs_gamma: rho = +0.560 (p = 0.0000)
- v2x_libdem x ses_magnitude: rho = +0.554 (p = 0.0000)
- v2x_polyarchy x spearman_rho_with_median: rho = +0.553 (p = 0.0000)
- v2x_libdem x spearman_rho_with_median: rho = +0.552 (p = 0.0000)
- v2x_libdem x sig_pct: rho = +0.551 (p = 0.0000)
- v2x_polyarchy x ses_magnitude: rho = +0.546 (p = 0.0000)
- v2x_polyarchy x sig_pct: rho = +0.542 (p = 0.0000)
- v2x_egaldem x spectral_entropy: rho = +0.403 (p = 0.0013)
- v2x_libdem x spectral_entropy: rho = +0.380 (p = 0.0025)
- v2x_egaldem x spectral_radius: rho = -0.368 (p = 0.0035)
- v2x_polyarchy x spectral_entropy: rho = +0.364 (p = 0.0040)
- v2x_libdem x spectral_radius: rho = -0.345 (p = 0.0064)
- v2x_polyarchy x spectral_radius: rho = -0.329 (p = 0.0096)

### Democracy vs. Income as Predictors

- **sig_pct**: Baseline R2=0.355, Democracy-only R2=0.297, Full R2=0.405
- **fiedler_value**: Baseline R2=0.076, Democracy-only R2=0.005, Full R2=0.059
- **spearman_rho_with_median**: Baseline R2=0.384, Democracy-only R2=0.326, Full R2=0.417

### Cultural Zone × Democracy Interaction

- **African-Islamic** (n=14): mean democracy=0.333, mean Fiedler=0.685, mean sig%=29.7%
- **Confucian** (n=6): mean democracy=0.518, mean Fiedler=0.723, mean sig%=42.7%
- **English-speaking** (n=5): mean democracy=0.866, mean Fiedler=0.681, mean sig%=65.0%
- **Latin America** (n=12): mean democracy=0.608, mean Fiedler=0.727, mean sig%=35.3%
- **Orthodox/ex-Communist** (n=12): mean democracy=0.448, mean Fiedler=0.719, mean sig%=37.5%
- **South/Southeast Asian** (n=8): mean democracy=0.445, mean Fiedler=0.705, mean sig%=39.6%

### Mexico in Context

- Electoral Democracy: 0.621
- Liberal Democracy: 0.453
- Egalitarian Democracy: 0.420
- GNI per capita: $9.2K
- Gini: 45.4
- Sig edges: 39.9%
- Fiedler: 0.726
- Spearman rho: 0.669

## Output Files

- `macro_indicator_analysis.png` — V-Dem scatter panels
- `macro_indicator_correlations.png` — correlation heatmap
- `macro_indicator_mantel.png` — Mantel test results
- `macro_indicator_democracy_fiedler.png` — democracy x Fiedler deep dive
- `cross_country_geometry/interaction_effects.png` — democracy x macro interaction scatter
- `cross_country_interactions.json` — interaction model results
- `vdem_indicators.json` — V-Dem data cache
- `macro_indicator_data.json` — full merged country-level dataset
