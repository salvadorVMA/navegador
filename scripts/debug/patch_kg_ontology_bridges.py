"""
patch_kg_ontology_bridges.py — Update kg_ontology_v2.json bridge signs and
fingerprint_cos values using the latest ses_fingerprints.json.

When constructs are reverse-coded after the sweep:
  - Their SES fingerprint vectors flip sign (rho values negate)
  - Their bridge γ values with other constructs should also flip sign
  - The stored fingerprint_cos in each edge becomes stale

This script:
  1. Loads the new fingerprints from ses_fingerprints.json.
  2. For each bridge edge, recomputes fingerprint_cos from the new vectors.
  3. If sign(fingerprint_cos_new) != sign(gamma_old), flips gamma + CI.
  4. Writes the patched bridges back to kg_ontology_v2.json.

Usage:
    python scripts/debug/patch_kg_ontology_bridges.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FP_PATH = ROOT / "data" / "results" / "ses_fingerprints.json"
KG_PATH = ROOT / "data" / "results" / "kg_ontology_v2.json"

SES_DIMS = ["rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad"]


def _load_unit_vecs(fp: dict) -> Dict[str, np.ndarray]:
    """Return L2-normalised fingerprint vectors for all constructs."""
    constructs = fp.get("constructs", {})
    vecs: Dict[str, np.ndarray] = {}
    for key, data in constructs.items():
        v = np.array([data.get(d, 0.0) for d in SES_DIMS], dtype=float)
        norm = np.linalg.norm(v)
        if norm > 1e-12:
            vecs[key] = v / norm
        else:
            vecs[key] = v  # zero vector
    return vecs


def _patch_bridges(
    bridges: List[dict],
    unit_vecs: Dict[str, np.ndarray],
) -> Tuple[List[dict], int, int, int]:
    """
    For each bridge edge, recompute fingerprint_cos and optionally flip γ.

    Returns (patched_bridges, n_cos_updated, n_gamma_flipped, n_skipped).
    """
    patched = []
    n_cos = 0
    n_flip = 0
    n_skip = 0

    for edge in bridges:
        src = edge.get("from", "")
        tgt = edge.get("to", "")
        gamma_old = edge.get("gamma", 0.0) or edge.get("dr_gamma", 0.0)

        if not src or not tgt or gamma_old == 0.0:
            patched.append(edge)
            n_skip += 1
            continue

        va = unit_vecs.get(src)
        vb = unit_vecs.get(tgt)

        if va is None or vb is None:
            patched.append(edge)
            n_skip += 1
            continue

        cos_new = float(np.dot(va, vb))
        cos_old = edge.get("fingerprint_cos", None)

        new_edge = dict(edge)

        # Update fingerprint_cos
        if cos_old is None or abs(cos_new - cos_old) > 1e-6:
            new_edge["fingerprint_cos"] = round(cos_new, 6)
            n_cos += 1

        # Flip gamma if sign disagrees with new fingerprint dot product
        # (sign agreement between fingerprint_cos and gamma is ~99.4%)
        gamma_key = "dr_gamma" if "dr_gamma" in edge else "gamma"
        ci_lo_key = "dr_ci_lo" if "dr_ci_lo" in edge else "ci_lo"
        ci_hi_key = "dr_ci_hi" if "dr_ci_hi" in edge else "ci_hi"

        if gamma_old != 0.0 and cos_new != 0.0:
            if math.copysign(1, cos_new) != math.copysign(1, gamma_old):
                new_edge[gamma_key] = -edge[gamma_key]
                # ci_lo and ci_hi swap when sign flips
                lo = edge.get(ci_lo_key, 0.0)
                hi = edge.get(ci_hi_key, 0.0)
                new_edge[ci_lo_key] = -hi
                new_edge[ci_hi_key] = -lo
                n_flip += 1

        patched.append(new_edge)

    return patched, n_cos, n_flip, n_skip


def main() -> None:
    print("Loading ses_fingerprints.json …")
    with open(FP_PATH) as f:
        fp = json.load(f)
    unit_vecs = _load_unit_vecs(fp)
    print(f"  {len(unit_vecs)} construct vectors loaded")

    print("Loading kg_ontology_v2.json …")
    with open(KG_PATH) as f:
        kg = json.load(f)
    bridges_old = kg.get("bridges", [])
    print(f"  {len(bridges_old)} bridge edges found")

    if not bridges_old:
        print("  No bridges to patch — exiting.")
        return

    bridges_new, n_cos, n_flip, n_skip = _patch_bridges(bridges_old, unit_vecs)
    print(f"\n  fingerprint_cos updated : {n_cos}")
    print(f"  gamma sign flipped      : {n_flip}")
    print(f"  edges skipped           : {n_skip}")

    kg["bridges"] = bridges_new
    kg.setdefault("_patch_history", []).append({
        "script": "patch_kg_ontology_bridges.py",
        "reason": "RC fix after scale_audit_v1 — fingerprint_cos + gamma signs corrected",
        "n_cos_updated": n_cos,
        "n_gamma_flipped": n_flip,
    })

    with open(KG_PATH, "w") as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)
    print(f"\nPatched kg written to {KG_PATH}")


if __name__ == "__main__":
    main()
