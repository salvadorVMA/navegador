"""
    ses_encoder.jl — SES variable encoding

Encodes the four bridge SES variables:
  sexo    : binary dummy  (1→0.0 Male, 2→1.0 Female)
  edad    : ordinal 0–6   (age bins: "0-18"→0, "19-24"→1, ..., "65+"→6)
  escol   : ordinal 1–5   (education level, parsed as Float64)
  Tam_loc : ordinal 1–4   (locality size, parsed as Float64)

Sentinel codes (≥97 or <0) are mapped to NaN so they are excluded from models.
"""

using DataFrames


const EDAD_ORDER = Dict(
    "0-18"  => 0, "19-24" => 1, "25-34" => 2, "35-44" => 3,
    "45-54" => 4, "55-64" => 5, "65+"   => 6,
)

const SES_VARS = [:sexo, :edad, :escol, :Tam_loc]

const SENTINEL_HIGH = 97.0
const SENTINEL_LOW  = 0.0


"""is_sentinel(v) → true if v is a survey sentinel code (≥97 or <0)."""
function is_sentinel(v)::Bool
    try
        f = v isa AbstractString ? parse(Float64, v) : Float64(v)
        return f < SENTINEL_LOW || f >= SENTINEL_HIGH
    catch
        return false
    end
end


"""Encode sexo: 1/"01" → 0.0, 2/"02" → 1.0, else NaN."""
function encode_sexo(col::AbstractVector)::Vector{Float64}
    result = Vector{Float64}(undef, length(col))
    for (i, v) in enumerate(col)
        s = strip(string(v))
        result[i] = s in ("1","01","1.0") ? 0.0 :
                    s in ("2","02","2.0") ? 1.0 : NaN
    end
    return result
end


"""
Encode edad as ordinal 0–6.
Handles string bins ("25-34") and numeric raw ages (35.0).
"""
function encode_edad(col::AbstractVector)::Vector{Float64}
    result  = Vector{Float64}(undef, length(col))
    n_mapped = 0
    for (i, v) in enumerate(col)
        s = strip(string(v))
        if haskey(EDAD_ORDER, s)
            result[i] = Float64(EDAD_ORDER[s])
            n_mapped += 1
        else
            result[i] = NaN
        end
    end
    # If > 50% unmapped, try numeric age binning
    if n_mapped < length(col) ÷ 2
        bins  = [-1.0, 18.0, 24.0, 34.0, 44.0, 54.0, 64.0, 999.0]
        ranks = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        for (i, v) in enumerate(col)
            try
                age = v isa AbstractString ? parse(Float64, v) : Float64(v)
                isnan(age) && continue
                bin = findfirst(k -> age > bins[k] && age <= bins[k+1], 1:length(ranks))
                result[i] = isnothing(bin) ? NaN : ranks[bin]
            catch
                result[i] = NaN
            end
        end
    end
    return result
end


"""Generic ordinal encoding: parse as Float64, sentinel → NaN."""
function encode_ordinal(col::AbstractVector)::Vector{Float64}
    result = Vector{Float64}(undef, length(col))
    for (i, v) in enumerate(col)
        try
            f = v isa AbstractString ? parse(Float64, v) : Float64(v)
            result[i] = is_sentinel(f) ? NaN : f
        catch
            result[i] = NaN
        end
    end
    return result
end


"""
    encode_ses(df::DataFrame, ses_vars=SES_VARS) -> Matrix{Float64}

Encode SES variables into a numeric design matrix (n × p).
NaN values are propagated; filter complete rows before regression.
"""
function encode_ses(df::DataFrame, ses_vars::Vector{Symbol} = SES_VARS)::Matrix{Float64}
    parts = Vector{Vector{Float64}}()
    for var in ses_vars
        var ∉ propertynames(df) && continue
        col = df[!, var]
        push!(parts, var == :sexo ? encode_sexo(col) :
                     var == :edad ? encode_edad(col) :
                     encode_ordinal(col))
    end
    isempty(parts) && error("No SES columns found. Expected: $ses_vars")
    return hcat(parts...)
end


"""
    drop_sentinel_rows(df, ses_vars=SES_VARS) -> DataFrame

Remove rows with NaN in any encoded SES column.
"""
function drop_sentinel_rows(df::DataFrame, ses_vars::Vector{Symbol} = SES_VARS)::DataFrame
    present = [v for v in ses_vars if v in propertynames(df)]
    isempty(present) && return df
    X    = encode_ses(df, present)
    keep = [!any(isnan.(X[i, :])) for i in 1:size(X, 1)]
    return df[keep, :]
end
