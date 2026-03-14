# ordinal_model.jl — Proportional-odds ordered logit via hand-coded MLE
#
# ── Why hand-coded instead of using a package? ───────────────────────────────
# GLM.jl does not implement the proportional-odds model.  The closest Python
# equivalent (statsmodels.OrderedModel) is also a custom implementation — just
# a well-tested one.  We replicate its mathematical core here using:
#
#   Optim.jl    — LBFGS optimizer (same algorithm as statsmodels' 'bfgs' method)
#   ForwardDiff.jl — Automatic differentiation for exact gradient computation
#
# The advantage of ForwardDiff over statsmodels' numerical finite-difference
# gradient:  exact gradients mean fewer optimizer iterations to convergence
# and no step-size tuning.  On typical 1200-row survey data with K=5 categories
# and p=4 predictors, this cuts the number of function evaluations by ~3×.
#
# ── Proportional-odds model recap ────────────────────────────────────────────
# For ordinal Y ∈ {1,...,K} and covariates X (n×p):
#
#   P(Y ≤ k | X) = σ(α_k − X·β)    k = 1,...,K−1
#
# where σ is the logistic sigmoid and α_1 < α_2 < ... < α_{K-1} are cut-points
# (thresholds) separating adjacent categories on the latent scale.
#
# Cell probabilities:
#   P(Y = k | X) = P(Y ≤ k | X) − P(Y ≤ k−1 | X)
#               = σ(α_k − η) − σ(α_{k-1} − η)
#
# with α_0 = −∞  (σ(−∞) = 0) and  α_K = +∞  (σ(+∞) = 1).
#
# ── Unconstrained threshold parametrization ──────────────────────────────────
# The constraint α_1 < α_2 < ... < α_{K-1} cannot be imposed directly in an
# unconstrained optimizer.  We use the exp-sum reparametrization:
#
#   α_1 = γ_1                 (free: any real number)
#   α_k = α_{k-1} + exp(γ_k) for k ≥ 2
#
# Because exp(γ_k) > 0 always, the ordering α_{k-1} < α_k is guaranteed
# automatically for any γ.  The optimizer works entirely in γ-space (unconstrained),
# and we decode back to α only when evaluating the log-likelihood.
# See JULIA_BRIDGE_PRIMER.md § 4.2 for full derivation.
#
# ── Parameter vector layout ──────────────────────────────────────────────────
# The optimizer receives a single vector `params` of length p + (K−1):
#   params[1:p]      = β  (regression coefficients)
#   params[p+1:end]  = γ  (unconstrained threshold parameters)
#
# ── ForwardDiff and type parametrization ─────────────────────────────────────
# ForwardDiff computes gradients by replacing Float64 values with dual numbers
# (a + bε where ε² = 0).  All arithmetic operations are overloaded for duals.
# For this to work, every function in the computational graph must be generic
# over the numeric type T — if we hardcode `Float64` inside `ordered_logit_nll`,
# ForwardDiff cannot propagate dual numbers through it.
#
# The `where T` and `where T <: Real` clauses make functions generic:
#   `function foo(x::T) where T` compiles a specialized version for each T.
# This is Julia's version of C++ templates or Rust generics.

using LinearAlgebra: dot
using Optim
using ForwardDiff


# ── Helpers ───────────────────────────────────────────────────────────────────

"""
    sigmoid(x::T) where T <: Real -> T

Numerically stable logistic sigmoid σ(x) = 1 / (1 + exp(−x)).

# Why two branches?

For large positive x, exp(−x) underflows to 0 → result is cleanly 1.0.
For large negative x, exp(x) underflows to 0 → result is cleanly 0.0.
The naive formula `1/(1+exp(-x))` overflows for large negative x on
some platforms (exp(800) = Inf → 1/Inf = 0, but intermediate Inf can
cause NaN in gradients).

# `@inline`

The `@inline` macro hints to the Julia compiler to inline this call at each
call site (copy the function body instead of generating a function call
instruction).  Useful for tiny functions called millions of times in inner loops.
Python has no equivalent; numpy's ufuncs are already vectorized C.

# `where T <: Real`

Constrains T to be a subtype of Real (Float64, Float32, dual numbers, etc.).
Without this constraint, T could be a String or a DataFrame, which makes no sense.
ForwardDiff will call this with T = Dual{...} when computing gradients.
"""
@inline function sigmoid(x::T) where T <: Real
    x >= 0 ? one(T) / (one(T) + exp(-x)) : exp(x) / (one(T) + exp(x))
    # `one(T)` returns the multiplicative identity element of type T.
    # For Float64 it is 1.0; for Dual numbers it is Dual(1.0, 0.0).
    # This ensures type stability — the return type is always T.
end


"""
    decode_thresholds(γ::AbstractVector{T}) where T -> Vector{T}

Decode unconstrained γ parameters into ordered cut-points α.

    α_1 = γ_1
    α_k = α_{k-1} + exp(γ_k)   for k ≥ 2

# Why `AbstractVector{T}` rather than `Vector{T}`?

ForwardDiff passes slices of its dual-number parameter vector as SubArray types
(a view into a larger array).  `AbstractVector{T}` accepts both `Vector{T}` and
`SubArray` slices, making the function compatible with both normal and AD calls.

# Type propagation

Because `exp` is overloaded for dual numbers, and `α[k-1] + exp(γ[k])` uses
only + and exp, the result is automatically a Vector{T} whether T is Float64 or
Dual.  This is how ForwardDiff propagates derivatives through the whole chain.
"""
function decode_thresholds(γ::AbstractVector{T}) where T
    K1 = length(γ)
    α  = Vector{T}(undef, K1)   # allocate output of the same type as input
    α[1] = γ[1]
    for k in 2:K1
        α[k] = α[k-1] + exp(γ[k])   # guaranteed > α[k-1] because exp > 0
    end
    return α
end


"""
    encode_thresholds(α::Vector{Float64}) -> Vector{Float64}

Inverse of decode_thresholds: convert ordered α into unconstrained γ.

    γ_1 = α_1
    γ_k = log(α_k − α_{k-1})   for k ≥ 2

Used to initialize the optimizer at a sensible starting point derived from
empirical cumulative proportions.  Without a good initialization, LBFGS may
take many more iterations or converge to a local minimum.

The `max(..., 1e-6)` guards against α_k − α_{k-1} ≤ 0, which can happen when
empirical proportions produce degenerate starting thresholds.
"""
function encode_thresholds(α::Vector{Float64})
    K1 = length(α)
    γ  = Vector{Float64}(undef, K1)
    γ[1] = α[1]
    for k in 2:K1
        γ[k] = log(max(α[k] - α[k-1], 1e-6))
    end
    return γ
end


# ── Negative log-likelihood ────────────────────────────────────────────────────

"""
    ordered_logit_nll(params, X, y, K) -> T

Negative log-likelihood of the proportional-odds model.

# Parameter vector

    params = [β₁, ..., βₚ, γ₁, ..., γ_{K-1}]
    length = p + (K − 1)

# Computation per observation i

    η_i  = X[i, :] · β              (linear predictor)
    P(Y_i = k | X_i) = σ(α_k − η_i) − σ(α_{k-1} − η_i)

    contribution to log-likelihood:  log P(Y_i = y_i | X_i)

# Numerical floor

`max(prob, T(1e-12))` prevents log(0) = −Inf which would produce NaN gradients.
`T(1e-12)` converts the literal to the current numeric type T (works for duals).

# Why minimize NLL instead of maximizing LL?

Optim.jl (and most numerical optimizers) minimize by convention.
NLL = −LL, so minimizing NLL is identical to maximizing LL.

# Generic type T

The function is generic over T so ForwardDiff can pass dual numbers through it
and compute exact gradients.  The caller (fit_ordered_logit) passes X and y as
plain Float64 arrays — only `params` needs to be T.
"""
function ordered_logit_nll(params::AbstractVector{T}, X::Matrix{Float64},
                            y::Vector{Int}, K::Int)::T where T
    p  = size(X, 2)
    β  = params[1:p]         # regression coefficients (view into params)
    γ  = params[p+1:end]     # unconstrained threshold parameters
    α  = decode_thresholds(γ) # ordered cut-points α_1 < ... < α_{K-1}
    n  = size(X, 1)
    ll = zero(T)              # `zero(T)` = 0 of the right type (Float64 or Dual)

    for i in 1:n
        η  = dot(X[i, :], β)   # linear predictor: dot product of row i with β
        yi = y[i]
        # Upper CDF boundary: σ(α_{yi} − η).  For yi = K (top category), use 1.
        upper = yi <= length(α) ? sigmoid(α[yi]   - η) : one(T)
        # Lower CDF boundary: σ(α_{yi-1} − η).  For yi = 1 (bottom category), use 0.
        lower = yi > 1          ? sigmoid(α[yi-1] - η) : zero(T)
        # Cell probability and its log contribution to the likelihood.
        prob  = upper - lower
        ll   += log(max(prob, T(1e-12)))   # T(1e-12) converts literal to type T
    end
    return -ll   # return negative LL (we minimize, so this is our objective)
end


# ── Fitted model struct ────────────────────────────────────────────────────────

"""
Fitted proportional-odds model.

# Struct in Julia

`struct` creates an immutable value type.  Unlike Python dataclasses or
namedtuples, Julia structs:
  - cannot be modified after construction (no `model.coef = ...`)
  - are stack-allocated if small enough (no heap pointer chasing)
  - benefit from full type inference — the compiler knows every field's type

Use `mutable struct` if you need to modify fields after construction.

# Fields

  coef       :: Vector{Float64}   — β coefficients, length p
  thresholds :: Vector{Float64}   — α cut-points, length K−1, strictly ordered
  K          :: Int               — number of outcome categories
  converged  :: Bool              — whether LBFGS reported convergence
  nll        :: Float64           — final negative log-likelihood (lower = better fit)
"""
struct OrderedLogitModel
    coef       :: Vector{Float64}
    thresholds :: Vector{Float64}
    K          :: Int
    converged  :: Bool
    nll        :: Float64
end


"""
    fit_ordered_logit(X, y; K, maxiter=500, tol=1e-6) -> OrderedLogitModel

Fit the proportional-odds model via LBFGS with ForwardDiff gradients.

# Arguments

  X        : n × p design matrix (no intercept — the PO model doesn't use one)
  y        : category labels Vector{Int}, values in 1:K
  K        : number of categories
  maxiter  : max optimizer iterations (100 for bootstrap, 500 for main fit)
  tol      : gradient norm tolerance for convergence

# Initialization strategy

Starting the optimizer near the true solution dramatically reduces iterations.
We initialize thresholds at the *logit of the empirical cumulative proportions*:

    qₖ = P(Y ≤ k)  (observed fraction of responses in categories 1..k)
    logit(qₖ) = log(qₖ / (1 − qₖ))

These are the MLE thresholds under the null model β = 0 (no covariates).
Starting β = 0 is always valid regardless of the data scale.

The `clamp(q, 1e-4, 1-1e-4)` prevents logit(0) = −∞ or logit(1) = +∞
when a category is empty.

# LBFGS

Limited-memory BFGS (L-BFGS) is a quasi-Newton method that approximates the
Hessian using a small history of gradient vectors.  It converges in O(p) steps
for well-conditioned problems.  With exact ForwardDiff gradients, one optimizer
step takes roughly the same wall time as one statsmodels step, but requires
far fewer steps.

# `allow_f_increases=true`

Tells the optimizer not to abort if the objective function temporarily increases
(which can happen due to floating-point rounding).  This improves robustness on
ill-conditioned bootstrap resamples.

# Design choice: maxiter=100 for bootstrap

Bootstrap refits run on resampled data which may be ill-conditioned (e.g. all
observations in one category).  Capping at 100 iterations prevents runaway BFGS
from hanging the sweep, matching the Python approach (`maxiter=100` in the
bootstrap loop of `sweep_construct_dr.py`).
"""
function fit_ordered_logit(
    X::Matrix{Float64},
    y::Vector{Int};
    K::Int,
    maxiter::Int   = 500,
    tol::Float64   = 1e-6,
)::OrderedLogitModel
    n, p = size(X)
    K1   = K - 1   # number of threshold parameters

    # ── Initialization ─────────────────────────────────────────────────────
    # Empirical cumulative proportions → logit → γ encoding.
    # `sum(y .<= k) / n`: `.<=` broadcasts, counts how many y values are ≤ k.
    counts  = [sum(y .<= k) / n for k in 1:K1]
    logit_q = [log(max(q, 1e-4) / max(1 - q, 1e-4)) for q in counts]
    γ0      = encode_thresholds(logit_q)
    params0 = vcat(zeros(p), γ0)   # vcat: vertical concatenate (stack vectors)

    # ── Objective and gradient ──────────────────────────────────────────────
    # `f` is a closure over X, y, K — captures them from the enclosing scope.
    f(params)    = ordered_logit_nll(params, X, y, K)

    # ForwardDiff.gradient!(grad, f, p_) computes ∇f(p_) and writes it into grad.
    # The `!` convention in Julia marks in-place mutation — `grad` is modified.
    # Python equivalent: scipy.optimize minimizes with numerical gradient by default;
    # to use exact gradient you pass `jac=lambda p: grad_fn(p)`.
    g!(grad, p_) = ForwardDiff.gradient!(grad, f, p_)

    # ── Optimization ───────────────────────────────────────────────────────
    result = Optim.optimize(
        f, g!, params0,
        Optim.LBFGS(),            # optimizer algorithm
        Optim.Options(
            iterations        = maxiter,
            g_tol             = tol,      # stop when ||∇f|| < tol
            show_trace        = false,    # no verbose output
            allow_f_increases = true,     # tolerate occasional increases (robustness)
        ),
    )

    # ── Extract results ─────────────────────────────────────────────────────
    params_hat = Optim.minimizer(result)   # parameter vector at minimum
    β̂  = params_hat[1:p]
    α̂  = decode_thresholds(params_hat[p+1:end])   # decode γ → α

    return OrderedLogitModel(β̂, α̂, K, Optim.converged(result), Optim.minimum(result))
end


"""
    predict_proba(model::OrderedLogitModel, X::Matrix{Float64}) -> Matrix{Float64}

Predict P(Y = k | X) for k = 1,...,K.  Returns n × K probability matrix.

# Algorithm

For each observation i:
  η_i = X[i,:] · β
  P(Y ≤ k | X_i) = σ(α_k − η_i)   for k = 1,...,K−1
  P(Y = k | X_i) = P(Y ≤ k | X_i) − P(Y ≤ k−1 | X_i)

# Why normalize at the end?

Floating-point rounding can make row sums slightly ≠ 1.  Dividing by the row sum
ensures the output is a valid probability distribution.  The `max(..., 1e-10)`
floor prevents probabilities from being exactly 0, which would cause log(0) = −Inf
in the downstream log-likelihood.

# Multiple dispatch in action

Calling `predict_proba(model, X)` dispatches to *this* method because the first
argument has type `OrderedLogitModel`.  If you later define a `BayesianModel`
struct and add `predict_proba(m::BayesianModel, X)`, Julia will dispatch correctly
without any `isinstance()` checks.  This is the Julia equivalent of Python's
`__call__` or method overloading.
"""
function predict_proba(model::OrderedLogitModel, X::Matrix{Float64})::Matrix{Float64}
    n     = size(X, 1)
    K     = model.K
    α     = model.thresholds
    β     = model.coef
    probs = Matrix{Float64}(undef, n, K)   # pre-allocate: no zero-initialization

    for i in 1:n
        η        = dot(X[i, :], β)   # linear predictor for observation i
        cum_prev = 0.0               # P(Y ≤ 0 | X) = 0 by convention
        for k in 1:K
            # Cumulative probability P(Y ≤ k | X).
            # For k = K, the upper threshold is +∞ → σ(+∞) = 1.
            cum_k      = k <= length(α) ? sigmoid(α[k] - η) : 1.0
            probs[i,k] = max(cum_k - cum_prev, 1e-10)   # cell probability, floored
            cum_prev   = cum_k
        end
        probs[i, :] ./= sum(probs[i, :])   # normalize row to valid probability distribution
    end
    return probs
end


# ── Logistic regression (propensity model) ────────────────────────────────────
#
# The DR estimator needs P(survey = A | SES) — a binary outcome.
# We use our own logistic regression rather than GLM.jl to:
#   1. Share the Optim.jl / ForwardDiff backend (consistent numerics)
#   2. Operate on Matrix{Float64} directly (no DataFrame overhead)
#   3. Avoid a GLM.jl dependency for a single binary model
#
# The propensity model uses an intercept column (design matrix Xc = [1 | X]).
# The ordered logit model does NOT use an intercept (the thresholds α absorb it).


"""
    fit_logistic(X, y; maxiter=500) -> Vector{Float64}

Binary logistic regression via LBFGS + ForwardDiff.

  X  : n × (p+1) design matrix with intercept in first column
  y  : binary labels Vector{Float64} in {0.0, 1.0}

Returns β of length p+1.  Caller is responsible for adding the intercept column.

# Nested function definition

`function nll(β)` is a *closure* — it captures `X` and `y` from the enclosing
scope of `fit_logistic`.  Julia creates a new closure object each time
`fit_logistic` is called, similar to Python's inner functions.
"""
function fit_logistic(
    X::Matrix{Float64},
    y::Vector{Float64};
    maxiter::Int = 500,
)::Vector{Float64}
    p = size(X, 2)

    # Closure over X and y — captures them by reference.
    function nll(β)
        ll = 0.0
        for i in axes(X, 1)    # axes(X, 1) = 1:n, valid index range for rows
            η   = dot(X[i, :], β)
            p_i = sigmoid(η)
            # Bernoulli log-likelihood: y·log(p) + (1-y)·log(1-p)
            ll += y[i] * log(max(p_i, 1e-12)) + (1 - y[i]) * log(max(1 - p_i, 1e-12))
        end
        return -ll
    end

    g!(grad, β) = ForwardDiff.gradient!(grad, nll, β)
    result = Optim.optimize(
        nll, g!, zeros(p),    # start at β = 0 (equal class prior)
        Optim.LBFGS(),
        Optim.Options(iterations=maxiter, show_trace=false, allow_f_increases=true),
    )
    return Optim.minimizer(result)
end


"""
    predict_logistic(β, X) -> Vector{Float64}

P(y = 1 | X) from logistic coefficients β.  Returns n-vector of probabilities.

# List comprehension

`[expr for i in range]` creates a Vector in one pass.
Python equivalent: `np.array([sigmoid(X[i,:] @ β) for i in range(n)])`.
Julia's list comprehensions are type-inferred and compiled, not interpreted.
"""
function predict_logistic(β::Vector{Float64}, X::Matrix{Float64})::Vector{Float64}
    return [sigmoid(dot(X[i, :], β)) for i in axes(X, 1)]
end
