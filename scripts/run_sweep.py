"""Run the JAX DR bridge sweep and print results summary.

Usage (CLI):
    python scripts/run_sweep.py --dataset wvs_temporal --data-repo /content/navegador_data

Usage (import):
    from scripts.load_pairs import load_sweep_tasks
    from scripts.run_sweep import run_sweep, print_summary
    context_dfs, sweep_tasks, config = load_sweep_tasks(...)
    results = run_sweep(context_dfs, sweep_tasks, config)
    print_summary(results)
"""

import argparse
import gc
import json
import os
import sys
import time
from datetime import datetime

import jax
import numpy as np

# Allow running as `python scripts/run_sweep.py` from repo root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from scripts.jax_dr_bridge import dr_estimate_single, prepare_pair_data
from scripts.load_pairs import load_sweep_tasks


def run_sweep(
    context_dfs: dict,
    sweep_tasks: list,
    config: dict,
    n_sim: int = 2000,
    n_bootstrap: int = 200,
    batch_size: int = 200,
    output_dir: str = "/content",
    push_fn=None,
) -> dict:
    """Run the full sweep with checkpointing.

    Returns the final results dict.
    """
    dataset = config["dataset"]
    sweep_mode = config["sweep_mode"]
    backend = jax.default_backend()

    output_file = os.path.join(output_dir, f"jax_dr_sweep_{dataset}.json")
    checkpoint_file = os.path.join(output_dir, f"jax_dr_sweep_{dataset}_checkpoint.json")

    # Resume from checkpoint
    estimates = {}
    skipped = {}
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file) as f:
            ckpt = json.load(f)
        estimates = ckpt.get("estimates", {})
        skipped = ckpt.get("skipped", {})
        print(f"Resumed: {len(estimates)} done, {len(skipped)} skipped.")

    done_keys = set(estimates.keys()) | set(skipped.keys())
    remaining = [t for t in sweep_tasks if t["key"] not in done_keys]
    print(f"Remaining: {len(remaining)} / {len(sweep_tasks)}")

    # Sweep — lazy preparation (one pair at a time to avoid RAM blowup)
    n_done = len(estimates)
    n_sig = sum(1 for v in estimates.values() if v.get("excl_zero"))
    batch_count = 0
    t0 = time.time()

    for task in remaining:
        pair_key = task["key"]
        df_a = context_dfs.get(task["context_a"])
        df_b = context_dfs.get(task["context_b"])
        col_a, col_b = task["col_a"], task["col_b"]

        if df_a is None or df_b is None:
            skipped[pair_key] = "missing context"
            continue
        if col_a not in df_a.columns or col_b not in df_b.columns:
            skipped[pair_key] = f"missing column: {col_a} or {col_b}"
            continue

        try:
            data = prepare_pair_data(df_a, col_a, df_b, col_b)
            if data is None:
                skipped[pair_key] = "K<3 or insufficient data"
                continue
            X_a, y_a, X_b, y_b, X_ref, K = data
        except Exception as e:
            skipped[pair_key] = str(e)[:200]
            continue

        try:
            seed = hash(pair_key) % 10000
            result = dr_estimate_single(
                X_a, y_a, X_b, y_b, X_ref,
                K=K, n_sim=n_sim, n_bootstrap=n_bootstrap,
                seed=seed)
            estimates[pair_key] = result
            n_done += 1
            if result["excl_zero"]:
                n_sig += 1
        except Exception as e:
            skipped[pair_key] = str(e)[:200]

        # Free numpy arrays immediately
        del X_a, y_a, X_b, y_b, X_ref, data
        batch_count += 1

        total_processed = n_done + len(skipped)
        if total_processed % 50 == 0:
            elapsed = time.time() - t0
            rate = n_done / max(elapsed, 1)
            left = len(remaining) - total_processed
            eta = left / max(rate, 0.01)
            print(
                f"  [{total_processed}/{len(sweep_tasks)}] "
                f"done={n_done} sig={n_sig} "
                f"({100*n_sig/max(n_done,1):.1f}%) "
                f"{rate:.1f}/s ETA={eta:.0f}s")

        # Checkpoint + GC after each batch
        if batch_count >= batch_size:
            batch_count = 0
            jax.clear_caches()
            gc.collect()
            ckpt = {
                "metadata": {
                    "dataset": dataset,
                    "sweep_mode": sweep_mode,
                    "n_sim": n_sim,
                    "n_bootstrap": n_bootstrap,
                    "timestamp": datetime.now().isoformat(),
                },
                "estimates": estimates,
                "skipped": skipped,
            }
            with open(checkpoint_file, "w") as f:
                json.dump(ckpt, f)
            if push_fn is not None:
                try:
                    push_fn(checkpoint_file)
                except Exception:
                    pass

    # Final checkpoint for last partial batch
    if batch_count > 0:
        gc.collect()
        ckpt = {
            "metadata": {
                "dataset": dataset, "sweep_mode": sweep_mode,
                "n_sim": n_sim, "n_bootstrap": n_bootstrap,
                "timestamp": datetime.now().isoformat(),
            },
            "estimates": estimates, "skipped": skipped,
        }
        with open(checkpoint_file, "w") as f:
            json.dump(ckpt, f)
        if push_fn is not None:
            try:
                push_fn(checkpoint_file)
            except Exception:
                pass

    elapsed = time.time() - t0
    print(f"\nDone: {n_done} estimates, {len(skipped)} skipped, "
          f"{n_sig} sig ({100*n_sig/max(n_done,1):.1f}%) in {elapsed:.1f}s")

    # Save final results
    final = {
        "metadata": {
            "dataset": dataset, "sweep_mode": sweep_mode,
            "n_sim": n_sim, "n_bootstrap": n_bootstrap,
            "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
            "engine": f"jax_{backend}_f64",
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": datetime.now().isoformat(),
        },
        "estimates": estimates, "skipped": skipped,
    }
    with open(output_file, "w") as f:
        json.dump(final, f)
    print(f"Saved: {output_file}")

    return final


def print_summary(results: dict):
    """Print results summary."""
    meta = results["metadata"]
    est = results["estimates"]
    skip = results.get("skipped", {})

    print("=" * 60)
    print("JAX DR Bridge Sweep — Results Summary")
    print("=" * 60)
    print(f"Engine:        {meta.get('engine', 'jax')}")
    print(f"SES vars:      {meta['ses_vars']}")
    print(f"n_sim:         {meta['n_sim']}")
    print(f"n_bootstrap:   {meta['n_bootstrap']}")
    print(f"Pairs total:   {meta.get('n_pairs_total', len(est) + len(skip))}")
    print(f"Estimates:     {len(est)}")
    print(f"Skipped:       {len(skip)}")
    print(f"Elapsed:       {meta.get('elapsed_seconds', '?')}s")
    print()

    if not est:
        print("No estimates to summarize.")
        return

    gammas = np.array([v["dr_gamma"] for v in est.values()])
    ci_widths = np.array([v["ci_width"] for v in est.values()])
    nmis = np.array([v["dr_nmi"] for v in est.values()])
    n_sig = sum(1 for v in est.values() if v["excl_zero"])

    print(f"--- Gamma distribution ---")
    print(f"  Median |gamma|: {np.median(np.abs(gammas)):.4f}")
    print(f"  Mean |gamma|:   {np.mean(np.abs(gammas)):.4f}")
    print(f"  Max |gamma|:    {np.max(np.abs(gammas)):.4f}")
    print(f"  P10/P90 gamma:  {np.percentile(gammas, 10):.4f} / {np.percentile(gammas, 90):.4f}")
    print()
    print(f"--- CI width distribution ---")
    print(f"  Median:         {np.median(ci_widths):.4f}")
    print(f"  Mean:           {np.mean(ci_widths):.4f}")
    print(f"  P10/P90:        {np.percentile(ci_widths, 10):.4f} / {np.percentile(ci_widths, 90):.4f}")
    print()
    print(f"--- Significance ---")
    print(f"  CIs excluding zero: {n_sig} / {len(est)} ({100*n_sig/len(est):.1f}%)")
    print()
    print(f"--- NMI ---")
    print(f"  Median NMI:     {np.median(nmis):.4f}")
    print(f"  Max NMI:        {np.max(nmis):.4f}")
    print()

    # Top 10 by |gamma|
    sorted_pairs = sorted(est.items(), key=lambda x: abs(x[1]["dr_gamma"]), reverse=True)
    print("--- Top 10 pairs by |gamma| ---")
    for pair_key, val in sorted_pairs[:10]:
        sig = "*" if val["excl_zero"] else " "
        print(f"  {sig} gamma={val['dr_gamma']:+.4f}  "
              f"CI=[{val['dr_ci_lo']:.4f}, {val['dr_ci_hi']:.4f}]  "
              f"NMI={val['dr_nmi']:.4f}  {pair_key[:80]}")


def main():
    parser = argparse.ArgumentParser(description="Run JAX DR bridge sweep")
    parser.add_argument("--dataset", default="wvs_temporal",
                        choices=["los_mex", "wvs", "wvs_temporal"])
    parser.add_argument("--data-repo", default="/content/navegador_data")
    parser.add_argument("--output-dir", default="/content")
    parser.add_argument("--n-sim", type=int, default=2000)
    parser.add_argument("--n-bootstrap", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()

    # JAX setup
    os.environ["JAX_ENABLE_X64"] = "1"
    jax.config.update("jax_enable_x64", True)
    backend = jax.default_backend()
    print(f"JAX backend: {backend}, devices: {jax.devices()}")
    import jax.numpy as jnp
    print(f"Float64: {jnp.array(1.0).dtype}")

    context_dfs, sweep_tasks, config = load_sweep_tasks(args.dataset, args.data_repo)
    results = run_sweep(
        context_dfs, sweep_tasks, config,
        n_sim=args.n_sim,
        n_bootstrap=args.n_bootstrap,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
    )
    print_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
