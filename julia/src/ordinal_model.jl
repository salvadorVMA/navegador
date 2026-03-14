"""
    ordinal_model.jl — Proportional-odds ordered logit via MLE

Implements a self-contained proportional-odds (PO) model using Optim.jl
for MLE and ForwardDiff.jl for gradients.

PO model:
    P(Y ≤ k | X) = σ(α_k - Xβ)    for k = 1 … K-1

Log-likelihood:
    ℓ = Σ_i log [σ(α_{y_i} - X_i β) - σ(α_{y_i-1} - X_i β)]

Threshold parametrization (unconstrained for optimization):
    α_1 = γ_1
    α_k = α_{k-1} + exp(γ_k)   for k ≥ 2
"""

using LinearAlgebra: dot
using Optim
using ForwardDiff


# ── Helpers ──────────────────────────────────────────────────────────────────

"""Numerically stable sigmoid σ(x) = 1/(1+exp(-x))."""
@inline function sigmoid(x::T) where T <: Real
    x >= 0 ? one(T) / (one(T) + exp(-x)) : exp(x) / (one(T) + exp(x))
end

"""Decode unconstrained γ → ordered thresholds α."""
function decode_thresholds(γ::AbstractVector{T}) where T
    K1 = length(γ)
    α  = Vector{T}(undef, K1)
    α[1] = γ[1]
    for k in 2:K1
        α[k] = α[k-1] + exp(γ[k])
    end
    return α
end

"""Encode ordered α → unconstrained γ (inverse of decode_thresholds)."""
function encode_thresholds(α::Vector{Float64})
    K1 = length(α)
    γ  = Vector{Float64}(undef, K1)
    γ[1] = α[1]
    for k in 2:K1
        γ[k] = log(max(α[k] - α[k-1], 1e-6))
    end
    return γ
end


# ── Negative log-likelihood ───────────────────────────────────────────────────

"""
Negative log-likelihood of the proportional-odds model.
params = [β (p,); γ (K-1,)]
"""
function ordered_logit_nll(params::AbstractVector{T}, X::Matrix{Float64},
                            y::Vector{Int}, K::Int)::T where T
    p  = size(X, 2)
    β  = params[1:p]
    γ  = params[p+1:end]
    α  = decode_thresholds(γ)
    n  = size(X, 1)
    ll = zero(T)
    for i in 1:n
        η  = dot(X[i, :], β)
        yi = y[i]
        upper = yi <= length(α) ? sigmoid(α[yi]   - η) : one(T)
        lower = yi > 1          ? sigmoid(α[yi-1] - η) : zero(T)
        prob  = upper - lower
        ll   += log(max(prob, T(1e-12)))
    end
    return -ll
end


# ── Fitted model struct ───────────────────────────────────────────────────────

"""Fitted proportional-odds model."""
struct OrderedLogitModel
    coef       :: Vector{Float64}   # β (p,)
    thresholds :: Vector{Float64}   # α (K-1,) ordered cut-points
    K          :: Int               # number of categories
    converged  :: Bool
    nll        :: Float64
end


"""
    fit_ordered_logit(X, y; K, maxiter=500, tol=1e-6) -> OrderedLogitModel

Fit proportional-odds ordered logit by LBFGS+ForwardDiff.

X  : n × p design matrix (no intercept column)
y  : 1-indexed category labels, Vector{Int} in 1:K
K  : number of categories
"""
function fit_ordered_logit(
    X::Matrix{Float64},
    y::Vector{Int};
    K::Int,
    maxiter::Int   = 500,
    tol::Float64   = 1e-6,
)::OrderedLogitModel
    n, p = size(X)
    K1   = K - 1

    # Initialise thresholds from empirical cumulative proportions
    counts = [sum(y .<= k) / n for k in 1:K1]
    logit_q = [log(max(q, 1e-4) / max(1 - q, 1e-4)) for q in counts]
    γ0      = encode_thresholds(logit_q)
    params0 = vcat(zeros(p), γ0)

    f(params)     = ordered_logit_nll(params, X, y, K)
    g!(grad, p_)  = ForwardDiff.gradient!(grad, f, p_)

    result = Optim.optimize(
        f, g!, params0,
        Optim.LBFGS(),
        Optim.Options(
            iterations        = maxiter,
            g_tol             = tol,
            show_trace        = false,
            allow_f_increases = true,
        ),
    )

    params_hat = Optim.minimizer(result)
    β̂  = params_hat[1:p]
    α̂  = decode_thresholds(params_hat[p+1:end])

    return OrderedLogitModel(β̂, α̂, K, Optim.converged(result), Optim.minimum(result))
end


"""
    predict_proba(model::OrderedLogitModel, X::Matrix{Float64}) -> Matrix{Float64}

Predict P(Y=k | X) for k = 1…K. Returns n × K matrix.
"""
function predict_proba(model::OrderedLogitModel, X::Matrix{Float64})::Matrix{Float64}
    n     = size(X, 1)
    K     = model.K
    α     = model.thresholds
    β     = model.coef
    probs = Matrix{Float64}(undef, n, K)

    for i in 1:n
        η         = dot(X[i, :], β)
        cum_prev  = 0.0
        for k in 1:K
            cum_k     = k <= length(α) ? sigmoid(α[k] - η) : 1.0
            probs[i,k] = max(cum_k - cum_prev, 1e-10)
            cum_prev   = cum_k
        end
        probs[i, :] ./= sum(probs[i, :])
    end
    return probs
end


# ── Logistic regression (for propensity model) ───────────────────────────────

"""
    fit_logistic(X, y; maxiter=500) -> Vector{Float64}

Binary logistic regression P(y=1|X) via LBFGS. X must include intercept column.
"""
function fit_logistic(
    X::Matrix{Float64},
    y::Vector{Float64};
    maxiter::Int = 500,
)::Vector{Float64}
    p = size(X, 2)

    function nll(β)
        ll = 0.0
        for i in axes(X, 1)
            η   = dot(X[i, :], β)
            p_i = sigmoid(η)
            ll += y[i] * log(max(p_i, 1e-12)) + (1 - y[i]) * log(max(1 - p_i, 1e-12))
        end
        return -ll
    end

    g!(grad, β) = ForwardDiff.gradient!(grad, nll, β)
    result = Optim.optimize(
        nll, g!, zeros(p),
        Optim.LBFGS(),
        Optim.Options(iterations=maxiter, show_trace=false, allow_f_increases=true),
    )
    return Optim.minimizer(result)
end


"""
    predict_logistic(β, X) -> Vector{Float64}

P(y=1|X) from logistic coefficients.
"""
function predict_logistic(β::Vector{Float64}, X::Matrix{Float64})::Vector{Float64}
    return [sigmoid(dot(X[i, :], β)) for i in axes(X, 1)]
end
