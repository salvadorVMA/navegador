# SES Bridge: Uses, Limitations, and Interpretive Boundaries

*Generated 2026-02-23 — worktree-knowledge-graph branch*

---

## 1. What the Bridge Does

The SES bridge estimates bivariate associations between variables from *different surveys* that share no common respondents. The approach has three steps:

1. **Fit each variable to a shared set of SES predictors.** For every candidate variable in survey A and survey B, an `OrderedModel` (ordinal target) or `MNLogit` (nominal target) is fitted using the five demographic predictors: `sexo`, `edad`, `region`, `empleo`, `escol`. The models capture how much each response category is predicted by demographic profile.

2. **Draw a reference SES population.** A synthetic population of 2,000 respondents is sampled from the pooled marginal distributions of the two surveys (weighted by `Pondi2`). This population represents a plausible joint demographic space.

3. **Simulate responses and measure association.** For each synthetic respondent, responses to both variables are independently predicted by their respective SES models. Cramér's V is computed on the resulting 2×N contingency table. A chi-square test produces a p-value.

The result is an estimate of "how much of the cross-domain association can be explained by the demographic skeleton shared by both surveys."

---

## 2. Results Summary

| Statistic | Value |
|-----------|-------|
| Domain pairs tested | 276 / 276 |
| Estimates produced | 2,484 (9 per pair) |
| Significant (p < 0.05) | ~93% |
| Mean Cramér's V | **0.097** |
| Median Cramér's V | 0.096 |
| Standard deviation | 0.007 |
| Min V (DEP×SAL) | **0.081** |
| Max V (CIE×POB) | **0.116** |
| Total range | 0.036 |
| Interquartile range | **0.010** |

**Domain-level SES loading** (mean V across all 23 pairings per domain):

| Tier | Domains | Mean V |
|------|---------|--------|
| High | IND, POB, CIE, REL, SOC, HAB | 0.100–0.103 |
| Mid | CUL, EDU, DER, ECO, GLO, FED, IDE, MIG, ENV, SEG | 0.096–0.100 |
| Low | JUS, FAM, NIN, GEN, SAL, COR, MED, DEP | 0.088–0.095 |

---

## 3. The Compression Problem

### 3.1 What compression looks like

The V range is 0.081–0.116 — a span of 0.036. In a direct cross-tabulation of real co-respondent data, you would expect pairs of genuinely unrelated variables to produce V ≈ 0 and genuinely strongly related variables to produce V ≈ 0.3–0.5. The bridge produces *none of this variance*. The interquartile range of 0.010 means 50% of all domain pairs are clustered within a band one hundredth of a unit wide. This is extreme compression.

The within-domain variance (how much one domain's pairings vary from its mean) is 0.004–0.008 — only slightly less than the between-domain variance (0.007). In other words, you cannot reliably distinguish domains from one another based on V alone.

### 3.2 Why compression is structurally guaranteed

The compression is not a bug or a data quality problem — it is mathematically inevitable given the design:

**The bridge can only recover shared SES variance.** Both variables are predicted by the *same* five predictors. The simulated Cramér's V captures:

```
V_bridge ≈ f( R²_SES(A) × R²_SES(B) )
```

Where R²_SES(A) is how much variance in variable A is explained by the SES predictors. If each variable has moderate SES prediction (R² ≈ 0.05–0.15, typical for attitudinal survey items), the resulting simulated V is necessarily small — you cannot recover from the product of two small numbers.

**The floor is structural.** Any two categorical survey variables that have *any* demographic variation will produce V > 0 from the bridge, because the shared SES skeleton introduces correlation even for conceptually unrelated constructs. DEP×SAL V=0.081 is not "low association" — it is the structural floor produced by the model architecture itself. There is no null case.

**The ceiling is constrained by SES R².** The bridge cannot produce V higher than what the SES predictors can jointly account for in both variables. High V from the bridge (e.g., CIE×POB at 0.116) means both variables are relatively more SES-saturated — more demographic variation — not that they are more conceptually related.

**Five predictors are insufficient to span the conceptual space.** Five demographic variables define a roughly 8–10-dimensional feature space (after one-hot encoding). Survey attitudes, beliefs, and behaviours operate in a much higher-dimensional latent space. Most of the variance that distinguishes domains from each other lives in dimensions the bridge cannot see.

---

## 4. The Significance Problem

93% of 2,484 estimates are p < 0.05. This near-universal significance reflects:

- **Large simulation size** (n_sim=2,000): with 2,000 synthetic respondents, even V=0.08 has statistical power to reject the null of V=0.
- **The floor effect**: because the bridge structurally cannot produce V=0, the chi-square test is effectively testing "does this domain pair have a detectable demographic skeleton?" — not "are these domains related?" The answer is almost always yes.

Significance here is a property of the method, not of the data. The 7% non-significant pairs are likely cases where one or both variables had very weak SES gradients and the model converged poorly, not cases where the domains are genuinely independent.

---

## 5. What the Bridge Is Useful For

Despite the limitations above, the bridge has genuine, bounded utility:

### 5.1 Ranking SES saturation across domains

The domain-level ranking (IND, POB, CIE at the top; DEP, MED, COR at the bottom) *is* interpretable as a measure of **how much demographic stratification characterises each domain**. Domains with high mean V have variables that vary substantially by age, education, sex, employment, and region. Domains with low mean V have variables that are more demographically uniform.

This is a meaningful sociological finding:
- Indigenous issues (IND), poverty (POB), and science/technology (CIE) are the most demographically stratified — responses vary strongly by who you are.
- Corruption (COR), media (MED), and sports/recreation (DEP) are the most demographically uniform — respondents tend to agree regardless of demographic profile.

### 5.2 Relative comparison within the bridge's scale

Even if absolute V values are not interpretable as "strength of association," *relative* comparisons within the same bridge run are valid: CIE×POB (V=0.116) genuinely has more shared SES variance than DEP×SAL (V=0.081). This can be used to:

- Flag domain pairs where SES confounding is particularly strong (if bridging to an essay or analytical context)
- Identify which pairings are most likely to produce spurious associations in downstream analyses that don't control for SES

### 5.3 KG ontology validation (with caveats)

The 5 CONFIRMED and 0 CONTRADICTED KG relationships suggest that the ontology's cross-domain edges are at least not empirically refuted by demographic data. This is a weak positive signal — it confirms the KG edges don't span demographically orthogonal domains.

### 5.4 Practical instrument design

When designing a survey or analysis that combines variables from two different surveys, the bridge V tells you: "if you don't control for these five demographics, expect approximately V≈0.10 of spurious correlation between any measure from Survey A and any measure from Survey B." This is a useful baseline correction factor.

---

## 6. What the Bridge Is Not Useful For

### 6.1 Measuring substantive domain associations

The bridge **cannot tell you** whether Religion and Indigenous Issues are conceptually related. It only tells you they both vary with age, education, and region. The fact that IND×REL is among the top pairs (V=0.111) reflects shared demographics, not shared conceptual territory.

The 271 "DATA ONLY" pairs are not evidence that those 271 domain pairs are related — they are simply pairs for which the KG made no cross-domain claim and the bridge produced its standard non-zero estimate.

### 6.2 Distinguishing real associations from SES confounding

The bridge conflates two entirely different phenomena:
- **Genuine cross-domain association**: Domain A's content directly influences or co-occurs with Domain B's content
- **SES confounding**: Both domains correlate with the same demographics

A richer dataset (panel data, co-embedded surveys) would be needed to separate these. The bridge cannot do it.

### 6.3 Validating the knowledge graph

The KG was built from semantic/conceptual analysis of question content. The bridge measures demographic structure. These are orthogonal evaluation criteria. A high bridge V does not validate a KG edge; a low bridge V does not invalidate one.

### 6.4 Producing effect-size estimates for research

V=0.097 is not the expected Cramér's V between a variable from, say, the SALUD and POBREZA surveys. It is a simulation artefact of the bridge design. Using it as an effect size estimate in substantive research would be misleading.

---

## 7. When the Bridge Approach Would Work Better

The bridge's limitations are inherent to the method, but could be mitigated by:

| Change | Effect |
|--------|--------|
| **More bridge variables** (10–15 SES+contextual predictors) | Wider V range, but compression remains unless R² increases substantially |
| **Higher-R² bridge** (use rich composite SES indices) | Ceiling rises, but so does the floor |
| **Partial-R² bridge** (subtract common SES component before V) | Could identify *residual* domain associations beyond SES — conceptually more valid |
| **Direct linkage** (RDD merging, overlapping respondent panels) | Eliminates the simulation entirely; produces real joint V |
| **Structural equation modelling** across surveys | Properly accounts for measurement error and latent constructs |

---

## 8. Summary Assessment

| Question | Answer |
|----------|--------|
| Is the bridge valid? | Yes — as a measure of shared SES variance |
| Does it identify conceptual domain relationships? | No |
| Is V=0.097 a meaningful effect size? | No — it is a method artefact |
| Are the 93% significant results meaningful? | No — significance reflects simulation power, not true association |
| Is the domain ranking (IND>POB>CIE>…>DEP) meaningful? | Yes — as a measure of SES saturation |
| Should the KG be updated based on bridge results? | Only to annotate edges with "SES co-variation" notes, not to add/remove conceptual links |
| Is the bridge worth keeping in the pipeline? | Yes, with scope limited to SES saturation analysis and confound-flagging |

**Bottom line**: The SES bridge is a narrow-purpose tool. It reliably measures how demographically stratified each domain is, and flags domain pairs where SES confounding will be strong. It does not — and structurally cannot — identify whether two domains are conceptually related. Given the compressed V range (0.081–0.116) and uniform significance (93%), it should not be presented to users as evidence of domain associations. Its most defensible use is as a confounder diagnostic and a domain-level demographic saturation score.
