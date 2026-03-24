"""
JAX-accelerated Doubly Robust Bridge Estimator

GPU-batched port of the Julia DR bridge (dr_estimator.jl).
Runs 500-1000+ independent pairs simultaneously via jax.vmap.

Key design decisions:
  - Fixed-iteration Newton (30 steps main, 20 bootstrap) instead of variable-iteration
    Newton+trust-region. GPU requires uniform work across all vectorized calls.
  - Float32 for model fitting (GPU-friendly), float64 for gamma/NMI (precision).
  - Double vmap: pairs × bootstrap iterations = 100K+ fits in one GPU kernel.

Usage:
    from jax_dr_bridge import batch_dr_estimate, prepare_pair_data
    results = batch_dr_estimate(pairs_data, n_sim=2000, n_bootstrap=200)
"""
from __future__ import annotations

import os
# Metal backend: use GPU but bypass triangular_solve via manual Cholesky.
# Float64 not available on Metal — use float32 for all GPU computation.
os.environ.setdefault("JAX_ENABLE_X64", "0")

import jax
import jax.numpy as jnp
from jax import random, vmap, jit
from functools import partial
import numpy as np

DTYPE = jnp.float32

# ---------------------------------------------------------------------------
# Numerically stable sigmoid
# ---------------------------------------------------------------------------

@jit
def sigmoid(x):
    """Logistic sigmoid, numerically stable."""
    return jax.nn.sigmoid(x)


# ---------------------------------------------------------------------------
# Threshold encoding/decoding (unconstrained parametrization)
# ---------------------------------------------------------------------------

@jit
def decode_thresholds(gamma_params):
    """γ → ordered α via cumulative exp: α_k = α_{k-1} + exp(γ_k)."""
    return jnp.cumsum(
        jnp.concatenate([gamma_params[:1], jnp.exp(gamma_params[1:])])
    )


def encode_thresholds(alpha):
    """α → γ (inverse of decode). NumPy, used for initialization only."""
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
    """Negative log-likelihood of proportional-odds model.

    params: [β (p,), γ (K-1,)] concatenated
    X: (n, p) design matrix
    y_onehot: (n, K) one-hot encoded outcome
    K: number of categories
    """
    p = X.shape[1]
    beta = params[:p]
    gamma_params = params[p:]
    alpha = decode_thresholds(gamma_params)

    # Linear predictor: (n,)
    eta = X @ beta

    # Cumulative probabilities P(Y <= k | X) for k=1..K-1: (n, K-1)
    # alpha is (K-1,), eta is (n,) → broadcast to (n, K-1)
    cum_probs = sigmoid(alpha[None, :] - eta[:, None])

    # Cell probabilities P(Y = k | X): (n, K)
    # P(Y=1) = cum[1], P(Y=k) = cum[k] - cum[k-1], P(Y=K) = 1 - cum[K-1]
    zeros_col = jnp.zeros((X.shape[0], 1), dtype=cum_probs.dtype)
    ones_col = jnp.ones((X.shape[0], 1), dtype=cum_probs.dtype)
    cum_full = jnp.concatenate([zeros_col, cum_probs, ones_col], axis=1)
    cell_probs = cum_full[:, 1:] - cum_full[:, :-1]
    cell_probs = jnp.maximum(cell_probs, 1e-12)

    # Log-likelihood: sum of log P(Y = y_i | X_i)
    ll = jnp.sum(y_onehot * jnp.log(cell_probs))
    return -ll


# ---------------------------------------------------------------------------
# Manual Cholesky solver — bypasses mhlo.triangular_solve (Metal-compatible)
#
# For SPD matrix A and vector b, solves A @ x = b via:
#   1. Cholesky: A = L @ L.T  (using only sqrt, multiply, subtract)
#   2. Forward substitution: L @ z = b  (sequential scan, 8 steps)
#   3. Backward substitution: L.T @ x = z  (sequential scan, 8 steps)
#
# All operations use only matmul, element-wise ops, and indexing —
# all supported on Metal GPU. No triangular_solve XLA op needed.
# ---------------------------------------------------------------------------

@jit
def _cholesky_manual(A):
    """Cholesky decomposition A = L @ L.T for small SPD matrix.

    Uses a jax.lax.fori_loop over columns. For n=8 this is 8 iterations.
    Only uses element-wise ops + sqrt — fully Metal-compatible.
    """
    n = A.shape[0]
    L = jnp.zeros_like(A)

    def col_step(j, L):
        # Compute L[j, :j] and L[j, j]
        # L[j, i] = (A[j, i] - sum(L[j, :i] * L[i, :i])) / L[i, i]  for i < j
        # L[j, j] = sqrt(A[j, j] - sum(L[j, :j]^2))

        def row_step(i, L):
            s = jnp.sum(L[j, :] * L[i, :])  # dot product of rows j and i
            val = (A[j, i] - s) / jnp.maximum(L[i, i], 1e-12)
            L = L.at[j, i].set(val)
            return L

        L = jax.lax.fori_loop(0, j, row_step, L)
        s = jnp.sum(L[j, :] ** 2)
        diag_val = jnp.sqrt(jnp.maximum(A[j, j] - s, 1e-12))
        L = L.at[j, j].set(diag_val)
        return L

    L = jax.lax.fori_loop(0, n, col_step, L)
    return L


@jit
def _forward_sub(L, b):
    """Solve L @ z = b where L is lower triangular. Sequential scan."""
    n = L.shape[0]
    z = jnp.zeros_like(b)

    def step(i, z):
        s = jnp.sum(L[i, :] * z)
        val = (b[i] - s) / jnp.maximum(L[i, i], 1e-12)
        z = z.at[i].set(val)
        return z

    return jax.lax.fori_loop(0, n, step, z)


@jit
def _backward_sub(LT, z):
    """Solve L.T @ x = z where L.T is upper triangular. Reverse scan."""
    n = LT.shape[0]
    x = jnp.zeros_like(z)

    def step(i_rev, x):
        i = n - 1 - i_rev
        s = jnp.sum(LT[i, :] * x)
        val = (z[i] - s) / jnp.maximum(LT[i, i], 1e-12)
        x = x.at[i].set(val)
        return x

    return jax.lax.fori_loop(0, n, step, x)


@jit
def solve_spd(A, b):
    """Solve A @ x = b for SPD matrix A via manual Cholesky.

    No triangular_solve XLA op — fully Metal GPU compatible.
    For 8×8 matrices: 8+8+8 = 24 sequential steps, trivial cost.
    """
    L = _cholesky_manual(A)
    z = _forward_sub(L, b)
    x = _backward_sub(L.T, z)
    return x


# ---------------------------------------------------------------------------
# Fixed-iteration Newton optimizer (GPU-friendly, Metal-compatible)
# ---------------------------------------------------------------------------

@partial(jit, static_argnums=(3, 4))
def fit_ordered_logit_newton(X, y_onehot, params0, K, n_iter=30):
    """Fit ordered logit via fixed-iteration Newton steps.

    Returns params (β, γ) after n_iter Newton iterations.
    Globally concave → Newton always converges in ~15-25 steps.
    Uses manual Cholesky solver instead of jnp.linalg.solve.
    """
    nll_fn = lambda p: ordered_logit_nll(p, X, y_onehot, K)
    grad_fn = jax.grad(nll_fn)
    hess_fn = jax.hessian(nll_fn)

    def newton_step(params, _):
        g = grad_fn(params)
        H = hess_fn(params)
        # Regularize Hessian: ensure SPD for Cholesky
        H_reg = H + 1e-4 * jnp.eye(H.shape[0], dtype=H.dtype)
        # Newton step via manual Cholesky (no triangular_solve op)
        delta = solve_spd(H_reg, g)
        # Damped step (trust-region-like)
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
    """Fit logistic regression via fixed-iteration Newton. Metal-compatible."""
    nll_fn = lambda b: logistic_nll(b, X, y)
    grad_fn = jax.grad(nll_fn)
    hess_fn = jax.hessian(nll_fn)

    def newton_step(beta, _):
        g = grad_fn(beta)
        H = hess_fn(beta)
        H_reg = H + 1e-4 * jnp.eye(H.shape[0], dtype=H.dtype)
        delta = solve_spd(H_reg, g)
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
    cum_probs = sigmoid(alpha[None, :] - eta[:, None])

    zeros_col = jnp.zeros((X.shape[0], 1), dtype=cum_probs.dtype)
    ones_col = jnp.ones((X.shape[0], 1), dtype=cum_probs.dtype)
    cum_full = jnp.concatenate([zeros_col, cum_probs, ones_col], axis=1)
    cell_probs = cum_full[:, 1:] - cum_full[:, :-1]
    cell_probs = jnp.maximum(cell_probs, 1e-10)
    # Normalize rows
    cell_probs = cell_probs / cell_probs.sum(axis=1, keepdims=True)
    return cell_probs


@jit
def predict_logistic(beta, X):
    """P(y=1|X) from logistic coefficients."""
    return sigmoid(X @ beta)


# ---------------------------------------------------------------------------
# Goodman-Kruskal gamma from joint table (float64 for precision)
# ---------------------------------------------------------------------------

@jit
def goodman_kruskal_gamma(joint):
    """γ from K_a × K_b joint probability table."""
    joint = joint.astype(jnp.float32)
    Ka, Kb = joint.shape
    concordant = jnp.float32(0.0)
    discordant = jnp.float32(0.0)

    # Cumulative sums for efficient concordant/discordant computation
    # C_ij = joint[i,j] * sum(joint[i+1:, j+1:])
    # D_ij = joint[i,j] * sum(joint[i+1:, :j])
    # Use reversed cumsum trick for O(K²) instead of O(K⁴)
    below_right = jnp.zeros_like(joint)
    below_left = jnp.zeros_like(joint)

    # Compute sum of joint[i+1:, j+1:] and joint[i+1:, :j] for each (i,j)
    # Start from bottom-right corner
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
    joint = joint.astype(jnp.float32)
    p = joint / jnp.maximum(jnp.sum(joint), 1e-12)
    p_a = jnp.sum(p, axis=1)
    p_b = jnp.sum(p, axis=0)

    h_a = -jnp.sum(jnp.where(p_a > 0, p_a * jnp.log(p_a), 0.0))
    h_b = -jnp.sum(jnp.where(p_b > 0, p_b * jnp.log(p_b), 0.0))
    min_h = jnp.minimum(h_a, h_b)

    # MI
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
    X_a, y_onehot_a,    # survey A: (n_a, p), (n_a, K)
    X_b, y_onehot_b,    # survey B: (n_b, p), (n_b, K)
    K,                   # number of outcome categories (static)
    n_sim,               # reference population size (static)
    X_ref,               # shared reference SES population: (n_sim, p)
    rng_key,             # JAX PRNG key
):
    """Single DR estimate: fit models, build joint table, compute gamma."""
    p = X_a.shape[1]
    n_params = p + (K - 1)

    # Initialize: β=0, γ from uniform cumulative proportions
    # For K=5: α = [-1.4, -0.4, 0.4, 1.4] (logit of 0.2, 0.4, 0.6, 0.8)
    uniform_cum = jnp.linspace(1.0 / K, 1.0 - 1.0 / K, K - 1)
    alpha_init = jnp.log(uniform_cum / (1.0 - uniform_cum))  # logit
    gamma_init = jnp.concatenate([alpha_init[:1],
                                   jnp.log(jnp.maximum(jnp.diff(alpha_init), 1e-6))])
    params0 = jnp.concatenate([jnp.zeros(p, dtype=DTYPE), gamma_init.astype(DTYPE)])

    # Step 1: Fit outcome models
    params_a = fit_ordered_logit_newton(X_a, y_onehot_a, params0, K, 30)
    params_b = fit_ordered_logit_newton(X_b, y_onehot_b, params0, K, 30)

    # Step 2: Propensity model
    n_a, n_b = X_a.shape[0], X_b.shape[0]
    X_pooled = jnp.concatenate([X_a, X_b], axis=0)
    # Add intercept
    Xc = jnp.concatenate([jnp.ones((X_pooled.shape[0], 1), dtype=DTYPE), X_pooled], axis=1)
    delta = jnp.concatenate([jnp.ones(n_a, dtype=DTYPE), jnp.zeros(n_b, dtype=DTYPE)])
    prop_beta0 = jnp.zeros(Xc.shape[1], dtype=DTYPE)
    prop_beta = fit_logistic_newton(Xc, delta, prop_beta0, 20)

    # Step 3: Build joint table on reference population
    Pa_ref = predict_proba_ordered(params_a, X_ref, K)[:, :K]  # (n_sim, K)
    Pb_ref = predict_proba_ordered(params_b, X_ref, K)[:, :K]  # (n_sim, K)

    # joint[k,l] = mean_i Pa[i,k] * Pb[i,l]
    joint = (Pa_ref.T @ Pb_ref) / n_sim  # (K, K)
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
    """One bootstrap iteration: resample → refit → gamma."""
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
    return boot_fn(keys)  # (n_bootstrap,) array of gamma values


# ---------------------------------------------------------------------------
# Full single-pair estimate with bootstrap CI
# ---------------------------------------------------------------------------

def dr_estimate_single(
    X_a: np.ndarray,       # (n_a, p) SES design matrix
    y_a: np.ndarray,       # (n_a,) integer outcome 0..K-1
    X_b: np.ndarray,       # (n_b, p)
    y_b: np.ndarray,       # (n_b,) integer outcome 0..K-1
    X_ref: np.ndarray,     # (n_sim, p) reference SES population
    K: int = 5,
    n_sim: int = 2000,
    n_bootstrap: int = 200,
    seed: int = 42,
) -> dict:
    """Full DR estimate for one pair with bootstrap CI.

    Inputs are NumPy arrays. Conversion to JAX happens internally.
    """
    # Convert to JAX arrays
    X_a_j = jnp.array(X_a, dtype=DTYPE)
    X_b_j = jnp.array(X_b, dtype=DTYPE)
    X_ref_j = jnp.array(X_ref, dtype=DTYPE)

    # One-hot encode outcomes
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

    # CI from bootstrap distribution
    gamma_pt = float(gamma_pt)
    nmi_pt = float(nmi_pt)
    boot_np = np.array(boot_gammas)
    # Filter out NaN/Inf from failed bootstraps
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
        "excl_zero": ci_lo > 0.0 or ci_hi < 0.0,
        "n_a": X_a.shape[0],
        "n_b": X_b.shape[0],
    }


# ---------------------------------------------------------------------------
# Data preparation helpers (NumPy, runs on CPU)
# ---------------------------------------------------------------------------

# SES encoding maps (matching Julia/Python implementations)
EDAD_ORDER = {
    "0-18": 0, "19-24": 1, "25-34": 2, "35-44": 3,
    "45-54": 4, "55-64": 5, "65+": 6,
}

SES_COLS = ["sexo", "edad", "escol", "Tam_loc"]


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
            encoded = s.map(lambda v: float(EDAD_ORDER.get(str(v).strip(), np.nan)))
        else:
            encoded = s.apply(lambda v: _encode_ordinal(v))
        parts.append(encoded.values)

    X = np.column_stack(parts)
    valid = ~np.isnan(X).any(axis=1)
    return X, valid


def _encode_ordinal(v):
    try:
        f = float(v)
        if f >= 97 or f < 0:
            return np.nan
        return f
    except (ValueError, TypeError):
        return np.nan


def rank_normalize(v):
    """Midrank transform → uniform [1, 10]. Matches Julia _rank_normalize."""
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
    """Equal-frequency quantile binning → integer categories 0..K-1."""
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


def prepare_pair_data(df, col_a, col_b, ses_cols=None):
    """Prepare data for one pair from a single DataFrame (within-survey).

    Returns (X_a, y_a, X_b, y_b, X_ref, K) or None if insufficient data.
    """
    import pandas as pd

    X_ses, valid_ses = encode_ses_numpy(df, ses_cols)

    def _prepare_outcome(col_name):
        raw = df[col_name].values.copy().astype(float)
        # Sentinel filter
        sentinel = (raw >= 97) | (raw < 0) | np.isnan(raw)
        raw[sentinel] = np.nan
        valid_out = np.isfinite(raw) & valid_ses
        if valid_out.sum() < 30:
            return None, None, None, None
        X_clean = X_ses[valid_out]
        vals_clean = raw[valid_out]
        # Rank normalize then bin
        ranked = rank_normalize(vals_clean)
        binned = bin_to_5(ranked)
        K = len(np.unique(binned))
        if K < 3:
            return None, None, None, None
        return X_clean, binned, K, valid_out

    result_a = _prepare_outcome(col_a)
    result_b = _prepare_outcome(col_b)
    if result_a[0] is None or result_b[0] is None:
        return None

    X_a, y_a, K_a, mask_a = result_a
    X_b, y_b, K_b, mask_b = result_b

    # Use consistent K (max of both)
    K = max(K_a, K_b)

    # Reference population: pool both valid sets
    X_ref_pool = np.concatenate([X_a, X_b], axis=0)
    n_ref = min(2000, len(X_ref_pool))
    rng = np.random.default_rng(42)
    ref_idx = rng.choice(len(X_ref_pool), n_ref, replace=True)
    X_ref = X_ref_pool[ref_idx]

    return X_a, y_a, X_b, y_b, X_ref, K


# ---------------------------------------------------------------------------
# Batch sweep over pairs
# ---------------------------------------------------------------------------

def sweep_within_survey(
    df,
    pairs: list[tuple[str, str]],
    n_sim: int = 2000,
    n_bootstrap: int = 200,
    ses_cols=None,
    verbose: bool = True,
) -> dict:
    """Run DR estimates for all pairs within a single survey DataFrame.

    Returns dict of {pair_key: result_dict}.
    """
    import time

    results = {}
    n_done = 0
    n_skip = 0
    n_sig = 0
    t0 = time.time()

    for i, (col_a, col_b) in enumerate(pairs):
        pair_key = f"{col_a}::{col_b}"

        data = prepare_pair_data(df, col_a, col_b, ses_cols)
        if data is None:
            n_skip += 1
            continue

        X_a, y_a, X_b, y_b, X_ref, K = data

        try:
            result = dr_estimate_single(
                X_a, y_a, X_b, y_b, X_ref,
                K=K, n_sim=n_sim, n_bootstrap=n_bootstrap,
                seed=i + 1,
            )
            results[pair_key] = result
            n_done += 1
            if result["excl_zero"]:
                n_sig += 1
        except Exception as e:
            n_skip += 1
            if verbose:
                print(f"  [{pair_key}] ERROR: {e}")
            continue

        if verbose and (n_done + n_skip) % 25 == 0:
            elapsed = time.time() - t0
            rate = (n_done + n_skip) / max(elapsed, 0.01)
            remain = (len(pairs) - n_done - n_skip) / max(rate, 0.01)
            print(f"  [{n_done + n_skip}/{len(pairs)}] "
                  f"done={n_done} skip={n_skip} sig={n_sig} "
                  f"{rate:.1f}/s ETA={remain:.0f}s")

    if verbose:
        elapsed = time.time() - t0
        print(f"\nComplete: {n_done} estimates, {n_skip} skipped, "
              f"{n_sig} significant ({100 * n_sig / max(n_done, 1):.1f}%) "
              f"in {elapsed:.1f}s")

    return results
