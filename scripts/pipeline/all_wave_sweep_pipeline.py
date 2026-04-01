"""
All-Wave Geographic Sweep Pipeline — Prefect Orchestration
===========================================================

Runs the geographic DR bridge sweep for waves 1-6 across all participating
countries. Wave 7 is already done (68,174 estimates). Each wave is independent
and produces its own output JSON.

ARCHITECTURE
------------
    For each wave W (in reverse priority order):
      Phase A: Build constructs (Python, ~30s)
      Phase B: Export CSVs for Julia (Python, ~10s)
      Phase C: Julia sweep (8 threads, variable runtime)

    After all waves:
      Phase D: Merge per-wave JSONs → unified γ-surface

RUNTIME ESTIMATES (8 Julia threads, ~1.35 pairs/sec)
----------------------------------------------------
    W6: ~60 countries × ~700 pairs = ~8.9h
    W5: ~55 countries × ~300 pairs = ~4.2h
    W3: ~50 countries × ~200 pairs = ~2.4h
    W4: ~40 countries × ~220 pairs = ~2.0h
    W2: ~40 countries × ~150 pairs = ~1.3h
    W1: ~20 countries × ~100 pairs = ~0.3h
    Total new: ~19h  |  W7 already done

USAGE
-----
    # Sweep specific waves:
    python scripts/pipeline/all_wave_sweep_pipeline.py --waves 6 5

    # All remaining waves (1-6):
    python scripts/pipeline/all_wave_sweep_pipeline.py --all

    # Overnight batch (W6 + W5, ~13h):
    python scripts/pipeline/all_wave_sweep_pipeline.py --waves 6 5

    # Merge only (after all waves done):
    python scripts/pipeline/all_wave_sweep_pipeline.py --merge-only

    # Dry run:
    python scripts/pipeline/all_wave_sweep_pipeline.py --all --dry-run
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
WVS_BRIDGE_DIR = REPO_ROOT / "data" / "julia_bridge_wvs"
CONDA_ENV = "nvg_py13_env"
JULIA_THREADS = 8

# Per-wave timeout estimates (seconds) with 50% headroom
WAVE_TIMEOUTS = {
    1: 1800,     # ~0.3h + headroom → 30 min
    2: 7200,     # ~1.3h + headroom → 2h
    3: 14400,    # ~2.4h + headroom → 4h
    4: 10800,    # ~2.0h + headroom → 3h
    5: 25200,    # ~4.2h + headroom → 7h
    6: 50400,    # ~8.9h + headroom → 14h
    7: 64800,    # ~9.7h + headroom → 18h (already done)
}


# ═══════════════════════════════════════════════════════════════════════════
# SUBPROCESS HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _stream_subprocess(
    cmd: list[str], cwd: str, env: dict, timeout: int | None, label: str,
) -> int:
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


def _run_julia(script: str, label: str, timeout: int = 3600,
               threads: int = JULIA_THREADS, extra_args: list[str] | None = None):
    env = os.environ.copy()
    julia_bin = os.path.expanduser("~/.juliaup/bin/julia")
    cmd = [julia_bin, f"-t{threads}", f"--project={JULIA_BRIDGE_ROOT}",
           str(JULIA_BRIDGE_ROOT / "scripts" / script)]
    if extra_args:
        cmd.extend(extra_args)
    _stream_subprocess(cmd, str(JULIA_BRIDGE_ROOT), env, timeout, label)


# ═══════════════════════════════════════════════════════════════════════════
# TASK: SWEEP ONE WAVE
# ═══════════════════════════════════════════════════════════════════════════

@task(
    name="sweep_wave",
    tags=["julia", "sweep"],
    retries=1,
    retry_delay_seconds=120,
)
def sweep_one_wave(wave: int):
    """
    Build constructs, export CSVs, and run Julia sweep for one wave.

    Three sub-steps per wave:
      A. build_wvs_constructs_multi.py --waves {wave} --scope geographic_w{wave}
      B. export_wvs_for_julia.py with wave-specific cache/manifest
      C. julia run_wvs_geographic_wave.jl {wave}
    """
    logger = get_run_logger()
    # Use "geographic" scope for all waves — the wave number is in --waves.
    # The scope controls output filename suffix: cache_geographic.pkl, manifest_geographic.json.
    # Since we run one wave at a time sequentially, there's no overlap risk.
    scope = "geographic"
    output_json = RESULTS_DIR / f"wvs_geographic_sweep_w{wave}.json"
    timeout = WAVE_TIMEOUTS.get(wave, 36000)

    # ── Check if already done ─────────────────────────────────────────────
    if output_json.exists():
        with open(output_json) as f:
            existing = json.load(f)
        n_est = len(existing.get("estimates", {}))
        if n_est > 0:
            logger.info(f"W{wave}: {n_est} estimates already exist — Julia will resume from checkpoint")

    # ── Step A: Build constructs ──────────────────────────────────────────
    logger.info(f"W{wave} Step A: Building constructs (--waves {wave} --scope {scope})")
    _run_python(
        "scripts/debug/build_wvs_constructs_multi.py",
        f"W{wave}-build",
        timeout=600,
        extra_args=["--waves", str(wave), "--scope", scope],
    )

    # ── Step B: Export CSVs ───────────────────────────────────────────────
    cache = RESULTS_DIR / f"wvs_multi_construct_cache_{scope}.pkl"
    manifest = RESULTS_DIR / f"wvs_multi_construct_manifest_{scope}.json"

    logger.info(f"W{wave} Step B: Exporting CSVs for Julia")
    _run_python(
        "scripts/debug/export_wvs_for_julia.py",
        f"W{wave}-export",
        timeout=120,
        extra_args=["--cache", str(cache), "--manifest", str(manifest),
                     "--out-dir", str(WVS_BRIDGE_DIR)],
    )

    # ── Step C: Julia sweep ───────────────────────────────────────────────
    logger.info(f"W{wave} Step C: Julia sweep (timeout={timeout}s = {timeout/3600:.1f}h)")
    _run_julia(
        "run_wvs_geographic_wave.jl",
        f"W{wave}-sweep",
        timeout=timeout,
        extra_args=[str(wave)],
    )

    # ── Validate output ──────────────────────────────────────────────────
    if not output_json.exists():
        raise FileNotFoundError(f"W{wave} sweep output missing: {output_json}")

    with open(output_json) as f:
        result = json.load(f)
    n_est = len(result.get("estimates", {}))
    n_skip = len(result.get("skipped", {}))
    n_sig = sum(1 for v in result.get("estimates", {}).values() if v.get("excl_zero"))

    logger.info(f"W{wave} complete: {n_est} estimates, {n_skip} skipped, {n_sig} sig ({100*n_sig/max(n_est,1):.1f}%)")
    create_markdown_artifact(
        key=f"wave-{wave}-sweep",
        markdown=f"**Wave {wave}**: {n_est:,} estimates, {n_sig} significant ({100*n_sig/max(n_est,1):.1f}%)",
    )
    return wave


@task(name="merge_wave_sweeps", tags=["python", "analysis"])
def merge_wave_sweeps():
    """Merge all per-wave sweep JSONs into unified γ-surface."""
    logger = get_run_logger()
    logger.info("Merging per-wave sweeps into unified γ-surface")
    _run_python("scripts/debug/merge_wave_sweeps.py", "merge")


# ═══════════════════════════════════════════════════════════════════════════
# FLOW
# ═══════════════════════════════════════════════════════════════════════════

@flow(
    name="all-wave-geographic-sweep",
    description="Geographic DR sweep across all WVS waves (W1-W7)",
)
def all_wave_sweep_pipeline(
    waves: list[int] | None = None,
    merge_only: bool = False,
    dry_run: bool = False,
):
    """
    Run geographic sweep for specified waves, then merge all results.

    Waves are processed SEQUENTIALLY (not in parallel) to avoid
    8-thread oversubscription. Each wave's Julia sweep uses all 8 threads.
    """
    logger = get_run_logger()

    if merge_only:
        waves_to_run = []
    elif waves is None:
        # All waves except W7 (already done)
        waves_to_run = [6, 5, 3, 4, 2, 1]  # reverse priority order
    else:
        waves_to_run = waves

    logger.info("=" * 60)
    logger.info("ALL-WAVE GEOGRAPHIC SWEEP PIPELINE")
    logger.info("=" * 60)

    if not merge_only:
        logger.info(f"Waves to sweep: {waves_to_run}")
        total_est_hours = sum(WAVE_TIMEOUTS.get(w, 0) / 3600 / 1.5 for w in waves_to_run)
        logger.info(f"Estimated runtime: ~{total_est_hours:.0f} hours")

    if dry_run:
        logger.info("\n[DRY RUN] Task graph:")
        for w in waves_to_run:
            t = WAVE_TIMEOUTS.get(w, 0) / 3600 / 1.5  # remove headroom for display
            existing = RESULTS_DIR / f"wvs_geographic_sweep_w{w}.json"
            status = "(resume)" if existing.exists() else "(new)"
            logger.info(f"  W{w}: build → export → Julia sweep (~{t:.1f}h) {status}")
        logger.info("  Merge: combine all wave JSONs → unified γ-surface")
        logger.info("\n[DRY RUN] No tasks executed.")
        return

    # ── Sweep each wave sequentially ──────────────────────────────────────
    for wave in waves_to_run:
        logger.info(f"\n{'─' * 40}")
        logger.info(f"Starting wave {wave}")
        logger.info(f"{'─' * 40}")
        sweep_one_wave(wave)

    # ── Merge all waves ───────────────────────────────────────────────────
    merge_wave_sweeps()

    logger.info("\n" + "=" * 60)
    logger.info("ALL-WAVE SWEEP PIPELINE COMPLETE")
    logger.info("=" * 60)

    # Summary
    for w in range(1, 8):
        path = RESULTS_DIR / f"wvs_geographic_sweep_w{w}.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            n = len(data.get("estimates", {}))
            logger.info(f"  ✓ W{w}: {n:,} estimates")
        else:
            logger.info(f"  ✗ W{w}: not done")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="All-Wave Geographic Sweep Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pipeline/all_wave_sweep_pipeline.py --waves 6 5   # overnight (~13h)
  python scripts/pipeline/all_wave_sweep_pipeline.py --waves 3 4   # next day (~4.4h)
  python scripts/pipeline/all_wave_sweep_pipeline.py --waves 2 1   # quick batch (~1.6h)
  python scripts/pipeline/all_wave_sweep_pipeline.py --all          # all W1-W6 (~19h)
  python scripts/pipeline/all_wave_sweep_pipeline.py --merge-only   # just merge
  python scripts/pipeline/all_wave_sweep_pipeline.py --all --dry-run
        """,
    )
    parser.add_argument("--waves", type=int, nargs="+", choices=range(1, 8),
                        help="Specific waves to sweep (1-7)")
    parser.add_argument("--all", action="store_true",
                        help="Sweep all waves 1-6 (W7 already done)")
    parser.add_argument("--merge-only", action="store_true",
                        help="Skip sweeps, just merge existing wave JSONs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.all and args.waves is None and not args.merge_only:
        parser.print_help()
        sys.exit(1)

    all_wave_sweep_pipeline(
        waves=None if args.all else args.waves,
        merge_only=args.merge_only,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
