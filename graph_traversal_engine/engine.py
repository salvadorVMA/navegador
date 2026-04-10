"""
GraphTraversalEngine -- unified orchestrator for the GTE pipeline.

Chains all four phases:
  Phase 1: Structure (WVSOntologyQuery) -- per-context graph access
  Phase 2: Dynamics (Propagator) -- BP + PPR + spectral + consensus
  Phase 3: Geometry (CrossContextProjector) -- cross-country, temporal, SES
  Phase 4: Narrative (NarrativeSynthesizer) -- human-readable output

Single entry point: engine.query(anchor, country, wave, direction)
"""

from __future__ import annotations

from typing import Callable, Optional

from graph_traversal_engine.context import GraphFamily
from graph_traversal_engine.data_loader import load_graph_family
from graph_traversal_engine.propagator import Propagator, PropagationResult
from graph_traversal_engine.projector import CrossContextProjector, ProjectionResult
from graph_traversal_engine.synthesizer import GTEOutput, NarrativeSynthesizer
from graph_traversal_engine.wvs_ontology import WVSOntologyQuery


class GraphTraversalEngine:
    """
    Unified query engine over the WVS gamma-surface.

    Loads data once, caches per-context Propagators, and chains all phases.

    Usage:
        engine = GraphTraversalEngine(waves=[7], countries=["MEX", "USA", "JPN"])
        result = engine.query(
            anchor="gender_role_traditionalism|WVS_D",
            country="MEX",
            wave=7,
            direction=-1,
        )
        print(result.narrative)
    """

    def __init__(
        self,
        family: Optional[GraphFamily] = None,
        waves: Optional[list[int]] = None,
        countries: Optional[list[str]] = None,
        load_mp: bool = True,
        llm_callable: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the engine.

        Args:
            family: Pre-loaded GraphFamily (if None, loads from disk)
            waves: Waves to load (default [7])
            countries: Countries to load (default all)
            load_mp: Whether to load message passing data
            llm_callable: Optional LLM function for narrative generation
        """
        if family is not None:
            self._family = family
        else:
            self._family = load_graph_family(
                waves=waves, countries=countries, load_mp=load_mp
            )

        self._projector = CrossContextProjector(self._family)
        self._synthesizer = NarrativeSynthesizer(llm_callable)

        # Cache propagators per (country, wave) to avoid re-computing eigens
        self._propagators: dict[tuple[str, int], Propagator] = {}

    @property
    def family(self) -> GraphFamily:
        return self._family

    def _get_propagator(self, country: str, wave: int) -> Propagator:
        """Get or create a cached Propagator for the given context."""
        key = (country, wave)
        if key not in self._propagators:
            oq = WVSOntologyQuery(self._family, country, wave)
            self._propagators[key] = Propagator(oq)
        return self._propagators[key]

    def query(
        self,
        anchor: str,
        country: str,
        wave: int = 7,
        direction: int = 1,
        include_narrative: bool = True,
        n_spectral_neighbors: int = 10,
    ) -> GTEOutput:
        """
        Full GTE query: structure -> dynamics -> geometry -> narrative.

        Args:
            anchor: Construct key (name|WVS_X format)
            country: ISO Alpha-3 country code
            wave: WVS wave number (3-7)
            direction: +1 (increasing) or -1 (decreasing)
            include_narrative: Whether to generate narrative text
            n_spectral_neighbors: Number of spectral neighbors to include

        Returns:
            GTEOutput with propagation, projection, narrative, and caveats.
        """
        # Phase 1: Structure
        graph = self._family.get(country, wave)
        if graph is None:
            raise ValueError(f"No context for ({country}, W{wave})")

        zone = self._family.country_zones.get(country, "")

        # Phase 2: Dynamics
        propagator = self._get_propagator(country, wave)
        propagation = propagator.propagate(anchor, direction)

        # Phase 3: Geometry
        projection = self._projector.project(
            country, wave, propagation,
            n_spectral_neighbors=n_spectral_neighbors,
        )

        # Phase 4: Narrative
        narrative = ""
        caveats = []
        if include_narrative:
            narrative, caveats = self._synthesizer.synthesize(
                propagation, projection, country, wave, zone
            )

        return GTEOutput(
            query_context={
                "anchor": anchor,
                "country": country,
                "wave": wave,
                "direction": direction,
                "zone": zone,
            },
            propagation=propagation,
            projection=projection,
            narrative=narrative,
            caveats=caveats,
            metadata={
                "n_contexts_loaded": len(self._family.contexts),
                "construct_index_size": len(self._family.construct_index),
                "has_spectral_distances": self._family.spectral_distances is not None,
                "has_fiedler_heatmap": self._family.fiedler_heatmap is not None,
            },
        )

    def compare_countries(
        self,
        anchor: str,
        countries: list[str],
        wave: int = 7,
        direction: int = 1,
    ) -> dict[str, GTEOutput]:
        """
        Run the same query across multiple countries and return results.

        Useful for cross-country comparison of propagation patterns.
        """
        results = {}
        for country in countries:
            try:
                results[country] = self.query(
                    anchor, country, wave, direction,
                    include_narrative=False,
                )
            except (ValueError, KeyError):
                continue
        return results

    def compare_waves(
        self,
        anchor: str,
        country: str,
        waves: Optional[list[int]] = None,
        direction: int = 1,
    ) -> dict[int, GTEOutput]:
        """
        Run the same query across waves for one country.

        Useful for temporal evolution of propagation patterns.
        """
        if waves is None:
            waves = self._family.waves_for_country(country)

        results = {}
        for wave in waves:
            try:
                results[wave] = self.query(
                    anchor, country, wave, direction,
                    include_narrative=False,
                )
            except (ValueError, KeyError):
                continue
        return results
