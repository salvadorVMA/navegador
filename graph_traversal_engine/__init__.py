"""
Graph Traversal Engine (GTE) -- unified query layer over the WVS gamma-surface.

Combines four analytical layers into a single query path:
  Phase 1: Structure (WVSOntologyQuery) -- per-context graph access
  Phase 2: Dynamics (Propagator) -- BP + PPR + spectral + consensus
  Phase 3: Geometry (CrossContextProjector) -- cross-country, temporal, SES
  Phase 4: Narrative (NarrativeSynthesizer) -- human-readable output

Quick start:
    from graph_traversal_engine import GraphTraversalEngine
    engine = GraphTraversalEngine(countries=["MEX", "USA", "JPN"])
    result = engine.query("gender_role_traditionalism|WVS_D", "MEX", direction=-1)
    print(result.narrative)
"""

from graph_traversal_engine.context import (
    Context,
    ContextGraph,
    Fingerprint,
    GraphFamily,
)
from graph_traversal_engine.engine import GraphTraversalEngine
from graph_traversal_engine.propagator import (
    ConsensusEffect,
    PropagationEffect,
    PropagationResult,
    Propagator,
)
from graph_traversal_engine.projector import (
    CrossContextProjector,
    ProjectionResult,
    SESProjection,
    TemporalTrajectory,
    ZonePattern,
)
from graph_traversal_engine.synthesizer import (
    GTEOutput,
    NarrativeSynthesizer,
)
from graph_traversal_engine.wvs_ontology import WVSOntologyQuery

__all__ = [
    # Engine
    "GraphTraversalEngine",
    # Phase 1: Structure
    "Context",
    "ContextGraph",
    "Fingerprint",
    "GraphFamily",
    "WVSOntologyQuery",
    # Phase 2: Dynamics
    "Propagator",
    "PropagationEffect",
    "PropagationResult",
    "ConsensusEffect",
    # Phase 3: Geometry
    "CrossContextProjector",
    "ProjectionResult",
    "ZonePattern",
    "TemporalTrajectory",
    "SESProjection",
    # Phase 4: Narrative
    "NarrativeSynthesizer",
    "GTEOutput",
]
