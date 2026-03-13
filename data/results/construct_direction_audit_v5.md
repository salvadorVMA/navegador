# Construct Direction & Sentinel Audit — V5

Generated: 2026-03-13 20:27

## Summary

| Metric | Count |
|--------|-------|
| Constructs audited | 95 |
| Constructs with ≥1 flag | 49 |
| FLAG_DIRECTION (item r < −0.10) | 0 |
| FLAG_WEAK (\|r\| < 0.05) | 0 |
| FLAG_COVERAGE (n < 600) | 1 |
| FLAG_SENTINEL_PARTIAL | 0 |
| FLAG_DOMINANCE (>50% one code) | 49 |
| FLAG_CARDINALITY (ratio >3×) | 0 |
| FLAG_SCALE_RANGE | 0 |

## All Constructs

| Key | Type | α | N | Flags |
|-----|------|---|---|-------|
| `CIE|household_science_cultural_capital` | good | 0.804 | 1200 | FLAG_DOMINANCE: p3_2(79%@2.0), p3_3(72%@2.0), p3_6(54%@2.0), p3_8(51%@2.0), p4(52%@2.0), p5(53%@2.0) |
| `CIE|institutional_trust_in_science` | questionable | 0.637 | 1200 | FLAG_DOMINANCE: p50_1(58%@1.0) |
| `CIE|perceived_societal_value_of_science_technology` | questionable | 0.508 | 1110 | FLAG_DOMINANCE: p44_1(50%@1.0) |
| `CIE|science_technology_interest_engagement` | good | 0.827 | 1194 | ✓ |
| `CIE|science_technology_self_efficacy` | questionable | 0.699 | 1104 | ✓ |
| `COR|civic_enforcement_norms` | questionable | 0.525 | 1139 | FLAG_DOMINANCE: p22(55%@1.0) |
| `COR|corruption_perception` | tier3_caveat | 0.487 | 1111 | FLAG_DOMINANCE: p2(77%@1.0), p3(68%@1.0), p15(92%@1.0), p16(74%@1.0) |
| `COR|reporting_behavior_and_barriers` | formative_index | 0.052 | 1200 | ✓ |
| `COR|tolerance_of_corrupt_behavior` | single_item_tier2 | 0.382 | 1200 | ✓ |
| `CUL|authoritarian_predisposition` | tier3_caveat | 0.495 | 1200 | FLAG_DOMINANCE: p64(63%@2.0) |
| `CUL|democratic_legitimacy_support` | questionable | 0.582 | 1200 | FLAG_DOMINANCE: p31(54%@1.0), p36(73%@2.0) |
| `CUL|institutional_trust_and_electoral_confidence` | tier3_caveat | 0.486 | 1200 | ✓ |
| `CUL|perceived_political_influence_of_actors` | good | 0.870 | 1200 | FLAG_DOMINANCE: p84_1(60%@1.0), p84_2(64%@1.0), p84_3(66%@1.0), p84_8(54%@1.0) |
| `CUL|political_efficacy_and_engagement` | questionable | 0.594 | 1200 | ✓ |
| `DEP|attitudes_toward_cultural_openness_and_foreign_influence` | questionable | 0.516 | 1200 | FLAG_DOMINANCE: p25(67%@2.0), p28(56%@1.0), p32(75%@1.0) |
| `DEP|cultural_identity_and_heritage` | tier3_caveat | 0.415 | 1200 | FLAG_DOMINANCE: p48(94%@1.0), p49(81%@3.0), p50(89%@2.0), p54(63%@2.0) |
| `DEP|cultural_socialization_in_childhood` | tier3_caveat | 0.480 | 1188 | FLAG_DOMINANCE: p11(54%@1.0) |
| `DEP|reading_engagement_and_literacy` | tier3_caveat | 0.365 | 1200 | FLAG_DOMINANCE: p15a_1(54%@2.0), p15a_2(60%@2.0), p15a_3(64%@2.0) |
| `DER|authoritarian_security_tradeoff` | questionable | 0.540 | 1200 | FLAG_DOMINANCE: p17(53%@4.0) |
| `DER|institutional_trust_justice` | good | 0.713 | 1200 | FLAG_DOMINANCE: p21(50%@2.0) |
| `DER|perceived_discrimination_social_exclusion` | questionable | 0.581 | 1200 | FLAG_DOMINANCE: p35_1(70%@2.0), p39(58%@2.0), p44(73%@2.0) |
| `DER|rights_awareness_personal_experience` | questionable | 0.554 | 1200 | FLAG_DOMINANCE: p45(59%@2.0), p54(83%@2.0) |
| `DER|social_rights_service_quality` | questionable | 0.628 | 1200 | ✓ |
| `ECO|economic_wellbeing_perception` | tier3_caveat | 0.489 | 1200 | ✓ |
| `ECO|job_search_and_employment_precarity` | formative_index | — | 709 | ✓ |
| `ECO|labor_union_attitudes` | questionable | 0.607 | 1200 | ✓ |
| `EDU|digital_and_cultural_capital` | good | 0.745 | 1199 | FLAG_DOMINANCE: p47_3(54%@2.0), p47_4(58%@2.0) |
| `EDU|educational_returns_belief` | questionable | 0.607 | 1194 | FLAG_DOMINANCE: p37(80%@1.0), p55_3(81%@1.0), p55_4(80%@1.0), p55_5(78%@1.0) |
| `EDU|perceived_education_quality` | tier3_caveat | 0.470 | 1199 | ✓ |
| `EDU|school_environment_quality` | formative_index | — | 997 | ✓ |
| `EDU|social_media_engagement` | new_construct | — | 1199 | FLAG_DOMINANCE: p48_1(52%@1.0), p48_3(55%@2.0), p44_5(61%@5.0) |
| `ENV|ageism_and_negative_stereotypes` | questionable | 0.518 | 1200 | ✓ |
| `ENV|assessment_of_older_adult_wellbeing_and_social_conditions` | questionable | 0.532 | 1200 | ✓ |
| `ENV|state_and_family_responsibility_for_elder_care` | tier3_caveat | 0.452 | 1200 | ✓ |
| `FAM|conjugal_union_attitudes` | questionable | 0.504 | 1200 | FLAG_DOMINANCE: p23(64%@1.0), p35(64%@1.0) |
| `FAM|family_cohesion_quality` | questionable | 0.522 | 1200 | FLAG_DOMINANCE: p25(56%@2.0), p26(52%@2.0) |
| `FAM|family_value_transmission` | tier3_caveat | 0.457 | 1200 | ✓ |
| `FAM|ideal_family_normativity` | tier3_caveat | 0.451 | 972 | FLAG_DOMINANCE: p13(70%@1.0) |
| `FAM|intergenerational_obligations` | tier3_caveat | 0.489 | 1200 | FLAG_DOMINANCE: p29(78%@1.0), p64(81%@1.0) |
| `FED|fiscal_and_service_federalism_preferences` | questionable | 0.603 | 1200 | FLAG_DOMINANCE: p33(61%@1.0), p60(58%@2.0) |
| `FED|legal_uniformity_preference` | good | 0.948 | 1200 | FLAG_DOMINANCE: p53_1(65%@1.0), p53_2(69%@1.0), p53_3(65%@1.0), p53_4(65%@1.0), p53_5(63%@1.0), p53_6(63%@1.0) |
| `FED|perceived_representativeness` | good | 0.916 | 1200 | ✓ |
| `FED|political_interest_and_engagement` | questionable | 0.634 | 1200 | FLAG_DOMINANCE: p5(51%@2.0) |
| `FED|security_governance_preferences` | questionable | 0.693 | 1200 | ✓ |
| `GEN|intimate_partner_power_dynamics` | tier3_caveat | 0.407 | 427 | FLAG_COVERAGE(n=427); FLAG_DOMINANCE: p19(64%@3.0), p23_1(59%@3.0), p23_5(61%@3.0) |
| `GEN|sexual_and_reproductive_attitudes` | single_item_tier2 | 0.353 | 1200 | ✓ |
| `GEN|tolerance_of_gender_based_violence` | single_item_tier2 | 0.336 | 1200 | ✓ |
| `GEN|traditional_gender_role_attitudes` | questionable | 0.506 | 1200 | ✓ |
| `GLO|economic_globalization_attitudes` | questionable | 0.694 | 1123 | FLAG_DOMINANCE: p46_1(70%@1.0), p47(56%@1.0), p31_1(61%@1.0) |
| `GLO|international_institutional_engagement` | questionable | 0.545 | 1200 | FLAG_DOMINANCE: p52_1(81%@1.0), p57(62%@1.0), p60_1(74%@1.0), p63_1(88%@1.0) |
| `GLO|transnational_exposure` | single_item_tier2 | 0.334 | 1200 | ✓ |
| `HAB|basic_services_access` | questionable | 0.530 | 1127 | FLAG_DOMINANCE: p7(78%@1.0), p7_1(66%@1.0), p10(84%@1.0), p11(99%@1.0) |
| `HAB|household_asset_endowment` | good | 0.725 | 1200 | FLAG_DOMINANCE: p36_1(78%@1.0), p36_2(97%@1.0), p36_4(89%@1.0), p36_5(78%@1.0), p36_6(90%@1.0), p36_8(72%@1.0), p36_9(59%@2.0), p36_10(63%@2.0), p36_18(53%@1.0), p36_21(93%@2.0), p36_22(96%@2.0), p36_29(80%@2.0) |
| `HAB|housing_tenure_security` | formative_index | -0.136 | 1200 | ✓ |
| `HAB|structural_housing_quality` | questionable | 0.511 | 1197 | FLAG_DOMINANCE: p1(79%@9.0), p2(84%@7.0), p3(58%@2.0) |
| `IDE|moral_normative_conservatism` | questionable | 0.507 | 1200 | ✓ |
| `IDE|national_identity_pride` | single_item_tier2 | 0.376 | 1200 | ✓ |
| `IDE|personal_optimism_efficacy` | tier3_caveat | 0.405 | 1200 | ✓ |
| `IDE|tolerance_social_diversity` | questionable | 0.588 | 1200 | FLAG_DOMINANCE: p9(70%@2.0), p73_1(57%@1.0) |
| `IND|national_economic_outlook` | good | 0.717 | 1111 | ✓ |
| `IND|perceived_indigenous_discrimination` | tier3_caveat | 0.401 | 1174 | FLAG_DOMINANCE: p21(72%@1.0), p25_1(83%@1.0), p34_1(63%@1.0) |
| `IND|social_distance_toward_indigenous_people` | questionable | 0.510 | 1109 | FLAG_DOMINANCE: p37_1(85%@1.0), p40_1(70%@1.0) |
| `JUS|judicial_institutional_trust` | questionable | 0.649 | 804 | FLAG_DOMINANCE: p33(74%@2.0), p50(60%@2.0) |
| `JUS|law_compliance_motivation` | questionable | 0.516 | 1200 | ✓ |
| `JUS|legal_cynicism_extrajudicial_justice` | questionable | 0.519 | 1200 | ✓ |
| `JUS|police_trust_and_legitimacy` | single_item_tier2 | 0.354 | 1200 | ✓ |
| `MED|climate_change_risk_perception` | single_item_tier2 | 0.362 | 1200 | ✓ |
| `MED|environmental_knowledge_self_efficacy` | questionable | 0.540 | 1057 | ✓ |
| `MED|environmental_problem_salience` | tier3_caveat | 0.467 | 1171 | ✓ |
| `MED|pro_environmental_civic_engagement` | good | 0.796 | 1200 | FLAG_DOMINANCE: p34_1(90%@2.0), p34_2(89%@2.0), p34_3(91%@2.0), p34_4(89%@2.0) |
| `MIG|attitudes_toward_foreigners_in_mexico` | questionable | 0.569 | 1199 | FLAG_DOMINANCE: p48(80%@2.0) |
| `MIG|emigration_intention_likelihood` | tier3_caveat | 0.466 | 1199 | FLAG_DOMINANCE: p15_1(65%@1.0) |
| `MIG|perceived_opportunity_structure` | good | 0.844 | 1199 | ✓ |
| `NIN|children_rights_recognition_and_respect` | single_item_tier2 | 0.376 | 1200 | ✓ |
| `NIN|perceived_situation_of_children_and_youth` | questionable | 0.546 | 1200 | ✓ |
| `NIN|youth_educational_opportunity_and_labor_prospects` | single_item_tier2 | 0.400 | 1200 | ✓ |
| `NIN|youth_participation_and_voice` | questionable | 0.546 | 1200 | FLAG_DOMINANCE: p13(53%@1.0), p39(56%@1.0) |
| `POB|intergenerational_mobility_perception` | questionable | 0.537 | 1097 | FLAG_DOMINANCE: p22(52%@2.0), p23(54%@2.0) |
| `POB|social_policy_preferences` | single_item_tier2 | 0.331 | 1125 | ✓ |
| `POB|subjective_economic_wellbeing_and_agency` | questionable | 0.623 | 1152 | ✓ |
| `REL|church_state_separation` | questionable | 0.568 | 1045 | FLAG_DOMINANCE: p52_1(53%@5.0), p56(54%@5.0), p57(53%@1.0) |
| `REL|personal_religiosity` | good | 0.732 | 968 | FLAG_DOMINANCE: p10(65%@1.0), p12(71%@1.0), p13_1(74%@1.0), p25(59%@1.0) |
| `REL|religious_socialization` | questionable | 0.555 | 1163 | FLAG_DOMINANCE: p5(65%@1.0), p33_1(60%@1.0) |
| `REL|religious_tolerance` | single_item_tier2 | 0.393 | 1077 | ✓ |
| `REL|supernatural_beliefs` | good | 0.900 | 1005 | FLAG_DOMINANCE: p17_1(82%@1.0), p17_2(59%@1.0), p17_4(52%@1.0), p17_5(62%@1.0), p17_6(65%@1.0), p17_7(69%@1.0), p17_8(53%@1.0), p17_9(51%@1.0), p17_11(53%@3.0), p17_13(59%@3.0) |
| `SAL|functional_health_status` | good | 0.723 | 1200 | FLAG_DOMINANCE: p2(73%@3.0), p3(72%@3.0), p4(79%@2.0), p5(83%@2.0) |
| `SAL|health_risk_behaviors` | questionable | 0.539 | 689 | ✓ |
| `SAL|subjective_wellbeing` | questionable | 0.588 | 1200 | FLAG_DOMINANCE: p37(52%@4.0) |
| `SEG|crime_victimization_exposure` | formative_index | 0.609 | 1200 | ✓ |
| `SEG|fear_and_risk_avoidance` | questionable | 0.568 | 1200 | ✓ |
| `SEG|perceived_security_trajectory` | good | 0.802 | 1200 | ✓ |
| `SEG|police_institutional_legitimacy` | tier3_caveat | 0.481 | 1008 | FLAG_DOMINANCE: p28_1(70%@1.0), p29_1(60%@1.0) |
| `SEG|punitive_and_vigilante_attitudes` | questionable | 0.528 | 1200 | ✓ |
| `SOC|media_trust_and_quality_evaluation` | questionable | 0.587 | 1200 | ✓ |
| `SOC|perceived_media_social_impact` | questionable | 0.587 | 1200 | FLAG_DOMINANCE: p60(68%@1.0) |

## Flagged Constructs (49)

### `CIE|household_science_cultural_capital`

**Type**: good  |  **α**: 0.804  |  **N**: 1200  |  **n_items**: 6

**Flags**: FLAG_DOMINANCE: p3_2(79%@2.0), p3_3(72%@2.0), p3_6(54%@2.0), p3_8(51%@2.0), p4(52%@2.0), p5(53%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p3_2` | 0.6017 | 1200 | OK |
| `p3_3` | 0.6048 | 1200 | OK |
| `p3_6` | 0.6591 | 1200 | OK |
| `p3_8` | 0.6691 | 1200 | OK |
| `p4` | 0.7208 | 1200 | OK |
| `p5` | 0.6943 | 1200 | OK |

**Dominant-code items**:

- `p3_2`: 78.8% at code 2.0 (n=1200)
- `p3_3`: 72.3% at code 2.0 (n=1200)
- `p3_6`: 53.7% at code 2.0 (n=1200)
- `p3_8`: 50.8% at code 2.0 (n=1200)
- `p4`: 52.3% at code 2.0 (n=1200)
- `p5`: 53.0% at code 2.0 (n=1200)

---

### `CIE|institutional_trust_in_science`

**Type**: questionable  |  **α**: 0.637  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p50_1(58%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p32_1` | 0.6721 | 1200 | OK |
| `p33` | 0.3740 | 1200 | OK |
| `p40_1` | 0.6720 | 1200 | OK |
| `p50_1` | 0.3156 | 1200 | OK |

**Dominant-code items**:

- `p50_1`: 57.7% at code 1.0 (n=1200)

---

### `CIE|perceived_societal_value_of_science_technology`

**Type**: questionable  |  **α**: 0.508  |  **N**: 1110  |  **n_items**: 5

**Flags**: FLAG_DOMINANCE: p44_1(50%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p34` | 0.4841 | 1110 | OK |
| `p36` | 0.5266 | 1110 | OK |
| `p44_1` | 0.4996 | 1110 | OK |
| `p42_1` | 0.4761 | 1110 | OK |
| `p39_1` | 0.5154 | 1110 | OK |

**Dominant-code items**:

- `p44_1`: 50.3% at code 1.0 (n=1200)

---

### `COR|civic_enforcement_norms`

**Type**: questionable  |  **α**: 0.525  |  **N**: 1139  |  **n_items**: 5

**Flags**: FLAG_DOMINANCE: p22(55%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p20` | 0.4599 | 1139 | OK |
| `p21` | 0.4934 | 1139 | OK |
| `p22` | 0.4421 | 1139 | OK |
| `p23` | 0.7211 | 1139 | OK |
| `p24` | 0.7175 | 1139 | OK |

**Dominant-code items**:

- `p22`: 54.7% at code 1.0 (n=1200)

---

### `COR|corruption_perception`

**Type**: tier3_caveat  |  **α**: 0.487  |  **N**: 1111  |  **n_items**: 5

**Flags**: FLAG_DOMINANCE: p2(77%@1.0), p3(68%@1.0), p15(92%@1.0), p16(74%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p2` | 0.4738 | 1111 | OK |
| `p3` | 0.6199 | 1111 | OK |
| `p15` | 0.1590 | 1111 | OK |
| `p16` | 0.5038 | 1111 | OK |
| `p17` | 0.5455 | 1111 | OK |

**Dominant-code items**:

- `p2`: 77.0% at code 1.0 (n=1200)
- `p3`: 67.7% at code 1.0 (n=1200)
- `p15`: 91.7% at code 1.0 (n=1200)
- `p16`: 73.7% at code 1.0 (n=1111)

---

### `CUL|authoritarian_predisposition`

**Type**: tier3_caveat  |  **α**: 0.495  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p64(63%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p17` | 0.3683 | 1200 | OK |
| `p61` | 0.5875 | 1200 | OK |
| `p64` | 0.5743 | 1200 | OK |
| `p65` | 0.6600 | 1200 | OK |

**Dominant-code items**:

- `p64`: 63.2% at code 2.0 (n=1200)

---

### `CUL|democratic_legitimacy_support`

**Type**: questionable  |  **α**: 0.582  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p31(54%@1.0), p36(73%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p31` | 0.4668 | 1200 | OK |
| `p32` | 0.7678 | 1200 | OK |
| `p35` | 0.6876 | 1200 | OK |
| `p36` | 0.4778 | 1200 | OK |

**Dominant-code items**:

- `p31`: 53.5% at code 1.0 (n=1200)
- `p36`: 73.0% at code 2.0 (n=1200)

---

### `CUL|perceived_political_influence_of_actors`

**Type**: good  |  **α**: 0.870  |  **N**: 1200  |  **n_items**: 7

**Flags**: FLAG_DOMINANCE: p84_1(60%@1.0), p84_2(64%@1.0), p84_3(66%@1.0), p84_8(54%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p84_1` | 0.6133 | 1200 | OK |
| `p84_2` | 0.6232 | 1200 | OK |
| `p84_3` | 0.5828 | 1200 | OK |
| `p84_4` | 0.4767 | 1200 | OK |
| `p84_6` | 0.6580 | 1200 | OK |
| `p84_7` | 0.7377 | 1200 | OK |
| `p84_8` | 0.6906 | 1200 | OK |

**Dominant-code items**:

- `p84_1`: 60.3% at code 1.0 (n=1200)
- `p84_2`: 63.8% at code 1.0 (n=1200)
- `p84_3`: 65.8% at code 1.0 (n=1200)
- `p84_8`: 53.9% at code 1.0 (n=1200)

---

### `DEP|attitudes_toward_cultural_openness_and_foreign_influence`

**Type**: questionable  |  **α**: 0.516  |  **N**: 1200  |  **n_items**: 6

**Flags**: FLAG_DOMINANCE: p25(67%@2.0), p28(56%@1.0), p32(75%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p25` | 0.3582 | 1200 | OK |
| `p26` | 0.4840 | 1200 | OK |
| `p27` | 0.5204 | 1200 | OK |
| `p28` | 0.3567 | 1200 | OK |
| `p31_1` | 0.4493 | 1200 | OK |
| `p32` | 0.2849 | 1200 | OK |

**Dominant-code items**:

- `p25`: 67.1% at code 2.0 (n=1200)
- `p28`: 56.2% at code 1.0 (n=1200)
- `p32`: 74.8% at code 1.0 (n=1200)

---

### `DEP|cultural_identity_and_heritage`

**Type**: tier3_caveat  |  **α**: 0.415  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p48(94%@1.0), p49(81%@3.0), p50(89%@2.0), p54(63%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p48` | 0.0912 | 1200 | OK |
| `p49` | 0.5376 | 1200 | OK |
| `p50` | 0.4418 | 1200 | OK |
| `p54` | 0.7607 | 1200 | OK |

**Dominant-code items**:

- `p48`: 94.1% at code 1.0 (n=1200)
- `p49`: 80.7% at code 3.0 (n=1200)
- `p50`: 88.9% at code 2.0 (n=1200)
- `p54`: 63.0% at code 2.0 (n=1200)

---

### `DEP|cultural_socialization_in_childhood`

**Type**: tier3_caveat  |  **α**: 0.480  |  **N**: 1188  |  **n_items**: 2

**Flags**: FLAG_DOMINANCE: p11(54%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p8` | 0.8990 | 1188 | OK |
| `p11` | 0.7946 | 1188 | OK |

**Dominant-code items**:

- `p11`: 53.8% at code 1.0 (n=1188)

---

### `DEP|reading_engagement_and_literacy`

**Type**: tier3_caveat  |  **α**: 0.365  |  **N**: 1200  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p15a_1(54%@2.0), p15a_2(60%@2.0), p15a_3(64%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p15a_1` | 0.7332 | 1200 | OK |
| `p15a_2` | 0.7718 | 1200 | OK |
| `p15a_3` | 0.7334 | 1200 | OK |

**Dominant-code items**:

- `p15a_1`: 53.9% at code 2.0 (n=1200)
- `p15a_2`: 59.8% at code 2.0 (n=1200)
- `p15a_3`: 63.7% at code 2.0 (n=1200)

---

### `DER|authoritarian_security_tradeoff`

**Type**: questionable  |  **α**: 0.540  |  **N**: 1200  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p17(53%@4.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p9` | 0.6044 | 1200 | OK |
| `p16` | 0.7574 | 1200 | OK |
| `p17` | 0.7259 | 1200 | OK |

**Dominant-code items**:

- `p17`: 52.7% at code 4.0 (n=1200)

---

### `DER|institutional_trust_justice`

**Type**: good  |  **α**: 0.713  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p21(50%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p18` | 0.3773 | 1200 | OK |
| `p20` | 0.3328 | 1200 | OK |
| `p21` | 0.4356 | 1200 | OK |
| `p34` | 0.3748 | 1200 | OK |

**Dominant-code items**:

- `p21`: 50.1% at code 2.0 (n=1200)

---

### `DER|perceived_discrimination_social_exclusion`

**Type**: questionable  |  **α**: 0.581  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p35_1(70%@2.0), p39(58%@2.0), p44(73%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p35_1` | 0.2866 | 1200 | OK |
| `p39` | 0.4967 | 1200 | OK |
| `p41` | 0.7260 | 1200 | OK |
| `p44` | 0.3941 | 1200 | OK |

**Dominant-code items**:

- `p35_1`: 70.2% at code 2.0 (n=1200)
- `p39`: 58.5% at code 2.0 (n=1200)
- `p44`: 72.8% at code 2.0 (n=1200)

---

### `DER|rights_awareness_personal_experience`

**Type**: questionable  |  **α**: 0.554  |  **N**: 1200  |  **n_items**: 2

**Flags**: FLAG_DOMINANCE: p45(59%@2.0), p54(83%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p45` | 0.8802 | 1200 | OK |
| `p54` | 0.6063 | 1200 | OK |

**Dominant-code items**:

- `p45`: 59.1% at code 2.0 (n=1200)
- `p54`: 83.2% at code 2.0 (n=1200)

---

### `EDU|digital_and_cultural_capital`

**Type**: good  |  **α**: 0.745  |  **N**: 1199  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p47_3(54%@2.0), p47_4(58%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p47_3` | 0.6068 | 1199 | OK |
| `p47_4` | 0.6153 | 1199 | OK |
| `p45_1` | 0.7511 | 1199 | OK |
| `p45_2` | 0.8280 | 1199 | OK |

**Dominant-code items**:

- `p47_3`: 54.4% at code 2.0 (n=1199)
- `p47_4`: 58.2% at code 2.0 (n=1199)

---

### `EDU|educational_returns_belief`

**Type**: questionable  |  **α**: 0.607  |  **N**: 1194  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p37(80%@1.0), p55_3(81%@1.0), p55_4(80%@1.0), p55_5(78%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p37` | 0.5661 | 1194 | OK |
| `p55_3` | 0.6495 | 1194 | OK |
| `p55_4` | 0.6920 | 1194 | OK |
| `p55_5` | 0.7011 | 1194 | OK |

**Dominant-code items**:

- `p37`: 79.6% at code 1.0 (n=1194)
- `p55_3`: 80.8% at code 1.0 (n=1199)
- `p55_4`: 79.8% at code 1.0 (n=1199)
- `p55_5`: 77.7% at code 1.0 (n=1199)

---

### `EDU|social_media_engagement`

**Type**: new_construct  |  **α**: —  |  **N**: 1199  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p48_1(52%@1.0), p48_3(55%@2.0), p44_5(61%@5.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p48_1` | 0.8515 | 1199 | OK |
| `p48_3` | 0.8168 | 1199 | OK |
| `p44_5` | 0.7541 | 1199 | OK |

**Dominant-code items**:

- `p48_1`: 52.1% at code 1.0 (n=1199)
- `p48_3`: 55.3% at code 2.0 (n=1199)
- `p44_5`: 60.7% at code 5.0 (n=1199)

---

### `FAM|conjugal_union_attitudes`

**Type**: questionable  |  **α**: 0.504  |  **N**: 1200  |  **n_items**: 6

**Flags**: FLAG_DOMINANCE: p23(64%@1.0), p35(64%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p21` | 0.3247 | 1200 | OK |
| `p22` | 0.2794 | 1200 | OK |
| `p23` | 0.5151 | 1200 | OK |
| `p32` | 0.4524 | 1200 | OK |
| `p35` | 0.4573 | 1200 | OK |
| `p38` | 0.4164 | 1200 | OK |

**Dominant-code items**:

- `p23`: 64.5% at code 1.0 (n=1200)
- `p35`: 64.2% at code 1.0 (n=1200)

---

### `FAM|family_cohesion_quality`

**Type**: questionable  |  **α**: 0.522  |  **N**: 1200  |  **n_items**: 2

**Flags**: FLAG_DOMINANCE: p25(56%@2.0), p26(52%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p25` | 0.8400 | 1200 | OK |
| `p26` | 0.8500 | 1200 | OK |

**Dominant-code items**:

- `p25`: 55.8% at code 2.0 (n=1200)
- `p26`: 52.2% at code 2.0 (n=1200)

---

### `FAM|ideal_family_normativity`

**Type**: tier3_caveat  |  **α**: 0.451  |  **N**: 972  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p13(70%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p13` | 0.4476 | 972 | OK |
| `p14` | 0.5953 | 972 | OK |
| `p15` | 0.5587 | 972 | OK |
| `p16` | 0.5144 | 972 | OK |

**Dominant-code items**:

- `p13`: 69.7% at code 1.0 (n=1200)

---

### `FAM|intergenerational_obligations`

**Type**: tier3_caveat  |  **α**: 0.489  |  **N**: 1200  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p29(78%@1.0), p64(81%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p28` | 0.7555 | 1200 | OK |
| `p29` | 0.3945 | 1200 | OK |
| `p64` | 0.5771 | 1200 | OK |

**Dominant-code items**:

- `p29`: 77.8% at code 1.0 (n=1200)
- `p64`: 81.4% at code 1.0 (n=1200)

---

### `FED|fiscal_and_service_federalism_preferences`

**Type**: questionable  |  **α**: 0.603  |  **N**: 1200  |  **n_items**: 7

**Flags**: FLAG_DOMINANCE: p33(61%@1.0), p60(58%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p31_1` | 0.4763 | 1200 | OK |
| `p32_1` | 0.4233 | 1200 | OK |
| `p33` | 0.3482 | 1200 | OK |
| `p34_1` | 0.4685 | 1200 | OK |
| `p36` | 0.4474 | 1200 | OK |
| `p38` | 0.1248 | 1200 | OK |
| `p60` | 0.3585 | 1200 | OK |

**Dominant-code items**:

- `p33`: 60.6% at code 1.0 (n=1200)
- `p60`: 58.3% at code 2.0 (n=1200)

---

### `FED|legal_uniformity_preference`

**Type**: good  |  **α**: 0.948  |  **N**: 1200  |  **n_items**: 6

**Flags**: FLAG_DOMINANCE: p53_1(65%@1.0), p53_2(69%@1.0), p53_3(65%@1.0), p53_4(65%@1.0), p53_5(63%@1.0), p53_6(63%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p53_1` | 0.7736 | 1200 | OK |
| `p53_2` | 0.7157 | 1200 | OK |
| `p53_3` | 0.7703 | 1200 | OK |
| `p53_4` | 0.7862 | 1200 | OK |
| `p53_5` | 0.8092 | 1200 | OK |
| `p53_6` | 0.8093 | 1200 | OK |

**Dominant-code items**:

- `p53_1`: 65.4% at code 1.0 (n=1200)
- `p53_2`: 69.0% at code 1.0 (n=1200)
- `p53_3`: 65.0% at code 1.0 (n=1200)
- `p53_4`: 64.7% at code 1.0 (n=1200)
- `p53_5`: 63.1% at code 1.0 (n=1200)
- `p53_6`: 62.6% at code 1.0 (n=1200)

---

### `FED|political_interest_and_engagement`

**Type**: questionable  |  **α**: 0.634  |  **N**: 1200  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p5(51%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p5` | 0.7302 | 1200 | OK |
| `p6` | 0.7944 | 1200 | OK |
| `p7` | 0.8063 | 1200 | OK |

**Dominant-code items**:

- `p5`: 50.6% at code 2.0 (n=1200)

---

### `GEN|intimate_partner_power_dynamics`

**Type**: tier3_caveat  |  **α**: 0.407  |  **N**: 427  |  **n_items**: 3

**Flags**: FLAG_COVERAGE(n=427); FLAG_DOMINANCE: p19(64%@3.0), p23_1(59%@3.0), p23_5(61%@3.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p19` | 0.3675 | 427 | OK |
| `p23_1` | 0.8057 | 427 | OK |
| `p23_5` | 0.8070 | 427 | OK |

**Dominant-code items**:

- `p19`: 64.4% at code 3.0 (n=637)
- `p23_1`: 59.1% at code 3.0 (n=489)
- `p23_5`: 61.3% at code 3.0 (n=496)

---

### `GLO|economic_globalization_attitudes`

**Type**: questionable  |  **α**: 0.694  |  **N**: 1123  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p46_1(70%@1.0), p47(56%@1.0), p31_1(61%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p46_1` | 0.6304 | 1123 | OK |
| `p47` | 0.6896 | 1123 | OK |
| `p48` | 0.6683 | 1123 | OK |
| `p31_1` | 0.5688 | 1123 | OK |

**Dominant-code items**:

- `p46_1`: 69.5% at code 1.0 (n=1200)
- `p47`: 56.3% at code 1.0 (n=1200)
- `p31_1`: 61.3% at code 1.0 (n=1164)

---

### `GLO|international_institutional_engagement`

**Type**: questionable  |  **α**: 0.545  |  **N**: 1200  |  **n_items**: 5

**Flags**: FLAG_DOMINANCE: p52_1(81%@1.0), p57(62%@1.0), p60_1(74%@1.0), p63_1(88%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p52_1` | 0.4422 | 1200 | OK |
| `p54_1` | 0.4730 | 1200 | OK |
| `p57` | 0.5307 | 1200 | OK |
| `p60_1` | 0.4568 | 1200 | OK |
| `p63_1` | 0.3339 | 1200 | OK |

**Dominant-code items**:

- `p52_1`: 80.7% at code 1.0 (n=1200)
- `p57`: 62.3% at code 1.0 (n=1200)
- `p60_1`: 74.3% at code 1.0 (n=1200)
- `p63_1`: 88.1% at code 1.0 (n=1200)

---

### `HAB|basic_services_access`

**Type**: questionable  |  **α**: 0.530  |  **N**: 1127  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p7(78%@1.0), p7_1(66%@1.0), p10(84%@1.0), p11(99%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p7` | 0.6943 | 1127 | OK |
| `p7_1` | 0.7504 | 1127 | OK |
| `p10` | 0.5278 | 1127 | OK |
| `p11` | 0.0971 | 1127 | OK |

**Dominant-code items**:

- `p7`: 77.9% at code 1.0 (n=1192)
- `p7_1`: 66.0% at code 1.0 (n=1146)
- `p10`: 83.5% at code 1.0 (n=1179)
- `p11`: 99.3% at code 1.0 (n=1200)

---

### `HAB|household_asset_endowment`

**Type**: good  |  **α**: 0.725  |  **N**: 1200  |  **n_items**: 12

**Flags**: FLAG_DOMINANCE: p36_1(78%@1.0), p36_2(97%@1.0), p36_4(89%@1.0), p36_5(78%@1.0), p36_6(90%@1.0), p36_8(72%@1.0), p36_9(59%@2.0), p36_10(63%@2.0), p36_18(53%@1.0), p36_21(93%@2.0), p36_22(96%@2.0), p36_29(80%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p36_1` | 0.3419 | 1200 | OK |
| `p36_2` | 0.2620 | 1200 | OK |
| `p36_4` | 0.4471 | 1200 | OK |
| `p36_5` | 0.5728 | 1200 | OK |
| `p36_6` | 0.4418 | 1200 | OK |
| `p36_8` | 0.5672 | 1200 | OK |
| `p36_9` | 0.6637 | 1200 | OK |
| `p36_10` | 0.7128 | 1200 | OK |
| `p36_18` | 0.5689 | 1200 | OK |
| `p36_21` | 0.3841 | 1200 | OK |
| `p36_22` | 0.2693 | 1200 | OK |
| `p36_29` | 0.4208 | 1200 | OK |

**Dominant-code items**:

- `p36_1`: 77.5% at code 1.0 (n=1200)
- `p36_2`: 96.8% at code 1.0 (n=1200)
- `p36_4`: 88.9% at code 1.0 (n=1200)
- `p36_5`: 78.1% at code 1.0 (n=1200)
- `p36_6`: 90.0% at code 1.0 (n=1200)
- `p36_8`: 72.3% at code 1.0 (n=1200)
- `p36_9`: 58.8% at code 2.0 (n=1200)
- `p36_10`: 62.9% at code 2.0 (n=1200)
- `p36_18`: 53.0% at code 1.0 (n=1200)
- `p36_21`: 92.6% at code 2.0 (n=1200)
- `p36_22`: 96.2% at code 2.0 (n=1200)
- `p36_29`: 80.2% at code 2.0 (n=1200)

---

### `HAB|structural_housing_quality`

**Type**: questionable  |  **α**: 0.511  |  **N**: 1197  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p1(79%@9.0), p2(84%@7.0), p3(58%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p1` | 0.5957 | 1197 | OK |
| `p2` | 0.6409 | 1197 | OK |
| `p3` | 0.7943 | 1197 | OK |

**Dominant-code items**:

- `p1`: 78.6% at code 9.0 (n=1199)
- `p2`: 84.1% at code 7.0 (n=1198)
- `p3`: 57.9% at code 2.0 (n=1200)

---

### `IDE|tolerance_social_diversity`

**Type**: questionable  |  **α**: 0.588  |  **N**: 1200  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p9(70%@2.0), p73_1(57%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p9` | 0.3112 | 1200 | OK |
| `p68` | 0.7999 | 1200 | OK |
| `p73_1` | 0.5290 | 1200 | OK |

**Dominant-code items**:

- `p9`: 70.4% at code 2.0 (n=1200)
- `p73_1`: 56.7% at code 1.0 (n=1200)

---

### `IND|perceived_indigenous_discrimination`

**Type**: tier3_caveat  |  **α**: 0.401  |  **N**: 1174  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p21(72%@1.0), p25_1(83%@1.0), p34_1(63%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p21` | 0.6052 | 1174 | OK |
| `p25_1` | 0.5261 | 1174 | OK |
| `p34_1` | 0.7679 | 1174 | OK |

**Dominant-code items**:

- `p21`: 72.5% at code 1.0 (n=1181)
- `p25_1`: 83.4% at code 1.0 (n=1188)
- `p34_1`: 63.4% at code 1.0 (n=1187)

---

### `IND|social_distance_toward_indigenous_people`

**Type**: questionable  |  **α**: 0.510  |  **N**: 1109  |  **n_items**: 2

**Flags**: FLAG_DOMINANCE: p37_1(85%@1.0), p40_1(70%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p37_1` | 0.6465 | 1109 | OK |
| `p40_1` | 0.9152 | 1109 | OK |

**Dominant-code items**:

- `p37_1`: 85.3% at code 1.0 (n=1126)
- `p40_1`: 69.9% at code 1.0 (n=1168)

---

### `JUS|judicial_institutional_trust`

**Type**: questionable  |  **α**: 0.649  |  **N**: 804  |  **n_items**: 6

**Flags**: FLAG_DOMINANCE: p33(74%@2.0), p50(60%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p22` | 0.5025 | 804 | OK |
| `p41` | 0.6491 | 804 | OK |
| `p42_1` | 0.6076 | 804 | OK |
| `p46` | 0.6843 | 804 | OK |
| `p33` | 0.3939 | 804 | OK |
| `p50` | 0.5426 | 804 | OK |

**Dominant-code items**:

- `p33`: 73.8% at code 2.0 (n=1200)
- `p50`: 60.0% at code 2.0 (n=1000)

---

### `MED|pro_environmental_civic_engagement`

**Type**: good  |  **α**: 0.796  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p34_1(90%@2.0), p34_2(89%@2.0), p34_3(91%@2.0), p34_4(89%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p34_1` | 0.6265 | 1200 | OK |
| `p34_2` | 0.5928 | 1200 | OK |
| `p34_3` | 0.6206 | 1200 | OK |
| `p34_4` | 0.6657 | 1200 | OK |

**Dominant-code items**:

- `p34_1`: 89.9% at code 2.0 (n=1200)
- `p34_2`: 88.9% at code 2.0 (n=1200)
- `p34_3`: 91.3% at code 2.0 (n=1200)
- `p34_4`: 88.7% at code 2.0 (n=1200)

---

### `MIG|attitudes_toward_foreigners_in_mexico`

**Type**: questionable  |  **α**: 0.569  |  **N**: 1199  |  **n_items**: 7

**Flags**: FLAG_DOMINANCE: p48(80%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p42` | 0.4673 | 1199 | OK |
| `p43_1` | 0.3903 | 1199 | OK |
| `p45` | 0.5332 | 1199 | OK |
| `p47` | 0.4033 | 1199 | OK |
| `p48` | 0.2595 | 1199 | OK |
| `p51` | 0.3085 | 1199 | OK |
| `p52` | 0.3259 | 1199 | OK |

**Dominant-code items**:

- `p48`: 79.6% at code 2.0 (n=1199)

---

### `MIG|emigration_intention_likelihood`

**Type**: tier3_caveat  |  **α**: 0.466  |  **N**: 1199  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p15_1(65%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p15_1` | 0.6261 | 1199 | OK |
| `p17` | 0.7209 | 1199 | OK |
| `p18` | 0.7292 | 1199 | OK |

**Dominant-code items**:

- `p15_1`: 65.4% at code 1.0 (n=1199)

---

### `NIN|youth_participation_and_voice`

**Type**: questionable  |  **α**: 0.546  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p13(53%@1.0), p39(56%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p12` | 0.8053 | 1200 | OK |
| `p13` | 0.7913 | 1200 | OK |
| `p38` | 0.8224 | 1200 | OK |
| `p39` | 0.8144 | 1200 | OK |

**Dominant-code items**:

- `p13`: 53.4% at code 1.0 (n=1200)
- `p39`: 56.1% at code 1.0 (n=1200)

---

### `POB|intergenerational_mobility_perception`

**Type**: questionable  |  **α**: 0.537  |  **N**: 1097  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p22(52%@2.0), p23(54%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p22` | 0.7477 | 1097 | OK |
| `p23` | 0.7777 | 1097 | OK |
| `p24` | 0.8093 | 1097 | OK |

**Dominant-code items**:

- `p22`: 51.8% at code 2.0 (n=1185)
- `p23`: 54.3% at code 2.0 (n=1128)

---

### `REL|church_state_separation`

**Type**: questionable  |  **α**: 0.568  |  **N**: 1045  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p52_1(53%@5.0), p56(54%@5.0), p57(53%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p52_1` | 0.6976 | 1045 | OK |
| `p55` | 0.8149 | 1045 | OK |
| `p56` | 0.7660 | 1045 | OK |
| `p57` | 0.4095 | 1045 | OK |

**Dominant-code items**:

- `p52_1`: 53.4% at code 5.0 (n=1200)
- `p56`: 54.2% at code 5.0 (n=1147)
- `p57`: 52.9% at code 1.0 (n=1088)

---

### `REL|personal_religiosity`

**Type**: good  |  **α**: 0.732  |  **N**: 968  |  **n_items**: 5

**Flags**: FLAG_DOMINANCE: p10(65%@1.0), p12(71%@1.0), p13_1(74%@1.0), p25(59%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p10` | 0.6670 | 968 | OK |
| `p12` | 0.6695 | 968 | OK |
| `p13_1` | 0.6403 | 968 | OK |
| `p14` | 0.7918 | 968 | OK |
| `p25` | 0.6459 | 968 | OK |

**Dominant-code items**:

- `p10`: 65.4% at code 1.0 (n=1026)
- `p12`: 71.3% at code 1.0 (n=995)
- `p13_1`: 73.9% at code 1.0 (n=1017)
- `p25`: 58.8% at code 1.0 (n=1190)

---

### `REL|religious_socialization`

**Type**: questionable  |  **α**: 0.555  |  **N**: 1163  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p5(65%@1.0), p33_1(60%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p5` | 0.6358 | 1163 | OK |
| `p6` | 0.7635 | 1163 | OK |
| `p33_1` | 0.7578 | 1163 | OK |

**Dominant-code items**:

- `p5`: 65.2% at code 1.0 (n=1185)
- `p33_1`: 59.9% at code 1.0 (n=1185)

---

### `REL|supernatural_beliefs`

**Type**: good  |  **α**: 0.900  |  **N**: 1005  |  **n_items**: 13

**Flags**: FLAG_DOMINANCE: p17_1(82%@1.0), p17_2(59%@1.0), p17_4(52%@1.0), p17_5(62%@1.0), p17_6(65%@1.0), p17_7(69%@1.0), p17_8(53%@1.0), p17_9(51%@1.0), p17_11(53%@3.0), p17_13(59%@3.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p17_1` | 0.5592 | 1005 | OK |
| `p17_2` | 0.6750 | 1005 | OK |
| `p17_4` | 0.7515 | 1005 | OK |
| `p17_5` | 0.7491 | 1005 | OK |
| `p17_6` | 0.7108 | 1005 | OK |
| `p17_7` | 0.6436 | 1005 | OK |
| `p17_8` | 0.7109 | 1005 | OK |
| `p17_9` | 0.7178 | 1005 | OK |
| `p17_10` | 0.7065 | 1005 | OK |
| `p17_11` | 0.6068 | 1005 | OK |
| `p17_12` | 0.5129 | 1005 | OK |
| `p17_13` | 0.6047 | 1005 | OK |
| `p17_14` | 0.5642 | 1005 | OK |

**Dominant-code items**:

- `p17_1`: 81.8% at code 1.0 (n=1172)
- `p17_2`: 58.7% at code 1.0 (n=1140)
- `p17_4`: 51.5% at code 1.0 (n=1152)
- `p17_5`: 62.3% at code 1.0 (n=1148)
- `p17_6`: 65.4% at code 1.0 (n=1156)
- `p17_7`: 69.3% at code 1.0 (n=1158)
- `p17_8`: 53.1% at code 1.0 (n=1135)
- `p17_9`: 50.9% at code 1.0 (n=1130)
- `p17_11`: 53.4% at code 3.0 (n=1142)
- `p17_13`: 59.2% at code 3.0 (n=1135)

---

### `SAL|functional_health_status`

**Type**: good  |  **α**: 0.723  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p2(73%@3.0), p3(72%@3.0), p4(79%@2.0), p5(83%@2.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p2` | 0.8218 | 1200 | OK |
| `p3` | 0.8448 | 1200 | OK |
| `p4` | 0.7511 | 1200 | OK |
| `p5` | 0.6941 | 1200 | OK |

**Dominant-code items**:

- `p2`: 72.6% at code 3.0 (n=1200)
- `p3`: 72.5% at code 3.0 (n=1200)
- `p4`: 79.2% at code 2.0 (n=1200)
- `p5`: 82.7% at code 2.0 (n=1200)

---

### `SAL|subjective_wellbeing`

**Type**: questionable  |  **α**: 0.588  |  **N**: 1200  |  **n_items**: 4

**Flags**: FLAG_DOMINANCE: p37(52%@4.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p37` | 0.6257 | 1200 | OK |
| `p38` | 0.7545 | 1200 | OK |
| `p39` | 0.6220 | 1200 | OK |
| `p40` | 0.7884 | 1200 | OK |

**Dominant-code items**:

- `p37`: 52.4% at code 4.0 (n=1200)

---

### `SEG|police_institutional_legitimacy`

**Type**: tier3_caveat  |  **α**: 0.481  |  **N**: 1008  |  **n_items**: 3

**Flags**: FLAG_DOMINANCE: p28_1(70%@1.0), p29_1(60%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p28_1` | 0.5886 | 1008 | OK |
| `p29_1` | 0.6668 | 1008 | OK |
| `p53` | 0.5026 | 1008 | OK |

**Dominant-code items**:

- `p28_1`: 70.2% at code 1.0 (n=1008)
- `p29_1`: 60.1% at code 1.0 (n=1008)

---

### `SOC|perceived_media_social_impact`

**Type**: questionable  |  **α**: 0.587  |  **N**: 1200  |  **n_items**: 6

**Flags**: FLAG_DOMINANCE: p60(68%@1.0)

**Item–Aggregate Spearman r** (after reverse coding applied):

| Item | r | n_pairs | Status |
|------|---|---------|--------|
| `p60` | 0.2063 | 1200 | OK |
| `p61` | 0.3811 | 1200 | OK |
| `p62_1` | 0.4656 | 1200 | OK |
| `p59_1` | 0.4806 | 1200 | OK |
| `p76` | 0.3845 | 1200 | OK |
| `p77_1` | 0.5956 | 1200 | OK |

**Dominant-code items**:

- `p60`: 68.1% at code 1.0 (n=1200)

---

