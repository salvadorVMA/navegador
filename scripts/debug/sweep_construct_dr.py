"""
sweep_construct_dr.py — DR sweep across all construct-level variable pairs.

Builds v4 construct variables (agg_* columns), then runs DoublyRobustBridgeEstimator
on all cross-domain construct pairs (~4,979 pairs).

Features:
  - Uses build_construct_variables.build_v4_constructs() for aggregated columns
  - Per-pair incremental save (crash-safe, resume-friendly)
  - Atomic JSON writes (write .tmp, rename)
  - Per-pair SIGALRM timeout
  - Progress/ETA reporting

Usage:
    nohup python scripts/debug/sweep_construct_dr.py \
        --n-bootstrap 200 --n-sim 2000 \
        > /tmp/construct_dr_sweep.log 2>&1 &
    tail -f /tmp/construct_dr_sweep.log

Output:
    data/results/construct_dr_sweep.json
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

OUTPUT_JSON = ROOT / "data" / "results" / "construct_dr_sweep.json"

# Defaults
DEFAULT_N_BOOTSTRAP = 200
DEFAULT_N_SIM = 2000
DEFAULT_PAIR_TIMEOUT = 120   # seconds per pair


class PairTimeout(Exception):
    """Raised when a single pair exceeds the time limit."""


def _alarm_handler(signum, frame):
    raise PairTimeout()


signal.signal(signal.SIGALRM, _alarm_handler)


def load_data() -> Tuple[dict, dict, list]:
    """Load survey data, build construct variables, return manifest."""
    from dataset_knowledge import enc_dict, enc_nom_dict
    from build_construct_variables import build_v4_constructs

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    print("Building v4 construct variables...", flush=True)
    enc_dict, manifest = build_v4_constructs(enc_dict, enc_nom_dict_rev)

    return enc_dict, enc_nom_dict_rev, manifest


def build_pair_list(manifest: list) -> List[Dict[str, Any]]:
    """Build all cross-domain construct pairs from manifest."""
    # Group constructs by domain
    by_domain: Dict[str, list] = {}
    for m in manifest:
        if not m.get("column"):
            continue
        domain = m["key"].split("|")[0]
        by_domain.setdefault(domain, []).append(m)

    pairs = []
    domains = sorted(by_domain.keys())
    for i, d1 in enumerate(domains):
        for d2 in domains[i+1:]:
            for c1 in by_domain[d1]:
                for c2 in by_domain[d2]:
                    pairs.append({
                        "var_a": c1["var_id"],
                        "var_b": c2["var_id"],
                        "construct_a": c1["key"],
                        "construct_b": c2["key"],
                        "type_a": c1["type"],
                        "type_b": c2["type"],
                        "alpha_a": c1.get("alpha"),
                        "alpha_b": c2.get("alpha"),
                    })

    return pairs


def estimate_single_pair(
    var_a: str, var_b: str,
    enc_dict: dict, enc_nom_dict_rev: dict,
    n_sim: int, n_bootstrap: int,
) -> Dict[str, Any]:
    """Run DR estimator on a single construct pair."""
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
        "dr_nmi": round(r.get("normalized_mi", 0), 4),
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
        description="DR sweep across all construct-level variable pairs")
    parser.add_argument("--n-bootstrap", type=int, default=DEFAULT_N_BOOTSTRAP,
                        help=f"Bootstrap iterations (default: {DEFAULT_N_BOOTSTRAP})")
    parser.add_argument("--n-sim", type=int, default=DEFAULT_N_SIM,
                        help=f"Simulation size (default: {DEFAULT_N_SIM})")
    parser.add_argument("--pair-timeout", type=int, default=DEFAULT_PAIR_TIMEOUT,
                        help=f"Max seconds per pair (default: {DEFAULT_PAIR_TIMEOUT})")
    parser.add_argument("--no-resume", action="store_true",
                        help="Start fresh, ignore existing checkpoint")
    parser.add_argument("--output", type=Path, default=OUTPUT_JSON,
                        help=f"Output path (default: {OUTPUT_JSON})")
    parser.add_argument("--save-every", type=int, default=1,
                        help="Save checkpoint every N pairs (default: 1)")
    args = parser.parse_args()

    t0 = time.time()
    print("=" * 70)
    print("Construct-Level DR Sweep")
    print("=" * 70)
    print(f"  n_bootstrap: {args.n_bootstrap}")
    print(f"  n_sim: {args.n_sim}")
    print(f"  pair_timeout: {args.pair_timeout}s")
    print(f"  output: {args.output}")
    print(f"  save_every: {args.save_every}")
    print()

    # Load data and build constructs
    print("Loading data...", flush=True)
    enc_dict, enc_nom_dict_rev, manifest = load_data()

    # Build all cross-domain pairs
    pairs = build_pair_list(manifest)
    print(f"  {len(pairs)} cross-domain construct pairs", flush=True)
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

    metadata = {
        "n_bootstrap": args.n_bootstrap,
        "n_sim": args.n_sim,
        "n_total_pairs": len(pairs),
        "pair_timeout_s": args.pair_timeout,
        "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
        "construct_source": "semantic_variable_selection_v4.json",
    }

    results = dict(existing)
    n_done = 0
    n_total = len(pairs_todo)
    n_since_save = 0

    for p in pairs_todo:
        pid = _pair_id(p)
        pair_t0 = time.time()
        signal.alarm(args.pair_timeout)
        try:
            result = estimate_single_pair(
                p["var_a"], p["var_b"],
                enc_dict, enc_nom_dict_rev,
                args.n_sim, args.n_bootstrap)
        except PairTimeout:
            result = {"error": f"TIMEOUT>{args.pair_timeout}s"}
        except Exception as e:
            result = {"error": str(e)}
        finally:
            signal.alarm(0)

        # Attach construct metadata
        result["construct_a"] = p["construct_a"]
        result["construct_b"] = p["construct_b"]
        result["type_a"] = p["type_a"]
        result["type_b"] = p["type_b"]

        results[pid] = result
        n_done += 1
        n_since_save += 1
        pair_elapsed = time.time() - pair_t0
        total_elapsed = time.time() - t0

        # ETA
        avg_per_pair = total_elapsed / n_done
        remaining = n_total - n_done
        eta_s = avg_per_pair * remaining
        eta_h = eta_s / 3600

        # Status line
        gamma = result.get("dr_gamma")
        ci = result.get("dr_gamma_ci")
        ci_width = ci[1] - ci[0] if ci else None
        ci_excl_zero = ci and (ci[0] > 0 or ci[1] < 0) if ci else False

        if gamma is not None:
            ci_str = f"[{ci[0]:+.3f},{ci[1]:+.3f}]" if ci else "—"
            sig = " ***" if ci_excl_zero else ""
            nmi = result.get("dr_nmi", 0)
            nmi_flag = " NM!" if nmi > 0.02 and abs(gamma) < 0.05 else ""
            print(
                f"  [{n_done}/{n_total}] {total_elapsed:.0f}s "
                f"(ETA {eta_h:.1f}h) "
                f"| γ={gamma:+.3f} NMI={nmi:.3f} CI={ci_str} w={ci_width:.3f}{sig}{nmi_flag} "
                f"| {p['construct_a'][:25]} × {p['construct_b'][:25]} "
                f"({pair_elapsed:.1f}s)",
                flush=True)
        else:
            print(
                f"  [{n_done}/{n_total}] {total_elapsed:.0f}s "
                f"(ETA {eta_h:.1f}h) "
                f"| FAIL: {result.get('error', '?')[:50]} "
                f"| {p['construct_a'][:25]} × {p['construct_b'][:25]}",
                flush=True)

        # Checkpoint save every N pairs
        if n_since_save >= args.save_every:
            metadata["elapsed_seconds"] = round(time.time() - t0, 1)
            metadata["n_completed"] = len(results)
            save_checkpoint(results, metadata, args.output)
            n_since_save = 0

    # Final save
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
    if gammas:
        print(f"  γ: mean={np.mean(np.abs(gammas)):.3f}, "
              f"median={np.median(np.abs(gammas)):.3f}, "
              f"max={np.max(np.abs(gammas)):.3f}")
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
