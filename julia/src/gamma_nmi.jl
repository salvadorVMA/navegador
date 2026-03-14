"""
    gamma_nmi.jl — Goodman-Kruskal γ and Normalized Mutual Information

Ported from ses_regression.py: `goodman_kruskal_gamma()` and
`normalized_mutual_information()`.

Both functions operate on a K_a × K_b joint probability table (a Matrix{Float64}
whose entries sum to 1). No external packages are needed.
"""

"""
    goodman_kruskal_gamma(joint_table::Matrix{Float64}) -> Float64

Goodman-Kruskal γ from a joint probability table.

γ = (C - D) / (C + D)  where C = concordant pairs, D = discordant pairs.
γ ∈ [-1, 1]:  +1 = perfect positive ordinal association, 0 = independence.

Rows index categories of variable A (ordered low→high).
Cols index categories of variable B (ordered low→high).
"""
function goodman_kruskal_gamma(joint_table::Matrix{Float64})::Float64
    Ka, Kb = size(joint_table)
    concordant = 0.0
    discordant = 0.0
    for i in 1:Ka
        for j in 1:Kb
            p_ij = joint_table[i, j]
            # concordant: rows strictly below i, cols strictly right of j
            if i < Ka && j < Kb
                concordant += p_ij * sum(joint_table[i+1:end, j+1:end])
            end
            # discordant: rows strictly below i, cols strictly left of j
            if i < Ka && j > 1
                discordant += p_ij * sum(joint_table[i+1:end, 1:j-1])
            end
        end
    end
    denom = concordant + discordant
    return denom > 0.0 ? (concordant - discordant) / denom : 0.0
end


"""
    normalized_mutual_information(joint_table::Matrix{Float64}) -> Float64

Normalized Mutual Information from a joint probability table.

    MI  = Σ P(a,b) · log(P(a,b) / (P(a)·P(b)))
    NMI = MI / min(H(A), H(B))

NMI ∈ [0, 1].  Returns 0.0 when either marginal has zero entropy.
"""
function normalized_mutual_information(joint_table::Matrix{Float64})::Float64
    # Normalize to sum-1
    p = joint_table ./ sum(joint_table)

    p_a = vec(sum(p, dims=2))  # marginal of A  (Ka,)
    p_b = vec(sum(p, dims=1))  # marginal of B  (Kb,)

    # Entropies
    h_a = -sum(x -> x > 0 ? x * log(x) : 0.0, p_a)
    h_b = -sum(x -> x > 0 ? x * log(x) : 0.0, p_b)

    min_h = min(h_a, h_b)
    if min_h < 1e-12
        return 0.0
    end

    # Mutual information
    mi = 0.0
    for i in axes(p, 1)
        for j in axes(p, 2)
            if p[i, j] > 0 && p_a[i] > 0 && p_b[j] > 0
                mi += p[i, j] * log(p[i, j] / (p_a[i] * p_b[j]))
            end
        end
    end

    return max(0.0, mi) / min_h
end
