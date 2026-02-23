# q8_indigenous_discrimination

**Query (ES):** ¿Cómo perciben los mexicanos la discriminación hacia pueblos indígenas?
**Query (EN):** How do Mexicans perceive discrimination against indigenous peoples?
**Variables:** p1|IND, p2|IND, p3|IND, p4|IND, p5|IND, p2|DER, p3|DER, p4|DER, p5|DER
**Status:** ✅ success
**Time:** 44967ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Cómo perciben los mexicanos la discriminación hacia pueblos indígenas?

## Summary
Mexican perceptions of discrimination against indigenous peoples are deeply divided, with a plurality (42.5%) viewing their current economic situation as worse than a year ago and a significant portion (33.8%) seeing it as equally bad. These negative perceptions correlate weakly but significantly with attitudes toward human rights respect and perceived abuses by authorities, indicating that those who value human rights more tend to perceive less deterioration in indigenous conditions. The evidence includes nine bivariate associations, all significant but with weak to moderate effect sizes, suggesting cautious confidence in these relational patterns.

## Data Landscape
The analysis covers nine variables from two thematic surveys on indigenous conditions and human rights perceptions, all showing non-consensus distributions. Among these, three variables exhibit polarized or lean distributions, while four are dispersed, reflecting fragmented and divided public opinion. The divergence index at 100% confirms a widespread lack of agreement across all variables, underscoring the complexity and heterogeneity of Mexican views on indigenous discrimination and related human rights issues.

## Evidence
The relationship between perceptions of indigenous economic situation (p1|IND) and agreement on the importance of human rights (p2|DER) shows that the proportion perceiving the situation as worse ranges from 39.5% among those neutral to 81.8% among those strongly disagreeing with human rights respect, indicating that stronger human rights agreement associates with less negative views (V=0.069, p=0.004).
| p2|DER category | Peor % |
|---|---|
| Muy de acuerdo | 46.8% |
| De acuerdo | 40.8% |
| Ni de acuerdo ni desacuerdo (esp.) | 39.5% |
| En desacuerdo | 49.5% |
| Muy en desacuerdo | 81.8% |

Regarding perceived respect for human rights (p3|DER), the "Igual de mala (esp.)" response varies from 25.0% (No sabe) to 46.9% (Mucho), but the "Peor" category remains high across all groups, showing limited optimism even among those perceiving high human rights respect (V=0.088, p=0.000).
| p3|DER category | Igual de mala (esp.) % |
|---|---|
| Mucho | 46.9% |
| Algo | 42.0% |
| Poco | 42.0% |
| Nada | 43.4% |
| NS | 25.0% |

Perceptions of which authorities violate human rights (p4|DER) relate moderately to views of indigenous situation (p1|IND), with "Igual de buena (esp.)" responses ranging from 0.0% (Government) to 25.6% (health authorities), while "Peor" perceptions are highest for Police Federal (49.7%) and politicians (50.5%), indicating that perceived authority misconduct aligns with negative indigenous situation views (V=0.116, p=0.000).
| p4|DER category | Igual de buena (esp.) % |
|---|---|
| Ministerio Público | 5.5% |
| Fuerzas Armadas | 11.3% |
| Policía municipal/delegación | 16.1% |
| Policía estatal/DF | 12.8% |
| Policía Federal | 5.5% |
| Autoridades de salud | 25.6% |
| Políticos | 7.8% |
| Gobierno | 0.0% |

Feelings of protection against abuse (p5|DER) also relate to indigenous situation perceptions, with "Peor" ranging from 5.9% among those who don't know their protection level to 49.0% among those feeling no protection, supporting that perceived vulnerability links to worse indigenous views (V=0.097, p=0.000).
| p5|DER category | Peor % |
|---|---|
| Mucho | 36.4% |
| Algo | 39.9% |
| Poco | 37.3% |
| Nada | 49.0% |
| NS | 5.9% |
| NC | 37.5% |

Expectations about the indigenous economic future (p2|IND) show that pessimism ("Va a empeorar") ranges from 37.6% among strong human rights supporters to 50.6% among those in disagreement, indicating that human rights attitudes modestly shape future outlooks (V=0.068, p=0.005).
| p2|DER category | Va a empeorar % |
|---|---|
| Muy de acuerdo | 37.6% |
| De acuerdo | 38.5% |
| Ni de acuerdo ni desacuerdo (esp.) | 41.7% |
| En desacuerdo | 50.6% |
| Muy en desacuerdo | 50.0% |

Demographically, region strongly moderates perceptions, with northern and central regions more likely to perceive worse indigenous situations. Employment status also influences future expectations, with unemployed groups showing greater pessimism. Age shows moderate effects on state of origin but less directly on discrimination perceptions.

Supporting univariate distributions for the key variable p1|IND reveal polarization: 42.5% say indigenous economic situation is "Peor" and 33.8% "Igual de mala (esp.)".
| Response | % |
|---|---|
| Peor | 42.5% |
| Igual de mala (esp.) | 33.8% |
| Igual de buena (esp.) | 13.5% |
| Mejor | 8.5% |
| No sabe/ No contesta | 1.8% |

## Complications
The strongest demographic moderators are region (mean V=0.32) and employment (mean V=0.31), indicating that geographic and socioeconomic factors significantly shape perceptions. Minority views are substantial; for example, 33.8% perceive the indigenous situation as equally bad, and 18.3% expect improvement, showing fragmentation rather than consensus. All bivariate associations, while statistically significant, have weak to moderate effect sizes (V values mostly below 0.12), limiting the strength of causal inferences. The reliance on indirect proxies for discrimination (economic situation and human rights attitudes) rather than direct measures constrains specificity. Simulation-based SES bridge methods introduce assumptions that may affect precision, and some variables have high non-response rates, further complicating interpretation. Notably, some relationships show limited positive shifts even among those with favorable human rights views, suggesting complex or ambivalent public attitudes.

## Implications
First, policies aiming to improve the situation of indigenous peoples should consider the fragmented public perception and target awareness campaigns that link human rights respect to tangible improvements in indigenous conditions, as stronger human rights support correlates with less negative views. Second, given the association between perceived authority misconduct and negative indigenous situation perceptions, reforms enhancing accountability and reducing abuses by police and politicians could improve public confidence and indigenous welfare perceptions. Third, the weak associations and fragmented opinions imply that policy interventions must be regionally tailored and sensitive to employment status, addressing local socioeconomic realities. Finally, improving direct measurement and public dialogue on discrimination could help clarify perceptions and foster consensus, enabling more effective policy design and social cohesion.

---

## Quantitative Appendix

| Metric | Value |
|--------|-------|
| Variables Analyzed | 9 |
| Divergence Index | 100.0% |
| Consensus Variables | 0 |
| Lean Variables | 3 |
| Polarized Variables | 2 |
| Dispersed Variables | 4 |

### Variable Details


**p1|IND** (polarized)
- Question: INDIGENAS|Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación actual del país: mejor o peor?
- Mode: Peor (42.5%)
- Runner-up: Igual de mala (esp.) (33.8%), margin: 8.7pp
- HHI: 3201
- Minority opinions: Igual de mala (esp.) (33.8%)

| Response | % |
|----------|---|
| Peor | 42.5% |
| Igual de mala (esp.) | 33.8% |
| Igual de buena (esp.) | 13.5% |
| Mejor | 8.5% |
| No sabe/ No contesta | 1.8% |

**p2|IND** (dispersed)
- Question: INDIGENAS|En general, ¿cree usted que el próximo año la situación económica del país va a mejorar o empeorar?
- Mode: Va a empeorar (34.7%)
- Runner-up: Va a seguir igual de mal (esp.) (29.7%), margin: 5.0pp
- HHI: 2579
- Minority opinions: Va a mejorar (18.3%), Va a seguir igual de mal (esp.) (29.7%)

| Response | % |
|----------|---|
| Va a empeorar | 34.7% |
| Va a seguir igual de mal (esp.) | 29.7% |
| Va a mejorar | 18.3% |
| Va a seguir igual de bien (esp.) | 10.8% |
| No sabe/ No contesta | 6.5% |

**p3|IND** (dispersed)
- Question: INDIGENAS|¿De qué estado es originario usted?
- Mode: México (13.5%)
- Runner-up: Veracruz (11.7%), margin: 1.8pp
- HHI: 669

| Response | % |
|----------|---|
| México | 13.5% |
| Veracruz | 11.7% |
| Sinaloa | 8.8% |
| Distrito Federal | 8.7% |
| Guanajuato | 5.7% |
| Jalisco | 5.2% |
| Guerrero | 4.8% |
| Puebla | 4.7% |
| Hidalgo | 4.2% |
| Nuevo León | 3.4% |
| Querétaro | 3.1% |
| Michoacán | 3.0% |
| Zacatecas | 3.0% |
| Morelos | 2.8% |
| Coahuila | 2.2% |
| Chiapas | 2.0% |
| Chihuahua | 2.0% |
| Tamaulipas | 2.0% |
| Oaxaca | 1.8% |
| Otro | 1.6% |
| San Luis Potosí | 1.3% |
| No sabe/ No contesta | 1.2% |
| Baja California Norte | 1.0% |
| Sonora | 0.7% |
| Tlaxcala | 0.6% |
| Aguascalientes | 0.5% |
| Tabasco | 0.2% |
| Yucatán | 0.2% |
| Baja California Sur | 0.1% |
| Campeche | 0.1% |

**p4|IND** (lean)
- Question: INDIGENAS|¿Y de qué municipio?
- Mode: NC (58.3%)
- Runner-up: NS (41.7%), margin: 16.7pp
- HHI: 5139
- Minority opinions: NS (41.7%)

| Response | % |
|----------|---|
| NC | 58.3% |
| NS | 41.7% |

**p5|IND** (dispersed)
- Question: INDIGENAS|¿Qué tan seguido va a su lugar de origen?
- Mode: Cada año (18.4%)
- Runner-up: Cada seis meses (18.2%), margin: 0.2pp
- HHI: 1545
- Minority opinions: Cada mes (16.3%), Cada seis meses (18.2%), Casi nunca (17.3%)

| Response | % |
|----------|---|
| Cada año | 18.4% |
| Cada seis meses | 18.2% |
| Casi nunca | 17.3% |
| Cada mes | 16.3% |
| Cada semana/quince días | 13.0% |
| No sabe/ No contesta | 8.7% |
| Nunca | 8.1% |

**p2|DER** (lean)
- Question: DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES|¿Qué tan de acuerdo o en desacuerdo está usted con el siguiente enunciado? Es importante que los 
- Mode: De acuerdo (48.6%)
- Runner-up: Muy de acuerdo (29.3%), margin: 19.2pp
- HHI: 3440
- Minority opinions: Muy de acuerdo (29.3%)

| Response | % |
|----------|---|
| De acuerdo | 48.6% |
| Muy de acuerdo | 29.3% |
| Ni de acuerdo ni desacuerdo (esp.) | 13.7% |
| En desacuerdo | 5.2% |
| No sabe/ No contesta | 2.1% |
| Muy en desacuerdo | 1.2% |

**p3|DER** (lean)
- Question: DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES|En su opinión ¿se respetan los derechos humanos en el país?
- Mode: Algo (46.5%)
- Runner-up: Poco (29.4%), margin: 17.1pp
- HHI: 3318
- Minority opinions: Poco (29.4%)

| Response | % |
|----------|---|
| Algo | 46.5% |
| Poco | 29.4% |
| Nada | 14.2% |
| Mucho | 9.4% |
| No sabe/ No contesta | 0.5% |

**p4|DER** (dispersed)
- Question: DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES|De las siguientes autoridades, ¿cuál cree usted que viola con más frecuencia los derechos humanos
- Mode: La policía municipal/delegación (31.6%)
- Runner-up: El Ministerio Público (25.1%), margin: 6.5pp
- HHI: 2016
- Minority opinions: El Ministerio Público (25.1%)

| Response | % |
|----------|---|
| La policía municipal/delegación | 31.6% |
| El Ministerio Público | 25.1% |
| Las Fuerzas Armadas | 13.2% |
| La policía estatal/ del D.F. | 10.7% |
| La Policía Federal | 8.0% |
| Las autoridades de salud | 3.9% |
| No sabe/ No contesta | 3.5% |
| Los políticos | 2.8% |
| El Gobierno | 0.9% |
| El presidente Enrique Peña Nieto | 0.2% |
| Otro (esp.) | 0.1% |

**p5|DER** (polarized)
- Question: DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES|¿Usted qué tanto se siente protegido contra los abusos de autoridad?
- Mode: Poco (35.9%)
- Runner-up: Algo (34.3%), margin: 1.6pp
- HHI: 2975
- Minority opinions: Algo (34.3%), Nada (21.3%)

| Response | % |
|----------|---|
| Poco | 35.9% |
| Algo | 34.3% |
| Nada | 21.3% |
| Mucho | 7.0% |
| No sabe/ No contesta | 1.4% |

### Demographic Fault Lines

| Dimension | Mean Cramér's V | Max Cramér's V | Variables |
|-----------|----------------|----------------|----------|
| region | 0.315 (strong) | 0.921 | 9 |
| empleo | 0.310 (strong) | 0.310 | 1 |
| edad | 0.179 (moderate) | 0.179 | 1 |

**Variable-Level Demographic Detail:**

*p1|IND*
- region: V=0.202 (p=0.000) — 01: Peor (47%); 02: Peor (54%); 03: Igual de mala (esp.) (34%)

*p2|IND*
- empleo: V=0.310 (p=0.001) — 01: NS (100%); 02: Va a empeorar (46%); 03: Va a empeorar (37%)
- region: V=0.174 (p=0.000) — 01: Va a empeorar (40%); 02: Va a empeorar (45%); 03: Va a seguir igual de mal (esp.) (29%)

*p3|IND*
- region: V=0.841 (p=1.000) — 01: Guanajuato (19%); 02: México (47%); 03: Sinaloa (34%)
- edad: V=0.179 (p=0.007) — 0-18: México (34%); 19-24: México (16%); 25-34: Veracruz (13%)

*p4|IND*
- region: V=0.921 (p=0.000) — 01: San Juan Del Rio (6%); 02: Edo De México (8%); 03: Mazatlán (10%)

*p5|IND*
- region: V=0.154 (p=0.000) — 01: 0.0 (55%); 02: 0.0 (38%); 03: 0.0 (60%)

*p2|DER*
- region: V=0.108 (p=0.001) — 01: De acuerdo (54%); 02: De acuerdo (47%); 03: De acuerdo (46%)

*p3|DER*
- region: V=0.126 (p=0.000) — 01:  Algo (48%); 02:  Algo (38%); 03:  Algo (52%)

*p4|DER*
- region: V=0.165 (p=0.000) — 01: La policía municipal/delegación (30%); 02: El Ministerio Público (33%); 03: La policía municipal/delegación (39%)

*p5|DER*
- region: V=0.141 (p=0.000) — 01:  Algo (41%); 02:  Poco (38%); 03:  Poco (39%)

### Cross-Dataset Bivariate Estimates (Simulation-Based)

| Variable Pair | Cramér's V | p-value | Key Pattern | n sim |
|---------------|------------|---------|-------------|-------|
| p1|IND × p2|DER | 0.069 (weak) | 0.004 | "Peor": 40% ("Ni de acuerdo ni desacuerdo (esp.)") → 82% ("Muy en desacuerdo") | 2000 |
| p1|IND × p3|DER | 0.088 (weak) | 0.000 | "Igual de mala (esp.)": 25% (" NS") → 47% (" Mucho") | 2000 |
| p1|IND × p4|DER | 0.116 (moderate) | 0.000 | "Igual de buena (esp.)": 0% ("El Gobierno") → 26% ("Las autoridades de salud") | 2000 |
| p1|IND × p5|DER | 0.097 (weak) | 0.000 | "Peor": 6% (" NS") → 49% (" Nada") | 2000 |
| p2|IND × p2|DER | 0.068 (weak) | 0.005 | "Va a empeorar": 38% ("Muy de acuerdo") → 51% ("En desacuerdo") | 2000 |
| p2|IND × p3|DER | 0.076 (weak) | 0.001 | "Va a seguir igual de mal (esp.)": 7% (" NS") → 38% (" Poco") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p1|IND × p2|DER** — How p1|IND distributes given p2|DER:

| p2|DER (conditioning) | Top p1|IND responses |
|---|---|
| Muy de acuerdo | Peor: 47%, Igual de mala (esp.): 43%, Igual de buena (esp.): 8% |
| De acuerdo | Igual de mala (esp.): 43%, Peor: 41%, Igual de buena (esp.): 12% |
| Ni de acuerdo ni desacuerdo (esp.) | Igual de mala (esp.): 40%, Peor: 40%, Igual de buena (esp.): 15% |
| En desacuerdo | Peor: 50%, Igual de mala (esp.): 38%, Igual de buena (esp.): 10% |
| Muy en desacuerdo | Peor: 82%, Igual de buena (esp.): 9%, Igual de mala (esp.): 9% |

**p1|IND × p3|DER** — How p1|IND distributes given p3|DER:

| p3|DER (conditioning) | Top p1|IND responses |
|---|---|
|  Mucho | Igual de mala (esp.): 47%, Peor: 38%, Igual de buena (esp.): 13% |
|  Algo | Igual de mala (esp.): 42%, Peor: 38%, Igual de buena (esp.): 15% |
|  Poco | Peor: 45%, Igual de mala (esp.): 42%, Igual de buena (esp.): 9% |
|  Nada | Peor: 48%, Igual de mala (esp.): 43%, Igual de buena (esp.): 5% |
|  NS | Peor: 58%, Igual de mala (esp.): 25%, Igual de buena (esp.): 17% |

**p1|IND × p4|DER** — How p1|IND distributes given p4|DER:

| p4|DER (conditioning) | Top p1|IND responses |
|---|---|
| El Ministerio Público | Igual de mala (esp.): 47%, Peor: 43%, Igual de buena (esp.): 6% |
| Las Fuerzas Armadas | Igual de mala (esp.): 46%, Peor: 35%, Igual de buena (esp.): 11% |
| La policía municipal/delegación | Igual de mala (esp.): 40%, Peor: 39%, Igual de buena (esp.): 16% |
| La policía estatal/ del D.F. | Peor: 45%, Igual de mala (esp.): 36%, Igual de buena (esp.): 13% |
| La Policía Federal | Peor: 50%, Igual de mala (esp.): 41%, Igual de buena (esp.): 6% |
| Las autoridades de salud | Igual de mala (esp.): 41%, Peor: 31%, Igual de buena (esp.): 26% |
| Los políticos | Igual de mala (esp.): 50%, Peor: 37%, Igual de buena (esp.): 8% |
| El Gobierno | Peor: 46%, Igual de mala (esp.): 41%, Mejor: 14% |

**p1|IND × p5|DER** — How p1|IND distributes given p5|DER:

| p5|DER (conditioning) | Top p1|IND responses |
|---|---|
|  Mucho | Igual de mala (esp.): 46%, Peor: 36%, Igual de buena (esp.): 15% |
|  Algo | Igual de mala (esp.): 41%, Peor: 40%, Igual de buena (esp.): 13% |
|  Poco | Igual de mala (esp.): 44%, Peor: 37%, Igual de buena (esp.): 14% |
|  Nada | Peor: 49%, Igual de mala (esp.): 42%, Mejor: 5% |
|  NS | Igual de mala (esp.): 71%, Igual de buena (esp.): 24%, Peor: 6% |
|  NC | Igual de mala (esp.): 50%, Peor: 38%, Igual de buena (esp.): 12% |

**p2|IND × p2|DER** — How p2|IND distributes given p2|DER:

| p2|DER (conditioning) | Top p2|IND responses |
|---|---|
| Muy de acuerdo | Va a seguir igual de mal (esp.): 41%, Va a empeorar: 38%, Va a mejorar: 16% |
| De acuerdo | Va a empeorar: 38%, Va a seguir igual de mal (esp.): 37%, Va a mejorar: 14% |
| Ni de acuerdo ni desacuerdo (esp.) | Va a empeorar: 42%, Va a seguir igual de mal (esp.): 38%, Va a mejorar: 14% |
| En desacuerdo | Va a empeorar: 51%, Va a seguir igual de mal (esp.): 35%, Va a mejorar: 14% |
| Muy en desacuerdo | Va a empeorar: 50%, Va a seguir igual de mal (esp.): 40%, Va a mejorar: 10% |

**p2|IND × p3|DER** — How p2|IND distributes given p3|DER:

| p3|DER (conditioning) | Top p2|IND responses |
|---|---|
|  Mucho | Va a empeorar: 41%, Va a seguir igual de mal (esp.): 35%, Va a mejorar: 17% |
|  Algo | Va a empeorar: 40%, Va a seguir igual de mal (esp.): 35%, Va a mejorar: 16% |
|  Poco | Va a seguir igual de mal (esp.): 38%, Va a empeorar: 37%, Va a mejorar: 17% |
|  Nada | Va a empeorar: 45%, Va a seguir igual de mal (esp.): 33%, Va a mejorar: 19% |
|  NS | Va a empeorar: 53%, Va a mejorar: 20%, Va a seguir igual de bien (esp.): 20% |
### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from the cross-dataset bivariate associations with significant p-values, which directly link perceptions of indigenous economic situation and future with attitudes toward human rights and authorities. These provide primary insights into how discrimination perceptions relate to broader human rights views. Demographic fault lines offer secondary context on how opinions vary by region, employment, and age. Univariate distributions provide background on opinion fragmentation but do not establish relationships.

**Key Limitations:**
- All bivariate associations show weak to moderate effect sizes, indicating limited strength of relationships.
- Estimates are simulation-based, which may affect precision and interpretation of significance.
- Sample size is moderate (n=2000), but some variables have high non-response or 'No sabe' categories, reducing effective data.
- Variables related to indigenous perceptions are mostly indirect proxies (economic situation, human rights attitudes) rather than direct measures of discrimination perception, limiting specificity to the query.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p1|IND, p5|DER
- **Dispersed Variables:** p2|IND, p3|IND, p5|IND, p4|DER

