"""
All-Wave TDA Pipeline — Prefect Orchestration
==============================================

Extends the v1 TDA pipeline (tda_pipeline.py) to the all-wave γ-surface.
Runs TDA across all waves (W2-W7) and all countries with multi-wave data.

Every sub-phase is a separate Prefect @task so each step appears individually
in the Prefect dashboard with a descriptive label (e.g. "W7 · Floyd-Warshall",
"MEX · Temporal Spectral").

Two orthogonal analysis modes:

  Mode A (geographic): For each wave with enough countries, run the full
    TDA pipeline (FW → Ricci → spectral → persistence → embeddings → GW).
    Compares countries WITHIN the same wave.

  Mode B (temporal): For each country with 3+ waves, run per-wave spectral
    analysis and temporal trajectory. Tracks how a single country EVOLVES.

Both modes output to data/tda/allwave/.

ARCHITECTURE
------------
    Phase 0: Convert all-wave JSON → matrices     (Python, ~30s)
        │
        ├── Mode A: Per-wave geographic TDA
        │   For waves W3–W7 (sequentially):
        │     A1: Floyd-Warshall      (Julia, <1s)
        │     A2: Ricci curvature     (Julia 8T, 1-5 min)  [optional]
        │     A3: Spectral distances  (Julia 8T, 5-30s)
        │     A4: Persistent homology (Python, 5-30s)
        │     A5: Embeddings + zones  (Python, ~10s)
        │     A6: GW alignment        (Julia 8T, 2-20 min) [optional]
        │
        ├── Mode B: Multi-country temporal TDA
        │   For ~37 countries with 3+ waves:
        │     B1: Per-wave FW + spectral (Julia, ~1s)
        │
        └── Phase C: Cross-mode synthesis
            C1: tda_allwave_analysis.py  (Python, ~30s)

USAGE
-----
    # Full pipeline (~70 min with Ricci, ~20 min without):
    python scripts/pipeline/allwave_tda_pipeline.py --all

    # Geographic only (specific waves):
    python scripts/pipeline/allwave_tda_pipeline.py --geographic --waves 5 6 7

    # Temporal only (specific countries):
    python scripts/pipeline/allwave_tda_pipeline.py --temporal --countries MEX BRA IND

    # Quick run (skip expensive phases):
    python scripts/pipeline/allwave_tda_pipeline.py --all --skip-ricci --skip-gw

    # Dry run:
    python scripts/pipeline/allwave_tda_pipeline.py --all --dry-run
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
ALLWAVE_DIR = REPO_ROOT / "data" / "tda" / "allwave"
CONDA_ENV = "nvg_py13_env"
JULIA_THREADS = 8

# Wave year mapping (for display)
WAVE_YEARS = {1: 1981, 2: 1990, 3: 1996, 4: 2000, 5: 2007, 6: 2012, 7: 2018}


# ═══════════════════════════════════════════════════════════════════════════
# SUBPROCESS STREAMING
# ═══════════════════════════════════════════════════════════════════════════
# Same pattern as tda_pipeline.py and ses_realignment_pipeline.py:
# real-time stdout streaming via Popen + line-by-line reading.

def _stream_subprocess(
    cmd: list[str],
    cwd: str,
    env: dict,
    timeout: int | None,
    label: str,
) -> int:
    """Run a subprocess and stream its output line-by-line."""
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

    elapsed = time.time() - start
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, cmd)
    logger.info(f"[{label}] completed in {elapsed:.1f}s")
    return returncode


def _run_python(script: str, label: str, timeout: int = 600, extra_args: list[str] | None = None):
    """Run a Python script in the conda environment."""
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT}:{REPO_ROOT / 'scripts' / 'debug'}"
    cmd = [
        "conda", "run", "-n", CONDA_ENV, "--no-capture-output",
        "python", str(REPO_ROOT / script),
    ]
    if extra_args:
        cmd.extend(extra_args)
    _stream_subprocess(cmd, str(REPO_ROOT), env, timeout, label)


def _run_python_with_env(
    script: str, label: str, timeout: int = 600,
    env_overrides: dict[str, str] | None = None,
):
    """Run a Python script with additional environment variable overrides."""
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT}:{REPO_ROOT / 'scripts' / 'debug'}"
    if env_overrides:
        env.update(env_overrides)
    cmd = [
        "conda", "run", "-n", CONDA_ENV, "--no-capture-output",
        "python", str(REPO_ROOT / script),
    ]
    _stream_subprocess(cmd, str(REPO_ROOT), env, timeout, label)


def _run_julia(
    script: str, label: str,
    timeout: int = 3600, threads: int = JULIA_THREADS,
    extra_args: list[str] | None = None,
):
    """Run a Julia script with threading enabled and optional CLI args."""
    env = os.environ.copy()
    julia_bin = os.path.expanduser("~/.juliaup/bin/julia")
    cmd = [
        julia_bin,
        f"-t{threads}",
        f"--project={JULIA_BRIDGE_ROOT}",
        str(JULIA_BRIDGE_ROOT / "scripts" / script),
    ]
    if extra_args:
        cmd.extend(extra_args)
    _stream_subprocess(cmd, str(JULIA_BRIDGE_ROOT), env, timeout, label)


# ═══════════════════════════════════════════════════════════════════════════
# HELPER: per-wave output directories
# ═══════════════════════════════════════════════════════════════════════════

def _wave_dirs(wave: int) -> dict[str, Path]:
    """Return output directory paths for a given wave, creating them."""
    out_base = ALLWAVE_DIR / "per_wave" / f"W{wave}"
    dirs = {
        "base": out_base,
        "fw": out_base / "floyd_warshall",
        "ricci": out_base / "ricci",
        "spectral": out_base / "spectral",
        "persistence": out_base / "persistence",
        "embeddings": out_base / "embeddings",
        "alignment": out_base / "alignment",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _wave_manifest(wave: int) -> Path:
    """Return the manifest path for a given wave."""
    return ALLWAVE_DIR / "matrices" / f"W{wave}" / "manifest.json"


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 0: CONVERT ALL-WAVE JSON → MATRICES
# ═══════════════════════════════════════════════════════════════════════════

@task(
    name="Phase 0 · Convert All-Wave Surface",
    task_run_name="Phase 0 · Convert All-Wave Surface",
    tags=["python", "data-prep"],
    timeout_seconds=120,
)
def phase_0_convert(mode: str, min_countries: int, min_waves: int):
    """Convert the all-wave γ-surface JSON to per-context CSV matrices."""
    logger = get_run_logger()
    logger.info(f"Phase 0: Converting all-wave surface (mode={mode})")
    _run_python(
        "scripts/debug/tda_convert_allwave_to_matrices.py", "Phase0",
        extra_args=["--mode", mode,
                     "--min-countries", str(min_countries),
                     "--min-waves", str(min_waves)],
    )

    global_manifest = ALLWAVE_DIR / "matrices" / "global_manifest.json"
    if not global_manifest.exists():
        raise FileNotFoundError(f"Phase 0 output missing: {global_manifest}")
    with open(global_manifest) as f:
        manifest = json.load(f)

    # Build summary for artifact
    geo = manifest.get("geographic", {}).get("waves", {})
    temp = manifest.get("temporal", {}).get("countries", {})
    summary_lines = [f"**Phase 0 complete**", ""]
    if geo:
        summary_lines.append(f"Geographic: {len(geo)} waves")
        for w_label, info in sorted(geo.items()):
            summary_lines.append(
                f"- {w_label} ({info['year']}): {info['n_countries']} countries, "
                f"{info['n_constructs']} constructs"
            )
    if temp:
        summary_lines.append(f"\nTemporal: {len(temp)} countries with 3+ waves")
    create_markdown_artifact(key="phase-0-summary", markdown="\n".join(summary_lines))


# ═══════════════════════════════════════════════════════════════════════════
# MODE A: PER-WAVE GEOGRAPHIC TDA — INDIVIDUAL TASKS PER SUB-PHASE
# ═══════════════════════════════════════════════════════════════════════════
# Each sub-phase (FW, Ricci, Spectral, Persistence, Embeddings, GW) is its
# own @task so it appears as a separate row in the Prefect dashboard.
# task_run_name uses a template string for dynamic labeling.

@task(
    name="A1 · Floyd-Warshall",
    task_run_name="W{wave} · A1 Floyd-Warshall ({year})",
    tags=["julia", "mode-a", "floyd-warshall"],
    timeout_seconds=120,
)
def geo_a1_floyd_warshall(wave: int, year: int):
    """Floyd-Warshall shortest paths + mediator scores for one wave."""
    manifest = _wave_manifest(wave)
    dirs = _wave_dirs(wave)
    _run_julia(
        "tda_floyd_warshall.jl", f"W{wave}-FW",
        timeout=60, threads=1,
        extra_args=[str(manifest), str(dirs["fw"])],
    )


@task(
    name="A2 · Ricci Curvature",
    task_run_name="W{wave} · A2 Ricci Curvature ({year})",
    tags=["julia", "mode-a", "ricci"],
    timeout_seconds=900,
)
def geo_a2_ricci(wave: int, year: int):
    """Ollivier-Ricci curvature via Sinkhorn OT for one wave."""
    manifest = _wave_manifest(wave)
    dirs = _wave_dirs(wave)
    _run_julia(
        "tda_ricci_curvature.jl", f"W{wave}-Ricci",
        timeout=600,
        extra_args=[str(manifest), str(dirs["fw"]), str(dirs["ricci"])],
    )


@task(
    name="A3 · Spectral Distances",
    task_run_name="W{wave} · A3 Spectral Distances ({year})",
    tags=["julia", "mode-a", "spectral"],
    timeout_seconds=300,
)
def geo_a3_spectral(wave: int, year: int):
    """Laplacian spectral distances between all countries for one wave."""
    manifest = _wave_manifest(wave)
    dirs = _wave_dirs(wave)
    _run_julia(
        "tda_spectral_distances.jl", f"W{wave}-Spectral",
        timeout=120,
        extra_args=[str(manifest), str(dirs["spectral"])],
    )


@task(
    name="A4 · Persistent Homology",
    task_run_name="W{wave} · A4 Persistent Homology ({year})",
    tags=["python", "mode-a", "persistence"],
    timeout_seconds=300,
)
def geo_a4_persistence(wave: int, year: int):
    """Vietoris-Rips persistent homology via ripser for one wave."""
    manifest = _wave_manifest(wave)
    dirs = _wave_dirs(wave)
    _run_python_with_env(
        "scripts/debug/tda_persistent_homology.py", f"W{wave}-Persist",
        timeout=120,
        env_overrides={
            "TDA_MANIFEST": str(manifest),
            "TDA_FW_DIR": str(dirs["fw"]),
            "TDA_OUTPUT_DIR": str(dirs["persistence"]),
        },
    )


@task(
    name="A5 · Embeddings & Zones",
    task_run_name="W{wave} · A5 Embeddings & Zones ({year})",
    tags=["python", "mode-a", "visualization"],
    timeout_seconds=300,
)
def geo_a5_embeddings(wave: int, year: int, skip_ricci: bool):
    """MDS embedding + cultural zone coherence for one wave."""
    manifest = _wave_manifest(wave)
    dirs = _wave_dirs(wave)
    _run_python_with_env(
        "scripts/debug/tda_embeddings_and_zones.py", f"W{wave}-Embed",
        timeout=120,
        env_overrides={
            "TDA_SPECTRAL_PATH": str(dirs["spectral"] / "spectral_distance_matrix.csv"),
            "TDA_BOTTLENECK_PATH": str(dirs["persistence"] / "bottleneck_distances.csv"),
            "TDA_FEATURES_PATH": str(dirs["persistence"] / "topological_features.csv"),
            "TDA_RICCI_PATH": str(dirs["ricci"] / "ricci_summary.json"),
            "TDA_MEDIATOR_PATH": str(dirs["fw"] / "mediator_scores.json"),
            "TDA_SPECTRAL_FEAT": str(dirs["spectral"] / "spectral_features.json"),
            "TDA_OUTPUT_DIR": str(dirs["embeddings"]),
            "TDA_MANIFEST": str(manifest),
        },
    )


@task(
    name="A6 · Gromov-Wasserstein",
    task_run_name="W{wave} · A6 Gromov-Wasserstein ({year})",
    tags=["julia", "mode-a", "gw"],
    timeout_seconds=3600,
)
def geo_a6_gw(wave: int, year: int):
    """Gromov-Wasserstein alignment for all country pairs in one wave."""
    manifest = _wave_manifest(wave)
    dirs = _wave_dirs(wave)
    _run_julia(
        "tda_gromov_wasserstein.jl", f"W{wave}-GW",
        timeout=3600,
        extra_args=[str(manifest), str(dirs["fw"]), str(dirs["alignment"])],
    )


# ═══════════════════════════════════════════════════════════════════════════
# MODE B: MULTI-COUNTRY TEMPORAL TDA
# ═══════════════════════════════════════════════════════════════════════════

@task(
    name="B1 · Temporal Spectral",
    task_run_name="{alpha3} · B1 Temporal Spectral ({n_waves}w)",
    tags=["julia", "mode-b", "temporal"],
    timeout_seconds=120,
)
def temporal_country_tda(alpha3: str, n_waves: int):
    """Per-wave Floyd-Warshall + Laplacian spectral features for one country."""
    country_dir = ALLWAVE_DIR / "temporal" / alpha3
    manifest_path = country_dir / "manifest.json"

    if not manifest_path.exists():
        logger = get_run_logger()
        logger.warning(f"{alpha3}: temporal manifest not found, skipping")
        return

    _run_julia(
        "tda_temporal_spectral.jl", f"{alpha3}-TempSpec",
        timeout=60, threads=1,
        extra_args=[str(manifest_path), str(country_dir)],
    )


# ═══════════════════════════════════════════════════════════════════════════
# PHASE C: SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════

@task(
    name="Phase C · All-Wave Synthesis",
    task_run_name="Phase C · All-Wave Synthesis",
    tags=["python", "analysis"],
    timeout_seconds=120,
)
def phase_c_synthesis():
    """Cross-wave and cross-country synthesis analysis."""
    _run_python("scripts/debug/tda_allwave_analysis.py", "Synthesis", timeout=120)
    create_markdown_artifact(
        key="phase-c-summary",
        markdown="**Phase C complete** — convergence metrics, zone trends, and trajectories generated",
    )


# ═══════════════════════════════════════════════════════════════════════════
# FLOW DEFINITION
# ═══════════════════════════════════════════════════════════════════════════

@flow(
    name="allwave-tda-pipeline",
    description="All-wave TDA pipeline for WVS construct networks (W2-W7, 100+ countries)",
)
def allwave_tda_pipeline(
    run_geographic: bool = False,
    run_temporal: bool = False,
    run_synthesis: bool = False,
    waves: list[int] | None = None,
    countries: list[str] | None = None,
    min_countries: int = 5,
    min_waves: int = 3,
    skip_ricci: bool = False,
    skip_gw: bool = False,
    dry_run: bool = False,
):
    """
    Run the all-wave TDA pipeline.

    Parameters
    ----------
    run_geographic : Run Mode A (per-wave geographic TDA)
    run_temporal : Run Mode B (multi-country temporal TDA)
    run_synthesis : Run Phase C (cross-mode synthesis)
    waves : Specific waves for Mode A (default: all available)
    countries : Specific countries for Mode B (default: all eligible)
    min_countries : Minimum countries per wave for Mode A (default: 5)
    min_waves : Minimum waves per country for Mode B (default: 3)
    skip_ricci : Skip Ricci curvature in Mode A
    skip_gw : Skip GW alignment in Mode A
    dry_run : Print task graph without executing
    """
    logger = get_run_logger()
    logger.info("=" * 60)
    logger.info("ALL-WAVE TDA PIPELINE")
    logger.info("=" * 60)

    if dry_run:
        logger.info("\n[DRY RUN] Pipeline structure:")
        logger.info("  Phase 0: Convert all-wave surface → matrices")
        if run_geographic:
            w_list = waves or [3, 4, 5, 6, 7]
            logger.info(f"  Mode A (geographic): waves {w_list}")
            logger.info(f"    Per wave: FW → Ricci{'(skip)' if skip_ricci else ''} → "
                         f"Spectral → Persistence → Embeddings → GW{'(skip)' if skip_gw else ''}")
        if run_temporal:
            logger.info(f"  Mode B (temporal): countries with {min_waves}+ waves")
            logger.info("    Per country: temporal spectral (FW + Laplacian)")
        if run_synthesis:
            logger.info("  Phase C: Cross-wave synthesis + convergence analysis")
        logger.info("\n[DRY RUN] No tasks executed.")
        return

    # ── Phase 0: Convert ──────────────────────────────────────────────────
    mode = "both"
    if run_geographic and not run_temporal:
        mode = "geographic"
    elif run_temporal and not run_geographic:
        mode = "temporal"
    phase_0_convert(mode=mode, min_countries=min_countries, min_waves=min_waves)

    # ── Mode A: Geographic TDA per wave ───────────────────────────────────
    if run_geographic:
        logger.info("\n" + "─" * 60)
        logger.info("MODE A: Per-wave geographic TDA")
        logger.info("─" * 60)

        # Determine available waves from global manifest
        global_manifest_path = ALLWAVE_DIR / "matrices" / "global_manifest.json"
        with open(global_manifest_path) as f:
            gm = json.load(f)

        available_waves = sorted([
            int(w[1:]) for w in gm.get("geographic", {}).get("waves", {}).keys()
        ])
        target_waves = waves if waves else available_waves
        target_waves = [w for w in target_waves if w in available_waves]

        logger.info(f"Target waves: {target_waves}")

        for wave in target_waves:
            year = WAVE_YEARS.get(wave, 0)
            n_info = gm["geographic"]["waves"].get(f"W{wave}", {})
            n_countries = n_info.get("n_countries", "?")
            n_constructs = n_info.get("n_constructs", "?")
            logger.info(f"\n{'─' * 40}")
            logger.info(f"W{wave} ({year}): {n_countries} countries, {n_constructs} constructs")

            # A1: Floyd-Warshall (always)
            geo_a1_floyd_warshall(wave=wave, year=year)

            # A2: Ricci curvature (optional, depends on A1)
            if not skip_ricci:
                geo_a2_ricci(wave=wave, year=year)
            else:
                logger.info(f"  W{wave} A2 Ricci — SKIPPED")

            # A3: Spectral distances (depends on Phase 0 matrices, not on A1/A2)
            geo_a3_spectral(wave=wave, year=year)

            # A4: Persistent homology (depends on A1)
            geo_a4_persistence(wave=wave, year=year)

            # A5: Embeddings (depends on A3, A4, optionally A2)
            geo_a5_embeddings(wave=wave, year=year, skip_ricci=skip_ricci)

            # A6: GW alignment (optional, depends on A1)
            if not skip_gw and int(n_countries) >= 5:
                geo_a6_gw(wave=wave, year=year)
            else:
                reason = "SKIPPED" if skip_gw else f"only {n_countries} countries"
                logger.info(f"  W{wave} A6 GW — {reason}")

            logger.info(f"  W{wave} geographic TDA COMPLETE")

    # ── Mode B: Temporal TDA per country ──────────────────────────────────
    if run_temporal:
        logger.info("\n" + "─" * 60)
        logger.info("MODE B: Multi-country temporal TDA")
        logger.info("─" * 60)

        global_manifest_path = ALLWAVE_DIR / "matrices" / "global_manifest.json"
        with open(global_manifest_path) as f:
            gm = json.load(f)

        temp_countries = gm.get("temporal", {}).get("countries", {})
        available_countries = sorted(temp_countries.keys())
        target_countries = countries if countries else available_countries
        target_countries = [c for c in target_countries if c in available_countries]

        logger.info(f"Target countries: {len(target_countries)} "
                     f"({', '.join(target_countries[:10])}{'...' if len(target_countries) > 10 else ''})")

        for alpha3 in target_countries:
            n_waves = len(temp_countries.get(alpha3, {}).get("waves", []))
            temporal_country_tda(alpha3=alpha3, n_waves=n_waves)

    # ── Phase C: Synthesis ────────────────────────────────────────────────
    if run_synthesis:
        logger.info("\n" + "─" * 60)
        logger.info("PHASE C: Cross-mode synthesis")
        logger.info("─" * 60)
        phase_c_synthesis()

    logger.info("\n" + "=" * 60)
    logger.info("ALL-WAVE TDA PIPELINE COMPLETE")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="All-Wave TDA Pipeline for WVS Construct Networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pipeline/allwave_tda_pipeline.py --all
  python scripts/pipeline/allwave_tda_pipeline.py --geographic --waves 5 6 7
  python scripts/pipeline/allwave_tda_pipeline.py --temporal --countries MEX BRA IND
  python scripts/pipeline/allwave_tda_pipeline.py --all --skip-ricci --skip-gw
  python scripts/pipeline/allwave_tda_pipeline.py --all --dry-run
        """,
    )
    parser.add_argument("--all", action="store_true", help="Run all modes")
    parser.add_argument("--geographic", action="store_true", help="Run Mode A (per-wave)")
    parser.add_argument("--temporal", action="store_true", help="Run Mode B (per-country)")
    parser.add_argument("--synthesis", action="store_true", help="Run Phase C (synthesis)")
    parser.add_argument("--waves", type=int, nargs="+", help="Specific waves for Mode A")
    parser.add_argument("--countries", type=str, nargs="+", help="Specific countries for Mode B")
    parser.add_argument("--min-countries", type=int, default=5,
                        help="Min countries per wave (default: 5)")
    parser.add_argument("--min-waves", type=int, default=3,
                        help="Min waves per country (default: 3)")
    parser.add_argument("--skip-ricci", action="store_true",
                        help="Skip Ricci curvature (saves ~5 min/wave)")
    parser.add_argument("--skip-gw", action="store_true",
                        help="Skip GW alignment (saves ~20 min/wave)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print task graph without executing")
    args = parser.parse_args()

    if not args.all and not args.geographic and not args.temporal and not args.synthesis:
        parser.print_help()
        print("\nError: specify --all, --geographic, --temporal, or --synthesis")
        sys.exit(1)

    run_geo = args.all or args.geographic
    run_temp = args.all or args.temporal
    run_synth = args.all or args.synthesis

    allwave_tda_pipeline(
        run_geographic=run_geo,
        run_temporal=run_temp,
        run_synthesis=run_synth,
        waves=args.waves,
        countries=args.countries,
        min_countries=args.min_countries,
        min_waves=args.min_waves,
        skip_ricci=args.skip_ricci,
        skip_gw=args.skip_gw,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
