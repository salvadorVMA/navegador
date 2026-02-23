"""
sweep_cross_domain.py — Full 276-pair domain sweep of cross-dataset bivariate estimates.

For every pair of viable survey domains (26 domains minus JUE/CON), selects
3 representative variables per domain (top Shannon entropy) and estimates
all 9 cross-pairs via the SES bridge simulation.

Outputs a structured JSON to /tmp/cross_domain_sweep.json that can be
consumed by the visualization script on the feature/knowledge-graph branch.

Usage:
    python scripts/debug/sweep_cross_domain.py
    python scripts/debug/sweep_cross_domain.py --workers 4 --vars-per-domain 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Suppress convergence warnings from statsmodels — they are expected for
# variables with few categories or sparse cells.
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*convergence.*")
warnings.filterwarnings("ignore", message=".*Maximum Likelihood.*")

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUTPUT_PATH = Path("/tmp/cross_domain_sweep.json")

# Domains to exclude: JUE has 0 questions, CON has 1 question
EXCLUDE_DOMAINS = {"JUE", "CON"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> Tuple[dict, dict, dict, dict]:
    """Load and SES-preprocess survey data.

    Returns (enc_dict, enc_nom_dict_rev, rev_topic_dict, pregs_dict).
    The enc_dict DataFrames are preprocessed to include standardised SES
    columns (sexo, edad, region, empleo) required by the bivariate estimator.
    """
    from dataset_knowledge import (
        los_mex_dict, rev_topic_dict, pregs_dict, enc_nom_dict, DATA_AVAILABLE
    )
    if not DATA_AVAILABLE:
        print("ERROR: Survey data not available.", file=sys.stderr)
        sys.exit(1)

    # SES preprocessing — creates edad/region/empleo from raw columns
    from ses_analysis import AnalysisConfig
    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get("enc_dict", los_mex_dict.get("enc_dict", {}))

    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}
    return enc_dict, enc_nom_dict_rev, rev_topic_dict, pregs_dict


# ---------------------------------------------------------------------------
# Variable selection (top entropy)
# ---------------------------------------------------------------------------

def _shannon_entropy(series: pd.Series) -> float:
    """Shannon entropy of a categorical series (higher = more dispersed)."""
    counts = series.dropna().value_counts(normalize=True)
    counts = counts[counts > 0]
    return float(-np.sum(counts * np.log2(counts)))


def select_representative_vars(
    domain: str,
    pregs_dict: dict,
    enc_dict: dict,
    enc_nom_dict_rev: dict,
    n_vars: int = 3,
) -> List[str]:
    """
    Select the top-N highest-entropy variables for a domain.
    Falls back to evenly spaced variables if entropy fails.
    """
    # Collect all var IDs for this domain
    domain_vars = [qid for qid in pregs_dict if qid.endswith(f"|{domain}")]
    if not domain_vars:
        return []

    # Get the DataFrame for this domain
    survey_name = enc_nom_dict_rev.get(domain)
    if not survey_name:
        return domain_vars[:n_vars]
    df = enc_dict.get(survey_name, {}).get('dataframe')
    if not isinstance(df, pd.DataFrame):
        return domain_vars[:n_vars]

    # Compute entropy per variable
    scored: List[Tuple[str, float]] = []
    for qid in domain_vars:
        col = qid.split("|")[0]
        if col in df.columns:
            try:
                h = _shannon_entropy(df[col])
                scored.append((qid, h))
            except Exception:
                pass

    if len(scored) < n_vars:
        # Fallback: evenly spaced
        step = max(1, len(domain_vars) // n_vars)
        return [domain_vars[i * step] for i in range(min(n_vars, len(domain_vars)))]

    # Top-N by entropy
    scored.sort(key=lambda x: -x[1])
    return [qid for qid, _ in scored[:n_vars]]


# ---------------------------------------------------------------------------
# Single domain-pair estimation
# ---------------------------------------------------------------------------

def estimate_domain_pair(
    domain_a: str,
    domain_b: str,
    vars_a: List[str],
    vars_b: List[str],
    enc_dict: dict,
    enc_nom_dict_rev: dict,
) -> Dict[str, Any]:
    """
    Estimate all cross-pairs between vars_a and vars_b.
    Returns a summary dict for this domain pair.
    """
    from ses_regression import CrossDatasetBivariateEstimator

    survey_name_a = enc_nom_dict_rev.get(domain_a)
    survey_name_b = enc_nom_dict_rev.get(domain_b)

    df_a = enc_dict.get(survey_name_a, {}).get('dataframe') if survey_name_a else None
    df_b = enc_dict.get(survey_name_b, {}).get('dataframe') if survey_name_b else None

    if not isinstance(df_a, pd.DataFrame) or not isinstance(df_b, pd.DataFrame):
        return {
            "domain_a": domain_a, "domain_b": domain_b,
            "estimates": [], "mean_v": None, "max_v": None,
            "n_significant": 0, "n_total": 0, "error": "DataFrame not found",
        }

    estimator = CrossDatasetBivariateEstimator(n_sim=2000)
    estimates: List[Dict[str, Any]] = []

    for va in vars_a:
        col_a = va.split("|")[0]
        if col_a not in df_a.columns:
            continue
        for vb in vars_b:
            col_b = vb.split("|")[0]
            if col_b not in df_b.columns:
                continue
            try:
                est = estimator.estimate(
                    var_id_a=va, var_id_b=vb,
                    df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b,
                )
                if est is not None:
                    estimates.append({
                        "var_a": est["var_a"],
                        "var_b": est["var_b"],
                        "cramers_v": round(est["cramers_v"], 4),
                        "p_value": round(est["p_value"], 6),
                        "n_sim": est["n_simulated"],
                    })
            except Exception as e:
                estimates.append({
                    "var_a": va, "var_b": vb,
                    "error": str(e),
                })

    # Aggregate
    valid = [e for e in estimates if "cramers_v" in e]
    vs = [e["cramers_v"] for e in valid]
    n_sig = sum(1 for e in valid if e["p_value"] < 0.05)

    return {
        "domain_a": domain_a,
        "domain_b": domain_b,
        "estimates": estimates,
        "mean_v": round(float(np.mean(vs)), 4) if vs else None,
        "max_v": round(float(np.max(vs)), 4) if vs else None,
        "n_significant": n_sig,
        "n_total": len(valid),
    }


# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------

def main(n_vars: int = 3, max_workers: int = 8) -> None:
    t0 = time.time()
    print("=" * 60)
    print("Cross-Domain Bivariate Sweep")
    print("=" * 60)

    # Load data
    print("\nLoading survey data...")
    enc_dict, enc_nom_dict_rev, rev_topic_dict, pregs_dict = load_data()

    # Viable domains
    all_domains = sorted(rev_topic_dict.keys())
    viable = [d for d in all_domains if d not in EXCLUDE_DOMAINS]
    print(f"Viable domains: {len(viable)} (excluded: {EXCLUDE_DOMAINS})")

    # Select representative variables per domain
    print(f"\nSelecting {n_vars} representative variables per domain (top entropy)...")
    selected_vars: Dict[str, List[str]] = {}
    for domain in viable:
        selected = select_representative_vars(
            domain, pregs_dict, enc_dict, enc_nom_dict_rev, n_vars
        )
        selected_vars[domain] = selected
        print(f"  {domain}: {selected}")

    # Enumerate all pairs
    all_pairs = list(combinations(viable, 2))
    n_estimates_expected = len(all_pairs) * n_vars * n_vars
    print(f"\nDomain pairs: {len(all_pairs)}")
    print(f"Expected estimates: {n_estimates_expected}")
    print(f"Workers: {max_workers}", flush=True)

    # Parallel sweep
    print(f"\nRunning sweep...", flush=True)
    results: Dict[str, Dict[str, Any]] = {}
    n_done = 0

    def _run_pair(pair):
        da, db = pair
        return pair, estimate_domain_pair(
            da, db, selected_vars[da], selected_vars[db],
            enc_dict, enc_nom_dict_rev,
        )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_pair, p): p for p in all_pairs}
        for future in as_completed(futures):
            pair = futures[future]
            try:
                (da, db), result = future.result()
                key = f"{da}::{db}"
                results[key] = result
                n_done += 1
                v_str = f"V={result['mean_v']:.3f}" if result['mean_v'] is not None else "FAIL"
                if n_done % 10 == 0 or n_done == len(all_pairs):
                    elapsed = time.time() - t0
                    print(f"  [{n_done}/{len(all_pairs)}] {elapsed:.0f}s — last: {key} {v_str}",
                          flush=True)
            except Exception as e:
                da, db = pair
                key = f"{da}::{db}"
                results[key] = {
                    "domain_a": da, "domain_b": db,
                    "estimates": [], "mean_v": None, "max_v": None,
                    "n_significant": 0, "n_total": 0, "error": str(e),
                }
                n_done += 1

    elapsed = time.time() - t0

    # Compile output
    n_successful = sum(1 for r in results.values() if r["mean_v"] is not None)
    total_estimates = sum(r["n_total"] for r in results.values())
    total_significant = sum(r["n_significant"] for r in results.values())

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "n_domains": len(viable),
            "n_pairs_attempted": len(all_pairs),
            "n_pairs_with_results": n_successful,
            "n_estimates_total": total_estimates,
            "n_estimates_significant": total_significant,
            "vars_per_domain": n_vars,
            "selection_method": "top_entropy",
            "elapsed_seconds": round(elapsed, 1),
        },
        "domain_pairs": results,
        "selected_variables": selected_vars,
    }

    # Save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n{'=' * 60}")
    print(f"SWEEP COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Time:              {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Domain pairs:      {n_successful}/{len(all_pairs)} with results")
    print(f"  Estimates:         {total_estimates} successful")
    print(f"  Significant:       {total_significant} (p<0.05)")
    print(f"  Output:            {OUTPUT_PATH}")

    # Top 15 strongest pairs
    ranked = sorted(
        [(k, r) for k, r in results.items() if r["mean_v"] is not None],
        key=lambda x: -x[1]["mean_v"]
    )
    print(f"\n  Top 15 strongest domain pairs:")
    for k, r in ranked[:15]:
        sig = f"{r['n_significant']}/{r['n_total']}" if r['n_total'] else "—"
        print(f"    {k:<12} mean_V={r['mean_v']:.3f}  max_V={r['max_v']:.3f}  sig={sig}")

    # Weakest 5
    print(f"\n  Bottom 5 weakest domain pairs:")
    for k, r in ranked[-5:]:
        print(f"    {k:<12} mean_V={r['mean_v']:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full cross-domain bivariate sweep")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers (default: 8)")
    parser.add_argument("--vars-per-domain", type=int, default=3, help="Vars per domain (default: 3)")
    args = parser.parse_args()
    main(n_vars=args.vars_per_domain, max_workers=args.workers)
