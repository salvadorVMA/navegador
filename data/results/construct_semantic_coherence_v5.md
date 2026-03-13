# Construct Semantic Coherence Review — V5

Generated: 2026-03-13 20:23

## Summary

| Metric | Count |
|--------|-------|
| Constructs reviewed | 79 |
| COHERENT | 22 |
| MIXED | 56 |
| INCOHERENT | 1 |
| ERROR | 0 |
| Items flagged for removal | 83 |
| Constructs with ≥1 flagged item | 56 |

## Suggested items_to_drop Additions

Paste into `construct_v5_overrides.json` → `items_to_drop`:

```json
  "CIE|household_science_cultural_capital": ["p3_11"],
  "CIE|institutional_trust_in_science": ["p49_1"],
  "CIE|perceived_societal_value_of_science_technology": ["p57", "p58", "p51_1"],
  "CIE|science_technology_interest_engagement": ["p38_4", "p38_5", "p38_6"],
  "CUL|authoritarian_predisposition": ["p60", "p23"],
  "CUL|democratic_legitimacy_support": ["p30"],
  "CUL|institutional_trust_and_electoral_confidence": ["p71", "p72"],
  "CUL|political_efficacy_and_engagement": ["p21", "p51"],
  "DEP|attitudes_toward_cultural_openness_and_foreign_influence": ["p29_1"],
  "DEP|cultural_identity_and_heritage": ["p34", "p35"],
  "DEP|cultural_socialization_in_childhood": ["p12_1"],
  "DER|institutional_trust_justice": ["p19"],
  "DER|perceived_discrimination_social_exclusion": ["p36_1", "p40_1"],
  "DER|rights_awareness_personal_experience": ["p53"],
  "ECO|labor_union_attitudes": ["p22"],
  "EDU|digital_and_cultural_capital": ["p47_6"],
  "EDU|social_media_engagement": ["p48_1", "p48_3", "p44_5"],
  "ENV|ageism_and_negative_stereotypes": ["p27"],
  "ENV|state_and_family_responsibility_for_elder_care": ["p44", "p30", "p31"],
  "FAM|conjugal_union_attitudes": ["p33"],
  "FAM|family_cohesion_quality": ["p27", "p52", "p53"],
  "FAM|family_value_transmission": ["p57"],
  "FAM|ideal_family_normativity": ["p67", "p68"],
  "FAM|intergenerational_obligations": ["p62", "p63"],
  "FED|fiscal_and_service_federalism_preferences": ["p37_1"],
  "FED|perceived_representativeness": ["p12_1"],
  "FED|security_governance_preferences": ["p47"],
  "GEN|traditional_gender_role_attitudes": ["p61_1", "p63_1", "p59_1"],
  "GLO|economic_globalization_attitudes": ["p49_1"],
  "GLO|international_institutional_engagement": ["p58"],
  "HAB|basic_services_access": ["p8", "p36_30"],
  "IDE|moral_normative_conservatism": ["p57"],
  "IDE|personal_optimism_efficacy": ["p24"],
  "IDE|tolerance_social_diversity": ["p54_5", "p54_6", "p54_8"],
  "IND|perceived_indigenous_discrimination": ["p20"],
  "IND|social_distance_toward_indigenous_people": ["p39_1"],
  "JUS|judicial_institutional_trust": ["p43"],
  "JUS|law_compliance_motivation": ["p8", "p9", "p10"],
  "MED|environmental_knowledge_self_efficacy": ["p28_1", "p36_1"],
  "MED|environmental_problem_salience": ["p6"],
  "MED|pro_environmental_civic_engagement": ["p34_5"],
  "MIG|attitudes_toward_foreigners_in_mexico": ["p44"],
  "MIG|perceived_opportunity_structure": ["p3_9"],
  "NIN|perceived_situation_of_children_and_youth": ["p61"],
  "NIN|youth_participation_and_voice": ["p41", "p47"],
  "POB|intergenerational_mobility_perception": ["p36"],
  "POB|subjective_economic_wellbeing_and_agency": ["p10"],
  "REL|church_state_separation": ["p58"],
  "REL|personal_religiosity": ["p11"],
  "REL|supernatural_beliefs": ["p17_15"],
  "SAL|health_risk_behaviors": ["p28"],
  "SAL|subjective_wellbeing": ["p8_1"],
  "SEG|fear_and_risk_avoidance": ["p48", "p49"],
  "SEG|punitive_and_vigilante_attitudes": ["p72"],
  "SOC|media_trust_and_quality_evaluation": ["p53_1"],
  "SOC|perceived_media_social_impact": ["p63_1"],
```

## All Constructs

| Key | Verdict | Flagged items | Reason |
|-----|---------|---------------|--------|
| `IDE|tolerance_social_diversity` | MIXED | `p54_5`, `p54_6`, `p54_8` | Most items measure tolerance attitudes, but p54_5, p54_6, and p54_8 measure actual social contact/friendship patterns rather than openness or acceptance beliefs. |
| `IDE|personal_optimism_efficacy` | MIXED | `p24` | Most items measure personal agency and optimism about the future, but p24 measures retrospective life satisfaction rather than forward-looking efficacy or control. |
| `IDE|moral_normative_conservatism` | MIXED | `p57` | Most items measure moral conservatism on family and sexuality norms, but p57 measures political ideology which is conceptually distinct from moral normative conservatism. |
| `MED|environmental_problem_salience` | MIXED | `p6` | Items p4 and p7 align well with the construct, but p6 measures problem prioritization rather than perceived severity or personal relevance. |
| `MED|environmental_knowledge_self_efficacy` | MIXED | `p28_1`, `p36_1` | Most items measure self-assessed knowledge (self-efficacy), but p28_1 and p36_1 measure actual knowledge/recall rather than perceived competence. |
| `MED|pro_environmental_civic_engagement` | MIXED | `p34_5` | Most items measure active civic/collective environmental actions, but p34_5 measures passive attendance at informational events rather than active engagement. |
| `POB|intergenerational_mobility_perception` | MIXED | `p36` | Three items directly measure perceived intergenerational mobility, but p36 measures beliefs about structural barriers (education-employment link) rather than perceived mobility outcomes or opportunities. |
| `POB|subjective_economic_wellbeing_and_agency` | MIXED | `p10` | Most items measure subjective economic wellbeing and agency as described, but p10 measures objective social class identification rather than subjective economic control or life satisfaction. |
| `CUL|democratic_legitimacy_support` | MIXED | `p30` | Most items measure normative commitment to democracy and satisfaction with democratic functioning, but p30 measures conceptual understanding of democracy rather than valuation or trust in it. |
| `CUL|institutional_trust_and_electoral_confidence` | MIXED | `p71`, `p72` | Most items measure electoral integrity perceptions and institutional trust in electoral bodies, but p71 and p72 shift focus to vote-buying behavior—a substantively distinct electoral malpractice rather than trust in institutions or confidence in process integrity. |
| `CUL|political_efficacy_and_engagement` | MIXED | `p21`, `p51` | Most items measure political interest, relevance, and efficacy as described, but p21 measures beliefs about political outcomes rather than personal efficacy or engagement, and p51 conflates satisfaction with participation opportunities with lack of interest. |
| `CUL|authoritarian_predisposition` | MIXED | `p60`, `p23` | Most items measure authoritarian predisposition coherently, but p60 measures democratic compliance behavior rather than authoritarian preference, and p23 measures pragmatic problem-solving rather than authoritarianism. |
| `CUL|perceived_political_influence_of_actors` | COHERENT | — | All items directly measure perceived political influence of specified actors using identical semantic framing and response scales. |
| `REL|supernatural_beliefs` | MIXED | `p17_15` | Most items validly measure supernatural and religious beliefs, but p17_15 measures a naturalistic psychological/cognitive phenomenon rather than a supernatural entity or force. |
| `REL|personal_religiosity` | MIXED | `p11` | Most items measure internalized religious practice and meaning-making, but one item measures a specific behavioral tendency that conflates religious practice with folk devotionalism in a way that may not reflect personal religiosity as defined. |
| `REL|religious_socialization` | COHERENT | — | All three items directly measure core components of religious socialization: family religious homogeneity, formal religious education received, and intergenerational transmission of religious beliefs. |
| `REL|church_state_separation` | MIXED | `p58` | Most items directly measure church-state separation attitudes, but p58 conflates a descriptive premise (media currently broadcasts religious content) with an attitudinal question, making it semantically distinct from the normative boundary-setting focus of other items. |
| `SEG|perceived_security_trajectory` | COHERENT | — | All four items directly measure retrospective and prospective security trajectory assessments at both personal and national levels, with clear semantic alignment to the construct definition. |
| `SEG|police_institutional_legitimacy` | COHERENT | — | All three items measure distinct but semantically related dimensions of police institutional legitimacy: perceived corruption, human rights violations, and normative acceptance of police authority. |
| `SEG|fear_and_risk_avoidance` | MIXED | `p48`, `p49` | Most items measure fear of crime victimization and avoidance behaviors, but two items measure fear of wrongful arrest and perceived probability of unjust imprisonment, which are substantively distinct constructs. |
| `SEG|punitive_and_vigilante_attitudes` | MIXED | `p72` | Four items directly measure punitive and vigilante attitudes, but p72 measures approval of specific government anti-drug actions rather than endorsement of coercive or extralegal response principles. |
| `SAL|functional_health_status` | COHERENT | — | All items directly measure physical health limitations on everyday functioning within the specified domain of moderate physical effort, stair climbing, and activity/work reduction. |
| `SAL|subjective_wellbeing` | MIXED | `p8_1` | Most items validly measure subjective wellbeing dimensions, but one item measures emotional state rather than self-assessed quality of life or satisfaction. |
| `SAL|health_risk_behaviors` | MIXED | `p28` | Items p34 and p35 directly measure alcohol consumption frequency and intensity as described, but p28 measures only lifetime smoking history without capturing current smoking intensity or frequency. |
| `IND|perceived_indigenous_discrimination` | MIXED | `p20` | Most items directly measure perceived discrimination against indigenous people, but p20 measures general skin color discrimination without indigenous-specific focus, making it tangentially related rather than directly on-target. |TODO leave as is
| `IND|social_distance_toward_indigenous_people` | MIXED | `p39_1` | Two items measure willingness/acceptance (on-target), but one item measures past behavior/experience rather than willingness or social distance. |
| `IND|national_economic_outlook` | COHERENT | — | Both items directly measure the intended construct of national economic outlook through retrospective (p1) and prospective (p2) evaluations of Mexico's economic situation. |
| `SOC|media_trust_and_quality_evaluation` | MIXED | `p53_1` | Most items measure critical assessment of media quality and coverage, but p53_1 measures trust in family information sources, which is semantically distinct from evaluating media institutions. |
| `SOC|perceived_media_social_impact` | MIXED | `p63_1` | Most items measure perceived societal consequences of media content, but p63_1 measures parental behavior/responsibility rather than beliefs about media's societal impact. |
| `ENV|ageism_and_negative_stereotypes` | MIXED | `p27` | Three items directly measure ageist stereotypes and discriminatory attitudes, but one item measures perceived labor market conditions rather than personal stereotyping or discriminatory beliefs. |
| `ENV|state_and_family_responsibility_for_elder_care` | MIXED | `p44`, `p30`, `p31` | The construct mixes normative beliefs about responsibility allocation with behavioral outcomes and descriptive observations, creating semantic heterogeneity. |
| `ENV|assessment_of_older_adult_wellbeing_and_social_conditions` | COHERENT | — | All three items measure respondents' evaluations of older adults' circumstances in Mexico—past trends, future prospects, and societal recognition—which directly align with the construct's focus on assessment of wellbeing, social conditions, and salience of their problems. |
| `DER|institutional_trust_justice` | MIXED | `p19` | Most items measure trust and perceived legitimacy of justice institutions, but p19 shifts focus to victim treatment quality, which is a distinct outcome rather than institutional trust. |
| `DER|authoritarian_security_tradeoff` | COHERENT | — | All three items directly measure acceptance of coercive state practices and rights violations framed as necessary for security purposes. |
| `DER|perceived_discrimination_social_exclusion` | MIXED | `p36_1`, `p40_1` | Most items measure perceived discrimination and attitudes toward vulnerable groups, but two items measure personal discriminatory intentions rather than perceptions of discrimination or social exclusion. |
| `DER|rights_awareness_personal_experience` | MIXED | `p53` | The construct targets personal experience with human rights and labor rights violations, but includes school bullying which is a distinct harm domain outside the rights violation framework. |
| `DER|social_rights_service_quality` | COHERENT | — | All three items directly measure perceived quality/adequacy of distinct social rights domains (health services, housing, education) that align with the construct definition. |
| `COR|corruption_perception` | COHERENT | — | All items measure subjective perceptions of corruption's prevalence, trajectory, or spatial location in Mexico, directly aligned with the construct definition. |
| `COR|civic_enforcement_norms` | COHERENT | — | All items consistently measure beliefs about appropriate sanctions for rule violations and personal behavioral responses to misconduct across different social contexts. |
| `HAB|structural_housing_quality` | COHERENT | — | All three items directly measure the physical material composition of core structural elements (walls, roof, floor) that collectively indicate structural adequacy and habitability. |
| `HAB|basic_services_access` | MIXED | `p8`, `p36_30` | Most items directly measure basic service availability, but p8 conflates sanitation facility type with drainage access, and p36_30 is redundant with p10. |
| `HAB|household_asset_endowment` | COHERENT | — | All items measure the presence of durable goods and domestic appliances in the household, directly operationalizing the construct of household asset endowment as a socioeconomic status proxy. |
| `GLO|economic_globalization_attitudes` | MIXED | `p49_1` | Most items measure attitudes toward economic globalization and trade, but p49_1 shifts focus to a specific sectoral foreign investment policy question that may reflect regulatory/nationalist concerns distinct from general trade attitudes. |
| `GLO|international_institutional_engagement` | MIXED | `p58` | Most items measure support for international institutional engagement, but p58 measures behavioral intention/willingness to use institutions rather than support for institutional authority. |
| `JUS|judicial_institutional_trust` | MIXED | `p43` | Most items validly measure judicial institutional trust, but p43 measures normative preferences about judicial philosophy rather than perceived legitimacy or trustworthiness of institutions. |
| `JUS|legal_cynicism_extrajudicial_justice` | COHERENT | — | All items directly measure core dimensions of legal cynicism: tolerance for extrajudicial punishment, acceptance of lethal force outside due process, willingness to override judicial authority, belief in informal connections determining outcomes, and skepticism of judicial verdicts. |
| `JUS|law_compliance_motivation` | MIXED | `p8`, `p9`, `p10` | Items p7 directly measures motivational basis for compliance, but p8, p9, and p10 measure perceived or self-assessed law-abidingness rather than the underlying reasons for compliance. |
| `MIG|emigration_intention_likelihood` | COHERENT | — | All three items directly measure emigration intention and likelihood through complementary approaches: willingness for work-related emigration, general emigration preference, and prospective probability. |
| `MIG|perceived_opportunity_structure` | MIXED | `p3_9` | Most items validly measure perceived opportunity structure in Mexico, but p3_9 measures perceived opportunity to leave Mexico rather than opportunities within Mexico's structural context. |
| `MIG|attitudes_toward_foreigners_in_mexico` | MIXED | `p44` | Most items measure attitudes toward foreigners, but p44 is a behavioral/demographic item measuring actual contact rather than evaluative orientation. |
| `FED|perceived_representativeness` | MIXED | `p12_1` | Item p12_1 measures party representativeness rather than elected officials' representativeness, introducing a conceptually distinct element into a scale otherwise focused on multi-level political representation. |
| `FED|fiscal_and_service_federalism_preferences` | MIXED | `p37_1` | Most items validly measure federalism preferences regarding distribution of responsibilities and resources, but p37_1 measures satisfaction with service delivery rather than preferences about how governance should be structured. |
| `FED|legal_uniformity_preference` | COHERENT | — | All items consistently measure preference for national versus state-level legal uniformity across the specified policy domains, directly operationalizing the normative dimension of legal centralization. |
| `FED|security_governance_preferences` | MIXED | `p47` | Most items measure preferences and evaluations of security governance levels, but p47 measures performance satisfaction rather than governance preferences or coordination assessments. |
| `FED|political_interest_and_engagement` | COHERENT | — | All three items directly measure core dimensions of political interest and engagement: news consumption frequency, self-reported political interest, and perceived relevance of politics to daily life. |
| `GEN|traditional_gender_role_attitudes` | MIXED | `p61_1`, `p63_1`, `p59_1` | Most items measure traditional gender role attitudes, but two items measure gender stereotypes and ideological equivalence rather than endorsement of traditional role norms. |
| `GEN|intimate_partner_power_dynamics` | COHERENT | — | All three items directly measure power imbalances and autonomy restrictions within intimate partnerships across distinct domains (financial control, movement freedom, and family contact). |
| `DEP|cultural_socialization_in_childhood` | MIXED | `p12_1` | Two items measure parental cultural socialization behavior, but one item measures the child's own reading behavior, which is an outcome rather than exposure to parental cultural transmission. |
| `DEP|reading_engagement_and_literacy` | MIXED | — | Items measure only one narrow subdomain (reading habits for newspapers/magazines) and omit key construct elements like access to books, reading ability, and barriers to reading. |
| `DEP|cultural_identity_and_heritage` | MIXED | `p34`, `p35` | Most items validly measure cultural identity and heritage self-identification, but two items measuring indigenous language ability are tangentially related behavioral competencies rather than direct measures of cultural belonging or self-identification. | TODO leave as is
| `DEP|attitudes_toward_cultural_openness_and_foreign_influence` | MIXED | `p29_1` | Most items measure attitudes toward cultural openness and pluralism, but p29_1 measures behavioral preference for cultural preservation rather than attitudes toward openness/foreign influence. |
| `ECO|economic_wellbeing_perception` | COHERENT | — | All three items directly measure economic wellbeing perception across personal, national, and intergenerational dimensions as described in the construct definition. |
| `ECO|labor_union_attitudes` | MIXED | `p22` | Two items directly measure union attitudes, but one item measures perceived labor rights respect, which is a contextual outcome rather than an evaluative orientation toward unions themselves. |
| `NIN|perceived_situation_of_children_and_youth` | MIXED | `p61` | Two items measure general situation perception across age groups, but one item narrows focus specifically to economic situation, introducing a substantive domain distinction. |
| `NIN|youth_participation_and_voice` | MIXED | `p41`, `p47` | Most items directly measure normative attitudes toward youth voice and participation, but p41 and p47 shift focus to conditional participation scenarios and rights frameworks rather than attitudes about whether youth opinions should be heard. |
| `FAM|family_cohesion_quality` | MIXED | `p27`, `p52`, `p53` | Items p25 and p26 directly measure perceived relationship quality, but p27, p52, and p53 measure beliefs about what determines or sustains family cohesion rather than the respondent's actual perception of their own family's cohesion quality. |
| `FAM|ideal_family_normativity` | MIXED | `p67`, `p68` | Items p13-p16 directly measure normative beliefs about ideal family structure and ideology, but p67-p68 measure descriptive observations about family change rather than normative beliefs about what should be ideal. |
| `FAM|intergenerational_obligations` | MIXED | `p62`, `p63` | Items p28-p29 and p64 measure normative beliefs about intergenerational obligations, while p62-p63 measure behavioral/actual coping strategies and current care arrangements, which are outcomes rather than attitudinal beliefs about obligations. |
| `FAM|conjugal_union_attitudes` | MIXED | `p33` | Most items measure attitudes toward conjugal unions, but p33 is a behavioral disclosure item that measures past conduct rather than attitudes or normative orientations. |
| `FAM|family_value_transmission` | MIXED | `p57` | Two items directly measure family value transmission, but one item measures religious influence on family life, which is a contextual factor rather than the values themselves. |
| `CIE|science_technology_self_efficacy` | COHERENT | — | All three items directly measure perceived competence and self-assessed ability to understand science and technology, which are core components of science-technology self-efficacy. |
| `CIE|science_technology_interest_engagement` | MIXED | `p38_4`, `p38_5`, `p38_6` | Most items validly measure science and technology interest and engagement, but three items (p38_4, p38_5, p38_6) measure interest in specific science policy/environmental topics rather than general science-technology interest or media consumption behavior. |
| `CIE|institutional_trust_in_science` | MIXED | `p49_1` | Most items measure institutional trust and perceived integrity of scientists, but p49_1 measures a normative belief about what universities should do rather than trust in or perception of scientific institutions. |
| `CIE|perceived_societal_value_of_science_technology` | MIXED | `p57`, `p58`, `p51_1` | Most items measure perceived societal value of science/technology, but two items measure evaluations of institutional efficiency and policy preferences rather than beliefs about practical contribution and importance. |
| `CIE|household_science_cultural_capital` | MIXED | `p3_11` | Most items validly measure scientific and educational cultural capital through books and digital infrastructure, but one item measures educational resources that are functional/curricular rather than cultural capital. |
| `EDU|perceived_education_quality` | COHERENT | — | Both items directly measure perceived education quality through complementary dimensions: trend perception and relevance evaluation. |
| `EDU|educational_returns_belief` | COHERENT | — | All four items directly measure beliefs about the instrumental value (employment, income) and social value (societal well-being) of education, as well as overall perceived worthwhileness of studying. |
| `EDU|digital_and_cultural_capital` | MIXED | `p47_6` | Most items measure technology access and reading habits as intended, but smartphone ownership (p47_6) is a tangential proxy for digital capital rather than a direct measure of access to or use of ICTs for learning. |
| `EDU|social_media_engagement` | INCOHERENT | `p48_1`, `p48_3`, `p44_5` | The construct mixes computer use for information/education with museum/exhibition attendance, which are substantively distinct behaviors unrelated to social media engagement or account ownership. |

## Flagged Constructs

### `IDE|tolerance_social_diversity`

**Verdict**: MIXED — Most items measure tolerance attitudes, but p54_5, p54_6, and p54_8 measure actual social contact/friendship patterns rather than openness or acceptance beliefs.

| Item | Verdict | Reason |
|------|---------|--------|
| `p9` | OK | Directly measures opinion on how cultural differences should be managed in society, core to the construct. |
| `p54_5` | FLAG | Measures actual friendship composition (behavioral outcome) rather than openness or acceptance toward religious diversity. |
| `p54_6` | FLAG | Measures actual friendship composition based on political views rather than tolerance or acceptance attitudes. |
| `p54_8` | FLAG | Measures actual friendship composition with homosexuals rather than acceptance or openness toward homosexuality. |
| `p68` | OK | Directly measures acceptance and support for rights of homosexual couples, core attitudinal component of tolerance. |
| `p73_1` | OK | Measures willingness to accept people of different religions in close proximity, reflecting openness to religious diversity. |

### `IDE|personal_optimism_efficacy`

**Verdict**: MIXED — Most items measure personal agency and optimism about the future, but p24 measures retrospective life satisfaction rather than forward-looking efficacy or control.

| Item | Verdict | Reason |
|------|---------|--------|
| `p19` | OK | Directly measures perceived ability to secure economic future, a core component of personal efficacy and optimism about life outcomes. |
| `p20` | OK | Directly measures confidence in achieving future goals and projects, a central element of personal agency and optimism. |
| `p24` | FLAG | Measures retrospective satisfaction with past life rather than forward-looking sense of control, efficacy, or optimism about future outcomes. |TODO test alphaotherwise drop
| `p30_1` | OK | Directly measures perceived control over a specific life domain (economic situation), a core indicator of personal agency. |

### `IDE|moral_normative_conservatism`

**Verdict**: MIXED — Most items measure moral conservatism on family and sexuality norms, but p57 measures political ideology which is conceptually distinct from moral normative conservatism.

| Item | Verdict | Reason |
|------|---------|--------|
| `p55` | OK | Directly measures conservative moral norm regarding corporal punishment of children, a core domain of the construct. |
| `p56` | OK | Directly measures self-identified conservatism in family and household moral matters, which is central to the construct. |
| `p57` | FLAG | Measures political ideology conservatism-liberalism, which is substantively distinct from moral normative conservatism on family, sexuality, and social conduct. |TODO test alpha
| `p58` | OK | Measures conservative moral norms regarding family autonomy and independence, relevant to traditional family structure values. |
| `p60` | OK | Directly measures conservative moral norms regarding premarital sexual conduct, explicitly mentioned in the construct description. |

### `MED|environmental_problem_salience`

**Verdict**: MIXED — Items p4 and p7 align well with the construct, but p6 measures problem prioritization rather than perceived severity or personal relevance.

| Item | Verdict | Reason |
|------|---------|--------|
| `p4` | OK | Directly measures perceived severity of environmental conditions at the macro (national) level, core to environmental problem salience. |
| `p6` | FLAG | Measures which environmental problem respondents rank as most important nationally, which is a prioritization judgment distinct from perceived severity or personal relevance of environmental problems. |
| `p7` | OK | Directly measures personal relevance by asking which environmental problem most affects the respondent and family at the micro (household) level. |

### `MED|environmental_knowledge_self_efficacy`

**Verdict**: MIXED — Most items measure self-assessed knowledge (self-efficacy), but p28_1 and p36_1 measure actual knowledge/recall rather than perceived competence.

| Item | Verdict | Reason |
|------|---------|--------|
| `p8` | OK | Directly measures self-assessed understanding of environmental problem causes on a 0-10 scale, aligned with construct definition. |
| `p9` | OK | Directly measures self-assessed understanding of environmental solutions on a 0-10 scale, aligned with construct definition. |
| `p28_1` | FLAG | Measures actual ability to recall/mention renewable energy sources, not perceived knowledge competence; this is objective knowledge, not self-efficacy. |
| `p29` | OK | Directly measures self-assessed knowledge level regarding renewable energy on a 0-10 scale, aligned with construct definition. |
| `p36_1` | FLAG | Measures actual knowledge of climate change causes through open-ended recall, not perceived competence; this is objective knowledge, not self-efficacy. |

### `MED|pro_environmental_civic_engagement`

**Verdict**: MIXED — Most items measure active civic/collective environmental actions, but p34_5 measures passive attendance at informational events rather than active engagement.

| Item | Verdict | Reason |
|------|---------|--------|
| `p34_1` | OK | Signing collective petitions is a direct form of active civic environmental engagement. |
| `p34_2` | OK | Donating to environmental groups is a direct form of active collective environmental engagement. |
| `p34_3` | OK | Participating in protests or demonstrations is a direct form of active civic environmental engagement. |
| `p34_4` | OK | Reporting environmental damage to authorities is a direct form of active civic environmental engagement. |
| `p34_5` | FLAG | Attending talks or conferences is passive information consumption rather than active civic or collective action in defense of the environment. |TODO test alpha

### `POB|intergenerational_mobility_perception`

**Verdict**: MIXED — Three items directly measure perceived intergenerational mobility, but p36 measures beliefs about structural barriers (education-employment link) rather than perceived mobility outcomes or opportunities.

| Item | Verdict | Reason |
|------|---------|--------|
| `p22` | OK | Directly measures perceived personal economic mobility relative to parents at comparable life stage. |
| `p23` | OK | Directly measures expected intergenerational mobility for next generation relative to respondent's current situation. |
| `p24` | OK | Directly measures perceived structural opportunities for youth upward mobility relative to parental generation. |
| `p36` | FLAG | Measures belief about the efficacy of education as a pathway to employment rather than perceived intergenerational mobility or structural opportunity. | TODO test alpha

### `POB|subjective_economic_wellbeing_and_agency`

**Verdict**: MIXED — Most items measure subjective economic wellbeing and agency as described, but p10 measures objective social class identification rather than subjective economic control or life satisfaction.

| Item | Verdict | Reason |
|------|---------|--------|
| `p13` | OK | Directly measures perceived resilience and personal strength in facing life adversities, a core component of subjective agency. |
| `p14` | OK | Directly measures perceived influence of national economic conditions on personal welfare, a key element of the construct. |
| `p15` | OK | Directly measures perceived personal agency and control over future economic outcomes. |
| `p16` | OK | Measures overall life satisfaction, which is explicitly included in the construct description as part of subjective economic wellbeing. |
| `p10` | FLAG | Measures objective social class self-identification rather than subjective economic control, resilience, or life satisfaction; it is a demographic proxy correlated with but semantically distinct from the construct. |

### `CUL|democratic_legitimacy_support`

**Verdict**: MIXED — Most items measure normative commitment to democracy and satisfaction with democratic functioning, but p30 measures conceptual understanding of democracy rather than valuation or trust in it.

| Item | Verdict | Reason |
|------|---------|--------|
| `p30` | FLAG | Measures which aspect respondents consider most important to democracy (conceptual knowledge/priorities) rather than their valuation, trust, or satisfaction with democratic governance. |
| `p31` | OK | Directly measures normative commitment to democracy as a preferred system of governance. |
| `p32` | OK | Measures evaluation of Mexico's actual democratic functioning, a core component of assessing democratic legitimacy. |
| `p35` | OK | Directly measures satisfaction with democracy in Mexico, a key indicator of democratic legitimacy support. |
| `p36` | OK | Measures normative beliefs about the relationship between democracy and human rights, reflecting commitment to democratic principles. |

### `CUL|institutional_trust_and_electoral_confidence`

**Verdict**: MIXED — Most items measure electoral integrity perceptions and institutional trust in electoral bodies, but p71 and p72 shift focus to vote-buying behavior—a substantively distinct electoral malpractice rather than trust in institutions or confidence in process integrity.

| Item | Verdict | Reason |
|------|---------|--------|
| `p41` | OK | Directly measures confidence in electoral process integrity (freedom and fairness), a core component of electoral confidence. |
| `p42` | OK | Directly measures trust in INE's ability to ensure clean elections, a key institutional trust component. |
| `p43` | OK | Measures confidence in electoral reliability under expanded INE jurisdiction, assessing trust in institutional capacity. |
| `p71` | FLAG | Measures perception of vote-buying prevalence, which is a specific electoral malpractice behavior rather than trust in institutions or confidence in process integrity. |
| `p72` | FLAG | Measures personal experience with vote-buying offers, a behavioral outcome and individual victimization measure rather than institutional trust or electoral confidence. |

### `CUL|political_efficacy_and_engagement`

**Verdict**: MIXED — Most items measure political interest, relevance, and efficacy as described, but p21 measures beliefs about political outcomes rather than personal efficacy or engagement, and p51 conflates satisfaction with participation opportunities with lack of interest.

| Item | Verdict | Reason |
|------|---------|--------|
| `p10` | OK | Directly measures subjective interest in politics, a core component of the construct. |
| `p11` | OK | Directly measures perceived relevance of politics to daily life, a core component of the construct. |
| `p20` | OK | Measures subjective comprehension/complexity of politics, a core component of the construct. |
| `p21` | FLAG | Measures beliefs about whether politics improves citizens' welfare, which is a political attitude/outcome evaluation distinct from personal efficacy, relevance, or engagement. |
| `p25` | OK | Measures perceived value of political participation, which relates to engagement and perceived relevance of politics. |
| `p46` | OK | Directly measures perceived ability to influence government decisions, a core component of political efficacy. |
| `p51` | FLAG | Conflates satisfaction with current participation opportunities with lack of interest; the response option 'no le interesa participar' measures disinterest rather than efficacy or engagement. |
| `p52` | OK | Measures satisfaction that one's opinions are heard by government, which reflects perceived influence and efficacy. |

### `CUL|authoritarian_predisposition`

**Verdict**: MIXED — Most items measure authoritarian predisposition coherently, but p60 measures democratic compliance behavior rather than authoritarian preference, and p23 measures pragmatic problem-solving rather than authoritarianism.

| Item | Verdict | Reason |
|------|---------|--------|
| `p17` | OK | Directly measures preference for security over freedom, a core component of authoritarian predisposition. |
| `p61` | OK | Directly measures preference for strong executive leadership over legal constraints, a central element of the construct. |
| `p64` | OK | Directly measures willingness to bypass legal rules to achieve justice, consistent with the construct's tolerance for rule-breaking. |
| `p65` | OK | Directly measures agreement that breaking the law can be justified for moral ends, a key aspect of authoritarian predisposition. |
| `p60` | FLAG | Measures compliance with majority decisions regardless of personal preference, which is democratic deference rather than authoritarian predisposition toward strong leadership or rule-breaking. |
| `p23` | FLAG | Measures pragmatic willingness to implement effective solutions despite conflict, which is a general problem-solving orientation distinct from authoritarian preference for strong leadership or subordinating freedoms to order. | TODO test alpha on both

### `REL|supernatural_beliefs`

**Verdict**: MIXED — Most items validly measure supernatural and religious beliefs, but p17_15 measures a naturalistic psychological/cognitive phenomenon rather than a supernatural entity or force.

| Item | Verdict | Reason |
|------|---------|--------|
| `p17_1` | OK | Directly measures belief in God, a core supernatural entity central to the construct. |
| `p17_2` | OK | Directly measures belief in afterlife, a fundamental supernatural/metaphysical belief. |
| `p17_4` | OK | Directly measures belief in hell, an orthodox Christian supernatural entity. |
| `p17_5` | OK | Directly measures belief in paradise, an orthodox Christian supernatural entity. |
| `p17_6` | OK | Directly measures belief in sin, a core religious/supernatural concept. |
| `p17_7` | OK | Directly measures belief in the soul, a fundamental supernatural entity. |
| `p17_8` | OK | Directly measures belief in resurrection of the dead, an orthodox Christian supernatural belief. |
| `p17_9` | OK | Directly measures belief in the devil, a core supernatural entity in Christian cosmology. |
| `p17_10` | OK | Directly measures belief in reincarnation, a syncretic/folk supernatural belief. |
| `p17_11` | OK | Directly measures belief in witchcraft, a folk supernatural belief explicitly mentioned in the construct description. |
| `p17_12` | OK | Directly measures belief in karma, a metaphysical supernatural belief explicitly mentioned in the construct description. |
| `p17_13` | OK | Directly measures belief in limpias, a folk/syncretic supernatural practice explicitly mentioned in the construct description. |
| `p17_14` | OK | Directly measures belief in destiny/fate, a metaphysical supernatural force. |
| `p17_15` | FLAG | Measures belief in the power of mind, a naturalistic psychological/cognitive phenomenon rather than a supernatural entity or metaphysical force. | TODO leave as is

### `REL|personal_religiosity`

**Verdict**: MIXED — Most items measure internalized religious practice and meaning-making, but one item measures a specific behavioral tendency that conflates religious practice with folk devotionalism in a way that may not reflect personal religiosity as defined.

| Item | Verdict | Reason |
|------|---------|--------|
| `p10` | OK | Directly measures prayer outside formal worship, a core indicator of personal religious practice. |
| `p12` | OK | Directly measures finding comfort and strength in religion, a key aspect of personal meaningfulness. |
| `p13_1` | OK | Directly measures using religious values to guide family behavior, explicitly mentioned in the construct description. |
| `p14` | OK | Directly measures reliance on clergy for life decisions, explicitly mentioned in the construct description. |
| `p25` | OK | Directly measures prayer, meditation, and contemplation practices, core indicators of personal religious practice. |
| `p11` | FLAG | Measures willingness to petition specific saints/religious figures, which is a folk devotional practice distinct from internalized personal religiosity and may reflect cultural tradition rather than personal religious commitment. | TODO leave as is

### `REL|church_state_separation`

**Verdict**: MIXED — Most items directly measure church-state separation attitudes, but p58 conflates a descriptive premise (media currently broadcasts religious content) with an attitudinal question, making it semantically distinct from the normative boundary-setting focus of other items.

| Item | Verdict | Reason |
|------|---------|--------|
| `p52_1` | OK | Directly measures attitudes toward clergy political speech in religious settings, a core church-state boundary issue. |
| `p55` | OK | Directly measures attitudes toward public resource allocation to religious events, a central church-state separation concern. |
| `p56` | OK | Directly measures attitudes toward institutional religious political participation through party formation, a key church-state boundary. |
| `p57` | OK | Directly measures attitudes toward tax treatment of religious institutions, reflecting their public-sphere status and secular governance principles. |
| `p58` | FLAG | Embeds a factual premise about current media practices before asking about agreement, conflating descriptive reality with normative attitudes about religious content in media, which is tangentially related to institutional church-state boundaries rather than directly measuring them. |

### `SEG|fear_and_risk_avoidance`

**Verdict**: MIXED — Most items measure fear of crime victimization and avoidance behaviors, but two items measure fear of wrongful arrest and perceived probability of unjust imprisonment, which are substantively distinct constructs.

| Item | Verdict | Reason |
|------|---------|--------|
| `p11_1` | OK | Directly measures subjective fear of a specific crime (street robbery with violence), which is core to the construct. |
| `p22_1` | OK | Directly measures avoidance of places due to crime fear, a key behavioral manifestation of the construct. |
| `p23_1` | OK | Directly measures cessation of activities (going out at night) to reduce crime victimization risk, a core construct element. |
| `p48` | FLAG | Measures fear of wrongful arrest by authorities, which is distinct from fear of crime victimization and not part of the described construct domain. |
| `p49` | FLAG | Measures perceived probability of unjust imprisonment in the criminal justice system, which concerns institutional injustice rather than crime victimization fear or avoidance. |

### `SEG|punitive_and_vigilante_attitudes`

**Verdict**: MIXED — Four items directly measure punitive and vigilante attitudes, but p72 measures approval of specific government anti-drug actions rather than endorsement of coercive or extralegal response principles.

| Item | Verdict | Reason |
|------|---------|--------|
| `p66` | OK | Directly measures endorsement of using violence to combat violence, a core component of the construct. |
| `p67` | OK | Directly measures preference for security over liberty, explicitly mentioned in the construct description. |
| `p68` | OK | Directly measures endorsement of community self-justice when authorities fail, a core vigilante attitude component. |
| `p71` | OK | Directly measures support for capital punishment, explicitly mentioned in the construct description. |
| `p72` | FLAG | Measures approval of specific government anti-drug policy implementation rather than endorsement of punitive/vigilante response principles, conflating policy evaluation with attitudinal construct. |

### `SAL|subjective_wellbeing`

**Verdict**: MIXED — Most items validly measure subjective wellbeing dimensions, but one item measures emotional state rather than self-assessed quality of life or satisfaction.

| Item | Verdict | Reason |
|------|---------|--------|
| `p37` | OK | Directly measures self-assessed quality of life, a core evaluative dimension of subjective wellbeing. |
| `p38` | OK | Directly measures life satisfaction, a central evaluative component of subjective wellbeing. |
| `p39` | OK | Directly measures enjoyment of life, an affective dimension of subjective wellbeing explicitly mentioned in the construct description. |
| `p40` | OK | Directly measures sexual satisfaction, explicitly included in the construct description as part of subjective wellbeing. |
| `p8_1` | FLAG | Measures momentary emotional state (feeling calm and tranquil) rather than self-assessed quality of life, life satisfaction, or enjoyment—a transient affective experience distinct from the evaluative wellbeing construct. |

### `SAL|health_risk_behaviors`

**Verdict**: MIXED — Items p34 and p35 directly measure alcohol consumption frequency and intensity as described, but p28 measures only lifetime smoking history without capturing current smoking intensity or frequency.

| Item | Verdict | Reason |
|------|---------|--------|
| `p28` | FLAG | Measures lifetime smoking history (yes/no) but does not capture current smoking status, intensity, or frequency as required by the construct description; a behavioral outcome indicator rather than engagement in the behavior. | TODO leave as is
| `p34` | OK | Directly measures frequency of alcohol consumption in the past 12 months, which aligns with the construct's focus on frequency and intensity of alcohol consumption. |
| `p35` | OK | Directly measures intensity of alcohol consumption (maximum drinks per occasion in past 12 months), which aligns with the construct's focus on intensity of alcohol consumption. |

### `IND|perceived_indigenous_discrimination`

**Verdict**: MIXED — Most items directly measure perceived discrimination against indigenous people, but p20 measures general skin color discrimination without indigenous-specific focus, making it tangentially related rather than directly on-target.

| Item | Verdict | Reason |
|------|---------|--------|
| `p20` | FLAG | Measures perception of skin color discrimination in general society rather than discrimination specifically against indigenous people; conflates racial/colorism discrimination with indigenous-specific discrimination. | TODO leave as is
| `p21` | OK | Directly measures recognition of racism in Mexico, which is foundational to perceiving systemic discrimination against indigenous populations. |
| `p25_1` | OK | Directly assesses whether employment discrimination against indigenous people is recognized as discriminatory, measuring attitudinal recognition of indigenous-specific discrimination. |
| `p34_1` | OK | Directly measures perception that indigenous identity creates systemic barriers to employment, capturing assessment of structural inequality affecting indigenous people. |

### `IND|social_distance_toward_indigenous_people`

**Verdict**: MIXED — Two items measure willingness/acceptance (on-target), but one item measures past behavior/experience rather than willingness or social distance.

| Item | Verdict | Reason |
|------|---------|--------|
| `p37_1` | OK | Directly measures willingness to engage in a professional/domestic relationship (hiring for childcare), reflecting behavioral acceptance and social distance. |
| `p39_1` | FLAG | Measures past friendship experience rather than willingness or social distance; a behavioral outcome that may correlate with but is semantically distinct from the construct of social distance attitudes. |
| `p40_1` | OK | Directly measures willingness to allow indigenous people into one's home, a core indicator of residential social distance and acceptance. |

### `SOC|media_trust_and_quality_evaluation`

**Verdict**: MIXED — Most items measure critical assessment of media quality and coverage, but p53_1 measures trust in family information sources, which is semantically distinct from evaluating media institutions.

| Item | Verdict | Reason |
|------|---------|--------|
| `p54` | OK | Directly measures perceived quality of Mexican media content, a core component of media quality evaluation. |
| `p55` | OK | Assesses satisfaction with how public affairs are covered in media, directly aligned with the construct's coverage evaluation domain. |
| `p66` | OK | Measures perceived difficulty in obtaining reliable information from media, reflecting critical assessment of information completeness and trustworthiness. |
| `p69_1` | OK | Directly evaluates perceived completeness and clarity of media information, core to assessing media quality and accuracy. |
| `p67` | OK | Assesses sufficiency of media options available, a legitimate dimension of media system quality evaluation. |
| `p53_1` | FLAG | Measures trust in family as an information source, which is substantively distinct from critical assessment of Mexican media institutions. |

### `SOC|perceived_media_social_impact`

**Verdict**: MIXED — Most items measure perceived societal consequences of media content, but p63_1 measures parental behavior/responsibility rather than beliefs about media's societal impact.

| Item | Verdict | Reason |
|------|---------|--------|
| `p60` | OK | Directly measures perceived change in media violence over time, a core aspect of media's societal consequences. |
| `p61` | OK | Measures belief about how media violence portrayal relates to reality, assessing perceived accuracy and societal impact of media representation. |
| `p62_1` | OK | Directly measures perceived representation of women in media, explicitly mentioned in construct description. |
| `p59_1` | OK | Directly measures perceived influence of media on family relationships, explicitly mentioned in construct description. |
| `p63_1` | FLAG | Measures parental supervisory responsibility and behavior rather than beliefs about media's societal consequences or impact. |
| `p76` | OK | Measures perceived necessity of regulatory oversight, explicitly mentioned in construct description. |
| `p77_1` | OK | Measures beliefs about government intervention in media regulation, aligned with perceived necessity of regulatory oversight. |

### `ENV|ageism_and_negative_stereotypes`

**Verdict**: MIXED — Three items directly measure ageist stereotypes and discriminatory attitudes, but one item measures perceived labor market conditions rather than personal stereotyping or discriminatory beliefs.

| Item | Verdict | Reason |
|------|---------|--------|
| `p13_1` | OK | Directly measures a negative stereotype about older adults' health status, a core component of ageist attitudes. |
| `p14_1` | OK | Directly measures a negative stereotype about older adults' disengagement and loss of interest, explicitly mentioned in the construct description. |
| `p26` | OK | Directly measures justification for age-based employment discrimination, explicitly mentioned in the construct description. |
| `p27` | FLAG | Measures perceived labor market opportunities for older adults rather than personal ageist stereotypes or discriminatory attitudes, conflating a descriptive belief about structural conditions with normative stereotyping. |

### `ENV|state_and_family_responsibility_for_elder_care`

**Verdict**: MIXED — The construct mixes normative beliefs about responsibility allocation with behavioral outcomes and descriptive observations, creating semantic heterogeneity.

| Item | Verdict | Reason |
|------|---------|--------|
| `p42_1` | OK | Directly measures normative belief about state responsibility for elder care, core to the construct. |
| `p44` | FLAG | Measures willingness to contribute financially (behavioral intention/outcome) rather than normative beliefs about who should bear responsibility. |
| `p30` | FLAG | Measures perceived willingness of children to care for parents (descriptive observation of actual behavior/attitudes) rather than respondent's normative beliefs about responsibility allocation. |
| `p31` | FLAG | Measures perceived change in actual caregiving frequency over time (behavioral trend observation) rather than normative beliefs about responsibility. | TODO  drop only 31

### `DER|institutional_trust_justice`

**Verdict**: MIXED — Most items measure trust and perceived legitimacy of justice institutions, but p19 shifts focus to victim treatment quality, which is a distinct outcome rather than institutional trust.

| Item | Verdict | Reason |
|------|---------|--------|
| `p18` | OK | Directly measures perceived effectiveness of prosecutor offices in fulfilling their core justice function, a key component of institutional trust. |
| `p19` | FLAG | Measures quality of victim treatment rather than trust in or legitimacy of the institution itself; this is a service outcome distinct from institutional confidence. |
| `p20` | OK | Directly measures confidence and trust in judges, the core construct of institutional trust. |
| `p21` | OK | Measures perceived legitimacy and effectiveness of the Supreme Court in upholding human rights, consistent with the construct definition. |
| `p34` | OK | Directly measures perceived effectiveness of human rights commissions in defending rights, consistent with institutional trust in formal justice institutions. |

### `DER|perceived_discrimination_social_exclusion`

**Verdict**: MIXED — Most items measure perceived discrimination and attitudes toward vulnerable groups, but two items measure personal discriminatory intentions rather than perceptions of discrimination or social exclusion.

| Item | Verdict | Reason |
|------|---------|--------|
| `p35_1` | OK | Directly measures personal experience of rights violations based on physical appearance, core to the construct. |
| `p36_1` | FLAG | Measures respondent's own discriminatory behavior/intentions (whether they would discriminate in housing) rather than perception of discrimination or attitudes toward discrimination against others. |
| `p39` | OK | Measures perception of how dark-skinned people are treated in society, directly assessing perceived discrimination against a vulnerable group. |
| `p40_1` | FLAG | Measures respondent's personal tolerance of their child's homosexuality rather than perception of discrimination or attiTOudes toward societal discrimination against LGBTQ+ individuals. |TODO leave as is
| `p41` | OK | Measures attitudes toward penalizing public expression of homosexuality, reflecting perception of and stance on discrimination against LGBTQ+ individuals. |
| `p44` | OK | Measures attitudes toward discriminatory exclusion from public spaces based on appearance, assessing normative judgments about discrimination. |

### `DER|rights_awareness_personal_experience`

**Verdict**: MIXED — The construct targets personal experience with human rights and labor rights violations, but includes school bullying which is a distinct harm domain outside the rights violation framework.

| Item | Verdict | Reason |
|------|---------|--------|
| `p45` | OK | Directly measures personal experience with human rights violations, core to the construct's lived dimension. |
| `p53` | FLAG | School bullying is a peer-to-peer harm distinct from human rights or labor rights violations and does not measure rights abuses by authority or institutional actors. |tTODO leave as is
| `p54` | OK | Directly measures personal experience with labor rights abuse (workplace mobbing), aligned with the construct's focus on lived rights violations. |

### `HAB|basic_services_access`

**Verdict**: MIXED — Most items directly measure basic service availability, but p8 conflates sanitation facility type with drainage access, and p36_30 is redundant with p10.

| Item | Verdict | Reason |
|------|---------|--------|
| `p7` | OK | Directly measures water supply frequency, a core component of basic services access. |
| `p7_1` | OK | Directly measures water delivery adequacy (continuous vs. intermittent), complementing p7 to assess water service quality. |
| `p8` | FLAG | Measures sanitation facility type rather than drainage infrastructure or public utility connection, conflating household sanitation with basic services access. |
| `p10` | OK | Directly measures drainage/sewage disposal method and connection to public networks, a core component of basic services access. |
| `p11` | OK | Directly measures electricity availability, a core component of basic services access. |
| `p36_30` | FLAG | Redundant binary measure of drainage presence that duplicates p10's more detailed assessment of drainage infrastructure and connection type. |

### `GLO|economic_globalization_attitudes`

**Verdict**: MIXED — Most items measure attitudes toward economic globalization and trade, but p49_1 shifts focus to a specific sectoral foreign investment policy question that may reflect regulatory/nationalist concerns distinct from general trade attitudes.

| Item | Verdict | Reason |
|------|---------|--------|
| `p46_1` | OK | Directly measures evaluation of free trade agreements' impact on Mexican economy, core to economic globalization attitudes. |
| `p47` | OK | Directly measures perspective on whether foreign trade benefits the Mexican economy, central to economic globalization attitudes. |
| `p48` | OK | Directly measures agreement with free trade agreements, a key component of economic globalization attitudes. |
| `p49_1` | FLAG | Measures approval of foreign investment in a specific strategic sector (telecommunications) rather than general attitudes toward foreign investment or economic globalization, conflating sectoral protectionism with broader trade orientation. |
| `p31_1` | OK | Directly measures evaluation of bilateral trade relationship with the US, explicitly mentioned in construct description as part of economic globalization attitudes. |

### `GLO|international_institutional_engagement`

**Verdict**: MIXED — Most items measure support for international institutional engagement, but p58 measures behavioral intention/willingness to use institutions rather than support for institutional authority.

| Item | Verdict | Reason |
|------|---------|--------|
| `p52_1` | OK | Directly measures support for Mexico's involvement with the international community on a global issue. |
| `p54_1` | OK | Measures preference for UN authority over national governments on international peace, core to institutional deference. |
| `p57` | OK | Measures support for UN's active role in human rights promotion, directly assessing institutional authority. |
| `p58` | FLAG | Measures personal behavioral intention to use international institutions rather than support for institutional engagement or authority. |
| `p60_1` | OK | Measures support for UN authority to use military force, directly assessing deference to international institutional power. |
| `p63_1` | OK | Measures support for Mexico's collaborative engagement with other countries on a multilateral issue. |

### `JUS|judicial_institutional_trust`

**Verdict**: MIXED — Most items validly measure judicial institutional trust, but p43 measures normative preferences about judicial philosophy rather than perceived legitimacy or trustworthiness of institutions.

| Item | Verdict | Reason |
|------|---------|--------|
| `p22` | OK | Directly assesses perceived functional effectiveness of the justice system, a core component of institutional trust. |
| `p41` | OK | Measures perceived judicial independence, a key dimension of institutional legitimacy and impartiality. |
| `p42_1` | OK | Assesses belief that judges guarantee fair trials, directly measuring perceived fairness and trustworthiness. |
| `p46` | OK | Measures perceived justice of Supreme Court decisions, capturing trust in judicial fairness and legitimacy. |
| `p33` | OK | Assesses perceived equal treatment and impartiality in courts, a fundamental aspect of institutional fairness. |
| `p50` | OK | Measures perceived accountability of judges, reflecting trust in institutional oversight and legitimacy. |
| `p43` | FLAG | Measures respondent's normative preference between justice and legal adherence rather than perceived trustworthiness or legitimacy of judicial institutions. |

### `JUS|law_compliance_motivation`

**Verdict**: MIXED — Items p7 directly measures motivational basis for compliance, but p8, p9, and p10 measure perceived or self-assessed law-abidingness rather than the underlying reasons for compliance.

| Item | Verdict | Reason |
|------|---------|--------|
| `p7` | OK | Directly captures normative and instrumental motivations for obeying laws, which is the core of the construct. |
| `p8` | FLAG | Measures perceived respect for laws by government officials, which is a behavioral outcome or perception of compliance rather than the motivational basis underlying compliance. |
| `p9` | FLAG | Measures perceived respect for laws by citizens, which is a perception of compliance behavior rather than the motivational reasons for compliance. |
| `p10` | FLAG | Measures self-assessed law-abidingness rather than the underlying normative or instrumental motivations that drivTODO leave as ise compliance behavior. |TODO. leave as is

### `MIG|perceived_opportunity_structure`

**Verdict**: MIXED — Most items validly measure perceived opportunity structure in Mexico, but p3_9 measures perceived opportunity to leave Mexico rather than opportunities within Mexico's structural context.

| Item | Verdict | Reason |
|------|---------|--------|
| `p3_1` | OK | Directly measures perceived access to educational opportunities, a core economic/social domain of opportunity structure. |
| `p3_2` | OK | Directly measures perceived access to employment opportunities, a fundamental component of economic opportunity structure. |
| `p3_3` | OK | Directly measures perceived access to entrepreneurial opportunities, a key economic domain of opportunity structure. |
| `p3_4` | OK | Directly measures perceived access to financial resources/credit, an important structural enabler of economic mobility. |
| `p3_9` | FLAG | Measures perceived opportunity to emigrate rather than perceived opportunities within Mexico's opportunity structure, representing a distinct construct of international mobility rather than domestic structural access. |

### `MIG|attitudes_toward_foreigners_in_mexico`

**Verdict**: MIXED — Most items measure attitudes toward foreigners, but p44 is a behavioral/demographic item measuring actual contact rather than evaluative orientation.

| Item | Verdict | Reason |
|------|---------|--------|
| `p42` | OK | Directly measures general evaluative opinion toward foreigners in Mexico. |
| `p43_1` | OK | Measures perceived economic contribution, an explicit component of the construct domain. |
| `p44` | FLAG | Measures actual behavioral contact/cohabitation with foreigners rather than evaluative attitudes or opinions about them. |
| `p45` | OK | Measures views on appropriate number of foreigners, an explicit component of the construct domain. |
| `p47` | OK | Measures perceived respect for foreigners' rights, relevant to attitudes about their treatment and entitlements. |
| `p48` | OK | Measures beliefs about rights entitlements for foreigners, an explicit component of the construct domain. |
| `p51` | OK | Measures perceived discrimination against foreigners, an explicit component of the construct domain. |
| `p52` | OK | Measures perceived differential treatment based on origin, relevant to attitudes about discrimination and fairness toward foreigners. |

### `FED|perceived_representativeness`

**Verdict**: MIXED — Item p12_1 measures party representativeness rather than elected officials' representativeness, introducing a conceptually distinct element into a scale otherwise focused on multi-level political representation.

| Item | Verdict | Reason |
|------|---------|--------|
| `p12_1` | FLAG | Measures political parties' representativeness rather than elected officials' representativeness; parties are organizational entities distinct from the elected representatives (deputies, governors, presidents) that comprise the rest of the scale. | TODO. leave as is
| `p12_2` | OK | Directly measures perceived representativeness of local deputies, consistent with the multi-level assessment of elected officials. |
| `p12_3` | OK | Directly measures perceived representativeness of federal deputies, consistent with the multi-level assessment of elected officials. |
| `p12_4` | OK | Directly measures perceived representativeness of state governors, consistent with the multi-level assessment of elected officials. |
| `p12_5` | OK | Directly measures perceived representativeness of the national president, consistent with the multi-level assessment of elected officials. |
| `p12_6` | OK | Directly measures perceived representativeness of municipal presidents, consistent with the multi-level assessment of elected officials. |

### `FED|fiscal_and_service_federalism_preferences`

**Verdict**: MIXED — Most items validly measure federalism preferences regarding distribution of responsibilities and resources, but p37_1 measures satisfaction with service delivery rather than preferences about how governance should be structured.

| Item | Verdict | Reason |
|------|---------|--------|
| `p31_1` | OK | Measures attribution of responsibility for a public service across government levels, relevant to understanding federalism preferences. |
| `p32_1` | OK | Directly measures preference for which government level should manage a specific service, core to fiscal and service federalism. |
| `p33` | OK | Measures general preference for which government level should address local problems, directly relevant to decentralization attitudes. |
| `p34_1` | OK | Measures preference for which government level should manage education services, a key domain of federalism preferences. |
| `p36` | OK | Directly measures preferences about fiscal distribution and resource allocation across government levels, core to fiscal federalism. |
| `p37_1` | FLAG | Measures satisfaction with municipal service delivery relative to taxes paid, which is an outcome evaluation rather than a preference about how governance should be structured. |
| `p38` | OK | Measures preference for how tax revenue should be distributed geographically, directly relevant to fiscal federalism preferences. |
| `p60` | OK | Measures preference for centralization versus decentralization of decision-making authority, core to federalism preferences. |

### `FED|security_governance_preferences`

**Verdict**: MIXED — Most items measure preferences and evaluations of security governance levels, but p47 measures performance satisfaction rather than governance preferences or coordination assessments.

| Item | Verdict | Reason |
|------|---------|--------|
| `p45` | OK | Directly measures evaluation of intergovernmental coordination between federal and state governments in security matters, a core component of security governance. |
| `p46` | OK | Measures preference regarding police organizational structure and command authority, which is a substantive aspect of security governance preferences. |
| `p47` | FLAG | Measures satisfaction with state government performance in security rather than preferences about which level should be responsible or how governance should be organized. |
| `p48` | OK | Measures preference for which government level should assume emergency security response authority, directly addressing governance responsibility allocation. |
| `p49` | OK | Directly measures preference regarding which government level should hold primary responsibility for public security, the core construct domain. |

### `GEN|traditional_gender_role_attitudes`

**Verdict**: MIXED — Most items measure traditional gender role attitudes, but two items measure gender stereotypes and ideological equivalence rather than endorsement of traditional role norms.

| Item | Verdict | Reason |
|------|---------|--------|
| `p11_1` | OK | Directly measures endorsement of male economic dominance, a core component of traditional gender role attitudes. |
| `p26_1` | OK | Directly measures belief that household labor is women's responsibility, a central traditional gender role norm. |
| `p61_1` | FLAG | Measures a gender stereotype about male sexual behavior rather than endorsement of traditional role divisions in domestic, economic, or social life. |
| `p63_1` | FLAG | Measures a negative gender stereotype about female emotional manipulation rather than endorsement of traditional gender role norms. |
| `p59_1` | FLAG | Measures ideological equivalence between feminism and machismo rather than direct endorsement of traditional gender roles. |

### `DEP|cultural_socialization_in_childhood`

**Verdict**: MIXED — Two items measure parental cultural socialization behavior, but one item measures the child's own reading behavior, which is an outcome rather than exposure to parental cultural transmission.

| Item | Verdict | Reason |
|------|---------|--------|
| `p8` | OK | Directly measures parental communication about cultural topics during childhood, a core mechanism of cultural socialization. |
| `p11` | OK | Directly measures parental/familial behavior of gifting books, a concrete cultural resource transmission practice. |
| `p12_1` | FLAG | Measures the child's own reading frequency, which is a behavioral outcome of socialization rather than exposure to parental cultural practices or resources. |TODO LEAVE AS IS

### `DEP|reading_engagement_and_literacy`

**Verdict**: MIXED — Items measure only one narrow subdomain (reading habits for newspapers/magazines) and omit key construct elements like access to books, reading ability, and barriers to reading.
<!-- NOTE: MIXED verdict reflects narrow construct coverage given available items (only acostumbra newspaper/magazine items), not off-target items. No items flagged for removal — construct is what the survey allows. -->
| Item | Verdict | Reason |
|------|---------|--------|
| `p15a_1` | OK | Directly measures self-reported reading habits for a specific publication type, which is a core component of reading engagement. |
| `p15a_2` | OK | Directly measures self-reported reading habits for a specific publication type, which is a core component of reading engagement. |
| `p15a_3` | OK | Directly measures self-reported reading habits for a specific publication type, which is a core component of reading engagement. |

### `DEP|cultural_identity_and_heritage`

**Verdict**: MIXED — Most items validly measure cultural identity and heritage self-identification, but two items measuring indigenous language ability are tangentially related behavioral competencies rather than direct measures of cultural belonging or self-identification.

| Item | Verdict | Reason |
|------|---------|--------|
| `p48` | OK | Directly measures first language acquisition, a core component of cultural heritage and identity formation. |
| `p49` | OK | Directly assesses self-perceived cultural distinctiveness and heritage recognition relative to the majority population. |
| `p50` | OK | Directly measures self-identification as part of a discriminated ethnic/racial group, explicitly mentioned in the construct description. |
| `p54` | OK | Directly measures ethnic/racial self-categorization and self-perception, a core component of cultural identity. |
| `p34` | FLAG | Measures behavioral language competency (ability to converse) rather than cultural identity or belonging; someone may identify culturally with indigenous heritage without conversational ability. |
| `p35` | FLAG | Measures literacy skill in indigenous languages rather than cultural identity or self-identification; literacy is a behavioral outcome distinct from cultural belonging. |TODO leave as is

### `DEP|attitudes_toward_cultural_openness_and_foreign_influence`

**Verdict**: MIXED — Most items measure attitudes toward cultural openness and pluralism, but p29_1 measures behavioral preference for cultural preservation rather than attitudes toward openness/foreign influence.

| Item | Verdict | Reason |
|------|---------|--------|
| `p25` | OK | Directly measures preference for cultural homogeneity (singular culture) versus pluralism (multiple cultures), core to the construct. |
| `p26` | OK | Measures perception of foreign cultural influence magnitude, directly relevant to attitudes toward external cultural impact. |
| `p27` | OK | Measures evaluative orientation toward foreign cultural influence (harmful vs. beneficial), central to the construct domain. |
| `p28` | OK | Directly measures preference for cultural homogeneity versus diversity as a normative position for the country. |
| `p29_1` | FLAG | Measures which cultural elements respondents prioritize for preservation rather than attitudes toward openness to foreign influence or cultural pluralism. |
| `p31_1` | OK | Measures perceived importance of teachers' exposure to foreign cultures, reflecting openness to external cultural knowledge in education. |
| `p32` | OK | Measures support for multicultural education through indigenous language inclusion, consistent with openness to cultural pluralism in schools. |

### `ECO|labor_union_attitudes`

**Verdict**: MIXED — Two items directly measure union attitudes, but one item measures perceived labor rights respect, which is a contextual outcome rather than an evaluative orientation toward unions themselves.

| Item | Verdict | Reason |
|------|---------|--------|
| `p23` | OK | Directly measures perceived necessity of unions, a core normative orientation toward collective labor representation. |
| `p24` | OK | Directly measures evaluative orientations toward unions' role and legitimacy across multiple dimensions (rights protection, corruption, efficiency, governance). |
| `p22` | FLAG | Measures perceived respect for worker rights in Mexico, which is a contextual outcome or labor market condition rather than a direct evaluative orientation toward unions as institutions. |

### `NIN|perceived_situation_of_children_and_youth`

**Verdict**: MIXED — Two items measure general situation perception across age groups, but one item narrows focus specifically to economic situation, introducing a substantive domain distinction.

| Item | Verdict | Reason |
|------|---------|--------|
| `p5` | OK | Directly measures perceived change in general situation of children, aligned with construct definition. |
| `p31` | OK | Directly measures perceived change in general situation of adolescents, aligned with construct definition. |
| `p61` | FLAG | Narrows focus to economic situation specifically rather than general situation, measuring a distinct subdomain that may not be semantically equivalent to the broader evaluative orientation described. |

### `NIN|youth_participation_and_voice`

**Verdict**: MIXED — Most items directly measure normative attitudes toward youth voice and participation, but p41 and p47 shift focus to conditional participation scenarios and rights frameworks rather than attitudes about whether youth opinions should be heard.

| Item | Verdict | Reason |
|------|---------|--------|
| `p12` | OK | Directly measures normative belief about whether children's opinions should be considered in family decisions. |
| `p13` | OK | Directly measures normative belief about whether children's opinions should be considered in school decisions. |
| `p38` | OK | Directly measures normative belief about whether adolescents' opinions should be considered in family decisions. |
| `p39` | OK | Directly measures normative belief about whether adolescents' opinions should be considered in school decisions. |
| `p41` | FLAG | Measures conditional circumstances under which adolescents should participate in public mobilization rather than normative attitudes about whether their voice should be heard in decisions. |
| `p47` | FLAG | Measures beliefs about the source and legitimacy of adolescent rights rather than attitudes about whether youth opinions should be considered in decisions affecting them. |

### `FAM|family_cohesion_quality`

**Verdict**: MIXED — Items p25 and p26 directly measure perceived relationship quality, but p27, p52, and p53 measure beliefs about what determines or sustains family cohesion rather than the respondent's actual perception of their own family's cohesion quality.

| Item | Verdict | Reason |
|------|---------|--------|
| `p25` | OK | Directly measures perceived quality of relationships with co-resident family members, core to family cohesion quality. |
| `p26` | OK | Directly measures perceived quality of relationships with non-resident family members, aligning with construct's inclusion of both co-resident and non-resident bonds. |
| `p27` | FLAG | Measures respondent's beliefs about what determines good/bad family relations in general, not their perception of their own family's cohesion quality. |
| `p52` | FLAG | Measures respondent's beliefs about what keeps families united in general, not their perception of their own family's actual cohesion or unity. |
| `p53` | FLAG | Measures family values held by the respondent rather than perceived quality of family relationships or sense of unity. |

### `FAM|ideal_family_normativity`

**Verdict**: MIXED — Items p13-p16 directly measure normative beliefs about ideal family structure and ideology, but p67-p68 measure descriptive observations about family change rather than normative beliefs about what should be ideal.

| Item | Verdict | Reason |
|------|---------|--------|
| `p13` | OK | Directly asks respondents to identify their conception of an ideal family structure, core to measuring family normativity. |
| `p14` | OK | Asks about barriers to achieving the ideal family type, which reflects normative ideology about what prevents family ideals. |
| `p15` | OK | Asks what actions could enable achievement of ideal family, reflecting normative beliefs about solutions and values. |
| `p16` | OK | Directly measures acceptance or rejection of non-traditional family arrangements, capturing traditionalism versus pluralism in family ideology. |
| `p67` | FLAG | Measures descriptive observations about actual family changes across generations rather than normative beliefs about what constitutes an ideal family. |
| `p68` | FLAG | Measures predictions about future family trends rather than normative beliefs about what family structure should ideally be. |

### `FAM|intergenerational_obligations`

**Verdict**: MIXED — Items p28-p29 and p64 measure normative beliefs about intergenerational obligations, while p62-p63 measure behavioral/actual coping strategies and current care arrangements, which are outcomes rather than attitudinal beliefs about obligations.

| Item | Verdict | Reason |
|------|---------|--------|
| `p28` | OK | Directly measures parental obligations toward children, a core component of intergenerational duty beliefs. |
| `p29` | OK | Directly measures filial obligations toward parents, including elder care responsibility, a core component of the construct. |
| `p62` | FLAG | Measures actual behavioral strategies and preparations for old age rather than beliefs about intergenerational obligations; conflates personal coping mechanisms with familial duty attitudes. |
| `p63` | FLAG | Measures current or anticipated actual care arrangements and who will provide care, not beliefs about obligations; describes behavioral reality rather than normative attitudes toward intergenerational duty. |
| `p64` | OK | Measures willingness to assume caregiving responsibility for family members, which reflects beliefs about filial and familial obligations toward dependent relatives. |

### `FAM|conjugal_union_attitudes`

**Verdict**: MIXED — Most items measure attitudes toward conjugal unions, but p33 is a behavioral disclosure item that measures past conduct rather than attitudes or normative orientations.

| Item | Verdict | Reason |
|------|---------|--------|
| `p21` | OK | Directly measures criteria and motivations for selecting a conjugal partner, core to attitudes about forming unions. |
| `p22` | OK | Measures family influence on partner selection, relevant to normative orientations toward conjugal union formation. |
| `p23` | OK | Measures personal motivations for initiating a conjugal union, directly aligned with attitudes about forming partnerships. |
| `p32` | OK | Measures perceived causes of extramarital relations, relevant to attitudes about conjugal union stability and maintenance. |
| `p33` | FLAG | Measures actual past behavior (whether respondent has had affairs) rather than attitudes, normative orientations, or tolerance toward infidelity. |
| `p35` | OK | Measures tolerance and conditions for accepting infidelity, directly relevant to attitudes about conjugal union stability and normative orientations. |
| `p38` | OK | Measures perceived causes of divorce, directly aligned with attitudes about conjugal union dissolution and stability. |

### `FAM|family_value_transmission`

**Verdict**: MIXED — Two items directly measure family value transmission, but one item measures religious influence on family life, which is a contextual factor rather than the values themselves.

| Item | Verdict | Reason |
|------|---------|--------|
| `p54` | OK | Directly measures values learned from family of origin and practiced daily, core to the construct. |
| `p55` | OK | Directly measures fundamental values parents should transmit to children, core to the construct. |
| `p57` | FLAG | Measures the influence of religion on family life rather than the values themselves or their transmission—a contextual factor distinct from the construct domain. |

### `CIE|science_technology_interest_engagement`

**Verdict**: MIXED — Most items validly measure science and technology interest and engagement, but three items (p38_4, p38_5, p38_6) measure interest in specific science policy/environmental topics rather than general science-technology interest or media consumption behavior.

| Item | Verdict | Reason |
|------|---------|--------|
| `p11` | OK | Directly measures expressed interest in science, a core component of the construct. |
| `p22` | OK | Directly measures expressed interest in technology, a core component of the construct. |
| `p23` | OK | Measures frequency of media consumption about technology, explicitly included in the construct description. |
| `p35` | OK | Measures desire to participate in science-related activities, a core engagement component of the construct. |
| `p43` | OK | Measures desire to participate in technology-related activities, a core engagement component of the construct. |
| `p38_4` | FLAG | Measures interest in a specific environmental policy topic (climate change) rather than general science-technology interest or engagement. |
| `p38_5` | FLAG | Measures interest in a specific environmental policy topic (renewable energy) rather than general science-technology interest or engagement. |
| `p38_6` | FLAG | Measures interest in a specific controversial science policy topic (transgenic crops) rather than general science-technology interest or engagement. |

### `CIE|institutional_trust_in_science`

**Verdict**: MIXED — Most items measure institutional trust and perceived integrity of scientists, but p49_1 measures a normative belief about what universities should do rather than trust in or perception of scientific institutions.

| Item | Verdict | Reason |
|------|---------|--------|
| `p32_1` | OK | Directly measures perceived utility and societal value of scientific research, which reflects trust in scientists' commitment to producing socially relevant work. |
| `p33` | OK | Directly measures perceived commitment of Mexican scientists to society, a core component of institutional trust as described. |
| `p40_1` | OK | Measures skepticism about scientists' motivations (political interests), which is explicitly mentioned in the construct description as part of institutional trust assessment. |
| `p50_1` | OK | Directly measures confidence in research conducted within a specific discipline (Medicine), which reflects trust in scientific institutions and their work. |
| `p49_1` | FLAG | Measures a normative belief about what universities should prioritize rather than respondents' actual trust in or perception of scientific institutions' integrity or commitment. |

### `CIE|perceived_societal_value_of_science_technology`

**Verdict**: MIXED — Most items measure perceived societal value of science/technology, but two items measure evaluations of institutional efficiency and policy preferences rather than beliefs about practical contribution and importance.

| Item | Verdict | Reason |
|------|---------|--------|
| `p34` | OK | Directly measures perceived contribution of Mexican science to solving national problems, core to the construct. |
| `p36` | OK | Measures perceived importance of scientific knowledge, a key component of societal value beliefs. |
| `p44_1` | OK | Measures perceived importance of technology for learning, relevant to practical utility and value of technology. |
| `p57` | FLAG | Measures perceived efficiency of technology utilization in Mexico, which is an evaluation of institutional performance rather than beliefs about science/technology's societal value or importance. |
| `p58` | FLAG | Measures perceived government support for technology development, which is a policy/resource allocation assessment distinct from beliefs about science/technology's practical contribution to solving social problems. |
| `p42_1` | OK | Measures perceived quality of science education, which relates to the construct's inclusion of science education quality as a component of societal value. |
| `p39_1` | OK | Measures agreement that science education is indispensable, reflecting beliefs about the importance and value of science in society. |
| `p51_1` | FLAG | Measures agreement with a technology import policy position, which is a normative policy preference rather than a belief about science/technology's practical contribution or importance to Mexico. |

### `CIE|household_science_cultural_capital`

**Verdict**: MIXED — Most items validly measure scientific and educational cultural capital through books and digital infrastructure, but one item measures educational resources that are functional/curricular rather than cultural capital.

| Item | Verdict | Reason |
|------|---------|--------|
| `p3_2` | OK | Directly measures presence of scientific books, a core component of scientific cultural capital. |
| `p3_3` | OK | Directly measures presence of technical books, a core component of scientific and technical cultural capital. |
| `p3_6` | OK | Directly measures presence of encyclopedic books, explicitly mentioned in the construct description. |
| `p3_8` | OK | Directly measures presence of history books, explicitly mentioned in the construct description. |
| `p3_11` | FLAG | School textbooks measure functional educational resources for academic performance rather than cultural capital reflecting exposure to scientific and educational culture. |GTODO leave as is
| `p4` | OK | Directly measures access to computers, a core digital infrastructure component of the construct. |
| `p5` | OK | Directly measures access to internet, a core digital infrastructure component of the construct. |

### `EDU|digital_and_cultural_capital`

**Verdict**: MIXED — Most items measure technology access and reading habits as intended, but smartphone ownership (p47_6) is a tangential proxy for digital capital rather than a direct measure of access to or use of ICTs for learning.

| Item | Verdict | Reason |
|------|---------|--------|
| `p47_3` | OK | Directly measures access to computers/tablets, core ICT resources for informal learning. |
| `p47_4` | OK | Directly measures internet access, essential infrastructure for digital capital and information access. |
| `p47_6` | FLAG | Smartphone ownership is a consumer device measure that does not substantively reflect access to ICTs for learning or cultural participation as described in the construct. | TODO leave as is
| `p45_1` | OK | Measures newspaper reading frequency, a direct indicator of information consumption and cultural engagement habits. |
| `p45_2` | OK | Measures book reading frequency, a direct indicator of reading habits and cultural participation. |

### `EDU|social_media_engagement`

**Verdict**: INCOHERENT — The construct mixes computer use for information/education with museum/exhibition attendance, which are substantively distinct behaviors unrelated to social media engagement or account ownership.

| Item | Verdict | Reason |
|------|---------|--------|
| `p48_1` | FLAG | Measures general computer use for information retrieval, not social media engagement or account ownership specifically. |
| `p48_3` | FLAG | Measures computer use for educational support, not social media engagement or internet-based social/communicative activity. |
| `p44_5` | FLAG | Measures offline cultural attendance (museums/exhibitions), which is unrelated to social media engagement, account ownership, or internet use for news. |
