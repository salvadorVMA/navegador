#!/usr/bin/env python
"""
GTE All-Waves Pipeline
======================

Runs camps, fingerprints, and message passing for WVS waves 3-7.

Phase 1: Camps (from weight matrices, fast — ~seconds per wave)
Phase 2: Fingerprints (W7 from pre-built CSVs, W3-W6 from raw Time Series)
Phase 3: Message passing (BP + spectral + PPR for each wave)

The Time Series CSV (1.3 GB) is loaded once and cached in memory.
Total runtime estimate: ~1-2 hours on 2-core.

Usage:
    python scripts/debug/run_gte_allwaves.py                # all phases, W3-W7
    python scripts/debug/run_gte_allwaves.py --waves 5 6    # specific waves
    python scripts/debug/run_gte_allwaves.py --skip-fingerprints  # camps + MP only
    python scripts/debug/run_gte_allwaves.py --skip-mp           # camps + fingerprints only
    python scripts/debug/run_gte_allwaves.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import VALID_WAVES, load_manifest


def phase1_camps(waves: list[int]) -> None:
    """Compute Fiedler bipartitions from weight matrices."""
    from scripts.debug.compute_gte_camps import run_wave
    print("\n" + "=" * 70)
    print("  PHASE 1: CAMPS (Fiedler bipartitions)")
    print("=" * 70)
    for w in waves:
        run_wave(w)


def phase2_fingerprints(waves: list[int]) -> None:
    """Compute SES fingerprints.

    W7: fast path from pre-built julia_bridge CSVs.
    W3-W6: loads the 1.3 GB Time Series CSV once, then iterates.
    """
    from scripts.debug.compute_gte_fingerprints import (
        compute_fingerprints,
        JULIA_BRIDGE_DIR,
    )
    from scripts.debug.mp_utils import GTE_DIR
    import json

    print("\n" + "=" * 70)
    print("  PHASE 2: FINGERPRINTS (SES Spearman ρ)")
    print("=" * 70)

    # Separate W7 (fast) from W3-W6 (need Time Series)
    fast_waves = [w for w in waves if w == 7]
    slow_waves = [w for w in waves if w != 7]

    # Fast path: W7 from pre-built CSVs
    for w in fast_waves:
        manifest = load_manifest(wave=w)
        countries = sorted(manifest["countries"])
        construct_names = [l.split("|")[0] for l in manifest.get("construct_index", [])]
        out_dir = GTE_DIR / f"W{w}" / "fingerprints"
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  W{w}: {len(countries)} countries (fast path)")
        t0 = time.time()
        for i, c in enumerate(countries):
            try:
                result = compute_fingerprints(c, w, construct_names)
                with open(out_dir / f"{c}.json", "w") as f:
                    json.dump(result, f, indent=2)
                if (i + 1) % 10 == 0:
                    print(f"    [{i+1}/{len(countries)}] ...")
            except Exception as e:
                print(f"    {c}: ERROR — {e}")
        print(f"  W{w} done in {time.time()-t0:.1f}s")

    # Slow path: W3-W6 from raw Time Series
    if slow_waves:
        print(f"\n  Loading WVS Time Series CSV (1.3 GB, ~5 min)...")
        t_load = time.time()

        # Pre-warm the WVSLoader cache by calling load_slice once
        from wvs_loader import WVSLoader
        loader = WVSLoader(wvs_dir=ROOT / "data" / "wvs")
        # Trigger Time Series parse
        _ = loader.load_slice(wave=3, countries=["MEX"])
        print(f"  Time Series loaded in {time.time()-t_load:.1f}s")

        from scripts.debug.build_wvs_constructs_multi import (
            build_qcode_resolver,
            build_wvs_constructs_context,
        )
        from scripts.debug.compute_gte_fingerprints import _get_svs_and_overrides
        import math
        from scipy.stats import spearmanr
        import warnings
        from scipy.stats import ConstantInputWarning
        warnings.filterwarnings("ignore", category=ConstantInputWarning)

        svs, overrides = _get_svs_and_overrides()
        SES_DIMS = ["escol", "Tam_loc", "sexo", "edad"]

        for w in slow_waves:
            manifest = load_manifest(wave=w)
            countries = sorted(manifest["countries"])
            construct_names = [l.split("|")[0] for l in manifest.get("construct_index", [])]
            construct_set = set(construct_names)
            out_dir = GTE_DIR / f"W{w}" / "fingerprints"
            out_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n  W{w}: {len(countries)} countries, "
                  f"{len(construct_names)} constructs")
            t0 = time.time()

            # Check if pre-built CSVs exist for this wave
            for i, c in enumerate(countries):
                try:
                    csv_path = JULIA_BRIDGE_DIR / f"WVS_W{w}_{c}.csv"
                    if csv_path.exists():
                        # Fast path even for earlier waves if CSV exists
                        result = compute_fingerprints(c, w, construct_names)
                    else:
                        # Slow path: build from raw
                        df = loader.load_slice(wave=w, countries=[c])
                        n_resp = len(df)
                        if n_resp < 50:
                            result = {"country": c, "wave": w, "n_constructs": 0,
                                      "n_respondents": n_resp, "constructs": {}}
                        else:
                            resolver = build_qcode_resolver(
                                loader.equivalences, w, list(df.columns))
                            df, mf = build_wvs_constructs_context(
                                df, svs, overrides, resolver, f"W{w}_{c}")

                            constructs = {}
                            for entry in mf:
                                col = entry.get("column")
                                if col is None:
                                    continue
                                cname = col.replace("wvs_agg_", "")
                                if cname not in construct_set:
                                    continue
                                rhos = {}
                                n_valid = 0
                                for dim in SES_DIMS:
                                    if dim not in df.columns:
                                        continue
                                    mask = df[[col, dim]].dropna()
                                    if len(mask) < 30:
                                        continue
                                    with warnings.catch_warnings():
                                        warnings.simplefilter("ignore")
                                        rho, _ = spearmanr(mask[col], mask[dim])
                                    if not math.isnan(rho):
                                        rhos[f"rho_{dim}"] = round(rho, 6)
                                    n_valid = max(n_valid, len(mask))
                                if not rhos:
                                    continue
                                mag = math.sqrt(
                                    sum(v ** 2 for v in rhos.values()) / len(rhos))
                                dominant = max(rhos, key=lambda k: abs(rhos[k]))
                                constructs[cname] = {
                                    **{f"rho_{d}": rhos.get(f"rho_{d}", 0.0)
                                       for d in SES_DIMS},
                                    "ses_magnitude": round(mag, 6),
                                    "dominant_dim": dominant.replace("rho_", ""),
                                    "n_valid": n_valid,
                                }
                            result = {"country": c, "wave": w,
                                      "n_constructs": len(constructs),
                                      "n_respondents": n_resp,
                                      "constructs": constructs}

                    with open(out_dir / f"{c}.json", "w") as f:
                        json.dump(result, f, indent=2)
                    if (i + 1) % 5 == 0 or i == 0:
                        print(f"    [{i+1}/{len(countries)}] {c}: "
                              f"{result['n_constructs']} constructs")
                except Exception as e:
                    print(f"    [{i+1}/{len(countries)}] {c}: ERROR — {e}")

            print(f"  W{w} done in {time.time()-t0:.1f}s")


def phase3_mp(waves: list[int]) -> None:
    """Run message passing (BP + spectral + PPR) for each wave."""
    from scripts.debug.mp_belief_propagation import run_country as run_bp
    from scripts.debug.mp_spectral_diffusion import run_country as run_spectral
    from scripts.debug.mp_ppr_influence import run_country as run_ppr
    from scripts.debug.mp_utils import get_output_dir, save_json

    print("\n" + "=" * 70)
    print("  PHASE 3: MESSAGE PASSING (BP + spectral + PPR)")
    print("=" * 70)

    for w in waves:
        manifest = load_manifest(wave=w)
        countries = sorted(manifest["countries"])
        out_dir = get_output_dir(wave=w)

        print(f"\n  W{w}: {len(countries)} countries → {out_dir}")
        t0 = time.time()

        for i, c in enumerate(countries):
            # BP
            try:
                result = run_bp(c, wave=w)
                save_json(result, out_dir / f"{c}_bp.json")
            except Exception as e:
                print(f"    BP {c}: ERROR — {e}")

            # Spectral
            try:
                result = run_spectral(c, wave=w)
                save_json(result, out_dir / f"{c}_spectral.json")
            except Exception as e:
                print(f"    Spectral {c}: ERROR — {e}")

            # PPR
            try:
                result = run_ppr(c, wave=w)
                save_json(result, out_dir / f"{c}_ppr.json")
            except Exception as e:
                print(f"    PPR {c}: ERROR — {e}")

            if (i + 1) % 5 == 0:
                elapsed = time.time() - t0
                rate = elapsed / (i + 1)
                remaining = rate * (len(countries) - i - 1)
                print(f"    [{i+1}/{len(countries)}] "
                      f"{elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining")

        elapsed = time.time() - t0
        print(f"  W{w} MP done in {elapsed:.1f}s")


def main():
    parser = argparse.ArgumentParser(
        description="GTE All-Waves Pipeline: camps + fingerprints + message passing")
    parser.add_argument("--waves", type=int, nargs="+", default=VALID_WAVES,
                        help=f"Waves to process (default: {VALID_WAVES})")
    parser.add_argument("--skip-camps", action="store_true",
                        help="Skip camp computation")
    parser.add_argument("--skip-fingerprints", action="store_true",
                        help="Skip fingerprint computation")
    parser.add_argument("--skip-mp", action="store_true",
                        help="Skip message passing")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print plan without executing")
    args = parser.parse_args()

    waves = sorted(args.waves)
    print(f"GTE All-Waves Pipeline")
    print(f"  Waves: {waves}")
    print(f"  Camps: {'skip' if args.skip_camps else 'run'}")
    print(f"  Fingerprints: {'skip' if args.skip_fingerprints else 'run'}")
    print(f"  Message Passing: {'skip' if args.skip_mp else 'run'}")

    if args.dry_run:
        for w in waves:
            m = load_manifest(wave=w)
            print(f"  W{w}: {len(m['countries'])} countries, "
                  f"{m['n_constructs']} constructs")
        print("\n  (dry run — nothing executed)")
        return

    t_total = time.time()

    if not args.skip_camps:
        phase1_camps(waves)

    if not args.skip_fingerprints:
        phase2_fingerprints(waves)

    if not args.skip_mp:
        phase3_mp(waves)

    elapsed = time.time() - t_total
    print(f"\n{'=' * 70}")
    print(f"  ALL DONE in {elapsed/60:.1f} minutes")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
