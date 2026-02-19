# 2x2 Architecture × Model Comparison

**Generated:** 2026-02-18 04:22:38

**Test Questions:** 10 (semantic search selected variables)

**Models:** mini = gpt-4.1-mini-2025-04-14 | full = gpt-4.1-2025-04-14

---

## Success Rate

| Question | OLD+mini | OLD+full | NEW+mini | NEW+full |
|----------|----------|----------|----------|----------|
| q1_religion_politics | ✅ | ✅ | ✅ | ✅ |
| q2_environment_economy | ✅ | ✅ | ✅ | ✅ |
| q3_education_poverty | ✅ | ✅ | ✅ | ✅ |
| q4_gender_family | ✅ | ✅ | ✅ | ✅ |
| q5_migration_culture | ✅ | ✅ | ✅ | ✅ |
| q6_health_poverty | ✅ | ✅ | ✅ | ✅ |
| q7_democracy_corruption | ✅ | ✅ | ✅ | ✅ |
| q8_indigenous_discrimination | ✅ | ✅ | ✅ | ✅ |
| q9_technology_education | ✅ | ✅ | ✅ | ✅ |
| q10_security_justice | ✅ | ✅ | ✅ | ✅ |

---

## Latency (seconds)

| Question | OLD+mini | OLD+full | NEW+mini | NEW+full |
|----------|----------|----------|----------|----------|
| q1_religion_politics | 56.6 | 73.3 | 19.0 | 27.6 |
| q2_environment_economy | 57.3 | 62.8 | 23.7 | 48.3 |
| q3_education_poverty | 51.5 | 65.1 | 18.0 | 32.9 |
| q4_gender_family | 57.7 | 59.9 | 18.8 | 27.5 |
| q5_migration_culture | 61.7 | 80.8 | 19.5 | 57.2 |
| q6_health_poverty | 62.7 | 72.1 | 23.5 | 46.3 |
| q7_democracy_corruption | 66.8 | 114.8 | 35.1 | 39.6 |
| q8_indigenous_discrimination | 58.9 | 67.3 | 25.7 | 33.3 |
| q9_technology_education | 55.6 | 60.3 | 25.8 | 32.0 |
| q10_security_justice | 58.6 | 69.5 | 20.6 | 38.5 |

---

## Variables Selected per Question

- **q1_religion_politics** (10): p44_4|CUL, p52_4|REL, p84_6|CUL, p56|REL, p52_2|REL, p52_1|REL, p43_1|REL, p53|REL, p52_5|REL, p52_3|REL
- **q2_environment_economy** (10): p21_4|MED, p23_1|MED, p2|MED, p1_2|MED, p14|MED, p6|MED, p41|MED, p24_1|MED, p1_3|MED, p30_3|MED
- **q3_education_poverty** (10): p21_1|POB, p18_4|POB, p55_4|EDU, p36|POB, p54_1|EDU, p39_9|EDU, p52|EDU, p37|POB, p49|EDU, p14|POB
- **q4_gender_family** (10): p43|FAM, p54_1|GEN, p59_2|GEN, p24|GEN, p68|FAM, p32|GEN, p66|FAM, p56|GEN, p56a_1|GEN, p14|FAM
- **q5_migration_culture** (10): p26_5|MIG, p36|MIG, p9_2|MIG, p43_5|MIG, p26_3|MIG, p26_6|MIG, p26_4|MIG, p2_1a_1|IDE, p4|IDE, p6|IDE
- **q6_health_poverty** (10): p9|POB, p21_2|POB, p48_3|SAL, p18_7|POB, p37|POB, p23_1|SAL, p21_5|POB, p9|SAL, p48|POB, p32|POB
- **q7_democracy_corruption** (10): p61_1|COR, p34|CUL, p33|CUL, p32|CUL, p61_2|COR, p19|COR, p26_1a_1|COR, p37_1|CUL, p35|CUL, p16|COR
- **q8_indigenous_discrimination** (10): p26_8|IND, p14|IND, p14a_1|IND, p26_5|IND, p26_6|IND, p45a_1|IND, p30|IND, p21|IND, p33_5|IND, p26_7|IND
- **q9_technology_education** (10): p47_1a|CIE, p27|CIE, p47_1|CIE, p44_1|CIE, p57|CIE, p52|CIE, p54_1|EDU, p4|CIE, p6|CIE, p44_10|CIE
- **q10_security_justice** (10): p29_4|SEG, p65|SEG, p8_3|SEG, p69|SEG, p68|SEG, p25a_1|JUS, p8_1|SEG, p54_16|SEG, p54_5|SEG, p62b_4|SEG

---

## Individual Reports

- [q1_religion_politics](./q1_religion_politics_comparison.md) — How do religion and politics relate in Mexico?
- [q2_environment_economy](./q2_environment_economy_comparison.md) — How do Mexicans balance environmental concerns with economic development?
- [q3_education_poverty](./q3_education_poverty_comparison.md) — What relationship do Mexicans see between education and poverty?
- [q4_gender_family](./q4_gender_family_comparison.md) — How are gender roles changing in the Mexican family?
- [q5_migration_culture](./q5_migration_culture_comparison.md) — How does migration affect Mexican cultural identity?
- [q6_health_poverty](./q6_health_poverty_comparison.md) — How does health access relate to poverty in Mexico?
- [q7_democracy_corruption](./q7_democracy_corruption_comparison.md) — What do Mexicans think about the relationship between democracy and corruption?
- [q8_indigenous_discrimination](./q8_indigenous_discrimination_comparison.md) — How do Mexicans perceive discrimination against indigenous peoples?
- [q9_technology_education](./q9_technology_education_comparison.md) — How does technology impact education according to Mexicans?
- [q10_security_justice](./q10_security_justice_comparison.md) — What relationship do Mexicans see between public security and justice?
