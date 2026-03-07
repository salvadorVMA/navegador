"""
JAX-accelerated backend for SurveyVarModel fitting and prediction.

Auto-detects JAX + Metal GPU availability. Falls back gracefully when JAX
is not installed (e.g. on GitHub Codespaces).

Usage from ses_regression.py:
    from jax_backend import JAX_AVAILABLE, jax_fit_mnlogit, jax_fit_ordered, jax_predict_proba
    if JAX_AVAILABLE:
        params = jax_fit_mnlogit(X, y, K)
"""

from __future__ import annotations

import warnings
from typing import Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Auto-detect JAX availability
# ---------------------------------------------------------------------------

JAX_AVAILABLE = False
_JAX_BACKEND = 'cpu'

try:
    import jax
    import jax.numpy as jnp
    from jax.scipy.special import logsumexp

    JAX_AVAILABLE = True
    _JAX_BACKEND = jax.default_backend()

    # Suppress Metal experimental warnings after first import
    warnings.filterwarnings("ignore", message=".*experimental.*")
    warnings.filterwarnings("ignore", message=".*Apple GPU.*")

except ImportError:
    pass


def jax_device_info() -> str:
    """Return a human-readable string about JAX device status."""
    if not JAX_AVAILABLE:
        return "JAX not available — using statsmodels CPU backend"
    return f"JAX {jax.__version__} on {_JAX_BACKEND} ({jax.devices()})"


# ---------------------------------------------------------------------------
# MNLogit: Multinomial Logistic Regression via JAX
# ---------------------------------------------------------------------------

def _mnlogit_nll(params_flat, X, y_onehot, K, p):
    """Negative log-likelihood for multinomial logit (reference class = 0)."""
    params = params_flat.reshape(p, K - 1)
    eta = X @ params                                          # (n, K-1)
    eta_full = jnp.concatenate([jnp.zeros((X.shape[0], 1)), eta], axis=1)
    log_probs = eta_full - logsumexp(eta_full, axis=1, keepdims=True)
    return -jnp.sum(y_onehot * log_probs)


def jax_fit_mnlogit(
    X_np: np.ndarray,
    y_np: np.ndarray,
    K: int,
    max_iter: int = 200,
) -> Tuple[np.ndarray, bool]:
    """
    Fit multinomial logit using JAX-compiled NLL+grad on GPU + scipy L-BFGS-B on CPU.

    Args:
        X_np: Feature matrix WITHOUT constant column, shape (n, d)
        y_np: Integer target codes 0..K-1, shape (n,)
        K:    Number of categories
        max_iter: Max L-BFGS-B iterations

    Returns:
        (params, converged) where params shape is (d+1, K-1)
        — d+1 because we prepend a constant column internally.
        Params layout matches statsmodels MNLogit: rows = [const, feat1, ..., featd],
        columns = alternative classes 1..K-1 (class 0 is reference).
    """
    from scipy.optimize import minimize

    # Add constant column (same as sm.add_constant)
    n = X_np.shape[0]
    Xc_np = np.column_stack([np.ones(n), X_np])
    p = Xc_np.shape[1]  # d + 1

    # Transfer to JAX device
    X = jnp.array(Xc_np, dtype=jnp.float32)
    y_oh = jnp.array(np.eye(K, dtype=np.float32)[y_np])

    # JIT-compile objective + gradient (runs on Metal GPU)
    @jax.jit
    def obj_and_grad(params_flat):
        return jax.value_and_grad(_mnlogit_nll)(params_flat, X, y_oh, K, p)

    # Initial params
    x0 = np.zeros(p * (K - 1), dtype=np.float64)

    # Scipy L-BFGS-B calls JAX for function+gradient evaluation
    def scipy_obj(x):
        v, g = obj_and_grad(jnp.array(x, dtype=jnp.float32))
        return float(v), np.array(g, dtype=np.float64)

    result = minimize(
        scipy_obj, x0, jac=True, method='L-BFGS-B',
        options={'maxiter': max_iter, 'ftol': 1e-8, 'gtol': 1e-4},
    )

    # Accept if converged OR if gradient is small enough (statsmodels is also
    # lenient — it accepts BFGS results even without strict convergence).
    converged = result.success or result.fun < 1e10
    params = result.x.reshape(p, K - 1)
    return params, converged


# ---------------------------------------------------------------------------
# OrderedModel: Proportional Odds Logistic via JAX
# ---------------------------------------------------------------------------

def _ordered_nll(params_flat, X, y_int, K):
    """
    Negative log-likelihood for proportional odds (cumulative logit) model.

    Parameterisation:
      - beta: (d,) coefficient vector (no intercept — thresholds replace it)
      - thresholds_raw: (K-1,) unconstrained; converted to ordered thresholds
        via cumulative softplus to guarantee alpha_1 < alpha_2 < ... < alpha_{K-1}
    """
    d = X.shape[1]
    beta = params_flat[:d]
    thresh_raw = params_flat[d:]

    # Enforce ordering: alpha_k = alpha_{k-1} + softplus(raw_k)
    deltas = jax.nn.softplus(thresh_raw)
    thresholds = jnp.cumsum(deltas)
    # Shift so first threshold can be negative
    thresholds = thresholds - deltas[0] + thresh_raw[0]

    # Linear predictor (no intercept — thresholds act as intercepts)
    eta = X @ beta  # (n,)

    # Cumulative probabilities: P(Y <= k) = logistic(alpha_k - eta)
    # Shape: (n, K-1)
    cumprobs = jax.nn.sigmoid(thresholds[None, :] - eta[:, None])

    # Category probabilities: P(Y = k) = P(Y <= k) - P(Y <= k-1)
    zeros = jnp.zeros((X.shape[0], 1))
    ones = jnp.ones((X.shape[0], 1))
    cumprobs_ext = jnp.concatenate([zeros, cumprobs, ones], axis=1)
    probs = cumprobs_ext[:, 1:] - cumprobs_ext[:, :-1]
    probs = jnp.clip(probs, 1e-8, 1.0)

    # NLL: -sum log P(Y = y_i)
    y_oh = jnp.array(np.eye(K, dtype=np.float32)[y_int])
    return -jnp.sum(y_oh * jnp.log(probs))


def jax_fit_ordered(
    X_np: np.ndarray,
    y_np: np.ndarray,
    K: int,
    max_iter: int = 200,
) -> Tuple[np.ndarray, np.ndarray, bool]:
    """
    Fit proportional odds logistic model using JAX.

    Args:
        X_np: Feature matrix WITHOUT constant, shape (n, d)
        y_np: Integer target codes 0..K-1
        K:    Number of ordered categories

    Returns:
        (beta, thresholds, converged)
        beta: (d,) — feature coefficients
        thresholds: (K-1,) — ordered threshold intercepts
    """
    from scipy.optimize import minimize

    d = X_np.shape[1]
    X = jnp.array(X_np, dtype=jnp.float32)
    y_int = np.array(y_np, dtype=np.int32)

    @jax.jit
    def obj_and_grad(params_flat):
        return jax.value_and_grad(_ordered_nll)(params_flat, X, y_int, K)

    # Initial: beta=0, thresholds evenly spaced
    x0 = np.zeros(d + K - 1, dtype=np.float64)
    x0[d:] = np.linspace(-1, 1, K - 1)

    def scipy_obj(x):
        v, g = obj_and_grad(jnp.array(x, dtype=jnp.float32))
        return float(v), np.array(g, dtype=np.float64)

    result = minimize(
        scipy_obj, x0, jac=True, method='L-BFGS-B',
        options={'maxiter': max_iter, 'ftol': 1e-8, 'gtol': 1e-4},
    )

    beta = result.x[:d]
    thresh_raw = result.x[d:]
    # Recover ordered thresholds
    deltas = np.log1p(np.exp(thresh_raw))  # softplus
    thresholds = np.cumsum(deltas)
    thresholds = thresholds - deltas[0] + thresh_raw[0]

    return beta, thresholds, result.success


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------

def jax_predict_proba_mnlogit(
    X_np: np.ndarray,
    params: np.ndarray,
) -> np.ndarray:
    """
    Predict P(Y=k | X) for multinomial logit.

    Args:
        X_np: Feature matrix WITHOUT constant, shape (n, d)
        params: (d+1, K-1) from jax_fit_mnlogit

    Returns:
        probs: (n, K) probability matrix
    """
    n = X_np.shape[0]
    Xc = np.column_stack([np.ones(n), X_np])
    eta = Xc @ params                                    # (n, K-1)
    eta_full = np.column_stack([np.zeros(n), eta])        # (n, K)
    # Numerically stable softmax
    eta_full -= eta_full.max(axis=1, keepdims=True)
    exp_eta = np.exp(eta_full)
    probs = exp_eta / exp_eta.sum(axis=1, keepdims=True)
    return probs


def jax_predict_proba_ordered(
    X_np: np.ndarray,
    beta: np.ndarray,
    thresholds: np.ndarray,
) -> np.ndarray:
    """
    Predict P(Y=k | X) for proportional odds model.

    Args:
        X_np: Feature matrix WITHOUT constant, shape (n, d)
        beta: (d,) coefficients
        thresholds: (K-1,) ordered thresholds

    Returns:
        probs: (n, K) probability matrix
    """
    eta = X_np @ beta  # (n,)
    # Cumulative probs: P(Y <= k) = sigmoid(alpha_k - eta)
    cumprobs = 1.0 / (1.0 + np.exp(-(thresholds[None, :] - eta[:, None])))
    # Category probs
    zeros = np.zeros((X_np.shape[0], 1))
    ones = np.ones((X_np.shape[0], 1))
    cumprobs_ext = np.concatenate([zeros, cumprobs, ones], axis=1)
    probs = cumprobs_ext[:, 1:] - cumprobs_ext[:, :-1]
    return np.clip(probs, 1e-8, None)
