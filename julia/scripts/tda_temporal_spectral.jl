# tda_temporal_spectral.jl — Phase 5 (Temporal): Per-wave Floyd-Warshall + spectral
#
# For each Mexico wave (W3-W7), computes:
#   1. Floyd-Warshall shortest paths + mediator scores
#   2. Normalized Laplacian spectrum + spectral features
#
# This produces per-wave topological features that Phase 6 (Python) uses to
# compute the temporal spectral trajectory — how Mexico's construct network
# geometry evolves from 1996 to 2018.
#
# Input:
#   data/tda/temporal/manifest.json  — per-wave file paths
#
# Output:
#   data/tda/temporal/W{n}_shortest_paths.csv
#   data/tda/temporal/W{n}_mediators.json
#   data/tda/temporal/spectral_features.json  — per-wave spectral summary
#
# Run:
#   julia --project=. scripts/tda_temporal_spectral.jl

using JSON
using CSV
using DataFrames
using Printf
using Dates
using LinearAlgebra
using Statistics: mean, median

const JULIA_DIR    = dirname(dirname(@__FILE__))
const ROOT         = dirname(JULIA_DIR)
const NAV_ROOT     = joinpath(dirname(ROOT), "navegador")
const MANIFEST     = length(ARGS) >= 1 ? ARGS[1] : joinpath(NAV_ROOT, "data", "tda", "temporal", "manifest.json")
const OUTPUT_DIR   = length(ARGS) >= 2 ? ARGS[2] : joinpath(NAV_ROOT, "data", "tda", "temporal")


function read_csv_matrix(path::String, default_val::Float64=0.0)
    df = CSV.read(path, DataFrame)
    constructs = string.(df[!, 1])
    mat = Matrix{Float64}(coalesce.(Matrix(df[!, 2:end]), default_val))
    return mat, constructs
end


function floyd_warshall!(D::Matrix{Float64})
    n = size(D, 1)
    @inbounds for k in 1:n
        for i in 1:n
            d_ik = D[i, k]
            if d_ik >= 9000.0; continue; end
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


function mediator_scores(D_raw::Matrix{Float64})
    n = size(D_raw, 1)
    scores = zeros(Float64, n)
    for j in 1:n
        total = 0.0
        @inbounds for i in 1:n
            if i == j; continue; end
            for k in 1:n
                if k == j || k == i; continue; end
                improvement = D_raw[i, k] - (D_raw[i, j] + D_raw[j, k])
                if improvement > 0
                    total += improvement
                end
            end
        end
        scores[j] = total
    end
    return scores
end


function normalized_laplacian_spectrum(W_abs::Matrix{Float64})
    n = size(W_abs, 1)
    deg = vec(sum(W_abs, dims=2))
    L = Matrix{Float64}(I, n, n)
    for i in 1:n, j in 1:n
        if i != j && deg[i] > 0 && deg[j] > 0
            L[i, j] = -W_abs[i, j] / sqrt(deg[i] * deg[j])
        end
    end
    L = (L + L') / 2
    return sort(eigvals(Symmetric(L)))
end


function main()
    println("=" ^ 60)
    println("Temporal Phase 5 — Per-wave Floyd-Warshall + Spectral")
    println("=" ^ 60)
    println("Start: $(now())")

    manifest = JSON.parsefile(MANIFEST)
    waves = manifest["waves"]
    constructs = manifest["construct_index"]
    n = length(constructs)
    println("Waves: $waves, Constructs: $n")

    all_spectra = Dict{String, Any}()
    all_mediators = Dict{String, Any}()

    for wave in waves
        wkey = "W$wave"
        info = manifest["files"][wkey]
        year = info["year"]

        # Read distance matrix
        D_raw, _ = read_csv_matrix(info["distance"], 9999.0)

        # Floyd-Warshall
        D_sp = copy(D_raw)
        floyd_warshall!(D_sp)

        # Save shortest paths
        sp_df = DataFrame(D_sp, Symbol.(constructs))
        insertcols!(sp_df, 1, :construct => constructs)
        CSV.write(joinpath(OUTPUT_DIR, "$(wkey)_shortest_paths.csv"), sp_df)

        # Mediator scores
        med = mediator_scores(D_raw)
        top_idx = argmax(med)
        med_dict = Dict{String, Any}(
            "scores" => Dict(constructs[i] => round(med[i], digits=2) for i in 1:n),
            "top_mediator" => constructs[top_idx],
            "top_score" => round(med[top_idx], digits=2),
        )
        all_mediators[wkey] = med_dict

        # Read weight matrix for spectral analysis
        W, _ = read_csv_matrix(info["weight"], 0.0)
        W_abs = abs.(W)
        W_abs[isnan.(W_abs)] .= 0.0
        W_sym = (W_abs .+ W_abs') ./ 2

        # Spectral features
        spec = normalized_laplacian_spectrum(W_sym)
        non_zero = filter(x -> abs(x) > 1e-6, spec)
        fiedler = isempty(non_zero) ? 0.0 : minimum(non_zero)
        total = sum(spec)
        if total > 0
            p = spec ./ total
            p = p[p .> 0]
            entropy = -sum(p .* log.(p))
        else
            entropy = 0.0
        end

        all_spectra[wkey] = Dict{String, Any}(
            "wave" => wave,
            "year" => year,
            "n_pairs" => info["n_pairs"],
            "n_constructs_present" => info["n_constructs_present"],
            "fiedler_value" => round(fiedler, digits=6),
            "spectral_gap" => round(length(spec) >= 2 ? spec[2] - spec[1] : 0.0, digits=6),
            "spectral_entropy" => round(entropy, digits=4),
            "spectral_radius" => round(maximum(spec), digits=4),
            "spectrum" => [round(s, digits=6) for s in spec],
            "top_mediator" => constructs[top_idx],
        )

        @printf("  W%d (%d): %d pairs, fiedler=%.4f, entropy=%.3f, mediator=%s\n",
                wave, year, info["n_pairs"], fiedler, entropy, constructs[top_idx])
    end

    # Save
    open(joinpath(OUTPUT_DIR, "spectral_features.json"), "w") do f
        JSON.print(f, all_spectra, 2)
    end
    open(joinpath(OUTPUT_DIR, "mediators_per_wave.json"), "w") do f
        JSON.print(f, all_mediators, 2)
    end

    println("\nOutput: $OUTPUT_DIR")
    println("Done.")
end

main()
