"""
    cronbach.jl — Cronbach's alpha and scale helpers

Ported from build_construct_variables.py:
  - cronbach_alpha        : standard formula
  - scale_to_output       : rescale to [out_min, out_max]
  - reverse_code          : reverse-code ordinal items
  - build_construct_scale : reflective scale aggregation with alpha
"""

using Statistics: mean, var


"""
    cronbach_alpha(X::Matrix{Float64}) -> Float64

Cronbach's alpha for an n_obs × n_items item matrix.

Formula:  α = (K / (K-1)) · (1 - Σσ²_i / σ²_total)
"""
function cronbach_alpha(X::Matrix{Float64})::Float64
    n_obs, K = size(X)
    if K < 2 || n_obs < 2
        return NaN
    end
    item_vars  = [var(X[:, j]; corrected=true) for j in 1:K]
    total_vars = var(vec(sum(X, dims=2)); corrected=true)
    total_vars ≈ 0.0 && return NaN
    return (K / (K - 1)) * (1.0 - sum(item_vars) / total_vars)
end


"""
    scale_to_output(v; out_min=1.0, out_max=10.0) -> Vector{Float64}

Linearly rescale v from its [min,max] to [out_min, out_max].
Returns midpoint vector if max ≈ min.
"""
function scale_to_output(v::Vector{Float64}; out_min=1.0, out_max=10.0)::Vector{Float64}
    lo, hi = minimum(v), maximum(v)
    if hi - lo < 1e-10
        return fill((out_min + out_max) / 2.0, length(v))
    end
    return out_min .+ (out_max - out_min) .* (v .- lo) ./ (hi - lo)
end


"""
    reverse_code(v::Vector{Float64}) -> Vector{Float64}

Reverse-code: new = max + min - original.
"""
function reverse_code(v::Vector{Float64})::Vector{Float64}
    lo, hi = minimum(v), maximum(v)
    return hi .+ lo .- v
end


"""
    build_construct_scale(items; reverse_idx, out_min, out_max)
        -> (scores::Vector{Float64}, alpha::Float64)

Build a reflective scale from item matrix (n_obs × n_items):
1. Reverse-code columns in reverse_idx (1-indexed).
2. Row means (NaN-aware, require ≥ 1 item).
3. Scale to [out_min, out_max].

Returns (scores, cronbach_alpha).
"""
function build_construct_scale(
    items::Matrix{Float64};
    reverse_idx::Vector{Int} = Int[],
    out_min::Float64 = 1.0,
    out_max::Float64 = 10.0,
)::Tuple{Vector{Float64}, Float64}
    n_obs, K = size(items)
    work = copy(items)

    for j in reverse_idx
        col = work[:, j]
        valid = col[.!isnan.(col)]
        if !isempty(valid)
            lo, hi = minimum(valid), maximum(valid)
            work[:, j] = hi .+ lo .- col
        end
    end

    scores = Vector{Float64}(undef, n_obs)
    for i in 1:n_obs
        row   = work[i, :]
        valid = row[.!isnan.(row)]
        scores[i] = isempty(valid) ? NaN : mean(valid)
    end

    complete = vec(.!any(isnan.(work), dims=2))
    alpha = sum(complete) >= 2 ? cronbach_alpha(work[complete, :]) : NaN

    valid_mask = .!isnan.(scores)
    if sum(valid_mask) > 0
        scaled = copy(scores)
        scaled[valid_mask] = scale_to_output(scores[valid_mask]; out_min=out_min, out_max=out_max)
        return scaled, alpha
    end
    return scores, alpha
end
