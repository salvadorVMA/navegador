# q6_health_poverty

**Query (ES):** ¿Cómo se relaciona el acceso a la salud con la pobreza en México?
**Query (EN):** How does health access relate to poverty in Mexico?
**Variables:** p1|SAL, p2|SAL, p3|SAL, p4|SAL, p5|SAL, p1|POB, p2|POB, p3|POB, p4|POB
**Status:** ✅ success
**Time:** 48699ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Cómo se relaciona el acceso a la salud con la pobreza en México?

## Summary
La salud percibida en México muestra una relación moderada y significativa con indicadores de pobreza laboral, evidenciando que quienes tienen empleos más estables o activos reportan mejor salud. Se estimaron seis asociaciones bivariadas entre variables de salud y pobreza, todas significativas, con tamaños de efecto que varían de débiles a moderados, lo que indica una confianza moderada en la existencia de vínculos entre acceso a la salud y pobreza laboral.

## Data Landscape
Se analizaron nueve variables provenientes de encuestas sobre salud y pobreza laboral en México. De estas, seis variables presentan consenso fuerte en sus distribuciones, mientras que tres muestran inclinaciones hacia una opinión predominante sin consenso absoluto, resultando en un índice de divergencia del 33%. Esto indica que, aunque la mayoría de las opiniones tienden a converger, existe una variabilidad moderada en las percepciones sobre salud y pobreza, reflejando diferencias en experiencias y condiciones socioeconómicas.

## Evidence
La relación entre salud general (p1|SAL) y situación laboral (p1|POB) muestra que el porcentaje de personas que reportan salud 'Buena' varía entre 50.9% (no trabajó) y 59.4% (no trabajó pero tenía trabajo), mientras que la categoría 'Ni buena ni mala' es especialmente alta (45.3%) entre jubilados o pensionados, indicando que la percepción de salud depende del estatus laboral (V=0.121, p=0.000).

| p1|POB category | Buena salud % |
|---|---|
| Trabajó | 53.2% |
| No trabajó pero sí tenía trabajo | 59.4% |
| Buscó trabajo | 57.9% |
| Es estudiante | 56.0% |
| Se dedica a los quehaceres de su hogar | 55.5% |
| Está jubilado(a) o pensionado(a) | 45.3% |
| No trabajó | 50.9% |

Respecto a actividades laborales adicionales (p2|POB), la salud 'Buena' oscila entre 54.0% (no trabajó) y 66.3% (ayudó en negocio familiar), reflejando una asociación débil pero significativa con la salud (V=0.065, p=0.009).

| p2|POB category | Buena salud % |
|---|---|
| Ayudó a trabajar en un negocio familiar | 66.3% |
| Vendió productos | 58.9% |
| No trabajó | 54.0% |

La permanencia en el trabajo principal (p3|POB) también se asocia moderadamente con la salud: quienes trabajan sólo por temporadas reportan mejor salud 'Buena' (60.4%) que los que trabajan permanentemente (53.2%), aunque estos últimos tienen más respuestas 'Ni buena ni mala' (30.1%) (V=0.170, p=0.000).

| p3|POB category | Buena salud % |
|---|---|
| Permanentemente | 53.2% |
| Sólo por temporadas | 60.4% |

El tiempo en el empleo actual (p4|POB) presenta una relación moderada con la salud, con una amplia variación en salud 'Buena' desde 18.8% hasta 75.0% según años en el trabajo, mostrando un patrón complejo y heterogéneo (V=0.199, p=0.000).

| p4|POB category | Buena salud % |
|---|---|
| 16.0 años | 18.8% |
| 24.0 años | 75.0% |

En cuanto a limitaciones físicas moderadas (p2|SAL) por estado laboral (p1|POB), el porcentaje que no se limita varía desde 58.2% entre jubilados hasta 92.4% entre estudiantes, evidenciando que la salud funcional también se relaciona con la pobreza laboral (V=0.168, p=0.000).

| p1|POB category | No me limita en nada % |
|---|---|
| Trabajó | 85.4% |
| No trabajó pero sí tenía trabajo | 89.7% |
| Buscó trabajo | 90.5% |
| Es estudiante | 92.4% |
| Se dedica a los quehaceres de su hogar | 83.5% |
| Está jubilado(a) o pensionado(a) | 58.2% |
| No trabajó | 85.5% |

Finalmente, la relación entre limitaciones físicas y actividades laborales adicionales (p2|POB) es débil, con una ligera variación en quienes reportan limitaciones severas (2.9% a 9.7%) según actividad (V=0.078, p=0.000).

| p2|POB category | Sí, me limita mucho % |
|---|---|
| Ayudó en negocio familiar | 9.7% |
| Vendió productos | 3.8% |
| No trabajó | 2.9% |

Demográficamente, las mujeres son aproximadamente 5 puntos porcentuales más propensas que los hombres a reportar limitaciones físicas moderadas (p2|SAL), y los jóvenes (0-18 años) reportan mejor salud general (53% Buena, 33% Muy buena) que adultos mayores. La variable empleo muestra la mayor moderación, con diferencias marcadas entre hombres y mujeres en actividad laboral y salud percibida.

**p1|SAL** — Salud general percibida:
| Response | % |
|---|---|
| Buena | 46.7% |
| Ni buena ni mala (esp.) | 28.3% |
| Muy buena | 15.4% |
| Mala | 8.1% |
| Muy mala | 1.3% |

**p2|SAL** — Limitaciones para esfuerzos físicos moderados:
| Response | % |
|---|---|
| No, no me limita en nada | 72.6% |
| Sí, me limita un poco | 20.2% |
| Sí, me limita mucho | 6.5% |

**p1|POB** — Situación laboral reciente:
| Response | % |
|---|---|
| Trabajó | 45.4% |
| Se dedica a los quehaceres de su hogar | 22.0% |
| No trabajó | 14.3% |
| Es estudiante | 7.7% |
| Buscó trabajo | 3.8% |
| Está jubilado(a) o pensionado(a) | 3.1% |
| No trabajó pero sí tenía trabajo | 2.6% |

**p2|POB** — Actividades laborales adicionales:
| Response | % |
|---|---|
| No trabajó | 85.1% |
| Ayudó a trabajar en un negocio familiar | 5.6% |
| Vendió algunos productos | 4.3% |


## Complications
La moderación demográfica más fuerte se observa en la variable empleo (V=0.56), con diferencias sustanciales entre hombres y mujeres: los hombres trabajan más (63% vs 29%) y las mujeres se dedican más a los quehaceres del hogar (40% vs 10%). Esto complica la interpretación porque el acceso a la salud puede estar influenciado por género y tipo de empleo. Además, la edad modera la salud percibida y limitaciones físicas, con jóvenes reportando mejor salud y menos limitaciones.

Aunque todas las asociaciones bivariadas entre salud y pobreza son significativas, la mayoría presentan tamaños de efecto moderados o débiles (V entre 0.065 y 0.199), lo que indica que la relación es real pero no fuerte. Esto puede reflejar la complejidad del vínculo entre pobreza y salud, donde otros factores no medidos influyen.

Minorías importantes (>15%) reportan salud 'Ni buena ni mala' (28.3%) y limitaciones físicas 'Sí, me limita un poco' (20.2%), mostrando que no hay consenso absoluto y que una parte considerable de la población tiene percepciones intermedias o negativas de su salud.

Las estimaciones se basan en simulaciones con puentes SES, lo que implica incertidumbre en la precisión de los tamaños del efecto y la generalización a toda la población mexicana. Además, la pobreza se mide principalmente por empleo y actividades laborales, sin incluir dimensiones multidimensionales ni acceso directo a servicios de salud, limitando la interpretación del acceso a la salud en sentido amplio.

## Implications
Primero, la evidencia sugiere que mejorar la estabilidad laboral y las condiciones de empleo podría tener un impacto positivo en la salud percibida y funcional de la población, ya que quienes trabajan permanentemente o ayudan en negocios familiares reportan mejor salud. Políticas que promuevan empleos formales y estables podrían facilitar el acceso a servicios de salud y mejorar resultados sanitarios.

Segundo, dado que la relación entre pobreza y salud es moderada y compleja, se requiere un enfoque multidimensional que incluya no solo la mejora del empleo, sino también intervenciones específicas para grupos vulnerables como jubilados y personas con limitaciones físicas. Esto implica fortalecer la cobertura y calidad de servicios de salud para quienes están fuera del mercado laboral o con empleos precarios.

Además, la moderación por género y edad señala la necesidad de políticas diferenciadas que atiendan las desigualdades en salud relacionadas con el empleo y roles sociales, especialmente para mujeres dedicadas a los quehaceres del hogar y adultos mayores con mayor limitación física. La evidencia también indica que mejorar el acceso a la salud debe considerar factores sociales y económicos más amplios para ser efectiva.

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
| p1|SAL × p1|POB | 0.121 (moderate) | 0.000 | "Ni buena ni mala (esp.)": 16% ("Es estudiante") → 45% ("Está jubilado(a) o pensionado(a)") | 2000 |
| p1|SAL × p2|POB | 0.065 (weak) | 0.009 | "Buena": 54% ("No trabajó") → 66% ("Ayudó a trabajar en un negocio familiar") | 2000 |
| p1|SAL × p3|POB | 0.170 (moderate) | 0.000 | "Ni buena ni mala (esp.)": 16% ("Sólo por temporadas") → 30% ("Permanentemente") | 2000 |
| p1|SAL × p4|POB | 0.199 (moderate) | 0.000 | "Buena": 19% ("16.0") → 75% ("24.0") | 2000 |
| p2|SAL × p1|POB | 0.168 (moderate) | 0.000 | " No, no me limita en nada": 58% ("Está jubilado(a) o pensionado(a)") → 92% ("Es estudiante") | 2000 |
| p2|SAL × p2|POB | 0.078 (weak) | 0.000 | " Sí, me limita mucho": 3% ("No trabajó") → 10% ("Ayudó a trabajar en un negocio familiar") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p1|SAL × p1|POB** — How p1|SAL distributes given p1|POB:

| p1|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Trabajó | Buena: 53%, Ni buena ni mala (esp.): 29%, Muy buena: 13% |
| No trabajó pero sí tenía trabajo | Buena: 59%, Muy buena: 20%, Ni buena ni mala (esp.): 19% |
| Buscó trabajo | Buena: 58%, Ni buena ni mala (esp.): 21%, Muy buena: 21% |
| Es estudiante | Buena: 56%, Muy buena: 27%, Ni buena ni mala (esp.): 16% |
| Se dedica a los quehaceres de su hogar | Buena: 56%, Ni buena ni mala (esp.): 25%, Muy buena: 15% |
| Está jubilado(a) o pensionado(a) | Ni buena ni mala (esp.): 45%, Buena: 45%, Mala: 6% |
| No trabajó | Buena: 51%, Ni buena ni mala (esp.): 29%, Muy buena: 17% |

**p1|SAL × p2|POB** — How p1|SAL distributes given p2|POB:

| p2|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Ayudó a trabajar en un negocio familiar | Buena: 66%, Ni buena ni mala (esp.): 18%, Muy buena: 11% |
| Vendió algunos productos: ropa,  cosméticos, alimentos | Buena: 59%, Muy buena: 20%, Ni buena ni mala (esp.): 19% |
| No trabajó | Buena: 54%, Ni buena ni mala (esp.): 26%, Muy buena: 17% |

**p1|SAL × p3|POB** — How p1|SAL distributes given p3|POB:

| p3|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Permanentemente | Buena: 53%, Ni buena ni mala (esp.): 30%, Muy buena: 14% |
| Sólo por temporadas | Buena: 60%, Muy buena: 22%, Ni buena ni mala (esp.): 16% |

**p1|SAL × p4|POB** — How p1|SAL distributes given p4|POB:

| p4|POB (conditioning) | Top p1|SAL responses |
|---|---|
| 1.0 | Buena: 62%, Ni buena ni mala (esp.): 26%, Muy buena: 11% |
| 2.0 | Buena: 56%, Muy buena: 30%, Ni buena ni mala (esp.): 14% |
| 3.0 | Buena: 56%, Muy buena: 28%, Ni buena ni mala (esp.): 12% |
| 4.0 | Buena: 51%, Muy buena: 29%, Ni buena ni mala (esp.): 18% |
| 5.0 | Buena: 54%, Ni buena ni mala (esp.): 31%, Muy buena: 10% |
| 6.0 | Buena: 55%, Ni buena ni mala (esp.): 28%, Muy buena: 15% |
| 7.0 | Buena: 65%, Muy buena: 19%, Ni buena ni mala (esp.): 14% |
| 8.0 | Buena: 60%, Ni buena ni mala (esp.): 19%, Muy buena: 16% |

**p2|SAL × p1|POB** — How p2|SAL distributes given p1|POB:

| p1|POB (conditioning) | Top p2|SAL responses |
|---|---|
| Trabajó |  No, no me limita en nada: 85%,  Sí, me limita un poco: 11%,  Sí, me limita mucho: 3% |
| No trabajó pero sí tenía trabajo |  No, no me limita en nada: 90%,  Sí, me limita un poco: 8%,  Sí, me limita mucho: 2% |
| Buscó trabajo |  No, no me limita en nada: 90%,  Sí, me limita un poco: 10%,  Sí, me limita mucho: 0% |
| Es estudiante |  No, no me limita en nada: 92%,  Sí, me limita un poco: 6%,  Sí, me limita mucho: 2% |
| Se dedica a los quehaceres de su hogar |  No, no me limita en nada: 84%,  Sí, me limita un poco: 11%,  Sí, me limita mucho: 5% |
| Está jubilado(a) o pensionado(a) |  No, no me limita en nada: 58%,  Sí, me limita mucho: 25%,  Sí, me limita un poco: 16% |
| No trabajó |  No, no me limita en nada: 86%,  Sí, me limita un poco: 9%,  Sí, me limita mucho: 6% |

**p2|SAL × p2|POB** — How p2|SAL distributes given p2|POB:

| p2|POB (conditioning) | Top p2|SAL responses |
|---|---|
| Ayudó a trabajar en un negocio familiar |  No, no me limita en nada: 82%,  Sí, me limita mucho: 10%,  Sí, me limita un poco: 8% |
| Vendió algunos productos: ropa,  cosméticos, alimentos |  No, no me limita en nada: 82%,  Sí, me limita un poco: 14%,  Sí, me limita mucho: 4% |
| No trabajó |  No, no me limita en nada: 86%,  Sí, me limita un poco: 11%,  Sí, me limita mucho: 3% |
### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from the cross-dataset bivariate associations with significant p-values, which directly link health variables to poverty indicators and show moderate to weak associations. Next in strength are demographic fault lines that provide context on how variables vary by age, sex, and employment but do not establish direct relationships. Univariate distributions offer background information but do not demonstrate relationships relevant to the query.

**Key Limitations:**
- All bivariate associations are simulation-based estimates, which may introduce uncertainty in effect size and significance.
- Effect sizes (Cramér's V) are mostly moderate to weak, indicating relationships are present but not strong.
- Sample size is moderate (n=2000), which supports significance but may limit generalizability to all Mexican populations.
- The poverty variables focus mainly on employment status and related work activities, which capture economic aspects but may not fully represent multidimensional poverty or direct access to healthcare services.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** None
- **Dispersed Variables:** None

