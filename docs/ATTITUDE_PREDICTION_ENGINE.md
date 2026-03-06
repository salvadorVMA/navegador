# Attitude Prediction Engine — Implementation Plan

*Created: 2026-03-04*
*Branch: `feature/bivariate-analysis`*

---

## 1. Problem Statement

The bridge estimators in `ses_regression.py` currently answer one question:
**do attitudes in domain A correlate with attitudes in domain B, through SES?**
They return a scalar (Cramér's V, Goodman-Kruskal γ, Spearman ρ) for each
variable pair.

The attitude prediction engine answers a different question:
**given that a specific respondent holds attitude Y_a = j, what is the full
probability distribution over Y_b?**

This shifts the output from an association summary to a conditional predictive
distribution — useful for the conversational interface, the analytical essay
pipeline, and potential recommendation features.

---

## 2. Core Mathematical Framework

### 2.1 Prediction via Bayesian SES updating

The target quantity is the predictive distribution over Y_b given an observed
Y_a value:

```
P(Y_b = k | Y_a = j) = Σ_x  P(Y_b = k | SES = x) × P(SES = x | Y_a = j)
```

The posterior over SES given the observed attitude is computed via Bayes:

```
P(SES = x | Y_a = j) ∝ P(Y_a = j | SES = x) × P(SES = x)
```

Both terms on the right-hand side are already available from the existing
infrastructure:

- **P(Y_a = j | SES = x)**: the fitted `SurveyVarModel` for variable Y_a
  gives this as a row of predicted probabilities for any SES cell x.
- **P(SES = x)**: the marginal SES distribution of the reference population,
  drawn by `_sample_ses_population()` from the pooled survey respondents.
- **P(Y_b = k | SES = x)**: the fitted `SurveyVarModel` for variable Y_b.

The result is a full K_b-dimensional probability vector, not a point prediction.

### 2.2 Connection to the existing bridge

The `CrossDatasetBivariateEstimator` already computes this joint table
implicitly — it draws SES cells, generates Y_a and Y_b independently, and
tabulates the result. The prediction engine makes the conditioning on Y_a = j
explicit: it uses the same joint table but slices a row and renormalises.

Formally, if `J[j, k]` is the (j, k) entry of the K_a × K_b joint table:

```
P(Y_b = k | Y_a = j) = J[j, k] / Σ_k' J[j, k']
```

### 2.3 Why Bayesian SES updating is preferred over direct row-slicing

The direct row-slice is correct in expectation but ignores parameter
uncertainty. The Bayesian approach, via `BayesianBridgeEstimator._draw_proba()`,
propagates uncertainty in the MNLogit/OrderedModel coefficients through to
the prediction, producing calibrated credible intervals on P(Y_b = k | Y_a = j).

---

## 3. Class Design: `AttitudePredictionEngine`

The new class lives at the end of `ses_regression.py`, or in a new module
`attitude_prediction.py` if the file grows beyond 1 500 lines.

```python
class AttitudePredictionEngine:
    """Predicts the distribution over Y_b given an observed Y_a value.

    Uses the CIA bridge: P(Y_a, Y_b | SES) = P(Y_a|SES) * P(Y_b|SES).
    Bayesian posterior draws on the SES models propagate coefficient
    uncertainty to the output distribution.

    Args:
        ses_pop:   Reference SES population DataFrame (pooled from both surveys,
                   sentinel-filtered).  Passed directly to SurveyVarModel.fit().
        survey_a:  Short survey code, e.g. 'DEP'.
        survey_b:  Short survey code, e.g. 'REL'.
        n_draws:   Number of Laplace posterior draws for uncertainty (default 200).
        rng_seed:  Reproducibility seed.
    """

    def __init__(
        self,
        ses_pop: pd.DataFrame,
        survey_a: str,
        survey_b: str,
        n_draws: int = 200,
        rng_seed: int = 42,
    ) -> None: ...

    def fit(
        self,
        df_a: pd.DataFrame,
        var_a: str,
        df_b: pd.DataFrame,
        var_b: str,
    ) -> "AttitudePredictionEngine":
        """Fit SurveyVarModel for Y_a and Y_b.  Returns self for chaining."""
        ...

    def predict(
        self,
        observed_category: int,
        credible_interval: float = 0.95,
    ) -> Dict:
        """Return prediction dict for P(Y_b | Y_a = observed_category).

        Returns:
            {
              'predicted_distribution': {k: prob, ...},   # full P(Y_b=k) vector
              'modal_category':         int,              # argmax category
              'modal_prob':             float,            # point-estimate probability
              'credible_interval':      [lower, upper],   # CI on modal prob
              'association_gamma':      float,            # Goodman-Kruskal gamma
              'n_ses_cells':            int,              # cells with >= 1 respondent
              'pseudo_r2_a':            float,            # McFadden R2 of model A
              'pseudo_r2_b':            float,            # McFadden R2 of model B
            }
        """
        ...

    def predict_proba(self, observed_category: int) -> np.ndarray:
        """Return K_b-length array of P(Y_b = k | Y_a = observed_category).
        Point estimate only (no CI)."""
        ...

    def joint_table(self) -> np.ndarray:
        """Return K_a x K_b joint probability table (sums to 1.0)."""
        ...

    def prediction_uncertainty_decomposition(
        self,
        observed_category: int,
    ) -> Dict:
        """Decompose variance of P(Y_b=modal | Y_a=j) into two additive parts:

        1. SES-sampling variance: variance of P(Y_b|Y_a) across Laplace draws.
        2. CIA-violation proxy: spread of gamma estimates from
           CrossDatasetBivariateEstimator vs BayesianBridgeEstimator.
           Large divergence signals that the CIA assumption is under stress
           and prediction intervals should be interpreted conservatively.

        Returns:
            {
              'total_variance':          float,
              'ses_sampling_variance':   float,
              'cia_violation_proxy':     float,   # |gamma_bay - gamma_base|
              'reliability_flag':        str,     # 'high'|'medium'|'low'
            }
        """
        ...
```

### 3.1 Internal implementation sketch

`fit()` calls `SurveyVarModel(var_a, ...).fit(df_a, ses_pop)` and stores the
fitted model as `self._model_a`, and likewise for B.  No new fitting logic is
needed — this reuses the existing `OrderedModel`/`MNLogit` backbone.

`joint_table()` iterates over SES cells sampled from `ses_pop`, computes
`P(Y_a | SES=x)` and `P(Y_b | SES=x)` from the two models, and accumulates
the outer product weighted by the cell's marginal probability.  This is
identical to the simulation loop in `CrossDatasetBivariateEstimator.estimate()`.

`predict_proba(j)` slices row `j` of `joint_table()` and renormalises.

`predict(j)` wraps `predict_proba()` and adds CI from Bayesian draws: for
each of the `n_draws` posterior parameter vectors, compute
`predict_proba(j)`, collect the `n_draws` × K_b matrix, and report quantiles.

---

## 4. Worked Example: Soccer Interest → Religious Attendance

**Survey A**: `CULTURA_LECTURA_Y_DEPORTE` (DEP), variable `p3_23|DEP`
(importance of concerts — a proxy for active cultural participation).

**Survey B**: `RELIGION_SECULARIZACION_Y_LAICIDAD` (REL), variable
`p45_8|REL` (trust in NGOs — a proxy for civic-religious disposition).

Both variables are SES-predictable: education and urbanisation (Tam_loc)
are the top predictors for both leisure cultural engagement and civic trust.

```python
from ses_regression import AttitudePredictionEngine

engine = AttitudePredictionEngine(
    ses_pop=ses_df_pooled,
    survey_a='DEP',
    survey_b='REL',
    n_draws=200,
    rng_seed=42,
)
engine.fit(df_dep, 'p3_23|DEP', df_rel, 'p45_8|REL')

# Respondent rates concerts 8 out of 10 (category 8)
result = engine.predict(observed_category=8)
# result['predicted_distribution'] -> {1: 0.08, 2: 0.14, 3: 0.31, 4: 0.29, 5: 0.18}
# result['modal_category'] -> 3   (moderate civic/religious trust)
# result['association_gamma'] -> 0.22  (mild positive ordinal association)
```

**Sex-stratified prediction**: to produce gender-specific predictions, filter
`ses_pop` to males or females before calling `fit()`.  The SES models will be
estimated on the subpopulation, and the predictions will reflect sex-specific
SES distributions.  The difference between the two resulting distributions
quantifies how much of the A→B relationship is mediated by gender.

---

## 5. Uncertainty Quantification

Two independent sources of uncertainty are propagated.

**Source 1 — Coefficient uncertainty (Laplace posterior).**
`BayesianBridgeEstimator._draw_proba()` draws `n_draws` parameter vectors
from the multivariate normal approximation at the MLE.  For each draw,
`predict_proba(j)` is recomputed, yielding a `n_draws × K_b` matrix.
Column-wise quantiles give the credible interval on each P(Y_b = k | Y_a = j).

**Source 2 — CIA violation uncertainty.**
The CIA is untestable from the data alone, but its impact can be bounded by
comparing estimators.  If the baseline CIA estimate (γ from
`CrossDatasetBivariateEstimator`) and the Bayesian estimate agree closely,
CIA violation is unlikely to dominate.  If they diverge by more than 0.15
in absolute γ, a `reliability_flag = 'low'` is set, and the LLM is instructed
to qualify its interpretation.

The `prediction_uncertainty_decomposition()` method reports both components
and their ratio, supporting transparent communication of prediction quality.

---

## 6. Implementation Phases

### Phase 1 — Core engine (1–2 days)
Build `AttitudePredictionEngine` using `CrossDatasetBivariateEstimator` as
the computational backend.  `predict_proba()` slices the joint table.
No Bayesian draws yet.  Write `tests/unit/test_attitude_prediction.py`
with 10 tests covering: fit/predict shapes, joint table normalisation,
modal category extraction, degenerate cases (single SES cell, binary Y_b).

### Phase 2 — Bayesian uncertainty propagation (1 day)
Integrate `BayesianBridgeEstimator._draw_proba()` into `predict()`.
The existing `_draw_proba()` method is parameter-ready; the engine
calls it for each of the `n_draws` posterior samples and aggregates quantiles.
Add 3 tests: CI width decreases with larger n, CI coverage on synthetic data,
MNLogit vs OrderedModel CI comparison.

### Phase 3 — Ensemble prediction (1 day)
Run all six estimators on the same pair and compute a precision-weighted
average of their γ estimates.  Weight = 1 / CI_width² (narrower CI → higher
weight).  Expose `ensemble_gamma` alongside the individual estimates in
`predict()`.  This is the "best available" association signal for the LLM.

### Phase 4 — Multi-hop prediction (2 days)
Compute `P(Y_c | Y_a)` as:

```
P(Y_c = m | Y_a = j) = Σ_k  P(Y_c = m | Y_b = k) × P(Y_b = k | Y_a = j)
```

where the inner term is obtained from a second `AttitudePredictionEngine`
instance connecting B and C.  The two-hop CIA is stronger than the one-hop
CIA (it requires joint independence of Y_a, Y_b, Y_c given SES), so
`reliability_flag` is automatically downgraded to 'medium' or lower.

### Phase 5 — LLM integration (1 day)
Add `predict_cross_domain_attitude()` to `quantitative_engine.py`.  It calls
`AttitudePredictionEngine.predict()` and formats the result as a structured
block passed to the LLM prompt.  The block includes: variable labels, the
predicted distribution (converted to human-readable category labels via
`_get_var_labels()`), the credible interval, γ, and the reliability flag.
The LLM is instructed to acknowledge uncertainty when `reliability_flag != 'high'`.

---

## 7. File Structure

| File | Change |
|------|--------|
| `ses_regression.py` | Add `AttitudePredictionEngine` class at end |
| `attitude_prediction.py` | Alternative if `ses_regression.py` exceeds ~1 500 lines |
| `quantitative_engine.py` | Add `predict_cross_domain_attitude(var_a, cat_a, var_b, ...)` |
| `tests/unit/test_attitude_prediction.py` | New — 10 unit tests (Phases 1 and 2) |

---

## 8. Validation Strategy

**Split-domain test.** Take one survey with two thematically related
questions (e.g., two trust items from CULTURA_POLITICA), hold out the
cross-tabulation, fit the engine on the SES marginals only, and compare
the predicted `P(Y_b | Y_a = j)` to the observed conditional frequency.
The Brier score on this test quantifies how much explanatory power the SES
bridge captures.

**Known-direction test.** Higher `escol` (education) predicts higher scores
on science/technology questions (CIE).  The engine should predict that
respondents with the highest Y_a rating on `p29|ECO` (employment satisfaction
as a proxy for economic security) show an above-marginal distribution on
science optimism in CIE.  Failure here signals a broken pipeline, not a wrong
assumption.

**Calibration check.** For any survey containing both a leisure item and a
civic item (e.g., IDE — IDENTIDAD_Y_VALORES), compute the observed
P(civic_item = k | leisure_item = j) directly and compare to the engine's
prediction.  The expected calibration error (ECE) should be below 0.05 for
variables with McFadden pseudo-R² > 0.10 on the SES models.

---

## 9. Limitations and Honest Assumptions

**CIA is untestable by construction.** Any cross-domain correlation that does
not operate through the seven SES variables is invisible to the engine.
The bridge can only detect SES-mediated associations; unmeasured confounders
(e.g., shared cultural exposure, geographic clustering at sub-regional level)
are excluded.

**Prediction precision degrades with SES R².** If the SES model for Y_b has
McFadden R² < 0.05, the engine's prediction is barely distinguishable from
the marginal distribution of Y_b.  The `pseudo_r2_b` field in the prediction
dict signals this; the LLM integration should flag low-R² predictions explicitly.

**Sparse SES cells.** Rare SES combinations (e.g., divorced indigenous-language
speakers in Norte) may have zero or one respondent in the reference population,
making the local conditional probability unreliable.  `n_ses_cells` in the
output tracks how many cells had at least one respondent.

**Label resolution.** Category labels must be resolved from
`variable_value_labels` in the survey metadata before the output reaches the
LLM.  Raw numeric category codes (e.g., `4` on a 5-point trust scale) are
meaningless without labels.  The existing `_get_var_labels()` function in
`quantitative_engine.py` handles this.

---

## 10. Citations

- Pearl, J. (2009). *Causality: Models, Reasoning, and Inference* (2nd ed.).
  Cambridge University Press. — Do-calculus and counterfactual prediction via
  conditioning.
- Rubin, D. B. (1974). Estimating causal effects of treatments in randomized
  and nonrandomized studies. *Journal of Educational Psychology*, 66(5),
  688–701. — Potential outcomes framework; CIA as ignorability.
- D'Orazio, M., Di Zio, M., & Scanu, M. (2006). *Statistical Matching: Theory
  and Practice*. John Wiley & Sons. — Data fusion prediction under CIA;
  directly models the problem solved by the bridge.
- Rässler, S. (2002). *Statistical Matching: A Frequentist Theory, Practical
  Applications, and Alternative Bayesian Approaches*. Springer. — CIA
  in data fusion; Bayesian treatment of the untestable assumption.
- Bang, H., & Robins, J. M. (2005). Doubly robust estimation in missing data
  and causal inference models. *Biometrics*, 61(4), 962–973. — Theoretical
  basis for the `DoublyRobustBridgeEstimator` used in Phase 3 ensemble.
- Tierney, L., & Kadane, J. B. (1986). Accurate approximations for posterior
  moments and marginal densities. *Journal of the American Statistical
  Association*, 81(393), 82–86. — Laplace approximation used in
  `BayesianBridgeEstimator._draw_proba()` and Phase 2 uncertainty propagation.
- Gelman, A., & Hill, J. (2006). *Data Analysis Using Regression and
  Multilevel/Hierarchical Models*. Cambridge University Press. — Bayesian
  multilevel prediction; MRP shrinkage used in `MRPBridgeEstimator`.
