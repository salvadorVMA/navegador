# tda_floyd_warshall.jl — Phase 1: All-pairs shortest paths + mediator scores
#
# For each country's distance matrix (from Phase 0), computes:
#   1. Floyd-Warshall all-pairs shortest paths (APSP)
#   2. Triangle violation matrix (how much the raw distance exceeds the SP distance)
#   3. Mediator scores (which constructs serve as routing hubs)
#
# ── Mathematical background ──────────────────────────────────────────────────
#
# Floyd-Warshall: Dynamic programming algorithm for APSP on weighted graphs.
#   D_sp[i,j] = min over all paths from i to j of (sum of edge weights).
#   Recurrence: D[i,j] = min(D[i,j], D[i,k] + D[k,j]) for each intermediate k.
#   Complexity: O(n³) where n = number of nodes (55 constructs → 166K ops, trivial).
#
# Triangle violations: V[i,k] = D_raw[i,k] - D_sp[i,k]
#   If V[i,k] > 0, the direct distance from i to k exceeds the shortest path through
#   some intermediary. This means the raw γ-derived distance violates the triangle
#   inequality — the relationship between i and k is "weaker than expected" given
#   their connections through other constructs. High violations indicate interesting
#   non-transitive SES relationships.
#
# Mediator scores: For each construct j, how much total "shortcutting" flows through j.
#   med_score[j] = Σ_{i≠j,k≠j,i≠k} max(0, D_raw[i,k] - D_raw[i,j] - D_raw[j,k])
#   High score → j is a bottleneck/bridge between otherwise disconnected construct groups.
#   This is analogous to betweenness centrality but uses the continuous distance structure.
#
# Reference: Floyd (1962), "Algorithm 97: Shortest Path", CACM 5(6):345.
#
# Input:
#   data/tda/matrices/manifest.json  — country list + file paths
#
# Output:
#   data/tda/floyd_warshall/{COUNTRY}_shortest_paths.csv
#   data/tda/floyd_warshall/{COUNTRY}_violations.csv
#   data/tda/floyd_warshall/mediator_scores.json
#
# Run:
#   julia --project=. scripts/tda_floyd_warshall.jl

using JSON
using CSV
using DataFrames
using Printf
using Dates

# ── Path setup ────────────────────────────────────────────────────────────────
const JULIA_DIR    = dirname(dirname(@__FILE__))
const ROOT         = dirname(JULIA_DIR)
const NAV_ROOT     = joinpath(dirname(ROOT), "navegador")
const MANIFEST     = length(ARGS) >= 1 ? ARGS[1] : joinpath(NAV_ROOT, "data", "tda", "matrices", "manifest.json")
const OUTPUT_DIR   = length(ARGS) >= 2 ? ARGS[2] : joinpath(NAV_ROOT, "data", "tda", "floyd_warshall")

# ── Floyd-Warshall ────────────────────────────────────────────────────────────

"""
    floyd_warshall!(D::Matrix{Float64})

In-place all-pairs shortest paths via Floyd-Warshall.
Modifies D so that D[i,j] = shortest path distance from i to j.
Unreachable pairs stay as their initial value (typically a large sentinel).

Python equivalent: scipy.sparse.csgraph.shortest_path(D, method='FW')
"""
function floyd_warshall!(D::Matrix{Float64})
    n = size(D, 1)
    @inbounds for k in 1:n
        for i in 1:n
            d_ik = D[i, k]
            if d_ik >= 9000.0  # sentinel / unreachable
                continue
            end
            for j in 1:n
                new_d = d_ik + D[k, j]
                if new_d < D[i, j]
                    D[i, j] = new_d
                end
            end
        end
    end
    return D
end


"""
    triangle_violations(D_raw, D_sp) → Matrix{Float64}

Compute how much each raw distance exceeds its shortest-path distance.
V[i,j] = max(0, D_raw[i,j] - D_sp[i,j])

If V[i,j] > 0, the direct i↔j connection is "weaker" than what the shortest
path through intermediaries would predict. This is a triangle inequality violation
in the raw distance space — the network is not metric-consistent at (i,j).

High-violation edges are candidates for topological "holes" — they may appear
as persistent H1 features (loops) in the Vietoris-Rips complex.
"""
function triangle_violations(D_raw::Matrix{Float64}, D_sp::Matrix{Float64})
    V = max.(D_raw .- D_sp, 0.0)
    # Diagonal is always 0
    for i in 1:size(V, 1)
        V[i, i] = 0.0
    end
    return V
end


"""
    mediator_scores(D_raw, n) → Vector{Float64}

For each node j, compute how much total routing improvement flows through j.

med_score[j] = Σ_{i≠k, i≠j, k≠j} max(0, D_raw[i,k] - (D_raw[i,j] + D_raw[j,k]))

Intuition: if going i→j→k is shorter than going i→k directly, then j "mediates"
the i↔k relationship. The sum over all such (i,k) pairs gives the total mediation
power of construct j.

This is a weighted analog of betweenness centrality: instead of counting how many
shortest paths pass through j, we sum the distance savings.

Python equivalent: networkx.betweenness_centrality (but this is distance-weighted).
"""
function mediator_scores(D_raw::Matrix{Float64})
    n = size(D_raw, 1)
    scores = zeros(Float64, n)
    for j in 1:n
        total = 0.0
        @inbounds for i in 1:n
            if i == j; continue; end
            for k in 1:n
                if k == j || k == i; continue; end
                indirect = D_raw[i, j] + D_raw[j, k]
                improvement = D_raw[i, k] - indirect
                if improvement > 0
                    total += improvement
                end
            end
        end
        scores[j] = total
    end
    return scores
end


"""
    read_distance_csv(path) → (Matrix{Float64}, Vector{String})

Read a square distance matrix CSV where row 1 is headers and col 1 is row labels.
Returns the numeric matrix and the construct names.
"""
function read_distance_csv(path::String)
    df = CSV.read(path, DataFrame)
    # First column is construct names (row labels)
    constructs = string.(df[!, 1])
    # Remaining columns are the matrix values
    # CSV.jl reads NaN as Missing — coalesce to sentinel (9999.0 = unreachable)
    mat = Matrix{Float64}(coalesce.(Matrix(df[!, 2:end]), 9999.0))
    return mat, constructs
end


# ── Main ─────────────────────────────────────────────────────────────────────

function main()
    mkpath(OUTPUT_DIR)

    println("=" ^ 60)
    println("TDA Phase 1 — Floyd-Warshall + Mediator Scores")
    println("=" ^ 60)
    println("Start: $(now())")

    # Load manifest
    manifest = JSON.parsefile(MANIFEST)
    countries = manifest["countries"]
    constructs = manifest["construct_index"]
    n_constructs = length(constructs)
    println("Countries: $(length(countries)), Constructs: $n_constructs")

    # Process each country
    all_mediators = Dict{String, Any}()
    total_violations = 0
    t0 = time()

    for (idx, alpha3) in enumerate(countries)
        # Read distance matrix
        d_path = manifest["files"][alpha3]["distance"]
        D_raw, _ = read_distance_csv(d_path)

        # Floyd-Warshall
        D_sp = copy(D_raw)
        floyd_warshall!(D_sp)

        # Triangle violations
        V = triangle_violations(D_raw, D_sp)
        n_violations = count(V .> 0.01)  # count non-trivial violations
        total_violations += n_violations

        # Mediator scores
        med = mediator_scores(D_raw)
        top_idx = argmax(med)
        top_construct = constructs[top_idx]

        # Save shortest-path matrix
        sp_df = DataFrame(D_sp, Symbol.(constructs))
        insertcols!(sp_df, 1, :construct => constructs)
        CSV.write(joinpath(OUTPUT_DIR, "$(alpha3)_shortest_paths.csv"), sp_df)

        # Save violation matrix
        v_df = DataFrame(V, Symbol.(constructs))
        insertcols!(v_df, 1, :construct => constructs)
        CSV.write(joinpath(OUTPUT_DIR, "$(alpha3)_violations.csv"), v_df)

        # Store mediator scores
        med_dict = Dict(constructs[i] => round(med[i], digits=4) for i in 1:n_constructs)
        all_mediators[alpha3] = Dict(
            "scores" => med_dict,
            "top_mediator" => top_construct,
            "top_score" => round(med[top_idx], digits=4),
            "n_violations" => n_violations,
        )

        if idx % 10 == 0 || idx == length(countries)
            @printf("  [%d/%d] %s: top mediator = %s (%.2f), violations = %d\n",
                    idx, length(countries), alpha3, top_construct, med[top_idx], n_violations)
        end
    end

    elapsed = time() - t0

    # Save mediator scores JSON
    mediator_path = joinpath(OUTPUT_DIR, "mediator_scores.json")
    open(mediator_path, "w") do f
        JSON.print(f, all_mediators, 2)
    end

    # Summary
    println("\n" * "─" ^ 60)
    @printf("  Countries processed: %d\n", length(countries))
    @printf("  Total triangle violations (>0.01): %d\n", total_violations)
    @printf("  Time: %.1f seconds\n", elapsed)
    println("  Output: $OUTPUT_DIR")
    println("Done.")
end

main()
