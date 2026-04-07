"""
Graph Traversal Engine (GTE) — unified query layer over the WVS γ-surface.

Combines three analytical subsystems into a single query path:
  Structure (ontology) + Dynamics (message passing) + Geometry (TDA)

Phase 1: Structure layer — context-aware WVS ontology with per-country
fingerprints, bipartitions, path finding, and neighborhood queries.
"""

from graph_traversal_engine.context import (
    Context,
    ContextGraph,
    Fingerprint,
    GraphFamily,
)
from graph_traversal_engine.wvs_ontology import WVSOntologyQuery

__all__ = [
    "Context",
    "ContextGraph",
    "Fingerprint",
    "GraphFamily",
    "WVSOntologyQuery",
]
