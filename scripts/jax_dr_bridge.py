"""JAX Doubly Robust Bridge Estimator — GPU/TPU/CPU.

Pure JAX functions for the ordered-logit DR bridge estimator.
No side effects, no I/O. Import and call from notebook or CLI.

Usage:
    from scripts.jax_dr_bridge import dr_estimate_single, prepare_pair_data
"""

import jax
import jax.numpy as jnp
from jax import random, vmap, jit
from functools import partial
import numpy as np
import pandas as pd

DTYPE = jnp.float64

# ---------------------------------------------------------------------------
# Threshold encoding/decoding (unconstrained parametrization)
# ---------------------------------------------------------------------------

@jit
def decode_thresholds(gamma_params):
    """gamma -> ordered alpha via cumulative exp: alpha_k = alpha_{k-1} + exp(gamma_k)."""
    return jnp.cumsum(
        jnp.concatenate([gamma_params[:1], jnp.exp(gamma_params[1:])])
    )


def encode_thresholds(alpha):
    """alpha -> gamma (inverse of decode). NumPy, used for initialization only."""
    K1 = len(alpha)
    gamma = np.zeros(K1)
    gamma[0] = alpha[0]
    for k in range(1, K1):
        gamma[k] = np.log(max(alpha[k] - alpha[k - 1], 1e-6))
    return gamma


# ---------------------------------------------------------------------------
# Ordered logit NLL (JAX-differentiable)
# ---------------------------------------------------------------------------

@jit
def ordered_logit_nll(params, X, y_onehot, K):
    """Negative log-likelihood of proportional-odds model."""
    p = X.shape[1]
    beta = params[:p]
    gamma_params = params[p:]
    alpha = decode_thresholds(gamma_params)

    eta = X @ beta
    cum_probs = jax.nn.sigmoid(alpha[None, :] - eta[:, None])

    zeros_col = jnp.zeros((X.shape[0], 1), dtype=cum_probs.dtype)
    ones_col = jnp.ones((X.shape[0], 1), dtype=cum_probs.dtype)
    cum_full = jnp.concatenate([zeros_col, cum_probs, ones_col], axis=1)
    cell_probs = cum_full[:, 1:] - cum_full[:, :-1]
    cell_probs = jnp.maximum(cell_probs, 1e-12)

    ll = jnp.sum(y_onehot * jnp.log(cell_probs))
    return -ll


# ---------------------------------------------------------------------------
# Fixed-iteration Newton optimizer (uses jnp.linalg.solve)
# ---------------------------------------------------------------------------

@partial(jit, static_argnums=(3, 4))
def fit_ordered_logit_newton(X, y_onehot, params0, K, n_iter=30):
    """Fit ordered logit via fixed-iteration Newton steps.

    Globally concave -> Newton always converges in ~15-25 steps.
    Uses jnp.linalg.solve (CUDA triangular_solve / TPU Cholesky).
    """
    nll_fn = lambda p: ordered_logit_nll(p, X, y_onehot, K)
    grad_fn = jax.grad(nll_fn)
    hess_fn = jax.hessian(nll_fn)

    def newton_step(params, _):
        g = grad_fn(params)
        H = hess_fn(params)
        H_reg = H + 1e-4 * jnp.eye(H.shape[0], dtype=H.dtype)
        # TPU only supports f32 for LU decomposition; downcast solve, upcast result
        delta = jnp.linalg.solve(H_reg.astype(jnp.float32), g.astype(jnp.float32)).astype(params.dtype)
        step_norm = jnp.sqrt(jnp.sum(delta ** 2))
        scale = jnp.minimum(1.0, 2.0 / jnp.maximum(step_norm, 1e-8))
        return params - scale * delta, None

    params_final, _ = jax.lax.scan(newton_step, params0, None, length=n_iter)
    return params_final


# ---------------------------------------------------------------------------
# Logistic regression (propensity model)
# ---------------------------------------------------------------------------

@jit
def logistic_nll(beta, X, y):
    """Binary logistic regression NLL."""
    logits = X @ beta
    return -jnp.sum(y * jax.nn.log_sigmoid(logits) + (1 - y) * jax.nn.log_sigmoid(-logits))


@partial(jit, static_argnums=(3,))
def fit_logistic_newton(X, y, beta0, n_iter=20):
    """Fit logistic regression via fixed-iteration Newton."""
    nll_fn = lambda b: logistic_nll(b, X, y)
    grad_fn = jax.grad(nll_fn)
    hess_fn = jax.hessian(nll_fn)

    def newton_step(beta, _):
        g = grad_fn(beta)
        H = hess_fn(beta)
        H_reg = H + 1e-4 * jnp.eye(H.shape[0], dtype=H.dtype)
        # TPU only supports f32 for LU decomposition; downcast solve, upcast result
        delta = jnp.linalg.solve(H_reg.astype(jnp.float32), g.astype(jnp.float32)).astype(beta.dtype)
        step_norm = jnp.sqrt(jnp.sum(delta ** 2))
        scale = jnp.minimum(1.0, 2.0 / jnp.maximum(step_norm, 1e-8))
        return beta - scale * delta, None

    beta_final, _ = jax.lax.scan(newton_step, beta0, None, length=n_iter)
    return beta_final


# ---------------------------------------------------------------------------
# Predict probabilities
# ---------------------------------------------------------------------------

@jit
def predict_proba_ordered(params, X, K):
    """P(Y=k|X) for k=1..K. Returns (n, K) matrix."""
    p = X.shape[1]
    beta = params[:p]
    gamma_params = params[p:]
    alpha = decode_thresholds(gamma_params)

    eta = X @ beta
    cum_probs = jax.nn.sigmoid(alpha[None, :] - eta[:, None])

    zeros_col = jnp.zeros((X.shape[0], 1), dtype=cum_probs.dtype)
    ones_col = jnp.ones((X.shape[0], 1), dtype=cum_probs.dtype)
    cum_full = jnp.concatenate([zeros_col, cum_probs, ones_col], axis=1)
    cell_probs = cum_full[:, 1:] - cum_full[:, :-1]
    cell_probs = jnp.maximum(cell_probs, 1e-10)
    cell_probs = cell_probs / cell_probs.sum(axis=1, keepdims=True)
    return cell_probs


@jit
def predict_logistic(beta, X):
    """P(y=1|X) from logistic coefficients."""
    return jax.nn.sigmoid(X @ beta)


# ---------------------------------------------------------------------------
# Goodman-Kruskal gamma from joint table (float64 precision)
# ---------------------------------------------------------------------------

@jit
def goodman_kruskal_gamma(joint):
    """Goodman-Kruskal gamma from K_a x K_b joint probability table."""
    joint = joint.astype(jnp.float64)
    Ka, Kb = joint.shape
    concordant = jnp.float64(0.0)
    discordant = jnp.float64(0.0)

    below_right = jnp.zeros_like(joint)
    below_left = jnp.zeros_like(joint)

    for i in range(Ka - 2, -1, -1):
        for j in range(Kb - 2, -1, -1):
            below_right = below_right.at[i, j].set(
                jnp.sum(joint[i + 1:, j + 1:])
            )
    for i in range(Ka - 2, -1, -1):
        for j in range(1, Kb):
            below_left = below_left.at[i, j].set(
                jnp.sum(joint[i + 1:, :j])
            )

    concordant = jnp.sum(joint * below_right)
    discordant = jnp.sum(joint * below_left)

    denom = concordant + discordant
    return jnp.where(denom > 0, (concordant - discordant) / denom, 0.0)


@jit
def normalized_mutual_information(joint):
    """NMI from joint probability table."""
    joint = joint.astype(jnp.float64)
    p = joint / jnp.maximum(jnp.sum(joint), 1e-12)
    p_a = jnp.sum(p, axis=1)
    p_b = jnp.sum(p, axis=0)

    h_a = -jnp.sum(jnp.where(p_a > 0, p_a * jnp.log(p_a), 0.0))
    h_b = -jnp.sum(jnp.where(p_b > 0, p_b * jnp.log(p_b), 0.0))
    min_h = jnp.minimum(h_a, h_b)

    outer = p_a[:, None] * p_b[None, :]
    mi = jnp.sum(jnp.where(
        (p > 0) & (outer > 0),
        p * jnp.log(p / jnp.maximum(outer, 1e-30)),
        0.0
    ))
    mi = jnp.maximum(mi, 0.0)
    return jnp.where(min_h > 1e-12, mi / min_h, 0.0)


# ---------------------------------------------------------------------------
# Single-pair DR estimate (pure JAX, no side effects)
# ---------------------------------------------------------------------------

@partial(jit, static_argnums=(4, 5))
def _dr_estimate_single(
    X_a, y_onehot_a,
    X_b, y_onehot_b,
    K,
    n_sim,
    X_ref,
    rng_key,
):
    """Single DR estimate: fit models, build joint table, compute gamma."""
    p = X_a.shape[1]

    # Initialize: beta=0, gamma from uniform cumulative proportions
    uniform_cum = jnp.linspace(1.0 / K, 1.0 - 1.0 / K, K - 1)
    alpha_init = jnp.log(uniform_cum / (1.0 - uniform_cum))
    gamma_init = jnp.concatenate([alpha_init[:1],
                                   jnp.log(jnp.maximum(jnp.diff(alpha_init), 1e-6))])
    params0 = jnp.concatenate([jnp.zeros(p, dtype=DTYPE), gamma_init.astype(DTYPE)])

    # Step 1: Fit outcome models
    params_a = fit_ordered_logit_newton(X_a, y_onehot_a, params0, K, 30)
    params_b = fit_ordered_logit_newton(X_b, y_onehot_b, params0, K, 30)

    # Step 2: Propensity model (part of DR formulation)
    n_a, n_b = X_a.shape[0], X_b.shape[0]
    X_pooled = jnp.concatenate([X_a, X_b], axis=0)
    Xc = jnp.concatenate([jnp.ones((X_pooled.shape[0], 1), dtype=DTYPE), X_pooled], axis=1)
    delta = jnp.concatenate([jnp.ones(n_a, dtype=DTYPE), jnp.zeros(n_b, dtype=DTYPE)])
    prop_beta0 = jnp.zeros(Xc.shape[1], dtype=DTYPE)
    prop_beta = fit_logistic_newton(Xc, delta, prop_beta0, 20)

    # Step 3: Build joint table on reference population
    Pa_ref = predict_proba_ordered(params_a, X_ref, K)[:, :K]
    Pb_ref = predict_proba_ordered(params_b, X_ref, K)[:, :K]

    joint = (Pa_ref.T @ Pb_ref) / n_sim
    joint = joint / jnp.maximum(jnp.sum(joint), 1e-12)

    # Step 4: Gamma and NMI
    gamma = goodman_kruskal_gamma(joint)
    nmi = normalized_mutual_information(joint)

    return gamma, nmi, joint


# ---------------------------------------------------------------------------
# Bootstrap single iteration
# ---------------------------------------------------------------------------

@partial(jit, static_argnums=(4, 5))
def _bootstrap_iter(
    X_a, y_onehot_a, X_b, y_onehot_b,
    K, n_sim, X_ref, rng_key,
):
    """One bootstrap iteration: resample -> refit -> gamma."""
    n_a, n_b = X_a.shape[0], X_b.shape[0]
    p = X_a.shape[1]

    key1, key2 = random.split(rng_key)
    idx_a = random.randint(key1, (n_a,), 0, n_a)
    idx_b = random.randint(key2, (n_b,), 0, n_b)

    X_a_boot = X_a[idx_a]
    y_a_boot = y_onehot_a[idx_a]
    X_b_boot = X_b[idx_b]
    y_b_boot = y_onehot_b[idx_b]

    # Initialize
    uniform_cum = jnp.linspace(1.0 / K, 1.0 - 1.0 / K, K - 1)
    alpha_init = jnp.log(uniform_cum / (1.0 - uniform_cum))
    gamma_init = jnp.concatenate([alpha_init[:1],
                                   jnp.log(jnp.maximum(jnp.diff(alpha_init), 1e-6))])
    params0 = jnp.concatenate([jnp.zeros(p, dtype=DTYPE), gamma_init.astype(DTYPE)])

    # Fit on bootstrap sample (fewer iterations)
    params_a = fit_ordered_logit_newton(X_a_boot, y_a_boot, params0, K, 20)
    params_b = fit_ordered_logit_newton(X_b_boot, y_b_boot, params0, K, 20)

    Pa = predict_proba_ordered(params_a, X_ref, K)[:, :K]
    Pb = predict_proba_ordered(params_b, X_ref, K)[:, :K]
    joint = (Pa.T @ Pb) / n_sim
    joint = joint / jnp.maximum(jnp.sum(joint), 1e-12)

    return goodman_kruskal_gamma(joint)


# ---------------------------------------------------------------------------
# Vectorized bootstrap (vmap over bootstrap iterations)
# ---------------------------------------------------------------------------

@partial(jit, static_argnums=(4, 5, 7))
def _bootstrap_all(
    X_a, y_onehot_a, X_b, y_onehot_b,
    K, n_sim, X_ref,
    n_bootstrap,
    rng_key,
):
    """Run n_bootstrap iterations in parallel via vmap."""
    keys = random.split(rng_key, n_bootstrap)

    boot_fn = vmap(
        lambda key: _bootstrap_iter(X_a, y_onehot_a, X_b, y_onehot_b,
                                     K, n_sim, X_ref, key)
    )
    return boot_fn(keys)


# ---------------------------------------------------------------------------
# Full single-pair estimate with bootstrap CI
# ---------------------------------------------------------------------------

def dr_estimate_single(
    X_a: np.ndarray,
    y_a: np.ndarray,
    X_b: np.ndarray,
    y_b: np.ndarray,
    X_ref: np.ndarray,
    K: int = 5,
    n_sim: int = 2000,
    n_bootstrap: int = 200,
    seed: int = 42,
) -> dict:
    """Full DR estimate for one pair with bootstrap CI."""
    X_a_j = jnp.array(X_a, dtype=DTYPE)
    X_b_j = jnp.array(X_b, dtype=DTYPE)
    X_ref_j = jnp.array(X_ref, dtype=DTYPE)

    y_a_oh = jnp.eye(K, dtype=DTYPE)[y_a]
    y_b_oh = jnp.eye(K, dtype=DTYPE)[y_b]

    rng = random.PRNGKey(seed)
    key1, key2 = random.split(rng)

    # Point estimate
    gamma_pt, nmi_pt, joint = _dr_estimate_single(
        X_a_j, y_a_oh, X_b_j, y_b_oh, K, n_sim, X_ref_j, key1
    )

    # Bootstrap CI
    boot_gammas = _bootstrap_all(
        X_a_j, y_a_oh, X_b_j, y_b_oh,
        K, n_sim, X_ref_j, n_bootstrap, key2
    )

    gamma_pt = float(gamma_pt)
    nmi_pt = float(nmi_pt)
    boot_np = np.array(boot_gammas)
    valid = np.isfinite(boot_np)
    if valid.sum() >= 10:
        ci_lo = float(np.percentile(boot_np[valid], 2.5))
        ci_hi = float(np.percentile(boot_np[valid], 97.5))
    else:
        ci_lo = ci_hi = gamma_pt

    return {
        "dr_gamma": round(gamma_pt, 4),
        "dr_ci_lo": round(ci_lo, 4),
        "dr_ci_hi": round(ci_hi, 4),
        "dr_nmi": round(nmi_pt, 4),
        "ci_width": round(ci_hi - ci_lo, 4),
        "excl_zero": bool(ci_lo > 0.0 or ci_hi < 0.0),
        "n_a": int(X_a.shape[0]),
        "n_b": int(X_b.shape[0]),
    }


# ---------------------------------------------------------------------------
# Data preparation helpers (NumPy, runs on CPU)
# ---------------------------------------------------------------------------

EDAD_ORDER = {
    "0-18": 0, "19-24": 1, "25-34": 2, "35-44": 3,
    "45-54": 4, "55-64": 5, "65+": 6,
}

SES_COLS = ["sexo", "edad", "escol", "Tam_loc"]


def _encode_ordinal(v):
    try:
        f = float(v)
        if f >= 97 or f < 0:
            return np.nan
        return f
    except (ValueError, TypeError):
        return np.nan


def encode_ses_numpy(df, ses_cols=None):
    """Encode SES columns to numeric matrix. Returns (X, valid_mask)."""
    if ses_cols is None:
        ses_cols = [c for c in SES_COLS if c in df.columns]

    parts = []
    for col in ses_cols:
        if col not in df.columns:
            continue
        s = df[col]
        if col == "sexo":
            encoded = s.map(lambda v: 0.0 if str(v).strip() in ("1", "1.0", "01")
                            else (1.0 if str(v).strip() in ("2", "2.0", "02") else np.nan))
        elif col == "edad":
            numeric = pd.to_numeric(s, errors="coerce")
            n_valid_numeric = numeric.notna().sum()
            n_unique = numeric.dropna().nunique()
            if n_valid_numeric > len(s) * 0.5 and n_unique > 20:
                encoded = numeric
            else:
                encoded = s.map(lambda v: float(EDAD_ORDER.get(str(v).strip(), np.nan)))
        else:
            encoded = s.apply(lambda v: _encode_ordinal(v))
        parts.append(encoded.values)

    X = np.column_stack(parts)
    valid = ~np.isnan(X).any(axis=1)
    return X, valid


def rank_normalize(v):
    """Midrank transform -> uniform [1, 10]. Matches Julia _rank_normalize."""
    n = len(v)
    if n <= 1:
        return v.copy()
    order = np.argsort(v, kind='mergesort')
    ranks = np.empty(n, dtype=np.float64)
    i = 0
    while i < n:
        j = i
        while j < n - 1 and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return 1.0 + ranks / max(n - 1, 1) * 9.0


def bin_to_5(vals):
    """Equal-frequency quantile binning -> integer categories 0..K-1."""
    clean = vals[np.isfinite(vals) & (vals >= 0) & (vals < 97)]
    if len(clean) == 0:
        return np.zeros(len(vals), dtype=np.int32)
    if len(np.unique(clean)) <= 5:
        cats = np.sort(np.unique(clean))
        mapping = {v: i for i, v in enumerate(cats)}
        return np.array([mapping.get(v, 0) for v in vals], dtype=np.int32)

    edges = np.percentile(clean, [0, 20, 40, 60, 80, 100])
    edges = np.unique(edges)
    bins = np.searchsorted(edges, vals, side='right') - 1
    bins = np.clip(bins, 0, len(edges) - 2)
    return bins.astype(np.int32)


def prepare_pair_data(df_a, col_a, df_b, col_b, ses_cols=None):
    """Prepare data for one pair. Supports cross-survey (different DataFrames).

    Returns (X_a, y_a, X_b, y_b, X_ref, K) or None if insufficient data.
    """
    def _prepare_outcome(df, col_name):
        X_ses, valid_ses = encode_ses_numpy(df, ses_cols)
        raw = df[col_name].values.copy().astype(float)
        sentinel = (raw >= 97) | (raw < 0) | np.isnan(raw)
        raw[sentinel] = np.nan
        valid_out = np.isfinite(raw) & valid_ses
        if valid_out.sum() < 30:
            return None, None, None
        X_clean = X_ses[valid_out]
        vals_clean = raw[valid_out]
        ranked = rank_normalize(vals_clean)
        binned = bin_to_5(ranked)
        K = len(np.unique(binned))
        if K < 3:
            return None, None, None
        return X_clean, binned, K

    result_a = _prepare_outcome(df_a, col_a)
    result_b = _prepare_outcome(df_b, col_b)
    if result_a[0] is None or result_b[0] is None:
        return None

    X_a, y_a, K_a = result_a
    X_b, y_b, K_b = result_b
    K = max(K_a, K_b)

    X_ref_pool = np.concatenate([X_a, X_b], axis=0)
    n_ref = min(2000, len(X_ref_pool))
    rng = np.random.default_rng(42)
    ref_idx = rng.choice(len(X_ref_pool), n_ref, replace=True)
    X_ref = X_ref_pool[ref_idx]

    return X_a, y_a, X_b, y_b, X_ref, K
