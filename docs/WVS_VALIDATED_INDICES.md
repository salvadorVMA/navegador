# WVS Validated Composite Indices — Complete Reference

*Compiled 2026-03-13. Verification note: Item codes drawn from training knowledge (cutoff August 2025). Before using in production code, verify Q-codes against the official WVS Wave 7 codebook at https://www.worldvaluessurvey.org/WVSDocumentationWV7.jsp. Time-series codes (A165, E069_06, etc.) are stable across waves and are the safest identifiers to use programmatically.*

---

## 1. Inglehart-Welzel Cultural Map Dimensions

### 1.1 Traditional vs. Secular-Rational Values (Y-axis)

**Authors:** Ronald Inglehart & Christian Welzel

**Key publications:**
- Inglehart, R. (1997). *Modernization and Postmodernization.* Princeton University Press.
- Inglehart, R. & Welzel, C. (2005). *Modernization, Cultural Change, and Democracy.* Cambridge University Press. ISBN 0-521-84635-9.
- Inglehart, R. (2018). *Cultural Evolution.* Cambridge University Press.

**Composing items:**

| Time-series code | Wave 7 Q-code | Description | Secular-rational direction |
|---|---|---|---|
| F034 | Q164 | Importance of God in life (1–10) | Low score |
| A006 | Q6 | Importance of religion in life | Low score |
| F120 | Q173 | Believe in God (yes/no) | No |
| E018 | Q45 | Respect for authority desirable | Disagree |
| A042 | Q22 | Child quality: Obedience | Not mentioned |
| G006 | Q254 | National pride (very proud) | Low score |
| F198 | Q185 | Abortion justifiable (1–10) | High score |

**Method:** First principal component of a ~10-item battery. **Waves:** 1–7.

---

### 1.2 Survival vs. Self-Expression Values (X-axis)

**Key publications:**
- Inglehart, R. & Welzel, C. (2005). *Modernization, Cultural Change, and Democracy.* Cambridge University Press.
- Welzel, C., Inglehart, R., & Klingemann, H.D. (2003). The theory of human development. *European Journal of Political Research*, 42(3), 341–379. https://doi.org/10.1111/1475-6765.00086
- Inglehart, R. & Welzel, C. (2010). Changing mass priorities. *Perspectives on Politics*, 8(2), 551–567. https://doi.org/10.1017/S1537592710001258

**Composing items:**

| Time-series code | Wave 7 Q-code | Description | Self-expression direction |
|---|---|---|---|
| Y001 | — | Post-materialist index (derived) | High |
| A165 | Q57 | Most people can be trusted | Yes |
| E025 | Q209 | Signing petitions (have done) | Yes |
| F118 | Q182 | Homosexuality justifiable (1–10) | High |
| A001 | Q1 | Importance of family in life | Low |
| H010 | Q131 | Life satisfaction (1–10) | High |

**Method:** Second principal component. **Waves:** 1–7.

---

### 1.3 Post-Materialist Index (Y001 / Y002)

**Author:** Ronald Inglehart

**Key publications:**
- Inglehart, R. (1971). The silent revolution in Europe. *American Political Science Review*, 65(4), 991–1017. https://doi.org/10.2307/1953494
- Inglehart, R. (1977). *The Silent Revolution.* Princeton University Press.
- Inglehart, R. (1990). *Culture Shift in Advanced Industrial Society.* Princeton University Press.

**4-item version (priority-ranking format):**

| Item code | Description | Materialist pole |
|---|---|---|
| E001 | Maintaining order in the nation | Yes |
| E002 | Giving people more say in government | No |
| E003 | Fighting rising prices | Yes |
| E004 | Protecting freedom of speech | No |

**Scoring:** Materialists prioritize E001+E003; Post-materialists prioritize E002+E004. 5-category scale.
**Official derived variables:** Y001 (4-item), Y002 (12-item). **Waves:** 1–7.

---

## 2. Emancipative Values Index (EVI) — Welzel 2013

**Author:** Christian Welzel

**Key publications:**
- Welzel, C. (2013). *Freedom Rising: Human Empowerment and the Quest for Emancipation.* Cambridge University Press. ISBN 978-1-107-03470-1. https://doi.org/10.1017/CBO9781139540919
- Welzel, C. & Inglehart, R. (2008). The role of ordinary people in democratization. *Journal of Democracy*, 19(1), 126–140.

**Structure:** 4 sub-indices × 3 items = 12 items total. Each item scored 0–1; sub-indices averaged; EVI ∈ [0, 1].

### Sub-index 1: Autonomy Values (Y003)

| Time-series code | Wave 7 Q-code | Description |
|---|---|---|
| A029 | Q7 | Child quality: Independence |
| A038 | Q18 | Child quality: Imagination |
| A040 | Q20 | Child quality: Non-obedience (reverse of A042) |

### Sub-index 2: Equality Values

| Time-series code | Wave 7 Q-code | Description |
|---|---|---|
| C001 | Q33 | Men have more right to jobs when scarce (disagree) |
| D059 | Q105 | Men make better political leaders (disagree) |
| D060 | Q106 | University education more important for boys (disagree) |

### Sub-index 3: Choice Values

| Time-series code | Wave 7 Q-code | Description |
|---|---|---|
| F118 | Q182 | Homosexuality justifiable (1–10) |
| F120 | Q184 | Abortion justifiable (1–10) |
| F121 | Q185 | Divorce justifiable (1–10) |

### Sub-index 4: Voice Values

| Time-series code | Wave 7 Q-code | Description |
|---|---|---|
| E025 | Q209 | Signing petitions (have done) |
| E026 | Q210 | Joining boycotts (have done) |
| E027 | Q211 | Attending demonstrations (have done) |

**Waves:** 3–7 (Waves 1–2 partial coverage).

---

## 3. Religiosity Indices

### 3.1 WVS Religiosity Composite (Norris & Inglehart)

**Key publication:**
- Norris, P. & Inglehart, R. (2004). *Sacred and Secular: Religion and Politics Worldwide.* Cambridge University Press. https://doi.org/10.1017/CBO9780511791017

**Items:**

| Time-series code | Wave 7 Q-code | Description |
|---|---|---|
| F034 | Q164 | Importance of God in life (1–10) |
| F028 | Q171 | Frequency of religious service attendance (1–8) |
| F029 | Q172 | Frequency of prayer (1–8) |
| F024 | Q173 | Believe in God (yes/no) |
| F025 | Q174 | Believe in life after death (yes/no) |
| A006 | Q6 | Importance of religion in life (1–4) |

**Waves:** 2–7.

### 3.2 Centrality of Religiosity Scale (CRS) — WVS approximation

**Key publication:**
- Huber, S. & Huber, O.W. (2012). The Centrality of Religiosity Scale (CRS). *Religions*, 3(3), 710–724. https://doi.org/10.3390/rel3030710

**WVS approximation items:** F024, F025, F028, F029, F034. **Waves:** 2–7.

---

## 4. Political & Institutional Trust

### 4.1 Confidence in Institutions Battery (official WVS)

**Key publications:**
- Newton, K. & Norris, P. (2000). Confidence in public institutions. In Pharr & Putnam (Eds.), *Disaffected Democracies.* Princeton University Press.
- Norris, P. (2011). *Democratic Deficit: Critical Citizens Revisited.* Cambridge University Press.

**Items (selected):**

| Time-series code | Wave 7 Q-code | Institution |
|---|---|---|
| E069_01 | Q64 | Churches |
| E069_02 | Q65 | Armed Forces |
| E069_03 | Q66 | Press |
| E069_04 | Q67 | Labour unions |
| E069_05 | Q68 | Police |
| E069_06 | Q69 | Parliament/Congress |
| E069_07 | Q70 | Civil services |
| E069_08 | Q71 | Television |
| E069_11 | Q74 | Major companies |
| E069_17 | Q80 | Government (national) |
| E069_18 | Q81 | Political parties |
| E069_61 | Q82 | Supreme Court |
| E069_62 | Q83 | Electoral commission |
| E069_63 | Q84 | Civil society organizations |

**Scale:** 4-point (1=great deal, 4=none at all; reverse-coded for analysis). **Waves:** 1–7.

**Common sub-indices:**
- Electoral/democratic: Parliament + Political parties + Electoral commission
- Law enforcement: Police + Courts
- Media: Press + Television

### 4.2 Political Trust Index (Zmerli & Newton)

**Key publication:**
- Zmerli, S. & Newton, K. (2008). Social trust and attitudes toward democracy. *Public Opinion Quarterly*, 72(4), 706–724. https://doi.org/10.1093/poq/nfn054

**Items:** E069_05 (Q68), E069_06 (Q69), E069_17 (Q80), A165 (Q57).

### 4.3 Generalized Social Trust

**Item:** A165 → Q57: "Generally speaking, would you say that most people can be trusted..."

**Key publications:**
- Putnam, R.D. (2000). *Bowling Alone.* Simon & Schuster.
- Delhey, J. & Newton, K. (2005). Predicting cross-national levels of social trust. *European Sociological Review*, 21(4), 311–327.

**Waves:** 1–7.

---

## 5. Authoritarianism & Democratic Values

### 5.1 Democratic Deconsolidation / Autocracy Support (Foa & Mounk)

**Key publication:**
- Foa, R.S. & Mounk, Y. (2016). The danger of deconsolidation. *Journal of Democracy*, 27(3), 5–17.

**Items:**

| Time-series code | Wave 7 Q-code | Description |
|---|---|---|
| E114 | Q235 | Strong leader without parliament (1–4) |
| E115 | Q236 | Army rule (1–4) |
| E116 | Q237 | Expert technocracy (1–4) |
| E117 | Q238 | Democratic system rating (1–4) |
| E123 | Q240 | Democracy importance (1–10) |
| E226 | Q252 | Democracy: free elections (essential) |
| E227 | Q253 | Democracy: civil rights (essential) |

**Key measures:** % rating army rule "good/very good" (E115); % rating democracy "not important" (E123 ≤ 5). **Waves:** 5–7.

### 5.2 Right-Wing Authoritarianism Approximation

**Key publications:**
- Cohrs, J.C., et al. (2005). *Personality and Social Psychology Bulletin*, 31(10), 1425–1434.
- Funke, F. (2005). *Political Psychology*, 26(2), 195–218.

**WVS proxy items:** A042 (Q22), E018 (Q45), E025/E026 reverse, F063 (Q6), D059 (Q105). **Waves:** 2–7.

---

## 6. Gender Equality Attitudes

### 6.1 Gender Egalitarianism Index (Inglehart & Norris)

**Key publication:**
- Inglehart, R. & Norris, P. (2003). *Rising Tide: Gender Equality and Cultural Change Around the World.* Cambridge University Press. https://doi.org/10.1017/CBO9780511550362

**Items:**

| Time-series code | Wave 7 Q-code | Description |
|---|---|---|
| C001 | Q33 | Men have more right to jobs when scarce |
| D059 | Q105 | Men make better political leaders |
| D060 | Q106 | University more important for boys |
| D061 | Q107 | Men make better business executives |
| D078 | Q37 | Housewife role as fulfilling as working |

**Scoring:** Reverse-coded (higher = more egalitarian), averaged. **Waves:** 2–7.

### 6.2 Traditional Gender Norms (Alesina, Giuliano & Nunn)

**Key publication:**
- Alesina, A., Giuliano, P., & Nunn, N. (2013). On the origins of gender roles: Women and the plough. *Quarterly Journal of Economics*, 128(2), 469–530. https://doi.org/10.1093/qje/qjt005

**Items:** C001 + D059 + D060 averaged.

---

## 7. Additional Indices

### 7.1 Social Capital (Bjørnskov)

**Key publication:**
- Bjørnskov, C. (2006). The multiple facets of social capital. *European Journal of Political Economy*, 22(1), 22–40. https://doi.org/10.1016/j.ejpoleco.2005.05.006

**Items:** A165 (Q57, interpersonal trust), A098–A106 (voluntary associations), E025–E027 (political action). **Waves:** 2–7.

### 7.2 Subjective Well-Being (Inglehart et al.)

**Key publication:**
- Inglehart, R., Foa, R., Peterson, C., & Welzel, C. (2008). Development, freedom, and rising happiness. *Perspectives on Psychological Science*, 3(4), 264–285. https://doi.org/10.1111/j.1745-6924.2008.00078.x

**Items:** A008 (Q46, happiness 1–4), A170 (Q49, life satisfaction 1–10). **Waves:** 1–7.

### 7.3 Environmental Concern Index

**Key publication:**
- Knight, K. (2016). Temporal variation in the relationship between national income and environmental concern. *Social Forces*, 94(3), 1157–1184.

**Items:** B001 (Q111), B002 (Q112), B003 (Q113), B004 (Q114). **Waves:** 3–7.

---

## 8. Official WVS Y-prefix Derived Variables

| Code | Name | Description |
|---|---|---|
| Y001 | Post-Materialist Index (4-item) | Materialist (1) to Post-Materialist (3) |
| Y002 | Post-Materialist Index (12-item) | Extended version |
| Y003 | Autonomy Index | EVI Autonomy sub-component (child qualities) |

---

## 9. Complete Item Code Cross-Walk (validated indices only)

| Time-series code | Wave 7 Q-code | Used in |
|---|---|---|
| A001 | Q1 | Self-Expression dimension |
| A006 | Q6 | Traditional/Secular dimension, Religiosity |
| A008 | Q46 | Subjective Well-Being |
| A029 | Q7 | EVI Autonomy |
| A038 | Q18 | EVI Autonomy |
| A040 | Q20 | EVI Autonomy |
| A042 | Q22 | Traditional/Secular, RWA |
| A098–A106 | Q94–Q102 | Social Capital |
| A165 | Q57 | Self-Expression, Interpersonal Trust, Political Trust |
| A170 | Q49 | Subjective Well-Being |
| B001–B004 | Q111–Q114 | Environmental Concern |
| C001 | Q33 | EVI Equality, Gender Egalitarianism |
| D059 | Q105 | EVI Equality, Gender Egalitarianism, RWA |
| D060 | Q106 | EVI Equality, Gender Egalitarianism |
| D061 | Q107 | Gender Egalitarianism |
| D078 | Q37 | Gender Egalitarianism |
| E001–E004 | Q150–Q153 | Post-Materialist |
| E018 | Q45 | Traditional/Secular, RWA |
| E025 | Q209 | Self-Expression, EVI Voice, Social Capital |
| E026 | Q210 | EVI Voice, Social Capital |
| E027 | Q211 | EVI Voice, Social Capital |
| E069_01–E069_63 | Q64–Q84 | Confidence in Institutions |
| E114 | Q235 | Autocracy Support |
| E115 | Q236 | Autocracy Support |
| E117 | Q238 | Democratic Values |
| E123 | Q240 | Democratic Values |
| F024 | Q173 | Religiosity |
| F025 | Q174 | Religiosity |
| F028 | Q171 | Religiosity |
| F029 | Q172 | Religiosity |
| F034 | Q164 | Traditional/Secular, Religiosity |
| F118 | Q182 | Self-Expression, EVI Choice |
| F120 | Q184 | EVI Choice |
| F121 | Q185 | EVI Choice |
| G006 | Q254 | Traditional/Secular |
| H010 | Q131 | Self-Expression |
| Y001 | — | Post-Materialist (derived) |
| Y002 | — | Post-Materialist 12-item (derived) |
| Y003 | — | EVI Autonomy sub-index (derived) |

---

## 10. Master Summary Table

| Index | Author(s) | Year | Items | Waves | Key Publication |
|---|---|---|---|---|---|
| Traditional/Secular-Rational | Inglehart & Welzel | 2005 | F034, A006, F120, E018, A042, G006 | 1–7 | *Modernization, Cultural Change, and Democracy* |
| Survival/Self-Expression | Inglehart & Welzel | 2005 | Y001, A165, E025, F118, H010 | 1–7 | *Modernization, Cultural Change, and Democracy* |
| Post-Materialist (4-item) | Inglehart | 1971 | E001–E004 | 1–7 | *APSR* 65(4) |
| Emancipative Values Index | Welzel | 2013 | 12 items across 4 sub-indices | 3–7 | *Freedom Rising* |
| Religiosity composite | Norris & Inglehart | 2004 | F034, F028, F029, F024, F025, A006 | 2–7 | *Sacred and Secular* |
| Centrality of Religiosity (CRS approx.) | Huber & Huber | 2012 | F024, F025, F028, F029, F034 | 2–7 | *Religions* 3(3) |
| Confidence in Institutions | WVS / Newton & Norris | 2000 | E069_01–E069_63 | 1–7 | *Disaffected Democracies* |
| Political Trust Index | Zmerli & Newton | 2008 | E069_05, E069_06, E069_17, A165 | 2–7 | *POQ* 72(4) |
| Generalized Trust | Putnam; Delhey & Newton | 2000/2005 | A165 | 1–7 | *Bowling Alone* |
| Autocracy Support | Foa & Mounk | 2016 | E114, E115, E123 | 5–7 | *Journal of Democracy* 27(3) |
| RWA approximation | Cohrs et al.; Funke | 2005 | A042, E018, D059, F063 | 2–7 | *PSPB* 31(10) |
| Gender Egalitarianism | Inglehart & Norris | 2003 | C001, D059, D060, D061 | 2–7 | *Rising Tide* |
| Traditional Gender Norms | Alesina, Giuliano & Nunn | 2013 | C001, D059, D060 | 3–5 | *QJE* 128(2) |
| Social Capital | Bjørnskov | 2006 | A165, A098–A106, E025–E027 | 2–7 | *EJPE* 22(1) |
| Subjective Well-Being | Inglehart et al. | 2008 | A008, A170 | 1–7 | *PPS* 3(4) |
| Environmental Concern | Knight | 2016 | B001–B004 | 3–7 | *Social Forces* 94(3) |
| Liberal Democracy Values Index | Inglehart | 2018 | F118, F120, E025, A029, D059 | 3–7 | *Cultural Evolution* |
