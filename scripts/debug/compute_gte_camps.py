"""
Compute GTE camp bipartitions from weight matrices.

For each (wave, country), computes the Fiedler bipartition (spectral bisection
of the signed Laplacian), structural balance, and per-construct frustration.

Output matches the existing W7 camp format in data/gte/camps/.

Usage:
    python scripts/debug/compute_gte_camps.py --wave 5 --all
    python scripts/debug/compute_gte_camps.py --wave 5 --country MEX
    python scripts/debug/compute_gte_camps.py --all-waves
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import (
    GTE_DIR,
    VALID_WAVES,
    adjacency_mask,
    fill_nan_zero,
    load_manifest,
    load_weight_matrix,
    save_json,
)


def _find_largest_component(adj: np.ndarray) -> list[int]:
    """Return node indices of the largest connected component via BFS."""
    n = adj.shape[0]
    visited = [False] * n
    best = []
    for start in range(n):
        if visited[start]:
            continue
        comp = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if visited[node]:
                continue
            visited[node] = True
            comp.append(node)
            for j in range(n):
                if adj[node, j] and not visited[j]:
                    queue.append(j)
        if len(comp) > len(best):
            best = comp
    return sorted(best)


def compute_camps(country: str, wave: int) -> dict:
    """Compute Fiedler bipartition and structural balance for one country."""
    W, labels = load_weight_matrix(country, wave=wave)
    k = W.shape[0]

    # Build unsigned Laplacian from |W| (NaN → 0)
    W_abs = np.abs(fill_nan_zero(W))

    # Extract largest connected component (LCC) — isolated nodes (degree=0)
    # create spurious zero eigenvalues that mask the true Fiedler value.
    adj = W_abs > 0
    lcc_idx = _find_largest_component(adj)
    isolated_idx = [i for i in range(k) if i not in lcc_idx]

    # Compute Fiedler on LCC only
    W_lcc = W_abs[np.ix_(lcc_idx, lcc_idx)]
    D_lcc = np.diag(W_lcc.sum(axis=1))
    L_lcc = D_lcc - W_lcc

    eigenvalues, eigenvectors = np.linalg.eigh(L_lcc)
    fiedler_value = float(eigenvalues[1])
    fiedler_vector_lcc = eigenvectors[:, 1]

    # Sign alignment: ensure the group containing the construct with highest
    # absolute education-related fingerprint loading gets "cosmopolitan" (+1).
    # Heuristic: if any construct with "education" or "science" in its name
    # has a negative Fiedler loading, flip all signs.
    edu_keywords = {"education", "science", "university", "knowledge"}
    flip = False
    for li, gi in enumerate(lcc_idx):
        name = labels[gi].split("|")[0].lower()
        if any(kw in name for kw in edu_keywords):
            if fiedler_vector_lcc[li] < 0:
                flip = True
            break  # use first match
    if flip:
        fiedler_vector_lcc = -fiedler_vector_lcc

    # Expand Fiedler vector to full graph (isolated nodes get 0 → cosmopolitan)
    fiedler_vector = np.zeros(k)
    for li, gi in enumerate(lcc_idx):
        fiedler_vector[gi] = fiedler_vector_lcc[li]

    # Partition
    camp_ids = np.where(fiedler_vector >= 0, 1, -1)
    n_cosmopolitan = int((camp_ids == 1).sum())
    n_tradition = int((camp_ids == -1).sum())

    # Structural balance: count frustrated triangles
    mask = adjacency_mask(W)
    W_sign = np.sign(fill_nan_zero(W))
    n_triangles = 0
    n_frustrated = 0
    per_construct_triangles = np.zeros(k, dtype=int)
    per_construct_frustrated = np.zeros(k, dtype=int)

    for i in range(k):
        for j in range(i + 1, k):
            if not mask[i, j]:
                continue
            for m in range(j + 1, k):
                if not (mask[i, m] and mask[j, m]):
                    continue
                n_triangles += 1
                product = W_sign[i, j] * W_sign[i, m] * W_sign[j, m]
                is_frustrated = product < 0
                if is_frustrated:
                    n_frustrated += 1
                for node in (i, j, m):
                    per_construct_triangles[node] += 1
                    if is_frustrated:
                        per_construct_frustrated[node] += 1

    structural_balance = 1.0 - (n_frustrated / max(n_triangles, 1))

    # Confidence threshold for boundary constructs
    abs_loadings = np.abs(fiedler_vector)
    median_loading = float(np.median(abs_loadings))

    # Build per-construct output
    constructs = {}
    for i, label in enumerate(labels):
        tri = int(per_construct_triangles[i])
        frust = int(per_construct_frustrated[i])
        conf = float(abs_loadings[i])
        constructs[label] = {
            "camp_id": int(camp_ids[i]),
            "camp_name": "cosmopolitan" if camp_ids[i] == 1 else "tradition",
            "confidence": round(conf, 4),
            "frustrated_ratio": round(frust / max(tri, 1), 4),
            "n_triangles": tri,
            "is_boundary": conf < median_loading * 0.3,
        }

    return {
        "country": country,
        "wave": wave,
        "fiedler_value": round(fiedler_value, 6),
        "n_constructs": k,
        "n_lcc": len(lcc_idx),
        "n_isolated": len(isolated_idx),
        "n_cosmopolitan": n_cosmopolitan,
        "n_tradition": n_tradition,
        "n_triangles": n_triangles,
        "n_frustrated": n_frustrated,
        "structural_balance": round(structural_balance, 4),
        "constructs": constructs,
    }


def run_wave(wave: int, country: str | None = None) -> None:
    """Run camp computation for one wave (all countries or single)."""
    manifest = load_manifest(wave=wave)
    countries = [country] if country else sorted(manifest["countries"])

    out_dir = GTE_DIR / f"W{wave}" / "camps"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  GTE Camps — Wave {wave} ({len(countries)} countries)")
    print(f"  Output: {out_dir}")
    print(f"{'='*60}")

    t0 = time.time()
    for i, c in enumerate(countries):
        try:
            result = compute_camps(c, wave)
            path = out_dir / f"{c}.json"
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  [{i+1}/{len(countries)}] {c}: "
                  f"Fiedler={result['fiedler_value']:.4f}, "
                  f"balance={result['structural_balance']:.3f}, "
                  f"{result['n_cosmopolitan']}C/{result['n_tradition']}T")
        except Exception as e:
            print(f"  [{i+1}/{len(countries)}] {c}: ERROR — {e}")

    elapsed = time.time() - t0
    print(f"\n  Done W{wave} in {elapsed:.1f}s")


def main():
    parser = argparse.ArgumentParser(
        description="Compute GTE camp bipartitions from weight matrices")
    parser.add_argument("--wave", type=int, default=7, choices=VALID_WAVES,
                        help="WVS wave number (default: 7)")
    parser.add_argument("--country", default=None,
                        help="Single country code (default: all)")
    parser.add_argument("--all", action="store_true",
                        help="Run all countries for the specified wave")
    parser.add_argument("--all-waves", action="store_true",
                        help="Run all countries for waves 3-7")
    args = parser.parse_args()

    if args.all_waves:
        for w in VALID_WAVES:
            run_wave(w)
    elif args.all or args.country is None:
        run_wave(args.wave)
    else:
        run_wave(args.wave, country=args.country)


if __name__ == "__main__":
    main()
