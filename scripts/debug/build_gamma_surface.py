"""
Phase 4.1 — Build Unified γ-Surface

Combines all sweep outputs into a single γ-surface:
  gamma_surface[(construct_pair, country, wave)] = {gamma, ci_lo, ci_hi, n, excl_zero}

Sources:
  - wvs_mex_w7_within_sweep.json         (Phase 1: Mexico validation)
  - wvs_geographic_sweep_w7.json          (Phase 2: ~60 countries, Wave 7)
  - wvs_temporal_sweep_mex.json           (Phase 3: Mexico, 7 waves)
  - construct_dr_sweep_v5_julia_v4.json   (los_mex cross-survey baseline)

Output:
  data/results/gamma_surface.json

Run:
  conda run -n nvg_py13_env python scripts/debug/build_gamma_surface.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "results"

SOURCES = {
    "wvs_mex_w7_within": RESULTS / "wvs_mex_w7_within_sweep.json",
    "wvs_geographic_w7": RESULTS / "wvs_geographic_sweep_w7.json",
    "wvs_temporal_mex":  RESULTS / "wvs_temporal_sweep_mex.json",
    "losmex_construct":  RESULTS / "construct_dr_sweep_v5_julia_v4.json",
}

OUTPUT = RESULTS / "gamma_surface.json"

WAVE_YEARS = {1: 1982, 2: 1992, 3: 1996, 4: 2001, 5: 2007, 6: 2012, 7: 2018}


def parse_wvs_key(full_key: str) -> tuple[str, str, str]:
    """Parse 'WVS_W7_MEX::va::vb' → (context, va, vb)."""
    parts = full_key.split("::")
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    return "", "", ""


def pair_id(va: str, vb: str) -> str:
    return "::".join(sorted([va, vb]))


def main():
    surface = {}
    source_counts = {}

    for source_name, path in SOURCES.items():
        if not path.exists():
            print(f"  SKIP {source_name}: {path} not found")
            continue

        with open(path) as f:
            data = json.load(f)
        estimates = data.get("estimates", {})
        n_added = 0

        if source_name == "losmex_construct":
            # los_mex keys: "agg_X|DOMAIN::agg_Y|DOMAIN"
            for key, est in estimates.items():
                if "dr_gamma" not in est:
                    continue
                parts = key.split("::")
                if len(parts) != 2:
                    continue
                pid = pair_id(parts[0], parts[1])
                surface_key = f"losmex::cross_survey::{pid}"
                surface[surface_key] = {
                    "gamma": est["dr_gamma"],
                    "ci_lo": est.get("dr_ci_lo", 0),
                    "ci_hi": est.get("dr_ci_hi", 0),
                    "ci_width": est.get("ci_width", 0),
                    "excl_zero": est.get("excl_zero", False),
                    "nmi": est.get("dr_nmi", 0),
                    "source": "losmex_construct",
                    "dataset": "los_mex",
                    "country": "MEX",
                    "wave": None,
                    "year": 2015,  # los_mex fieldwork year
                    "sweep_type": "cross_survey",
                }
                n_added += 1

        else:
            # WVS keys: "WVS_Wn_XXX::va::vb"
            for key, est in estimates.items():
                if "dr_gamma" not in est:
                    continue
                ctx, va, vb = parse_wvs_key(key)
                if not ctx:
                    continue
                parts = ctx.split("_")
                wave = int(parts[1][1:])  # W7 → 7
                alpha3 = parts[2]
                pid = pair_id(va, vb)

                surface_key = f"wvs::W{wave}_{alpha3}::{pid}"
                surface[surface_key] = {
                    "gamma": est["dr_gamma"],
                    "ci_lo": est.get("dr_ci_lo", 0),
                    "ci_hi": est.get("dr_ci_hi", 0),
                    "ci_width": est.get("ci_width", 0),
                    "excl_zero": est.get("excl_zero", False),
                    "nmi": est.get("dr_nmi", 0),
                    "source": source_name,
                    "dataset": "wvs",
                    "country": alpha3,
                    "wave": wave,
                    "year": WAVE_YEARS.get(wave, 0),
                    "sweep_type": "within_survey",
                }
                n_added += 1

        source_counts[source_name] = n_added
        print(f"  {source_name}: {n_added} estimates")

    # Save
    output = {
        "metadata": {
            "description": "Unified γ-surface: γ(construct_pair, country, wave)",
            "sources": source_counts,
            "total_estimates": len(surface),
        },
        "surface": surface,
    }
    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved: {OUTPUT} ({len(surface)} entries)")


if __name__ == "__main__":
    main()
