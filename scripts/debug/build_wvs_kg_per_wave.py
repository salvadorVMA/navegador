#!/usr/bin/env python3
"""
Build per-wave WVS Knowledge Graph ontologies from the all-wave γ-surface.

For each wave, aggregates bridge estimates across countries:
- A bridge exists if >50% of countries with that pair have excl_zero=True
- Gamma is the median across significant countries
- Fingerprints come from per-wave GTE fingerprints (country-median)

Outputs per wave:
  data/results/wvs_kg_ontology_w{N}.json
  data/results/wvs_ses_fingerprints_v2_w{N}.json

Usage:
    python scripts/debug/build_wvs_kg_per_wave.py             # all waves 3-7
    python scripts/debug/build_wvs_kg_per_wave.py --waves 5 7  # specific waves
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "results"
NAVEGADOR_DATA = Path("/workspaces/navegador_data")
GTE_DIR = NAVEGADOR_DATA / "data" / "gte"

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


def _load_allwave_surface() -> dict:
    path = NAVEGADOR_DATA / "data" / "results" / "wvs_all_wave_gamma_surface.json"
    if not path.exists():
        raise FileNotFoundError(f"All-wave surface not found: {path}")
    return json.load(open(path))


def _load_wave_fingerprints(wave: int) -> dict[str, dict]:
    """Load per-country fingerprints and compute country-median per construct."""
    fp_dir = GTE_DIR / f"W{wave}" / "fingerprints"
    if not fp_dir.exists():
        return {}

    # Collect per-construct values across countries
    construct_vals = defaultdict(lambda: {d: [] for d in ALL_DIMS})
    n_respondents_total = 0

    for f in fp_dir.glob("*.json"):
        data = json.load(open(f))
        n_respondents_total += data.get("n_respondents", 0)
        for cname, cdata in data.get("constructs", {}).items():
            for d in ALL_DIMS:
                v = cdata.get(d, None)
                if v is not None:
                    construct_vals[cname][d].append(v)

    # Compute median per construct
    result = {}
    for cname, dims in construct_vals.items():
        fp = {}
        for d in ALL_DIMS:
            vals = dims[d]
            fp[d] = round(float(np.median(vals)), 6) if vals else 0.0
        mag = float(np.sqrt(np.mean([fp[d] ** 2 for d in ALL_DIMS])))
        dominant = max(ALL_DIMS, key=lambda d: abs(fp[d]))
        fp["ses_magnitude"] = round(mag, 6)
        fp["dominant_dim"] = dominant.replace("rho_", "")
        fp["n_countries"] = min(len(v) for v in dims.values())
        result[cname] = fp

    return result


def _load_manifest(wave: int) -> list[str]:
    """Get construct index from allwave TDA manifest."""
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.debug.mp_utils import load_manifest
    m = load_manifest(wave=wave)
    return m.get("construct_index", [])


def build_wave_kg(wave: int, surface: dict) -> tuple[dict, dict]:
    """Build KG and fingerprints for one wave.

    Returns (kg_dict, fp_v2_dict).
    """
    construct_index = _load_manifest(wave)
    if not construct_index:
        print(f"  W{wave}: no construct index found")
        return {}, {}

    # Build construct key mapping
    # Manifest format: "construct_name|WVS_DOM"
    # Surface key format: "WVS_W{n}_{COUNTRY}::wvs_agg_{name}|WVS_{DOM}::..."
    # We need: col_to_key mapping
    key_set = set(construct_index)  # "name|WVS_DOM"
    col_to_key = {}  # "wvs_agg_name" → "WVS_DOM|name"
    for label in construct_index:
        name, domain = label.split("|")
        col = f"wvs_agg_{name}"
        kg_key = f"{domain}|{name}"
        col_to_key[col] = kg_key

    # Filter surface to this wave
    wave_prefix = f"WVS_W{wave}_"
    wave_estimates = {}
    for k, v in surface["estimates"].items():
        ctx = v.get("context", k.split("::")[0])
        if ctx.startswith(wave_prefix):
            wave_estimates[k] = v

    # Aggregate per construct pair across countries
    # pair_key = "col_a::col_b" (sorted) → {gammas: [], excl_zeros: []}
    pair_data = defaultdict(lambda: {"gammas": [], "excl_zeros": [], "cis": []})
    for k, v in wave_estimates.items():
        parts = k.split("::")
        if len(parts) != 3:
            continue
        col_a = parts[1].rsplit("|", 1)[0]
        col_b = parts[2].rsplit("|", 1)[0]
        pair_key = "::".join(sorted([col_a, col_b]))
        pair_data[pair_key]["gammas"].append(v["dr_gamma"])
        pair_data[pair_key]["excl_zeros"].append(v.get("excl_zero", False))
        pair_data[pair_key]["cis"].append((v.get("dr_ci_lo", 0), v.get("dr_ci_hi", 0)))

    # Load country-median fingerprints
    fp_median = _load_wave_fingerprints(wave)

    # Build fingerprints v2 (OntologyQuery-compatible)
    constructs_fp = {}
    for label in construct_index:
        name, domain = label.split("|")
        kg_key = f"{domain}|{name}"
        fp = fp_median.get(name, {})
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
            "source": f"WVS_W{wave}_aggregate",
            "n_countries": len(list((GTE_DIR / f"W{wave}" / "fingerprints").glob("*.json")))
                          if (GTE_DIR / f"W{wave}" / "fingerprints").exists() else 0,
            "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
            "generated": datetime.now().isoformat(),
        },
        "constructs": constructs_fp,
        "items": {},
        "domains": {},
    }

    # Build domain nodes
    domain_set = sorted({label.split("|")[1] for label in construct_index})
    domains = [{"id": d, "label": WVS_DOMAIN_LABELS.get(d, d)} for d in domain_set]

    # Build construct nodes
    constructs = []
    for label in construct_index:
        name, domain = label.split("|")
        kg_key = f"{domain}|{name}"
        fp = constructs_fp.get(kg_key, {})
        constructs.append({
            "id": kg_key,
            "label": name.replace("_", " ").title(),
            "domain": domain,
            "manifest_key": label,
            "column": f"wvs_agg_{name}",
            "rho_escol": fp.get("rho_escol", 0.0),
            "rho_Tam_loc": fp.get("rho_Tam_loc", 0.0),
            "rho_sexo": fp.get("rho_sexo", 0.0),
            "rho_edad": fp.get("rho_edad", 0.0),
            "ses_magnitude": fp.get("ses_magnitude", 0.0),
            "dominant_dim": fp.get("dominant_dim", "escol"),
            "ses_sign": 1 if fp.get("rho_escol", 0) >= 0 else -1,
        })

    # Build bridge edges (majority-vote aggregation)
    bridges = []
    for pair_key, pd_ in pair_data.items():
        cols = pair_key.split("::")
        if len(cols) != 2:
            continue
        key_a = col_to_key.get(cols[0])
        key_b = col_to_key.get(cols[1])
        if not key_a or not key_b:
            continue

        # Majority vote: >50% of countries must have excl_zero
        n_sig = sum(pd_["excl_zeros"])
        n_total = len(pd_["excl_zeros"])
        if n_sig / max(n_total, 1) <= 0.5:
            continue

        # Median gamma across significant countries only
        sig_gammas = [g for g, e in zip(pd_["gammas"], pd_["excl_zeros"]) if e]
        if not sig_gammas:
            continue
        gamma = float(np.median(sig_gammas))

        # CI from all estimates
        all_los = [c[0] for c in pd_["cis"]]
        all_his = [c[1] for c in pd_["cis"]]

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
            "gamma": round(gamma, 6),
            "ci_lo": round(float(np.median(all_los)), 6),
            "ci_hi": round(float(np.median(all_his)), 6),
            "ci_width": round(float(np.median(all_his) - np.median(all_los)), 6),
            "excl_zero": True,
            "n_countries_sig": n_sig,
            "n_countries_total": n_total,
            "pct_sig": round(n_sig / n_total, 3),
            "nmi": 0.0,
            "fingerprint_dot": round(fp_dot, 6),
            "fingerprint_cos": round(fp_cos, 6),
            "dot_sign_consistent": bool(dot_consistent),
        })

    kg = {
        "version": f"v1_wvs_w{wave}",
        "dataset": f"wvs_w{wave}_aggregate",
        "description": f"WVS Wave {wave} ({len(constructs)} constructs, "
                       f"{len(bridges)} bridges, aggregate across countries)",
        "generated": datetime.now().isoformat(),
        "metadata": {
            "wave": wave,
            "year": {3: 1996, 4: 2000, 5: 2007, 6: 2012, 7: 2018}.get(wave),
            "n_constructs": len(constructs),
            "n_bridges": len(bridges),
            "n_domains": len(domains),
            "aggregation": "majority_vote_excl_zero_gt50pct",
            "ses_vars": ["sexo", "edad", "escol", "Tam_loc"],
        },
        "domains": domains,
        "constructs": constructs,
        "relationships": [],
        "bridges": bridges,
    }

    return kg, fp_v2


def main():
    parser = argparse.ArgumentParser(
        description="Build per-wave WVS KG ontologies from all-wave γ-surface")
    parser.add_argument("--waves", type=int, nargs="+", default=VALID_WAVES,
                        help=f"Waves to build (default: {VALID_WAVES})")
    args = parser.parse_args()

    print("Loading all-wave γ-surface...")
    surface = _load_allwave_surface()
    print(f"  {len(surface['estimates'])} estimates")

    for wave in sorted(args.waves):
        print(f"\n{'='*60}")
        print(f"  Building KG for Wave {wave}")
        print(f"{'='*60}")

        kg, fp_v2 = build_wave_kg(wave, surface)
        if not kg:
            continue

        kg_path = DATA / f"wvs_kg_ontology_w{wave}.json"
        fp_path = DATA / f"wvs_ses_fingerprints_v2_w{wave}.json"

        with open(kg_path, "w") as f:
            json.dump(kg, f, indent=2)
        with open(fp_path, "w") as f:
            json.dump(fp_v2, f, indent=2)

        n_bridges = kg["metadata"]["n_bridges"]
        n_constructs = kg["metadata"]["n_constructs"]
        consistent = sum(1 for b in kg["bridges"] if b["dot_sign_consistent"])
        pct = consistent / n_bridges * 100 if n_bridges else 0

        print(f"  Constructs: {n_constructs}")
        print(f"  Bridges: {n_bridges}")
        print(f"  Fingerprint-gamma consistency: {consistent}/{n_bridges} ({pct:.1f}%)")
        if kg["bridges"]:
            gammas = [abs(b["gamma"]) for b in kg["bridges"]]
            print(f"  |gamma| median: {np.median(gammas):.4f}, max: {np.max(gammas):.4f}")
        print(f"  Saved: {kg_path.name}, {fp_path.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
