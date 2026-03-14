# gamma_nmi.jl — Goodman-Kruskal γ and Normalized Mutual Information
#
# Ported from ses_regression.py: `goodman_kruskal_gamma()` and
# `normalized_mutual_information()`.
#
# Both functions operate on a K_a × K_b joint probability table (a Matrix{Float64}
# whose entries sum to 1.0).  No external packages are needed — only Base Julia.
#
# ── Why a joint probability table? ───────────────────────────────────────────
# In the DR bridge, we don't observe both variables on the same respondents.
# Instead, we *simulate* the joint distribution by:
#   1. Sampling a shared SES reference population X_ref (n_sim rows)
#   2. Computing P(Y_a = k | X_i) and P(Y_b = l | X_i) for each reference row
#   3. Averaging the outer products: joint[k,l] = mean_i P_a(k|X_i)·P_b(l|X_i)
# The result is a K_a × K_b matrix of probabilities summing to 1.  Passing this
# to the two functions below gives γ and NMI without any further model fitting.


"""
    goodman_kruskal_gamma(joint_table::Matrix{Float64}) -> Float64

Compute Goodman-Kruskal γ from a joint probability table.

# Statistical interpretation

γ = (C − D) / (C + D)   where:
  C = sum of concordant probability mass  (pairs ordered the same on both vars)
  D = sum of discordant probability mass  (pairs ordered oppositely)

γ ∈ [−1, +1]:
  +1 = perfectly concordant ordinal association (monotone increasing)
   0 = no ordinal tendency (pairs equally concordant and discordant)
  −1 = perfectly discordant (monotone decreasing)

Unlike Pearson's r, γ only requires the variables to be *ordinal*, not
interval-scaled.  It ignores tied pairs (i = i' or j = j'), which is why
high-concentration distributions (many ties) can have γ ≈ 0 even with visible
trends.

# Computation

For a K_a × K_b table P[i, j]:

  C = Σ_{i,j} P[i,j] · Σ_{i'>i, j'>j} P[i', j']
  D = Σ_{i,j} P[i,j] · Σ_{i'>i, j'<j} P[i', j']

The inner sums are computed with `sum(joint_table[i+1:end, j+1:end])` etc.
Julia's slicing syntax `a:b` creates a range; `end` refers to the last index.

# Design choice: rows index A, cols index B

Rows are categories of variable A ordered low→high.
Cols are categories of variable B ordered low→high.
If the sign matters for your application, ensure consistent row/col orientation.

# Returns 0.0 if C+D = 0 (degenerate table or all ties)
"""
function goodman_kruskal_gamma(joint_table::Matrix{Float64})::Float64
    Ka, Kb = size(joint_table)   # Julia: size() returns a Tuple, not a shape object
    concordant = 0.0
    discordant = 0.0

    for i in 1:Ka          # Julia loops are 1-indexed
        for j in 1:Kb
            p_ij = joint_table[i, j]

            # Concordant mass: everything strictly below-right (higher on both axes).
            # `i+1:end` is a UnitRange from i+1 to Ka; slice creates no copy here
            # because we immediately pass it to sum().
            if i < Ka && j < Kb
                concordant += p_ij * sum(joint_table[i+1:end, j+1:end])
            end

            # Discordant mass: everything strictly below-left (lower on B, higher on A).
            if i < Ka && j > 1
                discordant += p_ij * sum(joint_table[i+1:end, 1:j-1])
            end
        end
    end

    denom = concordant + discordant
    # Ternary expression:  condition ? value_if_true : value_if_false
    # Same as Python's:    value_if_true if condition else value_if_false
    return denom > 0.0 ? (concordant - discordant) / denom : 0.0
end


"""
    normalized_mutual_information(joint_table::Matrix{Float64}) -> Float64

Normalized Mutual Information (NMI) from a joint probability table.

# Statistical interpretation

    MI  = Σ_{i,j} P(a_i, b_j) · log[ P(a_i, b_j) / (P(a_i)·P(b_j)) ]
    NMI = MI / min(H(A), H(B))

NMI ∈ [0, 1]:
  0 = statistical independence (joint = product of marginals)
  1 = one variable fully determines the other

Unlike γ, NMI detects *any* form of statistical dependence — monotonic,
U-shaped, crossover, or complex.  In the DR sweep, we use γ as the primary
estimate and NMI as a diagnostic:
  |γ| ≈ 0 AND NMI >> 0  →  non-monotonic SES structure (flagged with "NM!")
  |γ| ≈ 0 AND NMI ≈ 0   →  genuinely SES-independent pair

The v3 and v4 sweeps found NMI universally low (max 0.037), confirming that
SES-mediated structure — where it exists — is predominantly monotonic.

# Implementation notes

`vec(sum(p, dims=2))` collapses a 2D matrix along axis 2 (sum over columns),
then `vec` converts the Kx1 result to a 1D vector.
Python equivalent: `p.sum(axis=1)` returns a 1D array.

`sum(x -> x > 0 ? x * log(x) : 0.0, p_a)` maps a lambda over p_a and sums.
Python equivalent: `(-np.where(p_a > 0, p_a * np.log(p_a), 0)).sum()`.

# Returns 0.0 when either variable is constant (entropy = 0)
"""
function normalized_mutual_information(joint_table::Matrix{Float64})::Float64
    # Normalize to a proper probability table (sum = 1).
    # The `./ ` dot-operator broadcasts division element-wise over the matrix.
    # Python analogue: p = joint_table / joint_table.sum()
    p = joint_table ./ sum(joint_table)

    # Marginal distributions by summing over the opposite axis.
    # dims=2 means "sum across columns for each row" → vector of row probabilities.
    # dims=1 means "sum across rows for each column" → vector of column probabilities.
    p_a = vec(sum(p, dims=2))  # marginal of A  (Ka,)
    p_b = vec(sum(p, dims=1))  # marginal of B  (Kb,)

    # Shannon entropies H(A) and H(B).
    # `x -> expr` is an anonymous function (lambda).  Applied element-wise via sum.
    # We handle x == 0 with the conditional to avoid -Inf from log(0).
    h_a = -sum(x -> x > 0 ? x * log(x) : 0.0, p_a)
    h_b = -sum(x -> x > 0 ? x * log(x) : 0.0, p_b)

    min_h = min(h_a, h_b)
    if min_h < 1e-12
        # One variable is constant → zero entropy → NMI undefined, return 0.
        return 0.0
    end

    # Mutual information: sum over all (i, j) cells.
    # `axes(p, 1)` returns the valid index range for dimension 1 (= 1:Ka).
    # This is preferred over `1:size(p,1)` because it works for any array type.
    mi = 0.0
    for i in axes(p, 1)
        for j in axes(p, 2)
            # Only sum cells with positive probability; 0·log(0) = 0 by convention.
            if p[i, j] > 0 && p_a[i] > 0 && p_b[j] > 0
                mi += p[i, j] * log(p[i, j] / (p_a[i] * p_b[j]))
            end
        end
    end

    # Clamp to ≥0: floating-point rounding can produce tiny negatives.
    return max(0.0, mi) / min_h
end
