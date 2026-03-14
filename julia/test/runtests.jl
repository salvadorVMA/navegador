"""
    runtests.jl — NavegadorBridge test suite

Tests:
  1. goodman_kruskal_gamma  — analytic answers for known tables
  2. normalized_mutual_information — independent → NMI≈0
  3. cronbach_alpha         — known high/low alpha inputs
  4. fit_ordered_logit      — recovers β=1.5 on synthetic data (N=600)
  5. dr_estimate            — valid output on synthetic data (N=600 each)
"""

using Test, Random, Statistics, LinearAlgebra, Distributions, Printf
using DataFrames
using NavegadorBridge

println("=" ^ 60)
println("NavegadorBridge — Running test suite")
println("=" ^ 60)

# ── 1. goodman_kruskal_gamma ──────────────────────────────────────────────
@testset "goodman_kruskal_gamma" begin
    # Perfect positive concordance (diagonal mass) → γ = +1
    pos = Float64[1 0 0; 0 1 0; 0 0 1] ./ 3.0
    @test goodman_kruskal_gamma(pos) ≈ 1.0 atol=1e-10

    # Perfect negative concordance (anti-diagonal) → γ = -1
    neg = Float64[0 0 1; 0 1 0; 1 0 0] ./ 3.0
    @test goodman_kruskal_gamma(neg) ≈ -1.0 atol=1e-10

    # Independence (outer product) → γ ≈ 0
    p_a = [0.3, 0.4, 0.3]; p_b = [0.5, 0.5]
    indep = p_a * p_b'
    @test abs(goodman_kruskal_gamma(indep)) < 0.01

    # 2×2 anti-diagonal → γ = -1
    @test goodman_kruskal_gamma(Float64[0 1; 1 0] ./ 2) ≈ -1.0 atol=1e-10

    # Output range [-1, 1] for random tables
    rng = MersenneTwister(42)
    for _ in 1:20
        m = abs.(randn(rng, 3, 4)) .+ 0.01
        m ./= sum(m)
        g = goodman_kruskal_gamma(m)
        @test -1.0 <= g <= 1.0
    end
end

# ── 2. normalized_mutual_information ─────────────────────────────────────
@testset "normalized_mutual_information" begin
    # Independence → NMI = 0
    p_a = [0.3, 0.4, 0.3]; p_b = [0.5, 0.5]
    @test normalized_mutual_information(p_a * p_b') < 1e-10

    # Perfect correlation (diagonal 3×3) → NMI = 1
    @test normalized_mutual_information(Matrix(Diagonal([1/3,1/3,1/3]))) ≈ 1.0 atol=1e-8

    # NMI ∈ [0, 1]
    rng = MersenneTwister(7)
    for _ in 1:20
        m = abs.(randn(rng, 3, 4)) .+ 0.01
        m ./= sum(m)
        nmi = normalized_mutual_information(m)
        @test 0.0 <= nmi <= 1.0 + 1e-8
    end
end

# ── 3. Cronbach's alpha ───────────────────────────────────────────────────
@testset "cronbach_alpha" begin
    rng = MersenneTwister(1)
    # High alpha: items near-perfectly correlated
    latent = randn(rng, 200)
    X_high = hcat([latent .+ randn(rng, 200) .* 0.05 for _ in 1:4]...)
    @test cronbach_alpha(X_high) > 0.95

    # Low alpha: independent items
    X_low = randn(rng, 200, 4)
    @test cronbach_alpha(X_low) < 0.3

    # Single item → NaN
    @test isnan(cronbach_alpha(randn(rng, 50, 1)))

    # scale_to_output: correct range
    v = randn(rng, 100)
    s = scale_to_output(v; out_min=1.0, out_max=10.0)
    @test minimum(s) ≈ 1.0 atol=1e-8
    @test maximum(s) ≈ 10.0 atol=1e-8

    # reverse_code: [1,2,3,4,5] → [5,4,3,2,1]
    @test reverse_code(collect(1.0:5.0)) ≈ [5.0,4.0,3.0,2.0,1.0] atol=1e-8
end

# ── 4. Ordered logit — coefficient recovery ───────────────────────────────
@testset "fit_ordered_logit" begin
    rng     = MersenneTwister(2024)
    n, K    = 600, 4
    β_true  = [1.5]
    α_true  = [-1.0, 0.0, 1.0]
    X       = randn(rng, n, 1)

    # Simulate outcomes
    y = Int[]
    for i in 1:n
        η = X[i,1] * β_true[1]
        probs = zeros(K)
        cp = 0.0
        for k in 1:K
            ck = k <= length(α_true) ? NavegadorBridge.sigmoid(α_true[k] - η) : 1.0
            probs[k] = max(ck - cp, 1e-10)
            cp = ck
        end
        probs ./= sum(probs)
        push!(y, rand(rng, Categorical(probs)))
    end

    model = fit_ordered_logit(X, y; K=K)

    @test model.converged
    @test abs(model.coef[1] - β_true[1]) < 0.4   # within 0.4 of truth
    @test issorted(model.thresholds)               # α_1 < α_2 < α_3

    P = predict_proba(model, X)
    @test size(P) == (n, K)
    @test all(abs.(sum(P, dims=2) .- 1.0) .< 1e-6)
    @test all(P .>= 0.0)
end

# ── 5. DR estimate — synthetic integration test ───────────────────────────
@testset "dr_estimate" begin
    rng  = MersenneTwister(999)
    n    = 600
    bins = ["0-18","19-24","25-34","35-44","45-54","55-64","65+"]

    # Survey A
    escol_a  = Float64.(rand(rng, 1:5, n))
    df_a = DataFrame(
        sexo    = Float64.(rand(rng, [1,2], n)),
        edad    = bins[clamp.(rand(rng, 1:7, n), 1, 7)],
        escol   = escol_a,
        Tam_loc = Float64.(rand(rng, 1:4, n)),
        attitude = Float64.(clamp.(round.(Int, escol_a .+ randn(rng,n).*0.5), 1, 5)),
    )

    # Survey B
    escol_b  = Float64.(rand(rng, 1:5, n))
    df_b = DataFrame(
        sexo    = Float64.(rand(rng, [1,2], n)),
        edad    = bins[clamp.(rand(rng, 1:7, n), 1, 7)],
        escol   = escol_b,
        Tam_loc = Float64.(rand(rng, 1:4, n)),
        attitude = Float64.(clamp.(round.(Int, escol_b .+ randn(rng,n).*0.5), 1, 5)),
    )

    result = dr_estimate(df_a, :attitude, df_b, :attitude;
                         n_sim=500, n_bootstrap=20, seed=42)

    @test -1.0 <= result.gamma <= 1.0
    @test result.gamma_ci_lo <= result.gamma_ci_hi
    @test result.gamma_ci_hi - result.gamma_ci_lo >= 0.0
    @test 0.0 <= result.nmi <= 1.0
    @test result.cramers_v >= 0.0
    @test result.n_a == n
    @test result.n_b == n
    # Both attitudes driven by escol → positive gamma expected
    @test result.gamma > -0.3

    @printf("  DR: γ=%.4f CI=[%.4f,%.4f] NMI=%.4f\n",
        result.gamma, result.gamma_ci_lo, result.gamma_ci_hi, result.nmi)
end

println("=" ^ 60)
println("All tests passed.")
println("=" ^ 60)
