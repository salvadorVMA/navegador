# Bridge Estimators — Methodology, Interpretation, and Diagnostics

*Last updated: 2026-03-04*

## 1. What problem are we solving?

We have two different surveys (e.g., ENCUP on culture, ENVIPE on security) that
asked different questions to different people. We want to know: **do the answers
to question A (from survey 1) relate to the answers to question B (from survey
2)?**

Since no single person answered both questions, we cannot compute a direct
cross-tabulation. Instead, we use **SES variables** (sex, age, education, region,
employment, locality size, marital status) that appear in both surveys as a
**bridge**: we model how each target variable depends on SES, then use those
models to estimate the joint distribution of (Y_a, Y_b) under the
**Conditional Independence Assumption** (CIA):

> Given SES, the answers to Y_a and Y_b are independent.

All six estimators are different approaches to building and evaluating this
bridge. They report different metrics, test different assumptions, and have
different failure modes.

---

## 2. What is being linked? Survey domains and variable pairs

### 2.1 The 24 Mexican survey domains

The "los_mex" dataset contains 24 national surveys on Mexican society, each
covering a distinct thematic domain. They were conducted by UNAM on 2015 
on different samples — so no person answered
more than one survey. The bridge estimators allow us to ask: **do people's
attitudes or behaviours across these different topics correlate through their
socioeconomic background?**

| Code | Survey (abbreviated) | Topic |
|------|----------------------|-------|
| CIE | CIENCIA_Y_TECNOLOGIA | Science, technology attitudes |
| CON | CULTURA_CONSTITUCIONAL | Constitutional culture |
| COR | CORRUPCION_Y_CULTURA_DE_LA_LEGALIDAD | Corruption perceptions |
| CUL | CULTURA_POLITICA | Political culture |
| DEP | CULTURA_LECTURA_Y_DEPORTE | Reading, sports, leisure |
| DER | DERECHOS_HUMANOS_DISCRIMINACION_Y_GRUPOS_VULNERABLES | Human rights, discrimination |
| ECO | ECONOMIA_Y_EMPLEO | Economy, employment |
| EDU | EDUCACION | Education attitudes |
| ENV | ENVEJECIMIENTO | Aging, elderly issues |
| FAM | FAMILIA | Family values, structures |
| FED | FEDERALISMO | Federalism, government trust |
| GEN | GENERO | Gender attitudes |
| GLO | GLOBALIZACION | Globalization perceptions |
| HAB | LA_CONDICION_DE_HABITABILIDAD... | Housing conditions |
| IDE | IDENTIDAD_Y_VALORES | Identity, values |
| IND | INDIGENAS | Indigenous peoples |
| JUE | JUEGOS_DE_AZAR | Gambling |
| JUS | JUSTICIA | Justice, courts |
| MED | MEDIO_AMBIENTE | Environment |
| MIG | MIGRACION | Migration |
| NIN | NINOS_ADOLESCENTES_Y_JOVENES | Children, youth |
| POB | POBREZA | Poverty perceptions |
| REL | RELIGION_SECULARIZACION_Y_LAICIDAD | Religion, secularism |
| SAL | SALUD | Health |
| SEG | SEGURIDAD_PUBLICA | Public security |
| SOC | SOCIEDAD_DE_LA_INFORMACION | Information society |

### 2.2 The 276 domain pairs

The sweep tests all C(24, 2) = **276 unique cross-domain pairs** — every
combination of two surveys from the 24 above. For example:

- `CIE::COR` — do science attitudes correlate with corruption perceptions?
- `GEN::REL` — do gender attitudes correlate with religious practice?
- `POB::SEG` — does poverty perception correlate with security concerns?

### 2.3 Which questions within each survey?

For each survey, the sweep selects the **top 3 variables by entropy** (the 3
questions with the most evenly-distributed responses, indicating maximum
discriminating power). This avoids highly skewed questions (e.g., 95%
agree/disagree) that produce little signal in any cross-tabulation.

Each domain pair thus produces **9 variable-pair estimates** (3 × 3 questions).
Across 276 domain pairs: 276 × 9 = **2,484 total variable-pair estimates**.

Variable IDs have the format `{question_code}|{DOMAIN_CODE}`, e.g.:
- `p17|CIE` — question 17 from the Science & Technology survey
- `p36_8|COR` — question 36.8 from the Corruption survey

### 2.4 What do the bridge estimates measure?

For each of the 2,484 variable pairs, the bridge estimates answer:

> **"If we could observe the same person in both surveys, how strongly would
> their answer to question X correlate with their answer to question Y?"**

Under CIA, this is approximated as: *the correlation we would see if we sorted
both survey populations by their SES profile and compared the resulting
distributions.* A large Cramér's V or γ means that the SES patterns driving the
two questions are similar — which is social scientists' shorthand for "these
domains are connected through socioeconomic inequality."

---

## 3. The six estimators

### 2.1 Baseline — `CrossDatasetBivariateEstimator`

**What it does:**
1. Fit `P(Y_a | SES)` and `P(Y_b | SES)` via MNLogit/OrderedModel on each survey.
2. Sample a synthetic reference population of `n_sim` people by drawing SES
   profiles from the pooled marginals of both surveys.
3. For each simulated person, draw one response from each model's predicted
   distribution (`simulate_responses()`).
4. Cross-tabulate the two sets of simulated responses.
5. Compute Cramér's V and χ² p-value from that table.

**Reports:**
| Field | Meaning |
|-------|---------|
| `baseline_v` | Cramér's V on the simulated joint table |
| `baseline_p` | χ² p-value (null: independence) |

**What it tells you:** "If we standardize both surveys to the same population mix,
how strongly do Y_a and Y_b co-vary?" This is the simplest bridge estimate and
serves as the anchor for all other methods.

**Limitations:** (1) V is inflated by multinomial sampling noise when `n_sim` is
small relative to K_a × K_b cells; (2) V is unsigned — it captures *any*
deviation from independence, not just ordinal association; (3) the SES-mediated
signal is not separated from direct SES confounding.

---

### 2.2 Residual — `ResidualBridgeEstimator`

**What it does:**
1. Same reference population as baseline.
2. Cluster the population into `n_cells` SES-homogeneous groups (KMeans on
   encoded SES features).
3. Within each cell, simulate responses and compute Cramér's V on the
   within-cell cross-tab.
4. Pool across cells as: `v_residual = Σ(v_k × n_k) / Σ(n_k)`.
5. Compute `ses_fraction = v_residual / v_baseline`.

**Reports:**
| Field | Meaning |
|-------|---------|
| `residual_v` | Weighted-average within-cell Cramér's V |
| `ses_fraction` | Ratio residual / baseline (intended: fraction surviving after SES control) |
| `n_cells_used` | Number of KMeans cells with enough data |

**What it should tell you:** "How much of the baseline association is genuine
(not just SES confounding)?" A `ses_fraction` near 0 would mean pure
confounding; near 1 would mean the link exists beyond SES.

**Current status: PATHOLOGICAL.** The sweep shows `ses_fraction > 1` for 100% of
pairs (mean 3.05). The within-cell V is always *larger* than the baseline V.
Root cause: **small-sample Cramér's V bias.** With `n_sim=500` split into ~20
cells of ~25 people and cross-tabs of ~4×5, the expected V under *complete
independence* is already ~0.25 from sampling noise alone. The pooled average of
these inflated values exceeds the baseline V, which is computed on the full 500
rows and has much less bias. See §5.1 for proposed fixes.

---

### 2.3 Ecological — `EcologicalBridgeEstimator`

**What it does:**
1. Divide both surveys into demographic cells by `cell_cols` (default:
   `[escol, edad]` → up to 35 cells).
2. For each shared cell, compute the mean response to Y_a in survey A and the
   mean response to Y_b in survey B.
3. Correlate those two vectors of cell means using Spearman's ρ.
4. Bootstrap CI by resampling respondents within cells.

**Reports:**
| Field | Meaning |
|-------|---------|
| `eco_rho` | Spearman ρ on cell-level means |
| `eco_p` | p-value for ρ = 0 |
| `eco_ci` | 95% bootstrap CI |
| `eco_n_cells` | Number of shared cells with enough data |

**What it tells you:** "Do the same demographic subgroups tend to answer both
questions similarly?" If young, educated people score high on Y_a *and* high on
Y_b, ρ is positive.

**Critical caveat — ecological fallacy:** This measures a *group-level*
correlation, not an individual-level one. Strong `eco_rho` does not mean the
same individuals who answer Y_a one way also answer Y_b the same way.

**Sweep diagnosis:** Most differentiated estimator — 26% of pairs have |ρ| > 0.3,
with substantively coherent top signals (economic perception × education,
science trust × culture). The `eco_n_cells` distribution (median 25, min 5) is
generally adequate. Pairs with fewer than 10 cells should be flagged.

---

### 2.4 Bayesian — `BayesianBridgeEstimator`

**What it does:**
1. Fit `P(Y_a | SES)` and `P(Y_b | SES)` via MNLogit/OrderedModel.
2. Sample a reference population of `n_sim` people (same as baseline).
3. Draw `n_draws` parameter vectors from the Laplace posterior (multivariate
   normal: mean = MLE, covariance = inverse Hessian).
4. For each draw, predict probability vectors for all reference people, then
   compute the CIA joint table:
   `J(j,k) = mean_i[ P(Y_a=j | SES_i) × P(Y_b=k | SES_i) ]`.
5. Compute Goodman-Kruskal γ and Cramér's V from each joint table.
6. Report mean and 2.5–97.5 percentile CI over draws.

**Reports:**
| Field | Meaning |
|-------|---------|
| `bay_gamma` | Mean γ across posterior draws |
| `bay_gamma_ci` | 95% credible interval for γ |
| `bay_v` | Mean Cramér's V across draws |
| `bay_v_ci` | 95% CI for V |
| `bay_r2_a`, `bay_r2_b` | McFadden pseudo-R² for each outcome model |

**What it should tell you:** "Accounting for parameter uncertainty, how strong is
the ordinal association between Y_a and Y_b through the SES bridge?"

**Current status: NEAR-ZERO GAMMA.** The sweep shows bay_γ ≈ 0 for all 276
domain pairs. Two compounding causes:

1. **Real but small signal.** With K_a ≈ 10 and K_b ≈ 11, the CIA joint table
   has 110 cells. Even with R² ≈ 0.17, the ordinal deviation from independence
   in each cell is ~0.001, yielding |γ| ≈ 0.04 at the MLE. The signal is
   genuine but inherently small.

2. **Ill-conditioned Laplace posterior.** MNLogit with K=10 outcomes, ~1200
   observations, and ~15 SES features suffers near-separation. Many parameters
   have BSE > 10 (some > 100). Posterior draws are wildly different from the
   MLE, producing random probability landscapes where γ flips sign across draws
   and averages to zero. Meanwhile, V is always positive (any random table
   structure inflates V), so bay_v ≈ 0.14 is an artifact of posterior diffusion,
   not real association.

**Diagnostic:** `bay_r2_a` and `bay_r2_b` are useful — they tell you whether SES
predicts the target variables at all. Values below 0.05 mean the bridge has no
leg to stand on. But even with R² ≈ 0.17, the Bayesian γ is unreliable due to
the ill-conditioned posterior. See §5.2 for proposed fixes.

---

### 2.5 MRP — `MRPBridgeEstimator`

**What it does:**
1. Divide both surveys into cells by `cell_cols` (default: `[escol, edad, sexo]`
   → up to ~70 cells).
2. For each shared cell in each survey, compute the empirical distribution of Y.
3. Apply James-Stein shrinkage: pull each cell's distribution toward the global
   marginal, weighted by cell sample size (`κ` controls shrinkage strength).
4. Post-stratify: weight each cell by its share of the combined population.
5. Build the CIA joint table:
   `J(j,k) = Σ_c [ w_c × P_shrunk(Y_a=j | c) × P_shrunk(Y_b=k | c) ]`
6. Bootstrap CI by resampling respondents within cells.

**Reports:**
| Field | Meaning |
|-------|---------|
| `mrp_gamma` | Goodman-Kruskal γ from the post-stratified joint table |
| `mrp_gamma_ci` | 95% bootstrap CI |
| `mrp_v` | Cramér's V from the same table |
| `mrp_cells` | Number of shared cells used |

**What it tells you:** "Using cell-level patterns without assuming a functional
form (like logistic regression), what is the ordinal association through the SES
bridge?" MRP is the nonparametric counterpart to the Bayesian estimator.

**Shrinkage bias:** James-Stein intentionally attenuates toward the grand mean →
γ is systematically pulled toward zero. This is a feature (guards against
overfitting noisy cells) but means `mrp_γ` underestimates the true association.

**Sweep diagnosis:** Best-performing estimator for discrimination. 12.3% of CIs
exclude zero (vs 0% for Bayesian). Top signals are substantively coherent
(education × economic perception). Tight CIs (mean width 0.014 vs 0.210 for
Bayesian). Correlates with ecological ρ (r = 0.45), providing cross-validation.

---

### 2.6 Doubly Robust (DR) — `DoublyRobustBridgeEstimator`

**What it does:**
1. Fit outcome models `P(Y_a | SES)`, `P(Y_b | SES)` as before.
2. Fit a propensity model `P(survey = A | SES)` via logistic regression on the
   pooled respondents from both surveys.
3. Compute IPW weights for survey A respondents: `w_i = (1 − π_i) / π_i`,
   which reweights them to look like the combined population.
4. AIPW correction: `marg_k = imputed_mean + IPW_residual`. This combines the
   outcome model prediction with a bias-correction term weighted by propensity.
5. Build CIA joint table on a shared reference population (same individual-level
   approach as Bayesian).
6. Bootstrap CI by resampling and refitting both models.

The "doubly robust" property means γ is consistent if **either** the outcome
model **or** the propensity model is correctly specified.

**Reports:**
| Field | Meaning |
|-------|---------|
| `dr_gamma` | AIPW-corrected Goodman-Kruskal γ |
| `dr_gamma_ci` | 95% bootstrap CI |
| `dr_v` | Cramér's V |
| `dr_ks` | Kolmogorov-Smirnov statistic on propensity scores |

**The KS diagnostic — why DR is the only estimator that reports it:**

KS measures how well the propensity model separates respondents from survey A vs
survey B based on their SES profiles. It quantifies the **positivity assumption**
that DR requires: every SES profile in survey A must also have some probability
of appearing in survey B.

The propensity model is fit ONLY on the DR estimator. No other estimator uses
a propensity model, so no other estimator has this diagnostic.

**How KS is computed — mathematically:**

Let:
- `sub_a` = respondents who answered `col_a` in survey A with valid SES data
- `sub_b` = respondents who answered `col_b` in survey B with valid SES data
- `X_a`, `X_b` = their encoded SES feature matrices (same columns)
- `δ = [1,...,1, 0,...,0]` = survey indicator for the pooled sample

Fit: `logit(π_i) = α + β' X_i`, where `π_i = P(from survey A | SES_i)`

Then:
- `prop_a = { π_i : i ∈ sub_a }` = propensity scores for survey A respondents
- `prop_b = { π_j : j ∈ sub_b }` = propensity scores for survey B respondents
- `KS = sup_t | F_a(t) − F_b(t) |` = maximum gap between the two empirical CDFs

**KS is comparing the SES composition of who answered each question** — NOT the
distribution of answers. The answer values `col_a[i]`, `col_b[j]` are used only
to filter respondents (exclude sentinels/NaN). After filtering, only the SES
columns enter the propensity model.

**Interpretation of KS:**
| KS range | Meaning | Action |
|----------|---------|--------|
| < 0.2 | Excellent overlap. IPW weights are well-behaved. | Trust DR γ |
| 0.2–0.4 | Moderate overlap. Some weight trimming. | DR γ is indicative |
| 0.4–0.6 | Poor overlap. Aggressive trimming. | Treat with caution |
| > 0.6 | Very poor overlap or near-complete separation. | DR is unreliable |

**Sweep diagnosis:** Bimodal distribution — 46% have KS < 0.3 (good overlap),
43% have KS > 0.5 (poor overlap). The two clusters correspond to survey pairs
with similar vs. dissimilar SES distributions (KS varies by survey pair, not by
variable pair). When overlap is poor, trimming suppresses the signal: mean
|dr_γ| = 0.026 for KS < 0.3 vs 0.017 for KS > 0.8.

---

## 4. Cross-method interpretation

### Reading a sweep output line

```
base=0.18 resid=0.11 bay_γ=+0.22 mrp_γ=+0.09 dr_γ=+0.19 ks=0.61
```

| Comparison | What it reveals |
|------------|-----------------|
| base vs resid | What fraction of the association is SES-mediated confounding (when residual is working correctly) |
| bay_γ sign and CI | Direction and robustness under parameter uncertainty |
| mrp_γ vs bay_γ | Parametric (logistic) vs nonparametric (cell-based) agreement |
| dr_γ vs bay_γ | Whether propensity correction changes the picture |
| ks value | Whether DR is operating in its valid regime |
| eco_ρ vs mrp_γ | Group-level (ecological) vs individual-level (CIA) agreement |

### Concordance patterns

| Pattern | Diagnosis |
|---------|-----------|
| High base V + high resid V (ses_fraction ≈ 1) | Strong conceptual link, not just SES confounding |
| High base V + low resid V (ses_fraction ≈ 0) | Association is SES-mediated (pure confounding) |
| bay_γ CI excludes 0 | Robust ordinal association under parameter uncertainty |
| mrp_γ ≈ bay_γ | Parametric and nonparametric approaches agree |
| mrp_γ << bay_γ | Cells too small (heavy shrinkage) or logistic model overfits |
| |eco_ρ| > 0.3 + |mrp_γ| > 0.02 | Both cell-based methods see signal → robust |
| DR KS > 0.5 | DR weights unreliable; prefer Bayesian/MRP for this pair |
| DR γ ≠ bay_γ with good KS | Possible outcome model misspecification |

### Method reliability hierarchy (based on sweep results)

1. **MRP** — best discrimination (12.3% CIs exclude zero), substantively
   coherent top signals, tight CIs, no pathological failure modes
2. **Ecological** — widest effect range, useful for group-level patterns, but
   subject to ecological fallacy
3. **DR** — theoretically strongest (doubly robust), but half the pairs have
   KS > 0.5 (unreliable overlap); good where overlap is adequate
4. **Bayesian** — currently unreliable due to ill-conditioned posterior; V is
   inflated, γ is washed out. Needs fixes (see §5)
5. **Baseline** — useful anchor but V is unsigned and includes sampling noise
6. **Residual** — currently pathological (ses_fraction > 1 always). Needs fix

---

## 5. Sweep diagnostics (276 domain pairs, 2484 variable pairs)

### 4.1 Summary statistics

| Method | N | Mean | IQR [25, 75] | Range |
|--------|---|------|--------------|-------|
| Baseline V | 2484 | 0.162 | [0.156, 0.167] | [0.107, 0.302] |
| Residual V | 2484 | 0.489 | [0.477, 0.505] | [0.347, 0.564] |
| Eco \|ρ\| | 2484 | 0.113 | [0.035, 0.154] | [0.000, 0.895] |
| Bayesian γ | 2484 | -0.000 | [-0.005, +0.005] | [-0.103, +0.084] |
| MRP γ | 2484 | +0.001 | [-0.001, +0.001] | [-0.044, +0.116] |
| DR γ | 2484 | -0.000 | [-0.010, +0.011] | [-0.185, +0.131] |
| DR KS | 2484 | 0.462 | [0.243, 0.680] | [0.130, 1.000] |

### 4.2 Red flags

| Issue | Severity | Impact |
|-------|----------|--------|
| Residual V > Baseline V in 100% of pairs | Critical | Residual estimator is unusable — ses_fraction is meaningless |
| Bayesian γ CI never excludes zero | Critical | Bayesian estimator provides no discrimination between pairs |
| DR KS > 0.5 for 43% of pairs | Moderate | DR unreliable for nearly half the survey pairings |
| Bayesian V ≈ 0.14 everywhere (artifact) | Moderate | Misleading if interpreted as real association strength |

### 4.3 Cross-method correlations

|  | bay_γ | mrp_γ | dr_γ | eco_ρ |
|--|-------|-------|------|-------|
| bay_γ | 1.00 | 0.14 | 0.71 | 0.08 |
| mrp_γ | — | 1.00 | 0.14 | 0.45 |
| dr_γ | — | — | 1.00 | 0.11 |
| eco_ρ | — | — | — | 1.00 |

Two clusters: Bayesian+DR (r=0.71, share individual-level CIA) and MRP+Eco
(r=0.45, share cell-based approach). The two families are nearly uncorrelated.

---

## 6. Proposed improvements

### 5.1 Fix: Residual estimator (CRITICAL)

**Problem:** Small-sample Cramér's V bias. With ~25 people per cell and 4×5
cross-tabs, V ≈ 0.25 under pure independence from sampling noise alone.

**Options (from least to most invasive):**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A. Bias-corrected V | Use Bergsma's correction: `V_c = sqrt(max(0, χ²/n - (r-1)(c-1)/(n-1)) / (min(r,c)-1))` | Simple, fixes the root cause | Still averages per-cell V (not true MH) |
| B. True CMH pooling | Pool raw concordance/discordance counts across cells, compute one combined test statistic | Statistically proper | More complex implementation |
| C. Increase n_sim | Use n_sim = 5000–10000 so cells have 250–500 people | Eliminates bias naturally | Slower (5–10× more model evaluations) |

**Recommendation:** Option B (true CMH) is the correct solution. Option A is a
quick fix. Option C is a brute-force workaround.

### 5.2 Fix: Bayesian γ recovery (CRITICAL)

**Problem:** Two causes — (a) many outcome categories → small inherent γ signal;
(b) ill-conditioned Laplace posterior → random draws wash out ordinal structure.

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A. Category binning | Collapse Y into 3–5 ordinal bins before model fitting | Dramatically reduces near-separation; stronger γ signal per cell; better-conditioned covariance | Loses granularity; bin boundaries are arbitrary |
| B. Covariance regularization | Ledoit-Wolf shrinkage or diagonal BSE cap (e.g., max BSE = 5.0) on the Laplace covariance | Keeps draws near MLE; preserves ordinal structure | Underestimates true uncertainty; choice of cap is ad hoc |
| C. Compute γ from mean joint table | Instead of `mean(γ_per_draw)`, compute `γ(mean_joint_table)` | Eliminates sign-cancellation of per-draw γ | Less Bayesian (doesn't properly propagate uncertainty to γ) |
| D. Penalized MNLogit | L2-regularized (ridge) MNLogit to shrink extreme coefficients | Better-conditioned covariance; closer to well-separated regime | statsmodels doesn't support L2-penalized MNLogit natively; would need sklearn or manual implementation |

**Recommendation:** Options A + C together. Category binning addresses the root
cause (too many near-empty cells in the 10×11 joint table). Computing γ from the
mean joint table eliminates the sign-cancellation artifact. Option B is a
reasonable complement if A alone is insufficient.

### 5.3 Improvement: MRP cell structure (user proposal 1)

**Problem:** Default `cell_cols = [escol, edad, sexo]` → up to 70 cells.
With ~1200 respondents per survey, some cells have < 10 people → heavy
shrinkage → γ attenuated.

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A. Reduce cell_cols | Use `[escol_binned, sexo]` (e.g., 3 education groups × 2 sexo = 6 cells) | Much larger cells; less shrinkage; more stable estimates | Loses age variation |
| B. Adaptive cell merging | Automatically merge small cells with their nearest neighbor until all cells have ≥ min_n | Retains granularity where data permits | More complex implementation |
| C. Bin cell_cols variables | Bin edad into 3 groups (young/mid/old), escol into 3 (low/mid/high), keep sexo → 18 cells | Good balance of granularity and cell size | Bin boundaries are arbitrary |

**Recommendation:** Option C — bin edad and escol into 3 levels each before cell
construction. This gives 18 cells with ~60+ people each, reducing shrinkage
while maintaining meaningful demographic variation. Combined with category
binning of the outcome variables (§5.2 Option A), the MRP estimator should
produce substantially larger and more meaningful γ values.

### 5.4 Improvement: DR propensity overlap (user proposal 2)

**Problem:** 43% of pairs have KS > 0.5, meaning the propensity model perfectly
separates the two survey populations. IPW weights become extreme and unreliable.

**Causes of high KS:**
1. Surveys target different subpopulations (skip patterns filter different
   demographic groups).
2. The propensity model uses too many SES features (7 variables → ~15 encoded
   columns), making it easy to discriminate even similar populations.
3. SES cells with very few observations from one survey drive propensity
   scores to extreme values.

**Options:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A. Restrict propensity features | Use only `[sexo, escol, edad]` (3 vars, ~8 columns) instead of all 7 SES variables | Less discriminating model → lower KS → better overlap | May undercount real SES differences |
| B. Filter small SES cells | Before fitting propensity model, drop respondents from SES cells with < min_n from either survey | Removes the cases that drive extreme propensity | Reduces sample size; may introduce selection bias |
| C. Propensity score calibration | Use Platt scaling or isotonic regression on propensity scores to improve calibration | Better-calibrated weights → less extreme IPW | Adds complexity; marginal improvement if model is well-specified |
| D. Overlap weight (OW) instead of IPW | Replace `(1-π)/π` with `min(π, 1-π)` weights (Li & Thomas 2019) | Naturally downweights non-overlapping regions | Different estimand (focuses on overlap population, not full population) |
| E. KS-gated reporting | Don't suppress DR — but flag pairs with KS > 0.4 as "low confidence" and prefer MRP/Bayesian for those pairs | Transparent; uses DR where valid, falls back elsewhere | Doesn't improve DR itself |

**Recommendation:** Options A + E together. Restricting to 3 propensity features
lowers KS mechanically while keeping the most important demographic variables.
KS-gating ensures that pairs with persistently poor overlap are reported honestly
rather than masked. Option D (overlap weights) is a principled alternative for
future investigation.

### 5.5 Additional improvement: outcome category binning (applies to ALL estimators)

**Rationale:** Most survey questions have 5–12 response categories. MNLogit with
K > 6 and ~15 features on ~1200 observations produces near-separation
(parameters with BSE > 100). This propagates to every estimator:

- **Baseline:** More multinomial noise in simulated responses from diffuse models.
- **Bayesian:** Wild posterior draws (the primary failure cause).
- **MRP:** More unique response patterns per cell, less signal per pattern.
- **DR:** Outcome model predictions are noisier.

**Proposal:** Before model fitting, collapse outcome categories into 3–5 ordinal
bins. For example, a 10-point Likert scale becomes [1–2, 3–4, 5–6, 7–8, 9–10].
This should be the **single highest-impact improvement** across all estimators:

- Baseline V: less simulation noise.
- Bayesian: well-conditioned covariance, γ detectable at MLE.
- MRP: fewer categories per cell → more observations per category → less shrinkage.
- DR: better-specified outcome model → less extreme IPW corrections.
- Residual: smaller cross-tabs → less small-sample V bias.

### 5.6 Additional improvement: increase n_sim (BASELINE, BAYESIAN, DR)

**Current:** `n_sim = 500`. With K_a × K_b ≈ 110 cells, many cells in the
simulated joint table have < 5 expected observations → sampling noise dominates.

**Proposal:** Increase to `n_sim = 2000–5000`. This stabilizes the baseline V,
reduces multinomial sampling variance in the Bayesian joint table, and provides
a larger reference population for DR.

**Cost:** Linear in n_sim for prediction time. With category binning (3×4 = 12
cells instead of 110), n_sim = 2000 gives ~167 per cell — adequate.

### 5.7 Additional improvement: penalized outcome models

**Problem:** MNLogit near-separation produces extreme coefficients and ill-
conditioned Hessians.

**Proposal:** Use L2-regularized (ridge) logistic regression for the outcome
models. This caps coefficient magnitudes, improves the Hessian condition number,
and produces better-calibrated predicted probabilities.

**Implementation:** statsmodels `Logit/MNLogit` doesn't support L2 natively.
Options: (a) use `sm.MNLogit(...).fit_regularized(alpha=...)`, or (b) add a
manual Tikhonov penalty to the log-likelihood.

---

## 7. Improvement priority matrix

| # | Improvement | Impact | Effort | Fixes |
|---|-------------|--------|--------|-------|
| 1 | Category binning (§5.5) | **Very High** | Low | Bayesian, MRP, DR, Residual, Baseline |
| 2 | Residual: true CMH pooling (§5.1B) | **High** | Medium | Residual |
| 3 | Bayesian: γ from mean joint table (§5.2C) | **High** | Low | Bayesian |
| 4 | MRP: bin cell_cols variables (§5.3C) | **Medium** | Low | MRP |
| 5 | DR: restrict propensity features (§5.4A) | **Medium** | Low | DR KS |
| 6 | Increase n_sim to 2000 (§5.6) | **Medium** | Trivial | Baseline, Bayesian, DR |
| 7 | Bayesian: covariance regularization (§5.2B) | **Medium** | Medium | Bayesian |
| 8 | DR: KS-gated reporting (§5.4E) | **Low** | Low | Transparency |
| 9 | Penalized MNLogit (§5.7) | **Medium** | High | All parametric estimators |

**Recommended implementation order:** 1 → 6 → 3 → 2 → 4 → 5 → 8 → 7 → 9.

The first three changes (category binning + n_sim increase + γ-from-mean-table)
should resolve the two critical failures (Bayesian γ ≈ 0, Residual V inflation)
with minimal code changes, and improve every other estimator as a side effect.

---

## 8. v2 Improvements implemented (2026-03-04)

All 7 improvements from §5 and §6 are now implemented in `ses_regression.py`:

| # | Change | Status | What it fixed |
|---|--------|--------|---------------|
| 1 | **Category binning** (`bin_categories()`, `max_categories=5`) | ✅ Done | Near-separation in all parametric estimators |
| 2 | **`n_sim` 500 → 2000** | ✅ Done | High-variance reference SES population |
| 3 | **Bayesian γ from mean joint table** | ✅ Done | Jensen's inequality sign cancellation |
| 4 | **Residual bias-corrected V + CMH pooling** | ✅ Done | Small-sample V inflation, wrong per-stratum averaging |
| 5 | **MRP cell binning** (`bin_cell_vars={'edad':3,'escol':3}`) | ✅ Done | Too many cells with <5 members |
| 6 | **DR restricted propensity** (`propensity_vars=['sexo','escol','edad']`) | ✅ Done | Over-fitted propensity → KS > 0.5 |
| 7 | **Bayesian covariance regularization** (diagonal shrinkage + BSE cap) | ✅ Done | Ill-conditioned Hessian from near-separation |

New output fields:
- **Residual**: `stratified_gamma` (CMH pooled ordinal γ)
- **DR**: `ks_warning` (bool, True when KS > 0.4), `propensity_features` (list of vars used)

---

## 9. Cross-estimator metrics and ensemble selection

### 8.1 Why compare estimators against each other?

Each estimator makes different assumptions and has different failure modes. No
single estimator is uniformly best — the right strategy is to:

1. Run all 6 estimators on every pair.
2. Use **cross-estimator metrics** to detect when one estimator is unreliable.
3. Either (a) **select the most reliable estimator** for each pair, or
   (b) **combine estimators** in a weighted ensemble.

This is analogous to the "combining forecasts" literature (Bates & Granger 1969)
and the method comparison framework of Bland & Altman (1999).

### 8.2 Cross-estimator metrics in the test suite

The `TestCrossEstimatorConsistency` class in
[`tests/unit/test_bridge_evaluation.py`](tests/unit/test_bridge_evaluation.py)
implements the following metrics across 6 synthetic replications:

#### Sign concordance (Bland & Altman 1999)

**What it measures:** What fraction of replications does estimator X assign the
same sign to γ as the true DGP?

**Why it matters:** The most basic reliability check. An estimator that gets the
_direction_ of association wrong is worse than useless — it would cause a
researcher to conclude "inverse relationship" when the true one is positive.

**Formula:** Sign concordance = #{replicas where sign(γ̂) = sign(γ_true)} / N_replicas

**Threshold:** We require ≥ (N/2 + 1) concordant signs (majority), tested for
both Bayesian and MRP. A random estimator would pass 50% of the time; passing at
the majority threshold provides mild evidence of correct orientation.

**Citation:** Bland J.M. & Altman D.G. (1999). Measuring agreement in method
comparison studies. *Statistical Methods in Medical Research* 8(2):135-160.
DOI:[10.1177/096228029900800204](https://doi.org/10.1177/096228029900800204)

---

#### Inter-method gamma agreement (Bland-Altman Limits of Agreement)

**What it measures:** The mean absolute difference |γ_Bayesian - γ_MRP| across
replications. Small mean difference → both estimators are consistent with the
same underlying quantity.

**Why it matters:** If Bayesian and MRP γ estimates differ by > 0.4 on average,
at least one of them is biased or has failed. This triggers further diagnosis
(check pseudo-R², check n_cells, check KS).

**Formula:** LOA = mean|γ_Bay - γ_MRP| ± 1.96 × SD(γ_Bay - γ_MRP)

**Threshold:** Mean |diff| < 0.4 for correlated synthetic pairs.

**Citation:** Same Bland & Altman (1999) reference above.

---

#### Rank-order consistency (Datta & Satten 2005)

**What it measures:** Spearman rank correlation between Bayesian γ estimates and
DR γ estimates across replications. If both estimators are measuring the same
underlying quantity, they should rank the replications similarly even if their
absolute values differ.

**Why it matters:** Two estimators can disagree in magnitude but still be
useful — they're capturing the same ordinal information about which pairs are
more strongly associated. Rank correlation ρ < 0 would indicate one estimator is
noise-dominated.

**Formula:** ρ_Spearman(γ_Bay, γ_DR) across K replications

**Threshold:** ρ > -0.5 (we allow low positive or slightly negative ρ with only
6 replications, since Spearman ρ on 6 points is noisy).

**Citation:** Datta S. & Satten G.A. (2005). Rank-sum tests for clustered data.
*Journal of the American Statistical Association* 100(471):1040-1053.
DOI:[10.1198/016214505000000197](https://doi.org/10.1198/016214505000000197)

---

#### CI width efficiency

**What it measures:** Whether Bayesian and DR both produce positive-width
confidence intervals. This is a structural check: degenerate zero-width CIs
indicate numerical failure.

**Why it matters:** The Bayesian Laplace CI uses 200 posterior draws without
model refitting; the DR bootstrap CI uses 25 model refits. The Bayesian CI
should be more stable. If either produces zero width, the estimator has collapsed.

**Threshold:** Both CI widths > 0 for every replica.

---

#### Propensity overlap calibration (Li, Morgan & Zaslavsky 2018)

**What it measures:** The Kolmogorov-Smirnov statistic between propensity scores
of survey A respondents and survey B respondents. Low KS → good overlap → DR
weights are well-behaved.

**Why it matters:** DR consistency requires the positivity assumption:
every SES profile must have nonzero probability in both surveys. The propensity
score KS statistic operationalises this. With restricted features (only 3–4
encoded columns), KS should be < 0.5 for surveys drawn from the same DGP.

**Formula:** KS = sup|F_A(e) - F_B(e)| where e_i = P(survey=A | SES_i)

**Threshold:** Mean KS < 0.6 across same-DGP replications.

**Citation:** Li L., Morgan J.N., & Zaslavsky A.M. (2018). Balancing covariates
via propensity score weighting. *Journal of the American Statistical Association*
113(521):390-400. DOI:[10.1080/01621459.2016.1260466](https://doi.org/10.1080/01621459.2016.1260466)

---

#### Finiteness under correlated data (Rubin 1974)

**What it measures:** All 3 new estimators (Bayesian, MRP, DR) return finite
gamma values on at least 3 of 6 synthetic replications with known positive γ.

**Why it matters:** Rubin (1974) established that the DR estimator is consistent
if _either_ the outcome model or the propensity model is correctly specified.
But this guarantee only holds if the estimator converges. Checking that ≥50% of
runs succeed is a minimal robustness requirement.

**Citation:** Rubin D.B. (1974). Estimating causal effects of treatments in
randomised and nonrandomised studies. *Journal of Educational Psychology*
66(5):688-701.

---

### 8.3 Ensemble selection strategy

The 6 estimators address different potential failures of CIA. Rather than
picking one, we propose the following **selection and ensemble rules**:

#### Selection rule (pick the best single estimator per pair)

| Condition | Action |
|-----------|--------|
| DR `ks_warning = True` | Downweight or exclude DR estimate |
| Residual `ses_fraction > 2.0` after bias correction | Suspect both surveys have insufficient SES variation |
| Bayesian `pseudo_r2_a < 0.01` or `pseudo_r2_b < 0.01` | SES explains nothing; all bridge estimates are noise |
| MRP `n_cells_used < 5` | James-Stein shrinkage collapses to global mean; MRP uninformative |
| All estimators `|gamma| < 0.05` | Report "no detectable cross-survey association" |

#### Ensemble rule (confidence-weighted average)

When multiple estimators are reliable, combine them as:

```
γ_ensemble = Σ_k w_k × γ_k / Σ_k w_k

where w_k = 1 / CI_width_k  (inverse CI width = precision weight)
```

This is the **minimum-variance unbiased combination** (Bates & Granger 1969) of
estimators with known uncertainty. Estimators with wider CIs get less weight.

- Bayesian: typically narrow Laplace CI → high weight
- MRP: moderate CI from bootstrap → medium weight
- DR: wide CI from 25-bootstrap → low weight (but provides robustness check)
- Baseline/Residual: report V, not γ; convert via `cramers_v ≈ |gamma|^0.5`
  for rough ensemble inclusion

**Citation for ensemble:** Bates J.M. & Granger C.W.J. (1969). The combination
of forecasts. *OR* 20(4):451-468. DOI:[10.1057/jors.1969.103](https://doi.org/10.1057/jors.1969.103)

#### Implementation status

The selection and ensemble logic is **not yet in code** — it is a recommended
next step. The sweep script (`sweep_bridge_comparison.py`) now captures
`ks_warning`, `stratified_gamma`, `n_cells_used`, `pseudo_r2_a/b`, and CI
widths, which are the inputs needed to implement these rules.

A post-processing script (`scripts/debug/select_best_estimator.py`) should:
1. Load `bridge_comparison_results.json`
2. Apply selection rules to flag unreliable estimates per pair
3. Compute precision-weighted ensemble γ for each pair
4. Output a ranked list of cross-survey associations with ensemble confidence

---

## 10. File reference

| File | Description |
|------|-------------|
| [`ses_regression.py`](ses_regression.py) | All 6 estimators, `goodman_kruskal_gamma()`, `SESEncoder` |
| [`ses_analysis.py`](ses_analysis.py) | SES preprocessing, sentinel remapping |
| [`scripts/debug/sweep_bridge_comparison.py`](scripts/debug/sweep_bridge_comparison.py) | 276-pair sweep runner |
| [`data/results/bridge_comparison_results.json`](data/results/bridge_comparison_results.json) | Full sweep output |
| [`data/results/bridge_comparison_report.md`](data/results/bridge_comparison_report.md) | Auto-generated summary table |
| [`tests/unit/test_ses_regression.py`](tests/unit/test_ses_regression.py) | 77 unit tests (original + `stratified_gamma`) |
| [`tests/unit/test_bridge_estimators_v2.py`](tests/unit/test_bridge_estimators_v2.py) | 47 unit tests (v2 + binning + DR keys + `TestCategoryBinning`) |
| [`tests/unit/test_bridge_evaluation.py`](tests/unit/test_bridge_evaluation.py) | 45 evaluation tests (+ `TestCrossEstimatorConsistency`) |
