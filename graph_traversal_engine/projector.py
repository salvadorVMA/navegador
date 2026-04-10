"""
Projector -- Phase 3 geometry layer for the Graph Traversal Engine.

Projects a propagation result across countries, zones, and time. Answers:
  - Does this pattern generalize to other countries?
  - Do cultural zones share propagation patterns?
  - How has the network structure evolved over time?
  - Where in SES space do the downstream effects land?
  - How confident can we be when transferring results across contexts?

The Projector does NOT recompute propagations for other countries (that would
be expensive). Instead, it combines pre-loaded structural metadata (spectral
distances, Fiedler heatmaps, zone assignments) with the source propagation
to make projections.

For detailed cross-country propagation comparison, run the Propagator on
each target country separately. The Projector provides fast approximations
from pre-computed data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from graph_traversal_engine.context import (
    ContextGraph,
    Fingerprint,
    GraphFamily,
)
from graph_traversal_engine.propagator import (
    ConsensusEffect,
    Propagator,
    PropagationResult,
)
from graph_traversal_engine.wvs_ontology import WVSOntologyQuery


# -- Result containers ---------------------------------------------------------

@dataclass
class ZonePattern:
    """Propagation pattern aggregated at the cultural zone level."""
    zone: str
    countries: list[str]
    n_countries: int
    # If propagation was run on zone members:
    mean_fiedler: float             # Average Fiedler value in zone
    fiedler_spread: float           # Std of Fiedler values
    top_constructs: list[str]       # Most common top-5 effects across zone members
    sign_consistency: float         # Fraction agreeing on direction of top effects


@dataclass
class TemporalTrajectory:
    """Temporal evolution of network structure for one country."""
    country: str
    waves_available: list[int]
    fiedler_trajectory: dict[int, float]  # wave -> fiedler value
    fiedler_trend: str                     # "tightening", "stable", "loosening"
    fiedler_slope: float                   # Linear regression slope
    mediator_trajectory: dict[int, str]    # wave -> top mediator construct
    mediator_stability: float              # Fraction of transitions with same mediator


@dataclass
class SESProjection:
    """SES geometry characterization of propagation effects."""
    mean_ses_vector: list[float]     # Mean SES fingerprint of top effects
    dominant_dimension: str           # Dimension with highest |mean rho|
    dominant_direction: str           # "positive" or "negative"
    ses_spread: float                 # Std of fingerprint magnitudes
    within_dimension: float           # Fraction of effects in same SES dimension as anchor
    cross_dimension_effects: list[str]  # Constructs driven by different SES dim


@dataclass
class ProjectionResult:
    """Full cross-context projection of a propagation result."""
    source_context: str
    source_country: str
    anchor: str
    spectral_neighbors: list[tuple[str, float]]  # (country, distance)
    zone_patterns: dict[str, ZonePattern]
    temporal: Optional[TemporalTrajectory]
    ses_projection: Optional[SESProjection]
    transfer_confidence: dict[str, float]  # country -> 0-1 confidence score


# -- Projector -----------------------------------------------------------------

class CrossContextProjector:
    """
    Projects propagation patterns across countries, zones, and time.

    Uses pre-loaded GraphFamily metadata (spectral distances, Fiedler heatmap,
    zone assignments) to characterize how a propagation result would transfer
    to other contexts.

    Usage:
        projector = CrossContextProjector(family)
        projection = projector.project("MEX", 7, propagation_result)
    """

    def __init__(self, family: GraphFamily) -> None:
        self._family = family

    def project(
        self,
        source_country: str,
        source_wave: int,
        propagation: PropagationResult,
        n_spectral_neighbors: int = 10,
    ) -> ProjectionResult:
        """
        Full projection: spectral neighbors, zones, temporal, SES geometry.

        Args:
            source_country: Country that produced the propagation
            source_wave: Wave of the source context
            propagation: Result from Propagator.propagate()
            n_spectral_neighbors: Number of spectral neighbors to return
        """
        source_graph = self._family.get(source_country, source_wave)

        # 1. Spectral neighbors
        spectral_nbrs = self._family.spectral_neighbors(
            source_country, n=n_spectral_neighbors
        )

        # 2. Zone aggregation
        zone_patterns = self._zone_aggregation(source_country, source_wave)

        # 3. Temporal trajectory
        temporal = self._temporal_trajectory(source_country)

        # 4. SES geometry of effects
        ses_proj = None
        if source_graph is not None:
            ses_proj = self._ses_projection(propagation, source_graph)

        # 5. Transfer confidence for spectral neighbors
        transfer = {}
        for country, dist in spectral_nbrs:
            transfer[country] = self._compute_transfer_confidence(
                source_country, country, dist
            )

        return ProjectionResult(
            source_context=propagation.context_str,
            source_country=source_country,
            anchor=propagation.anchor,
            spectral_neighbors=spectral_nbrs,
            zone_patterns=zone_patterns,
            temporal=temporal,
            ses_projection=ses_proj,
            transfer_confidence=transfer,
        )

    # -- Spectral projection (delegates to GraphFamily) ------------------------

    # (handled directly in project() via family.spectral_neighbors)

    # -- Zone aggregation ------------------------------------------------------

    def _zone_aggregation(
        self, source_country: str, source_wave: int
    ) -> dict[str, ZonePattern]:
        """
        Aggregate Fiedler values and structural metadata by cultural zone.

        Uses pre-loaded data (no new propagation runs).
        """
        zones: dict[str, list[str]] = {}
        for country, zone in self._family.country_zones.items():
            if zone:
                zones.setdefault(zone, []).append(country)

        fiedler_map = self._family.fiedler_heatmap or {}
        patterns = {}

        for zone, countries in zones.items():
            fiedler_vals = []
            for c in countries:
                fv = fiedler_map.get(c, {}).get(source_wave)
                if fv is not None:
                    fiedler_vals.append(fv)

            mean_f = float(np.mean(fiedler_vals)) if fiedler_vals else 0.0
            spread_f = float(np.std(fiedler_vals)) if len(fiedler_vals) > 1 else 0.0

            patterns[zone] = ZonePattern(
                zone=zone,
                countries=countries,
                n_countries=len(countries),
                mean_fiedler=round(mean_f, 4),
                fiedler_spread=round(spread_f, 4),
                top_constructs=[],  # Would require running Propagator on each
                sign_consistency=0.0,  # Requires per-country propagation
            )

        return patterns

    # -- Temporal trajectory ---------------------------------------------------

    def _temporal_trajectory(self, country: str) -> Optional[TemporalTrajectory]:
        """Build temporal trajectory from Fiedler heatmap and mediator data."""
        fiedler_map = self._family.fiedler_heatmap or {}
        fiedler_data = fiedler_map.get(country, {})

        if len(fiedler_data) < 2:
            return None

        waves = sorted(fiedler_data.keys())
        fiedler_vals = [fiedler_data[w] for w in waves]

        # Linear regression for trend
        x = np.array(waves, dtype=float)
        y = np.array(fiedler_vals)
        if len(x) > 1:
            slope = float(np.polyfit(x, y, 1)[0])
        else:
            slope = 0.0

        if slope > 0.005:
            trend = "tightening"
        elif slope < -0.005:
            trend = "loosening"
        else:
            trend = "stable"

        # Mediator trajectory
        mediator_data = self._family.mediator_stability or {}
        country_med = mediator_data.get(country, {})
        mediator_traj = {}
        if isinstance(country_med, dict):
            for w_str, med in country_med.items():
                try:
                    w = int(w_str)
                    if isinstance(med, str):
                        mediator_traj[w] = med
                    elif isinstance(med, dict):
                        mediator_traj[w] = med.get("top_mediator", "")
                except (ValueError, TypeError):
                    pass

        # Mediator stability: fraction of consecutive-wave pairs with same mediator
        med_stable = 0
        med_total = 0
        med_waves = sorted(mediator_traj.keys())
        for i in range(len(med_waves) - 1):
            med_total += 1
            if mediator_traj[med_waves[i]] == mediator_traj[med_waves[i + 1]]:
                med_stable += 1
        med_stability = med_stable / med_total if med_total > 0 else 0.0

        return TemporalTrajectory(
            country=country,
            waves_available=waves,
            fiedler_trajectory=fiedler_data,
            fiedler_trend=trend,
            fiedler_slope=round(slope, 5),
            mediator_trajectory=mediator_traj,
            mediator_stability=round(med_stability, 3),
        )

    # -- SES geometry of effects -----------------------------------------------

    def _ses_projection(
        self, propagation: PropagationResult, graph: ContextGraph
    ) -> Optional[SESProjection]:
        """
        Characterize where in SES space the propagation effects land.

        Maps top consensus effects to their 4D SES fingerprints and
        summarizes the geometry: dominant dimension, spread, and whether
        effects stay "within dimension" or cross SES axes.
        """
        top_effects = propagation.consensus[:10]
        if not top_effects:
            return None

        # Anchor fingerprint
        anchor_fp = graph.fingerprints.get(propagation.anchor)
        anchor_dominant = anchor_fp.dominant_dim if anchor_fp else None

        fp_vecs = []
        within_dim = 0
        cross_dim_constructs = []
        dims = ["escol", "Tam_loc", "sexo", "edad"]

        for eff in top_effects:
            fp = graph.fingerprints.get(eff.construct)
            if fp is None:
                continue
            v = fp.to_vec() * eff.direction
            fp_vecs.append(v)

            # Check if this effect shares the anchor's dominant dimension
            if anchor_dominant and fp.dominant_dim == anchor_dominant:
                within_dim += 1
            elif anchor_dominant:
                cross_dim_constructs.append(eff.construct)

        if not fp_vecs:
            return None

        mean_fp = np.mean(fp_vecs, axis=0)
        dominant_idx = int(np.argmax(np.abs(mean_fp)))
        magnitudes = [np.linalg.norm(v) for v in fp_vecs]

        return SESProjection(
            mean_ses_vector=[round(float(x), 4) for x in mean_fp],
            dominant_dimension=dims[dominant_idx],
            dominant_direction="positive" if mean_fp[dominant_idx] > 0 else "negative",
            ses_spread=round(float(np.std(magnitudes)), 4),
            within_dimension=within_dim / len(fp_vecs) if fp_vecs else 0.0,
            cross_dimension_effects=cross_dim_constructs[:5],
        )

    # -- Transfer confidence ---------------------------------------------------

    def _compute_transfer_confidence(
        self, source: str, target: str, spectral_distance: float
    ) -> float:
        """
        Score reliability of transferring a propagation from source to target.

        Combines:
          - Spectral distance (inverse, normalized): 50% weight
          - Zone match (same zone = 1.0): 30% weight
          - Fiedler stability of target (stable = bonus): 20% weight
        """
        # Spectral distance component (inverse, capped)
        if self._family.spectral_distances is not None:
            max_dist = float(self._family.spectral_distances.max())
        else:
            max_dist = 1.0
        spectral_score = 1.0 - min(spectral_distance / max(max_dist, 1e-6), 1.0)

        # Zone match
        source_zone = self._family.country_zones.get(source, "")
        target_zone = self._family.country_zones.get(target, "")
        zone_score = 1.0 if (source_zone and source_zone == target_zone) else 0.0

        # Fiedler stability of target
        stability_score = 0.5  # Default middle
        fiedler_map = self._family.fiedler_heatmap or {}
        target_fiedler = fiedler_map.get(target, {})
        if len(target_fiedler) >= 2:
            vals = list(target_fiedler.values())
            mean_f = np.mean(vals)
            if mean_f > 0:
                cv = np.std(vals) / mean_f  # Coefficient of variation
                stability_score = max(0.0, 1.0 - cv * 5)  # Low CV = high stability

        confidence = 0.5 * spectral_score + 0.3 * zone_score + 0.2 * stability_score
        return round(float(confidence), 3)
