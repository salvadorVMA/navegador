# SES Bridge: Uses, Limitations, and Interpretive Boundaries

*Updated 2026-02-24 — worktree-knowledge-graph branch*
*Original: 2026-02-23 (5-predictor baseline). Updated with 7-predictor extended bridge results.*

---

## 1. What the Bridge Does

The SES bridge estimates bivariate associations between variables from *different surveys* that share no common respondents. The approach has three steps:

1. **Fit each variable to a shared set of SES predictors.** For every candidate variable in survey A and survey B, an `OrderedModel` (ordinal target) or `MNLogit` (nominal target) is fitted using demographic predictors. The models capture how much each response category is predicted by demographic profile.

2. **Draw a reference SES population.** A synthetic population of 2,000 respondents is sampled from the pooled marginal distributions of the two surveys (weighted by `Pondi2`). This population represents a plausible joint demographic space.

3. **Simulate responses and measure association.** For each synthetic respondent, responses to both variables are independently predicted by their respective SES models. Cramér's V is computed on the resulting 2×N contingency table. A chi-square test produces a p-value.

The result is an estimate of "how much of the cross-domain association can be explained by the demographic skeleton shared by both surveys."

---

## 2. Predictor Variable Audit (2026-02-24)

A full audit of the 26 surveys in `los_mex_dict.json` identified the following variables:

| Variable | Coverage | Decision |
|----------|----------|----------|
| `sexo` | 26/26 | Baseline predictor |
| `edad` | 26/26 | Baseline predictor |
| `region` | 26/26 | Baseline predictor |
| `empleo` | 26/26 | Baseline predictor |
| `escol` | 26/26 | Baseline predictor |
| `Tam_loc` (locality size / urban-rural) | 24/26 | **Added** — ordinal 1-4 |
| `est_civil` (marital status) | 26/26 | **Added** — nominal one-hot |
| `religion` | 2/26 | Excluded — not universal |
| `edo` (state, INEGI codes 1-32) | 26/26 | Excluded — no value labels, convergence risk |
| `ing_ind`, `ing_fam` (income) | 26/26 | Candidate for future extension |
| `Estrato` (SES stratum) | 24/26 | Candidate for future extension |

`Tam_loc` is absent from JUEGOS_DE_AZAR and CULTURA_CONSTITUCIONAL (older survey format); the encoder degrades gracefully for those surveys.

---

## 3. Results Comparison: Baseline (5 vars) vs Extended (7 vars)

| Statistic | Baseline (5 vars) | Extended (7 vars) | Change |
|-----------|-------------------|-------------------|--------|
| Domain pairs tested | 276 / 276 | 276 / 276 | — |
| Estimates produced | 2,484 | 2,484 | — |
| Significant (p < 0.05) | ~93% | **98.5%** | +5.5pp |
| Mean Cramér's V | 0.097 | **0.106** | +0.009 |
| Median Cramér's V | 0.096 | **0.106** | +0.010 |
| Standard deviation | 0.007 | **0.009** | +0.002 |
| Min V | 0.081 | **0.085** | +0.004 |
| Max V | 0.116 | **0.140** | +0.024 |
| **Range** | **0.036** | **0.055** | **+54%** |
| **IQR** | **0.010** | **0.011** | +10% |
| Runtime | — | 18.1 min | — |

**Key finding:** The extended bridge widens the V range by 54% (0.036 → 0.055) and raises the ceiling substantially (0.116 → 0.140), with the floor moving only marginally (0.081 → 0.085). The additional predictors improve discriminability, though the IQR improvement is modest (+10%), indicating the distribution remains somewhat compressed in the middle.

---

## 4. Domain-Level SES Saturation Rankings

**Extended bridge** (mean V across all 23 pairings per domain):

| Tier | Domains | Mean V |
|------|---------|--------|
| High | DER, SOC, CUL, IND, POB, JUS | 0.110–0.118 |
| Mid-high | REL, CIE, ECO, MIG, EDU, GLO | 0.108–0.110 |
| Mid | IDE, GEN, SEG, HAB, FED | 0.104–0.107 |
| Mid-low | NIN, SAL, ENV | 0.101–0.103 |
| Low | MED, COR, FAM, DEP | 0.095–0.099 |

**Comparison to baseline** — what changed:
- **DER** (Derechos Humanos/Discriminación) emerges as the most demographically saturated domain in the extended bridge, surpassing IND and POB from the baseline. Human rights and discrimination opinions vary strongly by marital status and locality size.
- **SOC** (Sociedad de la Información) and **CUL** (Cultura) rise significantly — both are sensitive to urban/rural locality.
- **FAM** (Familia) drops to near-bottom: family attitudes appear more demographically uniform once locality size is controlled.
- **DEP** (Deportes/Recreación) and **COR** (Corrupción) remain at the bottom — robustly confirmed as the most demographically uniform domains across both bridge versions.

**Top domain pairs (extended):**

| Pair | Mean V | Interpretation |
|------|--------|----------------|
| DER × SOC | 0.140 | Human rights + digital society: both strongly SES-stratified |
| IND × SOC | 0.139 | Indigenous issues + digital society: shared urban/rural gradient |
| CUL × DER | 0.134 | Culture + human rights: education and locality driven |
| DER × MIG | 0.132 | Human rights + migration: age/education gradient |
| DER × POB | 0.129 | Human rights + poverty: as expected |

---

## 5. The Compression Problem (Updated)

### 5.1 What compression looks like

The extended bridge V range is 0.085–0.140, a span of 0.055. This is 54% wider than the baseline (0.036) but still far below what direct co-respondent data would show (V=0 to 0.3–0.5 for real associations). The IQR of 0.011 means 50% of all domain pairs remain within a band ~1 hundredth of a unit wide.

### 5.2 Why compression persists

The structural formula remains:

```
V_bridge ≈ f( R²_SES(A) × R²_SES(B) )
```

Adding two more predictors raises R²_SES modestly for variables sensitive to urban/rural and marital status, pushing the ceiling to 0.140. But the product of two moderate R² values remains small. The compression is a mathematical property of the bridge design, not a data quality problem.

### 5.3 What the wider range tells us

The ceiling rise from 0.116 → 0.140 is driven by domain pairs where **both** variables are sensitive to the new predictors (especially `Tam_loc`). Pairs like DER×SOC and IND×SOC benefit because both digital society and indigenous/human rights attitudes vary strongly by locality size. This is a genuine finding: these domains share a strong urban/rural demographic gradient.

---

## 6. The Significance Problem (Updated)

Significance has increased from 93% → 98.5%. More predictors → tighter SES predictions → more statistical power to detect even the structural floor. This reinforces the earlier conclusion: significance here is a property of the method's power, not evidence of substantive domain associations.

---

## 7. What the Bridge Is Useful For

### 7.1 Ranking SES saturation across domains

The domain-level ranking remains the bridge's most interpretable output. Key findings confirmed across both bridge versions:
- **DER, IND, POB, CIE** are consistently the most demographically stratified
- **DEP, COR, MED** are consistently the most demographically uniform
- New finding: **SOC and CUL** are more urban/rural sensitive than the baseline revealed

### 7.2 Relative comparison and confound-flagging

The wider range (0.085–0.140 vs 0.081–0.116) gives slightly more room for relative comparison. Domain pairs near 0.140 have notably stronger shared SES loading than pairs near 0.085 — a difference that was largely invisible in the baseline.

### 7.3 KG ontology validation (unchanged caveats)

High bridge V still does not validate a KG edge; low bridge V still does not invalidate one. The bridge measures demographic structure, not conceptual structure.

---

## 8. What the Bridge Is Not Useful For

Same as baseline: the bridge cannot measure substantive domain associations, cannot distinguish genuine cross-domain association from SES confounding, and should not be used to produce research-grade effect sizes.

---

## 9. Planned Improvements

Full algorithm details: `docs/SES_BRIDGE_IMPROVEMENT_PLAN.md`

| Option | Description | Expected gain | Status |
|--------|-------------|--------------|--------|
| A | Expand predictors: +Tam_loc, +est_civil | Wider range (+54% achieved) | **Done** |
| B | Option 3: Mantel-Haenszel Residual Bridge | Measure association *beyond* SES | Planned |
| C | Option 4: Ecological Bridge (geo cells) | Real geographic correlations | Planned |
| D | Comparison sweep: all 3 methods | Triangulated domain picture | Planned |

**Option 3 (Residual bridge):** New `ResidualBridgeEstimator` in `ses_regression.py`. Stratifies synthetic SES population into K≈30 KMeans cells, computes V within each cell, aggregates via Mantel-Haenszel. Output: `cramers_v_residual` + `ses_fraction`.

**Option 4 (Ecological bridge):** New `EcologicalBridgeEstimator` in `ses_regression.py`. Aggregates survey responses at `edo` × `Tam_loc` cells (max 128), merges both surveys on geographic key, computes weighted Spearman ρ. Subject to ecological fallacy but immune to V compression.

---

## 10. Summary Assessment (Updated)

| Question | Baseline answer | Extended answer |
|----------|----------------|-----------------|
| Is the bridge valid? | Yes — as SES variance measure | Yes — same |
| Does it identify conceptual domain relationships? | No | No |
| Is V meaningful as effect size? | No — method artefact | No — same |
| Are 93%+ significant results meaningful? | No | No (98.5% confirms this) |
| Is the domain ranking meaningful? | Yes — SES saturation | Yes — now more differentiated |
| Should KG be updated based on bridge? | Annotate only | Annotate only |
| Is the bridge worth keeping? | Yes, narrow scope | Yes, slightly wider scope |
| Did adding Tam_loc + est_civil help? | N/A | Yes — range +54%, ceiling +0.024 |

**Bottom line:** The extended bridge (7 predictors) is a meaningfully better instrument than the baseline. The 54% range increase and the emergence of DER, SOC, and CUL as high-saturation domains are genuine findings not visible in the baseline. However, compression remains structural. The next priority is implementing Options 3 and 4 to provide measures that go beyond shared SES variance.
