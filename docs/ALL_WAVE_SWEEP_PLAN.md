# All-Wave WVS Sweep: Motivation, GPU/TPU Assessment, and Julia Batch Plan

## 1. Motivation

The current gamma-surface covers two slices:

| Sweep | Scope | Pairs | Status |
|-------|-------|-------|--------|
| **Geographic W7** | 66 countries, Wave 7 only | 68,174 | Done (Julia, 9.7 hr) |
| **Temporal MEX** | Mexico only, Waves 3-7 | 2,334 | Done (Julia, 42 min) |

This leaves a massive gap: **Waves 1-6 across all participating countries**. Without these, we cannot answer:

- How has SES stratification evolved **within** each country across decades?
- Are the structural patterns found in W7 (e.g., education dominance, zone coherence) stable over time, or are they artifacts of the 2017-2022 measurement window?
- Do countries that joined the WVS in different waves show selection bias in their gamma profiles?
- What does the full 4D gamma-surface (variable pair x country x wave x SES reference) look like?

The temporal MEX sweep showed significant structural evolution (Spearman rho = 0.63-0.75 between adjacent waves). Extrapolating from one country is insufficient -- we need the full panel.

### Scale of the full sweep

WVS country participation by wave:

| Wave | Period | Countries (approx) | Constructs (est) | Pairs (est) |
|------|--------|-------------------|-------------------|-------------|
| W1 | 1981-1984 | ~20 | ~16 | ~2,400 |
| W2 | 1990-1994 | ~40 | ~22 | ~9,200 |
| W3 | 1995-1998 | ~50 | ~26 | ~16,250 |
| W4 | 1999-2004 | ~40 | ~27 | ~14,000 |
| W5 | 2005-2009 | ~55 | ~33 | ~29,000 |
| W6 | 2010-2014 | ~60 | ~46 | ~61,000 |
| W7 | 2017-2022 | 66 | 55 | 68,174 |
| **Total** | | **~330 contexts** | | **~200,000** |

Earlier waves have fewer constructs (fewer questions available), so pairs grow sub-linearly with countries. The total is roughly **3x the geographic W7 sweep**.

At Julia's measured rate of ~1.9 pairs/s on 8-thread CPU: **~29 hours total**.

## 2. Why GPU/TPU Won't Help

### 2.1 The workload shape is wrong for accelerators

The DR bridge estimator fits ordered logit models with **6-8 parameters** (4 SES vars + 2-4 thresholds). The Hessian is a 6x6 to 8x8 matrix. GPU/TPU accelerators are designed for large matrix operations (thousands of dimensions), not hundreds of thousands of tiny matrix solves.

**Per-pair compute profile:**
- 2 ordered logit fits (30 Newton steps each, 6x6 Hessian solve per step)
- 1 logistic regression fit (20 Newton steps, 5x5 Hessian)
- 200 bootstrap iterations (each: 2 ordered logits + gamma computation)
- Total: ~600 tiny (6x6) linear solves + ~400 matrix-vector multiplies

On CPU, each solve takes microseconds. On GPU, the kernel launch overhead alone (~5-10 us) exceeds the actual compute time. The GPU is never saturated.

### 2.2 JAX vmap doesn't help enough

The bootstrap loop is vmapped (scan), so 200 iterations run in parallel on GPU. But each iteration still involves a sequential 20-step Newton loop (`jax.lax.scan`), and the matrices are too small to fill GPU warps. Measured TPU throughput was not significantly faster than CPU for this workload.

### 2.3 f64 vs f32

The JAX estimator was originally f64. We switched to f32 (commit `363e526` on `colab_jax`) since the Hessian solve was already f32-downcast for TPU compatibility. f32 is sufficient -- the regularization (`1e-4 * I`) and step-size damping absorb any precision loss on these tiny systems.

However, f32 doesn't change the fundamental problem: **kernel launch overhead >> compute time** for 6x6 matrices.

### 2.4 Memory crashes on Colab

The JAX sweep on Colab (12 GB RAM free tier, 25 GB Pro) ran out of memory repeatedly:

1. **JIT compilation cache**: JAX compiles a separate kernel for each unique combination of static args (`K`, `n_sim`, `n_bootstrap`). With K varying (3, 4, or 5) across pairs, the cache grows.
2. **Device buffer accumulation**: JAX arrays on TPU/GPU memory are not freed immediately when Python references are deleted.
3. **Checkpoint dict**: 69K estimates in a Python dict grows to ~100 MB.
4. **Context DataFrames**: All 72 contexts loaded upfront (fixed with lazy loading in commit `363e526`, but Colab sessions still die before pulling the fix).

Even with fixes, Colab's session instability (disconnects every few hours) makes 20+ hour sweeps impractical.

### 2.5 Cost comparison

| Platform | Engine | Est. time | Cost | Reliability |
|----------|--------|-----------|------|-------------|
| Colab free (TPU) | JAX | Unknown (crashes) | Free | Unusable |
| Colab Pro+ (TPU) | JAX | ~20 hr? | $50/mo | Unreliable (disconnects) |
| GCP A100 VM | JAX | ~15 hr? | ~$45 | Reliable but unproven speed |
| GCP n2-highcpu-8 | Julia | ~29 hr | ~$8 | Proven |
| **Mac 8-core (local)** | **Julia** | **~29 hr** | **Free** | **Proven, no network** |

**Conclusion**: Julia on local Mac is the optimal choice. Proven speed, proven reliability, zero cost, no network dependency.

## 3. Julia Batch Sweep Plan

### 3.1 Strategy: one wave per batch

Each wave is independent -- different countries, different construct sets, different output file. Run them sequentially (or in parallel on separate machines). Checkpoint/resume within each wave handles interruptions.

### 3.2 Pipeline per wave

```
Step 1 (Python): Build constructs for wave N
  python scripts/debug/build_wvs_constructs_multi.py \
    --waves N --scope geographic_wN

Step 2 (Python): Export CSVs for Julia
  python scripts/debug/export_wvs_for_julia.py \
    --cache data/results/wvs_multi_construct_cache_geographic_wN.pkl \
    --manifest data/results/wvs_multi_construct_manifest_geographic_wN.json \
    --out-dir data/julia_bridge_wvs/wN/

Step 3 (Julia): Run sweep for wave N
  julia -t 8 --project=julia julia/scripts/run_wvs_geographic_wave.jl \
    --wave N \
    --data-dir data/julia_bridge_wvs/wN/ \
    --output data/results/wvs_geographic_sweep_wN.json

Step 4 (Python): Merge wave results into unified gamma-surface
  python scripts/debug/merge_wave_sweeps.py
```

### 3.3 Execution order (recommended)

Run waves in reverse order (most valuable first):

| Batch | Wave | Countries | Est. pairs | Est. time | Priority |
|-------|------|-----------|-----------|-----------|----------|
| 0 | W7 | 66 | 68,174 | 9.7 hr | **Already done** |
| 1 | W6 | ~60 | ~61,000 | ~8.9 hr | High (largest pre-W7) |
| 2 | W5 | ~55 | ~29,000 | ~4.2 hr | High |
| 3 | W3 | ~50 | ~16,250 | ~2.4 hr | Medium |
| 4 | W4 | ~40 | ~14,000 | ~2.0 hr | Medium |
| 5 | W2 | ~40 | ~9,200 | ~1.3 hr | Low (few constructs) |
| 6 | W1 | ~20 | ~2,400 | ~0.3 hr | Low (few constructs) |
| **Total** | | **~330** | **~200,000** | **~29 hr** | |

**Overnight strategy**: Run W6 + W5 overnight (~13 hr). Run W3 + W4 the next day (~4.4 hr). Run W2 + W1 as a quick batch (~1.6 hr). Total: 2-3 days of overnight/background runs.

### 3.4 Prerequisites

1. **WVS data files**: The WVS CSV/zip files must be present on the Mac (`data/wvs/`). These are already there from the W7 geographic sweep.
2. **Julia environment**: Julia 1.12+ with `NavegadorBridge` project dependencies. Already installed.
3. **Construct overrides**: The `construct_v5_overrides.json` and `wvs_svs_v1.json` files must be current. Already in place.
4. **Q-code resolution**: Waves 1-6 use A-codes (time-series format), not Q-codes. The `build_wvs_constructs_multi.py` handles this via the equivalences table. Already implemented.

### 3.5 New scripts needed

| Script | Purpose | Complexity |
|--------|---------|------------|
| `julia/scripts/run_wvs_geographic_wave.jl` | Parameterized per-wave geographic sweep (accepts `--wave N`) | Low -- adapt `run_wvs_geographic_fast.jl` |
| `scripts/debug/merge_wave_sweeps.py` | Merge per-wave JSON outputs into unified gamma-surface | Low |
| `scripts/pipeline/all_wave_sweep_pipeline.py` | Prefect orchestration for full 7-wave batch | Medium |

### 3.6 Output structure

```
data/results/
  wvs_geographic_sweep_w7.json          # existing (68K estimates)
  wvs_geographic_sweep_w6.json          # new
  wvs_geographic_sweep_w5.json          # new
  wvs_geographic_sweep_w4.json          # new
  wvs_geographic_sweep_w3.json          # new
  wvs_geographic_sweep_w2.json          # new
  wvs_geographic_sweep_w1.json          # new
  wvs_all_wave_gamma_surface.json       # merged (all ~200K estimates)
```

### 3.7 Analysis unlocked by all-wave sweep

With the full panel, we can compute:

1. **Per-country temporal trajectories**: gamma(pair, country, wave) -- how each country's SES stratification evolves
2. **Structural stability by zone**: Do cultural zones maintain coherence across decades?
3. **Convergence/divergence analysis**: Are countries becoming more similar or more different in SES stratification over time?
4. **Wave-entry bias**: Do countries that joined in later waves systematically differ?
5. **Decade-level TDA**: Persistent homology per decade, tracking topological features through time
6. **Full 4D gamma-surface visualization**: Interactive exploration of the complete variable x country x wave x SES space
