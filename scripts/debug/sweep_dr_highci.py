"""
sweep_dr_highci.py — Targeted DR re-sweep with high-quality bootstrap CIs.

Reads the v1 DR sweep (dr_sweep_results.json), filters to variable pairs above
a |γ| threshold, and re-estimates with many more bootstrap iterations.

Features:
  - Per-variable-pair incremental save (crash-safe, resume-friendly)
  - Saves after every completed variable pair
  - Atomic JSON writes (write .tmp, rename)

Usage:
    nohup python scripts/debug/sweep_dr_highci.py \
        --workers 3 --n-bootstrap 200 \
        > /tmp/dr_highci.log 2>&1 &
    tail -f /tmp/dr_highci.log

Output:
    data/results/dr_sweep_results_v2.json
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*convergence.*")
warnings.filterwarnings("ignore", message=".*Maximum Likelihood.*")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))

V1_SWEEP_PATH = ROOT / "data" / "results" / "dr_sweep_results.json"
OUTPUT_JSON = ROOT / "data" / "results" / "dr_sweep_results_v3.json"

# Defaults
DEFAULT_GAMMA_THRESHOLD = 0.15   # re-run pairs with |γ| > this from v1
DEFAULT_N_BOOTSTRAP = 200        # 20x more than v1's 10
DEFAULT_N_SIM = 2000             # v3: 4x more for tighter CIs
DEFAULT_PAIR_TIMEOUT = 120       # seconds per pair before giving up


class PairTimeout(Exception):
    """Raised when a single pair exceeds the time limit."""


def _alarm_handler(signum, frame):
    raise PairTimeout()


# Install once; each pair will call signal.alarm() to arm/disarm.
signal.signal(signal.SIGALRM, _alarm_handler)


def load_v1_pairs(gamma_threshold: float) -> List[Dict[str, Any]]:
    """Load v1 sweep and filter to pairs above threshold."""
    with open(V1_SWEEP_PATH) as f:
        v1 = json.load(f)

    pairs = []
    for pair_key, pair_data in v1.get("domain_pairs", {}).items():
        for est in pair_data.get("estimates", []):
            gamma = est.get("dr_gamma")
            if gamma is not None and abs(gamma) >= gamma_threshold:
                pairs.append({
                    "pair_key": pair_key,
                    "var_a": est["var_a"],
                    "var_b": est["var_b"],
                    "v1_gamma": gamma,
                    "v1_ci": est.get("dr_gamma_ci"),
                    "v1_v": est.get("dr_v"),
                    "v1_ks": est.get("dr_ks"),
                })
    # Sort by |γ| descending — strongest first
    pairs.sort(key=lambda p: -abs(p["v1_gamma"]))
    return pairs


def load_data() -> Tuple[dict, dict]:
    """Load and preprocess survey data."""
    from dataset_knowledge import los_mex_dict, enc_nom_dict
    from ses_analysis import AnalysisConfig
    from select_bridge_variables_semantic import SemanticVariableSelector

    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get("enc_dict", los_mex_dict.get("enc_dict", {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    # Build aggregated columns
    sel_path = ROOT / "data" / "results" / "semantic_variable_selection.json"
    if sel_path.exists():
        SemanticVariableSelector.build_aggregates(
            enc_dict, enc_nom_dict_rev, selection_path=sel_path)

    return enc_dict, enc_nom_dict_rev


def estimate_single_pair(
    var_a: str, var_b: str,
    enc_dict: dict, enc_nom_dict_rev: dict,
    n_sim: int, n_bootstrap: int,
) -> Dict[str, Any]:
    """Run DR estimator on a single variable pair with high bootstrap count."""
    from ses_regression import DoublyRobustBridgeEstimator

    col_a = var_a.split("|")[0]
    col_b = var_b.split("|")[0]
    domain_a = var_a.split("|")[1]
    domain_b = var_b.split("|")[1]

    survey_a = enc_nom_dict_rev.get(domain_a)
    survey_b = enc_nom_dict_rev.get(domain_b)
    df_a = enc_dict.get(survey_a, {}).get("dataframe") if survey_a else None
    df_b = enc_dict.get(survey_b, {}).get("dataframe") if survey_b else None

    if not isinstance(df_a, pd.DataFrame) or not isinstance(df_b, pd.DataFrame):
        return {"error": "DataFrame not found"}

    if col_a not in df_a.columns or col_b not in df_b.columns:
        return {"error": f"Column not found: {col_a} or {col_b}"}

    est = DoublyRobustBridgeEstimator(
        n_sim=n_sim, n_bootstrap=n_bootstrap, max_categories=5)

    r = est.estimate(
        var_id_a=var_a, var_id_b=var_b,
        df_a=df_a, df_b=df_b,
        col_a=col_a, col_b=col_b)

    if not r:
        return {"error": "Estimator returned None"}

    return {
        "dr_gamma": round(r["gamma"], 4),
        "dr_gamma_ci": [round(r["gamma_ci_95"][0], 4),
                        round(r["gamma_ci_95"][1], 4)],
        "dr_v": round(r["cramers_v"], 4),
        "dr_ks": round(r["propensity_overlap"], 4),
        "dr_ks_warning": r.get("ks_warning", False),
        "n_trimmed": r.get("n_trimmed", 0),
    }


def save_checkpoint(results: Dict, metadata: dict, path: Path):
    """Atomic save."""
    output = {
        "metadata": {**metadata, "timestamp": datetime.now().isoformat()},
        "estimates": results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(
        description="Targeted DR re-sweep with high-quality bootstrap CIs")
    parser.add_argument("--gamma-threshold", type=float, default=DEFAULT_GAMMA_THRESHOLD,
                        help=f"Min |γ| from v1 to include (default: {DEFAULT_GAMMA_THRESHOLD})")
    parser.add_argument("--n-bootstrap", type=int, default=DEFAULT_N_BOOTSTRAP,
                        help=f"Bootstrap iterations (default: {DEFAULT_N_BOOTSTRAP})")
    parser.add_argument("--n-sim", type=int, default=DEFAULT_N_SIM,
                        help=f"Simulation size (default: {DEFAULT_N_SIM})")
    parser.add_argument("--workers", type=int, default=1,
                        help="Parallel workers")
    parser.add_argument("--pair-timeout", type=int, default=DEFAULT_PAIR_TIMEOUT,
                        help=f"Max seconds per pair (default: {DEFAULT_PAIR_TIMEOUT})")
    parser.add_argument("--no-resume", action="store_true",
                        help="Start fresh, ignore existing checkpoint")
    parser.add_argument("--output", type=Path, default=OUTPUT_JSON,
                        help=f"Output path (default: {OUTPUT_JSON})")
    args = parser.parse_args()

    t0 = time.time()
    print("=" * 70)
    print("DR High-CI Re-sweep")
    print("=" * 70)
    print(f"  gamma_threshold: {args.gamma_threshold}")
    print(f"  n_bootstrap: {args.n_bootstrap}")
    print(f"  n_sim: {args.n_sim}")
    print(f"  workers: {args.workers}")
    print(f"  pair_timeout: {args.pair_timeout}s")
    print(f"  output: {args.output}")
    print()

    # Load v1 pairs
    print("Loading v1 sweep results...", flush=True)
    pairs = load_v1_pairs(args.gamma_threshold)
    print(f"  {len(pairs)} variable pairs with |γ| >= {args.gamma_threshold}")
    print()

    # Load existing checkpoint for resume
    existing: Dict[str, Dict] = {}
    if not args.no_resume and args.output.exists():
        try:
            with open(args.output) as f:
                prev = json.load(f)
            existing = prev.get("estimates", {})
            print(f"  Resuming: {len(existing)} pairs already computed")
        except Exception as e:
            print(f"  Warning: could not load checkpoint ({e})")

    # Filter out already-done pairs
    def _pair_id(p):
        return f"{p['var_a']}::{p['var_b']}"

    pairs_todo = [p for p in pairs if _pair_id(p) not in existing]
    print(f"  Pairs remaining: {len(pairs_todo)} / {len(pairs)}")
    print()

    # Load survey data
    print("Loading survey data...", flush=True)
    enc_dict, enc_nom_dict_rev = load_data()
    print("  Data loaded.\n", flush=True)

    metadata = {
        "gamma_threshold": args.gamma_threshold,
        "n_bootstrap": args.n_bootstrap,
        "n_sim": args.n_sim,
        "n_total_pairs": len(pairs),
        "pair_timeout_s": args.pair_timeout,
        "v1_source": str(V1_SWEEP_PATH),
    }

    results = dict(existing)
    n_done = 0
    n_total = len(pairs_todo)

    # Sequential processing with per-pair save
    # (ThreadPoolExecutor with workers>1 would parallelize, but DR is CPU-heavy
    #  and statsmodels isn't thread-safe; use workers=1 for safety)
    if args.workers <= 1:
        for p in pairs_todo:
            pid = _pair_id(p)
            pair_t0 = time.time()
            signal.alarm(args.pair_timeout)
            try:
                result = estimate_single_pair(
                    p["var_a"], p["var_b"],
                    enc_dict, enc_nom_dict_rev,
                    args.n_sim, args.n_bootstrap)
                result["v1_gamma"] = p["v1_gamma"]
                result["v1_ci"] = p["v1_ci"]
            except PairTimeout:
                result = {"error": f"TIMEOUT>{args.pair_timeout}s",
                          "v1_gamma": p["v1_gamma"]}
            except Exception as e:
                result = {"error": str(e), "v1_gamma": p["v1_gamma"]}
            finally:
                signal.alarm(0)

            results[pid] = result
            n_done += 1
            pair_elapsed = time.time() - pair_t0
            total_elapsed = time.time() - t0

            # ETA
            avg_per_pair = total_elapsed / n_done
            remaining = n_total - n_done
            eta_s = avg_per_pair * remaining
            eta_min = eta_s / 60

            # Status line
            gamma = result.get("dr_gamma")
            ci = result.get("dr_gamma_ci")
            ci_width = ci[1] - ci[0] if ci else None
            ci_excl_zero = ci and (ci[0] > 0 or ci[1] < 0) if ci else False

            if gamma is not None:
                ci_str = f"[{ci[0]:+.3f},{ci[1]:+.3f}]" if ci else "—"
                sig = " ***" if ci_excl_zero else ""
                print(
                    f"  [{n_done}/{n_total}] {total_elapsed:.0f}s "
                    f"(ETA {eta_min:.0f}m) "
                    f"| γ={gamma:+.3f} CI={ci_str} w={ci_width:.3f}{sig} "
                    f"| v1={p['v1_gamma']:+.3f} "
                    f"| {p['var_a'][:30]} × {p['var_b'][:30]} "
                    f"({pair_elapsed:.1f}s)",
                    flush=True)
            else:
                print(
                    f"  [{n_done}/{n_total}] {total_elapsed:.0f}s "
                    f"(ETA {eta_min:.0f}m) "
                    f"| FAIL: {result.get('error', '?')[:50]} "
                    f"| {p['var_a'][:30]} × {p['var_b'][:30]}",
                    flush=True)

            # Save after every pair
            metadata["elapsed_seconds"] = round(time.time() - t0, 1)
            metadata["n_completed"] = len(results)
            save_checkpoint(results, metadata, args.output)
    else:
        # Multi-worker path
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def _run(p):
            return _pair_id(p), p, estimate_single_pair(
                p["var_a"], p["var_b"],
                enc_dict, enc_nom_dict_rev,
                args.n_sim, args.n_bootstrap)

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(_run, p): p for p in pairs_todo}
            for future in as_completed(futures):
                try:
                    pid, p, result = future.result()
                    result["v1_gamma"] = p["v1_gamma"]
                    result["v1_ci"] = p["v1_ci"]
                except Exception as e:
                    p = futures[future]
                    pid = _pair_id(p)
                    result = {"error": str(e), "v1_gamma": p["v1_gamma"]}

                results[pid] = result
                n_done += 1
                total_elapsed = time.time() - t0
                avg_per_pair = total_elapsed / n_done
                remaining = n_total - n_done
                eta_min = (avg_per_pair * remaining / max(args.workers, 1)) / 60

                gamma = result.get("dr_gamma")
                ci = result.get("dr_gamma_ci")
                ci_excl_zero = ci and (ci[0] > 0 or ci[1] < 0) if ci else False
                sig = " ***" if ci_excl_zero else ""

                if gamma is not None:
                    ci_str = f"[{ci[0]:+.3f},{ci[1]:+.3f}]" if ci else "—"
                    print(
                        f"  [{n_done}/{n_total}] {total_elapsed:.0f}s "
                        f"(ETA {eta_min:.0f}m) "
                        f"| γ={gamma:+.3f} CI={ci_str}{sig} "
                        f"| v1={p['v1_gamma']:+.3f}",
                        flush=True)
                else:
                    print(
                        f"  [{n_done}/{n_total}] {total_elapsed:.0f}s "
                        f"| FAIL",
                        flush=True)

                # Save after every pair
                metadata["elapsed_seconds"] = round(time.time() - t0, 1)
                metadata["n_completed"] = len(results)
                save_checkpoint(results, metadata, args.output)

    # Summary
    elapsed = time.time() - t0
    all_results = list(results.values())
    gammas = [r["dr_gamma"] for r in all_results if "dr_gamma" in r]
    ci_widths = [r["dr_gamma_ci"][1] - r["dr_gamma_ci"][0]
                 for r in all_results if r.get("dr_gamma_ci")]
    n_excl_zero = sum(1 for r in all_results
                      if r.get("dr_gamma_ci")
                      and (r["dr_gamma_ci"][0] > 0 or r["dr_gamma_ci"][1] < 0))

    print()
    print("=" * 70)
    print("SWEEP COMPLETE")
    print("=" * 70)
    print(f"  Elapsed: {elapsed:.0f}s ({elapsed/3600:.1f}h)")
    print(f"  Pairs completed: {len(gammas)} / {len(pairs)}")
    if ci_widths:
        print(f"  CI width: mean={np.mean(ci_widths):.3f}, "
              f"median={np.median(ci_widths):.3f}, "
              f"P10={np.percentile(ci_widths, 10):.3f}, "
              f"P90={np.percentile(ci_widths, 90):.3f}")
        print(f"  CIs excluding zero: {n_excl_zero}/{len(ci_widths)} "
              f"({100*n_excl_zero/len(ci_widths):.1f}%)")
    print(f"  Output: {args.output}")


if __name__ == "__main__":
    main()
