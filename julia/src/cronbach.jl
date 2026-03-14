# cronbach.jl — Cronbach's alpha and scale construction helpers
#
# Ported from build_construct_variables.py.
#
# ── Reflective scale model ────────────────────────────────────────────────────
# A *reflective* construct is one where a latent variable causes the item
# responses.  Items should:
#   1. Correlate with each other (internal consistency → Cronbach's α)
#   2. Carry the same directional polarity (reverse-coded items need flipping)
#   3. Average to a composite score
#
# This file implements those three operations and wraps them in
# `build_construct_scale`, which is the main entry point for the sweep.
#
# ── Selective import ──────────────────────────────────────────────────────────
# `using Statistics: mean, var` imports only those two names from Statistics.
# This avoids polluting the module namespace with everything in Statistics and
# makes dependencies explicit.  Same rationale as Python's
# `from statistics import mean` vs `import statistics`.

using Statistics: mean, var


"""
    cronbach_alpha(X::Matrix{Float64}) -> Float64

Cronbach's α for an n_obs × n_items item matrix X.

# Formula

    α = (K / (K − 1)) · (1 − Σᵢ σ²ᵢ / σ²_total)

where:
  K         = number of items
  σ²ᵢ       = variance of item i (Bessel-corrected, i.e. divided by n−1)
  σ²_total  = variance of the row sums (the composite score)

# Interpretation

  α ≥ 0.70  → "good" — items measure a coherent underlying construct
  α 0.50–0.69 → "questionable" — useful but noisy
  α < 0.50  → "poor" — items likely measuring different things

# Why Bessel correction (`corrected=true`)?

Julia's `var()` defaults to `corrected=true` (denominator n−1), matching the
standard sample variance.  Python's `numpy.var()` defaults to `ddof=0` (n).
We explicitly pass `corrected=true` to document the intent.

# Returns NaN if K < 2 or n_obs < 2 (not enough data for a meaningful alpha)
"""
function cronbach_alpha(X::Matrix{Float64})::Float64
    n_obs, K = size(X)    # Julia: size(M) returns (nrows, ncols)
    if K < 2 || n_obs < 2
        return NaN
    end
    # Item variances: list comprehension over column indices 1:K.
    # `X[:, j]` extracts column j as a Vector{Float64} (a copy).
    item_vars = [var(X[:, j]; corrected=true) for j in 1:K]

    # Total score variance: sum rows to get the composite, then take variance.
    # `vec(sum(X, dims=2))` → 1D vector of row sums.
    total_vars = var(vec(sum(X, dims=2)); corrected=true)

    # Guard against degenerate case (all items have zero variance).
    total_vars ≈ 0.0 && return NaN    # `≈` is `isapprox(a, b)`, ≈ means ≅ numerically

    return (K / (K - 1)) * (1.0 - sum(item_vars) / total_vars)
end


"""
    scale_to_output(v; out_min=1.0, out_max=10.0) -> Vector{Float64}

Min-max rescale `v` from its empirical [min, max] to [out_min, out_max].

# Why rescale to [1, 10]?

The construct sweep uses ordinal categories 1–5 or 1–10.  Rescaling ensures
that constructs built from differently-scaled items (e.g. 1–4 Likert vs. 1–7)
land on a common range before entering the ordered logit model.

# Degenerate case

If max ≈ min (all values identical), returns a constant vector at the midpoint
rather than dividing by zero.

# Broadcasting

`.+` and `.*` broadcast over vectors element-wise.
Python equivalent: `out_min + (out_max - out_min) * (v - lo) / (hi - lo)`
with numpy arrays.
"""
function scale_to_output(v::Vector{Float64}; out_min=1.0, out_max=10.0)::Vector{Float64}
    lo, hi = minimum(v), maximum(v)
    if hi - lo < 1e-10
        # All identical — return midpoint vector.
        # `fill(val, n)` creates a Vector{Float64} of length n filled with val.
        return fill((out_min + out_max) / 2.0, length(v))
    end
    # Broadcasting: `.+`, `.-`, `.*`, `./` apply element-wise.
    # Parentheses group operations as usual.
    return out_min .+ (out_max - out_min) .* (v .- lo) ./ (hi - lo)
end


"""
    reverse_code(v::Vector{Float64}) -> Vector{Float64}

Reverse-code ordinal items: new = max + min − original.

# Why reverse-code?

Some survey items are phrased so that higher scores indicate *less* of the
construct being measured (e.g. "I never trust anyone" on a trust scale).
Reverse-coding flips the scale so all items point in the same direction before
averaging.

# Formula

For an item with observed range [lo, hi]:
  reversed_i = hi + lo − original_i

This maps lo → hi and hi → lo, preserving the ordinal distances.
For a 1–5 scale: 1→5, 2→4, 3→3, 4→2, 5→1.

# Design choice

We compute min/max from the data rather than from the declared scale to handle
surveys where not all scale points are used.
"""
function reverse_code(v::Vector{Float64})::Vector{Float64}
    lo, hi = minimum(v), maximum(v)
    return hi .+ lo .- v    # broadcast: applies to every element
end


"""
    build_construct_scale(items; reverse_idx, out_min, out_max)
        -> (scores::Vector{Float64}, alpha::Float64)

Build a reflective composite scale from a K-item matrix (n_obs × K).

# Steps

1. **Reverse-code** columns listed in `reverse_idx` (1-indexed column numbers).
2. **Row means** across all items, NaN-aware (requires ≥ 1 valid item per row).
   A row where all items are NaN gets score NaN.
3. **Scale** to [out_min, out_max] (default [1, 10]).
4. **Compute α** on complete rows (all items present).

# Keyword arguments

`reverse_idx::Vector{Int}` — 1-indexed columns to reverse-code before averaging.
`out_min`, `out_max` — output range (default 1.0, 10.0).

# Returns

Tuple `(scores, alpha)`:
  - `scores` : Vector{Float64} of length n_obs (may contain NaN)
  - `alpha`  : Cronbach's α on complete rows (NaN if < 2 complete rows)

# NaN handling in Julia

Julia uses `NaN` (IEEE 754) for missing numeric values, similar to how Python
uses `np.nan`.  Key Julia idioms:
  - `isnan.(v)`  → Bool array, element-wise check
  - `.!isnan.(v)` → negated mask
  - `v[mask]`   → filtered vector (creates a copy)
  - `any(isnan.(row))` → true if any element is NaN
"""
function build_construct_scale(
    items::Matrix{Float64};
    reverse_idx::Vector{Int} = Int[],   # empty by default; Int[] is typed empty array
    out_min::Float64 = 1.0,
    out_max::Float64 = 10.0,
)::Tuple{Vector{Float64}, Float64}      # return type is a 2-tuple
    n_obs, K = size(items)
    work = copy(items)    # copy() so we don't mutate the caller's array (defensive)

    # Step 1: Reverse-code selected columns.
    # `reverse_idx` contains 1-based column indices to flip.
    for j in reverse_idx
        col   = work[:, j]
        valid = col[.!isnan.(col)]    # filter to non-NaN values
        if !isempty(valid)
            lo, hi = minimum(valid), maximum(valid)
            work[:, j] = hi .+ lo .- col    # flip in place (NaN stays NaN: hi+lo-NaN = NaN)
        end
    end

    # Step 2: NaN-aware row means.
    # Pre-allocate output vector; `undef` means "don't zero-initialize" (faster).
    scores = Vector{Float64}(undef, n_obs)
    for i in 1:n_obs
        row   = work[i, :]            # extract row i as a 1D vector
        valid = row[.!isnan.(row)]    # keep only non-NaN items
        scores[i] = isempty(valid) ? NaN : mean(valid)
    end

    # Step 3: Compute α on complete-case rows.
    # `vec(...)` collapses a 2D Bool matrix to 1D; `any(isnan, dims=2)` checks row-wise.
    complete = vec(.!any(isnan.(work), dims=2))   # Bool vector: true = no NaN in row
    alpha = sum(complete) >= 2 ? cronbach_alpha(work[complete, :]) : NaN

    # Step 4: Rescale to [out_min, out_max] on valid (non-NaN) scores only.
    valid_mask = .!isnan.(scores)
    if sum(valid_mask) > 0
        scaled = copy(scores)
        # `scores[valid_mask]` selects valid elements; result is a new Vector{Float64}.
        scaled[valid_mask] = scale_to_output(scores[valid_mask]; out_min=out_min, out_max=out_max)
        return scaled, alpha
    end
    return scores, alpha    # all NaN case
end
