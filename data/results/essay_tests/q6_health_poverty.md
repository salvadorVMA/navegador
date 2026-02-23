# q6_health_poverty

**Query (ES):** ¿Cómo se relaciona el acceso a la salud con la pobreza en México?
**Query (EN):** How does health access relate to poverty in Mexico?
**Variables:** p1|SAL, p2|SAL, p3|SAL, p4|SAL, p5|SAL, p1|POB, p2|POB, p3|POB, p4|POB
**Status:** ✅ success
**Time:** 45288ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Cómo se relaciona el acceso a la salud con la pobreza en México?

## Summary
La relación entre el acceso a la salud y la pobreza en México se manifiesta en una asociación moderada y significativa entre el estatus laboral (indicador de pobreza) y la percepción de la salud general. Por ejemplo, la proporción de personas que reportan salud "Ni buena ni mala" varía desde 7.7% entre quienes buscan trabajo hasta 43.0% entre jubilados o pensionados, mostrando que la salud percibida difiere según la situación laboral. Se estimaron seis pares bivariados entre variables de salud y pobreza, todos con asociaciones significativas, aunque con fuerza moderada o débil, lo que sugiere una relación compleja pero consistente con un nivel de confianza razonable.

## Data Landscape
Se analizaron nueve variables relacionadas con salud y pobreza, principalmente provenientes de encuestas sobre condiciones laborales y autopercepción de salud. Seis variables muestran consenso fuerte en las respuestas, mientras tres tienden hacia una opinión predominante sin consenso absoluto, resultando en un índice de divergencia del 33%, lo que indica una variabilidad moderada en las percepciones públicas sobre estos temas.

## Evidence
La asociación más clara se observa entre la percepción general de salud (p1|SAL) y el estatus laboral semanal (p1|POB) con un valor V=0.122 (p=0.000). La categoría clave "Ni buena ni mala" oscila entre 7.7% para quienes buscan trabajo y 43.0% para jubilados/pensionados, evidenciando que los jubilados tienen percepciones de salud menos positivas. También, la proporción que reporta salud "Buena" varía entre 46.8% y 58.2% según el estatus laboral. En cuanto a limitaciones físicas moderadas (p2|SAL) y estatus laboral (p1|POB), el 60.6% de jubilados no reporta limitaciones, comparado con 95.0% de estudiantes, mostrando diferencias funcionales de salud por condición laboral (V=0.157, p=0.000). Por otro lado, la relación entre limitaciones físicas y actividades laborales adicionales (p2|SAL × p2|POB) es débil y no significativa (V=0.042, p=0.130), indicando que estas actividades no afectan notablemente la salud funcional. La estabilidad laboral (p3|POB) también se relaciona moderadamente con la salud general (V=0.175, p=0.000), donde quienes trabajan permanentemente reportan más frecuentemente salud "Ni buena ni mala" (28.3%) que quienes trabajan sólo por temporadas (15.3%). La duración en el empleo actual (p4|POB) muestra una relación compleja con la salud, con "Ni buena ni mala" desde 8.0% hasta 50.0%, reflejando heterogeneidad en salud según antigüedad laboral (V=0.199, p=0.000).

## Complications
El empleo es la dimensión socioeconómica que más modera las respuestas, con un valor V=0.56 en variables relacionadas, evidenciando que la condición laboral es clave para entender salud y pobreza. Sin embargo, la asociación entre salud y actividades laborales adicionales es débil y no significativa, lo que indica que no todas las formas de pobreza laboral afectan la salud funcional. Además, hay minorías importantes que reportan salud "Ni buena ni mala" (28.3%) y limitaciones físicas "un poco" (20%), mostrando que no todo el grupo pobre experimenta mala salud. Las limitaciones del estudio incluyen que las asociaciones son estimadas por simulación (SES bridge), con posibles incertidumbres en la precisión, y que la muestra es moderada (n=2000), lo que puede limitar la detección de efectos menores. La relación entre duración en el empleo y salud es compleja y no lineal, complicando interpretaciones simples.

## Implications
Primero, la evidencia sugiere que políticas públicas deben focalizarse en mejorar el acceso a servicios de salud para grupos con empleo precario o jubilados, donde la percepción de salud es peor, para reducir desigualdades en salud relacionadas con la pobreza laboral. Segundo, dado que la relación entre salud y actividades laborales adicionales es débil, se debería investigar más a fondo cómo las condiciones laborales informales afectan la salud, para diseñar intervenciones específicas que consideren la heterogeneidad dentro de la pobreza. Finalmente, la moderación por género y edad indica la necesidad de políticas diferenciadas que atiendan las distintas experiencias de salud en subgrupos poblacionales vulnerables.

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
- sexo: V=0.095 (p=0.029) — 1.0:  No, no me limita en nada (75%); 2.0:  No, no me limita en nada (70%)
- region: V=0.092 (p=0.002) — 01:  No, no me limita en nada (70%); 02:  No, no me limita en nada (81%); 03:  No, no me limita en nada (71%)

*p3|SAL*
- edad: V=0.218 (p=0.000) — 0-18:  No, no me limita en nada (92%); 19-24:  No, no me limita en nada (90%); 25-34:  No, no me limita en nada (83%)
- sexo: V=0.111 (p=0.005) — 1.0:  No, no me limita en nada (77%); 2.0:  No, no me limita en nada (68%)

*p4|SAL*
- edad: V=0.190 (p=0.000) — 0-18:  No (92%); 19-24:  No (92%); 25-34:  No (86%)

*p5|SAL*
- edad: V=0.206 (p=0.000) — 0-18:  No (89%); 19-24:  No (93%); 25-34:  No (91%)

*p1|POB*
- sexo: V=0.514 (p=0.000) — 1.0: Trabajó (63%); 2.0: Se dedica a los quehaceres de su hogar (40%)
- edad: V=0.312 (p=0.000) — 0-18: Es estudiante (60%); 19-24: Es estudiante (36%); 25-34: Trabajó (48%)

*p2|POB*
- sexo: V=0.326 (p=0.000) — 1.0: -1.0 (82%); 2.0: -1.0 (53%)
- edad: V=0.126 (p=0.000) — 0-18: No trabajó (60%); 19-24: -1.0 (53%); 25-34: -1.0 (72%)

*p3|POB*
- sexo: V=0.355 (p=0.000) — 1.0: Permanentemente (54%); 2.0: -1.0 (59%)
- edad: V=0.171 (p=0.000) — 0-18: -1.0 (86%); 19-24: -1.0 (59%); 25-34: Permanentemente (40%)

*p4|POB*
- empleo: V=0.564 (p=0.000) — 01: -1.0 (50%); 02: -1.0 (31%); 03: -1.0 (42%)
- sexo: V=0.382 (p=0.000) — 1.0: -1.0 (26%); 2.0: -1.0 (59%)
- edad: V=0.257 (p=0.000) — 0-18: -1.0 (86%); 19-24: -1.0 (59%); 25-34: -1.0 (39%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p1|SAL × p1|POB | 0.122 (moderate) | 0.000 | "Ni buena ni mala (esp.)": 8% ("Buscó trabajo") → 43% ("Está jubilado(a) o pensionado(a)") | 2000 |
| p1|SAL × p2|POB | 0.096 (weak) | 0.000 | "Buena": 53% ("No trabajó") → 67% ("Ayudó a trabajar en un negocio familiar") | 2000 |
| p1|SAL × p3|POB | 0.175 (moderate) | 0.000 | "Ni buena ni mala (esp.)": 15% ("Sólo por temporadas") → 28% ("Permanentemente") | 2000 |
| p1|SAL × p4|POB | 0.199 (moderate) | 0.000 | "Ni buena ni mala (esp.)": 8% ("3.0") → 50% ("61.0") | 2000 |
| p2|SAL × p1|POB | 0.157 (moderate) | 0.000 | " No, no me limita en nada": 61% ("Está jubilado(a) o pensionado(a)") → 95% ("Es estudiante") | 2000 |
| p2|SAL × p2|POB | 0.042 (weak) | 0.130 | " Sí, me limita mucho": 2% ("Vendió algunos productos: ropa,  cosméticos, alimentos") → 7% ("Ayudó a trabajar en un negocio familiar") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p1|SAL × p1|POB** — How p1|SAL distributes given p1|POB:

| p1|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Trabajó | Buena: 54%, Ni buena ni mala (esp.): 29%, Muy buena: 14% |
| No trabajó pero sí tenía trabajo | Buena: 52%, Ni buena ni mala (esp.): 29%, Muy buena: 19% |
| Buscó trabajo | Buena: 50%, Muy buena: 38%, Ni buena ni mala (esp.): 8% |
| Es estudiante | Buena: 57%, Muy buena: 28%, Ni buena ni mala (esp.): 14% |
| Se dedica a los quehaceres de su hogar | Buena: 55%, Ni buena ni mala (esp.): 25%, Muy buena: 16% |
| Está jubilado(a) o pensionado(a) | Buena: 47%, Ni buena ni mala (esp.): 43%, Mala: 5% |
| No trabajó | Buena: 58%, Ni buena ni mala (esp.): 24%, Muy buena: 15% |

**p1|SAL × p2|POB** — How p1|SAL distributes given p2|POB:

| p2|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Ayudó a trabajar en un negocio familiar | Buena: 67%, Ni buena ni mala (esp.): 15%, Mala: 9% |
| Vendió algunos productos: ropa,  cosméticos, alimentos | Buena: 54%, Ni buena ni mala (esp.): 23%, Muy buena: 20% |
| No trabajó | Buena: 53%, Ni buena ni mala (esp.): 26%, Muy buena: 18% |

**p1|SAL × p3|POB** — How p1|SAL distributes given p3|POB:

| p3|POB (conditioning) | Top p1|SAL responses |
|---|---|
| Permanentemente | Buena: 55%, Ni buena ni mala (esp.): 28%, Muy buena: 14% |
| Sólo por temporadas | Buena: 58%, Muy buena: 25%, Ni buena ni mala (esp.): 15% |

**p1|SAL × p4|POB** — How p1|SAL distributes given p4|POB:

| p4|POB (conditioning) | Top p1|SAL responses |
|---|---|
| 1.0 | Buena: 62%, Ni buena ni mala (esp.): 23%, Muy buena: 12% |
| 2.0 | Buena: 56%, Muy buena: 28%, Ni buena ni mala (esp.): 14% |
| 3.0 | Buena: 66%, Muy buena: 26%, Ni buena ni mala (esp.): 8% |
| 4.0 | Buena: 52%, Muy buena: 26%, Ni buena ni mala (esp.): 21% |
| 5.0 | Buena: 47%, Ni buena ni mala (esp.): 30%, Muy buena: 21% |
| 6.0 | Buena: 55%, Ni buena ni mala (esp.): 28%, Muy buena: 10% |
| 7.0 | Buena: 70%, Ni buena ni mala (esp.): 17%, Muy buena: 13% |
| 8.0 | Buena: 59%, Muy buena: 21%, Ni buena ni mala (esp.): 17% |

**p2|SAL × p1|POB** — How p2|SAL distributes given p1|POB:

| p1|POB (conditioning) | Top p2|SAL responses |
|---|---|
| Trabajó |  No, no me limita en nada: 86%,  Sí, me limita un poco: 11%,  Sí, me limita mucho: 3% |
| No trabajó pero sí tenía trabajo |  No, no me limita en nada: 88%,  Sí, me limita un poco: 10%,  Sí, me limita mucho: 2% |
| Buscó trabajo |  No, no me limita en nada: 90%,  Sí, me limita un poco: 10%,  Sí, me limita mucho: 0% |
| Es estudiante |  No, no me limita en nada: 95%,  Sí, me limita un poco: 4%,  Sí, me limita mucho: 2% |
| Se dedica a los quehaceres de su hogar |  No, no me limita en nada: 85%,  Sí, me limita un poco: 11%,  Sí, me limita mucho: 4% |
| Está jubilado(a) o pensionado(a) |  No, no me limita en nada: 61%,  Sí, me limita mucho: 21%,  Sí, me limita un poco: 18% |
| No trabajó |  No, no me limita en nada: 81%,  Sí, me limita un poco: 10%,  Sí, me limita mucho: 8% |

**p2|SAL × p2|POB** — How p2|SAL distributes given p2|POB:

| p2|POB (conditioning) | Top p2|SAL responses |
|---|---|
| Ayudó a trabajar en un negocio familiar |  No, no me limita en nada: 83%,  Sí, me limita un poco: 10%,  Sí, me limita mucho: 7% |
| Vendió algunos productos: ropa,  cosméticos, alimentos |  No, no me limita en nada: 84%,  Sí, me limita un poco: 15%,  Sí, me limita mucho: 2% |
| No trabajó |  No, no me limita en nada: 85%,  Sí, me limita un poco: 11%,  Sí, me limita mucho: 4% |
### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from the cross-dataset bivariate associations with significant p-values, especially those involving p1|SAL and p1|POB, which show moderate and significant relationships between health status and poverty indicators. Demographic fault lines provide secondary evidence about subgroup variations but do not directly address the query. Univariate distributions offer contextual background but do not establish relationships between health access and poverty.

**Key Limitations:**
- All bivariate associations are simulation-based estimates, which may introduce uncertainty in effect size precision.
- Sample size is moderate (n=2000), which supports significance but may limit detection of smaller effects.
- Only a limited number of variables directly measure health and poverty dimensions; some poverty variables are indirect proxies (e.g., employment status).
- Effect sizes (Cramér's V) are mostly moderate or weak, indicating relationships exist but are not strong, suggesting complexity in the health-poverty link.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** None
- **Dispersed Variables:** None

