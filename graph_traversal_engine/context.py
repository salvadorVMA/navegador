"""
Data model for the Graph Traversal Engine.

Context-indexed graphs: each (country, wave) pair defines a context with its
own weight matrix, SES fingerprints, camp bipartition, and pre-computed
analytical outputs.

Dataclasses are immutable (frozen) where possible to prevent accidental
mutation after loading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass(frozen=True)
class Context:
    """
    A specific survey administration: one country in one WVS wave.

    This is the fundamental indexing unit. All graph data is stored per-context.
    """
    country: str       # ISO Alpha-3 (e.g., "MEX")
    wave: int          # WVS wave number (3-7)
    year: int = 0      # Survey year (approximate; 0 if unknown)
    zone: str = ""     # Inglehart-Welzel cultural zone
    n_constructs: int = 0  # Constructs present in this context

    def __str__(self) -> str:
        return f"{self.country}_W{self.wave}"


# -- Wave year mapping (approximate midpoints) --------------------------------
WAVE_YEARS = {3: 1998, 4: 2001, 5: 2007, 6: 2013, 7: 2019}


@dataclass(frozen=True)
class Fingerprint:
    """
    4D SES correlation profile for a construct in a specific context.

    Each component is Spearman rho between the construct score and one SES
    dimension in the given population. Context-specific: the same construct
    has different fingerprints in different countries.
    """
    rho_escol: float     # Spearman rho with education
    rho_Tam_loc: float   # Spearman rho with urbanization
    rho_sexo: float      # Spearman rho with gender
    rho_edad: float      # Spearman rho with age/cohort
    ses_magnitude: float  # RMS of 4 rho values
    dominant_dim: str     # Dimension with highest |rho|
    n_valid: int = 0      # Number of valid observations

    def to_vec(self) -> np.ndarray:
        """Return the 4D fingerprint as a numpy array."""
        return np.array([self.rho_escol, self.rho_Tam_loc,
                         self.rho_sexo, self.rho_edad])

    def to_unit_vec(self) -> Optional[np.ndarray]:
        """Return unit-normalized fingerprint, or None if zero-magnitude."""
        v = self.to_vec()
        norm = np.linalg.norm(v)
        return v / norm if norm > 1e-10 else None


@dataclass(frozen=True)
class CampAssignment:
    """Bipartition membership for one construct in one context."""
    camp_id: int           # +1 (cosmopolitan) or -1 (tradition)
    camp_name: str         # "cosmopolitan" or "tradition"
    confidence: float      # 0-1, distance from bipartition boundary
    frustrated_ratio: float  # Fraction of triangles with sign conflict
    n_triangles: int       # Total triangle count at this node
    is_boundary: bool      # frustrated_ratio > 0.10


@dataclass
class ContextGraph:
    """
    The per-context graph: weight matrix + fingerprints + camps + metadata.

    This replaces the single-network OntologyQuery for WVS data.
    Mutable because pre-computed dynamics/TDA features are loaded lazily.
    """
    context: Context
    constructs: list[str]            # Construct keys present (e.g., "name|WVS_X")
    weight_matrix: np.ndarray        # n x n signed gamma (NaN = missing/non-significant)
    fingerprints: dict[str, Fingerprint]   # construct_key -> Fingerprint
    camps: dict[str, CampAssignment]       # construct_key -> CampAssignment

    # Derived structural properties (computed on load)
    fiedler_value: float = 0.0
    structural_balance: float = 0.0
    n_significant_edges: int = 0

    # -- Pre-computed dynamics (loaded from MP outputs, Phase 2) --
    bp_lift_matrix: Optional[np.ndarray] = None    # n x n KL lift
    ppr_hub_scores: Optional[dict[str, float]] = None
    ppr_sink_scores: Optional[dict[str, float]] = None
    spectral_eigenvalues: Optional[np.ndarray] = None
    spectral_fiedler_partition: Optional[dict] = None

    # -- Pre-computed TDA features (Phase 3) --
    mediator_scores: Optional[dict[str, float]] = None
    top_mediator: Optional[str] = None
    betti_1: Optional[int] = None

    @property
    def present_constructs(self) -> list[str]:
        """Constructs with at least one non-NaN edge in the weight matrix.

        In earlier waves (W3=24 constructs, W7=55), many construct slots in
        the global index are structurally absent. This property returns only
        the constructs that have actual data in this context.
        """
        present = []
        for i, key in enumerate(self.constructs):
            row = self.weight_matrix[i, :]
            if np.any(~np.isnan(row)):
                present.append(key)
        return present

    @property
    def present_mask(self) -> np.ndarray:
        """Boolean mask over construct_index: True if construct has data."""
        n = len(self.constructs)
        mask = np.zeros(n, dtype=bool)
        for i in range(n):
            if np.any(~np.isnan(self.weight_matrix[i, :])):
                mask[i] = True
        return mask

    def construct_index(self, key: str) -> int:
        """Return index of construct in weight matrix, or -1 if not found."""
        try:
            return self.constructs.index(key)
        except ValueError:
            return -1

    def get_edge(self, key_a: str, key_b: str) -> Optional[float]:
        """Return gamma weight between two constructs, or None if no edge."""
        i, j = self.construct_index(key_a), self.construct_index(key_b)
        if i < 0 or j < 0:
            return None
        val = self.weight_matrix[i, j]
        return float(val) if not np.isnan(val) else None

    def get_significant_neighbors(
        self, key: str, min_abs_gamma: float = 0.0
    ) -> list[tuple[str, float]]:
        """Return (neighbor_key, gamma) pairs for significant edges above threshold."""
        i = self.construct_index(key)
        if i < 0:
            return []
        neighbors = []
        for j, other_key in enumerate(self.constructs):
            if j == i:
                continue
            val = self.weight_matrix[i, j]
            if not np.isnan(val) and abs(val) >= min_abs_gamma:
                neighbors.append((other_key, float(val)))
        # Sort by |gamma| descending
        neighbors.sort(key=lambda x: abs(x[1]), reverse=True)
        return neighbors


@dataclass
class GraphFamily:
    """
    The collection of all context graphs, plus cross-context relationships.

    This is the top-level data object the engine operates on.
    """
    contexts: dict[tuple[str, int], ContextGraph]  # (country, wave) -> graph
    construct_index: list[str]                      # Global construct list (W7)

    # Cross-context comparison data (TDA outputs)
    spectral_distances: Optional[np.ndarray] = None       # n_countries x n_countries
    spectral_countries: Optional[list[str]] = None         # Country order for distance matrix
    fiedler_heatmap: Optional[dict] = None                 # country -> {wave: fiedler_value}
    mediator_stability: Optional[dict] = None              # country -> stability data
    country_zones: dict[str, str] = field(default_factory=dict)  # Alpha3 -> zone

    # Construct descriptions for semantic search
    construct_descriptions: Optional[dict] = None  # key -> {label, description, ...}

    def get(self, country: str, wave: int = 7) -> Optional[ContextGraph]:
        """Get context graph by country and wave."""
        return self.contexts.get((country, wave))

    def countries(self, wave: int = 7) -> list[str]:
        """List countries available for a given wave."""
        return [c for (c, w) in self.contexts if w == wave]

    def waves_for_country(self, country: str) -> list[int]:
        """List waves available for a given country."""
        return sorted(w for (c, w) in self.contexts if c == country)

    def spectral_neighbors(
        self, country: str, n: int = 5, wave: int = 7
    ) -> list[tuple[str, float]]:
        """
        Return N nearest countries by spectral distance.

        Spectral distance = L2 norm of eigenvalue vectors of the normalized
        Laplacian. Countries with similar spectra have similar diffusion dynamics.
        """
        if self.spectral_distances is None or self.spectral_countries is None:
            return []
        if country not in self.spectral_countries:
            return []
        idx = self.spectral_countries.index(country)
        dists = self.spectral_distances[idx]
        # Sort by distance, exclude self
        ranked = sorted(
            [(self.spectral_countries[j], float(dists[j]))
             for j in range(len(self.spectral_countries)) if j != idx],
            key=lambda x: x[1]
        )
        return ranked[:n]
