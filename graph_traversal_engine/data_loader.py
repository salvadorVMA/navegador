"""
Data loader for the Graph Traversal Engine.

Reads pre-computed data from disk and assembles ContextGraph and GraphFamily
objects. All heavy computation (DR bridge, message passing, TDA) was done
offline — this module only reads and indexes.

Data sources:
  - data/tda/matrices/          (weight matrices, manifest)
  - data/gte/fingerprints/      (per-country SES fingerprints)
  - data/gte/camps/             (per-country bipartitions)
  - data/gte/construct_descriptions.json
  - data/tda/message_passing/   (BP, PPR, spectral — Phase 2)
  - data/tda/spectral/          (spectral distances — Phase 3)
  - data/tda/floyd_warshall/    (mediator scores — Phase 3)
  - data/tda/allwave/convergence/ (Fiedler heatmap, mediator stability)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from graph_traversal_engine.context import (
    WAVE_YEARS,
    CampAssignment,
    Context,
    ContextGraph,
    Fingerprint,
    GraphFamily,
)

# ── Default paths (relative to project root) ───────────────────────────────

ROOT = Path(__file__).resolve().parents[1]
MATRIX_DIR = ROOT / "data" / "tda" / "matrices"
FP_DIR = ROOT / "data" / "gte" / "fingerprints"
CAMP_DIR = ROOT / "data" / "gte" / "camps"
CORPUS_PATH = ROOT / "data" / "gte" / "construct_descriptions.json"
MP_DIR = ROOT / "data" / "tda" / "message_passing"
SPECTRAL_DIR = ROOT / "data" / "tda" / "spectral"
FW_DIR = ROOT / "data" / "tda" / "floyd_warshall"
CONVERGENCE_DIR = ROOT / "data" / "tda" / "allwave" / "convergence"


# ── Manifest Loading ───────────────────────────────────────────────────────

def load_manifest(path: Path = MATRIX_DIR / "manifest.json") -> dict:
    """Load the TDA manifest: countries, construct_index, zones."""
    with open(path) as f:
        return json.load(f)


# ── Fingerprint Loading ───────────────────────────────────────────────────

def _load_fingerprints(
    country: str, construct_index: list[str], fp_dir: Path = FP_DIR
) -> dict[str, Fingerprint]:
    """
    Load per-construct fingerprints for one country.

    Fingerprint JSON keys are bare construct names (e.g., "gender_role_traditionalism").
    Manifest keys include domain suffix (e.g., "gender_role_traditionalism|WVS_D").
    We match by stripping the domain suffix from manifest keys.
    """
    fp_path = fp_dir / f"{country}.json"
    if not fp_path.exists():
        return {}

    with open(fp_path) as f:
        data = json.load(f)

    raw = data.get("constructs", {})
    fingerprints = {}

    for full_key in construct_index:
        # "gender_role_traditionalism|WVS_D" → "gender_role_traditionalism"
        bare_name = full_key.split("|")[0] if "|" in full_key else full_key
        if bare_name not in raw:
            continue
        fp_data = raw[bare_name]

        # Handle None values (constant-input warnings during computation)
        rho_vals = {
            dim: fp_data.get(f"rho_{dim}") for dim in
            ["escol", "Tam_loc", "sexo", "edad"]
        }
        # Replace None/NaN with 0.0 for vector operations
        def _clean(v):
            if v is None:
                return 0.0
            try:
                import math
                return 0.0 if math.isnan(v) else v
            except (TypeError, ValueError):
                return 0.0

        clean = {k: _clean(v) for k, v in rho_vals.items()}

        raw_mag = fp_data.get("ses_magnitude", 0.0)
        ses_mag = 0.0 if (raw_mag is None or (isinstance(raw_mag, float) and np.isnan(raw_mag))) else raw_mag

        fingerprints[full_key] = Fingerprint(
            rho_escol=clean["escol"],
            rho_Tam_loc=clean["Tam_loc"],
            rho_sexo=clean["sexo"],
            rho_edad=clean["edad"],
            ses_magnitude=ses_mag,
            dominant_dim=fp_data.get("dominant_dim") or "",
            n_valid=fp_data.get("n_valid", 0),
        )

    return fingerprints


# ── Camp Loading ───────────────────────────────────────────────────────────

def _load_camps(
    country: str, camp_dir: Path = CAMP_DIR
) -> tuple[dict[str, CampAssignment], float, float]:
    """
    Load bipartition data for one country.

    Returns: (camps_dict, fiedler_value, structural_balance)
    """
    camp_path = camp_dir / f"{country}.json"
    if not camp_path.exists():
        return {}, 0.0, 0.0

    with open(camp_path) as f:
        data = json.load(f)

    camps = {}
    for key, cdata in data.get("constructs", {}).items():
        camps[key] = CampAssignment(
            camp_id=cdata["camp_id"],
            camp_name=cdata["camp_name"],
            confidence=cdata["confidence"],
            frustrated_ratio=cdata["frustrated_ratio"],
            n_triangles=cdata["n_triangles"],
            is_boundary=cdata["is_boundary"],
        )

    return camps, data.get("fiedler_value", 0.0), data.get("structural_balance", 0.0)


# ── Weight Matrix Loading ──────────────────────────────────────────────────

def _load_weight_matrix(
    country: str, construct_index: list[str], matrix_dir: Path = MATRIX_DIR
) -> tuple[np.ndarray, int]:
    """
    Load weight matrix CSV and align to global construct_index order.

    The CSV may have a different column/row order than construct_index.
    Returns (n×n matrix aligned to construct_index, n_significant_edges).
    """
    csv_path = matrix_dir / f"{country}.csv"
    n = len(construct_index)

    if not csv_path.exists():
        return np.full((n, n), np.nan), 0

    df = pd.read_csv(csv_path, index_col=0)
    W = np.full((n, n), np.nan)

    # Build lookup from CSV labels to construct_index positions
    csv_labels = list(df.columns)
    csv_to_idx = {}
    for ci, ck in enumerate(construct_index):
        if ck in csv_labels:
            csv_to_idx[ck] = ci

    n_sig = 0
    for ck_i, ci_i in csv_to_idx.items():
        for ck_j, ci_j in csv_to_idx.items():
            if ci_i == ci_j:
                continue
            val = df.loc[ck_i, ck_j] if ck_i in df.index and ck_j in df.columns else np.nan
            if pd.notna(val):
                W[ci_i, ci_j] = float(val)
                if ci_i < ci_j:
                    n_sig += 1

    return W, n_sig


# ── Message Passing Loading (Phase 2 — optional) ─────────────────────────

def _load_bp(country: str, mp_dir: Path = MP_DIR) -> Optional[np.ndarray]:
    """Load BP lift matrix for a country. Returns n×n array or None."""
    path = mp_dir / f"{country}_bp.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    lift = data.get("lift_matrix")
    if lift is None:
        return None
    return np.array(lift)


def _load_ppr(
    country: str, mp_dir: Path = MP_DIR
) -> tuple[Optional[dict], Optional[dict]]:
    """Load PPR hub and sink scores for a country."""
    path = mp_dir / f"{country}_ppr.json"
    if not path.exists():
        return None, None
    with open(path) as f:
        data = json.load(f)
    return data.get("hub_scores"), data.get("sink_scores")


def _load_spectral_mp(
    country: str, mp_dir: Path = MP_DIR
) -> tuple[Optional[np.ndarray], Optional[dict]]:
    """Load spectral eigenvalues and Fiedler partition."""
    path = mp_dir / f"{country}_spectral.json"
    if not path.exists():
        return None, None
    with open(path) as f:
        data = json.load(f)
    eig_summary = data.get("eigenvalue_summary", {})
    eigenvalues = eig_summary.get("all_eigenvalues")
    fiedler_part = data.get("fiedler_partition")
    return (np.array(eigenvalues) if eigenvalues else None), fiedler_part


# ── TDA Feature Loading (Phase 3 — optional) ─────────────────────────────

def _load_spectral_distances(
    spectral_dir: Path = SPECTRAL_DIR,
) -> tuple[Optional[np.ndarray], Optional[list[str]]]:
    """Load pairwise spectral distance matrix between countries."""
    path = spectral_dir / "spectral_distance_matrix.csv"
    if not path.exists():
        return None, None
    df = pd.read_csv(path, index_col=0)
    return df.values.astype(float), list(df.index)


def _load_mediator_scores(
    country: str, fw_dir: Path = FW_DIR
) -> Optional[dict[str, float]]:
    """Load Floyd-Warshall mediator scores for a country."""
    path = fw_dir / "mediator_scores.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    entry = data.get(country)
    if entry is None:
        return None
    # mediator_scores.json stores top_mediators per wave, not per-construct scores
    # Return the whole entry for now; Phase 3 will refine
    return entry


def _load_fiedler_heatmap(
    convergence_dir: Path = CONVERGENCE_DIR,
) -> Optional[dict]:
    """Load Fiedler heatmap (country × wave)."""
    path = convergence_dir / "fiedler_heatmap.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0)
    # Convert to dict: country → {wave: fiedler_value}
    result = {}
    for country in df.index:
        result[country] = {}
        for col in df.columns:
            val = df.loc[country, col]
            if pd.notna(val):
                result[country][int(col)] = float(val)
    return result


def _load_mediator_stability(
    convergence_dir: Path = CONVERGENCE_DIR,
) -> Optional[dict]:
    """Load mediator stability data."""
    path = convergence_dir / "mediator_stability.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


# ── Construct Descriptions ─────────────────────────────────────────────────

def _load_construct_descriptions(
    path: Path = CORPUS_PATH,
) -> Optional[dict]:
    """Load construct description corpus."""
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return data.get("constructs")


# ── Main Assembly Functions ────────────────────────────────────────────────

def load_context_graph(
    country: str,
    wave: int = 7,
    manifest: Optional[dict] = None,
    load_mp: bool = True,
) -> ContextGraph:
    """
    Load a complete ContextGraph for one (country, wave) context.

    Args:
        country: ISO Alpha-3 code
        wave: WVS wave number (currently only 7 has full data)
        manifest: Pre-loaded manifest dict (avoids re-reading)
        load_mp: Whether to load message passing outputs (BP, PPR, spectral)

    Returns:
        ContextGraph with weight matrix, fingerprints, camps, and optionally
        pre-computed dynamics.
    """
    if manifest is None:
        manifest = load_manifest()

    construct_index = manifest["construct_index"]
    country_zone = manifest.get("country_zone", {})

    # Core data
    W, n_sig = _load_weight_matrix(country, construct_index)
    fingerprints = _load_fingerprints(country, construct_index)
    camps_raw, fiedler, balance = _load_camps(country)

    # Map camp keys (which include domain suffix from weight matrix) to construct_index
    camps = {}
    for key in construct_index:
        if key in camps_raw:
            camps[key] = camps_raw[key]

    ctx = Context(
        country=country,
        wave=wave,
        year=WAVE_YEARS.get(wave, 0),
        zone=country_zone.get(country, ""),
        n_constructs=len(construct_index),
    )

    graph = ContextGraph(
        context=ctx,
        constructs=construct_index,
        weight_matrix=W,
        fingerprints=fingerprints,
        camps=camps,
        fiedler_value=fiedler,
        structural_balance=balance,
        n_significant_edges=n_sig,
    )

    # Optional: load pre-computed message passing outputs
    if load_mp and wave == 7:
        graph.bp_lift_matrix = _load_bp(country)
        graph.ppr_hub_scores, graph.ppr_sink_scores = _load_ppr(country)
        graph.spectral_eigenvalues, graph.spectral_fiedler_partition = (
            _load_spectral_mp(country)
        )

    # Optional: load TDA features
    mediator_data = _load_mediator_scores(country)
    if mediator_data:
        graph.top_mediator = mediator_data.get("most_common")

    return graph


def load_graph_family(
    waves: list[int] | None = None,
    countries: list[str] | None = None,
    load_mp: bool = True,
) -> GraphFamily:
    """
    Load the full graph family: all requested contexts + cross-context data.

    Args:
        waves: Which waves to load (default: [7])
        countries: Which countries to load (default: all in manifest)
        load_mp: Whether to load message passing outputs

    Returns:
        GraphFamily with all context graphs and cross-context comparison data.
    """
    if waves is None:
        waves = [7]

    manifest = load_manifest()
    construct_index = manifest["construct_index"]

    if countries is None:
        countries = manifest["countries"]

    # Load context graphs
    contexts = {}
    for wave in waves:
        for country in countries:
            graph = load_context_graph(
                country, wave, manifest=manifest, load_mp=load_mp
            )
            contexts[(country, wave)] = graph

    # Cross-context data
    spectral_dists, spectral_countries = _load_spectral_distances()
    fiedler_heatmap = _load_fiedler_heatmap()
    mediator_stability = _load_mediator_stability()
    descriptions = _load_construct_descriptions()

    return GraphFamily(
        contexts=contexts,
        construct_index=construct_index,
        spectral_distances=spectral_dists,
        spectral_countries=spectral_countries,
        fiedler_heatmap=fiedler_heatmap,
        mediator_stability=mediator_stability,
        country_zones=manifest.get("country_zone", {}),
        construct_descriptions=descriptions,
    )
