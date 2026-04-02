# tda_gromov_wasserstein.jl — Phase 6: Gromov-Wasserstein network alignment
#
# Computes Gromov-Wasserstein distances and transport plans for all 2145 country
# pairs (66 choose 2). GW alignment finds the optimal "soft correspondence"
# between nodes of two metric spaces, measuring how structurally similar they are.
#
# ── Mathematical background ──────────────────────────────────────────────────
#
# Gromov-Wasserstein distance (Mémoli, 2011):
#   Given two metric spaces (X, d_X) and (Y, d_Y), the GW distance measures
#   how well the internal distance structures can be matched:
#
#   GW(X,Y) = min_T Σ_{i,k,j,l} |d_X(i,k) - d_Y(j,l)|² · T_{ij} · T_{kl}
#
#   subject to: T·1 = p (marginal matches X distribution)
#               T'·1 = q (marginal matches Y distribution)
#               T ≥ 0
#
#   where T is the "transport plan" — a soft alignment matrix.
#   T[i,j] = how much of construct i in country 1 maps to construct j in country 2.
#
# Interpretation:
#   - GW distance ≈ 0: networks have identical distance structure (same shape)
#   - GW distance > 0: structural differences (constructs play different roles)
#   - Transport plan T: reveals which constructs correspond across countries.
#     If T[i,j] is large, construct i in country 1 occupies a similar
#     topological position to construct j in country 2.
#
# Entropic regularization (Peyré et al., 2016):
#   Adding -ε·H(T) to the objective makes the problem convex. Solved by
#   alternating Sinkhorn projections on a quadratic (not linear) cost.
#   Converges in O(max_iter × inner_iter × n²) operations.
#
# Why GW and not simpler measures?
#   - Spectral distance (Phase 3) compares global structure but loses node identity.
#   - GW preserves node correspondence: we can ask "what construct in Japan
#     plays the same role as 'personal_religiosity' in Mexico?"
#   - This is the "shape matching" step — like aligning two protein structures.
#
# References:
#   Mémoli (2011), "Gromov-Wasserstein distances and the metric approach to
#     object matching", Found. Comp. Math.
#   Peyré, Cuturi, Solomon (2016), "Gromov-Wasserstein Averaging of Kernel
#     and Distance Matrices", ICML.
#
# Input:
#   data/tda/matrices/manifest.json
#   data/tda/floyd_warshall/{COUNTRY}_shortest_paths.csv  (from Phase 1)
#
# Output:
#   data/tda/alignment/gw_distance_matrix.csv      — 66×66 GW distances
#   data/tda/alignment/gw_transport_top50.json      — transport plans for top-50 pairs
#   data/tda/alignment/gw_alignment_summary.json    — per-pair best-match constructs
#
# Run:
#   julia -t 8 --project=. scripts/tda_gromov_wasserstein.jl

using JSON
using CSV
using DataFrames
using Printf
using Dates
using LinearAlgebra
using Statistics: mean, median
using Base.Threads

# ── Path setup ────────────────────────────────────────────────────────────────
const JULIA_DIR    = dirname(dirname(@__FILE__))
const ROOT         = dirname(JULIA_DIR)
const NAV_ROOT     = joinpath(dirname(ROOT), "navegador")
const MANIFEST     = length(ARGS) >= 1 ? ARGS[1] : joinpath(NAV_ROOT, "data", "tda", "matrices", "manifest.json")
const FW_DIR       = length(ARGS) >= 2 ? ARGS[2] : joinpath(NAV_ROOT, "data", "tda", "floyd_warshall")
const OUTPUT_DIR   = length(ARGS) >= 3 ? ARGS[3] : joinpath(NAV_ROOT, "data", "tda", "alignment")

# ── GW parameters ─────────────────────────────────────────────────────────────
# Regularization strength. Smaller ε → sharper transport plans but slower convergence.
# For n=55, ε=0.01 gives good results in ~50 outer iterations.
const GW_EPS       = 0.01
const GW_MAXITER   = 100   # outer iterations (GW cost recomputation)
const GW_INNER     = 50    # inner Sinkhorn iterations per outer step
const GW_TOL       = 1e-5  # convergence tolerance on GW loss

# How many most-interesting transport plans to save in full (top-50 by GW distance)
const N_SAVE_PLANS = 50

# Minimum shared constructs for a reliable comparison
const MIN_SHARED   = 40


# ── Entropic Gromov-Wasserstein ───────────────────────────────────────────────

"""
    entropic_gw(D1, D2; eps, max_iter, inner_iter, tol) → (gw_dist, T)

Compute the entropic Gromov-Wasserstein distance between two metric spaces
represented by their distance matrices D1 (n₁×n₁) and D2 (n₂×n₂).

Returns (gw_distance, transport_plan_T).

Algorithm:
  1. Initialize T = p * q' (uniform coupling)
  2. Repeat:
     a. Compute quadratic GW cost: M[i,j] = Σ_{k,l} (D1[i,k] - D2[j,l])² T[k,l]
        Efficient form: M = D1² T 1·1' + 1·1' T D2² - 2 D1 T D2'
     b. Sinkhorn step on exp(-M/ε) → new T
  3. GW distance = ⟨M, T⟩

Python equivalent: ot.gromov_wasserstein(D1, D2, p, q, 'square_loss', epsilon=eps)
"""
function entropic_gw(
    D1::Matrix{Float64},
    D2::Matrix{Float64};
    eps::Float64 = GW_EPS,
    max_iter::Int = GW_MAXITER,
    inner_iter::Int = GW_INNER,
    tol::Float64 = GW_TOL,
)::Tuple{Float64, Matrix{Float64}}
    n1 = size(D1, 1)
    n2 = size(D2, 1)

    # Uniform marginals
    p = fill(1.0 / n1, n1)
    q = fill(1.0 / n2, n2)

    # Initialize transport plan (product coupling)
    T = p * q'

    # Precompute D² matrices
    D1sq = D1 .^ 2
    D2sq = D2 .^ 2
    ones_n1 = ones(n1)
    ones_n2 = ones(n2)

    prev_loss = Inf

    for outer in 1:max_iter
        # ── GW cost matrix ────────────────────────────────────────────────
        # M[i,j] = Σ_{k,l} (D1[i,k] - D2[j,l])² T[k,l]
        #        = Σ_k D1[i,k]² Σ_l T[k,l]  +  Σ_l D2[j,l]² Σ_k T[k,l]  -  2 Σ_{k,l} D1[i,k] D2[j,l] T[k,l]
        #        = (D1² · T · 1) · 1'  +  1 · (1' · T · D2²)'  -  2 · D1 · T · D2'
        #
        # This is the efficient O(n²·n) form instead of naive O(n⁴).
        A = D1sq * T * ones_n2          # n1-vector: row margins of D1²-weighted T
        B = D2sq' * T' * ones_n1        # n2-vector: column margins of D2²-weighted T
        M = A * ones_n2' .+ ones_n1 * B' .- 2.0 .* (D1 * T * D2')

        # ── Sinkhorn step ─────────────────────────────────────────────────
        K = exp.(.-M ./ eps)
        u = ones(n1)
        v = ones(n2)
        for _ in 1:inner_iter
            u = p ./ (K * v .+ 1e-12)
            v = q ./ (K' * u .+ 1e-12)
        end
        T = (u .* K) .* v'

        # ── Convergence check ─────────────────────────────────────────────
        loss = sum(M .* T)
        if abs(prev_loss - loss) < tol
            break
        end
        prev_loss = loss
    end

    # Final GW distance
    A = D1sq * T * ones(n2)
    B = D2sq' * T' * ones(n1)
    M_final = A * ones(n2)' .+ ones(n1) * B' .- 2.0 .* (D1 * T * D2')
    gw_dist = max(sum(M_final .* T), 0.0)

    return gw_dist, T
end


"""
    read_csv_matrix(path) → (Matrix{Float64}, Vector{String})
"""
function read_csv_matrix(path::String)
    df = CSV.read(path, DataFrame)
    constructs = string.(df[!, 1])
    mat = Matrix{Float64}(coalesce.(Matrix(df[!, 2:end]), 9999.0))
    return mat, constructs
end


"""
    shared_submatrix(D1, c1, D2, c2) → (D1_sub, D2_sub, shared, idx1, idx2)

Restrict two distance matrices to their shared construct set.
"""
function shared_submatrix(
    D1::Matrix{Float64}, c1::Vector{String},
    D2::Matrix{Float64}, c2::Vector{String}
)
    shared = sort(collect(intersect(Set(c1), Set(c2))))
    idx1 = [findfirst(==(s), c1) for s in shared]
    idx2 = [findfirst(==(s), c2) for s in shared]
    return D1[idx1, idx1], D2[idx2, idx2], shared, idx1, idx2
end


# ── Main ─────────────────────────────────────────────────────────────────────

function main()
    mkpath(OUTPUT_DIR)

    println("=" ^ 60)
    println("TDA Phase 6 — Gromov-Wasserstein Network Alignment")
    println("=" ^ 60)
    println("Start: $(now())")
    println("Threads: $(Threads.nthreads())")
    @printf("GW params: ε=%.3f, max_iter=%d, inner=%d\n", GW_EPS, GW_MAXITER, GW_INNER)

    manifest = JSON.parsefile(MANIFEST)
    countries = manifest["countries"]
    constructs_all = manifest["construct_index"]
    nc = length(countries)
    n_pairs = nc * (nc - 1) ÷ 2
    println("Countries: $nc → $n_pairs pairwise GW computations")

    # ── Load shortest-path distance matrices from Phase 1 ────────────────
    println("\n[1/3] Loading shortest-path distance matrices...")
    sp_matrices = Dict{String, Tuple{Matrix{Float64}, Vector{String}}}()
    for alpha3 in countries
        sp_path = joinpath(FW_DIR, "$(alpha3)_shortest_paths.csv")
        if !isfile(sp_path)
            println("  WARNING: $sp_path not found, skipping $alpha3")
            continue
        end
        D, cons = read_csv_matrix(sp_path)
        sp_matrices[alpha3] = (D, cons)
    end
    println("  Loaded $(length(sp_matrices)) matrices")

    # ── Build pair list ──────────────────────────────────────────────────
    available = sort(collect(keys(sp_matrices)))
    na = length(available)
    pairs = [(i, j) for i in 1:na for j in (i+1):na]
    println("  $(length(pairs)) pairs to compute")

    # ── Compute all GW distances ─────────────────────────────────────────
    println("\n[2/3] Computing GW distances (this may take ~20 min)...")
    GW_dists = fill(NaN, na, na)
    n_shared_arr = zeros(Int, length(pairs))

    # Thread-safe storage for transport plans and alignment summaries
    results_lock = ReentrantLock()
    pair_results = Vector{Dict{String, Any}}(undef, length(pairs))
    completed = Threads.Atomic{Int}(0)

    t0 = time()

    @threads for pidx in 1:length(pairs)
        i, j = pairs[pidx]
        c1, c2 = available[i], available[j]

        D1, cons1 = sp_matrices[c1]
        D2, cons2 = sp_matrices[c2]

        # Restrict to shared constructs
        D1_sub, D2_sub, shared, _, _ = shared_submatrix(D1, cons1, D2, cons2)
        n_shared = length(shared)
        n_shared_arr[pidx] = n_shared

        result = Dict{String, Any}(
            "country1" => c1, "country2" => c2, "n_shared" => n_shared,
        )

        if n_shared < MIN_SHARED
            result["gw_dist"] = NaN
            result["status"] = "skipped_low_overlap"
            pair_results[pidx] = result
            Threads.atomic_add!(completed, 1)
            continue
        end

        # Normalize distances to [0, 1] for numerical stability
        max1 = maximum(D1_sub[D1_sub .< 9000.0]; init=1.0)
        max2 = maximum(D2_sub[D2_sub .< 9000.0]; init=1.0)
        D1_norm = D1_sub ./ max(max1, 1e-9)
        D2_norm = D2_sub ./ max(max2, 1e-9)
        # Cap sentinel values at 1.0
        D1_norm = min.(D1_norm, 1.0)
        D2_norm = min.(D2_norm, 1.0)

        gw_dist, T = entropic_gw(D1_norm, D2_norm)

        GW_dists[i, j] = gw_dist
        GW_dists[j, i] = gw_dist

        # Best-match constructs (argmax of each row of T)
        best_matches = Dict{String, Any}()
        for k in 1:n_shared
            best_j = argmax(T[k, :])
            best_matches[shared[k]] = Dict(
                "matched_to" => shared[best_j],
                "transport_mass" => round(T[k, best_j], digits=4),
                "is_self_match" => (k == best_j),
            )
        end

        result["gw_dist"] = round(gw_dist, digits=6)
        result["status"] = "done"
        result["n_self_matches"] = count(k -> argmax(T[k, :]) == k, 1:n_shared)
        result["frac_self_match"] = round(
            result["n_self_matches"] / n_shared, digits=3
        )
        result["best_matches"] = best_matches
        # Store transport plan for potential saving
        result["_transport"] = T
        result["_shared"] = shared

        pair_results[pidx] = result

        done = Threads.atomic_add!(completed, 1) + 1
        if done % 100 == 0 || done == length(pairs)
            lock(results_lock) do
                @printf("  [%d/%d] (%.0f%%) elapsed: %.0fs\n",
                        done, length(pairs), 100 * done / length(pairs), time() - t0)
            end
        end
    end

    elapsed = time() - t0
    @printf("\n  All pairs done in %.1f seconds (%.1f min)\n", elapsed, elapsed / 60)

    # ── Save outputs ─────────────────────────────────────────────────────
    println("\n[3/3] Saving outputs...")

    # 1. GW distance matrix (full 66×66, using original country order)
    # Map available → original country indices
    GW_full = fill(NaN, nc, nc)
    for pidx in 1:length(pairs)
        i, j = pairs[pidx]
        c1_idx = findfirst(==(available[i]), countries)
        c2_idx = findfirst(==(available[j]), countries)
        if c1_idx !== nothing && c2_idx !== nothing
            GW_full[c1_idx, c2_idx] = GW_dists[i, j]
            GW_full[c2_idx, c1_idx] = GW_dists[i, j]
        end
    end
    for i in 1:nc
        GW_full[i, i] = 0.0
    end

    gw_df = DataFrame(GW_full, Symbol.(countries))
    insertcols!(gw_df, 1, :country => countries)
    CSV.write(joinpath(OUTPUT_DIR, "gw_distance_matrix.csv"), gw_df)

    # 2. Alignment summary (all pairs, without transport matrices)
    summary_list = []
    for pidx in 1:length(pairs)
        r = pair_results[pidx]
        push!(summary_list, Dict(
            "country1" => r["country1"],
            "country2" => r["country2"],
            "n_shared" => r["n_shared"],
            "gw_dist" => get(r, "gw_dist", NaN),
            "status" => get(r, "status", "unknown"),
            "n_self_matches" => get(r, "n_self_matches", 0),
            "frac_self_match" => get(r, "frac_self_match", 0.0),
        ))
    end
    open(joinpath(OUTPUT_DIR, "gw_alignment_summary.json"), "w") do f
        JSON.print(f, summary_list, 2)
    end

    # 3. Full transport plans for top-N most interesting pairs
    # "Most interesting" = completed pairs sorted by lowest GW distance (most similar)
    # plus highest GW distance (most different)
    completed_results = [
        (pidx, pair_results[pidx])
        for pidx in 1:length(pairs)
        if get(pair_results[pidx], "status", "") == "done"
    ]
    sort!(completed_results, by = x -> x[2]["gw_dist"])

    # Take N_SAVE_PLANS/2 most similar + N_SAVE_PLANS/2 most different
    n_half = min(N_SAVE_PLANS ÷ 2, length(completed_results) ÷ 2)
    selected = vcat(
        completed_results[1:n_half],           # most similar
        completed_results[end-n_half+1:end],   # most different
    )

    transport_plans = []
    for (pidx, r) in selected
        T = r["_transport"]
        shared = r["_shared"]
        plan = Dict(
            "country1" => r["country1"],
            "country2" => r["country2"],
            "gw_dist" => r["gw_dist"],
            "n_shared" => r["n_shared"],
            "constructs" => shared,
            "transport" => [[round(T[i, j], digits=4) for j in 1:size(T, 2)] for i in 1:size(T, 1)],
            "best_matches" => r["best_matches"],
        )
        push!(transport_plans, plan)
    end
    open(joinpath(OUTPUT_DIR, "gw_transport_top$(N_SAVE_PLANS).json"), "w") do f
        JSON.print(f, transport_plans, 2)
    end

    # ── Summary stats ────────────────────────────────────────────────────
    valid_dists = filter(!isnan, [GW_dists[i, j] for i in 1:na for j in (i+1):na])
    println("\n" * "─" ^ 60)
    @printf("  Pairs computed: %d / %d\n", length(valid_dists), length(pairs))
    if !isempty(valid_dists)
        @printf("  GW distance range: [%.6f, %.6f]\n", minimum(valid_dists), maximum(valid_dists))
        @printf("  Mean GW distance: %.6f\n", mean(valid_dists))
        @printf("  Median GW distance: %.6f\n", median(valid_dists))

        # Self-match rate (how often construct i maps to itself across countries)
        self_match_rates = [r["frac_self_match"] for (_, r) in completed_results]
        @printf("  Mean self-match rate: %.1f%%\n", 100 * mean(self_match_rates))
    end
    @printf("  Time: %.1f seconds (%.1f min)\n", elapsed, elapsed / 60)
    println("  Output: $OUTPUT_DIR")
    println("Done.")
end

main()
