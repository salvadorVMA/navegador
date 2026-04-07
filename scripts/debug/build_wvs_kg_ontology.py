#!/usr/bin/env python3
"""
Build WVS Knowledge Graph ontology and reformatted fingerprints.

Reads:
  - wvs_construct_manifest.json      → construct nodes
  - wvs_ses_fingerprints.json        → 4D SES fingerprints
  - wvs_mex_w7_within_sweep.json     → bridge edges (significant γ pairs)
  - wvs_svs_v1.json                  → domain labels

Writes:
  - data/results/wvs_kg_ontology.json           → KG (same schema as kg_ontology_v2.json)
  - data/results/wvs_ses_fingerprints_v2.json   → fingerprints (OntologyQuery-compatible)

Usage:
    python scripts/debug/build_wvs_kg_ontology.py
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "results"
NAVEGADOR_DATA = Path("/workspaces/navegador_data") / "data" / "results"

ALL_DIMS = ("rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad")

WVS_DOMAIN_LABELS = {
    "WVS_A": "Social Values, Attitudes & Stereotypes",
    "WVS_B": "Environment",
    "WVS_C": "Work & Employment",
    "WVS_D": "Family",
    "WVS_E": "Politics & Society",
    "WVS_F": "Religion & Morale",
    "WVS_G": "National Identity",
    "WVS_H": "Security",
    "WVS_I": "Science & Technology",
}


def _fp_vec(fp: dict) -> np.ndarray:
    return np.array([fp.get(d, 0.0) for d in ALL_DIMS])


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def main():
    print("Building WVS KG ontology...")

    # ── Load sources ─────────────────────────────────────────
    manifest = json.load(open(DATA / "wvs_construct_manifest.json"))
    fp_raw = json.load(open(DATA / "wvs_ses_fingerprints.json"))
    fp_flat = fp_raw["fingerprints"]  # keyed by wvs_agg_* column

    sweep_path = NAVEGADOR_DATA / "wvs_mex_w7_within_sweep.json"
    if not sweep_path.exists():
        raise FileNotFoundError(f"Within-sweep not found: {sweep_path}")
    sweep = json.load(open(sweep_path))

    # ── Build col→key mapping ────────────────────────────────
    col_to_key = {}   # wvs_agg_col → WVS_DOM|name
    key_to_col = {}
    for c in manifest:
        col_to_key[c["column"]] = c["key"]
        key_to_col[c["key"]] = c["column"]

    # ── Build fingerprints v2 (OntologyQuery-compatible) ─────
    constructs_fp = {}
    for c in manifest:
        col = c["column"]
        key = c["key"]
        fp = fp_flat.get(col, {})
        constructs_fp[key] = {
            "rho_escol": fp.get("rho_escol", 0.0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0.0),
            "rho_sexo": fp.get("rho_sexo", 0.0),
            "rho_edad": fp.get("rho_edad", 0.0),
            "ses_magnitude": fp.get("ses_magnitude", 0.0),
            "dominant_dim": fp.get("dominant_dim", "escol"),
        }

    fp_v2 = {
        "metadata": {
            "source": fp_raw.get("source", "WVS_W7_MEX"),
            "n": fp_raw.get("n", 1741),
            "ses_vars": fp_raw.get("ses_vars", ["sexo", "edad", "escol", "Tam_loc"]),
            "generated": datetime.now().isoformat(),
        },
        "constructs": constructs_fp,
        "items": {},
        "domains": {},
    }

    fp_v2_path = DATA / "wvs_ses_fingerprints_v2.json"
    with open(fp_v2_path, "w") as f:
        json.dump(fp_v2, f, indent=2)
    print(f"  Fingerprints v2: {fp_v2_path} ({len(constructs_fp)} constructs)")

    # ── Build domain nodes ───────────────────────────────────
    domain_set = sorted({c["key"].split("|")[0] for c in manifest})
    domains = []
    for d in domain_set:
        domains.append({
            "id": d,
            "label": WVS_DOMAIN_LABELS.get(d, d),
        })

    # ── Build construct nodes (enriched with fingerprints) ───
    constructs = []
    for c in manifest:
        key = c["key"]
        domain = key.split("|")[0]
        fp = constructs_fp.get(key, {})
        constructs.append({
            "id": key,
            "label": key.split("|")[1].replace("_", " ").title(),
            "domain": domain,
            "manifest_key": key,
            "column": c["column"],
            "type": c.get("type", "unknown"),
            "alpha": c.get("alpha"),
            "n_items": c.get("n_items", 0),
            "n_valid": c.get("n_valid", 0),
            "rho_escol": fp.get("rho_escol", 0.0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0.0),
            "rho_sexo": fp.get("rho_sexo", 0.0),
            "rho_edad": fp.get("rho_edad", 0.0),
            "ses_magnitude": fp.get("ses_magnitude", 0.0),
            "dominant_dim": fp.get("dominant_dim", "escol"),
            "ses_sign": 1 if fp.get("rho_escol", 0) >= 0 else -1,
            "n_surveys": 1,
        })

    # ── Build bridge edges from within-sweep ─────────────────
    estimates = sweep["estimates"]
    bridges = []
    n_skipped_key = 0

    for sweep_key, v in estimates.items():
        if not v.get("excl_zero", False):
            continue

        # Parse: WVS_W7_MEX::wvs_agg_col_a|WVS_DOM_A::wvs_agg_col_b|WVS_DOM_B
        parts = sweep_key.split("::")
        if len(parts) != 3:
            n_skipped_key += 1
            continue

        col_a = parts[1].rsplit("|", 1)[0]
        col_b = parts[2].rsplit("|", 1)[0]

        key_a = col_to_key.get(col_a)
        key_b = col_to_key.get(col_b)
        if not key_a or not key_b:
            n_skipped_key += 1
            continue

        # Compute fingerprint alignment
        fp_a = constructs_fp.get(key_a, {})
        fp_b = constructs_fp.get(key_b, {})
        vec_a = _fp_vec(fp_a)
        vec_b = _fp_vec(fp_b)
        fp_dot = float(np.dot(vec_a, vec_b))
        fp_cos = _cosine(vec_a, vec_b)
        gamma = v["dr_gamma"]

        dot_consistent = True
        if abs(fp_dot) > 1e-8 and abs(gamma) > 1e-8:
            dot_consistent = np.sign(fp_dot) == np.sign(gamma)

        bridges.append({
            "from": key_a,
            "to": key_b,
            "gamma": round(gamma, 6),
            "ci_lo": round(v["dr_ci_lo"], 6),
            "ci_hi": round(v["dr_ci_hi"], 6),
            "ci_width": round(v["ci_width"], 6),
            "excl_zero": True,
            "nmi": round(v.get("dr_nmi", 0), 6),
            "fingerprint_dot": round(fp_dot, 6),
            "fingerprint_cos": round(fp_cos, 6),
            "dot_sign_consistent": bool(dot_consistent),
        })

    # ── Assemble KG ──────────────────────────────────────────
    kg = {
        "version": "v1_wvs",
        "dataset": "wvs_w7_mex",
        "description": "WVS Wave 7 Mexico within-survey construct knowledge graph",
        "generated": datetime.now().isoformat(),
        "metadata": {
            "n_constructs": len(constructs),
            "n_bridges": len(bridges),
            "n_domains": len(domains),
            "sweep_source": str(sweep_path),
            "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
        },
        "domains": domains,
        "constructs": constructs,
        "relationships": [],
        "bridges": bridges,
    }

    kg_path = DATA / "wvs_kg_ontology.json"
    with open(kg_path, "w") as f:
        json.dump(kg, f, indent=2)

    # ── Summary ──────────────────────────────────────────────
    print(f"  KG: {kg_path}")
    print(f"    Domains: {len(domains)}")
    print(f"    Constructs: {len(constructs)}")
    print(f"    Bridges: {len(bridges)} (skipped {n_skipped_key} unmappable keys)")

    # Consistency check
    consistent = sum(1 for b in bridges if b["dot_sign_consistent"])
    print(f"    Fingerprint-gamma sign consistency: {consistent}/{len(bridges)}"
          f" ({consistent/len(bridges)*100:.1f}%)")

    gammas = [abs(b["gamma"]) for b in bridges]
    print(f"    |gamma| median: {np.median(gammas):.4f}, max: {np.max(gammas):.4f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
