#!/usr/bin/env python3
"""
Build per-country per-wave WVS Knowledge Graph ontologies.

Each (country, wave) pair gets its own KG + fingerprints, built from:
  - That country's weight matrix (γ values from the allwave sweep)
  - That country's SES fingerprints (Spearman ρ from respondent microdata)
  - Significance from the all-wave γ-surface (excl_zero per estimate)

Outputs:
  data/results/wvs_kg/W{N}/{COUNTRY}_kg.json
  data/results/wvs_kg/W{N}/{COUNTRY}_fp.json

Usage:
    python scripts/debug/build_wvs_kg_per_wave.py                      # all waves, all countries
    python scripts/debug/build_wvs_kg_per_wave.py --waves 5 7          # specific waves
    python scripts/debug/build_wvs_kg_per_wave.py --waves 5 --country MEX  # single country
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DATA = ROOT / "data" / "results"
NAVEGADOR_DATA = Path("/workspaces/navegador_data")
GTE_DIR = NAVEGADOR_DATA / "data" / "gte"
ALLWAVE_MATRIX_DIR = NAVEGADOR_DATA / "data" / "tda" / "allwave" / "matrices"

ALL_DIMS = ("rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad")
VALID_WAVES = [3, 4, 5, 6, 7]

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


def _load_significance_index(surface: dict, wave: int, country: str) -> dict:
    """Extract per-pair significance from the all-wave γ-surface.

    Returns {(col_a, col_b): {excl_zero, gamma, ci_lo, ci_hi, ci_width, nmi}}.
    """
    prefix = f"WVS_W{wave}_{country}::"
    pairs = {}
    for k, v in surface["estimates"].items():
        if not k.startswith(prefix):
            continue
        parts = k.split("::")
        if len(parts) != 3:
            continue
        col_a = parts[1].rsplit("|", 1)[0]  # "wvs_agg_name"
        col_b = parts[2].rsplit("|", 1)[0]
        pair = tuple(sorted([col_a, col_b]))
        pairs[pair] = {
            "excl_zero": v.get("excl_zero", False),
            "gamma": v["dr_gamma"],
            "ci_lo": v.get("dr_ci_lo", 0),
            "ci_hi": v.get("dr_ci_hi", 0),
            "ci_width": v.get("ci_width", 0),
            "nmi": v.get("dr_nmi", 0),
        }
    return pairs


def build_country_kg(
    wave: int,
    country: str,
    surface: dict,
) -> tuple[dict, dict] | None:
    """Build KG + fingerprints for one (country, wave) pair.

    Returns (kg_dict, fp_v2_dict) or None if data is missing.
    """
    # Load weight matrix
    matrix_path = ALLWAVE_MATRIX_DIR / f"W{wave}" / f"{country}.csv"
    if not matrix_path.exists():
        return None
    df = pd.read_csv(matrix_path, index_col=0)
    labels = list(df.columns)  # "name|WVS_DOM" format
    W = df.values.astype(np.float64)
    k = W.shape[0]

    # Load fingerprints
    fp_path = GTE_DIR / f"W{wave}" / "fingerprints" / f"{country}.json"
    if not fp_path.exists():
        return None
    fp_raw = json.load(open(fp_path))
    fp_constructs = fp_raw.get("constructs", {})

    # Build col→key mappings
    # Matrix labels: "name|WVS_DOM" → KG key: "WVS_DOM|name"
    label_to_key = {}
    label_to_col = {}
    for label in labels:
        name, domain = label.split("|")
        kg_key = f"{domain}|{name}"
        col = f"wvs_agg_{name}"
        label_to_key[label] = kg_key
        label_to_col[label] = col

    # Build significance index from γ-surface
    sig_index = _load_significance_index(surface, wave, country)

    # Build fingerprints v2 (OntologyQuery-compatible)
    constructs_fp = {}
    for label in labels:
        kg_key = label_to_key[label]
        name = label.split("|")[0]
        fp = fp_constructs.get(name, {})
        constructs_fp[kg_key] = {
            "rho_escol": fp.get("rho_escol", 0.0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0.0),
            "rho_sexo": fp.get("rho_sexo", 0.0),
            "rho_edad": fp.get("rho_edad", 0.0),
            "ses_magnitude": fp.get("ses_magnitude", 0.0),
            "dominant_dim": fp.get("dominant_dim", "escol"),
        }

    fp_v2 = {
        "metadata": {
            "source": f"WVS_W{wave}_{country}",
            "country": country,
            "wave": wave,
            "n_respondents": fp_raw.get("n_respondents", 0),
            "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
            "generated": datetime.now().isoformat(),
        },
        "constructs": constructs_fp,
        "items": {},
        "domains": {},
    }

    # Build domain nodes
    domain_set = sorted({label.split("|")[1] for label in labels})
    domains = [{"id": d, "label": WVS_DOMAIN_LABELS.get(d, d)} for d in domain_set]

    # Build construct nodes
    constructs = []
    for label in labels:
        kg_key = label_to_key[label]
        domain = label.split("|")[1]
        fp = constructs_fp.get(kg_key, {})
        constructs.append({
            "id": kg_key,
            "label": label.split("|")[0].replace("_", " ").title(),
            "domain": domain,
            "column": label_to_col[label],
            "rho_escol": fp.get("rho_escol", 0.0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0.0),
            "rho_sexo": fp.get("rho_sexo", 0.0),
            "rho_edad": fp.get("rho_edad", 0.0),
            "ses_magnitude": fp.get("ses_magnitude", 0.0),
            "dominant_dim": fp.get("dominant_dim", "escol"),
            "ses_sign": 1 if fp.get("rho_escol", 0) >= 0 else -1,
        })

    # Build bridge edges from weight matrix + significance
    bridges = []
    for i in range(k):
        for j in range(i + 1, k):
            gamma = W[i, j]
            if np.isnan(gamma) or gamma == 0.0:
                continue

            col_a = label_to_col[labels[i]]
            col_b = label_to_col[labels[j]]
            pair = tuple(sorted([col_a, col_b]))
            sig = sig_index.get(pair)

            # Use significance from γ-surface if available
            excl_zero = sig["excl_zero"] if sig else False
            ci_lo = sig["ci_lo"] if sig else 0.0
            ci_hi = sig["ci_hi"] if sig else 0.0
            ci_width = sig["ci_width"] if sig else 0.0
            nmi = sig["nmi"] if sig else 0.0

            if not excl_zero:
                continue

            key_a = label_to_key[labels[i]]
            key_b = label_to_key[labels[j]]

            # Fingerprint alignment
            fp_a = constructs_fp.get(key_a, {})
            fp_b = constructs_fp.get(key_b, {})
            vec_a, vec_b = _fp_vec(fp_a), _fp_vec(fp_b)
            fp_dot = float(np.dot(vec_a, vec_b))
            fp_cos = _cosine(vec_a, vec_b)

            dot_consistent = True
            if abs(fp_dot) > 1e-8 and abs(gamma) > 1e-8:
                dot_consistent = np.sign(fp_dot) == np.sign(gamma)

            bridges.append({
                "from": key_a,
                "to": key_b,
                "gamma": round(float(gamma), 6),
                "ci_lo": round(float(ci_lo), 6),
                "ci_hi": round(float(ci_hi), 6),
                "ci_width": round(float(ci_width), 6),
                "excl_zero": True,
                "nmi": round(float(nmi), 6),
                "fingerprint_dot": round(fp_dot, 6),
                "fingerprint_cos": round(fp_cos, 6),
                "dot_sign_consistent": bool(dot_consistent),
            })

    kg = {
        "version": f"v2_wvs_w{wave}_{country}",
        "dataset": f"wvs_w{wave}_{country.lower()}",
        "description": f"WVS Wave {wave} {country}: {len(constructs)} constructs, "
                       f"{len(bridges)} bridges",
        "generated": datetime.now().isoformat(),
        "metadata": {
            "wave": wave,
            "country": country,
            "year": {3: 1996, 4: 2000, 5: 2007, 6: 2012, 7: 2018}.get(wave),
            "n_constructs": len(constructs),
            "n_bridges": len(bridges),
            "n_domains": len(domains),
            "n_respondents": fp_raw.get("n_respondents", 0),
            "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
        },
        "domains": domains,
        "constructs": constructs,
        "relationships": [],
        "bridges": bridges,
    }

    return kg, fp_v2


def run_wave(wave: int, country: str | None, surface: dict) -> None:
    """Build KGs for one wave (all countries or single)."""
    manifest_path = ALLWAVE_MATRIX_DIR / f"W{wave}" / "manifest.json"
    if not manifest_path.exists():
        print(f"  W{wave}: no manifest found")
        return
    manifest = json.load(open(manifest_path))
    all_countries = sorted(manifest["countries"])
    countries = [country] if country else all_countries

    out_dir = DATA / "wvs_kg" / f"W{wave}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  W{wave}: {len(countries)} countries, {manifest['n_constructs']} constructs")

    n_ok = 0
    total_bridges = 0
    for i, c in enumerate(countries):
        result = build_country_kg(wave, c, surface)
        if result is None:
            continue
        kg, fp_v2 = result

        with open(out_dir / f"{c}_kg.json", "w") as f:
            json.dump(kg, f, indent=2)
        with open(out_dir / f"{c}_fp.json", "w") as f:
            json.dump(fp_v2, f, indent=2)

        n_bridges = kg["metadata"]["n_bridges"]
        total_bridges += n_bridges
        n_ok += 1

        if (i + 1) % 10 == 0 or i == 0 or len(countries) <= 5:
            print(f"    [{i+1}/{len(countries)}] {c}: {n_bridges} bridges")

    print(f"  W{wave}: {n_ok}/{len(countries)} countries, {total_bridges} total bridges")


def main():
    parser = argparse.ArgumentParser(
        description="Build per-country per-wave WVS KG ontologies")
    parser.add_argument("--waves", type=int, nargs="+", default=VALID_WAVES,
                        help=f"Waves to build (default: {VALID_WAVES})")
    parser.add_argument("--country", default=None,
                        help="Single country code (default: all)")
    args = parser.parse_args()

    print("Loading all-wave γ-surface...")
    surface_path = NAVEGADOR_DATA / "data" / "results" / "wvs_all_wave_gamma_surface.json"
    surface = json.load(open(surface_path))
    print(f"  {len(surface['estimates'])} estimates")

    for wave in sorted(args.waves):
        run_wave(wave, args.country, surface)

    print("\nDone.")


if __name__ == "__main__":
    main()
