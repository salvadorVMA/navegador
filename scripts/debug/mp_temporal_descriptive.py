"""
Temporal Dynamics for Mexico W3-W7 — Velocity, Equilibrium, Forecast
====================================================================

Stage 5 of the message-passing framework.

What this computes
------------------
Given the 5 Mexico temporal weight matrices (W3=1996, W4=2001, W5=2007,
W6=2012, W7=2018), each a 52x52 matrix of DR bridge gamma values, we study
how the SES-mediated construct network evolves over time.  The key analyses:

1. **Velocity field**.  For each wave, given a vector of mean construct
   responses x, the velocity at each construct is the net "pull" exerted by
   its neighbors:
       v_i = sum_j w_ij * (x_j - x_i)
   Positive velocity means the network is pulling construct i upward (toward
   higher values); negative means downward.  This is the signed Laplacian
   force — NOT the absolute-value Laplacian from spectral analysis.

2. **Equilibrium distance**.  The degree-weighted consensus value:
       x* = sum(d_i * x_i) / sum(d_i),    d_i = sum_j |w_ij|
   and the L2 distance ||x - x*|| measures how far the response vector is
   from the network's "natural resting point" — the state where all velocity
   is zero.  Decreasing equilibrium distance across waves suggests the
   network is settling; increasing suggests external shocks.

3. **Residual analysis**.  Using the absolute-value row-normalized adjacency
   as a predictor:
       x_hat(t+1) = A(t) @ x(t)
   The residual x(t+1) - x_hat measures what the network structure at time t
   CANNOT explain about responses at time t+1.  Large positive residuals
   indicate constructs that shifted more than network diffusion predicts
   (external shocks, generational change).

4. **Constrained 1-parameter forecast**.  A single parameter alpha blends
   network diffusion and persistence:
       x_hat(t+1) = alpha * A(t) @ x(t) + (1 - alpha) * x(t)
   alpha=1 means pure network diffusion; alpha=0 means pure persistence.
   We fit alpha* by least-squares over all transitions, then forecast W8:
       x_hat(W8) = alpha* * A(W7) @ x(W7) + (1 - alpha*) * x(W7)
   The 1-parameter constraint means we can make directional claims (up/down)
   even if magnitudes are unreliable.

5. **Uncertainty envelope**.  Per-construct sigma = std(residuals across 4
   transitions).  80% CI: x_hat +/- 1.28*sigma.  We flag constructs where
   sigma > |shift| (noise-dominated) and where the CI excludes the current
   W7 value (directional claim survives uncertainty).

6. **Linear trends**.  OLS per construct: x(year) = a + b*year.  The trend
   direction is compared against the network forecast direction to identify
   trend reversals (constructs where the network predicts a different
   direction than the historical trend).

Mean construct responses
------------------------
The weight matrices contain only gamma values (SES bridge strengths), not
mean responses.  Mean responses must be supplied externally:

  --means-file path/to/means.json
      Load pre-computed means from JSON (structure: {wave_str: {construct: mean}})

  --synthetic
      Generate structurally plausible synthetic means from the weight matrices
      themselves (mean of absolute row sums, scaled to [1,10]).  This allows
      the script to run end-to-end without microdata access, but the means
      are NOT empirically grounded.

  --compute-means
      Stub: prints a message about needing wvs_loader.  Not yet implemented.

Output
------
JSON in data/tda/message_passing/mex_temporal.json:
  - temporal_core: the 20 constructs present in all 5 waves
  - velocity_fields: per-wave top-5 velocities (magnitude and direction)
  - equilibrium_distances: trajectory across 5 waves
  - residuals: per-transition (4 transitions), per-construct
  - forecast: alpha_star, per-transition alphas, RMSE, W8 predictions
  - uncertainty: per-construct sigma, 80% CI, flags
  - trends: per-construct slope, R^2, direction vs. forecast comparison

Usage
-----
    python scripts/debug/mp_temporal_descriptive.py --synthetic
    python scripts/debug/mp_temporal_descriptive.py --means-file data/wvs/wave_means.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ── Project paths ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import (  # noqa: E402
    fill_nan_zero,
    get_output_dir,
    load_manifest,
    load_temporal_manifest,
    load_temporal_matrix,
    load_weight_matrix,
    row_normalize,
    save_json,
)

# ── Waves and years ──────────────────────────────────────────────────────────
# Mexico appears in WVS waves 3-7.  Wave-year mapping from the temporal
# manifest.  Hardcoded here as a constant for readability; validated against
# the manifest at load time.

WAVES = [3, 4, 5, 6, 7]
WAVE_YEARS = {3: 1996, 4: 2001, 5: 2007, 6: 2012, 7: 2018}


# ═════════════════════════════════════════════════════════════════════════════
# load_all_temporal — Load all 5 wave matrices and identify temporal core
# ═════════════════════════════════════════════════════════════════════════════

def load_all_temporal() -> dict:
    """
    Load all 5 temporal weight matrices and identify construct availability.

    A construct is "present" in a wave if its row in the weight matrix has
    at least one non-zero, non-NaN entry.  The "temporal core" is the
    intersection of present constructs across all 5 waves — these are the
    only constructs for which we can track continuous trajectories.

    Returns
    -------
    data : dict with keys:
        - matrices : {wave_int: np.ndarray}  — raw 52x52 weight matrices
        - labels : list[str]                 — 52 construct labels
        - present : {wave_int: set[int]}     — indices of present constructs
        - temporal_core : list[int]          — sorted indices present in ALL waves
        - n_constructs : int                 — total constructs (52)
    """
    # ── Load the temporal manifest for validation ────────────────────────
    manifest = load_temporal_manifest()
    manifest_years = {int(k): v for k, v in manifest["wave_years"].items()}

    # Validate wave-year mapping
    for w in WAVES:
        assert manifest_years.get(w) == WAVE_YEARS[w], (
            f"Wave {w} year mismatch: expected {WAVE_YEARS[w]}, "
            f"manifest says {manifest_years.get(w)}"
        )

    # ── Load each wave's weight matrix ───────────────────────────────────
    matrices = {}
    labels = None
    present = {}

    for wave in WAVES:
        W, wave_labels = load_temporal_matrix(wave)
        matrices[wave] = W

        # All waves share the same 52 construct labels (from the same
        # construct_index).  Verify consistency.
        if labels is None:
            labels = wave_labels
        else:
            assert labels == wave_labels, (
                f"Wave {wave} labels differ from wave {WAVES[0]}"
            )

        # ── Identify present constructs ──────────────────────────────
        # A construct is present if its row has any non-zero, non-NaN entry.
        # Empty rows (all NaN or all zero) indicate constructs not measured
        # in this wave.
        k = W.shape[0]
        present_set = set()
        for i in range(k):
            row = W[i, :]
            # Check: any entry that is both non-NaN AND non-zero
            valid = (~np.isnan(row)) & (row != 0.0)
            if valid.any():
                present_set.add(i)
        present[wave] = present_set

    # ── Temporal core: intersection across all 5 waves ───────────────────
    # Only constructs present in ALL waves can be tracked continuously.
    temporal_core = set(present[WAVES[0]])
    for wave in WAVES[1:]:
        temporal_core = temporal_core & present[wave]
    temporal_core = sorted(temporal_core)  # deterministic ordering

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n  Temporal data loaded:")
    print(f"    {len(labels)} total constructs, {len(temporal_core)} in temporal core")
    for wave in WAVES:
        n_present = len(present[wave])
        n_empty = len(labels) - n_present
        print(f"    W{wave} ({WAVE_YEARS[wave]}): "
              f"{n_present} present, {n_empty} empty rows")

    return {
        "matrices": matrices,
        "labels": labels,
        "present": present,
        "temporal_core": temporal_core,
        "n_constructs": len(labels),
    }


# ═════════════════════════════════════════════════════════════════════════════
# velocity_field — Signed Laplacian force on construct responses
# ═════════════════════════════════════════════════════════════════════════════

def velocity_field(W: np.ndarray, x: np.ndarray) -> np.ndarray:
    """
    Compute the velocity field: the net "pull" on each construct's mean
    response from its neighbors in the signed gamma network.

    For each construct i with mean response x_i:
        v_i = sum_j w_ij * (x_j - x_i)   [only over valid edges]

    Positive v_i means neighbors (weighted by gamma sign and magnitude)
    pull construct i toward higher values.  Negative means the opposite.

    Note the SIGNED weight matrix is used — not |W|.  A positive gamma
    between constructs A and B means they co-move: if A is higher, the
    network "wants" B to be higher too.  The velocity captures this
    directional coupling.

    Parameters
    ----------
    W : (k, k) ndarray
        Signed weight matrix (NaN for missing edges).
    x : (k,) ndarray
        Mean construct responses.

    Returns
    -------
    v : (k,) ndarray
        Velocity at each construct.  NaN for constructs with no edges
        (isolated nodes have no neighbors to pull them).
    """
    k = W.shape[0]
    v = np.full(k, np.nan)

    # Replace NaN edges with 0 so they contribute nothing to the sum
    W_clean = fill_nan_zero(W)

    for i in range(k):
        # Check if construct i has any edges at all
        row_abs = np.abs(W_clean[i, :])
        if row_abs.sum() == 0:
            continue  # isolated: no edges → NaN velocity (no information)

        # v_i = sum_j w_ij * (x_j - x_i)
        # This is equivalent to (W_clean[i,:] @ x) - x_i * sum(W_clean[i,:])
        # but the explicit loop makes the physics clearer.
        pull = 0.0
        for j in range(k):
            if W_clean[i, j] != 0.0 and not np.isnan(x[j]):
                pull += W_clean[i, j] * (x[j] - x[i])
        v[i] = pull

    return v


# ═════════════════════════════════════════════════════════════════════════════
# equilibrium_distance — Distance from degree-weighted consensus
# ═════════════════════════════════════════════════════════════════════════════

def equilibrium_distance(W: np.ndarray, x: np.ndarray) -> float:
    """
    Compute the L2 distance from the current response vector to the
    degree-weighted consensus equilibrium.

    The equilibrium state is the degree-weighted mean:
        x* = sum(d_i * x_i) / sum(d_i)
    where d_i = sum_j |w_ij| is the weighted degree of construct i.

    At x*, the velocity field is zero under a linear coupling model.
    The distance ||x - x*|| measures how far from this resting state
    the system is.

    Only constructs with edges (d_i > 0) and valid x_i contribute.

    Parameters
    ----------
    W : (k, k) ndarray
        Weight matrix (NaN for missing edges).
    x : (k,) ndarray
        Mean construct responses.

    Returns
    -------
    dist : float
        L2 distance from x to equilibrium, over present constructs.
    """
    # Absolute weight matrix, NaN → 0
    W_abs = fill_nan_zero(np.abs(W))

    # Degree vector: d_i = sum of absolute edge weights
    d = W_abs.sum(axis=1)  # (k,)

    # Only include constructs with edges and valid mean
    valid = (d > 0) & (~np.isnan(x))

    if valid.sum() == 0:
        return np.nan

    d_valid = d[valid]
    x_valid = x[valid]

    # Degree-weighted consensus
    x_star = np.sum(d_valid * x_valid) / np.sum(d_valid)

    # L2 distance from consensus
    dist = np.sqrt(np.sum((x_valid - x_star) ** 2))

    return float(dist)


# ═════════════════════════════════════════════════════════════════════════════
# compute_residuals — Prediction error from network diffusion
# ═════════════════════════════════════════════════════════════════════════════

def compute_residuals(
    W_t: np.ndarray,
    x_t: np.ndarray,
    x_next: np.ndarray,
    labels: list[str],
) -> dict:
    """
    Compute residuals between network-predicted and actual next-wave responses.

    The prediction model:
        A = row_normalize(|W_t|)    — absolute-value transition matrix
        x_hat = A @ x_t            — predicted next-wave means
        residual = x_next - x_hat  — prediction error

    Only constructs present in BOTH waves (valid x_t AND valid x_next)
    are included.  Residuals are signed: positive = actual exceeded
    prediction (construct moved higher than the network expected).

    Large positive residuals indicate external shocks pushing a construct
    upward beyond what network diffusion would predict.  Large negative
    residuals indicate unexplained declines.

    Parameters
    ----------
    W_t : (k, k) ndarray
        Weight matrix at time t.
    x_t : (k,) ndarray
        Mean responses at time t.
    x_next : (k,) ndarray
        Mean responses at time t+1.
    labels : list[str]
        Construct labels.

    Returns
    -------
    result : dict with keys:
        - predicted : {construct: float}
        - actual : {construct: float}
        - residual : {construct: float}
        - n_valid : int
        - rmse : float
        - residual_vector : list[float]  (aligned with valid constructs)
    """
    k = W_t.shape[0]

    # ── Build row-normalized absolute transition matrix ──────────────────
    # NaN → 0, then absolute value, then row-normalize.
    # This is the "diffusion" predictor: each construct's predicted next
    # value is a weighted average of its neighbors' current values.
    W_abs = np.abs(fill_nan_zero(W_t))
    A = row_normalize(W_abs)

    # ── Predict next-wave means ──────────────────────────────────────────
    # Replace NaN in x_t with 0 for the matrix multiply (these constructs
    # contribute nothing to their neighbors' predictions).
    x_t_clean = np.where(np.isnan(x_t), 0.0, x_t)
    x_hat = A @ x_t_clean

    # ── Compute residuals only for constructs valid in both waves ────────
    valid = (~np.isnan(x_t)) & (~np.isnan(x_next))

    predicted = {}
    actual = {}
    residual = {}
    residual_vec = []

    for i in range(k):
        if valid[i]:
            predicted[labels[i]] = float(x_hat[i])
            actual[labels[i]] = float(x_next[i])
            r = float(x_next[i] - x_hat[i])
            residual[labels[i]] = r
            residual_vec.append(r)

    n_valid = int(valid.sum())
    rmse = float(np.sqrt(np.mean(np.array(residual_vec) ** 2))) if residual_vec else np.nan

    return {
        "predicted": predicted,
        "actual": actual,
        "residual": residual,
        "n_valid": n_valid,
        "rmse": rmse,
        "residual_vector": residual_vec,
    }


# ═════════════════════════════════════════════════════════════════════════════
# fit_alpha — Constrained 1-parameter forecast model
# ═════════════════════════════════════════════════════════════════════════════

def fit_alpha(temporal_data: dict, wave_means: dict) -> dict:
    """
    Fit the 1-parameter blending model across all transitions.

    The model:
        x_hat(t+1) = alpha * A(t) @ x(t) + (1 - alpha) * x(t)
                    = x(t) + alpha * (A(t) @ x(t) - x(t))

    This is a blend of:
        alpha = 1 : pure network diffusion (A @ x)
        alpha = 0 : pure persistence (x stays the same)

    Closed-form solution (OLS over pooled transitions):
        Let a_i = (A(t) @ x(t))_i  and  x_i = x(t)_i,  y_i = x(t+1)_i
        Then: y = x + alpha * (a - x) + noise
              alpha* = sum((a_i - x_i)(y_i - x_i)) / sum((a_i - x_i)^2)

    We pool over ALL transitions (4 pairs) and the temporal core (20
    constructs), giving up to 80 observations.  We also fit per-transition
    alpha to check stationarity: if alpha varies wildly across transitions,
    the 1-parameter model is too rigid.

    Parameters
    ----------
    temporal_data : dict
        From load_all_temporal().
    wave_means : dict
        {wave_int: np.ndarray} — mean responses per wave, shape (k,).

    Returns
    -------
    result : dict with keys:
        - alpha_star : float
        - alpha_per_transition : {transition_str: float}
        - rmse : float (pooled)
        - n_observations : int
    """
    matrices = temporal_data["matrices"]
    labels = temporal_data["labels"]
    temporal_core = temporal_data["temporal_core"]
    k = temporal_data["n_constructs"]

    # ── Accumulate numerator and denominator for closed-form alpha ────────
    num = 0.0   # sum of (a_i - x_i) * (y_i - x_i)
    den = 0.0   # sum of (a_i - x_i)^2
    n_obs = 0

    per_transition_alphas = {}
    transitions = list(zip(WAVES[:-1], WAVES[1:]))

    for w_curr, w_next in transitions:
        W_t = matrices[w_curr]
        x_t = wave_means[w_curr]
        x_next = wave_means[w_next]

        # Build row-normalized absolute transition matrix
        W_abs = np.abs(fill_nan_zero(W_t))
        A = row_normalize(W_abs)

        # Predicted diffusion means
        x_t_clean = np.where(np.isnan(x_t), 0.0, x_t)
        a = A @ x_t_clean  # diffusion prediction

        # Per-transition numerator and denominator (only temporal core)
        t_num = 0.0
        t_den = 0.0

        for i in temporal_core:
            if np.isnan(x_t[i]) or np.isnan(x_next[i]):
                continue  # skip missing (shouldn't happen for core)

            diff_a = a[i] - x_t[i]   # diffusion shift
            diff_y = x_next[i] - x_t[i]  # actual shift

            t_num += diff_a * diff_y
            t_den += diff_a ** 2
            n_obs += 1

        num += t_num
        den += t_den

        # Per-transition alpha
        trans_label = f"W{w_curr}_to_W{w_next}"
        if t_den > 0:
            alpha_t = np.clip(t_num / t_den, 0.0, 1.0)
        else:
            alpha_t = 0.0
        per_transition_alphas[trans_label] = float(alpha_t)

    # ── Global alpha* ────────────────────────────────────────────────────
    if den > 0:
        alpha_star = float(np.clip(num / den, 0.0, 1.0))
    else:
        alpha_star = 0.0

    # ── Pooled RMSE with alpha* ──────────────────────────────────────────
    squared_errors = []
    for w_curr, w_next in transitions:
        W_t = matrices[w_curr]
        x_t = wave_means[w_curr]
        x_next = wave_means[w_next]

        W_abs = np.abs(fill_nan_zero(W_t))
        A = row_normalize(W_abs)
        x_t_clean = np.where(np.isnan(x_t), 0.0, x_t)
        a = A @ x_t_clean

        for i in temporal_core:
            if np.isnan(x_t[i]) or np.isnan(x_next[i]):
                continue
            x_hat_i = alpha_star * a[i] + (1 - alpha_star) * x_t[i]
            squared_errors.append((x_next[i] - x_hat_i) ** 2)

    rmse = float(np.sqrt(np.mean(squared_errors))) if squared_errors else np.nan

    print(f"\n  Alpha fit:")
    print(f"    alpha* = {alpha_star:.4f}  (0=persistence, 1=full diffusion)")
    print(f"    RMSE   = {rmse:.4f}")
    print(f"    n_obs  = {n_obs}  ({len(temporal_core)} core constructs x "
          f"{len(transitions)} transitions)")
    print(f"    Per-transition alphas:")
    for trans, alpha_t in per_transition_alphas.items():
        print(f"      {trans}: {alpha_t:.4f}")

    return {
        "alpha_star": alpha_star,
        "alpha_per_transition": per_transition_alphas,
        "rmse": rmse,
        "n_observations": n_obs,
    }


# ═════════════════════════════════════════════════════════════════════════════
# forecast_w8 — 1-parameter forecast for Wave 8
# ═════════════════════════════════════════════════════════════════════════════

def forecast_w8(
    W_w7: np.ndarray,
    x_w7: np.ndarray,
    alpha_star: float,
    temporal_core: list[int],
    labels: list[str],
) -> dict:
    """
    Forecast Wave 8 construct means using the 1-parameter model.

        x_hat(W8) = alpha* * A(W7) @ x(W7) + (1 - alpha*) * x(W7)

    Only temporal core constructs (present in all 5 waves) are forecast.
    The model assumes: (a) W7's network structure persists into W8, and
    (b) the alpha blending coefficient is stationary across transitions.

    Parameters
    ----------
    W_w7 : (k, k) ndarray
        Wave 7 weight matrix.
    x_w7 : (k,) ndarray
        Wave 7 mean responses.
    alpha_star : float
        Fitted blending coefficient.
    temporal_core : list[int]
        Indices of temporal core constructs.
    labels : list[str]
        Construct labels.

    Returns
    -------
    forecast : dict with keys:
        - alpha_used : float
        - per_construct : [{construct, x_w7, x_hat_w8, shift, direction}, ...]
        - forecast_vector : (k,) ndarray as list
    """
    # Build transition matrix from W7
    W_abs = np.abs(fill_nan_zero(W_w7))
    A = row_normalize(W_abs)
    x_w7_clean = np.where(np.isnan(x_w7), 0.0, x_w7)

    # Diffusion prediction
    a = A @ x_w7_clean

    # Blended forecast
    x_hat_w8 = np.full(len(labels), np.nan)
    per_construct = []

    for i in temporal_core:
        if np.isnan(x_w7[i]):
            continue
        x_hat_w8[i] = alpha_star * a[i] + (1 - alpha_star) * x_w7[i]
        shift = x_hat_w8[i] - x_w7[i]
        direction = "up" if shift > 0 else ("down" if shift < 0 else "flat")
        per_construct.append({
            "construct": labels[i],
            "x_w7": float(x_w7[i]),
            "x_hat_w8": float(x_hat_w8[i]),
            "shift": float(shift),
            "direction": direction,
        })

    # Sort by absolute shift (largest predicted change first)
    per_construct.sort(key=lambda x: abs(x["shift"]), reverse=True)

    return {
        "alpha_used": alpha_star,
        "per_construct": per_construct,
        "forecast_vector": x_hat_w8.tolist(),
    }


# ═════════════════════════════════════════════════════════════════════════════
# uncertainty_envelope — Per-construct sigma and 80% CI
# ═════════════════════════════════════════════════════════════════════════════

def uncertainty_envelope(
    residuals_all: list[dict],
    x_hat_w8: list[float],
    x_w7: np.ndarray,
    temporal_core: list[int],
    labels: list[str],
) -> dict:
    """
    Build uncertainty envelopes for the W8 forecast.

    Per-construct sigma is the standard deviation of residuals across the
    4 transitions (W3→W4, W4→W5, W5→W6, W6→W7).  The 80% confidence
    interval is:
        x_hat +/- 1.28 * sigma

    We flag two conditions:
      - noise_dominated: sigma > |shift|, meaning the prediction error
        in past transitions exceeds the predicted shift.  The direction
        claim is unreliable.
      - ci_excludes_current: the entire 80% CI is above or below x_w7.
        Even accounting for historical residual variance, the forecast
        direction is robust.

    Parameters
    ----------
    residuals_all : list[dict]
        Residual dicts from compute_residuals() for each transition.
    x_hat_w8 : list[float]
        Forecast vector from forecast_w8() (length k, NaN for non-core).
    x_w7 : (k,) ndarray
        Wave 7 mean responses.
    temporal_core : list[int]
        Indices of temporal core constructs.
    labels : list[str]
        Construct labels.

    Returns
    -------
    envelope : dict with keys:
        - per_construct : [{construct, x_hat, sigma, ci_lo, ci_hi,
                            shift, noise_dominated, ci_excludes_current}, ...]
        - n_directional_claims : int  (CI excludes x_w7)
        - n_noise_dominated : int
    """
    x_hat = np.array(x_hat_w8)
    per_construct = []

    for i in temporal_core:
        construct = labels[i]
        if np.isnan(x_hat[i]) or np.isnan(x_w7[i]):
            continue

        # ── Collect residuals for this construct across all transitions ──
        # Each residuals_all[t] is a dict with key "residual" = {construct: val}
        resids = []
        for r_dict in residuals_all:
            if construct in r_dict["residual"]:
                resids.append(r_dict["residual"][construct])

        # Need at least 2 residuals to estimate sigma
        if len(resids) < 2:
            continue

        sigma = float(np.std(resids, ddof=1))  # sample std
        shift = float(x_hat[i] - x_w7[i])

        # 80% CI: z = 1.28 for 80% confidence (two-tailed)
        ci_lo = float(x_hat[i] - 1.28 * sigma)
        ci_hi = float(x_hat[i] + 1.28 * sigma)

        # Flags
        noise_dominated = sigma > abs(shift) if abs(shift) > 0 else True
        ci_excludes_current = (ci_lo > float(x_w7[i])) or (ci_hi < float(x_w7[i]))

        per_construct.append({
            "construct": construct,
            "x_hat_w8": float(x_hat[i]),
            "sigma": sigma,
            "ci_80_lo": ci_lo,
            "ci_80_hi": ci_hi,
            "shift": shift,
            "noise_dominated": noise_dominated,
            "ci_excludes_current": ci_excludes_current,
            "n_residuals": len(resids),
        })

    # Sort by sigma (most precise first)
    per_construct.sort(key=lambda x: x["sigma"])

    n_directional = sum(1 for p in per_construct if p["ci_excludes_current"])
    n_noise = sum(1 for p in per_construct if p["noise_dominated"])

    return {
        "per_construct": per_construct,
        "n_directional_claims": n_directional,
        "n_noise_dominated": n_noise,
        "n_total": len(per_construct),
    }


# ═════════════════════════════════════════════════════════════════════════════
# fit_linear_trends — OLS trend per construct
# ═════════════════════════════════════════════════════════════════════════════

def fit_linear_trends(
    wave_means: dict,
    temporal_core: list[int],
    labels: list[str],
    forecast_per_construct: list[dict],
) -> dict:
    """
    Fit linear trends per construct over the 5 waves and compare against
    the network forecast direction.

    OLS: x(year) = a + b*year via scipy.stats.linregress.
    slope_per_decade = b * 10 (rescaled for interpretability).

    A "trend reversal" is flagged when the linear trend direction (sign of
    slope) disagrees with the network forecast direction.  This identifies
    constructs where the network structure at W7 predicts a different shift
    than the historical trend — potentially interesting for sociological
    interpretation (network-level versus cohort-level forces).

    Parameters
    ----------
    wave_means : {wave_int: np.ndarray}
        Mean responses per wave.
    temporal_core : list[int]
        Indices of temporal core constructs.
    labels : list[str]
        Construct labels.
    forecast_per_construct : list[dict]
        From forecast_w8(), for direction comparison.

    Returns
    -------
    trends : dict with keys:
        - per_construct : [{construct, slope_per_decade, r_squared, p_value,
                            trend_direction, forecast_direction, reversal}, ...]
        - n_trend_reversals : int
        - strongest_trends : list of top-5 by |slope|
    """
    # Build lookup of forecast direction from the forecast output
    forecast_dir = {}
    for entry in forecast_per_construct:
        forecast_dir[entry["construct"]] = entry["direction"]

    years = np.array([WAVE_YEARS[w] for w in WAVES], dtype=np.float64)
    per_construct = []

    for i in temporal_core:
        construct = labels[i]

        # ── Collect mean values across waves ─────────────────────────────
        # Only include waves where the mean is valid (not NaN).
        vals = []
        yrs = []
        for w in WAVES:
            x_w = wave_means[w]
            if not np.isnan(x_w[i]):
                vals.append(x_w[i])
                yrs.append(WAVE_YEARS[w])

        if len(vals) < 3:
            continue  # need at least 3 points for a meaningful trend

        vals = np.array(vals)
        yrs = np.array(yrs, dtype=np.float64)

        # ── OLS linear regression ────────────────────────────────────────
        slope, intercept, r_value, p_value, std_err = stats.linregress(yrs, vals)

        slope_per_decade = slope * 10.0
        r_squared = r_value ** 2
        trend_dir = "up" if slope > 0 else ("down" if slope < 0 else "flat")

        # ── Compare against forecast direction ───────────────────────────
        fc_dir = forecast_dir.get(construct, "unknown")
        reversal = (trend_dir != fc_dir) and (trend_dir != "flat") and (fc_dir != "flat")

        per_construct.append({
            "construct": construct,
            "slope_per_decade": float(slope_per_decade),
            "r_squared": float(r_squared),
            "p_value": float(p_value),
            "trend_direction": trend_dir,
            "forecast_direction": fc_dir,
            "reversal": reversal,
            "n_waves": len(vals),
        })

    # Sort by |slope| descending
    per_construct.sort(key=lambda x: abs(x["slope_per_decade"]), reverse=True)

    n_reversals = sum(1 for p in per_construct if p["reversal"])

    return {
        "per_construct": per_construct,
        "n_trend_reversals": n_reversals,
        "n_total": len(per_construct),
        "strongest_trends": per_construct[:5],
    }


# ═════════════════════════════════════════════════════════════════════════════
# _compute_means_from_cache — Extract real means from temporal pickle cache
# ═════════════════════════════════════════════════════════════════════════════

def _compute_means_from_cache() -> str:
    """
    Load wvs_multi_construct_cache_temporal.pkl (built by
    build_wvs_constructs_multi.py --scope temporal), extract per-wave
    per-construct means, and save as JSON for the temporal analysis.

    The cache contains DataFrames with `wvs_agg_{construct_name}` columns.
    We strip the prefix and append the WVS domain suffix (e.g., |WVS_A) to
    match the construct labels used in the temporal weight matrices.

    Returns the path to the saved JSON file (for use as --means-file).
    """
    import pickle

    cache_path = ROOT / "data" / "results" / "wvs_multi_construct_cache_temporal.pkl"
    if not cache_path.exists():
        print(f"ERROR: Cache not found at {cache_path}")
        print("  Run: python scripts/debug/build_wvs_constructs_multi.py "
              "--scope temporal")
        sys.exit(1)

    # Load temporal manifest for construct label mapping
    manifest = load_temporal_manifest()
    construct_index = manifest["construct_index"]

    # Build mapping: base_name → full_label (e.g., "importance_of_life_domains"
    # → "importance_of_life_domains|WVS_A")
    base_to_label = {}
    for ci in construct_index:
        base = ci.split("|")[0]
        base_to_label[base] = ci

    print("  Loading temporal construct cache...")
    with open(cache_path, "rb") as f:
        cache = pickle.load(f)

    wave_means: dict[str, dict[str, float]] = {}

    for wave in [3, 4, 5, 6, 7]:
        key = f"WVS_W{wave}_MEX"
        if key not in cache:
            print(f"  WARNING: {key} not in cache, skipping")
            continue

        df = cache[key]
        agg_cols = [c for c in df.columns if c.startswith("wvs_agg_")]
        wave_str = f"W{wave}"
        wave_means[wave_str] = {}

        for col in agg_cols:
            base = col.replace("wvs_agg_", "")
            label = base_to_label.get(base)
            if label is None:
                continue  # construct not in temporal manifest
            mean_val = float(df[col].mean())
            if not np.isnan(mean_val):
                wave_means[wave_str][label] = mean_val

        print(f"    {wave_str} ({manifest['wave_years'][str(wave)]}): "
              f"{len(wave_means[wave_str])} construct means")

    # Save
    out_path = get_output_dir() / "mex_wave_means.json"
    save_json(wave_means, out_path)
    print(f"  Wave means saved to {out_path.relative_to(ROOT)}")
    return str(out_path)


# ═════════════════════════════════════════════════════════════════════════════
# generate_synthetic_means — Structurally plausible but NOT empirical
# ═════════════════════════════════════════════════════════════════════════════

def generate_synthetic_means(temporal_data: dict) -> dict:
    """
    Generate synthetic mean responses from the weight matrix structure.

    For each wave, each construct's synthetic mean is computed as:
        mean_i = scale( mean(|w_ij| for valid j) )  →  [1, 10]

    The idea: constructs with higher average edge weights are "more
    connected" to the SES-mediated network, so we give them higher
    synthetic means.  This produces structurally plausible variation
    that tests the full pipeline, but these are NOT real survey means.

    Constructs with no edges (empty rows) get NaN.

    Parameters
    ----------
    temporal_data : dict
        From load_all_temporal().

    Returns
    -------
    wave_means : {wave_int: np.ndarray}
        Synthetic mean vectors, shape (k,), scaled to [1, 10].
    """
    matrices = temporal_data["matrices"]
    k = temporal_data["n_constructs"]
    wave_means = {}

    # ── Seed for reproducibility ─────────────────────────────────────────
    rng = np.random.default_rng(42)

    for wave in WAVES:
        W = matrices[wave]
        W_abs = np.abs(fill_nan_zero(W))

        means = np.full(k, np.nan)
        for i in range(k):
            row = W_abs[i, :]
            nonzero = row[row > 0]
            if len(nonzero) > 0:
                means[i] = np.mean(nonzero)

        # Scale to [1, 10] using min-max over valid entries
        valid = ~np.isnan(means)
        if valid.sum() > 1:
            mn = means[valid].min()
            mx = means[valid].max()
            rng_width = mx - mn if mx > mn else 1.0
            means[valid] = 1 + 9 * (means[valid] - mn) / rng_width

        # Add small wave-dependent perturbation so we don't get identical
        # means across waves (which would make velocity/forecast trivial)
        noise = rng.normal(0, 0.3, k)
        means[valid] += noise[valid]
        # Re-clip to [1, 10]
        means[valid] = np.clip(means[valid], 1.0, 10.0)

        wave_means[wave] = means

    print(f"\n  Synthetic means generated (seed=42, scaled to [1,10])")
    print(f"    WARNING: These are structurally plausible but NOT empirical.")
    print(f"    Use --means-file for real analysis.")

    return wave_means


# ═════════════════════════════════════════════════════════════════════════════
# load_means_file — Load pre-computed wave means from JSON
# ═════════════════════════════════════════════════════════════════════════════

def load_means_file(path: Path, labels: list[str]) -> dict:
    """
    Load pre-computed wave means from a JSON file.

    Expected JSON structure:
        {
            "3": {"construct_name": 5.2, ...},
            "4": {"construct_name": 4.8, ...},
            ...
        }

    Keys are wave numbers as strings.  Values are dicts mapping construct
    names to mean responses.

    Parameters
    ----------
    path : Path
        Path to the JSON file.
    labels : list[str]
        Construct labels (from load_all_temporal), used for alignment.

    Returns
    -------
    wave_means : {wave_int: np.ndarray}
        Mean vectors, shape (k,).  NaN for constructs not in the JSON.
    """
    with open(path) as f:
        raw = json.load(f)

    k = len(labels)
    wave_means = {}

    for wave in WAVES:
        # Try multiple key formats: "3", "W3", "wave_3"
        key = None
        for candidate in [str(wave), f"W{wave}", f"wave_{wave}"]:
            if candidate in raw:
                key = candidate
                break

        means = np.full(k, np.nan)

        if key is not None:
            wave_data = raw[key]
            for i, label in enumerate(labels):
                if label in wave_data:
                    means[i] = wave_data[label]
        else:
            print(f"  WARNING: Wave {wave} not found in means file")

        wave_means[wave] = means

    # Report coverage
    for wave in WAVES:
        n_valid = int((~np.isnan(wave_means[wave])).sum())
        print(f"    W{wave}: {n_valid}/{k} construct means loaded")

    return wave_means


# ═════════════════════════════════════════════════════════════════════════════
# print_summary — Comprehensive console output
# ═════════════════════════════════════════════════════════════════════════════

def print_summary(
    temporal_data: dict,
    velocity_results: dict,
    eq_distances: dict,
    residuals_all: list[dict],
    alpha_result: dict,
    forecast_result: dict,
    envelope_result: dict,
    trend_result: dict,
) -> None:
    """Print a comprehensive human-readable summary to stdout."""
    labels = temporal_data["labels"]

    # ── Velocity top-5 per wave ──────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  VELOCITY FIELD — Top-5 constructs by |velocity| per wave")
    print(f"{'='*70}")
    for wave in WAVES:
        v = velocity_results[wave]
        if v is None:
            print(f"\n  W{wave} ({WAVE_YEARS[wave]}): no means available")
            continue
        # Sort by |velocity|, excluding NaN
        indices = [i for i in range(len(v)) if not np.isnan(v[i])]
        indices.sort(key=lambda i: abs(v[i]), reverse=True)
        print(f"\n  W{wave} ({WAVE_YEARS[wave]}):")
        for rank, i in enumerate(indices[:5], 1):
            direction = "+" if v[i] > 0 else "-"
            print(f"    {rank}. {labels[i]:<45s} {direction}{abs(v[i]):.4f}")

    # ── Equilibrium distance trajectory ──────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  EQUILIBRIUM DISTANCE — Distance from degree-weighted consensus")
    print(f"{'='*70}")
    for wave in WAVES:
        d = eq_distances.get(wave, np.nan)
        year = WAVE_YEARS[wave]
        bar = "#" * int(d * 5) if not np.isnan(d) else "N/A"
        print(f"    W{wave} ({year}): {d:.4f}  {bar}")

    # ── Residual RMSE per transition ─────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  RESIDUALS — Network prediction error per transition")
    print(f"{'='*70}")
    transitions = list(zip(WAVES[:-1], WAVES[1:]))
    for t_idx, (w_curr, w_next) in enumerate(transitions):
        r = residuals_all[t_idx]
        print(f"    W{w_curr}→W{w_next}: RMSE={r['rmse']:.4f}  "
              f"({r['n_valid']} constructs)")
        # Top-3 largest residuals
        sorted_resids = sorted(r["residual"].items(),
                               key=lambda x: abs(x[1]), reverse=True)
        for name, val in sorted_resids[:3]:
            sign = "+" if val > 0 else ""
            print(f"      {name:<40s} {sign}{val:.4f}")

    # ── Alpha star and stationarity ──────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  ALPHA FIT — 1-parameter forecast model")
    print(f"{'='*70}")
    print(f"    alpha* = {alpha_result['alpha_star']:.4f}")
    print(f"    RMSE   = {alpha_result['rmse']:.4f}")
    alphas = alpha_result["alpha_per_transition"]
    alpha_vals = list(alphas.values())
    alpha_std = np.std(alpha_vals)
    print(f"    Stationarity: std(alpha_t) = {alpha_std:.4f}")
    if alpha_std < 0.1:
        print(f"    → alpha is reasonably stationary across transitions")
    else:
        print(f"    → alpha varies substantially — model may be too rigid")

    # ── Forecast directional claims ──────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  FORECAST — W8 predictions (top-5 by |shift|)")
    print(f"{'='*70}")
    for entry in forecast_result["per_construct"][:5]:
        arrow = "↑" if entry["direction"] == "up" else "↓"
        print(f"    {arrow} {entry['construct']:<42s} "
              f"{entry['x_w7']:.3f} → {entry['x_hat_w8']:.3f}  "
              f"(shift={entry['shift']:+.4f})")

    # ── Uncertainty summary ──────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  UNCERTAINTY — 80% CI from historical residuals")
    print(f"{'='*70}")
    env = envelope_result
    print(f"    Total core constructs: {env['n_total']}")
    print(f"    Directional claims (CI excludes x_w7): {env['n_directional_claims']}")
    print(f"    Noise-dominated (sigma > |shift|): {env['n_noise_dominated']}")

    # Show the directional claims
    claims = [p for p in env["per_construct"] if p["ci_excludes_current"]]
    if claims:
        print(f"\n    Directional claims:")
        for p in claims:
            arrow = "↑" if p["shift"] > 0 else "↓"
            print(f"      {arrow} {p['construct']:<40s} "
                  f"shift={p['shift']:+.4f}  "
                  f"80% CI=[{p['ci_80_lo']:.3f}, {p['ci_80_hi']:.3f}]")

    # ── Trend reversals ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  TREND ANALYSIS — Linear trends vs. network forecast")
    print(f"{'='*70}")
    print(f"    Total constructs: {trend_result['n_total']}")
    print(f"    Trend reversals: {trend_result['n_trend_reversals']}")
    print(f"\n    Strongest trends (by |slope per decade|):")
    for entry in trend_result["strongest_trends"][:5]:
        arrow = "↑" if entry["trend_direction"] == "up" else "↓"
        rev = " *** REVERSAL" if entry["reversal"] else ""
        print(f"      {arrow} {entry['construct']:<38s} "
              f"slope={entry['slope_per_decade']:+.4f}/dec  "
              f"R²={entry['r_squared']:.3f}{rev}")

    reversals = [p for p in trend_result["per_construct"] if p["reversal"]]
    if reversals:
        print(f"\n    Trend reversals (network predicts opposite direction):")
        for entry in reversals:
            print(f"      {entry['construct']:<40s} "
                  f"trend={entry['trend_direction']}  "
                  f"forecast={entry['forecast_direction']}")


# ═════════════════════════════════════════════════════════════════════════════
# run_all_w7_descriptive — Velocity + equilibrium for all 66 countries at W7
# ═════════════════════════════════════════════════════════════════════════════

def _load_means_from_bridge_csvs(country: str, waves: list[int],
                                  construct_index: list[str]) -> dict:
    """
    Load per-wave construct means from Julia bridge CSVs in
    data/julia_bridge_wvs/WVS_W{n}_{COUNTRY}.csv.

    These CSVs contain wvs_agg_* columns (construct scores per respondent).
    We compute the mean per construct per wave.
    """
    bridge_dir = ROOT / "data" / "julia_bridge_wvs"
    k = len(construct_index)

    # Build base_name → index mapping
    base_to_idx = {}
    for idx, ci in enumerate(construct_index):
        base = ci.split("|")[0]
        base_to_idx[base] = idx

    wave_means = {}
    for w in waves:
        csv_path = bridge_dir / f"WVS_W{w}_{country}.csv"
        if not csv_path.exists():
            # No data for this wave — fill with NaN
            wave_means[w] = np.full(k, np.nan)
            continue

        df = pd.read_csv(csv_path)
        agg_cols = [c for c in df.columns if c.startswith("wvs_agg_")]
        means = np.full(k, np.nan)
        for col in agg_cols:
            base = col.replace("wvs_agg_", "")
            idx = base_to_idx.get(base)
            if idx is not None:
                val = df[col].mean()
                if not np.isnan(val):
                    means[idx] = val
        wave_means[w] = means

    return wave_means


def run_all_temporal():
    """
    Run full temporal analysis (velocity, equilibrium, residuals, alpha fit,
    forecast, trends) for all 37 countries with multi-wave temporal weight
    matrices in data/tda/allwave/temporal/.

    Construct means are loaded from Julia bridge CSVs in
    data/julia_bridge_wvs/WVS_W{n}_{COUNTRY}.csv.
    """
    t_start = time.time()
    print(f"\n{'='*70}")
    print(f"  TEMPORAL DYNAMICS — All countries with multi-wave data")
    print(f"{'='*70}")

    # ── Load allwave global manifest ─────────────────────────────────────
    allwave_manifest_path = ROOT / "data" / "tda" / "allwave" / "matrices" / "global_manifest.json"
    with open(allwave_manifest_path) as f:
        global_manifest = json.load(f)

    temporal_countries = global_manifest["temporal"]["countries"]
    print(f"  {len(temporal_countries)} countries with temporal data")

    out_dir = get_output_dir()
    all_summaries = {}
    n_done = 0
    n_skip = 0

    for country, entry in sorted(temporal_countries.items()):
        waves = sorted(entry["waves"])
        zone = entry.get("zone", "unknown")

        if len(waves) < 3:
            n_skip += 1
            continue

        # ── Load per-wave weight matrices ────────────────────────────────
        per_country_manifest_path = (
            ROOT / "data" / "tda" / "allwave" / "temporal" / country / "manifest.json"
        )
        if not per_country_manifest_path.exists():
            n_skip += 1
            continue

        with open(per_country_manifest_path) as f:
            country_manifest = json.load(f)

        construct_index = country_manifest["construct_index"]
        k = len(construct_index)

        matrices = {}
        for w in waves:
            csv_path = (ROOT / "data" / "tda" / "allwave" / "temporal"
                        / country / f"{country}_W{w}.csv")
            if not csv_path.exists():
                continue
            df = pd.read_csv(csv_path, index_col=0)
            matrices[w] = df.values.astype(np.float64)

        waves = sorted(matrices.keys())
        if len(waves) < 3:
            n_skip += 1
            continue

        # ── Load construct means from bridge CSVs ────────────────────────
        wave_means = _load_means_from_bridge_csvs(country, waves, construct_index)

        # Check coverage
        valid_waves = [w for w in waves
                       if int((~np.isnan(wave_means[w])).sum()) >= 5]
        if len(valid_waves) < 3:
            print(f"  {country}: insufficient means coverage, skipping")
            n_skip += 1
            continue

        waves = valid_waves

        # ── Find temporal core (constructs present in all waves) ─────────
        present_per_wave = {}
        for w in waves:
            W = matrices[w]
            mask = (~np.isnan(W)) & (W != 0.0)
            present = set(np.where(mask.any(axis=1))[0])
            # Also require non-NaN mean
            present &= set(np.where(~np.isnan(wave_means[w]))[0])
            present_per_wave[w] = present

        temporal_core = sorted(set.intersection(*present_per_wave.values()))

        if len(temporal_core) < 5:
            print(f"  {country}: only {len(temporal_core)} core constructs, skipping")
            n_skip += 1
            continue

        # ── Velocity fields ──────────────────────────────────────────────
        velocity_results = {}
        for w in waves:
            velocity_results[w] = velocity_field(matrices[w], wave_means[w])

        # ── Equilibrium distances ────────────────────────────────────────
        eq_distances = {}
        for w in waves:
            eq_distances[w] = equilibrium_distance(matrices[w], wave_means[w])

        # ── Residuals ────────────────────────────────────────────────────
        transitions = [(waves[i], waves[i+1]) for i in range(len(waves)-1)]
        residuals_all = []
        for w_curr, w_next in transitions:
            r = compute_residuals(
                matrices[w_curr], wave_means[w_curr],
                wave_means[w_next], construct_index,
            )
            residuals_all.append(r)

        # ── Fit alpha ────────────────────────────────────────────────────
        # Manually fit alpha for this country's waves and core
        numerator = 0.0
        denominator = 0.0
        n_obs = 0
        per_transition_alpha = {}

        for w_curr, w_next in transitions:
            x = wave_means[w_curr]
            x_next = wave_means[w_next]

            # Mask W to only use constructs with valid means — prevents
            # NaN propagation through A @ x when some means are missing.
            valid_mask = ~np.isnan(x)
            W_abs = np.abs(fill_nan_zero(matrices[w_curr]))
            W_masked = W_abs * valid_mask[None, :]  # zero out invalid columns
            A = row_normalize(W_masked)
            x_clean = np.where(np.isnan(x), 0.0, x)
            a = A @ x_clean

            num_t = 0.0
            den_t = 0.0
            for i in temporal_core:
                if np.isnan(x[i]) or np.isnan(x_next[i]):
                    continue
                diff_a = a[i] - x[i]
                diff_x = x_next[i] - x[i]
                num_t += diff_a * diff_x
                den_t += diff_a ** 2
                n_obs += 1

            numerator += num_t
            denominator += den_t
            alpha_t_raw = num_t / (den_t + 1e-12)
            per_transition_alpha[f"W{w_curr}_to_W{w_next}"] = float(
                np.clip(alpha_t_raw, 0.0, 1.0)
            )

        alpha_raw = float(numerator / (denominator + 1e-12))
        alpha_star = float(np.clip(alpha_raw, 0.0, 1.0))

        # ── Top velocity construct at last wave ──────────────────────────
        last_wave = waves[-1]
        v = velocity_results[last_wave]
        v_clean = np.where(np.isnan(v), 0.0, v)
        top_idx = np.argsort(np.abs(v_clean))[::-1][:3]
        top_vel = [
            {"construct": construct_index[i], "velocity": float(v_clean[i])}
            for i in top_idx if abs(v_clean[i]) > 0
        ]

        # ── Summary for this country ─────────────────────────────────────
        summary = {
            "country": country,
            "zone": zone,
            "waves": waves,
            "n_waves": len(waves),
            "n_constructs": k,
            "n_temporal_core": len(temporal_core),
            "alpha_star": alpha_star,
            "alpha_raw": alpha_raw,
            "per_transition_alpha": per_transition_alpha,
            "n_observations": n_obs,
            "equilibrium_distances": {
                f"W{w}": float(eq_distances[w])
                if not np.isnan(eq_distances[w]) else None
                for w in waves
            },
            "eq_distance_trend": (
                "decreasing" if len(waves) >= 3 and
                eq_distances[waves[-1]] < eq_distances[waves[0]]
                else "increasing"
            ),
            "top_velocity_last_wave": top_vel,
            "residual_rmse": {
                f"W{w1}_W{w2}": float(r["rmse"])
                for (w1, w2), r in zip(transitions, residuals_all)
                if not np.isnan(r["rmse"])
            },
        }
        all_summaries[country] = summary

        # Save per-country
        save_json(summary, out_dir / f"{country}_temporal.json")
        n_done += 1

    # ── Cross-country summary ────────────────────────────────────────────
    print(f"\n  Processed {n_done} countries, skipped {n_skip}")

    # Rank by alpha
    alpha_ranked = sorted(
        [(c, s["alpha_star"]) for c, s in all_summaries.items()],
        key=lambda x: x[1], reverse=True,
    )
    print(f"\n  Alpha ranking (higher = more network-driven):")
    for c, a in alpha_ranked[:5]:
        print(f"    {c}: alpha*={a:.4f} ({all_summaries[c]['n_waves']} waves, "
              f"{all_summaries[c]['n_temporal_core']} core constructs)")
    print(f"    ...")
    for c, a in alpha_ranked[-5:]:
        print(f"    {c}: alpha*={a:.4f}")

    # Most common top-velocity construct
    from collections import Counter
    top_vel_constructs = Counter()
    for s in all_summaries.values():
        if s["top_velocity_last_wave"]:
            top_vel_constructs[s["top_velocity_last_wave"][0]["construct"]] += 1

    print(f"\n  Most common top-velocity construct at last wave:")
    for construct, count in top_vel_constructs.most_common(5):
        print(f"    {construct}: {count}/{n_done} countries")

    # Save summary
    cross_summary = {
        "n_countries": n_done,
        "alpha_ranking": [
            {"country": c, "alpha": a, "zone": all_summaries[c]["zone"],
             "n_waves": all_summaries[c]["n_waves"]}
            for c, a in alpha_ranked
        ],
        "top_velocity_frequency": dict(top_vel_constructs.most_common(20)),
    }
    save_json(cross_summary, out_dir / "temporal_all_summary.json")

    t_elapsed = time.time() - t_start
    print(f"\n  Done in {t_elapsed:.1f}s")


def run_all_w7_descriptive():
    """
    Run W7 descriptive analysis (velocity field + equilibrium distance) for
    all 66 countries using the geographic construct cache and the W7 weight
    matrices from data/tda/matrices/.

    This is the cross-sectional counterpart of the Mexico temporal analysis:
    instead of tracking one country across waves, we snapshot all countries
    at W7 and ask "where does each country's network pull beliefs right now?"
    """
    import pickle

    t_start = time.time()
    print(f"\n{'='*70}")
    print(f"  W7 DESCRIPTIVE — All countries (velocity + equilibrium)")
    print(f"{'='*70}")

    # ── Load geographic construct cache ──────────────────────────────────
    cache_path = ROOT / "data" / "results" / "wvs_geo_construct_cache.pkl"
    if not cache_path.exists():
        print(f"ERROR: Geographic cache not found at {cache_path}")
        print("  Run: python scripts/debug/build_wvs_constructs_multi.py "
              "--scope geographic")
        sys.exit(1)

    print("  Loading geographic construct cache...")
    with open(cache_path, "rb") as f:
        geo_cache = pickle.load(f)

    manifest = load_manifest()
    countries = manifest["countries"]
    construct_index = manifest["construct_index"]
    k = len(construct_index)

    # Build base_name → index mapping for the 55 geographic constructs
    base_to_idx = {}
    for idx, ci in enumerate(construct_index):
        base = ci.split("|")[0]
        base_to_idx[base] = idx

    all_results = {}
    n_done = 0

    for country in countries:
        cache_key = f"WVS_W7_{country}"
        if cache_key not in geo_cache:
            print(f"  {country}: not in geo cache, skipping")
            continue

        # Load weight matrix
        try:
            W, labels = load_weight_matrix(country)
        except FileNotFoundError:
            print(f"  {country}: no weight matrix, skipping")
            continue

        # Extract mean responses from cache
        df = geo_cache[cache_key]
        agg_cols = [c for c in df.columns if c.startswith("wvs_agg_")]
        x = np.full(k, np.nan)
        for col in agg_cols:
            base = col.replace("wvs_agg_", "")
            idx = base_to_idx.get(base)
            if idx is not None:
                val = df[col].mean()
                if not np.isnan(val):
                    x[idx] = val

        n_valid = int((~np.isnan(x)).sum())
        if n_valid < 5:
            print(f"  {country}: only {n_valid} construct means, skipping")
            continue

        # Compute velocity field and equilibrium distance
        v = velocity_field(W, x)
        eq_dist = equilibrium_distance(W, x)

        # Top-5 by |velocity|
        v_clean = np.where(np.isnan(v), 0.0, v)
        top5_idx = np.argsort(np.abs(v_clean))[::-1][:5]
        top5 = [
            {"construct": labels[i], "velocity": float(v_clean[i])}
            for i in top5_idx if abs(v_clean[i]) > 0
        ]

        all_results[country] = {
            "n_constructs_with_means": n_valid,
            "equilibrium_distance": float(eq_dist) if not np.isnan(eq_dist) else None,
            "top_velocity": top5,
            "velocity_vector": {
                labels[i]: float(v_clean[i])
                for i in range(k) if abs(v_clean[i]) > 0
            },
        }
        n_done += 1

    # ── Cross-country summary ────────────────────────────────────────────
    print(f"\n  Processed {n_done}/{len(countries)} countries")

    # Rank by equilibrium distance
    eq_ranked = sorted(
        [(c, r["equilibrium_distance"]) for c, r in all_results.items()
         if r["equilibrium_distance"] is not None],
        key=lambda x: x[1],
    )

    print(f"\n  Equilibrium distance ranking (lower = closer to network consensus):")
    for c, d in eq_ranked[:5]:
        print(f"    {c}: {d:.4f}")
    print(f"    ...")
    for c, d in eq_ranked[-5:]:
        print(f"    {c}: {d:.4f}")

    # Most common top-velocity construct across countries
    from collections import Counter
    top_vel_constructs = Counter()
    for r in all_results.values():
        if r["top_velocity"]:
            top_vel_constructs[r["top_velocity"][0]["construct"]] += 1

    print(f"\n  Most common top-velocity construct (highest network tension):")
    for construct, count in top_vel_constructs.most_common(5):
        print(f"    {construct}: top in {count}/{n_done} countries")

    # ── Save per-country and summary ─────────────────────────────────────
    out_dir = get_output_dir()

    # Per-country files
    for country, result in all_results.items():
        save_json(
            {"country": country, "wave": 7, **result},
            out_dir / f"{country}_w7_descriptive.json",
        )

    # Summary
    summary = {
        "n_countries": n_done,
        "equilibrium_distance_ranking": [
            {"country": c, "eq_distance": d} for c, d in eq_ranked
        ],
        "top_velocity_construct_frequency": dict(top_vel_constructs.most_common(20)),
    }
    save_json(summary, out_dir / "w7_descriptive_summary.json")

    t_elapsed = time.time() - t_start
    print(f"\n  Done in {t_elapsed:.1f}s")


# ═════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Temporal dynamics for Mexico W3-W7 (Stage 5): velocity fields, "
            "equilibrium distance, residual analysis, constrained forecast, "
            "and trend analysis."
        )
    )
    parser.add_argument(
        "--means-file", type=str, default=None,
        help="Path to pre-computed wave means JSON (structure: {wave: {construct: mean}})"
    )
    parser.add_argument(
        "--synthetic", action="store_true",
        help="Generate synthetic means from weight matrix structure (for testing)"
    )
    parser.add_argument(
        "--compute-means", action="store_true",
        help="Extract real means from wvs_multi_construct_cache_temporal.pkl"
    )
    parser.add_argument(
        "--all-w7", action="store_true",
        help="Run W7 descriptive analysis (velocity + equilibrium) for all 66 countries"
    )
    parser.add_argument(
        "--all-temporal", action="store_true",
        help="Run full temporal analysis for all 37 countries with multi-wave data"
    )
    args = parser.parse_args()

    # ── All-country modes ───────────────────────────────────────────────
    if args.all_w7:
        run_all_w7_descriptive()
        return

    if args.all_temporal:
        run_all_temporal()
        return

    # ── Validate arguments ───────────────────────────────────────────────
    if args.compute_means:
        args.means_file = _compute_means_from_cache()

    if not args.synthetic and args.means_file is None:
        print("ERROR: Must specify --synthetic, --means-file, or --compute-means")
        print("  --synthetic       Generate synthetic means for testing")
        print("  --means-file      Load pre-computed means from JSON")
        print("  --compute-means   Extract from wvs_multi_construct_cache_temporal.pkl")
        sys.exit(1)

    t_start = time.time()
    print(f"\n{'='*70}")
    print(f"  TEMPORAL DYNAMICS — Mexico W3-W7")
    print(f"{'='*70}")

    # ── 1. Load all temporal matrices ────────────────────────────────────
    temporal_data = load_all_temporal()
    labels = temporal_data["labels"]
    temporal_core = temporal_data["temporal_core"]
    matrices = temporal_data["matrices"]

    # ── 2. Load or generate mean responses ───────────────────────────────
    if args.synthetic:
        wave_means = generate_synthetic_means(temporal_data)
    else:
        means_path = Path(args.means_file)
        if not means_path.exists():
            print(f"ERROR: Means file not found: {means_path}")
            sys.exit(1)
        wave_means = load_means_file(means_path, labels)

    # ── 3. Velocity fields ───────────────────────────────────────────────
    print(f"\n  Computing velocity fields...")
    velocity_results = {}
    for wave in WAVES:
        W = matrices[wave]
        x = wave_means[wave]
        v = velocity_field(W, x)
        velocity_results[wave] = v

    # ── 4. Equilibrium distances ─────────────────────────────────────────
    print(f"  Computing equilibrium distances...")
    eq_distances = {}
    for wave in WAVES:
        W = matrices[wave]
        x = wave_means[wave]
        eq_distances[wave] = equilibrium_distance(W, x)

    # ── 5. Residuals across transitions ──────────────────────────────────
    print(f"  Computing residuals across 4 transitions...")
    transitions = list(zip(WAVES[:-1], WAVES[1:]))
    residuals_all = []
    for w_curr, w_next in transitions:
        r = compute_residuals(
            matrices[w_curr], wave_means[w_curr],
            wave_means[w_next], labels,
        )
        residuals_all.append(r)

    # ── 6. Fit alpha ─────────────────────────────────────────────────────
    alpha_result = fit_alpha(temporal_data, wave_means)
    alpha_star = alpha_result["alpha_star"]

    # ── 7. Forecast W8 ──────────────────────────────────────────────────
    print(f"  Forecasting W8...")
    forecast_result = forecast_w8(
        matrices[7], wave_means[7], alpha_star,
        temporal_core, labels,
    )

    # ── 8. Uncertainty envelope ──────────────────────────────────────────
    print(f"  Computing uncertainty envelopes...")
    envelope_result = uncertainty_envelope(
        residuals_all,
        forecast_result["forecast_vector"],
        wave_means[7],
        temporal_core,
        labels,
    )

    # ── 9. Linear trends ────────────────────────────────────────────────
    print(f"  Fitting linear trends...")
    trend_result = fit_linear_trends(
        wave_means, temporal_core, labels,
        forecast_result["per_construct"],
    )

    # ── Print comprehensive summary ──────────────────────────────────────
    print_summary(
        temporal_data, velocity_results, eq_distances,
        residuals_all, alpha_result, forecast_result,
        envelope_result, trend_result,
    )

    # ── Assemble output ──────────────────────────────────────────────────
    output = {
        "metadata": {
            "waves": WAVES,
            "wave_years": WAVE_YEARS,
            "n_constructs": temporal_data["n_constructs"],
            "temporal_core": [labels[i] for i in temporal_core],
            "n_temporal_core": len(temporal_core),
            "means_source": "synthetic" if args.synthetic else str(args.means_file),
        },
        "velocity_fields": {
            f"W{w}": {
                labels[i]: float(velocity_results[w][i])
                for i in range(len(labels))
                if not np.isnan(velocity_results[w][i])
            }
            for w in WAVES
        },
        "equilibrium_distances": {
            f"W{w}": eq_distances[w] for w in WAVES
        },
        "residuals": {
            f"W{w_curr}_to_W{w_next}": residuals_all[t_idx]
            for t_idx, (w_curr, w_next) in enumerate(transitions)
        },
        "alpha_fit": alpha_result,
        "forecast_w8": forecast_result,
        "uncertainty": envelope_result,
        "trends": trend_result,
    }

    # ── Save ─────────────────────────────────────────────────────────────
    out_dir = get_output_dir()
    out_path = out_dir / "mex_temporal.json"
    save_json(output, out_path)

    t_elapsed = time.time() - t_start
    print(f"\n  Total time: {t_elapsed:.1f}s")
    print(f"  Done.")


if __name__ == "__main__":
    main()
