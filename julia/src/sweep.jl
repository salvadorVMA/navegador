"""
    sweep.jl — DR sweep over construct pairs with atomic checkpointing

Mirrors sweep_construct_dr.py. Reads a CSV of construct pairs,
runs dr_estimate on each, saves results atomically to JSON.
Supports resume (skips already-computed pairs).
"""

using DataFrames
using CSV
using JSON
using Dates
using Statistics: median, quantile
using Printf


"""Load checkpoint JSON; return empty Dict on failure."""
function load_checkpoint(path::String)::Dict{String,Any}
    isfile(path) || return Dict{String,Any}()
    try
        return JSON.parsefile(path)
    catch e
        @warn "Could not load checkpoint: $e"
        return Dict{String,Any}()
    end
end


"""Atomic save: write to .tmp then rename."""
function save_checkpoint(results::Dict, metadata::Dict, path::String)
    output = Dict(
        "metadata"  => merge(metadata, Dict("timestamp" => string(now()))),
        "estimates" => results,
    )
    tmp = path * ".tmp"
    mkpath(dirname(abspath(path)))
    open(tmp, "w") do f
        JSON.print(f, output, 2)
    end
    mv(tmp, path; force=true)
end


"""Pair deduplication key."""
_pair_id(a::AbstractString, b::AbstractString) = "$(a)::$(b)"


"""
    run_sweep(pairs_csv, output_json; data_loader, n_sim, n_bootstrap, resume, save_every)

Batch DR sweep.

`data_loader` :: () -> Dict{String, DataFrame}
  Returns domain_code => DataFrame mapping (must include agg_* columns).

`pairs_csv` must have columns var_a, var_b in "agg_colname|DOMAIN" format.
"""
function run_sweep(
    pairs_csv   :: String,
    output_json :: String;
    data_loader :: Function = () -> Dict{String,DataFrame}(),
    n_sim       :: Int      = 2000,
    n_bootstrap :: Int      = 200,
    resume      :: Bool     = true,
    save_every  :: Int      = 1,
)
    t0 = time()
    println("=" ^ 70)
    println("Navegador Julia DR Sweep")
    println("=" ^ 70)
    @printf("  pairs_csv:   %s\n", pairs_csv)
    @printf("  output_json: %s\n", output_json)
    @printf("  n_sim=%d  n_bootstrap=%d\n\n", n_sim, n_bootstrap)

    pairs_df = CSV.read(pairs_csv, DataFrame)
    total    = nrow(pairs_df)
    @printf("  Total pairs: %d\n", total)

    println("Loading survey data...")
    domain_dfs = data_loader()

    existing = Dict{String,Any}()
    if resume && isfile(output_json)
        prev     = load_checkpoint(output_json)
        existing = get(prev, "estimates", Dict())
        @printf("  Resuming: %d pairs already computed\n", length(existing))
    end

    metadata = Dict(
        "n_sim"       => n_sim,
        "n_bootstrap" => n_bootstrap,
        "n_total"     => total,
        "ses_vars"    => ["sexo","edad","escol","Tam_loc"],
    )
    results = Dict{String,Any}(existing)
    n_done  = 0
    n_err   = 0
    gammas  = Float64[]

    for row in eachrow(pairs_df)
        var_a = string(row.var_a)
        var_b = string(row.var_b)
        key   = _pair_id(var_a, var_b)
        haskey(results, key) && continue

        parts_a  = split(var_a, "|")
        parts_b  = split(var_b, "|")
        col_a    = Symbol(parts_a[1])
        col_b    = Symbol(parts_b[1])
        domain_a = length(parts_a) > 1 ? parts_a[2] : ""
        domain_b = length(parts_b) > 1 ? parts_b[2] : ""

        df_a = get(domain_dfs, domain_a, nothing)
        df_b = get(domain_dfs, domain_b, nothing)
        entry = Dict{String,Any}()

        if isnothing(df_a) || isnothing(df_b)
            entry["error"] = "DataFrame not found: $domain_a or $domain_b"
        elseif col_a ∉ propertynames(df_a) || col_b ∉ propertynames(df_b)
            entry["error"] = "Column not found: $col_a or $col_b"
        else
            try
                r    = dr_estimate(df_a, col_a, df_b, col_b;
                                   n_sim=n_sim, n_bootstrap=n_bootstrap)
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
                )
                push!(gammas, r.gamma)
            catch e
                entry["error"] = string(e)
                n_err += 1
            end
        end

        results[key] = entry
        n_done += 1
        n_done % save_every == 0 && save_checkpoint(results, metadata, output_json)

        if n_done % 50 == 0
            elapsed = time() - t0
            rate    = n_done / elapsed
            remain  = (total - length(existing) - n_done) / max(rate, 1e-6)
            @printf("  [%d/%d] done=%d err=%d  %.1f/s  ETA=%.0fs\n",
                n_done + length(existing), total, n_done, n_err, rate, remain)
        end
    end

    save_checkpoint(results, metadata, output_json)
    elapsed = time() - t0
    @printf("\nSweep complete in %.1fs\n", elapsed)
    @printf("  Total: %d  Errors: %d\n", length(results), n_err)
    if !isempty(gammas)
        @printf("  Median |γ|: %.4f\n", median(abs.(gammas)))
        n_sig = count(k -> get(get(results, k, Dict()), "excl_zero", false), collect(keys(results)))
        @printf("  Significant (CI excl 0): %d\n", n_sig)
    end
    return results
end
