"""
    demo_dr.jl — Doubly Robust Bridge Estimator demo

Generates 1200 synthetic respondents in two separate surveys with 4 SES
variables and an attitude variable influenced by education (escol). The DR
bridge estimates how much shared SES structure drives co-variation.

Run:  julia --project=. examples/demo_dr.jl
Expected runtime: < 30 seconds.
"""

using NavegadorBridge
using DataFrames
using Random
using Printf

println("=" ^ 60)
println("NavegadorBridge — DR Bridge Demo")
println("=" ^ 60)

rng  = MersenneTwister(42)
n    = 1200
bins = ["0-18","19-24","25-34","35-44","45-54","55-64","65+"]

println("Generating synthetic surveys (n=$n each)...")

# ── Survey A: trust in institutions ──────────────────────────────────────
escol_a  = Float64.(rand(rng, 1:5, n))
tam_a    = Float64.(rand(rng, 1:4, n))
latent_a = 0.8 .* escol_a .- 0.3 .* tam_a .+ randn(rng, n) .* 0.8
trust_a  = Float64.(clamp.(round.(Int, latent_a .+ 2.5), 1, 5))

df_a = DataFrame(
    sexo    = Float64.(rand(rng, [1.0,2.0], n)),
    edad    = bins[clamp.(rand(rng, 1:7, n), 1, 7)],
    escol   = escol_a,
    Tam_loc = tam_a,
    trust_in_institutions = trust_a,
)

# ── Survey B: cultural consumption ───────────────────────────────────────
escol_b  = Float64.(rand(rng, 1:5, n))
tam_b    = Float64.(rand(rng, 1:4, n))
latent_b = 0.7 .* escol_b .+ 0.1 .* tam_b .+ randn(rng, n) .* 0.9
culture_b = Float64.(clamp.(round.(Int, latent_b .+ 1.5), 1, 5))

df_b = DataFrame(
    sexo    = Float64.(rand(rng, [1.0,2.0], n)),
    edad    = bins[clamp.(rand(rng, 1:7, n), 1, 7)],
    escol   = escol_b,
    Tam_loc = tam_b,
    cultural_consumption = culture_b,
)

println("  Survey A: $(nrow(df_a)) rows | trust_in_institutions (1–5)")
println("  Survey B: $(nrow(df_b)) rows | cultural_consumption  (1–5)")
println()
println("Running DR estimator (n_sim=2000, n_bootstrap=50)...")

t0 = time()
result = dr_estimate(
    df_a, :trust_in_institutions,
    df_b, :cultural_consumption;
    n_sim=2000, n_bootstrap=50, seed=42,
)
elapsed = time() - t0

println()
println("=" ^ 60)
println("RESULTS")
println("=" ^ 60)
@printf("  Goodman-Kruskal γ : %+.4f\n", result.gamma)
@printf("  95%% bootstrap CI  : [%+.4f, %+.4f]\n", result.gamma_ci_lo, result.gamma_ci_hi)
@printf("  CI width          : %.4f\n", result.gamma_ci_hi - result.gamma_ci_lo)
excl = result.gamma_ci_lo > 0 || result.gamma_ci_hi < 0
@printf("  CI excludes zero  : %s\n", excl ? "YES (significant)" : "no")
println()
@printf("  Normalized MI     : %.4f\n", result.nmi)
@printf("  Cramér's V        : %.4f\n", result.cramers_v)
println()
@printf("  Propensity KS     : %.4f%s\n",
    result.ks_overlap, result.ks_warning ? " (WARNING)" : " (ok)")
@printf("  Weights trimmed   : %d\n", result.n_trimmed)
@printf("  Models converged  : %s\n", result.converged ? "yes" : "no")
println()
@printf("  n_a=%d  n_b=%d  elapsed=%.1fs\n", result.n_a, result.n_b, elapsed)

println()
println("Interpretation:")
if abs(result.gamma) < 0.05
    println("  γ ≈ 0: No monotonic SES-mediated co-variation detected.")
elseif result.gamma > 0
    println("  γ > 0: Higher SES → higher scores on BOTH attitudes.")
else
    println("  γ < 0: Higher SES pushes attitudes in opposite directions.")
end
println("Done.")
