"""
sweep_bridge_comparison.py — Compare all six bridge estimators across 276 domain pairs.

Estimators:
  Baseline   — CrossDatasetBivariateEstimator  (Cramér's V via SES simulation)
  Residual   — ResidualBridgeEstimator          (within-cell Mantel-Haenszel V)
  Ecological — EcologicalBridgeEstimator        (geographic cell Spearman ρ)
  Bayesian   — BayesianBridgeEstimator          (Laplace posterior γ + V with CI)
  MRP        — MRPBridgeEstimator               (cell shrinkage + poststratification γ)
  DR         — DoublyRobustBridgeEstimator      (AIPW-corrected γ + KS overlap)

Results are saved incrementally after each domain pair (crash-safe).

Usage:
    # 1-worker run (~30 min with n_bootstrap=50 for DR):
    nohup python scripts/debug/sweep_bridge_comparison.py \\
        --workers 1 > /tmp/bridge_comparison.log 2>&1 &
    tail -f /tmp/bridge_comparison.log

    # Faster on a machine with 4+ cores:
    nohup python scripts/debug/sweep_bridge_comparison.py \\
        --workers 4 > /tmp/bridge_comparison.log 2>&1 &

Output:
    data/results/bridge_comparison_results.json   — per-pair estimates (all 6 methods)
    data/results/bridge_comparison_report.md      — human-readable comparison table
"""

from __future__ import annotations

import argparse
import json
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

# Ecological cell_cols: escol(1-5) × edad(7 groups) = 35 demographic cells
DEFAULT_ECO_CELL_COLS = ["escol", "edad"]

# MRP cell_cols: same as eco by default
DEFAULT_MRP_CELL_COLS = ["escol", "edad", "sexo"]

# Simulation size for baseline + residual
N_SIM = 500

# Bootstrap draws — DR is expensive (model refits); keep low for sweep speed.
# Full-precision runs can be done on individual pairs.
N_BOOTSTRAP_ECO = 200
N_BOOTSTRAP_BAY = 200   # posterior draws (cheap: no model refit)
N_BOOTSTRAP_MRP = 100
N_BOOTSTRAP_DR  = 50    # expensive: 50 × 2 model refits per pair


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data() -> Tuple[dict, dict]:
    """Load survey data and SES-preprocess. Returns (enc_dict, enc_nom_dict_rev)."""
    from dataset_knowledge import los_mex_dict, enc_nom_dict, DATA_AVAILABLE
    if not DATA_AVAILABLE:
        print("ERROR: Survey data not available.", file=sys.stderr)
        sys.exit(1)

    from ses_analysis import AnalysisConfig
    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get("enc_dict", los_mex_dict.get("enc_dict", {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}
    return enc_dict, enc_nom_dict_rev


# ---------------------------------------------------------------------------
# Single domain-pair estimation (all 6 methods)
# ---------------------------------------------------------------------------

def estimate_pair_all_methods(
    domain_a: str,
    domain_b: str,
    vars_a: List[str],
    vars_b: List[str],
    enc_dict: dict,
    enc_nom_dict_rev: dict,
    eco_cell_cols: List[str],
    mrp_cell_cols: List[str],
) -> Dict[str, Any]:
    """
    Run all 6 bridge methods on every (var_a, var_b) cross-combination.

    Returns a result dict with top-level aggregates for each method and the
    full per-variable-pair estimates list.
    """
    from ses_regression import (
        CrossDatasetBivariateEstimator,
        ResidualBridgeEstimator,
        EcologicalBridgeEstimator,
        BayesianBridgeEstimator,
        MRPBridgeEstimator,
        DoublyRobustBridgeEstimator,
    )

    survey_a = enc_nom_dict_rev.get(domain_a)
    survey_b = enc_nom_dict_rev.get(domain_b)
    df_a = enc_dict.get(survey_a, {}).get("dataframe") if survey_a else None
    df_b = enc_dict.get(survey_b, {}).get("dataframe") if survey_b else None

    if not isinstance(df_a, pd.DataFrame) or not isinstance(df_b, pd.DataFrame):
        return {
            "domain_a": domain_a, "domain_b": domain_b,
            "estimates": [], "n_total": 0,
            "error": "DataFrame not found",
            **{k: None for k in _AGG_KEYS},
        }

    est_baseline  = CrossDatasetBivariateEstimator(n_sim=N_SIM)
    est_residual  = ResidualBridgeEstimator(n_sim=N_SIM, n_cells=20)
    est_eco       = EcologicalBridgeEstimator(
        min_cell_n=10, min_merged_cells=5, n_bootstrap=N_BOOTSTRAP_ECO)
    est_bayesian  = BayesianBridgeEstimator(n_sim=N_SIM, n_draws=N_BOOTSTRAP_BAY)
    est_mrp       = MRPBridgeEstimator(
        cell_cols=mrp_cell_cols, min_cell_n=5, n_bootstrap=N_BOOTSTRAP_MRP)
    est_dr        = DoublyRobustBridgeEstimator(n_sim=N_SIM, n_bootstrap=N_BOOTSTRAP_DR)

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
                    col_a=col_a, col_b=col_b)
                if r:
                    row["baseline_v"] = round(r["cramers_v"], 4)
                    row["baseline_p"] = round(r["p_value"], 6)
            except Exception as e:
                row["baseline_error"] = str(e)

            # --- Residual ---
            try:
                r = est_residual.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b)
                if r:
                    row["residual_v"] = round(r["cramers_v_residual"], 4)
                    row["ses_fraction"] = (
                        round(r["ses_fraction"], 4)
                        if r["ses_fraction"] is not None else None
                    )
                    row["n_cells_used"] = r["n_cells_used"]
            except Exception as e:
                row["residual_error"] = str(e)

            # --- Ecological ---
            try:
                r = est_eco.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b, cell_cols=eco_cell_cols)
                if r:
                    row["eco_rho"]      = round(r["spearman_rho"], 4)
                    row["eco_p"]        = round(r["p_value"], 6)
                    ci = r.get("ci_95")
                    row["eco_ci"]       = [round(ci[0], 4), round(ci[1], 4)] if ci else None
                    row["eco_n_cells"]  = r["n_cells"]
            except Exception as e:
                row["eco_error"] = str(e)

            # --- Bayesian ---
            try:
                r = est_bayesian.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b)
                if r:
                    row["bay_gamma"]    = round(r["gamma"], 4)
                    row["bay_gamma_ci"] = r["gamma_ci_95"]
                    row["bay_v"]        = round(r["cramers_v"], 4)
                    row["bay_v_ci"]     = r["cramers_v_ci_95"]
                    row["bay_r2_a"]     = round(r["pseudo_r2_a"] or 0, 4)
                    row["bay_r2_b"]     = round(r["pseudo_r2_b"] or 0, 4)
            except Exception as e:
                row["bay_error"] = str(e)

            # --- MRP ---
            try:
                r = est_mrp.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b)
                if r:
                    row["mrp_gamma"]    = round(r["gamma"], 4)
                    row["mrp_gamma_ci"] = r["gamma_ci_95"]
                    row["mrp_v"]        = round(r["cramers_v"], 4)
                    row["mrp_cells"]    = r["n_cells_used"]
            except Exception as e:
                row["mrp_error"] = str(e)

            # --- Doubly Robust ---
            try:
                r = est_dr.estimate(
                    var_id_a=va, var_id_b=vb, df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b)
                if r:
                    row["dr_gamma"]     = round(r["gamma"], 4)
                    row["dr_gamma_ci"]  = r["gamma_ci_95"]
                    row["dr_v"]         = round(r["cramers_v"], 4)
                    row["dr_ks"]        = round(r["propensity_overlap"], 4)
            except Exception as e:
                row["dr_error"] = str(e)

            estimates.append(row)

    # --- Aggregate per-domain-pair ---
    def _mean(lst):
        return round(float(np.mean(lst)), 4) if lst else None

    def _extract(key):
        return [e[key] for e in estimates if key in e and e[key] is not None]

    return {
        "domain_a": domain_a,
        "domain_b": domain_b,
        "estimates": estimates,
        "n_total": len(estimates),
        "n_baseline_ok":  len(_extract("baseline_v")),
        "n_residual_ok":  len(_extract("residual_v")),
        "n_eco_ok":       len(_extract("eco_rho")),
        "n_bayesian_ok":  len(_extract("bay_gamma")),
        "n_mrp_ok":       len(_extract("mrp_gamma")),
        "n_dr_ok":        len(_extract("dr_gamma")),
        # Aggregates
        "baseline_mean_v":   _mean(_extract("baseline_v")),
        "residual_mean_v":   _mean(_extract("residual_v")),
        "eco_mean_rho":      _mean(_extract("eco_rho")),
        "mean_ses_fraction": _mean([e["ses_fraction"] for e in estimates
                                    if e.get("ses_fraction") is not None]),
        "bay_mean_gamma":    _mean(_extract("bay_gamma")),
        "bay_mean_v":        _mean(_extract("bay_v")),
        "mrp_mean_gamma":    _mean(_extract("mrp_gamma")),
        "mrp_mean_v":        _mean(_extract("mrp_v")),
        "dr_mean_gamma":     _mean(_extract("dr_gamma")),
        "dr_mean_v":         _mean(_extract("dr_v")),
        "dr_mean_ks":        _mean(_extract("dr_ks")),
    }


# Keys used for the "no-data" fallback
_AGG_KEYS = [
    "baseline_mean_v", "residual_mean_v", "eco_mean_rho", "mean_ses_fraction",
    "bay_mean_gamma", "bay_mean_v", "mrp_mean_gamma", "mrp_mean_v",
    "dr_mean_gamma", "dr_mean_v", "dr_mean_ks",
    "n_baseline_ok", "n_residual_ok", "n_eco_ok",
    "n_bayesian_ok", "n_mrp_ok", "n_dr_ok",
]


# ---------------------------------------------------------------------------
# Incremental checkpoint
# ---------------------------------------------------------------------------

def _save_checkpoint(results: Dict[str, Any], output_path: Path, metadata: dict) -> None:
    """Atomically write current results to JSON."""
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
    """Write a human-readable 6-method comparison markdown report."""
    pairs  = list(results.values())
    valid  = [p for p in pairs if p.get("baseline_mean_v") is not None]
    valid.sort(key=lambda p: -(p["baseline_mean_v"] or 0))

    def _stats(vals):
        if not vals:
            return "n/a"
        q25, q75 = np.percentile(vals, [25, 75])
        return (f"mean={np.mean(vals):.3f}  "
                f"IQR=[{q25:.3f}, {q75:.3f}]  "
                f"range=[{min(vals):.3f}, {max(vals):.3f}]")

    def _row(name, vals):
        if not vals:
            return f"| {name} | 0 | — | — | — |"
        q25, q75 = np.percentile(vals, [25, 75])
        return (f"| {name} | {len(vals)} | {np.mean(vals):.3f} "
                f"| [{q25:.3f}, {q75:.3f}] | [{min(vals):.3f}, {max(vals):.3f}] |")

    bvs  = [p["baseline_mean_v"]  for p in valid if p.get("baseline_mean_v") is not None]
    rvs  = [p["residual_mean_v"]  for p in valid if p.get("residual_mean_v") is not None]
    evs  = [p["eco_mean_rho"]     for p in valid if p.get("eco_mean_rho") is not None]
    bays = [p["bay_mean_gamma"]   for p in valid if p.get("bay_mean_gamma") is not None]
    mrps = [p["mrp_mean_gamma"]   for p in valid if p.get("mrp_mean_gamma") is not None]
    drs  = [p["dr_mean_gamma"]    for p in valid if p.get("dr_mean_gamma") is not None]
    dks  = [p["dr_mean_ks"]       for p in valid if p.get("dr_mean_ks") is not None]
    sfs  = [p["mean_ses_fraction"] for p in valid if p.get("mean_ses_fraction") is not None]

    lines: List[str] = [
        "# Bridge Comparison Report — All Six Methods",
        "",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Run Parameters",
        "",
        f"- `n_sim` (baseline / residual / bayesian): {meta.get('n_sim', N_SIM)}",
        f"- `n_bootstrap` eco / bayesian draws / mrp / DR: "
        f"{N_BOOTSTRAP_ECO} / {N_BOOTSTRAP_BAY} / {N_BOOTSTRAP_MRP} / {N_BOOTSTRAP_DR}",
        f"- `n_cells` (residual):      {meta.get('n_cells', 20)}",
        f"- Ecological `cell_cols`:    {meta.get('eco_cell_cols', DEFAULT_ECO_CELL_COLS)}",
        f"- MRP `cell_cols`:           {meta.get('mrp_cell_cols', DEFAULT_MRP_CELL_COLS)}",
        f"- Domain pairs attempted:    {meta.get('n_pairs_attempted', len(results))}",
        f"- Domain pairs with results: {len(valid)}",
        f"- Elapsed:                   {meta.get('elapsed_seconds', '?'):.0f}s",
        "",
        "## Summary Statistics",
        "",
        "| Method | N pairs | Mean | IQR (25–75) | Range |",
        "|--------|---------|------|-------------|-------|",
        _row("Baseline V (sim)",           bvs),
        _row("Residual V (within-cell)",   rvs),
        _row("Eco |ρ| (geographic)",       [abs(v) for v in evs]),
        _row("Bayesian γ (Laplace post.)", bays),
        _row("MRP γ (shrinkage cells)",    mrps),
        _row("DR γ (AIPW)",               drs),
        _row("DR KS overlap",              dks),
        _row("SES fraction (resid/base)",  sfs),
        "",
        "## Top 20 Domain Pairs by Baseline V",
        "",
        "| Domain pair | Base V | Resid V | Bay γ | MRP γ | DR γ | DR KS |",
        "|-------------|--------|---------|-------|-------|------|-------|",
    ]

    for p in valid[:20]:
        key  = f"{p['domain_a']}×{p['domain_b']}"
        bv   = f"{p['baseline_mean_v']:.3f}"    if p.get("baseline_mean_v") is not None else "—"
        rv   = f"{p['residual_mean_v']:.3f}"    if p.get("residual_mean_v") is not None else "—"
        bg   = f"{p['bay_mean_gamma']:+.3f}"    if p.get("bay_mean_gamma")  is not None else "—"
        mg   = f"{p['mrp_mean_gamma']:+.3f}"    if p.get("mrp_mean_gamma")  is not None else "—"
        dg   = f"{p['dr_mean_gamma']:+.3f}"     if p.get("dr_mean_gamma")   is not None else "—"
        dk   = f"{p['dr_mean_ks']:.3f}"         if p.get("dr_mean_ks")      is not None else "—"
        lines.append(f"| {key} | {bv} | {rv} | {bg} | {mg} | {dg} | {dk} |")

    lines += [
        "",
        "## Weakest 10 Domain Pairs (Baseline V)",
        "",
        "| Domain pair | Base V | Resid V | Bay γ | MRP γ | DR γ |",
        "|-------------|--------|---------|-------|-------|------|",
    ]
    for p in valid[-10:]:
        key  = f"{p['domain_a']}×{p['domain_b']}"
        bv   = f"{p['baseline_mean_v']:.3f}"    if p.get("baseline_mean_v") is not None else "—"
        rv   = f"{p['residual_mean_v']:.3f}"    if p.get("residual_mean_v") is not None else "—"
        bg   = f"{p['bay_mean_gamma']:+.3f}"    if p.get("bay_mean_gamma")  is not None else "—"
        mg   = f"{p['mrp_mean_gamma']:+.3f}"    if p.get("mrp_mean_gamma")  is not None else "—"
        dg   = f"{p['dr_mean_gamma']:+.3f}"     if p.get("dr_mean_gamma")   is not None else "—"
        lines.append(f"| {key} | {bv} | {rv} | {bg} | {mg} | {dg} |")

    lines += [
        "",
        "## Method Interpretation Guide",
        "",
        "| Signal | What it means |",
        "|--------|---------------|",
        "| High baseline V + high residual V | Strong conceptual link, not just SES confounding |",
        "| High baseline V + low residual V  | Association is SES-mediated (pure confounding) |",
        "| High |Eco ρ| + low baseline V     | Geographic pattern not captured by individual SES |",
        "| Bayesian CI excludes 0            | Robust association under parameter uncertainty |",
        "| MRP γ ≈ baseline V                | Cell-level pattern consistent with simulation |",
        "| DR KS > 0.3                       | Poor SES overlap: DR weights less reliable |",
        "| DR γ differs from baseline V      | Outcome model may be misspecified (one is wrong) |",
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
    mrp_cell_cols: List[str] = None,
    output_json: Path = OUTPUT_JSON,
    output_report: Path = OUTPUT_REPORT,
    resume: bool = True,
) -> None:
    if eco_cell_cols is None:
        eco_cell_cols = DEFAULT_ECO_CELL_COLS
    if mrp_cell_cols is None:
        mrp_cell_cols = DEFAULT_MRP_CELL_COLS

    t0 = time.time()
    print("=" * 70)
    print("Bridge Comparison Sweep — All Six Methods")
    print("=" * 70)
    print(f"  n_sim={N_SIM}  eco_cell_cols={eco_cell_cols}  mrp_cell_cols={mrp_cell_cols}")
    print(f"  n_bootstrap: eco={N_BOOTSTRAP_ECO}  bay={N_BOOTSTRAP_BAY}  "
          f"mrp={N_BOOTSTRAP_MRP}  dr={N_BOOTSTRAP_DR}")
    print(f"  workers={max_workers}")
    print()

    print("Loading survey data...")
    enc_dict, enc_nom_dict_rev = load_data()

    if not BASELINE_SWEEP.exists():
        print(f"ERROR: baseline sweep not found at {BASELINE_SWEEP}", file=sys.stderr)
        print("Run scripts/debug/sweep_cross_domain.py first.", file=sys.stderr)
        sys.exit(1)

    with open(BASELINE_SWEEP, encoding="utf-8") as f:
        baseline_data = json.load(f)

    selected_vars: Dict[str, List[str]] = baseline_data["selected_variables"]
    all_pair_keys = list(baseline_data["domain_pairs"].keys())
    print(f"Loaded {len(all_pair_keys)} domain pairs from baseline sweep.")

    # Resume: skip already-computed pairs
    existing_results: Dict[str, Any] = {}
    if resume and output_json.exists():
        try:
            with open(output_json, encoding="utf-8") as f:
                prev = json.load(f)
            existing_results = prev.get("domain_pairs", {})
            # Only skip if ALL new methods are present
            def _has_all_six(p):
                return (p.get("baseline_mean_v") is not None
                        and p.get("bay_mean_gamma") is not None)
            n_existing = sum(1 for v in existing_results.values() if _has_all_six(v))
            print(f"Resuming: {n_existing} pairs already have all 6 methods.")
        except Exception as e:
            print(f"Warning: could not load checkpoint ({e}); starting fresh.")

    def _needs_run(k):
        p = existing_results.get(k, {})
        return not (p.get("baseline_mean_v") is not None
                    and p.get("bay_mean_gamma") is not None)

    pairs_todo = [k for k in all_pair_keys if _needs_run(k)]
    print(f"Pairs remaining: {len(pairs_todo)} / {len(all_pair_keys)}", flush=True)

    results: Dict[str, Any] = dict(existing_results)

    meta = {
        "n_sim": N_SIM,
        "n_cells": 20,
        "eco_cell_cols": eco_cell_cols,
        "mrp_cell_cols": mrp_cell_cols,
        "n_bootstrap_eco": N_BOOTSTRAP_ECO,
        "n_bootstrap_bay": N_BOOTSTRAP_BAY,
        "n_bootstrap_mrp": N_BOOTSTRAP_MRP,
        "n_bootstrap_dr":  N_BOOTSTRAP_DR,
        "n_pairs_attempted": len(all_pair_keys),
        "workers": max_workers,
    }

    n_done = 0
    checkpoint_every = 5  # save more frequently (6 methods → more work per pair)

    def _run_pair(pair_key: str):
        da, db = pair_key.split("::")
        vars_a = selected_vars.get(da, [])
        vars_b = selected_vars.get(db, [])
        return pair_key, estimate_pair_all_methods(
            da, db, vars_a, vars_b, enc_dict, enc_nom_dict_rev,
            eco_cell_cols, mrp_cell_cols,
        )

    print(f"\nRunning sweep (workers={max_workers})...\n", flush=True)
    total = len(all_pair_keys)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_pair, k): k for k in pairs_todo}
        for future in as_completed(futures):
            pair_key = futures[future]
            try:
                key, result = future.result()
                results[key] = result
                n_done += 1
                elapsed = time.time() - t0
                n_so_far = len(existing_results) - (len(all_pair_keys) - len(pairs_todo)) + n_done

                bv  = result.get("baseline_mean_v")
                rv  = result.get("residual_mean_v")
                bg  = result.get("bay_mean_gamma")
                mg  = result.get("mrp_mean_gamma")
                dg  = result.get("dr_mean_gamma")
                dk  = result.get("dr_mean_ks")

                print(
                    f"  [{n_so_far}/{total}] {elapsed:.0f}s | {key}"
                    f" | base={bv:.3f}" if bv is not None else
                    f"  [{n_so_far}/{total}] {elapsed:.0f}s | {key} | FAIL",
                    end="",
                    flush=True,
                )
                if bv is not None:
                    print(
                        f" resid={rv:.3f}" if rv is not None else " resid=—",
                        f" bay_γ={bg:+.3f}" if bg is not None else " bay=—",
                        f" mrp_γ={mg:+.3f}" if mg is not None else " mrp=—",
                        f" dr_γ={dg:+.3f}" if dg is not None else " dr=—",
                        f" ks={dk:.2f}" if dk is not None else "",
                        flush=True,
                    )
                else:
                    print(flush=True)

                if n_done % checkpoint_every == 0:
                    meta["elapsed_seconds"] = round(time.time() - t0, 1)
                    _save_checkpoint(results, output_json, meta)

            except Exception as e:
                da, db = pair_key.split("::")
                results[pair_key] = {
                    "domain_a": da, "domain_b": db,
                    "estimates": [], "error": str(e),
                    **{k: None for k in _AGG_KEYS},
                }
                n_done += 1

    elapsed = time.time() - t0
    meta["elapsed_seconds"] = round(elapsed, 1)

    _save_checkpoint(results, output_json, meta)

    # Summary
    all_pairs = list(results.values())
    n_ok      = sum(1 for p in all_pairs if p.get("baseline_mean_v") is not None)
    bvs  = [p["baseline_mean_v"]  for p in all_pairs if p.get("baseline_mean_v") is not None]
    rvs  = [p["residual_mean_v"]  for p in all_pairs if p.get("residual_mean_v") is not None]
    bays = [p["bay_mean_gamma"]   for p in all_pairs if p.get("bay_mean_gamma") is not None]
    mrps = [p["mrp_mean_gamma"]   for p in all_pairs if p.get("mrp_mean_gamma") is not None]
    drs  = [p["dr_mean_gamma"]    for p in all_pairs if p.get("dr_mean_gamma") is not None]

    print()
    print("=" * 70)
    print("SWEEP COMPLETE")
    print("=" * 70)
    print(f"  Elapsed:      {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Pairs total:  {len(all_pairs)} | ok: {n_ok}")
    if bvs:
        print(f"  Baseline V:   mean={np.mean(bvs):.3f}  IQR=[{np.percentile(bvs,25):.3f}, {np.percentile(bvs,75):.3f}]")
    if rvs:
        print(f"  Residual V:   mean={np.mean(rvs):.3f}  IQR=[{np.percentile(rvs,25):.3f}, {np.percentile(rvs,75):.3f}]")
    if bays:
        print(f"  Bayesian γ:   mean={np.mean(bays):.3f}  IQR=[{np.percentile(bays,25):.3f}, {np.percentile(bays,75):.3f}]")
    if mrps:
        print(f"  MRP γ:        mean={np.mean(mrps):.3f}  IQR=[{np.percentile(mrps,25):.3f}, {np.percentile(mrps,75):.3f}]")
    if drs:
        print(f"  DR γ:         mean={np.mean(drs):.3f}  IQR=[{np.percentile(drs,25):.3f}, {np.percentile(drs,75):.3f}]")

    meta["elapsed_seconds"] = round(elapsed, 1)
    generate_report(results, output_report, meta)
    print(f"\n  JSON:   {output_json}")
    print(f"  Report: {output_report}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Six-method bridge comparison sweep across all 276 domain pairs"
    )
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Parallel workers (default: 1; use N-1 on an N-core machine)"
    )
    parser.add_argument(
        "--eco-cell-cols", nargs="+", default=DEFAULT_ECO_CELL_COLS, metavar="COL",
        help=f"Ecological cell columns (default: {DEFAULT_ECO_CELL_COLS})"
    )
    parser.add_argument(
        "--mrp-cell-cols", nargs="+", default=DEFAULT_MRP_CELL_COLS, metavar="COL",
        help=f"MRP cell columns (default: {DEFAULT_MRP_CELL_COLS})"
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
        mrp_cell_cols=args.mrp_cell_cols,
        output_json=args.output_json,
        output_report=args.output_report,
        resume=not args.no_resume,
    )
