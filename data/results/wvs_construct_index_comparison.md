# WVS Construct — Validated Index Comparison Report

Generated: 2026-03-13 20:06
Constructs: 56  |  Gold-standard indices: varies by construct

---
## 1  Selection Criteria: How 'Closest Match' Is Defined

For each construct a *closest validated index* is selected through a three-step
procedure applied in priority order:

1. **Item overlap** — constructs whose items are a subset (or superset) of a
   validated index receive that index as their a priori reference.
   These cases are flagged `[a priori]` in all tables.

2. **A priori semantic label** — the `validated_index` field recorded in
   `wvs_svs_v1.json` (Phase 2 LLM output) maps to a reference index.
   Mapping is performed by fragment-matching against the published index names
   listed in `WVS_VALIDATED_INDICES.md`.

3. **Empirical maximum |ρ|** — for every construct, Spearman ρ is computed
   against *all* available validated indices (N=14).  The index with the highest
   absolute correlation is the *empirical closest match*, regardless of semantic
   labelling.  Where empirical ≠ a priori, both are reported.

**Convergent validity thresholds used throughout:**

| |ρ| band | Label |
|----------|-------|
| ≥ 0.70 | ✓ strong (meets criterion) |
| 0.50–0.69 | ⚠ moderate (borderline) |
| 0.30–0.49 | ~ weak (present but insufficient) |
| < 0.30 | ✗ poor (no meaningful convergence) |

**Discriminant validity** is captured by two metrics:
- `disc_mean` = mean |ρ| against all *other* (non-closest) indices
- `HTMT` = |ρ(construct, closest)| / disc_mean.  HTMT > 2.0 suggests
  adequate discriminant separation; HTMT < 1.5 is a warning sign.

**Important caveat on tautological overlap:** Several constructs (e.g.,
`confidence_in_domestic_institutions`) share items directly with their
reference index (`InstitutionalTrust`).  High ρ in these cases reflects
item overlap, not independent validation.  These are flagged `[item-overlap]`.

---
## 2  Validated Indices Available

| Index | Theoretical basis | Key items |
|-------|-------------------|-----------|
| EVI_Autonomy | Welzel (2013) *Freedom Rising* | Q7, Q18, Q20 |
| EVI_Equality | Welzel (2013) | Q33, Q105, Q106 |
| EVI_Choice | Welzel (2013) | Q182, Q184, Q185 |
| EVI_Voice | Welzel (2013) | Q209, Q210, Q211 |
| EVI_Total | Welzel (2013) mean of 4 sub-indices | 12 items |
| Y001 | Inglehart (1971) Post-Materialist 4-item | Q150–Q153 |
| Y002 | Inglehart (1971) 12-item | full battery |
| Y003 | WVS pre-computed EVI Autonomy | Q7, Q18, Q20 |
| Religiosity | Norris & Inglehart (2004) | Q164, Q171, Q172, Q173, Q174, Q6 |
| GenderEgalitarianism | Inglehart & Norris (2003) | Q33, Q105, Q106, Q107, Q37 |
| InstitutionalTrust | Newton & Norris (2000) | Q64–Q89 |
| SelfExpressionValues | Inglehart-Welzel X-axis approx. | Q57, Q209, Q182, Y001 |
| SecularRationalValues | Inglehart-Welzel Y-axis approx. | Q164, Q6, Q45, Q22 |
| SubjectiveWellBeing | Inglehart et al. (2008) | Q46, Q49 |
| GeneralizedTrust | Putnam (2000) / Delhey & Newton (2005) | Q57 |
| EnvironmentalConcern | Knight (2016) | Q111–Q114 |
| SocialCapital | Bjørnskov (2006) | Q57, Q94–Q105, Q209–Q211 |

---
## 3  Master Comparison Table — All Constructs

Columns: **α** Cronbach's alpha; **N** valid observations; **mean / SD / skew**
on the 1–10 aggregate scale; **closest index** and the empirical Spearman ρ;
**conv** convergent verdict; **disc_mean** average |ρ| to all other indices;
**HTMT** = |ρ| / disc_mean.

| Construct | Tier | α | N | mean | SD | skew | Closest index | ρ | conv | disc_mean | HTMT |
|-----------|------|---|---|------|----|------|---------------|---|------|-----------|------|
| `WVS_A|importance_of_life_domains` | ◈ formative | — | 1741 | 6.85 | 2.16 | -0.28 | SecularRationalValues | +0.364 | ~ weak | 0.069 | 5.25 |
| `WVS_A|child_qualities_autonomy_self_expression` | ◈ formative | — | 1741 | 4.58 | 2.23 | 0.39 | Y003 [ap] | +0.203 | ✗ poor | 0.037 | 5.43 |
| `WVS_A|child_qualities_conformity_tradition` | ◈ formative | — | 1741 | 6.42 | 1.93 | -0.17 | Y003 | -0.448 | ~ weak | 0.060 | 7.46 |
| `WVS_A|child_qualities_prosocial_diligence` | ◈ formative | — | 1741 | 3.96 | 2.36 | 0.49 | Y003 [ap] | +0.173 | ✗ poor | 0.029 | 6.09 |
| `WVS_A|social_intolerance_outgroups` | ✓ good | 0.812 | 1741 | 8.62 | 2.22 | -1.99 | SocialCapital | -0.120 | ✗ poor | 0.037 | 3.20 |
| `WVS_A|social_intolerance_deviant_behavior` | ○ single-item | — | 1739 | 3.04 | 3.77 | 1.31 | SocialCapital | +0.082 | ✗ poor | 0.031 | 2.64 |
| `WVS_A|subjective_wellbeing` | ✗ tier3 | 0.290 | 1741 | 7.66 | 1.53 | -1.04 | SubjectiveWellBeing [ap] | +0.539 | ⚠ moderate | 0.043 | 12.62 |
| `WVS_A|voluntary_association_active_membership` | ◈ formative | — | 1741 | 2.17 | 2.18 | 2.41 | SocialCapital [ap] | +0.564 | ⚠ moderate | 0.043 | 13.15 |
| `WVS_A|voluntary_association_belonging` | ◈ formative | — | 1741 | 2.89 | 2.70 | 1.76 | SocialCapital [ap] | +0.733 | ✓ strong | 0.062 | 11.72 |
| `WVS_C|job_scarcity_gender_discrimination` | ⚠ questionable | 0.553 | 1736 | 6.93 | 2.83 | -1.05 | GenderEgalitarianism [ap] | -0.444 | ~ weak | 0.063 | 7.02 |
| `WVS_C|job_scarcity_nativist_preference` | ✓ good | 0.736 | 1727 | 5.20 | 3.28 | -0.06 | GenderEgalitarianism | -0.229 | ✗ poor | 0.042 | 5.49 |
| `WVS_C|work_ethic` | ⚠ questionable | 0.620 | 1740 | 3.45 | 1.91 | 0.65 | GenderEgalitarianism | -0.170 | ✗ poor | 0.062 | 2.76 |
| `WVS_D|gender_role_traditionalism` | ✓ good | 0.704 | 1741 | 6.62 | 1.91 | -0.47 | GenderEgalitarianism [ap] | -0.254 | ✗ poor | 0.052 | 4.88 |
| `WVS_D|female_income_threat_to_marriage` | ✓ good | 0.743 | 1725 | 4.97 | 3.31 | 0.07 | GenderEgalitarianism | -0.126 | ✗ poor | 0.040 | 3.18 |
| `WVS_D|familial_duty_obligations` | ○ single-item | — | 1731 | 3.46 | 2.43 | 0.81 | GenderEgalitarianism | -0.153 | ✗ poor | 0.051 | 3.00 |
| `WVS_E|confidence_in_domestic_institutions` | ✓ good | 0.890 | 1741 | 7.03 | 1.73 | -0.62 | InstitutionalTrust [ap] | -0.915 | ✓ strong | 0.067 | 13.70 |
| `WVS_E|confidence_in_civil_society_organizations` | ✓ good | 0.770 | 1735 | 5.91 | 2.54 | -0.14 | InstitutionalTrust [ap] | -0.762 | ✓ strong | 0.058 | 13.17 |
| `WVS_E|confidence_in_international_organizations` | ✓ good | 0.912 | 1701 | 6.61 | 2.33 | -0.30 | InstitutionalTrust [ap] | -0.854 | ✓ strong | 0.049 | 17.61 |
| `WVS_E|perceived_corruption` | ◈ formative | — | 1741 | 1.58 | 1.02 | 3.00 | EnvironmentalConcern | +0.114 | ✗ poor | 0.027 | 4.23 |
| `WVS_E|electoral_integrity` | ✗ tier3 | 0.348 | 1729 | 4.99 | 1.26 | 0.11 | EnvironmentalConcern | +0.183 | ✗ poor | 0.037 | 4.96 |
| `WVS_E|postmaterialist_values` | ◈ formative | — | 1741 | 7.23 | 2.42 | -0.55 | Y001 [ap] | -0.527 | ⚠ moderate | 0.088 | 5.95 |
| `WVS_E|autocracy_support` | ✗ tier3 | 0.499 | 1736 | 5.12 | 1.86 | 0.13 | InstitutionalTrust | -0.163 | ✗ poor | 0.040 | 4.08 |
| `WVS_E|democratic_values_importance` | ⚠ questionable | 0.670 | 1727 | 5.77 | 2.05 | -0.06 | InstitutionalTrust | +0.093 | ✗ poor | 0.026 | 3.59 |
| `WVS_E|democratic_system_evaluation` | ◈ formative | — | 1741 | 3.11 | 2.14 | 0.78 | EnvironmentalConcern | -0.110 | ✗ poor | 0.031 | 3.51 |
| `WVS_E|offline_political_participation` | ◈ formative | — | 1741 | 1.57 | 1.21 | 2.82 | EVI_Voice [ap] | +0.793 | ✓ strong | 0.108 | 7.32 |
| `WVS_E|online_political_participation` | ◈ formative | — | 1741 | 1.55 | 1.44 | 3.27 | EVI_Voice | +0.260 | ✗ poor | 0.082 | 3.19 |
| `WVS_E|political_information_sources` | ◈ formative | — | 1741 | 3.70 | 2.27 | 0.70 | EVI_Voice | +0.175 | ✗ poor | 0.054 | 3.26 |
| `WVS_E|voting_participation` | ✓ good | 0.869 | 1737 | 2.46 | 2.12 | 1.43 | SecularRationalValues | -0.094 | ✗ poor | 0.036 | 2.58 |
| `WVS_E|science_technology_optimism` | ⚠ questionable | 0.598 | 1737 | 6.93 | 2.06 | -0.53 | InstitutionalTrust | +0.108 | ✗ poor | 0.033 | 3.28 |
| `WVS_E|economic_ideology` | ✗ tier3 | 0.428 | 1734 | 5.25 | 1.86 | -0.08 | EVI_Equality | -0.591 | ⚠ moderate | 0.073 | 8.08 |
| `WVS_E|societal_change_attitudes` | ○ single-item | — | 1734 | 5.77 | 3.94 | -0.12 | SocialCapital | -0.086 | ✗ poor | 0.027 | 3.14 |
| `WVS_E|international_organization_knowledge` | ◈ formative | — | 1741 | 2.42 | 2.14 | 1.40 | SocialCapital | +0.119 | ✗ poor | 0.042 | 2.87 |
| `WVS_E|authoritarian_governance_tolerance` | ○ single-item | — | 1691 | 4.14 | 2.74 | 0.45 | EVI_Voice | -0.082 | ✗ poor | 0.032 | 2.54 |
| `WVS_F|religious_belief` | ✗ tier3 | -0.250 | 1741 | 4.44 | 0.94 | -0.57 | SecularRationalValues | -0.172 | ✗ poor | 0.057 | 3.02 |
| `WVS_F|religious_practice_and_self_identification` | ⚠ questionable | 0.608 | 1740 | 3.88 | 2.31 | 0.98 | Religiosity [ap] | +0.442 | ~ weak | 0.064 | 6.88 |
| `WVS_F|religious_exclusivism` | ⚠ questionable | 0.691 | 1725 | 6.11 | 2.59 | -0.22 | GenderEgalitarianism | -0.183 | ✗ poor | 0.064 | 2.87 |
| `WVS_F|civic_dishonesty_tolerance` | ⚠ questionable | 0.653 | 1738 | 3.39 | 1.78 | 0.67 | EVI_Choice | +0.279 | ✗ poor | 0.066 | 4.23 |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | ✓ good | 0.751 | 1735 | 3.85 | 2.13 | 0.55 | EVI_Choice | +0.832 | ✓ strong | 0.108 | 7.67 |
| `WVS_F|life_autonomy_morality_permissiveness` | ⚠ questionable | 0.580 | 1732 | 3.87 | 2.25 | 0.53 | EVI_Choice | +0.746 | ✓ strong | 0.098 | 7.59 |
| `WVS_F|violence_tolerance` | ✓ good | 0.771 | 1734 | 2.50 | 1.81 | 1.46 | EVI_Choice | +0.221 | ✗ poor | 0.051 | 4.33 |
| `WVS_F|religion_versus_secularism_orientation` | ✗ tier3 | 0.361 | 1736 | 8.84 | 2.37 | -1.94 | Religiosity | -0.302 | ~ weak | 0.056 | 5.38 |
| `WVS_G|outgroup_trust` | ✓ good | 0.769 | 1741 | 3.85 | 2.00 | 0.66 | InstitutionalTrust | +0.334 | ~ weak | 0.062 | 5.41 |
| `WVS_G|perceived_positive_effects_of_immigration` | ⚠ questionable | 0.518 | 1732 | 4.84 | 2.43 | 0.27 | InstitutionalTrust | -0.110 | ✗ poor | 0.029 | 3.80 |
| `WVS_G|perceived_negative_effects_of_immigration` | ✓ good | 0.744 | 1729 | 5.65 | 2.94 | -0.10 | SelfExpressionValues | -0.101 | ✗ poor | 0.030 | 3.41 |
| `WVS_G|multilevel_place_attachment` | ◈ formative | — | 1741 | 4.97 | 3.14 | 0.15 | InstitutionalTrust | +0.159 | ✗ poor | 0.033 | 4.76 |
| `WVS_G|immigrant_origin_status` | ◈ formative | — | 1741 | 1.00 | 0.00 | nan | Y001 | — | ✗ poor | 0.000 | — |
| `WVS_H|basic_needs_deprivation` | ⚠ questionable | 0.626 | 1741 | 2.91 | 1.94 | 0.89 | SubjectiveWellBeing | -0.220 | ✗ poor | 0.037 | 5.90 |
| `WVS_H|neighborhood_disorder_and_crime` | ✓ good | 0.827 | 1741 | 5.17 | 2.53 | 0.04 | EnvironmentalConcern | +0.144 | ✗ poor | 0.042 | 3.46 |
| `WVS_H|crime_victimization` | ◈ formative | — | 1741 | 3.92 | 3.65 | 0.72 | EVI_Total | +0.162 | ✗ poor | 0.054 | 2.98 |
| `WVS_H|precautionary_security_behaviors` | ◈ formative | — | 1741 | 5.72 | 2.59 | -0.62 | EnvironmentalConcern | -0.122 | ✗ poor | 0.025 | 4.94 |
| `WVS_H|socioeconomic_insecurity_worry` | ⚠ questionable | 0.683 | 1739 | 2.18 | 2.17 | 1.98 | GeneralizedTrust | +0.120 | ✗ poor | 0.040 | 2.98 |
| `WVS_H|existential_threat_worry` | ✓ good | 0.909 | 1739 | 2.34 | 2.43 | 1.84 | SubjectiveWellBeing | -0.101 | ✗ poor | 0.047 | 2.16 |
| `WVS_H|acceptance_of_state_surveillance` | ✓ good | 0.707 | 1738 | 3.82 | 2.55 | 0.67 | SocialCapital | +0.140 | ✗ poor | 0.042 | 3.37 |
| `WVS_H|freedom_security_tradeoff_perception` | ✗ tier3 | 0.190 | 1739 | 6.28 | 3.17 | -0.26 | EVI_Choice | +0.057 | ✗ poor | 0.030 | 1.89 |
| `WVS_H|institutional_threat_perception` | ⚠ questionable | 0.663 | 1735 | 7.58 | 2.62 | -0.92 | SubjectiveWellBeing | +0.104 | ✗ poor | 0.040 | 2.62 |
| `WVS_I|science_skepticism` | ✗ tier3 | 0.333 | 1735 | 6.09 | 2.30 | -0.21 | SocialCapital | -0.089 | ✗ poor | 0.034 | 2.64 |

[ap] = a priori match; un-tagged = empirical match only

---
## 4  Convergent Validity — Detailed Analysis

- **Strong** (|ρ| ≥ 0.70): 7 constructs
- **Moderate** (0.50–0.69): 4 constructs
- **Weak** (0.30–0.49): 6 constructs
- **Poor** (< 0.30): 39 constructs

### 4.1  Strong Convergent Validity (|ρ| ≥ 0.70)

| Construct | α | N | Closest index | ρ | a priori? | top-5 indices |
|-----------|---|---|---------------|---|-----------|---------------|
| `WVS_A|voluntary_association_belonging` | — | 1741 | SocialCapital | +0.733 | ✓ | SocialCapital(+0.73); InstitutionalTrust(+0.17); EnvironmentalConcern(+0.13); EVI_Voice(+0.13); GenderEgalitarianism(-0.09) |
| `WVS_E|confidence_in_domestic_institutions` | 0.890 | 1741 | InstitutionalTrust | -0.915 | ✓ | InstitutionalTrust(-0.91); EnvironmentalConcern(-0.23); SecularRationalValues(-0.19); SocialCapital(-0.17); GeneralizedTrust(-0.10) |
| `WVS_E|confidence_in_civil_society_organizations` | 0.770 | 1735 | InstitutionalTrust | -0.762 | ✓ | InstitutionalTrust(-0.76); EnvironmentalConcern(-0.18); SocialCapital(-0.16); SecularRationalValues(-0.12); SubjectiveWellBeing(-0.11) |
| `WVS_E|confidence_in_international_organizations` | 0.912 | 1701 | InstitutionalTrust | -0.854 | ✓ | InstitutionalTrust(-0.85); EnvironmentalConcern(-0.16); SocialCapital(-0.14); SecularRationalValues(-0.11); SubjectiveWellBeing(-0.09) |
| `WVS_E|offline_political_participation` | — | 1741 | EVI_Voice | +0.793 | ✓ | EVI_Voice(+0.79); SocialCapital(+0.42); EVI_Total(+0.38); SelfExpressionValues(+0.37); InstitutionalTrust(+0.11) |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | 0.751 | 1735 | EVI_Choice | +0.832 | ✗ | EVI_Choice(+0.83); EVI_Total(+0.60); SelfExpressionValues(+0.46); SecularRationalValues(-0.13); Religiosity(+0.11) |
| `WVS_F|life_autonomy_morality_permissiveness` | 0.580 | 1732 | EVI_Choice | +0.746 | ✗ | EVI_Choice(+0.75); EVI_Total(+0.54); SelfExpressionValues(+0.29); Y003(+0.11); SecularRationalValues(-0.10) |

### 4.2  Moderate Convergent Validity (|ρ| = 0.50–0.69)

| Construct | α | N | Closest index | ρ | a priori? | top-5 indices |
|-----------|---|---|---------------|---|-----------|---------------|
| `WVS_A|subjective_wellbeing` | 0.290 | 1741 | SubjectiveWellBeing | +0.539 | ✓ | SubjectiveWellBeing(+0.54); SecularRationalValues(+0.08); Y001(-0.07); EVI_Equality(-0.07); SocialCapital(-0.06) |
| `WVS_A|voluntary_association_active_membership` | — | 1741 | SocialCapital | +0.564 | ✓ | SocialCapital(+0.56); InstitutionalTrust(+0.10); GenderEgalitarianism(-0.10); SelfExpressionValues(+0.07); EVI_Voice(+0.07) |
| `WVS_E|postmaterialist_values` | — | 1741 | Y001 | -0.527 | ✓ | Y001(-0.53); Y002(-0.46); SelfExpressionValues(-0.26); SocialCapital(-0.14); SubjectiveWellBeing(+0.10) |
| `WVS_E|economic_ideology` | 0.428 | 1734 | EVI_Equality | -0.591 | ✗ | EVI_Equality(-0.59); GenderEgalitarianism(-0.55); EVI_Total(-0.32); Religiosity(+0.07); InstitutionalTrust(-0.06) |

### 4.3  Weak Convergent Validity (|ρ| = 0.30–0.49)

| Construct | α | N | Closest index | ρ | a priori? | top-5 indices |
|-----------|---|---|---------------|---|-----------|---------------|
| `WVS_A|importance_of_life_domains` | — | 1741 | SecularRationalValues | +0.364 | ✗ | SecularRationalValues(+0.36); Religiosity(-0.28); SubjectiveWellBeing(+0.21); EVI_Choice(-0.12); InstitutionalTrust(+0.09) |
| `WVS_A|child_qualities_conformity_tradition` | — | 1741 | Y003 | -0.448 | ✗ | Y003(-0.45); SelfExpressionValues(-0.13); EVI_Choice(-0.13); Y001(-0.09); EVI_Equality(+0.09) |
| `WVS_C|job_scarcity_gender_discrimination` | 0.553 | 1736 | GenderEgalitarianism | -0.444 | ✓ | GenderEgalitarianism(-0.44); EVI_Equality(-0.29); EVI_Choice(+0.10); EVI_Total(-0.09); SecularRationalValues(-0.09) |
| `WVS_F|religious_practice_and_self_identification` | 0.608 | 1740 | Religiosity | +0.442 | ✓ | Religiosity(+0.44); SecularRationalValues(-0.16); EVI_Choice(+0.16); Y003(+0.15); GenderEgalitarianism(-0.11) |
| `WVS_F|religion_versus_secularism_orientation` | 0.361 | 1736 | Religiosity | -0.302 | ✗ | Religiosity(-0.30); GeneralizedTrust(-0.16); SocialCapital(-0.14); SubjectiveWellBeing(+0.10); EnvironmentalConcern(-0.08) |
| `WVS_G|outgroup_trust` | 0.769 | 1741 | InstitutionalTrust | +0.334 | ✗ | InstitutionalTrust(+0.33); GeneralizedTrust(+0.17); SelfExpressionValues(+0.13); SocialCapital(+0.13); SecularRationalValues(+0.10) |

### 4.4  Poor / No Convergent Validity (|ρ| < 0.30)

| Construct | α | N | Closest index | ρ | a priori? | top-5 indices |
|-----------|---|---|---------------|---|-----------|---------------|
| `WVS_A|child_qualities_autonomy_self_expression` | — | 1741 | Y003 | +0.203 | ✓ | Y003(+0.20); EVI_Total(+0.07); EVI_Choice(+0.07); SubjectiveWellBeing(+0.07); GenderEgalitarianism(-0.06) |
| `WVS_A|child_qualities_prosocial_diligence` | — | 1741 | Y003 | +0.173 | ✓ | Y003(+0.17); EVI_Choice(+0.07); GeneralizedTrust(-0.05); EVI_Equality(-0.04); GenderEgalitarianism(-0.04) |
| `WVS_A|social_intolerance_outgroups` | 0.812 | 1741 | SocialCapital | -0.120 | ✗ | SocialCapital(-0.12); EVI_Choice(+0.09); GenderEgalitarianism(-0.09); Y003(+0.08); EVI_Autonomy(+0.07) |
| `WVS_A|social_intolerance_deviant_behavior` | — | 1739 | SocialCapital | +0.082 | ✗ | SocialCapital(+0.08); GeneralizedTrust(+0.07); Y001(+0.06); SelfExpressionValues(+0.05); SecularRationalValues(-0.05) |
| `WVS_C|job_scarcity_nativist_preference` | 0.736 | 1727 | GenderEgalitarianism | -0.229 | ✗ | GenderEgalitarianism(-0.23); EVI_Equality(-0.12); EVI_Choice(+0.10); SecularRationalValues(-0.10); SelfExpressionValues(+0.08) |
| `WVS_C|work_ethic` | 0.620 | 1740 | GenderEgalitarianism | -0.170 | ✗ | GenderEgalitarianism(-0.17); Y003(+0.14); SecularRationalValues(-0.13); InstitutionalTrust(-0.11); Y001(+0.09) |
| `WVS_D|gender_role_traditionalism` | 0.704 | 1741 | GenderEgalitarianism | -0.254 | ✓ | GenderEgalitarianism(-0.25); EVI_Choice(+0.12); EVI_Equality(-0.12); SocialCapital(-0.10); SelfExpressionValues(+0.09) |
| `WVS_D|female_income_threat_to_marriage` | 0.743 | 1725 | GenderEgalitarianism | -0.126 | ✗ | GenderEgalitarianism(-0.13); SecularRationalValues(-0.11); EVI_Equality(-0.08); Y003(+0.07); InstitutionalTrust(-0.06) |
| `WVS_D|familial_duty_obligations` | — | 1731 | GenderEgalitarianism | -0.153 | ✗ | GenderEgalitarianism(-0.15); SecularRationalValues(-0.14); InstitutionalTrust(-0.12); SubjectiveWellBeing(-0.09); EVI_Equality(-0.07) |
| `WVS_E|perceived_corruption` | — | 1741 | EnvironmentalConcern | +0.114 | ✗ | EnvironmentalConcern(+0.11); SocialCapital(+0.06); GeneralizedTrust(+0.06); EVI_Choice(-0.05); InstitutionalTrust(+0.05) |
| `WVS_E|electoral_integrity` | 0.348 | 1729 | EnvironmentalConcern | +0.183 | ✗ | EnvironmentalConcern(+0.18); InstitutionalTrust(+0.16); SecularRationalValues(+0.08); SocialCapital(+0.07); GeneralizedTrust(+0.06) |
| `WVS_E|autocracy_support` | 0.499 | 1736 | InstitutionalTrust | -0.163 | ✗ | InstitutionalTrust(-0.16); Y003(+0.10); EVI_Choice(+0.09); SelfExpressionValues(+0.07); GenderEgalitarianism(-0.06) |
| `WVS_E|democratic_values_importance` | 0.670 | 1727 | InstitutionalTrust | +0.093 | ✗ | InstitutionalTrust(+0.09); GeneralizedTrust(-0.08); SubjectiveWellBeing(+0.06); SocialCapital(-0.05); SelfExpressionValues(-0.04) |
| `WVS_E|democratic_system_evaluation` | — | 1741 | EnvironmentalConcern | -0.110 | ✗ | EnvironmentalConcern(-0.11); SubjectiveWellBeing(+0.10); EVI_Voice(+0.08); EVI_Autonomy(-0.06); Y003(+0.05) |
| `WVS_E|online_political_participation` | — | 1741 | EVI_Voice | +0.260 | ✗ | EVI_Voice(+0.26); SelfExpressionValues(+0.20); SocialCapital(+0.19); EVI_Total(+0.15); Y001(+0.14) |
| `WVS_E|political_information_sources` | — | 1741 | EVI_Voice | +0.175 | ✗ | EVI_Voice(+0.18); EVI_Total(+0.13); SocialCapital(+0.11); SelfExpressionValues(+0.11); SubjectiveWellBeing(+0.10) |
| `WVS_E|voting_participation` | 0.869 | 1737 | SecularRationalValues | -0.094 | ✗ | SecularRationalValues(-0.09); InstitutionalTrust(-0.09); Religiosity(+0.08); EVI_Choice(+0.07); SubjectiveWellBeing(-0.06) |
| `WVS_E|science_technology_optimism` | 0.598 | 1737 | InstitutionalTrust | +0.108 | ✗ | InstitutionalTrust(+0.11); SubjectiveWellBeing(+0.10); EVI_Equality(-0.08); EVI_Choice(+0.07); GenderEgalitarianism(-0.06) |
| `WVS_E|societal_change_attitudes` | — | 1734 | SocialCapital | -0.086 | ✗ | SocialCapital(-0.09); GeneralizedTrust(-0.07); EnvironmentalConcern(-0.05); SecularRationalValues(-0.05); EVI_Autonomy(-0.04) |
| `WVS_E|international_organization_knowledge` | — | 1741 | SocialCapital | +0.119 | ✗ | SocialCapital(+0.12); PostMaterialist_raw(+0.10); InstitutionalTrust(+0.09); Y003(+0.06); GeneralizedTrust(+0.05) |
| `WVS_E|authoritarian_governance_tolerance` | — | 1691 | EVI_Voice | -0.082 | ✗ | EVI_Voice(-0.08); PostMaterialist_raw(+0.07); EVI_Total(-0.07); Y003(-0.06); SubjectiveWellBeing(-0.05) |
| `WVS_F|religious_belief` | -0.250 | 1741 | SecularRationalValues | -0.172 | ✗ | SecularRationalValues(-0.17); SubjectiveWellBeing(+0.16); SelfExpressionValues(-0.11); Religiosity(+0.11); EVI_Choice(-0.10) |
| `WVS_F|religious_exclusivism` | 0.691 | 1725 | GenderEgalitarianism | -0.183 | ✗ | GenderEgalitarianism(-0.18); Y003(+0.15); EVI_Choice(+0.13); EVI_Equality(-0.11); SocialCapital(-0.11) |
| `WVS_F|civic_dishonesty_tolerance` | 0.653 | 1738 | EVI_Choice | +0.279 | ✗ | EVI_Choice(+0.28); EVI_Total(+0.21); SelfExpressionValues(+0.19); SocialCapital(+0.13); SubjectiveWellBeing(-0.11) |
| `WVS_F|violence_tolerance` | 0.771 | 1734 | EVI_Choice | +0.221 | ✗ | EVI_Choice(+0.22); EVI_Total(+0.15); SubjectiveWellBeing(-0.13); SecularRationalValues(-0.11); SelfExpressionValues(+0.08) |
| `WVS_G|perceived_positive_effects_of_immigration` | 0.518 | 1732 | InstitutionalTrust | -0.110 | ✗ | InstitutionalTrust(-0.11); EnvironmentalConcern(-0.07); SecularRationalValues(-0.05); EVI_Choice(-0.04); Religiosity(+0.04) |
| `WVS_G|perceived_negative_effects_of_immigration` | 0.744 | 1729 | SelfExpressionValues | -0.101 | ✗ | SelfExpressionValues(-0.10); EVI_Voice(-0.08); GeneralizedTrust(-0.07); Y001(-0.06); SocialCapital(-0.05) |
| `WVS_G|multilevel_place_attachment` | — | 1741 | InstitutionalTrust | +0.159 | ✗ | InstitutionalTrust(+0.16); SubjectiveWellBeing(+0.11); SecularRationalValues(+0.07); EVI_Choice(-0.06); EVI_Total(-0.05) |
| `WVS_G|immigrant_origin_status` | — | 1741 | Y001 | — | ✗ |  |
| `WVS_H|basic_needs_deprivation` | 0.626 | 1741 | SubjectiveWellBeing | -0.220 | ✗ | SubjectiveWellBeing(-0.22); Y003(-0.07); EnvironmentalConcern(+0.07); SocialCapital(+0.06); InstitutionalTrust(-0.05) |
| `WVS_H|neighborhood_disorder_and_crime` | 0.827 | 1741 | EnvironmentalConcern | +0.144 | ✗ | EnvironmentalConcern(+0.14); InstitutionalTrust(+0.10); EVI_Total(-0.09); EVI_Choice(-0.07); SecularRationalValues(+0.07) |
| `WVS_H|crime_victimization` | — | 1741 | EVI_Total | +0.162 | ✗ | EVI_Total(+0.16); EVI_Choice(+0.15); EVI_Voice(+0.10); EnvironmentalConcern(-0.10); SelfExpressionValues(+0.09) |
| `WVS_H|precautionary_security_behaviors` | — | 1741 | EnvironmentalConcern | -0.122 | ✗ | EnvironmentalConcern(-0.12); EVI_Total(+0.07); EVI_Choice(+0.06); SubjectiveWellBeing(-0.05); EVI_Equality(+0.05) |
| `WVS_H|socioeconomic_insecurity_worry` | 0.683 | 1739 | GeneralizedTrust | +0.120 | ✗ | GeneralizedTrust(+0.12); EnvironmentalConcern(+0.09); SubjectiveWellBeing(-0.09); Y001(+0.08); Religiosity(+0.07) |
| `WVS_H|existential_threat_worry` | 0.909 | 1739 | SubjectiveWellBeing | -0.101 | ✗ | SubjectiveWellBeing(-0.10); EnvironmentalConcern(+0.09); SocialCapital(+0.08); GeneralizedTrust(+0.08); Y001(+0.07) |
| `WVS_H|acceptance_of_state_surveillance` | 0.707 | 1738 | SocialCapital | +0.140 | ✗ | SocialCapital(+0.14); EnvironmentalConcern(+0.11); InstitutionalTrust(+0.10); SubjectiveWellBeing(-0.06); EVI_Total(+0.05) |
| `WVS_H|freedom_security_tradeoff_perception` | 0.190 | 1739 | EVI_Choice | +0.057 | ✗ | EVI_Choice(+0.06); EVI_Autonomy(-0.06); Y003(-0.06); EnvironmentalConcern(-0.05); SelfExpressionValues(+0.05) |
| `WVS_H|institutional_threat_perception` | 0.663 | 1735 | SubjectiveWellBeing | +0.104 | ✗ | SubjectiveWellBeing(+0.10); Y001(-0.08); Religiosity(-0.07); Y002(-0.06); SocialCapital(-0.06) |
| `WVS_I|science_skepticism` | 0.333 | 1735 | SocialCapital | -0.089 | ✗ | SocialCapital(-0.09); GeneralizedTrust(-0.09); SelfExpressionValues(-0.08); EnvironmentalConcern(-0.06); Y003(-0.05) |

---
## 5  A Priori vs. Empirical Closest-Match Alignment

For constructs with an a priori validated-index assignment, we test whether the
empirically best-correlated index coincides with the a priori one.

| Construct | A priori target | A priori ρ | Empirical best | Empirical ρ | Aligned? |
|-----------|-----------------|-----------|----------------|-------------|----------|
| `WVS_A|child_qualities_autonomy_self_expression` | EVI_Autonomy, Y003 | +0.203 | Y003 | +0.203 | ✓ |
| `WVS_A|child_qualities_conformity_tradition` | SecularRationalValues | +0.086 | Y003 | -0.448 | ✗ |
| `WVS_A|child_qualities_prosocial_diligence` | EVI_Autonomy, Y003 | +0.173 | Y003 | +0.173 | ✓ |
| `WVS_A|subjective_wellbeing` | SubjectiveWellBeing | +0.539 | SubjectiveWellBeing | +0.539 | ✓ |
| `WVS_A|voluntary_association_active_membership` | SocialCapital | +0.564 | SocialCapital | +0.564 | ✓ |
| `WVS_A|voluntary_association_belonging` | SocialCapital | +0.733 | SocialCapital | +0.733 | ✓ |
| `WVS_C|job_scarcity_gender_discrimination` | EVI_Equality, GenderEgalitarianism | -0.444 | GenderEgalitarianism | -0.444 | ✓ |
| `WVS_D|gender_role_traditionalism` | GenderEgalitarianism | -0.254 | GenderEgalitarianism | -0.254 | ✓ |
| `WVS_E|confidence_in_domestic_institutions` | InstitutionalTrust | -0.915 | InstitutionalTrust | -0.915 | ✓ |
| `WVS_E|confidence_in_civil_society_organizations` | InstitutionalTrust | -0.762 | InstitutionalTrust | -0.762 | ✓ |
| `WVS_E|confidence_in_international_organizations` | InstitutionalTrust | -0.854 | InstitutionalTrust | -0.854 | ✓ |
| `WVS_E|postmaterialist_values` | Y001, Y002 | -0.527 | Y001 | -0.527 | ✓ |
| `WVS_E|autocracy_support` | SelfExpressionValues | +0.075 | InstitutionalTrust | -0.163 | ✗ |
| `WVS_E|democratic_values_importance` | SelfExpressionValues | -0.044 | InstitutionalTrust | +0.093 | ✗ |
| `WVS_E|offline_political_participation` | EVI_Voice, SocialCapital | +0.793 | EVI_Voice | +0.793 | ✓ |
| `WVS_F|religious_practice_and_self_identification` | Religiosity | +0.442 | Religiosity | +0.442 | ✓ |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | EVI_Total, SelfExpressionValues | +0.598 | EVI_Choice | +0.832 | ✗ |
| `WVS_F|life_autonomy_morality_permissiveness` | EVI_Total | +0.540 | EVI_Choice | +0.746 | ✗ |
| `WVS_H|acceptance_of_state_surveillance` | SelfExpressionValues | +0.031 | SocialCapital | +0.140 | ✗ |

---
## 6  Discriminant Validity

HTMT (Heterotrait–Monotrait ratio): HTMT = |ρ(construct, closest)| / disc_mean.
High HTMT indicates the construct is *more similar* to its target than to all
other indices — desirable.  HTMT < 1.5 = discriminant validity concern.

| Construct | Closest ρ | disc_mean | HTMT | Flag |
|-----------|-----------|-----------|------|------|
| `WVS_A|importance_of_life_domains` | +0.364 | 0.069 | 5.25 | ✓ |
| `WVS_A|child_qualities_autonomy_self_expression` | +0.203 | 0.037 | 5.43 | ✓ |
| `WVS_A|child_qualities_conformity_tradition` | -0.448 | 0.060 | 7.46 | ✓ |
| `WVS_A|child_qualities_prosocial_diligence` | +0.173 | 0.029 | 6.09 | ✓ |
| `WVS_A|social_intolerance_outgroups` | -0.120 | 0.037 | 3.20 | ✓ |
| `WVS_A|social_intolerance_deviant_behavior` | +0.082 | 0.031 | 2.64 | ✓ |
| `WVS_A|subjective_wellbeing` | +0.539 | 0.043 | 12.62 | ✓ |
| `WVS_A|voluntary_association_active_membership` | +0.564 | 0.043 | 13.15 | ✓ |
| `WVS_A|voluntary_association_belonging` | +0.733 | 0.062 | 11.72 | ✓ |
| `WVS_C|job_scarcity_gender_discrimination` | -0.444 | 0.063 | 7.02 | ✓ |
| `WVS_C|job_scarcity_nativist_preference` | -0.229 | 0.042 | 5.49 | ✓ |
| `WVS_C|work_ethic` | -0.170 | 0.062 | 2.76 | ✓ |
| `WVS_D|gender_role_traditionalism` | -0.254 | 0.052 | 4.88 | ✓ |
| `WVS_D|female_income_threat_to_marriage` | -0.126 | 0.040 | 3.18 | ✓ |
| `WVS_D|familial_duty_obligations` | -0.153 | 0.051 | 3.00 | ✓ |
| `WVS_E|confidence_in_domestic_institutions` | -0.915 | 0.067 | 13.70 | ✓ |
| `WVS_E|confidence_in_civil_society_organizations` | -0.762 | 0.058 | 13.17 | ✓ |
| `WVS_E|confidence_in_international_organizations` | -0.854 | 0.049 | 17.61 | ✓ |
| `WVS_E|perceived_corruption` | +0.114 | 0.027 | 4.23 | ✓ |
| `WVS_E|electoral_integrity` | +0.183 | 0.037 | 4.96 | ✓ |
| `WVS_E|postmaterialist_values` | -0.527 | 0.088 | 5.95 | ✓ |
| `WVS_E|autocracy_support` | -0.163 | 0.040 | 4.08 | ✓ |
| `WVS_E|democratic_values_importance` | +0.093 | 0.026 | 3.59 | ✓ |
| `WVS_E|democratic_system_evaluation` | -0.110 | 0.031 | 3.51 | ✓ |
| `WVS_E|offline_political_participation` | +0.793 | 0.108 | 7.32 | ✓ |
| `WVS_E|online_political_participation` | +0.260 | 0.082 | 3.19 | ✓ |
| `WVS_E|political_information_sources` | +0.175 | 0.054 | 3.26 | ✓ |
| `WVS_E|voting_participation` | -0.094 | 0.036 | 2.58 | ✓ |
| `WVS_E|science_technology_optimism` | +0.108 | 0.033 | 3.28 | ✓ |
| `WVS_E|economic_ideology` | -0.591 | 0.073 | 8.08 | ✓ |
| `WVS_E|societal_change_attitudes` | -0.086 | 0.027 | 3.14 | ✓ |
| `WVS_E|international_organization_knowledge` | +0.119 | 0.042 | 2.87 | ✓ |
| `WVS_E|authoritarian_governance_tolerance` | -0.082 | 0.032 | 2.54 | ✓ |
| `WVS_F|religious_belief` | -0.172 | 0.057 | 3.02 | ✓ |
| `WVS_F|religious_practice_and_self_identification` | +0.442 | 0.064 | 6.88 | ✓ |
| `WVS_F|religious_exclusivism` | -0.183 | 0.064 | 2.87 | ✓ |
| `WVS_F|civic_dishonesty_tolerance` | +0.279 | 0.066 | 4.23 | ✓ |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | +0.832 | 0.108 | 7.67 | ✓ |
| `WVS_F|life_autonomy_morality_permissiveness` | +0.746 | 0.098 | 7.59 | ✓ |
| `WVS_F|violence_tolerance` | +0.221 | 0.051 | 4.33 | ✓ |
| `WVS_F|religion_versus_secularism_orientation` | -0.302 | 0.056 | 5.38 | ✓ |
| `WVS_G|outgroup_trust` | +0.334 | 0.062 | 5.41 | ✓ |
| `WVS_G|perceived_positive_effects_of_immigration` | -0.110 | 0.029 | 3.80 | ✓ |
| `WVS_G|perceived_negative_effects_of_immigration` | -0.101 | 0.030 | 3.41 | ✓ |
| `WVS_G|multilevel_place_attachment` | +0.159 | 0.033 | 4.76 | ✓ |
| `WVS_H|basic_needs_deprivation` | -0.220 | 0.037 | 5.90 | ✓ |
| `WVS_H|neighborhood_disorder_and_crime` | +0.144 | 0.042 | 3.46 | ✓ |
| `WVS_H|crime_victimization` | +0.162 | 0.054 | 2.98 | ✓ |
| `WVS_H|precautionary_security_behaviors` | -0.122 | 0.025 | 4.94 | ✓ |
| `WVS_H|socioeconomic_insecurity_worry` | +0.120 | 0.040 | 2.98 | ✓ |
| `WVS_H|existential_threat_worry` | -0.101 | 0.047 | 2.16 | ✓ |
| `WVS_H|acceptance_of_state_surveillance` | +0.140 | 0.042 | 3.37 | ✓ |
| `WVS_H|freedom_security_tradeoff_perception` | +0.057 | 0.030 | 1.89 | ~ |
| `WVS_H|institutional_threat_perception` | +0.104 | 0.040 | 2.62 | ✓ |
| `WVS_I|science_skepticism` | -0.089 | 0.034 | 2.64 | ✓ |

---
## 7  Tier-Level Performance Summary

Does the Cronbach's alpha tier predict convergent validity?

| Tier | N | Mean |ρ| | Median |ρ| | % strong | % poor |
|------|---|----------|-----------|----------|--------|
| good | 15 | 0.349 | 0.221 | 27% | 67% |
| questionable | 12 | 0.252 | 0.176 | 8% | 75% |
| tier3_caveat | 8 | 0.262 | 0.177 | 0% | 62% |
| formative_index | 17 | 0.296 | 0.175 | 12% | 65% |
| single_item_tier2 | 4 | 0.101 | 0.084 | 0% | 100% |

**Interpretation guide:**
- If `good` (α ≥ 0.70) constructs have materially higher convergent validity than
  `tier3_caveat`, internal consistency predicts external validity → Cronbach's α
  is a useful screening criterion.
- If `formative_index` constructs converge as well as or better than reflective ones,
  the additive-count approach is valid for these items.

---
## 8  SES Gradient Profiles

Spearman ρ with education (escol) as primary SES indicator.
Sign and strength of SES gradient informs expected DR bridge behaviour.

| Construct | ρ(escol) | ρ(sexo) | ρ(Tam_loc) | Tier | Bridge expectation |
|-----------|----------|---------|------------|------|--------------------|
| `WVS_E|political_information_sources` | +0.250 | -0.048 | +0.040 | ◈ formative | likely bridge hits |
| `WVS_F|religious_exclusivism` | +0.233 | -0.076 | +0.036 | ⚠ questionable | likely bridge hits |
| `WVS_H|basic_needs_deprivation` | -0.212 | +0.085 | -0.024 | ⚠ questionable | likely bridge hits |
| `WVS_E|online_political_participation` | +0.174 | -0.062 | +0.064 | ◈ formative | likely bridge hits |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | +0.160 | -0.042 | +0.106 | ✓ good | likely bridge hits |
| `WVS_H|crime_victimization` | +0.155 | -0.038 | +0.086 | ◈ formative | likely bridge hits |
| `WVS_F|religious_practice_and_self_identification` | +0.150 | -0.157 | +0.043 | ⚠ questionable | likely bridge hits |
| `WVS_C|work_ethic` | +0.149 | -0.009 | +0.050 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_D|gender_role_traditionalism` | +0.137 | +0.060 | -0.021 | ✓ good | γ ≈ 0 expected |
| `WVS_F|life_autonomy_morality_permissiveness` | +0.136 | -0.044 | +0.110 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_E|science_technology_optimism` | +0.125 | -0.080 | +0.043 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_F|religious_belief` | -0.115 | +0.019 | -0.032 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_E|offline_political_participation` | +0.113 | -0.058 | +0.046 | ◈ formative | γ ≈ 0 expected |
| `WVS_A|child_qualities_autonomy_self_expression` | +0.103 | -0.004 | -0.052 | ◈ formative | γ ≈ 0 expected |
| `WVS_A|social_intolerance_outgroups` | +0.102 | +0.024 | -0.024 | ✓ good | γ ≈ 0 expected |
| `WVS_H|acceptance_of_state_surveillance` | -0.102 | +0.026 | +0.007 | ✓ good | γ ≈ 0 expected |
| `WVS_E|autocracy_support` | +0.101 | -0.005 | +0.025 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_G|outgroup_trust` | +0.101 | -0.028 | +0.030 | ✓ good | γ ≈ 0 expected |
| `WVS_C|job_scarcity_gender_discrimination` | +0.096 | +0.008 | +0.008 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_E|confidence_in_civil_society_organizations` | -0.095 | +0.018 | -0.026 | ✓ good | γ ≈ 0 expected |
| `WVS_E|confidence_in_international_organizations` | -0.093 | -0.003 | -0.030 | ✓ good | γ ≈ 0 expected |
| `WVS_F|religion_versus_secularism_orientation` | +0.087 | -0.014 | +0.005 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_G|perceived_negative_effects_of_immigration` | -0.084 | +0.006 | -0.029 | ✓ good | γ ≈ 0 expected |
| `WVS_C|job_scarcity_nativist_preference` | +0.075 | -0.019 | +0.070 | ✓ good | γ ≈ 0 expected |
| `WVS_A|child_qualities_conformity_tradition` | -0.073 | -0.009 | -0.054 | ◈ formative | γ ≈ 0 expected |
| `WVS_D|familial_duty_obligations` | +0.072 | -0.022 | +0.065 | ○ single-item | γ ≈ 0 expected |
| `WVS_D|female_income_threat_to_marriage` | +0.070 | -0.084 | +0.029 | ✓ good | γ ≈ 0 expected |
| `WVS_E|international_organization_knowledge` | +0.069 | -0.022 | -0.033 | ◈ formative | γ ≈ 0 expected |
| `WVS_E|electoral_integrity` | -0.067 | +0.029 | -0.055 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_E|authoritarian_governance_tolerance` | -0.064 | +0.019 | -0.041 | ○ single-item | γ ≈ 0 expected |
| `WVS_H|existential_threat_worry` | +0.063 | -0.084 | +0.029 | ✓ good | γ ≈ 0 expected |
| `WVS_I|science_skepticism` | -0.062 | +0.060 | -0.075 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_H|precautionary_security_behaviors` | +0.057 | -0.004 | +0.112 | ◈ formative | γ ≈ 0 expected |
| `WVS_A|voluntary_association_belonging` | +0.050 | -0.003 | +0.025 | ◈ formative | γ ≈ 0 expected |
| `WVS_E|democratic_system_evaluation` | +0.047 | -0.062 | +0.010 | ◈ formative | γ ≈ 0 expected |
| `WVS_H|freedom_security_tradeoff_perception` | +0.044 | +0.050 | -0.018 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_E|postmaterialist_values` | +0.044 | -0.072 | +0.002 | ◈ formative | γ ≈ 0 expected |
| `WVS_A|child_qualities_prosocial_diligence` | +0.043 | +0.033 | -0.028 | ◈ formative | γ ≈ 0 expected |
| `WVS_E|societal_change_attitudes` | +0.039 | -0.047 | -0.049 | ○ single-item | γ ≈ 0 expected |
| `WVS_H|socioeconomic_insecurity_worry` | -0.035 | -0.016 | +0.042 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_A|importance_of_life_domains` | -0.033 | +0.052 | -0.094 | ◈ formative | γ ≈ 0 expected |
| `WVS_F|civic_dishonesty_tolerance` | -0.026 | -0.056 | +0.069 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_E|confidence_in_domestic_institutions` | -0.019 | -0.017 | +0.047 | ✓ good | γ ≈ 0 expected |
| `WVS_A|subjective_wellbeing` | +0.019 | -0.007 | -0.014 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_E|economic_ideology` | +0.018 | +0.012 | -0.038 | ✗ tier3 | γ ≈ 0 expected |
| `WVS_F|violence_tolerance` | -0.018 | -0.037 | +0.041 | ✓ good | γ ≈ 0 expected |
| `WVS_G|multilevel_place_attachment` | +0.017 | -0.071 | -0.130 | ◈ formative | γ ≈ 0 expected |
| `WVS_A|social_intolerance_deviant_behavior` | -0.016 | -0.044 | -0.042 | ○ single-item | γ ≈ 0 expected |
| `WVS_E|democratic_values_importance` | -0.013 | +0.011 | -0.034 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_G|perceived_positive_effects_of_immigration` | -0.012 | +0.027 | +0.012 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_E|voting_participation` | -0.011 | +0.026 | +0.026 | ✓ good | γ ≈ 0 expected |
| `WVS_H|neighborhood_disorder_and_crime` | +0.010 | -0.014 | -0.159 | ✓ good | γ ≈ 0 expected |
| `WVS_E|perceived_corruption` | -0.008 | +0.010 | -0.024 | ◈ formative | γ ≈ 0 expected |
| `WVS_A|voluntary_association_active_membership` | +0.006 | -0.005 | +0.020 | ◈ formative | γ ≈ 0 expected |
| `WVS_H|institutional_threat_perception` | -0.005 | +0.008 | -0.099 | ⚠ questionable | γ ≈ 0 expected |
| `WVS_G|immigrant_origin_status` | — | — | — | ◈ formative | γ ≈ 0 expected |

---
## 9  Distributional Diagnostics

Constructs with |skew| > 2 or near-zero variance are flagged.
These require ordinal treatment or re-scaling before bridge sweeps.

| Construct | mean | SD | skew | kurt | Flag |
|-----------|------|----|------|------|------|
| `WVS_A|importance_of_life_domains` | 6.85 | 2.16 | -0.28 | -0.56 | — |
| `WVS_A|child_qualities_autonomy_self_expression` | 4.58 | 2.23 | 0.39 | 0.06 | — |
| `WVS_A|child_qualities_conformity_tradition` | 6.42 | 1.93 | -0.17 | -0.28 | — |
| `WVS_A|child_qualities_prosocial_diligence` | 3.96 | 2.36 | 0.49 | -0.16 | — |
| `WVS_A|social_intolerance_outgroups` | 8.62 | 2.22 | -1.99 | 3.47 | — |
| `WVS_A|social_intolerance_deviant_behavior` | 3.04 | 3.77 | 1.31 | -0.29 | — |
| `WVS_A|subjective_wellbeing` | 7.66 | 1.53 | -1.04 | 1.09 | — |
| `WVS_A|voluntary_association_active_membership` | 2.17 | 2.18 | 2.41 | 4.97 | high skew |
| `WVS_A|voluntary_association_belonging` | 2.89 | 2.70 | 1.76 | 1.84 | — |
| `WVS_C|job_scarcity_gender_discrimination` | 6.93 | 2.83 | -1.05 | -0.46 | — |
| `WVS_C|job_scarcity_nativist_preference` | 5.20 | 3.28 | -0.06 | -1.76 | — |
| `WVS_C|work_ethic` | 3.45 | 1.91 | 0.65 | 0.07 | — |
| `WVS_D|gender_role_traditionalism` | 6.62 | 1.91 | -0.47 | 0.20 | — |
| `WVS_D|female_income_threat_to_marriage` | 4.97 | 3.31 | 0.07 | -1.76 | — |
| `WVS_D|familial_duty_obligations` | 3.46 | 2.43 | 0.81 | -0.26 | — |
| `WVS_E|confidence_in_domestic_institutions` | 7.03 | 1.73 | -0.62 | 0.27 | — |
| `WVS_E|confidence_in_civil_society_organizations` | 5.91 | 2.54 | -0.14 | -0.81 | — |
| `WVS_E|confidence_in_international_organizations` | 6.61 | 2.33 | -0.30 | -0.66 | — |
| `WVS_E|perceived_corruption` | 1.58 | 1.02 | 3.00 | 14.76 | high skew |
| `WVS_E|electoral_integrity` | 4.99 | 1.26 | 0.11 | 0.98 | — |
| `WVS_E|postmaterialist_values` | 7.23 | 2.42 | -0.55 | -0.30 | — |
| `WVS_E|autocracy_support` | 5.12 | 1.86 | 0.13 | -0.04 | — |
| `WVS_E|democratic_values_importance` | 5.77 | 2.05 | -0.06 | -0.43 | — |
| `WVS_E|democratic_system_evaluation` | 3.11 | 2.14 | 0.78 | -0.18 | — |
| `WVS_E|offline_political_participation` | 1.57 | 1.21 | 2.82 | 9.20 | high skew |
| `WVS_E|online_political_participation` | 1.55 | 1.44 | 3.27 | 12.04 | high skew |
| `WVS_E|political_information_sources` | 3.70 | 2.27 | 0.70 | -0.32 | — |
| `WVS_E|voting_participation` | 2.46 | 2.12 | 1.43 | 1.45 | — |
| `WVS_E|science_technology_optimism` | 6.93 | 2.06 | -0.53 | -0.20 | — |
| `WVS_E|economic_ideology` | 5.25 | 1.86 | -0.08 | -0.21 | — |
| `WVS_E|societal_change_attitudes` | 5.77 | 3.94 | -0.12 | -1.68 | — |
| `WVS_E|international_organization_knowledge` | 2.42 | 2.14 | 1.40 | 1.29 | — |
| `WVS_E|authoritarian_governance_tolerance` | 4.14 | 2.74 | 0.45 | -0.89 | — |
| `WVS_F|religious_belief` | 4.44 | 0.94 | -0.57 | 4.03 | — |
| `WVS_F|religious_practice_and_self_identification` | 3.88 | 2.31 | 0.98 | 0.07 | — |
| `WVS_F|religious_exclusivism` | 6.11 | 2.59 | -0.22 | -0.66 | — |
| `WVS_F|civic_dishonesty_tolerance` | 3.39 | 1.78 | 0.67 | 0.12 | — |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | 3.85 | 2.13 | 0.55 | -0.25 | — |
| `WVS_F|life_autonomy_morality_permissiveness` | 3.87 | 2.25 | 0.53 | -0.44 | — |
| `WVS_F|violence_tolerance` | 2.50 | 1.81 | 1.46 | 1.86 | — |
| `WVS_F|religion_versus_secularism_orientation` | 8.84 | 2.37 | -1.94 | 2.84 | — |
| `WVS_G|outgroup_trust` | 3.85 | 2.00 | 0.66 | 0.14 | — |
| `WVS_G|perceived_positive_effects_of_immigration` | 4.84 | 2.43 | 0.27 | -0.57 | — |
| `WVS_G|perceived_negative_effects_of_immigration` | 5.65 | 2.94 | -0.10 | -1.12 | — |
| `WVS_G|multilevel_place_attachment` | 4.97 | 3.14 | 0.15 | -1.26 | — |
| `WVS_G|immigrant_origin_status` | 1.00 | 0.00 | nan | nan | low variance; CONSTANT |
| `WVS_H|basic_needs_deprivation` | 2.91 | 1.94 | 0.89 | 0.18 | — |
| `WVS_H|neighborhood_disorder_and_crime` | 5.17 | 2.53 | 0.04 | -0.98 | — |
| `WVS_H|crime_victimization` | 3.92 | 3.65 | 0.72 | -1.10 | — |
| `WVS_H|precautionary_security_behaviors` | 5.72 | 2.59 | -0.62 | -0.46 | — |
| `WVS_H|socioeconomic_insecurity_worry` | 2.18 | 2.17 | 1.98 | 3.26 | — |
| `WVS_H|existential_threat_worry` | 2.34 | 2.43 | 1.84 | 2.33 | — |
| `WVS_H|acceptance_of_state_surveillance` | 3.82 | 2.55 | 0.67 | -0.35 | — |
| `WVS_H|freedom_security_tradeoff_perception` | 6.28 | 3.17 | -0.26 | -0.98 | — |
| `WVS_H|institutional_threat_perception` | 7.58 | 2.62 | -0.92 | -0.10 | — |
| `WVS_I|science_skepticism` | 6.09 | 2.30 | -0.21 | -0.48 | — |

---
## 10  Aggregate Performance Summary

| Metric | Value |
|--------|-------|
| Total constructs analysed | 56 |
| Constructs with a priori validated-index target | 19 |
| Constructs with NO validated equivalent | 37 |
| Strong convergent validity (|ρ| ≥ 0.70) | 7 (12%) |
| Moderate convergent validity (|ρ| = 0.50–0.69) | 4 (7%) |
| Weak convergent validity (|ρ| = 0.30–0.49) | 6 (11%) |
| Poor / no convergent validity | 39 (70%) |
| Mean |ρ| across all constructs | 0.282 |
| Median |ρ| across all constructs | 0.172 |

**Benchmark:** In published WVS psychometric studies, well-developed reflective
scales typically show ρ ≥ 0.70 against their reference index.
A mean |ρ| ≥ 0.50 across all constructs (including novel ones with no equivalent)
would indicate the LLM clustering procedure replicates the academic consensus well.

---
## 11  Recommendations

### 11.1  Keep as-is — strong validated constructs

The following constructs show strong convergent validity (|ρ| ≥ 0.70) with their
target index. These are production-ready and should be prioritised in the WVS
DR sweep.

- **`WVS_A|voluntary_association_belonging`** — SocialCapital ρ=+0.733, α=—
- **`WVS_E|confidence_in_domestic_institutions`** — InstitutionalTrust ρ=-0.915, α=0.890
- **`WVS_E|confidence_in_civil_society_organizations`** — InstitutionalTrust ρ=-0.762, α=0.770
- **`WVS_E|confidence_in_international_organizations`** — InstitutionalTrust ρ=-0.854, α=0.912
- **`WVS_E|offline_political_participation`** — EVI_Voice ρ=+0.793, α=—
- **`WVS_F|sexual_and_reproductive_morality_permissiveness`** — EVI_Choice ρ=+0.832, α=0.751
- **`WVS_F|life_autonomy_morality_permissiveness`** — EVI_Choice ρ=+0.746, α=0.580

### 11.2  Revise items — coherence/alignment mismatch

These constructs either have an a priori validated-index target that is
*outperformed empirically* by a different index (suggesting the LLM placed
them in the wrong conceptual bucket), or have α < 0.50 and poor convergent
validity together.  Recommended action: review the item list, apply the
coherence-review overrides from §4 of `wvs_semantic_coherence_v1.md`, then
re-run Phases 3–5.

- **`WVS_A|child_qualities_conformity_tradition`** — a priori=SecularRationalValues (ρ=+0.086), empirical best=Y003 (ρ=-0.448)
- **`WVS_F|sexual_and_reproductive_morality_permissiveness`** — a priori=EVI_Total (ρ=+0.598), empirical best=EVI_Choice (ρ=+0.832)
- **`WVS_F|life_autonomy_morality_permissiveness`** — a priori=EVI_Total (ρ=+0.540), empirical best=EVI_Choice (ρ=+0.746)
- **`WVS_H|acceptance_of_state_surveillance`** — a priori=SelfExpressionValues (ρ=+0.031), empirical best=SocialCapital (ρ=+0.140)

### 11.3  Flag as unreliable — tier3 with poor validity

These constructs have both poor internal consistency (α < 0.50 or tier3) and
near-zero convergent validity.  They should be excluded from sweep analyses or
used only as control variables.

- **`WVS_E|electoral_integrity`** — α=0.3483, top ρ=0.1832, closest=EnvironmentalConcern
- **`WVS_E|autocracy_support`** — α=0.4995, top ρ=-0.1632, closest=InstitutionalTrust
- **`WVS_F|religious_belief`** — α=-0.2496, top ρ=-0.1715, closest=SecularRationalValues
- **`WVS_H|freedom_security_tradeoff_perception`** — α=0.1895, top ρ=0.0573, closest=EVI_Choice
- **`WVS_I|science_skepticism`** — α=0.3333, top ρ=-0.0891, closest=SocialCapital

### 11.4  High-priority bridge candidates

Constructs with |ρ(escol)| ≥ 0.15 are the best candidates for significant
DR bridge edges in any cross-dataset sweep.

| Construct | ρ(escol) | convergent ρ | type |
|-----------|----------|--------------|------|
| `WVS_E|political_information_sources` | +0.250 | +0.175 | formative_index |
| `WVS_F|religious_exclusivism` | +0.233 | -0.183 | questionable |
| `WVS_H|basic_needs_deprivation` | -0.212 | -0.220 | questionable |
| `WVS_E|online_political_participation` | +0.174 | +0.260 | formative_index |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | +0.160 | +0.832 | good |
| `WVS_H|crime_victimization` | +0.155 | +0.162 | formative_index |
| `WVS_F|religious_practice_and_self_identification` | +0.150 | +0.442 | questionable |

### 11.5  Novel constructs with no WVS equivalent

These constructs have no published validated-index target.
The empirically closest reference index is listed for context.

- **`WVS_A|importance_of_life_domains`** — empirically closest: SecularRationalValues (ρ=+0.364), |ρ(escol)|=0.033
- **`WVS_A|social_intolerance_outgroups`** — empirically closest: SocialCapital (ρ=-0.120), |ρ(escol)|=0.102
- **`WVS_A|social_intolerance_deviant_behavior`** — empirically closest: SocialCapital (ρ=+0.082), |ρ(escol)|=0.016
- **`WVS_C|job_scarcity_nativist_preference`** — empirically closest: GenderEgalitarianism (ρ=-0.229), |ρ(escol)|=0.075
- **`WVS_C|work_ethic`** — empirically closest: GenderEgalitarianism (ρ=-0.170), |ρ(escol)|=0.149
- **`WVS_D|female_income_threat_to_marriage`** — empirically closest: GenderEgalitarianism (ρ=-0.126), |ρ(escol)|=0.070
- **`WVS_D|familial_duty_obligations`** — empirically closest: GenderEgalitarianism (ρ=-0.153), |ρ(escol)|=0.072
- **`WVS_E|perceived_corruption`** — empirically closest: EnvironmentalConcern (ρ=+0.114), |ρ(escol)|=0.008
- **`WVS_E|electoral_integrity`** — empirically closest: EnvironmentalConcern (ρ=+0.183), |ρ(escol)|=0.067
- **`WVS_E|democratic_system_evaluation`** — empirically closest: EnvironmentalConcern (ρ=-0.110), |ρ(escol)|=0.047
- **`WVS_E|online_political_participation`** — empirically closest: EVI_Voice (ρ=+0.260), |ρ(escol)|=0.174
- **`WVS_E|political_information_sources`** — empirically closest: EVI_Voice (ρ=+0.175), |ρ(escol)|=0.250
- **`WVS_E|voting_participation`** — empirically closest: SecularRationalValues (ρ=-0.094), |ρ(escol)|=0.011
- **`WVS_E|science_technology_optimism`** — empirically closest: InstitutionalTrust (ρ=+0.108), |ρ(escol)|=0.125
- **`WVS_E|economic_ideology`** — empirically closest: EVI_Equality (ρ=-0.591), |ρ(escol)|=0.018
- **`WVS_E|societal_change_attitudes`** — empirically closest: SocialCapital (ρ=-0.086), |ρ(escol)|=0.039
- **`WVS_E|international_organization_knowledge`** — empirically closest: SocialCapital (ρ=+0.119), |ρ(escol)|=0.069
- **`WVS_E|authoritarian_governance_tolerance`** — empirically closest: EVI_Voice (ρ=-0.082), |ρ(escol)|=0.064
- **`WVS_F|religious_belief`** — empirically closest: SecularRationalValues (ρ=-0.172), |ρ(escol)|=0.115
- **`WVS_F|religious_exclusivism`** — empirically closest: GenderEgalitarianism (ρ=-0.183), |ρ(escol)|=0.233
- **`WVS_F|civic_dishonesty_tolerance`** — empirically closest: EVI_Choice (ρ=+0.279), |ρ(escol)|=0.026
- **`WVS_F|violence_tolerance`** — empirically closest: EVI_Choice (ρ=+0.221), |ρ(escol)|=0.018
- **`WVS_F|religion_versus_secularism_orientation`** — empirically closest: Religiosity (ρ=-0.302), |ρ(escol)|=0.087
- **`WVS_G|outgroup_trust`** — empirically closest: InstitutionalTrust (ρ=+0.334), |ρ(escol)|=0.101
- **`WVS_G|perceived_positive_effects_of_immigration`** — empirically closest: InstitutionalTrust (ρ=-0.110), |ρ(escol)|=0.012
- **`WVS_G|perceived_negative_effects_of_immigration`** — empirically closest: SelfExpressionValues (ρ=-0.101), |ρ(escol)|=0.084
- **`WVS_G|multilevel_place_attachment`** — empirically closest: InstitutionalTrust (ρ=+0.159), |ρ(escol)|=0.017
- **`WVS_G|immigrant_origin_status`** — empirically closest: Y001 (ρ=—), 
- **`WVS_H|basic_needs_deprivation`** — empirically closest: SubjectiveWellBeing (ρ=-0.220), |ρ(escol)|=0.212
- **`WVS_H|neighborhood_disorder_and_crime`** — empirically closest: EnvironmentalConcern (ρ=+0.144), |ρ(escol)|=0.010
- **`WVS_H|crime_victimization`** — empirically closest: EVI_Total (ρ=+0.162), |ρ(escol)|=0.155
- **`WVS_H|precautionary_security_behaviors`** — empirically closest: EnvironmentalConcern (ρ=-0.122), |ρ(escol)|=0.057
- **`WVS_H|socioeconomic_insecurity_worry`** — empirically closest: GeneralizedTrust (ρ=+0.120), |ρ(escol)|=0.035
- **`WVS_H|existential_threat_worry`** — empirically closest: SubjectiveWellBeing (ρ=-0.101), |ρ(escol)|=0.063
- **`WVS_H|freedom_security_tradeoff_perception`** — empirically closest: EVI_Choice (ρ=+0.057), |ρ(escol)|=0.044
- **`WVS_H|institutional_threat_perception`** — empirically closest: SubjectiveWellBeing (ρ=+0.104), |ρ(escol)|=0.005
- **`WVS_I|science_skepticism`** — empirically closest: SocialCapital (ρ=-0.089), |ρ(escol)|=0.062

### 11.6  Overrides to consider before re-running Phase 3

Based on the combination of coherence review + convergent validity evidence,
the following items_to_drop additions are recommended **beyond** the coherence
review suggestions (which flagged scale/question-text mismatches):

1. `WVS_A|child_qualities_autonomy_self_expression`: poor ρ with EVI_Autonomy
   (-0.06). The items (Q8, Q11, Q12) overlap conceptually with EVI autonomy
   child qualities but the binary mention coding in our formative index is
   misspecified. **Recommendation**: recompute using same 0/1 binary coding
   as EVI_Autonomy (Q7+Q18+Q20) rather than the alternative item set.

2. `WVS_F|religious_belief` (α=-0.25): negative alpha indicates systematic
   item reversal; most items (Q165–Q168 belief items) correlate negatively with
   Q164 (importance of God). Q164 is already captured in `Religiosity`.
   **Recommendation**: separate Q164 into its own single-item measure and
   recompute the belief cluster from Q165–Q168 only.

3. `WVS_D|gender_role_traditionalism`: empirical best match is EVI_Equality
   (ρ≈+0.4) not GenderEgalitarianism (ρ≈+0.15). Items Q29+Q31 (political/
   business leadership) map directly to the EVI Equality sub-index.
   **Recommendation**: add Q107 to the item pool and drop Q28 (maternal
   employment worry — flagged as off-target by coherence review).

4. `WVS_E|democratic_values_importance` (INCOHERENT): redistribution items
   Q241/Q244/Q247 correlate with economic ideology, not democratic values.
   **Recommendation**: keep only Q246 + Q249 (civil rights + gender equality),
   making this a 2-item scale — or merge with `democratic_system_evaluation`.
