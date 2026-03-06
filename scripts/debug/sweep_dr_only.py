"""DR-only sweep across all 276 domain pairs with semantic variables.

Runs only DoublyRobustBridgeEstimator (skips baseline, residual, ecological,
bayesian) for maximum speed. Each pair fits 2 outcome models + 1 propensity
model + n_bootstrap refits.

Timing estimate:
  n_bootstrap=10:  ~30s per pair → ~2.5h total on 3 workers
  n_bootstrap=50:  ~120s per pair → ~10h total on 3 workers

Usage:
    nohup python scripts/debug/sweep_dr_only.py --workers 3 \\
        > /tmp/dr_sweep.log 2>&1 &
    tail -f /tmp/dr_sweep.log
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*convergence.*')
warnings.filterwarnings('ignore', message='.*Maximum Likelihood.*')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts' / 'debug'))

BASELINE_SWEEP = ROOT / 'data' / 'results' / 'cross_domain_sweep.json'
SEMANTIC_SEL = ROOT / 'data' / 'results' / 'semantic_variable_selection.json'
OUTPUT_JSON = ROOT / 'data' / 'results' / 'dr_sweep_results.json'

N_SIM = 500
N_BOOTSTRAP_DR = 10


def load_data():
    from dataset_knowledge import los_mex_dict, enc_nom_dict, DATA_AVAILABLE
    if not DATA_AVAILABLE:
        print('ERROR: Survey data not available.', file=sys.stderr)
        sys.exit(1)
    from ses_analysis import AnalysisConfig
    from select_bridge_variables_semantic import SemanticVariableSelector

    preprocessed = AnalysisConfig.preprocess_survey_data(los_mex_dict)
    enc_dict = preprocessed.get('enc_dict', los_mex_dict.get('enc_dict', {}))
    enc_nom_dict_rev = {v: k for k, v in enc_nom_dict.items()}

    if SEMANTIC_SEL.exists():
        SemanticVariableSelector.build_aggregates(
            enc_dict, enc_nom_dict_rev, selection_path=SEMANTIC_SEL)

    return enc_dict, enc_nom_dict_rev


def _extract_construct_name(var_id: str) -> Optional[str]:
    """Extract construct name from variable id like 'agg_corruption_perception|COR'."""
    col = var_id.split('|')[0]
    if col.startswith('agg_'):
        return col[4:]  # strip 'agg_'
    return None


def estimate_pair_dr(
    domain_a: str, domain_b: str,
    vars_a: List[str], vars_b: List[str],
    enc_dict: dict, enc_nom_dict_rev: dict,
    direction_map: Optional[Dict] = None,
) -> Dict[str, Any]:
    from ses_regression import DoublyRobustBridgeEstimator
    from select_bridge_variables_semantic import SemanticVariableSelector

    survey_a = enc_nom_dict_rev.get(domain_a)
    survey_b = enc_nom_dict_rev.get(domain_b)
    df_a = enc_dict.get(survey_a, {}).get('dataframe') if survey_a else None
    df_b = enc_dict.get(survey_b, {}).get('dataframe') if survey_b else None

    if not isinstance(df_a, pd.DataFrame) or not isinstance(df_b, pd.DataFrame):
        return {'domain_a': domain_a, 'domain_b': domain_b,
                'estimates': [], 'n_total': 0, 'error': 'DataFrame not found',
                'dr_mean_gamma': None, 'dr_mean_v': None, 'dr_mean_ks': None}

    est = DoublyRobustBridgeEstimator(
        n_sim=N_SIM, n_bootstrap=N_BOOTSTRAP_DR, max_categories=5)

    estimates = []
    for va in vars_a:
        col_a = va.split('|')[0]
        if col_a not in df_a.columns:
            continue
        construct_a = _extract_construct_name(va)
        for vb in vars_b:
            col_b = vb.split('|')[0]
            if col_b not in df_b.columns:
                continue
            construct_b = _extract_construct_name(vb)

            # Resolve per-construct causal direction
            if direction_map and construct_a and construct_b:
                src, tgt, dir_type = SemanticVariableSelector.get_pair_direction(
                    domain_a, domain_b, direction_map,
                    construct_a=construct_a, construct_b=construct_b)
            else:
                id_a = f"{domain_a}:{construct_a}" if construct_a else domain_a
                id_b = f"{domain_b}:{construct_b}" if construct_b else domain_b
                src, tgt, dir_type = id_a, id_b, 'ambiguous'

            # Swap source/target if causal direction says B causes A
            src_dom = src.split(':')[0] if ':' in src else src
            if dir_type == 'causal' and src_dom == domain_b:
                e_df_a, e_df_b = df_b, df_a
                e_col_a, e_col_b = col_b, col_a
                e_va, e_vb = vb, va
            else:
                e_df_a, e_df_b = df_a, df_b
                e_col_a, e_col_b = col_a, col_b
                e_va, e_vb = va, vb

            row = {'var_a': e_va, 'var_b': e_vb,
                   'causal_direction': dir_type}
            try:
                r = est.estimate(var_id_a=e_va, var_id_b=e_vb,
                                 df_a=e_df_a, df_b=e_df_b,
                                 col_a=e_col_a, col_b=e_col_b)
                if r:
                    row['dr_gamma'] = round(r['gamma'], 4)
                    row['dr_gamma_ci'] = r['gamma_ci_95']
                    row['dr_v'] = round(r['cramers_v'], 4)
                    row['dr_ks'] = round(r['propensity_overlap'], 4)
                    row['dr_ks_warning'] = r.get('ks_warning', False)
            except Exception as e:
                row['dr_error'] = str(e)
            estimates.append(row)

    def _mean(lst):
        return round(float(np.mean(lst)), 4) if lst else None

    def _extract(key):
        return [e[key] for e in estimates if key in e and e[key] is not None]

    return {
        'domain_a': domain_a, 'domain_b': domain_b,
        'estimates': estimates, 'n_total': len(estimates),
        'n_dr_ok': len(_extract('dr_gamma')),
        'dr_mean_gamma': _mean(_extract('dr_gamma')),
        'dr_mean_v': _mean(_extract('dr_v')),
        'dr_mean_ks': _mean(_extract('dr_ks')),
        'n_dr_ks_warning': sum(1 for e in estimates if e.get('dr_ks_warning')),
    }


def main(max_workers=1, resume=True):
    t0 = time.time()
    print('=' * 70)
    print('DR-Only Sweep — Semantic Variables')
    print('=' * 70)
    print(f'  n_sim={N_SIM}  n_bootstrap_dr={N_BOOTSTRAP_DR}  workers={max_workers}')

    print('\nLoading data...', flush=True)
    enc_dict, enc_nom_dict_rev = load_data()

    # Load variable selection
    if SEMANTIC_SEL.exists():
        from select_bridge_variables_semantic import SemanticVariableSelector
        selected_vars = SemanticVariableSelector.load(SEMANTIC_SEL)
        print(f'Using semantic selection ({len(selected_vars)} domains)')
    else:
        with open(BASELINE_SWEEP) as f:
            selected_vars = json.load(f)['selected_variables']
        print('Using naive selection (no semantic file)')

    # Load causal direction map (construct-to-construct only)
    direction_map = SemanticVariableSelector.load_causal_direction_map()
    n_causal = sum(1 for v in direction_map.values()
                   if v.get('direction') == 'causal')
    n_empirical = sum(1 for v in direction_map.values()
                      if v.get('source') == 'empirical')
    print(f'Causal direction map: {len(direction_map)} construct pairs '
          f'({n_causal} causal, {n_empirical} empirical)')

    # Load pair list from baseline sweep
    with open(BASELINE_SWEEP) as f:
        all_pair_keys = list(json.load(f)['domain_pairs'].keys())
    print(f'Domain pairs: {len(all_pair_keys)}')

    # Resume
    existing = {}
    if resume and OUTPUT_JSON.exists():
        try:
            with open(OUTPUT_JSON) as f:
                existing = json.load(f).get('domain_pairs', {})
            n_done = sum(1 for v in existing.values() if v.get('dr_mean_gamma') is not None)
            print(f'Resuming: {n_done} pairs already done')
        except Exception:
            pass

    pairs_todo = [k for k in all_pair_keys
                  if existing.get(k, {}).get('dr_mean_gamma') is None]
    print(f'Remaining: {len(pairs_todo)} pairs\n', flush=True)

    results = dict(existing)

    def _run(pair_key):
        da, db = pair_key.split('::')
        va = selected_vars.get(da, [])
        vb = selected_vars.get(db, [])
        result = estimate_pair_dr(da, db, va, vb, enc_dict, enc_nom_dict_rev,
                                  direction_map=direction_map)
        return pair_key, result

    n_done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run, k): k for k in pairs_todo}
        for f in as_completed(futures):
            try:
                key, result = f.result()
                results[key] = result
                n_done += 1
                elapsed = time.time() - t0
                avg = elapsed / n_done
                remaining = len(pairs_todo) - n_done
                eta = avg * remaining / max(max_workers, 1) / 60

                dg = result.get('dr_mean_gamma')
                dk = result.get('dr_mean_ks')
                total = len(existing) + n_done
                dg_str = f'g={dg:+.3f}' if dg is not None else 'FAIL'
                dk_str = f'ks={dk:.2f}' if dk is not None else ''
                print(f'  [{total}/{len(all_pair_keys)}] {elapsed:.0f}s (ETA {eta:.0f}m) '
                      f'| {key} | {dg_str} {dk_str}', flush=True)

                # Checkpoint every pair
                out = {'metadata': {
                    'n_sim': N_SIM, 'n_bootstrap_dr': N_BOOTSTRAP_DR,
                    'timestamp': datetime.now().isoformat(),
                    'n_pairs': len(results), 'elapsed_seconds': round(elapsed, 1),
                }, 'domain_pairs': results}
                tmp = OUTPUT_JSON.with_suffix('.tmp')
                with open(tmp, 'w') as fh:
                    json.dump(out, fh, indent=2, ensure_ascii=False)
                tmp.replace(OUTPUT_JSON)
            except Exception as e:
                pk = futures[f]
                da, db = pk.split('::')
                results[pk] = {'domain_a': da, 'domain_b': db,
                               'error': str(e), 'dr_mean_gamma': None}
                n_done += 1

    elapsed = time.time() - t0
    all_pairs = list(results.values())
    drs = [p['dr_mean_gamma'] for p in all_pairs if p.get('dr_mean_gamma') is not None]

    print('\n' + '=' * 70)
    print('SWEEP COMPLETE')
    print('=' * 70)
    print(f'  Elapsed: {elapsed:.0f}s ({elapsed/60:.1f} min)')
    print(f'  Pairs: {len(all_pairs)} total, {len(drs)} with results')
    if drs:
        print(f'  DR g: mean={np.mean(drs):.3f}  '
              f'IQR=[{np.percentile(drs,25):.3f}, {np.percentile(drs,75):.3f}]  '
              f'range=[{min(drs):.3f}, {max(drs):.3f}]')
    print(f'\n  Output: {OUTPUT_JSON}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DR-only sweep with semantic variables')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--no-resume', action='store_true')
    args = parser.parse_args()
    main(max_workers=args.workers, resume=not args.no_resume)
