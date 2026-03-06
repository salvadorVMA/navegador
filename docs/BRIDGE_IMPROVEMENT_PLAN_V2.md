# Bridge Estimator Improvements — Methodology and Justification

*Version 2 — 2026-03-03*

## 1. Motivation

A full sweep of all 276 domain pairs (2484 variable pairs) across 6 bridge
estimators revealed critical pathologies in 4 of 6 methods. This document
describes each improvement, its mathematical basis, and the literature that
justifies it.

### 1.1 Sweep findings

| Finding | Severity | Root Cause |
|---------|----------|------------|
| Bayesian γ ≈ 0 for all 2484 pairs (0% CIs exclude zero) | Critical | (a) High K (6–13 categories) → MNLogit near-separation → ill-conditioned Laplace posterior; (b) averaging per-draw γ causes sign cancellation |
| Residual V > Baseline V in 100% of pairs (ses\_fraction = 3.05) | Critical | Small-sample Cramér's V bias in KMeans cells (~25 respondents per cell, 4×5 tables) |
| DR KS > 0.5 for 43% of pairs | Moderate | Propensity model uses ~15 encoded SES features; overpowered discrimination |
| MRP γ near-zero in aggregate (but 12.3% CIs exclude zero) | Moderate | ~70 cells with ~17 respondents each → heavy James-Stein shrinkage |

### 1.2 Cross-method correlations

The sweep revealed two estimator clusters:

1. **Individual-level CIA**: Bayesian + DR (r = 0.71) — both use `mean_i[P(Y_a|X_i) × P(Y_b|X_i)]`
2. **Cell-based**: MRP + Ecological (r = 0.45) — both aggregate within demographic cells

The two families are nearly uncorrelated (bay\_γ vs eco\_ρ: r = 0.08), confirming
they measure genuinely different aspects of the cross-survey association.

---

## 2. Change 1: Outcome Category Binning

### 2.1 Problem

Survey questions typically have 5–13 response categories. MNLogit with K outcome
categories estimates (K−1) × (p+1) parameters. With K = 10 and p = 15 SES
features (after one-hot encoding), the model has 144 free parameters estimated
from ~1,200 observations, yielding an events-per-variable (EPV) ratio of ~8.

### 2.2 Statistical basis

**Peduzzi, P., Concato, J., Kemper, E., Holford, T. R. & Feinstein, A. R. (1996).**
"A simulation study of the number of events per variable in logistic regression
analysis." *Journal of Clinical Epidemiology*, 49(12), 1373–1379.
DOI: [10.1016/S0895-4356(96)00236-3](https://doi.org/10.1016/S0895-4356(96)00236-3)

> With fewer than 10 events per predictor variable, logistic regression estimates
> exhibit large bias, poor coverage of confidence intervals, and convergence
> problems. For multinomial models, each additional category adds parameters,
> reducing the effective EPV.

**Agresti, A. (2002).** *Categorical Data Analysis*, 2nd ed. Wiley.
DOI: [10.1002/0471249688](https://doi.org/10.1002/0471249688)

> Collapsing sparse categories into fewer groups ensures adequate expected cell
> counts, reduces separation risk, and produces better-conditioned parameter
> estimates (§6.5).

**McCullagh, P. (1980).** "Regression models for ordinal data." *Journal of the
Royal Statistical Society: Series B*, 42(2), 109–142.
DOI: [10.1111/j.2517-6161.1980.tb01109.x](https://doi.org/10.1111/j.2517-6161.1980.tb01109.x)

> Ordinal models exploit ordinal structure, requiring K−1 intercepts plus p slope
> parameters (vs. (K−1)×p slopes in MNLogit). When ordinal structure is
> appropriate, fewer categories make ordinal models more practical.

### 2.3 Specification

Add `bin_categories(series, max_categories=5, var_type)`:

- **Ordinal variables** (numeric codes): sort unique values, partition into
  `max_categories` groups of approximately equal width via `np.array_split`.
  Each group maps to a consecutive integer code (1, 2, ..., max\_categories).

- **Nominal variables**: rank categories by frequency; keep the top
  `max_categories − 1`; merge all remaining categories into a single "other"
  bin coded as `max_categories`.

- **Identity**: if `len(unique_values) ≤ max_categories`, return unchanged.

Integrate into `SurveyVarModel.fit()` with parameter `max_categories=5`. Pass
through from all estimators. To reproduce pre-improvement behavior, callers
pass `max_categories=None`.

### 2.4 Expected impact

| Estimator | Before (K≈10) | After (K≤5) |
|-----------|---------------|-------------|
| MNLogit params | ~144 | ~64 |
| EPV | ~8 | ~19 |
| Max BSE (typical) | > 100 | < 5 |
| Joint table cells | ~110 | ~20 |
| Gamma signal strength | ~0.04 | ~0.15 (est.) |

This is the single highest-impact change; every other estimator benefits from
better-conditioned models.

---

## 3. Change 2: Increase Reference Population Size

### 3.1 Problem

With `n_sim = 500` and K_a × K_b ≈ 20 cells (after binning), the expected count
per cell is ~25 — adequate but not generous. With K_a × K_b ≈ 110 (before
binning), it was ~4.5, making the joint table heavily noise-dominated.

### 3.2 Specification

Change default `n_sim` from 500 to 2000 in `BayesianBridgeEstimator` and
`DoublyRobustBridgeEstimator`. Combined with category binning, this gives
~100 expected counts per cell in the joint table.

The sweep script `N_SIM` changes from 500 to 2000. Per-pair runtime increases
by ~2× for prediction (cheap) but model fitting time is unchanged.

---

## 4. Change 3: Bayesian γ — Compute from Mean Joint Table

### 4.1 Problem

The current code computes γ for each posterior draw and reports `mean(γ_draws)`.
With an ill-conditioned posterior (BSEs > 100), each draw produces a random
probability landscape. The per-draw γ values are roughly symmetric around zero
because:

1. Concordant and discordant pairs are **nonlinear** functions of the joint
   table entries.
2. Each draw produces random (non-ordinal) table structure, so γ flips sign
   across draws.
3. The mean of these sign-alternating values converges to zero.

Meanwhile, `mean(V_draws) ≈ 0.14` because Cramér's V is non-negative — any
random table structure inflates V, creating an artifact.

### 4.2 Statistical basis

The Goodman-Kruskal γ is:

$$\gamma = \frac{C - D}{C + D}$$

where C = concordant pairs, D = discordant pairs (Goodman & Kruskal, 1954).

**Goodman, L. A. & Kruskal, W. H. (1954).** "Measures of association for cross
classifications." *JASA*, 49(268), 732–764.
DOI: [10.1080/01621459.1954.10501231](https://doi.org/10.1080/01621459.1954.10501231)

Since C and D are sums of products of joint table entries,
`E[γ(J)] ≠ γ(E[J])` in general (Jensen's inequality). The mean table `E[J]`
preserves the ordinal structure of the MLE CIA table because:

$$E[J_{jk}] = \frac{1}{M} \sum_{m=1}^{M} J_{jk}^{(m)} \to E_\theta[J_{jk}(\theta)]$$

which is the posterior mean of the (j,k) cell probability. This converges to
the MLE value as the posterior concentrates. Computing `γ(E[J])` thus recovers
the MLE's ordinal signal.

### 4.3 Specification

Replace:
```python
'gamma': round(float(gammas.mean()), 4)
```
With:
```python
joint_mean = joint_tables.mean(axis=0)
gamma_point = goodman_kruskal_gamma(joint_mean)
...
'gamma': round(float(gamma_point), 4)
```

The CI (`gamma_ci_95`) continues to use per-draw percentiles — these correctly
reflect posterior uncertainty even though the point estimate uses the mean table.

---

## 5. Change 4: Residual Estimator — Bias-Corrected V + Stratified Gamma

### 5.1 Problem

Cramér's V is positively biased in small samples. For an r × c table with n
observations under true independence:

$$E[\hat{V}^2] = \frac{(r-1)(c-1)}{n-1} \cdot \frac{1}{\min(r,c)-1}$$

With r = 4, c = 5, n = 25 (typical cell size after KMeans), the expected V
under independence is:

$$E[\hat{V}] \approx \sqrt{\frac{3 \times 4}{24 \times 3}} = \sqrt{0.167} \approx 0.41$$

This exceeds the baseline V (~0.16 computed on all 500 observations), producing
the observed ses\_fraction > 1 for every pair.

### 5.2 Statistical basis — Bias-corrected V

**Bergsma, W. (2013).** "A bias-correction for Cramér's V and Tschuprow's T."
*Journal of the Korean Statistical Society*, 42(3), 323–328.
DOI: [10.1016/j.jkss.2012.10.002](https://doi.org/10.1016/j.jkss.2012.10.002)
PDF: `docs/references/bergsma_2013_bias_corrected_V.pdf`

Bergsma proposes replacing the standard estimator with:

$$\tilde{\phi}^2 = \max\!\left(0,\; \frac{\chi^2}{n} - \frac{(r-1)(c-1)}{n-1}\right)$$

$$\tilde{r} = r - \frac{(r-1)^2}{n-1}, \quad \tilde{c} = c - \frac{(c-1)^2}{n-1}$$

$$\tilde{V} = \sqrt{\frac{\tilde{\phi}^2}{\min(\tilde{r}, \tilde{c}) - 1}}$$

This correction removes the first-order bias. For the example above,
$\tilde{V} = 0$ under true independence (as desired).

### 5.3 Statistical basis — CMH-style stratified pooling

**Mantel, N. & Haenszel, W. (1959).** "Statistical aspects of the analysis of
data from retrospective studies of disease." *JNCI*, 22(4), 719–748.
DOI: [10.1093/jnci/22.4.719](https://doi.org/10.1093/jnci/22.4.719)

**Cochran, W. G. (1954).** "Some methods for strengthening the common
chi-squared tests." *Biometrics*, 10(4), 417–451.
DOI: [10.2307/3001616](https://doi.org/10.2307/3001616)

The Mantel-Haenszel principle requires pooling **raw counts** across strata
before computing a summary statistic. Averaging per-stratum V values is
incorrect because (a) V is non-negative and biased in small samples, and (b)
averaging does not weight by information content properly.

For ordinal data, the appropriate stratified statistic pools concordance and
discordance counts:

$$C_{\text{total}} = \sum_{k=1}^{K} C_k, \quad D_{\text{total}} = \sum_{k=1}^{K} D_k$$

$$\gamma_{\text{stratified}} = \frac{C_{\text{total}} - D_{\text{total}}}{C_{\text{total}} + D_{\text{total}}}$$

### 5.4 Specification

1. Add `bias_corrected_cramers_v(contingency_table)` using Bergsma's formula.
2. Replace the per-cell `association(ct, method='cramer')` with the corrected
   version.
3. Add CMH-style concordance/discordance pooling across cells to produce
   `stratified_gamma`.
4. Include `stratified_gamma` in the return dict (backward-compatible addition).

---

## 6. Change 5: MRP Cell Binning

### 6.1 Problem

Default `cell_cols = ['escol', 'edad', 'sexo']` with 5 × 7 × 2 = 70 cells.
With ~1,200 respondents per survey: ~17 per cell. James-Stein shrinkage with
κ = 10:

$$\lambda = \frac{n_c}{n_c + \kappa} = \frac{17}{17 + 10} = 0.63$$

This pulls 37% of each cell estimate toward the global marginal — heavy
attenuation of cell-specific signal.

### 6.2 Statistical basis

**Stein, C. (1956).** "Inadmissibility of the usual estimator for the mean of a
multivariate normal distribution." *Proceedings of the Third Berkeley Symposium*,
Vol. 1, 197–206.
DOI: [10.1525/9780520313880-018](https://doi.org/10.1525/9780520313880-018)

**James, W. & Stein, C. (1961).** "Estimation with quadratic loss." *Proceedings
of the Fourth Berkeley Symposium*, Vol. 1, 361–379.

> The James-Stein shrinkage estimator dominates the unbiased estimator in total
> MSE when estimating ≥ 3 parameters simultaneously. Shrinkage is largest for
> cells with the smallest sample sizes.

**Park, D. K., Gelman, A. & Bafumi, J. (2004).** "Bayesian multilevel estimation
with poststratification." *Political Analysis*, 12(4), 375–385.
DOI: [10.1093/pan/mph024](https://doi.org/10.1093/pan/mph024)
PDF: `docs/references/park_gelman_bafumi_2004_mrp.pdf`

> MRP produces reliable subnational estimates even with small cell sizes, but
> works best when cells are large enough that the empirical distribution is
> informative. With very small cells, partial pooling dominates and the
> estimates converge to the population average.

### 6.3 Specification

Bin edad (7 groups → 3: young/mid/old) and escol (5 levels → 3: low/mid/high)
before cell construction. This produces 3 × 3 × 2 = 18 cells with ~67
respondents each.

New parameter `bin_cell_vars: Dict[str, int]` defaults to `{'edad': 3, 'escol': 3}`.
Binning uses `pd.cut` with equal-width bins on the numeric column.

Shrinkage factor improves: λ = 67/(67+10) = 0.87 — only 13% pull toward the
global marginal.

---

## 7. Change 6: DR Propensity Feature Restriction + KS Gating

### 7.1 Problem

The propensity model P(survey = A | SES) uses ~15 encoded columns from 7 SES
variables. With this many features and ~2,400 pooled observations, the logistic
regression can nearly perfectly discriminate the two survey populations (KS > 0.5
for 43% of pairs). This violates the **positivity assumption** required for
valid IPW estimation.

### 7.2 Statistical basis — Positivity

**Petersen, M. L., Porter, K. E., Gruber, S., Wang, Y. & van der Laan, M. J.
(2012).** "Diagnosing and responding to violations in the positivity assumption."
*Statistical Methods in Medical Research*, 21(1), 31–54.
DOI: [10.1177/0962280210386207](https://doi.org/10.1177/0962280210386207)

> Positivity requires that every covariate stratum has non-zero probability of
> belonging to either group. Near-violations produce extreme IPW weights,
> inflated variance, and bias. The Kolmogorov-Smirnov test on propensity score
> distributions quantifies the degree of overlap violation.

**Zhu, Y., Hubbard, R. A., Chubak, J., Roy, J. & Mitra, N. (2021).**
"Core concepts in pharmacoepidemiology: Violations of the positivity assumption."
*Pharmacoepidemiology and Drug Safety*, 30(11), 1471–1485.
DOI: [10.1002/pds.5338](https://doi.org/10.1002/pds.5338)

> Comprehensive review of positivity violation consequences. Compares trimming,
> truncation, matching weights, overlap weights, and entropy weights.

### 7.3 Statistical basis — Overlap weights (future option)

**Li, F., Morgan, K. L. & Zaslavsky, A. M. (2018).** "Balancing covariates via
propensity score weighting." *JASA*, 113(521), 390–400.
DOI: [10.1080/01621459.2016.1260466](https://doi.org/10.1080/01621459.2016.1260466)
PDF: `docs/references/li_morgan_zaslavsky_2018_overlap_weights.pdf`

> Overlap weights w_i = min(e(x), 1-e(x)) are bounded (unlike IPW), minimize
> asymptotic variance among all balancing weight estimators, and naturally
> down-weight units in regions of poor overlap.

### 7.4 Specification

Add `propensity_vars: List[str]` parameter (default `['sexo', 'escol', 'edad']`).
Fit propensity model on this restricted set using a separate `SESEncoder`.
Outcome models continue using the full SES feature set.

With 3 vars → ~4 encoded columns (sexo binary, escol ordinal, edad ordinal +
intercept), the propensity model is much less powerful, keeping scores in the
moderate range.

Add `ks_threshold: float = 0.4` and `'ks_warning': bool` to output dict.

---

## 8. Change 7: Bayesian Covariance Regularization

### 8.1 Problem

MNLogit near-separation (even after category binning, some edge cases remain)
produces BSEs > 10 for some parameters, making the Laplace posterior overly
diffuse. Posterior draws wander far from the MLE.

### 8.2 Statistical basis

**Tierney, L. & Kadane, J. B. (1986).** "Accurate approximations for posterior
moments and marginal densities." *JASA*, 81(393), 82–86.
DOI: [10.1080/01621459.1986.10478240](https://doi.org/10.1080/01621459.1986.10478240)

> The Laplace approximation requires a positive-definite, well-conditioned
> Hessian. Ill-conditioned Hessians (from flat or near-singular likelihoods)
> produce unreliable approximations.

**Albert, A. & Anderson, J. A. (1984).** "On the existence of maximum likelihood
estimates in logistic regression models." *Biometrika*, 71(1), 1–10.
DOI: [10.1093/biomet/71.1.1](https://doi.org/10.1093/biomet/71.1.1)

> MLE exists and is unique only when no separating hyperplane exists (overlap
> condition). Under quasi-separation, at least one parameter diverges to
> infinity.

**Firth, D. (1993).** "Bias reduction of maximum likelihood estimates."
*Biometrika*, 80(1), 27–38.
DOI: [10.1093/biomet/80.1.27](https://doi.org/10.1093/biomet/80.1.27)

> Modifying the score function (equivalent to a Jeffreys prior) always yields
> finite estimates even under separation.

**Mansournia, M. A., Geroldinger, A., Greenland, S. & Heinze, G. (2018).**
"Separation in logistic regression: Causes, consequences, and control."
*American Journal of Epidemiology*, 187(4), 864–870.
DOI: [10.1093/aje/kwx299](https://doi.org/10.1093/aje/kwx299)

> Separation is most frequent with rare outcomes, many covariates, or strong
> effects — exactly the conditions in cross-tabulation cells. Penalized
> likelihood (Firth) is the recommended default solution.

### 8.3 Specification

After extracting `cov = res.cov_params()` and applying the existing PSD fix,
add two regularization steps:

**Diagonal shrinkage** (Ledoit-Wolf style):
```
target = median(diag(cov)) × I
cov_reg = (1 - α) × cov + α × target,  α = 0.1
```

**BSE capping**: for any parameter with BSE > 10, scale the corresponding
row/column of the covariance matrix:
```
scale_i = min(1, 10 / BSE_i)
cov_reg[i,:] *= scale_i; cov_reg[:,i] *= scale_i
```

This is a post-hoc approximation to Firth's penalized likelihood — it keeps
posterior draws near the MLE while preserving the correlation structure of
well-identified parameters.

---

## 9. Background References

### 9.1 Cross-survey bridging and CIA

**Rässler, S. (2002).** *Statistical Matching: A Frequentist Theory, Practical
Applications, and Alternative Bayesian Approaches*. Lecture Notes in Statistics
168, Springer.
DOI: [10.1007/978-1-4613-0053-3](https://doi.org/10.1007/978-1-4613-0053-3)

> Standard monograph on statistical matching. Under CIA, the joint distribution
> P(X,Y|Z) = P(X|Z) × P(Y|Z) can be estimated from separate surveys sharing
> common variables Z. The CIA is strong and often untestable.

**D'Orazio, M., Di Zio, M. & Scanu, M. (2006).** *Statistical Matching: Theory
and Practice*. Wiley.
DOI: [10.1002/0470023554](https://doi.org/10.1002/0470023554)

> When the common variables Z explain both target variables well, the CIA is more
> plausible. Bridge quality depends on R² of outcome models.

**Donatiello, G. et al. (2016).** "The role of the conditional independence
assumption in statistically matching income and consumption." *Statistical
Journal of the IAOS*, 32(4), 667–675.
DOI: [10.3233/SJI-161000](https://doi.org/10.3233/SJI-161000)

> Empirical evaluation: when the common block has strong predictive power for
> both targets, CIA is adequate. Weak predictive power leads to underestimation
> of the joint association.

### 9.2 Doubly robust estimation

**Robins, J. M., Rotnitzky, A. & Zhao, L. P. (1994).** "Estimation of regression
coefficients when some regressors are not always observed." *JASA*, 89(427),
846–866.
DOI: [10.1080/01621459.1994.10476818](https://doi.org/10.1080/01621459.1994.10476818)

> Introduces AIPW estimators: consistent if either the propensity or outcome
> model is correctly specified.

**Bang, H. & Robins, J. M. (2005).** "Doubly robust estimation in missing data
and causal inference models." *Biometrics*, 61(4), 962–972.
DOI: [10.1111/j.1541-0420.2005.00377.x](https://doi.org/10.1111/j.1541-0420.2005.00377.x)

### 9.3 Ecological inference

**Robinson, W. S. (1950).** "Ecological correlations and the behavior of
individuals." *American Sociological Review*, 15(3), 351–357.
DOI (reprint): [10.1093/ije/dyn357](https://doi.org/10.1093/ije/dyn357)

> Demonstrated that state-level correlation (0.77) can differ dramatically from
> individual-level correlation (0.20). Ecological correlations cannot be used to
> infer individual-level associations.

**King, G. (1997).** *A Solution to the Ecological Inference Problem*. Princeton
University Press.
DOI: [10.1515/9781400849208](https://doi.org/10.1515/9781400849208)

### 9.4 MRP

**Little, R. J. A. (1993).** "Post-stratification: A modeler's perspective."
*JASA*, 88(423), 1001–1012.
DOI: [10.1080/01621459.1993.10476368](https://doi.org/10.1080/01621459.1993.10476368)

**Gelman, A. & Little, T. C. (1997).** "Poststratification into many categories
using hierarchical logistic regression." *Survey Methodology*, 23(2), 127–135.
PDF: `docs/references/gelman_little_1997_mrp.pdf`

---

## 10. Downloaded Reference PDFs

All stored in `docs/references/`:

| File | Reference |
|------|-----------|
| `bergsma_2013_bias_corrected_V.pdf` | Bergsma (2013) — bias-corrected Cramér's V |
| `gelman_little_1997_mrp.pdf` | Gelman & Little (1997) — MRP foundations |
| `park_gelman_bafumi_2004_mrp.pdf` | Park, Gelman & Bafumi (2004) — MRP validation |
| `li_morgan_zaslavsky_2018_overlap_weights.pdf` | Li, Morgan & Zaslavsky (2018) — overlap weights |
| `li_morgan_zaslavsky_2018_overlap_weights_arxiv.pdf` | Same (arXiv version) |

---

## 11. Priority and Expected Impact

| # | Change | Impact | Effort | Estimators Fixed |
|---|--------|--------|--------|------------------|
| 1 | Category binning (max K = 5) | Very High | Low | All 6 |
| 2 | n\_sim 500 → 2000 | Medium | Trivial | Baseline, Bayesian, DR |
| 3 | Bayesian γ from mean table | High | Low | Bayesian |
| 4 | Residual: Bergsma V + CMH γ | High | Medium | Residual |
| 5 | MRP: bin cell\_cols | Medium | Low | MRP |
| 6 | DR: restrict propensity vars | Medium | Low | DR |
| 7 | Covariance regularization | Medium | Medium | Bayesian |

Implementation order: 1 → 2 → 3 → 4 → 5 → 6 → 7.
