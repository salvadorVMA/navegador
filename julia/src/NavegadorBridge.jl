# NavegadorBridge.jl — Julia bridge estimator for Navegador
#
# Julia port of the Python DoublyRobust bridge pipeline from ses_regression.py.
#
# ── Module system in Julia ────────────────────────────────────────────────────
# A Julia `module` is a namespace boundary.  Unlike Python packages, a module:
#   - is defined in a single file (which can `include` other files into the
#     same namespace — see below)
#   - is activated with `using NavegadorBridge` (imports all exported names) or
#     `import NavegadorBridge` (imports only the module name itself)
#   - uses `export` to declare the public API.  Unexported symbols are still
#     reachable as `NavegadorBridge.internal_fn` but won't pollute the caller's
#     namespace when `using` is invoked.
#
# ── Dependency graph ──────────────────────────────────────────────────────────
#
#   dr_estimator.jl  ←  ordinal_model.jl  ←  (Optim, ForwardDiff)
#        ↑                                ↑
#   gamma_nmi.jl               ses_encoder.jl
#        ↑
#   cronbach.jl
#        ↑
#   sweep.jl  ←  (CSV, JSON, Dates)
#
# All files share the same module scope: a function in `gamma_nmi.jl` can call
# a function in `ses_encoder.jl` because both are `include`d into NavegadorBridge
# before any caller runs.

module NavegadorBridge

# ── Standard library modules ──────────────────────────────────────────────────
# Julia's standard library is split into sub-packages that must be explicitly
# loaded even though they ship with every Julia installation.
#
# `using Foo` brings all of Foo's exports into scope.
# `using Foo: bar, baz` brings only those names (more precise, avoids clashes).
#
# Python analogue:
#   using DataFrames   ≈   from pandas import DataFrame, nrow, dropmissing ...
#   using Statistics   ≈   from statistics import mean, var
#   using LinearAlgebra≈   from numpy.linalg import dot, norm

using DataFrames      # pandas equivalent — DataFrame, nrow, dropmissing, filter, select
using Statistics      # mean, var, quantile, median (standard library)
using LinearAlgebra   # dot, norm, cholesky (standard library)
using Random          # rand, MersenneTwister, AbstractRNG (standard library)
using Distributions   # Normal, Categorical, Binomial — probability distributions
using StatsBase       # describe, countmap, sample — general stats utilities
using GLM             # GeneralizedLinearModel (available but not used for ordered logit)
using Optim           # Numerical optimization: LBFGS, NelderMead, Brent, etc.
using ForwardDiff     # Automatic differentiation: exact gradients via dual numbers
using JSON            # JSON parsing and serialization
using CSV             # Fast CSV reading/writing
using Printf          # @printf, @sprintf — C-style formatted output

# ── Source files ──────────────────────────────────────────────────────────────
# `include(path)` inserts the contents of `path` into the current module scope.
# This is NOT like Python's `import` — it is textual inclusion that shares the
# module's variable/type/function namespace.  Order matters: types used by
# later files must be defined first.

include("gamma_nmi.jl")     # Step 1: pure math functions, no dependencies
include("cronbach.jl")      # Step 2: scale helpers, depends on Statistics only
include("ordinal_model.jl") # Step 3: PO model, depends on Optim + ForwardDiff
include("ses_encoder.jl")   # Step 4: SES encoding, depends on DataFrames
include("dr_estimator.jl")  # Step 5: DR estimator, depends on all of the above
include("sweep.jl")         # Step 6: batch sweep, depends on dr_estimator + CSV/JSON
include("wvs_sweep.jl")    # Step 7: WVS multi-context sweep (within/cross modes)

# ── Public API ────────────────────────────────────────────────────────────────
# `export` makes these symbols available with bare names after `using NavegadorBridge`.
# Unexported symbols (e.g. `_fit_outcome_model`) remain accessible as
# `NavegadorBridge._fit_outcome_model` but are considered internal/private.
# Python analogue: `__all__` in a package's `__init__.py`.

export goodman_kruskal_gamma, normalized_mutual_information
export cronbach_alpha, scale_to_output, reverse_code, build_construct_scale
export fit_ordered_logit, predict_proba, fit_logistic, predict_logistic
export encode_ses, drop_sentinel_rows, is_sentinel, SES_VARS
export DRResult, dr_estimate
export run_sweep, load_checkpoint, save_checkpoint
export run_wvs_sweep

end # module NavegadorBridge
