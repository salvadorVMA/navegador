"""
TDA Pipeline — Prefect Orchestration for Topological Data Analysis
==================================================================

This script orchestrates the full TDA pipeline for WVS construct networks.
It runs 7 phases (data conversion, Floyd-Warshall, Ricci curvature, spectral
distances, persistent homology, embeddings, and Gromov-Wasserstein alignment),
managing dependencies between Python and Julia steps.

ARCHITECTURE
------------
    Phase 0: Convert sweep JSON → per-country CSV matrices  (Python, ~10s)
                    │
         ┌─────────┴──────────┐
         ▼                    ▼
    Phase 1: Floyd-Warshall   Phase 4: Persistent homology
    (Julia, <1s)              (Python, ~30s)
         │                         │
         ▼                         ▼
    Phase 2: Ricci curvature  (bottleneck distances)
    (Julia 8-thread, ~5m)          │
         │                         │
    Phase 3: Spectral dists        │
    (Julia 8-thread, ~30s)         │
         │                         │
         └────────┬────────────────┘
                  ▼
    Phase 5: MDS embeddings + zone coherence  (Python, ~10s)
                  │
                  ▼
    Phase 6: Gromov-Wasserstein alignment     (Julia 8-thread, ~20m)

USAGE
-----
    # Full pipeline (~30 minutes):
    python scripts/pipeline/tda_pipeline.py --all

    # Specific phases:
    python scripts/pipeline/tda_pipeline.py --phase 0 1 4

    # Skip expensive phases for exploratory runs:
    python scripts/pipeline/tda_pipeline.py --all --skip-ricci --skip-gw

    # Dry run (print task graph only):
    python scripts/pipeline/tda_pipeline.py --all --dry-run
"""

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
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
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JULIA_BRIDGE_ROOT = REPO_ROOT.parent / "navegador_julia_bridge" / "julia"
TDA_DIR = REPO_ROOT / "data" / "tda"
CONDA_ENV = "nvg_py13_env"
JULIA_THREADS = 8

# Phase output directories — used for validation checks
PHASE_OUTPUTS = {
    0: TDA_DIR / "matrices" / "manifest.json",
    1: TDA_DIR / "floyd_warshall" / "mediator_scores.json",
    2: TDA_DIR / "ricci" / "ricci_summary.json",
    3: TDA_DIR / "spectral" / "spectral_distance_matrix.csv",
    4: TDA_DIR / "persistence" / "topological_features.csv",
    5: TDA_DIR / "embeddings" / "zone_coherence.json",
    6: TDA_DIR / "alignment" / "gw_distance_matrix.csv",
}


# ═══════════════════════════════════════════════════════════════════════════
# SUBPROCESS STREAMING
# ═══════════════════════════════════════════════════════════════════════════
# Same pattern as ses_realignment_pipeline.py: real-time stdout streaming
# via Popen + line-by-line reading. See that file for detailed annotations.

def _stream_subprocess(
    cmd: list[str],
    cwd: str,
    env: dict,
    timeout: int | None,
    label: str,
) -> int:
    """
    Run a subprocess and stream its output line-by-line to the Prefect logger.

    Returns the exit code. Raises on non-zero exit or timeout.
    """
    logger = get_run_logger()
    start = time.time()

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        for line in iter(proc.stdout.readline, ""):
            stripped = line.rstrip("\n")
            if stripped:
                logger.info(f"[{label}] {stripped}")
            if timeout is not None:
                elapsed = time.time() - start
                if elapsed > timeout:
                    proc.kill()
                    raise subprocess.TimeoutExpired(cmd, timeout)

        remaining = None
        if timeout is not None:
            remaining = max(0, timeout - (time.time() - start))
        returncode = proc.wait(timeout=remaining)

    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        raise

    elapsed = time.time() - start
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, cmd)
    logger.info(f"[{label}] completed in {elapsed:.1f}s (exit code {returncode})")
    return returncode


def _run_python(script: str, label: str, timeout: int = 600, extra_args: list[str] | None = None):
    """Run a Python script in the conda environment with PYTHONPATH set."""
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT}:{REPO_ROOT / 'scripts' / 'debug'}"
    cmd = [
        "conda", "run", "-n", CONDA_ENV, "--no-capture-output",
        "python", str(REPO_ROOT / script),
    ]
    if extra_args:
        cmd.extend(extra_args)
    _stream_subprocess(cmd, str(REPO_ROOT), env, timeout, label)


def _run_julia(script: str, label: str, timeout: int = 3600, threads: int = JULIA_THREADS):
    """Run a Julia script with threading enabled."""
    env = os.environ.copy()
    julia_bin = os.path.expanduser("~/.juliaup/bin/julia")
    cmd = [
        julia_bin,
        f"-t{threads}",
        f"--project={JULIA_BRIDGE_ROOT}",
        str(JULIA_BRIDGE_ROOT / "scripts" / script),
    ]
    _stream_subprocess(cmd, str(JULIA_BRIDGE_ROOT), env, timeout, label)


# ═══════════════════════════════════════════════════════════════════════════
# TASK DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════
# Each phase is a Prefect @task. Tasks run sequentially by default but can
# be submitted in parallel with .submit() when they have no data dependencies.

@task(
    name="phase_0_convert",
    tags=["python", "data-prep"],
    retries=0,
    timeout_seconds=120,
)
def phase_0_convert():
    """
    Phase 0: Convert γ-surface sweep JSON → per-country CSV weight/distance matrices.

    Reads:  data/results/wvs_geographic_sweep_w7.json (68K estimates)
    Writes: data/tda/matrices/{COUNTRY}.csv, manifest.json
    """
    logger = get_run_logger()
    logger.info("Phase 0: Converting sweep JSON to per-country matrices")
    _run_python("scripts/debug/tda_convert_sweep_to_matrices.py", "Phase0")

    # Validate output
    manifest_path = PHASE_OUTPUTS[0]
    if not manifest_path.exists():
        raise FileNotFoundError(f"Phase 0 output missing: {manifest_path}")
    with open(manifest_path) as f:
        manifest = json.load(f)
    n = len(manifest.get("countries", []))
    logger.info(f"Phase 0 complete: {n} country matrices generated")
    create_markdown_artifact(
        key="phase-0-summary",
        markdown=f"**Phase 0**: {n} countries, {manifest.get('n_constructs', '?')} constructs",
    )


@task(
    name="phase_1_floyd_warshall",
    tags=["julia", "topology"],
    retries=0,
    timeout_seconds=60,
)
def phase_1_floyd_warshall():
    """
    Phase 1: Floyd-Warshall shortest paths + mediator scores (Julia).

    Reads:  data/tda/matrices/*.csv
    Writes: data/tda/floyd_warshall/{COUNTRY}_shortest_paths.csv, mediator_scores.json
    Time:   < 1 second (55×55 matrices are trivial)
    """
    logger = get_run_logger()
    logger.info("Phase 1: Floyd-Warshall (Julia)")
    _run_julia("tda_floyd_warshall.jl", "Phase1", threads=1)  # No threading needed

    if not PHASE_OUTPUTS[1].exists():
        raise FileNotFoundError(f"Phase 1 output missing: {PHASE_OUTPUTS[1]}")


@task(
    name="phase_2_ricci_curvature",
    tags=["julia", "topology"],
    retries=0,
    timeout_seconds=600,
)
def phase_2_ricci_curvature():
    """
    Phase 2: Ollivier-Ricci curvature via Sinkhorn OT (Julia, 8 threads).

    Reads:  data/tda/matrices/*.csv, data/tda/floyd_warshall/*_shortest_paths.csv
    Writes: data/tda/ricci/{COUNTRY}_ricci.csv, ricci_summary.json
    Time:   ~5 minutes on 8 cores
    """
    logger = get_run_logger()
    logger.info("Phase 2: Ricci curvature (Julia, 8 threads)")
    _run_julia("tda_ricci_curvature.jl", "Phase2", timeout=600)

    if not PHASE_OUTPUTS[2].exists():
        raise FileNotFoundError(f"Phase 2 output missing: {PHASE_OUTPUTS[2]}")


@task(
    name="phase_3_spectral_distances",
    tags=["julia", "topology"],
    retries=0,
    timeout_seconds=120,
)
def phase_3_spectral_distances():
    """
    Phase 3: Laplacian spectral distances between country networks (Julia).

    Reads:  data/tda/matrices/*.csv
    Writes: data/tda/spectral/spectral_distance_matrix.csv, spectral_features.json
    Time:   ~30 seconds
    """
    logger = get_run_logger()
    logger.info("Phase 3: Spectral distances (Julia, 8 threads)")
    _run_julia("tda_spectral_distances.jl", "Phase3", timeout=120)

    if not PHASE_OUTPUTS[3].exists():
        raise FileNotFoundError(f"Phase 3 output missing: {PHASE_OUTPUTS[3]}")


@task(
    name="phase_4_persistent_homology",
    tags=["python", "topology"],
    retries=0,
    timeout_seconds=120,
)
def phase_4_persistent_homology():
    """
    Phase 4: Persistent homology via Ripser (Python).

    Reads:  data/tda/floyd_warshall/*_shortest_paths.csv (or raw distance matrices)
    Writes: data/tda/persistence/topological_features.csv, bottleneck_distances.csv
    Time:   < 30 seconds (Ripser is C++-backed, 55×55 matrices are tiny)
    """
    logger = get_run_logger()
    logger.info("Phase 4: Persistent homology (ripser)")
    _run_python("scripts/debug/tda_persistent_homology.py", "Phase4")

    if not PHASE_OUTPUTS[4].exists():
        raise FileNotFoundError(f"Phase 4 output missing: {PHASE_OUTPUTS[4]}")

    features = __import__("pandas").read_csv(PHASE_OUTPUTS[4])
    mean_b1 = features["betti_1"].mean()
    max_b1_country = features.loc[features["betti_1"].idxmax(), "country"]
    create_markdown_artifact(
        key="phase-4-summary",
        markdown=(
            f"**Phase 4**: Mean β₁ = {mean_b1:.1f}, "
            f"Max β₁ = {features['betti_1'].max()} ({max_b1_country})"
        ),
    )


@task(
    name="phase_5_embeddings",
    tags=["python", "visualization"],
    retries=0,
    timeout_seconds=120,
)
def phase_5_embeddings():
    """
    Phase 5: MDS embeddings + cultural zone coherence tests (Python).

    Reads:  data/tda/spectral/*.csv, data/tda/persistence/*.csv, data/tda/ricci/*.json
    Writes: data/tda/embeddings/mds_*.png, zone_coherence.json, combined_features.csv
    """
    logger = get_run_logger()
    logger.info("Phase 5: MDS embeddings + zone coherence")
    _run_python("scripts/debug/tda_embeddings_and_zones.py", "Phase5")

    if not PHASE_OUTPUTS[5].exists():
        raise FileNotFoundError(f"Phase 5 output missing: {PHASE_OUTPUTS[5]}")

    with open(PHASE_OUTPUTS[5]) as f:
        coherence = json.load(f)
    lines = []
    for metric, result in coherence.items():
        lines.append(
            f"- **{metric}**: ratio={result['observed_ratio']:.3f}, "
            f"p={result['p_value']:.4f}, silhouette={result['silhouette']:.3f} "
            f"({result['interpretation']})"
        )
    create_markdown_artifact(
        key="phase-5-summary",
        markdown="**Phase 5 — Zone Coherence**\n\n" + "\n".join(lines),
    )


@task(
    name="phase_6_gromov_wasserstein",
    tags=["julia", "topology"],
    retries=0,
    timeout_seconds=3600,
)
def phase_6_gromov_wasserstein():
    """
    Phase 6: Gromov-Wasserstein network alignment for all 2145 pairs (Julia).

    Reads:  data/tda/floyd_warshall/*_shortest_paths.csv
    Writes: data/tda/alignment/gw_distance_matrix.csv, gw_transport_top50.json
    Time:   ~20 minutes on 8 cores
    """
    logger = get_run_logger()
    logger.info("Phase 6: Gromov-Wasserstein alignment (Julia, 8 threads)")
    _run_julia("tda_gromov_wasserstein.jl", "Phase6", timeout=3600)

    if not PHASE_OUTPUTS[6].exists():
        raise FileNotFoundError(f"Phase 6 output missing: {PHASE_OUTPUTS[6]}")


# ═══════════════════════════════════════════════════════════════════════════
# FLOW DEFINITION
# ═══════════════════════════════════════════════════════════════════════════

@flow(
    name="tda-pipeline",
    description="Topological Data Analysis pipeline for WVS construct networks",
)
def tda_pipeline(
    phases: list[int] | None = None,
    skip_ricci: bool = False,
    skip_gw: bool = False,
    dry_run: bool = False,
):
    """
    Run the TDA pipeline.

    Parameters
    ----------
    phases : list[int] or None
        Specific phases to run (0-6). None = all phases.
    skip_ricci : bool
        Skip Phase 2 (Ricci curvature, ~5 min). Useful for quick iteration.
    skip_gw : bool
        Skip Phase 6 (Gromov-Wasserstein, ~20 min).
    dry_run : bool
        Print the task graph without executing.
    """
    logger = get_run_logger()
    all_phases = set(range(7)) if phases is None else set(phases)

    if skip_ricci:
        all_phases.discard(2)
    if skip_gw:
        all_phases.discard(6)

    logger.info("=" * 60)
    logger.info("TDA PIPELINE — Topological Analysis of WVS Construct Networks")
    logger.info("=" * 60)
    logger.info(f"Phases to run: {sorted(all_phases)}")
    logger.info(f"Skip Ricci: {skip_ricci}, Skip GW: {skip_gw}")

    if dry_run:
        logger.info("\n[DRY RUN] Task graph:")
        task_names = {
            0: "Phase 0: Convert sweep → matrices (Python, ~10s)",
            1: "Phase 1: Floyd-Warshall (Julia, <1s)",
            2: "Phase 2: Ricci curvature (Julia 8T, ~5min)",
            3: "Phase 3: Spectral distances (Julia 8T, ~30s)",
            4: "Phase 4: Persistent homology (Python, ~30s)",
            5: "Phase 5: MDS + zone coherence (Python, ~10s)",
            6: "Phase 6: Gromov-Wasserstein (Julia 8T, ~20min)",
        }
        for p in sorted(all_phases):
            marker = "✓" if p in all_phases else "✗"
            logger.info(f"  {marker} {task_names[p]}")
        logger.info("\nDependency graph:")
        logger.info("  0 → {1, 4} (parallel)")
        logger.info("  1 → 2 → 3 (sequential)")
        logger.info("  {3, 4} → 5")
        logger.info("  1 → 6")
        logger.info("\n[DRY RUN] No tasks executed.")
        return

    # ── Phase 0: always runs first ─────────────────────────────────────────
    if 0 in all_phases:
        phase_0_convert()

    # ── Phases 1 and 4 can run in parallel ────────────────────────────────
    # (both depend on Phase 0 output but not on each other)
    if 1 in all_phases and 4 in all_phases:
        # Submit both in parallel
        future_1 = phase_1_floyd_warshall.submit()
        future_4 = phase_4_persistent_homology.submit()
        future_1.result()  # wait for Phase 1
        future_4.result()  # wait for Phase 4
    elif 1 in all_phases:
        phase_1_floyd_warshall()
    elif 4 in all_phases:
        phase_4_persistent_homology()

    # ── Phase 2: depends on Phase 1 ───────────────────────────────────────
    if 2 in all_phases:
        phase_2_ricci_curvature()

    # ── Phase 3: independent of Phase 2, needs Phase 0 matrices ──────────
    if 3 in all_phases:
        phase_3_spectral_distances()

    # ── Phase 5: depends on Phases 3 and 4 ────────────────────────────────
    if 5 in all_phases:
        phase_5_embeddings()

    # ── Phase 6: depends on Phase 1 (shortest-path matrices) ─────────────
    if 6 in all_phases:
        phase_6_gromov_wasserstein()

    logger.info("\n" + "=" * 60)
    logger.info("TDA PIPELINE COMPLETE")
    logger.info("=" * 60)

    # Final summary
    for p in sorted(all_phases):
        output = PHASE_OUTPUTS.get(p)
        exists = output.exists() if output else False
        status = "✓" if exists else "✗"
        logger.info(f"  {status} Phase {p}: {output.name if output else 'N/A'}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="TDA Pipeline for WVS Construct Networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pipeline/tda_pipeline.py --all              # full pipeline (~30 min)
  python scripts/pipeline/tda_pipeline.py --phase 0 1 4 5    # specific phases
  python scripts/pipeline/tda_pipeline.py --all --skip-ricci  # skip Phase 2
  python scripts/pipeline/tda_pipeline.py --all --skip-gw     # skip Phase 6
  python scripts/pipeline/tda_pipeline.py --all --dry-run     # print task graph
        """,
    )
    parser.add_argument("--all", action="store_true", help="Run all phases")
    parser.add_argument(
        "--phase", type=int, nargs="+", choices=range(7),
        help="Run specific phases (0-6)",
    )
    parser.add_argument("--skip-ricci", action="store_true",
                        help="Skip Phase 2 (Ricci curvature, ~5 min)")
    parser.add_argument("--skip-gw", action="store_true",
                        help="Skip Phase 6 (Gromov-Wasserstein, ~20 min)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print task graph without executing")
    args = parser.parse_args()

    if not args.all and args.phase is None:
        parser.print_help()
        print("\nError: specify --all or --phase <numbers>")
        sys.exit(1)

    phases = None if args.all else args.phase

    tda_pipeline(
        phases=phases,
        skip_ricci=args.skip_ricci,
        skip_gw=args.skip_gw,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
