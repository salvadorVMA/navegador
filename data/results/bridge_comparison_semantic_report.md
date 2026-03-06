# Bridge Comparison Report — All Six Methods

*Generated 2026-03-05 05:45*

## Run Parameters

- `n_sim` (baseline / residual / bayesian): 500
- `n_bootstrap` eco / bayesian draws / mrp / DR: 50 / 100 / 50 / 10
- `n_cells` (residual):      20
- Ecological `cell_cols`:    ['escol', 'edad']
- MRP `cell_cols`:           ['escol', 'edad', 'sexo']
- Domain pairs attempted:    276
- Domain pairs with results: 276
- Elapsed:                   26870s

## Summary Statistics

| Method | N pairs | Mean | IQR (25–75) | Range |
|--------|---------|------|-------------|-------|
| Baseline V (sim) | 276 | 0.103 | [0.098, 0.107] | [0.084, 0.124] |
| Residual V (within-cell) | 276 | 0.095 | [0.091, 0.099] | [0.072, 0.112] |
| Eco |ρ| (geographic) | 276 | 0.050 | [0.016, 0.065] | [0.000, 0.365] |
| Bayesian γ (Laplace post.) | 276 | -0.000 | [-0.004, 0.005] | [-0.030, 0.026] |
| MRP γ (shrinkage cells) | 253 | -0.000 | [-0.001, 0.001] | [-0.044, 0.017] |
| DR γ (AIPW) | 276 | 0.000 | [-0.005, 0.005] | [-0.039, 0.034] |
| DR KS overlap | 276 | 0.300 | [0.145, 0.569] | [0.052, 0.697] |
| SES fraction (resid/base) | 276 | 0.970 | [0.911, 1.027] | [0.758, 1.318] |

## Top 20 Domain Pairs by Baseline V

| Domain pair | Base V | Resid V | Bay γ | MRP γ | DR γ | DR KS |
|-------------|--------|---------|-------|-------|------|-------|
| CIE×EDU | 0.124 | 0.095 | -0.007 | +0.009 | -0.004 | 0.075 |
| ECO×GEN | 0.122 | 0.100 | -0.030 | -0.005 | -0.039 | 0.164 |
| CIE×ECO | 0.120 | 0.104 | -0.001 | -0.001 | +0.008 | 0.163 |
| EDU×ENV | 0.119 | 0.109 | +0.011 | -0.002 | -0.002 | 0.341 |
| EDU×SEG | 0.119 | 0.102 | -0.010 | -0.001 | -0.016 | 0.141 |
| CIE×SOC | 0.119 | 0.097 | +0.005 | +0.000 | +0.004 | 0.635 |
| CIE×REL | 0.118 | 0.091 | +0.003 | +0.001 | -0.000 | 0.176 |
| ECO×EDU | 0.118 | 0.097 | -0.006 | -0.044 | -0.018 | 0.149 |
| ECO×REL | 0.118 | 0.099 | +0.002 | -0.004 | +0.007 | 0.177 |
| ENV×IND | 0.117 | 0.108 | +0.003 | +0.000 | +0.002 | 0.201 |
| ECO×FED | 0.116 | 0.097 | -0.001 | +0.013 | +0.003 | 0.160 |
| ECO×SAL | 0.116 | 0.099 | +0.003 | +0.002 | +0.017 | 0.545 |
| JUS×SOC | 0.116 | 0.091 | -0.006 | +0.001 | +0.009 | 0.630 |
| EDU×FED | 0.116 | 0.098 | +0.007 | -0.019 | +0.010 | 0.277 |
| SEG×SOC | 0.115 | 0.092 | +0.005 | -0.001 | +0.013 | 0.621 |
| EDU×REL | 0.115 | 0.091 | -0.003 | +0.009 | -0.010 | 0.158 |
| GEN×SOC | 0.114 | 0.105 | -0.002 | -0.001 | -0.003 | 0.629 |
| REL×SEG | 0.114 | 0.093 | -0.007 | -0.000 | -0.007 | 0.206 |
| REL×SOC | 0.114 | 0.098 | +0.005 | +0.001 | +0.001 | 0.633 |
| DER×ENV | 0.114 | 0.094 | +0.011 | +0.001 | +0.008 | 0.090 |

## Weakest 10 Domain Pairs (Baseline V)

| Domain pair | Base V | Resid V | Bay γ | MRP γ | DR γ |
|-------------|--------|---------|-------|-------|------|
| EDU×FAM | 0.091 | 0.090 | +0.003 | — | +0.004 |
| CUL×FAM | 0.090 | 0.091 | +0.002 | — | +0.002 |
| FAM×NIN | 0.090 | 0.072 | +0.001 | — | +0.005 |
| COR×MIG | 0.090 | 0.083 | +0.006 | -0.001 | +0.012 |
| COR×FAM | 0.089 | 0.087 | -0.001 | — | +0.000 |
| FAM×GLO | 0.088 | 0.100 | -0.000 | — | +0.001 |
| DER×FAM | 0.087 | 0.086 | +0.001 | — | +0.003 |
| FAM×SAL | 0.086 | 0.090 | -0.003 | — | -0.004 |
| MED×MIG | 0.086 | 0.095 | -0.006 | +0.002 | +0.003 |
| FAM×MED | 0.084 | 0.092 | -0.001 | — | +0.000 |

## Method Interpretation Guide

| Signal | What it means |
|--------|---------------|
| High baseline V + high residual V | Strong conceptual link, not just SES confounding |
| High baseline V + low residual V  | Association is SES-mediated (pure confounding) |
| High |Eco ρ| + low baseline V     | Geographic pattern not captured by individual SES |
| Bayesian CI excludes 0            | Robust association under parameter uncertainty |
| MRP γ ≈ baseline V                | Cell-level pattern consistent with simulation |
| DR KS > 0.3                       | Poor SES overlap: DR weights less reliable |
| DR γ differs from baseline V      | Outcome model may be misspecified (one is wrong) |

---
*Full results: `/workspaces/navegador/data/results/bridge_comparison_results.json`*