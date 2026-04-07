#!/usr/bin/env python3
"""
WVS Ontology & Prediction Engine Readiness Diagnostic

Assesses whether WVS data can support an ontology + prediction engine
equivalent to the los_mex system. Outputs JSON + markdown report.

Usage:
    python scripts/debug/diagnostic_wvs_ontology_readiness.py
"""
import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "results"
TDA = ROOT / "data" / "tda"
NAVEGADOR_DATA = Path("/workspaces/navegador_data") / "data" / "results"

ALL_DIMS = ("rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad")


# ─── Helpers ──────────────────────────────────────────────────────────

def _fp_vec(fp: dict) -> np.ndarray:
    return np.array([fp[d] for d in ALL_DIMS])


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _percentiles(vals, ps=(10, 25, 50, 75, 90, 95, 99)):
    arr = np.array(vals)
    return {f"p{p}": round(float(np.percentile(arr, p)), 6) for p in ps}


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _parse_sweep_key(key):
    """Parse WVS sweep key → (context, col_a, domain_a, col_b, domain_b)."""
    parts = key.split("::")
    if len(parts) == 3:
        ctx, pair_a, pair_b = parts
    else:
        ctx, pair_a, pair_b = None, parts[0], parts[1]
    col_a, dom_a = pair_a.rsplit("|", 1)
    col_b, dom_b = pair_b.rsplit("|", 1)
    return ctx, col_a, dom_a, col_b, dom_b


# ─── Section 1: WVS Construct Quality ─────────────────────────────────

def check_construct_coverage():
    manifest = _load_json(DATA / "wvs_construct_manifest.json")
    types = Counter(c["type"] for c in manifest)
    alphas = [c["alpha"] for c in manifest if c.get("alpha") is not None]
    alpha_good = sum(1 for a in alphas if a >= 0.7)
    alpha_quest = sum(1 for a in alphas if 0.5 <= a < 0.7)
    alpha_poor = sum(1 for a in alphas if a < 0.5)

    # Domain coverage
    domains = Counter(c["key"].split("|")[0] for c in manifest)

    return {
        "n_constructs": len(manifest),
        "type_distribution": dict(types),
        "n_with_alpha": len(alphas),
        "alpha_good_gte_0.7": alpha_good,
        "alpha_questionable_0.5_0.7": alpha_quest,
        "alpha_poor_lt_0.5": alpha_poor,
        "alpha_median": round(float(np.median(alphas)), 3) if alphas else None,
        "domains": dict(domains.most_common()),
        "n_domains": len(domains),
        "comparison_losmex": "los_mex has 93 constructs across 24 domains",
    }


def check_fingerprint_quality():
    wvs_fp = _load_json(DATA / "wvs_ses_fingerprints.json")["fingerprints"]
    lm_fp_raw = _load_json(DATA / "ses_fingerprints.json")
    lm_fp = lm_fp_raw.get("constructs", {})

    wvs_mags = [fp["ses_magnitude"] for fp in wvs_fp.values()]
    lm_mags = [fp["ses_magnitude"] for fp in lm_fp.values()] if lm_fp else []

    wvs_doms = Counter(fp["dominant_dim"] for fp in wvs_fp.values())
    lm_doms = Counter(fp["dominant_dim"] for fp in lm_fp.values()) if lm_fp else {}

    return {
        "wvs_n": len(wvs_fp),
        "losmex_n": len(lm_fp),
        "wvs_ses_magnitude": {
            "median": round(float(np.median(wvs_mags)), 4),
            "mean": round(float(np.mean(wvs_mags)), 4),
            "max": round(float(np.max(wvs_mags)), 4),
            **_percentiles(wvs_mags, (25, 75)),
        },
        "losmex_ses_magnitude": {
            "median": round(float(np.median(lm_mags)), 4) if lm_mags else None,
        },
        "wvs_dominant_dim": dict(wvs_doms.most_common()),
        "losmex_dominant_dim": dict(Counter(lm_doms).most_common()),
    }


def check_construct_map_alignment():
    cmap = _load_json(DATA / "wvs_losmex_construct_map_v2.json")
    mappings = cmap["mappings"]

    wvs_fp = _load_json(DATA / "wvs_ses_fingerprints.json")["fingerprints"]
    lm_fp = _load_json(DATA / "ses_fingerprints.json").get("constructs", {})

    grade_dist = Counter(m.get("match_quality") for m in mappings)

    # Fingerprint cosine for grade-3 (near_identical) pairs
    cosines_g3 = []
    polarity_mismatches = []
    for m in mappings:
        if m.get("match_quality") != "near_identical":
            continue
        bm = m.get("best_match", {})
        lm_id = bm.get("losmex_id", "")
        # Map los_mex ID to fingerprint key: DOMAIN__name → DOMAIN|name
        lm_key = lm_id.replace("__", "|", 1)

        wvs_col = m.get("wvs_col", "")
        wvs_vec = _fp_vec(wvs_fp[wvs_col]) if wvs_col in wvs_fp else None
        lm_vec = _fp_vec(lm_fp[lm_key]) if lm_key in lm_fp else None

        if wvs_vec is not None and lm_vec is not None:
            cos = _cosine(wvs_vec, lm_vec)
            cosines_g3.append(cos)
            if bm.get("polarity") == "reversed":
                polarity_mismatches.append(m["wvs_key"])

    divergence_risks = cmap.get("divergence_risk_frequency", {})

    return {
        "n_mappings": len(mappings),
        "grade_distribution": dict(grade_dist.most_common()),
        "grade3_fingerprint_cosines": {
            "n_computable": len(cosines_g3),
            "median": round(float(np.median(cosines_g3)), 4) if cosines_g3 else None,
            "mean": round(float(np.mean(cosines_g3)), 4) if cosines_g3 else None,
            "min": round(float(np.min(cosines_g3)), 4) if cosines_g3 else None,
            "max": round(float(np.max(cosines_g3)), 4) if cosines_g3 else None,
            "negative_count": sum(1 for c in cosines_g3 if c < 0),
        },
        "polarity_mismatches": polarity_mismatches,
        "n_divergence_risk_types": len(divergence_risks),
        "top_divergence_risks": dict(
            sorted(divergence_risks.items(), key=lambda x: -x[1])[:5]
        ),
    }


# ─── Section 2: WVS Bridge Network Structure ─────────────────────────

def build_wvs_mex_bridge_network():
    """Build construct-level adjacency from MEX W7 within-survey sweep."""
    within = _load_json(NAVEGADOR_DATA / "wvs_mex_w7_within_sweep.json")
    estimates = within["estimates"]

    adj = defaultdict(list)
    n_sig = 0
    gammas = []
    ci_widths = []

    for key, v in estimates.items():
        _, col_a, dom_a, col_b, dom_b = _parse_sweep_key(key)
        g = v["dr_gamma"]
        gammas.append(g)
        ci_widths.append(v["ci_width"])

        if v["excl_zero"]:
            n_sig += 1
            edge = {
                "col_a": col_a, "col_b": col_b,
                "dom_a": dom_a, "dom_b": dom_b,
                "gamma": g,
                "ci_lo": v["dr_ci_lo"], "ci_hi": v["dr_ci_hi"],
                "ci_width": v["ci_width"],
                "nmi": v.get("dr_nmi", 0),
            }
            adj[col_a].append({**edge, "neighbor": col_b})
            adj[col_b].append({**edge, "neighbor": col_a})

    # Unique constructs in sweep
    all_constructs = set()
    for key in estimates:
        _, col_a, _, col_b, _ = _parse_sweep_key(key)
        all_constructs.add(col_a)
        all_constructs.add(col_b)

    connected = set(adj.keys())
    isolated = all_constructs - connected

    # Connected components via BFS
    visited = set()
    components = []
    for n in connected:
        if n in visited:
            continue
        comp = set()
        stack = [n]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            for e in adj[node]:
                if e["neighbor"] not in visited:
                    stack.append(e["neighbor"])
        components.append(comp)
    components.sort(key=len, reverse=True)

    # Graph metrics on giant component
    giant = components[0] if components else set()
    n_edges_giant = sum(len(adj[n]) for n in giant) // 2
    n_nodes = len(giant)
    max_edges = n_nodes * (n_nodes - 1) // 2
    density = n_edges_giant / max_edges if max_edges > 0 else 0

    # Diameter and APL via BFS from each node in giant
    def _bfs_distances(start):
        dist = {start: 0}
        queue = [start]
        i = 0
        while i < len(queue):
            node = queue[i]
            i += 1
            for e in adj[node]:
                nb = e["neighbor"]
                if nb not in dist and nb in giant:
                    dist[nb] = dist[node] + 1
                    queue.append(nb)
        return dist

    all_dists = []
    for node in giant:
        dists = _bfs_distances(node)
        all_dists.extend(dists.values())
    diameter = max(all_dists) if all_dists else 0
    apl = np.mean([d for d in all_dists if d > 0]) if all_dists else 0

    return {
        "n_total_pairs": len(estimates),
        "n_significant": n_sig,
        "sig_rate": round(n_sig / len(estimates), 4) if estimates else 0,
        "n_constructs_in_sweep": len(all_constructs),
        "n_connected": len(connected),
        "n_isolated": len(isolated),
        "isolated_list": sorted(isolated),
        "n_components": len(components),
        "giant_component_size": len(giant),
        "giant_component_edges": n_edges_giant,
        "density": round(density, 4),
        "diameter": diameter,
        "avg_path_length": round(float(apl), 3),
        "gamma_distribution": {
            "all_pairs": {
                "median_abs": round(float(np.median(np.abs(gammas))), 5),
                "mean_abs": round(float(np.mean(np.abs(gammas))), 5),
                **_percentiles(np.abs(gammas)),
            },
            "significant_only": {
                "n": n_sig,
                "median_abs": round(float(np.median([abs(g) for k, v in estimates.items()
                                                      if v["excl_zero"]
                                                      for g in [v["dr_gamma"]]])), 5),
            },
        },
        "ci_width_median": round(float(np.median(ci_widths)), 5),
        "_adj": adj,  # internal, for downstream use
        "_giant": giant,
    }


def check_fingerprint_gamma_consistency(network):
    """Check if sign(dot(fp_A, fp_B)) predicts sign(gamma) for significant edges."""
    wvs_fp = _load_json(DATA / "wvs_ses_fingerprints.json")["fingerprints"]
    adj = network["_adj"]

    seen = set()
    match = 0
    mismatch = 0
    skipped = 0

    for col, edges in adj.items():
        for e in edges:
            pair = tuple(sorted([col, e["neighbor"]]))
            if pair in seen:
                continue
            seen.add(pair)

            fp_a = wvs_fp.get(col)
            fp_b = wvs_fp.get(e["neighbor"])
            if not fp_a or not fp_b:
                skipped += 1
                continue

            dot = np.dot(_fp_vec(fp_a), _fp_vec(fp_b))
            if abs(dot) < 1e-8 or abs(e["gamma"]) < 1e-8:
                skipped += 1
                continue

            if np.sign(dot) == np.sign(e["gamma"]):
                match += 1
            else:
                mismatch += 1

    total = match + mismatch
    return {
        "total_tested": total,
        "sign_match": match,
        "sign_mismatch": mismatch,
        "skipped": skipped,
        "accuracy": round(match / total, 4) if total > 0 else None,
        "comparison_losmex": "los_mex: 99.4% (984/984 edges)",
    }


def check_camp_bipartition(network):
    """Compute signed Laplacian Fiedler bipartition for WVS bridge graph."""
    adj = network["_adj"]
    giant = network["_giant"]

    if len(giant) < 3:
        return {"error": "Giant component too small for bipartition"}

    nodes = sorted(giant)
    idx = {n: i for i, n in enumerate(nodes)}
    N = len(nodes)

    # Build signed adjacency and degree matrices
    A = np.zeros((N, N))
    seen = set()
    for n in nodes:
        for e in adj.get(n, []):
            nb = e["neighbor"]
            if nb not in idx:
                continue
            pair = tuple(sorted([n, nb]))
            if pair in seen:
                continue
            seen.add(pair)
            i, j = idx[n], idx[nb]
            A[i, j] = e["gamma"]
            A[j, i] = e["gamma"]

    D = np.diag(np.sum(np.abs(A), axis=1))
    L = D - A

    eigenvalues, eigenvectors = np.linalg.eigh(L)
    fiedler_vec = eigenvectors[:, 1]  # second smallest

    # Orient: camp +1 has higher median rho_escol
    wvs_fp = _load_json(DATA / "wvs_ses_fingerprints.json")["fingerprints"]
    pos_escol = [wvs_fp[n]["rho_escol"] for n in nodes
                 if fiedler_vec[idx[n]] > 0 and n in wvs_fp]
    neg_escol = [wvs_fp[n]["rho_escol"] for n in nodes
                 if fiedler_vec[idx[n]] <= 0 and n in wvs_fp]
    if pos_escol and neg_escol:
        if np.median(neg_escol) > np.median(pos_escol):
            fiedler_vec = -fiedler_vec

    camp = {n: (1 if fiedler_vec[idx[n]] > 0 else -1) for n in nodes}
    max_f = max(abs(fiedler_vec))
    confidence = {n: abs(fiedler_vec[idx[n]]) / max_f if max_f > 0 else 0
                  for n in nodes}

    camp_counts = Counter(camp.values())

    # Cross-camp vs within-camp edges
    cross = within = 0
    for pair in seen:
        a, b = pair
        if camp.get(a, 0) != camp.get(b, 0):
            cross += 1
        else:
            within += 1

    # Structural balance: count frustrated triangles
    n_balanced = n_frustrated = 0
    for i, ni in enumerate(nodes):
        for j in range(i + 1, N):
            if abs(A[i, j]) < 1e-8:
                continue
            for k in range(j + 1, N):
                if abs(A[i, k]) < 1e-8 or abs(A[j, k]) < 1e-8:
                    continue
                prod = np.sign(A[i, j]) * np.sign(A[i, k]) * np.sign(A[j, k])
                if prod > 0:
                    n_balanced += 1
                else:
                    n_frustrated += 1

    total_tri = n_balanced + n_frustrated
    balance_rate = n_balanced / total_tri if total_tri > 0 else 1.0

    conf_vals = list(confidence.values())
    return {
        "camp_distribution": {"+1_cosmopolitan": camp_counts.get(1, 0),
                              "-1_tradition": camp_counts.get(-1, 0)},
        "confidence_stats": {
            "median": round(float(np.median(conf_vals)), 4),
            "mean": round(float(np.mean(conf_vals)), 4),
            "min": round(float(np.min(conf_vals)), 4),
            "fraction_below_0.1": round(sum(1 for c in conf_vals if c < 0.1) / len(conf_vals), 3),
        },
        "cross_camp_edges": cross,
        "within_camp_edges": within,
        "structural_balance": round(balance_rate, 4),
        "n_triangles": total_tri,
        "fiedler_eigenvalue": round(float(eigenvalues[1]), 6),
    }


# ─── Section 3: Cross-Study Bridge Capacity ───────────────────────────

def check_geographic_consistency():
    """How many countries share significant edges for each construct pair."""
    geo = _load_json(NAVEGADOR_DATA / "wvs_geographic_sweep_w7.json")
    estimates = geo["estimates"]

    pair_countries = defaultdict(lambda: {"sig": [], "total": 0})
    for key, v in estimates.items():
        _, col_a, dom_a, col_b, dom_b = _parse_sweep_key(key)
        ctx = v.get("context", key.split("::")[0])
        country = ctx.replace("WVS_W7_", "")
        pair_key = f"{col_a}::{col_b}" if col_a < col_b else f"{col_b}::{col_a}"
        pair_countries[pair_key]["total"] += 1
        if v["excl_zero"]:
            pair_countries[pair_key]["sig"].append(country)

    # Universality analysis
    n_pairs = len(pair_countries)
    sig_counts = [len(v["sig"]) for v in pair_countries.values()]
    universal = sum(1 for s in sig_counts if s >= 33)  # >50% of 66 countries
    widespread = sum(1 for s in sig_counts if 10 <= s < 33)
    rare = sum(1 for s in sig_counts if 1 <= s < 10)
    never_sig = sum(1 for s in sig_counts if s == 0)

    # Sign consensus for widespread pairs
    sign_consensus = []
    for pk, v in pair_countries.items():
        if len(v["sig"]) < 10:
            continue
        # Count positive vs negative gammas among significant countries
        pos = neg = 0
        for key, est in estimates.items():
            _, ca, _, cb, _ = _parse_sweep_key(key)
            pair = f"{ca}::{cb}" if ca < cb else f"{cb}::{ca}"
            if pair != pk or not est["excl_zero"]:
                continue
            if est["dr_gamma"] > 0:
                pos += 1
            else:
                neg += 1
        total = pos + neg
        if total > 0:
            consensus = max(pos, neg) / total
            sign_consensus.append(consensus)

    return {
        "n_construct_pairs": n_pairs,
        "universality": {
            "universal_gte_33_countries": universal,
            "widespread_10_32": widespread,
            "rare_1_9": rare,
            "never_significant": never_sig,
        },
        "sig_countries_per_pair": {
            "median": round(float(np.median(sig_counts)), 1),
            "mean": round(float(np.mean(sig_counts)), 1),
            "max": max(sig_counts),
        },
        "sign_consensus_among_widespread": {
            "n_pairs": len(sign_consensus),
            "median": round(float(np.median(sign_consensus)), 3) if sign_consensus else None,
            "min": round(float(np.min(sign_consensus)), 3) if sign_consensus else None,
        },
    }


def check_temporal_stability():
    """Assess stability of bridge estimates across Mexico waves."""
    temp = _load_json(NAVEGADOR_DATA / "wvs_temporal_sweep_mex.json")
    estimates = temp["estimates"]

    # Group by construct pair, collect (wave, gamma)
    pair_waves = defaultdict(list)
    for key, v in estimates.items():
        _, col_a, dom_a, col_b, dom_b = _parse_sweep_key(key)
        ctx = v.get("context", key.split("::")[0])
        # Extract wave number
        wave_str = ctx.replace("WVS_W", "").split("_")[0]
        try:
            wave = int(wave_str)
        except ValueError:
            continue
        pair_key = f"{col_a}::{col_b}" if col_a < col_b else f"{col_b}::{col_a}"
        pair_waves[pair_key].append((wave, v["dr_gamma"], v["excl_zero"]))

    # Pairs present in 3+ waves
    stable_pairs = {k: v for k, v in pair_waves.items() if len(v) >= 3}

    # Sign stability
    sign_stable = 0
    for k, waves in stable_pairs.items():
        sig_gammas = [g for _, g, excl in waves if excl]
        if not sig_gammas:
            continue
        signs = [np.sign(g) for g in sig_gammas]
        if len(set(signs)) <= 1:
            sign_stable += 1

    # Trends
    trends = []
    for k, waves in stable_pairs.items():
        waves_sorted = sorted(waves)
        gammas = [g for _, g, _ in waves_sorted]
        if len(gammas) >= 3:
            # Simple linear trend: gamma per wave
            x = np.arange(len(gammas))
            slope = np.polyfit(x, gammas, 1)[0]
            trends.append(abs(slope))

    # TDA trajectory
    traj = _load_json(TDA / "temporal" / "temporal_trajectory.json")
    spectral = _load_json(TDA / "temporal" / "spectral_features.json")

    return {
        "n_total_pairs": len(pair_waves),
        "n_in_3_plus_waves": len(stable_pairs),
        "sign_stability": {
            "stable": sign_stable,
            "tested": len([k for k, v in stable_pairs.items()
                           if any(excl for _, _, excl in v)]),
        },
        "trend_magnitude": {
            "median_abs_slope": round(float(np.median(trends)), 5) if trends else None,
            "max_abs_slope": round(float(np.max(trends)), 5) if trends else None,
        },
        "tda_trajectory": traj,
        "spectral_features": spectral,
    }


def check_cross_study_fingerprint_alignment():
    """Compare WVS and los_mex fingerprints for matched construct pairs."""
    cmap = _load_json(DATA / "wvs_losmex_construct_map_v2.json")
    wvs_fp = _load_json(DATA / "wvs_ses_fingerprints.json")["fingerprints"]
    lm_fp = _load_json(DATA / "ses_fingerprints.json").get("constructs", {})

    cosines = []
    dim_agreement = 0
    n_compared = 0

    for m in cmap["mappings"]:
        if m.get("match_quality") != "near_identical":
            continue
        bm = m.get("best_match", {})
        lm_id = bm.get("losmex_id", "")
        lm_key = lm_id.replace("__", "|", 1)
        wvs_col = m.get("wvs_col", "")

        if wvs_col not in wvs_fp or lm_key not in lm_fp:
            continue

        wvs_v = _fp_vec(wvs_fp[wvs_col])
        lm_v = _fp_vec(lm_fp[lm_key])
        cos = _cosine(wvs_v, lm_v)
        cosines.append(cos)
        n_compared += 1

        # Dominant dimension agreement
        wvs_dom = wvs_fp[wvs_col]["dominant_dim"]
        lm_dom = lm_fp[lm_key]["dominant_dim"]
        if wvs_dom == lm_dom:
            dim_agreement += 1

    return {
        "n_grade3_pairs": sum(1 for m in cmap["mappings"]
                              if m.get("match_quality") == "near_identical"),
        "n_computable": n_compared,
        "fingerprint_cosine": {
            "median": round(float(np.median(cosines)), 4) if cosines else None,
            "mean": round(float(np.mean(cosines)), 4) if cosines else None,
            "min": round(float(np.min(cosines)), 4) if cosines else None,
            "max": round(float(np.max(cosines)), 4) if cosines else None,
            "negative_count": sum(1 for c in cosines if c < 0),
            "gte_0.5": sum(1 for c in cosines if c >= 0.5),
        },
        "dominant_dim_agreement": {
            "agreed": dim_agreement,
            "total": n_compared,
            "rate": round(dim_agreement / n_compared, 3) if n_compared > 0 else None,
        },
        "pre_realignment_reference": "median cosine was 0.195 before SES realignment",
    }


# ─── Section 4: Feasibility Assessment ────────────────────────────────

def assess_ontology_extension(network):
    """What's needed to build a WVS OntologyQuery."""
    gaps = []
    ready = []

    # Fingerprint compatibility
    ready.append("Fingerprint format compatible: same 4D structure (rho_escol, rho_Tam_loc, rho_sexo, rho_edad)")

    # Bridge edges
    n_sig = network["n_significant"]
    if n_sig > 100:
        ready.append(f"Bridge edge source: {n_sig} significant edges from MEX W7 within-sweep")
    else:
        gaps.append(f"Only {n_sig} significant edges — may need lower threshold or more sweeps")

    # Check which gaps have been filled
    kg_exists = (DATA / "wvs_kg_ontology.json").exists()
    fp_v2_exists = (DATA / "wvs_ses_fingerprints_v2.json").exists()

    if kg_exists:
        ready.append("WVS KG ontology built (wvs_kg_ontology.json)")
    else:
        gaps.append("No WVS KG file — run build_wvs_kg_ontology.py")

    if fp_v2_exists:
        ready.append("WVS fingerprints reformatted for OntologyQuery (wvs_ses_fingerprints_v2.json)")
    else:
        gaps.append("WVS fingerprints not in OntologyQuery format — run build_wvs_kg_ontology.py")

    # Check OntologyQuery compatibility
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        from opinion_ontology import OntologyQuery
        sig = OntologyQuery.__init__.__code__.co_varnames
        if "dataset" in sig:
            ready.append("OntologyQuery accepts dataset parameter")
        else:
            gaps.append("OntologyQuery missing dataset parameter")
    except Exception:
        gaps.append("Could not inspect OntologyQuery")

    # Remaining gaps
    gaps.append("No WVS item-level fingerprints (L0) — only L1 construct-level available")

    return {
        "ready": ready,
        "gaps": gaps,
        "effort_estimate": {
            "build_wvs_kg_json": "DONE" if kg_exists else "~2 hours",
            "parameterize_ontology_query": "DONE" if "dataset" in ready[-1] else "~4 hours",
            "compute_item_level_fingerprints": "~1 hour (if WVS CSVs available)",
        },
    }


def assess_prediction_engine(network):
    """DRPredictionEngine feasibility for WVS."""
    manifest = _load_json(DATA / "wvs_construct_manifest.json")
    n_valid = [c.get("n_valid", 0) for c in manifest]

    return {
        "ses_var_compatibility": "Full — same 4 vars after SES harmonization",
        "weight_variable": "W_WEIGHT (WVS) normalized to bridge_weight; same API as Pondi2",
        "sample_sizes": {
            "mex_w7": 1741,
            "min_n_valid": min(n_valid),
            "median_n_valid": int(np.median(n_valid)),
        },
        "feasibility": "HIGH — DRPredictionEngine can work with WVS data with minimal changes",
        "required_changes": [
            "Pass weight_col='bridge_weight' instead of 'Pondi2'",
            "Ensure SES columns are harmonized via SESHarmonizer before calling fit()",
        ],
    }


def assess_scaling():
    """Estimate scaling characteristics."""
    return {
        "current_scope": {
            "countries": 66,
            "constructs": 56,
            "waves": 7,
            "total_contexts": "66 countries × 1 wave + 7 Mexico waves = 73",
            "pairs_per_context": "C(56,2) - skipped ≈ 982",
        },
        "full_surface": {
            "total_estimates": "73 × 982 ≈ 71,686 (already computed: 72,756 in gamma_surface)",
            "memory_estimate": "~30 MB JSON (already measured at 29 MB)",
        },
        "bottlenecks": [
            "Geographic sweep: 11-14 hours on Julia 8-thread for 66 countries",
            "No incremental update — adding a country/wave requires partial re-sweep",
            "2-core VM: geographic sweep would take ~30-40 hours; use 8-core for sweeps",
        ],
    }


def synthesize_readiness_score(results):
    """Composite readiness score 0-100."""
    scores = {}

    # Construct quality (25 points)
    n = results["construct_quality"]["construct_coverage"]["n_constructs"]
    scores["construct_quality"] = min(25, round(25 * n / 60))  # 60 as target

    # Network structure (25 points)
    net = results["bridge_network"]
    sig_rate = net["network_build"]["sig_rate"]
    density = net["network_build"]["density"]
    fp_acc = net["fingerprint_gamma_consistency"].get("accuracy", 0) or 0
    scores["network_structure"] = round(
        10 * min(1, sig_rate / 0.40) +  # sig rate vs los_mex 25%
        5 * min(1, density / 0.23) +     # density vs los_mex 23%
        10 * fp_acc                       # fingerprint accuracy
    )

    # Cross-study alignment (25 points)
    cs = results["cross_study"]
    cos_med = cs["fingerprint_alignment"]["fingerprint_cosine"].get("median", 0) or 0
    dim_rate = cs["fingerprint_alignment"]["dominant_dim_agreement"].get("rate", 0) or 0
    scores["cross_study"] = round(
        15 * max(0, min(1, (cos_med + 1) / 2)) +  # cosine [-1,1] → [0,1]
        10 * dim_rate
    )

    # Feasibility (25 points)
    oe = results["feasibility"]["ontology_extension"]
    n_gaps = len(oe["gaps"])
    n_ready = len(oe["ready"])
    feasibility_base = max(0, 25 - n_gaps * 3)

    # Bonus for e2e working
    e2e = results.get("ontology_query_e2e", {})
    if e2e.get("all_methods_pass"):
        feasibility_base = min(25, feasibility_base + 10)
    scores["feasibility"] = feasibility_base

    total = sum(scores.values())
    return {"total": total, "breakdown": scores, "max": 100}


# ─── Section 5: OntologyQuery End-to-End ──────────────────────────────

def check_ontology_query_e2e():
    """Verify OntologyQuery works end-to-end with WVS data."""
    fp_path = DATA / "wvs_ses_fingerprints_v2.json"
    kg_path = DATA / "wvs_kg_ontology.json"

    if not fp_path.exists() or not kg_path.exists():
        return {"status": "SKIP", "reason": "WVS KG/FP files not built"}

    import sys
    sys.path.insert(0, str(ROOT))
    from opinion_ontology import OntologyQuery

    t0 = time.time()
    oq = OntologyQuery(fp_path=fp_path, kg_path=kg_path, dataset="wvs")
    init_time = time.time() - t0

    results = {
        "status": "OK",
        "init_time_s": round(init_time, 3),
        "n_constructs": len(oq._constructs),
        "n_bridge_nodes": len(oq._bridges),
    }

    # Test each public method
    connected = [k for k in oq._constructs if k in oq._bridges]
    if len(connected) < 2:
        results["status"] = "FAIL"
        results["reason"] = "Fewer than 2 connected constructs"
        return results

    test_key = connected[0]
    methods_ok = {}

    try:
        p = oq.get_profile(test_key)
        methods_ok["get_profile"] = p.get("error") is None
    except Exception as e:
        methods_ok["get_profile"] = str(e)

    try:
        s = oq.get_similar(test_key, n=5)
        methods_ok["get_similar"] = len(s) == 5
    except Exception as e:
        methods_ok["get_similar"] = str(e)

    try:
        nb = oq.get_neighbors(test_key, top_n=5)
        methods_ok["get_neighbors"] = len(nb) > 0
    except Exception as e:
        methods_ok["get_neighbors"] = str(e)

    try:
        nh = oq.get_neighborhood(test_key, top_n=5)
        methods_ok["get_neighborhood"] = nh.get("error") is None
    except Exception as e:
        methods_ok["get_neighborhood"] = str(e)

    try:
        path = oq.find_path(connected[0], connected[1])
        methods_ok["find_path"] = path.get("error") is None and path.get("path") is not None
    except Exception as e:
        methods_ok["find_path"] = str(e)

    try:
        camp = oq.get_camp(test_key)
        methods_ok["get_camp"] = camp.get("camp_id") in {1, -1, None}
    except Exception as e:
        methods_ok["get_camp"] = str(e)

    try:
        net = oq.get_network(test_key, hops=1)
        methods_ok["get_network"] = len(net["nodes"]) > 0
    except Exception as e:
        methods_ok["get_network"] = str(e)

    try:
        frust = oq.get_frustrated_nodes(min_frustrated_ratio=0.05)
        methods_ok["get_frustrated_nodes"] = isinstance(frust, list)
    except Exception as e:
        methods_ok["get_frustrated_nodes"] = str(e)

    results["methods"] = methods_ok
    all_pass = all(v is True for v in methods_ok.values())
    results["all_methods_pass"] = all_pass
    if not all_pass:
        results["status"] = "PARTIAL"
        results["failed"] = [k for k, v in methods_ok.items() if v is not True]

    # Benchmark: 100 find_path calls
    import itertools
    pairs = list(itertools.combinations(connected[:15], 2))[:100]
    t0 = time.time()
    for a, b in pairs:
        oq.find_path(a, b)
    path_time = time.time() - t0
    results["benchmark"] = {
        "find_path_100_calls_s": round(path_time, 3),
        "find_path_mean_ms": round(path_time / len(pairs) * 1000, 2),
    }

    return results


# ─── Report Generation ────────────────────────────────────────────────

def generate_markdown(report):
    r = report
    cq = r["construct_quality"]
    bn = r["bridge_network"]
    cs = r["cross_study"]
    fe = r["feasibility"]
    sc = r["readiness_score"]
    meta = r["metadata"]

    lines = []
    lines.append(f"# WVS Ontology Readiness Diagnostic")
    lines.append(f"Generated: {meta['timestamp']}  Duration: {meta['duration_s']:.1f}s")
    lines.append(f"\n**Readiness Score: {sc['total']}/100**")
    for k, v in sc["breakdown"].items():
        lines.append(f"- {k}: {v}/{25 if k != 'total' else 100}")

    # Section 1
    lines.append("\n## 1. Construct Quality")
    cc = cq["construct_coverage"]
    lines.append(f"- WVS constructs: **{cc['n_constructs']}** (los_mex: 93)")
    lines.append(f"- Type distribution: {cc['type_distribution']}")
    lines.append(f"- Alpha >= 0.7: {cc['alpha_good_gte_0.7']} | 0.5-0.7: {cc['alpha_questionable_0.5_0.7']} | <0.5: {cc['alpha_poor_lt_0.5']}")

    fp = cq["fingerprint_quality"]
    lines.append(f"\n### SES Fingerprints")
    lines.append(f"- WVS median ses_magnitude: **{fp['wvs_ses_magnitude']['median']}** (los_mex: {fp['losmex_ses_magnitude']['median']})")
    lines.append(f"- Dominant dim distribution: {fp['wvs_dominant_dim']}")

    cm = cq["construct_map"]
    lines.append(f"\n### Cross-Study Construct Alignment")
    lines.append(f"- Grade distribution: {cm['grade_distribution']}")
    cos = cm["grade3_fingerprint_cosines"]
    lines.append(f"- Grade-3 fingerprint cosines: median={cos['median']}, min={cos['min']}, max={cos['max']}, negative={cos['negative_count']}")

    # Section 2
    lines.append("\n## 2. Bridge Network Structure (WVS MEX W7)")
    nb = bn["network_build"]
    lines.append(f"\n| Metric | WVS MEX W7 | los_mex |")
    lines.append(f"|--------|-----------|---------|")
    lines.append(f"| Total pairs | {nb['n_total_pairs']} | 4,135 |")
    lines.append(f"| Significant | {nb['n_significant']} ({nb['sig_rate']*100:.1f}%) | 984 (23.8%) |")
    lines.append(f"| Constructs | {nb['n_constructs_in_sweep']} | 93 |")
    lines.append(f"| Connected | {nb['n_connected']} | 71 |")
    lines.append(f"| Isolated | {nb['n_isolated']} | 22 |")
    lines.append(f"| Density | {nb['density']} | 0.230 |")
    lines.append(f"| Diameter | {nb['diameter']} | 4 |")
    lines.append(f"| Avg path length | {nb['avg_path_length']} | 1.728 |")

    fpc = bn["fingerprint_gamma_consistency"]
    lines.append(f"\n### Fingerprint-Gamma Sign Consistency")
    lines.append(f"- Accuracy: **{fpc['accuracy']*100:.1f}%** ({fpc['sign_match']}/{fpc['total_tested']}) — los_mex: 99.4%")

    camp = bn["camp_bipartition"]
    lines.append(f"\n### Camp Bipartition")
    lines.append(f"- Distribution: {camp['camp_distribution']}")
    lines.append(f"- Structural balance: **{camp['structural_balance']*100:.1f}%** (los_mex: 94%)")
    lines.append(f"- Fiedler eigenvalue: {camp['fiedler_eigenvalue']}")
    lines.append(f"- Confidence median: {camp['confidence_stats']['median']}")

    # Section 3
    lines.append("\n## 3. Cross-Study Bridge Capacity")
    gc = cs["geographic_consistency"]
    lines.append(f"\n### Geographic Universality")
    u = gc["universality"]
    lines.append(f"- Universal (>50% countries): {u['universal_gte_33_countries']}")
    lines.append(f"- Widespread (10-32): {u['widespread_10_32']}")
    lines.append(f"- Rare (1-9): {u['rare_1_9']}")
    lines.append(f"- Never significant: {u['never_significant']}")
    lines.append(f"- Sign consensus (widespread): median={gc['sign_consensus_among_widespread']['median']}")

    ts = cs["temporal_stability"]
    lines.append(f"\n### Temporal Stability (Mexico W3-W7)")
    lines.append(f"- Pairs in 3+ waves: {ts['n_in_3_plus_waves']}")
    lines.append(f"- Sign-stable: {ts['sign_stability']['stable']}/{ts['sign_stability']['tested']}")
    lines.append(f"- Median trend magnitude: {ts['trend_magnitude']['median_abs_slope']}")

    fa = cs["fingerprint_alignment"]
    lines.append(f"\n### Cross-Study Fingerprint Alignment (Post-Realignment)")
    lines.append(f"- Computable grade-3 pairs: {fa['n_computable']}/{fa['n_grade3_pairs']}")
    lines.append(f"- Median cosine: **{fa['fingerprint_cosine']['median']}** (pre-realignment: 0.195)")
    lines.append(f"- Dominant dim agreement: {fa['dominant_dim_agreement']['rate']*100:.0f}%")

    # Section 4
    lines.append("\n## 4. Feasibility Assessment")
    oe = fe["ontology_extension"]
    lines.append(f"\n### Ready")
    for item in oe["ready"]:
        lines.append(f"- {item}")
    lines.append(f"\n### Gaps")
    for item in oe["gaps"]:
        lines.append(f"- {item}")
    lines.append(f"\n### Effort Estimate")
    for k, v in oe["effort_estimate"].items():
        lines.append(f"- {k}: {v}")

    pe = fe["prediction_engine"]
    lines.append(f"\n### Prediction Engine")
    lines.append(f"- SES compatibility: {pe['ses_var_compatibility']}")
    lines.append(f"- Feasibility: **{pe['feasibility']}**")
    lines.append(f"- MEX W7 sample: {pe['sample_sizes']['mex_w7']}")

    sc_info = fe["scaling"]
    lines.append(f"\n### Scaling")
    lines.append(f"- Full surface: {sc_info['full_surface']['total_estimates']}")
    for b in sc_info["bottlenecks"]:
        lines.append(f"- Bottleneck: {b}")

    # Section 5
    e2e = r.get("ontology_query_e2e", {})
    if e2e:
        lines.append("\n## 5. OntologyQuery End-to-End")
        lines.append(f"- Status: **{e2e.get('status', 'N/A')}**")
        lines.append(f"- Init time: {e2e.get('init_time_s', 'N/A')}s")
        lines.append(f"- Constructs loaded: {e2e.get('n_constructs', 'N/A')}")
        lines.append(f"- Bridge-connected: {e2e.get('n_bridge_nodes', 'N/A')}")
        methods = e2e.get("methods", {})
        if methods:
            lines.append(f"\n| Method | Status |")
            lines.append(f"|--------|--------|")
            for m, ok in methods.items():
                status = "PASS" if ok is True else f"FAIL: {ok}"
                lines.append(f"| {m} | {status} |")
        bench = e2e.get("benchmark", {})
        if bench:
            lines.append(f"\n- find_path 100 calls: {bench.get('find_path_100_calls_s', 'N/A')}s")
            lines.append(f"- find_path mean: **{bench.get('find_path_mean_ms', 'N/A')} ms**")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("WVS Ontology Readiness Diagnostic")
    print("=" * 50)

    report = {}

    # Section 1: Construct Quality
    print("\n[1/5] Construct Quality...")
    report["construct_quality"] = {
        "construct_coverage": check_construct_coverage(),
        "fingerprint_quality": check_fingerprint_quality(),
        "construct_map": check_construct_map_alignment(),
    }
    print(f"  {report['construct_quality']['construct_coverage']['n_constructs']} constructs, "
          f"{report['construct_quality']['construct_map']['n_mappings']} mappings")

    # Section 2: Bridge Network
    print("\n[2/5] Bridge Network Structure...")
    network = build_wvs_mex_bridge_network()
    # Remove internal fields from report
    network_report = {k: v for k, v in network.items() if not k.startswith("_")}
    report["bridge_network"] = {
        "network_build": network_report,
        "fingerprint_gamma_consistency": check_fingerprint_gamma_consistency(network),
        "camp_bipartition": check_camp_bipartition(network),
    }
    print(f"  {network['n_significant']} significant edges, "
          f"density={network['density']}")

    # Section 3: Cross-Study
    print("\n[3/5] Cross-Study Bridge Capacity...")
    print("  Loading geographic sweep (29 MB)...")
    t_geo = time.time()
    geo_result = check_geographic_consistency()
    print(f"  Geographic: {time.time()-t_geo:.1f}s")
    temp_result = check_temporal_stability()
    fp_align = check_cross_study_fingerprint_alignment()
    report["cross_study"] = {
        "geographic_consistency": geo_result,
        "temporal_stability": temp_result,
        "fingerprint_alignment": fp_align,
    }
    print(f"  Median cross-study cosine: {fp_align['fingerprint_cosine']['median']}")

    # Section 4: Feasibility
    print("\n[4/5] Feasibility Assessment...")
    report["feasibility"] = {
        "ontology_extension": assess_ontology_extension(network),
        "prediction_engine": assess_prediction_engine(network),
        "scaling": assess_scaling(),
    }

    # Section 5: OntologyQuery E2E
    print("\n[5/5] OntologyQuery End-to-End...")
    e2e = check_ontology_query_e2e()
    report["ontology_query_e2e"] = e2e
    print(f"  Status: {e2e['status']}")
    if e2e.get("all_methods_pass"):
        print(f"  All methods pass, find_path mean: {e2e['benchmark']['find_path_mean_ms']:.1f} ms")

    # Readiness score
    report["readiness_score"] = synthesize_readiness_score(report)
    print(f"\n  Readiness score: {report['readiness_score']['total']}/100")

    # Metadata
    duration = time.time() - t0
    report["metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "duration_s": round(duration, 1),
        "data_sources": {
            "wvs_construct_manifest": str(DATA / "wvs_construct_manifest.json"),
            "wvs_ses_fingerprints": str(DATA / "wvs_ses_fingerprints.json"),
            "wvs_construct_map_v2": str(DATA / "wvs_losmex_construct_map_v2.json"),
            "wvs_mex_w7_within_sweep": str(NAVEGADOR_DATA / "wvs_mex_w7_within_sweep.json"),
            "wvs_geographic_sweep_w7": str(NAVEGADOR_DATA / "wvs_geographic_sweep_w7.json"),
            "wvs_temporal_sweep_mex": str(NAVEGADOR_DATA / "wvs_temporal_sweep_mex.json"),
        },
    }

    # Write outputs
    out_json = DATA / "wvs_ontology_readiness_report.json"
    with open(out_json, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nJSON: {out_json}")

    md = generate_markdown(report)
    out_md = DATA / "wvs_ontology_readiness_report.md"
    with open(out_md, "w") as f:
        f.write(md)
    print(f"Markdown: {out_md}")
    print(f"\nDone in {duration:.1f}s")


if __name__ == "__main__":
    main()
