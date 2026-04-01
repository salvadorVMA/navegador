# Topological Analysis of WVS Construct Networks — v2
## JSON Input · Julia-Accelerated · 8-Core Parallel

---

## 1. Architecture Overview

The pipeline splits computation across two runtimes:

- **Python**: orchestration, data loading, TDA (ripser), visualization, output
- **Julia**: all O(n³) bottlenecks — Floyd-Warshall, Ricci curvature, Gromov-Wasserstein, spectral distances — parallelized across 8 cores via `Threads` and `Distributed`

Communication between runtimes uses **intermediate numpy/CSV files** written to a scratch directory, called from Python via `subprocess`. This avoids the complexity of PyJulia while keeping the interface clean.

```
JSON weight files
      │
      ▼
Python loader ──► scratch/.npy matrices
                        │
                        ▼
               Julia workers (8 cores)
               ├── floyd_warshall_parallel.jl
               ├── ricci_curvature_parallel.jl
               ├── spectral_distances_parallel.jl
               └── gromov_wasserstein_parallel.jl
                        │
                        ▼
               scratch/results/*.npy
                        │
                        ▼
               Python TDA + visualization
```

---

## 2. Expected JSON Format

The pipeline supports two common JSON layouts. Specify which via `json_format` in the loader.

### Format A — Nested dict (construct × construct)
```json
{
  "country": "MEX",
  "wave": 7,
  "constructs": ["trust_institutions", "satisfaction_democracy", ...],
  "weights": {
    "trust_institutions": {
      "satisfaction_democracy": 0.42,
      "support_government": -0.18,
      ...
    },
    ...
  }
}
```

### Format B — Edge list
```json
{
  "country": "MEX",
  "wave": 7,
  "constructs": ["trust_institutions", "satisfaction_democracy", ...],
  "edges": [
    {"from": "trust_institutions", "to": "satisfaction_democracy",
     "weight": 0.42, "direction": 1},
    {"from": "trust_institutions", "to": "support_government",
     "weight": 0.18, "direction": -1},
    ...
  ]
}
```

---

## 3. Project Structure

```
wvs_topology/
├── data/
│   └── weights/
│       ├── wave_6/
│       │   ├── MEX.json
│       │   ├── BRA.json
│       │   └── ...
│       └── wave_7/
│           └── ...
├── metadata/
│   ├── constructs.csv
│   ├── countries.csv
│   └── waves.csv
├── scratch/          # intermediate arrays (auto-created)
├── output/           # results and plots
├── julia/
│   ├── setup.jl                      # environment setup
│   ├── floyd_warshall_parallel.jl
│   ├── ricci_curvature_parallel.jl
│   ├── spectral_distances_parallel.jl
│   └── gromov_wasserstein_parallel.jl
└── python/
    ├── loader.py
    ├── within_tda.py
    ├── between_tda.py
    ├── temporal.py
    ├── features.py
    ├── visualize.py
    └── pipeline.py
```

---

## 4. Julia Setup

### 4.1 Environment (`julia/setup.jl`)

Run once to install all Julia dependencies:

```julia
# julia/setup.jl
using Pkg

Pkg.add([
    "LinearAlgebra",
    "SparseArrays",
    "SharedArrays",
    "Distributed",
    "NPZ",           # numpy .npy file I/O
    "JSON3",
    "DataFrames",
    "CSV",
    "Tullio",        # fast einsum-style tensor ops
    "LoopVectorization",
    "Distances",
    "OptimalTransport",  # GW distance
    "Graphs",
    "Statistics",
    "Base.Threads",
])

println("Julia environment ready. Threads available: ", Threads.nthreads())
```

Run with: `julia -t 8 julia/setup.jl`

### 4.2 Floyd-Warshall + Triangle Violations (`julia/floyd_warshall_parallel.jl`)

Reads a batch of distance matrices, computes all-pairs shortest paths and
violation matrices in parallel across 8 threads.

```julia
# julia/floyd_warshall_parallel.jl
# Usage: julia -t 8 floyd_warshall_parallel.jl <input_manifest.json> <output_dir>

using NPZ, JSON3, Base.Threads, LinearAlgebra

function floyd_warshall!(D::Matrix{Float64})
    """In-place all-pairs shortest path. O(n³) but cache-friendly."""
    n = size(D, 1)
    @inbounds for k in 1:n
        @threads for i in 1:n
            if D[i, k] == Inf; continue; end
            for j in 1:n
                new_d = D[i, k] + D[k, j]
                if new_d < D[i, j]
                    D[i, j] = new_d
                end
            end
        end
    end
    return D
end

function process_matrix(key::String, D_raw::Matrix{Float64}, output_dir::String)
    n = size(D_raw, 1)

    # Replace zeros off-diagonal with Inf for shortest path
    D = copy(D_raw)
    for i in 1:n, j in 1:n
        if i != j && D[i,j] == 0.0
            D[i,j] = Inf
        end
    end

    D_sp = copy(D)
    floyd_warshall!(D_sp)

    # Replace Inf with large sentinel for numpy compatibility
    D_sp[isinf.(D_sp)] .= 2.0

    # Triangle violations: V(i,k) = D_raw(i,k) - D_sp(i,k)
    V = D_raw .- D_sp
    V[diagind(V)] .= 0.0
    V = max.(V, 0.0)

    # Mediator scores: for each j, sum of improvements routing through j
    med_scores = zeros(Float64, n)
    @threads for j in 1:n
        total = 0.0
        for i in 1:n, k in 1:n
            if i == j || k == j || i == k; continue; end
            indirect = D_raw[i,j] + D_raw[j,k]
            improvement = D_raw[i,k] - indirect
            if improvement > 0
                total += improvement
            end
        end
        med_scores[j] = total
    end

    safe_key = replace(key, "/" => "_")
    npzwrite(joinpath(output_dir, "$(safe_key)_shortest.npy"), D_sp)
    npzwrite(joinpath(output_dir, "$(safe_key)_violations.npy"), V)
    npzwrite(joinpath(output_dir, "$(safe_key)_mediators.npy"), med_scores)
end

# ── Main ─────────────────────────────────────────────────────────────────────

manifest_path = ARGS[1]
output_dir    = ARGS[2]
mkpath(output_dir)

manifest = JSON3.read(read(manifest_path, String))

println("Floyd-Warshall: processing $(length(manifest)) matrices on $(Threads.nthreads()) threads")

# Process each matrix (outer loop over networks, inner parallelism over nodes)
for item in manifest
    key   = item["key"]
    fpath = item["path"]
    D_raw = npzread(fpath)
    process_matrix(key, D_raw, output_dir)
    println("  ✓ $key")
end

println("Done.")
```

### 4.3 Spectral Distances (`julia/spectral_distances_parallel.jl`)

Computes the full pairwise spectral distance matrix across all country-wave
networks for a given wave. Parallelized over pairs.

```julia
# julia/spectral_distances_parallel.jl
# Usage: julia -t 8 spectral_distances_parallel.jl <manifest.json> <output.npy>

using NPZ, JSON3, LinearAlgebra, Base.Threads

function laplacian_spectrum(W_sym::Matrix{Float64})::Vector{Float64}
    n = size(W_sym, 1)
    deg = vec(sum(W_sym, dims=2))
    L = diagm(deg) .- W_sym
    # Symmetric eigendecomposition — exploit symmetry for speed
    vals = eigvals(Symmetric(L))
    return sort(vals)
end

function spectral_distance(s1::Vector{Float64}, s2::Vector{Float64})::Float64
    return norm(s1 .- s2)
end

manifest_path = ARGS[1]
output_path   = ARGS[2]

manifest = JSON3.read(read(manifest_path, String))
n = length(manifest)
keys_list = [item["key"] for item in manifest]

println("Computing spectra for $n networks...")

# Compute all spectra first (parallelizable)
spectra = Vector{Vector{Float64}}(undef, n)
@threads for i in 1:n
    W = npzread(manifest[i]["path"])
    W_abs = abs.(W)
    W_sym = (W_abs .+ W_abs') ./ 2
    spectra[i] = laplacian_spectrum(W_sym)
end

println("Computing $(n*(n-1)÷2) pairwise distances...")

# Pairwise distance matrix
D = zeros(Float64, n, n)
pairs = [(i,j) for i in 1:n for j in i+1:n]

@threads for idx in 1:length(pairs)
    i, j = pairs[idx]
    d = spectral_distance(spectra[i], spectra[j])
    D[i,j] = d
    D[j,i] = d
end

npzwrite(output_path, D)

# Save key order for Python to reconstruct labels
open(replace(output_path, ".npy" => "_keys.json"), "w") do f
    JSON3.write(f, keys_list)
end

println("Done. Distance matrix saved to $output_path")
```

### 4.4 Ollivier-Ricci Curvature (`julia/ricci_curvature_parallel.jl`)

The most expensive computation — O(n² × OT) per network. Parallelized over
edges using a thread-safe OT solver.

```julia
# julia/ricci_curvature_parallel.jl
# Usage: julia -t 8 ricci_curvature_parallel.jl <manifest.json> <output_dir>

using NPZ, JSON3, LinearAlgebra, Base.Threads

"""
Sinkhorn OT solver (entropy-regularized) — fast approximation of W1.
"""
function sinkhorn_w1(
    a::Vector{Float64},
    b::Vector{Float64},
    C::Matrix{Float64};
    eps::Float64 = 0.05,
    max_iter::Int = 200,
    tol::Float64 = 1e-6
)::Float64
    n, m = length(a), length(b)
    K = exp.(-C ./ eps)
    u = ones(n)
    v = ones(m)

    for _ in 1:max_iter
        u_new = a ./ (K * v .+ 1e-10)
        v_new = b ./ (K' * u_new .+ 1e-10)
        if norm(u_new - u) < tol; break; end
        u = u_new
        v = v_new
    end

    T = diagm(u) * K * diagm(v)
    return sum(T .* C)
end

function ricci_curvature_matrix(
    W_sym::Matrix{Float64},
    D::Matrix{Float64};
    alpha::Float64 = 0.5
)::Matrix{Float64}
    n = size(W_sym, 1)

    # Row-normalize W_sym → transition matrix P
    row_sums = sum(W_sym, dims=2)
    row_sums[row_sums .== 0] .= 1.0
    P = W_sym ./ row_sums

    kappa = zeros(Float64, n, n)

    # Collect edges to process
    edges = [(i,j) for i in 1:n for j in i+1:n if W_sym[i,j] > 0]

    @threads for idx in 1:length(edges)
        i, j = edges[idx]
        d_ij = D[i, j]
        if d_ij < 1e-10; continue; end

        # Lazy random walk measures at i and j
        mu_i = (1 - alpha) .* P[i, :] .+ alpha .* (1:n .== i)
        mu_j = (1 - alpha) .* P[j, :] .+ alpha .* (1:n .== j)

        # Normalize (should sum to 1, but float safety)
        mu_i ./= sum(mu_i)
        mu_j ./= sum(mu_j)

        w1 = sinkhorn_w1(mu_i, mu_j, D)
        k = 1.0 - w1 / d_ij

        kappa[i, j] = k
        kappa[j, i] = k
    end

    return kappa
end

manifest_path = ARGS[1]
output_dir    = ARGS[2]
mkpath(output_dir)

manifest = JSON3.read(read(manifest_path, String))
alpha    = length(ARGS) >= 3 ? parse(Float64, ARGS[3]) : 0.5

println("Ricci curvature: $(length(manifest)) networks on $(Threads.nthreads()) threads")

for item in manifest
    key   = item["key"]
    W     = npzread(item["w_path"])
    D     = npzread(item["d_path"])

    W_abs = abs.(W)
    W_sym = (W_abs .+ W_abs') ./ 2

    kappa = ricci_curvature_matrix(W_sym, D; alpha=alpha)
    safe_key = replace(key, "/" => "_")
    npzwrite(joinpath(output_dir, "$(safe_key)_ricci.npy"), kappa)
    println("  ✓ $key  (edges processed: $(count(W_sym .> 0) ÷ 2))")
end

println("Done.")
```

### 4.5 Gromov-Wasserstein (`julia/gromov_wasserstein_parallel.jl`)

Computes GW distances and transport plans for a specified list of country pairs.

```julia
# julia/gromov_wasserstein_parallel.jl
# Usage: julia -t 8 gromov_wasserstein_parallel.jl <pairs_manifest.json> <output_dir>

using NPZ, JSON3, LinearAlgebra, Base.Threads

"""
Entropic Gromov-Wasserstein via Sinkhorn iterations.
Returns (gw_distance, transport_plan).
"""
function entropic_gw(
    D1::Matrix{Float64},
    D2::Matrix{Float64};
    eps::Float64 = 0.01,
    max_iter::Int = 100,
    inner_iter::Int = 50,
    tol::Float64 = 1e-5
)::Tuple{Float64, Matrix{Float64}}
    n1 = size(D1, 1)
    n2 = size(D2, 1)

    p = fill(1.0/n1, n1)
    q = fill(1.0/n2, n2)

    # Initialize transport plan
    T = p * q'

    function gw_cost(T)
        # GW loss: sum_{i,j,k,l} (D1_{ik} - D2_{jl})^2 T_{ij} T_{kl}
        # Efficient form: uses D1²p + D2²q - 2 D1 T D2'
        A = (D1.^2) * T * ones(n2, 1) * ones(1, n2)
        B = ones(n1, 1) * ones(1, n1) * T * (D2.^2)'
        C = 2.0 .* D1 * T * D2'
        return A .+ B .- C
    end

    prev_loss = Inf
    for outer in 1:max_iter
        M = gw_cost(T)

        # Sinkhorn step
        K = exp.(.-M ./ eps)
        u = ones(n1)
        v = ones(n2)
        for _ in 1:inner_iter
            u_new = p ./ (K * v .+ 1e-10)
            v_new = q ./ (K' * u_new .+ 1e-10)
            u = u_new
            v = v_new
        end
        T = diagm(u) * K * diagm(v)

        loss = sum(gw_cost(T) .* T)
        if abs(prev_loss - loss) < tol; break; end
        prev_loss = loss
    end

    gw_dist = sum(gw_cost(T) .* T)
    return max(gw_dist, 0.0), T
end

manifest_path = ARGS[1]
output_dir    = ARGS[2]
mkpath(output_dir)

pairs = JSON3.read(read(manifest_path, String))
results_lock = ReentrantLock()

println("GW distances: $(length(pairs)) pairs on $(Threads.nthreads()) threads")

@threads for idx in 1:length(pairs)
    pair  = pairs[idx]
    key1  = pair["key1"]
    key2  = pair["key2"]
    D1    = npzread(pair["d1_path"])
    D2    = npzread(pair["d2_path"])

    # Normalize to [0,1]
    D1 ./= max(maximum(D1), 1e-9)
    D2 ./= max(maximum(D2), 1e-9)

    gw_dist, T = entropic_gw(D1, D2)

    pair_key = replace("$(key1)__$(key2)", "/" => "_")
    npzwrite(joinpath(output_dir, "$(pair_key)_gwdist.npy"), [gw_dist])
    npzwrite(joinpath(output_dir, "$(pair_key)_transport.npy"), T)

    lock(results_lock) do
        println("  ✓ $key1 ↔ $key2  GW=$(round(gw_dist, digits=4))")
    end
end

println("Done.")
```

---

## 5. Python Layer

### 5.1 JSON Loader (`python/loader.py`)

```python
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, List, Optional


class WVSJsonLoader:
    """
    Load WVS construct-pair weight matrices from JSON files.
    Supports nested-dict (Format A) and edge-list (Format B) layouts.
    """

    def __init__(self, data_root: str, json_format: str = 'auto'):
        self.root = Path(data_root)
        self.json_format = json_format
        self._constructs: Optional[List[str]] = None

        # Load metadata
        meta_path = self.root / 'metadata'
        self.countries = pd.read_csv(meta_path / 'countries.csv')
        self.waves_df  = pd.read_csv(meta_path / 'waves.csv')
        try:
            self.constructs_df = pd.read_csv(meta_path / 'constructs.csv')
            self._constructs = self.constructs_df['construct_id'].tolist()
        except FileNotFoundError:
            self.constructs_df = None

    # ── Format detection ────────────────────────────────────────────────────

    def _detect_format(self, data: dict) -> str:
        if 'weights' in data and isinstance(data['weights'], dict):
            return 'nested'
        elif 'edges' in data and isinstance(data['edges'], list):
            return 'edgelist'
        else:
            raise ValueError(
                f"Cannot detect JSON format. Keys found: {list(data.keys())}"
            )

    # ── Parsing ─────────────────────────────────────────────────────────────

    def _parse_nested(self, data: dict) -> Tuple[np.ndarray, List[str]]:
        constructs = data['constructs']
        k = len(constructs)
        idx = {c: i for i, c in enumerate(constructs)}
        W = np.zeros((k, k))
        for src, targets in data['weights'].items():
            if src not in idx:
                continue
            for tgt, w in targets.items():
                if tgt not in idx:
                    continue
                W[idx[src], idx[tgt]] = float(w)
        return W, constructs

    def _parse_edgelist(self, data: dict) -> Tuple[np.ndarray, List[str]]:
        constructs = data['constructs']
        k = len(constructs)
        idx = {c: i for i, c in enumerate(constructs)}
        W = np.zeros((k, k))
        for edge in data['edges']:
            src = edge['from']
            tgt = edge['to']
            w   = float(edge['weight'])
            direction = float(edge.get('direction', 1))
            if src in idx and tgt in idx:
                W[idx[src], idx[tgt]] = direction * w
        return W, constructs

    # ── Public API ──────────────────────────────────────────────────────────

    def load_one(
        self,
        country: str,
        wave: int
    ) -> Tuple[np.ndarray, List[str]]:
        """Load weight matrix for a single (country, wave). Returns (W, constructs)."""
        path = self.root / 'data' / 'weights' / f'wave_{wave}' / f'{country}.json'
        with open(path) as f:
            data = json.load(f)

        fmt = self.json_format
        if fmt == 'auto':
            fmt = self._detect_format(data)

        if fmt == 'nested':
            W, constructs = self._parse_nested(data)
        elif fmt == 'edgelist':
            W, constructs = self._parse_edgelist(data)
        else:
            raise ValueError(f"Unknown format: {fmt}")

        # Cache construct list from first file (assumed consistent)
        if self._constructs is None:
            self._constructs = constructs

        return W, constructs

    def load_all(
        self,
        waves: Optional[List[int]] = None,
        countries: Optional[List[str]] = None
    ) -> Tuple[Dict[Tuple[str, int], np.ndarray], List[str]]:
        """
        Load all available (country, wave) matrices.
        Returns (networks_dict, construct_labels).
        """
        networks: Dict[Tuple[str, int], np.ndarray] = {}
        constructs_out: Optional[List[str]] = None
        wave_ids = waves or self.waves_df['wave_id'].tolist()
        country_codes = countries or self.countries['country_code'].tolist()

        missing = []
        for wave in wave_ids:
            for country in country_codes:
                path = (self.root / 'data' / 'weights'
                        / f'wave_{wave}' / f'{country}.json')
                if not path.exists():
                    missing.append((country, wave))
                    continue
                try:
                    W, constructs = self.load_one(country, wave)
                    networks[(country, wave)] = W
                    if constructs_out is None:
                        constructs_out = constructs
                except Exception as e:
                    print(f"  Warning: failed to load {country} wave {wave}: {e}")

        if missing:
            print(f"  Note: {len(missing)} (country, wave) files not found.")

        return networks, constructs_out or []

    # ── Derived matrices ────────────────────────────────────────────────────

    @staticmethod
    def symmetrize(W: np.ndarray) -> np.ndarray:
        W_abs = np.abs(W)
        return (W_abs + W_abs.T) / 2

    @staticmethod
    def to_distance(W: np.ndarray) -> np.ndarray:
        W_sym = WVSJsonLoader.symmetrize(W)
        D = 1.0 - W_sym
        np.fill_diagonal(D, 0.0)
        return D

    @staticmethod
    def asymmetry(W: np.ndarray) -> np.ndarray:
        W_abs = np.abs(W)
        return W_abs - W_abs.T
```

### 5.2 Julia Bridge (`python/julia_bridge.py`)

```python
import subprocess
import json
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import tempfile
import os


class JuliaBridge:
    """
    Calls Julia scripts for computationally intensive operations,
    passing data via .npy scratch files.
    """

    def __init__(
        self,
        julia_dir: str,
        scratch_dir: str = './scratch',
        n_threads: int = 8,
        julia_bin: str = 'julia'
    ):
        self.julia_dir  = Path(julia_dir)
        self.scratch    = Path(scratch_dir)
        self.scratch.mkdir(parents=True, exist_ok=True)
        self.n_threads  = n_threads
        self.julia_bin  = julia_bin

    def _run(self, script: str, *args, timeout: int = 3600):
        """Execute a Julia script with arguments."""
        cmd = [
            self.julia_bin,
            f'--threads={self.n_threads}',
            str(self.julia_dir / script),
            *[str(a) for a in args]
        ]
        print(f"  → julia -t {self.n_threads} {script}")
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Julia script failed:\n{result.stderr}"
            )
        print(result.stdout)

    # ── Floyd-Warshall + mediators ──────────────────────────────────────────

    def floyd_warshall_batch(
        self,
        distance_matrices: Dict[str, np.ndarray]
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Run Floyd-Warshall on a batch of distance matrices.
        Returns dict key → {shortest, violations, mediators}.
        """
        fw_scratch = self.scratch / 'fw_input'
        fw_out     = self.scratch / 'fw_output'
        fw_scratch.mkdir(exist_ok=True)
        fw_out.mkdir(exist_ok=True)

        # Write inputs + manifest
        manifest = []
        for key, D in distance_matrices.items():
            safe_key = key.replace('/', '_')
            npy_path = fw_scratch / f'{safe_key}.npy'
            np.save(npy_path, D.astype(np.float64))
            manifest.append({'key': key, 'path': str(npy_path)})

        manifest_path = self.scratch / 'fw_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        self._run(
            'floyd_warshall_parallel.jl',
            str(manifest_path),
            str(fw_out)
        )

        # Read results
        results = {}
        for item in manifest:
            key = item['key']
            safe_key = key.replace('/', '_')
            results[key] = {
                'shortest':   np.load(fw_out / f'{safe_key}_shortest.npy'),
                'violations': np.load(fw_out / f'{safe_key}_violations.npy'),
                'mediators':  np.load(fw_out / f'{safe_key}_mediators.npy'),
            }
        return results

    # ── Spectral distances ──────────────────────────────────────────────────

    def spectral_distances(
        self,
        weight_matrices: Dict[str, np.ndarray]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Compute full pairwise spectral distance matrix.
        Returns (D_matrix, ordered_keys).
        """
        spec_scratch = self.scratch / 'spec_input'
        spec_scratch.mkdir(exist_ok=True)
        output_path = self.scratch / 'spectral_D.npy'

        manifest = []
        keys = list(weight_matrices.keys())
        for key in keys:
            safe_key = key.replace('/', '_')
            npy_path = spec_scratch / f'{safe_key}.npy'
            np.save(npy_path, weight_matrices[key].astype(np.float64))
            manifest.append({'key': key, 'path': str(npy_path)})

        manifest_path = self.scratch / 'spec_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        self._run(
            'spectral_distances_parallel.jl',
            str(manifest_path),
            str(output_path)
        )

        D = np.load(output_path)
        return D, keys

    # ── Ricci curvature ─────────────────────────────────────────────────────

    def ricci_curvature_batch(
        self,
        weight_matrices: Dict[str, np.ndarray],
        distance_matrices: Dict[str, np.ndarray],
        alpha: float = 0.5
    ) -> Dict[str, np.ndarray]:
        """
        Compute Ollivier-Ricci curvature for a batch of networks.
        Returns dict key → kappa matrix.
        """
        ricci_scratch = self.scratch / 'ricci_input'
        ricci_out     = self.scratch / 'ricci_output'
        ricci_scratch.mkdir(exist_ok=True)
        ricci_out.mkdir(exist_ok=True)

        manifest = []
        for key, W in weight_matrices.items():
            safe_key = key.replace('/', '_')
            w_path = ricci_scratch / f'{safe_key}_W.npy'
            d_path = ricci_scratch / f'{safe_key}_D.npy'
            np.save(w_path, W.astype(np.float64))
            np.save(d_path, distance_matrices[key].astype(np.float64))
            manifest.append({
                'key': key,
                'w_path': str(w_path),
                'd_path': str(d_path)
            })

        manifest_path = self.scratch / 'ricci_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        self._run(
            'ricci_curvature_parallel.jl',
            str(manifest_path),
            str(ricci_out),
            str(alpha)
        )

        results = {}
        for item in manifest:
            key = item['key']
            safe_key = key.replace('/', '_')
            results[key] = np.load(ricci_out / f'{safe_key}_ricci.npy')
        return results

    # ── Gromov-Wasserstein ──────────────────────────────────────────────────

    def gromov_wasserstein_batch(
        self,
        distance_matrices: Dict[str, np.ndarray],
        pairs: List[Tuple[str, str]]
    ) -> Dict[Tuple[str, str], Dict]:
        """
        Compute GW distances and transport plans for specified country pairs.
        Returns dict (key1, key2) → {gw_dist, transport}.
        """
        gw_scratch = self.scratch / 'gw_input'
        gw_out     = self.scratch / 'gw_output'
        gw_scratch.mkdir(exist_ok=True)
        gw_out.mkdir(exist_ok=True)

        # Save all needed distance matrices
        saved = {}
        for key, D in distance_matrices.items():
            if any(key in pair for pair in pairs):
                safe_key = key.replace('/', '_')
                npy_path = gw_scratch / f'{safe_key}.npy'
                np.save(npy_path, D.astype(np.float64))
                saved[key] = str(npy_path)

        manifest = []
        for key1, key2 in pairs:
            if key1 not in saved or key2 not in saved:
                continue
            manifest.append({
                'key1': key1,
                'key2': key2,
                'd1_path': saved[key1],
                'd2_path': saved[key2]
            })

        manifest_path = self.scratch / 'gw_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        self._run(
            'gromov_wasserstein_parallel.jl',
            str(manifest_path),
            str(gw_out)
        )

        results = {}
        for item in manifest:
            key1, key2 = item['key1'], item['key2']
            pair_key = f"{key1.replace('/','_')}__{key2.replace('/','_')}"
            dist_arr = np.load(gw_out / f'{pair_key}_gwdist.npy')
            T        = np.load(gw_out / f'{pair_key}_transport.npy')
            results[(key1, key2)] = {
                'gw_dist': float(dist_arr[0]),
                'transport': T
            }
        return results
```

### 5.3 Within-Network TDA (`python/within_tda.py`)

```python
import numpy as np
import ripser
from ripser import ripser as rips
import persim
from typing import Dict, List, Optional


class WithinNetworkTDA:

    def __init__(self, max_dim: int = 2, persistence_threshold: float = 0.05):
        self.max_dim = max_dim
        self.thresh  = persistence_threshold

    def compute_persistence(self, D: np.ndarray) -> Dict:
        result = rips(D, maxdim=self.max_dim, distance_matrix=True, thresh=1.0)
        dgms   = result['dgms']
        return {
            'dgms': dgms,
            'H0':   dgms[0],
            'H1':   dgms[1] if len(dgms) > 1 else np.empty((0, 2)),
            'H2':   dgms[2] if len(dgms) > 2 else np.empty((0, 2)),
        }

    def significant_features(self, dgm: np.ndarray) -> np.ndarray:
        finite = dgm[~np.isinf(dgm).any(axis=1)]
        pers   = finite[:, 1] - finite[:, 0]
        return finite[pers > self.thresh]

    def persistence_entropy(self, dgm: np.ndarray) -> float:
        finite = dgm[~np.isinf(dgm).any(axis=1)]
        if len(finite) == 0:
            return 0.0
        lt = finite[:, 1] - finite[:, 0]
        lt = lt[lt > 0]
        if len(lt) == 0:
            return 0.0
        p = lt / lt.sum()
        return float(-np.sum(p * np.log(p + 1e-12)))

    def betti_curve(
        self,
        dgms: List[np.ndarray],
        eps_range: np.ndarray
    ) -> np.ndarray:
        betti = np.zeros((len(eps_range), self.max_dim + 1))
        for k, dgm in enumerate(dgms[:self.max_dim + 1]):
            finite = dgm[~np.isinf(dgm).any(axis=1)]
            for i, eps in enumerate(eps_range):
                betti[i, k] = np.sum(
                    (finite[:, 0] <= eps) & (finite[:, 1] > eps)
                )
        return betti

    def analyze(
        self,
        W: np.ndarray,
        D: np.ndarray,
        fw_result: Optional[Dict] = None,
        ricci: Optional[np.ndarray] = None,
        eps_range: Optional[np.ndarray] = None,
    ) -> Dict:
        if eps_range is None:
            eps_range = np.linspace(0, 1, 100)

        pers  = self.compute_persistence(D)
        betti = self.betti_curve(pers['dgms'], eps_range)

        result = {
            'persistence':  pers,
            'betti_curve':  betti,
            'eps_range':    eps_range,
            'sig_H0':       self.significant_features(pers['H0']),
            'sig_H1':       self.significant_features(pers['H1']),
            'sig_H2':       self.significant_features(pers['H2']),
            'h0_entropy':   self.persistence_entropy(pers['H0']),
            'h1_entropy':   self.persistence_entropy(pers['H1']),
            'asymmetry':    np.abs(W) - np.abs(W).T,
        }

        result['n_clusters'] = len(result['sig_H0'])
        result['n_loops']    = len(result['sig_H1'])
        result['n_voids']    = len(result['sig_H2'])

        # Julia-computed quantities (if provided)
        if fw_result is not None:
            result['triangle_violations'] = fw_result['violations']
            result['mediator_scores']     = fw_result['mediators']
            result['shortest_path_D']     = fw_result['shortest']

        if ricci is not None:
            result['ricci_curvature'] = ricci
            # Bottleneck edges: most negative Ricci curvature
            result['bottleneck_edges'] = np.argwhere(
                ricci < np.percentile(ricci[ricci != 0], 10)
            )

        return result
```

### 5.4 Main Pipeline (`python/pipeline.py`)

```python
import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Tuple, List, Optional

from loader      import WVSJsonLoader
from julia_bridge import JuliaBridge
from within_tda  import WithinNetworkTDA

import ripser, persim
from sklearn.manifold import MDS
from sklearn.cluster  import AgglomerativeClustering


class WVSTopologyPipeline:

    def __init__(
        self,
        data_root:   str,
        julia_dir:   str,
        output_dir:  str  = './output',
        scratch_dir: str  = './scratch',
        n_threads:   int  = 8,
        persistence_threshold: float = 0.05,
    ):
        self.loader     = WVSJsonLoader(data_root)
        self.julia      = JuliaBridge(julia_dir, scratch_dir, n_threads)
        self.within_tda = WithinNetworkTDA(
            max_dim=2, persistence_threshold=persistence_threshold
        )
        self.output  = Path(output_dir)
        self.scratch = Path(scratch_dir)
        self.output.mkdir(parents=True, exist_ok=True)
        self.scratch.mkdir(parents=True, exist_ok=True)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _key(self, country: str, wave: int) -> str:
        return f"{country}_w{wave}"

    def _build_distance_dict(
        self,
        networks: Dict[Tuple[str, int], np.ndarray]
    ) -> Dict[str, np.ndarray]:
        return {
            self._key(c, w): self.loader.to_distance(W)
            for (c, w), W in networks.items()
        }

    def _build_weight_dict(
        self,
        networks: Dict[Tuple[str, int], np.ndarray]
    ) -> Dict[str, np.ndarray]:
        return {self._key(c, w): W for (c, w), W in networks.items()}

    # ── Step 1: Load ─────────────────────────────────────────────────────────

    def load(
        self,
        waves: Optional[List[int]] = None,
        countries: Optional[List[str]] = None
    ) -> Tuple[Dict, List[str]]:
        print("[1/6] Loading JSON weight matrices...")
        networks, constructs = self.loader.load_all(waves, countries)
        print(f"      Loaded {len(networks)} networks · {len(constructs)} constructs")
        return networks, constructs

    # ── Step 2: Julia — Floyd-Warshall + Ricci ───────────────────────────────

    def run_julia_within(
        self,
        networks: Dict[Tuple[str, int], np.ndarray],
        compute_ricci: bool = True,
        ricci_alpha: float = 0.5
    ) -> Tuple[Dict[str, Dict], Dict[str, np.ndarray]]:
        print("[2/6] Julia — Floyd-Warshall + mediator scores...")
        D_dict  = self._build_distance_dict(networks)
        W_dict  = self._build_weight_dict(networks)
        fw_results = self.julia.floyd_warshall_batch(D_dict)

        ricci_results = {}
        if compute_ricci:
            print("[2/6] Julia — Ricci curvature...")
            # Use shortest-path distances for Ricci (more geometrically meaningful)
            D_sp_dict = {k: v['shortest'] for k, v in fw_results.items()}
            ricci_results = self.julia.ricci_curvature_batch(
                W_dict, D_sp_dict, alpha=ricci_alpha
            )

        return fw_results, ricci_results

    # ── Step 3: Within-network TDA ───────────────────────────────────────────

    def run_within_tda(
        self,
        networks: Dict[Tuple[str, int], np.ndarray],
        fw_results: Dict[str, Dict],
        ricci_results: Dict[str, np.ndarray]
    ) -> Dict[Tuple[str, int], Dict]:
        print("[3/6] Within-network TDA (ripser)...")
        tda_results = {}
        for (country, wave), W in networks.items():
            key = self._key(country, wave)
            D   = self.loader.to_distance(W)
            fw  = fw_results.get(key)
            ric = ricci_results.get(key)
            tda_results[(country, wave)] = self.within_tda.analyze(
                W, D, fw_result=fw, ricci=ric
            )
            n_cl = tda_results[(country,wave)]['n_clusters']
            n_lp = tda_results[(country,wave)]['n_loops']
            print(f"      ✓ {country} w{wave}  β0={n_cl}  β1={n_lp}")
        return tda_results

    # ── Step 4: Between-network (per wave) ───────────────────────────────────

    def run_between_tda(
        self,
        networks: Dict[Tuple[str, int], np.ndarray],
        tda_results: Dict[Tuple[str, int], Dict],
        waves: List[int]
    ) -> Dict[int, Dict]:
        print("[4/6] Julia — spectral distances (between-network)...")
        between = {}

        for wave in waves:
            wave_nets = {
                self._key(c, w): W
                for (c, w), W in networks.items() if w == wave
            }
            if len(wave_nets) < 2:
                continue

            D_countries, keys = self.julia.spectral_distances(wave_nets)

            # TDA on country point cloud
            country_pers = ripser.ripser(
                D_countries, maxdim=1, distance_matrix=True
            )['dgms']

            # 2D embedding
            mds    = MDS(n_components=2, dissimilarity='precomputed',
                         random_state=42)
            coords = mds.fit_transform(D_countries)

            # Hierarchical clustering
            n_clusters = min(6, len(keys) - 1)
            clust_labels = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='precomputed', linkage='average'
            ).fit_predict(D_countries)

            # Save
            emb_df = pd.DataFrame({
                'key': keys,
                'country': [k.split('_w')[0] for k in keys],
                'wave': wave,
                'x': coords[:, 0],
                'y': coords[:, 1],
                'cluster': clust_labels
            })
            emb_df.to_csv(
                self.output / f'embedding_wave{wave}.csv', index=False
            )
            np.save(self.output / f'D_countries_wave{wave}.npy', D_countries)

            between[wave] = {
                'D_countries':    D_countries,
                'keys':           keys,
                'embedding':      emb_df,
                'country_pers':   country_pers,
                'clusters':       clust_labels,
            }
            print(f"      Wave {wave}: {len(keys)} countries embedded.")

        return between

    # ── Step 5: GW alignment for selected pairs ───────────────────────────────

    def run_gw_alignment(
        self,
        networks: Dict[Tuple[str, int], np.ndarray],
        pairs: List[Tuple[Tuple[str,int], Tuple[str,int]]],
        constructs: List[str]
    ) -> pd.DataFrame:
        print(f"[5/6] Julia — Gromov-Wasserstein for {len(pairs)} pairs...")
        D_dict = self._build_distance_dict(networks)

        gw_pairs = [
            (self._key(*p1), self._key(*p2))
            for p1, p2 in pairs
        ]
        gw_results = self.julia.gromov_wasserstein_batch(D_dict, gw_pairs)

        rows = []
        for (key1, key2), res in gw_results.items():
            c1, w1 = key1.rsplit('_w', 1)
            c2, w2 = key2.rsplit('_w', 1)
            T = res['transport']
            k = T.shape[0]
            for i in range(k):
                j_best = int(np.argmax(T[i]))
                rows.append({
                    'country1': c1, 'wave1': int(w1),
                    'country2': c2, 'wave2': int(w2),
                    'construct1': constructs[i] if i < len(constructs) else str(i),
                    'construct2': constructs[j_best] if j_best < len(constructs) else str(j_best),
                    'transport_mass': float(T[i, j_best]),
                    'gw_dist': res['gw_dist'],
                })

        df = pd.DataFrame(rows)
        df.to_csv(self.output / 'gw_alignments.csv', index=False)
        print(f"      GW alignments saved.")
        return df

    # ── Step 6: Summary + temporal ───────────────────────────────────────────

    def build_outputs(
        self,
        tda_results: Dict[Tuple[str, int], Dict],
        between_results: Dict[int, Dict],
        constructs: List[str]
    ) -> Dict:
        print("[6/6] Building summary outputs...")

        # Topological feature table
        rows = []
        for (country, wave), res in tda_results.items():
            row = {
                'country': country,
                'wave':    wave,
                'n_clusters':       res['n_clusters'],
                'n_loops':          res['n_loops'],
                'n_voids':          res['n_voids'],
                'h0_entropy':       res['h0_entropy'],
                'h1_entropy':       res['h1_entropy'],
                'max_asymmetry':    float(np.abs(res['asymmetry']).max()),
                'mean_asymmetry':   float(np.abs(res['asymmetry']).mean()),
            }
            if 'mediator_scores' in res:
                top_idx = int(np.argmax(res['mediator_scores']))
                row['top_mediator'] = (
                    constructs[top_idx] if top_idx < len(constructs) else str(top_idx)
                )
                row['top_mediator_score'] = float(res['mediator_scores'][top_idx])

            if 'ricci_curvature' in res:
                kappa = res['ricci_curvature']
                kappa_nonzero = kappa[kappa != 0]
                if len(kappa_nonzero):
                    row['mean_ricci']  = float(kappa_nonzero.mean())
                    row['min_ricci']   = float(kappa_nonzero.min())
            rows.append(row)

        summary = pd.DataFrame(rows).sort_values(['country', 'wave'])
        summary.to_csv(self.output / 'topological_summary.csv', index=False)

        # Convergence: mean cross-country distance per wave
        conv_rows = []
        for wave, br in sorted(between_results.items()):
            D = br['D_countries']
            upper = D[np.triu_indices_from(D, k=1)]
            conv_rows.append({
                'wave':            wave,
                'mean_distance':   float(upper.mean()),
                'std_distance':    float(upper.std()),
                'median_distance': float(np.median(upper)),
                'n_countries':     D.shape[0],
            })
        convergence = pd.DataFrame(conv_rows)
        convergence.to_csv(self.output / 'convergence.csv', index=False)

        print(f"      Outputs written to {self.output}/")
        return {'summary': summary, 'convergence': convergence}

    # ── Full run ─────────────────────────────────────────────────────────────

    def run(
        self,
        waves: Optional[List[int]] = None,
        countries: Optional[List[str]] = None,
        compute_ricci: bool = True,
        gw_pairs: Optional[List[Tuple]] = None,
    ) -> Dict:
        print("=" * 60)
        print("WVS TOPOLOGY PIPELINE  v2  (Julia-accelerated)")
        print("=" * 60)

        networks, constructs = self.load(waves, countries)
        fw_results, ricci_results = self.run_julia_within(
            networks, compute_ricci=compute_ricci
        )
        tda_results = self.run_within_tda(
            networks, fw_results, ricci_results
        )
        wave_list = sorted(set(w for _, w in networks))
        between   = self.run_between_tda(networks, tda_results, wave_list)

        gw_df = pd.DataFrame()
        if gw_pairs:
            gw_df = self.run_gw_alignment(networks, gw_pairs, constructs)

        outputs = self.build_outputs(tda_results, between, constructs)

        print("\n" + "=" * 60)
        print("DONE")
        print("=" * 60)

        return {
            'networks':     networks,
            'constructs':   constructs,
            'tda_results':  tda_results,
            'between':      between,
            'gw_alignments': gw_df,
            **outputs,
        }
```

---

## 6. Running the Pipeline

### One-time Julia setup
```bash
julia -t 8 julia/setup.jl
```

### Full run
```python
from python.pipeline import WVSTopologyPipeline

pipeline = WVSTopologyPipeline(
    data_root  = './wvs_data',
    julia_dir  = './julia',
    output_dir = './output',
    scratch_dir= './scratch',
    n_threads  = 8,
    persistence_threshold = 0.05,
)

results = pipeline.run(
    waves      = [6, 7],
    countries  = None,        # all available
    compute_ricci = True,
    gw_pairs   = [            # country pairs for GW alignment
        (('MEX', 7), ('BRA', 7)),
        (('USA', 7), ('DEU', 7)),
        (('CHN', 7), ('JPN', 7)),
    ]
)

# Key outputs in ./output/:
#   topological_summary.csv   — β₀, β₁, entropy, mediators, Ricci per country-wave
#   convergence.csv            — mean cross-country distance per wave
#   embedding_wave{N}.csv      — 2D MDS coordinates of countries
#   D_countries_wave{N}.npy    — full country distance matrix
#   gw_alignments.csv          — construct equivalences across country pairs
```

---

## 7. Computational Cost and Thread Allocation

| Step | Method | Complexity | Julia threads | Typical time (80 countries) |
|---|---|---|---|---|
| Floyd-Warshall | Parallel FW | O(k³) per network | 8, inner | ~2 min |
| Mediator scores | Parallel loop | O(k³) per network | 8, outer | ~3 min |
| Ricci curvature | Sinkhorn OT per edge | O(k² × OT) | 8, over edges | ~15 min |
| Spectral distances | Eigendecomposition + pairs | O(k³ + n²) | 8, over pairs | ~1 min |
| GW per pair | Entropic GW | O(k³) per pair | 8, over pairs | ~5 min per pair |
| Ripser (TDA) | Vietoris-Rips | Subexponential | Python (single) | ~1 min total |

**Total for 80 countries × 2 waves, 3 GW pairs:** approximately 30–45 minutes on 8 cores.

Ricci curvature dominates. Set `compute_ricci=False` for exploratory runs — all other outputs remain available.

---

## 8. Dependencies

```bash
# Python
pip install numpy pandas scipy networkx matplotlib seaborn scikit-learn
pip install ripser persim giotto-tda POT

# Julia (handled by setup.jl, but requires Julia ≥ 1.9)
# Install Julia: https://julialang.org/downloads/
# Set JULIA_NUM_THREADS=8 in shell profile, or use -t 8 flag
```
