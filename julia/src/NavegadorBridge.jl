"""
    NavegadorBridge.jl — Julia bridge estimator for Navegador

Julia port of the Python DoublyRobust bridge pipeline from ses_regression.py.

Exports:
  goodman_kruskal_gamma, normalized_mutual_information
  cronbach_alpha, scale_to_output, reverse_code, build_construct_scale
  fit_ordered_logit, predict_proba, fit_logistic, predict_logistic
  encode_ses, drop_sentinel_rows, is_sentinel, SES_VARS
  DRResult, dr_estimate
  run_sweep, load_checkpoint, save_checkpoint
"""
module NavegadorBridge

using DataFrames
using Statistics
using LinearAlgebra
using Random
using Distributions
using StatsBase
using GLM
using Optim
using ForwardDiff
using JSON
using CSV
using Printf

include("gamma_nmi.jl")
include("cronbach.jl")
include("ordinal_model.jl")
include("ses_encoder.jl")
include("dr_estimator.jl")
include("sweep.jl")

export goodman_kruskal_gamma, normalized_mutual_information
export cronbach_alpha, scale_to_output, reverse_code, build_construct_scale
export fit_ordered_logit, predict_proba, fit_logistic, predict_logistic
export encode_ses, drop_sentinel_rows, is_sentinel, SES_VARS
export DRResult, dr_estimate
export run_sweep, load_checkpoint, save_checkpoint

end # module NavegadorBridge
