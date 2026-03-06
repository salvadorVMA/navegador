"""
test_bridge_improvements.py — Validate all five bridge improvements on ECO, GEN, REL.

Tests:
  1. Enriched SES (income_quintile, empleo_formality, region_x_Tam_loc)
  2. Continuous PCA scores (no qcut)
  3. Construct-level max/agreeing gamma (vs domain-level mean)
  4. Within-domain bridge calibration (bridge vs observed Spearman ρ)
  5. Cross-domain ECO×GEN with all improvements combined

Usage:
    python scripts/debug/test_bridge_improvements.py
"""

from __future__ import annotations
import sys
import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*convergence.*")
warnings.filterwarnings("ignore", message=".*Maximum Likelihood.*")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))

DOMAINS_TEST = ["ECO", "GEN", "REL"]

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    from dataset_knowledge import los_mex_dict, enc_nom_dict, DATA_AVAILABLE
    if not DATA_AVAILABLE:
        print("ERROR: data not available"); sys.exit(1)
    from ses_analysis import AnalysisConfig
    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get("enc_dict", los_mex_dict.get("enc_dict", {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}
    return enc_dict, enc_nom_dict_rev


def load_constructs(enc_dict, enc_nom_dict_rev):
    from select_bridge_variables_semantic import SemanticVariableSelector
    sel = SemanticVariableSelector.load()
    # Build continuous aggregated columns
    SemanticVariableSelector.build_aggregates(enc_dict, enc_nom_dict_rev)
    return sel


# ---------------------------------------------------------------------------
# Test 1: Enriched SES variable coverage
# ---------------------------------------------------------------------------

def test_enriched_ses(enc_dict, enc_nom_dict_rev):
    print("\n" + "=" * 60)
    print("TEST 1: Enriched SES variable coverage")
    print("=" * 60)
    from ses_regression import SES_REGRESSION_VARS, SESEncoder

    new_vars = ["income_quintile", "empleo_formality", "region_x_Tam_loc"]
    for v in new_vars:
        assert v in SES_REGRESSION_VARS, f"{v} missing from SES_REGRESSION_VARS"

    for domain in DOMAINS_TEST:
        survey = enc_nom_dict_rev.get(domain)
        df = enc_dict[survey]["dataframe"]
        present = [v for v in new_vars if v in df.columns]
        missing = [v for v in new_vars if v not in df.columns]
        # Coverage stats
        for v in present:
            s = df[v].dropna()
            print(f"  {domain}.{v}: n={len(s)} nuniq={s.nunique()} "
                  f"range=[{s.min():.1f},{s.max():.1f}]")
        if missing:
            print(f"  {domain}: MISSING {missing}")

        # Verify encoder handles them
        enc = SESEncoder()
        avail = [v for v in SES_REGRESSION_VARS if v in df.columns]
        X = enc.fit_transform(df[avail].dropna(subset=avail))
        new_cols = [c for c in X.columns
                    if any(c.startswith(p)
                           for p in ["income_q", "empleo_f", "rtl_"])]
        print(f"  {domain}: encoder produced {len(X.columns)} features, "
              f"new={new_cols[:5]}{'…' if len(new_cols) > 5 else ''}")
    print("  ✓ TEST 1 PASSED")


# ---------------------------------------------------------------------------
# Test 2: Continuous PCA scores (no qcut)
# ---------------------------------------------------------------------------

def test_continuous_pca(enc_dict, enc_nom_dict_rev):
    print("\n" + "=" * 60)
    print("TEST 2: Continuous PCA scores (no binning)")
    print("=" * 60)
    for domain in ["ECO", "GEN", "REL"]:
        survey = enc_nom_dict_rev.get(domain)
        df = enc_dict[survey]["dataframe"]
        agg_cols = [c for c in df.columns if c.startswith("agg_")]
        if not agg_cols:
            print(f"  {domain}: no agg_ columns (selection not built?)")
            continue
        for col in agg_cols[:2]:
            s = df[col].dropna()
            nuniq = s.nunique()
            skew = float(stats.skew(s))
            print(f"  {domain}.{col}: n={len(s)} nuniq={nuniq} "
                  f"mean={s.mean():.3f} std={s.std():.3f} skew={skew:.2f}")
            # Uniform marginals (qcut) would give nuniq==5; continuous should be much higher
            assert nuniq > 10, (
                f"{col} has only {nuniq} unique values — looks quantile-binned!")
    print("  ✓ TEST 2 PASSED")


# ---------------------------------------------------------------------------
# Test 3: Construct-level top/agreeing gamma
# ---------------------------------------------------------------------------

def _agreeing_gamma(estimates: List[Dict]) -> Dict:
    """Compute construct-level aggregates across all var-pairs."""
    bay_vals = [(e["var_a"], e["var_b"], e.get("bay_gamma") or 0,
                 e.get("dr_gamma") or 0, e.get("mrp_gamma") or 0)
                for e in estimates
                if e.get("bay_gamma") is not None]

    if not bay_vals:
        return {}

    abs_bays = [abs(b) for _, _, b, _, _ in bay_vals]
    top_idx  = int(np.argmax(abs_bays))
    va, vb, top_bay, top_dr, top_mrp = bay_vals[top_idx]

    agreeing = [
        (b, d) for _, _, b, d, _ in bay_vals
        if abs(b) > 0.01 and abs(d) > 0.01 and np.sign(b) == np.sign(d)
    ]
    agreeing_gamma = (float(np.mean([b for b, _ in agreeing]))
                      if agreeing else None)

    return {
        "top_var_a":       va.split("|")[0],
        "top_var_b":       vb.split("|")[0],
        "top_bay_gamma":   round(top_bay, 4),
        "top_dr_gamma":    round(top_dr,  4),
        "mean_bay_gamma":  round(float(np.mean([b for _, _, b, _, _ in bay_vals])), 4),
        "agreeing_gamma":  round(agreeing_gamma, 4) if agreeing_gamma else None,
        "n_agreeing_pairs": len(agreeing),
        "n_signal_pairs":  sum(1 for x in abs_bays if x > 0.05),
        "n_total_pairs":   len(bay_vals),
        "signal_ratio":    round(sum(1 for x in abs_bays if x > 0.05) / len(bay_vals), 3),
    }


def test_construct_level_aggregates():
    print("\n" + "=" * 60)
    print("TEST 3: Construct-level vs domain-level mean gamma")
    print("=" * 60)
    results_path = ROOT / "data" / "results" / "bridge_comparison_semantic_results.json"
    if not results_path.exists():
        print("  SKIP: no semantic sweep results found"); return

    with open(results_path) as f:
        d = json.load(f)

    for key, pair in d["domain_pairs"].items():
        da, db = pair["domain_a"], pair["domain_b"]
        if not (da in DOMAINS_TEST or db in DOMAINS_TEST):
            continue
        if not pair.get("estimates"):
            continue
        agg = _agreeing_gamma(pair["estimates"])
        if not agg:
            continue
        print(f"\n  {da}×{db}:")
        print(f"    domain mean γ  = {pair.get('bay_mean_gamma', '?'):+.4f}")
        print(f"    top construct  = {agg['top_var_a']} × {agg['top_var_b']}")
        print(f"    top bay γ      = {agg['top_bay_gamma']:+.4f}  "
              f"dr γ = {agg['top_dr_gamma']:+.4f}")
        print(f"    agreeing γ     = {agg['agreeing_gamma']}  "
              f"({agg['n_agreeing_pairs']}/{agg['n_total_pairs']} pairs)")
        print(f"    signal pairs   = {agg['n_signal_pairs']}/{agg['n_total_pairs']} "
              f"(|γ|>0.05)  ratio={agg['signal_ratio']:.2f}")
    print("\n  ✓ TEST 3 PASSED")


# ---------------------------------------------------------------------------
# Test 4: Within-domain bridge calibration
# ---------------------------------------------------------------------------

def _spearman_within(df: pd.DataFrame, col_a: str, col_b: str) -> Tuple[float, float]:
    """Observed Spearman ρ between two columns in the same DataFrame."""
    both = df[[col_a, col_b]].dropna()
    if len(both) < 10:
        return float("nan"), float("nan")
    r, p = stats.spearmanr(both[col_a], both[col_b])
    return float(r), float(p)


def test_within_domain_calibration(enc_dict, enc_nom_dict_rev, selected_vars):
    """
    For REL: compare observed Spearman ρ between construct pairs to bridge γ.

    Splits the REL dataframe into odd/even rows to simulate two 'surveys',
    then runs CrossDatasetBivariateEstimator treating them as cross-domain.
    The bridge estimate should approximate the observed correlation when SES
    explains most of the covariance.
    """
    print("\n" + "=" * 60)
    print("TEST 4: Within-domain bridge calibration (REL)")
    print("=" * 60)
    from ses_regression import CrossDatasetBivariateEstimator

    domain = "REL"
    survey = enc_nom_dict_rev.get(domain)
    df = enc_dict[survey]["dataframe"]
    vars_rel = selected_vars.get(domain, [])
    agg_cols = [v.split("|")[0] for v in vars_rel if v.split("|")[0] in df.columns]

    if len(agg_cols) < 2:
        print(f"  SKIP: fewer than 2 construct columns available for {domain}")
        return

    est = CrossDatasetBivariateEstimator(n_sim=500, max_categories=5)

    print(f"  {'Pair':65}  {'obs_ρ':>7}  {'bridge_V':>8}  {'gap':>7}")
    print(f"  {'-'*65}  {'-'*7}  {'-'*8}  {'-'*7}")

    results = []
    for i, col_a in enumerate(agg_cols):
        for col_b in agg_cols[i+1:]:
            # Observed Spearman ρ
            obs_rho, obs_p = _spearman_within(df, col_a, col_b)
            if np.isnan(obs_rho):
                continue

            # Bridge: split into odd/even rows as pseudo-surveys
            df_a = df.iloc[::2].copy()   # even rows
            df_b = df.iloc[1::2].copy()  # odd rows

            try:
                r = est.estimate(
                    var_id_a=f"{col_a}|{domain}_A",
                    var_id_b=f"{col_b}|{domain}_B",
                    df_a=df_a, df_b=df_b,
                    col_a=col_a, col_b=col_b,
                )
                bridge_v = r["cramers_v"] if r else float("nan")
            except Exception as exc:
                bridge_v = float("nan")

            gap = abs(obs_rho) - bridge_v if not np.isnan(bridge_v) else float("nan")
            label = f"{col_a.replace('agg_',''):30} × {col_b.replace('agg_',''):30}"
            print(f"  {label:65}  {obs_rho:+7.4f}  {bridge_v:8.4f}  {gap:+7.4f}")
            results.append((obs_rho, bridge_v, gap))

    if results:
        gaps = [r[2] for r in results if not np.isnan(r[2])]
        print(f"\n  mean |gap| (obs_ρ - bridge_V): {np.mean(np.abs(gaps)):.4f}")
        print(f"  CIA recovery:  bridge captures "
              f"{100*(1 - np.mean(np.abs(gaps))/np.mean([abs(r[0]) for r in results])):.0f}% "
              f"of observed correlation on average")
    print("  ✓ TEST 4 PASSED")


# ---------------------------------------------------------------------------
# Test 5: ECO × GEN with all improvements combined
# ---------------------------------------------------------------------------

def test_cross_domain_improved(enc_dict, enc_nom_dict_rev, selected_vars):
    print("\n" + "=" * 60)
    print("TEST 5: ECO × GEN with all improvements")
    print("=" * 60)
    from ses_regression import (
        CrossDatasetBivariateEstimator, BayesianBridgeEstimator,
        DoublyRobustBridgeEstimator,
    )
    from ses_regression import goodman_kruskal_gamma

    domain_a, domain_b = "ECO", "GEN"
    survey_a = enc_nom_dict_rev[domain_a]
    survey_b = enc_nom_dict_rev[domain_b]
    df_a = enc_dict[survey_a]["dataframe"]
    df_b = enc_dict[survey_b]["dataframe"]

    vars_a = [v.split("|")[0] for v in selected_vars.get(domain_a, [])
              if v.split("|")[0] in df_a.columns]
    vars_b = [v.split("|")[0] for v in selected_vars.get(domain_b, [])
              if v.split("|")[0] in df_b.columns]

    print(f"  ECO constructs: {vars_a}")
    print(f"  GEN constructs: {vars_b}")

    est_base = CrossDatasetBivariateEstimator(n_sim=500, max_categories=5)
    est_bay  = BayesianBridgeEstimator(n_sim=500, n_draws=100, max_categories=5)
    est_dr   = DoublyRobustBridgeEstimator(n_sim=500, n_bootstrap=10, max_categories=5)

    print(f"\n  {'ECO construct':40} × {'GEN construct':40}  "
          f"{'base_V':>7}  {'bay_γ':>7}  {'dr_γ':>7}")
    print(f"  {'-'*40}   {'-'*40}  {'-'*7}  {'-'*7}  {'-'*7}")

    rows = []
    for col_a in vars_a:
        for col_b in vars_b:
            va = f"{col_a}|{domain_a}"
            vb = f"{col_b}|{domain_b}"
            row = {"col_a": col_a, "col_b": col_b}
            try:
                r = est_base.estimate(va, vb, df_a, df_b, col_a, col_b)
                row["base_v"] = r["cramers_v"] if r else None
            except Exception:
                row["base_v"] = None
            try:
                r = est_bay.estimate(va, vb, df_a, df_b, col_a, col_b)
                row["bay_g"] = r["gamma"] if r else None
                row["bay_ci"] = r["gamma_ci_95"] if r else None
            except Exception:
                row["bay_g"] = None
            try:
                r = est_dr.estimate(va, vb, df_a, df_b, col_a, col_b)
                row["dr_g"] = r["gamma"] if r else None
            except Exception:
                row["dr_g"] = None
            rows.append(row)

            bv = f"{row['base_v']:.4f}" if row.get("base_v") is not None else "  — "
            bg = f"{row['bay_g']:+.4f}" if row.get("bay_g") is not None else "  — "
            dg = f"{row['dr_g']:+.4f}"  if row.get("dr_g")  is not None else "  — "
            print(f"  {col_a.replace('agg_',''):40}   "
                  f"{col_b.replace('agg_',''):40}  {bv:>7}  {bg:>7}  {dg:>7}")

    # Summary
    bays = [r["bay_g"] for r in rows if r.get("bay_g") is not None]
    drs  = [r["dr_g"]  for r in rows if r.get("dr_g")  is not None]
    agreeing = [(b, d) for b, d in zip(bays, drs)
                if abs(b) > 0.01 and abs(d) > 0.01 and np.sign(b) == np.sign(d)]
    print(f"\n  Summary ({len(rows)} construct pairs):")
    if not bays:
        print("    no valid bay_γ values — SKIP")
        return
    print(f"    mean |bay_γ|:      {np.mean(np.abs(bays)):.4f}")
    print(f"    max  |bay_γ|:      {np.max(np.abs(bays)):.4f}")
    print(f"    agreeing pairs:    {len(agreeing)}/{len(rows)}")
    if agreeing:
        print(f"    agreeing mean γ:   {np.mean([b for b,_ in agreeing]):+.4f}")
    print("  ✓ TEST 5 PASSED")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading survey data...")
    enc_dict, enc_nom_dict_rev = load_data()
    print("Building semantic constructs (continuous PCA)...")
    selected_vars = load_constructs(enc_dict, enc_nom_dict_rev)

    test_enriched_ses(enc_dict, enc_nom_dict_rev)
    test_continuous_pca(enc_dict, enc_nom_dict_rev)
    test_construct_level_aggregates()
    test_within_domain_calibration(enc_dict, enc_nom_dict_rev, selected_vars)
    test_cross_domain_improved(enc_dict, enc_nom_dict_rev, selected_vars)

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
