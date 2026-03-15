# WVS Construct Semantic Coherence Review — V1

Generated: 2026-03-13 19:47
Model: claude-haiku-4-5-20251001

## Summary

| Metric | Count |
|--------|-------|
| Constructs reviewed | 35 |
| COHERENT | 14 |
| MIXED | 14 |
| INCOHERENT | 7 |
| ERROR | 0 |
| Items flagged for removal | 43 |
| Constructs with ≥1 flagged item | 21 |

## Suggested items_to_drop for wvs_construct_overrides.json

```json
  "WVS_A|social_intolerance_outgroups": ["Q20", "Q25"],
  "WVS_A|subjective_wellbeing": ["Q46"],
  "WVS_D|female_income_threat_to_marriage": ["Q35_3"],
  "WVS_D|gender_role_traditionalism": ["Q28", "Q30"],
  "WVS_E|confidence_in_civil_society_organizations": ["Q79"],
  "WVS_E|confidence_in_domestic_institutions": ["Q64", "Q66", "Q67", "Q68", "Q75", "Q77", "Q78"],
  "WVS_E|confidence_in_international_organizations": ["Q82", "Q89"],
  "WVS_E|democratic_values_importance": ["Q241", "Q244", "Q247"],
  "WVS_E|electoral_integrity": ["Q233"],
  "WVS_E|science_technology_optimism": ["Q158", "Q159", "Q163"],
  "WVS_F|civic_dishonesty_tolerance": ["Q179"],
  "WVS_F|life_autonomy_morality_permissiveness": ["Q185", "Q187", "Q188"],
  "WVS_F|religion_versus_secularism_orientation": ["Q175"],
  "WVS_F|religious_belief": ["Q164"],
  "WVS_F|religious_practice_and_self_identification": ["Q171", "Q172", "Q173"],
  "WVS_F|sexual_and_reproductive_morality_permissiveness": ["Q182", "Q183", "Q184", "Q186", "Q193"],
  "WVS_F|violence_tolerance": ["Q192"],
  "WVS_G|outgroup_trust": ["Q60"],
  "WVS_H|freedom_security_tradeoff_perception": ["Q149", "Q150"],
  "WVS_H|institutional_threat_perception": ["Q135"],
  "WVS_I|science_skepticism": ["Q161"],
```

## All Constructs

| Key | Verdict | Flagged items | Reason |
|-----|---------|---------------|--------|
| `WVS_A|social_intolerance_outgroups` | MIXED | `Q20`, `Q25` | Most items measure unwillingness to have outgroups as neighbors (social intolera |
| `WVS_A|subjective_wellbeing` | MIXED | `Q46` | Q48 and Q49 directly measure the construct, but Q46 is vague and all three items |
| `WVS_C|job_scarcity_gender_discrimination` | COHERENT | — | Both items directly measure endorsement of gender-based employment prioritizatio |
| `WVS_C|job_scarcity_nativist_preference` | COHERENT | — | Both items directly measure preference for national workers over immigrants in e |
| `WVS_C|work_ethic` | COHERENT | — | All three items directly measure core dimensions of work ethic: negative views o |
| `WVS_D|gender_role_traditionalism` | MIXED | `Q28`, `Q30` | Three items directly measure belief in male superiority in specific domains, but |
| `WVS_D|female_income_threat_to_marriage` | MIXED | `Q35_3` | Q35 directly measures perceived threat to marriage from female income superiorit |
| `WVS_E|confidence_in_domestic_institutions` | MIXED | `Q64`, `Q66`, `Q67`, `Q68`, `Q75`, `Q77`, `Q78` | Most items measure confidence in domestic governmental and political institution |
| `WVS_E|confidence_in_civil_society_organizations` | MIXED | `Q79` | Q79 is too vague to reliably measure confidence in civil society organizations,  |
| `WVS_E|confidence_in_international_organizations` | MIXED | `Q82`, `Q89` | Most items measure confidence in international organizations, but Q82 (NAFTA/TLC |
| `WVS_E|electoral_integrity` | MIXED | `Q233` | Most items measure electoral integrity directly, but Q233 on gender equality in  |
| `WVS_E|autocracy_support` | COHERENT | — | All four items directly measure preference for distinct non-democratic governanc |
| `WVS_E|democratic_values_importance` | INCOHERENT | `Q241`, `Q244`, `Q247` | Items conflate perceived frequency of government actions with importance of demo |
| `WVS_E|voting_participation` | COHERENT | — | Both items directly measure self-reported voting frequency at different politica |
| `WVS_E|science_technology_optimism` | INCOHERENT | `Q158`, `Q159`, `Q163` | Items Q158 and Q159 are incomplete/truncated in the provided text, making semant |
| `WVS_E|economic_ideology` | COHERENT | — | All four items directly measure core dimensions of economic ideology along the l |
| `WVS_F|religious_belief` | MIXED | `Q164` | Most items validly measure religious belief content, but Q164 measures importanc |
| `WVS_F|religious_practice_and_self_identification` | INCOHERENT | `Q171`, `Q172`, `Q173` | Items Q171 and Q172 appear to measure service attendance frequency but use agree |
| `WVS_F|religious_exclusivism` | COHERENT | — | Both items directly measure privileging one's own religion over competing worldv |
| `WVS_F|civic_dishonesty_tolerance` | MIXED | `Q179` | Four items clearly measure tolerance for civic/economic dishonesty, but Q179 shi |
| `WVS_F|sexual_and_reproductive_morality_permissiveness` | INCOHERENT | `Q182`, `Q183`, `Q184`, `Q186`, `Q193` | Items measure frequency of occurrence or acceptability of behaviors, but the sca |
| `WVS_F|life_autonomy_morality_permissiveness` | INCOHERENT | `Q185`, `Q187`, `Q188` | Items measure frequency of occurrence or discussion rather than moral permissive |
| `WVS_F|violence_tolerance` | MIXED | `Q192` | Items Q189-Q191 measure tolerance for interpersonal violence, while Q192 measure |
| `WVS_F|religion_versus_secularism_orientation` | INCOHERENT | `Q175` | Q175 measures religious practice frequency (behavioral), not orientation toward  |
| `WVS_G|outgroup_trust` | MIXED | `Q60` | Q60 measures trust in acquaintances (ingroup), which is conceptually distinct fr |
| `WVS_G|perceived_positive_effects_of_immigration` | COHERENT | — | All four items directly measure beliefs about specific beneficial outcomes of im |
| `WVS_G|perceived_negative_effects_of_immigration` | COHERENT | — | All four items directly measure perceived negative consequences of immigration a |
| `WVS_H|basic_needs_deprivation` | COHERENT | — | All three items directly measure frequency of experiencing deprivation across co |
| `WVS_H|neighborhood_disorder_and_crime` | COHERENT | — | All items measure perceived frequency of specific antisocial behaviors and crime |
| `WVS_H|socioeconomic_insecurity_worry` | COHERENT | — | Both items directly measure worry about distinct but related dimensions of socio |
| `WVS_H|existential_threat_worry` | COHERENT | — | All three items directly measure worry about distinct large-scale violent threat |
| `WVS_H|acceptance_of_state_surveillance` | COHERENT | — | All three items directly measure acceptance of distinct government surveillance  |
| `WVS_H|freedom_security_tradeoff_perception` | INCOHERENT | `Q149`, `Q150` | Both items are incomplete/truncated in the provided text, making it impossible t |
| `WVS_H|institutional_threat_perception` | MIXED | `Q135` | Q134 directly measures institutional intrusion threat perception, but Q135 measu |
| `WVS_I|science_skepticism` | MIXED | `Q161` | Q161 measures perceived negative consequences of science (outcome evaluation), w |

## Flagged Constructs

### `WVS_A|social_intolerance_outgroups`

**Verdict**: MIXED — Most items measure unwillingness to have outgroups as neighbors (social intolerance), but Q20 (people with AIDS) and Q25 (unmarried cohabiting couples) measure disease-related stigma and moral disapproval of lifestyle rather than prejudice against social identity groups.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q19` | OK | Directly measures social distance from racial/ethnic outgroups, core to social intolerance construct. |
| `Q20` | FLAG | Measures health-related stigma and fear of contagion rather than prejudice against a social identity group or outgroup. |
| `Q21` | OK | Directly measures social distance from immigrants/foreign workers, a classic outgroup in intolerance research. |
| `Q22` | OK | Directly measures social distance from homosexuals based on sexual orientation, a key outgroup in social intolerance. |
| `Q23` | OK | Directly measures social distance from religious outgroups, core to social intolerance construct. |
| `Q25` | FLAG | Measures moral disapproval of a lifestyle choice rather than prejudice against a social identity group or demographic outgroup. |
| `Q26` | OK | Directly measures social distance from linguistic outgroups, consistent with ethnic/cultural intolerance. |

### `WVS_A|subjective_wellbeing`

**Verdict**: MIXED — Q48 and Q49 directly measure the construct, but Q46 is vague and all three items have mismatched scale labels that do not align with their question text.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q46` | FLAG | Question text is incomplete/unclear ('¿usted diría que es...?') and scale labels (Bueno/Le da igual/Malo) do not semantically match subjective wellbeing dimensions; unclear what is being evaluated. |
| `Q48` | OK | Directly measures perceived freedom of choice and control over life, a core component of subjective wellbeing, despite scale label mismatch in documentation. |
| `Q49` | OK | Directly measures life satisfaction on a 1-10 scale, a core component of subjective wellbeing, despite scale label mismatch in documentation. |

### `WVS_D|gender_role_traditionalism`

**Verdict**: MIXED — Three items directly measure belief in male superiority in specific domains, but Q28 measures a distinct concern about maternal employment's effects on children rather than male superiority.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q28` | FLAG | Measures concern about child welfare outcomes from maternal employment rather than belief in male superiority or male advantage in public roles; substantively distinct from the gender hierarchy dimension. |
| `Q29` | OK | Directly measures belief in male superiority in political leadership, a core public-role domain of the construct. |
| `Q30` | FLAG | Item text is incomplete (cuts off mid-sentence); cannot assess whether it measures male superiority in education or a different concept entirely. |
| `Q31` | OK | Directly measures belief in male superiority in business leadership, a core public-role domain of the construct. |

### `WVS_D|female_income_threat_to_marriage`

**Verdict**: MIXED — Q35 directly measures perceived threat to marriage from female income superiority, but Q35_3 appears to be a recoded or collapsed version of the same item rather than a distinct measure, creating redundancy rather than construct validation.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q35` | OK | Directly measures perception that a wife earning more than her husband causes relational problems (threat to marriage), aligned with the construct definition. |
| `Q35_3` | FLAG | Appears to be a recoded version of Q35 rather than a separate item; using the same source item in different categorical formats does not provide independent construct validation. |

### `WVS_E|confidence_in_domestic_institutions`

**Verdict**: MIXED — Most items measure confidence in domestic governmental and political institutions, but several items (churches, media, unions, universities, large companies, banks) measure confidence in non-governmental or civil society institutions that fall outside the core construct definition.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q64` | FLAG | Churches are religious institutions, not domestic governmental or political institutions. |
| `Q65` | OK | The military is a key domestic governmental institution. |
| `Q66` | FLAG | The press is a media institution, not a governmental or political institution per se. |
| `Q67` | FLAG | Television is a media institution, not a governmental or political institution per se. |
| `Q68` | FLAG | Labor unions are civil society organizations, not domestic governmental or political institutions. |
| `Q69` | OK | The police are a key domestic governmental institution. |
| `Q70` | OK | Courts and judges are core domestic governmental institutions. |
| `Q71` | OK | The government is a central domestic governmental institution. |
| `Q72` | OK | Political parties are core domestic political institutions. |
| `Q73` | OK | Congress is a central domestic political institution. |
| `Q74` | OK | Public bureaucracy is a key domestic governmental institution. |
| `Q75` | FLAG | Universities are educational institutions, not domestic governmental or political institutions. |
| `Q76` | OK | Elections are a core domestic political institution. |
| `Q77` | FLAG | Large companies are private sector entities, not domestic governmental or political institutions. |
| `Q78` | FLAG | Banks are private financial institutions, not domestic governmental or political institutions. |

### `WVS_E|confidence_in_civil_society_organizations`

**Verdict**: MIXED — Q79 is too vague to reliably measure confidence in civil society organizations, while Q80 and Q81 are appropriately specific.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q79` | FLAG | Question text 'Las organizaciones' is incomplete and ambiguous—it does not specify which organizations are being asked about, making it impossible to confirm it measures confidence in civil society organizations specifically. |
| `Q80` | OK | Directly measures confidence in women's organizations, a clear subset of civil society organizations. |
| `Q81` | OK | Directly measures confidence in charitable and humanitarian organizations, a clear subset of civil society organizations. |

### `WVS_E|confidence_in_international_organizations`

**Verdict**: MIXED — Most items measure confidence in international organizations, but Q82 (NAFTA/TLCAN) and Q89 (INE) are off-target: TLCAN is a trade agreement rather than an organization, and INE is a domestic Mexican institution, not an international organization.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q82` | FLAG | TLCAN is a trade agreement, not an international organization; measures confidence in a bilateral/regional trade regime rather than supranational institutional confidence. |
| `Q83` | OK | UN is a core international organization matching the construct definition. |
| `Q84` | OK | IMF is a major international financial organization matching the construct definition. |
| `Q85` | OK | International Criminal Court is an international judicial organization matching the construct definition. |
| `Q86` | OK | NATO is an international military alliance organization matching the construct definition. |
| `Q87` | OK | World Bank is a major international financial organization matching the construct definition. |
| `Q88` | OK | WHO is a major international health organization matching the construct definition. |
| `Q89` | FLAG | INE is Mexico's domestic electoral institute, not an international or supranational organization; measures confidence in a national institution. |

### `WVS_E|electoral_integrity`

**Verdict**: MIXED — Most items measure electoral integrity directly, but Q233 on gender equality in candidacy is tangentially related to electoral fairness rather than core integrity concerns.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q224` | OK | Directly measures vote counting integrity, a core component of electoral process fairness. |
| `Q225` | OK | Directly measures opposition candidate exclusion, a fundamental electoral integrity violation. |
| `Q226` | OK | Directly measures media bias toward ruling party, a key threat to fair electoral competition. |
| `Q227` | OK | Directly measures vote buying, a classic electoral integrity violation. |
| `Q228` | OK | Directly measures objective media coverage, essential to fair electoral information environment. |
| `Q229` | OK | Directly measures fairness of electoral authorities, central to process integrity. |
| `Q230` | OK | Directly measures wealth-based electoral manipulation, a key integrity concern. |
| `Q231` | OK | Directly measures voter intimidation at polling sites, a critical electoral integrity violation. |
| `Q232` | OK | Directly measures meaningful electoral choice availability, fundamental to electoral integrity. |
| `Q233` | FLAG | Measures gender representation opportunity in candidacy, which is electoral inclusion/equality rather than process integrity or fairness of vote counting and competition. |

### `WVS_E|democratic_values_importance`

**Verdict**: INCOHERENT — Items conflate perceived frequency of government actions with importance of democratic values, and mix redistributive policy outcomes with fundamental democratic principles.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q241` | FLAG | Measures perceived frequency of redistributive taxation, not importance of democratic values; conflates policy outcome with democratic principle. |
| `Q244` | FLAG | Measures perceived frequency of unemployment assistance provision, not importance of democratic values; conflates welfare policy outcome with democratic principle. |
| `Q246` | OK | Directly addresses importance of civil rights protection from state oppression, a core democratic value. |
| `Q247` | FLAG | Measures perceived frequency of state income equalization, not importance of democratic values; conflates redistributive outcome with democratic principle. |
| `Q249` | OK | Addresses importance of gender equality rights, a fundamental democratic value. |

### `WVS_E|science_technology_optimism`

**Verdict**: INCOHERENT — Items Q158 and Q159 are incomplete/truncated in the provided text, making semantic assessment impossible; Q163's scale (frequency anchors) is semantically mismatched to a comparative judgment question about world improvement.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q158` | FLAG | Question text is incomplete ('La ciencia y la tecnología están haciendo que nuestras vidas sean...'); cannot assess semantic validity without full item wording. |
| `Q159` | FLAG | Question text is incomplete ('Gracias a la ciencia y la tecnología habrá más oportunidades para...'); cannot assess semantic validity without full item wording. |
| `Q163` | FLAG | Scale uses frequency anchors (Muy frecuentemente/Algo frecuente/Poco frecuente/Nada frecuente) but question asks for comparative judgment ('mejor o peor'), creating a mismatch between construct response mode and scale semantics. |

### `WVS_F|religious_belief`

**Verdict**: MIXED — Most items validly measure religious belief content, but Q164 measures importance/salience rather than belief itself, creating a semantic distinction between attitudinal centrality and propositional belief.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q164` | FLAG | Measures importance of God in life (salience/centrality) rather than belief in God's existence; these are conceptually distinct dimensions. |
| `Q165` | OK | Directly measures belief in God, core component of religious belief construct. |
| `Q166` | OK | Directly measures belief in afterlife, a central supernatural belief within the construct. |
| `Q167` | OK | Directly measures belief in hell, a core religious/supernatural belief. |
| `Q168` | OK | Directly measures belief in heaven, a core religious/supernatural belief. |

### `WVS_F|religious_practice_and_self_identification`

**Verdict**: INCOHERENT — Items Q171 and Q172 appear to measure service attendance frequency but use agreement scales inappropriate for frequency questions, while Q173 text is incomplete making assessment impossible; scale-question mismatches undermine construct validity.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q171` | FLAG | Question asks about frequency of religious service attendance ('¿Con qué frecuencia...?') but uses agreement scale (Muy de acuerdo/En desacuerdo) rather than frequency scale; semantic mismatch between question and response options. |
| `Q172` | FLAG | Question text is incomplete ('Sin considerar bodas o funerales, ¿con qué...') making it impossible to assess whether it measures the intended construct; appears to be a frequency question with agreement scale mismatch. |
| `Q173` | FLAG | Question text is incomplete ('Independientemente de si va o no a la iglesia,') preventing assessment of whether it measures self-identified religiousness or another construct; cannot evaluate semantic validity. |

### `WVS_F|civic_dishonesty_tolerance`

**Verdict**: MIXED — Four items clearly measure tolerance for civic/economic dishonesty, but Q179 shifts from behavioral/attitudinal frequency to abstract justifiability judgment, creating semantic inconsistency.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q177` | OK | Directly measures frequency of claiming undeserved government benefits, a core civic dishonesty behavior. |
| `Q178` | OK | Directly measures frequency of fare evasion, a prototypical economic dishonesty behavior. |
| `Q179` | FLAG | Asks about justifiability of stealing (abstract moral judgment) rather than frequency of behavior/tolerance, creating scale inconsistency with other items. |
| `Q180` | OK | Directly measures frequency of tax evasion, a core economic dishonesty behavior. |
| `Q181` | OK | Directly measures frequency of accepting bribes, a prototypical civic dishonesty behavior. |

### `WVS_F|sexual_and_reproductive_morality_permissiveness`

**Verdict**: INCOHERENT — Items measure frequency of occurrence or acceptability of behaviors, but the scale labels ('Muy frecuentemente' to 'Nada frecuente') are ambiguous regarding whether they assess personal moral permissiveness, perceived social prevalence, or personal engagement.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q182` | FLAG | Scale measures frequency of occurrence (how often homosexuality happens), not tolerance or moral permissiveness toward it. |
| `Q183` | FLAG | Scale measures frequency of occurrence (how often prostitution happens), not tolerance or moral permissiveness toward it. |
| `Q184` | FLAG | Scale measures frequency of occurrence (how often abortion happens), not tolerance or moral permissiveness toward it. |
| `Q186` | FLAG | Scale measures frequency of occurrence (how often premarital sex happens), not tolerance or moral permissiveness toward it. |
| `Q193` | FLAG | Scale measures frequency of occurrence (how often casual sex happens), not tolerance or moral permissiveness toward it. |

### `WVS_F|life_autonomy_morality_permissiveness`

**Verdict**: INCOHERENT — Items measure frequency of occurrence or discussion rather than moral permissiveness toward these life-course decisions.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q185` | FLAG | Scale measures how frequently divorce occurs, not respondent's moral permissiveness toward divorce as a personal choice. |
| `Q187` | FLAG | Scale measures how frequently suicide occurs, not respondent's moral permissiveness toward suicide as a personal decision. |
| `Q188` | FLAG | Scale measures how frequently euthanasia occurs, not respondent's moral permissiveness toward euthanasia as a personal choice. |

### `WVS_F|violence_tolerance`

**Verdict**: MIXED — Items Q189-Q191 measure tolerance for interpersonal violence, while Q192 measures justifiability of political violence as a means to an end—a conceptually distinct dimension.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q189` | OK | Directly measures moral justifiability of domestic violence (interpersonal). |
| `Q190` | OK | Directly measures moral justifiability of parental corporal punishment (interpersonal). |
| `Q191` | OK | Directly measures moral justifiability of general interpersonal violence. |
| `Q192` | FLAG | Measures justifiability of violence as instrumental political/ideological means, which is conceptually distinct from tolerance for interpersonal violence and conflates means-justification reasoning with violence tolerance. |

### `WVS_F|religion_versus_secularism_orientation`

**Verdict**: INCOHERENT — Q175 measures religious practice frequency (behavioral), not orientation toward religion versus secularism (attitudinal), creating a fundamental semantic mismatch with the construct definition.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q174` | OK | Agreement scale directly measures attitudinal orientation on religion-secular reasoning tension as described. |
| `Q175` | FLAG | Frequency scale (daily to never) measures behavioral religious practice, not orientation or belief about whether religion should guide life versus secular reasoning. |

### `WVS_G|outgroup_trust`

**Verdict**: MIXED — Q60 measures trust in acquaintances (ingroup), which is conceptually distinct from outgroup trust; the remaining three items validly measure generalized trust toward outgroups.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q60` | FLAG | Acquaintances (conocidos) represent an established ingroup rather than outgroup; this measures ingroup trust, not generalized trust toward strangers or those outside one's social circle. |
| `Q61` | OK | People met for the first time are genuine strangers and represent outgroup trust as defined. |
| `Q62` | OK | People of different religions represent a key outgroup dimension specified in the construct definition. |
| `Q63` | OK | People of different nationalities represent a key outgroup dimension specified in the construct definition. |

### `WVS_H|freedom_security_tradeoff_perception`

**Verdict**: INCOHERENT — Both items are incomplete/truncated in the provided text, making it impossible to assess whether they measure complementary vs. competing values perceptions, and they appear to measure different directional claims about the freedom-security relationship.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q149` | FLAG | Item text is incomplete ('tanto la libertad como la' cuts off mid-sentence), preventing assessment of whether it measures complementarity or tradeoff perception. |
| `Q150` | FLAG | Item text is incomplete ('la libertad y la seguridad' cuts off mid-sentence), preventing assessment of the specific directional claim about the freedom-security relationship. |

### `WVS_H|institutional_threat_perception`

**Verdict**: MIXED — Q134 directly measures institutional intrusion threat perception, but Q135 measures racist conduct as a social threat rather than institutional threat to private life.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q134` | OK | Directly measures perceived frequency of police/military intrusion into private life, the core institutional threat component. |
| `Q135` | FLAG | Racist conduct is a social/interpersonal threat distinct from institutional intrusion; it does not measure police/military threat to private life specifically. |

### `WVS_I|science_skepticism`

**Verdict**: MIXED — Q161 measures perceived negative consequences of science (outcome evaluation), while Q162 measures perceived personal relevance of science knowledge (utility judgment)—related but semantically distinct dimensions.

| Item | Verdict | Reason |
|------|---------|--------|
| `Q161` | FLAG | Measures belief in negative consequences of science rather than skepticism toward science itself; conflates science criticism with science skepticism. |
| `Q162` | OK | Directly measures dismissive attitude toward science's relevance in everyday life, core to science skepticism. |
