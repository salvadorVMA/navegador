# Low-N Construct Investigation — Stream 4

For each construct with suspiciously low `n_valid`, diagnoses whether the cause is:
- Skip/routing patterns (prior question filters respondents)
- Sub-population design (migrants, religious, partnered, etc.)
- High non-response / data quality

**Risk thresholds**: N < 400 → flag for removal; N < 600 → caution.

---

## SOC|digital_technology_access_and_ownership

**Expected n_valid**: 255  |  **Alpha**: 0.7857  |  **Type**: good

> ⚠️ **REMOVAL CANDIDATE** — N=255 < 400. DR bridge estimates may be unreliable. Recommend removal unless routing is explainable.

**Survey**: `SOCIEDAD_DE_LA_INFORMACION` | **Total rows**: 1200

**Items**: ['p5a_7', 'p5a_10']

### Per-Item Coverage

| item | n_valid | pct_valid | n_sentinel | n_nan |
|------|---------|-----------|------------|-------|
| `p5a_7` | 316 | 26.3% | 884 | 0 |
| `p5a_10` | 385 | 32.1% | 815 | 0 |

**Rows with ALL items valid**: 255 / 1200 (21.2%)

**Missingness pattern**: 754 rows ALL items missing (62.8%), 191 rows partially missing

> Pattern: **block missingness** — large fraction has ALL items missing. Strongly suggests skip/routing (respondents skipped entire battery).

### Routing Candidate Analysis

Top 8 columns most correlated with having valid construct responses (|r| > 0.15):

**`p5_7` — * 5 Por favor, ¿podría decirme si alguien en esta vivienda cuenta con computadora de escritorio?*** (r=-0.626, n=1200)

  code=1 (Sí): n=317, 255 have construct (80%)
  code=2 (No): n=878, 0 have construct (0%)
  code=8 (NS): n=1, 0 have construct (0%)
  code=9 (NC): n=4, 0 have construct (0%)

**`p5_10` — * 5 Por favor, ¿podría decirme si alguien en esta vivienda cuenta con conexión a internet?*** (r=-0.555, n=1200)

  code=1 (Sí): n=392, 255 have construct (65%)
  code=2 (No): n=803, 0 have construct (0%)
  code=8 (NS): n=1, 0 have construct (0%)
  code=9 (NC): n=4, 0 have construct (0%)

**`p39_4` — * 39 ¿En qué lugares suele usar internet? Café Internet*** (r=+0.433, n=1200)

  code=-1 (-1): n=748, 58 have construct (8%)
  code=1 (Sí): n=193, 71 have construct (37%)
  code=2 (No): n=259, 126 have construct (49%)

**`p48_1` — * 48 Ahora dígame, ¿usted tiene cuenta en alguna de las siguientes Redes sociales? Facebook*** (r=+0.413, n=1200)

  code=-1 (-1): n=748, 58 have construct (8%)
  code=1 (Sí): n=414, 183 have construct (44%)
  code=2 (No): n=38, 14 have construct (37%)

**`p39_2` — * 39 ¿En qué lugares suele usar internet? Trabajo*** (r=+0.411, n=1200)

  code=-1 (-1): n=748, 58 have construct (8%)
  code=1 (Sí): n=177, 75 have construct (42%)
  code=2 (No): n=270, 118 have construct (44%)
  code=8 (NS): n=1, 1 have construct (100%)
  code=9 (NC): n=4, 3 have construct (75%)

**`p50_13` — * 50 ¿En las redes sociales usted acostumbra publicar o compartir problemas personales?*** (r=+0.409, n=1200)

  code=-1 (-1): n=780, 68 have construct (9%)
  code=1 (Sí): n=100, 32 have construct (32%)
  code=2 (No): n=313, 151 have construct (48%)
  code=8 (NS): n=2, 1 have construct (50%)
  code=9 (NC): n=5, 3 have construct (60%)

**`p44_6` — * 44 ¿Cuál de las siguientes fuentes en internet consulta principalmente para mantenerse informado? Buscadores como Google*** (r=+0.407, n=1200)

  code=-1 (-1): n=748, 58 have construct (8%)
  code=1 (Sí): n=362, 161 have construct (44%)
  code=2 (No): n=88, 34 have construct (39%)
  code=8 (NS): n=1, 1 have construct (100%)
  code=9 (NC): n=1, 1 have construct (100%)

**`p50_7` — * 50 ¿En las redes sociales usted acostumbra publicar o compartir lugar donde vive?*** (r=+0.407, n=1200)

  code=-1 (-1): n=780, 68 have construct (9%)
  code=1 (Sí): n=107, 45 have construct (42%)
  code=2 (No): n=305, 136 have construct (45%)
  code=8 (NS): n=3, 2 have construct (67%)
  code=9 (NC): n=5, 4 have construct (80%)

### Recommendation

**Remove from bridge** — N=255 is below the minimum for reliable DR estimation. Even if routing is explainable, bootstrap CIs will be unreliably wide. Mark construct as `excluded_low_n` in SVS v4.
TODO build new construct with vars above

---

## MIG|transnational_social_ties

**Expected n_valid**: 360  |  **Alpha**: 0.601  |  **Type**: questionable

> ⚠️ **REMOVAL CANDIDATE** — N=360 < 400. DR bridge estimates may be unreliable. Recommend removal unless routing is explainable.

**Survey**: `MIGRACION` | **Total rows**: 1199

**Items**: ['p21', 'p21_2', 'p22', 'p23', 'p24']

### Per-Item Coverage

| item | n_valid | pct_valid | n_sentinel | n_nan |
|------|---------|-----------|------------|-------|
| `p21` | 1199 | 100.0% | 0 | 0 |
| `p21_2` | 360 | 30.0% | 839 | 0 |
| `p22` | 1199 | 100.0% | 0 | 0 |
| `p23` | 487 | 40.6% | 712 | 0 |
| `p24` | 487 | 40.6% | 712 | 0 |

**Rows with ALL items valid**: 360 / 1199 (30.0%)

**Missingness pattern**: 0 rows ALL items missing (0.0%), 839 rows partially missing

> Pattern: **scattered missingness** — high partial missingness. May indicate item-level non-response rather than routing.

### Routing Candidate Analysis

Top 8 columns most correlated with having valid construct responses (|r| > 0.15):

**`p21_1` — * 21.1 ¿En qué país(es)?*** (r=+0.560, n=1199)

  code=-1 (-1): n=839, 0 have construct (0%)
  code=10 (Otro): n=1, 1 have construct (100%)
  code=11 (Estados Unidos): n=284, 284 have construct (100%)
  code=12 (Canadá): n=12, 12 have construct (100%)
  code=13 (Alemania): n=1, 1 have construct (100%)
  code=14 (España): n=10, 10 have construct (100%)
  code=15 (Argentina): n=2, 2 have construct (100%)
  code=17 (Francia): n=2, 2 have construct (100%)
  code=18 (Cuba): n=1, 1 have construct (100%)
  code=21 (Inglaterra): n=1, 1 have construct (100%)
  code=35 (Honduras): n=1, 1 have construct (100%)
  code=43 (Chile): n=1, 1 have construct (100%)
  code=48 (Uruguay): n=1, 1 have construct (100%)
  code=98 (NS): n=8, 8 have construct (100%)
  code=99 (NC): n=35, 35 have construct (100%)

**`p21_3` — * 21.3  Y en promedio, ¿cuánto del ingreso mensual de su hogar representa el dinero que recibe de sus parientes fuera del país?*** (r=+0.409, n=1199)

  code=-1 (-1): n=1100, 261 have construct (24%)
  code=1 (Más de la mitad): n=10, 10 have construct (100%)
  code=2 (La mitad): n=27, 27 have construct (100%)
  code=3 (Menos de la mitad): n=50, 50 have construct (100%)
  code=8 (NS): n=9, 9 have construct (100%)
  code=9 (NC): n=3, 3 have construct (100%)

**`p16_1` — * 16.1 ¿En qué país?*** (r=+0.244, n=1199)

  code=-1 (-1): n=1115, 297 have construct (27%)
  code=10 (Otro): n=1, 0 have construct (0%)
  code=11 (Estados Unidos): n=71, 55 have construct (77%)
  code=14 (España): n=3, 3 have construct (100%)
  code=15 (Argentina): n=1, 0 have construct (0%)
  code=16 (Guatemala): n=1, 0 have construct (0%)
  code=17 (Francia): n=1, 1 have construct (100%)
  code=18 (Cuba): n=1, 1 have construct (100%)
  code=19 (Holanda): n=1, 1 have construct (100%)
  code=28 (China): n=1, 0 have construct (0%)
  code=30 (Eslovenia): n=1, 0 have construct (0%)
  code=35 (Honduras): n=1, 1 have construct (100%)
  code=46 (Nicaragua): n=1, 1 have construct (100%)

**`p16_3` — * 16.3 ¿Y cuál fue la principal razón?*** (r=+0.226, n=1199)

  code=-1 (-1): n=1115, 297 have construct (27%)
  code=1 (Trabajo): n=59, 46 have construct (78%)
  code=2 (Estudios): n=14, 10 have construct (71%)
  code=3 (Reagrupación familiar): n=3, 1 have construct (33%)
  code=4 (Sentimentales (pareja)): n=5, 5 have construct (100%)
  code=5 (Desastres Naturales): n=1, 0 have construct (0%)
  code=7 (Inseguridad): n=1, 0 have construct (0%)
  code=9 (NC): n=1, 1 have construct (100%)

**`p4_1` — * 4 Con la palabra maíz, yo asocio comida, mercado, animales. ¿Podría decirme, por favor, tres palabras que asocie con la palabra MIGRANTE? 1° MENCIÓN*** (r=-0.216, n=165)

  code=98 (98): n=133, 40 have construct (30%)
  code=99 (99): n=32, 2 have construct (6%)

**`Region` — *Región*** (r=-0.167, n=1199)

  code=1 (Centro): n=348, 139 have construct (40%)
  code=2 (D. F. y Estado de México): n=311, 98 have construct (32%)
  code=3 (Norte): n=312, 81 have construct (26%)
  code=4 (Sur): n=228, 42 have construct (18%)

**`p17` — * 17  ¿Si pudiera, se iría a vivir fuera de México?*** (r=-0.167, n=1199)

  code=1 (Sí): n=544, 222 have construct (41%)
  code=2 (No): n=449, 92 have construct (20%)
  code=3 (Depende (esp)): n=183, 45 have construct (25%)
  code=8 (NS): n=16, 1 have construct (6%)
  code=9 (NC): n=7, 0 have construct (0%)

**`Estrato` — *Estrato*** (r=-0.162, n=1199)

  code=11 (Centro y 100 000 y más habitantes): n=144, 60 have construct (42%)
  code=12 (Centro y 15 000-99 999 habitantes): n=72, 15 have construct (21%)
  code=13 (Centro y 2 500-14 999 habitantes): n=72, 33 have construct (46%)
  code=14 (Centro y 1-2499 habitantes): n=60, 31 have construct (52%)
  code=21 (D. F. y Estado de México y 100 000 y más habitantes): n=191, 60 have construct (31%)
  code=22 (D. F. y Estado de México y 15 000-99 999 habitantes): n=48, 20 have construct (42%)
  code=23 (D. F. y Estado de México y 2 500-14 999 habitantes): n=48, 11 have construct (23%)
  code=24 (D. F. y Estado de México y 1-2499 habitantes): n=24, 7 have construct (29%)
  code=31 (Norte y 100 000 y más habitantes): n=192, 52 have construct (27%)
  code=32 (Norte y 15 000-99 999 habitantes): n=48, 12 have construct (25%)
  code=33 (Norte y 2 500-14 999 habitantes): n=48, 10 have construct (21%)
  code=34 (Norte y 1-2499 habitantes): n=24, 7 have construct (29%)
  code=41 (Sur y 100 000 y más habitantes): n=96, 11 have construct (11%)
  code=42 (Sur y 15 000-99 999 habitantes): n=48, 4 have construct (8%)
  code=43 (Sur y 2 500-14 999 habitantes): n=48, 22 have construct (46%)
  code=44 (Sur y 1-2499 habitantes): n=36, 5 have construct (14%)

### Recommendation

**Remove from bridge** — N=360 is below the minimum for reliable DR estimation. Even if routing is explainable, bootstrap CIs will be unreliably wide. Mark construct as `excluded_low_n` in SVS v4.
TODO remove
---

## SOC|internet_engagement_and_digital_literacy

**Expected n_valid**: 364  |  **Alpha**: 0.4825  |  **Type**: tier3_caveat

> ⚠️ **REMOVAL CANDIDATE** — N=364 < 400. DR bridge estimates may be unreliable. Recommend removal unless routing is explainable.

**Survey**: `SOCIEDAD_DE_LA_INFORMACION` | **Total rows**: 1200

**Items**: ['p33_7', 'p45_2', 'p39_7']

### Per-Item Coverage

| item | n_valid | pct_valid | n_sentinel | n_nan |
|------|---------|-----------|------------|-------|
| `p33_7` | 407 | 33.9% | 793 | 0 |
| `p45_2` | 452 | 37.7% | 748 | 0 |
| `p39_7` | 452 | 37.7% | 748 | 0 |

**Rows with ALL items valid**: 364 / 1200 (30.3%)

**Missingness pattern**: 705 rows ALL items missing (58.8%), 131 rows partially missing

> Pattern: **block missingness** — large fraction has ALL items missing. Strongly suggests skip/routing (respondents skipped entire battery).

### Routing Candidate Analysis

Top 8 columns most correlated with having valid construct responses (|r| > 0.15):

**`p30` — * 30 ¿Cómo diría que es el manejo que tiene de la computadora?*** (r=+0.860, n=1200)

  code=-1 (-1): n=793, 0 have construct (0%)
  code=1 (Muy bueno): n=75, 72 have construct (96%)
  code=2 (Bueno): n=191, 176 have construct (92%)
  code=3 (Regular (esp.)): n=125, 103 have construct (82%)
  code=4 (Malo): n=13, 11 have construct (85%)
  code=5 (Muy malo): n=2, 1 have construct (50%)
  code=6 (Nulo): n=1, 1 have construct (100%)

**`p33_3` — * 33 ¿Para qué utiliza la computadora? Entretenerse*** (r=+0.854, n=1200)

  code=-1 (-1): n=793, 0 have construct (0%)
  code=1 (Sí): n=314, 281 have construct (89%)
  code=2 (No): n=91, 82 have construct (90%)
  code=9 (NC): n=2, 1 have construct (50%)

**`p33_1` — * 33 ¿Para qué utiliza la computadora? Trabajar*** (r=+0.844, n=1200)

  code=-1 (-1): n=793, 0 have construct (0%)
  code=1 (Sí): n=178, 162 have construct (91%)
  code=2 (No): n=225, 199 have construct (88%)
  code=8 (NS): n=1, 1 have construct (100%)
  code=9 (NC): n=3, 2 have construct (67%)

**`p33_4` — * 33 ¿Para qué utiliza la computadora? Jugar*** (r=+0.844, n=1200)

  code=-1 (-1): n=793, 0 have construct (0%)
  code=1 (Sí): n=230, 208 have construct (90%)
  code=2 (No): n=174, 154 have construct (89%)
  code=9 (NC): n=3, 2 have construct (67%)

**`p33_5` — * 33 ¿Para qué utiliza la computadora? Comunicarse con sus amigos o familiares*** (r=+0.838, n=1200)

  code=-1 (-1): n=793, 0 have construct (0%)
  code=1 (Sí): n=345, 319 have construct (92%)
  code=2 (No): n=60, 44 have construct (73%)
  code=9 (NC): n=2, 1 have construct (50%)

**`p48_4` — * 48 Ahora dígame, ¿usted tiene cuenta en alguna de las siguientes Redes sociales? LinkedIn*** (r=+0.832, n=1200)

  code=-1 (-1): n=748, 0 have construct (0%)
  code=1 (Sí): n=51, 43 have construct (84%)
  code=2 (No): n=400, 320 have construct (80%)
  code=9 (NC): n=1, 1 have construct (100%)

**`p45_3` — * 45 ¿Y alguna vez usted ha usado internet para hacer pago de servicios (luz, predial, tenencia, banco…)?*** (r=+0.830, n=1200)

  code=-1 (-1): n=748, 0 have construct (0%)
  code=1 (Sí): n=99, 79 have construct (80%)
  code=2 (No): n=352, 284 have construct (81%)
  code=8 (NS): n=1, 1 have construct (100%)

**`p33_6` — * 33 ¿Para qué utiliza la computadora? Informarse*** (r=+0.829, n=1200)

  code=-1 (-1): n=793, 0 have construct (0%)
  code=1 (Sí): n=269, 254 have construct (94%)
  code=2 (No): n=134, 106 have construct (79%)
  code=8 (NS): n=2, 2 have construct (100%)
  code=9 (NC): n=2, 2 have construct (100%)

### Recommendation

**Remove from bridge** — N=364 is below the minimum for reliable DR estimation. Even if routing is explainable, bootstrap CIs will be unreliably wide. Mark construct as `excluded_low_n` in SVS v4.
TODO remove

---

## DEP|reading_engagement_and_literacy

**Expected n_valid**: 483  |  **Alpha**: 0.3654  |  **Type**: single_item_tier2

> ⚠️ **CAUTION** — N=483 < 600. CI widths will be inflated. Review routing before keeping.

**Survey**: `CULTURA_LECTURA_Y_DEPORTE` | **Total rows**: 1200

**Items**: ['p15a_1', 'p15c_2', 'p15c_3']

### Per-Item Coverage

| item | n_valid | pct_valid | n_sentinel | n_nan |
|------|---------|-----------|------------|-------|
| `p15a_1` | 1200 | 100.0% | 0 | 0 |
| `p15c_2` | 483 | 40.2% | 717 | 0 |
| `p15c_3` | 436 | 36.3% | 764 | 0 |

**Rows with ALL items valid**: 291 / 1200 (24.2%)

**Missingness pattern**: 0 rows ALL items missing (0.0%), 909 rows partially missing

> Pattern: **scattered missingness** — high partial missingness. May indicate item-level non-response rather than routing.

### Routing Candidate Analysis

Top 8 columns most correlated with having valid construct responses (|r| > 0.15):

**`p15a_3` — * 15. ¿Acostumbra leer algunas de las siguientes publicaciones? Periódicos o revistas nacionales (del país)*** (r=-0.749, n=1200)

  code=1 (Sí): n=436, 291 have construct (67%)
  code=2 (No): n=764, 0 have construct (0%)

**`p15b_3` — * 15. ¿Con que frecuencia las lee? Periódicos o revistas nacionales (del país)*** (r=+0.694, n=1200)

  code=-1 (-1): n=764, 0 have construct (0%)
  code=1 (Menos de una vez a la semana): n=106, 73 have construct (69%)
  code=2 (Una vez a la semana): n=139, 95 have construct (68%)
  code=3 (Algunas veces a la semana): n=129, 81 have construct (63%)
  code=4 (Varias veces a la semana): n=62, 42 have construct (68%)

**`p15a_2` — * 15. ¿Acostumbra leer algunas de las siguientes publicaciones? Periódicos o revistas  regionales (del estado)*** (r=-0.689, n=1200)

  code=1 (Sí): n=483, 291 have construct (60%)
  code=2 (No): n=717, 0 have construct (0%)

**`p15b_2` — * 15. ¿Con que frecuencia las lee? Periódicos o revistas  regionales (del estado)*** (r=+0.660, n=1200)

  code=-1 (-1): n=717, 0 have construct (0%)
  code=1 (Menos de una vez a la semana): n=106, 59 have construct (56%)
  code=2 (Una vez a la semana): n=155, 95 have construct (61%)
  code=3 (Algunas veces a la semana): n=154, 91 have construct (59%)
  code=4 (Varias veces a la semana): n=68, 46 have construct (68%)

**`p15a_4` — * 15. ¿Acostumbra leer algunas de las siguientes publicaciones? Periódicos o revistas internacionales  (del extranjero)*** (r=-0.472, n=1200)

  code=1 (Sí): n=200, 139 have construct (70%)
  code=2 (No): n=1000, 152 have construct (15%)

**`p15b_4` — * 15. ¿Con que frecuencia las lee? Periódicos o revistas internacionales  (del extranjero)*** (r=+0.467, n=1200)

  code=-1 (-1): n=1000, 152 have construct (15%)
  code=1 (Menos de una vez a la semana): n=44, 30 have construct (68%)
  code=2 (Una vez a la semana): n=76, 48 have construct (63%)
  code=3 (Algunas veces a la semana): n=58, 41 have construct (71%)
  code=4 (Varias veces a la semana): n=22, 20 have construct (91%)

**`p15c_4` — * 15. Versión :Periódicos o revistas internacionales  (del extranjero)*** (r=+0.464, n=1200)

  code=-1 (-1): n=1000, 152 have construct (15%)
  code=1 (Versión impresa): n=116, 79 have construct (68%)
  code=2 (Versión digital): n=84, 60 have construct (71%)

**`p15b_1` — * 15. ¿Con que frecuencia las lee? Periódicos o revistas locales (del barrio)*** (r=+0.277, n=1200)

  code=-1 (-1): n=647, 85 have construct (13%)
  code=1 (Menos de una vez a la semana): n=114, 38 have construct (33%)
  code=2 (Una vez a la semana): n=193, 71 have construct (37%)
  code=3 (Algunas veces a la semana): n=153, 57 have construct (37%)
  code=4 (Varias veces a la semana): n=93, 40 have construct (43%)

### Recommendation

**Keep with annotation** — Strong routing pattern detected via `p15a_3` (r=-0.749). Construct measures a sub-population. γ estimates are conditional on that sub-population. Add routing note to `significant_constructs.md`.
TODO USE acostumbra questions, not frecuencia
---

## JUS|legal_self_efficacy_and_access

**Expected n_valid**: 635  |  **Alpha**: 0.4386  |  **Type**: tier3_caveat

**Survey**: `JUSTICIA` | **Total rows**: 1200

**Items**: ['p35', 'p36', 'p37', 'p39', 'p54']

### Per-Item Coverage

| item | n_valid | pct_valid | n_sentinel | n_nan |
|------|---------|-----------|------------|-------|
| `p35` | 668 | 55.7% | 532 | 0 |
| `p36` | 1200 | 100.0% | 0 | 0 |
| `p37` | 1200 | 100.0% | 0 | 0 |
| `p39` | 1119 | 93.2% | 81 | 0 |
| `p54` | 1200 | 100.0% | 0 | 0 |

**Rows with ALL items valid**: 635 / 1200 (52.9%)

**Missingness pattern**: 0 rows ALL items missing (0.0%), 565 rows partially missing

> Pattern: **scattered missingness** — high partial missingness. May indicate item-level non-response rather than routing.

### Routing Candidate Analysis

Top 5 columns most correlated with having valid construct responses (|r| > 0.15):

**`p34_1` — * 34.1 ¿Para qué sirve el amparo?*** (r=+0.868, n=1200)

  code=-1 (-1): n=532, 0 have construct (0%)
  code=1 (Forma de evitar ir a la cárcel): n=314, 289 have construct (92%)
  code=2 (Forma de protección y apoyo): n=206, 203 have construct (99%)
  code=3 (Forma de proteger los Derechos Humanos): n=144, 139 have construct (97%)
  code=4 (Otra (esp.)): n=2, 2 have construct (100%)
  code=8 (NS): n=1, 1 have construct (100%)
  code=9 (NC): n=1, 1 have construct (100%)

**`p34` — * 34 ¿Sabe usted qué es el amparo?*** (r=-0.503, n=1200)

  code=1 (Sí): n=618, 586 have construct (95%)
  code=2 (No): n=517, 0 have construct (0%)
  code=3 (Más o menos (esp.)): n=50, 49 have construct (98%)
  code=8 (NS): n=10, 0 have construct (0%)
  code=9 (NC): n=5, 0 have construct (0%)

**`p49` — * 49 Si un juez o magistrado realiza una conducta indebida durante un juicio, ¿quién considera usted que debe sancionarlo?*** (r=-0.193, n=1200)

  code=1 (Un tribunal superior): n=532, 331 have construct (62%)
  code=2 (El Consejo de la Judicatura): n=294, 145 have construct (49%)
  code=3 (El Ministerio Público): n=134, 65 have construct (49%)
  code=4 (La Cámara de Diputados): n=56, 32 have construct (57%)
  code=5 (Otro): n=3, 2 have construct (67%)
  code=6 (La sociedad/ El pueblo): n=8, 6 have construct (75%)
  code=7 (El ejercito): n=1, 0 have construct (0%)
  code=8 (El presidente): n=33, 17 have construct (52%)
  code=98 (NS): n=103, 28 have construct (27%)
  code=99 (NC): n=36, 9 have construct (25%)

**`p49a` — * 49 Si un juez o magistrado realiza una conducta indebida durante un juicio, ¿quién considera usted que debe sancionarlo?*** (r=-0.193, n=1200)

  code=1 (Un tribunal superior): n=532, 331 have construct (62%)
  code=2 (El Consejo de la Judicatura): n=294, 145 have construct (49%)
  code=3 (El Ministerio Público): n=134, 65 have construct (49%)
  code=4 (La Cámara de Diputados): n=56, 32 have construct (57%)
  code=5 (Otro (esp.)): n=45, 25 have construct (56%)
  code=98 (NS): n=103, 28 have construct (27%)
  code=99 (NC): n=36, 9 have construct (25%)

**`escol` — *Escolaridad*** (r=+0.154, n=1200)

  code=1 (Ninguna): n=126, 44 have construct (35%)
  code=2 (Primaria): n=223, 114 have construct (51%)
  code=3 (Secundaria): n=458, 233 have construct (51%)
  code=4 (Preparatoria o Bachillerato): n=318, 189 have construct (59%)
  code=5 (Universidad o Posgrado): n=74, 55 have construct (74%)
  code=9 (NC): n=1, 0 have construct (0%)

### Recommendation

**Keep with annotation** — Strong routing pattern detected via `p34_1` (r=+0.868). Construct measures a sub-population. γ estimates are conditional on that sub-population. Add routing note to `significant_constructs.md`.

---TODO remove

## GEN|intimate_partner_power_dynamics

**Expected n_valid**: 637  |  **Alpha**: 0.4071  |  **Type**: tier3_caveat

**Survey**: `GENERO` | **Total rows**: 1200

**Items**: ['p19', 'p23_1', 'p23_5']

### Per-Item Coverage

| item | n_valid | pct_valid | n_sentinel | n_nan |
|------|---------|-----------|------------|-------|
| `p19` | 637 | 53.1% | 563 | 0 |
| `p23_1` | 637 | 53.1% | 563 | 0 |
| `p23_5` | 637 | 53.1% | 563 | 0 |

**Rows with ALL items valid**: 637 / 1200 (53.1%)

**Missingness pattern**: 563 rows ALL items missing (46.9%), 0 rows partially missing

> Pattern: **block missingness** — large fraction has ALL items missing. Strongly suggests skip/routing (respondents skipped entire battery).

### Routing Candidate Analysis

Top 8 columns most correlated with having valid construct responses (|r| > 0.15):

**`p23_3` — * 23. Regularmente, ¿usted pide permiso a su pareja para hacer gastos cotidianos?*** (r=+0.937, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Sí): n=162, 162 have construct (100%)
  code=2 (Depende): n=173, 173 have construct (100%)
  code=3 (No): n=302, 302 have construct (100%)

**`p20_1` — * 20. En su hogar, ¿Quién toma o tomaba las decisiones con respecto a comprar muebles para la casa?*** (r=+0.936, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Usted): n=121, 121 have construct (100%)
  code=2 (Su pareja): n=73, 73 have construct (100%)
  code=3 (Ambos): n=433, 433 have construct (100%)
  code=4 (Otra persona): n=7, 7 have construct (100%)
  code=8 (NS): n=1, 1 have construct (100%)
  code=9 (NC): n=2, 2 have construct (100%)

**`p23_4` — * 23. Regularmente, ¿usted pide permiso a su pareja para visitar amistades?*** (r=+0.932, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Sí): n=181, 181 have construct (100%)
  code=2 (Depende): n=156, 156 have construct (100%)
  code=3 (No): n=300, 300 have construct (100%)

**`p20_4` — * 20. En su hogar, ¿Quién toma o tomaba las decisiones con respecto a realizar un gasto fuerte?*** (r=+0.932, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Usted): n=108, 108 have construct (100%)
  code=2 (Su pareja): n=87, 87 have construct (100%)
  code=3 (Ambos): n=430, 430 have construct (100%)
  code=4 (Otra persona): n=7, 7 have construct (100%)
  code=8 (NS): n=1, 1 have construct (100%)
  code=9 (NC): n=4, 4 have construct (100%)

**`p20_5` — * 20. En su hogar, ¿Quién toma o tomaba las decisiones con respecto a decidir dónde vivir?*** (r=+0.930, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Usted): n=103, 103 have construct (100%)
  code=2 (Su pareja): n=84, 84 have construct (100%)
  code=3 (Ambos): n=439, 439 have construct (100%)
  code=4 (Otra persona): n=4, 4 have construct (100%)
  code=8 (NS): n=4, 4 have construct (100%)
  code=9 (NC): n=3, 3 have construct (100%)

**`p18` — * 18. En su hogar ¿quién lleva el manejo del dinero diario?*** (r=+0.924, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Usted): n=190, 190 have construct (100%)
  code=2 (Su pareja): n=135, 135 have construct (100%)
  code=3 (Ambos): n=310, 310 have construct (100%)
  code=4 (Alguien más): n=1, 1 have construct (100%)
  code=9 (NC): n=1, 1 have construct (100%)

**`p20_6` — * 20. En su hogar, ¿Quién toma o tomaba las decisiones con respecto a qué hacer el fin de semana?*** (r=+0.921, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Usted): n=94, 94 have construct (100%)
  code=2 (Su pareja): n=77, 77 have construct (100%)
  code=3 (Ambos): n=451, 451 have construct (100%)
  code=4 (Otra persona): n=4, 4 have construct (100%)
  code=8 (NS): n=6, 6 have construct (100%)
  code=9 (NC): n=5, 5 have construct (100%)

**`p23_2` — * 23. Regularmente, ¿usted pide permiso a su pareja para salir sola(o) de noche?*** (r=+0.904, n=1200)

  code=-1 (-1): n=563, 0 have construct (0%)
  code=1 (Sí): n=239, 239 have construct (100%)
  code=2 (Depende): n=154, 154 have construct (100%)
  code=3 (No): n=241, 241 have construct (100%)
  code=8 (NS): n=1, 1 have construct (100%)
  code=9 (NC): n=2, 2 have construct (100%)

### Recommendation

**Keep with annotation** — Strong routing pattern detected via `p23_3` (r=+0.937). Construct measures a sub-population. γ estimates are conditional on that sub-population. Add routing note to `significant_constructs.md`.
TODO find question that filters, and see is it makes sense to recover these rows with a neutral point on a scale built with the others - but what scale? think about it and make a proposal
---

## REL|religious_socialization

**Expected n_valid**: 847  |  **Alpha**: 0.5548  |  **Type**: questionable

**Survey**: `RELIGION_SECULARIZACION_Y_LAICIDAD` | **Total rows**: 1200

**Items**: ['p2', 'p3', 'p4', 'p5', 'p6', 'p33_1']

### Per-Item Coverage

| item | n_valid | pct_valid | n_sentinel | n_nan |
|------|---------|-----------|------------|-------|
| `p2` | 1012 | 84.3% | 188 | 0 |
| `p3` | 972 | 81.0% | 228 | 0 |
| `p4` | 974 | 81.2% | 226 | 0 |
| `p5` | 1185 | 98.8% | 15 | 0 |
| `p6` | 1192 | 99.3% | 8 | 0 |
| `p33_1` | 1185 | 98.8% | 15 | 0 |

**Rows with ALL items valid**: 847 / 1200 (70.6%)

**Missingness pattern**: 0 rows ALL items missing (0.0%), 353 rows partially missing

> Pattern: **scattered missingness** — high partial missingness. May indicate item-level non-response rather than routing.

### Routing Candidate Analysis

Top 8 columns most correlated with having valid construct responses (|r| > 0.15):

**`religion` — *Religión*** (r=-0.537, n=1194)

  code=1 (Católicos): n=796, 656 have construct (82%)
  code=2 (Religiones históricas): n=21, 15 have construct (71%)
  code=3 (Disidencias históricas): n=207, 176 have construct (85%)
  code=4 (New Age): n=1, 0 have construct (0%)
  code=5 (Ateos o no religiosos): n=169, 0 have construct (0%)

**`p18` — * 18. En una escala de 0 a 10, en donde 0 es nada y 10 es mucha, ¿qué tanta importancia tiene Dios en su vida?*** (r=-0.236, n=1200)

  code=0 (0): n=69, 13 have construct (19%)
  code=1 (1): n=10, 5 have construct (50%)
  code=2 (2): n=9, 3 have construct (33%)
  code=3 (3): n=3, 1 have construct (33%)
  code=4 (4): n=3, 0 have construct (0%)
  code=5 (5): n=36, 22 have construct (61%)
  code=6 (6): n=29, 15 have construct (52%)
  code=7 (7): n=83, 57 have construct (69%)
  code=8 (8): n=153, 117 have construct (76%)
  code=9 (9): n=143, 116 have construct (81%)
  code=10 (10): n=589, 483 have construct (82%)
  code=98 (NS): n=34, 6 have construct (18%)
  code=99 (NC): n=39, 9 have construct (23%)

**`p7_2` — * 7. ¿En cuáles de los siguientes lugares recibió una educación religiosa? 2° MENCIÓN*** (r=+0.198, n=1200)

  code=-1 (-1): n=841, 544 have construct (65%)
  code=1 (En la casa): n=94, 77 have construct (82%)
  code=2 (En la escuela): n=48, 37 have construct (77%)
  code=3 (En el templo): n=196, 170 have construct (87%)
  code=4 (En todos estos lugares (esp.)): n=11, 10 have construct (91%)
  code=5 (En otro lugar (esp.)): n=10, 9 have construct (90%)

**`p52_4` — * 52. ¿Qué tan de acuerdo o en desacuerdo está usted con las siguientes afirmaciones? Sería mejor para México si al cubrir cargos públicos se eligiera a personas con fuertes convicciones religiosas*** (r=-0.182, n=1200)

  code=1 (De acuerdo): n=130, 110 have construct (85%)
  code=2 (De acuerdo en parte (esp.)): n=126, 104 have construct (83%)
  code=3 (Ni de acuerdo ni en desacuerdo (esp.)): n=228, 154 have construct (68%)
  code=4 (En desacuerdo en parte (esp.)): n=108, 85 have construct (79%)
  code=5 (En desacuerdo): n=535, 360 have construct (67%)
  code=6 (Otra (esp.)): n=4, 4 have construct (100%)
  code=8 (8): n=55, 26 have construct (47%)
  code=9 (9): n=14, 4 have construct (29%)

**`p16_1` — * 16. Para usted en lo personal, ¿es importante realizar una ceremonia o rito para algunos de los siguientes eventos?  Nacimiento*** (r=-0.169, n=1200)

  code=1 (Sí, es importante): n=802, 649 have construct (81%)
  code=2 (No, es importante): n=369, 191 have construct (52%)
  code=98 (NS): n=18, 5 have construct (28%)
  code=99 (NC): n=11, 2 have construct (18%)

**`p45_6` — * 45. En una escala de 0 a 10, donde 0 es no confío nada y 10 es confío mucho, ¿qué tanta confianza tiene usted en su Iglesia?*** (r=-0.159, n=1200)

  code=0 (0): n=87, 26 have construct (30%)
  code=1 (1): n=12, 4 have construct (33%)
  code=2 (2): n=16, 10 have construct (62%)
  code=3 (3): n=19, 11 have construct (58%)
  code=4 (4): n=20, 11 have construct (55%)
  code=5 (5): n=91, 54 have construct (59%)
  code=6 (6): n=67, 47 have construct (70%)
  code=7 (7): n=118, 86 have construct (73%)
  code=8 (8): n=181, 128 have construct (71%)
  code=9 (9): n=165, 145 have construct (88%)
  code=10 (10): n=356, 303 have construct (85%)
  code=98 (NS): n=30, 12 have construct (40%)
  code=99 (NC): n=38, 10 have construct (26%)

**`p17_1` — * 17. ¿Cree usted en la existencia de Dios?*** (r=-0.158, n=1200)

  code=1 (Sí): n=959, 773 have construct (81%)
  code=2 (Sí, en parte (esp.)): n=89, 41 have construct (46%)
  code=3 (No): n=124, 25 have construct (20%)
  code=4 (Otra (esp.)): n=5, 2 have construct (40%)
  code=98 (NS): n=15, 4 have construct (27%)
  code=99 (NC): n=8, 2 have construct (25%)

**`p33_3` — * 33. ¿Sus padres y usted piensan (pensaban) de la misma manera sobre los siguientes aspectos? El matrimonio*** (r=-0.152, n=1200)

  code=1 (Sí): n=728, 573 have construct (79%)
  code=2 (Sí, en parte (esp.)): n=217, 151 have construct (70%)
  code=3 (No): n=241, 121 have construct (50%)
  code=98 (NS): n=11, 2 have construct (18%)
  code=99 (NC): n=3, 0 have construct (0%)

### Recommendation

**Keep with annotation** — Strong routing pattern detected via `religion` (r=-0.537). Construct measures a sub-population. γ estimates are conditional on that sub-population. Add routing note to `significant_constructs.md`.
TODO propose a n alternative list os questions to measure religiuos sociialization, but be careful with gateways and filters to keep n high
---

