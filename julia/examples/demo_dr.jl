# demo_dr.jl — Doubly Robust Bridge Estimator demo
#
# Generates synthetic respondents in two separate surveys connected only through
# shared SES variables.  The DR bridge estimates how much of the co-variation
# between attitudes across surveys is mediated by SES.
#
# ── What this demo tests ──────────────────────────────────────────────────────
# Survey A: "trust in institutions" — positively driven by education (escol)
# Survey B: "cultural consumption"  — also positively driven by education
# Both variables share the same positive-direction SES gradient, so we expect
# γ > 0 (higher SES → higher scores on both attitudes).
#
# Expected γ ≈ +0.58, CI excludes zero → significant SES-mediated co-variation.
#
# ── How to run ────────────────────────────────────────────────────────────────
# julia --project=. examples/demo_dr.jl
# Expected runtime: < 10 seconds (after JIT warmup on first run).
#
# ── `using` at top-level ──────────────────────────────────────────────────────
# Unlike Python where `import` can appear anywhere, Julia convention is to put
# all `using` statements at the top of the file.  This makes dependencies
# visible at a glance and avoids repeated compilation.

using NavegadorBridge   # our module: goodman_kruskal_gamma, dr_estimate, etc.
using DataFrames        # DataFrame constructor, nrow
using Random            # MersenneTwister, rand
using Printf            # @printf for formatted output

println("=" ^ 60)
println("NavegadorBridge — DR Bridge Demo")
println("=" ^ 60)

# ── Random number generation ──────────────────────────────────────────────────
# `MersenneTwister(42)` creates a seeded RNG for reproducibility.
# Unlike Python's `np.random.default_rng(42)` which is stateless between calls,
# Julia's RNG is a mutable object.  We pass it explicitly to `rand` so that the
# same seed always produces the same synthetic data.
rng  = MersenneTwister(42)
n    = 1200   # respondents per survey (matches real survey n ≈ 1200)

# Age bins as string labels — matching the format that `encode_edad` expects.
# The real surveys store edad as pre-binned strings, not continuous ages.
bins = ["0-18","19-24","25-34","35-44","45-54","55-64","65+"]

println("Generating synthetic surveys (n=$n each)...")

# ── Survey A: trust in institutions ──────────────────────────────────────────
# Data-generating process:
#   latent_a = 0.8·escol − 0.3·Tam_loc + ε    (strong education effect)
#   trust_a  = clamp(round(latent_a + 2.5), 1, 5)
#
# `rand(rng, 1:5, n)` samples integers uniformly from 1 to 5, n times.
# `Float64.(...)` converts the integer array to Float64 (type coercion).
# Python equivalent: `rng.integers(1, 6, size=n).astype(float)`.
escol_a  = Float64.(rand(rng, 1:5, n))
tam_a    = Float64.(rand(rng, 1:4, n))

# `randn(rng, n)` samples n values from N(0,1).  The explicit `rng` argument
# ensures reproducibility.  Python equivalent: `rng.standard_normal(n)`.
latent_a = 0.8 .* escol_a .- 0.3 .* tam_a .+ randn(rng, n) .* 0.8
# `round.(Int, v)` rounds element-wise and converts to Int array.
# `clamp.(v, 1, 5)` clips to [1, 5] element-wise.
trust_a  = Float64.(clamp.(round.(Int, latent_a .+ 2.5), 1, 5))

# `DataFrame(col1=vec1, col2=vec2, ...)` — keyword-argument constructor.
# Each column is a Vector; all must have the same length.
# Python equivalent: `pd.DataFrame({'sexo': ..., 'edad': ..., ...})`.
df_a = DataFrame(
    sexo    = Float64.(rand(rng, [1.0,2.0], n)),   # binary 1=M, 2=F
    edad    = bins[clamp.(rand(rng, 1:7, n), 1, 7)],  # string bins (vector indexing)
    escol   = escol_a,
    Tam_loc = tam_a,
    trust_in_institutions = trust_a,
)

# ── Survey B: cultural consumption ───────────────────────────────────────────
# Similar education effect (0.7) → γ > 0 is expected.
# Smaller town-size effect (+0.1 vs -0.3 in A) → partial confounding.
escol_b   = Float64.(rand(rng, 1:5, n))
tam_b     = Float64.(rand(rng, 1:4, n))
latent_b  = 0.7 .* escol_b .+ 0.1 .* tam_b .+ randn(rng, n) .* 0.9
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

# ── Run the DR estimator ──────────────────────────────────────────────────────
# `time()` returns seconds since Unix epoch as Float64.
# `elapsed = time() - t0` gives wall-clock time in seconds.
t0 = time()

# `:trust_in_institutions` is a Symbol (column name) created with the : prefix.
# In Python you would pass the string "trust_in_institutions" as a column name.
# n_bootstrap=50 (not 200) for a fast demo; use 200 for production estimates.
result = dr_estimate(
    df_a, :trust_in_institutions,
    df_b, :cultural_consumption;
    n_sim=2000, n_bootstrap=50, seed=42,
)
elapsed = time() - t0

# ── Print results ─────────────────────────────────────────────────────────────
# `@printf("format", args...)` is a macro for C-style formatted printing.
# `%+.4f` = print with sign, 4 decimal places.
# `%%` = literal percent sign (escaping).
println()
println("=" ^ 60)
println("RESULTS")
println("=" ^ 60)
@printf("  Goodman-Kruskal γ : %+.4f\n", result.gamma)
@printf("  95%% bootstrap CI  : [%+.4f, %+.4f]\n", result.gamma_ci_lo, result.gamma_ci_hi)
@printf("  CI width          : %.4f\n", result.gamma_ci_hi - result.gamma_ci_lo)

# `result.gamma_ci_lo > 0 || result.gamma_ci_hi < 0` is the significance criterion:
# the CI must entirely exclude zero.  Julia's `||` is short-circuit OR (same as Python).
excl = result.gamma_ci_lo > 0 || result.gamma_ci_hi < 0
@printf("  CI excludes zero  : %s\n", excl ? "YES (significant)" : "no")
println()
@printf("  Normalized MI     : %.4f\n", result.nmi)
@printf("  Cramér's V        : %.4f\n", result.cramers_v)
println()
@printf("  Propensity KS     : %.4f%s\n",
    result.ks_overlap, result.ks_warning ? " (WARNING: surveys differ in SES)" : " (ok)")
@printf("  Weights trimmed   : %d\n", result.n_trimmed)
@printf("  Models converged  : %s\n", result.converged ? "yes" : "no")
println()
@printf("  n_a=%d  n_b=%d  elapsed=%.1fs\n", result.n_a, result.n_b, elapsed)

# ── Interpretation ────────────────────────────────────────────────────────────
println()
println("Interpretation:")
if abs(result.gamma) < 0.05
    println("  γ ≈ 0: No monotonic SES-mediated co-variation detected.")
    println("  Both attitudes are SES-independent (or driven in orthogonal directions).")
elseif result.gamma > 0
    println("  γ > 0: Higher SES → higher scores on BOTH attitudes.")
    println("  SES mediates a positive co-variation across surveys.")
else
    println("  γ < 0: Higher SES pushes attitudes in opposite directions.")
    println("  SES creates a trade-off between these two attitude domains.")
end
println("Done.")
