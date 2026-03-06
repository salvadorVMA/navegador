# q7_democracy_corruption

**Query (ES):** ¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?
**Query (EN):** What do Mexicans think about the relationship between democracy and corruption?
**Variables:** p1|CUL, p2|CUL, p3|CUL, p4|CUL, p5|CUL, p2|COR, p3|COR, p5|COR, p8|COR
**Status:** ✅ success
**Time:** 54972ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?

## Summary
Mexican public opinion reveals a generally pessimistic view linking democracy and corruption, with most perceiving corruption as increasing and expecting political conditions to worsen or remain bad. While multiple bivariate associations between perceptions of corruption and political outlook are statistically significant, their strength is weak to moderate, indicating nuanced but not definitive relationships. The evidence quality is based on five significant cross-dataset pairs, supporting cautious confidence in these findings.

## Data Landscape
Eight variables from surveys on political culture and corruption perceptions were analyzed. Among these, three variables show strong consensus (e.g., perceptions of corruption increase), one is polarized (expectations about political future), one is dispersed, and three lean toward one view without strong consensus. The divergence index of 62% indicates substantial variation in opinions, reflecting fragmented and diverse views about democracy and corruption in Mexico.

## Evidence
Cross-tab analyses show that expectations about the political situation next year (p2|CUL) vary weakly but significantly with perceived current corruption levels (p2|COR). For example, when corruption is seen as 'Mayor', 38.1% expect the political situation to worsen, compared to 41.6% when corruption is 'Menor', while the belief that the situation will remain equally bad ranges from 24.8% to 43.8% across corruption perceptions (V=0.066, p=0.038).

| p2|COR category | Va a seguir igual de mal % |
|---|---|
| Mayor | 28.6% |
| Menor | 24.8% |
| Igual (esp.) | 29.5% |
| NS | 43.8% |

Expectations about future corruption (p3|COR) also relate weakly to political outlook (p2|CUL). The share expecting political conditions to worsen ranges from 32.1% when corruption is expected to be 'Menor' to 58.0% among those who do not know (NS), indicating that more negative corruption expectations align with worse political outlook (V=0.084, p=0.000).

| p3|COR category | Va a empeorar % |
|---|---|
| Mayor | 38.4% |
| Menor | 32.1% |
| Igual (esp.) | 41.9% |
| NS | 58.0% |

Perceptions of where corruption occurs (p5|COR) also influence political outlook; those who perceive corruption in the church report the highest pessimism (62.5% say political situation will worsen), while those associating corruption with the family are least pessimistic (30.5%) (V=0.093, p=0.000).

| p5|COR category | Va a empeorar % |
|---|---|
| En la iglesia | 62.5% |
| En el sector privado | 52.3% |
| Otro (esp.) | 60.0% |
| En la familia | 30.5% |

Current political sentiment (p3|CUL) shows a moderate association with future corruption expectations (p3|COR). Negative sentiments like "Peor que antes" rise to 19.0% among those uncertain about corruption trends (NS), compared to only 1.8% among those expecting less corruption (V=0.101, p=0.000).

| p3|COR category | Peor que antes % |
|---|---|
| Mayor | 6.8% |
| Menor | 1.8% |
| Igual (esp.) | 8.3% |
| NS | 19.0% |

Demographically, employment status strongly moderates political sentiment, with some regions and age groups showing notable differences in pessimism and perceptions of corruption increase. For example, younger groups (0-18) are somewhat less likely to perceive corruption as "Mayor" (70%) compared to older groups (35-44 at 79%).

**p2|CUL** — Expectations about political situation next year:
| Response | % |
|---|---|
| Va a empeorar | 37.2% |
| Va a seguir igual de mal | 29.4% |
| Va a mejorar | 17.8% |
| Va a seguir igual de bien | 11.2% |
| No sabe/ No contesta | 3.9% |

**p3|CUL** — Current political situation description:
| Response | % |
|---|---|
| Preocupante | 40.7% |
| Peligrosa | 21.0% |
| Tranquila | 10.8% |
| Prometedora | 8.6% |
| Peor que antes | 8.4% |

**p2|COR** — Corruption compared to childhood:
| Response | % |
|---|---|
| Mayor | 77.0% |
| Igual (esp.) | 14.7% |
| Menor | 6.9% |

**p3|COR** — Corruption expected in 5 years:
| Response | % |
|---|---|
| Mayor | 67.7% |
| Igual (esp.) | 19.3% |
| Menor | 8.2% |

**p5|COR** — Where corruption first occurs:
| Response | % |
|---|---|
| En el gobierno | 51.3% |
| En los partidos políticos | 12.3% |
| En la escuela | 11.8% |
| En la colonia | 7.8% |

## Complications
Employment status is the strongest demographic moderator, with a Cramér's V of 0.32 for political sentiment variables, indicating that working conditions and job security may shape perceptions about democracy and corruption. Regional differences are moderate (V≈0.11-0.14), with some regions more pessimistic than others. Minority views include about 17-22% who expect political conditions to improve or see corruption as stable, challenging the dominant pessimistic narrative. The weak strength of bivariate associations (V mostly below 0.1) limits causal inference and suggests that other unmeasured factors influence opinions. The self-assessed honesty variable (p8|COR) is unusable due to 100% non-response, eliminating a potentially insightful personal integrity perspective. Some expected relationships, like between current political sentiment and perceived corruption levels, are weak or absent (V=0.054, p=0.506), highlighting complexity in public attitudes.

## Implications
First, the weak but significant links between corruption perceptions and political outlook suggest that anti-corruption policies could improve democratic legitimacy if they tangibly reduce corruption or public perceptions thereof. Policymakers should prioritize transparency and accountability reforms, especially targeting institutions perceived as corrupt such as government and political parties. Second, the substantial variation and polarization in opinions imply that communication strategies must be tailored regionally and socioeconomically to address diverse experiences and expectations. Efforts to engage youth and employment sectors may be particularly impactful given their distinct views. Finally, given the data limitations and weak associations, further research should explore additional factors influencing the democracy-corruption nexus, including media influence, trust in institutions, and civic engagement, to design more effective interventions.

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
- sexo: V=0.136 (p=0.034) —  Hombre: 8.0 (32%);  Mujer: 8.0 (31%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p2|CUL × p2|COR | 0.066 (weak) | 0.038 | " Va a seguir igual de mal (esp)": 25% ("Menor") → 44% ("NS") | 2000 |
| p2|CUL × p3|COR | 0.084 (weak) | 0.000 | " Va a empeorar": 32% ("Menor") → 58% ("NS") | 2000 |
| p2|CUL × p5|COR | 0.093 (weak) | 0.000 | " Va a empeorar": 30% ("En la familia") → 62% ("En la iglesia") | 2000 |
| p2|CUL × p8|COR | 0.104 (moderate) | 0.000 | " Va a empeorar": 35% ("8.0") → 69% ("2.0") | 2000 |
| p3|CUL × p2|COR | 0.054 (weak) | 0.506 | " Peligrosa": 6% ("NS") → 21% ("Mayor") | 2000 |
| p3|CUL × p3|COR | 0.101 (moderate) | 0.000 | " Peor que antes   (esp)": 2% ("Menor") → 19% ("NS") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p2|CUL × p2|COR** — How p2|CUL distributes given p2|COR:

| p2|COR (conditioning) | Top p2|CUL responses |
|---|---|
| Mayor |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 29%,  Va a mejorar: 18% |
| Menor |  Va a empeorar: 42%,  Va a seguir igual de mal (esp): 25%,  Va a mejorar: 20% |
| Igual (esp.) |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 30%,  Va a seguir igual de bien (esp): 16% |
| NS |  Va a seguir igual de mal (esp): 44%,  Va a empeorar: 25%,  Va a seguir igual de bien (esp): 19% |

**p2|CUL × p3|COR** — How p2|CUL distributes given p3|COR:

| p3|COR (conditioning) | Top p2|CUL responses |
|---|---|
| Mayor |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 30%,  Va a mejorar: 18% |
| Menor |  Va a empeorar: 32%,  Va a seguir igual de mal (esp): 25%,  Va a mejorar: 23% |
| Igual (esp.) |  Va a empeorar: 42%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 15% |
| NS |  Va a empeorar: 58%,  Va a seguir igual de mal (esp): 31%,  Va a mejorar: 6% |

**p2|CUL × p5|COR** — How p2|CUL distributes given p5|COR:

| p5|COR (conditioning) | Top p2|CUL responses |
|---|---|
| En la escuela |  Va a empeorar: 44%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 21% |
| En la colonia |  Va a empeorar: 40%,  Va a seguir igual de mal (esp): 37%,  Va a mejorar: 12% |
| En el trabajo |  Va a empeorar: 33%,  Va a seguir igual de mal (esp): 29%,  Va a seguir igual de bien (esp): 20% |
| En el gobierno |  Va a empeorar: 36%,  Va a seguir igual de mal (esp): 32%,  Va a mejorar: 17% |
| En el sector privado |  Va a empeorar: 52%,  Va a seguir igual de mal (esp): 34%,  Va a mejorar: 9% |
| En la iglesia |  Va a empeorar: 62%,  Va a seguir igual de mal (esp): 38%,  Va a mejorar: 0% |
| En la familia |  Va a empeorar: 30%,  Va a seguir igual de mal (esp): 30%,  Va a mejorar: 23% |
| En los partidos políticos |  Va a empeorar: 46%,  Va a seguir igual de mal (esp): 23%,  Va a seguir igual de bien (esp): 14% |

**p2|CUL × p8|COR** — How p2|CUL distributes given p8|COR:

| p8|COR (conditioning) | Top p2|CUL responses |
|---|---|
| 0.0 |  Va a seguir igual de mal (esp): 44%,  Va a empeorar: 36%,  Va a mejorar: 8% |
| 2.0 |  Va a empeorar: 69%,  Va a seguir igual de mal (esp): 25%,  Va a seguir igual de bien (esp): 6% |
| 3.0 |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 23%,  Va a mejorar: 15% |
| 5.0 |  Va a empeorar: 58%,  Va a seguir igual de mal (esp): 24%,  Va a mejorar: 12% |
| 6.0 |  Va a empeorar: 59%,  Va a seguir igual de mal (esp): 27%,  Va a mejorar: 9% |
| 7.0 |  Va a empeorar: 36%,  Va a seguir igual de mal (esp): 28%,  Va a mejorar: 20% |
| 8.0 |  Va a empeorar: 35%,  Va a seguir igual de mal (esp): 34%,  Va a mejorar: 15% |
| 9.0 |  Va a empeorar: 47%,  Va a seguir igual de mal (esp): 22%,  Va a mejorar: 16% |

**p3|CUL × p2|COR** — How p3|CUL distributes given p2|COR:

| p2|COR (conditioning) | Top p3|CUL responses |
|---|---|
| Mayor |  Preocupante: 46%,  Peligrosa: 21%,  Tranquila: 8% |
| Menor |  Preocupante: 58%,  Peligrosa: 13%,  Tranquila: 10% |
| Igual (esp.) |  Preocupante: 46%,  Peligrosa: 20%,  Tranquila: 9% |
| NS |  Preocupante: 61%,  Prometedora: 11%,  Tranquila: 11% |

**p3|CUL × p3|COR** — How p3|CUL distributes given p3|COR:

| p3|COR (conditioning) | Top p3|CUL responses |
|---|---|
| Mayor |  Preocupante: 47%,  Peligrosa: 23%,  Tranquila: 9% |
| Menor |  Preocupante: 39%,  Peligrosa: 26%,  Más o menos (esp): 14% |
| Igual (esp.) |  Preocupante: 50%,  Peligrosa: 18%,  Tranquila: 8% |
| NS |  Preocupante: 40%,  Peor que antes   (esp): 19%,  Peligrosa: 15% |
### Bridge Model Diagnostics

> For human inspection only — not passed to the LLM.

#### Summary

| Variable | Model | Pseudo-R² | LLR p | Dominant SES | Quality |
|----------|-------|-----------|-------|--------------|---------|
| p2|COR | mnlogit | 0.122 | 0.297 | region | weak |
| p2|CUL | mnlogit | 0.175 | 0.096 | est_civil | fair |
| p3|COR | mnlogit | 0.124 | 0.117 | edad | weak |
| p3|CUL | mnlogit | 0.181 | 0.109 | Tam_loc | weak |
| p5|COR | mnlogit | 0.150 | 0.459 | Tam_loc | weak |
| p8|COR | mnlogit | 0.137 | 0.806 | sexo | weak |

**Mean pseudo-R²:** 0.148 &ensp;|&ensp; **Overall dominant SES dimension:** Tam_loc

> ⚠ 5/6 bridge models are weak (R²<0.02 or LLR p≥0.10). Simulated Cramér's V for those variables may underestimate the true association.

#### Per-Variable SES Predictor Detail

Top predictors by |t|-statistic — answers: which SES variable is doing the work?

**p2|COR** (mnlogit, R²=0.122, LLR p=0.297, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_03 | 0.799 | 2.242 | 1.753 | 0.080 |
| Tam_loc | -0.877 | 1.638 | -1.709 | 0.088 |
| region_02 | 1.297 | 1.870 | 1.672 | 0.095 |
| sexo | 0.145 | 1.338 | -1.581 | 0.114 |
| region_04 | -0.058 | 3.592 | 1.557 | 0.120 |
| edad | -1.047 | 0.888 | -1.280 | 0.201 |

**p2|CUL** (mnlogit, R²=0.175, LLR p=0.096, quality=fair)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| est_civil_6.0 | -0.972 | 3.651 | -2.651 | 0.008 |
| region_02 | 0.652 | 2.130 | 2.337 | 0.019 |
| region_04 | 0.485 | 3.000 | 2.133 | 0.033 |
| sexo | 0.470 | 1.826 | 2.115 | 0.034 |
| region_03 | 0.994 | 2.149 | 1.553 | 0.121 |
| edad | 0.185 | 0.702 | -1.374 | 0.169 |

**p3|COR** (mnlogit, R²=0.124, LLR p=0.117, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| edad | 0.150 | 0.344 | 2.242 | 0.025 |
| region_04 | -0.002 | 1.929 | 2.080 | 0.038 |
| est_civil_2.0 | 0.055 | 1.512 | 1.977 | 0.048 |
| region_02 | 0.988 | 1.097 | 1.928 | 0.054 |
| Tam_loc | -0.854 | 1.832 | 1.513 | 0.130 |
| est_civil_6.0 | -0.590 | 1.162 | 1.464 | 0.143 |

**p3|CUL** (mnlogit, R²=0.181, LLR p=0.109, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| Tam_loc | -0.535 | 0.664 | -2.061 | 0.039 |
| empleo_03 | 0.798 | 1.435 | 1.820 | 0.069 |
| region_02 | 0.503 | 1.670 | 1.555 | 0.120 |
| sexo | 0.285 | 1.014 | 1.399 | 0.162 |
| est_civil_6.0 | -0.758 | 1.646 | -1.349 | 0.177 |
| region_03 | 0.921 | 2.532 | 1.320 | 0.187 |

**p5|COR** (mnlogit, R²=0.150, LLR p=0.459, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| Tam_loc | 0.044 | 1.502 | 2.579 | 0.010 |
| region_03 | 0.442 | 2.015 | 1.896 | 0.058 |
| edad | 0.121 | 0.623 | 1.631 | 0.103 |
| sexo | 0.250 | 1.128 | -1.582 | 0.114 |
| region_04 | -0.341 | 1.710 | -1.475 | 0.140 |
| est_civil_6.0 | -0.387 | 1.508 | -1.279 | 0.201 |

**p8|COR** (mnlogit, R²=0.137, LLR p=0.806, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| sexo | 0.321 | 2.680 | 1.318 | 0.188 |
| Tam_loc | -0.872 | 1.922 | -0.967 | 0.334 |
| edad | 0.305 | 1.138 | -0.964 | 0.335 |
| region_04 | -0.236 | 3.559 | 0.864 | 0.388 |
| region_02 | 0.208 | 3.503 | 0.856 | 0.392 |
| est_civil_6.0 | -0.159 | 4.214 | 0.823 | 0.411 |

*Pseudo-R² = McFadden's. Low values mean SES explains little variance in that variable — the bridge simulation still produces an estimate, but its precision is reduced.*

### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from cross-dataset bivariate associations with significant p-values, especially those linking political outlook variables (p2|CUL, p3|CUL) with corruption perception variables (p2|COR, p3|COR, p5|COR). Demographic fault lines provide secondary evidence about group differences but do not directly address the relationship between democracy and corruption. Univariate distributions offer contextual background but cannot establish relationships alone.

**Key Limitations:**
- All cross-dataset associations are weak to moderate in strength, limiting explanatory power.
- Some variables (e.g., p8|COR) have data quality issues (100% no response), reducing their utility.
- Only a limited number of variable pairs from different surveys are available for bivariate analysis, restricting comprehensive assessment.
- Estimates are simulation-based, which may introduce uncertainty in significance and effect size interpretation.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p4|CUL
- **Dispersed Variables:** p2|CUL

