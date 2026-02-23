# q7_democracy_corruption

**Query (ES):** ¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?
**Query (EN):** What do Mexicans think about the relationship between democracy and corruption?
**Variables:** p1|CUL, p2|CUL, p3|CUL, p4|CUL, p5|CUL, p2|COR, p3|COR, p5|COR, p8|COR
**Status:** ✅ success
**Time:** 41929ms | **Cross-dataset pairs:** 6

---

# Analytical Essay

**Query:** ¿Qué piensan los mexicanos sobre la relación entre democracia y corrupción?

## Summary
Mexicans overwhelmingly perceive corruption as increasing compared to the past (77.0%) and expect it to remain high or worsen in the future (67.7%), but the relationship between these corruption perceptions and expectations about the political future, which reflects views on democracy, is weak and only occasionally statistically significant. Among four tested bivariate associations linking corruption perceptions to political outlooks, only two show weak but significant correlations, indicating limited confidence in a strong connection between democracy and corruption views in the data.

## Data Landscape
The analysis covers eight variables from surveys on political culture and corruption perceptions, with three showing strong consensus, one polarized, one dispersed, and three leaning toward a dominant view. The divergence index of 62% indicates substantial variation in public opinion, reflecting fragmented and diverse attitudes toward democracy and corruption among Mexicans.

## Evidence
The relationship between perceived corruption levels compared to childhood (p2|COR) and expectations about the political future (p2|CUL) is weak and not statistically significant (V=0.062, p=0.081). The proportion expecting the political situation to "Va a empeorar" remains similar across corruption perceptions, ranging narrowly from 40.3% to 52.0%:
| p2|COR category | Va a empeorar % |
|---|---|
| Mayor | 40.8% |
| Menor | 40.3% |
| Igual (esp.) | 40.8% |
| NS | 52.0% |

Expectations about future corruption (p3|COR) show a weak but statistically significant association with political future outlooks (p2|CUL) (V=0.085, p=0.000). Here, the share expecting the political situation to "Va a empeorar" ranges from 30.2% when corruption is expected to be "NS" to 38.7% when expected to be "Mayor":
| p3|COR category | Va a empeorar % |
|---|---|
| Mayor | 38.7% |
| Menor | 37.2% |
| Igual (esp.) | 37.0% |
| NS | 30.2% |

Perceptions of where corruption occurs (p5|COR) do not significantly relate to political future expectations (p2|CUL) (V=0.073, p=0.082), despite variation in the "Va a seguir igual de mal" response from 11.1% to 37.5%:
| p5|COR category | Va a seguir igual de mal % |
|---|---|
| En la escuela | 22.5% |
| En la colonia | 27.7% |
| En el trabajo | 25.0% |
| En el gobierno | 29.0% |
| En el sector privado | 26.1% |
| En la iglesia | 37.5% |
| En la familia | 26.0% |
| En los partidos políticos | 25.3% |
| Otro (esp.) | 11.1% |

Current political sentiment (p3|CUL) and perceived corruption levels (p2|COR) show no significant association (V=0.062, p=0.201), with the "Prometedora" outlook ranging narrowly from 0.0% to 9.6% across corruption categories:
| p2|COR category | Prometedora % |
|---|---|
| Mayor | 0.0% |
| Menor | 0.0% |
| Igual (esp.) | 9.6% |
| NS | 0.0% |

However, current political sentiment (p3|CUL) and future corruption expectations (p3|COR) have a weak but significant relationship (V=0.076, p=0.010). The "Peor que antes" response varies from 3.8% when corruption is expected to be "Menor" to 12.8% when respondents are uncertain (NS):
| p3|COR category | Peor que antes % |
|---|---|
| Mayor | 7.5% |
| Menor | 3.8% |
| Igual (esp.) | 9.6% |
| NS | 12.8% |

Demographically, employment status shows the strongest moderation effect on political sentiment (p3|CUL), with some regions and age groups differing moderately in their views about political and corruption issues. For example, younger Mexicans (0-18) are 15 points less likely than those aged 25-34 to say corruption is "Mayor" compared to childhood (70% vs. 77%). Women and men show minor differences in self-assessed honesty, but this variable is invalid due to 100% non-response.

**p2|CUL** — Expectation about the political situation next year:
| Response | % |
|---|---|
| Va a empeorar | 37.2% |
| Va a seguir igual de mal | 29.4% |
| Va a mejorar | 17.8% |
| Va a seguir igual de bien | 11.2% |
| No sabe/ No contesta | 3.9% |
| Otra | 0.6% |

**p3|CUL** — Description of current political situation:
| Response | % |
|---|---|
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

**p2|COR** — Corruption compared to childhood:
| Response | % |
|---|---|
| Mayor | 77.0% |
| Igual (esp.) | 14.7% |
| Menor | 6.9% |
| No sabe/ No contesta | 1.4% |

**p3|COR** — Corruption expected in 5 years:
| Response | % |
|---|---|
| Mayor | 67.7% |
| Igual (esp.) | 19.3% |
| Menor | 8.2% |
| No sabe/ No contesta | 4.8% |

**p5|COR** — Where first acts of corruption occur:
| Response | % |
|---|---|
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

## Complications
Employment status is the strongest demographic moderator, with a Cramér's V of up to 0.32, indicating moderate differences in how groups perceive political and corruption issues. For example, employment groups differ by up to 23 points in views of the political situation as "Preocupante" or "Peligrosa." Regional differences are moderate (V≈0.11-0.14), with some regions more pessimistic about corruption and political futures. Age also moderates perceptions moderately, with younger respondents slightly less likely to see corruption as "Mayor" than older groups. Minority opinions, such as the 17.8% expecting political improvement and 14.7% perceiving corruption as unchanged, challenge the dominant pessimism but do not overturn it. The simulation-based SES-bridge method yields mostly weak associations (V < 0.1), limiting causal inference. The variable for self-assessed honesty (p8|COR) is unusable due to 100% non-response, removing a potentially relevant dimension. Several expected relationships, such as between perceived corruption levels and political future outlook, are statistically insignificant, indicating complexity or independence between democracy and corruption perceptions in this dataset.

## Implications
First, the weak but significant link between expectations of corruption worsening and pessimistic political outlooks suggests that anti-corruption efforts could have a modest positive effect on democratic confidence, but policymakers should not overestimate the impact of corruption perceptions alone on democratic attitudes. Second, the strong consensus that corruption has increased and will remain high indicates a deep-rooted societal concern that may undermine democratic legitimacy; thus, comprehensive institutional reforms and transparency initiatives are needed to address this systemic distrust. Additionally, given the demographic variation, tailored communication and engagement strategies might be necessary to reach different employment and regional groups effectively. Finally, the absence of strong associations between current corruption perceptions and political outlooks implies that other factors beyond corruption may shape democratic attitudes, warranting broader political and social analyses.

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
| p2|CUL × p2|COR | 0.062 (weak) | 0.081 | " Va a empeorar": 40% ("Menor") → 52% ("NS") | 2000 |
| p2|CUL × p3|COR | 0.085 (weak) | 0.000 | " Va a empeorar": 30% ("NS") → 39% ("Mayor") | 2000 |
| p2|CUL × p5|COR | 0.073 (weak) | 0.082 | " Va a seguir igual de mal (esp)": 11% ("Otro (esp.)") → 38% ("En la iglesia") | 2000 |
| p2|CUL × p8|COR | 0.064 (weak) | 0.420 | " Va a empeorar": 24% ("2.0") → 55% ("6.0") | 2000 |
| p3|CUL × p2|COR | 0.062 (weak) | 0.201 | " Prometedora": 0% ("Menor") → 10% ("Igual (esp.)") | 2000 |
| p3|CUL × p3|COR | 0.076 (weak) | 0.010 | " Peor que antes   (esp)": 4% ("Menor") → 13% ("NS") | 2000 |

*Estimates derived from SES-bridge regression simulation.*


**p2|CUL × p2|COR** — How p2|CUL distributes given p2|COR:

| p2|COR (conditioning) | Top p2|CUL responses |
|---|---|
| Mayor |  Va a empeorar: 41%,  Va a seguir igual de mal (esp): 29%,  Va a mejorar: 16% |
| Menor |  Va a empeorar: 40%,  Va a seguir igual de mal (esp): 33%,  Va a mejorar: 17% |
| Igual (esp.) |  Va a empeorar: 41%,  Va a seguir igual de mal (esp): 28%,  Va a seguir igual de bien (esp): 16% |
| NS |  Va a empeorar: 52%,  Va a seguir igual de mal (esp): 24%,  Va a mejorar: 12% |

**p2|CUL × p3|COR** — How p2|CUL distributes given p3|COR:

| p3|COR (conditioning) | Top p2|CUL responses |
|---|---|
| Mayor |  Va a empeorar: 39%,  Va a seguir igual de mal (esp): 30%,  Va a mejorar: 18% |
| Menor |  Va a empeorar: 37%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 18% |
| Igual (esp.) |  Va a empeorar: 37%,  Va a seguir igual de mal (esp): 33%,  Va a mejorar: 15% |
| NS |  Va a seguir igual de mal (esp): 34%,  Va a empeorar: 30%,  Va a mejorar: 15% |

**p2|CUL × p5|COR** — How p2|CUL distributes given p5|COR:

| p5|COR (conditioning) | Top p2|CUL responses |
|---|---|
| En la escuela |  Va a empeorar: 42%,  Va a seguir igual de mal (esp): 22%,  Va a mejorar: 18% |
| En la colonia |  Va a empeorar: 57%,  Va a seguir igual de mal (esp): 28%,  Va a mejorar: 12% |
| En el trabajo |  Va a empeorar: 36%,  Va a seguir igual de mal (esp): 25%,  Va a seguir igual de bien (esp): 18% |
| En el gobierno |  Va a empeorar: 40%,  Va a seguir igual de mal (esp): 29%,  Va a mejorar: 17% |
| En el sector privado |  Va a empeorar: 42%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 20% |
| En la iglesia |  Va a seguir igual de mal (esp): 38%,  Va a empeorar: 38%,  Va a mejorar: 17% |
| En la familia |  Va a empeorar: 36%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 20% |
| En los partidos políticos |  Va a empeorar: 45%,  Va a seguir igual de mal (esp): 25%,  Va a mejorar: 13% |

**p2|CUL × p8|COR** — How p2|CUL distributes given p8|COR:

| p8|COR (conditioning) | Top p2|CUL responses |
|---|---|
| 0.0 |  Va a empeorar: 50%,  Va a seguir igual de mal (esp): 30%,  Va a seguir igual de bien (esp): 20% |
| 2.0 |  Va a seguir igual de mal (esp): 35%,  Va a empeorar: 24%,  Va a seguir igual de bien (esp): 18% |
| 3.0 |  Va a empeorar: 48%,  Va a seguir igual de mal (esp): 30%,  Va a seguir igual de bien (esp): 13% |
| 5.0 |  Va a empeorar: 54%,  Va a seguir igual de mal (esp): 25%,  Va a mejorar: 17% |
| 6.0 |  Va a empeorar: 55%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 13% |
| 7.0 |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 28%,  Va a mejorar: 18% |
| 8.0 |  Va a empeorar: 38%,  Va a seguir igual de mal (esp): 27%,  Va a mejorar: 18% |
| 9.0 |  Va a empeorar: 45%,  Va a seguir igual de mal (esp): 26%,  Va a mejorar: 17% |

**p3|CUL × p2|COR** — How p3|CUL distributes given p2|COR:

| p2|COR (conditioning) | Top p3|CUL responses |
|---|---|
| Mayor |  Preocupante: 49%,  Peligrosa: 22%,  Tranquila: 9% |
| Menor |  Preocupante: 52%,  Peligrosa: 28%,  Tranquila: 8% |
| Igual (esp.) |  Preocupante: 43%,  Peligrosa: 23%,  Tranquila: 10% |
| NS |  Preocupante: 46%,  Peligrosa: 25%,  Tranquila: 12% |

**p3|CUL × p3|COR** — How p3|CUL distributes given p3|COR:

| p3|COR (conditioning) | Top p3|CUL responses |
|---|---|
| Mayor |  Preocupante: 49%,  Peligrosa: 22%,  Tranquila: 9% |
| Menor |  Preocupante: 41%,  Peligrosa: 24%,  Prometedora: 12% |
| Igual (esp.) |  Preocupante: 44%,  Peligrosa: 23%,  Peor que antes   (esp): 10% |
| NS |  Preocupante: 45%,  Peligrosa: 22%,  Peor que antes   (esp): 13% |
### Reasoning Outline

**Evidence Hierarchy:** The strongest evidence comes from cross-dataset bivariate associations with statistically significant p-values, notably between p2|CUL and p3|COR, and between p3|CUL and p3|COR, which show weak but significant relationships linking corruption expectations to political outlooks. Demographic fault lines provide secondary evidence about variation in opinions across groups but do not establish direct relationships. Univariate distributions offer contextual background on general attitudes but do not demonstrate relationships relevant to the query.

**Key Limitations:**
- Most bivariate relationships show weak effect sizes (low V values), limiting strength of conclusions.
- Several cross-survey pairs lack significant associations, reducing clarity on how democracy and corruption perceptions interrelate.
- One key variable (p8|COR) is unusable due to 100% non-response, limiting insights on self-perception of honesty.
- The analysis relies on simulation-based estimates and a limited number of cross-survey variable pairs, constraining the depth of relational evidence.

### Analysis Metadata
- **Analysis Type:** Analytical Essay (Quantitative + Qualitative)
- **Polarized Variables:** p4|CUL
- **Dispersed Variables:** p2|CUL

