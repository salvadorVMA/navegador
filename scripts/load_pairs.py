"""Load manifest, CSVs, and build sweep task list.

Usage (CLI):
    python scripts/load_pairs.py --dataset wvs_temporal --data-repo /content/navegador_data

Usage (import):
    from scripts.load_pairs import load_sweep_tasks
    context_dfs, sweep_tasks, config = load_sweep_tasks(
        dataset="wvs_temporal", data_repo_dir="/content/navegador_data"
    )
"""

import argparse
import json
import os
import sys

import pandas as pd


def resolve_paths(dataset: str, data_repo_dir: str) -> dict:
    """Return DATA_DIR, SWEEP_MODE, RESULTS_DIR, TDA_DIR for a given dataset."""
    if dataset == "los_mex":
        data_dir = os.path.join(data_repo_dir, "data", "julia_bridge")
        sweep_mode = "cross_domain"
    elif dataset in ("wvs", "wvs_temporal"):
        data_dir = os.path.join(data_repo_dir, "data", "julia_bridge_wvs")
        sweep_mode = "within_survey"
    else:
        raise ValueError(f"Unknown dataset: {dataset!r}")

    results_dir = os.path.join(data_repo_dir, "data", "results")
    tda_dir = os.path.join(data_repo_dir, "data", "tda")
    if not os.path.isdir(tda_dir):
        tda_dir = None

    return {
        "data_dir": data_dir,
        "sweep_mode": sweep_mode,
        "results_dir": results_dir,
        "tda_dir": tda_dir,
    }


def load_sweep_tasks(
    dataset: str,
    data_repo_dir: str,
) -> tuple:
    """Load data and build sweep tasks.

    Returns:
        context_dfs: dict[str, pd.DataFrame]
        sweep_tasks: list[dict]
        config: dict with dataset, sweep_mode, data_dir, manifest_file, pairs_file
    """
    paths = resolve_paths(dataset, data_repo_dir)
    data_dir = paths["data_dir"]
    sweep_mode = paths["sweep_mode"]

    # Auto-detect manifest and pairs files
    data_files = os.listdir(data_dir)
    manifest_file = next(
        (f for f in data_files if "manifest" in f.lower() and f.endswith(".json")),
        None,
    )
    pairs_file = next(
        (f for f in data_files if "pairs" in f.lower() and f.endswith(".csv")),
        None,
    )
    assert manifest_file, f"No manifest JSON found in {data_dir}"
    assert pairs_file, f"No pairs CSV found in {data_dir}"

    # Load manifest -> {context_key: csv_path}
    manifest_path = os.path.join(data_dir, manifest_file)
    with open(manifest_path) as f:
        manifest_raw = json.load(f)

    manifest = {}
    for key, val in manifest_raw.items():
        if isinstance(val, str):
            manifest[key] = os.path.join(data_dir, os.path.basename(val))
        elif isinstance(val, dict) and "csv_path" in val:
            manifest[key] = os.path.join(data_dir, os.path.basename(val["csv_path"]))

    # Build lazy loader — CSVs are read on demand and cached with LRU eviction
    # to avoid holding all 72 DataFrames in RAM simultaneously.
    context_csv_paths = {}
    available_contexts = []
    for ctx, csv_path in manifest.items():
        if os.path.exists(csv_path):
            context_csv_paths[ctx] = csv_path
            available_contexts.append(ctx)

    class LazyContextDFs:
        """Dict-like object that loads CSVs on demand with LRU cache."""
        def __init__(self, paths, max_cached=8):
            self._paths = paths
            self._cache = {}
            self._order = []
            self._max = max_cached

        def get(self, key, default=None):
            if key not in self._paths:
                return default
            if key in self._cache:
                self._order.remove(key)
                self._order.append(key)
                return self._cache[key]
            df = pd.read_csv(self._paths[key])
            self._cache[key] = df
            self._order.append(key)
            while len(self._cache) > self._max:
                evict = self._order.pop(0)
                del self._cache[evict]
            return df

        def __contains__(self, key):
            return key in self._paths

        def __len__(self):
            return len(self._paths)

        def items(self):
            """Iterate all contexts (loads each once, evicts as needed)."""
            for key in self._paths:
                yield key, self.get(key)

        @property
        def columns_map(self):
            """Load just column headers (cheap) for task building."""
            if not hasattr(self, '_cols'):
                self._cols = {}
                for ctx, path in self._paths.items():
                    cols = pd.read_csv(path, nrows=0).columns.tolist()
                    self._cols[ctx] = set(cols)
            return self._cols

    context_dfs = LazyContextDFs(context_csv_paths)

    print(f"Registered {len(context_dfs)} contexts (lazy loading, max 8 cached).")
    for ctx in sorted(available_contexts):
        cols = context_dfs.columns_map.get(ctx, set())
        print(f"  {ctx}: {len(cols)} cols")

    # Load pairs
    pairs_path = os.path.join(data_dir, pairs_file)
    pairs_df = pd.read_csv(pairs_path)
    pairs_list = list(zip(pairs_df["var_a"], pairs_df["var_b"]))
    print(f"\nPair templates: {len(pairs_list)}")

    # Build sweep tasks
    sweep_tasks = []

    if sweep_mode == "cross_domain":
        for var_a, var_b in pairs_list:
            parts_a = var_a.rsplit("|", 1)
            parts_b = var_b.rsplit("|", 1)
            if len(parts_a) == 2 and len(parts_b) == 2:
                domain_a, col_a = parts_a[1], parts_a[0]
                domain_b, col_b = parts_b[1], parts_b[0]
                sweep_tasks.append({
                    "key": f"{var_a}::{var_b}",
                    "context_a": domain_a, "col_a": col_a,
                    "context_b": domain_b, "col_b": col_b,
                })

    elif sweep_mode == "within_survey":
        for ctx in available_contexts:
            available_cols = context_dfs.columns_map.get(ctx, set())
            for var_a, var_b in pairs_list:
                col_a = var_a.rsplit("|", 1)[0] if "|" in var_a else var_a
                col_b = var_b.rsplit("|", 1)[0] if "|" in var_b else var_b
                if col_a in available_cols and col_b in available_cols:
                    sweep_tasks.append({
                        "key": f"{ctx}::{var_a}::{var_b}",
                        "context_a": ctx, "col_a": col_a,
                        "context_b": ctx, "col_b": col_b,
                    })

    print(f"\nSweep tasks: {len(sweep_tasks)}")
    if sweep_tasks:
        print(f"First task: {sweep_tasks[0]['key']}")

    config = {
        "dataset": dataset,
        "sweep_mode": sweep_mode,
        "data_dir": data_dir,
        "results_dir": paths["results_dir"],
        "tda_dir": paths["tda_dir"],
        "manifest_file": manifest_file,
        "pairs_file": pairs_file,
    }
    return context_dfs, sweep_tasks, config


def main():
    parser = argparse.ArgumentParser(description="Load and validate sweep tasks")
    parser.add_argument("--dataset", default="wvs_temporal",
                        choices=["los_mex", "wvs", "wvs_temporal"])
    parser.add_argument("--data-repo", default="/content/navegador_data")
    args = parser.parse_args()

    context_dfs, sweep_tasks, config = load_sweep_tasks(args.dataset, args.data_repo)
    print(f"\nConfig: {json.dumps(config, indent=2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
