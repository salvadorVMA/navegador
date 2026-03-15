# run_v5_sweep.jl — Julia v4 replication of Python v5 construct sweep
#
# V4 changes vs V3:
#   - _rank_normalize: rank-transform outcome before binning (proposal 3)
#     Converts any distribution to uniform [1,10] before qcut.
#     Eliminates near-separation even for extreme constructs like
#     household_science_cultural_capital (mean≈9.0) — now always K=5
#     equal-frequency bins regardless of skew.
#   - K<3 guard raised from K<2: degenerate constructs (floor/ceiling
#     effects collapsing to 1-2 bins) now raise an error → recorded as
#     skipped in JSON rather than producing misleading γ≈0 results.
#
# V3 changes vs V2:
#   - _find_bin: returns integer bin INDEX (1..K) instead of edge value.
#     Fixes K=6 bug (spurious 6th category for min/max observations).
#
# V2 changes vs V1:
#   - _bin_to_5: equal-frequency quantile binning (matches Python pd.qcut)
#   - Optimizer: NewtonTrustRegion (primary) + LBFGS (fallback)
#
# Run (multi-threaded, recommended):
#   export PATH="$HOME/.juliaup/bin:$PATH"
#   julia -t 8 --project=. scripts/run_v5_sweep.jl
#
# Expected time: ~40-45 min (8 threads).
# Rank normalization guarantees K=5 on every pair → faster bootstrap
# convergence → slightly faster than v3.

using NavegadorBridge
using DataFrames
using CSV
using JSON
using Printf
using Dates

# ── Paths ─────────────────────────────────────────────────────────────────────
const JULIA_DIR  = dirname(dirname(@__FILE__))           # navegador_julia_bridge/julia/
const ROOT       = dirname(JULIA_DIR)                    # navegador_julia_bridge/
const DATA_ROOT  = joinpath(dirname(ROOT), "navegador", "data", "julia_bridge")
const PAIRS_CSV  = joinpath(DATA_ROOT, "v5_pairs.csv")
const MANIFEST   = joinpath(DATA_ROOT, "manifest.json")
const OUTPUT_DIR = joinpath(dirname(ROOT), "navegador", "data", "results")
const OUTPUT_JSON = joinpath(OUTPUT_DIR, "construct_dr_sweep_v5_julia_v4.json")

println("=" ^ 70)
println("NavegadorBridge — V5 Construct Sweep (Julia v4: rank-norm + K<3 guard)")
println("=" ^ 70)
println("Start: $(now())")
println()
@printf("  Pairs CSV:  %s\n", PAIRS_CSV)
@printf("  Output:     %s\n", OUTPUT_JSON)
println()

# ── Data loader ────────────────────────────────────────────────────────────────
# Reads the manifest.json (domain -> CSV path) and loads each CSV into a DataFrame.
# Called once before the sweep begins.
function load_survey_data()::Dict{String, DataFrame}
    println("Loading domain CSVs from manifest...")
    t0 = time()

    manifest = JSON.parsefile(MANIFEST)
    domain_dfs = Dict{String, DataFrame}()

    for (domain, csv_path) in manifest
        if isfile(csv_path)
            df = CSV.read(csv_path, DataFrame; missingstring=["", "NA", "NaN", "nan"])
            domain_dfs[domain] = df
            n_agg = sum(1 for col in propertynames(df) if startswith(string(col), "agg_"))
            @printf("  %-5s  %5d rows  %d constructs\n", domain, nrow(df), n_agg)
        else
            @warn "CSV not found: $csv_path"
        end
    end

    elapsed = time() - t0
    @printf("\n  %d domains loaded in %.1fs\n\n", length(domain_dfs), elapsed)
    return domain_dfs
end

# ── Run sweep ──────────────────────────────────────────────────────────────────
t_start = time()

results = run_sweep(
    PAIRS_CSV,
    OUTPUT_JSON;
    data_loader  = load_survey_data,
    n_sim        = 2000,
    n_bootstrap  = 200,
    resume       = false,    # fresh run: v3 is a different estimator
    save_every   = 10,       # save checkpoint every 10 pairs (reduce I/O)
)

t_total = time() - t_start
println()
println("=" ^ 70)
@printf("TIMING:  %.1f seconds  (%.2f hours)\n", t_total, t_total/3600)
@printf("         %.1f seconds per pair average\n", t_total / max(length(results), 1))
println("End: $(now())")
println("Output: $OUTPUT_JSON")
println("=" ^ 70)
