# Bridge Comparison Report — All Six Methods

*Generated 2026-03-04 08:53*

## Run Parameters

- `n_sim` (baseline / residual / bayesian): 2000
- `n_bootstrap` eco / bayesian draws / mrp / DR: 200 / 200 / 150 / 25
- `n_cells` (residual):      20
- Ecological `cell_cols`:    ['escol', 'edad']
- MRP `cell_cols`:           ['escol', 'edad', 'sexo']
- Domain pairs attempted:    276
- Domain pairs with results: 276
- Elapsed:                   22397s

## Summary Statistics

| Method | N pairs | Mean | IQR (25–75) | Range |
|--------|---------|------|-------------|-------|
| Baseline V (sim) | 276 | 0.066 | [0.058, 0.072] | [0.040, 0.095] |
| Residual V (within-cell) | 276 | 0.052 | [0.047, 0.057] | [0.036, 0.069] |
| Eco |ρ| (geographic) | 276 | 0.113 | [0.035, 0.154] | [0.000, 0.542] |
| Bayesian γ (Laplace post.) | 276 | -0.001 | [-0.008, 0.006] | [-0.047, 0.045] |
| MRP γ (shrinkage cells) | 253 | 0.002 | [-0.001, 0.002] | [-0.025, 0.108] |
| DR γ (AIPW) | 276 | -0.001 | [-0.013, 0.012] | [-0.078, 0.095] |
| DR KS overlap | 276 | 0.300 | [0.145, 0.567] | [0.050, 0.697] |
| SES fraction (resid/base) | 276 | 0.842 | [0.741, 0.932] | [0.528, 1.323] |

## Top 20 Domain Pairs by Baseline V

| Domain pair | Base V | Resid V | Bay γ | MRP γ | DR γ | DR KS |
|-------------|--------|---------|-------|-------|------|-------|
| DER×IND | 0.095 | 0.066 | -0.006 | -0.002 | -0.012 | 0.220 |
| CUL×POB | 0.095 | 0.063 | +0.039 | +0.001 | +0.076 | 0.613 |
| ECO×JUS | 0.095 | 0.069 | -0.007 | +0.004 | -0.019 | 0.188 |
| IND×SOC | 0.094 | 0.061 | -0.006 | -0.002 | +0.009 | 0.643 |
| IND×POB | 0.094 | 0.058 | +0.001 | +0.002 | -0.015 | 0.618 |
| ENV×IND | 0.092 | 0.058 | -0.004 | +0.001 | +0.034 | 0.197 |
| ECO×IND | 0.092 | 0.064 | +0.009 | +0.002 | +0.013 | 0.076 |
| HAB×IND | 0.092 | 0.049 | +0.007 | +0.001 | +0.032 | 0.159 |
| CUL×IND | 0.090 | 0.061 | -0.014 | +0.002 | +0.002 | 0.205 |
| FED×IND | 0.087 | 0.054 | -0.013 | -0.001 | -0.044 | 0.182 |
| CUL×DER | 0.087 | 0.063 | +0.015 | +0.001 | +0.020 | 0.121 |
| DER×HAB | 0.086 | 0.057 | -0.002 | -0.001 | -0.005 | 0.123 |
| FED×POB | 0.085 | 0.044 | +0.045 | -0.000 | +0.095 | 0.636 |
| ECO×EDU | 0.085 | 0.055 | +0.001 | +0.108 | +0.013 | 0.149 |
| IND×REL | 0.085 | 0.050 | -0.015 | +0.000 | -0.046 | 0.180 |
| ECO×POB | 0.084 | 0.048 | -0.015 | +0.007 | -0.018 | 0.650 |
| CUL×ENV | 0.084 | 0.064 | +0.012 | +0.002 | +0.035 | 0.158 |
| DER×ENV | 0.083 | 0.054 | -0.002 | -0.001 | -0.028 | 0.097 |
| EDU×JUS | 0.083 | 0.066 | +0.008 | +0.005 | +0.003 | 0.315 |
| IND×MIG | 0.082 | 0.050 | -0.003 | +0.001 | -0.002 | 0.142 |

## Weakest 10 Domain Pairs (Baseline V)

| Domain pair | Base V | Resid V | Bay γ | MRP γ | DR γ |
|-------------|--------|---------|-------|-------|------|
| GEN×MED | 0.048 | 0.050 | +0.001 | +0.001 | -0.000 |
| ECO×FAM | 0.048 | 0.048 | +0.009 | — | +0.013 |
| FED×MED | 0.047 | 0.046 | +0.001 | -0.002 | +0.008 |
| FAM×NIN | 0.046 | 0.046 | -0.001 | — | -0.006 |
| COR×SAL | 0.046 | 0.043 | +0.001 | +0.000 | +0.005 |
| FAM×REL | 0.045 | 0.039 | -0.000 | — | +0.004 |
| ENV×FAM | 0.044 | 0.046 | -0.006 | — | -0.008 |
| FAM×HAB | 0.044 | 0.045 | +0.005 | — | +0.006 |
| FAM×SAL | 0.040 | 0.041 | -0.002 | — | -0.003 |
| FAM×POB | 0.040 | 0.053 | -0.003 | — | -0.007 |

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