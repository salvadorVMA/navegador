#!/usr/bin/env python3
"""
Phase 0a+0b: Compute per-country WVS SES fingerprints and bipartitions.

For each of the 66 W7 countries, reads the Julia bridge CSV and computes:
  - Per-construct Spearman ρ with each of 4 SES dimensions
  - SES magnitude (RMS of 4 ρ values)
  - Dominant SES dimension
  - Signed Laplacian bipartition (camps) from weight matrices

Inputs:
  - data/julia_bridge_wvs/WVS_W7_{ALPHA3}.csv   (respondent-level microdata)
  - data/tda/matrices/{ALPHA3}.csv                (55×55 weight matrices)
  - data/tda/matrices/manifest.json               (construct index)

Outputs:
  - data/gte/fingerprints/{ALPHA3}.json           (per-construct fingerprints)
  - data/gte/camps/{ALPHA3}.json                  (bipartition + frustrated triangles)
  - data/gte/fingerprints_summary.json            (cross-country summary stats)

Usage:
  python scripts/debug/compute_wvs_country_fingerprints.py [--country MEX] [--all]
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.sparse.linalg import eigsh

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
BRIDGE_DIR = ROOT / "data" / "julia_bridge_wvs"
MATRIX_DIR = ROOT / "data" / "tda" / "matrices"
OUT_FP_DIR = ROOT / "data" / "gte" / "fingerprints"
OUT_CAMP_DIR = ROOT / "data" / "gte" / "camps"
MANIFEST_PATH = MATRIX_DIR / "manifest.json"

SES_DIMS = ["escol", "Tam_loc", "sexo", "edad"]
CONSTRUCT_PREFIX = "wvs_agg_"


# ── Fingerprint Computation ────────────────────────────────────────────────

def compute_fingerprints(df: pd.DataFrame) -> dict:
    """
    Compute SES fingerprints for all constructs in a country's microdata.

    For each construct column (wvs_agg_*), computes Spearman ρ against each
    of the 4 SES dimensions. Rows with NaN in either variable are dropped
    per pair (pairwise complete).

    Returns dict: construct_key → {rho_escol, rho_Tam_loc, rho_sexo, rho_edad,
                                    ses_magnitude, dominant_dim, n_valid}
    """
    # Identify construct columns
    agg_cols = [c for c in df.columns if c.startswith(CONSTRUCT_PREFIX)]
    fingerprints = {}

    for col in agg_cols:
        # Strip prefix to get construct name
        construct_name = col[len(CONSTRUCT_PREFIX):]
        fp = {}
        rhos = []

        for dim in SES_DIMS:
            if dim not in df.columns:
                fp[f"rho_{dim}"] = None
                continue
            # Pairwise complete: drop rows where either is NaN
            mask = df[[col, dim]].notna().all(axis=1)
            n_valid = mask.sum()
            if n_valid < 30:
                # Too few observations for reliable ρ
                fp[f"rho_{dim}"] = None
                continue
            rho, _ = stats.spearmanr(df.loc[mask, col], df.loc[mask, dim])
            fp[f"rho_{dim}"] = round(float(rho), 6)
            rhos.append(rho)

        # SES magnitude = RMS of available ρ values
        if rhos:
            fp["ses_magnitude"] = round(float(np.sqrt(np.mean(np.array(rhos)**2))), 6)
            # Dominant dimension = highest |ρ|
            dim_rhos = {d: abs(fp.get(f"rho_{d}", 0) or 0) for d in SES_DIMS}
            fp["dominant_dim"] = max(dim_rhos, key=dim_rhos.get)
        else:
            fp["ses_magnitude"] = 0.0
            fp["dominant_dim"] = None

        fp["n_valid"] = int(df[col].notna().sum())
        fingerprints[construct_name] = fp

    return fingerprints


# ── Bipartition Computation ────────────────────────────────────────────────

def compute_bipartition(weight_matrix: pd.DataFrame, fingerprints: dict) -> dict:
    """
    Compute signed Laplacian bipartition from a country's weight matrix.

    The Fiedler vector of L_s = D_{|W|} - W partitions constructs into two
    camps. Orientation: camp +1 has higher median rho_escol (cosmopolitan).

    Also computes frustrated triangle ratio per node (sign-inconsistent
    triangles as fraction of total).

    Returns dict with camps, confidence, frustrated_ratio, fiedler_value.
    """
    W = weight_matrix.values.astype(float)
    labels = list(weight_matrix.columns)
    n = len(labels)

    # Replace NaN with 0 for Laplacian computation (no edge)
    W_clean = np.nan_to_num(W, nan=0.0)

    # Signed Laplacian: L_s = D_{|W|} - W
    D = np.diag(np.abs(W_clean).sum(axis=1))
    L_s = D - W_clean

    # Fiedler vector (second-smallest eigenvalue of L_s)
    # Use shift-invert mode for smallest eigenvalues
    try:
        eigenvalues, eigenvectors = eigsh(L_s, k=2, which="SM")
        fiedler_idx = 1  # second-smallest
        fiedler_value = float(eigenvalues[fiedler_idx])
        fiedler_vec = eigenvectors[:, fiedler_idx]
    except Exception:
        # Fallback: full eigendecomposition for small matrices
        eigenvalues, eigenvectors = np.linalg.eigh(L_s)
        fiedler_idx = 1
        fiedler_value = float(eigenvalues[fiedler_idx])
        fiedler_vec = eigenvectors[:, fiedler_idx]

    # Assign camps: sign of Fiedler vector
    raw_camps = np.sign(fiedler_vec)
    raw_camps[raw_camps == 0] = 1  # tie-break

    # Orient: camp +1 should have higher median rho_escol (cosmopolitan)
    camp_plus = [labels[i] for i in range(n) if raw_camps[i] > 0]
    camp_minus = [labels[i] for i in range(n) if raw_camps[i] < 0]

    # Strip domain suffix for fingerprint lookup
    def strip_domain(label):
        """'gender_role_traditionalism|WVS_D' → 'gender_role_traditionalism'"""
        return label.split("|")[0] if "|" in label else label

    def median_rho_escol(camp_labels):
        vals = []
        for lbl in camp_labels:
            key = strip_domain(lbl)
            if key in fingerprints:
                r = fingerprints[key].get("rho_escol")
                if r is not None:
                    vals.append(r)
        return np.median(vals) if vals else 0.0

    if median_rho_escol(camp_minus) > median_rho_escol(camp_plus):
        # Flip orientation
        raw_camps = -raw_camps

    # Confidence: normalized absolute Fiedler component
    max_fiedler = np.max(np.abs(fiedler_vec)) or 1.0
    confidence = np.abs(fiedler_vec) / max_fiedler

    # Frustrated triangle counting
    # A triangle (i,j,k) is frustrated if sign(W_ij) * sign(W_jk) * sign(W_ik) < 0
    sign_W = np.sign(W_clean)
    # Only count edges that actually exist (non-zero weight)
    has_edge = np.abs(W_clean) > 0

    frustrated_ratio = {}
    n_triangles = {}
    for i in range(n):
        total = 0
        frustrated = 0
        for j in range(n):
            if j == i or not has_edge[i, j]:
                continue
            for k in range(j + 1, n):
                if k == i or not has_edge[i, k] or not has_edge[j, k]:
                    continue
                total += 1
                parity = sign_W[i, j] * sign_W[j, k] * sign_W[i, k]
                if parity < 0:
                    frustrated += 1
        label = labels[i]
        n_triangles[label] = total
        frustrated_ratio[label] = round(frustrated / total, 4) if total > 0 else 0.0

    # Build output
    camps = {}
    for i, label in enumerate(labels):
        camps[label] = {
            "camp_id": int(raw_camps[i]),
            "camp_name": "cosmopolitan" if raw_camps[i] > 0 else "tradition",
            "confidence": round(float(confidence[i]), 4),
            "frustrated_ratio": frustrated_ratio.get(label, 0.0),
            "n_triangles": n_triangles.get(label, 0),
            "is_boundary": frustrated_ratio.get(label, 0.0) > 0.10,
        }

    # Camp summary
    plus_labels = [labels[i] for i in range(n) if raw_camps[i] > 0]
    minus_labels = [labels[i] for i in range(n) if raw_camps[i] < 0]
    total_tris = sum(n_triangles.values()) // 3  # each triangle counted 3×
    total_frust = sum(
        1 for i in range(n) for j in range(i+1, n) for k in range(j+1, n)
        if has_edge[i,j] and has_edge[j,k] and has_edge[i,k]
        and sign_W[i,j] * sign_W[j,k] * sign_W[i,k] < 0
    )

    return {
        "fiedler_value": round(fiedler_value, 6),
        "n_cosmopolitan": len(plus_labels),
        "n_tradition": len(minus_labels),
        "n_triangles": total_tris,
        "n_frustrated": total_frust,
        "structural_balance": round(1.0 - total_frust / total_tris, 4) if total_tris > 0 else 1.0,
        "constructs": camps,
    }


# ── Main Pipeline ──────────────────────────────────────────────────────────

def process_country(alpha3: str, construct_index: list[str]) -> dict:
    """Process a single country: fingerprints + bipartition."""

    # ── Step 1: Fingerprints from microdata ──
    csv_path = BRIDGE_DIR / f"WVS_W7_{alpha3}.csv"
    if not csv_path.exists():
        return {"error": f"No microdata CSV: {csv_path}"}

    df = pd.read_csv(csv_path)
    fingerprints = compute_fingerprints(df)

    # Save fingerprints
    OUT_FP_DIR.mkdir(parents=True, exist_ok=True)
    fp_path = OUT_FP_DIR / f"{alpha3}.json"
    with open(fp_path, "w") as f:
        json.dump({
            "country": alpha3,
            "wave": 7,
            "n_constructs": len(fingerprints),
            "n_respondents": len(df),
            "constructs": fingerprints,
        }, f, indent=2)

    # ── Step 2: Bipartition from weight matrix ──
    matrix_path = MATRIX_DIR / f"{alpha3}.csv"
    if not matrix_path.exists():
        return {"fingerprints": len(fingerprints), "camps": "no weight matrix"}

    W = pd.read_csv(matrix_path, index_col=0)
    camps = compute_bipartition(W, fingerprints)

    OUT_CAMP_DIR.mkdir(parents=True, exist_ok=True)
    camp_path = OUT_CAMP_DIR / f"{alpha3}.json"
    with open(camp_path, "w") as f:
        json.dump({"country": alpha3, "wave": 7, **camps}, f, indent=2)

    return {
        "fingerprints": len(fingerprints),
        "fiedler": camps["fiedler_value"],
        "balance": camps["structural_balance"],
    }


def main():
    parser = argparse.ArgumentParser(description="Compute WVS per-country fingerprints and bipartitions")
    parser.add_argument("--country", type=str, help="Single country (ISO Alpha-3)")
    parser.add_argument("--all", action="store_true", help="Process all 66 W7 countries")
    args = parser.parse_args()

    if not args.country and not args.all:
        parser.print_help()
        sys.exit(1)

    # Load manifest for construct index
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    construct_index = manifest["construct_index"]
    countries = manifest["countries"]

    if args.country:
        countries = [args.country.upper()]

    print(f"Processing {len(countries)} countries, {len(construct_index)} constructs")
    t0 = time.time()
    results = {}

    for i, alpha3 in enumerate(countries):
        t1 = time.time()
        result = process_country(alpha3, construct_index)
        dt = time.time() - t1
        results[alpha3] = result
        status = f"fp={result.get('fingerprints', '?')}"
        if "fiedler" in result:
            status += f" fiedler={result['fiedler']:.3f} balance={result['balance']:.1%}"
        print(f"  [{i+1}/{len(countries)}] {alpha3}: {status} ({dt:.1f}s)")

    # Save summary
    summary = {
        "n_countries": len(results),
        "wave": 7,
        "ses_dims": SES_DIMS,
        "countries": results,
    }
    summary_path = OUT_FP_DIR / "fingerprints_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    dt_total = time.time() - t0
    n_ok = sum(1 for r in results.values() if "error" not in r)
    print(f"\nDone: {n_ok}/{len(countries)} countries in {dt_total:.1f}s")
    print(f"Fingerprints: {OUT_FP_DIR}/")
    print(f"Camps: {OUT_CAMP_DIR}/")


if __name__ == "__main__":
    main()
