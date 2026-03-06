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

OUTPUT_PATH = ROOT / "data" / "results" / "cross_domain_sweep.json"

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



# Maximum number of unique response categories for a variable to be considered
# ordinal/categorical and therefore suitable for OrderedModel / MNLogit.
# Variables with more unique values are open-ended text fields (e.g. "what word
# comes to mind?") or continuous numeric fields (e.g. income in pesos, housing
# area in m²) — neither can be meaningfully modelled by the SES bridge regression.
MAX_ORDINAL_CATEGORIES = 15


def select_representative_vars(
    domain: str,
    pregs_dict: dict,
    enc_dict: dict,
    enc_nom_dict_rev: dict,
    n_vars: int = 3,
) -> List[str]:
    """
    Select the top-N highest-entropy *categorical/ordinal* variables for a domain.

    Only variables with at most MAX_ORDINAL_CATEGORIES unique non-NaN values are
    eligible.  Open-ended text fields and continuous numeric fields (income, area,
    counts) are excluded because:
      - Shannon entropy is maximised by text/continuous fields, which would
        otherwise always be selected.
      - OrderedModel / MNLogit requires categorical / ordinal targets with a
        small, finite number of levels.

    Falls back to evenly spaced variables if too few categorical vars are found.
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

    # Compute entropy per variable, skipping continuous / open-text ones
    scored: List[Tuple[str, float]] = []
    for qid in domain_vars:
        col = qid.split("|")[0]
        if col in df.columns:
            series = df[col].dropna()
            # Exclude open-ended text / continuous numeric variables
            if series.nunique() > MAX_ORDINAL_CATEGORIES:
                continue
            try:
                h = _shannon_entropy(series)
                scored.append((qid, h))
            except Exception:
                pass

    if len(scored) < n_vars:
        # Fallback: evenly spaced from the categorical-eligible list
        eligible = [
            qid for qid in domain_vars
            if qid.split("|")[0] in df.columns
            and df[qid.split("|")[0]].dropna().nunique() <= MAX_ORDINAL_CATEGORIES
        ]
        if not eligible:
            # Last resort: use domain_vars without filtering
            eligible = domain_vars
        step = max(1, len(eligible) // n_vars)
        return [eligible[i * step] for i in range(min(n_vars, len(eligible)))]

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

def main(
    n_vars: int = 3,
    max_workers: int = 8,
    output_path: Path = OUTPUT_PATH,
    var_selection: str = "naive",
    semantic_selection_file: Optional[Path] = None,
) -> None:
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
    selected_vars: Dict[str, List[str]] = {}
    if var_selection == "semantic" and semantic_selection_file is not None:
        print(f"\nLoading semantic variable selection from {semantic_selection_file}...")
        sys.path.insert(0, str(ROOT / "scripts" / "debug"))
        from select_bridge_variables_semantic import SemanticVariableSelector
        loaded = SemanticVariableSelector.load(semantic_selection_file)
        # Build aggregated columns in enc_dict DataFrames
        SemanticVariableSelector.build_aggregates(
            enc_dict, enc_nom_dict_rev,
            selection_path=semantic_selection_file,
        )
        for domain in viable:
            if domain in loaded:
                selected_vars[domain] = loaded[domain]
                print(f"  {domain}: {loaded[domain]}")
            else:
                # Fallback for missing domains
                selected_vars[domain] = select_representative_vars(
                    domain, pregs_dict, enc_dict, enc_nom_dict_rev, n_vars
                )
                print(f"  {domain}: {selected_vars[domain]}  [fallback to entropy]")
    else:
        print(f"\nSelecting {n_vars} representative variables per domain (top entropy)...")
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
            "selection_method": var_selection,
            "elapsed_seconds": round(elapsed, 1),
        },
        "domain_pairs": results,
        "selected_variables": selected_vars,
    }

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n{'=' * 60}")
    print(f"SWEEP COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Time:              {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Domain pairs:      {n_successful}/{len(all_pairs)} with results")
    print(f"  Estimates:         {total_estimates} successful")
    print(f"  Significant:       {total_significant} (p<0.05)")
    print(f"  Output:            {output_path}")

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
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help="Output JSON path (default: data/results/cross_domain_sweep.json)")
    parser.add_argument("--var-selection", choices=["naive", "semantic"], default="naive",
                        help="Variable selection method: naive (max entropy) or semantic (LLM pipeline)")
    parser.add_argument("--semantic-selection-file", type=Path,
                        default=ROOT / "data" / "results" / "semantic_variable_selection.json",
                        help="Path to semantic_variable_selection.json (used when --var-selection=semantic)")
    args = parser.parse_args()
    main(
        n_vars=args.vars_per_domain,
        max_workers=args.workers,
        output_path=args.output,
        var_selection=args.var_selection,
        semantic_selection_file=args.semantic_selection_file if args.var_selection == "semantic" else None,
    )
