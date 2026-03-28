"""
Temporal TDA Pipeline — Mexico W3-W7 Sweep + Temporal Topology
==============================================================

Orchestrates the full temporal analysis for Mexico across WVS waves 3-7:

  Phase 0: Build temporal constructs (Python, ~30s)
  Phase 1: Export per-wave CSVs for Julia (Python, ~10s)
  Phase 2: Julia temporal sweep — 7 waves × ~400 pairs (Julia 8T, ~42 min)
  Phase 3: Temporal analysis — trends, stability (Python, ~10s)
  Phase 4: Convert temporal sweep → per-wave matrices (Python, ~5s)
  Phase 5: Per-wave TDA — Floyd-Warshall + spectral per wave (Julia, ~5s)
  Phase 6: Temporal spectral trajectory — wave-to-wave distances (Python, ~5s)

ARCHITECTURE
------------
    Phase 0: build_wvs_constructs_multi --scope temporal
                    │
    Phase 1: export_wvs_for_julia (temporal cache)
                    │
    Phase 2: Julia temporal sweep (W3-W7, ~42 min)
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    Phase 3: analyze_wvs_temporal   Phase 4: Convert → per-wave matrices
    (trends, stability)                     │
                               Phase 5: Per-wave Floyd-Warshall + spectral
                                            │
                               Phase 6: Temporal trajectory analysis

USAGE
-----
    # Full pipeline (~45 min, dominated by Julia sweep):
    python scripts/pipeline/temporal_tda_pipeline.py --all

    # Skip Julia sweep (if already done, just run analysis):
    python scripts/pipeline/temporal_tda_pipeline.py --phase 3 4 5 6

    # Dry run:
    python scripts/pipeline/temporal_tda_pipeline.py --all --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from prefect import flow, task, get_run_logger
from prefect.artifacts import create_markdown_artifact

# ═══════════════════════════════════════════════════════════════════════════
# PATH CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JULIA_BRIDGE_ROOT = REPO_ROOT.parent / "navegador_julia_bridge" / "julia"
RESULTS_DIR = REPO_ROOT / "data" / "results"
TDA_DIR = REPO_ROOT / "data" / "tda"
WVS_BRIDGE_DIR = REPO_ROOT / "data" / "julia_bridge_wvs"
CONDA_ENV = "nvg_py13_env"
JULIA_THREADS = 8

# Phase output files — used for validation
PHASE_OUTPUTS = {
    0: RESULTS_DIR / "wvs_multi_construct_manifest_temporal.json",
    1: WVS_BRIDGE_DIR / "wvs_manifest.json",
    2: RESULTS_DIR / "wvs_temporal_sweep_mex.json",
    3: RESULTS_DIR / "wvs_temporal_report.md",
    4: TDA_DIR / "temporal" / "manifest.json",
    5: TDA_DIR / "temporal" / "spectral_features.json",
    6: TDA_DIR / "temporal" / "temporal_trajectory.json",
}


# ═══════════════════════════════════════════════════════════════════════════
# SUBPROCESS HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _stream_subprocess(
    cmd: list[str], cwd: str, env: dict, timeout: int | None, label: str,
) -> int:
    """Run subprocess with real-time stdout streaming to Prefect logger."""
    logger = get_run_logger()
    start = time.time()
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    try:
        for line in iter(proc.stdout.readline, ""):
            stripped = line.rstrip("\n")
            if stripped:
                logger.info(f"[{label}] {stripped}")
            if timeout is not None and (time.time() - start) > timeout:
                proc.kill()
                raise subprocess.TimeoutExpired(cmd, timeout)
        remaining = max(0, timeout - (time.time() - start)) if timeout else None
        returncode = proc.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        raise
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, cmd)
    logger.info(f"[{label}] completed in {time.time() - start:.1f}s")
    return returncode


def _run_python(script: str, label: str, timeout: int = 600, extra_args: list[str] | None = None):
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT}:{REPO_ROOT / 'scripts' / 'debug'}"
    cmd = ["conda", "run", "-n", CONDA_ENV, "--no-capture-output",
           "python", str(REPO_ROOT / script)]
    if extra_args:
        cmd.extend(extra_args)
    _stream_subprocess(cmd, str(REPO_ROOT), env, timeout, label)


def _run_julia(script: str, label: str, timeout: int = 3600, threads: int = JULIA_THREADS):
    env = os.environ.copy()
    julia_bin = os.path.expanduser("~/.juliaup/bin/julia")
    cmd = [julia_bin, f"-t{threads}", f"--project={JULIA_BRIDGE_ROOT}",
           str(JULIA_BRIDGE_ROOT / "scripts" / script)]
    _stream_subprocess(cmd, str(JULIA_BRIDGE_ROOT), env, timeout, label)


# ═══════════════════════════════════════════════════════════════════════════
# TASK DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@task(name="temporal_0_build_constructs", tags=["python", "data-prep"])
def phase_0_build_constructs():
    """
    Build WVS constructs for all 7 Mexico waves with temporal scope.

    Calls: build_wvs_constructs_multi.py --waves 1 2 3 4 5 6 7 --countries MEX --scope temporal
    Output: wvs_multi_construct_cache_temporal.pkl + manifest_temporal.json
    """
    logger = get_run_logger()
    logger.info("Phase 0: Building temporal constructs (7 waves × MEX)")
    _run_python(
        "scripts/debug/build_wvs_constructs_multi.py",
        "Phase0",
        timeout=300,
        extra_args=["--waves", "1", "2", "3", "4", "5", "6", "7",
                     "--countries", "MEX", "--scope", "temporal"],
    )
    assert PHASE_OUTPUTS[0].exists(), f"Missing: {PHASE_OUTPUTS[0]}"


@task(name="temporal_1_export_julia", tags=["python", "data-prep"])
def phase_1_export_julia():
    """
    Export per-wave CSVs and manifest for Julia sweep.

    Calls: export_wvs_for_julia.py with temporal cache/manifest
    Output: WVS_W{1-7}_MEX.csv + wvs_pairs.csv + wvs_manifest.json
    """
    logger = get_run_logger()
    logger.info("Phase 1: Exporting temporal CSVs for Julia")
    cache = RESULTS_DIR / "wvs_multi_construct_cache_temporal.pkl"
    manifest = RESULTS_DIR / "wvs_multi_construct_manifest_temporal.json"
    _run_python(
        "scripts/debug/export_wvs_for_julia.py",
        "Phase1",
        timeout=120,
        extra_args=["--cache", str(cache), "--manifest", str(manifest),
                     "--out-dir", str(WVS_BRIDGE_DIR)],
    )
    assert PHASE_OUTPUTS[1].exists(), f"Missing: {PHASE_OUTPUTS[1]}"


@task(
    name="temporal_2_julia_sweep",
    tags=["julia", "sweep"],
    retries=1,
    retry_delay_seconds=60,
    timeout_seconds=7200,
)
def phase_2_julia_sweep():
    """
    Julia temporal sweep: DR bridge estimates for all construct pairs across W3-W7.

    ~2,300 estimates total (varying pair count per wave due to construct availability).
    Runtime: ~42 minutes on 8 threads.
    """
    logger = get_run_logger()
    logger.info("Phase 2: Julia temporal sweep (W3-W7 MEX, ~42 min)")
    _run_julia("run_wvs_temporal.jl", "Phase2", timeout=7200)
    output = PHASE_OUTPUTS[2]
    assert output.exists(), f"Missing: {output}"
    with open(output) as f:
        data = json.load(f)
    n_est = len(data.get("estimates", {}))
    logger.info(f"Phase 2 complete: {n_est} estimates")
    create_markdown_artifact(
        key="temporal-sweep",
        markdown=f"**Temporal sweep**: {n_est} estimates across Mexico W3-W7",
    )


@task(name="temporal_3_analyze", tags=["python", "analysis"])
def phase_3_analyze():
    """
    Temporal analysis: per-wave summaries, trends, structural stability.

    Output: wvs_temporal_report.md + wvs_temporal_stats.json
    """
    logger = get_run_logger()
    logger.info("Phase 3: Temporal analysis (trends, stability)")
    _run_python("scripts/debug/analyze_wvs_temporal.py", "Phase3")
    assert PHASE_OUTPUTS[3].exists(), f"Missing: {PHASE_OUTPUTS[3]}"


@task(name="temporal_4_convert_matrices", tags=["python", "data-prep"])
def phase_4_convert_matrices():
    """
    Convert temporal sweep JSON → per-wave weight/distance matrices.

    Produces MEX_W{3-7}.csv and MEX_W{3-7}_distance.csv in data/tda/temporal/
    """
    logger = get_run_logger()
    logger.info("Phase 4: Converting temporal sweep to per-wave matrices")
    _run_python("scripts/debug/tda_convert_temporal_matrices.py", "Phase4")
    assert PHASE_OUTPUTS[4].exists(), f"Missing: {PHASE_OUTPUTS[4]}"


@task(name="temporal_5_per_wave_tda", tags=["julia", "topology"])
def phase_5_per_wave_tda():
    """
    Per-wave TDA: Floyd-Warshall + spectral features for each wave.

    Produces mediator scores and Laplacian spectra per wave.
    """
    logger = get_run_logger()
    logger.info("Phase 5: Per-wave Floyd-Warshall + spectral (Julia)")
    _run_julia("tda_temporal_spectral.jl", "Phase5", timeout=120, threads=1)
    assert PHASE_OUTPUTS[5].exists(), f"Missing: {PHASE_OUTPUTS[5]}"


@task(name="temporal_6_trajectory", tags=["python", "analysis"])
def phase_6_trajectory():
    """
    Temporal trajectory: spectral distances between consecutive waves,
    mediator evolution, structural change detection.
    """
    logger = get_run_logger()
    logger.info("Phase 6: Temporal trajectory analysis")
    _run_python("scripts/debug/tda_temporal_trajectory.py", "Phase6")
    assert PHASE_OUTPUTS[6].exists(), f"Missing: {PHASE_OUTPUTS[6]}"


# ═══════════════════════════════════════════════════════════════════════════
# FLOW
# ═══════════════════════════════════════════════════════════════════════════

@flow(name="temporal-tda-pipeline", description="Mexico temporal sweep + TDA")
def temporal_tda_pipeline(
    phases: list[int] | None = None,
    dry_run: bool = False,
):
    logger = get_run_logger()
    all_phases = set(range(7)) if phases is None else set(phases)

    logger.info("=" * 60)
    logger.info("TEMPORAL TDA PIPELINE — Mexico W3-W7")
    logger.info("=" * 60)
    logger.info(f"Phases: {sorted(all_phases)}")

    if dry_run:
        names = {
            0: "Build temporal constructs (Python, ~30s)",
            1: "Export per-wave CSVs for Julia (Python, ~10s)",
            2: "Julia temporal sweep W3-W7 (~42 min)",
            3: "Temporal analysis — trends, stability (Python, ~10s)",
            4: "Convert sweep → per-wave matrices (Python, ~5s)",
            5: "Per-wave TDA — Floyd-Warshall + spectral (Julia, ~5s)",
            6: "Temporal trajectory — wave-to-wave distances (Python, ~5s)",
        }
        for p in sorted(all_phases):
            logger.info(f"  {'✓' if p in all_phases else '✗'} Phase {p}: {names[p]}")
        logger.info("\n  0 → 1 → 2 → {3, 4} parallel → 5 → 6")
        return

    if 0 in all_phases:
        phase_0_build_constructs()
    if 1 in all_phases:
        phase_1_export_julia()
    if 2 in all_phases:
        phase_2_julia_sweep()

    # Phases 3 and 4 can run in parallel
    if 3 in all_phases and 4 in all_phases:
        f3 = phase_3_analyze.submit()
        f4 = phase_4_convert_matrices.submit()
        f3.result()
        f4.result()
    elif 3 in all_phases:
        phase_3_analyze()
    elif 4 in all_phases:
        phase_4_convert_matrices()

    if 5 in all_phases:
        phase_5_per_wave_tda()
    if 6 in all_phases:
        phase_6_trajectory()

    logger.info("\n" + "=" * 60)
    logger.info("TEMPORAL TDA PIPELINE COMPLETE")
    logger.info("=" * 60)
    for p in sorted(all_phases):
        out = PHASE_OUTPUTS.get(p)
        status = "✓" if out and out.exists() else "✗"
        logger.info(f"  {status} Phase {p}: {out.name if out else 'N/A'}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Temporal TDA Pipeline (Mexico W3-W7)")
    parser.add_argument("--all", action="store_true", help="Run all phases")
    parser.add_argument("--phase", type=int, nargs="+", choices=range(7))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.all and args.phase is None:
        parser.print_help()
        sys.exit(1)

    temporal_tda_pipeline(
        phases=None if args.all else args.phase,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
