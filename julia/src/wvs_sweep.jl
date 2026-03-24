# wvs_sweep.jl — WVS multi-context DR sweep
#
# Three sweep modes:
#   :within        — γ for all pairs within each context CSV (same respondents)
#   :cross_context — γ across two context CSVs (e.g., W3_MEX vs W7_MEX)
#   :cross_dataset — γ between WVS context CSV and los_mex domain CSV
#
# For :within mode (the primary use case), both constructs come from the same
# DataFrame — unlike the los_mex sweep where each domain is a separate survey.
# The existing dr_estimate(df_a, col_a, df_b, col_b) handles this naturally:
# when df_a === df_b, the propensity model separates "respondent answered A"
# from "respondent answered B" even though they're the same individuals.
#
# Actually, for within-survey estimation with the SAME respondents, we can
# still use dr_estimate because it creates synthetic cross-dataset structure
# via the SES simulation. The key difference: both outcome columns come from
# the same DataFrame, so there's no cross-dataset sampling uncertainty.

using DataFrames
using CSV
using JSON
using Dates
using Statistics: median, quantile
using Printf
using Base.Threads


"""
    run_wvs_sweep(contexts_dir, pairs_csv, manifest_path, output_json;
                  n_sim, n_bootstrap, context_filter, resume, save_every)

Multi-threaded WVS within-survey sweep.

For each context (wave×country CSV), runs dr_estimate on all pairs where
both constructs are present. Results are keyed as "context::var_a::var_b".

# Arguments
  contexts_dir : directory containing per-context CSVs
  pairs_csv    : CSV with var_a, var_b columns (superset of all pairs)
  manifest_path: JSON manifest {context_key: {csv_path, constructs, ...}}
  output_json  : output path for results JSON

# Keyword arguments
  n_sim        : SES reference population size (default 2000)
  n_bootstrap  : bootstrap iterations (default 200)
  context_filter: list of context keys to process (default: all)
  resume       : skip already-computed pairs (default true)
  save_every   : checkpoint frequency (default 10)
"""
function run_wvs_sweep(
    pairs_csv     :: String,
    manifest_path :: String,
    output_json   :: String;
    n_sim         :: Int  = 2000,
    n_bootstrap   :: Int  = 200,
    context_filter:: Vector{String} = String[],
    resume        :: Bool = true,
    save_every    :: Int  = 10,
)
    t0 = time()
    println("=" ^ 70)
    println("NavegadorBridge — WVS Within-Survey Sweep")
    println("=" ^ 70)
    @printf("  pairs_csv:    %s\n", pairs_csv)
    @printf("  manifest:     %s\n", manifest_path)
    @printf("  output_json:  %s\n", output_json)
    @printf("  n_sim=%d  n_bootstrap=%d\n\n", n_sim, n_bootstrap)

    # Load manifest
    manifest = JSON.parsefile(manifest_path)
    contexts_to_run = if isempty(context_filter)
        collect(keys(manifest))
    else
        context_filter
    end
    sort!(contexts_to_run)

    @printf("  Contexts: %d\n", length(contexts_to_run))

    # Load pairs
    pairs_df = CSV.read(pairs_csv, DataFrame)
    @printf("  Total pair templates: %d\n", nrow(pairs_df))

    # Resume
    existing = Dict{String,Any}()
    skipped_existing = Dict{String,Any}()
    if resume && isfile(output_json)
        prev = load_checkpoint(output_json)
        existing = get(prev, "estimates", Dict())
        skipped_existing = get(prev, "skipped", Dict())
        @printf("  Resuming: %d estimates + %d skipped already computed\n",
                length(existing), length(skipped_existing))
    end

    metadata = Dict(
        "n_sim"       => n_sim,
        "n_bootstrap" => n_bootstrap,
        "ses_vars"    => ["sexo","edad","escol","Tam_loc"],
        "sweep_type"  => "within",
    )
    results = Dict{String,Any}(existing)
    skipped = Dict{String,Any}(skipped_existing)

    # Process each context sequentially (pairs within each context in parallel)
    for ctx_key in contexts_to_run
        ctx_info = get(manifest, ctx_key, nothing)
        if isnothing(ctx_info)
            @warn "Context $ctx_key not in manifest, skipping"
            continue
        end

        csv_path = ctx_info["csv_path"]
        if !isfile(csv_path)
            @warn "CSV not found: $csv_path"
            continue
        end

        println("\n" * ("─" ^ 60))
        @printf("Context: %s\n", ctx_key)
        t_ctx = time()

        df = CSV.read(csv_path, DataFrame; missingstring=["", "NA", "NaN", "nan"])
        @printf("  Rows: %d  Cols: %d\n", nrow(df), ncol(df))

        # Available construct columns in this context
        available_cols = Set(string.(propertynames(df)))

        # Build todo list: pairs where both constructs are available
        todo = NamedTuple{(:var_a, :var_b, :pair_idx), Tuple{String,String,Int}}[]
        for (i, row) in enumerate(eachrow(pairs_df))
            va = string(row.var_a)
            vb = string(row.var_b)

            # Extract column name from "wvs_agg_name|WVS_X" format
            col_a = split(va, "|")[1]
            col_b = split(vb, "|")[1]

            # Both columns must exist in this context's DataFrame
            if col_a ∉ available_cols || col_b ∉ available_cols
                continue
            end

            # Check if already computed
            full_key = "$(ctx_key)::$(va)::$(vb)"
            if haskey(results, full_key) || haskey(skipped, full_key)
                continue
            end

            push!(todo, (var_a=va, var_b=vb, pair_idx=i))
        end

        n_todo = length(todo)
        @printf("  Pairs to compute: %d\n", n_todo)

        if n_todo == 0
            @printf("  All pairs done or unavailable, skipping\n")
            continue
        end

        # Threading setup
        lk     = ReentrantLock()
        n_done = Ref(0)
        n_err  = Ref(0)
        gammas = Float64[]

        @printf("  Threads: %d\n", Threads.nthreads())

        Threads.@threads :dynamic for item in todo
            var_a    = item.var_a
            var_b    = item.var_b
            pair_idx = item.pair_idx

            parts_a = split(var_a, "|")
            parts_b = split(var_b, "|")
            col_a   = Symbol(parts_a[1])
            col_b   = Symbol(parts_b[1])

            entry = Dict{String,Any}()

            try
                # Within-survey: both columns from the same DataFrame
                # Use a unique seed combining context hash and pair index
                ctx_hash = Int(hash(ctx_key) % UInt(10000))
                seed = ctx_hash * 10000 + pair_idx

                r = dr_estimate(df, col_a, df, col_b;
                                n_sim=n_sim, n_bootstrap=n_bootstrap,
                                seed=seed)
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
                full_key = "$(ctx_key)::$(var_a)::$(var_b)"

                if haskey(entry, "error")
                    skipped[full_key] = entry["error"]
                    n_err[] += 1
                else
                    results[full_key] = entry
                    push!(gammas, entry["dr_gamma"])
                end

                n_done[] += 1
                done = n_done[]

                if done % save_every == 0
                    _save_wvs_checkpoint(results, skipped, metadata, output_json)
                end

                if done % 25 == 0
                    elapsed = time() - t_ctx
                    rate    = done / max(elapsed, 1e-6)
                    remain  = (n_todo - done) / max(rate, 1e-6)
                    @printf("    [%d/%d] done=%d err=%d  %.1f/s  ETA=%.0fs\n",
                        done, n_todo, done, n_err[], rate, remain)
                end
            end
        end

        # Context summary
        ctx_elapsed = time() - t_ctx
        @printf("  Context %s done in %.1fs (%d ok, %d err)\n",
                ctx_key, ctx_elapsed, n_done[] - n_err[], n_err[])
    end

    # Final save
    _save_wvs_checkpoint(results, skipped, metadata, output_json)

    elapsed = time() - t0
    println("\n" * ("=" ^ 70))
    @printf("WVS sweep complete in %.1fs (%.2f hours)\n", elapsed, elapsed/3600)
    @printf("  Estimates: %d  Skipped: %d\n", length(results), length(skipped))
    if !isempty(results)
        all_gammas = [v["dr_gamma"] for (_, v) in results if haskey(v, "dr_gamma")]
        if !isempty(all_gammas)
            @printf("  Median |gamma|: %.4f\n", median(abs.(all_gammas)))
            n_sig = count(v -> get(v, "excl_zero", false), values(results))
            @printf("  Significant (CI excl 0): %d (%.1f%%)\n",
                    n_sig, 100 * n_sig / length(results))
        end
    end

    return results
end


"""Atomic save for WVS sweep (includes skipped dict)."""
function _save_wvs_checkpoint(results::Dict, skipped::Dict, metadata::Dict, path::String)
    output = Dict(
        "metadata"  => merge(metadata, Dict("timestamp" => string(now()))),
        "estimates" => results,
        "skipped"   => skipped,
    )
    tmp = path * ".tmp"
    mkpath(dirname(abspath(path)))
    open(tmp, "w") do f
        JSON.print(f, output, 2)
    end
    mv(tmp, path; force=true)
end
