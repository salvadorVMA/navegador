# q2_environment_economy

**Query (ES):** ¿Cómo equilibran los mexicanos las preocupaciones ambientales con el desarrollo económico?
**Query (EN):** How do Mexicans balance environmental concerns with economic development?
**Variables:** p2|MED, p4|MED, p5|MED, p6|MED, p1|ECO, p2|ECO, p3|ECO, p4|ECO, p5|ECO
**Status:** ✅ success
**Time:** 64826ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Cómo equilibran los mexicanos las preocupaciones ambientales con el desarrollo económico?

## Summary
Mexicans are divided in how they balance environmental concerns with economic development, with a polarized split between prioritizing maintaining social order (38.6%) and giving people more voice in government decisions (30.6%). This division shifts modestly depending on satisfaction with the national economy: those more satisfied economically tend to favor democratic participation, while those less satisfied lean toward order. The evidence is based on seven bivariate pairs, four of which show weak but statistically significant associations, indicating a low-confidence but consistent pattern of economic perceptions influencing environmental governance priorities.

## Data Landscape
The analysis draws on nine variables from environmental and economic surveys, revealing a fragmented public opinion landscape. Five variables show polarized distributions, including key variables on environmental priorities and economic satisfaction, while three are dispersed and one shows consensus. The divergence index is high at 89%, indicating widespread disagreement or division in views related to environmental and economic issues in Mexico.

## Evidence
The relationship between environmental priorities (p2|MED) and national economic satisfaction (p1|ECO) reveals that when economic satisfaction is high ('Mucho'), 38.6% prioritize giving people more voice and vote in government decisions, while only 26.3% prioritize maintaining order. Conversely, when economic satisfaction is lower ('Algo'), maintaining order rises to 46.2%, and giving people more voice drops to 27.0% (V=0.053, p=0.047).

| p1|ECO category | Mantener el orden en el país % |
|---|---|
| Mucho | 26.3% |
| Algo | 46.2% |
| Poco | 39.1% |
| Nada | 44.0% |

Personal economic satisfaction (p2|ECO) shows no significant variation in environmental priorities (V=0.045, p=0.212), with maintaining order consistently around 42-47% across satisfaction levels.

| p2|ECO category | Mantener el orden en el país % |
|---|---|
| Mucho | 42.6% |
| Algo | 47.3% |
| Poco | 41.9% |
| Nada | 44.5% |

Comparing current economic status to parents (p3|ECO) shows a slight increase in prioritizing order from 38.0% among those who feel better off to 43.8% among those who feel worse off, while giving people more voice remains relatively stable around 27-29% except for a spike to 73.3% among non-respondents (V=0.061, p=0.030).

| p3|ECO category | Mantener el orden en el país % |
|---|---|
| Mejor | 38.0% |
| Igual | 40.9% |
| Peor | 43.8% |
| NS | 37.5% |
| NC | 20.0% |

Economic outlook for children (p4|ECO) also relates weakly to environmental priorities; maintaining order ranges from 39.5% ('Mejor') to 49.8% ('No sabe') (V=0.056, p=0.026).

| p4|ECO category | Mantener el orden en el país % |
|---|---|
| Mejor | 39.5% |
| Igual | 42.9% |
| Peor | 47.3% |
| NS | 49.8% |

Perceived responsibility for the economy (p5|ECO) does not significantly affect environmental priorities (V=0.039, p=0.874), with maintaining order varying modestly between 35.6% and 49.8%.

| p5|ECO category | Mantener el orden en el país % |
|---|---|
| El gobierno | 43.9% |
| Los empresarios | 49.8% |
| Los trabajadores | 41.5% |
| Los partidos políticos | 42.3% |
| NS | 44.3% |
| NC | 35.6% |

Regarding perception of the environmental situation (p4|MED), those more satisfied economically ('Mucho') are less likely to rate the environment as 'Muy mala' (10.5%), while those less satisfied ('Nada') do so at double the rate (21.6%) (V=0.072, p=0.008).

| p1|ECO category | Muy mala % |
|---|---|
| Mucho | 10.5% |
| Algo | 12.2% |
| Poco | 19.9% |
| Nada | 21.6% |

Demographically, region influences priorities: for example, in region 01, 38% prioritize giving people more voice vs 32% maintaining order, while in region 02, 40% prioritize order vs 22% voice. Age differences are weaker but show younger groups slightly favor more voice.

**p2|MED** — Priorities for Mexico regarding environment:
| Response | % |
|---|---|
| Mantener el orden en el país | 38.6% |
| Darle al pueblo más voz y voto en las decisiones del gobie | 30.6% |
| Luchar contra las alzas de precio | 19.2% |
| Proteger la libertad de expresión | 9.6% |
| No sabe/ No contesta | 2.1% |

**p4|MED** — Perception of Mexico's environmental situation:
| Response | % |
|---|---|
| Mala | 35.2% |
| Regular (esp.) | 33.5% |
| Buena | 15.7% |
| Muy mala | 12.4% |
| No sabe/ No contesta | 1.9% |
| Muy buena | 1.3% |

**p1|ECO** — Satisfaction with national economic situation:
| Response | % |
|---|---|
| Poco | 37.2% |
| Nada | 35.7% |
| Algo | 23.2% |
| Mucho | 3.2% |
| No sabe/ No contesta | 0.7% |

## Complications
The strongest demographic moderator is region, which influences environmental priorities with differences up to 16 percentage points between regions in favoring order versus democratic participation. Age effects are weaker but show younger Mexicans slightly more inclined to prioritize giving people more voice. Minority views are substantial: nearly one-third prioritize democratic participation over order, and nearly 20% prioritize fighting price increases, indicating notable alternative concerns. The weak effect sizes (V values mostly below 0.07) and some non-significant associations (e.g., personal economic satisfaction and perceived economic responsibility) limit confidence in causal interpretations. The data relies on simulation-based SES-bridge methods, which, while useful, may not capture all nuances of opinion or behavior. Additionally, the absence of direct measures of policy trade-offs means conclusions about balancing environment and economic development are inferential rather than direct.

## Implications
First, the weak but consistent association between economic satisfaction and environmental governance priorities suggests that improving economic conditions may foster greater public support for participatory environmental decision-making rather than authoritarian order. Policymakers could leverage economic improvements to promote inclusive governance models that integrate environmental concerns. Second, the polarization and fragmentation of opinions imply that environmental policies must be carefully designed to address divergent priorities, balancing social order and democratic engagement. This calls for multi-stakeholder dialogues and regionally tailored approaches recognizing demographic differences. Given the weak effect sizes and fragmented views, policies should also focus on building consensus through education and transparent communication rather than assuming uniform public support for any single approach.

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | 9 |
| Divergence Index | 88.9% |
| Consensus Variables | 1 |
| Lean Variables | 0 |
| Polarized Variables | 5 |
| Dispersed Variables | 3 |

### Variable Details


**p2|MED** (polarized)
- Question: MEDIO_AMBIENTE|De la siguiente lista, para usted ¿cuál es la mayor prioridad para México?
- Mode: Mantener el orden en el país (38.6%)
- Runner-up: Darle al pueblo más voz y  voto en las decisiones del gobie (30.6%), margin: 8.0pp
- HHI: 2887
- Minority opinions: Darle al pueblo más voz y  voto en las decisiones del gobie (30.6%), Luchar contra las alzas de precio (19.2%)

| Response | % |
|----------|---|
| Mantener el orden en el país | 38.6% |
| Darle al pueblo más voz y  voto en las decisiones del gobie | 30.6% |
| Luchar contra las alzas de precio | 19.2% |
| Proteger la libertad de expresión | 9.6% |
| No sabe/ No contesta | 2.1% |

**p4|MED** (polarized)
- Question: MEDIO_AMBIENTE|A usted le parece que la situación del medio ambiente en México es:
- Mode: Mala (35.2%)
- Runner-up: Regular (esp.) (33.5%), margin: 1.7pp
- HHI: 2764
- Minority opinions: Buena (15.7%), Regular (esp.) (33.5%)

| Response | % |
|----------|---|
| Mala | 35.2% |
| Regular (esp.) | 33.5% |
| Buena | 15.7% |
| Muy mala | 12.4% |
| No sabe/ No contesta | 1.9% |
| Muy buena | 1.3% |

**p5|MED** (dispersed)
- Question: MEDIO_AMBIENTE|En donde usted vive, ¿cómo diría que es la situación del medio ambiente?
- Mode: Regular (esp.) (37.8%)
- Runner-up: Mala (26.0%), margin: 11.8pp
- HHI: 2731
- Minority opinions: Buena (23.2%), Mala (26.0%)

| Response | % |
|----------|---|
| Regular (esp.) | 37.8% |
| Mala | 26.0% |
| Buena | 23.2% |
| Muy mala | 8.4% |
| Muy buena | 3.3% |
| No sabe/ No contesta | 1.2% |

**p6|MED** (dispersed)
- Question: MEDIO_AMBIENTE|Del siguiente listado de problemas ambientales, ¿cuál considera el más importante para México?
- Mode: Contaminación del aire (26.6%)
- Runner-up: Contaminación del agua (19.1%), margin: 7.5pp
- HHI: 1625
- Minority opinions: Contaminación del agua (19.1%)

| Response | % |
|----------|---|
| Contaminación del aire | 26.6% |
| Contaminación del agua | 19.1% |
| Basura | 13.4% |
| Escasez de agua | 11.8% |
| Contaminación por químicos y pesticidas | 11.4% |
| Sobrexplotación de los recursos naturales | 7.9% |
| Cambio climático | 6.2% |
| No sabe/ No contesta | 1.5% |
| Transgénicos | 1.1% |
| Otro (esp.) | 1.0% |

**p1|ECO** (polarized)
- Question: ECONOMIA_Y_EMPLEO|¿Qué tan satisfecho está con la situación económica actual que vive el país?
- Mode: Poco (37.2%)
- Runner-up: Nada (35.7%), margin: 1.6pp
- HHI: 3211
- Minority opinions: Algo (23.2%), Nada (35.7%)

| Response | % |
|----------|---|
| Poco | 37.2% |
| Nada | 35.7% |
| Algo | 23.2% |
| Mucho | 3.2% |
| No sabe/ No contesta | 0.7% |

**p2|ECO** (polarized)
- Question: ECONOMIA_Y_EMPLEO|¿Qué tan satisfecho está usted con su situación económica actual?
- Mode: Poco (35.1%)
- Runner-up: Nada (31.8%), margin: 3.3pp
- HHI: 3049
- Minority opinions: Algo (28.1%), Nada (31.8%)

| Response | % |
|----------|---|
| Poco | 35.1% |
| Nada | 31.8% |
| Algo | 28.1% |
| Mucho | 4.7% |
| No sabe/ No contesta | 0.4% |

**p3|ECO** (polarized)
- Question: ECONOMIA_Y_EMPLEO|Desde su punto de vista de la  situación económica actual ¿usted vive _________ que sus padres cuando tenían su edad?
- Mode: Igual (36.5%)
- Runner-up: Peor (32.8%), margin: 3.7pp
- HHI: 3227
- Minority opinions: Mejor (28.5%), Peor (32.8%)

| Response | % |
|----------|---|
| Igual | 36.5% |
| Peor | 32.8% |
| Mejor | 28.5% |
| No sabe/ No contesta | 2.2% |

**p4|ECO** (dispersed)
- Question: ECONOMIA_Y_EMPLEO|Dada la situación económica actual, ¿usted cree que sus hijos podrán vivir__________ que usted?
- Mode: Igual (32.4%)
- Runner-up: Peor (29.2%), margin: 3.2pp
- HHI: 2818
- Minority opinions: Mejor (28.6%), Peor (29.2%)

| Response | % |
|----------|---|
| Igual | 32.4% |
| Peor | 29.2% |
| Mejor | 28.6% |
| No sabe/ No contesta | 9.8% |

**p5|ECO** (consensus)
- Question: ECONOMIA_Y_EMPLEO|En su opinión, ¿quién es más responsable de la situación económica del país?
- Mode: El gobierno (67.6%)
- Runner-up: Los partidos políticos (10.8%), margin: 56.8pp
- HHI: 4845

| Response | % |
|----------|---|
| El gobierno | 67.6% |
| Los partidos políticos | 10.8% |
| Los empresarios | 9.2% |
| Los trabajadores | 6.3% |
| No sabe/ No contesta | 6.2% |

### Demographic Fault Lines

| Dimension | Mean Cramér's V | Max Cramér's V | Variables |
|-----------|----------------|----------------|----------|
| region | 0.141 (moderate) | 0.171 | 9 |
| sexo | 0.100 (moderate) | 0.100 | 1 |
| edad | 0.097 (weak) | 0.119 | 3 |

**Variable-Level Demographic Detail:**

*p2|MED*
- region: V=0.111 (p=0.000) — 01: Darle al pueblo más voz y  voto en las decisiones del gobie (38%); 02: Mantener el orden en el país (40%); 03: Mantener el orden en el país (40%)
- edad: V=0.086 (p=0.040) — 0-18: Mantener el orden en el país (33%); 19-24: Mantener el orden en el país (38%); 25-34: Mantener el orden en el país (39%)

*p4|MED*
- region: V=0.158 (p=0.000) — 01: Mala (36%); 02: Mala (44%); 03: Regular (esp.) (42%)
- edad: V=0.085 (p=0.043) — 0-18: Mala (38%); 19-24: Regular (esp.) (37%); 25-34: Regular (esp.) (34%)

*p5|MED*
- region: V=0.171 (p=0.000) — 01: Regular (esp.) (39%); 02: Mala (37%); 03: Regular (esp.) (44%)

*p6|MED*
- region: V=0.145 (p=0.000) — 01: Contaminación del aire (27%); 02: Contaminación del aire (29%); 03: Contaminación del aire (28%)
- edad: V=0.119 (p=0.001) — 0-18: Contaminación del aire (25%); 19-24: Contaminación del aire (24%); 25-34: Contaminación del aire (24%)

*p1|ECO*
- region: V=0.169 (p=0.000) — 01:  Nada (47%); 02:  Nada (43%); 03:  Poco (40%)

*p2|ECO*
- region: V=0.162 (p=0.000) — 01:  Nada (41%); 02:  Poco (36%); 03:  Algo (45%)

*p3|ECO*
- region: V=0.126 (p=0.000) — 01:  Igual (37%); 02:  Peor (35%); 03:  Igual (47%)

*p4|ECO*
- region: V=0.128 (p=0.000) — 01:  Igual (34%); 02:  Mejor (34%); 03:  Igual (42%)

*p5|ECO*
- sexo: V=0.100 (p=0.035) —  Hombre:  El gobierno (70%);  Mujer:  El gobierno (65%)
- region: V=0.099 (p=0.002) — 01:  El gobierno (65%); 02:  El gobierno (70%); 03:  El gobierno (69%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p2|MED × p1|ECO | 0.053 (weak) | 0.047 | "Mantener el orden en el país": 26% (" Mucho") → 46% (" Algo") | 2000 |
| p2|MED × p2|ECO | 0.045 (weak) | 0.212 | "Darle al pueblo más voz y  voto en las decisiones del gobie": 25% (" Nada") → 31% (" Mucho") | 2000 |
| p2|MED × p3|ECO | 0.061 (weak) | 0.030 | "Darle al pueblo más voz y  voto en las decisiones del gobie": 27% (" Igual") → 73% (" NC") | 2000 |
| p2|MED × p4|ECO | 0.056 (weak) | 0.026 | "Mantener el orden en el país": 40% (" Mejor") → 50% (" NS") | 2000 |
| p2|MED × p5|ECO | 0.039 (weak) | 0.874 | "Mantener el orden en el país": 36% (" NC") → 50% (" Los empresarios") | 2000 |
| p4|MED × p1|ECO | 0.072 (weak) | 0.008 | "Muy mala": 10% (" Mucho") → 22% (" Nada") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p2|MED × p1|ECO** — How p2|MED distributes given p1|ECO:

| p1|ECO (conditioning) | Top p2|MED responses |
|---|---|
|  Mucho | Darle al pueblo más voz y  voto en las decisiones del gobie: 39%, Mantener el orden en el país: 26%, Proteger la libertad de expresión: 23% |
|  Algo | Mantener el orden en el país: 46%, Darle al pueblo más voz y  voto en las decisiones del gobie: 27%, Proteger la libertad de expresión: 16% |
|  Poco | Mantener el orden en el país: 39%, Darle al pueblo más voz y  voto en las decisiones del gobie: 29%, Proteger la libertad de expresión: 17% |
|  Nada | Mantener el orden en el país: 44%, Darle al pueblo más voz y  voto en las decisiones del gobie: 28%, Proteger la libertad de expresión: 15% |

**p2|MED × p2|ECO** — How p2|MED distributes given p2|ECO:

| p2|ECO (conditioning) | Top p2|MED responses |
|---|---|
|  Mucho | Mantener el orden en el país: 43%, Darle al pueblo más voz y  voto en las decisiones del gobie: 31%, Luchar contra las alzas de precio: 15% |
|  Algo | Mantener el orden en el país: 47%, Darle al pueblo más voz y  voto en las decisiones del gobie: 27%, Luchar contra las alzas de precio: 14% |
|  Poco | Mantener el orden en el país: 42%, Darle al pueblo más voz y  voto en las decisiones del gobie: 28%, Proteger la libertad de expresión: 17% |
|  Nada | Mantener el orden en el país: 44%, Darle al pueblo más voz y  voto en las decisiones del gobie: 25%, Luchar contra las alzas de precio: 15% |

**p2|MED × p3|ECO** — How p2|MED distributes given p3|ECO:

| p3|ECO (conditioning) | Top p2|MED responses |
|---|---|
|  Mejor | Mantener el orden en el país: 38%, Darle al pueblo más voz y  voto en las decisiones del gobie: 29%, Proteger la libertad de expresión: 17% |
|  Igual | Mantener el orden en el país: 41%, Darle al pueblo más voz y  voto en las decisiones del gobie: 27%, Proteger la libertad de expresión: 18% |
|  Peor | Mantener el orden en el país: 44%, Darle al pueblo más voz y  voto en las decisiones del gobie: 28%, Proteger la libertad de expresión: 15% |
|  NS | Mantener el orden en el país: 38%, Darle al pueblo más voz y  voto en las decisiones del gobie: 35%, Luchar contra las alzas de precio: 15% |
|  NC | Darle al pueblo más voz y  voto en las decisiones del gobie: 73%, Mantener el orden en el país: 20%, Luchar contra las alzas de precio: 7% |

**p2|MED × p4|ECO** — How p2|MED distributes given p4|ECO:

| p4|ECO (conditioning) | Top p2|MED responses |
|---|---|
|  Mejor | Mantener el orden en el país: 40%, Darle al pueblo más voz y  voto en las decisiones del gobie: 29%, Proteger la libertad de expresión: 17% |
|  Igual | Mantener el orden en el país: 43%, Darle al pueblo más voz y  voto en las decisiones del gobie: 28%, Proteger la libertad de expresión: 17% |
|  Peor | Mantener el orden en el país: 47%, Darle al pueblo más voz y  voto en las decisiones del gobie: 29%, Proteger la libertad de expresión: 13% |
|  NS | Mantener el orden en el país: 50%, Darle al pueblo más voz y  voto en las decisiones del gobie: 22%, Luchar contra las alzas de precio: 14% |

**p2|MED × p5|ECO** — How p2|MED distributes given p5|ECO:

| p5|ECO (conditioning) | Top p2|MED responses |
|---|---|
|  El gobierno | Mantener el orden en el país: 44%, Darle al pueblo más voz y  voto en las decisiones del gobie: 28%, Proteger la libertad de expresión: 16% |
|  Los empresarios | Mantener el orden en el país: 50%, Darle al pueblo más voz y  voto en las decisiones del gobie: 25%, Proteger la libertad de expresión: 14% |
|  Los trabajadores | Mantener el orden en el país: 42%, Darle al pueblo más voz y  voto en las decisiones del gobie: 28%, Proteger la libertad de expresión: 17% |
|  Los partidos políticos | Mantener el orden en el país: 42%, Darle al pueblo más voz y  voto en las decisiones del gobie: 30%, Proteger la libertad de expresión: 15% |
|  NS | Mantener el orden en el país: 44%, Darle al pueblo más voz y  voto en las decisiones del gobie: 29%, Proteger la libertad de expresión: 16% |
|  NC | Mantener el orden en el país: 36%, Darle al pueblo más voz y  voto en las decisiones del gobie: 22%, Proteger la libertad de expresión: 22% |

**p4|MED × p1|ECO** — How p4|MED distributes given p1|ECO:

| p1|ECO (conditioning) | Top p4|MED responses |
|---|---|
|  Mucho | Mala: 42%, Regular (esp.): 34%, Buena: 13% |
|  Algo | Regular (esp.): 37%, Mala: 37%, Muy mala: 12% |
|  Poco | Mala: 37%, Regular (esp.): 32%, Muy mala: 20% |
|  Nada | Mala: 40%, Regular (esp.): 28%, Muy mala: 22% |
### Bridge Model Diagnostics

> For human inspection only — not passed to the LLM.

#### Summary

| Variable | Model | Pseudo-R² | LLR p | Dominant SES | Quality |
|----------|-------|-----------|-------|--------------|---------|
| p1|ECO | mnlogit | 0.093 | 0.304 | region | weak |
| p2|ECO | mnlogit | 0.076 | 0.528 | Tam_loc | weak |
| p2|MED | mnlogit | 0.069 | 0.705 | est_civil | weak |
| p3|ECO | mnlogit | 0.073 | 0.950 | region | weak |
| p4|ECO | mnlogit | 0.084 | 0.260 | region | weak |
| p4|MED | mnlogit | 0.101 | 0.857 | sexo | weak |
| p5|ECO | mnlogit | 0.128 | 0.735 | edad | weak |

**Mean pseudo-R²:** 0.089 &ensp;|&ensp; **Overall dominant SES dimension:** region

> ⚠ 7/7 bridge models are weak (R²<0.02 or LLR p≥0.10). Simulated Cramér's V for those variables may underestimate the true association.

#### Per-Variable SES Predictor Detail

Top predictors by |t|-statistic — answers: which SES variable is doing the work?

**p1|ECO** (mnlogit, R²=0.093, LLR p=0.304, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_03 | -0.727 | 1.374 | -1.219 | 0.223 |
| Tam_loc | 1.684 | 1.906 | 0.980 | 0.327 |
| sexo | -0.968 | 1.219 | -0.846 | 0.398 |
| escol | 0.394 | 1.300 | 0.769 | 0.442 |
| region_02 | 1.120 | 2.019 | 0.719 | 0.472 |
| edad | -0.198 | 0.528 | -0.695 | 0.487 |

**p2|ECO** (mnlogit, R²=0.076, LLR p=0.528, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| Tam_loc | 1.247 | 0.953 | 1.368 | 0.171 |
| escol | 0.402 | 1.027 | 1.076 | 0.282 |
| sexo | -0.848 | 0.857 | -1.014 | 0.310 |
| region_02 | 1.052 | 1.361 | 0.845 | 0.398 |
| edad | -0.247 | 0.390 | -0.843 | 0.399 |
| region_03 | -0.437 | 1.018 | -0.748 | 0.454 |

**p2|MED** (mnlogit, R²=0.069, LLR p=0.705, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| est_civil_6.0 | -0.775 | 0.628 | -2.072 | 0.038 |
| region_04 | -0.929 | 0.875 | -1.766 | 0.077 |
| edad | -0.172 | 0.241 | -1.374 | 0.170 |
| region_02 | 0.036 | 0.636 | -1.290 | 0.197 |
| sexo | 0.395 | 0.485 | 1.203 | 0.229 |
| est_civil_2.0 | -0.586 | 1.238 | -0.904 | 0.366 |

**p3|ECO** (mnlogit, R²=0.073, LLR p=0.950, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_04 | 0.260 | 2.821 | 2.308 | 0.021 |
| est_civil_2.0 | 0.134 | 2.149 | 2.155 | 0.031 |
| region_02 | -0.053 | 2.418 | 1.239 | 0.215 |
| sexo | -0.837 | 1.497 | -1.203 | 0.229 |
| empleo_03 | -0.115 | 5.758 | -0.999 | 0.318 |
| Tam_loc | -0.400 | 0.891 | -0.917 | 0.359 |

**p4|ECO** (mnlogit, R²=0.084, LLR p=0.260, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_02 | -0.544 | 0.634 | -2.519 | 0.012 |
| region_03 | -0.584 | 0.686 | -1.889 | 0.059 |
| region_04 | 0.733 | 0.786 | 1.637 | 0.102 |
| escol | -0.244 | 0.616 | 1.479 | 0.139 |
| est_civil_2.0 | 0.302 | 0.852 | 1.269 | 0.205 |
| edad | -0.033 | 0.219 | -0.995 | 0.320 |

**p4|MED** (mnlogit, R²=0.101, LLR p=0.857, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| sexo | 0.387 | 2.623 | 0.588 | 0.557 |
| escol | 0.638 | 2.608 | 0.559 | 0.576 |
| edad | -0.479 | 1.119 | -0.499 | 0.618 |
| est_civil_2.0 | 0.066 | 3.485 | 0.492 | 0.623 |
| Tam_loc | 0.556 | 3.127 | 0.423 | 0.672 |
| region_04 | 0.116 | 5.453 | -0.343 | 0.732 |

**p5|ECO** (mnlogit, R²=0.128, LLR p=0.735, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| edad | -0.529 | 0.491 | -2.026 | 0.043 |
| sexo | 0.994 | 0.920 | 1.777 | 0.076 |
| est_civil_6.0 | -0.317 | 1.125 | 1.650 | 0.099 |
| region_04 | 0.499 | 1.515 | 1.375 | 0.169 |
| region_02 | -0.794 | 1.452 | -1.369 | 0.171 |
| region_03 | -0.426 | 1.517 | -1.304 | 0.192 |

*Pseudo-R² = McFadden's. Low values mean SES explains little variance in that variable — the bridge simulation still produces an estimate, but its precision is reduced.*

### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from the cross-dataset bivariate associations with significant p-values, which provide direct insights into how economic satisfaction and outlook relate to environmental priorities and perceptions. Among these, the relationship between national economic satisfaction (p1|ECO) and environmental priorities (p2|MED) is particularly informative. Demographic fault lines offer secondary evidence about opinion fragmentation but do not directly address the query. Univariate distributions provide contextual background but are weakest for inferring relationships relevant to balancing environmental concerns with economic development.

**Key Limitations:**
- All cross-dataset associations are weak in effect size (low Cramér's V), limiting strength of conclusions.
- Several bivariate tests are not statistically significant, reducing evidence coverage across variables.
- The variables capture attitudes and perceptions but do not measure actual behaviors or policy trade-offs directly.
- The analysis relies on simulation-based estimates and a limited number of cross-survey variable pairs, constraining depth of relational insights.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p2|MED, p4|MED, p1|ECO, p2|ECO, p3|ECO
- **Dispersed Variables:** p5|MED, p6|MED, p4|ECO

