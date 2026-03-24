# run_wvs_geographic.jl — Phase 2.2: Geographic sweep (Wave 7, all countries)
#
# Estimates γ for all construct pairs within each Wave 7 country.
# ~60 countries × ~1200 pairs × ~4s/pair / 8 threads ≈ ~10 hours
#
# Run:
#   export PATH="$HOME/.juliaup/bin:$PATH"
#   julia -t 8 --project=. scripts/run_wvs_geographic.jl
#
# Checkpoint: saves after every 10 pairs, resume-friendly.

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
const OUTPUT_JSON  = joinpath(OUTPUT_DIR, "wvs_geographic_sweep_w7.json")

println("=" ^ 70)
println("NavegadorBridge — WVS Geographic Sweep (Wave 7, all countries)")
println("=" ^ 70)
println("Start: $(now())")
println()

if !isfile(PAIRS_CSV)
    error("Pairs CSV not found: $PAIRS_CSV\nRun build+export pipeline first.")
end
if !isfile(MANIFEST)
    error("Manifest not found: $MANIFEST\nRun build+export pipeline first.")
end

# Filter to Wave 7 contexts only
manifest = JSON.parsefile(MANIFEST)
w7_contexts = sort([k for k in keys(manifest) if startswith(k, "WVS_W7_")])
@printf("Wave 7 countries: %d\n\n", length(w7_contexts))

for ctx in w7_contexts
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
    context_filter = w7_contexts,
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
