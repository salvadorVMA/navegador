# DR Bridge Development Guide

*For onboarding a new Claude instance or developer to the Doubly Robust bridge estimator system.*

## What the DR Bridge Does

The DR (Doubly Robust) bridge estimates **cross-survey associations** between survey questions that were asked to *different respondents* in *different surveys*. Since no one answered both questions, we can't compute a direct cross-tab. Instead, the DR bridge uses shared SES (socioeconomic) covariates that appear in all surveys to statistically "bridge" between them.

### The core idea

Given:
- Survey A asks question Y_A to respondents with SES features X
- Survey B asks question Y_B to different respondents with the same SES features X

We want: **P(Y_A, Y_B)** — the joint distribution, as if both questions were asked to the same person.

The DR estimator:
1. Fits outcome models: P(Y_A | X) and P(Y_B | X) using MNLogit/OrderedModel
2. Fits a propensity model: P(survey=A | X) to reweight for selection differences
3. Computes AIPW-corrected marginals (robust if either model is correct)
4. Builds a joint table via individual-level CIA (Conditional Independence Assumption): for each person i in a reference SES population, compute P(Y_A|X_i) × P(Y_B|X_i), then average
5. Extracts Goodman-Kruskal γ (ordinal association, ∈ [-1,+1]) from the joint table

### Why γ and not Cramér's V?

γ respects ordinal structure (concordant vs discordant pairs). V treats categories as unordered. For survey Likert scales (strongly agree → strongly disagree), γ captures the direction and strength of association, while V only captures deviation from independence.

## Architecture

```
sweep_dr_highci.py          — Targeted re-sweep script (resume-safe)
  ↓ calls
ses_regression.py           — Core estimators
  DoublyRobustBridgeEstimator   — AIPW + propensity + bootstrap
    SurveyVarModel              — MNLogit/OrderedModel wrapper
    SESEncoder                  — One-hot/ordinal encoding for SES vars
  goodman_kruskal_gamma()       — γ from joint table
  ↓ depends on
ses_analysis.py             — SES preprocessing (region/edad/empleo creation)
dataset_knowledge.py        — Survey data loader (los_mex_dict)

dr_sweep_results.json       — v1 results: 6790 pairs, n_bootstrap=10 (rough CIs)
dr_sweep_results_v2.json    — v2 results: ~1531 pairs (|γ|≥0.25), n_bootstrap=200
                              148/1531 completed (checkpoint)
```

## Computational Bottleneck

### Where time is spent per variable pair

Each variable pair requires:
1. **2 model fits** (point estimate): SurveyVarModel.fit() × 2 — MNLogit/OrderedModel via BFGS
2. **1 propensity fit**: Logistic regression via BFGS
3. **2B model fits** (bootstrap): For each of `n_bootstrap` iterations, re-fit both outcome models on resampled data
4. **Matrix multiplications**: predict_proba on reference population, outer products for joint tables

**Total model fits per pair = 3 + 2 × n_bootstrap**

With n_bootstrap=200: **403 BFGS optimizations per variable pair**.

Each BFGS optimization takes 0.1–5s depending on:
- Number of categories K (more categories = more parameters in MNLogit: (K-1) × (n_features+1))
- Sample size (larger = slower Hessian computation)
- Conditioning (poorly conditioned → more iterations)

**Per-pair time**: 30–180s with n_bootstrap=200

### The 1531-pair sweep

- 1531 pairs × ~100s average = **~42 hours on 4-core Codespace**
- On M2 Mac (8 perf cores): **~20 hours with --workers 7**

## Running the Sweep on Mac

### Setup

```bash
git clone https://github.com/salvadorVMA/navegador.git
cd navegador
git checkout feature/bivariate-analysis
pip install -r config/requirements.txt
```

Verify data file exists (191MB, Git LFS):
```bash
ls -lh data/encuestas/los_mex_dict.json
# If zero-size or missing: git lfs pull
```

### Run (resumes from checkpoint automatically)

```bash
nohup python scripts/debug/sweep_dr_highci.py \
    --gamma-threshold 0.25 --n-bootstrap 200 --workers 7 \
    > /tmp/dr_highci.log 2>&1 &
tail -f /tmp/dr_highci.log
```

- **`--workers N`**: Set to (CPU cores - 1). M2 = 8 perf cores → `--workers 7`. M2 Pro = 10 → `--workers 9`.
- **`--gamma-threshold 0.25`**: Only re-estimate pairs where v1 |γ| ≥ 0.25 (1531 pairs).
- **`--n-bootstrap 200`**: 200 bootstrap iterations (v1 had 10).
- **Resume**: Reads `dr_sweep_results_v2.json` and skips completed pairs. 148 already done.
- **Saves after every pair**: Crash-safe. Kill and restart anytime.

### Monitor progress

```bash
# Live log
tail -f /tmp/dr_highci.log

# Count completed
python -c "import json; d=json.load(open('data/results/dr_sweep_results_v2.json')); print(f'{len(d[\"estimates\"])} / 1531')"
```

### Check CI quality as it runs

```bash
python -c "
import json, numpy as np
d = json.load(open('data/results/dr_sweep_results_v2.json'))
results = list(d['estimates'].values())
widths = [r['dr_gamma_ci'][1]-r['dr_gamma_ci'][0] for r in results if r.get('dr_gamma_ci')]
excl_zero = sum(1 for r in results if r.get('dr_gamma_ci') and (r['dr_gamma_ci'][0]>0 or r['dr_gamma_ci'][1]<0))
print(f'Completed: {len(results)}')
print(f'CI width: mean={np.mean(widths):.3f}, median={np.median(widths):.3f}')
print(f'CIs excluding zero: {excl_zero}/{len(widths)} ({100*excl_zero/len(widths):.1f}%)')
"
```

## GPU Acceleration on M2 Mac

### What CAN be accelerated

The bottleneck is 403 BFGS optimizations per pair. Each involves:
- Matrix multiplications (X'X, X'y) — **GPU-friendly**
- Log-likelihood evaluation — **GPU-friendly**
- Hessian computation — **GPU-friendly**
- BFGS iteration control — **CPU-only** (sequential by nature)

### Option 1: JAX backend (recommended, moderate effort)

Replace statsmodels MNLogit/OrderedModel with JAX-based implementations. JAX natively supports M2 GPU via Metal.

```bash
pip install jax jaxlib-metal  # M2 Metal backend
```

**What to change in `ses_regression.py`**:

Replace `SurveyVarModel.fit()` (lines ~478-600) with a JAX-based MNLogit:

```python
import jax
import jax.numpy as jnp
from jax.scipy.special import logsumexp

def mnlogit_nll(params, X, y_onehot, K):
    """Negative log-likelihood for multinomial logit."""
    # params shape: (n_features+1, K-1), ref class = 0
    eta = X @ params  # (n, K-1)
    eta_full = jnp.hstack([jnp.zeros((X.shape[0], 1)), eta])  # prepend ref
    log_probs = eta_full - logsumexp(eta_full, axis=1, keepdims=True)
    return -jnp.sum(y_onehot * log_probs)

# Use jax.value_and_grad + scipy.optimize.minimize(method='L-BFGS-B')
# The grad computation runs on GPU; the L-BFGS step is CPU
from jax import value_and_grad
from scipy.optimize import minimize

def fit_mnlogit_jax(X_np, y_np, K):
    X = jnp.array(X_np)
    y_oh = jnp.eye(K)[y_np]
    Xc = jnp.hstack([jnp.ones((X.shape[0], 1)), X])
    p = Xc.shape[1]
    x0 = jnp.zeros(p * (K - 1))

    def objective(params_flat):
        params = params_flat.reshape(p, K - 1)
        return mnlogit_nll(params, Xc, y_oh, K)

    obj_and_grad = jax.jit(value_and_grad(objective))

    def scipy_obj(x):
        v, g = obj_and_grad(jnp.array(x))
        return float(v), np.array(g, dtype=np.float64)

    result = minimize(scipy_obj, np.array(x0), jac=True, method='L-BFGS-B')
    return result.x.reshape(p, K - 1)
```

**Expected speedup**: 2-5x for the matrix operations. The BFGS iteration count stays the same, but each iteration is faster because grad/Hessian runs on Metal GPU. The biggest gain is from `jax.jit` compiling the NLL+grad once and reusing across all 403 fits (same shapes).

**Key constraint**: All 403 fits in a pair have the same X shape (same SES features, same bootstrap sample size). This means JAX compiles the function once and reuses it — no recompilation overhead.

### Option 2: Batch bootstrap with vectorized model fits (high effort, highest speedup)

Instead of fitting 200 bootstrap models sequentially, vectorize across bootstraps using `jax.vmap`:

```python
# Fit all 200 bootstrap models simultaneously on GPU
batched_fit = jax.vmap(fit_single_bootstrap, in_axes=(0, None))
# bootstrap_indices shape: (200, n_samples) — pre-generated
all_params = batched_fit(bootstrap_indices, data)
```

This would be a significant rewrite of `DoublyRobustBridgeEstimator.estimate()` but could give **10-50x speedup** because all bootstraps run in parallel on GPU.

### Option 3: Multiprocessing instead of threading (zero effort, immediate)

The current `sweep_dr_highci.py` uses `ThreadPoolExecutor`. Due to Python's GIL, threads don't truly parallelize CPU-bound statsmodels work. Switch to `ProcessPoolExecutor`:

```python
# In sweep_dr_highci.py, change:
from concurrent.futures import ProcessPoolExecutor as Executor
# instead of ThreadPoolExecutor
```

**Caveat**: Each process loads the full dataset (~191MB) into memory. With 7 workers, that's ~1.3GB RAM. M2 Macs with 16GB+ should be fine.

**This change alone could cut time by 3-4x** if the GIL is currently the bottleneck (likely, since statsmodels releases the GIL only partially during BFGS).

### Option 4: PyTorch MPS backend (alternative to JAX)

```bash
pip install torch  # MPS backend included for M2
```

Similar approach to JAX but using `torch.optim.LBFGS` with MPS device:
```python
device = torch.device("mps")
X_t = torch.tensor(X, dtype=torch.float32, device=device)
```

PyTorch MPS support is more mature than JAX Metal as of 2026.

### Recommendation

1. **Immediate**: Switch to `ProcessPoolExecutor` in `sweep_dr_highci.py` (5 min change)
2. **If still too slow**: Implement JAX MNLogit (replaces ~150 lines in `SurveyVarModel.fit()` and `predict_proba()`)
3. **Maximum speedup**: JAX vmap batch bootstrap (major rewrite of DR estimator)

## Key Files Reference

| File | Purpose |
|------|---------|
| `ses_regression.py` | All estimators. DR class at line ~1790. SurveyVarModel at line ~454. |
| `ses_analysis.py` | SES preprocessing. `preprocess_survey_data()` creates region/edad/empleo. |
| `scripts/debug/sweep_dr_highci.py` | Targeted re-sweep script. Resume-safe, saves per-pair. |
| `scripts/debug/sweep_bridge_comparison.py` | Full 5-method sweep (not needed for v2). |
| `scripts/debug/detect_construct_communities.py` | Louvain community detection on the network. |
| `scripts/debug/visualize_construct_network.py` | Network visualization (concentric rings). |
| `data/results/dr_sweep_results.json` | v1 sweep: 6790 pairs, n_bootstrap=10. |
| `data/results/dr_sweep_results_v2.json` | v2 sweep: 148/1531 done, n_bootstrap=200. |
| `data/results/construct_network.json` | Network: 120 nodes, 6990 edges. |
| `data/results/construct_communities.json` | Louvain results at 5 resolutions. |
| `data/results/semantic_variable_selection.json` | LLM-selected constructs per domain. |

## Critical Implementation Details

### Encoder mismatch bug (fixed)

**Always use `model._encoder.transform()` when predicting against a specific model.** Never create a fresh `SESEncoder()` for prediction data — it may produce different one-hot columns than the model was trained on, causing shape mismatches.

### MNLogit param layout

- `res.params` is `DataFrame(n_feat+1, K-1)` — K-1 alternative-specific columns
- `res.cov_params()` is `(p*(K-1), p*(K-1))` — alt-first (column-major) ordering
- To flatten params for Bayesian draws: `ravel(order='F')` + `reshape(order='F')`

### Sentinel codes

Values ≥ 97 or < 0 are "no answer" / "not applicable". Filtered by `_is_sentinel()`. Must be excluded from all models.

### SES variables used (7 total)

```python
SES_REGRESSION_VARS = ['sexo', 'edad', 'region', 'empleo', 'escol', 'Tam_loc', 'est_civil']
```

These are created/normalized by `ses_analysis.py:preprocess_survey_data()`. Some surveys lack `Tam_loc` — the estimator degrades gracefully (uses available subset).

### Propensity model uses restricted features

To avoid near-separation in the propensity logistic regression, it uses only `['sexo', 'escol', 'edad']` by default (3 vars instead of 7). This is intentional per Petersen et al. (2012).

## What Comes After the Sweep

Once the v2 sweep completes with good CIs:

1. **Filter edges by CI-excludes-zero** — only edges where the 95% CI doesn't span zero
2. **Reweight network by signal-to-noise**: edge_weight = |γ| / CI_width
3. **Re-run Louvain community detection** on the filtered/reweighted graph
4. **Compare modularity**: expect higher Q than the current 0.063 once noisy edges are removed
5. **Bootstrap community stability**: perturb γ values within CIs, re-run Louvain 100x, compute co-membership probabilities
6. **Build empirical ontology**: stable communities become latent dimensions
