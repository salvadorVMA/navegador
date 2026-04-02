"""
Message Passing — Shared Utilities

Common data loading, matrix operations, and output serialization
for the WVS belief network message passing framework.

Data convention:
  - Weight matrices have empty cells (empty string in CSV) for pairs where
    no DR bridge estimate exists.  These are structural NaN — "no edge",
    distinct from a zero-weight edge (γ = 0.0).
  - All load functions preserve this distinction via np.nan.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ── Project paths ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TDA_DIR    = ROOT / "data" / "tda"
MATRIX_DIR = TDA_DIR / "matrices"
OUTPUT_DIR = TDA_DIR / "message_passing"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_manifest() -> dict:
    """Load matrices/manifest.json — countries, construct_index, cultural_zones."""
    with open(MATRIX_DIR / "manifest.json") as f:
        return json.load(f)


def load_weight_matrix(country: str) -> tuple[np.ndarray, list[str]]:
    """
    Load a 55×55 weight matrix CSV for one country.

    Returns
    -------
    W : (55, 55) float array with np.nan for missing edges
    labels : list of 55 construct label strings
    """
    path = MATRIX_DIR / f"{country}.csv"
    df = pd.read_csv(path, index_col=0)
    labels = list(df.columns)
    # pd.read_csv leaves empty cells as NaN — exactly what we want
    W = df.values.astype(np.float64)
    return W, labels


def load_temporal_matrix(wave: int) -> tuple[np.ndarray, list[str]]:
    """Load a 52×52 temporal weight matrix for Mexico at wave *wave*."""
    path = TDA_DIR / "temporal" / f"MEX_W{wave}.csv"
    df = pd.read_csv(path, index_col=0)
    labels = list(df.columns)
    W = df.values.astype(np.float64)
    return W, labels


def load_temporal_manifest() -> dict:
    """Load temporal/manifest.json — waves, wave_years, construct_index."""
    with open(TDA_DIR / "temporal" / "manifest.json") as f:
        return json.load(f)


def load_gw_transport_plans() -> dict[tuple[str, str], np.ndarray]:
    """
    Load GW transport plans from alignment/gw_transport_top50.json.

    Returns dict keyed by (country1, country2) → 55×55 transport matrix.
    """
    with open(TDA_DIR / "alignment" / "gw_transport_top50.json") as f:
        raw = json.load(f)
    plans = {}
    for entry in raw:
        c1 = entry["country1"]
        c2 = entry["country2"]
        T  = np.array(entry["transport"], dtype=np.float64)
        plans[(c1, c2)] = T
    return plans


def load_spectral_distance_matrix() -> tuple[np.ndarray, list[str]]:
    """Load 66×66 spectral distance matrix."""
    path = TDA_DIR / "spectral" / "spectral_distance_matrix.csv"
    df = pd.read_csv(path, index_col=0)
    return df.values.astype(np.float64), list(df.columns)


def load_spectral_features() -> dict:
    """Load per-country spectral features (Fiedler, entropy, etc.)."""
    with open(TDA_DIR / "spectral" / "spectral_features.json") as f:
        return json.load(f)


def load_mediator_scores() -> dict:
    """Load per-country Floyd-Warshall mediator scores."""
    with open(TDA_DIR / "floyd_warshall" / "mediator_scores.json") as f:
        return json.load(f)


# ── Matrix helpers ───────────────────────────────────────────────────────────

def adjacency_mask(W: np.ndarray) -> np.ndarray:
    """Boolean mask: True where W has a real edge (not NaN, not zero)."""
    return (~np.isnan(W)) & (W != 0.0)


def neighbors(W: np.ndarray, i: int) -> list[int]:
    """Return indices of nodes adjacent to i (non-NaN, non-zero)."""
    mask = adjacency_mask(W)
    return list(np.where(mask[i])[0])


def symmetrize_abs(W: np.ndarray) -> np.ndarray:
    """
    Symmetrize and take absolute value: W_sym = (|W| + |W|^T) / 2.
    NaN propagation: if either cell is NaN, result is NaN.
    """
    absW = np.abs(W)
    return (absW + absW.T) / 2.0


def fill_nan_zero(W: np.ndarray) -> np.ndarray:
    """Replace NaN with 0.0 — for Laplacian and transition matrix computation."""
    return np.where(np.isnan(W), 0.0, W)


def row_normalize(W: np.ndarray) -> np.ndarray:
    """
    Row-normalize: P[i,:] = W[i,:] / sum(W[i,:]).
    Zero-sum rows are left as zeros (isolated nodes teleport on restart).
    """
    rs = W.sum(axis=1, keepdims=True)
    rs[rs == 0] = 1.0  # avoid division by zero
    return W / rs


# ── Output ───────────────────────────────────────────────────────────────────

class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def save_json(data: dict, path: Path) -> None:
    """Save dict to JSON with numpy-safe encoding. Creates parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, cls=_NumpyEncoder, indent=2)
    print(f"  saved → {path.relative_to(ROOT)}")


def get_output_dir() -> Path:
    """Return the message passing output directory (creates if needed)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR
