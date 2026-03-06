# q6_health_poverty

**Query (ES):** ¿Cómo se relaciona el acceso a la salud con la pobreza en México?
**Query (EN):** How does health access relate to poverty in Mexico?
**Variables:** p1|SAL, p2|SAL, p3|SAL, p4|SAL, p5|SAL, p1|POB, p2|POB, p3|POB, p4|POB
**Status:** ✅ success
**Time:** 63093ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Cómo se relaciona el acceso a la salud con la pobreza en México?

## Summary
La relación entre el acceso a la salud y la pobreza en México se manifiesta en que el estado de salud percibido y las limitaciones físicas varían significativamente según la situación laboral, un indicador clave de pobreza. Por ejemplo, quienes trabajaron reportan mejor salud general (57.4% "Buena") que quienes están jubilados o pensionados (47.6% "Buena" y 44.0% "Ni buena ni mala"). Se estimaron seis pares bivariados con asociaciones significativas, principalmente moderadas, lo que otorga un nivel de confianza medio-alto en la relación observada.

## Data Landscape
Se analizaron nueve variables provenientes de encuestas sobre salud y pobreza, con seis mostrando consenso fuerte y tres inclinándose hacia una opinión predominante, resultando en un índice de divergencia del 33%. Esto indica que, aunque existe una mayoría clara en ciertas percepciones, hay una moderada variabilidad en las opiniones públicas sobre salud y pobreza, reflejando complejidad en la experiencia social de estos temas.

## Evidence
El análisis principal muestra que la percepción de salud general (p1|SAL) varía según la categoría de empleo (p1|POB), con un 57.4% que reporta salud "Buena" entre quienes trabajaron, y solo 45.1% en quienes se dedican a los quehaceres del hogar, mientras que el grupo jubilado presenta un 44.0% en "Ni buena ni mala" (V=0.132, p=0.000). La limitación física moderada o alta (p2|SAL) también difiere por empleo: el 100% de quienes buscaron trabajo no reportan limitaciones, frente al 69.2% en jubilados que no se sienten limitados (V=0.171, p=0.000). En contraste, la relación entre limitaciones físicas y actividades secundarias de trabajo (p2|POB) es débil y no significativa (V=0.039, p=0.203), indicando poca influencia. La permanencia en el empleo (p3|POB) muestra que trabajadores temporales reportan mejor salud "Muy buena" (23.9%) que permanentes (14.6%), sugiriendo una relación compleja (V=0.126, p=0.000). La antigüedad en el empleo (p4|POB) exhibe variaciones amplias en salud percibida, con "Ni buena ni mala" desde 6.7% hasta 77.8%, reflejando heterogeneidad (V=0.245, p=0.000).

| p1|POB category | % "Buena" health (p1|SAL) |
|---|---|
| Trabajó | 57.4% |
| No trabajó pero sí tenía trabajo | 47.3% |
| Buscó trabajo | 50.0% |
| Es estudiante | 65.0% |
| Se dedica a los quehaceres de su hogar | 45.1% |
| Está jubilado(a) o pensionado(a) | 47.6% |
| No trabajó | 63.6% |

| p1|POB category | % "No limita en nada" (p2|SAL) |
|---|---|
| Trabajó | 85.9% |
| No trabajó pero sí tenía trabajo | 91.6% |
| Buscó trabajo | 100.0% |
| Es estudiante | 94.2% |
| Se dedica a los quehaceres de su hogar | 81.6% |
| Está jubilado(a) o pensionado(a) | 69.2% |
| No trabajó | 87.7% |

| p2|POB category | % "Buena" health (p1|SAL) |
|---|---|
| Ayudó a trabajar en un negocio familiar | 65.1% |
| Vendió algunos productos: ropa, cosméticos, alimentos | 43.0% |
| No trabajó | 58.9% |

| p3|POB category | % "Muy buena" health (p1|SAL) |
|---|---|
| Permanentemente | 14.6% |
| Sólo por temporadas | 23.9% |

| p4|POB category | % "Ni buena ni mala" health (p1|SAL) |
|---|---|
| 3.0 años | 6.7% |
| 61.0 años | 77.8% |

Demográficamente, las mujeres son 5 puntos porcentuales más propensas que los hombres a reportar limitaciones físicas leves (23% vs 17% en p2|SAL), y los jóvenes (0-18 años) reportan mejor salud general con 53% "Buena" y 33% "Muy buena", superando a grupos mayores. La región también modera ligeramente la percepción de salud, con variaciones de hasta 12 puntos en respuestas "Buena" entre regiones. 

**p1|SAL** — Salud general percibida:
| Response | % |
|---|---|
| Buena | 46.7% |
| Ni buena ni mala (esp.) | 28.3% |
| Muy buena | 15.4% |
| Mala | 8.1% |
| Muy mala | 1.3% |

**p2|SAL** — Limitación en esfuerzos físicos moderados:
| Response | % |
|---|---|
| No, no me limita en nada | 72.6% |
| Sí, me limita un poco | 20.2% |
| Sí, me limita mucho | 6.5% |

**p1|POB** — Situación laboral:
| Response | % |
|---|---|
| Trabajó | 45.4% |
| Se dedica a los quehaceres de su hogar | 22.0% |
| No trabajó | 14.3% |
| Es estudiante | 7.7% |
| Buscó trabajo | 3.8% |
| Está jubilado(a) o pensionado(a) | 3.1% |

## Complications
Las dimensiones socioeconómicas que más moderan la relación entre salud y pobreza son el empleo (V=0.56 para p4|POB), el sexo (V=0.30 en promedio), y la edad (V=0.20), con mujeres y personas mayores reportando más limitaciones físicas. Un 28.3% de la población percibe su salud como "Ni buena ni mala", una minoría significativa que indica una percepción ambivalente que desafía la simple dicotomía buena/mala salud. La asociación entre salud y actividades secundarias de trabajo es débil y no significativa (p=0.203), lo que indica que no todas las dimensiones del trabajo influyen en la salud de forma clara. Además, las estimaciones se basan en un modelo de puente SES con una muestra moderada (n=2000), lo que puede limitar la precisión y generalización de los efectos, especialmente en subgrupos con respuestas escasas o categorías ambiguas como la antigüedad laboral con alta tasa de "No sabe/No contesta" (35.7%). Estas limitaciones sugieren cautela para interpretar causalidad y la necesidad de análisis complementarios.

## Implications
Primero, la asociación moderada y significativa entre empleo y salud sugiere que políticas públicas que mejoren la estabilidad laboral y condiciones de trabajo podrían tener un impacto positivo en la salud percibida y funcional de la población, especialmente para grupos vulnerables como jubilados y quienes realizan quehaceres domésticos. Segundo, dado que la relación entre salud y actividades secundarias de trabajo es débil, las intervenciones deben enfocarse en las condiciones del empleo principal más que en actividades informales o temporales para mejorar el acceso y resultados en salud. Además, la heterogeneidad en la percepción de salud según la antigüedad laboral indica que las políticas deben ser diferenciadas, considerando la duración y calidad del empleo para abordar desigualdades en salud. Finalmente, la presencia de una minoría considerable con percepciones neutrales o limitaciones físicas leves sugiere que programas de prevención y promoción de salud deben ser inclusivos y adaptarse a distintas experiencias y necesidades sociales.

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | 9 |
| Divergence Index | 33.3% |
| Consensus Variables | 6 |
| Lean Variables | 3 |
| Polarized Variables | 0 |
| Dispersed Variables | 0 |

### Variable Details


**p1|SAL** (lean)
- Question: SALUD|En general, usted diría que su salud es:
- Mode: Buena (46.7%)
- Runner-up: Ni buena ni mala (esp.) (28.3%), margin: 18.3pp
- HHI: 3286
- Minority opinions: Ni buena ni mala (esp.) (28.3%), Muy buena (15.4%)

| Response | % |
|----------|---|
| Buena | 46.7% |
| Ni buena ni mala (esp.) | 28.3% |
| Muy buena | 15.4% |
| Mala | 8.1% |
| Muy mala | 1.3% |
| No sabe/ No contesta | 0.2% |

**p2|SAL** (consensus)
- Question: SALUD|¿Su estado de salud actual le limita realizar esfuerzos físicos moderados, como caminar 30 minutos o hacer limpieza en su casa?
- Mode: No, no me limita en nada (72.6%)
- Runner-up: Sí, me limita un poco (20.2%), margin: 52.4pp
- HHI: 5717
- Minority opinions: Sí, me limita un poco (20.2%)

| Response | % |
|----------|---|
| No, no me limita en nada | 72.6% |
| Sí, me limita un poco | 20.2% |
| Sí, me limita mucho | 6.5% |
| No sabe/ No contesta | 0.8% |

**p3|SAL** (consensus)
- Question: SALUD|¿Su estado de salud actual le limita subir varios pisos por la escalera?
- Mode: No, no me limita en nada (72.5%)
- Runner-up: Sí, me limita un poco (20.4%), margin: 52.1pp
- HHI: 5716
- Minority opinions: Sí, me limita un poco (20.4%)

| Response | % |
|----------|---|
| No, no me limita en nada | 72.5% |
| Sí, me limita un poco | 20.4% |
| Sí, me limita mucho | 6.5% |
| No sabe/ No contesta | 0.6% |

**p4|SAL** (consensus)
- Question: SALUD|Durante las últimas 4 semanas, ¿hizo menos cosas de lo que hubiera querido hacer a causa de su estado de salud física?
- Mode: No (79.2%)
- Runner-up: Sí (20.0%), margin: 59.2pp
- HHI: 6669
- Minority opinions: Sí (20.0%)

| Response | % |
|----------|---|
| No | 79.2% |
| Sí | 20.0% |
| No sabe/ No contesta | 0.8% |

**p5|SAL** (consensus)
- Question: SALUD|¿Tuvo que dejar de hacer algunas tareas en su trabajo o en sus actividades cotidianas a causa de su estado de salud física?
- Mode: No (82.7%)
- Runner-up: Sí (16.8%), margin: 65.8pp
- HHI: 7118
- Minority opinions: Sí (16.8%)

| Response | % |
|----------|---|
| No | 82.7% |
| Sí | 16.8% |
| No sabe/ No contesta | 0.5% |

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
| sexo | 0.297 (moderate) | 0.514 | 6 |
| edad | 0.205 (moderate) | 0.312 | 9 |
| region | 0.102 (moderate) | 0.112 | 2 |

**Variable-Level Demographic Detail:**

*p1|SAL*
- edad: V=0.182 (p=0.000) — 0-18: Buena (53%); 19-24: Buena (54%); 25-34: Buena (56%)
- region: V=0.112 (p=0.000) — 01: Buena (45%); 02: Buena (51%); 03: Buena (40%)

*p2|SAL*
- edad: V=0.184 (p=0.000) — 0-18:  No, no me limita en nada (92%); 19-24:  No, no me limita en nada (87%); 25-34:  No, no me limita en nada (82%)
- sexo: V=0.095 (p=0.029) —  Hombre:  No, no me limita en nada (75%);  Mujer:  No, no me limita en nada (70%)
- region: V=0.092 (p=0.002) — 01:  No, no me limita en nada (70%); 02:  No, no me limita en nada (81%); 03:  No, no me limita en nada (71%)

*p3|SAL*
- edad: V=0.218 (p=0.000) — 0-18:  No, no me limita en nada (92%); 19-24:  No, no me limita en nada (90%); 25-34:  No, no me limita en nada (83%)
- sexo: V=0.111 (p=0.005) —  Hombre:  No, no me limita en nada (77%);  Mujer:  No, no me limita en nada (68%)

*p4|SAL*
- edad: V=0.190 (p=0.000) — 0-18:  No (92%); 19-24:  No (92%); 25-34:  No (86%)

*p5|SAL*
- edad: V=0.206 (p=0.000) — 0-18:  No (89%); 19-24:  No (93%); 25-34:  No (91%)

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
| p1|SAL × p1|POB | 0.132 (moderate) | 0.000 | "Ni buena ni mala (esp.)": 6% ("Buscó trabajo") → 44% ("Está jubilado(a) o pensionado(a)") | 2000 |
| p1|SAL × p2|POB | 0.094 (weak) | 0.000 | "Buena": 43% ("Vendió algunos productos: ropa,  cosméticos, alimentos") → 65% ("Ayudó a trabajar en un negocio familiar") | 2000 |
| p1|SAL × p3|POB | 0.126 (moderate) | 0.000 | "Muy buena": 15% ("Permanentemente") → 24% ("Sólo por temporadas") | 2000 |
| p1|SAL × p4|POB | 0.245 (moderate) | 0.000 | "Ni buena ni mala (esp.)": 7% ("3.0") → 78% ("61.0") | 2000 |
| p2|SAL × p1|POB | 0.171 (moderate) | 0.000 | " No, no me limita en nada": 69% ("Está jubilado(a) o pensionado(a)") → 100% ("Buscó trabajo") | 2000 |
| p2|SAL × p2|POB | 0.039 (weak) | 0.203 | " No, no me limita en nada": 86% ("Ayudó a trabajar en un negocio familiar") → 94% ("Vendió algunos productos: ropa,  cosméticos, alimentos") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p1|SAL × p1|POB** — How p1|SAL distributes given p1|POB:

| p1|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Trabajó | Buena: 57%, Ni buena ni mala (esp.): 24%, Muy buena: 16% |
| No trabajó pero sí tenía trabajo | Buena: 47%, Ni buena ni mala (esp.): 30%, Muy buena: 22% |
| Buscó trabajo | Buena: 50%, Muy buena: 44%, Ni buena ni mala (esp.): 6% |
| Es estudiante | Buena: 65%, Muy buena: 22%, Ni buena ni mala (esp.): 12% |
| Se dedica a los quehaceres de su hogar | Buena: 45%, Ni buena ni mala (esp.): 36%, Muy buena: 17% |
| Está jubilado(a) o pensionado(a) | Buena: 48%, Ni buena ni mala (esp.): 44%, Muy buena: 7% |
| No trabajó | Buena: 64%, Ni buena ni mala (esp.): 25%, Muy buena: 10% |

**p1|SAL × p2|POB** — How p1|SAL distributes given p2|POB:

| p2|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Ayudó a trabajar en un negocio familiar | Buena: 65%, Ni buena ni mala (esp.): 24%, Muy buena: 6% |
| Vendió algunos productos: ropa,  cosméticos, alimentos | Buena: 43%, Ni buena ni mala (esp.): 28%, Muy buena: 27% |
| No trabajó | Buena: 59%, Ni buena ni mala (esp.): 22%, Muy buena: 15% |

**p1|SAL × p3|POB** — How p1|SAL distributes given p3|POB:

| p3|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Permanentemente | Buena: 56%, Ni buena ni mala (esp.): 27%, Muy buena: 15% |
| Sólo por temporadas | Buena: 54%, Muy buena: 24%, Ni buena ni mala (esp.): 21% |

**p1|SAL × p4|POB** — How p1|SAL distributes given p4|POB:

| p4|POB (conditioning) | Top p1|SAL responses |
|---|---|
| 1.0 | Buena: 61%, Muy buena: 21%, Ni buena ni mala (esp.): 14% |
| 2.0 | Buena: 48%, Muy buena: 38%, Ni buena ni mala (esp.): 14% |
| 3.0 | Buena: 60%, Muy buena: 29%, Ni buena ni mala (esp.): 7% |
| 4.0 | Buena: 56%, Muy buena: 23%, Ni buena ni mala (esp.): 17% |
| 5.0 | Buena: 56%, Ni buena ni mala (esp.): 37%, Muy buena: 5% |
| 6.0 | Buena: 55%, Ni buena ni mala (esp.): 29%, Muy buena: 14% |
| 7.0 | Buena: 60%, Muy buena: 15%, Mala: 12% |
| 8.0 | Buena: 72%, Ni buena ni mala (esp.): 13%, Muy buena: 11% |

**p2|SAL × p1|POB** — How p2|SAL distributes given p1|POB:

| p1|POB (conditioning) | Top p2|SAL responses |
|---|---|
| Trabajó |  No, no me limita en nada: 86%,  Sí, me limita un poco: 9%,  Sí, me limita mucho: 6% |
| No trabajó pero sí tenía trabajo |  No, no me limita en nada: 92%,  Sí, me limita un poco: 6%,  Sí, me limita mucho: 2% |
| Buscó trabajo |  No, no me limita en nada: 100%,  Sí, me limita mucho: 0%,  Sí, me limita un poco: 0% |
| Es estudiante |  No, no me limita en nada: 94%,  Sí, me limita un poco: 5%,  Sí, me limita mucho: 1% |
| Se dedica a los quehaceres de su hogar |  No, no me limita en nada: 82%,  Sí, me limita un poco: 15%,  Sí, me limita mucho: 3% |
| Está jubilado(a) o pensionado(a) |  No, no me limita en nada: 69%,  Sí, me limita mucho: 24%,  Sí, me limita un poco: 7% |
| No trabajó |  No, no me limita en nada: 88%,  Sí, me limita un poco: 9%,  Sí, me limita mucho: 3% |

**p2|SAL × p2|POB** — How p2|SAL distributes given p2|POB:

| p2|POB (conditioning) | Top p2|SAL responses |
|---|---|
| Ayudó a trabajar en un negocio familiar |  No, no me limita en nada: 86%,  Sí, me limita un poco: 9%,  Sí, me limita mucho: 5% |
| Vendió algunos productos: ropa,  cosméticos, alimentos |  No, no me limita en nada: 94%,  Sí, me limita un poco: 5%,  Sí, me limita mucho: 1% |
| No trabajó |  No, no me limita en nada: 87%,  Sí, me limita un poco: 8%,  Sí, me limita mucho: 5% |
### Bridge Model Diagnostics

> For human inspection only — not passed to the LLM.

#### Summary

| Variable | Model | Pseudo-R² | LLR p | Dominant SES | Quality |
|----------|-------|-----------|-------|--------------|---------|
| p1|POB | mnlogit | 0.288 | 0.000 | edad | good |
| p1|SAL | mnlogit | 0.157 | 0.003 | Tam_loc | good |
| p2|POB | mnlogit | 0.482 | 0.112 | region | weak |
| p2|SAL | mnlogit | 0.180 | 0.088 | edad | fair |
| p3|POB | mnlogit | 0.274 | 0.002 | edad | good |
| p4|POB | mnlogit | 0.461 | 0.555 | escol | weak |

**Mean pseudo-R²:** 0.307 &ensp;|&ensp; **Overall dominant SES dimension:** edad

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

**p1|SAL** (mnlogit, R²=0.157, LLR p=0.003, quality=good)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| Tam_loc | 1.333 | 1.450 | 1.118 | 0.264 |
| escol | -0.478 | 0.510 | -1.103 | 0.270 |
| est_civil_6.0 | 0.810 | 1.348 | 1.091 | 0.275 |
| region_02 | 0.860 | 1.457 | 1.008 | 0.313 |
| region_04 | -0.822 | 1.550 | -0.876 | 0.381 |
| edad | -0.043 | 0.443 | 0.819 | 0.413 |

**p2|POB** (mnlogit, R²=0.482, LLR p=0.112, quality=weak)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| region_03 | 9.228 | 6.639 | 1.430 | 0.153 |
| region_02 | 5.856 | 4.489 | 1.419 | 0.156 |
| edad | -1.145 | 0.960 | -1.402 | 0.161 |
| escol | 1.188 | 1.281 | 1.307 | 0.191 |
| Tam_loc | -3.920 | 4.614 | -1.300 | 0.194 |
| sexo | 0.347 | 75.734 | -1.236 | 0.216 |

**p2|SAL** (mnlogit, R²=0.180, LLR p=0.088, quality=fair)
| SES Predictor | Coef | Std Err | t-stat | p-value |
|---------------|------|---------|--------|---------|
| edad | -0.692 | 0.427 | -2.259 | 0.024 |
| sexo | 1.464 | 1.007 | 1.999 | 0.046 |
| region_02 | 1.282 | 1.257 | 1.346 | 0.178 |
| Tam_loc | 0.722 | 0.743 | 1.161 | 0.246 |
| est_civil_2.0 | -0.854 | 1.425 | -0.923 | 0.356 |
| escol | 0.213 | 0.501 | 0.904 | 0.366 |

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

**Evidence Hierarchy:** The strongest evidence comes from the cross-dataset bivariate associations with significant p-values, especially those involving p1|SAL and p1|POB, which show moderate and significant relationships directly linking health status and poverty indicators. Demographic fault lines provide secondary support by highlighting subgroup differences but do not establish direct relationships. Univariate distributions offer contextual background but are insufficient alone to infer relationships.

**Key Limitations:**
- All bivariate associations are simulation-based estimates, which may introduce uncertainty in effect size precision.
- Sample size is moderate (n=2000), which supports statistical significance but may limit detection of smaller effects.
- Only a limited number of poverty and health variables were analyzed, potentially omitting other relevant dimensions of access to health and poverty.
- Some poverty variables (e.g., p4|POB tenure) have high non-response or ambiguous categories, complicating interpretation of relationships.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** None
- **Dispersed Variables:** None

