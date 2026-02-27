"""
sweep_bridge_comparison.py — Compare three bridge estimators across all 276 domain pairs.

Runs CrossDatasetBivariateEstimator (baseline), ResidualBridgeEstimator (Option C),
and EcologicalBridgeEstimator (Option D) on the same variable pairs selected by the
existing cross-domain sweep.

Results are saved incrementally after each domain pair (crash-safe).  Run via nohup:

    nohup python scripts/debug/sweep_bridge_comparison.py \\
        --workers 1 > /tmp/bridge_comparison.log 2>&1 &
    tail -f /tmp/bridge_comparison.log

Output:
    data/results/bridge_comparison_results.json   — per-pair estimates for all 3 methods
    data/results/bridge_comparison_report.md      — human-readable comparison table
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*convergence.*")
warnings.filterwarnings("ignore", message=".*Maximum Likelihood.*")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BASELINE_SWEEP = ROOT / "data" / "results" / "cross_domain_sweep.json"
OUTPUT_JSON = ROOT / "data" / "results" / "bridge_comparison_results.json"
OUTPUT_REPORT = ROOT / "data" / "results" / "bridge_comparison_report.md"

# Default ecological cell_cols: demographic cells are denser than geographic ones.
# escol(1-5) × edad(7 groups) = 35 cells, ~57 rows/cell at n_sim=2000.
DEFAULT_ECO_CELL_COLS = ["escol", "edad"]

# n_sim for baseline and residual bridges (lower than 2000 default for speed)
N_SIM = 500


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> Tuple[dict, dict]:
    """Load survey data and SES-preprocess.  Returns (enc_dict, enc_nom_dict_rev)."""
    from dataset_knowledge import (
        los_mex_dict, enc_nom_dict, DATA_AVAILABLE,
    )
    if not DATA_AVAILABLE:
        print("ERROR: Survey data not available.", file=sys.stderr)
        sys.exit(1)

    from ses_analysis import AnalysisConfig
    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get("enc_dict", los_mex_dict.get("enc_dict", {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}
    return enc_dict, enc_nom_dict_rev


# ---------------------------------------------------------------------------
# Single domain-pair estimation (all 3 methods)
# ---------------------------------------------------------------------------

def estimate_pair_all_methods(
    domain_a: str,
    domain_b: str,
    vars_a: List[str],
    vars_b: List[str],
    enc_dict: dict,
    enc_nom_dict_rev: dict,
    eco_cell_cols: List[str],
) -> Dict[str, Any]:
    """
    Run all 3 bridge methods on every (var_a, var_b) cross-combination.

    Returns a result dict with top-level aggregates for each method and the
    full per-variable-pair estimates list.
    """
    from ses_regression import (
        CrossDatasetBivariateEstimator,
        ResidualBridgeEstimator,
        EcologicalBridgeEstimator,
    )

    survey_a = enc_nom_dict_rev.get(domain_a)
    survey_b = enc_nom_dict_rev.get(domain_b)
    df_a = enc_dict.get(survey_a, {}).get("dataframe") if survey_a else None
    df_b = enc_dict.get(survey_b, {}).get("dataframe") if survey_b else None

    if not isinstance(df_a, pd.DataFrame) or not isinstance(df_b, pd.DataFrame):
        return {
            "domain_a": domain_a, "domain_b": domain_b,
            "estimates": [],
            "baseline_mean_v": None, "residual_mean_v": None,
            "eco_mean_rho": None, "mean_ses_fraction": None,
            "n_total": 0, "error": "DataFrame not found",
        }

    est_baseline = CrossDatasetBivariateEstimator(n_sim=N_SIM)
    est_residual = ResidualBridgeEstimator(n_sim=N_SIM, n_cells=20)
    est_eco = EcologicalBridgeEstimator(min_cell_n=10, min_merged_cells=5, n_bootstrap=200)

    estimates: List[Dict[str, Any]] = []

    for va in vars_a:
        col_a = va.split("|")[0]
        if col_a not in df_a.columns:
            continue
        for vb in vars_b:
            col_b = vb.split("|")[0]
            if col_b not in df_b.columns:
                continue

            row: Dict[str, Any] = {"var_a": va, "var_b": vb}

            # --- Baseline ---
            try:
                r = est_baseline.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b,
                )
                if r:
                    row["baseline_v"] = round(r["cramers_v"], 4)
                    row["baseline_p"] = round(r["p_value"], 6)
            except Exception as e:
                row["baseline_error"] = str(e)

            # --- Residual (Option C) ---
            try:
                r = est_residual.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b,
                )
                if r:
                    row["residual_v"] = round(r["cramers_v_residual"], 4)
                    row["ses_fraction"] = round(r["ses_fraction"], 4) if r["ses_fraction"] is not None else None
                    row["n_cells_used"] = r["n_cells_used"]
            except Exception as e:
                row["residual_error"] = str(e)

            # --- Ecological (Option D) ---
            try:
                r = est_eco.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b,
                    cell_cols=eco_cell_cols,
                )
                if r:
                    row["eco_rho"] = round(r["spearman_rho"], 4)
                    row["eco_p"] = round(r["p_value"], 6)
                    ci = r.get("ci_95")
                    row["eco_ci"] = [round(ci[0], 4), round(ci[1], 4)] if ci else None
                    row["eco_n_cells"] = r["n_cells"]
                    row["eco_cell_cols"] = r.get("cell_cols_used", eco_cell_cols)
            except Exception as e:
                row["eco_error"] = str(e)

            estimates.append(row)

    # Aggregate
    baseline_vs = [e["baseline_v"] for e in estimates if "baseline_v" in e]
    residual_vs = [e["residual_v"] for e in estimates if "residual_v" in e]
    eco_rhos = [e["eco_rho"] for e in estimates if "eco_rho" in e]
    ses_fracs = [e["ses_fraction"] for e in estimates
                 if e.get("ses_fraction") is not None]

    def _safe_mean(lst):
        return round(float(np.mean(lst)), 4) if lst else None

    return {
        "domain_a": domain_a,
        "domain_b": domain_b,
        "estimates": estimates,
        "baseline_mean_v": _safe_mean(baseline_vs),
        "residual_mean_v": _safe_mean(residual_vs),
        "eco_mean_rho": _safe_mean(eco_rhos),
        "mean_ses_fraction": _safe_mean(ses_fracs),
        "n_total": len(estimates),
        "n_baseline_ok": len(baseline_vs),
        "n_residual_ok": len(residual_vs),
        "n_eco_ok": len(eco_rhos),
    }


# ---------------------------------------------------------------------------
# Incremental save
# ---------------------------------------------------------------------------

def _save_checkpoint(
    results: Dict[str, Any],
    output_path: Path,
    metadata: dict,
) -> None:
    """Atomically write current results to JSON (overwrite)."""
    output: Dict[str, Any] = {
        "metadata": {**metadata, "timestamp": datetime.now().isoformat()},
        "domain_pairs": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    tmp.replace(output_path)


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def generate_report(results: Dict[str, Any], output_path: Path, meta: dict) -> None:
    """Write a human-readable comparison markdown report."""
    pairs = list(results.values())
    valid = [p for p in pairs if p.get("baseline_mean_v") is not None]
    valid.sort(key=lambda p: -(p["baseline_mean_v"] or 0))

    lines: List[str] = [
        "# Bridge Comparison Report",
        "",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Run Parameters",
        "",
        f"- `n_sim` (baseline + residual): {meta.get('n_sim', N_SIM)}",
        f"- `n_cells` (residual): {meta.get('n_cells', 20)}",
        f"- Ecological `cell_cols`: {meta.get('eco_cell_cols', DEFAULT_ECO_CELL_COLS)}",
        f"- Domain pairs attempted: {meta.get('n_pairs_attempted', len(results))}",
        f"- Domain pairs with results: {len(valid)}",
        f"- Elapsed: {meta.get('elapsed_seconds', '?'):.0f}s",
        "",
        "## Summary Statistics",
        "",
    ]

    def _stats(vals):
        if not vals:
            return "n/a"
        return f"mean={np.mean(vals):.3f}  IQR=[{np.percentile(vals,25):.3f}, {np.percentile(vals,75):.3f}]  range=[{min(vals):.3f}, {max(vals):.3f}]"

    bvs = [p["baseline_mean_v"] for p in valid if p["baseline_mean_v"] is not None]
    rvs = [p["residual_mean_v"] for p in valid if p.get("residual_mean_v") is not None]
    evs = [p["eco_mean_rho"] for p in valid if p.get("eco_mean_rho") is not None]
    sfs = [p["mean_ses_fraction"] for p in valid if p.get("mean_ses_fraction") is not None]

    lines += [
        f"| Method | N pairs | {_stats(bvs)} |",
        "|--------|---------|" + "-" * 55 + "|",
    ]
    # table proper
    lines = lines[:-2]  # remove malformed header attempt
    lines += [
        "| Method | N pairs | Mean | IQR (25–75) | Range |",
        "|--------|---------|------|-------------|-------|",
    ]

    def _row(name, vals):
        if not vals:
            return f"| {name} | 0 | — | — | — |"
        q25, q75 = np.percentile(vals, [25, 75])
        return (f"| {name} | {len(vals)} | {np.mean(vals):.3f} "
                f"| [{q25:.3f}, {q75:.3f}] | [{min(vals):.3f}, {max(vals):.3f}] |")

    lines += [
        _row("Baseline V", bvs),
        _row("Residual V (Option C)", rvs),
        _row("|Eco ρ| (Option D)", [abs(v) for v in evs]),
        _row("SES fraction (resid/base)", sfs),
        "",
    ]

    # Top 20 pairs by baseline V
    lines += [
        "## Top 20 Domain Pairs by Baseline V",
        "",
        "| Domain pair | Base V | Resid V | SES frac | Eco ρ | Interpretation |",
        "|-------------|--------|---------|----------|-------|----------------|",
    ]
    for p in valid[:20]:
        key = f"{p['domain_a']}×{p['domain_b']}"
        bv = f"{p['baseline_mean_v']:.3f}" if p.get("baseline_mean_v") is not None else "—"
        rv = f"{p['residual_mean_v']:.3f}" if p.get("residual_mean_v") is not None else "—"
        sf = f"{p['mean_ses_fraction']:.2f}" if p.get("mean_ses_fraction") is not None else "—"
        er = f"{p['eco_mean_rho']:.3f}" if p.get("eco_mean_rho") is not None else "—"

        # Simple 3-way interpretation
        bv_f = p.get("baseline_mean_v") or 0
        rv_f = p.get("residual_mean_v") or 0
        er_f = abs(p.get("eco_mean_rho") or 0)
        hi_b = bv_f > 0.08
        hi_r = rv_f > 0.04
        hi_e = er_f > 0.15
        if hi_b and hi_r and hi_e:
            interp = "demographic + geographic + conceptual"
        elif hi_b and hi_r and not hi_e:
            interp = "demographic + conceptual; geog. uniform"
        elif hi_b and not hi_r and hi_e:
            interp = "SES-mediated + geographic"
        elif hi_b and not hi_r and not hi_e:
            interp = "pure SES confounding"
        elif not hi_b and hi_e:
            interp = "geographic, not captured by demographics"
        else:
            interp = "weak / independent"
        lines.append(f"| {key} | {bv} | {rv} | {sf} | {er} | {interp} |")

    lines += [
        "",
        "## Weakest 10 Domain Pairs (Baseline V)",
        "",
        "| Domain pair | Base V | Resid V | Eco ρ |",
        "|-------------|--------|---------|-------|",
    ]
    for p in valid[-10:]:
        key = f"{p['domain_a']}×{p['domain_b']}"
        bv = f"{p['baseline_mean_v']:.3f}" if p.get("baseline_mean_v") is not None else "—"
        rv = f"{p['residual_mean_v']:.3f}" if p.get("residual_mean_v") is not None else "—"
        er = f"{p['eco_mean_rho']:.3f}" if p.get("eco_mean_rho") is not None else "—"
        lines.append(f"| {key} | {bv} | {rv} | {er} |")

    lines += [
        "",
        "## Interpretation Matrix",
        "",
        "| V_baseline | V_residual | |Eco ρ| | Interpretation |",
        "|-----------|-----------|--------|----------------|",
        "| High | High | High | Strong: demographic + geographic + conceptual |",
        "| High | High | Low  | Demographic + conceptual; geographically uniform |",
        "| High | Low  | High | Geographically real but SES-mediated |",
        "| High | Low  | Low  | Pure SES confounding |",
        "| Low  | Low  | High | Geographic pattern not explained by demographics |",
        "| Low  | Low  | Low  | Genuinely independent domains |",
        "",
        "---",
        f"*Full results: `{OUTPUT_JSON}`*",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Report saved → {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(
    max_workers: int = 1,
    eco_cell_cols: List[str] = None,
    output_json: Path = OUTPUT_JSON,
    output_report: Path = OUTPUT_REPORT,
    resume: bool = True,
) -> None:
    if eco_cell_cols is None:
        eco_cell_cols = DEFAULT_ECO_CELL_COLS

    t0 = time.time()
    print("=" * 60)
    print("Bridge Comparison Sweep  (baseline + residual + ecological)")
    print("=" * 60)
    print(f"n_sim={N_SIM}, eco_cell_cols={eco_cell_cols}, workers={max_workers}")
    print()

    # Load survey data
    print("Loading survey data...")
    enc_dict, enc_nom_dict_rev = load_data()

    # Load selected variables from existing baseline sweep
    if not BASELINE_SWEEP.exists():
        print(f"ERROR: baseline sweep not found at {BASELINE_SWEEP}", file=sys.stderr)
        print("Run scripts/debug/sweep_cross_domain.py first.", file=sys.stderr)
        sys.exit(1)

    with open(BASELINE_SWEEP, encoding="utf-8") as f:
        baseline_data = json.load(f)

    selected_vars: Dict[str, List[str]] = baseline_data["selected_variables"]
    all_pair_keys = list(baseline_data["domain_pairs"].keys())
    print(f"Loaded {len(all_pair_keys)} domain pairs from baseline sweep.")
    print(f"Variable selection: {baseline_data['metadata'].get('vars_per_domain', '?')} vars/domain")

    # Resume: skip already-computed pairs
    existing_results: Dict[str, Any] = {}
    if resume and output_json.exists():
        try:
            with open(output_json, encoding="utf-8") as f:
                prev = json.load(f)
            existing_results = prev.get("domain_pairs", {})
            n_existing = sum(1 for v in existing_results.values()
                             if v.get("baseline_mean_v") is not None)
            print(f"Resuming: {n_existing} pairs already computed.")
        except Exception as e:
            print(f"Warning: could not load checkpoint ({e}); starting fresh.")

    pairs_todo = [
        k for k in all_pair_keys
        if k not in existing_results or existing_results[k].get("baseline_mean_v") is None
    ]
    print(f"Pairs remaining: {len(pairs_todo)} / {len(all_pair_keys)}", flush=True)

    results: Dict[str, Any] = dict(existing_results)

    meta = {
        "n_sim": N_SIM,
        "n_cells": 20,
        "eco_cell_cols": eco_cell_cols,
        "n_pairs_attempted": len(all_pair_keys),
        "workers": max_workers,
        "baseline_sweep": str(BASELINE_SWEEP),
    }

    n_done = 0
    checkpoint_every = 10  # save after every N completed pairs

    def _run_pair(pair_key: str):
        da, db = pair_key.split("::")
        vars_a = selected_vars.get(da, [])
        vars_b = selected_vars.get(db, [])
        return pair_key, estimate_pair_all_methods(
            da, db, vars_a, vars_b, enc_dict, enc_nom_dict_rev, eco_cell_cols
        )

    print(f"\nRunning sweep (workers={max_workers})...\n", flush=True)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_pair, k): k for k in pairs_todo}
        for future in as_completed(futures):
            pair_key = futures[future]
            try:
                key, result = future.result()
                results[key] = result
                n_done += 1
                elapsed = time.time() - t0

                bv = result.get("baseline_mean_v")
                rv = result.get("residual_mean_v")
                er = result.get("eco_mean_rho")
                bv_s = f"{bv:.3f}" if bv is not None else "FAIL"
                rv_s = f"{rv:.3f}" if rv is not None else "FAIL"
                er_s = f"{er:.3f}" if er is not None else "n/a"
                print(
                    f"  [{n_done + len(existing_results) - (len(all_pair_keys) - len(pairs_todo))}"
                    f"/{len(all_pair_keys)}] {elapsed:.0f}s | {key}"
                    f" | base={bv_s} resid={rv_s} eco={er_s}",
                    flush=True,
                )

                if n_done % checkpoint_every == 0:
                    meta["elapsed_seconds"] = round(time.time() - t0, 1)
                    _save_checkpoint(results, output_json, meta)

            except Exception as e:
                da, db = pair_key.split("::")
                results[pair_key] = {
                    "domain_a": da, "domain_b": db,
                    "estimates": [], "error": str(e),
                    "baseline_mean_v": None, "residual_mean_v": None,
                    "eco_mean_rho": None,
                }
                n_done += 1

    elapsed = time.time() - t0
    meta["elapsed_seconds"] = round(elapsed, 1)

    # Final save
    _save_checkpoint(results, output_json, meta)

    # Summary stats
    all_pairs = list(results.values())
    n_ok = sum(1 for p in all_pairs if p.get("baseline_mean_v") is not None)
    n_residual_ok = sum(1 for p in all_pairs if p.get("residual_mean_v") is not None)
    n_eco_ok = sum(1 for p in all_pairs if p.get("eco_mean_rho") is not None)

    bvs = [p["baseline_mean_v"] for p in all_pairs if p.get("baseline_mean_v") is not None]
    rvs = [p["residual_mean_v"] for p in all_pairs if p.get("residual_mean_v") is not None]
    evs = [p["eco_mean_rho"] for p in all_pairs if p.get("eco_mean_rho") is not None]

    print()
    print("=" * 60)
    print("SWEEP COMPLETE")
    print("=" * 60)
    print(f"  Elapsed:       {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Pairs total:   {len(all_pairs)} / baseline ok: {n_ok} / residual ok: {n_residual_ok} / eco ok: {n_eco_ok}")
    if bvs:
        print(f"  Baseline V:    mean={np.mean(bvs):.3f}  IQR=[{np.percentile(bvs,25):.3f}, {np.percentile(bvs,75):.3f}]")
    if rvs:
        print(f"  Residual V:    mean={np.mean(rvs):.3f}  IQR=[{np.percentile(rvs,25):.3f}, {np.percentile(rvs,75):.3f}]")
    if evs:
        print(f"  Eco |ρ|:       mean={np.mean([abs(v) for v in evs]):.3f}  IQR=[{np.percentile([abs(v) for v in evs],25):.3f}, {np.percentile([abs(v) for v in evs],75):.3f}]")

    # Top 10 pairs
    ranked = sorted(
        [(k, v) for k, v in results.items() if v.get("baseline_mean_v") is not None],
        key=lambda x: -(x[1]["baseline_mean_v"] or 0),
    )
    print("\n  Top 10 pairs by baseline V:")
    print(f"  {'Pair':<15} {'Base':>6} {'Resid':>6} {'SES%':>6} {'Eco ρ':>7}")
    print("  " + "-" * 46)
    for key, r in ranked[:10]:
        bv = r.get("baseline_mean_v") or 0
        rv = r.get("residual_mean_v")
        sf = r.get("mean_ses_fraction")
        er = r.get("eco_mean_rho")
        rv_s = f"{rv:.3f}" if rv is not None else "  —  "
        sf_s = f"{sf:.2f}" if sf is not None else "  —  "
        er_s = f"{er:+.3f}" if er is not None else "  —  "
        print(f"  {key:<15} {bv:>6.3f} {rv_s:>6} {sf_s:>6} {er_s:>7}")

    # Generate markdown report
    meta["elapsed_seconds"] = round(elapsed, 1)
    generate_report(results, output_report, meta)
    print(f"\n  JSON:   {output_json}")
    print(f"  Report: {output_report}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Comparison sweep: baseline + residual + ecological bridge"
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Parallel workers (default: 1; use 1 on 2-core VMs)"
    )
    parser.add_argument(
        "--eco-cell-cols", nargs="+", default=DEFAULT_ECO_CELL_COLS,
        metavar="COL",
        help=(
            f"Columns for ecological cell key (default: {DEFAULT_ECO_CELL_COLS}). "
            "Any column present in both surveys is valid, e.g.: --eco-cell-cols edo Tam_loc"
        ),
    )
    parser.add_argument(
        "--output-json", type=Path, default=OUTPUT_JSON,
        help="Output JSON path"
    )
    parser.add_argument(
        "--output-report", type=Path, default=OUTPUT_REPORT,
        help="Output markdown report path"
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Ignore existing checkpoint and rerun from scratch"
    )
    args = parser.parse_args()

    main(
        max_workers=args.workers,
        eco_cell_cols=args.eco_cell_cols,
        output_json=args.output_json,
        output_report=args.output_report,
        resume=not args.no_resume,
    )
