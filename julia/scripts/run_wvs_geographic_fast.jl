# run_wvs_geographic_fast.jl — Flat-parallel geographic sweep
#
# Unlike the original (sequential per-country, parallel within), this
# flattens ALL (country, pair) combos into one thread pool.
# When one country's pairs finish early, threads immediately pick up
# another country's pairs — no idle time between countries.
#
# Resume: reads existing checkpoint, skips already-computed pairs.
#
# Run:
#   export PATH="$HOME/.juliaup/bin:$PATH"
#   julia -t 8 --project=. scripts/run_wvs_geographic_fast.jl

using NavegadorBridge
using DataFrames
using CSV
using JSON
using Printf
using Dates
using Statistics: median
using Base.Threads

const JULIA_DIR    = dirname(dirname(@__FILE__))
const ROOT         = dirname(JULIA_DIR)
const NAV_ROOT     = joinpath(dirname(ROOT), "navegador")
const WVS_DATA_DIR = joinpath(NAV_ROOT, "data", "julia_bridge_wvs")
const PAIRS_CSV    = joinpath(WVS_DATA_DIR, "wvs_pairs.csv")
const MANIFEST     = joinpath(WVS_DATA_DIR, "wvs_manifest.json")
const OUTPUT_DIR   = joinpath(NAV_ROOT, "data", "results")
const OUTPUT_JSON  = joinpath(OUTPUT_DIR, "wvs_geographic_sweep_w7.json")

const N_SIM       = 2000
const N_BOOTSTRAP = 200
const SAVE_EVERY  = 50

println("=" ^ 70)
println("NavegadorBridge — FAST Geographic Sweep (flat-parallel)")
println("=" ^ 70)
println("Start: $(now())")
println("Threads: $(Threads.nthreads())")
println()

# ── Load manifest + pairs ────────────────────────────────────────────────────
manifest = JSON.parsefile(MANIFEST)
w7_contexts = sort([k for k in keys(manifest) if startswith(k, "WVS_W7_")])
pairs_df = CSV.read(PAIRS_CSV, DataFrame)
@printf("Contexts: %d  Pair templates: %d\n\n", length(w7_contexts), nrow(pairs_df))

# ── Load all CSVs into memory ────────────────────────────────────────────────
println("Loading all country CSVs...")
t_load = time()
context_dfs = Dict{String, DataFrame}()
for ctx_key in w7_contexts
    csv_path = manifest[ctx_key]["csv_path"]
    if isfile(csv_path)
        context_dfs[ctx_key] = CSV.read(csv_path, DataFrame;
                                         missingstring=["", "NA", "NaN", "nan"])
    end
end
@printf("Loaded %d contexts in %.1fs\n\n", length(context_dfs), time() - t_load)

# ── Resume from checkpoint ───────────────────────────────────────────────────
existing_est = Dict{String,Any}()
existing_skip = Dict{String,Any}()
if isfile(OUTPUT_JSON)
    prev = JSON.parsefile(OUTPUT_JSON)
    existing_est  = get(prev, "estimates", Dict())
    existing_skip = get(prev, "skipped", Dict())
    @printf("Resuming: %d estimates + %d skipped\n", length(existing_est), length(existing_skip))
end

# ── Build flat todo list: ALL (context, pair) combos ─────────────────────────
# This is the key change: instead of looping contexts then threading pairs,
# we create one flat list and thread across EVERYTHING.
println("Building flat todo list...")
todo = NamedTuple{(:ctx, :var_a, :var_b, :idx), Tuple{String,String,String,Int}}[]
pair_counter = Ref(0)

for ctx_key in sort(collect(keys(context_dfs)))
    df = context_dfs[ctx_key]
    available_cols = Set(string.(propertynames(df)))

    for row in eachrow(pairs_df)
        va = string(row.var_a)
        vb = string(row.var_b)
        col_a = split(va, "|")[1]
        col_b = split(vb, "|")[1]

        # Both columns must exist
        col_a ∉ available_cols && continue
        col_b ∉ available_cols && continue

        full_key = "$(ctx_key)::$(va)::$(vb)"
        haskey(existing_est, full_key) && continue
        haskey(existing_skip, full_key) && continue

        pair_counter[] += 1
        push!(todo, (ctx=ctx_key, var_a=va, var_b=vb, idx=pair_counter[]))
    end
end

n_todo = length(todo)
n_already = length(existing_est) + length(existing_skip)
@printf("Already done: %d  Remaining: %d  Total: %d\n\n", n_already, n_todo, n_already + n_todo)

if n_todo == 0
    println("Nothing to do — all pairs computed.")
    exit(0)
end

# ── Shared state ─────────────────────────────────────────────────────────────
results  = Dict{String,Any}(existing_est)
skipped  = Dict{String,Any}(existing_skip)
lk       = ReentrantLock()
n_done   = Ref(0)
n_err    = Ref(0)
gammas   = Float64[]
t0       = time()

metadata = Dict(
    "n_sim"       => N_SIM,
    "n_bootstrap" => N_BOOTSTRAP,
    "ses_vars"    => ["sexo","edad","escol","Tam_loc"],
    "sweep_type"  => "within",
    "parallel"    => "flat",
)

# ── Atomic save ──────────────────────────────────────────────────────────────
function _save()
    output = Dict(
        "metadata"  => merge(metadata, Dict("timestamp" => string(now()))),
        "estimates" => results,
        "skipped"   => skipped,
    )
    tmp = OUTPUT_JSON * ".tmp"
    mkpath(dirname(abspath(OUTPUT_JSON)))
    open(tmp, "w") do f
        JSON.print(f, output, 2)
    end
    mv(tmp, OUTPUT_JSON; force=true)
end

# ── Flat-parallel main loop ──────────────────────────────────────────────────
println("Starting flat-parallel sweep...")
Threads.@threads :dynamic for item in todo
    ctx_key  = item.ctx
    var_a    = item.var_a
    var_b    = item.var_b
    pair_idx = item.idx

    df = context_dfs[ctx_key]
    col_a = Symbol(split(var_a, "|")[1])
    col_b = Symbol(split(var_b, "|")[1])

    entry = Dict{String,Any}()
    full_key = "$(ctx_key)::$(var_a)::$(var_b)"

    try
        ctx_hash = Int(hash(ctx_key) % UInt(10000))
        seed = ctx_hash * 10000 + pair_idx

        r = dr_estimate(df, col_a, df, col_b;
                        n_sim=N_SIM, n_bootstrap=N_BOOTSTRAP, seed=seed)
        ci_w = r.gamma_ci_hi - r.gamma_ci_lo
        entry = Dict(
            "dr_gamma"  => round(r.gamma,        digits=4),
            "dr_ci_lo"  => round(r.gamma_ci_lo,  digits=4),
            "dr_ci_hi"  => round(r.gamma_ci_hi,  digits=4),
            "dr_nmi"    => round(r.nmi,          digits=4),
            "dr_v"      => round(r.cramers_v,    digits=4),
            "dr_ks"     => round(r.ks_overlap,   digits=4),
            "ci_width"  => round(ci_w,           digits=4),
            "excl_zero" => r.gamma_ci_lo > 0.0 || r.gamma_ci_hi < 0.0,
            "n_a"       => r.n_a,
            "n_b"       => r.n_b,
            "context"   => ctx_key,
        )
    catch e
        entry["error"] = string(e)
        entry["context"] = ctx_key
    end

    lock(lk) do
        if haskey(entry, "error")
            skipped[full_key] = entry["error"]
            n_err[] += 1
        else
            results[full_key] = entry
            push!(gammas, entry["dr_gamma"])
        end

        n_done[] += 1
        done = n_done[]

        if done % SAVE_EVERY == 0
            _save()
        end

        if done % 100 == 0
            elapsed = time() - t0
            rate    = done / max(elapsed, 1e-6)
            remain  = (n_todo - done) / max(rate, 1e-6)
            total   = done + n_already
            @printf("  [%d/%d] +%d new (err=%d) %.1f/s ETA=%.0fs (%.1fmin)\n",
                total, n_already + n_todo, done, n_err[], rate, remain, remain/60)
        end
    end
end

# ── Final save ───────────────────────────────────────────────────────────────
_save()
elapsed = time() - t0

println("\n" * ("=" ^ 70))
@printf("Flat-parallel sweep complete in %.1fs (%.2f hours)\n", elapsed, elapsed/3600)
@printf("  New estimates: %d  New skipped: %d\n", n_done[] - n_err[], n_err[])
@printf("  Total estimates: %d  Total skipped: %d\n", length(results), length(skipped))
if !isempty(gammas)
    @printf("  Median |gamma|: %.4f\n", median(abs.(gammas)))
    n_sig = count(v -> get(v, "excl_zero", false), values(results))
    @printf("  Significant: %d (%.1f%%)\n", n_sig, 100 * n_sig / length(results))
end
println("End: $(now())")
println("Output: $OUTPUT_JSON")
println("=" ^ 70)
