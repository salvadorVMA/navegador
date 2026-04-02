# tda_spectral_distances.jl — Phase 3: Laplacian spectral distances between networks
#
# Computes pairwise distances between all 66 country networks based on their
# graph Laplacian spectra. The result is a 66×66 distance matrix that captures
# how structurally similar/different two countries' construct networks are.
#
# ── Mathematical background ──────────────────────────────────────────────────
#
# Graph Laplacian:
#   For a weighted adjacency matrix W (symmetric, non-negative), the
#   combinatorial Laplacian is L = D - W, where D = diag(W·1) is the
#   degree matrix. The normalized Laplacian is L_norm = I - D^{-1/2} W D^{-1/2}.
#
#   We use the normalized Laplacian because it's scale-invariant: two networks
#   with the same structure but different overall edge magnitudes will have
#   similar spectra. This matters because γ magnitudes vary across countries.
#
# Laplacian spectrum:
#   The eigenvalues λ₁ ≤ λ₂ ≤ ... ≤ λₙ of L encode the network's global shape:
#   - λ₁ = 0 always (constant eigenvector)
#   - λ₂ = algebraic connectivity (Fiedler value) — larger = more connected
#   - Number of zero eigenvalues = number of connected components
#   - Spectral gap λ₂ - λ₁ relates to mixing time of random walks
#   - Eigenvalue distribution captures community structure
#
# Spectral distance:
#   d(G₁, G₂) = ‖λ⁽¹⁾ - λ⁽²⁾‖₂ (L2 norm of sorted eigenvalue difference)
#
#   This distance is invariant to node labeling (only depends on eigenvalues),
#   computationally cheap (O(n³) eigendecomposition for n=55 is instant),
#   and well-studied in graph comparison (Wilson & Zhu, 2008).
#
# Construct set alignment:
#   Not all countries have all 55 constructs. When comparing two countries,
#   we restrict to their shared constructs (intersection). This gives a fair
#   comparison on the same construct subspace. Countries with < 40 shared
#   constructs are marked as potentially unreliable.
#
# References:
#   Wilson & Zhu (2008), "A study of graph spectra for comparing graphs and trees"
#   Chung (1997), "Spectral Graph Theory"
#
# Input:
#   data/tda/matrices/manifest.json — country list + weight matrix paths
#
# Output:
#   data/tda/spectral/spectral_distance_matrix.csv   — 66×66 pairwise distances
#   data/tda/spectral/spectral_features.json          — per-country spectral features
#
# Run:
#   julia -t 8 --project=. scripts/tda_spectral_distances.jl

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
const OUTPUT_DIR   = length(ARGS) >= 2 ? ARGS[2] : joinpath(NAV_ROOT, "data", "tda", "spectral")

# Minimum shared constructs for a reliable spectral comparison.
# Defaults to 40 but adapts to smaller construct sets via the manifest
# (set dynamically in main() as min(40, floor(0.7 * n_constructs))).
MIN_SHARED = 40


# ── Spectral computation ─────────────────────────────────────────────────────

"""
    normalized_laplacian_spectrum(W_abs) → Vector{Float64}

Compute the sorted eigenvalues of the normalized graph Laplacian.

The normalized Laplacian is: L_norm = I - D^{-1/2} W D^{-1/2}
where D = diag(row sums of W).

Eigenvalues are always in [0, 2] for the normalized Laplacian.
We exclude isolated nodes (zero degree) from the computation.

Python equivalent:
  from scipy.sparse.csgraph import laplacian
  L = laplacian(W, normed=True)
  eigvals = np.linalg.eigvalsh(L)
"""
function normalized_laplacian_spectrum(W_abs::Matrix{Float64})::Vector{Float64}
    n = size(W_abs, 1)

    # Degree vector (row sums)
    deg = vec(sum(W_abs, dims=2))

    # Build normalized Laplacian: L = I - D^{-1/2} W D^{-1/2}
    L = Matrix{Float64}(I, n, n)  # start with identity

    for i in 1:n
        for j in 1:n
            if i == j
                # L[i,i] = 1 (from identity) — already set
                continue
            end
            if deg[i] > 0 && deg[j] > 0
                L[i, j] = -W_abs[i, j] / sqrt(deg[i] * deg[j])
            end
        end
    end

    # Force symmetry (floating point safety)
    L = (L + L') / 2

    # Eigenvalues of symmetric matrix
    vals = eigvals(Symmetric(L))
    return sort(vals)
end


"""
    spectral_distance(s1, s2) → Float64

L2 distance between two sorted eigenvalue vectors.
If vectors have different lengths, pad the shorter one with zeros.
"""
function spectral_distance(s1::Vector{Float64}, s2::Vector{Float64})::Float64
    n1, n2 = length(s1), length(s2)
    if n1 == n2
        return norm(s1 .- s2)
    end

    # Pad shorter vector with zeros (eigenvalue 0 = disconnected component)
    n_max = max(n1, n2)
    v1 = zeros(n_max)
    v2 = zeros(n_max)
    v1[1:n1] = s1
    v2[1:n2] = s2
    return norm(v1 .- v2)
end


"""
    extract_spectral_features(spectrum) → Dict

Extract interpretable features from the Laplacian spectrum.
"""
function extract_spectral_features(spectrum::Vector{Float64})::Dict{String, Any}
    n = length(spectrum)
    # Number of zero eigenvalues = connected components (within tolerance)
    n_components = count(x -> abs(x) < 1e-6, spectrum)
    # Fiedler value = smallest non-zero eigenvalue (algebraic connectivity)
    non_zero = filter(x -> abs(x) > 1e-6, spectrum)
    fiedler = isempty(non_zero) ? 0.0 : minimum(non_zero)
    # Spectral gap
    spectral_gap = n >= 2 ? spectrum[2] - spectrum[1] : 0.0
    # Spectral radius (largest eigenvalue)
    spectral_radius = maximum(spectrum)
    # Spectral entropy: H = -Σ pᵢ log(pᵢ) where pᵢ = λᵢ / Σλ
    total = sum(spectrum)
    if total > 0
        p = spectrum ./ total
        p = p[p .> 0]
        entropy = -sum(p .* log.(p))
    else
        entropy = 0.0
    end

    return Dict(
        "n_eigenvalues" => n,
        "n_components" => n_components,
        "fiedler_value" => round(fiedler, digits=6),
        "spectral_gap" => round(spectral_gap, digits=6),
        "spectral_radius" => round(spectral_radius, digits=4),
        "spectral_entropy" => round(entropy, digits=4),
        "mean_eigenvalue" => round(mean(spectrum), digits=4),
    )
end


"""
    read_weight_csv(path) → (Matrix{Float64}, Vector{String})
"""
function read_weight_csv(path::String)
    df = CSV.read(path, DataFrame)
    constructs = string.(df[!, 1])
    # CSV.jl reads NaN as Missing — coalesce to 0.0 for weight matrices
    mat = Matrix{Float64}(coalesce.(Matrix(df[!, 2:end]), 0.0))
    return mat, constructs
end


"""
    shared_submatrix(W1, c1, W2, c2) → (Matrix, Matrix, Vector{String}, Int)

Extract submatrices restricted to shared constructs between two countries.
Returns (W1_sub, W2_sub, shared_constructs, n_shared).
"""
function shared_submatrix(
    W1::Matrix{Float64}, c1::Vector{String},
    W2::Matrix{Float64}, c2::Vector{String}
)
    shared = intersect(Set(c1), Set(c2))
    shared_sorted = sort(collect(shared))
    n_shared = length(shared_sorted)

    idx1 = [findfirst(==(s), c1) for s in shared_sorted]
    idx2 = [findfirst(==(s), c2) for s in shared_sorted]

    W1_sub = W1[idx1, idx1]
    W2_sub = W2[idx2, idx2]

    return W1_sub, W2_sub, shared_sorted, n_shared
end


# ── Main ─────────────────────────────────────────────────────────────────────

function main()
    mkpath(OUTPUT_DIR)

    println("=" ^ 60)
    println("TDA Phase 3 — Spectral Distances Between Country Networks")
    println("=" ^ 60)
    println("Start: $(now())")
    println("Threads: $(Threads.nthreads())")
    println("Min shared constructs: $MIN_SHARED")

    manifest = JSON.parsefile(MANIFEST)
    countries = manifest["countries"]
    nc = length(countries)
    println("Countries: $nc → $(nc * (nc - 1) ÷ 2) pairwise comparisons")

    # Adapt MIN_SHARED to smaller construct sets (e.g. W3 has 24 constructs)
    n_constructs = get(manifest, "n_constructs", 55)
    global MIN_SHARED = min(40, floor(Int, 0.7 * n_constructs))
    println("Adjusted MIN_SHARED: $MIN_SHARED (n_constructs=$n_constructs)")

    # ── Step 1: Load all weight matrices and compute spectra ─────────────
    println("\n[1/3] Loading weight matrices and computing spectra...")
    weight_matrices = Dict{String, Tuple{Matrix{Float64}, Vector{String}}}()
    spectra = Dict{String, Vector{Float64}}()
    features = Dict{String, Any}()

    for alpha3 in countries
        w_path = manifest["files"][alpha3]["weight"]
        W, constructs = read_weight_csv(w_path)
        W_abs = abs.(W)
        W_abs[isnan.(W_abs)] .= 0.0
        # Symmetrize (should already be, but safety)
        W_sym = (W_abs .+ W_abs') ./ 2

        weight_matrices[alpha3] = (W, constructs)
        spec = normalized_laplacian_spectrum(W_sym)
        spectra[alpha3] = spec
        features[alpha3] = extract_spectral_features(spec)
    end
    println("  All spectra computed.")

    # ── Step 2: Pairwise spectral distances ──────────────────────────────
    println("\n[2/3] Computing pairwise spectral distances...")
    D = zeros(Float64, nc, nc)
    n_shared_mat = zeros(Int, nc, nc)

    # Build pairs list for parallel processing
    pairs = [(i, j) for i in 1:nc for j in (i+1):nc]
    println("  $(length(pairs)) pairs to compute")

    t0 = time()

    @threads for pidx in 1:length(pairs)
        i, j = pairs[pidx]
        c1, c2 = countries[i], countries[j]

        # Get shared constructs
        W1, cons1 = weight_matrices[c1]
        W2, cons2 = weight_matrices[c2]
        W1_sub, W2_sub, shared, n_shared = shared_submatrix(
            abs.(W1), cons1, abs.(W2), cons2
        )
        n_shared_mat[i, j] = n_shared
        n_shared_mat[j, i] = n_shared

        if n_shared < MIN_SHARED
            D[i, j] = NaN
            D[j, i] = NaN
            continue
        end

        # Replace NaN with 0 in submatrices
        W1_sub[isnan.(W1_sub)] .= 0.0
        W2_sub[isnan.(W2_sub)] .= 0.0
        W1_sub = (W1_sub .+ W1_sub') ./ 2
        W2_sub = (W2_sub .+ W2_sub') ./ 2

        # Compute spectra on shared subspace
        s1 = normalized_laplacian_spectrum(W1_sub)
        s2 = normalized_laplacian_spectrum(W2_sub)

        d = spectral_distance(s1, s2)
        D[i, j] = d
        D[j, i] = d
    end

    elapsed = time() - t0
    @printf("  Done in %.1f seconds\n", elapsed)

    # Count reliable pairs
    n_reliable = count(!isnan, [D[i, j] for i in 1:nc for j in (i+1):nc])
    n_total = nc * (nc - 1) ÷ 2
    @printf("  Reliable pairs (≥%d shared): %d/%d (%.0f%%)\n",
            MIN_SHARED, n_reliable, n_total, 100 * n_reliable / n_total)

    # ── Step 3: Save outputs ─────────────────────────────────────────────
    println("\n[3/3] Saving outputs...")

    # Distance matrix CSV
    D_df = DataFrame(D, Symbol.(countries))
    insertcols!(D_df, 1, :country => countries)
    CSV.write(joinpath(OUTPUT_DIR, "spectral_distance_matrix.csv"), D_df)

    # Shared constructs matrix
    ns_df = DataFrame(n_shared_mat, Symbol.(countries))
    insertcols!(ns_df, 1, :country => countries)
    CSV.write(joinpath(OUTPUT_DIR, "shared_constructs_matrix.csv"), ns_df)

    # Spectral features JSON
    open(joinpath(OUTPUT_DIR, "spectral_features.json"), "w") do f
        JSON.print(f, features, 2)
    end

    # Summary
    valid_dists = [D[i, j] for i in 1:nc for j in (i+1):nc if !isnan(D[i, j])]
    println("\n" * "─" ^ 60)
    @printf("  Countries: %d\n", nc)
    @printf("  Reliable pairs: %d / %d\n", n_reliable, n_total)
    if !isempty(valid_dists)
        @printf("  Distance range: [%.4f, %.4f]\n", minimum(valid_dists), maximum(valid_dists))
        @printf("  Mean distance: %.4f\n", mean(valid_dists))
        @printf("  Median distance: %.4f\n", median(valid_dists))
    else
        println("  No valid distances (all pairs below MIN_SHARED threshold)")
    end
    @printf("  Time: %.1f seconds\n", time() - t0)
    println("  Output: $OUTPUT_DIR")
    println("Done.")
end

main()
