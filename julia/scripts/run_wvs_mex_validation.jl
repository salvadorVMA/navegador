# run_wvs_mex_validation.jl — Phase 1.1: WVS Mexico W7 within-survey sweep
#
# Estimates γ for all cross-domain construct pairs within WVS Wave 7 Mexico.
# Same respondents answer all questions → "gold standard" (no cross-dataset noise).
#
# Run:
#   export PATH="$HOME/.juliaup/bin:$PATH"
#   julia -t 8 --project=. scripts/run_wvs_mex_validation.jl
#
# Expected: ~1271 pairs × ~4s/pair / 8 threads ≈ ~10-15 min

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
const OUTPUT_JSON  = joinpath(OUTPUT_DIR, "wvs_mex_w7_within_sweep.json")

println("=" ^ 70)
println("NavegadorBridge — WVS Mexico W7 Within-Survey Sweep (Phase 1.1)")
println("=" ^ 70)
println("Start: $(now())")
println()
@printf("  Pairs CSV:  %s\n", PAIRS_CSV)
@printf("  Manifest:   %s\n", MANIFEST)
@printf("  Output:     %s\n", OUTPUT_JSON)
println()

# Verify files exist
if !isfile(PAIRS_CSV)
    error("Pairs CSV not found: $PAIRS_CSV\nRun export_wvs_for_julia.py first.")
end
if !isfile(MANIFEST)
    error("Manifest not found: $MANIFEST\nRun export_wvs_for_julia.py first.")
end

# ── Run sweep (Mexico W7 only) ──────────────────────────────────────────────
t_start = time()

results = run_wvs_sweep(
    PAIRS_CSV,
    MANIFEST,
    OUTPUT_JSON;
    n_sim        = 2000,
    n_bootstrap  = 200,
    context_filter = ["WVS_W7_MEX"],
    resume       = true,
    save_every   = 10,
)

t_total = time() - t_start
println()
println("=" ^ 70)
@printf("TIMING:  %.1f seconds  (%.2f hours)\n", t_total, t_total/3600)
@printf("         %.1f seconds per pair average\n", t_total / max(length(results), 1))
println("End: $(now())")
println("Output: $OUTPUT_JSON")
println("=" ^ 70)
