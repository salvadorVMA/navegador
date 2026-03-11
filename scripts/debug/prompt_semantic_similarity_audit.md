# Prompt: Semantic Similarity Audit of Cross-Domain SES-Bridge Edges

You are reviewing a network of survey construct pairs that show statistically significant SES-mediated association (Goodman-Kruskal gamma ≠ 0 via Doubly Robust bridge estimation). Your task is to flag edges that may be **tautological or trivially similar** — pairs where the measured association reflects semantic overlap in what the questions ask, rather than a substantively interesting cross-domain relationship.

## Context

- Each node is either an **aggregate construct** (mean of multiple survey items measuring a latent concept) or a **raw variable** (a single survey question selected for its bridging potential).
- All edges are **cross-domain**: they link constructs from different survey instruments administered to different samples. The association is estimated via SES simulation (shared demographic profile imputation), not direct co-observation.
- **Gamma (γ)** measures monotonic ordinal association mediated by SES demographics (sex, age, education, locality size).
- A **tautological edge** is one where both constructs essentially measure the same underlying concept, just with different wording or in a different survey. Such edges are uninformative — they tell us "similar questions get similar answers from similar demographics," which is trivially true.

## Instructions

For each edge below, evaluate:

1. **Semantic similarity**: Do the two constructs/questions ask about the same or very similar things? Consider:
   - Conceptual overlap (e.g., "trust in institutions" ↔ "institutional representativeness")
   - Measurement overlap (e.g., both measure technology access/usage)
   - Domain adjacency (e.g., both tap into education or socioeconomic resources)

2. **Flag level**:
   - 🔴 **TAUTOLOGICAL**: The pair measures essentially the same concept. The edge is uninformative.
   - 🟡 **HIGH OVERLAP**: Substantial conceptual overlap, but there is some meaningful distinction. The edge should be interpreted with caution.
   - 🟢 **SUBSTANTIVE**: The pair links genuinely different concepts. The association is informative.

3. **Brief justification** (1-2 sentences): Why you assigned that flag level.

## Construct Descriptions

### Aggregate Constructs

| Construct | Domain | Description |
|-----------|--------|-------------|
| agg_digital_and_cultural_capital | EDU | Breadth of informational, technological, and cultural resources available to respondents (books, computers, internet, cultural activities) |
| agg_digital_access_and_equipment | SOC | Material dimension of digital inclusion: quantity and variety of technology devices and internet connections |
| agg_science_technology_engagement | CIE | Extent to which respondents actively seek, consume, and engage with science/technology information and activities |
| agg_digital_literacy_and_internet_engagement | SOC | Functional/behavioral dimension of digital inclusion: proficiency and frequency of computer/internet use |
| agg_intimate_partner_control_autonomy | GEN | Extent of control dynamics within romantic partnerships (financial control, isolation, jealousy monitoring) |
| agg_emigration_intention | MIG | Personal disposition and likelihood to emigrate from Mexico |
| agg_media_consumption_and_news_habits | SOC | Breadth, frequency, and preferred channels of news/media consumption |
| agg_religious_socialization_and_identity | REL | Degree of religious identity transmitted through family/education, stability across life |
| agg_civil_liberties_and_protest_rights | DER | Attitudes toward freedom of expression, protest rights, civil disobedience |
| agg_job_quality_precariousness | ECO | Objective conditions of employment: contract type, social security, work schedule, benefits |
| agg_digital_civic_and_political_participation | SOC | Use of digital technologies/social media for civic engagement and political expression |
| agg_school_environment_quality | EDU | Physical and social conditions of school: infrastructure, safety, teacher quality |
| agg_religious_practice_and_devotion | REL | Intensity of personal religious practice: prayer, seeking comfort in faith, ritual attendance |
| agg_household_asset_endowment | HAB | Stock of consumer durables and household goods as SES proxy |
| agg_legal_cynicism_extrajudicial_tolerance | JUS | Distrust of formal legal norms, tolerance for extrajudicial punishment and vigilantism |
| agg_cultural_socialization_in_childhood | DEP | Childhood exposure to cultural practices and resources through parental initiative |
| agg_education_quality_and_opportunity | NIN | Perceptions of educational system quality, accessibility, and adequacy for children/adolescents |
| agg_material_living_standards | POB | Objective household material conditions: dwelling quality, asset ownership |
| agg_global_governance_support | GLO | Support for international institutions, multilateral cooperation, supranational governance |
| agg_functional_health_status | SAL | Degree to which physical health limits everyday activities (mobility, pain, fatigue) |
| agg_cultural_openness | GLO | Receptivity to foreign cultures, media, and consumption practices |
| agg_basic_services_access | HAB | Availability/reliability of essential infrastructure: water, drainage, electricity, sanitation |
| agg_federalism_preference | FED | Preferences for how political/fiscal authority should be distributed across government levels |
| agg_institutional_trust_and_representativeness | FED | Trust in and feeling represented by key political institutions and actors |
| agg_socioeconomic_environmental_context | MED | Material/infrastructural conditions of households and communities shaping environmental exposure |
| agg_procedural_justice_expectations | JUS | Expectations about fair treatment by justice system actors (courts, police, public ministry) |
| agg_child_agency_and_participation | NIN | Attitudes toward voice, autonomy, and civic participation of children/adolescents |
| agg_institutional_and_social_trust | IDE | Trust in formal institutions (police) and informal social actors (neighbors, strangers) |
| agg_intergenerational_contact_and_family_integration | ENV | Integration of older adults into family life and decision-making |
| agg_pro_environmental_civic_engagement | MED | Collective/civic action taken to address environmental issues |
| agg_ethnocultural_identity_and_linguistic_capital | DEP | Identification with indigenous/minority cultural heritage, linguistic competence |
| agg_tolerance_of_gender_based_violence | GEN | Attitudes toward acceptability of physical/emotional violence against women |
| agg_victimization_exposure | SEG | Direct experience of crime victimization at household/personal level |
| agg_human_capital_labor_alignment | ECO | Relationship between educational attainment, training, and job skill requirements |
| agg_science_self_efficacy | CIE | Perceived ability to understand and engage with science and technology |
| agg_cosmopolitan_identity | GLO | Identification as citizen of the world vs. exclusively national |
| agg_children_rights_recognition | NIN | Recognition and endorsement of fundamental rights of children and adolescents |
| agg_legal_problem_resolution_efficacy | JUS | Practical experience resolving everyday legal/administrative disputes |
| agg_national_cultural_pride | GLO | Pride toward specific Mexican cultural symbols, traditions, social characteristics |
| agg_physical_housing_quality | HAB | Structural/material quality of dwelling: walls, roof, floor composition |
| agg_gender_role_traditionalism | GEN | Endorsement of traditional patriarchal norms about gender roles |
| agg_supernatural_belief_system | REL | Breadth of supernatural/metaphysical beliefs: orthodox religious doctrines and folk beliefs |
| agg_ageism_and_age_discrimination | ENV | Attitudes about discrimination and unequal treatment of older adults |
| agg_science_technology_policy_attitudes | CIE | Normative beliefs about science/technology's role in addressing national problems |
| agg_fear_of_crime_and_risk_perception | SEG | Subjective insecurity and perceived likelihood of crime victimization |

### Raw Variables (Single Survey Questions)

| Variable | Domain | Survey | Question Text |
|----------|--------|--------|---------------|
| p14 | HAB | HABITABILIDAD | "¿A quién pertenece esta vivienda?" (Who owns this dwelling?) |
| p18_1a_1 | IND | INDIGENAS | "Podría mencionarme tres grupos indígenas que recuerde: 1° mención" (Name three indigenous groups: 1st mention) |
| p18_1 | DEP | CULTURA_LECTURA_Y_DEPORTE | "¿Para qué sirve la lectura? 1° mención" (What is reading for? 1st mention) |
| p19 | ECO | ECONOMIA_Y_EMPLEO | "¿Cuál de estos valora usted más?" (Which of these [job attributes] do you value most?) |
| p1_2 | EDU | EDUCACION_Y_VALORES | "¿Cuál es el máximo nivel de escolaridad de su padre?" (Father's maximum education level) |
| p23_1 | SAL | SALUD | "¿Qué tan de acuerdo está con que buscar atención médica les afecta económicamente?" (Healthcare causes economic hardship — agree/disagree) |
| p24 | SAL | SALUD | "Si necesitara ir al médico, ¿a dónde iría?" (Where would you go for medical attention?) |
| p26_1 | NIN | NINOS_ADOLESCENTES | "¿Cuándo se justifica pegarle a un niño? 1° mención" (When is hitting a child justified? 1st mention) |
| p34 | SAL | SALUD | "¿Con qué frecuencia tomó alcohol en los últimos 12 meses?" (Alcohol frequency, past 12 months) |
| p52 | DEP | CULTURA_LECTURA_Y_DEPORTE | "¿Cuál emoción refleja mejor lo que siente sobre México?" (Which emotion best reflects how you feel about Mexico?) |

## Edges to Evaluate (56 total)

Format: [Tier] γ = value | Source (Domain) ↔ Target (Domain)

### Tier A — CI excludes zero (38 edges)

1. [A] γ=+0.205 | agg_digital_and_cultural_capital (EDU) ↔ agg_digital_access_and_equipment (SOC)
2. [A] γ=-0.176 | agg_science_technology_engagement (CIE) ↔ agg_digital_literacy_and_internet_engagement (SOC)
3. [A] γ=-0.150 | agg_intimate_partner_control_autonomy (GEN) ↔ agg_digital_literacy_and_internet_engagement (SOC)
4. [A] γ=-0.142 | agg_emigration_intention (MIG) ↔ agg_media_consumption_and_news_habits (SOC)
5. [A] γ=+0.137 | agg_religious_socialization_and_identity (REL) ↔ agg_media_consumption_and_news_habits (SOC)
6. [A] γ=+0.137 | agg_civil_liberties_and_protest_rights (DER) ↔ agg_digital_and_cultural_capital (EDU)
7. [A] γ=+0.135 | agg_job_quality_precariousness (ECO) ↔ p1_2 [father's education] (EDU)
8. [A] γ=+0.110 | agg_science_technology_engagement (CIE) ↔ agg_intimate_partner_control_autonomy (GEN)
9. [A] γ=-0.100 | agg_science_technology_engagement (CIE) ↔ agg_emigration_intention (MIG)
10. [A] γ=-0.097 | p1_2 [father's education] (EDU) ↔ agg_digital_civic_and_political_participation (SOC)
11. [A] γ=+0.094 | agg_science_technology_engagement (CIE) ↔ agg_digital_civic_and_political_participation (SOC)
12. [A] γ=+0.094 | agg_science_technology_engagement (CIE) ↔ agg_school_environment_quality (EDU)
13. [A] γ=-0.074 | agg_religious_practice_and_devotion (REL) ↔ agg_digital_access_and_equipment (SOC)
14. [A] γ=-0.067 | agg_household_asset_endowment (HAB) ↔ agg_legal_cynicism_extrajudicial_tolerance (JUS)
15. [A] γ=+0.065 | agg_cultural_socialization_in_childhood (DEP) ↔ agg_emigration_intention (MIG)
16. [A] γ=-0.064 | agg_education_quality_and_opportunity (NIN) ↔ agg_material_living_standards (POB)
17. [A] γ=+0.059 | agg_global_governance_support (GLO) ↔ agg_digital_access_and_equipment (SOC)
18. [A] γ=-0.054 | agg_functional_health_status (SAL) ↔ agg_digital_civic_and_political_participation (SOC)
19. [A] γ=+0.054 | agg_cultural_openness (GLO) ↔ agg_basic_services_access (HAB)
20. [A] γ=-0.054 | agg_federalism_preference (FED) ↔ agg_religious_practice_and_devotion (REL)
21. [A] γ=+0.050 | p14 [housing tenure] (HAB) ↔ agg_material_living_standards (POB)
22. [A] γ=+0.050 | agg_job_quality_precariousness (ECO) ↔ agg_victimization_exposure (SEG)
23. [A] γ=+0.050 | p14 [housing tenure] (HAB) ↔ agg_functional_health_status (SAL)
24. [A] γ=-0.046 | agg_human_capital_labor_alignment (ECO) ↔ agg_victimization_exposure (SEG)
25. [A] γ=-0.046 | agg_legal_problem_resolution_efficacy (JUS) ↔ agg_education_quality_and_opportunity (NIN)
26. [A] γ=-0.041 | agg_institutional_trust_and_representativeness (FED) ↔ agg_digital_civic_and_political_participation (SOC)
27. [A] γ=-0.038 | agg_institutional_trust_and_representativeness (FED) ↔ agg_socioeconomic_environmental_context (MED)
28. [A] γ=+0.035 | agg_basic_services_access (HAB) ↔ agg_religious_socialization_and_identity (REL)
29. [A] γ=-0.034 | agg_procedural_justice_expectations (JUS) ↔ p26_1 [when is hitting a child justified] (NIN)
30. [A] γ=+0.033 | agg_procedural_justice_expectations (JUS) ↔ agg_child_agency_and_participation (NIN)
31. [A] γ=+0.031 | agg_intergenerational_contact_and_family_integration (ENV) ↔ agg_intimate_partner_control_autonomy (GEN)
32. [A] γ=-0.029 | agg_institutional_and_social_trust (IDE) ↔ agg_emigration_intention (MIG)
33. [A] γ=+0.028 | agg_intergenerational_contact_and_family_integration (ENV) ↔ agg_pro_environmental_civic_engagement (MED)
34. [A] γ=+0.026 | p52 [emotion about Mexico] (DEP) ↔ p14 [housing tenure] (HAB)
35. [A] γ=-0.022 | agg_institutional_trust_and_representativeness (FED) ↔ p26_1 [when is hitting a child justified] (NIN)
36. [A] γ=+0.020 | agg_ethnocultural_identity_and_linguistic_capital (DEP) ↔ agg_digital_civic_and_political_participation (SOC)
37. [A] γ=-0.019 | agg_tolerance_of_gender_based_violence (GEN) ↔ agg_victimization_exposure (SEG)
38. [A] γ=+0.015 | agg_global_governance_support (GLO) ↔ agg_child_agency_and_participation (NIN)

### Tier B — Zero within 2.5% of CI edge (6 edges)

39. [B] γ=-0.108 | agg_functional_health_status (SAL) ↔ agg_media_consumption_and_news_habits (SOC)
40. [B] γ=-0.073 | agg_basic_services_access (HAB) ↔ agg_legal_cynicism_extrajudicial_tolerance (JUS)
41. [B] γ=-0.034 | agg_gender_role_traditionalism (GEN) ↔ agg_pro_environmental_civic_engagement (MED)
42. [B] γ=-0.027 | p19 [job value preference] (ECO) ↔ agg_digital_access_and_equipment (SOC)
43. [B] γ=+0.025 | agg_socioeconomic_environmental_context (MED) ↔ agg_religious_practice_and_devotion (REL)
44. [B] γ=+0.022 | p26_1 [when is hitting a child justified] (NIN) ↔ agg_digital_civic_and_political_participation (SOC)

### Tier C — Zero within 5% of CI edge (12 edges)

45. [C] γ=+0.146 | agg_intergenerational_contact_and_family_integration (ENV) ↔ agg_media_consumption_and_news_habits (SOC)
46. [C] γ=+0.135 | agg_job_quality_precariousness (ECO) ↔ agg_ageism_and_age_discrimination (ENV)
47. [C] γ=+0.133 | agg_cultural_openness (GLO) ↔ agg_media_consumption_and_news_habits (SOC)
48. [C] γ=+0.104 | agg_science_technology_engagement (CIE) ↔ agg_human_capital_labor_alignment (ECO)
49. [C] γ=-0.103 | agg_science_self_efficacy (CIE) ↔ agg_intimate_partner_control_autonomy (GEN)
50. [C] γ=-0.065 | agg_physical_housing_quality (HAB) ↔ agg_digital_literacy_and_internet_engagement (SOC)
51. [C] γ=+0.055 | agg_human_capital_labor_alignment (ECO) ↔ agg_children_rights_recognition (NIN)
52. [C] γ=+0.043 | agg_civil_liberties_and_protest_rights (DER) ↔ agg_cosmopolitan_identity (GLO)
53. [C] γ=-0.034 | agg_procedural_justice_expectations (JUS) ↔ agg_supernatural_belief_system (REL)
54. [C] γ=-0.034 | agg_cultural_socialization_in_childhood (DEP) ↔ agg_cultural_openness (GLO)
55. [C] γ=-0.031 | agg_cultural_openness (GLO) ↔ agg_socioeconomic_environmental_context (MED)
56. [C] γ=+0.019 | agg_national_cultural_pride (GLO) ↔ agg_material_living_standards (POB)

## Output Format

For each edge, respond with:

```
Edge #N: [Source] ↔ [Target]
Flag: 🔴/🟡/🟢
Justification: [1-2 sentences]
```

After reviewing all 56 edges, provide a summary:
- Count of each flag level
- List the 🔴 TAUTOLOGICAL edges (if any) that should be excluded from substantive interpretation
- List the 🟡 HIGH OVERLAP edges that need cautious interpretation
- Any patterns you notice (e.g., certain domains or construct types that tend to produce tautological edges)
