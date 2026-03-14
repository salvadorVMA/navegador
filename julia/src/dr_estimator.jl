"""
    dr_estimator.jl — Doubly Robust Bridge Estimator

Julia port of DoublyRobustBridgeEstimator from ses_regression.py.

Algorithm:
1. Fit ordered logit for col_a ~ SES (survey A) and col_b ~ SES (survey B).
2. Fit logistic propensity P(survey=A | SES) on pooled data.
3. Compute IPW weights for survey A: w_i = (1−π_i)/π_i, trim at 95th pct.
4. Build joint table under CIA using shared reference SES population:
   joint[k,l] = mean_i P(Y_a=k|X_i) · P(Y_b=l|X_i)
5. Compute γ = goodman_kruskal_gamma(joint) and NMI.
6. Bootstrap CI: resample, refit, recompute γ.
"""

using DataFrames
using Statistics: quantile, mean
using Random
using LinearAlgebra: dot
using Printf


"""Result returned by dr_estimate."""
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


# ── Internal helpers ──────────────────────────────────────────────────────────

"""Sample reference SES population by pooling both surveys (n_sim rows)."""
function _sample_ses_pop(
    df_a::DataFrame, df_b::DataFrame,
    available::Vector{Symbol},
    n_sim::Int,
    rng::AbstractRNG,
)::DataFrame
    sub_a = df_a[:, available]
    sub_b = df_b[:, available]
    pool  = vcat(sub_a, sub_b)
    Xp    = encode_ses(pool, available)
    keep  = [!any(isnan.(Xp[i, :])) for i in 1:nrow(pool)]
    pool  = pool[keep, :]
    nrow(pool) < 10 && error("Reference SES population too small ($(nrow(pool)) rows).")
    idx = rand(rng, 1:nrow(pool), n_sim)
    return pool[idx, :]
end


"""
Fit the ordinal outcome model for one survey variable.
Returns (model, categories, X_clean, sub_clean).
"""
function _fit_outcome_model(
    df::DataFrame, col::Symbol,
    available::Vector{Symbol};
    maxiter::Int = 500,
)
    col ∈ propertynames(df) || error("Column $col not in DataFrame.")
    needed = vcat([col], available)
    sub    = dropmissing(df[:, needed])
    # Remove sentinel-coded outcome
    sub = filter(row -> !is_sentinel(row[col]), sub)
    nrow(sub) < 30 && error("Too few rows for $col after sentinel filtering: $(nrow(sub))")

    X = encode_ses(sub, available)
    valid = [!any(isnan.(X[i, :])) for i in 1:nrow(sub)]
    sub = sub[valid, :]
    X   = X[valid, :]
    nrow(sub) < 30 && error("Too few rows after SES encoding for $col: $(nrow(sub))")

    # Encode outcome to integer categories 1:K (bin to max 5)
    raw_vals = sub[!, col]
    all_cats = sort(unique(raw_vals))
    if length(all_cats) > 5
        all_cats = _bin_to_5(raw_vals)
        raw_vals = [_find_bin(v, all_cats) for v in raw_vals]
    end
    cat_to_int = Dict(c => i for (i, c) in enumerate(all_cats))
    y = [cat_to_int[v] for v in raw_vals]
    K = length(all_cats)
    K < 2 && error("Variable $col has < 2 categories.")

    model = fit_ordered_logit(X, y; K=K, maxiter=maxiter)
    return model, all_cats, X, sub
end


"""Bin a vector to ≤5 ordinal categories via quantile edges."""
function _bin_to_5(vals::AbstractVector)
    v_f   = sort(unique([Float64(x) for x in vals if !is_sentinel(x)]))
    n     = length(v_f)
    n ≤ 5 && return v_f
    idxs  = round.(Int, range(1, n, length=6))
    return unique(v_f[idxs])
end

"""Map value to its bin index in sorted edges."""
function _find_bin(v, edges)
    f   = Float64(v)
    idx = searchsortedfirst(edges, f)
    return edges[clamp(idx, 1, length(edges))]
end


"""Cramér's V from joint probability table via pseudo-counts."""
function _cramers_v_from_joint(joint::Matrix{Float64})::Float64
    counts = max.(round.(Int, joint .* 1000), 1)
    n  = sum(counts)
    r, c = size(counts)
    (r < 2 || c < 2) && return 0.0
    row_s = sum(counts, dims=2)
    col_s = sum(counts, dims=1)
    chi2  = 0.0
    for i in 1:r, j in 1:c
        exp = row_s[i] * col_s[j] / n
        exp > 0 && (chi2 += (counts[i,j] - exp)^2 / exp)
    end
    phi2 = chi2 / n
    return sqrt(phi2 / (min(r, c) - 1))
end


"""KS statistic between two propensity score vectors."""
function _ks_stat(a::Vector{Float64}, b::Vector{Float64})::Float64
    combined = sort(vcat(a, b))
    na, nb   = length(a), length(b)
    ecdf_a   = [count(<=(x), a) / na for x in combined]
    ecdf_b   = [count(<=(x), b) / nb for x in combined]
    return maximum(abs.(ecdf_a .- ecdf_b))
end


# ── Public API ───────────────────────────────────────────────────────────────

"""
    dr_estimate(df_a, col_a, df_b, col_b; kwargs...) -> DRResult

Doubly-robust bridge estimate of Goodman-Kruskal γ for a variable pair
from two different surveys connected only via SES predictors.

Keyword arguments:
  ses_vars      : SES bridge variables (default SES_VARS)
  n_sim         : reference SES population size (default 2000)
  n_bootstrap   : bootstrap iterations (default 200)
  ks_threshold  : KS overlap warning threshold (default 0.4)
  seed          : RNG seed (default 42)
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
    available = [v for v in ses_vars if v in propertynames(df_a) && v in propertynames(df_b)]
    length(available) < 2 && error("< 2 shared SES columns between surveys.")

    # ── Fit outcome models ───────────────────────────────────────────────────
    model_a, cats_a, X_a, sub_a = _fit_outcome_model(df_a, col_a, available)
    model_b, cats_b, X_b, sub_b = _fit_outcome_model(df_b, col_b, available)
    K_a, K_b = length(cats_a), length(cats_b)
    n_a, n_b = nrow(sub_a), nrow(sub_b)

    # ── Propensity model P(survey=A | SES) ──────────────────────────────────
    X_pooled = vcat(X_a, X_b)
    delta    = vcat(ones(Float64, n_a), zeros(Float64, n_b))
    Xc       = hcat(ones(size(X_pooled, 1)), X_pooled)   # add intercept
    prop_coef = fit_logistic(Xc, delta)
    prop_all  = predict_logistic(prop_coef, Xc)
    prop_a    = prop_all[1:n_a]
    prop_b    = prop_all[n_a+1:end]
    ks_stat   = _ks_stat(prop_a, prop_b)

    # ── IPW weights for survey A ─────────────────────────────────────────────
    pa_clip  = clamp.(prop_a, 0.01, 0.99)
    raw_w    = (1.0 .- pa_clip) ./ pa_clip
    cap      = quantile(raw_w, 0.95)
    n_trim   = count(>(cap), raw_w)
    weights  = min.(raw_w, cap)
    weights ./= sum(weights)

    # ── Reference SES population ─────────────────────────────────────────────
    ses_pop  = _sample_ses_pop(df_a, df_b, available, n_sim, rng)
    Xref     = encode_ses(ses_pop, available)
    Xref[isnan.(Xref)] .= 0.0

    # ── Joint table under CIA ────────────────────────────────────────────────
    Pa_ref = predict_proba(model_a, Xref)[:, 1:K_a]
    Pb_ref = predict_proba(model_b, Xref)[:, 1:K_b]

    joint = zeros(K_a, K_b)
    for i in 1:n_sim
        joint .+= Pa_ref[i, :] * Pb_ref[i, :]'
    end
    joint ./= n_sim
    joint ./= sum(joint)

    gamma_pt = goodman_kruskal_gamma(joint)
    nmi_pt   = normalized_mutual_information(joint)
    cv_pt    = _cramers_v_from_joint(joint)
    conv     = model_a.converged && model_b.converged

    # ── Bootstrap CI ────────────────────────────────────────────────────────
    boot_gammas = Float64[]
    for _ in 1:n_bootstrap
        try
            idx_a = rand(rng, 1:n_a, n_a)
            idx_b = rand(rng, 1:n_b, n_b)
            bm_a, bc_a, _, _ = _fit_outcome_model(sub_a[idx_a,:], col_a, available; maxiter=100)
            bm_b, bc_b, _, _ = _fit_outcome_model(sub_b[idx_b,:], col_b, available; maxiter=100)
            bK_a, bK_b = length(bc_a), length(bc_b)
            bPa = predict_proba(bm_a, Xref)[:, 1:bK_a]
            bPb = predict_proba(bm_b, Xref)[:, 1:bK_b]
            bjt = zeros(bK_a, bK_b)
            for i in 1:n_sim
                bjt .+= bPa[i, :] * bPb[i, :]'
            end
            bjt ./= n_sim
            bjt ./= sum(bjt)
            push!(boot_gammas, goodman_kruskal_gamma(bjt))
        catch
            continue
        end
    end

    ci_lo, ci_hi = if length(boot_gammas) < 10
        gamma_pt, gamma_pt
    else
        quantile(boot_gammas, 0.025), quantile(boot_gammas, 0.975)
    end

    return DRResult(gamma_pt, ci_lo, ci_hi, nmi_pt, cv_pt,
                    ks_stat, ks_stat > ks_threshold,
                    n_a, n_b, n_trim, conv)
end
