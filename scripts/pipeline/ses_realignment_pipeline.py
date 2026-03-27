"""
SES Realignment Pipeline — Prefect Orchestration
=================================================

This script orchestrates the full re-computation of the Navegador bridge
estimates after SES variable realignment (Tam_loc direction, escol boundaries,
continuous edad).  It runs both the los_mex and WVS paths end-to-end, from
construct building through Julia sweeps to gamma-surface visualization.

WHY PREFECT?
------------
Prefect is a Python-native workflow orchestration framework.  Unlike Airflow
(DAG-based, server-heavy) or Make (file-based, no retries), Prefect lets you
write normal Python functions decorated with @task and @flow, and it handles:

  - **Dependency tracking**: tasks wait for upstream results automatically
  - **Parallel execution**: submit tasks concurrently with .submit()
  - **Retries**: failed tasks can retry with exponential backoff
  - **Observability**: built-in logging, task states, and a web UI
  - **Artifacts**: attach output files to task runs for inspection

To monitor a running pipeline, launch the Prefect UI in another terminal:
    $ prefect server start
    Then open http://localhost:4200 in your browser.

ARCHITECTURE
------------
The pipeline has two parallel branches (los_mex and WVS) that converge for
fingerprint computation, ontology patching, and gamma-surface assembly:

    ┌─────────────────┐          ┌──────────────────┐
    │  LOS_MEX PATH   │          │   WVS PATH       │
    └────────┬────────┘          └────────┬─────────┘
             │                            │
    1. build_constructs()        1. build_wvs_constructs()
             │                            │
    2. export_for_julia()        2. export_wvs_for_julia()
             │                            │
    3. julia_los_mex_sweep()     ├─→ julia_wvs_geographic()  (~10h)
             │                   └─→ julia_wvs_temporal()     (~42m)
             │                            │
             └──────────┬─────────────────┘
                        ▼
             4. compute_fingerprints()
                        │
             5. patch_ontology_bridges()
                        │
             6. build_gamma_surface()
                        │
             7. visualize()

USAGE
-----
    # Full pipeline (both datasets, ~11 hours):
    conda run -n nvg_py13_env python scripts/pipeline/ses_realignment_pipeline.py

    # Los_mex only (~45 minutes):
    conda run -n nvg_py13_env python scripts/pipeline/ses_realignment_pipeline.py --los-mex-only

    # WVS only (~10.5 hours):
    conda run -n nvg_py13_env python scripts/pipeline/ses_realignment_pipeline.py --wvs-only

    # Dry run (print task graph, no execution):
    conda run -n nvg_py13_env python scripts/pipeline/ses_realignment_pipeline.py --dry-run
"""

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
#
# Prefect's API surface is small.  The two core decorators are:
#   @flow  — marks a function as the top-level orchestration entry point.
#            Flows can call tasks and other flows (sub-flows).
#   @task  — marks a function as an individual unit of work.  Tasks get
#            their own log context, retry logic, caching, and state tracking.
#
# `get_run_logger()` returns a logger scoped to the current task/flow run.
# It writes to both stdout and Prefect's log store (visible in the UI).
#
# `create_markdown_artifact()` attaches rich text to a task run.  We use it
# to record sweep statistics (pair counts, significance rates) so they're
# visible in the Prefect UI without digging through logs.

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact

# ═══════════════════════════════════════════════════════════════════════════
# PATH CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
#
# All paths are absolute and resolved relative to the navegador repo root.
# This makes the pipeline work regardless of the current working directory.
#
# The Julia bridge lives in a sibling worktree (navegador_julia_bridge).
# Julia scripts reference data files in the main navegador repo via the
# manifest.json, which contains absolute paths to the domain CSVs.

# Resolve repo root: this script is at scripts/pipeline/ses_realignment_pipeline.py
# so repo root is two levels up from the script's directory.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Julia bridge worktree — sibling directory to the main repo.
# This is where julia/src/, julia/scripts/, and julia/test/ live.
JULIA_BRIDGE_ROOT = REPO_ROOT.parent / "navegador_julia_bridge" / "julia"

# Data output directories
RESULTS_DIR = REPO_ROOT / "data" / "results"
LOS_MEX_BRIDGE_DIR = REPO_ROOT / "data" / "julia_bridge"
WVS_BRIDGE_DIR = REPO_ROOT / "data" / "julia_bridge_wvs"

# Conda environment name for Python tasks.
# All navegador Python code runs inside this conda env, which has pandas,
# statsmodels, scipy, and all other dependencies pre-installed.
CONDA_ENV = "nvg_py13_env"

# Number of Julia threads.  Julia's `Threads.@threads` macro distributes
# loop iterations across this many OS threads.  8 is optimal for the
# flat-parallel geographic sweep on an 8-core machine.
JULIA_THREADS = 8

# Sweep output files that Julia's resume logic checks.
# If these exist, Julia skips already-computed pairs.  After SES realignment
# we need fresh sweeps — old results use the wrong SES encoding.
# The pipeline's --fresh flag renames these to *.pre_realignment.json
# before launching Julia, forcing a full recompute.
SWEEP_OUTPUTS = {
    "los_mex": RESULTS_DIR / "construct_dr_sweep_v5_julia_v4.json",
    "wvs_geographic": RESULTS_DIR / "wvs_geographic_sweep_w7.json",
    "wvs_temporal": RESULTS_DIR / "wvs_temporal_sweep_mex.json",
}


def archive_old_sweep(key: str) -> None:
    """
    Rename an existing sweep output so Julia starts fresh.

    Instead of deleting, we rename to *.pre_realignment.json so the old
    results are preserved for comparison.  If the archive already exists
    (from a previous --fresh run), it is overwritten.

    Parameters
    ----------
    key : str
        One of "los_mex", "wvs_geographic", "wvs_temporal".
    """
    path = SWEEP_OUTPUTS[key]
    if path.exists():
        archive = path.with_suffix(".pre_realignment.json")
        path.rename(archive)
        logger = get_run_logger()
        logger.info(f"Archived old sweep: {path.name} → {archive.name}")


# ═══════════════════════════════════════════════════════════════════════════
# HELPER: run_script()
# ═══════════════════════════════════════════════════════════════════════════
#
# All pipeline tasks delegate to existing standalone scripts via subprocess.
# This "orchestration-only" pattern keeps the pipeline decoupled from script
# internals — the same commands you'd run manually in a terminal.
#
# Why subprocess instead of importing Python functions directly?
#   1. Scripts have their own sys.path setup and argparse entry points.
#   2. Julia sweeps are inherently subprocess calls.
#   3. Isolation: a segfault in Julia doesn't crash the Prefect process.
#   4. Reproducibility: the pipeline log shows exact shell commands.

def _stream_subprocess(
    cmd: list[str],
    cwd: str,
    env: dict,
    timeout: int | None,
    label: str,
) -> int:
    """
    Run a subprocess and stream its output line-by-line to the Prefect logger.

    WHY STREAMING MATTERS
    ---------------------
    `subprocess.run(capture_output=True)` buffers ALL stdout/stderr in memory
    until the child process exits.  For a Julia sweep that runs 40 minutes or
    10 hours, this means:
      - The terminal shows NOTHING until the sweep finishes
      - You can't tell if it's making progress or hung
      - If the process is killed, you lose all diagnostic output

    `subprocess.Popen` + line-by-line reading solves this.  Each line Julia
    prints (e.g., "Pair 500/4135  γ=+0.012  CI=[...]") appears in real time
    in both the terminal and the Prefect UI.

    HOW IT WORKS
    ------------
    1. `Popen()` starts the child process and returns immediately.
    2. `stdout=subprocess.PIPE` connects the child's stdout to a pipe we can
       read from.  `stderr=subprocess.STDOUT` merges stderr into the same pipe
       so we get a single interleaved stream (like running in a terminal).
    3. `iter(proc.stdout.readline, "")` reads one line at a time until EOF.
       This is a blocking iterator — it waits for each line, so the loop
       naturally follows the child's pace.
    4. `proc.wait(timeout=remaining)` blocks until the process exits.
       We subtract elapsed time from the timeout to enforce the overall limit.

    TIMEOUT HANDLING
    ----------------
    Popen doesn't have a built-in timeout.  We track wall-clock time manually:
      - Before each readline, check if we've exceeded the timeout
      - After the read loop, use `proc.wait(timeout=remaining)` as a final guard
      - If timeout is exceeded, `proc.kill()` sends SIGKILL and we raise TimeoutError

    Parameters
    ----------
    cmd : list[str]
        Command and arguments (e.g., ["julia", "-t8", "script.jl"]).
    cwd : str
        Working directory for the child process.
    env : dict
        Environment variables (copy of os.environ with modifications).
    timeout : int or None
        Maximum wall-clock seconds.  None = no limit.
    label : str
        Human-readable prefix for log messages.

    Returns
    -------
    int
        The child process's exit code (0 = success).

    Raises
    ------
    subprocess.CalledProcessError
        If the child exits with a non-zero return code.
    subprocess.TimeoutExpired
        If wall-clock time exceeds `timeout`.
    """
    logger = get_run_logger()
    start = time.time()

    # Popen starts the process and returns a handle immediately.
    # Unlike subprocess.run(), it does NOT wait for the process to finish.
    #
    # Key arguments:
    #   stdout=PIPE      — we'll read stdout line by line
    #   stderr=STDOUT    — merge stderr into stdout (single stream)
    #   text=True        — decode bytes as UTF-8 strings
    #   bufsize=1        — line-buffered (flush after each newline)
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,   # merge stderr into stdout stream
        text=True,
        bufsize=1,                  # line-buffered for real-time output
    )

    try:
        # Read stdout line by line until the process closes the pipe (EOF).
        # `iter(callable, sentinel)` calls `proc.stdout.readline` repeatedly
        # until it returns "" (empty string = EOF = process exited or closed stdout).
        #
        # Each line is logged immediately — this is what makes the output
        # visible in real time instead of buffered until process exit.
        for line in iter(proc.stdout.readline, ""):
            # Strip trailing newline for cleaner log output.
            stripped = line.rstrip("\n")
            if stripped:
                logger.info(f"[{label}] {stripped}")

            # Check timeout between lines.
            # This catches long-running processes even if they're still
            # producing output (e.g., a sweep printing progress but stuck
            # on one pair for too long overall).
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed > timeout:
                    proc.kill()
                    raise subprocess.TimeoutExpired(cmd, timeout)

        # Wait for the process to fully exit and collect its return code.
        # The read loop above may finish before the process exits (if it
        # closes stdout early), so we need an explicit wait.
        remaining = None
        if timeout is not None:
            remaining = max(0, timeout - (time.time() - start))
        returncode = proc.wait(timeout=remaining)

    except subprocess.TimeoutExpired:
        # If timeout expired during wait(), kill the process.
        proc.kill()
        proc.wait()   # reap the zombie process
        raise

    elapsed = time.time() - start
    logger.info(f"[{label}] Completed in {elapsed:.1f}s ({elapsed / 60:.1f} min)")

    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, cmd)

    return returncode


def run_python_script(
    script_path: str,
    args: list[str] | None = None,
    timeout: int | None = None,
    label: str = "",
) -> None:
    """
    Run a Python script inside the conda environment via `conda run`.

    Output is streamed line-by-line to the Prefect logger in real time.

    Parameters
    ----------
    script_path : str
        Path to the Python script, relative to REPO_ROOT or absolute.
    args : list[str], optional
        Command-line arguments to pass to the script.
    timeout : int, optional
        Maximum seconds before killing the process.  None = no limit.
    label : str
        Human-readable name for log messages (e.g., "build_constructs").

    Notes
    -----
    `conda run -n ENV --no-capture-output` executes the command inside the
    named conda environment.  `--no-capture-output` ensures conda itself
    doesn't buffer the child's output.

    `PYTHONPATH` is set to include the repo root so that scripts can import
    modules like `ses_regression`, `wvs_loader`, etc. without sys.path hacks.
    """
    logger = get_run_logger()

    # Build the command list.
    # `conda run -n <env>` activates the environment without requiring
    # the user to have run `conda activate` first.
    cmd = [
        "conda", "run",
        "-n", CONDA_ENV,
        "--no-capture-output",      # don't let conda buffer output
        "python", "-u",             # -u = unbuffered Python stdout
        str(script_path),
    ]
    if args:
        cmd.extend(args)

    # Set PYTHONPATH so scripts can import from the repo root.
    # os.environ is inherited by subprocess — we modify a copy.
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    logger.info(f"[{label}] Running: {' '.join(cmd)}")

    _stream_subprocess(cmd, cwd=str(REPO_ROOT), env=env, timeout=timeout, label=label)


def run_julia_script(
    script_path: str,
    timeout: int | None = None,
    label: str = "",
) -> None:
    """
    Run a Julia script with multi-threading enabled.

    Output is streamed line-by-line to the Prefect logger in real time,
    so you can see Julia's per-pair progress (e.g., "Pair 500/4135 γ=...")
    as it happens — not buffered until the 40-minute sweep finishes.

    Parameters
    ----------
    script_path : str
        Path to the Julia script (absolute or relative to JULIA_BRIDGE_ROOT).
    timeout : int, optional
        Maximum seconds.  Geographic sweep needs ~50,400 (14 hours).
    label : str
        Human-readable name for log messages.

    Notes
    -----
    Julia flags explained:
      `-t 8`          : start 8 worker threads (Threads.nthreads() == 8)
      `--project=.`   : activate the Project.toml in the current directory,
                         so that `using NavegadorBridge` finds our module
      `--startup-file=no` : skip ~/.julia/config/startup.jl for reproducibility

    The PATH is prepended with juliaup's bin directory so that the `julia`
    binary is found even if the user hasn't added it to their shell profile.
    """
    logger = get_run_logger()

    # Ensure julia is on PATH via juliaup.
    # juliaup installs julia to ~/.juliaup/bin/ and manages versions.
    env = os.environ.copy()
    juliaup_bin = Path.home() / ".juliaup" / "bin"
    env["PATH"] = f"{juliaup_bin}:{env.get('PATH', '')}"

    cmd = [
        "julia",
        f"-t{JULIA_THREADS}",       # number of worker threads
        "--project=.",               # activate local Project.toml
        "--startup-file=no",         # skip user startup for reproducibility
        str(script_path),
    ]

    logger.info(f"[{label}] Running: {' '.join(cmd)}")
    logger.info(f"[{label}] Working dir: {JULIA_BRIDGE_ROOT}")

    _stream_subprocess(
        cmd, cwd=str(JULIA_BRIDGE_ROOT), env=env, timeout=timeout, label=label,
    )


# ═══════════════════════════════════════════════════════════════════════════
# TASKS — Individual units of work
# ═══════════════════════════════════════════════════════════════════════════
#
# PREFECT TASK CONCEPTS:
#
# @task decorator turns a function into a Prefect task.  Key parameters:
#
#   name : str
#       Display name in the UI and logs.  Defaults to function name.
#
#   retries : int
#       How many times to retry on failure.  Useful for flaky operations
#       (network calls, OOM on large datasets).  0 = no retries (default).
#
#   retry_delay_seconds : int | list[int]
#       Wait time between retries.  A list gives exponential backoff:
#       [10, 30, 60] means wait 10s, 30s, 60s for retries 1, 2, 3.
#
#   timeout_seconds : int
#       Kill the task if it runs longer than this.  Essential for Julia
#       sweeps that might hang on ill-conditioned data.
#
#   tags : list[str]
#       Categorize tasks for filtering in the UI.  We use "python", "julia",
#       "analysis" to group related tasks.
#
#   log_prints : bool
#       If True, print() statements inside the task are captured by Prefect's
#       logger.  We set this globally via the flow decorator instead.
#
# TASK vs FLOW:
#   Tasks are the smallest trackable unit — they can't contain other tasks.
#   Flows can contain tasks and sub-flows.  Think of flows as "chapters"
#   and tasks as "paragraphs".


# ── LOS_MEX PATH ─────────────────────────────────────────────────────────

@task(
    name="build_los_mex_constructs",
    tags=["python", "los_mex", "constructs"],
    timeout_seconds=300,  # 5 min — normally takes ~5s
)
def build_los_mex_constructs() -> Path:
    """
    Build aggregated construct columns (agg_*) in los_mex survey DataFrames.

    Reads the Semantic Variable Selection v4 spec and creates construct
    aggregates scaled to [1, 10].  Handles reflective scales (mean with
    reverse coding), tier-2 constructs (single best item by item-total
    correlation), and formative indices (additive gateway counts).

    Returns the path to the construct manifest JSON.
    """
    script = REPO_ROOT / "scripts" / "debug" / "build_construct_variables.py"
    run_python_script(str(script), label="build_los_mex_constructs")

    manifest = RESULTS_DIR / "construct_variable_manifest.json"
    assert manifest.exists(), f"Expected output not found: {manifest}"
    return manifest


@task(
    name="export_los_mex_for_julia",
    tags=["python", "los_mex", "export"],
    timeout_seconds=300,
)
def export_los_mex_for_julia() -> Path:
    """
    Export los_mex construct DataFrames to per-domain CSVs for Julia.

    Creates one CSV per domain (e.g., CIE.csv, REL.csv) containing SES
    columns + agg_* construct columns.  Also outputs:
      - manifest.json: maps domain codes to CSV file paths
      - v5_pairs.csv: all cross-domain construct pairs to estimate

    These are read by Julia's run_v5_sweep.jl.
    """
    script = REPO_ROOT / "scripts" / "debug" / "export_constructs_for_julia.py"
    run_python_script(str(script), label="export_los_mex_for_julia")

    manifest = LOS_MEX_BRIDGE_DIR / "manifest.json"
    assert manifest.exists(), f"Expected output not found: {manifest}"
    return manifest


@task(
    name="julia_los_mex_sweep",
    tags=["julia", "los_mex", "sweep"],
    retries=1,
    retry_delay_seconds=60,
    # 2 hours timeout — normally takes ~40 min, but retries might need headroom.
    # The retry is for transient OOM on large bootstrap matrices.
    timeout_seconds=7200,
)
def julia_los_mex_sweep() -> Path:
    """
    Run the los_mex construct-level DR bridge sweep in Julia.

    Estimates Goodman-Kruskal γ for all cross-domain construct pairs using
    the Doubly Robust (AIPW) estimator with 200 bootstrap iterations.

    The Julia implementation is ~15x faster than Python's statsmodels-based
    estimator because:
      1. Newton solver converges reliably (vs. BFGS maxiter=100 cap)
      2. Multi-threaded bootstrap (Threads.@threads over 8 cores)
      3. No Python GIL overhead

    Output: construct_dr_sweep_v5_julia_v4.json
    Expected: ~4,100 pairs, ~40-45 minutes on 8 threads.
    """
    logger = get_run_logger()

    script = JULIA_BRIDGE_ROOT / "scripts" / "run_v5_sweep.jl"
    run_julia_script(str(script), timeout=7200, label="julia_los_mex_sweep")

    # Validate output
    output = RESULTS_DIR / "construct_dr_sweep_v5_julia_v4.json"
    assert output.exists(), f"Sweep output not found: {output}"

    # Log summary statistics and create a Prefect artifact.
    with open(output) as f:
        data = json.load(f)
    n_done = len(data.get("estimates", {}))
    n_skip = len(data.get("skipped", {}))
    n_sig = sum(1 for e in data["estimates"].values() if e.get("excl_zero"))
    pct = 100 * n_sig / n_done if n_done else 0

    summary = (
        f"## Los_Mex Sweep Results\n\n"
        f"- **Pairs completed**: {n_done}\n"
        f"- **Pairs skipped**: {n_skip}\n"
        f"- **Significant (CI excl 0)**: {n_sig} ({pct:.1f}%)\n"
    )
    logger.info(summary)
    create_markdown_artifact(summary, key="los-mex-sweep-results")

    return output


# ── WVS PATH ─────────────────────────────────────────────────────────────

@task(
    name="build_wvs_constructs",
    tags=["python", "wvs", "constructs"],
    timeout_seconds=1800,  # 30 min — temporal (7 waves) can take ~12 min
)
def build_wvs_constructs(
    waves: list[int],
    countries: list[str] | None = None,
    scope: str = "geographic",
) -> Path:
    """
    Build WVS construct aggregates for specified wave×country combinations.

    This is the WVS equivalent of build_los_mex_constructs.  For each
    (wave, country) context, it resolves Q-codes to the appropriate column
    names, builds wvs_agg_* columns, and saves a pickle cache + JSON manifest.

    Parameters
    ----------
    waves : list[int]
        WVS wave numbers to process (1-7).  Wave 7 = geographic, 1-7 = temporal.
    countries : list[str], optional
        ISO alpha-3 country codes.  None = all countries in the wave.
        For temporal sweep, pass ["MEX"].
    scope : str
        "geographic" or "temporal".  Determines output filenames so the two
        scopes don't overwrite each other's cache and manifest files.
        E.g., scope="geographic" → wvs_multi_construct_cache_geographic.pkl

    Returns
    -------
    Path to the scope-specific construct manifest JSON.
    """
    script = REPO_ROOT / "scripts" / "debug" / "build_wvs_constructs_multi.py"

    # Build argument list.
    # --scope ensures output files are scope-specific (no overwrites).
    args = ["--waves"] + [str(w) for w in waves] + ["--scope", scope]
    if countries:
        args.extend(["--countries"] + countries)

    run_python_script(str(script), args=args, label=f"build_wvs_constructs_{scope}")

    manifest = RESULTS_DIR / f"wvs_multi_construct_manifest_{scope}.json"
    assert manifest.exists(), f"Expected output not found: {manifest}"
    return manifest


@task(
    name="export_wvs_for_julia",
    tags=["python", "wvs", "export"],
    timeout_seconds=600,
)
def export_wvs_for_julia(scope: str = "geographic") -> Path:
    """
    Export WVS construct DataFrames to per-context CSVs for Julia.

    Reads the scope-specific WVS construct cache (pickle) and writes one CSV
    per (wave, country) context.  Also outputs wvs_pairs.csv (all cross-domain
    pairs) and wvs_manifest.json (context metadata with CSV paths).

    Parameters
    ----------
    scope : str
        "geographic" or "temporal".  Determines which cache/manifest files
        to read.  The export always writes to the same output directory
        (data/julia_bridge_wvs/) — CSVs accumulate, and the manifest is
        overwritten.  Run geographic last so the final manifest has all
        66 W7 contexts for Julia's geographic sweep.
    """
    script = REPO_ROOT / "scripts" / "debug" / "export_wvs_for_julia.py"

    # Point the export script at the scope-specific cache and manifest.
    cache_path = RESULTS_DIR / f"wvs_multi_construct_cache_{scope}.pkl"
    manifest_path = RESULTS_DIR / f"wvs_multi_construct_manifest_{scope}.json"

    args = [
        "--cache", str(cache_path),
        "--manifest", str(manifest_path),
    ]
    run_python_script(str(script), args=args, label=f"export_wvs_{scope}")

    manifest = WVS_BRIDGE_DIR / "wvs_manifest.json"
    assert manifest.exists(), f"Expected output not found: {manifest}"
    return manifest


@task(
    name="julia_wvs_geographic_sweep",
    tags=["julia", "wvs", "sweep", "geographic"],
    retries=1,
    retry_delay_seconds=300,  # 5 min backoff before retry
    # 18 hours timeout — sweep takes ~11-14h with continuous edad.
    # Previous 14h limit (50400s) timed out at 97.2% completion.
    timeout_seconds=64800,
)
def julia_wvs_geographic_sweep() -> Path:
    """
    Run the WVS geographic sweep: all construct pairs × 66 countries (Wave 7).

    Uses `run_wvs_geographic_fast.jl` — the FLAT-PARALLEL variant that puts
    all (country, pair) combinations into a single thread pool.  This avoids
    the batch-per-country pattern where one slow country (e.g., large-N
    India or USA) blocks the entire batch, wasting idle threads.

    The flat approach reduced runtime from ~15h to ~9.7h in empirical testing.

    Output: wvs_geographic_sweep_w7.json
    Expected: ~68,000 estimates across 66 countries.
    """
    logger = get_run_logger()

    # IMPORTANT: use the _fast variant (flat-parallel), not the batched one.
    script = JULIA_BRIDGE_ROOT / "scripts" / "run_wvs_geographic_fast.jl"
    run_julia_script(str(script), timeout=50400, label="julia_wvs_geographic")

    output = RESULTS_DIR / "wvs_geographic_sweep_w7.json"
    assert output.exists(), f"Sweep output not found: {output}"

    with open(output) as f:
        data = json.load(f)
    n_done = len(data.get("estimates", {}))
    n_sig = sum(1 for e in data["estimates"].values() if e.get("excl_zero"))
    pct = 100 * n_sig / n_done if n_done else 0

    summary = (
        f"## WVS Geographic Sweep Results\n\n"
        f"- **Estimates**: {n_done:,}\n"
        f"- **Significant**: {n_sig:,} ({pct:.1f}%)\n"
    )
    logger.info(summary)
    create_markdown_artifact(summary, key="wvs-geographic-sweep-results")

    return output


@task(
    name="julia_wvs_temporal_sweep",
    tags=["julia", "wvs", "sweep", "temporal"],
    retries=1,
    retry_delay_seconds=60,
    timeout_seconds=7200,  # 2 hours — normally ~42 min
)
def julia_wvs_temporal_sweep() -> Path:
    """
    Run the WVS temporal sweep: construct pairs across 7 Mexico waves (1981-2022).

    Estimates γ for each construct pair within each wave, enabling analysis
    of how SES-attitude relationships change over 40 years of Mexican history.

    Output: wvs_temporal_sweep_mex.json
    Expected: ~2,300 estimates across 5-7 waves (early waves have fewer constructs).
    """
    logger = get_run_logger()

    script = JULIA_BRIDGE_ROOT / "scripts" / "run_wvs_temporal.jl"
    run_julia_script(str(script), timeout=7200, label="julia_wvs_temporal")

    output = RESULTS_DIR / "wvs_temporal_sweep_mex.json"
    assert output.exists(), f"Sweep output not found: {output}"

    with open(output) as f:
        data = json.load(f)
    n_done = len(data.get("estimates", {}))

    summary = (
        f"## WVS Temporal Sweep Results\n\n"
        f"- **Estimates**: {n_done:,}\n"
    )
    logger.info(summary)
    create_markdown_artifact(summary, key="wvs-temporal-sweep-results")

    return output


# ── ANALYSIS TASKS (run after all sweeps complete) ────────────────────────

@task(
    name="compute_ses_fingerprints",
    tags=["python", "analysis"],
    timeout_seconds=600,  # 10 min — normally ~2 min
)
def compute_ses_fingerprints() -> Path:
    """
    Compute 4D SES fingerprint vectors for all constructs and items.

    Each construct gets a vector [ρ_escol, ρ_Tam_loc, ρ_sexo, ρ_edad]
    measuring how strongly it correlates with each SES dimension.

    The fingerprint dot product predicts bridge γ sign at 99.4% accuracy:
    two constructs whose SES profiles point in the same 4D direction are
    co-elevated by the same sociodemographic position → γ > 0.
    """
    script = REPO_ROOT / "scripts" / "debug" / "compute_ses_fingerprints.py"
    run_python_script(str(script), label="compute_ses_fingerprints")

    output = RESULTS_DIR / "ses_fingerprints.json"
    assert output.exists(), f"Expected output not found: {output}"
    return output


@task(
    name="patch_ontology_bridges",
    tags=["python", "analysis"],
    timeout_seconds=120,
)
def patch_ontology_bridges() -> Path:
    """
    Update bridge γ signs in the knowledge graph after fingerprint changes.

    When a construct's fingerprint vector changes direction (e.g., Tam_loc
    sign flip due to scale reversal), bridges involving that construct may
    need their γ sign flipped to maintain consistency with the geometric
    prediction: sign(γ) = sign(dot(fingerprint_A, fingerprint_B)).
    """
    script = REPO_ROOT / "scripts" / "debug" / "patch_kg_ontology_bridges.py"
    run_python_script(str(script), label="patch_ontology_bridges")

    output = RESULTS_DIR / "kg_ontology_v2.json"
    assert output.exists(), f"Expected output not found: {output}"
    return output


@task(
    name="build_gamma_surface",
    tags=["python", "analysis"],
    timeout_seconds=120,
)
def build_gamma_surface() -> Path:
    """
    Assemble the unified γ-surface from all sweep outputs.

    Combines 4 sources:
      1. los_mex construct sweep (Julia)
      2. WVS geographic sweep (66 countries, Wave 7)
      3. WVS temporal sweep (Mexico, 7 waves)
      4. WVS Mexico W7 within-survey validation

    Output: gamma_surface.json (~72,000+ entries indexed by
    dataset, country, wave, and construct pair).
    """
    script = REPO_ROOT / "scripts" / "debug" / "build_gamma_surface.py"
    run_python_script(str(script), label="build_gamma_surface")

    output = RESULTS_DIR / "gamma_surface.json"
    assert output.exists(), f"Expected output not found: {output}"

    # Log surface size
    logger = get_run_logger()
    with open(output) as f:
        surface = json.load(f)
    # Surface may be a dict or list depending on format
    n_entries = len(surface) if isinstance(surface, (dict, list)) else 0
    logger.info(f"Gamma surface: {n_entries:,} entries")
    create_markdown_artifact(
        f"## Gamma Surface\n\n- **Entries**: {n_entries:,}",
        key="gamma-surface-size",
    )

    return output


@task(
    name="visualize_gamma_surface",
    tags=["python", "visualization"],
    timeout_seconds=600,  # 10 min — plotting can be slow
)
def visualize_gamma_surface() -> list[Path]:
    """
    Generate γ-surface visualizations: PCA, heatmaps, temporal ribbons.

    Produces 4 PNG files:
      1. Country PCA scatter (colored by cultural zone)
      2. Countries × top-50 pairs dendrogram heatmap
      3. Temporal ribbon plots (Mexico 1981-2022)
      4. Mexico trajectory across waves in PCA space
    """
    script = REPO_ROOT / "scripts" / "debug" / "visualize_gamma_surface.py"
    run_python_script(str(script), label="visualize_gamma_surface")

    expected = [
        "gamma_surface_pca.png",
        "gamma_surface_heatmap.png",
        "gamma_surface_temporal.png",
        "gamma_surface_mex_trajectory.png",
    ]
    outputs = [RESULTS_DIR / f for f in expected]
    for p in outputs:
        if not p.exists():
            get_run_logger().warning(f"Expected visualization not found: {p}")
    return outputs


# ═══════════════════════════════════════════════════════════════════════════
# FLOW — Top-level orchestration
# ═══════════════════════════════════════════════════════════════════════════
#
# PREFECT FLOW CONCEPTS:
#
# @flow is the entry point for a pipeline run.  Key parameters:
#
#   name : str
#       The flow name shown in the Prefect UI.
#
#   log_prints : bool
#       If True, all print() calls inside the flow (and its tasks) are
#       redirected to Prefect's structured logger.  This means you can
#       use print() normally and it shows up in the UI with timestamps.
#
#   timeout_seconds : int
#       Maximum total wall-clock time for the entire flow.
#
# PARALLEL EXECUTION:
#
#   task.submit() returns a PrefectFuture immediately (non-blocking).
#   future.result() blocks until the task completes and returns its value.
#
#   To run tasks in parallel:
#       future_a = task_a.submit()
#       future_b = task_b.submit()   # starts concurrently with task_a
#       result_a = future_a.result() # blocks until task_a finishes
#       result_b = future_b.result() # blocks until task_b finishes
#
#   Tasks without .submit() run sequentially (blocking the flow).
#   Use .submit() when tasks are independent and can overlap.
#
# DEPENDENCY TRACKING:
#
#   Prefect tracks which tasks depend on which by observing data flow.
#   If task_b uses the return value of task_a, Prefect knows task_a
#   must complete before task_b starts.  This is implicit — no need
#   for explicit `depends_on` declarations.

@flow(
    name="ses_realignment_pipeline",
    log_prints=True,         # capture print() as structured logs
    timeout_seconds=57600,   # 16 hours total limit (full run ~11h)
)
def ses_realignment_pipeline(
    run_los_mex: bool = False,
    run_wvs_geographic: bool = False,
    run_wvs_temporal: bool = False,
    fresh: bool = False,
) -> dict:
    """
    Full SES realignment pipeline: rebuild constructs → sweep → analyze.

    Each dataset path is an explicit opt-in flag — nothing runs by default.
    This prevents accidentally launching a 10-hour geographic sweep when
    you only wanted a 40-minute los_mex run.

    Parameters
    ----------
    run_los_mex : bool
        If True, run the los_mex path (construct build + Julia sweep, ~40 min).
    run_wvs_geographic : bool
        If True, run WVS geographic sweep (66 countries, Wave 7, ~10 hours).
        Uses run_wvs_geographic_fast.jl (flat-parallel across all countries).
    run_wvs_temporal : bool
        If True, run WVS temporal sweep (Mexico, 7 waves, ~42 min).
    fresh : bool
        If True, archive existing sweep outputs before running Julia.
        Julia's sweep scripts have resume logic — they skip pairs found in
        the output JSON.  After SES realignment the old estimates use wrong
        encodings, so --fresh renames them to *.pre_realignment.json and
        forces a full recompute.  Without --fresh, Julia resumes and may
        finish in seconds with stale data.

    Returns
    -------
    dict
        Summary of all completed tasks and their output paths.
    """
    logger = get_run_logger()

    # Determine which WVS sub-paths are active.
    # Geographic and temporal share the construct-build and export steps,
    # so we need WVS data prep if either is requested.
    run_wvs = run_wvs_geographic or run_wvs_temporal

    logger.info("=" * 60)
    logger.info("SES Realignment Pipeline — Starting")
    logger.info(f"  los_mex:        {'ON' if run_los_mex else 'OFF'}")
    logger.info(f"  WVS geographic: {'ON' if run_wvs_geographic else 'OFF'}  (66 countries, W7)")
    logger.info(f"  WVS temporal:   {'ON' if run_wvs_temporal else 'OFF'}  (Mexico, 7 waves)")
    logger.info(f"  fresh:          {'YES — archive old sweeps' if fresh else 'NO — resume if exists'}")
    logger.info(f"  Repo:           {REPO_ROOT}")
    logger.info(f"  Julia:          {JULIA_BRIDGE_ROOT}")
    logger.info("=" * 60)

    if not (run_los_mex or run_wvs):
        logger.warning("Nothing selected! Use --los-mex, --wvs-geographic, --wvs-temporal, or --all.")
        return {}

    # ── Archive old sweep outputs if --fresh ──────────────────────────────
    #
    # Julia's sweep scripts (run_v5_sweep.jl, run_wvs_geographic_fast.jl,
    # run_wvs_temporal.jl) all have checkpoint/resume logic: they load the
    # output JSON at startup and skip any pair already present.  This is
    # great for recovering from crashes, but after SES realignment the old
    # estimates use wrong Tam_loc direction / escol boundaries / binned edad.
    # We must remove them so Julia starts fresh.
    #
    # Instead of deleting, we rename to *.pre_realignment.json for comparison.
    if fresh:
        logger.info("Archiving old sweep outputs (--fresh mode)...")
        if run_los_mex:
            archive_old_sweep("los_mex")
        if run_wvs_geographic:
            archive_old_sweep("wvs_geographic")
        if run_wvs_temporal:
            archive_old_sweep("wvs_temporal")

    results = {}

    # ── Phase 1: Build constructs ─────────────────────────────────────────
    #
    # .submit() is Prefect's way of launching a task asynchronously.
    # It returns a PrefectFuture object immediately — the task runs in
    # the background (in a thread pool by default, or on a worker if
    # using Prefect's distributed infrastructure).
    #
    # Los_mex and WVS operate on independent datasets, so they could run
    # in parallel.  We run them sequentially here because the WVS construct
    # build loads ~1.3GB of CSV data and benefits from having full memory.

    if run_los_mex:
        logger.info("Phase 1a: Building los_mex constructs...")
        # No .submit() here — run sequentially within the los_mex path
        # because export_for_julia depends on constructs being built.
        los_mex_manifest = build_los_mex_constructs()
        results["los_mex_constructs"] = str(los_mex_manifest)

    # ── WVS construct build + export ─────────────────────────────────────
    #
    # Each scope (geographic / temporal) now has its own cache and manifest
    # files, via the --scope flag in build_wvs_constructs_multi.py:
    #   geographic → wvs_multi_construct_cache_geographic.pkl
    #   temporal   → wvs_multi_construct_cache_temporal.pkl
    #
    # This means they can run in any order without overwriting each other.
    # The export script writes per-context CSVs (WVS_W7_MEX.csv etc.) that
    # accumulate in data/julia_bridge_wvs/.  Geographic runs last so the
    # final wvs_manifest.json has all 66 W7 contexts for Julia.

    if run_wvs_temporal:
        logger.info("Phase 1c: Building WVS constructs (temporal: Waves 1-7, Mexico)...")
        build_wvs_constructs(
            waves=[1, 2, 3, 4, 5, 6, 7], countries=["MEX"], scope="temporal",
        )
        logger.info("Phase 2c: Exporting WVS temporal for Julia...")
        export_wvs_for_julia(scope="temporal")
        results["wvs_temporal_constructs"] = "built+exported"

    if run_wvs_geographic:
        logger.info("Phase 1b: Building WVS constructs (geographic: Wave 7, all countries)...")
        build_wvs_constructs(waves=[7], scope="geographic")
        logger.info("Phase 2b: Exporting WVS geographic for Julia...")
        export_wvs_for_julia(scope="geographic")
        results["wvs_geographic_constructs"] = "built+exported"

    # ── Phase 2: Export los_mex to Julia CSVs ────────────────────────────
    #
    # Convert construct DataFrames to the CSV format Julia expects.
    # Each domain becomes one CSV with SES columns + agg_* columns.
    # The manifest JSON maps domain codes to CSV file paths.

    if run_los_mex:
        logger.info("Phase 2a: Exporting los_mex for Julia...")
        los_mex_julia_manifest = export_los_mex_for_julia()
        results["los_mex_julia_export"] = str(los_mex_julia_manifest)

    # ── Phase 3: Julia sweeps (sequential) ──────────────────────────────
    #
    # This is the computationally expensive phase.  Each Julia sweep uses
    # all 8 threads (-t8).  Running two 8-thread Julia processes on an
    # 8-core machine causes 2× oversubscription: threads fight for CPU,
    # throughput drops, and the first attempt may get killed by Prefect's
    # retry logic or the OS.
    #
    # Empirically confirmed: parallel geographic + temporal caused the
    # geographic sweep to run at 1.5 pairs/s (vs 3.0 normally) and fail
    # on first attempt.  The retry succeeded only because temporal had
    # already finished.
    #
    # Strategy: run all sweeps sequentially.  Shortest first so results
    # are available sooner:
    #   1. los_mex (~40 min)
    #   2. temporal (~42 min)
    #   3. geographic (~10 hours)
    #
    # On machines with ≥16 cores, you could safely run temporal + geographic
    # in parallel by setting JULIA_THREADS=8 for each (16 total threads).
    # To do so, replace the sequential calls below with .submit().

    if run_los_mex:
        logger.info("Phase 3a: Running los_mex Julia sweep (~40 min)...")
        los_mex_sweep = julia_los_mex_sweep()
        results["los_mex_sweep"] = str(los_mex_sweep)

    if run_wvs_temporal:
        logger.info("Phase 3b: Running WVS temporal sweep (~42 min)...")
        wvs_temporal_result = julia_wvs_temporal_sweep()
        results["wvs_temporal_sweep"] = str(wvs_temporal_result)

    if run_wvs_geographic:
        logger.info("Phase 3c: Running WVS geographic sweep (~10 hours)...")
        wvs_geographic_result = julia_wvs_geographic_sweep()
        results["wvs_geographic_sweep"] = str(wvs_geographic_result)

    # ── Phase 4: Fingerprints + ontology (sequential) ────────────────────
    #
    # These tasks depend on ALL sweeps being complete, because fingerprints
    # are computed from the sweep results.  They run sequentially because
    # each step's output is the next step's input:
    #   fingerprints → ontology patch → gamma surface → visualization

    logger.info("Phase 4: Computing SES fingerprints...")
    fingerprints = compute_ses_fingerprints()
    results["fingerprints"] = str(fingerprints)

    logger.info("Phase 5: Patching ontology bridges...")
    ontology = patch_ontology_bridges()
    results["ontology"] = str(ontology)

    logger.info("Phase 6: Building gamma surface...")
    gamma_surface = build_gamma_surface()
    results["gamma_surface"] = str(gamma_surface)

    logger.info("Phase 7: Generating visualizations...")
    viz_paths = visualize_gamma_surface()
    results["visualizations"] = [str(p) for p in viz_paths]

    # ── Done ─────────────────────────────────────────────────────────────

    logger.info("=" * 60)
    logger.info("SES Realignment Pipeline — Complete")
    for key, val in results.items():
        logger.info(f"  {key}: {val}")
    logger.info("=" * 60)

    return results


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════
#
# Prefect flows are normal Python functions — you can call them directly.
# The @flow decorator adds tracking, logging, and state management, but
# the function still returns its value like any other function.
#
# `if __name__ == "__main__"` is Python's idiom for "only run this block
# when the file is executed directly (not when imported as a module)."

def print_task_graph(
    run_los_mex: bool,
    run_wvs_geographic: bool,
    run_wvs_temporal: bool,
) -> None:
    """
    Print the task dependency graph without executing anything.

    This is a dry-run mode for verifying the pipeline structure before
    committing to a multi-hour run.
    """
    print("\nSES Realignment Pipeline — Task Graph")
    print("=" * 55)

    run_wvs = run_wvs_geographic or run_wvs_temporal

    if not (run_los_mex or run_wvs):
        print("  Nothing selected! Use --los-mex, --wvs-geographic,")
        print("  --wvs-temporal, or --all.")
        return

    tasks = []
    if run_los_mex:
        tasks.extend([
            ("1a", "build_los_mex_constructs", "~5s",   "python"),
            ("2a", "export_los_mex_for_julia",  "~5s",   "python"),
            ("3a", "julia_los_mex_sweep",       "~40m",  "julia"),
        ])
    # WVS: temporal builds+exports first, then geographic builds+exports.
    # This ensures the final manifest has all 66 W7 contexts for Julia.
    if run_wvs_temporal:
        tasks.extend([
            ("1c", "build_wvs_constructs (W1-7 × MEX)", "~12m",  "python"),
            ("2c", "export_wvs_for_julia (temporal)",    "~10s",  "python"),
        ])
    if run_wvs_geographic:
        tasks.extend([
            ("1b", "build_wvs_constructs (W7 × 66 countries)", "~40s",  "python"),
            ("2b", "export_wvs_for_julia (geographic)",  "~10s",  "python"),
        ])

    # Sweeps run sequentially: temporal before geographic (shortest first).
    if run_wvs_temporal:
        tasks.append(
            ("3b", "julia_wvs_temporal_sweep",    "~42m",  "julia"),
        )
    if run_wvs_geographic:
        tasks.append(
            ("3c", "julia_wvs_geographic_sweep",  "~10h",  "julia"),
        )

    tasks.extend([
        ("4",  "compute_ses_fingerprints",    "~2m",   "python"),
        ("5",  "patch_ontology_bridges",      "~10s",  "python"),
        ("6",  "build_gamma_surface",         "~5s",   "python"),
        ("7",  "visualize_gamma_surface",     "~3m",   "python"),
    ])

    for step, name, runtime, engine in tasks:
        parallel = " (parallel)" if "║" in engine else ""
        engine_clean = engine.replace(" ║", "")
        print(f"  [{step:>2s}] {name:<42s} {runtime:>6s}  [{engine_clean}]{parallel}")

    # Estimate total time based on what's selected.
    if run_wvs_geographic:
        total = "~11h" if run_los_mex else "~10.5h"
    elif run_wvs_temporal and run_los_mex:
        total = "~1.5h"
    elif run_wvs_temporal:
        total = "~1h"
    else:
        total = "~45m"

    print(f"\n  Estimated total: {total}")
    print(f"  Julia threads: {JULIA_THREADS}")
    print(f"  Conda env: {CONDA_ENV}")
    print()


if __name__ == "__main__":
    # argparse builds the CLI interface.
    #
    # Each dataset path is an explicit opt-in flag.  Nothing runs by
    # default — you must specify which sweeps you want.  This prevents
    # accidentally launching a 10-hour geographic sweep.
    #
    # Use --all to run everything, or combine flags:
    #   --los-mex --wvs-temporal   → los_mex + Mexico temporal (~1.5h)
    #   --wvs-geographic           → geographic only (~10h)
    #   --all                      → everything (~11h)
    parser = argparse.ArgumentParser(
        description="SES Realignment Pipeline — Prefect orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--los-mex",
        action="store_true",
        help="Run los_mex path: construct build + Julia sweep (~40 min)",
    )
    parser.add_argument(
        "--wvs-geographic",
        action="store_true",
        help="Run WVS geographic sweep: 66 countries, Wave 7 (~10 hours)",
    )
    parser.add_argument(
        "--wvs-temporal",
        action="store_true",
        help="Run WVS temporal sweep: Mexico, Waves 1-7 (~42 min)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all three paths (~11 hours total)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Archive old sweep outputs and recompute from scratch. "
             "Without this, Julia resumes from existing checkpoints.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print task graph without executing",
    )

    args = parser.parse_args()

    # --all is shorthand for enabling all three paths.
    run_los_mex = args.los_mex or args.all
    run_wvs_geographic = args.wvs_geographic or args.all
    run_wvs_temporal = args.wvs_temporal or args.all

    if args.dry_run:
        print_task_graph(run_los_mex, run_wvs_geographic, run_wvs_temporal)
        sys.exit(0)

    # If nothing selected and not --dry-run, show help.
    if not (run_los_mex or run_wvs_geographic or run_wvs_temporal):
        parser.print_help()
        print("\nError: specify at least one of --los-mex, --wvs-geographic,")
        print("--wvs-temporal, or --all.")
        sys.exit(1)

    # Launch the Prefect flow.
    # This call blocks until the entire pipeline completes (or fails).
    # Progress is visible in the terminal logs and in the Prefect UI
    # if you have `prefect server start` running.
    ses_realignment_pipeline(
        run_los_mex=run_los_mex,
        run_wvs_geographic=run_wvs_geographic,
        run_wvs_temporal=run_wvs_temporal,
        fresh=args.fresh,
    )
