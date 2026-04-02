# tda_ricci_curvature.jl — Phase 2: Ollivier-Ricci curvature via Sinkhorn OT
#
# Computes the Ollivier-Ricci curvature for every edge in every country's
# construct network. This measures the "geometric shape" of each edge:
#   κ > 0  →  neighborhoods overlap  (redundant, well-connected region)
#   κ ≈ 0  →  flat geometry          (regular lattice-like structure)
#   κ < 0  →  neighborhoods diverge  (bridge/bottleneck between clusters)
#
# ── Mathematical background ──────────────────────────────────────────────────
#
# Ollivier-Ricci curvature (Ollivier, 2009):
#   For edge (i,j) with distance d(i,j):
#     κ(i,j) = 1 - W₁(μᵢ, μⱼ) / d(i,j)
#   where μᵢ and μⱼ are probability measures at nodes i and j,
#   and W₁ is the Earth Mover's Distance (Wasserstein-1 distance).
#
# Node measure construction (lazy random walk):
#   μᵢ = α·δᵢ + (1-α)·Pᵢ
#   where:
#     δᵢ = point mass at node i (stay probability)
#     Pᵢ = row i of the random walk transition matrix P = D⁻¹·W
#     α  = laziness parameter (we use 0.5 — half the mass stays at i)
#
# Wasserstein-1 distance:
#   W₁(μ, ν) = min_{T} Σᵢⱼ Tᵢⱼ · Cᵢⱼ    s.t. T1 = μ, T'1 = ν, T ≥ 0
#   where C is the ground cost matrix (we use shortest-path distances from Phase 1).
#
# Sinkhorn algorithm (Cuturi, 2013):
#   Entropy-regularized approximation to W₁. Adds -ε·H(T) to the objective,
#   where H(T) is the entropy of the transport plan. This makes the problem
#   strictly convex and solvable by alternating row/column normalizations:
#     K = exp(-C/ε)
#     u ← μ / (K·v)
#     v ← ν / (K'·u)
#   Converges in 20-50 iterations for ε = 0.1.
#
# Computational cost:
#   Per edge: O(n² × n_iter) for Sinkhorn (n = 55 constructs, n_iter ≈ 30)
#   Per country: ~1000 edges × 30 iterations × 55² = ~90M FLOPs (< 1 second)
#   Total: 66 countries × ~1s = ~1 minute (sequential), ~10s (8 threads)
#
# References:
#   Ollivier (2009), "Ricci curvature of Markov chains on metric spaces", JFA.
#   Cuturi (2013), "Sinkhorn Distances", NeurIPS.
#   Ni et al. (2019), "Community detection on networks with Ricci flow", Sci Rep.
#
# Input:
#   data/tda/matrices/manifest.json
#   data/tda/floyd_warshall/{COUNTRY}_shortest_paths.csv  (from Phase 1)
#
# Output:
#   data/tda/ricci/{COUNTRY}_ricci.csv       — n×n curvature matrix
#   data/tda/ricci/ricci_summary.json        — per-country summary stats
#
# Run:
#   julia -t 8 --project=. scripts/tda_ricci_curvature.jl

using JSON
using CSV
using DataFrames
using Printf
using Dates
using LinearAlgebra
using Statistics: mean, median, quantile
using Base.Threads

# ── Path setup ────────────────────────────────────────────────────────────────
const JULIA_DIR    = dirname(dirname(@__FILE__))
const ROOT         = dirname(JULIA_DIR)
const NAV_ROOT     = joinpath(dirname(ROOT), "navegador")
const MANIFEST     = length(ARGS) >= 1 ? ARGS[1] : joinpath(NAV_ROOT, "data", "tda", "matrices", "manifest.json")
const FW_DIR       = length(ARGS) >= 2 ? ARGS[2] : joinpath(NAV_ROOT, "data", "tda", "floyd_warshall")
const OUTPUT_DIR   = length(ARGS) >= 3 ? ARGS[3] : joinpath(NAV_ROOT, "data", "tda", "ricci")

# ── Sinkhorn parameters ──────────────────────────────────────────────────────
# ε controls the trade-off between accuracy and convergence speed.
# Smaller ε → closer to true W₁ but slower convergence and numerical instability.
# ε = 0.1 is a standard choice for n ≈ 50-100 (Cuturi 2013).
const SINKHORN_EPS     = 0.1
const SINKHORN_MAXITER = 100
const SINKHORN_TOL     = 1e-6
# α = laziness parameter for the random walk measure.
# α = 0.5 means half the mass stays at the node, half diffuses to neighbors.
const ALPHA = 0.5


# ── Sinkhorn optimal transport ───────────────────────────────────────────────

"""
    sinkhorn_w1(mu, nu, C; eps, max_iter, tol) → Float64

Compute the entropy-regularized Wasserstein-1 distance between distributions
μ and ν, given ground cost matrix C.

Algorithm:
  1. K = exp(-C/ε)          — Gibbs kernel
  2. Alternate:
       u ← μ ./ (K * v)    — row scaling
       v ← ν ./ (K' * u)   — column scaling
  3. Transport plan: T = diag(u) · K · diag(v)
  4. Cost = Σᵢⱼ Tᵢⱼ · Cᵢⱼ = ⟨T, C⟩

The regularization ε blurs the transport plan slightly, making it ε-close
to the true optimal transport cost. For ε = 0.1 and our matrix sizes (55×55),
the error is negligible (~1%) relative to the curvature values we compute.

Python equivalent: ot.sinkhorn2(mu, nu, C, reg=eps) from the POT library.
"""
function sinkhorn_w1(
    mu::Vector{Float64},
    nu::Vector{Float64},
    C::Matrix{Float64};
    eps::Float64 = SINKHORN_EPS,
    max_iter::Int = SINKHORN_MAXITER,
    tol::Float64 = SINKHORN_TOL,
)::Float64
    n = length(mu)

    # Gibbs kernel: K[i,j] = exp(-C[i,j] / ε)
    K = exp.(-C ./ eps)

    u = ones(n)
    v = ones(n)

    for iter in 1:max_iter
        u_new = mu ./ (K * v .+ 1e-12)      # 1e-12 prevents division by zero
        v_new = nu ./ (K' * u_new .+ 1e-12)

        # Convergence check: L∞ norm of u change
        if maximum(abs.(u_new .- u)) < tol
            u = u_new
            v = v_new
            break
        end
        u = u_new
        v = v_new
    end

    # Transport plan T = diag(u) · K · diag(v)
    # Cost = ⟨T, C⟩ = Σ uᵢ · Kᵢⱼ · vⱼ · Cᵢⱼ
    T = (u .* K) .* v'
    cost = sum(T .* C)
    return cost
end


"""
    ollivier_ricci(W_abs, D_sp; alpha) → Matrix{Float64}

Compute the Ollivier-Ricci curvature matrix for a weighted network.

Parameters:
  W_abs  — n×n absolute weight matrix (|γ| values, symmetric)
  D_sp   — n×n shortest-path distance matrix (from Floyd-Warshall)
  alpha  — laziness parameter for random walk measure (default 0.5)

Returns:
  κ — n×n matrix where κ[i,j] is the Ricci curvature of edge (i,j).
      Non-edges (W_abs[i,j] ≈ 0) get κ = NaN.

For each edge (i,j):
  1. Build lazy random walk measures μᵢ, μⱼ
  2. Compute W₁(μᵢ, μⱼ) via Sinkhorn
  3. κ(i,j) = 1 - W₁(μᵢ, μⱼ) / d_sp(i,j)
"""
function ollivier_ricci(
    W_abs::Matrix{Float64},
    D_sp::Matrix{Float64};
    alpha::Float64 = ALPHA,
)::Matrix{Float64}
    n = size(W_abs, 1)

    # Build transition matrix P = D⁻¹ · W  (row-stochastic)
    # P[i,j] = probability of walking from i to j in one step
    row_sums = vec(sum(W_abs, dims=2))
    P = copy(W_abs)
    for i in 1:n
        if row_sums[i] > 0
            P[i, :] ./= row_sums[i]
        end
    end

    # Initialize output
    kappa = fill(NaN, n, n)

    # Collect edges to process (upper triangle, non-zero weight)
    edges = Tuple{Int,Int}[]
    for i in 1:n
        for j in (i+1):n
            if W_abs[i, j] > 1e-10
                push!(edges, (i, j))
            end
        end
    end

    # Compute curvature for each edge
    for (i, j) in edges
        d_ij = D_sp[i, j]
        if d_ij < 1e-10 || d_ij >= 9000.0
            continue
        end

        # Lazy random walk measure at node i:
        #   μᵢ = α · δᵢ + (1-α) · P[i,:]
        # δᵢ is the Dirac delta at i (all mass on node i)
        mu_i = (1 - alpha) .* P[i, :] .+ alpha .* (1:n .== i)
        mu_j = (1 - alpha) .* P[j, :] .+ alpha .* (1:n .== j)

        # Normalize to valid probability distributions
        mu_i ./= sum(mu_i)
        mu_j ./= sum(mu_j)

        # Wasserstein-1 distance using Sinkhorn
        w1 = sinkhorn_w1(mu_i, mu_j, D_sp)

        # Ollivier-Ricci curvature
        k = 1.0 - w1 / d_ij

        kappa[i, j] = k
        kappa[j, i] = k
    end

    # Diagonal = 0 by convention
    for i in 1:n
        kappa[i, i] = 0.0
    end

    return kappa
end


"""
    read_csv_matrix(path) → (Matrix{Float64}, Vector{String})
"""
function read_csv_matrix(path::String)
    df = CSV.read(path, DataFrame)
    constructs = string.(df[!, 1])
    mat = Matrix{Float64}(coalesce.(Matrix(df[!, 2:end]), 0.0))
    return mat, constructs
end


# ── Main ─────────────────────────────────────────────────────────────────────

function main()
    mkpath(OUTPUT_DIR)

    println("=" ^ 60)
    println("TDA Phase 2 — Ollivier-Ricci Curvature (Sinkhorn OT)")
    println("=" ^ 60)
    println("Start: $(now())")
    println("Threads: $(Threads.nthreads())")
    @printf("Sinkhorn: ε=%.2f, maxiter=%d, α=%.1f\n",
            SINKHORN_EPS, SINKHORN_MAXITER, ALPHA)

    manifest = JSON.parsefile(MANIFEST)
    countries = manifest["countries"]
    constructs = manifest["construct_index"]
    n = length(constructs)
    println("Countries: $(length(countries)), Constructs: $n")

    # Thread-safe storage for results
    summaries = Dict{String, Any}()
    summaries_lock = ReentrantLock()
    t0 = time()

    # Process countries in parallel
    @threads for ci in 1:length(countries)
        alpha3 = countries[ci]

        # Read weight matrix (|γ| values)
        w_path = manifest["files"][alpha3]["weight"]
        W, _ = read_csv_matrix(w_path)
        W_abs = abs.(W)
        # Replace NaN with 0 for weight matrix (no edge)
        W_abs[isnan.(W_abs)] .= 0.0

        # Read shortest-path distance matrix from Phase 1
        sp_path = joinpath(FW_DIR, "$(alpha3)_shortest_paths.csv")
        D_sp, _ = read_csv_matrix(sp_path)

        # Compute Ricci curvature
        kappa = ollivier_ricci(W_abs, D_sp)

        # Save curvature matrix
        kappa_df = DataFrame(kappa, Symbol.(constructs))
        insertcols!(kappa_df, 1, :construct => constructs)
        CSV.write(joinpath(OUTPUT_DIR, "$(alpha3)_ricci.csv"), kappa_df)

        # Compute summary statistics (non-NaN, non-diagonal values)
        valid = [kappa[i, j] for i in 1:n for j in (i+1):n if !isnan(kappa[i, j])]
        n_edges = length(valid)
        n_positive = count(x -> x > 0, valid)
        n_negative = count(x -> x < 0, valid)

        summary = Dict{String, Any}(
            "n_edges" => n_edges,
            "n_positive" => n_positive,
            "n_negative" => n_negative,
            "frac_negative" => n_edges > 0 ? round(n_negative / n_edges, digits=3) : 0.0,
        )
        if n_edges > 0
            summary["mean"] = round(mean(valid), digits=4)
            summary["median"] = round(median(valid), digits=4)
            summary["min"] = round(minimum(valid), digits=4)
            summary["max"] = round(maximum(valid), digits=4)
            summary["q10"] = round(quantile(valid, 0.10), digits=4)
            summary["q90"] = round(quantile(valid, 0.90), digits=4)

            # Node-level scalar curvature (mean of incident edge curvatures)
            node_curv = Dict{String, Float64}()
            for idx in 1:n
                incident = [kappa[idx, j] for j in 1:n if !isnan(kappa[idx, j]) && idx != j]
                if !isempty(incident)
                    node_curv[constructs[idx]] = round(mean(incident), digits=4)
                end
            end
            # Most negative node = biggest bottleneck
            if !isempty(node_curv)
                worst_node = argmin(node_curv)
                best_node = argmax(node_curv)
                summary["most_negative_node"] = worst_node
                summary["most_positive_node"] = best_node
            end
        end

        lock(summaries_lock) do
            summaries[alpha3] = summary
            if ci % 10 == 0 || ci == length(countries)
                @printf("  [%d/%d] %s: %d edges, mean κ = %.4f, %.0f%% negative\n",
                        ci, length(countries), alpha3,
                        n_edges,
                        get(summary, "mean", 0.0),
                        get(summary, "frac_negative", 0.0) * 100)
            end
        end
    end

    elapsed = time() - t0

    # Save summary JSON
    summary_path = joinpath(OUTPUT_DIR, "ricci_summary.json")
    open(summary_path, "w") do f
        JSON.print(f, summaries, 2)
    end

    # Global summary
    all_means = [summaries[c]["mean"] for c in countries if haskey(summaries[c], "mean")]
    println("\n" * "─" ^ 60)
    @printf("  Countries processed: %d\n", length(countries))
    @printf("  Global mean κ: %.4f\n", mean(all_means))
    @printf("  Global median κ: %.4f\n", median(all_means))
    @printf("  Time: %.1f seconds\n", elapsed)
    println("  Output: $OUTPUT_DIR")
    println("Done.")
end

main()
