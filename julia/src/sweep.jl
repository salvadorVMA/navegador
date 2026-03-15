# sweep.jl — Multi-threaded DR sweep over construct pairs with atomic checkpointing
#
# Mirrors sweep_construct_dr.py.  Reads a CSV of construct pairs, runs
# dr_estimate on each pair in parallel, saves results atomically to JSON.
# Supports resume (skips already-computed pairs).
#
# ── Multi-threading design ────────────────────────────────────────────────────
# Julia's threading model:
#   - `julia -t N` (or `JULIA_NUM_THREADS=N`) spawns N OS threads.
#   - `Threads.@threads :dynamic for item in collection` distributes work
#     dynamically across all threads.  `:dynamic` (Julia 1.8+) schedules work
#     items lazily rather than statically splitting the range upfront —
#     better when individual pair costs vary (some pairs converge fast, others
#     hit the BFGS iteration limit).
#   - `Threads.nthreads()` reports how many threads are active at runtime.
#
# ── Thread safety ─────────────────────────────────────────────────────────────
# Three resources are shared across threads and must be protected:
#
#   results :: Dict         — written by every thread (one entry per pair)
#   gammas  :: Vector       — appended by every thread that succeeds
#   n_done, n_err :: Ref    — counters incremented by every thread
#
# Protection strategy: a single `ReentrantLock` guards all four.  The lock is
# held only for the Dict update + counter increment + optional checkpoint —
# the heavy `dr_estimate` computation runs OUTSIDE the lock, in parallel.
#
# `ReentrantLock` vs `SpinLock`:
#   - `SpinLock` is faster for very short critical sections (microseconds).
#   - `ReentrantLock` allows the same thread to re-acquire the lock (needed if
#     `save_checkpoint` ever calls back into locked code — defensive choice).
#   - With dr_estimate taking ~4s, the lock wait fraction is negligible.
#
# ── Why dr_estimate is thread-safe ───────────────────────────────────────────
# Each call to `dr_estimate(...; seed=N)` creates its own `MersenneTwister(N)`
# internally.  Julia's MersenneTwister is NOT thread-safe if shared, but since
# each call gets its own seeded instance there is no shared state.
# We use `seed = pair_idx` (the 1-based row index in the original pairs CSV)
# so results are reproducible regardless of thread execution order.
#
# ── `Ref(0)` — mutable scalar ─────────────────────────────────────────────────
# Julia's `Int` is immutable (like Python's `int`).  To mutate a counter inside
# a closure or across function calls, wrap it in `Ref{Int}`:
#   n = Ref(0)      # create a mutable box containing 0
#   n[] += 1        # read and update: `n[]` dereferences the Ref
# Python equivalent: `n = [0]; n[0] += 1` (mutable list trick) or
#   `n = {'v': 0}; n['v'] += 1`.
#
# ── Atomic save pattern ───────────────────────────────────────────────────────
# Writing JSON directly to the output file risks partial writes (truncated file)
# if the process is killed mid-write.  The atomic pattern is:
#   1. Write to `output.json.tmp`  (a temporary file)
#   2. `mv(tmp, output)`           (atomic rename on POSIX filesystems)
# Because rename is atomic, any reader of `output.json` sees either the
# complete old file or the complete new file — never a partial write.
#
# ── `Function` type ──────────────────────────────────────────────────────────
# `data_loader::Function` means the argument must be callable.
# `Function` is Julia's abstract type for all callable objects.
# Passing a function as an argument is idiomatic Julia; no special decorator
# or interface is needed (compare Python's `Callable` type hint).

using DataFrames
using CSV
using JSON
using Dates
using Statistics: median, quantile
using Printf
using Base.Threads


"""
    load_checkpoint(path::String) -> Dict{String, Any}

Load a JSON checkpoint file.  Returns an empty Dict on any failure (file not
found, malformed JSON, permission error).

# `isfile(path)`

Julia's built-in check for whether a regular file exists.  Returns false for
directories, symlinks to non-existent targets, or non-existent paths.

# `JSON.parsefile(path)`

Reads and parses the entire JSON file, returning a nested `Dict{String, Any}`.
`Any` is Julia's universal supertype (equivalent to `object` in Python).
Nested JSON objects become `Dict{String, Any}`; arrays become `Vector{Any}`.

# `@warn`

Julia's structured logging macro.  Prints a yellow warning with file/line info.
More informative than `println` for diagnostic messages.
Python equivalent: `logging.warning(...)`.
"""
function load_checkpoint(path::String)::Dict{String,Any}
    isfile(path) || return Dict{String,Any}()   # short-circuit: return empty dict if no file
    try
        return JSON.parsefile(path)
    catch e
        @warn "Could not load checkpoint: $e"
        return Dict{String,Any}()
    end
end


"""
    save_checkpoint(results, metadata, path)

Atomically save sweep results to a JSON file.

# `merge(d1, d2)`

Creates a new Dict combining d1 and d2 (d2 wins on key conflicts).
Python equivalent: `{**d1, **d2}`.

# `mkpath(dirname(abspath(path)))`

Creates all parent directories if they don't exist.
`dirname` extracts the directory component; `abspath` resolves relative paths.
Python equivalent: `os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)`.

# `open(path, "w") do f ... end`

Julia's resource management idiom: `open` with a `do` block guarantees the file
is closed even if an exception occurs.
Python equivalent: `with open(path, 'w') as f: ...`.

# `mv(src, dst; force=true)`

Rename/move file.  `force=true` overwrites `dst` if it exists.
On POSIX systems this is atomic when src and dst are on the same filesystem.
"""
function save_checkpoint(results::Dict, metadata::Dict, path::String)
    output = Dict(
        "metadata"  => merge(metadata, Dict("timestamp" => string(now()))),
        "estimates" => results,
    )
    tmp = path * ".tmp"   # string concatenation with *  (not + as in Python)
    mkpath(dirname(abspath(path)))
    open(tmp, "w") do f
        JSON.print(f, output, 2)   # 2 = indent level (pretty-print)
    end
    mv(tmp, path; force=true)   # atomic rename
end


"""
Pair deduplication key.  Same format as Python: "var_a::var_b"."""
_pair_id(a::AbstractString, b::AbstractString) = "$(a)::$(b)"
# String interpolation: `"$(expr)"` evaluates `expr` and inserts the result.
# Python equivalent: f"{a}::{b}".


"""
    run_sweep(pairs_csv, output_json; data_loader, n_sim, n_bootstrap, resume, save_every)

Multi-threaded batch DR sweep over all pairs in a CSV file.

Launch with `julia -t 8 --project=. scripts/run_v5_sweep.jl` for 8 threads.

# Arguments

  pairs_csv   : path to CSV with columns `var_a`, `var_b` in "agg_col|DOMAIN" format
  output_json : path for JSON output (same schema as Python v4/v5 sweep)

# Keyword arguments

  data_loader : `() -> Dict{String, DataFrame}` — loads domain DataFrames
  n_sim       : reference SES population size (default 2000)
  n_bootstrap : bootstrap iterations (default 200)
  resume      : if true, skip already-computed pairs (default true)
  save_every  : save checkpoint every N pairs (default 1 = after every pair)

# Threading model

  All pairs not yet in the checkpoint are collected into a `todo` Vector.
  `Threads.@threads :dynamic` distributes them across available threads.
  `dr_estimate` runs in the thread's own stack, fully parallel.
  A `ReentrantLock` serializes Dict updates, counter increments, and saves.
  Lock hold time is O(μs); dr_estimate takes O(seconds) — near-linear scaling.

# `data_loader` design

The data_loader is injected as a function rather than passed as a DataFrame
to allow lazy loading (data is loaded once, before the sweep begins).  This
mirrors the Python pattern where `dataset_knowledge.py` is loaded once and
the resulting `enc_dict` is passed around.

# `eachrow(df)`

Iterates over DataFrame rows as NamedTuple-like row objects.
`row.var_a` accesses the `var_a` field of each row.
Python equivalent: `for _, row in df.iterrows(): row['var_a']`.

# `haskey(results, key)`

Dict membership test.  Python equivalent: `key in results`.
Used for resume logic: if the pair key already exists in the checkpoint, skip it.

# `split(str, delimiter)`

Splits a string and returns a `Vector{SubString}`.
`parts_a[1]` is the column name; `parts_a[2]` is the domain code.
Python equivalent: `str.split('|')`.

# `Symbol(str)`

Converts a String to a Symbol (for DataFrame column access).
`df[!, :col_name]` requires a Symbol, not a String.
Python equivalent: no direct analogue — pandas uses strings for column names.

# `get(dict, key, default)`

Returns `dict[key]` if key exists, else `default`.  Does not raise an error.
Python equivalent: `dict.get(key, default)`.

# `@printf`

C-style formatted printing (exact width specifiers, no f-string).
Julia's `@printf` is a macro that generates efficient formatted output.
Python equivalent: `print(f"...")` or `printf`-style `print("... %d ..." % n)`.
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
    t0 = time()   # Unix timestamp as Float64 (seconds); `time() - t0` = elapsed seconds
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
    domain_dfs = data_loader()   # call the injected loader function

    # ── Resume: load existing results ─────────────────────────────────────────
    existing = Dict{String,Any}()
    if resume && isfile(output_json)
        prev     = load_checkpoint(output_json)
        existing = get(prev, "estimates", Dict())   # `get` with default = empty Dict
        @printf("  Resuming: %d pairs already computed\n", length(existing))
    end

    metadata = Dict(
        "n_sim"       => n_sim,
        "n_bootstrap" => n_bootstrap,
        "n_total"     => total,
        "ses_vars"    => ["sexo","edad","escol","Tam_loc"],
    )
    results = Dict{String,Any}(existing)   # start with existing, add new results to it

    # ── Build todo list (pairs not yet computed) ───────────────────────────────
    # Pre-collect all pending pairs into a Vector before launching threads.
    # Each element is a NamedTuple: (var_a, var_b, pair_idx).
    # `pair_idx` = 1-based row index in the original pairs CSV — used as the
    # RNG seed for dr_estimate so results are reproducible regardless of thread
    # execution order.
    #
    # Why pre-collect instead of filtering inside @threads?
    # `@threads` needs a concrete indexable collection to distribute work.
    # Computing the todo list upfront also makes `n_todo` available for ETA.
    todo = NamedTuple{(:var_a, :var_b, :pair_idx), Tuple{String,String,Int}}[]
    for (i, row) in enumerate(eachrow(pairs_df))
        key = _pair_id(string(row.var_a), string(row.var_b))
        haskey(results, key) || push!(todo, (var_a=string(row.var_a),
                                             var_b=string(row.var_b),
                                             pair_idx=i))
    end
    n_todo = length(todo)

    # ── Threading setup ────────────────────────────────────────────────────────
    # `Threads.nthreads()` returns the number of threads available at runtime.
    # Set by `julia -t N` or `JULIA_NUM_THREADS=N` at launch.
    @printf("  Threads: %d  Pending: %d\n\n", Threads.nthreads(), n_todo)

    # Shared mutable state — all protected by `lk`:
    lk     = ReentrantLock()    # mutual exclusion for Dict + counters + checkpoint
    n_done = Ref(0)             # `Ref{Int}` is a mutable box; `n_done[]` dereferences
    n_err  = Ref(0)
    gammas = Float64[]          # growing list of γ values (for final stats)

    # ── Multi-threaded main loop ───────────────────────────────────────────────
    # `Threads.@threads :dynamic` is a macro that transforms the for loop into
    # a parallel task distribution.  `:dynamic` (Julia 1.8+) schedules work
    # items dynamically — a thread that finishes early picks up the next item
    # rather than waiting for its pre-assigned block to complete.
    #
    # All variables captured from the outer scope (domain_dfs, n_sim, etc.) are
    # read-only from the threads' perspective.  Only `results`, `gammas`,
    # `n_done`, `n_err` are written — always under `lk`.
    Threads.@threads :dynamic for item in todo

        var_a    = item.var_a
        var_b    = item.var_b
        pair_idx = item.pair_idx   # used as RNG seed → reproducible results

        # Parse "agg_colname|DOMAIN" format.
        # This runs in the thread, no lock needed (read-only data).
        parts_a  = split(var_a, "|")
        parts_b  = split(var_b, "|")
        col_a    = Symbol(parts_a[1])   # column name as Symbol for DataFrame access
        col_b    = Symbol(parts_b[1])
        domain_a = length(parts_a) > 1 ? string(parts_a[2]) : ""
        domain_b = length(parts_b) > 1 ? string(parts_b[2]) : ""

        # `get(dict, key, nothing)` is thread-safe for reads on an immutable dict.
        # `domain_dfs` is built once before threading and never mutated.
        df_a = get(domain_dfs, domain_a, nothing)
        df_b = get(domain_dfs, domain_b, nothing)

        # ── Compute result (runs in parallel, no lock) ─────────────────────────
        entry = Dict{String,Any}()   # local to this thread iteration

        if isnothing(df_a) || isnothing(df_b)
            entry["error"] = "DataFrame not found: $domain_a or $domain_b"
        elseif col_a ∉ propertynames(df_a) || col_b ∉ propertynames(df_b)
            entry["error"] = "Column not found: $col_a or $col_b"
        else
            try
                # dr_estimate creates its own MersenneTwister(seed) internally —
                # it is fully thread-safe when each call uses a unique seed.
                # seed = pair_idx ensures reproducibility across runs.
                r    = dr_estimate(df_a, col_a, df_b, col_b;
                                   n_sim=n_sim, n_bootstrap=n_bootstrap,
                                   seed=pair_idx)
                ci_w = r.gamma_ci_hi - r.gamma_ci_lo
                # `round(x, digits=4)` rounds to 4 decimal places.
                entry = Dict(
                    "dr_gamma"  => round(r.gamma,        digits=4),
                    "dr_ci_lo"  => round(r.gamma_ci_lo,  digits=4),
                    "dr_ci_hi"  => round(r.gamma_ci_hi,  digits=4),
                    "dr_nmi"    => round(r.nmi,          digits=4),
                    "dr_v"      => round(r.cramers_v,    digits=4),
                    "dr_ks"     => round(r.ks_overlap,   digits=4),
                    "ci_width"  => round(ci_w,           digits=4),
                    # CI excludes zero = statistically significant monotonic co-variation.
                    "excl_zero" => r.gamma_ci_lo > 0.0 || r.gamma_ci_hi < 0.0,
                    "n_a"       => r.n_a,
                    "n_b"       => r.n_b,
                )
            catch e
                entry["error"] = string(e)   # convert exception to string for JSON
            end
        end

        # ── Lock: update shared state ──────────────────────────────────────────
        # `lock(lk) do ... end` acquires the lock, runs the block, releases it.
        # This is Julia's idiomatic RAII pattern for locks (like Python's
        # `with lock: ...`).  The lock is held only for microseconds — the
        # heavy dr_estimate computation ran outside.
        lock(lk) do
            key = _pair_id(var_a, var_b)
            results[key] = entry

            if haskey(entry, "error")
                n_err[] += 1
            elseif haskey(entry, "dr_gamma")
                push!(gammas, entry["dr_gamma"])
            end

            # `n_done[]` reads the Ref; `n_done[] += 1` is `n_done[] = n_done[] + 1`
            n_done[] += 1
            done = n_done[]   # capture current value for modulo checks below

            # `%` is the modulo operator (same as Python).
            if done % save_every == 0
                save_checkpoint(results, metadata, output_json)
            end

            # Progress report every 50 pairs.
            if done % 50 == 0
                elapsed  = time() - t0
                rate     = done / max(elapsed, 1e-6)   # pairs per second
                remain   = (n_todo - done) / max(rate, 1e-6)
                all_done = done + length(existing)
                @printf("  [%d/%d] done=%d err=%d  %.1f/s  ETA=%.0fs\n",
                    all_done, total, done, n_err[], rate, remain)
            end
        end   # lock released here

    end   # @threads loop — all threads finish before execution continues here

    # ── Final save ────────────────────────────────────────────────────────────
    # After @threads, all pairs are done.  Save once more to catch any pairs
    # not saved by the `save_every` checkpoint inside the loop.
    save_checkpoint(results, metadata, output_json)
    elapsed = time() - t0
    @printf("\nSweep complete in %.1fs\n", elapsed)
    @printf("  Total: %d  Errors: %d\n", length(results), n_err[])
    if !isempty(gammas)
        @printf("  Median |gamma|: %.4f\n", median(abs.(gammas)))
        n_sig = count(k -> get(get(results, k, Dict()), "excl_zero", false),
                      collect(keys(results)))
        # `collect(keys(results))` converts the Dict key view to a Vector.
        # `count(predicate, collection)` counts elements satisfying predicate.
        @printf("  Significant (CI excl 0): %d\n", n_sig)
    end
    return results
end
