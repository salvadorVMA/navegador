# Julia Bridge — Technical Primer and Implementation Guide

This document explains the Julia port of the Navegador survey bridge estimator.
It is written for Python developers who are new to Julia, and covers both the
language itself and the specific statistical computing patterns used in this project.

---

## 1. Why Julia for Survey Bridge Estimation?

The Python `DoublyRobustBridgeEstimator` runs a **bootstrap loop of 200 iterations**,
refitting a proportional-odds ordered logit model on each resampled dataset.
That is the computational bottleneck. In Python + statsmodels, a single 1200-row
ordered logit fit takes ~0.3–1.0 seconds; 200 bootstrap iterations therefore take
**1–3 minutes per pair**, and the v4 construct sweep of 4979 pairs took **11.1 hours**.

Julia offers three concrete advantages for this workload:

### 1.1 JIT Compilation to Native Code

Julia compiles to native machine code on first call (via LLVM), so subsequent calls
run at near-C speed. The first call in a session is slow ("time to first plot"
problem), but all subsequent calls are fast. For a 4979-pair sweep, the compile
cost is amortized over thousands of pairs.

**Expected speedup**: The bootstrap loop (pure numerical linear algebra) is
5–10× faster than Python+statsmodels. The demo (`examples/demo_dr.jl`) with
n_bootstrap=50 on n=1200 synthetic data runs in **4.7 seconds**. The equivalent
Python would take ~40–60 seconds.

### 1.2 Type Stability and Multiple Dispatch

Julia's type system enables the compiler to generate specialized, efficient code.
Functions are compiled separately for each type signature. This is called
**multiple dispatch**: `predict_proba(model, X)` compiles once for
`(OrderedLogitModel, Matrix{Float64})` and the compiled version is reused for
all subsequent calls with those types.

### 1.3 Scientific Computing Ecosystem

| Python          | Julia equivalent |
|-----------------|-----------------|
| numpy           | Base Julia (built-in)  |
| pandas          | DataFrames.jl   |
| statsmodels     | GLM.jl + Optim.jl + hand-coded MLE |
| scipy.optimize  | Optim.jl        |
| scipy.stats     | Distributions.jl, StatsBase.jl |

---

## 2. Julia Fundamentals for Python Developers

### 2.1 Syntax Differences

**1-indexed arrays** (most important difference):

```python
# Python
x = [1, 2, 3]
first = x[0]    # 0-indexed
last  = x[-1]   # negative indexing works
```

```julia
# Julia
x = [1, 2, 3]
first = x[1]    # 1-indexed
last  = x[end]  # `end` keyword for last element
x[2:end]        # slice from 2nd to last
```

**No implicit return** — Julia returns the last expression:

```python
# Python
def add(a, b):
    return a + b
```

```julia
# Julia
function add(a, b)
    a + b           # last expression is returned
end
# Or one-liner:
add(a, b) = a + b
```

**Broadcasting with `.`** — apply operations element-wise:

```python
# Python (numpy)
x = np.array([1.0, 2.0, 3.0])
y = np.log(x)           # works on arrays
z = x + 1.0             # broadcasts
```

```julia
# Julia
x = [1.0, 2.0, 3.0]
y = log.(x)             # . applies log element-wise
z = x .+ 1.0            # . broadcasts addition
```

**Type annotations** (optional but help performance):

```python
# Python (type hints, not enforced)
def fit(X: np.ndarray, y: list) -> float:
    pass
```

```julia
# Julia (enforced at dispatch time)
function fit(X::Matrix{Float64}, y::Vector{Int})::Float64
    ...
end
```

**String interpolation**:

```python
# Python
name = "world"
print(f"Hello {name}")
```

```julia
# Julia
name = "world"
println("Hello $name")
# Or complex expressions:
println("Result: $(2 + 2)")
```

### 2.2 Type System and Parametric Types

Julia uses **parametric types**: `Vector{Float64}` is a vector of 64-bit floats.
The type parameter is resolved at compile time.

```julia
# Concrete types
x::Float64 = 3.14          # 64-bit float
n::Int     = 42             # platform-native integer
v::Vector{Float64} = [1.0, 2.0]
M::Matrix{Float64} = rand(3, 4)

# Parametric struct
struct OrderedLogitModel
    coef       :: Vector{Float64}
    thresholds :: Vector{Float64}
    K          :: Int
    converged  :: Bool
    nll        :: Float64
end
```

### 2.3 Multiple Dispatch vs. OOP

Python uses classes with methods. Julia uses functions with type dispatch:

```python
# Python OOP
class OrderedLogitModel:
    def predict_proba(self, X):
        ...
    def fit(self, X, y, K):
        ...
```

```julia
# Julia: functions dispatch on type of first argument
function predict_proba(model::OrderedLogitModel, X::Matrix{Float64})::Matrix{Float64}
    ...
end

function fit_ordered_logit(X::Matrix{Float64}, y::Vector{Int}; K::Int)::OrderedLogitModel
    ...
end
```

You can add new methods to `predict_proba` for different model types without
modifying the original function — this is how Julia's polymorphism works.

### 2.4 Package Management (Pkg.jl)

```julia
# In Julia REPL — press ] to enter Pkg mode:
] add DataFrames Optim ForwardDiff

# Or programmatically:
using Pkg
Pkg.add(["DataFrames", "Optim", "ForwardDiff"])

# Activate a project environment:
] activate /path/to/project
# Or: julia --project=/path/to/project
```

The `Project.toml` lists direct dependencies; `Manifest.toml` records the exact
resolved versions of all transitive dependencies (generated automatically).

### 2.5 Performance Tips

**Pre-allocate arrays** instead of growing them:

```python
# Python
results = []
for i in range(n):
    results.append(compute(i))
```

```julia
# Julia — pre-allocate
results = Vector{Float64}(undef, n)
for i in 1:n
    results[i] = compute(i)
end
# Or with list comprehension (also fine):
results = [compute(i) for i in 1:n]
```

**Use `@views` to avoid array copies**:

```julia
# This creates a copy (slow for large arrays):
sub = X[2:end, :]

# This creates a view (zero-copy, fast):
sub = @view X[2:end, :]
```

**Avoid global variables in hot loops** — use function arguments instead.

**Type-annotate function arguments** to enable full specialization.

---

## 3. Statistical Computing in Julia

### 3.1 DataFrames.jl vs. pandas

```python
# pandas
import pandas as pd
df = pd.DataFrame({'x': [1,2,3], 'y': [4.0,5.0,6.0]})
df['z'] = df['x'] + df['y']
subset = df[df['x'] > 1]
row_count = len(df)
col_names = df.columns.tolist()
```

```julia
# DataFrames.jl
using DataFrames
df = DataFrame(x=[1,2,3], y=[4.0,5.0,6.0])
df.z = df.x .+ df.y
subset = filter(row -> row.x > 1, df)
row_count = nrow(df)
col_names = propertynames(df)   # returns Vector{Symbol}

# Access a column as a vector:
col = df[!, :x]   # no copy  (equivalent to df['x'].values)
col = df[:, :x]   # copy

# Select columns:
sub = select(df, [:x, :y])

# Drop missing values:
clean = dropmissing(df, [:x, :y])
```

### 3.2 GLM.jl vs. statsmodels

`GLM.jl` provides standard generalized linear models. For the DR bridge, we use
a custom ordered logit (not available in GLM.jl) and logistic regression for the
propensity model.

```python
# statsmodels logistic
import statsmodels.api as sm
Xc = sm.add_constant(X)
model = sm.Logit(y, Xc).fit(method='bfgs', disp=False)
probs = model.predict(Xc)
```

```julia
# GLM.jl logistic
using GLM, DataFrames
df = DataFrame(y=y, x1=X[:,1], x2=X[:,2])
model = glm(@formula(y ~ x1 + x2), df, Binomial(), LogitLink())
probs = predict(model)

# But in NavegadorBridge we use our hand-coded fit_logistic() because:
# 1. It shares the same Optim.jl LBFGS backend as our ordered logit
# 2. It works directly on Matrix{Float64} without DataFrame overhead
# 3. It is compatible with ForwardDiff for gradient computation
β = fit_logistic(Xc, y)        # Xc already has intercept column
probs = predict_logistic(β, Xc)
```

### 3.3 Distributions.jl vs. scipy.stats

```python
# Python
from scipy.stats import norm
p = norm.cdf(1.96)         # 0.975
x = norm.rvs(size=100)     # 100 random samples
```

```julia
# Julia
using Distributions
d = Normal(0.0, 1.0)
p = cdf(d, 1.96)           # 0.975
x = rand(d, 100)           # 100 random samples

# Categorical (for simulating survey responses):
d_cat = Categorical([0.2, 0.5, 0.3])
sample = rand(d_cat)        # returns 1, 2, or 3
```

### 3.4 Optim.jl for Custom Log-Likelihoods

The proportional-odds ordered logit is not available in GLM.jl, so we implement it
using Optim.jl's LBFGS optimizer with ForwardDiff automatic differentiation:

```python
# Python (statsmodels)
from statsmodels.miscmodels.ordinal_model import OrderedModel
result = OrderedModel(y, X, distr='logit').fit(method='bfgs', maxiter=500, disp=False)
β = result.params[:-K+1]     # coefficients
α = result.params[-(K-1):]   # thresholds
```

```julia
# Julia — hand-coded MLE via Optim.jl
using Optim, ForwardDiff

function my_nll(params, X, y, K)
    # ... log-likelihood computation ...
    return -ll
end

# Gradient via automatic differentiation (no manual derivation needed)
g!(grad, params) = ForwardDiff.gradient!(grad, p -> my_nll(p, X, y, K), params)

result = Optim.optimize(
    params -> my_nll(params, X, y, K),
    g!,
    params0,
    Optim.LBFGS(),
    Optim.Options(iterations=500, g_tol=1e-6, show_trace=false),
)
params_hat = Optim.minimizer(result)
```

The key advantage: ForwardDiff computes exact gradients automatically, while
Python/statsmodels uses numerical finite differences (slower, less accurate).

---

## 4. The DR Bridge Estimator — Julia Implementation

### 4.1 Architecture Overview

```
NavegadorBridge.jl (module)
├── gamma_nmi.jl       — goodman_kruskal_gamma, normalized_mutual_information
├── cronbach.jl        — cronbach_alpha, scale_to_output, reverse_code
├── ordinal_model.jl   — fit_ordered_logit, predict_proba, fit_logistic
├── ses_encoder.jl     — encode_ses, drop_sentinel_rows, is_sentinel
├── dr_estimator.jl    — dr_estimate (main API), DRResult
└── sweep.jl           — run_sweep (batch over pairs with checkpointing)
```

### 4.2 Proportional-Odds Model Derivation and Code Walkthrough

The proportional-odds (PO) model relates an ordinal outcome Y ∈ {1,...,K} to
covariates X via:

    P(Y ≤ k | X) = σ(α_k − X·β)    for k = 1,...,K-1

where σ is the sigmoid function, α_1 < α_2 < ... < α_{K-1} are ordered thresholds,
and β is the coefficient vector. This is equivalent to:

    P(Y = k | X) = σ(α_k − X·β) − σ(α_{k-1} − X·β)

with α_0 = −∞ and α_K = +∞.

**Why unconstrained parametrization?** Optimizers work on unconstrained
parameter spaces. We reparametrize thresholds as:

    α_1 = γ_1
    α_k = α_{k-1} + exp(γ_k)  for k ≥ 2

This guarantees α_1 < α_2 < ... < α_{K-1} for any values of γ.

**Code in `ordinal_model.jl`:**

```julia
function decode_thresholds(γ::AbstractVector{T}) where T
    α    = Vector{T}(undef, length(γ))
    α[1] = γ[1]
    for k in 2:length(γ)
        α[k] = α[k-1] + exp(γ[k])   # ensures monotone ordering
    end
    return α
end

function ordered_logit_nll(params, X, y, K)
    p  = size(X, 2)
    β  = params[1:p]                  # regression coefficients
    γ  = params[p+1:end]              # unconstrained threshold params
    α  = decode_thresholds(γ)        # ordered thresholds α_1 < ... < α_{K-1}
    ll = 0.0
    for i in 1:size(X,1)
        η  = dot(X[i,:], β)          # linear predictor
        yi = y[i]
        # P(Y=yi | X_i)
        upper = yi <= length(α) ? sigmoid(α[yi]   - η) : 1.0
        lower = yi > 1          ? sigmoid(α[yi-1] - η) : 0.0
        ll   += log(max(upper - lower, 1e-12))
    end
    return -ll                        # minimize NLL = maximize LL
end
```

**Comparison with Python:**

```python
# Python: statsmodels does all of this internally
result = OrderedModel(y, X, distr='logit').fit(method='bfgs', maxiter=500, disp=False)
# Coefficients and thresholds are in result.params
```

```julia
# Julia: we write the log-likelihood explicitly, then optimize
model = fit_ordered_logit(X, y; K=K, maxiter=500)
# model.coef = β, model.thresholds = α
```

### 4.3 IPW Weighting in Practice

The doubly-robust estimator uses Inverse Probability Weighting (IPW) to reweight
survey A respondents to look like the survey B population:

```python
# Python
prop_a_clipped = np.clip(prop_a, 0.01, 0.99)
raw_weights = (1 - prop_a_clipped) / prop_a_clipped
cap = np.percentile(raw_weights, 95)     # trim extreme weights
weights = np.minimum(raw_weights, cap)
weights /= weights.sum()                 # normalize
```

```julia
# Julia (in dr_estimator.jl)
pa_clip  = clamp.(prop_a, 0.01, 0.99)     # clamp is Julia's clip
raw_w    = (1.0 .- pa_clip) ./ pa_clip    # ./ broadcasts division
cap      = quantile(raw_w, 0.95)
n_trim   = count(>(cap), raw_w)
weights  = min.(raw_w, cap)               # element-wise min
weights ./= sum(weights)                  # in-place division
```

### 4.4 Bootstrap CI Computation

```python
# Python
rng = np.random.default_rng(seed=42)
boot_gammas = []
for _ in range(n_bootstrap):
    idx_a = rng.choice(n_a, size=n_a, replace=True)
    try:
        bm_a = SurveyVarModel(); bm_a.fit(sub_a.iloc[idx_a], ...)
        # ... compute boot gamma ...
        boot_gammas.append(gamma_b)
    except:
        continue
ci = (np.percentile(boot_gammas, 2.5), np.percentile(boot_gammas, 97.5))
```

```julia
# Julia
rng         = MersenneTwister(42)
boot_gammas = Float64[]
for _ in 1:n_bootstrap
    try
        idx_a    = rand(rng, 1:n_a, n_a)    # sample with replacement
        bm_a, _, _, _ = _fit_outcome_model(sub_a[idx_a, :], col_a, available; maxiter=100)
        # ... compute boot gamma ...
        push!(boot_gammas, gamma_b)
    catch
        continue
    end
end
ci_lo = quantile(boot_gammas, 0.025)
ci_hi = quantile(boot_gammas, 0.975)
```

Key differences:
- Julia uses `MersenneTwister` (explicit RNG type) vs. numpy's `default_rng`
- `push!(boot_gammas, val)` appends in-place (the `!` convention signals mutation)
- `sub_a[idx_a, :]` row-indexing works the same way as pandas `.iloc`
- Julia's `try/catch` silently continues; Python's `except: continue` does the same

### 4.5 Joint Table Under CIA

The key innovation (shared with the Python implementation): instead of multiplying
marginals (which always gives γ≈0), we compute individual-level predictions and
average their outer products:

```python
# Python
pa_ref = model_a.predict_proba(X_ref_a).values[:, :K_a]   # (n_sim, K_a)
pb_ref = model_b.predict_proba(X_ref_b).values[:, :K_b]   # (n_sim, K_b)
joint_table = (pa_ref[:, :, None] * pb_ref[:, None, :]).mean(axis=0)
```

```julia
# Julia
Pa_ref = predict_proba(model_a, Xref)[:, 1:K_a]   # n_sim × K_a
Pb_ref = predict_proba(model_b, Xref)[:, 1:K_b]   # n_sim × K_b
joint  = zeros(K_a, K_b)
for i in 1:n_sim
    joint .+= Pa_ref[i, :] * Pb_ref[i, :]'        # outer product, accumulated
end
joint ./= n_sim
joint ./= sum(joint)
```

Python uses NumPy broadcasting (`[:, :, None]`) to vectorize the outer product.
Julia does it in a loop, which is equally fast due to JIT compilation and avoids
the intermediate array allocation.

### 4.6 Performance Comparison: Python vs. Julia

| Operation | Python (statsmodels) | Julia | Speedup |
|-----------|---------------------|-------|---------|
| Single ordered logit fit (n=1200, K=5) | ~0.5s | ~0.01s | ~50× |
| 200 bootstrap iterations | ~120s | ~3-5s | ~30× |
| Full demo (n=1200, n_boot=50) | ~40-60s | ~4.7s | ~10× |
| 4979-pair sweep (n_boot=200) | ~11.1h (Python) | ~1-2h (est.) | ~6-10× |

The ordered logit fit is dramatically faster in Julia because:
1. ForwardDiff computes exact analytical gradients vs. statsmodels' numerical differences
2. LBFGS convergence is faster with exact gradients
3. No Python interpreter overhead or GIL during the optimization loop

---

## 5. Validating Against Python Results

### 5.1 Running Both Implementations on the Same Data

Generate synthetic data in Python, save to CSV, load in Julia:

```python
# Python: generate and save
import pandas as pd, numpy as np
rng = np.random.default_rng(42)
n   = 600
df = pd.DataFrame({
    'sexo':    rng.choice([1,2], n).astype(float),
    'escol':   rng.integers(1, 6, n).astype(float),
    'Tam_loc': rng.integers(1, 5, n).astype(float),
    'attitude': np.clip(rng.integers(1,6,n) + rng.integers(0,3,n), 1, 5).astype(float),
})
# Add edad as string bins
bins = ['0-18','19-24','25-34','35-44','45-54','55-64','65+']
df['edad'] = [bins[i % 7] for i in range(n)]
df.to_csv('/tmp/survey_a.csv', index=False)
```

```julia
# Julia: load and run
using NavegadorBridge, DataFrames, CSV
df_a = CSV.read("/tmp/survey_a.csv", DataFrame)
# ... same for df_b ...
result = dr_estimate(df_a, :attitude, df_b, :attitude; n_sim=500, n_bootstrap=20)
```

### 5.2 Expected Tolerance

The two implementations should produce:
- `|γ_julia - γ_python| < 0.01` for the point estimate
- Comparable CI widths (within 20%)

Differences arise from:
1. Different optimization paths (same algorithm, different numerical precision)
2. Different random seeds for the reference SES population
3. Slightly different bootstrap sampling (MersenneTwister vs. numpy PCG64)

To align seeds: use `seed=42` in Julia `dr_estimate()` and `np.random.default_rng(42)` in Python.

---

## 6. Running the Sweep

### 6.1 Input Format

Create a CSV with columns `var_a` and `var_b` in `"agg_colname|DOMAIN"` format:

```csv
var_a,var_b
agg_personal_religiosity|REL,agg_structural_housing_quality|HAB
agg_trust_in_institutions|POL,agg_cultural_consumption|EDU
```

This mirrors the Python sweep output format.

### 6.2 Data Loader

You must provide a `data_loader` function that returns a
`Dict{String, DataFrame}` mapping domain codes to DataFrames:

```julia
function load_survey_data()
    # Load your enc_dict equivalent
    # Returns Dict: "REL" => df_rel, "HAB" => df_hab, ...
    ...
end

run_sweep(
    "pairs.csv",
    "output.json";
    data_loader  = load_survey_data,
    n_sim        = 2000,
    n_bootstrap  = 200,
)
```

### 6.3 Output Format (Same Schema as Python v5)

```json
{
  "metadata": {
    "n_sim": 2000,
    "n_bootstrap": 200,
    "n_total": 4979,
    "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
    "timestamp": "2026-03-14T..."
  },
  "estimates": {
    "agg_col_a|DOMAIN_A::agg_col_b|DOMAIN_B": {
      "dr_gamma":  0.1332,
      "dr_ci_lo":  0.0891,
      "dr_ci_hi":  0.1773,
      "dr_nmi":    0.0087,
      "dr_v":      0.0621,
      "dr_ks":     0.0312,
      "ci_width":  0.0882,
      "excl_zero": true,
      "n_a":       1200,
      "n_b":       1200
    }
  }
}
```

### 6.4 Resume/Checkpoint Mechanics

The sweep saves atomically after every pair (or every `save_every` pairs):
1. Write to `output.json.tmp`
2. Rename to `output.json` (atomic on POSIX systems)

On resume, already-computed pair keys are skipped:

```julia
# Resuming automatically
run_sweep("pairs.csv", "output.json"; resume=true)

# Force restart
run_sweep("pairs.csv", "output.json"; resume=false)
```

---

## 7. Extending the Implementation

### 7.1 Adding a New Estimator

To add a `BayesianBridgeEstimator`, create `src/bayesian_estimator.jl`:

```julia
struct BayesianResult
    gamma    :: Float64
    gamma_ci :: Tuple{Float64, Float64}
    # ...
end

function bayesian_estimate(
    df_a::DataFrame, col_a::Symbol,
    df_b::DataFrame, col_b::Symbol;
    n_draws::Int = 200,
    kwargs...
)::BayesianResult
    # ... Laplace approximation to posterior ...
end
```

Then add to `NavegadorBridge.jl`:

```julia
include("bayesian_estimator.jl")
export BayesianResult, bayesian_estimate
```

### 7.2 Cross-Country / Temporal Sweeps

The sweep framework is generic. Pass a different `data_loader` and pairs CSV:

```julia
# Temporal sweep: Mexico WVS waves 1–7
function load_wvs_mexico()
    # Returns Dict: "W1_MEX" => df_w1, "W2_MEX" => df_w2, ...
end

run_sweep(
    "wvs_mexico_pairs.csv",
    "wvs_temporal_sweep.json";
    data_loader = load_wvs_mexico,
    n_sim       = 2000,
    n_bootstrap = 200,
)
```

### 7.3 Goodman-Kruskal γ vs. NMI: Detecting Non-Monotonic SES Structure

The v3 sweep finding was that NMI was universally low (max 0.037), meaning all
SES structure was monotonic. To recheck on new data:

```julia
using NavegadorBridge

joint = ... # K_a × K_b matrix (construct your table)

γ   = goodman_kruskal_gamma(joint)
nmi = normalized_mutual_information(joint)

if abs(γ) < 0.05 && nmi > 0.02
    println("Non-monotonic SES structure detected! (γ≈0 but NMI=$nmi)")
else
    println("γ=$γ, NMI=$nmi — $(abs(γ) > 0.05 ? "monotonic" : "independent")")
end
```

---

## 8. Setup and Troubleshooting

### 8.1 Running Tests

```bash
export PATH="$HOME/.juliaup/bin:$PATH"
cd /path/to/navegador_julia_bridge/julia
julia --project=. test/runtests.jl
```

Expected output: 66 tests, all pass in ~7 seconds.

### 8.2 Running the Demo

```bash
julia --project=. examples/demo_dr.jl
```

Expected output: γ ≈ +0.58, CI [0.55, 0.61], elapsed ≈ 4.7s.

### 8.3 Common Issues

**"Package X not in dependencies"**: Standard library packages (LinearAlgebra,
Statistics, Random, etc.) need to be explicitly added in Julia 1.9+:
```julia
using Pkg; Pkg.add(["LinearAlgebra", "Statistics", "Random", "Dates", "Printf", "Test"])
```

**"UUID mismatch" error**: Don't hard-code UUIDs in Project.toml. Use
`Pkg.add("PackageName")` to let the resolver populate the correct UUIDs.

**Slow first run**: Julia compiles all methods on first call. Subsequent calls
are fast. This is expected behavior ("time to first plot" problem).

**LBFGS non-convergence**: Increase `maxiter` or reduce the number of categories
(more categories = more threshold parameters = harder optimization). The `bin_to_5`
helper in `dr_estimator.jl` limits to 5 categories automatically.

### 8.4 Installing Packages Manually

If the automatic installation fails (e.g., in a restricted network environment):

```bash
# Start Julia REPL
julia --project=.

# In the REPL, press ] to enter Pkg mode:
] add DataFrames CSV JSON GLM Distributions StatsBase CategoricalArrays Optim ForwardDiff
] add LinearAlgebra Statistics Random Dates Printf Test
```

---

## Appendix: File Reference

| File | Purpose | Key Functions |
|------|---------|---------------|
| `src/NavegadorBridge.jl` | Module entry point | All exports |
| `src/gamma_nmi.jl` | γ and NMI | `goodman_kruskal_gamma`, `normalized_mutual_information` |
| `src/cronbach.jl` | Scale helpers | `cronbach_alpha`, `scale_to_output`, `reverse_code`, `build_construct_scale` |
| `src/ordinal_model.jl` | PO ordered logit | `fit_ordered_logit`, `predict_proba`, `fit_logistic`, `predict_logistic` |
| `src/ses_encoder.jl` | SES encoding | `encode_ses`, `drop_sentinel_rows`, `is_sentinel`, `SES_VARS` |
| `src/dr_estimator.jl` | DR bridge | `dr_estimate`, `DRResult` |
| `src/sweep.jl` | Batch sweep | `run_sweep`, `load_checkpoint`, `save_checkpoint` |
| `test/runtests.jl` | 66 unit tests | All public functions |
| `examples/demo_dr.jl` | Demo (4.7s) | End-to-end synthetic data run |
