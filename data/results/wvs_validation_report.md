# WVS Construct Validation Report

Generated: 2026-03-13 19:47

## Available Validated Indices (computed from raw items)

| Index | N_valid | Formula basis |
|-------|---------|---------------|
| Y001 | 1729 | WVS pre-computed Post-Materialist 4-item |
| Y002 | 1734 | WVS pre-computed Post-Materialist 12-item |
| Y003 | 954 | WVS pre-computed Autonomy sub-index |
| EVI_Autonomy | 1741 | A029+A038+A040 (child qualities, Welzel 2013) |
| EVI_Equality | 1741 | C001+D059+D060 (gender attitudes, Welzel 2013) |
| EVI_Choice | 1732 | F118+F120+F121 (lifestyle tolerance, Welzel 2013) |
| EVI_Voice | 1741 | E025+E026+E027 (political action, Welzel 2013) |
| EVI_Total | 1741 | Mean of 4 EVI sub-indices (Welzel 2013) |
| Religiosity | 1741 | F034+F028+F029+F024+F025+Q6 (Norris & Inglehart 2004) |
| GenderEgalitarianism | 1741 | C001+D059+D060+D061 (Inglehart & Norris 2003) |
| InstitutionalTrust | 1741 | Mean across E069 battery (Newton & Norris 2000) |
| SelfExpressionValues | 1741 | Q57+Q209+Q182+Y001 (Inglehart-Welzel X-axis approx.) |
| SecularRationalValues | 1741 | F034+Q6+Q45+Q22 (Inglehart-Welzel Y-axis approx.) |

---

## Part 1: Constructs with Validated Equivalents (14)

Spearman ρ with the closest validated WVS index. Target: ρ > 0.70 (good convergent validity).

| Construct | Type | α | N_valid | Validated index | ρ | p | Verdict |
|-----------|------|---|---------|-----------------|---|---|---------|
| `WVS_A|child_qualities_autonomy_self_expression` | formative_index | — | 1741 | EVI_Autonomy | -0.059 | 0.0131 | **poor** |
| `WVS_A|child_qualities_conformity_tradition` | formative_index | — | 1741 | SecularRationalValues | -0.039 | 0.0999 | **poor** |
| `WVS_A|child_qualities_prosocial_diligence` | formative_index | — | 1741 | EVI_Autonomy | -0.088 | 0.0003 | **poor** |
| `WVS_C|job_scarcity_gender_discrimination` | questionable | 0.553 | 1736 | EVI_Equality | +0.405 | 0.0000 | **poor** |
| `WVS_C|job_scarcity_gender_discrimination` | questionable | 0.553 | 1736 | GenderEgalitarianism | +0.317 | 0.0000 | **poor** |
| `WVS_D|gender_role_traditionalism` | good | 0.704 | 1741 | GenderEgalitarianism | +0.146 | 0.0000 | **poor** |
| `WVS_E|confidence_in_civil_society_organizations` | good | 0.770 | 1735 | InstitutionalTrust | -0.731 | 0.0000 | **good** |
| `WVS_E|confidence_in_domestic_institutions` | good | 0.890 | 1741 | InstitutionalTrust | -0.944 | 0.0000 | **good** |
| `WVS_E|confidence_in_international_organizations` | good | 0.912 | 1701 | InstitutionalTrust | -0.759 | 0.0000 | **good** |
| `WVS_E|offline_political_participation` | formative_index | — | 1741 | EVI_Voice | +0.793 | 0.0000 | **good** |
| `WVS_E|postmaterialist_values` | formative_index | — | 1741 | Y001 | -0.527 | 0.0000 | **partial** |
| `WVS_F|life_autonomy_morality_permissiveness` | questionable | 0.580 | 1732 | EVI_Total | +0.366 | 0.0000 | **poor** |
| `WVS_F|religious_practice_and_self_identification` | questionable | 0.608 | 1740 | Religiosity | -0.791 | 0.0000 | **good** |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | good | 0.751 | 1735 | EVI_Total | +0.401 | 0.0000 | **poor** |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | good | 0.751 | 1735 | SecularRationalValues | +0.059 | 0.0140 | **poor** |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | good | 0.751 | 1735 | SelfExpressionValues | +0.330 | 0.0000 | **poor** |
| `WVS_H|acceptance_of_state_surveillance` | good | 0.707 | 1738 | SelfExpressionValues | +0.035 | 0.1467 | **poor** |

### Detailed SES Gradients for Validated Constructs

**WVS_A|child_qualities_autonomy_self_expression** (α=None, formative_index)
  SES: sexo: ρ=-0.004 (p=0.861) | escol: ρ=+0.103 (p=0.000) | Tam_loc: ρ=-0.052 (p=0.030)

**WVS_A|child_qualities_conformity_tradition** (α=None, formative_index)
  SES: sexo: ρ=-0.009 (p=0.718) | escol: ρ=-0.073 (p=0.002) | Tam_loc: ρ=-0.054 (p=0.025)

**WVS_A|child_qualities_prosocial_diligence** (α=None, formative_index)
  SES: sexo: ρ=+0.033 (p=0.170) | escol: ρ=+0.043 (p=0.074) | Tam_loc: ρ=-0.028 (p=0.239)

**WVS_C|job_scarcity_gender_discrimination** (α=0.5529, questionable)
  SES: sexo: ρ=+0.008 (p=0.737) | escol: ρ=+0.096 (p=0.000) | Tam_loc: ρ=+0.008 (p=0.730)

**WVS_D|gender_role_traditionalism** (α=0.7044, good)
  SES: sexo: ρ=+0.060 (p=0.012) | escol: ρ=+0.137 (p=0.000) | Tam_loc: ρ=-0.021 (p=0.377)

**WVS_E|confidence_in_civil_society_organizations** (α=0.7696, good)
  SES: sexo: ρ=+0.017 (p=0.467) | escol: ρ=-0.095 (p=0.000) | Tam_loc: ρ=-0.026 (p=0.276)

**WVS_E|confidence_in_domestic_institutions** (α=0.8905, good)
  SES: sexo: ρ=-0.017 (p=0.486) | escol: ρ=-0.019 (p=0.419) | Tam_loc: ρ=+0.047 (p=0.052)

**WVS_E|confidence_in_international_organizations** (α=0.9119, good)
  SES: sexo: ρ=-0.003 (p=0.906) | escol: ρ=-0.093 (p=0.000) | Tam_loc: ρ=-0.030 (p=0.211)

**WVS_E|offline_political_participation** (α=None, formative_index)
  SES: sexo: ρ=-0.058 (p=0.015) | escol: ρ=+0.113 (p=0.000) | Tam_loc: ρ=+0.046 (p=0.054)

**WVS_E|postmaterialist_values** (α=None, formative_index)
  SES: sexo: ρ=-0.072 (p=0.003) | escol: ρ=+0.044 (p=0.066) | Tam_loc: ρ=+0.002 (p=0.927)

**WVS_F|life_autonomy_morality_permissiveness** (α=0.5799, questionable)
  SES: sexo: ρ=-0.044 (p=0.069) | escol: ρ=+0.136 (p=0.000) | Tam_loc: ρ=+0.110 (p=0.000)

**WVS_F|religious_practice_and_self_identification** (α=0.6079, questionable)
  SES: sexo: ρ=-0.157 (p=0.000) | escol: ρ=+0.150 (p=0.000) | Tam_loc: ρ=+0.043 (p=0.075)

**WVS_F|sexual_and_reproductive_morality_permissiveness** (α=0.7514, good)
  SES: sexo: ρ=-0.042 (p=0.082) | escol: ρ=+0.160 (p=0.000) | Tam_loc: ρ=+0.106 (p=0.000)

**WVS_H|acceptance_of_state_surveillance** (α=0.7072, good)
  SES: sexo: ρ=+0.026 (p=0.284) | escol: ρ=-0.102 (p=0.000) | Tam_loc: ρ=+0.007 (p=0.766)

---

## Part 2: Constructs Without Validated Equivalents (42)

These are either novel to WVS-Mexico context or WVS items not covered by major indices.
Profile: descriptive stats + SES gradient + overlap with los_mex domains.

### `WVS_A|importance_of_life_domains` (formative_index)

**Domain overlap (los_mex):** IDE (Identidad y Valores), FAM
**Items:** 5 | N_valid: 1741
**Descriptive:** mean=6.853, std=2.164, skew=-0.278 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.052* | 0.0305 | weak |
| escol | -0.033 | 0.1694 | weak |
| Tam_loc | -0.094* | 0.0001 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_A|social_intolerance_deviant_behavior` (single_item_tier2)

**Domain overlap (los_mex):** IDE (Identidad y Valores), FAM
**Items:** 1 | N_valid: 1739
**Descriptive:** mean=3.039, std=3.769, skew=1.308 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.045 | 0.0634 | weak |
| escol | -0.016 | 0.5173 | weak |
| Tam_loc | -0.042 | 0.0788 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_A|social_intolerance_outgroups` (α=0.812)

**Domain overlap (los_mex):** IDE (Identidad y Valores), FAM
**Items:** 7 | N_valid: 1741
**Descriptive:** mean=8.625, std=2.222, skew=-1.989 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.024 | 0.3211 | weak |
| escol | +0.102* | 0.0000 | moderate |
| Tam_loc | -0.024 | 0.3282 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_A|subjective_wellbeing` (α=0.290)

**Domain overlap (los_mex):** IDE (Identidad y Valores), FAM
**Items:** 3 | N_valid: 1741
**Descriptive:** mean=7.656, std=1.531, skew=-1.038 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.007 | 0.7806 | weak |
| escol | +0.019 | 0.4240 | weak |
| Tam_loc | -0.014 | 0.5592 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_A|voluntary_association_active_membership` (formative_index)

**Domain overlap (los_mex):** IDE (Identidad y Valores), FAM
**Items:** 12 | N_valid: 1741
**Descriptive:** mean=2.169, std=2.181, skew=2.414 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.005 | 0.8205 | weak |
| escol | +0.006 | 0.7994 | weak |
| Tam_loc | +0.020 | 0.4159 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_A|voluntary_association_belonging` (formative_index)

**Domain overlap (los_mex):** IDE (Identidad y Valores), FAM
**Items:** 12 | N_valid: 1741
**Descriptive:** mean=2.892, std=2.702, skew=1.759 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.003 | 0.9032 | weak |
| escol | +0.050* | 0.0391 | weak |
| Tam_loc | +0.025 | 0.3072 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_C|job_scarcity_nativist_preference` (α=0.736)

**Domain overlap (los_mex):** ECO (Economía)
**Items:** 2 | N_valid: 1727
**Descriptive:** mean=5.197, std=3.284, skew=-0.055 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.019 | 0.4307 | weak |
| escol | +0.075* | 0.0019 | weak |
| Tam_loc | +0.070* | 0.0036 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_C|work_ethic` (α=0.620)

**Domain overlap (los_mex):** ECO (Economía)
**Items:** 3 | N_valid: 1740
**Descriptive:** mean=3.446, std=1.91, skew=0.655 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.009 | 0.6997 | weak |
| escol | +0.149* | 0.0000 | moderate |
| Tam_loc | +0.050* | 0.0368 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_D|familial_duty_obligations` (single_item_tier2)

**Domain overlap (los_mex):** FAM (Familia), ENV (Envejecimiento)
**Items:** 1 | N_valid: 1731
**Descriptive:** mean=3.463, std=2.426, skew=0.809 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.022 | 0.3698 | weak |
| escol | +0.072* | 0.0029 | weak |
| Tam_loc | +0.065* | 0.0071 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_D|female_income_threat_to_marriage` (α=0.743)

**Domain overlap (los_mex):** FAM (Familia), ENV (Envejecimiento)
**Items:** 2 | N_valid: 1725
**Descriptive:** mean=4.966, std=3.305, skew=0.075 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.084* | 0.0005 | weak |
| escol | +0.070* | 0.0035 | weak |
| Tam_loc | +0.029 | 0.2255 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|authoritarian_governance_tolerance` (single_item_tier2)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 1 | N_valid: 1691
**Descriptive:** mean=4.136, std=2.742, skew=0.454 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.019 | 0.4344 | weak |
| escol | -0.064* | 0.0085 | weak |
| Tam_loc | -0.041 | 0.0921 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|autocracy_support` (α=0.499)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 4 | N_valid: 1736
**Descriptive:** mean=5.121, std=1.858, skew=0.128 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.005 | 0.8458 | weak |
| escol | +0.101* | 0.0000 | moderate |
| Tam_loc | +0.025 | 0.3051 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|democratic_system_evaluation` (formative_index)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 5 | N_valid: 1741
**Descriptive:** mean=3.108, std=2.141, skew=0.776 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.062* | 0.0091 | weak |
| escol | +0.047 | 0.0516 | weak |
| Tam_loc | +0.010 | 0.6746 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|democratic_values_importance` (α=0.670)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 5 | N_valid: 1727
**Descriptive:** mean=5.77, std=2.053, skew=-0.061 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.011 | 0.6393 | weak |
| escol | -0.013 | 0.5826 | weak |
| Tam_loc | -0.034 | 0.1562 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|economic_ideology` (α=0.428)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 4 | N_valid: 1734
**Descriptive:** mean=5.252, std=1.859, skew=-0.079 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.012 | 0.6215 | weak |
| escol | +0.018 | 0.4474 | weak |
| Tam_loc | -0.038 | 0.1177 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|electoral_integrity` (α=0.348)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 10 | N_valid: 1729
**Descriptive:** mean=4.993, std=1.264, skew=0.109 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.028 | 0.2366 | weak |
| escol | -0.067* | 0.0053 | weak |
| Tam_loc | -0.055* | 0.0232 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|international_organization_knowledge` (formative_index)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 3 | N_valid: 1741
**Descriptive:** mean=2.42, std=2.136, skew=1.405 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.022 | 0.3632 | weak |
| escol | +0.069* | 0.0043 | weak |
| Tam_loc | -0.033 | 0.1769 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|online_political_participation` (formative_index)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 4 | N_valid: 1741
**Descriptive:** mean=1.547, std=1.442, skew=3.276 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.062* | 0.0097 | weak |
| escol | +0.174* | 0.0000 | moderate |
| Tam_loc | +0.064* | 0.0078 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Meaningful SES gradients → likely to show significant DR bridge edges

### `WVS_E|perceived_corruption` (formative_index)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 8 | N_valid: 1741
**Descriptive:** mean=1.578, std=1.019, skew=3.006 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.010 | 0.6720 | weak |
| escol | -0.008 | 0.7418 | weak |
| Tam_loc | -0.024 | 0.3130 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|political_information_sources` (formative_index)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 8 | N_valid: 1741
**Descriptive:** mean=3.702, std=2.268, skew=0.705 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.048* | 0.0436 | weak |
| escol | +0.250* | 0.0000 | strong |
| Tam_loc | +0.040 | 0.0997 | weak |

**Bridge expectation:**
  - Meaningful SES gradients → likely to show significant DR bridge edges

### `WVS_E|science_technology_optimism` (α=0.598)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 3 | N_valid: 1737
**Descriptive:** mean=6.935, std=2.063, skew=-0.534 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.080* | 0.0008 | weak |
| escol | +0.125* | 0.0000 | moderate |
| Tam_loc | +0.043 | 0.0758 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|societal_change_attitudes` (single_item_tier2)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 1 | N_valid: 1734
**Descriptive:** mean=5.767, std=3.938, skew=-0.115 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.047 | 0.0514 | weak |
| escol | +0.039 | 0.1063 | weak |
| Tam_loc | -0.049* | 0.0430 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_E|voting_participation` (α=0.869)

**Domain overlap (los_mex):** CUL (Cultura Política), FED, JUS, COR
**Items:** 2 | N_valid: 1737
**Descriptive:** mean=2.455, std=2.118, skew=1.434 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.026 | 0.2768 | weak |
| escol | -0.011 | 0.6333 | weak |
| Tam_loc | +0.026 | 0.2868 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_F|civic_dishonesty_tolerance` (α=0.653)

**Domain overlap (los_mex):** REL (Religión)
**Items:** 5 | N_valid: 1738
**Descriptive:** mean=3.392, std=1.781, skew=0.674 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.056* | 0.0202 | weak |
| escol | -0.027 | 0.2701 | weak |
| Tam_loc | +0.069* | 0.0044 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_F|religion_versus_secularism_orientation` (α=0.361)

**Domain overlap (los_mex):** REL (Religión)
**Items:** 2 | N_valid: 1736
**Descriptive:** mean=8.836, std=2.369, skew=-1.937 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.014 | 0.5653 | weak |
| escol | +0.087* | 0.0003 | weak |
| Tam_loc | +0.005 | 0.8210 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_F|religious_belief` (α=-0.250)

**Domain overlap (los_mex):** REL (Religión)
**Items:** 5 | N_valid: 1741
**Descriptive:** mean=4.442, std=0.938, skew=-0.572 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.019 | 0.4237 | weak |
| escol | -0.115* | 0.0000 | moderate |
| Tam_loc | -0.032 | 0.1789 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)
  - Very low variance → ceiling/floor effect, CI may be wide

### `WVS_F|religious_exclusivism` (α=0.691)

**Domain overlap (los_mex):** REL (Religión)
**Items:** 2 | N_valid: 1725
**Descriptive:** mean=6.114, std=2.593, skew=-0.224 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.076* | 0.0015 | weak |
| escol | +0.233* | 0.0000 | strong |
| Tam_loc | +0.036 | 0.1387 | weak |

**Bridge expectation:**
  - Meaningful SES gradients → likely to show significant DR bridge edges

### `WVS_F|violence_tolerance` (α=0.771)

**Domain overlap (los_mex):** REL (Religión)
**Items:** 4 | N_valid: 1734
**Descriptive:** mean=2.504, std=1.814, skew=1.457 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.037 | 0.1230 | weak |
| escol | -0.018 | 0.4669 | weak |
| Tam_loc | +0.041 | 0.0916 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_G|immigrant_origin_status` (formative_index)

**Domain overlap (los_mex):** IDE (Identidad), GLO, MIG
**Items:** 3 | N_valid: 1741
**Descriptive:** mean=1.0, std=0.0, skew=0.0 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +nan | nan | weak |
| escol | +nan | nan | weak |
| Tam_loc | +nan | nan | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)
  - Very low variance → ceiling/floor effect, CI may be wide

### `WVS_G|multilevel_place_attachment` (formative_index)

**Domain overlap (los_mex):** IDE (Identidad), GLO, MIG
**Items:** 5 | N_valid: 1741
**Descriptive:** mean=4.968, std=3.141, skew=0.153 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.071* | 0.0030 | weak |
| escol | +0.017 | 0.4720 | weak |
| Tam_loc | -0.130* | 0.0000 | moderate |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_G|outgroup_trust` (α=0.769)

**Domain overlap (los_mex):** IDE (Identidad), GLO, MIG
**Items:** 4 | N_valid: 1741
**Descriptive:** mean=3.854, std=2.005, skew=0.659 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.028 | 0.2468 | weak |
| escol | +0.101* | 0.0000 | moderate |
| Tam_loc | +0.030 | 0.2130 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_G|perceived_negative_effects_of_immigration` (α=0.744)

**Domain overlap (los_mex):** IDE (Identidad), GLO, MIG
**Items:** 4 | N_valid: 1729
**Descriptive:** mean=5.648, std=2.941, skew=-0.098 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.006 | 0.8033 | weak |
| escol | -0.084* | 0.0005 | weak |
| Tam_loc | -0.029 | 0.2261 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_G|perceived_positive_effects_of_immigration` (α=0.518)

**Domain overlap (los_mex):** IDE (Identidad), GLO, MIG
**Items:** 4 | N_valid: 1732
**Descriptive:** mean=4.845, std=2.429, skew=0.273 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.027 | 0.2603 | weak |
| escol | -0.012 | 0.6229 | weak |
| Tam_loc | +0.012 | 0.6315 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_H|basic_needs_deprivation` (α=0.626)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 3 | N_valid: 1741
**Descriptive:** mean=2.913, std=1.939, skew=0.888 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.085* | 0.0004 | weak |
| escol | -0.213* | 0.0000 | strong |
| Tam_loc | -0.024 | 0.3276 | weak |

**Bridge expectation:**
  - Meaningful SES gradients → likely to show significant DR bridge edges

### `WVS_H|crime_victimization` (formative_index)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 2 | N_valid: 1741
**Descriptive:** mean=3.916, std=3.647, skew=0.724 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.038 | 0.1102 | weak |
| escol | +0.155* | 0.0000 | moderate |
| Tam_loc | +0.086* | 0.0004 | weak |

**Bridge expectation:**
  - Meaningful SES gradients → likely to show significant DR bridge edges

### `WVS_H|existential_threat_worry` (α=0.909)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 3 | N_valid: 1739
**Descriptive:** mean=2.337, std=2.428, skew=1.838 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.084* | 0.0004 | weak |
| escol | +0.063* | 0.0089 | weak |
| Tam_loc | +0.029 | 0.2316 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_H|freedom_security_tradeoff_perception` (α=0.190)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 2 | N_valid: 1739
**Descriptive:** mean=6.276, std=3.173, skew=-0.257 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.050* | 0.0374 | weak |
| escol | +0.044 | 0.0647 | weak |
| Tam_loc | -0.018 | 0.4506 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_H|institutional_threat_perception` (α=0.663)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 2 | N_valid: 1735
**Descriptive:** mean=7.581, std=2.62, skew=-0.919 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.008 | 0.7521 | weak |
| escol | -0.005 | 0.8500 | weak |
| Tam_loc | -0.099* | 0.0000 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_H|neighborhood_disorder_and_crime` (α=0.827)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 5 | N_valid: 1741
**Descriptive:** mean=5.171, std=2.531, skew=0.037 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.014 | 0.5719 | weak |
| escol | +0.010 | 0.6708 | weak |
| Tam_loc | -0.159* | 0.0000 | moderate |

**Bridge expectation:**
  - Meaningful SES gradients → likely to show significant DR bridge edges

### `WVS_H|precautionary_security_behaviors` (formative_index)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 3 | N_valid: 1741
**Descriptive:** mean=5.725, std=2.591, skew=-0.618 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.004 | 0.8827 | weak |
| escol | +0.057* | 0.0168 | weak |
| Tam_loc | +0.112* | 0.0000 | moderate |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_H|socioeconomic_insecurity_worry` (α=0.683)

**Domain overlap (los_mex):** SEG (Seguridad), COR (Corrupción)
**Items:** 2 | N_valid: 1739
**Descriptive:** mean=2.184, std=2.169, skew=1.977 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | -0.016 | 0.4944 | weak |
| escol | -0.035 | 0.1440 | weak |
| Tam_loc | +0.042 | 0.0813 | weak |

**Bridge expectation:**
  - Highly skewed distribution → may need ordinal treatment in bridge
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

### `WVS_I|science_skepticism` (α=0.333)

**Domain overlap (los_mex):** CIE (Ciencia y Tecnología)
**Items:** 2 | N_valid: 1735
**Descriptive:** mean=6.095, std=2.298, skew=-0.208 (scale 1–10)

**SES gradient:**

| SES variable | Spearman ρ | p-value | Interpretation |
|---|---|---|---|
| sexo | +0.061* | 0.0117 | weak |
| escol | -0.062* | 0.0101 | weak |
| Tam_loc | -0.075* | 0.0020 | weak |

**Bridge expectation:**
  - Weak SES gradients → expected γ ≈ 0 in bridge sweep (SES-independent construct)

---

## Part 3: Aggregate Validation Performance

| Metric | Value |
|--------|-------|
| Constructs with validated equivalent | 14 |
| Convergent validity tests | 17 |
| Good (ρ > 0.70) | 5 |
| Partial (0.50–0.70) | 1 |
| Poor (ρ < 0.50) | 11 |
| Mean \|ρ\| | 0.399 |
| Median \|ρ\| | 0.366 |

**Interpretation**: Mean |ρ| > 0.70 = our LLM clustering replicates academic indices well. Poor performers should be checked against the coherence review for potential item revision.

## Part 4: Constructs With No WVS Equivalent — What to Expect in the DR Bridge

Constructs without validated equivalents cluster into two groups:

**Group A — Novel WVS constructs** (items exist in WVS but no published scale):
- Expected: some will show significant DR bridge edges with los_mex (especially if SES gradient is present)
- Validation path: compare to los_mex constructs in the same semantic domain via anchor discovery

**Group B — Single-item tier2 constructs**:
- Expected: wider CIs in DR bridge sweep (less reliable measurement = more noise)
- These are included for breadth but should be interpreted cautiously

Key diagnostic: SES gradient ρ with escol (education) is the best predictor of DR bridge significance.
Constructs with |ρ(escol)| > 0.15 are strong candidates for significant bridge edges.
