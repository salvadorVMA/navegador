# ses_encoder.jl — SES variable encoding and sentinel filtering
#
# The four bridge SES variables must be encoded to numeric vectors before
# entering the ordered logit and logistic regression models.
#
# Variable semantics and encoding:
#   sexo    : binary sex (1=Male, 2=Female) → 0.0 / 1.0
#   edad    : age in 7 ordinal bins         → 0–6  (interval-like ordinal)
#   escol   : education 1–5 ordinal scale   → 1.0–5.0
#   Tam_loc : locality size 1–4 ordinal     → 1.0–4.0
#
# Sentinel codes: survey values ≥ 97 (e.g. 97=N/A, 98=refused, 99=don't know)
# or < 0 are invalid.  They are replaced with NaN so that rows with them can be
# dropped before regression (see drop_sentinel_rows).
#
# ── `const` in Julia ─────────────────────────────────────────────────────────
# `const` declares a module-level constant.  Unlike Python, where `ALL_CAPS`
# is only a naming convention, Julia's `const` is enforced by the compiler:
# reassigning a const variable raises an error.  More importantly, it enables
# type-stable dispatch — the compiler can assume the type never changes.

using DataFrames


# ── Module-level constants ────────────────────────────────────────────────────

# Dict literal syntax: `Dict(key => value, ...)`.
# Julia Dicts are hash maps, like Python dicts.
# Type annotation: `Dict{String, Int}` — keys are Strings, values are Ints.
const EDAD_ORDER = Dict(
    "0-18"  => 0, "19-24" => 1, "25-34" => 2, "35-44" => 3,
    "45-54" => 4, "55-64" => 5, "65+"   => 6,
)

# `Symbol` is Julia's type for identifiers like `:sexo`.
# Symbols are interned (one object per unique name), faster than string comparison.
# DataFrame columns are referenced by Symbol: `df[!, :sexo]`.
# Python analogue: column names as strings, e.g. `df['sexo']`.
const SES_VARS = [:sexo, :edad, :escol, :Tam_loc]

const SENTINEL_HIGH = 97.0   # codes ≥ 97 are invalid in los_mex surveys
const SENTINEL_LOW  = 0.0    # codes < 0 are invalid


"""
    is_sentinel(v) -> Bool

Return true if `v` is a survey sentinel code (invalid / missing indicator).

  ≥ 97  →  99=no sabe, 98=no contesta, 97=no aplica  (common in los_mex)
  < 0   →  WVS convention for "not asked", "interviewer error", etc.

# Duck typing

`v` has no type annotation — the function accepts anything (Int, Float64, String).
This is intentional: survey data arrives in heterogeneous types (strings, floats,
integers depending on how CSV/JSON was loaded).

`try / catch` swallows parse errors (e.g. v = "missing") and returns false,
meaning unparseable values are not treated as sentinels (they become NaN
through other paths).
"""
function is_sentinel(v)::Bool
    try
        f = v isa AbstractString ? parse(Float64, v) : Float64(v)
        return f < SENTINEL_LOW || f >= SENTINEL_HIGH
    catch
        return false   # unparseable → not a sentinel code
    end
end


"""
    encode_sexo(col::AbstractVector) -> Vector{Float64}

Encode binary sex variable: 1 / "01" / "1.0" → 0.0 (Male), 2 / "02" / "2.0" → 1.0 (Female).
Anything else → NaN.

# `string(v)` and `strip()`

Survey data arrives as mixed types after CSV loading.  Converting to string
then stripping whitespace normalizes e.g. `1`, `1.0`, `" 1 "` to `"1"`.
This is defensive programming for heterogeneous column types.

# `s in (...)` membership test

`s in ("1", "01", "1.0")` checks if s equals any element of the tuple.
Tuples are preferred over arrays for small membership sets because Julia
generates unrolled comparisons (faster than hash lookup).
Python equivalent: `s in {'1', '01', '1.0'}`.
"""
function encode_sexo(col::AbstractVector)::Vector{Float64}
    result = Vector{Float64}(undef, length(col))
    for (i, v) in enumerate(col)   # `enumerate` yields (index, value) pairs, 1-indexed
        s = strip(string(v))
        result[i] = s in ("1","01","1.0") ? 0.0 :
                    s in ("2","02","2.0") ? 1.0 : NaN
    end
    return result
end


"""
    encode_edad(col::AbstractVector) -> Vector{Float64}

Encode age as ordinal rank 0–6.

Two-pass strategy:
  Pass 1: Match string bins directly via EDAD_ORDER dict ("25-34" → 2, etc.)
  Pass 2: If > 50% of values are unmapped (numeric raw ages), bin continuous ages.

# Fallback to numeric binning

Los_mex stores edad as pre-binned strings ("25-34").  Other datasets may store
raw ages (35.0).  The `n_mapped < length(col) ÷ 2` heuristic detects numeric
data and switches to interval binning automatically.

`÷` is integer division (floor division) in Julia, equivalent to Python's `//`.

# `findfirst(predicate, collection)`

Returns the index of the first element satisfying `predicate`, or `nothing`.
`age > bins[k] && age <= bins[k+1]` checks if age falls in interval (bins[k], bins[k+1]].
`isnothing(bin)` handles the case where age is outside all bins → NaN.
"""
function encode_edad(col::AbstractVector)::Vector{Float64}
    result   = Vector{Float64}(undef, length(col))
    n_mapped = 0
    for (i, v) in enumerate(col)
        s = strip(string(v))
        if haskey(EDAD_ORDER, s)   # `haskey(dict, key)` = Python's `key in dict`
            result[i] = Float64(EDAD_ORDER[s])
            n_mapped += 1
        else
            result[i] = NaN
        end
    end

    # If the majority of values were unmapped, try numeric age binning.
    if n_mapped < length(col) ÷ 2
        bins  = [-1.0, 18.0, 24.0, 34.0, 44.0, 54.0, 64.0, 999.0]
        ranks = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        for (i, v) in enumerate(col)
            try
                age = v isa AbstractString ? parse(Float64, v) : Float64(v)
                isnan(age) && continue   # skip already-NaN entries
                # `findfirst` returns the first matching index or `nothing`.
                bin = findfirst(k -> age > bins[k] && age <= bins[k+1], 1:length(ranks))
                result[i] = isnothing(bin) ? NaN : ranks[bin]
            catch
                result[i] = NaN
            end
        end
    end
    return result
end


"""
    encode_ordinal(col::AbstractVector) -> Vector{Float64}

Generic ordinal encoder: parse as Float64, replace sentinel codes with NaN.

Used for escol (1–5) and Tam_loc (1–4).  No special range validation —
`is_sentinel` handles values ≥ 97 or < 0.
"""
function encode_ordinal(col::AbstractVector)::Vector{Float64}
    result = Vector{Float64}(undef, length(col))
    for (i, v) in enumerate(col)
        try
            f = v isa AbstractString ? parse(Float64, v) : Float64(v)
            result[i] = is_sentinel(f) ? NaN : f
        catch
            result[i] = NaN   # unparseable string → missing
        end
    end
    return result
end


"""
    encode_ses(df::DataFrame, ses_vars=SES_VARS) -> Matrix{Float64}

Encode all available SES variables into a numeric design matrix (n × p).

# Column dispatch via if/else

Julia has no `match`/`switch` statement.  We use `if/elseif/else` or — here —
a ternary chain to dispatch to the correct encoder per variable name.

# `∉` and `∈` operators

`v ∉ propertynames(df)` is equivalent to `!(v in propertynames(df))`.
`∈` and `∉` are Unicode operators entered in the REPL as backslash-in + Tab
and backslash-notin + Tab respectively.
Python equivalent: `v not in df.columns`.

# `propertynames(df)`

Returns a `Vector{Symbol}` of column names (e.g. `[:sexo, :edad, :escol, :Tam_loc]`).
Python equivalent: `df.columns.tolist()`.

# `hcat(parts...)`

Horizontal concatenation: stacks column vectors side by side into a matrix.
`parts...` splats the array into positional arguments.
Python equivalent: `np.column_stack(parts)`.
"""
function encode_ses(df::DataFrame, ses_vars::Vector{Symbol} = SES_VARS)::Matrix{Float64}
    parts = Vector{Vector{Float64}}()   # empty typed array; we'll push! columns into it
    for var in ses_vars
        var ∉ propertynames(df) && continue   # skip columns not present in this DataFrame
        col = df[!, var]   # df[!, :col] gives the column without copying (faster than df[:, :col])
        push!(parts, var == :sexo ? encode_sexo(col) :
                     var == :edad ? encode_edad(col) :
                     encode_ordinal(col))
        # `push!(array, val)` appends in place.  The `!` marks mutation.
    end
    isempty(parts) && error("No SES columns found in DataFrame.  Expected: $ses_vars")
    return hcat(parts...)   # n × p matrix
end


"""
    drop_sentinel_rows(df, ses_vars=SES_VARS) -> DataFrame

Remove rows with NaN in any encoded SES column.

# Why drop rather than impute?

Missing SES data is unlikely to be Missing At Random in survey data — respondents
who refuse to answer income or education questions are systematically different
from those who answer.  Imputation would introduce bias.  The DR estimator
achieves ~99.2% row retention with the 4-var SES set, so dropping is acceptable.

# `[v for v in ses_vars if v in propertynames(df)]`

List comprehension with a filter clause.  Python equivalent:
  `[v for v in ses_vars if v in df.columns]`

# `df[keep, :]`

Row-indexing with a Bool vector.  `keep[i] = true` → row i is retained.
Python equivalent: `df[keep]` or `df.loc[keep]`.
"""
function drop_sentinel_rows(df::DataFrame, ses_vars::Vector{Symbol} = SES_VARS)::DataFrame
    present = [v for v in ses_vars if v in propertynames(df)]
    isempty(present) && return df   # no SES columns → return unchanged
    X    = encode_ses(df, present)
    # `any(isnan.(X[i, :]))` checks if any element in row i is NaN.
    keep = [!any(isnan.(X[i, :])) for i in 1:size(X, 1)]
    return df[keep, :]   # copy of the filtered rows
end
