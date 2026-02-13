# Q5 Issue Analysis: Survey Code Error

**Issue:** Question 5 (political culture/democracy) initially failed in the NEW architecture.

**Root Cause:** Incorrect survey code used in test questions.

## The Problem

**Test Question:** "¿Qué opinan los mexicanos sobre la democracia y las instituciones políticas?"
*("What do Mexicans think about democracy and political institutions?")*

**Variables Used (INCORRECT):** `['p1|CUP', 'p2|CUP', 'p3|CUP', 'p5|CUP']`

**Error:**
```
Warning: Variable p1|CUP not found in df_tables
Warning: Variable p2|CUP not found in df_tables
Warning: Variable p3|CUP not found in df_tables
Warning: Variable p5|CUP not found in df_tables
```

## The Solution

**Correct Survey Code:** `CUL` (not `CUP`)

**Survey:** CULTURA_POLITICA
**Code:** CUL
**Variables in df_tables:** 235

**Variables Used (CORRECT):** `['p1|CUL', 'p2|CUL', 'p3|CUL', 'p5|CUL']`

## Survey Code Reference

Here are all available survey codes:

| Code | Survey Name |
|------|-------------|
| IDE | IDENTIDAD_Y_VALORES |
| MED | MEDIO_AMBIENTE |
| POB | POBREZA |
| **CUL** | **CULTURA_POLITICA** ✅ |
| REL | RELIGION_SECULARIZACION_Y_LAICIDAD |
| SEG | SEGURIDAD_PUBLICA |
| SAL | SALUD |
| IND | INDIGENAS |
| SOC | SOCIEDAD_DE_LA_INFORMACION |
| ENV | ENVEJECIMIENTO |
| DER | DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES |
| COR | CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD |
| CON | CULTURA_CONSTITUCIONAL |
| GEN | GENERO |
| ECO | ECONOMIA_Y_EMPLEO |
| FAM | FAMILIA |
| EDU | EDUCACION |

## Re-test Results (With Correct Code)

**Variables:** `p1|CUL, p2|CUL, p3|CUL, p5|CUL`

### OLD Architecture (detailed_report)
- ✅ Success
- Latency: 10,247 ms (~10.2 seconds)
- Generated 2 expert summaries

### NEW Architecture (analytical_essay)
- ✅ Success
- Latency: 13,184 ms (~13.2 seconds)
- Variables analyzed: 4
- Divergence index: 100% (all variables show non-consensus)
- Shape summary: All variables classified as polarized or dispersed

### Sample Questions from CUL Survey

**p1|CUL:** "Comparada con la situación económica que tenía el país hace un año, ¿cómo diría usted que es la situación actual?"
*("Compared to the economic situation the country had a year ago, how would you say the current situation is?")*

**p2|CUL:** "¿Y cree usted que en el próximo año…?"
*("And do you believe that in the next year...")*

**p3|CUL:** "De las siguientes palabras, ¿con cuál está usted más de acuerdo para describir la situación política actual?"
*("Of the following words, which do you most agree with to describe the current political situation?")*

**p5|CUL:** "¿Qué tan orgulloso se siente de ser mexicano?"
*("How proud do you feel to be Mexican?")*

## Lesson Learned

When creating test questions:
1. Always verify survey codes against `enc_nom_dict`
2. Confirm variables exist in `df_tables` before running tests
3. Common error: Confusing similar-sounding codes (CUP vs CUL)

## Recommendation

The comparison script should be updated to use **CUL** for question 5, and the comparison should be re-run to show accurate results for political culture/democracy questions.
