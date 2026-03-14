# dr_estimator.jl — Doubly Robust Bridge Estimator
#
# Julia port of DoublyRobustBridgeEstimator from ses_regression.py.
#
# ── What "doubly robust" means ────────────────────────────────────────────────
# The DR estimator combines two models:
#   1. Outcome models P(Y_a = k | SES) and P(Y_b = l | SES)
#      → correctly specified if SES fully explains the cross-survey relationship
#   2. Propensity model P(survey = A | SES)
#      → used to reweight survey A to look like survey B's SES distribution
#
# "Doubly robust" means the estimator is consistent if either model is correctly
# specified — though in practice both models are misspecified to some degree, so
# we treat the estimate as an approximation under the Conditional Independence
# Assumption (CIA): Y_a ⊥ Y_b | SES (the two attitude variables are conditionally
# independent given SES, i.e. SES fully mediates their co-variation).
#
# ── Algorithm overview ────────────────────────────────────────────────────────
# 1. Fit ordered logit:  col_a ~ SES on survey A  →  model_a
#    Fit ordered logit:  col_b ~ SES on survey B  →  model_b
# 2. Fit logistic:       I(survey=A) ~ SES on pooled data  →  propensity model
# 3. IPW weights for A:  w_i = (1 − π_i) / π_i,  trimmed at 95th percentile
# 4. Sample reference SES population X_ref (n_sim rows, pooled from A+B)
# 5. Build joint table under CIA:
#      joint[k,l] = (1/n_sim) Σ_i P(Y_a=k|X_ref_i) · P(Y_b=l|X_ref_i)
# 6. γ = goodman_kruskal_gamma(joint)
#    NMI = normalized_mutual_information(joint)
# 7. Bootstrap CI: resample rows of A and B independently, repeat steps 1–6

using DataFrames
using Statistics: quantile, mean
using Random
using LinearAlgebra: dot
using Printf


"""
Result returned by dr_estimate.

# Immutable struct design

All fields are set once at construction and never changed.  This makes
`DRResult` safe to pass between functions and store in arrays without aliasing
concerns.  Python equivalent: a frozen dataclass or namedtuple.

# Fields

  gamma       — Goodman-Kruskal γ point estimate
  gamma_ci_lo — 2.5th percentile of bootstrap distribution
  gamma_ci_hi — 97.5th percentile of bootstrap distribution
  nmi         — Normalized Mutual Information (diagnostic: detects non-monotonic SES)
  cramers_v   — Cramér's V (complementary association measure)
  ks_overlap  — Kolmogorov-Smirnov statistic between A/B propensity distributions
  ks_warning  — true if ks_overlap > threshold (surveys have very different SES)
  n_a, n_b    — effective sample sizes after sentinel filtering
  n_trimmed   — number of IPW weights clipped at 95th percentile
  converged   — true if both ordered logit models converged
"""
struct DRResult
    gamma       :: Float64
    gamma_ci_lo :: Float64
    gamma_ci_hi :: Float64
    nmi         :: Float64
    cramers_v   :: Float64
    ks_overlap  :: Float64
    ks_warning  :: Bool
    n_a         :: Int
    n_b         :: Int
    n_trimmed   :: Int
    converged   :: Bool
end


# ── Internal helpers ───────────────────────────────────────────────────────────
# Functions prefixed with `_` are private by convention (not exported).
# Julia has no access modifiers; `_` is a naming convention like Python.

"""
Sample a reference SES population by pooling rows from both surveys.

# Why pool both surveys for the reference population?

The joint table joint[k,l] = E_X[P(Y_a=k|X) · P(Y_b=l|X)] requires
integrating over a shared SES distribution.  Pooling A and B gives a
distribution that is "between" both surveys' SES profiles, which is appropriate
when we want to measure the association at a common reference population.

# `rand(rng, 1:nrow(pool), n_sim)`

Samples n_sim integers from 1:N with replacement.
Python equivalent: `rng.choice(N, size=n_sim, replace=True)`.
The explicit `rng` argument ensures reproducibility — the same seed always
produces the same reference population.
"""
function _sample_ses_pop(
    df_a::DataFrame, df_b::DataFrame,
    available::Vector{Symbol},
    n_sim::Int,
    rng::AbstractRNG,   # AbstractRNG accepts MersenneTwister or any other RNG
)::DataFrame
    # Stack both DataFrames vertically (concat rows).
    # `vcat` on DataFrames requires matching column names.
    sub_a = df_a[:, available]
    sub_b = df_b[:, available]
    pool  = vcat(sub_a, sub_b)

    # Filter to rows with no NaN in SES (so we sample only valid reference rows).
    Xp    = encode_ses(pool, available)
    keep  = [!any(isnan.(Xp[i, :])) for i in 1:nrow(pool)]
    pool  = pool[keep, :]
    nrow(pool) < 10 && error("Reference SES population too small ($(nrow(pool)) rows).")

    # Sample with replacement: creates a bootstrapped version of the pooled SES pop.
    idx = rand(rng, 1:nrow(pool), n_sim)
    return pool[idx, :]
end


"""
Fit an ordered logit outcome model for one survey column.

Returns (model, categories, X_clean, sub_clean):
  model      — fitted OrderedLogitModel
  categories — sorted unique outcome values (used to build K_a/K_b for joint table)
  X_clean    — design matrix after sentinel + NaN filtering
  sub_clean  — filtered DataFrame (used for bootstrap resampling)

# `col ∈ propertynames(df)` check

Ensures the column exists before trying to access it.
`∉` is the negation.  Using this check instead of `try/catch` gives a clear
error message when the column name is wrong.

# Category encoding

Survey outcomes are binned to at most 5 categories to keep the threshold count
(K−1) manageable for LBFGS.  With K=5, the parameter vector has p + 4 elements
(4 regression coefs + 4 threshold parameters), which LBFGS handles efficiently.
Larger K increases optimization dimensionality without meaningfully improving γ.
"""
function _fit_outcome_model(
    df::DataFrame, col::Symbol,
    available::Vector{Symbol};
    maxiter::Int = 500,
)
    col ∈ propertynames(df) || error("Column $col not in DataFrame.")

    # Select only the columns we need; dropmissing removes rows with `missing`
    # (Julia's typed missing, distinct from NaN which is a Float64 value).
    needed = vcat([col], available)
    sub    = dropmissing(df[:, needed])

    # Remove sentinel-coded outcome values (≥97 or <0).
    sub = filter(row -> !is_sentinel(row[col]), sub)
    nrow(sub) < 30 && error("Too few rows for $col after sentinel filtering: $(nrow(sub))")

    # Encode SES and drop rows with NaN in any SES variable.
    X     = encode_ses(sub, available)
    valid = [!any(isnan.(X[i, :])) for i in 1:nrow(sub)]
    sub   = sub[valid, :]
    X     = X[valid, :]
    nrow(sub) < 30 && error("Too few rows after SES encoding for $col: $(nrow(sub))")

    # ── Outcome encoding ─────────────────────────────────────────────────────
    raw_vals = sub[!, col]
    all_cats = sort(unique(raw_vals))   # sorted unique values = ordered categories

    # Bin to ≤5 categories if needed (reduces optimization dimension).
    if length(all_cats) > 5
        all_cats = _bin_to_5(raw_vals)
        raw_vals = [_find_bin(v, all_cats) for v in raw_vals]
    end

    # `Dict(c => i for (i, c) in enumerate(all_cats))` creates a mapping
    # category_value → integer label 1, 2, ..., K.
    # `enumerate` yields (index, value) pairs starting from 1.
    cat_to_int = Dict(c => i for (i, c) in enumerate(all_cats))
    y          = [cat_to_int[v] for v in raw_vals]
    K          = length(all_cats)
    K < 2 && error("Variable $col has < 2 distinct categories.")

    model = fit_ordered_logit(X, y; K=K, maxiter=maxiter)
    return model, all_cats, X, sub
end


"""
Bin a continuous vector to ≤5 ordinal categories via quantile edges.

`round.(Int, range(1, n, length=6))` generates 6 evenly-spaced indices into
the sorted unique values, giving quantile-based bin edges.
`unique()` removes duplicates that arise when many values share the same quantile.
"""
function _bin_to_5(vals::AbstractVector)
    # Filter sentinels and convert to Float64 for sorting.
    v_f  = sort(unique([Float64(x) for x in vals if !is_sentinel(x)]))
    n    = length(v_f)
    n ≤ 5 && return v_f   # already 5 or fewer — no binning needed
    idxs = round.(Int, range(1, n, length=6))   # 6 quantile positions → 5 bins
    return unique(v_f[idxs])
end


"""Map a value to its nearest bin edge (for category assignment)."""
function _find_bin(v, edges)
    f   = Float64(v)
    # `searchsortedfirst(edges, f)` returns the insertion point for f in sorted edges.
    # This gives the index of the first edge ≥ f (the bin f belongs to).
    # `clamp(idx, 1, length(edges))` handles out-of-bounds values.
    idx = searchsortedfirst(edges, f)
    return edges[clamp(idx, 1, length(edges))]
end


"""
Cramér's V from a joint probability table.

Converts the probability table to pseudo-counts (×1000, min 1) to use the
standard chi-squared formula.  This is an approximation — Cramér's V is
normally computed on actual counts — but it provides a comparable effect-size
measure alongside γ.

Cramér's V ∈ [0, 1] where 0 = independence and 1 = perfect association.
Unlike γ, it detects any form of association (not just monotonic).
"""
function _cramers_v_from_joint(joint::Matrix{Float64})::Float64
    # Convert probabilities to integer pseudo-counts (multiply by 1000).
    counts = max.(round.(Int, joint .* 1000), 1)   # `.` broadcasts; `max.` element-wise max
    n      = sum(counts)
    r, c   = size(counts)
    (r < 2 || c < 2) && return 0.0

    row_s = sum(counts, dims=2)   # row totals: r × 1 matrix
    col_s = sum(counts, dims=1)   # col totals: 1 × c matrix
    chi2  = 0.0
    for i in 1:r, j in 1:c      # compact double-loop (equivalent to nested for loops)
        exp = row_s[i] * col_s[j] / n   # expected count under independence
        exp > 0 && (chi2 += (counts[i,j] - exp)^2 / exp)
        # `cond && expr` is a short-circuit: evaluates `expr` only if `cond` is true.
        # Python equivalent: `if exp > 0: chi2 += ...`
    end
    phi2 = chi2 / n
    return sqrt(phi2 / (min(r, c) - 1))
end


"""
Kolmogorov-Smirnov statistic between two propensity score distributions.

KS measures the maximum difference between empirical CDFs.  A high KS statistic
(> 0.4) indicates that survey A and survey B have very different SES profiles —
the propensity weights will be extreme, and γ estimates less reliable.

This is a diagnostic, not a correction.  The KS warning flag in DRResult alerts
users to interpret results cautiously.
"""
function _ks_stat(a::Vector{Float64}, b::Vector{Float64})::Float64
    combined = sort(vcat(a, b))   # union of all observed propensity scores
    na, nb   = length(a), length(b)
    # ECDF at each combined value: fraction of scores in a (or b) ≤ x.
    ecdf_a   = [count(<=(x), a) / na for x in combined]
    ecdf_b   = [count(<=(x), b) / nb for x in combined]
    # `count(<=(x), a)` uses partial application: `<=(x)` creates a 1-arg function
    # equivalent to `y -> y <= x`.  Python equivalent: `np.sum(a <= x)`.
    return maximum(abs.(ecdf_a .- ecdf_b))
end


# ── Public API ─────────────────────────────────────────────────────────────────

"""
    dr_estimate(df_a, col_a, df_b, col_b; kwargs...) -> DRResult

Doubly-robust estimate of Goodman-Kruskal γ for a pair of ordinal variables
from two different surveys connected only through shared SES predictors.

# Keyword arguments

  ses_vars    : SES bridge variables (default SES_VARS = [:sexo, :edad, :escol, :Tam_loc])
  n_sim       : reference SES population size (default 2000; larger → less MC noise)
  n_bootstrap : bootstrap iterations for CI (default 200; <10 → degenerate CI)
  ks_threshold: KS statistic warning threshold (default 0.4)
  seed        : RNG seed (default 42; fix for reproducibility)

# Keyword argument syntax in Julia

After a semicolon in the function signature, arguments are keyword-only:
  `dr_estimate(df_a, col_a, df_b, col_b; n_sim=2000, seed=42)`
Python equivalent: `def dr_estimate(df_a, col_a, ..., *, n_sim=2000, seed=42)`.

# `available` SES variables

We use only SES variables present in *both* DataFrames to handle surveys with
different column subsets.  This mirrors the Python implementation's
`_check_ses_vars()` logic.

# MersenneTwister

Julia's default PRNG.  `MersenneTwister(42)` creates a deterministic RNG.
Pass the same `seed` to get the same bootstrap CI across runs.
Python equivalent: `np.random.default_rng(42)` (PCG64, different algorithm
but same reproducibility principle).
"""
function dr_estimate(
    df_a::DataFrame, col_a::Symbol,
    df_b::DataFrame, col_b::Symbol;
    ses_vars::Vector{Symbol} = SES_VARS,
    n_sim::Int               = 2000,
    n_bootstrap::Int         = 200,
    ks_threshold::Float64    = 0.4,
    seed::Int                = 42,
)::DRResult
    rng = MersenneTwister(seed)

    # Find SES variables present in both DataFrames.
    available = [v for v in ses_vars if v in propertynames(df_a) && v in propertynames(df_b)]
    length(available) < 2 && error("< 2 shared SES columns between surveys.")

    # ── Step 1: Fit ordered logit outcome models ──────────────────────────────
    model_a, cats_a, X_a, sub_a = _fit_outcome_model(df_a, col_a, available)
    model_b, cats_b, X_b, sub_b = _fit_outcome_model(df_b, col_b, available)
    K_a, K_b = length(cats_a), length(cats_b)
    n_a, n_b = nrow(sub_a), nrow(sub_b)

    # ── Step 2: Propensity model P(survey=A | SES) ────────────────────────────
    # Stack the design matrices vertically and create binary labels.
    X_pooled = vcat(X_a, X_b)
    delta    = vcat(ones(Float64, n_a), zeros(Float64, n_b))   # 1=survey A, 0=survey B
    # Add intercept column: `hcat(ones(n), X)` prepends a column of 1s.
    Xc       = hcat(ones(size(X_pooled, 1)), X_pooled)
    prop_coef = fit_logistic(Xc, delta)
    prop_all  = predict_logistic(prop_coef, Xc)
    prop_a    = prop_all[1:n_a]
    prop_b    = prop_all[n_a+1:end]
    ks_stat   = _ks_stat(prop_a, prop_b)

    # ── Step 3: IPW weights for survey A ─────────────────────────────────────
    # IPW weight = (1 − π_i) / π_i  reweights A to look like B's SES profile.
    # Clamp propensity scores away from 0/1 to prevent weight explosion.
    pa_clip  = clamp.(prop_a, 0.01, 0.99)   # `clamp.` broadcasts element-wise
    raw_w    = (1.0 .- pa_clip) ./ pa_clip  # Horvitz-Thompson style inverse weights
    cap      = quantile(raw_w, 0.95)        # 95th percentile cap (robust to outliers)
    n_trim   = count(>(cap), raw_w)         # `>(cap)` = partial application: x -> x > cap
    weights  = min.(raw_w, cap)             # trim weights at cap
    weights ./= sum(weights)               # normalize to sum = 1

    # ── Step 4: Reference SES population ─────────────────────────────────────
    ses_pop = _sample_ses_pop(df_a, df_b, available, n_sim, rng)
    Xref    = encode_ses(ses_pop, available)
    Xref[isnan.(Xref)] .= 0.0   # replace any residual NaN with 0 (shouldn't occur)

    # ── Step 5: Build joint table under CIA ───────────────────────────────────
    # Pa_ref[i,k] = P(Y_a = k | X_ref_i),  shape (n_sim, K_a)
    # Pb_ref[i,l] = P(Y_b = l | X_ref_i),  shape (n_sim, K_b)
    Pa_ref = predict_proba(model_a, Xref)[:, 1:K_a]
    Pb_ref = predict_proba(model_b, Xref)[:, 1:K_b]

    # Accumulate outer products: joint += Pa_ref[i,:] ⊗ Pb_ref[i,:]
    # Pa_ref[i,:] is a column vector (K_a,); Pb_ref[i,:]' is a row vector (K_b,).
    # Their product is a (K_a × K_b) matrix.
    joint = zeros(K_a, K_b)
    for i in 1:n_sim
        joint .+= Pa_ref[i, :] * Pb_ref[i, :]'   # `.+=` in-place addition (avoids allocation)
    end
    joint ./= n_sim    # normalize to average outer product
    joint ./= sum(joint)  # re-normalize to probability table (sum = 1)

    # ── Step 6: Point estimates ───────────────────────────────────────────────
    gamma_pt = goodman_kruskal_gamma(joint)
    nmi_pt   = normalized_mutual_information(joint)
    cv_pt    = _cramers_v_from_joint(joint)
    conv     = model_a.converged && model_b.converged

    # ── Step 7: Bootstrap CI ──────────────────────────────────────────────────
    # Resample rows independently from each survey (non-parametric bootstrap).
    # This preserves the within-survey correlation structure while allowing
    # the joint distribution to vary across resamples.
    boot_gammas = Float64[]   # grows dynamically as successes accumulate
    for _ in 1:n_bootstrap
        try
            # Sample n_a rows from A and n_b rows from B with replacement.
            idx_a = rand(rng, 1:n_a, n_a)
            idx_b = rand(rng, 1:n_b, n_b)
            # Refit outcome models on bootstrap samples (maxiter=100 to prevent hangs).
            bm_a, bc_a, _, _ = _fit_outcome_model(sub_a[idx_a,:], col_a, available; maxiter=100)
            bm_b, bc_b, _, _ = _fit_outcome_model(sub_b[idx_b,:], col_b, available; maxiter=100)
            bK_a, bK_b = length(bc_a), length(bc_b)
            # Reuse the same reference SES population X_ref for all bootstrap iterations.
            # This eliminates MC variance from reference sampling.
            bPa = predict_proba(bm_a, Xref)[:, 1:bK_a]
            bPb = predict_proba(bm_b, Xref)[:, 1:bK_b]
            bjt = zeros(bK_a, bK_b)
            for i in 1:n_sim
                bjt .+= bPa[i, :] * bPb[i, :]'
            end
            bjt ./= n_sim
            bjt ./= sum(bjt)
            push!(boot_gammas, goodman_kruskal_gamma(bjt))   # append to growing array
        catch
            continue   # skip failed bootstrap iterations (ill-conditioned resample)
        end
    end

    # Percentile bootstrap CI (2.5% and 97.5% quantiles of the boot distribution).
    # If fewer than 10 bootstrap iterations succeeded, return degenerate CI = point estimate.
    ci_lo, ci_hi = if length(boot_gammas) < 10
        gamma_pt, gamma_pt   # degenerate: returns two-element tuple
    else
        quantile(boot_gammas, 0.025), quantile(boot_gammas, 0.975)
    end

    # ── Construct and return result ───────────────────────────────────────────
    return DRResult(gamma_pt, ci_lo, ci_hi, nmi_pt, cv_pt,
                    ks_stat, ks_stat > ks_threshold,
                    n_a, n_b, n_trim, conv)
end
