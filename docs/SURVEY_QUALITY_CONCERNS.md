# Survey Quality Concerns — Navegador Construct Pipeline

**Audience**: Survey designers and data curators adding new modules to Navegador.
**Scope**: Known quality issues identified across all V5 construct reviews (Phase 1–3).
**Sources**:
- `construct_code_audit.md` — answer-code and sentinel audit (Stream 2)
- `construct_low_n_investigation.md` — coverage investigation (Stream 4)
- `construct_dimensionality_review.md` — PCA dimensionality review (Stream 3)
- `construct_direction_audit_v5.md` — item–aggregate correlation audit
- `construct_semantic_coherence_v5.md` — LLM semantic coherence review

---

## 1. Constructs Excluded from Analysis

The following constructs were excluded from the V5 DR sweep due to structural defects or insufficient coverage. They document patterns to avoid when designing future survey modules.

| Construct | Reason | N | Root Cause |
|-----------|--------|---|------------|
| `SOC\|digital_technology_access_and_ownership` | excluded_low_n | — | Gateway question — only asked to respondents who answered yes to internet access. n < 400 after filtering. |
| `SOC\|internet_engagement_and_digital_literacy` | excluded_low_n | — | Same gateway dependency as above. |
| `MIG\|transnational_social_ties` | excluded_low_n | — | Asked only to respondents with prior emigration experience. |
| `JUS\|legal_self_efficacy_and_access` | excluded_low_n | — | Asked only to respondents who reported legal proceedings. |
| `ECO\|job_quality_and_labor_conditions` | excluded_low_n | 231 | Conditional on being employed. Skip-pattern reduces effective n severely. |
| `SOC\|media_consumption_breadth` | excluded_low_n | 338 | TV/radio ownership gate; most respondents skip. |
| `SAL\|healthcare_access_and_utilization` | excluded_low_n | 177 | Conditional on recent healthcare contact. |
| `GEN\|intimate_partner_power_dynamics` | excluded_low_n | 427 | Conditional on being in a partnership; borderline N with α=0.41. |
| `ECO\|human_capital_and_employment_preparation` | audit_drop | — | Items measure structurally unrelated concepts; not recoverable. |
| `EDU\|social_media_engagement` | audit_drop | — | Construct name–item mismatch: items measure computer use and museum attendance, not social media. Lesson: verify item text against construct name before committing. |

**Rule for future surveys**: Constructs requiring respondents to pass a gateway question (ownership, prior experience, employment status) should be designed to reach ≥ 400 valid responses. If the target population is inherently small, note this explicitly and exclude from DR sweep.

---

## 2. Known Semantic Compromises (Items Kept Despite Coherence Concerns)

These items were flagged by the LLM coherence review but retained because removing them would hurt alpha or because the survey has no better alternative. They represent known limitations of the current measurement approach. **Future surveys should include dedicated replacement items.**

| Construct | Item | Concern | Why Kept |
|-----------|------|---------|----------|
| `IDE\|personal_optimism_efficacy` | p24 | Retrospective life satisfaction — measures past, not forward-looking efficacy | α would drop 0.018; no replacement |
| `IDE\|moral_normative_conservatism` | p57 | Political ideology (left-right), not moral normativity | α would drop 0.151 — item is load-bearing despite conceptual mismatch |
| `CUL\|authoritarian_predisposition` | p23 | Pragmatic problem-solving willingness, not authoritarian preference | α drops 0.048 without it |
| `CUL\|authoritarian_predisposition` | p60 | Democratic deference/compliance, not authoritarian preference | α drops 0.054 without it |
| `REL\|supernatural_beliefs` | p17_15 | Belief in "power of mind" — cognitive/psychological, not supernatural | Fits cultural folk-belief cluster; kept per researcher judgement |
| `REL\|personal_religiosity` | p11 | Petitioning saints — folk devotionalism, may reflect tradition over conviction | Kept per researcher judgement |
| `SAL\|health_risk_behaviors` | p28 | Lifetime smoking (yes/no), not current behavior or intensity | Only smoking indicator available |
| `IND\|perceived_indigenous_discrimination` | p20 | General skin-color discrimination, not indigenous-specific | Only colorism item available; closely related domain |
| `ENV\|state_and_family_responsibility_for_elder_care` | p44 | Behavioral intention (willingness to pay) vs. normative belief | 4-item scale; dropping creates 2-item scale |
| `ENV\|state_and_family_responsibility_for_elder_care` | p30 | Descriptive observation of children's behavior vs. normative belief | Same — scale coherence protected |
| `DER\|perceived_discrimination_social_exclusion` | p40_1 | Personal tolerance of child's homosexuality — individual not societal | No direct discrimination item available |
| `DER\|rights_awareness_personal_experience` | p53 | School bullying — peer harm, not institutional rights violation | Only additional experience item available |
| `JUS\|law_compliance_motivation` | p10 | Self-assessed law-abidingness (outcome), not motivation (process) | Kept; related construct dimension |
| `FED\|perceived_representativeness` | p12_1 | Party representativeness, not elected officials | Alpha protected; parties are proximate actors |
| `DEP\|cultural_socialization_in_childhood` | p12_1 | Child's own reading (outcome), not parental socialization (input) | Only second item in 3-item scale |
| `DEP\|cultural_identity_and_heritage` | p34, p35 | Indigenous language ability/literacy — behavioral competency not identity | Researcher judgement: language use is part of cultural identity |
| `CIE\|household_science_cultural_capital` | p3_11 | School textbooks — functional/curricular, not cultural capital | Retained as educational resource proxy |
| `EDU\|digital_and_cultural_capital` | p47_6 | Smartphone ownership — consumer device proxy, not ICT access | Retained; highly correlated with digital access in Mexican context |

**Recommendation for future surveys**: For each construct above, add 1–2 dedicated on-construct items that replace the semantic compromise. For example:
- `IDE|personal_optimism_efficacy`: add a forward-looking locus-of-control item ("¿Qué tanto cree que puede influir en su futuro?")
- `IDE|moral_normative_conservatism`: separate moral conservatism from political ideology with distinct battery
- `CUL|authoritarian_predisposition`: use validated authoritarian scale items (e.g., child-rearing values battery)
- `SAL|health_risk_behaviors`: replace lifetime smoking yes/no with current smoking frequency + alcohol combined scale

---

## 3. Constructs with Severe Item Dominance

Items where >85% of responses fall at one code behave like near-constants, adding little discriminatory power. They do not create bias (they're retained) but reduce the effective variance of the construct.

| Construct | Item | Dominance | Code meaning |
|-----------|------|-----------|--------------|
| `COR\|corruption_perception` | p15 | 92%@1.0 | "Yes, corruption exists" — ceiling effect |
| `HAB\|household_asset_endowment` | p36_2 | 97%@1.0 | Owns TV — near universal ownership |
| `HAB\|household_asset_endowment` | p36_21, p36_22 | 93–96%@2.0 | Doesn't own motorcycle/boat |
| `HAB\|basic_services_access` | p8 (dropped), p10 | 84–92%@1.0 | Basic water/electricity access — near universal |
| `HAB\|structural_housing_quality` | p2 | 84%@7.0 | Concrete roof — dominant in urban sample |
| `ENV\|state_and_family_responsibility_for_elder_care` | p44 | 84%@1.0 | Strongly agrees with elder care |
| `DEP\|cultural_identity_and_heritage` | p48, p50 | 89–94%@1.0 | Strong majority identities |
| `REL\|personal_religiosity` | p12, p13_1 | 71–74%@1.0 | Strong religious identification |

**Recommendation for future surveys**: Avoid including items where the expected population prevalence is >85% for one response. If the item is theoretically important (e.g., corruption exists, basic service access), use it as a filter/screener rather than part of a scaled construct.

---

## 4. Direction Coding Checklist

All of the following issues were found and corrected in V5. They represent common coding mistakes when designing multi-item scales:

### 4.1 Reversed scales mixed with direct scales
Many Mexican survey batteries mix "Mucho→Nada" (1=high, 4=low) with Likert agree/disagree (1=agree, 5=disagree). Items must be reverse-coded before aggregation so higher score = more of construct.

**Constructs corrected**: `FED|perceived_representativeness`, `MIG|perceived_opportunity_structure`, `SEG|perceived_security_trajectory`, `SAL|functional_health_status`, `DER|institutional_trust_justice`, `CIE|institutional_trust_in_science`, `FED|political_interest_and_engagement`, `CIE|science_technology_interest_engagement`, `IND|national_economic_outlook`, `ECO|labor_union_attitudes`, `FED|fiscal_and_service_federalism_preferences`, `REL|supernatural_beliefs`, `REL|personal_religiosity`, `HAB|household_asset_endowment`, `MED|pro_environmental_civic_engagement`, `CIE|household_science_cultural_capital`, `EDU|digital_and_cultural_capital`, `EDU|educational_returns_belief`, `DER|social_rights_service_quality`, `DEP|reading_engagement_and_literacy`, `REL|church_state_separation`.

**Rule**: Before finalizing a construct, verify item–aggregate Spearman r > 0 for all items. Items with r < −0.10 need reversal or removal. Run `verify_construct_directions.py` after every build.

### 4.2 Binary items with unexpected coding
Some binary (Sí/No) items code Sí=2 rather than Sí=1. Verify value labels before assuming scale direction.

**Affected**: `GEN|intimate_partner_power_dynamics` (p23_1, p23_5 coded 3=neutral, 2=yes — sentinel override needed).

### 4.3 "Depende"/"Otra" codes as pseudo-sentinels
Spontaneous/open response codes (typically 3–6 depending on item) act as ordinally invalid interruptions in otherwise ordinal scales. They must be explicitly excluded.

**Constructs corrected**: `JUS|judicial_institutional_trust` (codes 3, 5, 6), `GLO|economic_globalization_attitudes` (code 4), `REL|supernatural_beliefs` (code 4), `REL|personal_religiosity` (code 4), `EDU|educational_returns_belief` (code 4).

**Rule**: Always inspect value label dictionaries for non-ordinal codes below the ≥97 sentinel threshold. Add them to `item_sentinel_overrides` in the construct overrides file.

---

## 5. Construct Dimensionality

A PCA review found that `EDU|digital_and_cultural_capital` was two-dimensional:
- **PC1 (41.6%)**: device ownership (p47_3 desktop, p47_4 laptop, p47_6 phone)
- **PC2 (21.2%)**: social/communicative digital use (p48_1 computer for info, p48_3 computer for education)

The split was attempted as `EDU|social_media_engagement` but the construct name was wrong — the items were computer use for information/education and museum attendance, not social media. **Lesson**: when splitting a construct via PCA, verify item text against the proposed construct label before implementation.

**Rule for future surveys**: For constructs with ≥6 items, run PCA and inspect the first two components. If PC2 explains ≥15% of variance with opposing item loadings, consider a conceptual split with verified item labels.

---

## 6. Low-N Construct Patterns to Avoid

Gateway questions generate conditional subsamples that are unreliable for the DR bridge estimator (minimum usable N ≈ 400; recommended ≥ 600). Common patterns:

| Pattern | Example | Effect |
|---------|---------|--------|
| Employment-conditional items | "Among employed respondents only..." | Drops to ~40–60% of sample |
| Ownership-conditional items | "Among those who own a TV..." | Drops to ~70–80% (high) but drops lower for niche items |
| Experience-conditional items | "Among those who have emigrated..." | Can drop to 15–30% |
| Healthcare contact-conditional | "Among those who visited a doctor..." | Can drop to ~15% |
| Relationship-conditional items | "Among those currently partnered..." | ~60–70% but reduces further with sub-questions |

**Rule**: Construct items should be answerable by all respondents, or the skip-pattern population must exceed 400 respondents after sentinel filtering. When in doubt, use prevalence estimates from the survey's marginal distributions before designing skip-dependent batteries.

---

## 7. MIXED Constructs — Coverage Limitations

The following constructs are internally coherent but narrower in scope than their names suggest, due to limited survey coverage of the full theoretical domain. They are usable but should be interpreted with this caveat:

| Construct | Limitation |
|-----------|------------|
| `DEP\|reading_engagement_and_literacy` | Only newspaper/magazine reading habits; missing books, reading ability, barriers |
| `SAL\|health_risk_behaviors` | Only alcohol + lifetime smoking; missing dietary risk, sedentarism, other substances |
| `IDE\|personal_optimism_efficacy` | Missing future-orientation and locus-of-control items; includes retrospective item |
| `CUL\|authoritarian_predisposition` | Borderline items included to maintain alpha; pure authoritarian indicators are sparse |
| `DER\|rights_awareness_personal_experience` | Mixes institutional violations with peer harm (bullying); kept to avoid 2-item scale |
| `ENV\|state_and_family_responsibility_for_elder_care` | Mixes normative beliefs with behavioral observations; 1 purely normative item after drops |

---

## 8. Summary Checklist for New Survey Integration

Before adding a new survey module to the Navegador construct pipeline:

- [ ] **Item direction**: Check value labels — confirm Sí=1 or high=more of construct. Flag all items where scale direction is reversed.
- [ ] **Sentinel codes**: Inspect all codes below 97. Flag spontaneous/"depende"/"otra" codes as extra sentinels.
- [ ] **Gateway questions**: Identify skip-pattern subsets. Estimate effective n for each conditional construct; exclude if n < 400.
- [ ] **Semantic coherence**: For each proposed construct, list all items and their exact question text. Verify all items measure the same underlying concept. Remove items that are behavioral outcomes, demographic proxies, or tangentially related concepts.
- [ ] **Dimensionality**: For constructs with ≥6 items, run PCA. If PC2 ≥ 15%, consider conceptual split (with verified item labels).
- [ ] **Dominance**: Check marginal distributions. Flag items >85% at one code as low-discriminatory.
- [ ] **Alpha floor**: Target α ≥ 0.5 after item cleaning. Constructs with α < 0.4 and n_items < 3 become single-item tier2 and contribute less to the sweep.
- [ ] **Run `build_construct_variables.py`** and inspect the sanity-check output for warnings.
- [ ] **Run `verify_construct_directions.py`** and confirm 0 FLAG_DIRECTION before launching the sweep.
