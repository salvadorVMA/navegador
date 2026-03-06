# q3_education_poverty

**Query (ES):** ¿Qué relación ven los mexicanos entre educación y pobreza?
**Query (EN):** What relationship do Mexicans see between education and poverty?
**Variables:** p2|EDU, p3|EDU, p4|EDU, p5|EDU, p6|EDU, p1|POB, p2|POB, p3|POB, p4|POB
**Status:** ✅ success
**Time:** 50086ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Qué relación ven los mexicanos entre educación y pobreza?

## Summary
Mexicans perceive a strong relationship between education and poverty, with those currently studying being much more likely among certain poverty-related work categories, such as students themselves (67.1%) versus retirees (2.8%). This is supported by strong and moderate associations between education status and various poverty indicators, including work status, secondary work activities, job permanence, and job tenure. The evidence is based on multiple significant bivariate associations (5 pairs) with strong confidence due to consistent p-values and moderate to strong Cramér's V values.

## Data Landscape
The analysis covers 9 variables from education and poverty surveys, including current studying status, educational support, level and motivation of study, and multiple poverty-related work indicators. Among these, 5 variables show consensus, 1 is polarized, 1 is dispersed, and 2 lean toward a dominant view, yielding a divergence index of 44%, which indicates moderate variation in public opinion about the education-poverty relationship in Mexico.

## Evidence
The strongest relationship is between current studying status (p2|EDU) and work status last week (p1|POB), where the proportion currently studying ranges from 2.8% among retirees to 67.1% among those who are students (V=0.352, p=0.000). This shows that being a student is strongly linked to education status, while retirees rarely study.

| p1|POB category | Sí (studying) % |
|---|---|
| Trabajó | 27.8% |
| No trabajó pero sí tenía trabajo | 47.6% |
| Buscó trabajo | 58.3% |
| Es estudiante | 67.1% |
| Se dedica a los quehaceres de su hogar | 35.1% |
| Está jubilado(a) o pensionado(a) | 2.8% |
| No trabajó | 30.7% |

Education status also moderately varies with secondary work activities (p2|POB), with studying rates from 29.6% among those helping in a family business to 73.3% among those selling products (V=0.176, p=0.000).

| p2|POB category | Sí (studying) % |
|---|---|
| Ayudó a trabajar en un negocio familiar | 29.6% |
| Vendió algunos productos: ropa, cosméticos, alimentos | 73.3% |
| No trabajó | 36.0% |

Job permanence (p3|POB) also relates moderately to studying: 29.6% studying among those with permanent jobs versus 55.8% among seasonal workers (V=0.249, p=0.000).

| p3|POB category | Sí (studying) % |
|---|---|
| Permanentemente | 29.6% |
| Sólo por temporadas | 55.8% |

Years at current job (p4|POB) shows a strong association with studying status, ranging from 0% studying among those with 18 years at their job to 81.4% studying among those with 2 years tenure (V=0.519, p=0.000), indicating that newer job holders are more likely to be studying.

| p4|POB category | Sí (studying) % |
|---|---|
| 1.0 | 34.6% |
| 2.0 | 81.4% |
| 3.0 | 73.9% |
| 4.0 | 50.5% |
| 5.0 | 14.6% |
| 6.0 | 32.0% |
| 7.0 | 53.7% |
| 8.0 | 51.4% |
| 9.0 | 44.4% |
| 10.0 | 9.1% |
| 12.0 | 10.6% |
| 13.0 | 7.1% |
| 14.0 | 68.3% |
| 15.0 | 12.9% |
| 16.0 | 16.7% |
| 18.0 | 0.0% |
| 19.0 | 64.3% |
| 20.0 | 10.6% |
| 21.0 | 4.3% |
| 22.0 | 5.3% |
| 24.0 | 59.7% |
| 40.0 | 4.7% |
| 61.0 | 0.0% |

Receiving educational support (p3|EDU) moderately associates with work status (p1|POB), with support ranging from 26.0% among students to 70.8% among retirees (V=0.185, p=0.000), but the pattern is less clear.

| p1|POB category | Sí (support) % |
|---|---|
| Trabajó | 32.6% |
| No trabajó pero sí tenía trabajo | 31.0% |
| Buscó trabajo | 58.8% |
| Es estudiante | 26.0% |
| Se dedica a los quehaceres de su hogar | 28.0% |
| Está jubilado(a) o pensionado(a) | 70.8% |
| No trabajó | 39.8% |

Demographically, younger respondents (0-18 years) are 84% studying versus only 16% not, while older adults (35-44) are 97% not studying. Men are 21% currently studying compared to 13% of women. Educational support receipt also declines with age and is slightly higher among men.

**p2|EDU** — ¿Usted estudia actualmente?:
| Response | % |
|---|---|
| No | 83.2% |
| Sí | 16.9% |

**p3|EDU** — ¿Cuenta con una beca u otro apoyo económico para realizar sus estudios?:
| Response | % |
|---|---|
| No | 81.2% |
| Sí | 18.3% |

**p1|POB** — La semana pasada usted… (trabajo):
| Response | % |
|---|---|
| Trabajó | 45.4% |
| Se dedica a los quehaceres de su hogar | 22.0% |
| No trabajó | 14.3% |
| Es estudiante | 7.7% |
| Buscó trabajo | 3.8% |
| Está jubilado(a) o pensionado(a) | 3.1% |
| No trabajó pero sí tenía trabajo | 2.6% |


## Complications
Age is the strongest demographic moderator, with a Cramér's V of 0.68 for studying status, reflecting that youth are much more likely to be studying than older adults. Sex also moderates responses moderately (V=0.26 average), with men more likely to be studying and receiving educational support than women. Employment status strongly moderates poverty variables (V=0.56), affecting interpretation of education-poverty links. Minority views include 16.9% currently studying and 18.3% receiving educational support, indicating a significant portion of the population is engaged in education despite poverty. The weak association between educational support and secondary work activities (V=0.064) suggests some complexity in how poverty relates to educational aid. Simulation-based bivariate estimates rely on SES-bridge assumptions and a moderate sample size (n=2000), which may limit subgroup analysis and the precision of some associations. Some variables show dispersed or polarized distributions, such as level of education pursued, complicating a straightforward narrative.

## Implications
First, the strong association between current studying and poverty-related work statuses suggests policies that support students, especially young people and those with unstable or seasonal jobs, could be effective in breaking poverty cycles. Expanding access to education and scholarships for vulnerable working populations may enhance educational attainment and economic mobility.

Second, given the demographic disparities, particularly by age and sex, targeted interventions are necessary. For example, programs encouraging female participation in education and providing support for adult learners could address gaps. The weak link between educational support and informal work highlights the need for more nuanced policies that consider the diversity of poverty experiences and work arrangements in Mexico.

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | 9 |
| Divergence Index | 44.4% |
| Consensus Variables | 5 |
| Lean Variables | 2 |
| Polarized Variables | 1 |
| Dispersed Variables | 1 |

### Variable Details


**p2|EDU** (consensus)
- Question: EDUCACION|¿Usted estudia actualmente?
- Mode: No (83.2%)
- Runner-up: Sí (16.9%), margin: 66.3pp
- HHI: 7198
- Minority opinions: Sí (16.9%)

| Response | % |
|----------|---|
| No | 83.2% |
| Sí | 16.9% |

**p3|EDU** (consensus)
- Question: EDUCACION|¿Cuenta con una beca u otro apoyo económico para realizar sus estudios?
- Mode: No (81.2%)
- Runner-up: Sí (18.3%), margin: 62.8pp
- HHI: 6928
- Minority opinions: Sí (18.3%)

| Response | % |
|----------|---|
| No | 81.2% |
| Sí | 18.3% |
| No sabe/ No contesta | 0.5% |

**p4|EDU** (dispersed)
- Question: EDUCACION|¿Quién le otorga este apoyo?
- Mode: La escuela donde estudio (34.1%)
- Runner-up: PRONABES u otra entidad del gobierno federal (29.0%), margin: 5.0pp
- HHI: 2430
- Minority opinions: PRONABES u otra entidad del gobierno federal (29.0%), El gobierno estatal, municipal o alguna institución  pública (18.3%)

| Response | % |
|----------|---|
| La escuela donde estudio | 34.1% |
| PRONABES u otra entidad del gobierno federal | 29.0% |
| El gobierno estatal, municipal o alguna institución  pública | 18.3% |
| La empresa donde laboro | 5.4% |
| Un familiar | 5.4% |
| No sabe/ No contesta | 5.4% |
| Una organización social no gubernamental o  sindicato | 2.5% |

**p5|EDU** (polarized)
- Question: EDUCACION|¿Qué está usted estudiando?
- Mode: Nivel Medio Superior (47.5%)
- Runner-up: Licenciatura (34.6%), margin: 12.9pp
- HHI: 3565
- Minority opinions: Licenciatura (34.6%)

| Response | % |
|----------|---|
| Nivel Medio Superior | 47.5% |
| Licenciatura | 34.6% |
| Secundaria | 8.4% |
| Posgrado | 5.5% |
| Cursos de capacitación para el trabajo | 2.5% |
| Otro | 1.0% |
| Primaria | 0.5% |

**p6|EDU** (consensus)
- Question: EDUCACION|¿Por qué está usted estudiando?
- Mode: Porque deseo superarme (65.4%)
- Runner-up: Porque deseo aprender (11.4%), margin: 54.0pp
- HHI: 4575

| Response | % |
|----------|---|
| Porque deseo superarme | 65.4% |
| Porque deseo aprender | 11.4% |
| Porque quiero tener un mejor trabajo o un mejor sueldo | 10.4% |
| Porque me gusta estudiar | 6.4% |
| Porque para hacer lo que yo quiero hacer,  necesito estudiar | 4.5% |
| Porque tengo una escuela cerca | 1.0% |
| Porque mis papás me lo exigen | 0.5% |
| Porque me puede dar prestigio | 0.5% |

**p1|POB** (lean)
- Question: POBREZA|Hablemos un poco sobre el trabajo. Dígame, la semana pasada usted…
- Mode: Trabajó (45.4%)
- Runner-up: Se dedica a los quehaceres de su hogar (22.0%), margin: 23.4pp
- HHI: 2843
- Minority opinions: Se dedica a los quehaceres de su hogar (22.0%)

| Response | % |
|----------|---|
| Trabajó | 45.4% |
| Se dedica a los quehaceres de su hogar | 22.0% |
| No trabajó | 14.3% |
| Es estudiante | 7.7% |
| Buscó trabajo | 3.8% |
| Está jubilado(a) o pensionado(a) | 3.1% |
| No trabajó pero sí tenía trabajo | 2.6% |
| Está incapacitado(a) permanentemente para trabajar | 0.9% |
| No sabe/ No contesta | 0.2% |

**p2|POB** (consensus)
- Question: POBREZA|Además de lo que señaló en la pregunta anterior, la semana pasada usted…
- Mode: No trabajó (85.1%)
- Runner-up: Ayudó a trabajar en un negocio familiar (5.6%), margin: 79.5pp
- HHI: 7295

| Response | % |
|----------|---|
| No trabajó | 85.1% |
| Ayudó a trabajar en un negocio familiar | 5.6% |
| Vendió algunos productos: ropa,  cosméticos, alimentos | 4.3% |
| A cambio de un pago realizó otro tipo de  trabajo: lavó, plancho o cosió | 1.5% |
| No sabe/ No contesta | 1.5% |
| Hizo algún producto para vender: alimentos,  artesanías | 1.0% |
| Ayudó a trabajar en las actividades: agrícolas o en la cría de animales | 1.0% |

**p3|POB** (consensus)
- Question: POBREZA|Usted se dedica a su trabajo principal:
- Mode: Permanentemente (66.4%)
- Runner-up: Sólo por temporadas (31.3%), margin: 35.1pp
- HHI: 5390
- Minority opinions: Sólo por temporadas (31.3%)

| Response | % |
|----------|---|
| Permanentemente | 66.4% |
| Sólo por temporadas | 31.3% |
| No sabe/ No contesta | 2.3% |

**p4|POB** (lean)
- Question: POBREZA|¿Desde hace cuántos años se dedica a su trabajo en el lugar donde actualmente labora?
- Mode: Menos de un año (64.3%)
- Runner-up: No sabe/ No contesta (35.7%), margin: 28.5pp
- HHI: 5407
- Minority opinions: No sabe/ No contesta (35.7%)

| Response | % |
|----------|---|
| Menos de un año | 64.3% |
| No sabe/ No contesta | 35.7% |

### Demographic Fault Lines

| Dimension | Mean Cramér's V | Max Cramér's V | Variables |
|-----------|----------------|----------------|----------|
| empleo | 0.564 (strong) | 0.564 | 1 |
| edad | 0.300 (strong) | 0.676 | 9 |
| sexo | 0.255 (moderate) | 0.514 | 8 |

**Variable-Level Demographic Detail:**

*p2|EDU*
- edad: V=0.676 (p=0.000) — 0-18:  Sí (84%); 19-24:  Sí (51%); 25-34:  No (94%)
- sexo: V=0.101 (p=0.001) —  Hombre:  No (79%);  Mujer:  No (87%)

*p3|EDU*
- edad: V=0.396 (p=0.000) — 0-18:  No (64%); 19-24: -1.0 (49%); 25-34: -1.0 (94%)
- sexo: V=0.104 (p=0.005) —  Hombre: -1.0 (79%);  Mujer: -1.0 (87%)

*p4|EDU*
- edad: V=0.137 (p=0.000) — 0-18: -1.0 (80%); 19-24: -1.0 (92%); 25-34: -1.0 (100%)

*p5|EDU*
- edad: V=0.332 (p=0.000) — 0-18: Nivel Medio Superior (71%); 19-24: -1.0 (49%); 25-34: -1.0 (94%)
- sexo: V=0.141 (p=0.001) —  Hombre: -1.0 (79%);  Mujer: -1.0 (87%)

*p6|EDU*
- edad: V=0.289 (p=0.000) — 0-18: Porque deseo superarme (57%); 19-24: -1.0 (49%); 25-34: -1.0 (94%)
- sexo: V=0.119 (p=0.031) —  Hombre: -1.0 (79%);  Mujer: -1.0 (87%)

*p1|POB*
- sexo: V=0.514 (p=0.000) —  Hombre: Trabajó (63%);  Mujer: Se dedica a los quehaceres de su hogar (40%)
- edad: V=0.312 (p=0.000) — 0-18: Es estudiante (60%); 19-24: Es estudiante (36%); 25-34: Trabajó (48%)

*p2|POB*
- sexo: V=0.326 (p=0.000) —  Hombre: -1.0 (82%);  Mujer: -1.0 (53%)
- edad: V=0.126 (p=0.000) — 0-18: No trabajó (60%); 19-24: -1.0 (53%); 25-34: -1.0 (72%)

*p3|POB*
- sexo: V=0.355 (p=0.000) —  Hombre: Permanentemente (54%);  Mujer: -1.0 (59%)
- edad: V=0.171 (p=0.000) — 0-18: -1.0 (86%); 19-24: -1.0 (59%); 25-34: Permanentemente (40%)

*p4|POB*
- empleo: V=0.564 (p=0.000) — 01: -1.0 (50%); 02: -1.0 (31%); 03: -1.0 (42%)
- sexo: V=0.382 (p=0.000) —  Hombre: -1.0 (26%);  Mujer: -1.0 (59%)
- edad: V=0.257 (p=0.000) — 0-18: -1.0 (86%); 19-24: -1.0 (59%); 25-34: -1.0 (39%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p2|EDU × p1|POB | 0.352 (strong) | 0.000 | " Sí": 3% ("Está jubilado(a) o pensionado(a)") → 67% ("Es estudiante") | 2000 |
| p2|EDU × p2|POB | 0.176 (moderate) | 0.000 | " Sí": 30% ("Ayudó a trabajar en un negocio familiar") → 73% ("Vendió algunos productos: ropa,  cosméticos, alimentos") | 2000 |
| p2|EDU × p3|POB | 0.249 (moderate) | 0.000 | " Sí": 30% ("Permanentemente") → 56% ("Sólo por temporadas") | 2000 |
| p2|EDU × p4|POB | 0.519 (strong) | 0.000 | " Sí": 0% ("18.0") → 81% ("2.0") | 2000 |
| p3|EDU × p1|POB | 0.185 (moderate) | 0.000 | " Sí": 26% ("Es estudiante") → 71% ("Está jubilado(a) o pensionado(a)") | 2000 |
| p3|EDU × p2|POB | 0.064 (weak) | 0.017 | " Sí": 31% ("No trabajó") → 43% ("Vendió algunos productos: ropa,  cosméticos, alimentos") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p2|EDU × p1|POB** — How p2|EDU distributes given p1|POB:

| p1|POB (conditioning) | Top p2|EDU responses |
|---|---|
| Trabajó |  No: 72%,  Sí: 28% |
| No trabajó pero sí tenía trabajo |  No: 52%,  Sí: 48% |
| Buscó trabajo |  Sí: 58%,  No: 42% |
| Es estudiante |  Sí: 67%,  No: 33% |
| Se dedica a los quehaceres de su hogar |  No: 65%,  Sí: 35% |
| Está jubilado(a) o pensionado(a) |  No: 97%,  Sí: 3% |
| No trabajó |  No: 69%,  Sí: 31% |

**p2|EDU × p2|POB** — How p2|EDU distributes given p2|POB:

| p2|POB (conditioning) | Top p2|EDU responses |
|---|---|
| Ayudó a trabajar en un negocio familiar |  No: 70%,  Sí: 30% |
| Vendió algunos productos: ropa,  cosméticos, alimentos |  Sí: 73%,  No: 27% |
| No trabajó |  No: 64%,  Sí: 36% |

**p2|EDU × p3|POB** — How p2|EDU distributes given p3|POB:

| p3|POB (conditioning) | Top p2|EDU responses |
|---|---|
| Permanentemente |  No: 70%,  Sí: 30% |
| Sólo por temporadas |  Sí: 56%,  No: 44% |

**p2|EDU × p4|POB** — How p2|EDU distributes given p4|POB:

| p4|POB (conditioning) | Top p2|EDU responses |
|---|---|
| 1.0 |  No: 65%,  Sí: 35% |
| 2.0 |  Sí: 81%,  No: 19% |
| 3.0 |  Sí: 74%,  No: 26% |
| 4.0 |  Sí: 50%,  No: 50% |
| 5.0 |  No: 85%,  Sí: 15% |
| 6.0 |  No: 68%,  Sí: 32% |
| 7.0 |  Sí: 54%,  No: 46% |
| 8.0 |  Sí: 51%,  No: 49% |

**p3|EDU × p1|POB** — How p3|EDU distributes given p1|POB:

| p1|POB (conditioning) | Top p3|EDU responses |
|---|---|
| Trabajó |  No: 67%,  Sí: 33% |
| No trabajó pero sí tenía trabajo |  No: 69%,  Sí: 31% |
| Buscó trabajo |  Sí: 59%,  No: 41% |
| Es estudiante |  No: 74%,  Sí: 26% |
| Se dedica a los quehaceres de su hogar |  No: 72%,  Sí: 28% |
| Está jubilado(a) o pensionado(a) |  Sí: 71%,  No: 29% |
| No trabajó |  No: 60%,  Sí: 40% |

**p3|EDU × p2|POB** — How p3|EDU distributes given p2|POB:

| p2|POB (conditioning) | Top p3|EDU responses |
|---|---|
| Ayudó a trabajar en un negocio familiar |  No: 68%,  Sí: 32% |
| Vendió algunos productos: ropa,  cosméticos, alimentos |  No: 57%,  Sí: 43% |
| No trabajó |  No: 69%,  Sí: 31% |
### Bridge Model Diagnostics

> For human inspection only — not passed to the LLM.

#### Summary

| Variable | Model | Pseudo-R² | LLR p | Dominant SES | Quality |
|----------|-------|-----------|-------|--------------|---------|
| p1|POB | mnlogit | 0.288 | 0.000 | edad | good |
| p2|EDU | mnlogit | 0.646 | 0.000 | edad | good |
| p2|POB | mnlogit | 0.482 | 0.112 | region | weak |
| p3|EDU | mnlogit | 0.331 | 0.009 | edad | good |
| p3|POB | mnlogit | 0.274 | 0.002 | edad | good |
| p4|POB | mnlogit | 0.461 | 0.555 | escol | weak |

**Mean pseudo-R²:** 0.414 &ensp;|&ensp; **Overall dominant SES dimension:** edad

> ⚠ 2/6 bridge models are weak (R²<0.02 or LLR p≥0.10). Simulated Cramér's V for those variables may underestimate the true association.

#### Per-Variable SES Predictor Detail

Top predictors by |t|-statistic — answers: which SES variable is doing the work?

**p1|POB** (mnlogit, R²=0.288, LLR p=0.000, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| edad | -0.317 | 0.403 | -4.617 | 0.000 |
| sexo | 1.007 | 0.921 | 4.053 | 0.000 |
| escol | -0.428 | 0.427 | -2.229 | 0.026 |
| est_civil_2.0 | -0.612 | 1.506 | 2.004 | 0.045 |
| region_04 | -0.457 | 2.120 | -1.946 | 0.052 |
| region_03 | -0.324 | 1.812 | -1.833 | 0.067 |

**p2|EDU** (mnlogit, R²=0.646, LLR p=0.000, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| edad | 2.385 | 0.493 | 4.838 | 0.000 |
| est_civil_6.0 | -2.731 | 0.697 | -3.920 | 0.000 |
| escol | 1.408 | 0.633 | 2.224 | 0.026 |
| est_civil_2.0 | -3.237 | 1.802 | -1.796 | 0.072 |
| region_02 | -1.259 | 0.838 | -1.503 | 0.133 |
| Tam_loc | 0.541 | 0.429 | 1.262 | 0.207 |

**p2|POB** (mnlogit, R²=0.482, LLR p=0.112, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_03 | 9.228 | 6.639 | 1.430 | 0.153 |
| region_02 | 5.856 | 4.489 | 1.419 | 0.156 |
| edad | -1.145 | 0.960 | -1.402 | 0.161 |
| escol | 1.188 | 1.281 | 1.307 | 0.191 |
| Tam_loc | -3.920 | 4.614 | -1.300 | 0.194 |
| sexo | 0.347 | 75.734 | -1.236 | 0.216 |

**p3|EDU** (mnlogit, R²=0.331, LLR p=0.009, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| edad | -1.462 | 0.745 | -1.963 | 0.050 |
| est_civil_2.0 | -4.634 | 2.933 | -1.580 | 0.114 |
| region_02 | 1.405 | 0.919 | 1.529 | 0.126 |
| empleo_03 | -5.199 | 3.444 | -1.510 | 0.131 |
| est_civil_6.0 | -3.403 | 2.377 | -1.431 | 0.152 |
| escol | 2.125 | 1.619 | 1.312 | 0.190 |

**p3|POB** (mnlogit, R²=0.274, LLR p=0.002, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| edad | -0.894 | 0.339 | -2.638 | 0.008 |
| sexo | 1.258 | 0.641 | 1.965 | 0.049 |
| est_civil_2.0 | -1.943 | 1.091 | -1.780 | 0.075 |
| escol | -0.345 | 0.326 | -1.057 | 0.291 |
| region_03 | 0.653 | 1.160 | 0.563 | 0.574 |
| region_04 | 0.626 | 1.287 | 0.486 | 0.627 |

**p4|POB** (mnlogit, R²=0.461, LLR p=0.555, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| escol | -1.814 | 4.702 | -2.677 | 0.007 |
| Tam_loc | -0.201 | 9.244 | 1.922 | 0.055 |
| edad | 0.949 | 2.181 | 1.657 | 0.098 |
| est_civil_6.0 | -0.282 | 24.301 | 1.452 | 0.146 |
| sexo | -0.497 | 7.152 | 1.265 | 0.206 |
| est_civil_2.0 | 0.211 | 13.639 | 1.209 | 0.227 |

*Pseudo-R² = McFadden's. Low values mean SES explains little variance in that variable — the bridge simulation still produces an estimate, but its precision is reduced.*

### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from the cross-dataset bivariate associations with significant p-values, especially those involving p2|EDU (currently studying) and various poverty-related variables (p1|POB to p4|POB), which show moderate to strong associations. Next in strength are demographic fault lines that provide context on how education and poverty variables vary by age, sex, and employment. Univariate distributions offer supporting background but do not establish relationships on their own.

**Key Limitations:**
- All bivariate associations are simulation-based estimates, which may have inherent uncertainty.
- Sample size is moderate (n=2000), which supports significance but may limit subgroup analysis.
- Only a limited number of cross-survey variable pairs are available, restricting the scope of relationship analysis.
- Some variables (e.g., motivation for studying) relate only indirectly to poverty, limiting their explanatory power for the query.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p5|EDU
- **Dispersed Variables:** p4|EDU

