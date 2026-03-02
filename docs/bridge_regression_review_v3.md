
Bridge Regression and Cross-Survey Inference

Predicting Joint Distributions of Unobserved Variables via SES Bridges

Methods | Mathematics | Model Selection | Ordinal Data | Python | Pitfalls

# 1. The Core Inferential Problem

The fundamental challenge is this: Y_A and Y_B were never jointly observed. We want to estimate P(Y_A, Y_B), or more practically, the conditional distribution P(Y_A | Y_B = y) or summary statistics like the polychoric correlation between them. This is not a standard prediction problem — it is a problem of identifying a joint distribution from two marginals connected only by shared covariates.

## 1.1 What “Predicting the Distribution” Means Here

There are three increasingly ambitious targets:

- Level 1 – Marginal prediction: Given X_i from survey B, predict the distribution P(Y_A | X_i). This tells us what Y_A would look like for B respondents, marginally. Every bridge method in this review achieves at least this.

- Level 2 – Association estimation: Estimate Corr(Y_A, Y_B) or the full contingency table P(Y_A = a, Y_B = b) for the population covered by both surveys. This requires an explicit model for the joint distribution, beyond marginal predictions.

- Level 3 – Counterfactual joint distribution: What would the joint bivariate distribution of (Y_A, Y_B) look like in a single hypothetical survey containing both questions? This is the most complete target and requires the strongest assumptions.

Most operational analyses seek Level 2. The confidence of the assessment at Level 2 depends critically on: (a) how predictable Y_A is from SES (measured by R² or pseudo-R²), and (b) whether the CIA (Y_A ⊥ Y_B | X) is plausible.

## 1.2 The CIA and When It Is Defensible

The Conditional Independence Assumption (CIA) states:

Y_A  ⊥  Y_B  |  X          (CIA)

Under CIA, the joint distribution is identifiable from the two marginals:

P(Y_A, Y_B | X)  =  P(Y_A | X) · P(Y_B | X)

CIA is defensible when SES is the dominant driver of both outcomes and domain-specific confounders are minimal. For example, if Y_A = satisfaction with healthcare and Y_B = satisfaction with housing, and both are primarily SES-driven, CIA is reasonable. If Y_A = political ideology and Y_B = religiosity, CIA would be wrong because substantial correlation persists beyond SES.

## 1.3 Confidence Quantification

Confidence in the estimated joint distribution has two components that must be separately reported:

- Estimation uncertainty: Sampling variability from finite n. Quantified via bootstrap CIs, posterior credible intervals, or Rubin-combined SEs across multiple imputations. At n=1000 with ordinal outcomes and p~10 SES predictors, this is manageable.

- Model uncertainty: How much does the estimated association change if you use a different bridge model (logistic vs. random forest) or relax CIA? Quantified via model comparison and CIA sensitivity analysis. This component is often larger than estimation uncertainty and is routinely under-reported.

# 2. Distributional Prediction via the SES Bridge

## 2.1 General Framework

Let X ∈ ℝᵖ be the shared SES vector, observed in both surveys. The bridge works in three stages:

Stage 1: Estimate  f_A(X) = P(Y_A | X)  from survey A

Stage 2: Estimate  f_B(X) = P(Y_B | X)  from survey B

Stage 3: Under CIA: P(Y_A=a, Y_B=b) = ∫ P(Y_A=a|X) P(Y_B=b|X) dP(X)

In practice, Stage 3 is evaluated by averaging over observed X values from a reference population (either survey A, survey B, or a pooled sample):

P̂(Y_A=a, Y_B=b) = (1/N) ∑_i f̂_A(X_i, a) · f̂_B(X_i, b)

## 2.2 Estimating the Joint Table and Association Measures

For ordinal outcomes Y_A ∈ {1,...,K} and Y_B ∈ {1,...,J}, the estimated joint contingency table is:

π̂_{ab} = (1/n) ∑_{i=1}^{n} P̂(Y_A=a|X_i) · P̂(Y_B=b|X_i)      a=1..K, b=1..J

From this, standard association measures are derived:

- Polychoric correlation: treats both ordinal variables as discretized latent normals; appropriate when ordinal categories reflect an underlying continuous scale.

- Goodman-Kruskal gamma (γ): rank-based, non-parametric; appropriate when ordinal spacing is unknown.

- Cramér's V: for nominal categories; measures overall association without assuming order.

- Kendall's τ_b: robust rank correlation; better than Pearson for coarse ordinal scales.

Bootstrap the entire three-stage pipeline (fit f_A, fit f_B, average) to obtain valid CIs for all association measures.

## 2.3 Variance Components at n = 1000

With n_A = n_B ≈ 1000, the variance of P̂_{ab} has three components:

Var(P̂_{ab}) ≈ Var_A(f̂_A) / n_A  +  Var_B(f̂_B) / n_B  +  Var_{CIA}

- The first two terms are estimable via bootstrap or posterior variance and shrink at √ n rate.

- The third term, Var_{CIA}, is the variance contribution from possible CIA violation and is not estimable without additional data. It is zero only if CIA holds exactly.

# 3. Bridge Models: Linear, Ordinal, and Non-Parametric

The central modeling choice is how to estimate f(X) = P(Y | X) when Y is ordinal or categorical and n ≈ 1000. This section compares the main families systematically.

## 3.1 Binary Outcome: Logistic Regression

When Y ∈ {0,1}, the logistic model is:

logit P(Y=1 | X) = α + Xᵀβ

P(Y=1 | X) = σ(α + Xᵀβ) = 1 / (1 + exp(-α - Xᵀβ))

At n=1000 with p=10 SES predictors, logistic regression is well-powered, estimable by maximum likelihood in seconds, and produces valid probability estimates. Its main limitation is the linearity assumption: log-odds is linear in X, which may miss nonlinear SES effects (e.g., threshold effects at income deciles).

## 3.2 Ordinal Outcome: Proportional Odds Model

For ordinal Y ∈ {1,...,K}, the proportional odds model (McCullagh, 1980) is the standard:

logit P(Y ≤ k | X) = α_k - Xᵀβ      k = 1, ..., K-1

The K-1 intercepts α_1 < β_2 < ... < α_{K-1} are threshold parameters encoding the cumulative probabilities. The single coefficient vector β is shared across all thresholds — this is the proportional odds (PO) restriction.

Cell probabilities are recovered as:

P(Y=k|X) = σ(α_k - Xᵀβ) - σ(α_{k-1} - Xᵀβ)

At n=1000 with K ≤5 categories, the PO model is reliably estimated. It is semiparametric — makes no assumption about spacing between categories — and is equivalent to the Wilcoxon rank-sum test as a special case (Harrell, 2023).

## 3.3 Nominal Categorical Outcome: Multinomial Logistic Regression

For nominal Y ∈ {1,...,K} (unordered), the multinomial logistic model is:

P(Y=k|X) = exp(Xᵀβ_k) / ∑_{j=1}^{K} exp(Xᵀβ_j)       with β_K = 0 (reference)

This estimates K-1 separate coefficient vectors, one per non-reference category. At n=1000 with K=4 and p=10, this means estimating 30+ parameters. For K=6, it means 50+. With correlated SES predictors, this is at the edge of what n=1000 supports reliably.

## 3.4 Ordinal-Specific Machine Learning Models

For ordinal outcomes, naive application of classification forests (majority vote) discards the ordering information. Several ordinal-specific ML approaches exist:

### 3.4.1 Ordinal Forest (Hornung, 2019)

Assigns numeric scores to ordinal categories and uses regression forest predictions to recover a distribution over categories. The “frequency-adjusted borders” variant (fabOF, PMC11971599) explicitly handles the ordered structure during tree splitting.

Score mapping: Y ∈ {1,...,K} → s(Y) ∈ ℝ, then RF → ŝ, then P̂(Y=k) = P(ŝ ∈ [b_{k-1}, b_k])

### 3.4.2 Model-Based Transformation Forests (Buri & Hothorn, 2020)

Fits a conditional distribution model at each tree node, using the proportional odds model as the within-node model. This produces full conditional distributions P(Y≤k|X) from a forest, inheriting both the robustness of forests and the ordinal structure of PO.

Each node: logit P(Y≤k|X∈node) = α_k - β_{node}      (PO within node)

### 3.4.3 XGBoost / LightGBM with Ordinal Loss

Standard XGBoost can be adapted for ordinal outcomes using a cumulative-link loss function. Alternatively, treat ordinal prediction as K-1 binary problems (one per threshold), fit K-1 boosted classifiers, and recover P(Y=k|X) from differences in cumulative probabilities:

P̂(Y=k|X) = P̂(Y≤k|X) - P̂(Y≤k-1|X)

## 3.5 Model Selection Guidance for n≈1000

The following decision logic applies specifically to the bridge problem with ordinal/categorical outcomes and n≈1000:

For the primary bridge model, prefer the simplest well-specified model that passes calibration checks. ML models should serve as sensitivity checks to assess whether the parametric model's probability estimates are reliable.

# 4. Python Implementations for Distributional Bridge

## 4.1 Core Pipeline: Joint Table from Two Surveys

Master bridge pipeline for ordinal outcomes

## 4.2 Full Usage Example with Association Reporting

## 4.3 Bayesian Proportional Odds Bridge

Full posterior uncertainty over joint table using brms-style PyMC model

## 4.4 CIA Sensitivity Analysis

How much would gamma change if CIA is violated at level rho?

# 5. Method-by-Method Assessment for Joint Distribution Estimation

This section revisits each bridge method specifically through the lens of joint distribution estimation for ordinal/categorical outcomes at n=1000.

## 5.1 Mass Imputation for Ordinal Outcomes

Mass imputation predicts Y_A for every unit in survey B using the fitted model f_A(X). For ordinal Y, it should output the full conditional distribution P(Y_A=k|X_i) for each B unit — not just the modal category. The imputed records then support constructing a pseudo-joint dataset (X_i, ŷ_{A,i}, Y_{B,i}).

## 5.2 Doubly Robust for Ordinal: Semiparametric Efficiency

The doubly robust framework extends naturally to distributional targets. Instead of estimating E[Y], we target P(Y=k) for each category k, applying the AIPW correction to each binary indicator 1(Y=k):

P̂_{DR}(Y_A=k) = (1/n_B) ∑_{j∈B} f̂_A(X_j, k)  +  (1/n_B) ∑_{i∈A} [w_i · (1_{Y_{A,i}=k} - f̂_A(X_i, k))]

This gives DR estimates of the marginal distribution of Y_A in the B population, with a correction for model misspecification. The joint table is then estimated as the product of DR-corrected marginals (still under CIA).

## 5.3 Statistical Matching for Ordinal: the Rank Approach

For ordinal outcomes, rank-based matching is particularly natural. Both Y_A and Y_B have implicit orderings; PMM in the predicted-score space approximately preserves rank structure. The matched dataset can then be used to estimate the joint table by cross-tabulating matched pairs.

## 5.4 MRP for Joint Distribution: Cell-Level Prediction

MRP is naturally suited to distributional prediction because it works at the level of SES cells. For each SES cell j, fit P(Y_A=k | cell=j) from survey A and P(Y_B=l | cell=j) from survey B. The joint table for cell j is then their outer product (under CIA), and the population joint table is the cell-weighted average:

P(Y_A=k, Y_B=l) = ∑_j N_j / N  ·  P̂(Y_A=k|j) · P̂(Y_B=l|j)

At n=1000 with, say, 20 SES cells, MRP gives approximately 50 observations per cell — enough for reliable multinomial estimation within each cell using multilevel partial pooling.

# 6. Comprehensive Pitfalls Catalog for n≈1000 Ordinal Bridge

# 7. Best Practices for the Full Analysis Pipeline

## 7.1 Pre-Analysis Checklist

- SES overlap: run SMD and propensity score overlap diagnostic before any bridging

- Outcome type: confirm ordinal vs nominal; collapse sparse categories to K ≤ 5

- SES predictiveness: fit PO model Y|X in each survey; report McFadden pseudo-R²

- Proportional odds test: run Brant test; if violated for >2 predictors, switch to partial PO

- CIA plausibility: consult theory; if any third-survey test is available, run it

## 7.2 Recommended Pipeline (Operationally)

- Step 1: Fit proportional odds model in each survey (primary model)

- Step 2: Estimate joint table and gamma with 95% bootstrap CI (200 resamples minimum)

- Step 3: Fit RF/XGBoost bridge as sensitivity check; compare gamma estimates

- Step 4: Run CIA sensitivity analysis over rho ∈ [0, 0.5]

- Step 5: Report (a) point estimate, (b) bootstrap CI, (c) model sensitivity range, (d) CIA sensitivity bounds

- Step 6: Flag results where bootstrap CI width > model sensitivity range (model choice dominates)

## 7.3 Reporting Standards

# References

Bang, H. & Robins, J.M. (2005). Doubly robust estimation in missing data and causal inference models. Biometrics, 61, 962–973.

Brant, R. (1990). Assessing proportionality in the proportional odds model for ordinal logistic regression. Biometrics, 46(4), 1171–1178.

Buri, M. & Hothorn, T. (2020). Model-based random forests for ordinal regression. International Journal of Biostatistics, 16(2). PubMed 32764162.

Bürkner, P.-C. & Vuorre, M. (2019). Ordinal regression models in psychology: A tutorial. Advances in Methods and Practices in Psychological Science, 2(1), 77–101.

Chen, Y., Li, P. & Wu, C. (2020). Doubly robust inference with non-probability survey samples. JASA, 115(532), 2011–2021.

Chernozhukov, V. et al. (2018). Double/debiased machine learning for treatment and structural parameters. Econometrics Journal, 21(1), C1–C68.

D'Orazio, M., Di Zio, M. & Scanu, M. (2006). Statistical Matching: Theory and Practice. Wiley, Chichester.

Deville, J.-C. & Särndal, C.-E. (1992). Calibration estimators in survey sampling. JASA, 87, 376–382.

Flood, J. & Mostafa, S.A. (2025). Matched mass imputation for survey data integration. Journal of Data Science, 23(2), 332–352.

Frank, I.E. & Friedman, J.H. (1993). A statistical view of some chemometrics regression tools. Technometrics, 35(2), 109–135.

Gelman, A. & Little, T.C. (1997). Poststratification into many categories using hierarchical logistic regression. Survey Methodology, 23, 127–135.

Goodman, L.A. & Kruskal, W.H. (1954). Measures of association for cross classifications. JASA, 49(268), 732–764.

Harrell, F.E. (2023). Resources for Ordinal Regression Models. hbiostat.org/post/rpo/. Last modified 2023-05-01.

Hornung, R. (2019). Ordinal forests. Journal of Classification, 37(1), 4–28.

Kim, J.K. (2025). Calibration weighting for analyzing non-probability samples. Journal of Survey Statistics and Methodology. doi:10.1177/0282423X251318104.

Li, Y. & Si, Y. (2024). Embedded multilevel regression and poststratification. Statistics in Medicine, 43(2), 256–278. PMC11418010.

Little, R.J.A. (1988). Missing-data adjustments in large surveys. Journal of Business and Economic Statistics, 6(3), 287–296.

Mallick, H. & Yi, N. (2018). Bayesian bridge regression. Journal of Applied Statistics, 45(6), 988–1008. PMC6426306.

McCullagh, P. (1980). Regression models for ordinal data. Journal of the Royal Statistical Society B, 42(2), 109–142.

Moretti, A. & Shlomo, N. (2023). Data integration approaches in survey sampling. Journal of Survey Statistics and Methodology, 11(3).

Nooraee, N., Molenberghs, G. & van den Heuvel, E.R. (2014). GEE for longitudinal ordinal data: Comparing R-geepack, R-multgee, R-repolr, SAS-GENMOD, SPSS-GENLIN. Computational Statistics & Data Analysis, 77, 70–83.

Peterson, B. & Harrell, F.E. (1990). Partial proportional odds models for ordinal response variables. Applied Statistics, 39(2), 205–217.

Robbins, M.W. (2024). Joint imputation of general data. Journal of Survey Statistics and Methodology, 12(1), 183–210. doi:10.1093/jssam/smad034.

Tutz, G. & Gertheiss, J. (2021). Ordinal trees and random forests: Score-free recursive partitioning. Journal of Classification, 39(2), 241–271. doi:10.1007/s00357-021-09406-4.

van Buuren, S. (2018). Flexible Imputation of Missing Data, 2nd ed. CRC Press. freely available at flexiblemice.org.

Yang, S. & Kim, J.K. (2020). Statistical data integration in survey sampling: A review. Japanese Journal of Statistics and Data Science, 3, 625–650.

Yang, S., Kim, J.K. & Song, R. (2020). Doubly robust inference with high-dimensional data. JRSS-B, 82(2), 445–465.

Zhao, Y. & Udell, M. (2020). Missing value imputation for mixed data via Gaussian copula. Proceedings of KDD 2020.

End of Review  —  Bridge Regression & Cross-Survey Inference  |  February 2026  |  v3

| Scope and Context of This Review
Setting: K distinct surveys fielded in the same year, each containing an identical SES battery
(income, education, employment, household size, geographic unit). Surveys do NOT overlap:
no respondent appears in more than one survey. Each survey S_k also contains domain-specific
outcome variables Y_k not asked elsewhere.

Central question: Given that Y_A (outcome from survey A) and Y_B (outcome from survey B)
were never observed together, how can we estimate their joint distribution P(Y_A, Y_B) and
quantify uncertainty around this estimate?

Critical constraints addressed in this edition:
  - Most Y variables are ORDINAL (Likert scales, ranked categories) or NOMINAL CATEGORICAL
  - Sample sizes are approximately n = 1,000 per survey
  - Inference must extend to full distributional prediction, not just means
  - Model selection must balance expressiveness vs overfitting at n=1000 |
| --- |

| Practical CIA Assessment for Your Setting
With n=1000 and ordinal/categorical outcomes, a rough guide to CIA plausibility:
  - Check pseudo-R² of ordinal regression Y_k ~ X_SES. If R² > 0.30 for both outcomes,
    SES explains enough that residual correlation may be small.
  - Find any third survey with BOTH Y_A and Y_B. Even a sub-sample of n=50-100 lets you
    test CIA directly: compute partial correlation after residualizing on SES.
  - Use expert elicitation: ask domain experts whether they expect Y_A and Y_B to be
    correlated beyond SES. If yes, bound the CIA violation using sensitivity analysis. |
| --- |

| ⚠  The Fundamental Non-Identification Warning
Even with perfect SES measurement and n=∞, the joint distribution P(Y_A, Y_B) is
NOT identified from the two surveys without the CIA. This is not a statistical limitation
— it is a mathematical impossibility. The CIA (or some equivalent structural assumption)
is always required, regardless of sample size or model sophistication.
Confidence intervals from any method implicitly condition on this assumption being correct.
Any reported confidence interval should be understood as: 'uncertainty given CIA holds.' |
| --- |

| ℹ  Rule of Thumb for n=1000 with Ordinal Outcomes
With n=1000, p=10 SES predictors, and K=5 ordinal categories:
  - A well-specified ordinal logistic model estimates P(Y=k|X) with SE ≈ 0.02-0.05 per cell.
  - The estimated joint table π̂_{ab} has SE ≈ 0.01-0.03 per cell (from combined samples).
  - This is sufficient to detect strong associations (|gamma| > 0.3) but marginal for
    detecting weak associations (|gamma| < 0.15). Interpret weak associations cautiously.
  - With ordinal outcome of K=2 (binary), any logistic model works well at n=1000.
  - With K=7+ categories and p=15+ SES predictors, consider dimension reduction of SES first. |
| --- |

| ⚠  Logistic Pitfalls for Bridge
1. Complete separation: if any SES combination perfectly predicts Y=0 or Y=1,
   MLE does not exist. Add Firth or Bayesian penalization (logistf or brglm in R,
   or sklearn's LogisticRegression with strong C).
2. Calibration: logistic regression is well-calibrated by default but may lose
   calibration after regularization. Always check calibration curves.
3. Linearity: the log-odds is linear in X. If SES effects are non-monotone
   (e.g., middle-income group behaves differently), add polynomial or spline terms.
4. Predicted probabilities extrapolated to X_B values not seen in X_A: inspect
   the SES distribution overlap before imputing. |
| --- |

| ⚠  Proportional Odds Pitfalls
1. PO assumption violation: the log-odds ratio may differ across thresholds for some
   predictors. Test with the Brant test or Score test. If violated, use the partial
   proportional odds model (Peterson & Harrell, 1990) or multinomial logistic.
2. Sparse cells at n=1000: with K=7 and p=10 SES predictors, some cells may have
   n<5 observations. Consider collapsing adjacent categories or using Bayesian PO.
3. Predicted probabilities may be near-zero for rare categories after fitting;
   these will be unreliable for the joint table estimation at those cells.
4. Parallel slopes: if SES effects clearly differ across outcome levels (e.g., income
   predicts 'poor' strongly but not 'excellent'), force-fitting PO will produce
   systematically biased probability estimates for the joint table. |
| --- |

| ⚠  Multinomial Logistic Pitfalls at n=1000
1. Parameter explosion: K categories and p predictors require (K-1)×(p+1) parameters.
   At K=6, p=10, n=1000: 55 parameters, effective ratio 18:1. Regularize with elastic-net.
2. Independence of irrelevant alternatives (IIA): multinomial logit assumes that the odds
   Y=j vs Y=k is unaffected by other categories. This fails for similar categories (e.g.,
   'somewhat agree' vs 'agree' in a Likert scale).
3. Ordinal information wasted: if categories have a natural order, multinomial logit
   ignores it, losing statistical power. Prefer PO model for ordered outcomes.
4. Predicted cells can be very close to 0 for rare categories, making joint table
   P(Y_A=a, Y_B=b) estimates unreliable for rare cross-cells. |
| --- |

| ⚠  ML Models for Ordinal Outcomes at n=1000
1. Overfitting risk: random forests and XGBoost are designed for large n. At n=1000
   with p=10 SES predictors, a forest with 500 trees will overfit without strong
   regularization (min_samples_leaf ≥ 20, max_depth ≤3, or very high min_child_weight).
2. Probability calibration: tree ensembles produce uncalibrated probabilities, especially
   for rare categories. ALWAYS apply Platt scaling or isotonic regression post-training.
3. Variance estimates: sklearn RF provides no standard errors. Must bootstrap the full
   pipeline (resample -> fit -> predict) to get CIs for P(Y=k|X).
4. No gain over PO in small samples: at n=1000, well-specified PO model typically
   outperforms RF in terms of calibration and distributional accuracy. ML advantages
   only materialize at n ≥ 5000-10000. Use ML as sensitivity check, not primary model.
5. Ordinal order ignored by default: standard RF/XGBoost treat ordinal as nominal.
   Always use ordinal-specific variants or the cumulative threshold approach. |
| --- |

| Outcome type | Categories (K) | Recommended primary | Sensitivity check |
| --- | --- | --- | --- |
| Binary | 2 | Logistic (Firth if sparse) | RF with calibration |
| Ordinal | 3-5 | Proportional odds (PO) | Partial PO or ordinal RF |
| Ordinal | 6-10 | Bayesian PO (brms) | Transformation forest |
| Nominal | 3-5 | Regularized multinomial | RF (nominal) |
| Nominal | 6+ | Bayesian multinomial | Reduce to 5 categories |

| import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.utils import resample
import warnings

# ─────────────────────────────────────────────────────────────
# CORE BRIDGE PIPELINE
# Inputs:
#   X_a, Y_a  : SES matrix and ordinal outcome from survey A
#   X_b, Y_b  : SES matrix and ordinal outcome from survey B
#   ses_names : list of SES column names
# Outputs:
#   joint_table : K_a x K_b matrix with P(Y_A=a, Y_B=b)
#   ci_lower, ci_upper : bootstrap confidence intervals
# ─────────────────────────────────────────────────────────────

def fit_bridge_model(X, Y, model_type='ordinal', n_cats=None):
    '''Fit P(Y|X) for ordinal or categorical outcome.
    Returns fitted model and scaler. Use model_type=
    ordinal (PO), multinomial (MNL), or rf (forest).'''
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)
    cats = np.sort(np.unique(Y))

    if model_type == 'ordinal':
        # Proportional odds via K-1 cumulative binary logistic models
        thresholds = []
        for k in range(len(cats)-1):
            y_bin = (Y > cats[k]).astype(int)  # P(Y > k | X)
            lr = LogisticRegression(C=1.0, max_iter=2000,
                                    solver='lbfgs', random_state=0)
            lr.fit(X_s, y_bin)
            thresholds.append(lr)
        return ('ordinal', thresholds, scaler, cats)

    elif model_type == 'multinomial':
        # Regularized multinomial logistic
        lr = LogisticRegression(multi_class='multinomial', C=0.5,
                                max_iter=2000, solver='lbfgs', random_state=0)
        lr.fit(X_s, Y)
        # Calibrate probabilities
        cal = CalibratedClassifierCV(lr, cv='prefit', method='isotonic')
        cal.fit(X_s, Y)
        return ('multinomial', cal, scaler, cats)

    elif model_type == 'rf':
        from sklearn.ensemble import RandomForestClassifier
        # Heavily regularized RF for n=1000
        rf = RandomForestClassifier(n_estimators=500, max_depth=4,
                                    min_samples_leaf=20,  # KEY for n=1000
                                    n_jobs=-1, random_state=0)
        rf.fit(X_s, Y)
        cal = CalibratedClassifierCV(rf, cv=5, method='isotonic')
        cal.fit(X_s, Y)
        return ('rf', cal, scaler, cats)

def predict_proba_ordinal(model_tuple, X_new):
    '''Get P(Y=k|X) for all categories from fitted model tuple.'''
    mtype, model, scaler, cats = model_tuple
    X_s = scaler.transform(X_new)
    K = len(cats)

    if mtype == 'ordinal':
        # Cumulative probabilities from K-1 threshold models
        cum_probs = np.zeros((len(X_new), K+1))
        cum_probs[:, 0] = 0.0   # P(Y <= 0) = 0
        cum_probs[:, K] = 1.0   # P(Y <= K) = 1
        for k, thresh_model in enumerate(model):
            # P(Y > cats[k] | X) from binary model
            p_gt = thresh_model.predict_proba(X_s)[:, 1]
            cum_probs[:, k+1] = 1 - p_gt  # P(Y <= cats[k])
        # Enforce monotonicity (clip to [prev, 1])
        for k in range(1, K):
            cum_probs[:, k] = np.maximum(cum_probs[:, k], cum_probs[:, k-1])
        proba = np.diff(cum_probs, axis=1)  # shape (n, K)
        proba = np.clip(proba, 1e-8, 1.0)
        proba /= proba.sum(axis=1, keepdims=True)
        return proba

    else:
        return model.predict_proba(X_s)

def estimate_joint_table(model_a, model_b, X_ref):
    '''Estimate joint P(Y_A=a, Y_B=b) over reference population X_ref.
    Returns (K_a x K_b) matrix of joint probabilities.'''
    P_a = predict_proba_ordinal(model_a, X_ref)  # (n, K_a)
    P_b = predict_proba_ordinal(model_b, X_ref)  # (n, K_b)
    # Under CIA: P(a,b|X) = P(a|X)*P(b|X)
    # Average over X_ref: P(a,b) = E_X[P(a|X)*P(b|X)]
    joint = P_a[:, :, None] * P_b[:, None, :]  # (n, K_a, K_b)
    return joint.mean(axis=0)  # (K_a, K_b)

def bootstrap_joint_table(X_a, Y_a, X_b, Y_b, X_ref,
                           model_type='ordinal', n_boot=200, ci_level=0.95):
    '''Bootstrap the full pipeline to get CIs on joint table cells
    and derived association statistics.'''
    tables = []
    gammas = []

    for b in range(n_boot):
        # Resample each survey independently
        X_a_b, Y_a_b = resample(X_a, Y_a, random_state=b)
        X_b_b, Y_b_b = resample(X_b, Y_b, random_state=b+10000)

        ma = fit_bridge_model(X_a_b, Y_a_b, model_type)
        mb = fit_bridge_model(X_b_b, Y_b_b, model_type)
        tbl = estimate_joint_table(ma, mb, X_ref)
        tables.append(tbl)

        # Goodman-Kruskal gamma from joint table
        gammas.append(goodman_kruskal_gamma(tbl))

    tables = np.array(tables)  # (n_boot, K_a, K_b)
    alpha = (1 - ci_level) / 2
    ci_lo = np.quantile(tables, alpha, axis=0)
    ci_hi = np.quantile(tables, 1-alpha, axis=0)
    gamma_ci = np.quantile(gammas, [alpha, 1-alpha])

    return tables.mean(axis=0), ci_lo, ci_hi, gamma_ci

def goodman_kruskal_gamma(joint_table):
    '''Compute Goodman-Kruskal gamma from K_a x K_b joint table.'''
    K_a, K_b = joint_table.shape
    concordant = discordant = 0.0
    for i in range(K_a):
        for j in range(K_b):
            p_ij = joint_table[i, j]
            # Concordant: cells (k,l) with k>i AND l>j
            c = joint_table[i+1:, j+1:].sum()
            # Discordant: cells (k,l) with k>i AND l<j
            d = joint_table[i+1:, :j].sum()
            concordant += p_ij * c
            discordant += p_ij * d
    denom = concordant + discordant
    return (concordant - discordant) / denom if denom > 0 else 0.0 |
| --- |

| import numpy as np
from scipy.stats import pearsonr

# ── Simulate example data ──
np.random.seed(42)
n = 1000
# SES: income(0-1), education(0-1), employment(binary), age(norm)
X_a = np.column_stack([np.random.beta(2,3,n), np.random.beta(3,2,n),
                        np.random.binomial(1,.6,n), np.random.normal(0,1,n)])
X_b = np.column_stack([np.random.beta(2,3,n), np.random.beta(3,2,n),
                        np.random.binomial(1,.6,n), np.random.normal(0,1,n)])

# Ordinal outcomes (1-5 Likert, driven by SES + noise)
latent_a = X_a @ [1.5, 0.8, 0.6, 0.3] + np.random.normal(0,1,n)
Y_a = np.clip(np.digitize(latent_a, bins=[-1.5,-0.5,0.5,1.5]),1,5)
latent_b = X_b @ [1.0, 1.2, 0.4, 0.5] + np.random.normal(0,1,n)
Y_b = np.clip(np.digitize(latent_b, bins=[-1.5,-0.5,0.5,1.5]),1,5)

# ── Fit bridge models ──
X_ref = np.vstack([X_a, X_b])  # use pooled SES as reference population

print('Fitting ordinal (PO) bridge...')
model_a = fit_bridge_model(X_a, Y_a, model_type='ordinal')
model_b = fit_bridge_model(X_b, Y_b, model_type='ordinal')

# ── Estimate joint table ──
joint = estimate_joint_table(model_a, model_b, X_ref)
print('Estimated joint P(Y_A, Y_B):')
print(pd.DataFrame(joint, index=[f'Y_A={k}' for k in range(1,6)],
                          columns=[f'Y_B={k}' for k in range(1,6)]).round(3))

# ── Bootstrap CIs ──
print('Bootstrapping (n_boot=200)...')
jt_mean, jt_lo, jt_hi, gamma_ci = bootstrap_joint_table(
    X_a, Y_a, X_b, Y_b, X_ref, model_type='ordinal', n_boot=200)

gamma_est = goodman_kruskal_gamma(jt_mean)
print(f'Goodman-Kruskal gamma: {gamma_est:.3f}')
print(f'95% bootstrap CI: [{gamma_ci[0]:.3f}, {gamma_ci[1]:.3f}]')

# ── Sensitivity: compare ordinal vs RF ──
print('\nFitting RF bridge for sensitivity...')
model_a_rf = fit_bridge_model(X_a, Y_a, model_type='rf')
model_b_rf = fit_bridge_model(X_b, Y_b, model_type='rf')
joint_rf = estimate_joint_table(model_a_rf, model_b_rf, X_ref)
gamma_rf = goodman_kruskal_gamma(joint_rf)
print(f'RF gamma: {gamma_rf:.3f}')
print(f'Difference (model uncertainty): {abs(gamma_est-gamma_rf):.3f}')
print()
print('NOTE: If |gamma_ordinal - gamma_RF| is large relative to bootstrap CI,',
      'model uncertainty dominates. Report both.') |
| --- |

| import numpy as np
import pymc as pm
import pytensor.tensor as pt

def bayesian_po_bridge(X_a, Y_a, X_b, Y_b, X_ref,
                        n_samples=1000, n_chains=4):
    '''
    Bayesian proportional odds bridge.
    Propagates full posterior uncertainty into joint table estimates.
    Returns: (K_a x K_b) posterior mean joint table + HDI intervals.
    '''
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_all = scaler.fit_transform(np.vstack([X_a, X_b, X_ref]))
    na, nb, nr = len(X_a), len(X_b), len(X_ref)
    Xa_s = X_all[:na]
    Xb_s = X_all[na:na+nb]
    Xr_s = X_all[na+nb:]

    cats_a = np.sort(np.unique(Y_a))
    cats_b = np.sort(np.unique(Y_b))
    Ka, Kb = len(cats_a), len(cats_b)
    p = Xa_s.shape[1]

    # Encode to 0-indexed integers
    ya = np.searchsorted(cats_a, Y_a)  # 0..Ka-1
    yb = np.searchsorted(cats_b, Y_b)

    with pm.Model() as model:
        # Survey A: proportional odds
        beta_a = pm.Normal('beta_a', 0, 1, shape=p)
        cuts_a = pm.Normal('cuts_a', mu=np.linspace(-2,2,Ka-1), sigma=1, shape=Ka-1)
        cuts_a_sorted = pt.sort(cuts_a)  # enforce ordering
        eta_a = pm.math.dot(Xa_s, beta_a)  # (na,)
        obs_a = pm.OrderedLogistic('obs_a', eta=eta_a,
                                    cutpoints=cuts_a_sorted, observed=ya)

        # Survey B: proportional odds (independent model)
        beta_b = pm.Normal('beta_b', 0, 1, shape=p)
        cuts_b = pm.Normal('cuts_b', mu=np.linspace(-2,2,Kb-1), sigma=1, shape=Kb-1)
        cuts_b_sorted = pt.sort(cuts_b)
        eta_b = pm.math.dot(Xb_s, beta_b)
        obs_b = pm.OrderedLogistic('obs_b', eta=eta_b,
                                    cutpoints=cuts_b_sorted, observed=yb)

        # Posterior predictive: P(Y_A=k|X_ref) and P(Y_B=k|X_ref)
        eta_ref_a = pm.math.dot(Xr_s, beta_a)  # (nr,)
        eta_ref_b = pm.math.dot(Xr_s, beta_b)

        # Compute cell probs at each posterior draw (done in post-processing)
        trace = pm.sample(n_samples, chains=n_chains,
                          target_accept=0.9, return_inferencedata=True)

    # Post-process: for each posterior draw, compute joint table
    beta_a_post = trace.posterior['beta_a'].values  # (chains,draws,p)
    cuts_a_post = trace.posterior['cuts_a'].values
    beta_b_post = trace.posterior['beta_b'].values
    cuts_b_post = trace.posterior['cuts_b'].values

    def cum_probs(eta, cuts):
        # eta: (nr,), cuts: (K-1,) -> cum P(Y<=k) for k=0..K-1
        # shape (nr, K-1)
        return 1 / (1 + np.exp(eta[:,None] - cuts[None,:]))

    def cell_probs(cum):
        K = cum.shape[1] + 1
        p = np.zeros((cum.shape[0], K))
        p[:, 1:] = cum
        p = np.diff(p, axis=1)  # (nr, K)
        p = np.clip(p, 1e-8, 1)
        return p / p.sum(axis=1, keepdims=True)

    S = n_samples * n_chains
    joint_samples = np.zeros((S, Ka, Kb))

    s = 0
    for ch in range(n_chains):
        for dr in range(n_samples):
            ba = beta_a_post[ch, dr]
            ca = np.sort(cuts_a_post[ch, dr])
            bb = beta_b_post[ch, dr]
            cb = np.sort(cuts_b_post[ch, dr])
            eta_a = Xr_s @ ba
            eta_b = Xr_s @ bb
            pa = cell_probs(cum_probs(eta_a, ca))  # (nr, Ka)
            pb = cell_probs(cum_probs(eta_b, cb))  # (nr, Kb)
            # Under CIA: average outer product over ref pop
            joint_samples[s] = (pa[:,:,None] * pb[:,None,:]).mean(axis=0)
            s += 1

    joint_mean = joint_samples.mean(axis=0)
    joint_hdi_lo = np.quantile(joint_samples, 0.025, axis=0)
    joint_hdi_hi = np.quantile(joint_samples, 0.975, axis=0)

    # Posterior distribution of gamma
    gammas = np.array([goodman_kruskal_gamma(joint_samples[s])
                        for s in range(S)])
    print(f'Posterior gamma: mean={gammas.mean():.3f}, ',
          f'94% HDI=[{np.quantile(gammas,0.03):.3f}, {np.quantile(gammas,0.97):.3f}]')

    return joint_mean, joint_hdi_lo, joint_hdi_hi, gammas, trace |
| --- |

| import numpy as np
from scipy.stats import pearsonr

def cia_sensitivity_for_gamma(X_a, Y_a, X_b, Y_b, model_type='ordinal',
                               rho_violations=None):
    '''
    Bounds on estimated gamma if CIA is violated at level rho.
    Approach: simulate from a Gaussian copula with residual correlation rho
    between the latent variables underlying Y_A and Y_B.
    '''
    if rho_violations is None:
        rho_violations = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    # Fit base models
    ma = fit_bridge_model(X_a, Y_a, model_type)
    mb = fit_bridge_model(X_b, Y_b, model_type)

    # Reference population (pooled SES)
    X_ref = np.vstack([X_a, X_b])
    Pa = predict_proba_ordinal(ma, X_ref)   # (N, Ka)
    Pb = predict_proba_ordinal(mb, X_ref)   # (N, Kb)
    cats_a = ma[3]; cats_b = mb[3]
    Ka, Kb = len(cats_a), len(cats_b)

    print('CIA sensitivity: effect on Goodman-Kruskal gamma')
    print(f'  (under CIA, gamma_CIA = baseline estimate)')
    print(f'  rho = residual latent correlation after conditioning on SES')
    print()

    results = []
    for rho in rho_violations:
        # Simulate from Gaussian copula with correlation rho
        # in the latent space of Y_A and Y_B
        n_sim = 50000
        Sigma = np.array([[1, rho],[rho, 1]])
        Z = np.random.multivariate_normal([0,0], Sigma, n_sim)
        U = 1 / (1 + np.exp(-Z))  # uniform marginals via logistic CDF

        # For each ref unit, draw from copula-adjusted joint
        # (simplified: use average marginals)
        Pa_avg = Pa.mean(axis=0)   # (Ka,) marginal distribution of Y_A
        Pb_avg = Pb.mean(axis=0)   # (Kb,) marginal distribution of Y_B

        cum_a = np.concatenate([[0], Pa_avg.cumsum()])  # thresholds
        cum_b = np.concatenate([[0], Pb_avg.cumsum()])

        # Assign copula samples to categories
        cat_a = np.searchsorted(cum_a[1:-1], U[:,0])
        cat_b = np.searchsorted(cum_b[1:-1], U[:,1])

        # Build joint table from simulated (cat_a, cat_b) pairs
        joint_sim = np.zeros((Ka, Kb))
        for a in range(Ka):
            for b in range(Kb):
                joint_sim[a,b] = np.mean((cat_a==a) & (cat_b==b))

        gamma_rho = goodman_kruskal_gamma(joint_sim)
        results.append((rho, gamma_rho))
        print(f'  rho={rho:.1f}:  gamma={gamma_rho:.3f}')

    print()
    print('Interpretation: if the true residual correlation is rho,',
          'the true gamma lies near the value above.')
    print('Your CIA-based estimate assumes rho=0.')
    return results |
| --- |

| ⚠  Mass Imputation Ordinal Pitfalls
1. Modal imputation: using argmax P(Y|X) as the imputed value loses distributional
   information. ALWAYS impute the full PMF or use probabilistic (stochastic) imputation.
2. n=1000 risk: with 5-category outcome and p=10 SES predictors, the ordinal model
   estimates ~14 parameters. This is fine. But if Y_A is very weakly SES-predicted
   (pseudo-R² < 0.05), imputed values will be near the marginal distribution of Y_A
   and the joint table will show near-independence regardless of CIA.
3. Multiple imputation: at n=1000, use M=50 stochastic imputations to get valid
   variance estimates. Rubin's rules then give a valid SE for gamma. |
| --- |

| ⚠  Rank Matching Ordinal Pitfalls
1. Tied predicted scores: with ordinal 5-category outcomes, predicted scores
   from PO model will be heavily tied. Add jitter or use distance in covariate
   space rather than predicted score space.
2. Matching ratio: 1:1 matching at n=1000 produces only 1000 joint records,
   giving marginal precision. Use 1:k with k=3-5 to retain more information.
3. CIA still required: statistical matching does not escape CIA. The matched
   pairs assume Y_A ⊥ Y_B | X, so the joint table still reflects this assumption. |
| --- |

| Pitfall | Trigger condition | Effect on joint table | Solution |
| --- | --- | --- | --- |
| Weak SES predictors | Pseudo-R² < 0.05 for Y|X | Joint table ≈ product of marginals; gamma ≈ 0 regardless of true association | Report predictive R² before bridge; acknowledge if association is undetectable |
| PO assumption violation | Brant test p<0.05 | Wrong cell probabilities for some categories; biased gamma | Use partial PO, multinomial, or ordinal RF; compare gammas across models |
| CIA violation | Y_A and Y_B share unobserved drivers | gamma biased; direction depends on sign of residual correlation | CIA sensitivity analysis; report bounds; find third survey for empirical test |
| Sparse SES cells | n_cell < 10 after cross-tabulation | Unreliable within-cell P(Y|X); inflated variance | Coarsen SES into fewer cells; use multilevel partial pooling (MRP) |
| Propensity overlap failure | SES profiles unique to one survey | IPW/DR weights explode; imputed values extrapolated | Trim propensity scores; restrict inference to overlap region |
| Modal imputation | Using argmax instead of full PMF | Discretization error; underestimated variance in joint table | Always use stochastic (probabilistic) imputation from full PMF |
| Calibration failure in ML | RF overfit on n=1000 | P(Y=k|X) ≈ 0 or 1 for all X; joint table cells near 0 | Isotonic calibration post-training; Platt scaling; compare to PO model |
| Confidence inflation | Reporting only estimation CI | CI appears narrow; ignores CIA + model uncertainty | Report estimation CI, model sensitivity range, and CIA bounds separately |
| Ordinal treated as nominal | Multinomial on Likert scale | Wastes ordering information; loses power | Use PO model; gamma/tau_b instead of Cramer's V |
| Rare category collapse | K=7 with n=1000 | 2-3 obs in extreme categories; unstable P estimates | Collapse to K=4-5 before modeling; report both analyses |

| Minimum Reporting Requirements for SES Bridge Joint Distribution
For each bridged pair (Y_A, Y_B):
  1. Pseudo-R² of PO model for Y_A|X and Y_B|X separately
  2. Brant test result for PO assumption
  3. Estimated joint contingency table (K_A x K_B) with marginals
  4. Association measure (gamma or tau_b) with 95% bootstrap CI
  5. Same measure under RF bridge model (model sensitivity)
  6. CIA sensitivity: gamma under rho = 0.2 (moderate CIA violation)
  7. Effective sample size after any propensity weighting
Statements of the form 'Y_A and Y_B are positively associated (gamma=0.28, 95% CI
[0.14, 0.41], robust to model choice, sensitive to CIA at rho>0.3)' are appropriate. |
| --- |
