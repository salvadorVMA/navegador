# run_wvs_temporal.jl — Phase 3.2: Temporal sweep (Mexico, waves 1-7)
#
# Estimates γ for all construct pairs within each Mexico wave.
# 7 waves × ~800 pairs avg × ~4s/pair / 8 threads ≈ ~50 min
#
# Construct availability drops in earlier waves (W7: ~56, W1-4: ~15-25).
# Only pairs where both constructs are present in a wave are estimated.
#
# Run:
#   export PATH="$HOME/.juliaup/bin:$PATH"
#   julia -t 8 --project=. scripts/run_wvs_temporal.jl

using NavegadorBridge
using DataFrames
using CSV
using JSON
using Printf
using Dates

# ── Paths ────────────────────────────────────────────────────────────────────
const JULIA_DIR    = dirname(dirname(@__FILE__))
const ROOT         = dirname(JULIA_DIR)
const NAV_ROOT     = joinpath(dirname(ROOT), "navegador")
const WVS_DATA_DIR = joinpath(NAV_ROOT, "data", "julia_bridge_wvs")
const PAIRS_CSV    = joinpath(WVS_DATA_DIR, "wvs_pairs.csv")
const MANIFEST     = joinpath(WVS_DATA_DIR, "wvs_manifest.json")
const OUTPUT_DIR   = joinpath(NAV_ROOT, "data", "results")
const OUTPUT_JSON  = joinpath(OUTPUT_DIR, "wvs_temporal_sweep_mex.json")

println("=" ^ 70)
println("NavegadorBridge — WVS Temporal Sweep (Mexico, all waves)")
println("=" ^ 70)
println("Start: $(now())")
println()

if !isfile(PAIRS_CSV)
    error("Pairs CSV not found: $PAIRS_CSV\nRun build+export pipeline first.")
end
if !isfile(MANIFEST)
    error("Manifest not found: $MANIFEST\nRun build+export pipeline first.")
end

# Filter to Mexico contexts only (all waves)
manifest = JSON.parsefile(MANIFEST)
mex_contexts = sort([k for k in keys(manifest) if endswith(k, "_MEX")])
@printf("Mexico waves: %d\n\n", length(mex_contexts))

for ctx in mex_contexts
    info = manifest[ctx]
    @printf("  %-15s  %5d rows  %2d constructs\n",
            ctx, info["n_rows"], info["n_constructs"])
end
println()

# ── Run sweep ────────────────────────────────────────────────────────────────
t_start = time()

results = run_wvs_sweep(
    PAIRS_CSV,
    MANIFEST,
    OUTPUT_JSON;
    n_sim        = 2000,
    n_bootstrap  = 200,
    context_filter = mex_contexts,
    resume       = true,
    save_every   = 10,
)

t_total = time() - t_start
println()
println("=" ^ 70)
@printf("TIMING:  %.1f seconds  (%.2f hours)\n", t_total, t_total/3600)
println("End: $(now())")
println("Output: $OUTPUT_JSON")
println("=" ^ 70)
