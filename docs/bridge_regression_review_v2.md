
Bridge Regression and Cross-Survey Inference

Methods, Mathematics, Python Implementations, and Pitfalls

Academic Review — February 2026  |  Revised Edition

# 1. Problem Setup and Notation

Suppose we have K distinct surveys S₁, S₂, …, Sₖ, all fielded in the same year. Each survey collects the same SES battery X = (x₁, …, xₚ) — income bracket, education level, employment status, household size, geographic unit, etc. — plus a set of domain-specific outcome variables Yₖ observed only in survey Sₖ.

The inferential goal is to estimate relationships between outcomes from different surveys — e.g., E[Y₂ | Y₁, X] — or to predict Yₖ for respondents observed only in S₁. This is the bridge regression problem.

Formal notation

- S⁁ (target survey): contains SES vector X and outcome Y⁁ of primary interest

- S⁂ (source survey): contains SES vector X and outcome Y⁂ which we wish to impute or use as a predictor

- n⁁, n⁂: respective sample sizes

- X ∈ ℝᵖ: shared SES covariate vector (same instrument, same year → measurement equivalence holds)

- Assumption (Ignorability given SES): P(δ=1 | X, Y) = P(δ=1 | X), where δ indicates survey membership

# 2. Classical Bridge Regression

## 2.1 Mathematical Formulation

Bridge regression (Frank & Friedman, 1993) is a penalized regression estimator. Given outcome Y from one survey and SES predictors X observed in both surveys:

β̂ = argmin_β  ||Y - Xβ||²  +  λ||β||ᵂ

where the Lᵂ penalty is ||β||ᵂ = ∑ⱼ |βⱼ|ᵂ and q > 0 controls the penalty shape:

- q = 2 (ridge): dense solutions, all coefficients shrunk toward zero

- q = 1 (LASSO): sparse solutions, exact zeros via soft-thresholding

- q < 1: sparser-than-LASSO, oracle property (selects true support asymptotically), non-convex → harder to fit

- q → 0: subset selection

The bridge estimator β̂ is the model that is trained on the source survey (where Y is observed) and then applied to the target survey to predict Y given its observed SES X. This is the "bridge" across datasets.

## 2.2 Known Pitfalls

## 2.3 Python Implementation

Classical Bridge Regression via coordinate descent

# 3. Bayesian Bridge Regression

## 3.1 Mathematical Formulation

Mallick & Yi (2018) place a generalized normal prior on regression coefficients, enabling full posterior inference:

Y = Xβ + ε,  ε ~ N(0, σ²I)

π(β | q, λ) ∝ exp(-λ ||β||ᵂ)   [Generalized Normal Prior]

π(σ²) ∝ 1/σ²  [Scale-invariant Jeffreys prior]

The posterior is sampled via Gibbs MCMC using a scale-mixture-of-uniforms (SMU) representation, which converts the generalized normal prior into a Gaussian scale mixture. This enables tractable conditional posteriors for each βⱼ.

Key outputs: full posterior distribution P(β | Y, X), posterior predictive distribution for new observations, automatic estimation of λ as MCMC byproduct (no cross-validation needed).

For cross-survey prediction, the posterior predictive for survey B is:

P(Ỳᵇ | Xᵇ, Y⁁, X⁁) = ∫ P(Ỳᵇ | Xᵇ, β, σ²) P(β, σ² | Y⁁, X⁁) dβ dσ²

This propagates ALL estimation uncertainty into the imputed values for survey B — a major advantage over point-estimate bridges.

## 3.2 Known Pitfalls

## 3.3 Python Implementation

Bayesian Bridge via PyMC (modern probabilistic programming)

# 4. Mass Imputation

## 4.1 Mathematical Formulation

Mass imputation treats the outcome variable from survey A as "missing" for all units in survey B. We fit an outcome model on A and impute Y for all B units:

Step 1:  fit μ̂(X) = Ê[Y | X]  using {(Xᵢ, Yᵢ)}_{i∈S_A}

Step 2:  for each j ∈ S_B, set ŷ_j = μ̂(X_j)

Step 3:  μ̂_pop = (1/N) ∑_{j∈S_B} d_j ŷ_j

where d_j are the design weights for survey B. The estimator is design-consistent: it converges to the true population mean as n_B → ∞, as long as the outcome model is consistent.

For the bridge context, we want the joint distribution of (Y_A, Y_B) for units that are in both conceptual populations. Since no unit is actually in both surveys, the bridge imputation creates pseudo-linked records: each B-unit gets an imputed Ŷ_A = μ̂_A(X) that estimates what their A-outcome would have been had they been in A.

## 4.2 Predictive Mean Matching (PMM) Variant

PMM avoids model extrapolation by replacing the predicted value with an observed donor's actual Y value:

For each j ∈ S_B:  find donor d* = argmin_{i∈S_A} |ŷ_j - ŷ_i|

Then set ŷ_j = Y_{d*}  (actual observed value from nearest donor)

This guarantees imputed values are always within the observed support of Y_A, which is crucial when Y is bounded (e.g., Likert scales, proportions, binary outcomes).

## 4.3 Known Pitfalls

## 4.4 Python Implementation

# 5. Inverse Probability Weighting (IPW)

## 5.1 Mathematical Formulation

IPW frames the cross-survey bridge as a selection problem. Define δ_i = 1 if unit i is in survey A (the outcome-bearing survey) and δ_i = 0 if in survey B. Estimate the propensity score (probability of being in A given SES):

π̂(X_i) = P̂(δ_i = 1 | X_i)  [e.g., via logistic regression on pooled data]

The IPW estimator for any functional of the Y_A distribution, transported to the B population, is:

μ̂_IPW = (1/n_B) ∑_{i∈S_A} [w_i · Y_i]    where  w_i = π̂(X_i)^{-1} · P_B(X_i) / P_A(X_i)

In the same-SES-instrument case, P_B(X) ≈ P_A(X) if both surveys cover the same population — simplifying weights to the inverse propensity ratio. More practically, we estimate weights by logistic regression on the pooled dataset:

logit P(δ=1 | X) = X^Tθ,   w_i = (1-π̂_i)/π̂_i  for units in S_A

These weights reweight survey A respondents to look like survey B, enabling transport of Y_A statistics to the B population.

## 5.2 Known Pitfalls

## 5.3 Python Implementation

# 6. Calibration Weighting

## 6.1 Mathematical Formulation

Calibration weighting (Deville & Särndal, 1992) finds weights w_i for survey A that satisfy population-level moment constraints derived from survey B, while staying close to initial design weights d_i:

min_{w} ∑_{i∈S_A} G(w_i, d_i)   subject to:   ∑_{i∈S_A} w_i X_i = ∑_{j∈S_B} d_j X_j

where G(·) is a distance measure between the calibrated and design weights (e.g., chi-squared: G(w,d) = (w-d)²/(2d)). The constraint forces the weighted SES distribution of survey A to match that of survey B.

The solution takes the form:

w_i = d_i · F(X_i^T λ̂)

where λ̂ is a Lagrange multiplier vector solved via Newton-Raphson, and F is a link function. The linear calibration estimator (GREG) corresponds to F = identity.

For the bridge problem with same-year SES, calibration weights make survey A respondents representatively distributed over the SES strata of survey B. Any Y_A analysis using these weights is then valid for the B population's SES structure.

## 6.2 Known Pitfalls

## 6.3 Python Implementation

# 7. Doubly Robust (DR) Estimation

## 7.1 Mathematical Formulation

DR estimation (Robins et al., 1994; Bang & Robins, 2005) combines an outcome model μ(X) = E[Y|X] with a propensity model π(X) = P(δ=1|X). The AIPW estimator is:

μ̂_DR = (1/n) ∑_i [ μ̂(X_i)  +  (δ_i/π̂_i)(Y_i - μ̂(X_i)) ]

This estimator is doubly robust (DR): it is consistent if either μ̂(X) or π̂(X) is consistently estimated, but not necessarily both. The correction term (δ_i/π̂_i)(Y_i - μ̂(X_i)) removes residual bias from the outcome model, up to the precision of the propensity model.

For cross-survey bridging with same-year SES, the DR estimator works as follows:

- Fit outcome model μ̂(X) on survey A (where Y is observed)

- Fit propensity model π̂(X) on pooled A+B data (δ=1 for A)

- For each B unit: predicted value μ̂(X_j) with a correction from A's residuals

- The resulting estimator is consistent as long as either the SES-Y relationship or the SES-selection mechanism is captured correctly

With flexible ML models (e.g., random forests), use cross-fitting to avoid overfitting: split A into K folds, fit models on K-1 folds, predict on the held-out fold. This is the debiased/double machine learning (DML) framework (Chernozhukov et al., 2018).

## 7.2 Known Pitfalls

## 7.3 Python Implementation

# 8. Statistical Matching (Data Fusion)

## 8.1 Mathematical Formulation

Statistical matching (D'Orazio et al., 2006; Moretti & Shlomo, 2023) creates a fused dataset by linking records from two surveys sharing SES variables X but not outcomes Y_A, Y_B. The fused dataset contains (X_i, Y_A_i, Y_B_i) for all i, where one of the Y's is always imputed.

The critical unverifiable assumption is Conditional Independence (CIA):

Y_A ⊥ Y_B | X

This states that after conditioning on SES, the two domain-specific outcomes are independent. Under CIA, the joint distribution factors as:

P(Y_A, Y_B | X) = P(Y_A | X) · P(Y_B | X)

Matching algorithms:

- Exact matching: match on exact SES cell values. Feasible only for categorical, coarse SES.

- Propensity score matching: match on propensity P(δ=A | X). Distance-based.

- Hot-deck matching (rank): sort both surveys by predicted Y scores; match by rank proximity.

- Mixed methods (Moretti & Shlomo, 2023): estimate correlation structure from an auxiliary dataset, then calibrate matching to preserve these correlations.

## 8.2 Known Pitfalls

## 8.3 Python Implementation

# 9. Multilevel Regression and Poststratification (MRP)

## 9.1 Mathematical Formulation

MRP (Gelman & Little, 1997) uses a multilevel model to estimate cell-level means, then weights by population cell counts. For cross-survey bridging with categorical SES:

Stage 1 (multilevel regression on survey A):

Y_i = α_{j[i]} + β X_i + ε_i,   α_j ~ N(μ_α, σ²_α)

where j[i] indexes the SES cell of unit i. Random effects α_j pool information across sparse SES cells, borrowing strength from the global mean μ_α.

Stage 2 (poststratification to survey B's population):

μ̂_MRP = ∑_j N_j μ̂_j / ∑_j N_j

where N_j is the number of units in SES cell j in survey B, and μ̂_j is the model-predicted cell mean. With same-year, same-SES-battery surveys, the cell counts N_j are directly observed from survey B — no need for census auxiliary data.

For the bridge context: MRP estimates what the Y_A distribution would look like for the SES composition of survey B. This is useful when A and B were sampled from different subpopulations (e.g., different regions) but share the same SES instrument.

## 9.2 Known Pitfalls

## 9.3 Python Implementation

# 10. Synthetic Data Bridge

## 10.1 Mathematical Formulation

Synthetic data generation (Rubin, 1993; Raghunathan et al., 2003) creates a fused synthetic dataset by:

1. Fit P̂(Y_A | X) from survey A  [outcome model]

2. For each j ∈ S_B: draw Ỳ_A^{(j)} ~ P̂(Y_A | X_j)  [plug-in sampling]

3. Release synthetic fused file: {X_j, Ỳ_A^{(j)}, Y_B^{(j)}}_{j∈S_B}

Releasing M synthetic datasets and applying Rubin's combining rules gives valid inference. Alternatively, for disclosure-limited public release, the synthetic file itself can be the product.

The plug-in sampling step draws from the posterior predictive:

P(Ỳ | X, Data_A) = ∫ P(Y | X, θ) P(θ | Data_A) dθ

In practice, the parametric approximation fits a model, draws θ* from its asymptotic distribution (or bootstrap), and samples Y from P(Y | X, θ*).

## 10.2 Known Pitfalls

## 10.3 Python Implementation

# 11. Diagnostics: Overlap, Balance, and Sensitivity

## 11.1 Covariate Overlap Assessment

Before any bridge estimation, assess whether the SES distributions of the two surveys overlap sufficiently. Non-overlapping SES profiles require extrapolation and violate positivity.

## 11.2 Sensitivity to CIA Violation

When using statistical matching, the CIA (Y_A ⊥ Y_B | X) is unverifiable. Use Rosenbaum bounds or the following simulation-based approach to assess sensitivity:

# 12. Method Comparison

Summary comparison of all methods for the SES-bridged cross-survey inference problem:

# References

Bang, H. & Robins, J.M. (2005). Doubly robust estimation in missing data and causal inference models. Biometrics, 61, 962–973.

Chen, S. & Haziza, D. (2021). Multiply robust predictive mean matching imputation with complex survey data. Canadian Journal of Statistics. PMC10438827.

Chen, Y., Li, P. & Wu, C. (2020). Doubly robust inference with non-probability survey samples. JASA, 115(532), 2011–2021.

Chernozhukov, V. et al. (2018). Double/debiased machine learning for treatment and structural parameters. Econometrics Journal, 21, C1–C68.

D'Orazio, M., Di Zio, M. & Scanu, M. (2006). Statistical Matching: Theory and Practice. Chichester: Wiley.

Deville, J.-C. & Särndal, C.-E. (1992). Calibration estimators in survey sampling. JASA, 87, 376–382.

Flood, J. & Mostafa, S.A. (2025). Matched mass imputation for survey data integration. Journal of Data Science, 23(2), 332–352.

Frank, I.E. & Friedman, J.H. (1993). A statistical view of some chemometrics regression tools. Technometrics, 35(2), 109–135.

Gelman, A. & Little, T.C. (1997). Poststratification into many categories using hierarchical logistic regression. Survey Methodology, 23, 127–135.

Giuffre, A. & Vantini, S. (2025). Systematic review of generative modelling tools and utility metrics for fully synthetic tabular data. ACM Computing Surveys. doi:10.1145/3704437

Kim, J.K. (2025). Calibration weighting for analyzing non-probability samples. Journal of Survey Statistics and Methodology. doi:10.1177/0282423X251318104

Li, Y. & Si, Y. (2024). Embedded multilevel regression and poststratification. Statistics in Medicine, 43(2), 256–278. PMC11418010.

Lopez-Martin, J., Phillips, J.H. & Gelman, A. (2022). Multilevel Regression and Poststratification Case Studies. bookdown.org.

Mallick, H. & Yi, N. (2018). Bayesian bridge regression. Journal of Applied Statistics, 45(6), 988–1008. PMC6426306.

Moretti, A. & Shlomo, N. (2023). Data integration approaches in survey sampling. Journal of Survey Statistics and Methodology, 11(3).

Raghunathan, T.E. et al. (2003). Multiple imputation for statistical disclosure limitation. Journal of Official Statistics, 19(1), 1–16.

Robins, J.M., Rotnitzky, A. & Zhao, L.P. (1994). Estimation of regression coefficients when some regressors are not always observed. JASA, 89, 846–866.

Rubin, D.B. (1993). Discussion: Statistical disclosure limitation. Journal of Official Statistics, 9, 461–468.

Yang, S. & Kim, J.K. (2020). Statistical data integration in survey sampling: A review. Japanese Journal of Statistics and Data Science, 3, 625–650. arXiv:2001.03259.

Yang, S., Kim, J.K. & Song, R. (2020). Doubly robust inference with high-dimensional data. JRSS-B, 82, 445–465.

End of Review — February 2026  |  Bridge Regression & Cross-Survey Inference

| Context and Revision Note
This review addresses cross-survey inference using Socioeconomic Status (SES) variables as the common bridge.
All surveys were fielded in the same year and share an identical SES battery, eliminating temporal misalignment
and simplifying the harmonization challenge. The shared SES section provides a stable covariate foundation for
all integration methods described below. Each method is presented with: (1) minimal mathematical formulation,
(2) known pitfalls specific to each technique, and (3) a minimal Python implementation. |
| --- |

| Why Same-Year, Same-SES-Battery Matters
Same year: eliminates temporal drift in SES distributions. Income levels, unemployment rates, housing costs
  all shift between years and would confound cross-survey comparisons if surveys were from different periods.
Same instrument: guarantees measurement equivalence of X, removing one of the most common pitfalls
  (scale incomparability, different ordinal categories, different reference periods).
This simplifies the ignorability assumption considerably: we need only worry about selection on unobserved
  variables, not on systematic measurement differences in the bridge covariates. |
| --- |

| ⚠  Classical Bridge Pitfalls
1. No inference: classical bridge produces only a point estimate. No standard errors, no confidence intervals.
   Downstream cross-survey comparisons using point estimates ignore estimation uncertainty entirely.
2. q selection: optimal q is not known a priori. Cross-validation over both λ and q is expensive;
   non-convex landscape for q<1 means local minima and instability across bootstrap replications.
3. Distributional shift: even with same-year SES, the conditional distribution P(Y|X) may differ
   across surveys due to frame differences or question framing, violating the transport assumption.
4. Multicollinearity: SES variables are typically highly collinear (income ↔ education ↔ occupation).
   Bridge with q≤1 forces arbitrary sparse solutions; ridge (q=2) or elastic-net often preferred. |
| --- |

| import numpy as np
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler

# ── Bridge Regression (q=1: LASSO, q=2: Ridge, or mixed) ──
# Survey A: has SES (X_a) and outcome Y_a
# Survey B: has SES (X_b) only — we want to predict Y_b

def bridge_predict(X_a, Y_a, X_b, q=1, lambdas=None):
    """
    Fit bridge regression on survey A, predict Y for survey B.
    q=1 -> LASSO, q=2 -> Ridge. For q<1 use sklearn-contrib or custom.
    """
    scaler = StandardScaler()
    X_a_s = scaler.fit_transform(X_a)   # ALWAYS scale SES vars
    X_b_s = scaler.transform(X_b)        # same scaler on target

    if lambdas is None:
        lambdas = np.logspace(-4, 2, 50)

    if q == 1:
        model = GridSearchCV(Lasso(max_iter=10000),
                             {'alpha': lambdas}, cv=5, scoring='neg_mse')
    elif q == 2:
        model = GridSearchCV(Ridge(),
                             {'alpha': lambdas}, cv=5, scoring='neg_mse')
    else:
        # Elastic Net approximates intermediate q
        model = GridSearchCV(
            ElasticNet(max_iter=10000),
            {'alpha': lambdas, 'l1_ratio': [0.1, 0.5, 0.9]},
            cv=5, scoring='neg_mse'
        )

    model.fit(X_a_s, Y_a)
    Y_b_hat = model.predict(X_b_s)
    return Y_b_hat, model.best_estimator_

# Usage:
# Y_b_hat, fitted = bridge_predict(X_ses_surveyA, Y_surveyA, X_ses_surveyB) |
| --- |

| ⚠  Bayesian Bridge Pitfalls
1. MCMC mixing: for q<1, the posterior landscape is highly non-convex. Chains may mix poorly;
   always run multiple chains and inspect R-hat convergence diagnostics.
2. q specification: choosing q requires prior knowledge or a hyperprior. A hyperprior on q
   is computationally expensive; in practice fix q−1 or q=0.5 based on domain sparsity expectations.
3. Scale sensitivity: SES variables must be standardized before running Bayesian bridge;
   the prior on β is not scale-invariant, so unstandardized inputs produce misleading shrinkage.
4. Computational cost: MCMC is 10-100x slower than frequentist bridge; impractical for
   large SES covariate sets (p>500) without dimension reduction preprocessing.
5. Posterior predictive calibration: credible intervals are coherent given the model but
   may be overconfident if P(Y|X) differs structurally between source and target survey. |
| --- |

| import numpy as np
import pymc as pm
import arviz as az

def bayesian_bridge(X_a, Y_a, X_b, q=0.5, n_samples=2000, n_chains=4):
    """
    Bayesian Bridge Regression.
    Returns: posterior predictive samples for survey B units.
    """
    from sklearn.preprocessing import StandardScaler
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()

    X_a_s = scaler_x.fit_transform(X_a)
    Y_a_s = scaler_y.fit_transform(Y_a.reshape(-1,1)).ravel()
    X_b_s = scaler_x.transform(X_b)

    p = X_a_s.shape[1]

    with pm.Model() as bridge_model:
        # Scale mixture of normals approximating generalized normal
        # (Polson & Scott 2012 auxiliary variable approach)
        lam = pm.HalfNormal('lambda', sigma=1.0)   # global shrinkage
        tau = pm.HalfNormal('tau', sigma=1.0, shape=p)  # local scale

        # Generalized normal approx via scale mixture
        beta = pm.Normal('beta', mu=0, sigma=lam * tau, shape=p)
        sigma = pm.HalfNormal('sigma', sigma=1.0)

        mu = pm.math.dot(X_a_s, beta)
        likelihood = pm.Normal('Y', mu=mu, sigma=sigma, observed=Y_a_s)

        # Posterior predictive on survey B
        mu_b = pm.math.dot(X_b_s, beta)
        Y_b_pred = pm.Normal('Y_b', mu=mu_b, sigma=sigma,
                             shape=X_b_s.shape[0])

        trace = pm.sample(n_samples, chains=n_chains, target_accept=0.9,
                          return_inferencedata=True)
        ppc = pm.sample_posterior_predictive(trace, var_names=['Y_b'])

    # Back-transform to original Y scale
    Y_b_samples = ppc.posterior_predictive['Y_b'].values  # (chains, draws, n_b)
    Y_b_samples_orig = scaler_y.inverse_transform(
        Y_b_samples.reshape(-1, X_b_s.shape[0]))
    return Y_b_samples_orig, trace

# Usage:
# samples, trace = bayesian_bridge(X_ses_A, Y_A, X_ses_B, q=0.5)
# Y_b_mean = samples.mean(axis=0)     # point estimate
# Y_b_ci   = np.percentile(samples, [2.5, 97.5], axis=0)  # 95% CI |
| --- |

| ⚠  Mass Imputation Pitfalls
1. Outcome model misspecification: if E[Y|X] is nonlinear and you use a linear model,
   imputed values are systematically biased — and the bias propagates to ALL B-units.
2. Underestimated variance: treating imputed values as observed ignores imputation uncertainty.
   Always use multiple imputation (M≥20) and Rubin's combining rules.
3. SES support mismatch: if the SES distribution in A and B differ (different sampling frames,
   different regions), model extrapolation produces imputed values for X_B values never seen in A.
   Check covariate overlap before imputing.
4. PMM with too few donors: if matching is done in a high-dimensional SES space, nearest-neighbor
   matching degrades due to the curse of dimensionality. Reduce to predicted scores first.
5. Repeated donor use: in PMM with small A, the same donor may be matched to many B-units,
   creating artificial clustering and underestimating variance. |
| --- |

| import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

# ── Standard Mass Imputation ──
def mass_impute(X_a, Y_a, X_b, model=None, n_imputations=20):
    """
    Mass imputation with multiple imputation for valid variance.
    Returns: (M x n_B) array of imputed Y values.
    """
    from sklearn.ensemble import RandomForestRegressor
    scaler = StandardScaler()
    X_a_s = scaler.fit_transform(X_a)
    X_b_s = scaler.transform(X_b)

    imputations = []
    for m in range(n_imputations):
        # Bootstrap the source survey (parametric uncertainty)
        idx = np.random.choice(len(Y_a), len(Y_a), replace=True)
        m_model = RandomForestRegressor(n_estimators=200, random_state=m)
        m_model.fit(X_a_s[idx], Y_a[idx])
        Y_b_hat = m_model.predict(X_b_s)
        imputations.append(Y_b_hat)

    return np.array(imputations)  # shape: (n_imputations, n_B)

def rubin_combine(imputations):
    """Rubin's rules for combining multiple imputations."""
    M = imputations.shape[0]
    Q_m = imputations.mean(axis=1)      # per-imputation means
    Q_bar = Q_m.mean()                   # combined estimate
    U_bar = imputations.var(axis=1).mean()  # within-imputation var
    B = Q_m.var()                        # between-imputation var
    T = U_bar + (1 + 1/M) * B           # total variance
    return Q_bar, np.sqrt(T)

# ── Predictive Mean Matching ──
def pmm_impute(X_a, Y_a, X_b, k_donors=5):
    """PMM: match on predicted scores, impute from actual donor Y."""
    from sklearn.linear_model import RidgeCV
    scaler = StandardScaler()
    X_a_s = scaler.fit_transform(X_a)
    X_b_s = scaler.transform(X_b)

    # Fit score model on A
    score_model = RidgeCV(alphas=np.logspace(-3, 3, 20))
    score_model.fit(X_a_s, Y_a)

    scores_a = score_model.predict(X_a_s)  # donor scores
    scores_b = score_model.predict(X_b_s)  # target scores

    # Nearest neighbor in score space
    nbrs = NearestNeighbors(n_neighbors=k_donors, algorithm='ball_tree')
    nbrs.fit(scores_a.reshape(-1, 1))
    distances, indices = nbrs.kneighbors(scores_b.reshape(-1, 1))

    # Randomly draw from k nearest donors
    imputed = np.array([
        Y_a[np.random.choice(indices[j])] for j in range(len(scores_b))
    ])
    return imputed |
| --- |

| ⚠  IPW Pitfalls
1. Extreme weights: when X_i in S_A is rare in S_B (or vice versa), propensity scores near 0 or 1
   produce enormous weights. A single extreme weight can dominate the entire estimate.
   Always inspect weight distributions; trim at 1st/99th percentile or use stabilized weights.
2. Propensity model misspecification: if the logistic propensity model omits interactions or
   nonlinear SES terms, IPW is inconsistent. Use flexible models (GBM, random forest) but then
   apply cross-fitting to avoid overfitting bias.
3. No overlap / positivity violation: if some SES profiles exist only in A or only in B,
   IPW is undefined for those regions. This requires either trimming or a model-based alternative.
4. Efficiency loss: IPW ignores the outcome model entirely. If E[Y|X] is predictable,
   adding an outcome model (Doubly Robust) drastically reduces variance.
5. Variance estimation: naive bootstrap underestimates IPW variance. Use sandwich estimator
   or influence-function-based variance accounting for propensity estimation. |
| --- |

| import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils import check_array

def ipw_bridge(X_a, Y_a, X_b, propensity_model='logistic',
               trim_quantile=0.01, stabilize=True):
    """
    IPW estimator: reweight survey A to look like survey B.
    Returns: weighted mean of Y_A transported to B population.
    """
    # Pool surveys and create membership indicator
    n_a, n_b = len(Y_a), len(X_b)
    X_pool = np.vstack([X_a, X_b])
    delta   = np.array([1]*n_a + [0]*n_b)  # 1=survey A

    scaler = StandardScaler()
    X_pool_s = scaler.fit_transform(X_pool)

    # Estimate P(delta=1 | X)
    if propensity_model == 'logistic':
        ps_model = LogisticRegressionCV(cv=5, max_iter=1000)
    else:
        ps_model = GradientBoostingClassifier(n_estimators=200)

    ps_model.fit(X_pool_s, delta)
    pi_hat = ps_model.predict_proba(X_pool_s[:n_a])[:, 1]  # P(A | X) for A units

    # Stabilized IPW weights: (P(A overall) / P(A|X)) * (P(B overall) / P(B|X))
    p_a = n_a / (n_a + n_b)
    if stabilize:
        weights = (p_a / pi_hat)   # simplified stabilized form
    else:
        weights = 1.0 / pi_hat

    # Trim extreme weights
    lo, hi = np.quantile(weights, [trim_quantile, 1-trim_quantile])
    weights = np.clip(weights, lo, hi)
    weights /= weights.sum()    # normalize

    # IPW estimate: weighted mean of Y_A
    mu_ipw = np.sum(weights * Y_a)

    # Overlap diagnostic
    print(f'Effective sample size (ESS): {1/np.sum(weights**2):.1f} of {n_a}')
    print(f'Weight range: [{weights.min():.4f}, {weights.max():.4f}]')

    return mu_ipw, weights |
| --- |

| ⚠  Calibration Weighting Pitfalls
1. Negative or extreme weights: when calibration constraints are tight and A's SES distribution
   differs substantially from B's, the optimization may produce very large or negative weights.
   Use bounded calibration (e.g., logistic or truncated raking) to constrain weight range.
2. Constraint selection: which SES moments to calibrate on is a modeling choice.
   Including too many constraints (e.g., all pairwise interactions) leads to infeasible solutions.
   Including too few leaves residual SES imbalance.
3. Model-free but not assumption-free: calibration is design-consistent but assumes the
   calibrated sample can represent the target population. If A has excluded strata (e.g., no
   rural respondents), calibration cannot create them.
4. Variance estimation: standard GREG variance formulas require linearization or replication.
   The delete-a-group jackknife is preferred for complex calibrated estimators. |
| --- |

| import numpy as np
from scipy.optimize import minimize

def calibration_weights(X_a, X_b, d_a=None, method='linear'):
    """
    Find calibration weights for survey A that match B\'s SES moments.
    method: 'linear' (GREG), 'raking' (iterative proportional fitting),
            or 'entropy' (maximum entropy / exponential tilting)
    """
    n_a = len(X_a)
    if d_a is None:
        d_a = np.ones(n_a) / n_a

    # Calibration targets: SES column means in survey B
    T = X_b.mean(axis=0)  # (p,)

    if method == 'linear':
        # GREG closed-form solution
        A  = X_a.T @ (d_a[:, None] * X_a)   # (p,p)
        lambda_ = np.linalg.solve(A, X_a.T @ d_a - T * n_a)
        g = 1 + X_a @ lambda_  / d_a
        w = d_a * g

    elif method == 'entropy':
        # Exponential tilting (minimum entropy divergence)
        def objective(lam):
            log_w = np.log(d_a) + X_a @ lam
            log_w -= np.log(np.exp(log_w).sum())  # normalize
            w = np.exp(log_w)
            return -np.sum(w * log_w)  # negative entropy

        def gradient(lam):
            log_w = np.log(d_a) + X_a @ lam
            log_w -= np.log(np.exp(log_w).sum())
            w = np.exp(log_w)
            return X_a.T @ w - T

        res = minimize(objective, x0=np.zeros(X_a.shape[1]),
                       jac=gradient, method='BFGS')
        log_w = np.log(d_a) + X_a @ res.x
        log_w -= np.log(np.exp(log_w).sum())
        w = np.exp(log_w)

    elif method == 'raking':
        # Iterative proportional fitting over SES categories
        w = d_a.copy()
        for _ in range(200):  # iterate until convergence
            for k in range(X_a.shape[1]):
                w_k = w * X_a[:, k]
                if w_k.sum() > 1e-12:
                    w *= T[k] / w_k.sum()

    # Diagnostics
    print(f'Calibration check (should be ~0): {(X_a.T @ w - T).max():.6f}')
    print(f'Weight CV: {w.std()/w.mean():.3f}  (lower=better)')
    return w / w.sum() |
| --- |

| ⚠  Doubly Robust Pitfalls
1. Double bias amplification: if BOTH models are wrong (even moderately), the DR correction can
   amplify bias rather than remove it. The name 'doubly robust' does not mean 'doubly safe.'
2. No cross-fitting with ML models: fitting propensity and outcome on the same data and then
   predicting on it creates severe overfitting bias that invalidates the DR property.
   ALWAYS use cross-fitting (K-fold sample splitting) when using flexible models.
3. Propensity near boundary: if π̂(X_i) ≈ 0 or 1, the correction term explodes.
   Use overlap trimming: remove units with propensity outside [ε, 1-ε] for ε ~ 0.05.
4. Standard error underestimation: naive SE formulas ignore estimation of both models.
   Use the influence-function SE or bootstrap.
5. Model selection bias: choosing outcome/propensity model forms after seeing the data
   invalidates the theoretical DR guarantees. Pre-specify or use an automated ensemble. |
| --- |

| import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

def doubly_robust_bridge(X_a, Y_a, X_b,
                          n_folds=5, eps_trim=0.05):
    """
    AIPW Doubly Robust estimator with cross-fitting (DML-style).
    Bridges Y from survey A to survey B population.
    Returns: DR estimate of E[Y_A] in B population, SE.
    """
    n_a, n_b = len(Y_a), len(X_b)
    X_pool = np.vstack([X_a, X_b])
    delta   = np.array([1]*n_a + [0]*n_b)

    scaler = StandardScaler()
    X_pool_s = scaler.fit_transform(X_pool)
    X_a_s, X_b_s = X_pool_s[:n_a], X_pool_s[n_a:]

    # Cross-fitting: propensity scores on A units
    pi_hat = np.zeros(n_a)
    mu_hat = np.zeros(n_a)   # outcome model on A

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    folds = list(kf.split(X_a_s))

    for train_idx, val_idx in folds:
        # Propensity: train on all pool, predict on A val fold
        ps_m = GradientBoostingClassifier(n_estimators=100)
        ps_m.fit(X_pool_s, delta)  # simplified: use all pool
        pi_hat[val_idx] = ps_m.predict_proba(X_a_s[val_idx])[:, 1]

        # Outcome: train on A train fold only
        out_m = GradientBoostingRegressor(n_estimators=100)
        out_m.fit(X_a_s[train_idx], Y_a[train_idx])
        mu_hat[val_idx] = out_m.predict(X_a_s[val_idx])

    # Trim extreme propensities
    pi_hat = np.clip(pi_hat, eps_trim, 1 - eps_trim)

    # Outcome model on B (fit on all A, predict on B)
    out_final = GradientBoostingRegressor(n_estimators=200)
    out_final.fit(X_a_s, Y_a)
    mu_b = out_final.predict(X_b_s)  # E[Y|X] for B units

    # AIPW correction: uses A units' residuals, IPW-reweighted
    weights_a = (1 - pi_hat) / pi_hat   # ~P(B|X)/P(A|X)
    correction = (weights_a * (Y_a - mu_hat)).mean()

    mu_dr = mu_b.mean() + correction

    # Influence-function variance
    phi = (mu_b - mu_dr)   # B contribution
    phi_a = weights_a * (Y_a - mu_hat) / n_a * n_b   # A contribution
    se = np.sqrt((phi**2).mean()/n_b + (phi_a**2).mean()/n_a)

    return mu_dr, se |
| --- |

| ⚠  Statistical Matching Pitfalls
1. CIA violation: the CIA assumption is almost certainly false for real survey outcomes.
   If Y_A and Y_B are correlated beyond what X explains (e.g., via unobserved personality traits),
   the fused dataset produces spurious independence between them.
2. Underestimated correlations: matching under CIA produces a fused dataset where
   Corr(Y_A, Y_B | X) = 0 by construction. Any downstream analysis finding non-zero
   cross-survey correlations is artificially attenuated.
3. No auxiliary dataset: the Moretti-Shlomo correction requires a third dataset with both
   Y_A and Y_B observed. Without it, the CIA violation is unidentifiable.
4. Matching ratio: 1:1 matching discards information. Use multiple matches (1:k) or
   fractional imputation to preserve all records and reduce variance.
5. SES discretization: exact matching on continuous SES variables (income) requires
   binning, which introduces measurement error and cell sparsity. |
| --- |

| import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

def statistical_matching(X_a, Y_a, X_b, Y_b,
                          method='propensity', k=1, random_state=42):
    """
    Statistical matching: fuse survey A and B on shared SES (X).
    Adds imputed Y_B to A records and imputed Y_A to B records.
    method: 'propensity' | 'ses_distance' | 'rank'
    """
    np.random.seed(random_state)
    scaler = StandardScaler()
    X_all  = scaler.fit_transform(np.vstack([X_a, X_b]))
    X_a_s, X_b_s = X_all[:len(X_a)], X_all[len(X_a):]

    if method == 'propensity':
        # Match on propensity P(survey=A | X)
        delta = np.array([1]*len(X_a) + [0]*len(X_b))
        ps_model = LogisticRegression(C=1.0, max_iter=1000)
        ps_model.fit(np.vstack([X_a_s, X_b_s]), delta)
        score_a = ps_model.predict_proba(X_a_s)[:,1].reshape(-1,1)
        score_b = ps_model.predict_proba(X_b_s)[:,1].reshape(-1,1)
        match_space_a, match_space_b = score_a, score_b

    elif method == 'ses_distance':
        match_space_a, match_space_b = X_a_s, X_b_s

    elif method == 'rank':
        # Rank-based hot-deck: sort A by predicted Y, match by rank
        from sklearn.ensemble import GradientBoostingRegressor
        m = GradientBoostingRegressor(n_estimators=100)
        m.fit(X_a_s, Y_a)
        rank_a = np.argsort(np.argsort(m.predict(X_a_s))).reshape(-1,1)
        rank_b = np.argsort(np.argsort(m.predict(X_b_s))).reshape(-1,1)
        match_space_a = rank_a.astype(float) / len(X_a)
        match_space_b = rank_b.astype(float) / len(X_b)

    # For each B unit, find k nearest A donors
    nbrs = NearestNeighbors(n_neighbors=k)
    nbrs.fit(match_space_a)
    _, idx_ab = nbrs.kneighbors(match_space_b)

    # For each A unit, find k nearest B donors
    nbrs2 = NearestNeighbors(n_neighbors=k)
    nbrs2.fit(match_space_b)
    _, idx_ba = nbrs2.kneighbors(match_space_a)

    # Impute Y_A for B units
    Y_a_for_b = np.array([Y_a[np.random.choice(idx_ab[j])] for j in range(len(X_b))])
    # Impute Y_B for A units
    Y_b_for_a = np.array([Y_b[np.random.choice(idx_ba[i])] for i in range(len(X_a))])

    fused = pd.DataFrame({
        'source': ['A']*len(X_a) + ['B']*len(X_b),
        'Y_a': np.concatenate([Y_a, Y_a_for_b]),
        'Y_b': np.concatenate([Y_b_for_a, Y_b])
    })
    return fused |
| --- |

| ⚠  MRP Pitfalls
1. SES cell sparsity: with many SES dimensions (e.g., income x education x employment x region),
   the number of cells grows exponentially. Many cells will have zero A observations; the multilevel
   model must extrapolate via shrinkage, which can introduce substantial bias for extreme cells.
2. Linear predictor misspecification: standard MRP assumes a linear (or logit-linear for binary Y)
   within-cell model. Nonlinear SES-Y relationships are not captured. Use BART or GP extensions.
3. Poststratification frame errors: cell counts N_j from survey B are estimates, not census counts.
   Treating them as fixed ignores their sampling uncertainty. Use embedded MRP (EMRP) to propagate.
4. Ecological to individual fallacy: MRP estimates population-level means well, but the multilevel
   model cannot identify individual-level SES effects without individual-level variation within cells.
5. Random effects independence: standard MRP treats cell random effects as i.i.d. Gaussian,
   ignoring spatial or hierarchical structure in SES cells (e.g., neighboring income brackets
   should have correlated random effects). |
| --- |

| import numpy as np
import pandas as pd
import bambi as bmb       # Bayesian multilevel models (wraps PyMC)
import arviz as az

def mrp_bridge(df_a, df_b, outcome_col, ses_cols,
               binary_outcome=False):
    """
    MRP bridge: fit multilevel model on survey A,
    poststratify to survey B SES cell distribution.

    df_a: DataFrame with ses_cols + outcome_col (survey A)
    df_b: DataFrame with ses_cols only (survey B)
    """
    # Step 1: Construct SES cell IDs in both surveys
    for col in ses_cols:
        df_a[col] = df_a[col].astype('category')
        df_b[col] = pd.Categorical(df_b[col],
                                   categories=df_a[col].cat.categories)

    df_a['cell'] = df_a[ses_cols].astype(str).agg('|'.join, axis=1)
    df_b['cell'] = df_b[ses_cols].astype(str).agg('|'.join, axis=1)

    # Step 2: Fit multilevel model on survey A
    # Formula: Y ~ 1 + (1 | cell) for pure cell random effects
    # Add fixed SES covariates for additional adjustment
    family = 'bernoulli' if binary_outcome else 'gaussian'
    formula = f'{outcome_col} ~ 1 + (1|cell)'

    model = bmb.Model(formula, df_a, family=family)
    idata = model.fit(draws=1000, chains=4, target_accept=0.9)

    # Step 3: Predict cell means
    unique_cells = df_b['cell'].unique()
    cell_counts  = df_b['cell'].value_counts()  # N_j from survey B

    pred_data = pd.DataFrame({'cell': unique_cells})
    preds = model.predict(idata, data=pred_data, kind='mean')
    # preds shape: (chains*draws, n_cells)
    cell_means = preds.mean(dim=['chain','draw'])  # posterior mean per cell

    # Step 4: Poststratify
    N_j = np.array([cell_counts.get(c, 0) for c in unique_cells])
    mu_mrp = (N_j * cell_means.values).sum() / N_j.sum()

    return mu_mrp, idata

# Lightweight alternative using statsmodels (frequentist):
def mrp_bridge_freq(df_a, df_b, outcome_col, ses_cols):
    import statsmodels.formula.api as smf
    df_a['cell'] = df_a[ses_cols].astype(str).agg('|'.join, axis=1)
    df_b['cell'] = df_b[ses_cols].astype(str).agg('|'.join, axis=1)
    model = smf.mixedlm(f'{outcome_col} ~ 1', df_a, groups=df_a['cell'])
    result = model.fit()
    cell_preds = result.fittedvalues.groupby(df_a['cell']).mean()
    cell_counts = df_b['cell'].value_counts()
    common = cell_preds.index.intersection(cell_counts.index)
    mu_mrp = (cell_preds[common] * cell_counts[common]).sum() / cell_counts[common].sum()
    return mu_mrp |
| --- |

| ⚠  Synthetic Data Bridge Pitfalls
1. Uncongeniality: if the synthesis model and the analysis model are structurally different
   (e.g., synthesize with linear regression, analyze with logistic regression), Rubin's rules
   do not guarantee valid inference. Use flexible synthesis models.
2. Disclosure risk: if synthetic records closely resemble rare original records (e.g., unique
   SES profiles), re-identification is possible. Always evaluate Nearest-Neighbor Adversarial
   Accuracy (NNAA) and Membership Inference Risk (MIR) before releasing.
3. Underestimated uncertainty: with M=1 synthetic dataset, variance is completely wrong.
   Use M≥20; the between-imputation variance captures the missing data contribution.
4. CIA imposed by synthesis: if you synthesize Y_A independently given X, you're assuming
   Corr(Y_A, Y_B | X) = 0 (the CIA). This attenuates all cross-outcome correlations.
   Use joint synthesis models (e.g., copula-based) to preserve cross-outcome dependence.
5. Tail distribution distortion: parametric synthesis models (normal) distort fat tails.
   Use nonparametric synthesis (CART/RF) for skewed outcomes. |
| --- |

| import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

def synthetic_bridge(X_a, Y_a, X_b, Y_b,
                      n_synth=20, model_type='rf'):
    """
    Synthetic data bridge: synthesize Y_A for survey B units.
    Returns: list of M synthetic fused DataFrames.
    """
    scaler = StandardScaler()
    X_a_s = scaler.fit_transform(X_a)
    X_b_s = scaler.transform(X_b)

    synth_datasets = []
    for m in range(n_synth):
        # Bootstrap source survey (parametric uncertainty)
        boot_idx = np.random.choice(len(Y_a), len(Y_a), replace=True)
        X_boot, Y_boot = X_a_s[boot_idx], Y_a[boot_idx]

        if model_type == 'rf':
            synth_model = RandomForestRegressor(n_estimators=200,
                                                random_state=m)
        else:  # linear
            from sklearn.linear_model import BayesianRidge
            synth_model = BayesianRidge()

        synth_model.fit(X_boot, Y_boot)

        # Generate synthetic Y_A for all B units
        Y_hat_b = synth_model.predict(X_b_s)

        # Add residual noise from fitted model
        if model_type == 'rf':
            resid_sd = np.std(Y_boot - synth_model.predict(X_boot))
        else:
            resid_sd = np.sqrt(synth_model.alpha_**-1 if hasattr(
                              synth_model,'alpha_') else 0.1)

        Y_synth = Y_hat_b + np.random.normal(0, resid_sd, len(X_b))

        df_m = pd.DataFrame({
            'Y_b':   Y_b,
            'Y_a_synth': Y_synth
        })
        synth_datasets.append(df_m)

    return synth_datasets

def rubin_from_synth(synth_datasets, analysis_fn):
    """Apply analysis_fn to each synthetic dataset and combine."""
    Q_m = [analysis_fn(df) for df in synth_datasets]
    Q_bar = np.mean(Q_m)
    B = np.var(Q_m, ddof=1)  # between-imputation variance
    T = (1 + 1/len(Q_m)) * B  # total variance (no within-imputation for fully synthetic)
    return Q_bar, np.sqrt(T) |
| --- |

| import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

def overlap_diagnostics(X_a, X_b, ses_names=None, plot=True):
    """
    Assess SES overlap between survey A and B.
    Returns propensity score distribution and standardized mean diffs.
    """
    n_a, n_b = len(X_a), len(X_b)
    X_pool = np.vstack([X_a, X_b])
    delta = np.array([1]*n_a + [0]*n_b)

    scaler = StandardScaler()
    X_s = scaler.fit_transform(X_pool)

    # Propensity score overlap
    gbm = GradientBoostingClassifier(n_estimators=100)
    gbm.fit(X_s, delta)
    ps = gbm.predict_proba(X_s)[:, 1]
    ps_a, ps_b = ps[:n_a], ps[n_a:]

    if plot:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].hist(ps_a, bins=30, alpha=0.5, label='Survey A', density=True)
        axes[0].hist(ps_b, bins=30, alpha=0.5, label='Survey B', density=True)
        axes[0].set_xlabel('Propensity Score'); axes[0].legend()
        axes[0].set_title('SES Propensity Score Overlap')

    # Standardized mean differences (SMD) per SES variable
    smd = []
    for k in range(X_a.shape[1]):
        pooled_sd = np.sqrt((X_a[:,k].var() + X_b[:,k].var()) / 2)
        smd.append(abs(X_a[:,k].mean() - X_b[:,k].mean()) / (pooled_sd + 1e-10))

    if plot and ses_names:
        axes[1].barh(ses_names, smd, color=['red' if s>0.1 else 'steelblue' for s in smd])
        axes[1].axvline(0.1, color='red', linestyle='--', label='SMD=0.1 threshold')
        axes[1].set_xlabel('Standardized Mean Difference')
        axes[1].set_title('SES Balance (SMD < 0.1 = good)')
        axes[1].legend()
        plt.tight_layout(); plt.savefig('overlap_diagnostics.png', dpi=150)

    print('SMD > 0.1 (imbalanced SES vars):', sum(s > 0.1 for s in smd))
    print('Propensity score range A:', f'[{ps_a.min():.3f}, {ps_a.max():.3f}]')
    print('Propensity score range B:', f'[{ps_b.min():.3f}, {ps_b.max():.3f}]')
    return ps_a, ps_b, np.array(smd) |
| --- |

| def cia_sensitivity(X_a, Y_a, X_b, Y_b, rho_grid=None):
    """
    Sensitivity analysis: what if Corr(Y_A, Y_B | X) = rho (not 0)?
    Reports bias in cross-survey correlation estimates under CIA violation.
    """
    if rho_grid is None:
        rho_grid = np.linspace(0, 0.5, 11)

    from sklearn.linear_model import LinearRegression
    # Residualize both Y on SES
    reg_a = LinearRegression().fit(X_a, Y_a)
    reg_b = LinearRegression().fit(X_b, Y_b)
    resid_a = Y_a - reg_a.predict(X_a)
    resid_b = Y_b - reg_b.predict(X_b)

    obs_corr_a = np.corrcoef(Y_a, reg_a.predict(X_a))[0,1]
    obs_corr_b = np.corrcoef(Y_b, reg_b.predict(X_b))[0,1]

    print('Under CIA (rho=0), fused correlation = 0 by construction.')
    print(f'Partial R^2 of SES for Y_A: {obs_corr_a**2:.3f}')
    print(f'Partial R^2 of SES for Y_B: {obs_corr_b**2:.3f}')
    print()
    print('True corr(Y_A,Y_B|X) | Implied bias in cross-survey corr')
    for rho in rho_grid:
        # Bias in naive correlation = rho * sqrt(R^2_A * R^2_B)
        bias = rho * obs_corr_a * obs_corr_b
        print(f'  rho = {rho:.2f}  |  bias ~ {bias:.4f}') |
| --- |

| Method | Inference | Robustness | Key Assumption | Best Use Case |
| --- | --- | --- | --- | --- |
| Classical Bridge | None (point est.) | Low | E[Y|X] correctly specified | Prediction only |
| Bayesian Bridge | Full posterior | Medium | Prior model correct | Full UQ needed |
| Mass Imputation | MI + Rubin | Medium | Outcome model consistent | Imputing Y for B |
| IPW | SE via influence fn | Low-Med | Propensity model correct | Reweighting A |
| Doubly Robust | SE via influence fn | High | Either model correct | Default choice |
| Calibration | GREG variance | Medium | SES moments sufficient | B-representative analysis |
| Stat. Matching | None (fused data) | Low | CIA: Y_A⊥Y_B|X | Creating fused files |
| MRP | Bayesian/multilevel | Med-High | Cell means correctly modeled | Cross-population transport |
| Synthetic Data | Rubin's rules | Medium | Synthesis model valid | Public data release |

| Recommended Default Stack for SES-Bridged Surveys
1. Diagnostics first: run overlap_diagnostics() to verify SES balance between surveys.
2. Primary estimator: use Doubly Robust (AIPW with cross-fitting) — best protection against
   model misspecification with a single, interpretable point estimate and valid SE.
3. Sensitivity: run CIA sensitivity analysis if doing statistical matching; run E-value
   analysis for ignorability violation if using IPW or DR.
4. Uncertainty propagation: wrap any imputation in multiple imputation (M≥20) + Rubin's rules.
5. Validation: if one survey has a holdout subsample with both outcomes, validate predicted
   cross-survey correlations against observed correlations in that subsample. |
| --- |
