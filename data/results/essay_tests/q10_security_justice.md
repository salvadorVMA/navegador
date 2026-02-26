# q10_security_justice

**Query (ES):** ¿Qué relación ven los mexicanos entre seguridad pública y justicia?
**Query (EN):** What relationship do Mexicans see between public security and justice?
**Variables:** p3|SEG, p4|SEG, p5|SEG, p6|SEG, p7|SEG, p1|JUS, p2|JUS, p4|JUS, p7|JUS
**Status:** ✅ success
**Time:** 66992ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Qué relación ven los mexicanos entre seguridad pública y justicia?

## Summary
Los mexicanos muestran una relación débil pero estadísticamente significativa entre sus percepciones de seguridad pública y de justicia, especialmente en cómo perciben la situación económica del país y las razones para obedecer las leyes. Aunque estas asociaciones son consistentes, su fuerza es baja (Cramér's V < 0.1), lo que indica que la relación entre seguridad y justicia es limitada y fragmentada. Se analizaron cinco pares bivariados, de los cuales dos mostraron asociaciones significativas, pero débiles, lo que sugiere un nivel de confianza moderado en la interpretación de estos vínculos.

## Data Landscape
Se analizaron nueve variables provenientes de encuestas sobre seguridad pública y justicia, con formas de distribución mayormente dispersas (cinco variables) y polarizadas (dos variables), además de dos variables con sesgo hacia una opinión. El índice de divergencia del 100% indica una ausencia total de consenso entre la población, reflejando una fragmentación marcada en las opiniones sobre seguridad y justicia. Esta dispersión y polarización evidencian un escenario complejo y dividido en la percepción social sobre estos temas.

## Evidence
La relación entre la percepción de seguridad personal y la percepción económica de justicia (p3|SEG × p1|JUS) muestra que la proporción de personas que se sienten "Un poco más seguro" oscila entre 20.5% cuando la percepción de justicia es "NS" y 32.8% cuando la justicia es percibida como "Peor" (V=0.073, p=0.002), indicando una asociación débil pero significativa. 
| p1|JUS category | Un poco más seguro % |
|---|---|
| Mejor | 31.4% |
| Igual de bien (esp.) | 22.2% |
| Igual de mal (esp.) | 31.7% |
| Peor | 32.8% |
| NS | 20.5% |

En cuanto a la relación entre seguridad personal y razones para obedecer las leyes (p3|SEG × p7|JUS), la categoría "Un poco más seguro" varía desde 25.9% para quienes obedecen "Para evitar castigos" hasta 60.9% para quienes respondieron "NC" (V=0.090, p=0.000), mostrando también una asociación débil pero significativa.
| p7|JUS category | Un poco más seguro % |
|---|---|
| Porque cumplir la ley nos beneficia a todos | 31.3% |
| Para no ser criticado por los demás | 26.6% |
| Porque es un deber moral | 31.0% |
| Para evitar daños a mi familia y amistades | 29.5% |
| Para evitar castigos | 25.9% |
| Otra | 30.8% |
| NC | 60.9% |

Las otras asociaciones entre seguridad y justicia, como la percepción política (p3|SEG × p2|JUS) y la actitud hacia la tortura para obtener información (p3|SEG × p4|JUS), no mostraron relaciones significativas, indicando uniformidad en las respuestas.

Demográficamente, la región es la dimensión que más modera las percepciones, con diferencias moderadas en la percepción de seguridad y justicia. Por ejemplo, en seguridad pública, la percepción "Igual (esp.)" varía entre 27% y 34% según la región, y en justicia económica, la categoría "Peor" varía entre 29% y 50% según la región.

**p3|SEG** — Percepción personal de seguridad pública respecto a hace un año:
| Response | % |
|---|---|
| Igual (esp.) | 31.2% |
| Un poco más seguro | 27.4% |
| Un poco más inseguro | 20.4% |
| Mucho más inseguro | 15.4% |
| Mucho más seguro | 4.8% |

**p1|JUS** — Percepción de la situación económica actual respecto a hace un año:
| Response | % |
|---|---|
| Peor | 37.9% |
| Igual de mal (esp.) | 37.3% |
| Igual de bien (esp.) | 14.9% |
| Mejor | 8.9% |

**p7|JUS** — Razones para obedecer las leyes:
| Response | % |
|---|---|
| Porque cumplir la ley nos beneficia a todos | 45.0% |
| Porque es un deber moral | 22.1% |
| Para no ser criticado por los demás | 11.5% |
| Para evitar castigos | 9.6% |
| Para evitar daños a mi familia y amistades | 9.0% |

## Complications
La relación entre seguridad pública y justicia está moderada principalmente por la región, que muestra diferencias de hasta 20 puntos porcentuales en algunas categorías clave, como la percepción económica y de seguridad. El sexo y la edad tienen efectos moderados y débiles respectivamente, con diferencias menores en las respuestas. Además, hay opiniones minoritarias relevantes, por ejemplo, un 19.2% está de acuerdo con la tortura para obtener información, lo que desafía la mayoría que se opone a esta práctica.

Las asociaciones bivariadas entre seguridad y justicia son estadísticamente significativas solo en dos casos, pero con valores de Cramér's V menores a 0.1, lo que indica relaciones muy débiles. Esto limita la capacidad para hacer afirmaciones fuertes sobre la conexión entre estas percepciones. La ausencia de asociaciones significativas en otras variables sugiere que la relación es fragmentada y no uniforme.

Finalmente, las estimaciones derivadas del puente SES pueden tener limitaciones inherentes a la simulación y al tamaño muestral, lo que añade incertidumbre a la interpretación de las asociaciones débiles observadas.

## Implications
Primero, la débil pero significativa relación entre percepción de seguridad y justicia sugiere que mejorar la confianza en la justicia económica y en las razones éticas para obedecer leyes podría tener un impacto positivo, aunque limitado, en la percepción de seguridad pública. Políticas que fortalezcan la transparencia y eficacia del sistema judicial podrían contribuir a mejorar la sensación de seguridad.

Segundo, dada la fragmentación y polarización de opiniones, las intervenciones deben ser regionalmente diferenciadas, considerando las disparidades en percepción y actitudes. Además, la presencia de minorías que apoyan medidas controversiales como la tortura indica la necesidad de campañas educativas y de fortalecimiento de derechos humanos para evitar que percepciones negativas de justicia erosionen la cohesión social y la seguridad.

En conjunto, la evidencia apunta a que las políticas deben abordar tanto la mejora tangible en justicia como la construcción de confianza pública para influir en la percepción de seguridad, reconociendo que la relación entre ambos es compleja y no lineal.

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | 9 |
| Divergence Index | 100.0% |
| Consensus Variables | 0 |
| Lean Variables | 2 |
| Polarized Variables | 2 |
| Dispersed Variables | 5 |

### Variable Details


**p3|SEG** (dispersed)
- Question: SEGURIDAD_PUBLICA|Hablando en términos de seguridad pública, ¿qué tan seguro o inseguro se siente usted en la actualidad con respecto a hace doce mese
- Mode: Igual (esp.) (31.2%)
- Runner-up: Un poco más seguro (27.4%), margin: 3.8pp
- HHI: 2406
- Minority opinions: Un poco más seguro (27.4%), Un poco más inseguro (20.4%), Mucho más inseguro (15.4%)

| Response | % |
|----------|---|
| Igual (esp.) | 31.2% |
| Un poco más seguro | 27.4% |
| Un poco más inseguro | 20.4% |
| Mucho más inseguro | 15.4% |
| Mucho más seguro | 4.8% |
| No sabe/ No contesta | 0.8% |

**p4|SEG** (dispersed)
- Question: SEGURIDAD_PUBLICA|¿Cómo considera usted que será su seguridad dentro de doce meses respecto a la actual?
- Mode: Igual (36.2%)
- Runner-up: Peor (26.1%), margin: 10.1pp
- HHI: 2568
- Minority opinions: Mejor (22.2%), Peor (26.1%)

| Response | % |
|----------|---|
| Igual | 36.2% |
| Peor | 26.1% |
| Mejor | 22.2% |
| Mucho peor | 6.4% |
| Mucho mejor | 5.6% |
| No sabe/ No contesta | 3.5% |

**p5|SEG** (polarized)
- Question: SEGURIDAD_PUBLICA|¿Cómo considera usted la seguridad pública en el país hoy en día comparada con la que se tenía hace doce meses (un año atrás)?
- Mode: Igual (34.3%)
- Runner-up: Peor (31.0%), margin: 3.3pp
- HHI: 2609
- Minority opinions: Mejor (18.5%), Peor (31.0%)

| Response | % |
|----------|---|
| Igual | 34.3% |
| Peor | 31.0% |
| Mejor | 18.5% |
| Mucho peor | 10.3% |
| Mucho mejor | 4.2% |
| No sabe/ No contesta | 1.7% |

**p6|SEG** (dispersed)
- Question: SEGURIDAD_PUBLICA|¿Cómo considera que será la seguridad pública en el país dentro de doce meses respecto de la situación actual?
- Mode: Igual (30.9%)
- Runner-up: Peor (27.5%), margin: 3.4pp
- HHI: 2407
- Minority opinions: Mejor (23.8%), Peor (27.5%)

| Response | % |
|----------|---|
| Igual | 30.9% |
| Peor | 27.5% |
| Mejor | 23.8% |
| Mucho peor | 9.9% |
| No sabe/ No contesta | 4.5% |
| Mucho mejor | 3.4% |

**p7|SEG** (lean)
- Question: SEGURIDAD_PUBLICA|Dígame por favor, ¿cuánto tiempo hace que vive en esta colonia (localidad)?
- Mode: 6 años en adelante (61.8%)
- Runner-up: De 4 a 5 años (18.6%), margin: 43.2pp
- HHI: 4383
- Minority opinions: De 4 a 5 años (18.6%)

| Response | % |
|----------|---|
| 6 años en adelante | 61.8% |
| De 4 a 5 años | 18.6% |
| De un 1 a 3 años | 14.2% |
| Menos de un año | 4.6% |
| No sabe/ No contesta | 0.8% |

**p1|JUS** (polarized)
- Question: JUSTICIA|Comparada con la situación que tenía el país hace un año, ¿cómo diría usted que es la situación económica actual del país: mejor o peor?
- Mode: Peor (37.9%)
- Runner-up: Igual de mal (esp.) (37.3%), margin: 0.6pp
- HHI: 3134
- Minority opinions: Igual de mal (esp.) (37.3%)

| Response | % |
|----------|---|
| Peor | 37.9% |
| Igual de mal (esp.) | 37.3% |
| Igual de bien (esp.) | 14.9% |
| Mejor | 8.9% |
| No sabe/ No contesta | 0.9% |

**p2|JUS** (dispersed)
- Question: JUSTICIA|De las siguientes palabras, ¿con cuál está usted más de acuerdo para describir la situación política del país?
- Mode: Preocupante (37.2%)
- Runner-up: Peligrosa (19.8%), margin: 17.5pp
- HHI: 2126
- Minority opinions: Peligrosa (19.8%)

| Response | % |
|----------|---|
| Preocupante | 37.2% |
| Peligrosa | 19.8% |
| Con oportunidades | 11.2% |
| Peor que antes (esp.) | 10.6% |
| Tranquila | 6.3% |
| Más o menos (esp.) | 5.9% |
| Prometedora | 5.5% |
| No sabe/ No contesta | 1.6% |
| Mejor que antes (esp.) | 1.5% |
| Otra (esp.) | 0.3% |

**p4|JUS** (dispersed)
- Question: JUSTICIA|¿Qué tan de acuerdo o en desacuerdo está usted con que, para conseguir información, se torture a una persona detenida por pertenecer a un gru
- Mode: En desacuerdo (36.4%)
- Runner-up: Ni de acuerdo ni en desacuerdo (esp..) (25.4%), margin: 11.0pp
- HHI: 2503
- Minority opinions: De acuerdo (19.2%), Ni de acuerdo ni en desacuerdo (esp..) (25.4%)

| Response | % |
|----------|---|
| En desacuerdo | 36.4% |
| Ni de acuerdo ni en desacuerdo (esp..) | 25.4% |
| De acuerdo | 19.2% |
| Muy en desacuerdo | 11.2% |
| Muy de acuerdo | 5.7% |
| No sabe/ No contesta | 2.1% |

**p7|JUS** (lean)
- Question: JUSTICIA|Dígame, ¿usted por qué obedece las leyes?
- Mode: Porque cumplir la ley nos beneficia a todos (45.0%)
- Runner-up: Porque es un deber moral (22.1%), margin: 22.9pp
- HHI: 2822
- Minority opinions: Porque es un deber moral (22.1%)

| Response | % |
|----------|---|
| Porque cumplir la ley nos beneficia a todos | 45.0% |
| Porque es un deber moral | 22.1% |
| Para no ser criticado por los demás | 11.5% |
| Para evitar castigos | 9.6% |
| Para evitar daños a mi familia y amistades | 9.0% |
| No sabe/ No contesta | 1.9% |
| Otra | 0.9% |

### Demographic Fault Lines

| Dimension | Mean Cramér's V | Max Cramér's V | Variables |
|-----------|----------------|----------------|----------|
| region | 0.142 (moderate) | 0.172 | 9 |
| sexo | 0.096 (weak) | 0.096 | 1 |
| edad | 0.092 (weak) | 0.095 | 2 |

**Variable-Level Demographic Detail:**

*p3|SEG*
- region: V=0.170 (p=0.000) — 01: Igual (esp.) (32%); 02: Mucho más inseguro (29%); 03: Igual (esp.) (34%)

*p4|SEG*
- region: V=0.154 (p=0.000) — 01:  Igual (40%); 02:  Peor (39%); 03:  Igual (38%)

*p5|SEG*
- region: V=0.172 (p=0.000) — 01:  Igual (33%); 02:  Peor (43%); 03:  Igual (38%)

*p6|SEG*
- region: V=0.157 (p=0.000) — 01:  Igual (34%); 02:  Peor (37%); 03:  Igual (33%)

*p7|SEG*
- region: V=0.104 (p=0.001) — 01:  6 años en adelante (62%); 02:  6 años en adelante (67%); 03:  6 años en adelante (54%)
- sexo: V=0.096 (p=0.050) —  Hombre:  6 años en adelante (60%);  Mujer:  6 años en adelante (64%)
- edad: V=0.095 (p=0.005) — 0-18:  6 años en adelante (52%); 19-24:  6 años en adelante (53%); 25-34:  6 años en adelante (55%)

*p1|JUS*
- region: V=0.113 (p=0.000) — Centro: Igual de mal (esp.) (39%); D. F. y Estado de México: Peor (50%); Norte: Igual de mal (esp.) (43%)

*p2|JUS*
- region: V=0.146 (p=0.000) — Centro: Preocupante (31%); D. F. y Estado de México: Preocupante (37%); Norte: Preocupante (44%)

*p4|JUS*
- region: V=0.103 (p=0.004) — Centro: En desacuerdo (32%); D. F. y Estado de México: En desacuerdo (44%); Norte: En desacuerdo (40%)

*p7|JUS*
- region: V=0.159 (p=0.000) — Centro: Porque cumplir la ley nos beneficia a todos (40%); D. F. y Estado de México: Porque cumplir la ley nos beneficia a todos (49%); Norte: Porque cumplir la ley nos beneficia a todos (46%)
- edad: V=0.090 (p=0.047) — 0-18: Porque cumplir la ley nos beneficia a todos (54%); 19-24: Porque cumplir la ley nos beneficia a todos (42%); 25-34: Porque cumplir la ley nos beneficia a todos (45%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p3|SEG × p1|JUS | 0.073 (weak) | 0.002 | "Un poco más seguro": 20% ("NS") → 33% ("Peor") | 2000 |
| p3|SEG × p2|JUS | 0.068 (weak) | 0.107 | "Un poco más inseguro": 13% ("Tranquila") → 46% ("Mejor que antes (esp.)") | 2000 |
| p3|SEG × p4|JUS | 0.057 (weak) | 0.141 | "Un poco más seguro": 17% ("NC") → 34% ("Muy de acuerdo") | 2000 |
| p3|SEG × p7|JUS | 0.090 (weak) | 0.000 | "Un poco más seguro": 26% ("Para evitar castigos") → 61% ("NC") | 2000 |
| p4|SEG × p1|JUS | 0.063 (weak) | 0.045 | " Peor": 20% ("Igual de mal (esp.)") → 37% ("NS") | 2000 |
| p4|SEG × p2|JUS | 0.067 (weak) | 0.115 | " Mejor": 22% ("Preocupante") → 39% ("Más o menos (esp.)") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p3|SEG × p1|JUS** — How p3|SEG distributes given p1|JUS:

| p1|JUS (conditioning) | Top p3|SEG responses |
|---|---|
| Mejor | Igual (esp.): 36%, Un poco más seguro: 31%, Un poco más inseguro: 22% |
| Igual de bien (esp.) | Igual (esp.): 39%, Un poco más inseguro: 27%, Un poco más seguro: 22% |
| Igual de mal (esp.) | Igual (esp.): 37%, Un poco más seguro: 32%, Un poco más inseguro: 21% |
| Peor | Igual (esp.): 39%, Un poco más seguro: 33%, Un poco más inseguro: 18% |
| NS | Igual (esp.): 38%, Un poco más inseguro: 23%, Un poco más seguro: 20% |

**p3|SEG × p2|JUS** — How p3|SEG distributes given p2|JUS:

| p2|JUS (conditioning) | Top p3|SEG responses |
|---|---|
| Prometedora | Igual (esp.): 46%, Un poco más inseguro: 22%, Un poco más seguro: 20% |
| Con oportunidades | Igual (esp.): 40%, Un poco más seguro: 31%, Un poco más inseguro: 22% |
| Preocupante | Igual (esp.): 39%, Un poco más seguro: 27%, Un poco más inseguro: 22% |
| Tranquila | Igual (esp.): 47%, Un poco más seguro: 34%, Un poco más inseguro: 13% |
| Peligrosa | Igual (esp.): 35%, Un poco más seguro: 28%, Un poco más inseguro: 24% |
| Mejor que antes (esp.) | Un poco más inseguro: 46%, Un poco más seguro: 36%, Igual (esp.): 18% |
| Más o menos (esp.) | Un poco más seguro: 41%, Igual (esp.): 36%, Un poco más inseguro: 14% |
| Peor que antes (esp.) | Igual (esp.): 44%, Un poco más seguro: 31%, Un poco más inseguro: 18% |

**p3|SEG × p4|JUS** — How p3|SEG distributes given p4|JUS:

| p4|JUS (conditioning) | Top p3|SEG responses |
|---|---|
| Muy de acuerdo | Un poco más seguro: 34%, Igual (esp.): 31%, Un poco más inseguro: 21% |
| De acuerdo | Igual (esp.): 38%, Un poco más seguro: 27%, Un poco más inseguro: 20% |
| Ni de acuerdo ni en desacuerdo (esp..) | Igual (esp.): 40%, Un poco más seguro: 28%, Un poco más inseguro: 21% |
| En desacuerdo | Igual (esp.): 37%, Un poco más seguro: 30%, Un poco más inseguro: 23% |
| Muy en desacuerdo | Igual (esp.): 41%, Un poco más seguro: 26%, Un poco más inseguro: 17% |
| NC | Igual (esp.): 41%, Mucho más inseguro: 22%, Un poco más seguro: 17% |

**p3|SEG × p7|JUS** — How p3|SEG distributes given p7|JUS:

| p7|JUS (conditioning) | Top p3|SEG responses |
|---|---|
| Porque cumplir la ley nos beneficia a todos | Igual (esp.): 41%, Un poco más seguro: 31%, Un poco más inseguro: 17% |
| Para no ser criticado por los demás | Igual (esp.): 30%, Un poco más inseguro: 30%, Un poco más seguro: 27% |
| Porque es un deber moral | Igual (esp.): 36%, Un poco más seguro: 31%, Un poco más inseguro: 23% |
| Para evitar daños a mi familia y amistades | Igual (esp.): 37%, Un poco más seguro: 30%, Un poco más inseguro: 25% |
| Para evitar castigos | Igual (esp.): 37%, Un poco más seguro: 26%, Un poco más inseguro: 23% |
| Otra | Igual (esp.): 54%, Un poco más seguro: 31%, Un poco más inseguro: 8% |
| NC | Un poco más seguro: 61%, Igual (esp.): 35%, NS: 4% |

**p4|SEG × p1|JUS** — How p4|SEG distributes given p1|JUS:

| p1|JUS (conditioning) | Top p4|SEG responses |
|---|---|
| Mejor |  Igual: 45%,  Peor: 28%,  Mejor: 24% |
| Igual de bien (esp.) |  Igual: 38%,  Peor: 30%,  Mejor: 22% |
| Igual de mal (esp.) |  Igual: 41%,  Mejor: 28%,  Peor: 20% |
| Peor |  Igual: 40%,  Mejor: 26%,  Peor: 25% |
| NS |  Peor: 37%,  Igual: 32%,  Mejor: 22% |

**p4|SEG × p2|JUS** — How p4|SEG distributes given p2|JUS:

| p2|JUS (conditioning) | Top p4|SEG responses |
|---|---|
| Prometedora |  Igual: 42%,  Peor: 26%,  Mejor: 26% |
| Con oportunidades |  Igual: 42%,  Peor: 25%,  Mejor: 23% |
| Preocupante |  Igual: 45%,  Peor: 26%,  Mejor: 22% |
| Tranquila |  Igual: 40%,  Mejor: 31%,  Peor: 26% |
| Peligrosa |  Igual: 40%,  Mejor: 27%,  Peor: 24% |
| Mejor que antes (esp.) |  Igual: 44%,  Mejor: 33%,  Mucho mejor: 11% |
| Más o menos (esp.) |  Mejor: 39%,  Igual: 39%,  Peor: 20% |
| Peor que antes (esp.) |  Igual: 34%,  Mejor: 27%,  Peor: 25% |
### Bridge Model Diagnostics

> For human inspection only — not passed to the LLM.

#### Summary

| Variable | Model | Pseudo-R² | LLR p | Dominant SES | Quality |
|----------|-------|-----------|-------|--------------|---------|
| p1|JUS | mnlogit | 0.066 | 0.631 | ? | weak |
| p2|JUS | mnlogit | 0.088 | 0.604 | ? | weak |
| p3|SEG | mnlogit | 0.128 | 0.001 | ? | good |
| p4|JUS | mnlogit | 0.047 | 0.959 | ? | weak |
| p4|SEG | mnlogit | 0.063 | 0.535 | ? | weak |
| p7|JUS | mnlogit | 0.099 | 0.392 | ? | weak |

**Mean pseudo-R²:** 0.082 &ensp;|&ensp; **Overall dominant SES dimension:** ?

> ⚠ 5/6 bridge models are weak (R²<0.02 or LLR p≥0.10). Simulated Cramér's V for those variables may underestimate the true association.

#### Per-Variable SES Predictor Detail

Top predictors by |t|-statistic — answers: which SES variable is doing the work?

**p1|JUS** (mnlogit, R²=0.066, LLR p=0.631, quality=weak)
*(coefficient table unavailable)*

**p2|JUS** (mnlogit, R²=0.088, LLR p=0.604, quality=weak)
*(coefficient table unavailable)*

**p3|SEG** (mnlogit, R²=0.128, LLR p=0.001, quality=good)
*(coefficient table unavailable)*

**p4|JUS** (mnlogit, R²=0.047, LLR p=0.959, quality=weak)
*(coefficient table unavailable)*

**p4|SEG** (mnlogit, R²=0.063, LLR p=0.535, quality=weak)
*(coefficient table unavailable)*

**p7|JUS** (mnlogit, R²=0.099, LLR p=0.392, quality=weak)
*(coefficient table unavailable)*

*Pseudo-R² = McFadden's. Low values mean SES explains little variance in that variable — the bridge simulation still produces an estimate, but its precision is reduced.*

### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from cross-dataset bivariate associations with significant p-values, notably between personal security perceptions (p3|SEG) and justice economic perceptions (p1|JUS), as well as between personal security and reasons for obeying laws (p7|JUS). These indicate weak but statistically significant relationships linking security and justice perceptions. Demographic fault lines provide secondary context on opinion fragmentation by region, sex, and age. Univariate distributions offer supporting context but do not demonstrate relationships on their own.

**Key Limitations:**
- All cross-dataset associations show weak effect sizes (Cramér's V below 0.1), limiting strength of conclusions.
- Simulation-based bivariate estimates may have inherent uncertainty despite significance testing.
- Limited number of cross-survey variable pairs restricts comprehensive analysis of security-justice relationships.
- Variables related to justice focus more on economic and political perceptions rather than direct justice system evaluations, which may limit relevance to the query.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p5|SEG, p1|JUS
- **Dispersed Variables:** p3|SEG, p4|SEG, p6|SEG, p2|JUS, p4|JUS

