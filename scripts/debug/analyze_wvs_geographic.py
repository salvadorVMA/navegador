"""
Phase 2.3 — WVS Geographic Analysis

Analyzes geographic sweep results: γ stability across countries, cultural zone
aggregation (ANOVA), Mexico in Latin American context, bipartition generalization.

Output:
  data/results/wvs_geographic_report.md
  data/results/wvs_geographic_stats.json

Run:
  conda run -n nvg_py13_env python scripts/debug/analyze_wvs_geographic.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from wvs_metadata import CULTURAL_ZONES, COUNTRY_ZONE

SWEEP_PATH  = ROOT / "data" / "results" / "wvs_geographic_sweep_w7.json"
OUTPUT_MD   = ROOT / "data" / "results" / "wvs_geographic_report.md"
OUTPUT_JSON = ROOT / "data" / "results" / "wvs_geographic_stats.json"


def parse_key(full_key: str) -> tuple[str, str, str]:
    """Parse 'WVS_W7_MEX::va::vb' → (context, va, vb)."""
    parts = full_key.split("::")
    return parts[0], parts[1], parts[2]


def pair_id(va: str, vb: str) -> str:
    """Canonical pair key (sorted)."""
    return "::".join(sorted([va, vb]))


def main():
    if not SWEEP_PATH.exists():
        print(f"ERROR: {SWEEP_PATH} not found. Run geographic sweep first.")
        sys.exit(1)

    with open(SWEEP_PATH) as f:
        data = json.load(f)
    estimates = data.get("estimates", {})
    print(f"Total estimates: {len(estimates)}")

    # ── Organize by country and pair ──────────────────────────────────────
    by_country: dict[str, dict] = defaultdict(dict)
    by_pair: dict[str, dict] = defaultdict(dict)
    countries = set()

    for key, est in estimates.items():
        if "dr_gamma" not in est:
            continue
        ctx, va, vb = parse_key(key)
        alpha3 = ctx.split("_")[2]  # WVS_W7_MEX → MEX
        countries.add(alpha3)
        pid = pair_id(va, vb)
        by_country[alpha3][pid] = est
        by_pair[pid][alpha3] = est["dr_gamma"]

    countries = sorted(countries)
    print(f"Countries: {len(countries)}")
    print(f"Unique pairs: {len(by_pair)}")

    # ── Per-country summary ───────────────────────────────────────────────
    country_stats = {}
    for c in countries:
        ests = by_country[c]
        gammas = [e["dr_gamma"] for e in ests.values()]
        n_sig = sum(1 for e in ests.values() if e.get("excl_zero", False))
        zone = COUNTRY_ZONE.get(c, "Unknown")
        country_stats[c] = {
            "n_pairs": len(gammas),
            "n_significant": n_sig,
            "pct_significant": round(100 * n_sig / max(len(gammas), 1), 1),
            "median_abs_gamma": round(float(np.median(np.abs(gammas))), 4),
            "mean_abs_gamma": round(float(np.mean(np.abs(gammas))), 4),
            "cultural_zone": zone,
        }

    # ── Per-pair γ stability across countries ─────────────────────────────
    pair_stability = {}
    for pid, country_gammas in by_pair.items():
        if len(country_gammas) < 5:
            continue  # need at least 5 countries
        vals = list(country_gammas.values())
        pair_stability[pid] = {
            "n_countries": len(vals),
            "mean_gamma": round(float(np.mean(vals)), 4),
            "std_gamma": round(float(np.std(vals)), 4),
            "range_gamma": round(float(np.max(vals) - np.min(vals)), 4),
            "sign_consistency": round(
                max(sum(1 for v in vals if v > 0), sum(1 for v in vals if v <= 0)) / len(vals), 3
            ),
        }

    # Most stable pairs (lowest CV)
    stable_pairs = sorted(
        [(pid, s) for pid, s in pair_stability.items() if abs(s["mean_gamma"]) > 0.01],
        key=lambda x: x[1]["std_gamma"] / max(abs(x[1]["mean_gamma"]), 1e-6)
    )

    # Most variable pairs
    variable_pairs = sorted(
        [(pid, s) for pid, s in pair_stability.items() if abs(s["mean_gamma"]) > 0.01],
        key=lambda x: -x[1]["std_gamma"]
    )

    # ── Cultural zone aggregation ─────────────────────────────────────────
    zone_stats = defaultdict(lambda: {"gammas": [], "countries": []})
    for c, cs in country_stats.items():
        zone = cs["cultural_zone"]
        zone_stats[zone]["gammas"].append(cs["median_abs_gamma"])
        zone_stats[zone]["countries"].append(c)

    zone_summary = {}
    for zone, zs in sorted(zone_stats.items()):
        zone_summary[zone] = {
            "n_countries": len(zs["countries"]),
            "countries": zs["countries"],
            "mean_median_abs_gamma": round(float(np.mean(zs["gammas"])), 4),
            "std_median_abs_gamma": round(float(np.std(zs["gammas"])), 4),
        }

    # ── Mexico in context ─────────────────────────────────────────────────
    mex_stats = country_stats.get("MEX", {})
    latam_countries = [c for c in countries if COUNTRY_ZONE.get(c) == "Latin America"]
    latam_gammas = [country_stats[c]["median_abs_gamma"] for c in latam_countries if c in country_stats]
    mex_rank_latam = sum(1 for g in latam_gammas if g > mex_stats.get("median_abs_gamma", 0)) + 1 if latam_gammas else None

    # ── Write report ──────────────────────────────────────────────────────
    lines = [
        "# WVS Geographic Analysis — Wave 7",
        "",
        f"**Countries:** {len(countries)} | **Pairs per country:** ~{int(np.mean([cs['n_pairs'] for cs in country_stats.values()]))}",
        "",
        "## Country Summary",
        "",
        "| Country | Zone | Pairs | Sig | %Sig | Med|γ| |",
        "|---------|------|-------|-----|------|--------|",
    ]
    for c in sorted(countries):
        cs = country_stats[c]
        lines.append(f"| {c} | {cs['cultural_zone'][:12]} | {cs['n_pairs']} | "
                     f"{cs['n_significant']} | {cs['pct_significant']}% | {cs['median_abs_gamma']} |")

    lines.extend([
        "",
        "## Cultural Zone Summary",
        "",
        "| Zone | Countries | Mean Med|γ| | SD |",
        "|------|-----------|-----------|------|",
    ])
    for zone, zs in sorted(zone_summary.items()):
        lines.append(f"| {zone} | {zs['n_countries']} | {zs['mean_median_abs_gamma']} | {zs['std_median_abs_gamma']} |")

    lines.extend([
        "",
        "## Most Stable Pairs (lowest relative variation across countries)",
        "",
        "| Pair | N_countries | Mean γ | SD γ | Range | Sign consistency |",
        "|------|-------------|--------|------|-------|-----------------|",
    ])
    for pid, s in stable_pairs[:15]:
        lines.append(f"| {pid[:60]} | {s['n_countries']} | {s['mean_gamma']} | "
                     f"{s['std_gamma']} | {s['range_gamma']} | {s['sign_consistency']} |")

    lines.extend([
        "",
        "## Most Variable Pairs (highest SD across countries)",
        "",
        "| Pair | N_countries | Mean γ | SD γ | Range |",
        "|------|-------------|--------|------|-------|",
    ])
    for pid, s in variable_pairs[:15]:
        lines.append(f"| {pid[:60]} | {s['n_countries']} | {s['mean_gamma']} | "
                     f"{s['std_gamma']} | {s['range_gamma']} |")

    if mex_stats:
        lines.extend([
            "",
            "## Mexico in Context",
            "",
            f"- Mexico median |γ|: {mex_stats.get('median_abs_gamma', '?')}",
            f"- Mexico significant pairs: {mex_stats.get('n_significant', '?')} ({mex_stats.get('pct_significant', '?')}%)",
            f"- Latin American countries: {len(latam_countries)}",
            f"- Mexico rank in LATAM: {mex_rank_latam}/{len(latam_countries)}" if mex_rank_latam else "",
        ])

    lines.extend(["", "---", f"*Generated by analyze_wvs_geographic.py*"])

    with open(OUTPUT_MD, "w") as f:
        f.write("\n".join(lines))
    print(f"Report: {OUTPUT_MD}")

    output = {
        "country_stats": country_stats,
        "zone_summary": zone_summary,
        "n_stable_pairs": len(stable_pairs),
        "n_variable_pairs": len(variable_pairs),
    }
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Stats: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
