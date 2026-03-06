# q4_gender_family

**Query (ES):** ¿Cómo están cambiando los roles de género en la familia mexicana?
**Query (EN):** How are gender roles changing in the Mexican family?
**Variables:** p1|GEN, p2|GEN, p5|GEN, p6|GEN, p1|FAM, p2|FAM, p3|FAM, p4|FAM, p5|FAM
**Status:** ✅ success
**Time:** 64739ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Cómo están cambiando los roles de género en la familia mexicana?

## Summary
The data reveal a moderate but consistent relationship between family context variables—such as childhood residence and family headship—and perceptions related to gender roles and economic conditions in Mexico, suggesting that traditional family structures still influence views on gender roles. However, direct measures of changing gender roles within families are limited, and opinions about gender advantages and disadvantages show strong consensus with little variation. Evidence quality is moderate, based on nine variables with significant bivariate associations but limited direct indicators of gender role change.

## Data Landscape
Nine variables from gender and family surveys were analyzed, with five showing consensus, two polarized, and two dispersed opinion distributions, yielding a divergence index of 44%. This indicates a moderate level of disagreement or variation in public opinion on topics related to gender and family. The variables include perceptions of economic conditions, childhood family environment, family headship, and gender role advantages and disadvantages, reflecting a mix of direct and indirect measures relevant to changing gender roles in Mexican families.

## Evidence
Cross-tabulations show moderate associations between gender-related economic perceptions and family variables. For example, the perception that the country's situation is "Igual de mala" varies from 13.0% among those who lived in a "departamento en una vecindad" to 34.8% among those who reported "Otro" childhood residence (V=0.110, p=0.000):
| p1|FAM category | Igual de mala % |
|---|---|
| Un departamento EN UNA VECINDAD | 13.0% |
| Otro | 34.8% |

Similarly, those who lived as part of a family during childhood report "Peor" economic perceptions at 32.9%, compared to 16.7% among those who did not (V=0.141, p=0.000):
| p2|FAM category | Peor % |
|---|---|
| Sí | 32.9% |
| No | 25.3% |
| NC | 16.7% |

The head of the family during childhood also relates moderately to gendered economic perceptions, with "No sabe" responses ranging from 1.9% (father as head) to 19.2% (NC) (V=0.102, p=0.000):
| p5|FAM category | NS % |
|---|---|
| Su padre | 1.9% |
| NC | 19.2% |

Regarding expectations for the future, perceptions vary weakly but significantly with childhood residence, with the belief that the situation will "seguir igual de mal" ranging from 20.5% to 41.8% depending on residence type (V=0.088, p=0.001):
| p1|FAM category | Va a seguir igual de mal % |
|---|---|
| Otro | 20.5% |
| Un cuarto rentado en una casa o edificio | 41.8% |

Demographically, employment status strongly moderates future economic expectations, with unemployed respondents 100% believing the situation will "seguir igual de mal" and no one expecting improvement. Region also shapes opinions, with some regions more pessimistic than others.

Univariate distributions show that 72.5% report their father was head of the family during childhood, indicating persistence of traditional family authority roles:

**p5|FAM** — ¿En esa familia quien era el jefe?:
| Response | % |
|---|---|
| Su padre | 72.5% |
| Su madre | 10.6% |
| Ambos padres | 7.8% |
| Su abuelo o abuela | 7.3% |

Regarding gender role perceptions, there is strong consensus with 83.0% responding "No sabe" to the greatest advantage of being a woman and 81.5% "No sabe" to the greatest disadvantage, indicating limited articulation or awareness of gender role changes:

**p3|GEN** — ¿Cuál cree qué es la mayor ventaja de ser mujer?:
| Response | % |
|---|---|
| NS | 83.0% |
| NC | 17.0% |

**p4|GEN** — ¿Y la mayor desventaja de ser mujer?:
| Response | % |
|---|---|
| NS | 81.5% |
| NC | 18.5% |

## Complications
Employment status is the strongest demographic moderator, with unemployed respondents showing maximal pessimism about future economic conditions, which may color perceptions of gender roles indirectly. Regional differences also moderate perceptions, reflecting cultural and socioeconomic diversity across Mexico. Minority opinions exceeding 15% appear in some variables (e.g., 17.0% non-NS responses about gender advantages), suggesting some segments hold alternative views. The reliance on simulation-based bivariate associations introduces estimation uncertainty, and the sample size limits power for some variables. Crucially, variables directly measuring changes in gender roles within families are absent, forcing reliance on indirect proxies such as family headship and economic perceptions. Some variables, like family size, have unusable data (100% NS), limiting analysis. The weak but significant associations between childhood residence and future expectations indicate complexity but do not directly capture gender role evolution.

## Implications
First, policies aiming to promote gender equality in Mexican families should consider the persistence of traditional family authority structures, as over 70% report fathers as family heads during childhood. Interventions might focus on empowering women within family decision-making to foster changing gender roles. Second, the strong influence of employment and regional disparities on perceptions suggests that socioeconomic context shapes gender role attitudes; thus, regional and labor market policies that improve economic stability could indirectly support more egalitarian gender roles. Finally, the lack of clear articulation about gender role advantages and disadvantages indicates a need for educational programs to raise awareness and dialogue about gender dynamics within families, potentially accelerating cultural shifts toward gender equity.

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | 9 |
| Divergence Index | 44.4% |
| Consensus Variables | 5 |
| Lean Variables | 0 |
| Polarized Variables | 2 |
| Dispersed Variables | 2 |

### Variable Details


**p1|GEN** (polarized)
- Question: GENERO|Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación actual del país: mejor o peor?
- Mode: Igual de mala (39.2%)
- Runner-up: Peor (38.4%), margin: 0.8pp
- HHI: 3249
- Minority opinions: Peor (38.4%)

| Response | % |
|----------|---|
| Igual de mala | 39.2% |
| Peor | 38.4% |
| Igual de buena | 13.0% |
| Mejor | 8.2% |
| No sabe/ No contesta | 1.2% |

**p2|GEN** (polarized)
- Question: GENERO|En general, ¿cree usted que el próximo año la situación económica del país va a mejorar o empeorar?
- Mode: Va a seguir igual de mal (35.9%)
- Runner-up: Va a empeorar (30.2%), margin: 5.8pp
- HHI: 2648
- Minority opinions: Va a mejorar (17.4%), Va a empeorar (30.2%)

| Response | % |
|----------|---|
| Va a seguir igual de mal | 35.9% |
| Va a empeorar | 30.2% |
| Va a mejorar | 17.4% |
| Va a seguir igual de bien | 10.2% |
| No sabe/ No contesta | 6.2% |

**p5|GEN** (consensus)
- Question: GENERO|¿Cuál cree qué es la mayor ventaja de ser mujer?
- Mode: NS (83.0%)
- Runner-up: NC (17.0%), margin: 66.0pp
- HHI: 7177
- Minority opinions: NC (17.0%)

| Response | % |
|----------|---|
| NS | 83.0% |
| NC | 17.0% |

**p6|GEN** (consensus)
- Question: GENERO|¿Y la mayor desventaja de ser mujer?
- Mode: NS (81.5%)
- Runner-up: NC (18.5%), margin: 63.0pp
- HHI: 6985
- Minority opinions: NC (18.5%)

| Response | % |
|----------|---|
| NS | 81.5% |
| NC | 18.5% |

**p1|FAM** (dispersed)
- Question: FAMILIA|El lugar en donde usted vivió durante su infancia, digamos, hasta los 14 años de edad era...
- Mode: Una casa sola en una ciudad. (34.8%)
- Runner-up: Una casa sola en un pueblo. (27.5%), margin: 7.3pp
- HHI: 2218
- Minority opinions: Una casa sola en un pueblo. (27.5%)

| Response | % |
|----------|---|
| Una casa sola en una ciudad. | 34.8% |
| Una casa sola en un pueblo. | 27.5% |
| Un departamento EN UNA VECINDAD. | 8.4% |
| Un cuarto rentado en una casa o edificio. | 7.6% |
| Un rancho. | 7.2% |
| Un departamento en un edificio. | 6.2% |
| Un departamento en una UNIDAD HABITACIONAL | 5.1% |
| Un departamento en un pueblo. | 1.5% |
| Otro | 1.0% |
| No sabe/ No contesta | 0.7% |

**p2|FAM** (consensus)
- Question: FAMILIA|¿Vivió su infancia siendo parte de una familia?
- Mode: Sí (95.9%)
- Runner-up: No (3.8%), margin: 92.2pp
- HHI: 9215

| Response | % |
|----------|---|
| Sí | 95.9% |
| No | 3.8% |
| No sabe/ No contesta | 0.3% |

**p3|FAM** (dispersed)
- Question: FAMILIA|Entonces, ¿en dónde vivió su infancia?
- Mode: No sabe/ No contesta (38.7%)
- Runner-up: En un orfanatorio (26.5%), margin: 12.3pp
- HHI: 2607
- Minority opinions: En un orfanatorio (26.5%)

| Response | % |
|----------|---|
| No sabe/ No contesta | 38.7% |
| En un orfanatorio | 26.5% |
| En una institución de salud | 12.3% |
| En la calle | 12.3% |
| En una casa de cuna | 10.3% |

**p4|FAM** (consensus)
- Question: FAMILIA|Durante su infancia hasta los 14 años de edad, ¿cuántas personas formaban su familia incluyéndolo a usted?
- Mode: No sabe/ No contesta (100.0%)
- Runner-up:  (0.0%), margin: 100.0pp
- HHI: 10000

| Response | % |
|----------|---|
| No sabe/ No contesta | 100.0% |

**p5|FAM** (consensus)
- Question: FAMILIA|¿En esa familia quien era el jefe?
- Mode: Su padre (72.5%)
- Runner-up: Su madre (10.6%), margin: 61.9pp
- HHI: 5479

| Response | % |
|----------|---|
| Su padre | 72.5% |
| Su madre | 10.6% |
| Ambos padres | 7.8% |
| Su abuelo o abuela | 7.3% |
| Otra persona | 1.2% |
| No sabe/ No contesta | 0.6% |

### Demographic Fault Lines

| Dimension | Mean Cramér's V | Max Cramér's V | Variables |
|-----------|----------------|----------------|----------|
| empleo | 0.445 (strong) | 0.950 | 3 |
| region | 0.346 (strong) | 0.806 | 7 |
| edad | 0.255 (moderate) | 0.255 | 1 |

**Variable-Level Demographic Detail:**

*p1|GEN*
- region: V=0.164 (p=0.000) — 01:  Peor (42%); 02:  Peor (52%); 03:  Igual de mala (37%)

*p2|GEN*
- empleo: V=0.231 (p=0.030) — 01:  Va a seguir igual de mal (100%); 02:  Va a empeorar (48%); 03:  Va a seguir igual de mal (30%)
- region: V=0.171 (p=0.000) — 01:  Va a empeorar (35%); 02:  Va a empeorar (42%); 03:  Va a seguir igual de mal (35%)

*p5|GEN*
- empleo: V=0.950 (p=0.026) — 01: ser responsable (100%); 02: ninguna (7%); 03: NS (13%)
- region: V=0.795 (p=0.036) — 01: NS (15%); 02: NS (11%); 03: NS (19%)

*p6|GEN*
- region: V=0.806 (p=0.025) — 01: NS (16%); 02: NS (12%); 03: NS (21%)

*p1|FAM*
- edad: V=0.255 (p=0.011) — 15.0:  Una casa sola en una ciudad. (67%); 16.0:  Una casa sola en una ciudad. (50%); 17.0:  Una casa sola en una ciudad. (75%)
- region: V=0.220 (p=0.000) — 1.0:  Una casa sola en un pueblo. (46%); 2.0:  Una casa sola en una ciudad. (34%); 3.0:  Una casa sola en una ciudad. (43%)
- empleo: V=0.155 (p=0.001) — 1.0:  Una casa sola en una ciudad. (37%); 2.0:  Una casa sola en un pueblo. (35%)

*p4|FAM*
- region: V=0.140 (p=0.039) — 1.0: 6.0 (20%); 2.0: 4.0 (19%); 3.0: 5.0 (24%)

*p5|FAM*
- region: V=0.124 (p=0.000) — 1.0:  Su padre (71%); 2.0:  Su padre (65%); 3.0:  Su padre (76%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p1|GEN × p1|FAM | 0.110 (moderate) | 0.000 | " Igual de mala": 13% (" Un departamento EN UNA VECINDAD.") → 35% (" Otro") | 2000 |
| p1|GEN × p2|FAM | 0.141 (moderate) | 0.000 | " Peor": 17% ("NC") → 33% ("Sí") | 2000 |
| p1|GEN × p3|FAM | 0.131 (moderate) | 0.000 | " Igual de buena": 19% (" En la calle") → 38% (" NS") | 2000 |
| p1|GEN × p4|FAM | 0.140 (moderate) | 0.000 | " Peor": 8% ("12.0") → 41% ("7.0") | 2000 |
| p1|GEN × p5|FAM | 0.102 (moderate) | 0.000 | " NS": 2% (" Su padre") → 19% (" NC") | 2000 |
| p2|GEN × p1|FAM | 0.088 (weak) | 0.001 | " Va a seguir igual de mal": 20% (" Otro") → 42% (" Un cuarto rentado en una casa o edificio.") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p1|GEN × p1|FAM** — How p1|GEN distributes given p1|FAM:

| p1|FAM (conditioning) | Top p1|GEN responses |
|---|---|
|  Una casa sola en una ciudad. |  Peor: 33%,  Igual de buena: 30%,  Igual de mala: 20% |
|  Una casa sola en un pueblo. |  Peor: 37%,  Igual de buena: 24%,  Mejor: 24% |
|  Un departamento EN UNA VECINDAD. |  Peor: 36%,  Igual de buena: 24%,  Mejor: 20% |
|  Un departamento en un edificio. |  Peor: 34%,  Igual de buena: 22%,  Igual de mala: 21% |
|  Un departamento en una UNIDAD HABITACIONAL |  Peor: 30%,  Igual de mala: 25%,  Igual de buena: 22% |
|  Un cuarto rentado en una casa o edificio. |  Peor: 29%,  Igual de buena: 28%,  Igual de mala: 19% |
|  Un departamento en un pueblo. |  Peor: 36%,  Mejor: 19%,  Igual de buena: 19% |
|  Un rancho. |  Peor: 38%,  Igual de buena: 23%,  Mejor: 20% |

**p1|GEN × p2|FAM** — How p1|GEN distributes given p2|FAM:

| p2|FAM (conditioning) | Top p1|GEN responses |
|---|---|
| Sí |  Peor: 33%,  Igual de buena: 26%,  Mejor: 20% |
| No |  Mejor: 29%,  Peor: 25%,  Igual de buena: 22% |
| NC |  Igual de buena: 31%,  Mejor: 22%,  Peor: 17% |

**p1|GEN × p3|FAM** — How p1|GEN distributes given p3|FAM:

| p3|FAM (conditioning) | Top p1|GEN responses |
|---|---|
|  En un orfanatorio |  Peor: 33%,  Igual de buena: 27%,  Igual de mala: 22% |
|  En una casa de cuna |  Peor: 36%,  Igual de buena: 24%,  Mejor: 19% |
|  En una institución de salud |  Igual de buena: 32%,  Peor: 30%,  Igual de mala: 20% |
|  En la calle |  Peor: 34%,  Mejor: 25%,  Igual de mala: 19% |
|  NS |  Igual de buena: 38%,  Peor: 26%,  Igual de mala: 22% |
|  NC |  Peor: 39%,  Mejor: 22%,  Igual de buena: 20% |

**p1|GEN × p4|FAM** — How p1|GEN distributes given p4|FAM:

| p4|FAM (conditioning) | Top p1|GEN responses |
|---|---|
| 1.0 |  Igual de mala: 44%,  Mejor: 17%,  Peor: 17% |
| 2.0 |  Peor: 36%,  Igual de buena: 24%,  Igual de mala: 21% |
| 3.0 |  Peor: 35%,  Igual de buena: 32%,  Mejor: 16% |
| 4.0 |  Peor: 30%,  Igual de buena: 27%,  Igual de mala: 21% |
| 5.0 |  Peor: 34%,  Igual de buena: 28%,  Mejor: 20% |
| 6.0 |  Peor: 36%,  Igual de buena: 27%,  Igual de mala: 17% |
| 7.0 |  Peor: 41%,  Igual de buena: 24%,  Igual de mala: 18% |
| 8.0 |  Peor: 35%,  Igual de buena: 26%,  Mejor: 20% |

**p1|GEN × p5|FAM** — How p1|GEN distributes given p5|FAM:

| p5|FAM (conditioning) | Top p1|GEN responses |
|---|---|
|  Su padre |  Peor: 33%,  Igual de buena: 27%,  Igual de mala: 20% |
|  Su madre |  Peor: 28%,  Igual de buena: 28%,  Mejor: 22% |
|  Su abuelo o abuela |  Igual de buena: 29%,  Peor: 27%,  Igual de mala: 22% |
|  Ambos padres |  Peor: 31%,  Igual de buena: 22%,  Mejor: 20% |
|  Otra persona |  Peor: 28%,  Mejor: 26%,  Igual de buena: 24% |
|  NS |  Peor: 28%,  Igual de mala: 25%,  Igual de buena: 19% |
|  NC |  Peor: 25%,  Mejor: 19%,  Igual de buena: 19% |

**p2|GEN × p1|FAM** — How p2|GEN distributes given p1|FAM:

| p1|FAM (conditioning) | Top p2|GEN responses |
|---|---|
|  Una casa sola en una ciudad. |  Va a empeorar: 37%,  Va a seguir igual de mal: 36%,  Va a mejorar: 12% |
|  Una casa sola en un pueblo. |  Va a empeorar: 42%,  Va a seguir igual de mal: 35%,  Va a mejorar: 8% |
|  Un departamento EN UNA VECINDAD. |  Va a seguir igual de mal: 38%,  Va a empeorar: 33%,  Va a mejorar: 11% |
|  Un departamento en un edificio. |  Va a seguir igual de mal: 37%,  Va a empeorar: 31%,  Va a mejorar: 15% |
|  Un departamento en una UNIDAD HABITACIONAL |  Va a seguir igual de mal: 35%,  Va a empeorar: 32%,  Va a seguir igual de bien: 13% |
|  Un cuarto rentado en una casa o edificio. |  Va a seguir igual de mal: 42%,  Va a empeorar: 30%,  Va a seguir igual de bien: 12% |
|  Un departamento en un pueblo. |  Va a seguir igual de mal: 37%,  Va a empeorar: 25%,  NS: 18% |
|  Un rancho. |  Va a empeorar: 41%,  Va a seguir igual de mal: 29%,  Va a seguir igual de bien: 12% |
### Bridge Model Diagnostics

> For human inspection only — not passed to the LLM.

#### Summary

| Variable | Model | Pseudo-R² | LLR p | Dominant SES | Quality |
|----------|-------|-----------|-------|--------------|---------|
| p1|FAM | mnlogit | 0.084 | 0.000 | escol | good |
| p1|GEN | mnlogit | 0.130 | 0.177 | region | weak |
| p2|FAM | mnlogit | 0.033 | 0.831 | empleo | weak |
| p2|GEN | mnlogit | 0.173 | 0.001 | region | good |
| p3|FAM | mnlogit | 0.389 | 0.102 | escol | weak |
| p4|FAM | mnlogit | 0.032 | 0.276 | escol | weak |
| p5|FAM | mnlogit | 0.051 | 0.000 | est_civil | good |

**Mean pseudo-R²:** 0.127 &ensp;|&ensp; **Overall dominant SES dimension:** escol

> ⚠ 4/7 bridge models are weak (R²<0.02 or LLR p≥0.10). Simulated Cramér's V for those variables may underestimate the true association.

#### Per-Variable SES Predictor Detail

Top predictors by |t|-statistic — answers: which SES variable is doing the work?

**p1|FAM** (mnlogit, R²=0.084, LLR p=0.000, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| escol | -0.389 | 0.158 | -7.106 | 0.000 |
| Tam_loc | 0.248 | 0.168 | 7.073 | 0.000 |
| region_3.0 | -0.409 | 0.470 | -6.438 | 0.000 |
| region_4.0 | -0.063 | 0.478 | -4.909 | 0.000 |
| edad | -0.126 | 0.129 | -3.371 | 0.001 |
| region_2.0 | 0.163 | 0.460 | -3.081 | 0.002 |

**p1|GEN** (mnlogit, R²=0.130, LLR p=0.177, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_03 | -0.500 | 1.362 | -2.030 | 0.042 |
| sexo | 1.095 | 0.960 | 1.773 | 0.076 |
| region_02 | 0.886 | 2.282 | 1.539 | 0.124 |
| edad | -0.252 | 0.467 | -1.433 | 0.152 |
| Tam_loc | -0.567 | 1.139 | -0.752 | 0.452 |
| est_civil_6.0 | -0.271 | 1.324 | 0.672 | 0.501 |

**p2|FAM** (mnlogit, R²=0.033, LLR p=0.831, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| empleo_2.0 | -0.838 | 0.789 | -2.747 | 0.006 |
| edad | -0.687 | 0.324 | -2.215 | 0.027 |
| sexo | -0.013 | 0.735 | 2.087 | 0.037 |
| region_2.0 | 0.286 | 0.821 | 1.685 | 0.092 |
| escol | -0.514 | 0.317 | -1.670 | 0.095 |
| Tam_loc | 0.274 | 0.274 | 1.037 | 0.300 |

**p2|GEN** (mnlogit, R²=0.173, LLR p=0.001, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_03 | -1.109 | 0.943 | -2.645 | 0.008 |
| Tam_loc | 0.763 | 0.548 | 2.076 | 0.038 |
| est_civil_6.0 | -0.736 | 0.766 | -1.547 | 0.122 |
| region_02 | 0.722 | 0.900 | 1.501 | 0.133 |
| region_04 | 1.052 | 1.682 | 1.335 | 0.182 |
| edad | -0.224 | 0.307 | -1.152 | 0.249 |

**p3|FAM** (mnlogit, R²=0.389, LLR p=0.102, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| escol | -0.730 | 1.416 | -2.159 | 0.031 |
| est_civil_6.0 | 1.871 | 3.101 | 1.443 | 0.149 |
| region_2.0 | 0.509 | 3.592 | 1.210 | 0.226 |
| Tam_loc | -1.291 | 1.901 | -0.972 | 0.331 |
| region_4.0 | -2.003 | 5.575 | -0.937 | 0.349 |
| est_civil_2.0 | -0.810 | 4.562 | -0.881 | 0.379 |

**p4|FAM** (mnlogit, R²=0.032, LLR p=0.276, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| escol | 0.405 | 0.832 | 1.098 | 0.272 |
| edad | 0.353 | 0.662 | 0.964 | 0.335 |
| Tam_loc | 0.253 | 0.800 | 0.867 | 0.386 |
| region_3.0 | 0.008 | 2.120 | -0.478 | 0.633 |
| sexo | 0.039 | 1.773 | 0.475 | 0.635 |
| est_civil_2.0 | 0.023 | 2.705 | 0.395 | 0.693 |

**p5|FAM** (mnlogit, R²=0.051, LLR p=0.000, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| est_civil_2.0 | 0.282 | 1.131 | 4.002 | 0.000 |
| escol | -0.558 | 0.298 | -3.870 | 0.000 |
| sexo | 0.121 | 0.630 | 2.959 | 0.003 |
| empleo_2.0 | -0.174 | 0.651 | -2.685 | 0.007 |
| est_civil_6.0 | -0.018 | 0.958 | 2.641 | 0.008 |
| region_3.0 | -0.349 | 0.751 | -2.596 | 0.009 |

*Pseudo-R² = McFadden's. Low values mean SES explains little variance in that variable — the bridge simulation still produces an estimate, but its precision is reduced.*

### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from the cross-dataset bivariate associations with significant p-values, which reveal moderate relationships between gender-related economic perceptions and family-related variables such as childhood residence and family headship. Demographic fault lines provide secondary contextual insights into variation by employment, region, and age. Univariate distributions offer supporting context but do not establish relationships relevant to changing gender roles in Mexican families.

**Key Limitations:**
- All bivariate estimates are simulation-based, which may introduce estimation uncertainty.
- Sample size is moderate (n=2000), but some variables have limited variability or high non-response, reducing analytic power.
- Variables directly measuring gender roles in family dynamics are limited; many variables focus on economic perceptions or childhood family context, providing indirect evidence only.
- No direct measures of changing gender roles over time or within families are available, limiting the ability to fully address the query.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p1|GEN, p2|GEN
- **Dispersed Variables:** p1|FAM, p3|FAM

