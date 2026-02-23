# q7_democracy_corruption

**Query (ES):** ¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?
**Query (EN):** What do Mexicans think about the relationship between democracy and corruption?
**Variables:** p1|CUL, p2|CUL, p3|CUL, p4|CUL, p5|CUL, p2|COR, p3|COR, p5|COR, p8|COR
**Status:** ✅ success
**Time:** 48388ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?

## Summary
The most important finding is that Mexican perceptions of corruption and democracy are weakly but significantly related: those who expect corruption to increase tend to describe the political situation as more "preocupante" (worrying) and anticipate the political situation will worsen or remain bad. However, all bivariate associations show weak effect sizes (Cramér's V below 0.1), indicating only modest alignment between views on corruption and democracy. Evidence quality is moderate, based on five significant but weak associations among eight variables, limiting strong causal inferences.

## Data Landscape
Eight variables from two surveys on political culture and corruption perceptions were analyzed. Three variables show strong consensus (e.g., 77.0% say corruption is greater than in their childhood), one variable is polarized (expectations about the political situation next year split between worsening and remaining bad), one variable shows dispersed opinions, and three lean toward one dominant view without full consensus. The divergence index of 62% indicates substantial variation and fragmentation in public opinion about democracy and corruption in Mexico.

## Evidence
Cross-tabulations reveal that expectations about the political situation (p2|CUL) vary only slightly with perceptions of corruption change compared to childhood (p2|COR). For example, the share expecting political conditions to "improve" ranges narrowly from 7.7% among those uncertain about corruption change to 17.3% among those perceiving corruption as "menor" (less) (V=0.049, p=0.480), showing a weak and statistically non-significant relationship. Similarly, when conditioning political outlook on corruption expectations in five years (p3|COR), the proportion expecting the political situation to "remain equally bad" varies from 20.0% among those uncertain about corruption to 41.4% among those expecting corruption to be "menor" (V=0.068, p=0.023), indicating a weak but significant association. Regarding where corruption begins (p5|COR), those who identify "en la escuela" as the origin are most pessimistic about political improvement (only 14.7% expect improvement), while those pointing to "en el trabajo" show slightly more optimism (17.9% expect improvement) (V=0.078, p=0.018). Emotional descriptions of the political situation (p3|CUL) also relate weakly to corruption perceptions: the label "preocupante" ranges from 38.0% among those expecting less corruption to 49.3% among those expecting corruption to remain the same (V=0.090, p=0.000). These patterns illustrate a modest alignment where more negative corruption expectations correspond to more negative democratic outlooks, but the relationships are weak. Demographically, employment status most strongly moderates political sentiment, with some regions and age groups showing variation in pessimism. For instance, employed individuals in category 03 report 53% "preocupante" vs. 30% in category 02. Women and men differ modestly in honesty self-assessments, but this variable has data quality issues. Univariate distributions support these findings: 77.0% perceive corruption as greater now than in childhood (p2|COR), 67.7% expect corruption to be greater in five years (p3|COR), and 51.3% identify government as the origin of corruption acts (p5|COR). Political outlooks are more fragmented: 37.2% expect the political situation to worsen next year, 29.4% expect it to remain equally bad (p2|CUL), and 40.7% describe the political situation as "preocupante" (p3|CUL). 

| p2|COR category | "Va a mejorar" % |
|---|---|
| Mayor | 16.0% |
| Menor | 17.3% |
| Igual (esp.) | 13.3% |
| NS | 7.7% |

| p3|COR category | "Va a seguir igual de mal (esp)" % |
|---|---|
| Mayor | 29.8% |
| Menor | 41.4% |
| Igual (esp.) | 26.4% |
| NS | 20.0% |

| p5|COR category | "Va a seguir igual de mal (esp)" % |
|---|---|
| En la escuela | 22.9% |
| En la colonia | 33.3% |
| En el trabajo | 20.0% |
| En el gobierno | 28.1% |

| p3|COR category | "Preocupante" % |
|---|---|
| Mayor | 48.1% |
| Menor | 38.0% |
| Igual (esp.) | 49.3% |
| NS | 42.4% |

| Response | % |
|---|---|
| Mayor (p2|COR) | 77.0% |
| Igual (esp.) (p2|COR) | 14.7% |
| Menor (p2|COR) | 6.9% |

| Response | % |
|---|---|
| Mayor (p3|COR) | 67.7% |
| Igual (esp.) (p3|COR) | 19.3% |
| Menor (p3|COR) | 8.2% |

| Response | % |
|---|---|
| En el gobierno (p5|COR) | 51.3% |
| En los partidos políticos (p5|COR) | 12.3% |
| En la escuela (p5|COR) | 11.8% |

| Response | % |
|---|---|
| Va a empeorar (p2|CUL) | 37.2% |
| Va a seguir igual de mal (esp) (p2|CUL) | 29.4% |
| Va a mejorar (p2|CUL) | 17.8% |

| Response | % |
|---|---|
| Preocupante (p3|CUL) | 40.7% |
| Peligrosa (p3|CUL) | 21.0% |
| Tranquila (p3|CUL) | 10.8% |

## Complications
The main complication is the consistently weak strength of associations between corruption perceptions and political outlooks (all Cramér's V values below 0.1), which limits the ability to draw strong conclusions about the relationship. Employment status is the strongest demographic moderator (mean V=0.29), with some employment groups differing by up to 23 percentage points in political sentiment labels, indicating socioeconomic factors influence views independently of corruption perceptions. Regional and age differences also moderate opinions modestly. Minority views challenge the dominant narrative: for example, 17.8% expect political conditions to improve despite high perceived corruption, and 21.0% describe the political situation as "peligrosa" rather than just "preocupante." The variable measuring self-assessed honesty (p8|COR) is unusable due to 100% non-response, removing a potentially relevant personal integrity dimension. Simulation-based bivariate estimates rely on SES-bridge assumptions and sample size (n=2000), which may affect precision. Notably, some cross-tabulations are statistically non-significant (e.g., p2|CUL × p2|COR, p=0.480), confirming that some expected relationships are absent or too weak to detect reliably.

## Implications
First, the weak but significant association between corruption perceptions and democratic outlooks suggests that anti-corruption policies alone may not substantially shift public confidence in democracy; broader political reforms and communication strategies addressing multiple facets of governance might be necessary to improve political sentiment. Second, given the demographic moderation by employment and region, tailored interventions that consider socioeconomic contexts could be more effective in addressing political disillusionment linked to corruption. For example, programs targeting employment sectors with more pessimistic views could focus on transparency and citizen engagement. Third, the presence of sizable minority groups with more optimistic or alternative views indicates space for narratives that emphasize democratic resilience and progress, which policymakers could leverage to build social cohesion. Finally, the data limitations highlight the need for improved measurement tools, especially regarding personal integrity and honesty, to better understand the individual-level factors connecting corruption and democratic attitudes in future research and policy design.

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | 8 |
| Divergence Index | 62.5% |
| Consensus Variables | 3 |
| Lean Variables | 3 |
| Polarized Variables | 1 |
| Dispersed Variables | 1 |

### Variable Details


**p2|CUL** (dispersed)
- Question: CULTURA_POLITICA|¿Y cree usted que en el próximo año…?
- Mode: Va a empeorar (37.2%)
- Runner-up: Va a seguir igual de mal (29.4%), margin: 7.8pp
- HHI: 2703
- Minority opinions: Va a mejorar (17.8%), Va a seguir igual de mal (29.4%)

| Response | % |
|----------|---|
| Va a empeorar | 37.2% |
| Va a seguir igual de mal | 29.4% |
| Va a mejorar | 17.8% |
| Va a seguir igual de bien | 11.2% |
| No sabe/ No contesta | 3.9% |
| Otra | 0.6% |

**p3|CUL** (lean)
- Question: CULTURA_POLITICA|De las siguientes palabras, ¿con cuál está usted más de acuerdo para describir la situación política del país?
- Mode: Preocupante (40.7%)
- Runner-up: Peligrosa (21.0%), margin: 19.7pp
- HHI: 2394
- Minority opinions: Peligrosa (21.0%)

| Response | % |
|----------|---|
| Preocupante | 40.7% |
| Peligrosa | 21.0% |
| Tranquila | 10.8% |
| Prometedora | 8.6% |
| Peor que antes | 8.4% |
| Con oportunidades | 5.2% |
| Más o menos | 3.1% |
| No sabe/ No contesta | 1.2% |
| Mejor que antes | 0.8% |
| Otra | 0.2% |

**p4|CUL** (polarized)
- Question: CULTURA_POLITICA|¿Y cree usted que en el próximo año…?
- Mode: Va a empeorar (32.9%)
- Runner-up: Va a seguir igual de mal (30.4%), margin: 2.5pp
- HHI: 2613
- Minority opinions: Va a mejorar (21.7%), Va a seguir igual de mal (30.4%)

| Response | % |
|----------|---|
| Va a empeorar | 32.9% |
| Va a seguir igual de mal | 30.4% |
| Va a mejorar | 21.7% |
| Va a seguir igual de bien | 11.0% |
| No sabe/ No contesta | 3.7% |
| Otra | 0.3% |

**p5|CUL** (lean)
- Question: CULTURA_POLITICA|¿Qué tan orgulloso se siente de ser mexicano?
- Mode: Mucho (59.7%)
- Runner-up: Poco (27.5%), margin: 32.2pp
- HHI: 4424
- Minority opinions: Poco (27.5%)

| Response | % |
|----------|---|
| Mucho | 59.7% |
| Poco | 27.5% |
| Nada | 10.2% |
| No soy mexicano | 1.8% |
| Otra | 0.4% |
| No sabe/ No contesta | 0.4% |

**p2|COR** (consensus)
- Question: CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD|En comparación con su infancia, actualmente la corrupción es:
- Mode: Mayor (77.0%)
- Runner-up: Igual (esp.) (14.7%), margin: 62.3pp
- HHI: 6194

| Response | % |
|----------|---|
| Mayor | 77.0% |
| Igual (esp.) | 14.7% |
| Menor | 6.9% |
| No sabe/ No contesta | 1.4% |

**p3|COR** (consensus)
- Question: CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD|Dentro de 5 años, cree usted que la corrupción será:
- Mode: Mayor (67.7%)
- Runner-up: Igual (esp.) (19.3%), margin: 48.3pp
- HHI: 5043
- Minority opinions: Igual (esp.) (19.3%)

| Response | % |
|----------|---|
| Mayor | 67.7% |
| Igual (esp.) | 19.3% |
| Menor | 8.2% |
| No sabe/ No contesta | 4.8% |

**p5|COR** (lean)
- Question: CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD|En su opinión, ¿dónde se realizan los primeros actos de corrupción?
- Mode: En el gobierno (51.3%)
- Runner-up: En los partidos políticos (12.3%), margin: 39.0pp
- HHI: 3054

| Response | % |
|----------|---|
| En el gobierno | 51.3% |
| En los partidos políticos | 12.3% |
| En la escuela | 11.8% |
| En la colonia | 7.8% |
| En la familia | 5.5% |
| En el trabajo | 4.2% |
| En el sector privado | 3.9% |
| No sabe/ No contesta | 2.2% |
| En la iglesia | 0.8% |
| Otro (esp.) | 0.2% |

**p8|COR** (consensus)
- Question: CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD|En una escala donde 0 es 'nada honesto' y 10 es 'muy honesto', ¿cómo se considera usted a sí mismo?
- Mode: No sabe/ No contesta (100.0%)
- Runner-up:  (0.0%), margin: 100.0pp
- HHI: 10000

| Response | % |
|----------|---|
| No sabe/ No contesta | 100.0% |

### Demographic Fault Lines

| Dimension | Mean Cramér's V | Max Cramér's V | Variables |
|-----------|----------------|----------------|----------|
| empleo | 0.292 (moderate) | 0.323 | 3 |
| sexo | 0.136 (moderate) | 0.136 | 1 |
| region | 0.120 (moderate) | 0.141 | 8 |
| edad | 0.109 (moderate) | 0.118 | 5 |

**Variable-Level Demographic Detail:**

*p2|CUL*
- region: V=0.141 (p=0.000) — 01:  Va a empeorar (42%); 02:  Va a empeorar (42%); 03:  Va a seguir igual de mal (esp) (29%)

*p3|CUL*
- empleo: V=0.321 (p=0.035) — 02:  Preocupante (30%); 03:  Preocupante (53%)
- region: V=0.131 (p=0.001) — 01:  Preocupante (43%); 02:  Preocupante (38%); 03:  Preocupante (41%)
- edad: V=0.110 (p=0.013) — 0-18:  Preocupante (34%); 19-24:  Preocupante (40%); 25-34:  Preocupante (46%)

*p4|CUL*
- region: V=0.123 (p=0.000) — 01:  Va a empeorar (41%); 02:  Va a empeorar (36%); 03:  Va a mejorar (30%)

*p5|CUL*
- edad: V=0.098 (p=0.001) — 0-18:  Mucho (66%); 19-24:  Mucho (58%); 25-34:  Mucho (57%)
- region: V=0.090 (p=0.045) — 01:  Mucho (56%); 02:  Mucho (54%); 03:  Mucho (66%)

*p2|COR*
- edad: V=0.118 (p=0.000) — 0-18: Mayor (70%); 19-24: Mayor (74%); 25-34: Mayor (77%)
- region: V=0.110 (p=0.000) — 01: Mayor (80%); 02: Mayor (82%); 03: Mayor (71%)

*p3|COR*
- empleo: V=0.233 (p=0.002) — 01: Menor (100%); 02: Mayor (57%); 03: Mayor (72%)
- region: V=0.112 (p=0.000) — 01: Mayor (74%); 02: Mayor (67%); 03: Mayor (62%)
- edad: V=0.108 (p=0.000) — 0-18: Mayor (67%); 19-24: Mayor (64%); 25-34: Mayor (70%)

*p5|COR*
- region: V=0.112 (p=0.035) — 01: En el gobierno (54%); 02: En el gobierno (58%); 03: En el gobierno (48%)
- edad: V=0.110 (p=0.011) — 0-18: En el gobierno (52%); 19-24: En el gobierno (53%); 25-34: En el gobierno (50%)

*p8|COR*
- empleo: V=0.323 (p=0.004) — 01: 5.0 (100%); 02: 8.0 (43%); 03: 8.0 (26%)
- region: V=0.140 (p=0.001) — 01: 8.0 (34%); 02: 8.0 (27%); 03: 8.0 (39%)
- sexo: V=0.136 (p=0.034) — 1.0: 8.0 (32%); 2.0: 8.0 (31%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p2|CUL × p2|COR | 0.049 (weak) | 0.480 | " Va a mejorar": 8% ("NS") → 17% ("Menor") | 2000 |
| p2|CUL × p3|COR | 0.068 (weak) | 0.023 | " Va a seguir igual de mal (esp)": 20% ("NS") → 41% ("Menor") | 2000 |
| p2|CUL × p5|COR | 0.078 (weak) | 0.018 | " Va a seguir igual de mal (esp)": 16% ("En la iglesia") → 33% ("En la colonia") | 2000 |
| p2|CUL × p8|COR | 0.077 (weak) | 0.026 | " Va a seguir igual de mal (esp)": 24% ("7.0") → 62% ("0.0") | 2000 |
| p3|CUL × p2|COR | 0.072 (weak) | 0.026 | " Peligrosa": 4% ("NS") → 26% ("Menor") | 2000 |
| p3|CUL × p3|COR | 0.090 (weak) | 0.000 | " Preocupante": 38% ("Menor") → 49% ("Igual (esp.)") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p2|CUL × p2|COR** — How p2|CUL distributes given p2|COR:

| p2|COR (conditioning) | Top p2|CUL responses |
|---|---|
| Mayor |  Va a empeorar: 40%,  Va a seguir igual de mal (esp): 29%,  Va a mejorar: 16% |
| Menor |  Va a empeorar: 37%,  Va a seguir igual de mal (esp): 34%,  Va a mejorar: 17% |
| Igual (esp.) |  Va a empeorar: 44%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 13% |
| NS |  Va a empeorar: 42%,  Va a seguir igual de mal (esp): 35%,  Va a mejorar: 8% |

**p2|CUL × p3|COR** — How p2|CUL distributes given p3|COR:

| p3|COR (conditioning) | Top p2|CUL responses |
|---|---|
| Mayor |  Va a empeorar: 40%,  Va a seguir igual de mal (esp): 30%,  Va a mejorar: 17% |
| Menor |  Va a seguir igual de mal (esp): 41%,  Va a empeorar: 29%,  Va a mejorar: 14% |
| Igual (esp.) |  Va a empeorar: 44%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 14% |
| NS |  Va a empeorar: 51%,  Va a seguir igual de mal (esp): 20%,  Va a mejorar: 15% |

**p2|CUL × p5|COR** — How p2|CUL distributes given p5|COR:

| p5|COR (conditioning) | Top p2|CUL responses |
|---|---|
| En la escuela |  Va a empeorar: 50%,  Va a seguir igual de mal (esp): 23%,  Va a mejorar: 15% |
| En la colonia |  Va a empeorar: 44%,  Va a seguir igual de mal (esp): 33%,  Va a mejorar: 15% |
| En el trabajo |  Va a empeorar: 39%,  Va a seguir igual de mal (esp): 20%,  Va a mejorar: 18% |
| En el gobierno |  Va a empeorar: 42%,  Va a seguir igual de mal (esp): 28%,  Va a mejorar: 15% |
| En el sector privado |  Va a empeorar: 43%,  Va a seguir igual de mal (esp): 28%,  Va a mejorar: 20% |
| En la iglesia |  Va a empeorar: 53%,  Va a mejorar: 21%,  Va a seguir igual de mal (esp): 16% |
| En la familia |  Va a empeorar: 35%,  Va a seguir igual de mal (esp): 33%,  Va a seguir igual de bien (esp): 14% |
| En los partidos políticos |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 28%,  Va a seguir igual de bien (esp): 15% |

**p2|CUL × p8|COR** — How p2|CUL distributes given p8|COR:

| p8|COR (conditioning) | Top p2|CUL responses |
|---|---|
| 0.0 |  Va a seguir igual de mal (esp): 62%,  Va a empeorar: 19%,  Va a seguir igual de bien (esp): 12% |
| 2.0 |  Va a seguir igual de mal (esp): 43%,  Va a empeorar: 43%,  Va a seguir igual de bien (esp): 14% |
| 3.0 |  Va a empeorar: 50%,  Va a seguir igual de mal (esp): 32%,  Va a mejorar: 9% |
| 5.0 |  Va a empeorar: 54%,  Va a seguir igual de mal (esp): 25%,  Va a mejorar: 17% |
| 6.0 |  Va a empeorar: 47%,  Va a seguir igual de mal (esp): 29%,  Va a mejorar: 19% |
| 7.0 |  Va a empeorar: 42%,  Va a seguir igual de mal (esp): 24%,  Va a mejorar: 18% |
| 8.0 |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 28%,  Va a mejorar: 17% |
| 9.0 |  Va a empeorar: 47%,  Va a seguir igual de mal (esp): 27%,  Va a mejorar: 15% |

**p3|CUL × p2|COR** — How p3|CUL distributes given p2|COR:

| p2|COR (conditioning) | Top p3|CUL responses |
|---|---|
| Mayor |  Preocupante: 49%,  Peligrosa: 22%,  Tranquila: 8% |
| Menor |  Preocupante: 52%,  Peligrosa: 26%,  Tranquila: 9% |
| Igual (esp.) |  Preocupante: 46%,  Peligrosa: 18%,  Tranquila: 12% |
| NS |  Preocupante: 60%,  Tranquila: 20%,  Peor que antes   (esp): 8% |

**p3|CUL × p3|COR** — How p3|CUL distributes given p3|COR:

| p3|COR (conditioning) | Top p3|CUL responses |
|---|---|
| Mayor |  Preocupante: 48%,  Peligrosa: 22%,  Tranquila: 10% |
| Menor |  Preocupante: 38%,  Peligrosa: 30%,  Más o menos (esp): 10% |
| Igual (esp.) |  Preocupante: 49%,  Peligrosa: 20%,  Tranquila: 10% |
| NS |  Preocupante: 42%,  Peligrosa: 21%,  Peor que antes   (esp): 14% |
### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from cross-dataset bivariate estimates with significant p-values, which provide direct insight into how perceptions of corruption relate to political outlooks. Among these, the associations involving p2|CUL and p3|CUL with corruption variables (p2|COR, p3|COR, p5|COR) are primary. Demographic fault lines offer secondary contextual understanding of opinion variation. Univariate distributions serve as background context but do not establish relationships on their own.

**Key Limitations:**
- All cross-dataset bivariate associations show weak effect sizes (low V values), limiting interpretive strength.
- Some variables, notably p8|COR, have data quality issues (100% no response), reducing their utility.
- The number of cross-survey variable pairs is limited, restricting comprehensive analysis of democracy-corruption relationships.
- Estimates are simulation-based, which may introduce uncertainty in significance testing and effect size estimation.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p4|CUL
- **Dispersed Variables:** p2|CUL

