"""
GTE Cross-Wave Analysis
========================

Analyzes how SES-mediated attitude structure evolves across WVS waves 3-7
(1996-2018). Reads pre-computed camps, fingerprints, and message passing
outputs. Produces descriptive summaries, cross-wave evolution metrics,
visualizations, and a markdown report.

Usage:
    python scripts/debug/analyze_gte_allwaves.py
    python scripts/debug/analyze_gte_allwaves.py --waves 5 6 7
    python scripts/debug/analyze_gte_allwaves.py --skip-plots
    python scripts/debug/analyze_gte_allwaves.py --country MEX
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.debug.mp_utils import (
    GTE_DIR,
    NAVEGADOR_DATA,
    VALID_WAVES,
    load_manifest,
)

WAVE_YEARS = {1: 1981, 2: 1990, 3: 1996, 4: 2000, 5: 2007, 6: 2012, 7: 2018}
TDA_DIR = NAVEGADOR_DATA / "data" / "tda"
MP_DIR = TDA_DIR / "message_passing"
RESULTS_DIR = ROOT / "data" / "results"
PLOT_DIR = RESULTS_DIR / "gte_allwave_plots"

SES_DIMS = ["escol", "Tam_loc", "sexo", "edad"]
SES_COLORS = {"escol": "#2166ac", "Tam_loc": "#4dac26", "sexo": "#d53e4f", "edad": "#ff7f00"}
ZONE_COLORS = {
    "Latin America": "#e41a1c", "English-speaking": "#377eb8",
    "Protestant Europe": "#4daf4a", "Catholic Europe": "#984ea3",
    "Orthodox/ex-Communist": "#ff7f00", "Confucian": "#a65628",
    "South/Southeast Asian": "#f781bf", "African-Islamic": "#999999",
}

warnings.filterwarnings("ignore")


# ── Data loading ────────────────────────────────────────────────────────────

def _camp_dir(wave: int) -> Path:
    d = GTE_DIR / f"W{wave}" / "camps"
    if d.exists():
        return d
    if wave == 7:
        return GTE_DIR / "camps"
    return d


def _fp_dir(wave: int) -> Path:
    d = GTE_DIR / f"W{wave}" / "fingerprints"
    if d.exists():
        return d
    if wave == 7:
        return GTE_DIR / "fingerprints"
    return d


def _mp_dir(wave: int) -> Path:
    if wave == 7:
        return MP_DIR  # legacy flat dir
    return MP_DIR / f"W{wave}"


def load_camps(wave: int) -> dict[str, dict]:
    """Load all camp JSONs for a wave. Returns {country: camp_data}."""
    d = _camp_dir(wave)
    camps = {}
    for f in sorted(d.glob("*.json")):
        camps[f.stem] = json.load(open(f))
    return camps


def load_fingerprints(wave: int) -> dict[str, dict]:
    """Load all fingerprint JSONs for a wave. Returns {country: fp_data}."""
    d = _fp_dir(wave)
    fps = {}
    for f in sorted(d.glob("*.json")):
        fps[f.stem] = json.load(open(f))
    return fps


def load_bp_results(wave: int) -> dict[str, dict]:
    d = _mp_dir(wave)
    results = {}
    for f in sorted(d.glob("*_bp.json")):
        code = f.stem.replace("_bp", "")
        results[code] = json.load(open(f))
    return results


def load_spectral_results(wave: int) -> dict[str, dict]:
    d = _mp_dir(wave)
    results = {}
    for f in sorted(d.glob("*_spectral.json")):
        code = f.stem.replace("_spectral", "")
        results[code] = json.load(open(f))
    return results


def load_ppr_results(wave: int) -> dict[str, dict]:
    d = _mp_dir(wave)
    results = {}
    for f in sorted(d.glob("*_ppr.json")):
        code = f.stem.replace("_ppr", "")
        results[code] = json.load(open(f))
    return results


def get_country_zone() -> dict[str, str]:
    from wvs_metadata import COUNTRY_ZONE
    return dict(COUNTRY_ZONE)


# ── Phase A: Per-wave descriptive summary ───────────────────────────────────

def phase_a_descriptives(waves: list[int]) -> dict:
    """Compute per-wave network, camp, fingerprint, and MP summaries."""
    country_zone = get_country_zone()
    summaries = {}

    for w in waves:
        manifest = load_manifest(wave=w)
        n_constructs = manifest["n_constructs"]
        countries = sorted(manifest["countries"])

        # Camps
        camps = load_camps(w)
        fiedler_vals = [c["fiedler_value"] for c in camps.values()]
        balance_vals = [c["structural_balance"] for c in camps.values()]

        # Fingerprints
        fps = load_fingerprints(w)
        dominant_counts = Counter()
        magnitudes = []
        for fp in fps.values():
            for c_data in fp.get("constructs", {}).values():
                dominant_counts[c_data.get("dominant_dim", "?")] += 1
                magnitudes.append(c_data.get("ses_magnitude", 0))
        total_dom = sum(dominant_counts.values()) or 1

        # BP top influencers
        bp = load_bp_results(w)
        bp_top = Counter()
        for b in bp.values():
            if b.get("top_influencers"):
                bp_top[b["top_influencers"][0]["construct"]] += 1

        # Spectral
        spectral = load_spectral_results(w)
        mp_fiedler = [s["fiedler_partition"]["fiedler_value"]
                      for s in spectral.values()
                      if "fiedler_partition" in s]

        # PPR hubs
        ppr = load_ppr_results(w)
        ppr_top10 = Counter()
        for p in ppr.values():
            for entry in p.get("hub_ranking", [])[:10]:
                ppr_top10[entry["construct"]] += 1

        summaries[f"W{w}"] = {
            "wave": w,
            "year": WAVE_YEARS.get(w, "?"),
            "n_countries": len(countries),
            "n_constructs": n_constructs,
            "camp": {
                "median_fiedler": round(float(np.median(fiedler_vals)), 4) if fiedler_vals else None,
                "mean_balance": round(float(np.mean(balance_vals)), 4) if balance_vals else None,
                "fiedler_range": [round(min(fiedler_vals), 4), round(max(fiedler_vals), 4)] if fiedler_vals else None,
            },
            "fingerprint": {
                "ses_dominance": {d: round(dominant_counts[d] / total_dom, 3) for d in SES_DIMS},
                "median_magnitude": round(float(np.median(magnitudes)), 4) if magnitudes else None,
            },
            "bp": {
                "most_common_top_influencer": bp_top.most_common(1)[0] if bp_top else None,
                "n_unique_top_influencers": len(bp_top),
            },
            "spectral": {
                "median_fiedler": round(float(np.median(mp_fiedler)), 4) if mp_fiedler else None,
            },
            "ppr": {
                "top3_hubs": ppr_top10.most_common(3),
            },
        }

        print(f"  W{w} ({WAVE_YEARS.get(w, '?')}): {len(countries)} countries, "
              f"med Fiedler={summaries[f'W{w}']['camp']['median_fiedler']}, "
              f"med |SES|={summaries[f'W{w}']['fingerprint']['median_magnitude']}")

    return summaries


# ── Phase B: Cross-wave evolution ───────────────────────────────────────────

def _build_country_wave_map(waves: list[int]) -> dict[str, list[int]]:
    """Map each country to its available waves."""
    cw = {}
    for w in waves:
        d = _camp_dir(w)
        if d.exists():
            for f in d.glob("*.json"):
                cw.setdefault(f.stem, []).append(w)
    for c in cw:
        cw[c] = sorted(cw[c])
    return cw


def _common_constructs(waves: list[int]) -> list[str]:
    """Find constructs present in ALL specified waves."""
    sets = []
    for w in waves:
        m = load_manifest(wave=w)
        sets.append(set(m.get("construct_index", [])))
    if not sets:
        return []
    return sorted(set.intersection(*sets))


def phase_b_evolution(waves: list[int], focus_country: str | None = None) -> dict:
    """Cross-wave evolution analysis."""
    country_zone = get_country_zone()
    cw_map = _build_country_wave_map(waves)
    multi_wave = {c: ws for c, ws in cw_map.items() if len(ws) >= 2}

    if focus_country:
        multi_wave = {c: ws for c, ws in multi_wave.items() if c == focus_country}

    print(f"\n  Cross-wave: {len(multi_wave)} countries with 2+ waves")

    # ── Camp stability ──────────────────────────────────────────────────

    camp_data = {}  # {wave: {country: {construct: camp_name}}}
    for w in waves:
        camps = load_camps(w)
        camp_data[w] = {}
        for c, data in camps.items():
            camp_data[w][c] = {k: v["camp_name"] for k, v in data.get("constructs", {}).items()}

    camp_flips = {}  # {country: {construct: n_flips}}
    for country, ws in multi_wave.items():
        camp_flips[country] = {}
        for i in range(len(ws) - 1):
            w1, w2 = ws[i], ws[i + 1]
            c1 = camp_data.get(w1, {}).get(country, {})
            c2 = camp_data.get(w2, {}).get(country, {})
            shared = set(c1) & set(c2)
            for construct in shared:
                if c1[construct] != c2[construct]:
                    camp_flips[country][construct] = camp_flips[country].get(construct, 0) + 1

    # Aggregate: most volatile constructs
    construct_volatility = Counter()
    for flips in camp_flips.values():
        for construct, n in flips.items():
            construct_volatility[construct] += n

    # ── Fingerprint drift ───────────────────────────────────────────────

    fp_data = {}
    for w in waves:
        fp_data[w] = load_fingerprints(w)

    drift_results = {}  # {country: [{wave_pair, cosine_sim, dim_shifts}]}
    for country, ws in multi_wave.items():
        drifts = []
        for i in range(len(ws) - 1):
            w1, w2 = ws[i], ws[i + 1]
            fp1 = fp_data.get(w1, {}).get(country, {}).get("constructs", {})
            fp2 = fp_data.get(w2, {}).get(country, {}).get("constructs", {})
            shared = set(fp1) & set(fp2)
            if len(shared) < 5:
                continue

            # Build matched fingerprint matrices
            vecs1, vecs2 = [], []
            for c in sorted(shared):
                v1 = [fp1[c].get(f"rho_{d}", 0) for d in SES_DIMS]
                v2 = [fp2[c].get(f"rho_{d}", 0) for d in SES_DIMS]
                vecs1.append(v1)
                vecs2.append(v2)

            m1 = np.array(vecs1)
            m2 = np.array(vecs2)

            # Per-construct cosine similarity
            cos_sims = []
            for j in range(len(vecs1)):
                a, b = m1[j], m2[j]
                norm = np.linalg.norm(a) * np.linalg.norm(b)
                if norm > 0:
                    cos_sims.append(float(np.dot(a, b) / norm))

            # Dimension-level shift: mean |rho| change per dimension
            dim_shifts = {}
            for di, d in enumerate(SES_DIMS):
                dim_shifts[d] = round(float(np.mean(np.abs(m2[:, di]) - np.abs(m1[:, di]))), 4)

            drifts.append({
                "wave_pair": f"W{w1}→W{w2}",
                "n_shared": len(shared),
                "median_cosine": round(float(np.median(cos_sims)), 4) if cos_sims else None,
                "mean_cosine": round(float(np.mean(cos_sims)), 4) if cos_sims else None,
                "dim_shifts": dim_shifts,
            })
        drift_results[country] = drifts

    # ── Hub evolution ───────────────────────────────────────────────────

    bp_hubs = {}  # {wave: {country: top_construct}}
    ppr_hubs = {}  # {wave: {country: [top10_constructs]}}
    for w in waves:
        bp = load_bp_results(w)
        ppr = load_ppr_results(w)
        bp_hubs[w] = {}
        ppr_hubs[w] = {}
        for c, data in bp.items():
            if data.get("top_influencers"):
                bp_hubs[w][c] = data["top_influencers"][0]["construct"]
        for c, data in ppr.items():
            ppr_hubs[w][c] = [e["construct"] for e in data.get("hub_ranking", [])[:10]]

    # Track hub rank across waves for multi-wave countries
    hub_trajectories = {}  # {country: {construct: {wave: ppr_rank}}}
    for country, ws in multi_wave.items():
        hub_trajectories[country] = {}
        for w in ws:
            if country not in ppr_hubs.get(w, {}):
                continue
            for rank, construct in enumerate(ppr_hubs[w][country], 1):
                hub_trajectories[country].setdefault(construct, {})[w] = rank

    # ── Connectivity trend ──────────────────────────────────────────────

    spectral_trajectory = {}  # {country: {wave: fiedler}}
    for w in waves:
        spectral = load_spectral_results(w)
        for c, data in spectral.items():
            fv = data.get("fiedler_partition", {}).get("fiedler_value")
            if fv is not None:
                spectral_trajectory.setdefault(c, {})[w] = round(fv, 4)

    return {
        "multi_wave_countries": len(multi_wave),
        "camp_stability": {
            "most_volatile_constructs": construct_volatility.most_common(10),
            "total_flips": sum(construct_volatility.values()),
        },
        "fingerprint_drift": drift_results,
        "hub_trajectories": hub_trajectories,
        "spectral_trajectory": spectral_trajectory,
    }


# ── Phase C: Visualizations ────────────────────────────────────────────────

def phase_c_plots(waves: list[int], descriptives: dict, evolution: dict) -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    country_zone = get_country_zone()

    # 1. Fiedler heatmap
    _plot_fiedler_heatmap(waves, evolution["spectral_trajectory"], country_zone)

    # 2. SES dominance stacked bars
    _plot_ses_dominance(waves, descriptives)

    # 3. Fingerprint drift scatter
    _plot_fingerprint_drift(waves, evolution["fingerprint_drift"], country_zone)

    # 4. Camp volatility bar
    _plot_camp_volatility(evolution["camp_stability"])

    # 5. Hub rank ribbon (Mexico if available)
    _plot_hub_ribbon(waves, evolution["hub_trajectories"])

    # 6. Structural balance trajectory
    _plot_balance_trajectory(waves, country_zone)


def _plot_fiedler_heatmap(waves, spectral_traj, country_zone):
    # Collect all countries with 2+ waves
    countries = sorted(c for c, ws in spectral_traj.items() if len(ws) >= 2)
    if not countries:
        return
    # Sort by zone then country
    countries.sort(key=lambda c: (country_zone.get(c, "ZZZ"), c))

    matrix = np.full((len(countries), len(waves)), np.nan)
    for i, c in enumerate(countries):
        for j, w in enumerate(waves):
            matrix[i, j] = spectral_traj.get(c, {}).get(w, np.nan)

    fig, ax = plt.subplots(figsize=(8, max(10, len(countries) * 0.22)))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlBu_r", vmin=0.5, vmax=1.0)
    ax.set_xticks(range(len(waves)))
    ax.set_xticklabels([f"W{w}\n({WAVE_YEARS.get(w, '')})" for w in waves])
    ax.set_yticks(range(len(countries)))
    ax.set_yticklabels(countries, fontsize=6)
    ax.set_title("Fiedler Value (Algebraic Connectivity) by Country × Wave")
    plt.colorbar(im, ax=ax, label="Fiedler value", shrink=0.5)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "fiedler_heatmap.png", dpi=150)
    plt.close(fig)
    print(f"  Saved fiedler_heatmap.png")


def _plot_ses_dominance(waves, descriptives):
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(waves))
    bottom = np.zeros(len(waves))
    for d in SES_DIMS:
        vals = [descriptives.get(f"W{w}", {}).get("fingerprint", {}).get("ses_dominance", {}).get(d, 0)
                for w in waves]
        ax.bar(x, vals, bottom=bottom, label=d, color=SES_COLORS[d], width=0.6)
        bottom += np.array(vals)
    ax.set_xticks(x)
    ax.set_xticklabels([f"W{w} ({WAVE_YEARS.get(w, '')})" for w in waves])
    ax.set_ylabel("Fraction of construct-country pairs")
    ax.set_title("SES Dimension Dominance Across Waves")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "ses_dominance_stacked.png", dpi=150)
    plt.close(fig)
    print(f"  Saved ses_dominance_stacked.png")


def _plot_fingerprint_drift(waves, drift_results, country_zone):
    # Collect all adjacent-wave cosine similarities
    points = []  # (wave_pair_label, cosine, zone)
    for country, drifts in drift_results.items():
        zone = country_zone.get(country, "Unknown")
        for d in drifts:
            if d["median_cosine"] is not None:
                points.append((d["wave_pair"], d["median_cosine"], zone))

    if not points:
        return

    # Group by wave pair
    pairs = sorted(set(p[0] for p in points))
    fig, ax = plt.subplots(figsize=(10, 5))
    for pair_idx, pair in enumerate(pairs):
        for wp, cos, zone in points:
            if wp == pair:
                ax.scatter(pair_idx + np.random.uniform(-0.15, 0.15), cos,
                           c=ZONE_COLORS.get(zone, "#999999"), s=20, alpha=0.6,
                           edgecolors="none")
    ax.set_xticks(range(len(pairs)))
    ax.set_xticklabels(pairs, fontsize=9)
    ax.set_ylabel("Median cosine similarity (fingerprint)")
    ax.set_title("Fingerprint Stability Between Adjacent Waves")
    ax.axhline(0, color="gray", lw=0.5, ls="--")
    ax.set_ylim(-0.5, 1.0)
    # Legend
    for zone, color in ZONE_COLORS.items():
        ax.scatter([], [], c=color, s=30, label=zone)
    ax.legend(fontsize=6, loc="lower left", ncol=2)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "fingerprint_drift_scatter.png", dpi=150)
    plt.close(fig)
    print(f"  Saved fingerprint_drift_scatter.png")


def _plot_camp_volatility(camp_stability):
    top = camp_stability["most_volatile_constructs"][:15]
    if not top:
        return
    names = [t[0].split("|")[0][:30] for t in top]
    counts = [t[1] for t in top]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(names)), counts, color="#d53e4f")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("Total camp flips across countries and wave transitions")
    ax.set_title("Most Volatile Constructs (Camp Membership Changes)")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "camp_volatility.png", dpi=150)
    plt.close(fig)
    print(f"  Saved camp_volatility.png")


def _plot_hub_ribbon(waves, hub_trajectories):
    # Use MEX if available, else first country with most waves
    if "MEX" in hub_trajectories:
        country = "MEX"
    else:
        country = max(hub_trajectories, key=lambda c: len(hub_trajectories[c]),
                      default=None)
    if not country:
        return

    data = hub_trajectories[country]
    # Find top-5 constructs by best (lowest) rank across all waves
    best_rank = {}
    for construct, ws in data.items():
        best_rank[construct] = min(ws.values())
    top5 = sorted(best_rank, key=best_rank.get)[:5]

    fig, ax = plt.subplots(figsize=(10, 5))
    for construct in top5:
        ws = data[construct]
        x = sorted(ws.keys())
        y = [ws[w] for w in x]
        label = construct.split("|")[0][:35]
        ax.plot(x, y, "o-", label=label, markersize=5)

    ax.set_xticks(waves)
    ax.set_xticklabels([f"W{w}" for w in waves])
    ax.set_ylabel("PPR Hub Rank (1 = most influential)")
    ax.set_title(f"Hub Rank Trajectory — {country}")
    ax.invert_yaxis()
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "hub_rank_ribbon.png", dpi=150)
    plt.close(fig)
    print(f"  Saved hub_rank_ribbon.png ({country})")


def _plot_balance_trajectory(waves, country_zone):
    # Load camps per wave, compute zone-level median balance
    zone_balance = defaultdict(lambda: defaultdict(list))  # {zone: {wave: [balance]}}
    for w in waves:
        camps = load_camps(w)
        for c, data in camps.items():
            zone = country_zone.get(c, "Unknown")
            zone_balance[zone][w].append(data["structural_balance"])

    fig, ax = plt.subplots(figsize=(10, 5))
    for zone in sorted(zone_balance.keys()):
        x = sorted(zone_balance[zone].keys())
        y = [float(np.median(zone_balance[zone][w])) for w in x]
        if len(x) >= 2:
            ax.plot(x, y, "o-", label=zone, color=ZONE_COLORS.get(zone, "#999"),
                    markersize=5)
    ax.set_xticks(waves)
    ax.set_xticklabels([f"W{w}\n({WAVE_YEARS.get(w, '')})" for w in waves])
    ax.set_ylabel("Median structural balance")
    ax.set_title("Structural Balance by Cultural Zone Across Waves")
    ax.set_ylim(0.6, 1.02)
    ax.legend(fontsize=7, loc="lower left", ncol=2)
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "balance_trajectory.png", dpi=150)
    plt.close(fig)
    print(f"  Saved balance_trajectory.png")


# ── Phase D: Report ─────────────────────────────────────────────────────────

def phase_d_report(waves: list[int], descriptives: dict, evolution: dict,
                   focus_country: str | None = None) -> str:
    lines = []
    lines.append("# GTE Cross-Wave Analysis Report\n")
    lines.append(f"Waves analyzed: {', '.join(f'W{w} ({WAVE_YEARS.get(w)})' for w in waves)}\n")

    # Section 1: Per-wave summary table
    lines.append("## 1. Per-Wave Summary\n")
    lines.append("| Wave | Year | Countries | Constructs | Med Fiedler | Med Balance | Med |SES| | Top BP Hub |")
    lines.append("|------|------|-----------|-----------|------------|------------|---------|------------|")
    for w in waves:
        s = descriptives.get(f"W{w}", {})
        camp = s.get("camp", {})
        fp = s.get("fingerprint", {})
        bp = s.get("bp", {})
        top_bp = bp.get("most_common_top_influencer")
        top_str = f"{top_bp[0].split('|')[0][:25]} ({top_bp[1]})" if top_bp else "—"
        lines.append(
            f"| W{w} | {WAVE_YEARS.get(w, '?')} | {s.get('n_countries', '?')} "
            f"| {s.get('n_constructs', '?')} | {camp.get('median_fiedler', '?')} "
            f"| {camp.get('mean_balance', '?')} | {fp.get('median_magnitude', '?')} "
            f"| {top_str} |"
        )
    lines.append("")

    # SES dominance
    lines.append("### SES Dimension Dominance\n")
    lines.append("| Wave | escol | Tam_loc | sexo | edad |")
    lines.append("|------|-------|---------|------|------|")
    for w in waves:
        dom = descriptives.get(f"W{w}", {}).get("fingerprint", {}).get("ses_dominance", {})
        lines.append(f"| W{w} | {dom.get('escol', '?'):.1%} | {dom.get('Tam_loc', '?'):.1%} "
                     f"| {dom.get('sexo', '?'):.1%} | {dom.get('edad', '?'):.1%} |")
    lines.append("")

    # Section 2: Cross-wave evolution
    lines.append("## 2. Cross-Wave Evolution\n")
    lines.append(f"Countries with 2+ waves: **{evolution['multi_wave_countries']}**\n")

    # Camp stability
    lines.append("### Camp Stability\n")
    lines.append(f"Total camp flips across all countries and transitions: **{evolution['camp_stability']['total_flips']}**\n")
    lines.append("Most volatile constructs:\n")
    for construct, count in evolution["camp_stability"]["most_volatile_constructs"][:10]:
        name = construct.split("|")[0]
        lines.append(f"- {name}: {count} flips")
    lines.append("")

    # Fingerprint drift
    lines.append("### Fingerprint Drift\n")
    # Aggregate across countries
    all_cosines = defaultdict(list)
    for country, drifts in evolution["fingerprint_drift"].items():
        for d in drifts:
            if d["median_cosine"] is not None:
                all_cosines[d["wave_pair"]].append(d["median_cosine"])

    if all_cosines:
        lines.append("| Transition | Countries | Median cosine | Mean cosine | Min | Max |")
        lines.append("|-----------|-----------|--------------|------------|-----|-----|")
        for pair in sorted(all_cosines):
            vals = all_cosines[pair]
            lines.append(
                f"| {pair} | {len(vals)} | {np.median(vals):.3f} | {np.mean(vals):.3f} "
                f"| {min(vals):.3f} | {max(vals):.3f} |"
            )
    lines.append("")

    # Section 3: Mexico deep-dive (if available)
    if "MEX" in evolution["fingerprint_drift"]:
        lines.append("## 3. Mexico Deep Dive\n")
        mex_drifts = evolution["fingerprint_drift"]["MEX"]
        if mex_drifts:
            lines.append("### Fingerprint Drift\n")
            for d in mex_drifts:
                lines.append(f"**{d['wave_pair']}** ({d['n_shared']} shared constructs): "
                             f"median cosine = {d['median_cosine']}")
                shifts = d.get("dim_shifts", {})
                gaining = max(shifts, key=shifts.get) if shifts else "?"
                losing = min(shifts, key=shifts.get) if shifts else "?"
                lines.append(f"  - Gaining importance: {gaining} ({shifts.get(gaining, 0):+.4f})")
                lines.append(f"  - Losing importance: {losing} ({shifts.get(losing, 0):+.4f})")
            lines.append("")

        mex_traj = evolution["spectral_trajectory"].get("MEX", {})
        if mex_traj:
            lines.append("### Connectivity (Fiedler)\n")
            for w in sorted(mex_traj):
                lines.append(f"- W{w} ({WAVE_YEARS.get(w, '?')}): {mex_traj[w]}")
            lines.append("")

    # Section 4: Figures
    lines.append("## 4. Figures\n")
    for fname in sorted(PLOT_DIR.glob("*.png")):
        lines.append(f"![{fname.stem}](gte_allwave_plots/{fname.name})")
    lines.append("")

    report = "\n".join(lines)
    report_path = RESULTS_DIR / "gte_allwave_analysis_report.md"
    report_path.write_text(report)
    print(f"\n  Report saved → {report_path.relative_to(ROOT)}")
    return report


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GTE Cross-Wave Analysis")
    parser.add_argument("--waves", type=int, nargs="+", default=VALID_WAVES,
                        help=f"Waves to analyze (default: {VALID_WAVES})")
    parser.add_argument("--skip-plots", action="store_true",
                        help="Skip plot generation")
    parser.add_argument("--country", default=None,
                        help="Focus on a single country for cross-wave analysis")
    args = parser.parse_args()

    waves = sorted(args.waves)
    print(f"GTE Cross-Wave Analysis — Waves {waves}")

    # Phase A
    print("\n=== Phase A: Per-Wave Descriptives ===")
    descriptives = phase_a_descriptives(waves)

    # Save descriptives
    desc_path = RESULTS_DIR / "gte_allwave_descriptive.json"
    with open(desc_path, "w") as f:
        json.dump(descriptives, f, indent=2, default=str)
    print(f"  Saved → {desc_path.relative_to(ROOT)}")

    # Phase B
    print("\n=== Phase B: Cross-Wave Evolution ===")
    evolution = phase_b_evolution(waves, focus_country=args.country)

    # Save evolution (skip large hub_trajectories for JSON)
    evo_save = {k: v for k, v in evolution.items() if k != "hub_trajectories"}
    evo_path = RESULTS_DIR / "gte_crosswave_evolution.json"
    with open(evo_path, "w") as f:
        json.dump(evo_save, f, indent=2, default=str)
    print(f"  Saved → {evo_path.relative_to(ROOT)}")

    # Phase C
    if not args.skip_plots:
        print("\n=== Phase C: Visualizations ===")
        phase_c_plots(waves, descriptives, evolution)

    # Phase D
    print("\n=== Phase D: Report ===")
    phase_d_report(waves, descriptives, evolution, focus_country=args.country)

    print("\nDone.")


if __name__ == "__main__":
    main()
