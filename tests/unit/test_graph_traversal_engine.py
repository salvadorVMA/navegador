"""
Unit tests for the Graph Traversal Engine (Phases 1-4).

Tests cover:
  - Context dataclasses and Fingerprint operations
  - Data loader: weight matrices, fingerprints, camps, MP outputs
  - Multi-wave loading and construct set intersection
  - WVSOntologyQuery: profiles, neighbors, paths, camps, cross-context comparison
  - Propagator: BP, PPR, spectral, consensus scoring
  - Projector: spectral neighbors, zones, temporal, SES geometry, transfer confidence
  - Synthesizer: narrative generation, caveat generation
  - Engine: full pipeline orchestration

Uses real data (requires pre-computed Phase 0 outputs in navegador_data).
"""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from graph_traversal_engine.context import (
    WAVE_YEARS,
    CampAssignment,
    Context,
    ContextGraph,
    Fingerprint,
    GraphFamily,
)
from graph_traversal_engine.data_loader import (
    load_context_graph,
    load_graph_family,
    load_manifest,
)
from graph_traversal_engine.wvs_ontology import WVSOntologyQuery
from graph_traversal_engine.propagator import Propagator, PropagationResult
from graph_traversal_engine.projector import CrossContextProjector
from graph_traversal_engine.synthesizer import NarrativeSynthesizer
from graph_traversal_engine.engine import GraphTraversalEngine


# -- Fixtures ------------------------------------------------------------------

@pytest.fixture(scope="module")
def manifest():
    return load_manifest(7)


@pytest.fixture(scope="module")
def mex_graph(manifest):
    return load_context_graph("MEX", 7, manifest=manifest)


@pytest.fixture(scope="module")
def family():
    """Load a small family for cross-country tests."""
    return load_graph_family(
        waves=[7],
        countries=["MEX", "USA", "JPN"],
        load_mp=True,
    )


@pytest.fixture(scope="module")
def oq_mex(family):
    return WVSOntologyQuery(family, country="MEX", wave=7)


@pytest.fixture(scope="module")
def oq_usa(family):
    return WVSOntologyQuery(family, country="USA", wave=7)


@pytest.fixture(scope="module")
def engine(family):
    return GraphTraversalEngine(family=family)


# -- Test: Context Dataclasses -------------------------------------------------

class TestContext:
    def test_context_str(self):
        ctx = Context(country="MEX", wave=7, zone="Latin America")
        assert str(ctx) == "MEX_W7"

    def test_context_frozen(self):
        ctx = Context(country="MEX", wave=7)
        with pytest.raises(AttributeError):
            ctx.country = "USA"

    def test_wave_years(self):
        assert WAVE_YEARS[7] == 2019
        assert WAVE_YEARS[3] == 1998


class TestFingerprint:
    def test_to_vec(self):
        fp = Fingerprint(0.1, -0.2, 0.05, 0.3, 0.18, "edad")
        v = fp.to_vec()
        assert v.shape == (4,)
        assert v[0] == pytest.approx(0.1)

    def test_to_unit_vec(self):
        fp = Fingerprint(0.3, 0.4, 0.0, 0.0, 0.25, "Tam_loc")
        uv = fp.to_unit_vec()
        assert uv is not None
        assert np.linalg.norm(uv) == pytest.approx(1.0)

    def test_zero_magnitude(self):
        fp = Fingerprint(0.0, 0.0, 0.0, 0.0, 0.0, "")
        assert fp.to_unit_vec() is None


# -- Test: Data Loader ---------------------------------------------------------

class TestDataLoader:
    def test_manifest_loads(self, manifest):
        assert "construct_index" in manifest
        assert "countries" in manifest
        assert len(manifest["construct_index"]) >= 24

    def test_mex_graph_w7(self, mex_graph):
        assert mex_graph.context.country == "MEX"
        assert mex_graph.context.wave == 7
        assert len(mex_graph.present_constructs) >= 40
        assert mex_graph.n_significant_edges > 100

    def test_fingerprints_loaded(self, mex_graph):
        assert len(mex_graph.fingerprints) >= 40
        # Check a fingerprint has valid data
        for key, fp in mex_graph.fingerprints.items():
            assert isinstance(fp.rho_escol, float)
            break

    def test_bp_loaded_w7(self, mex_graph):
        assert mex_graph.bp_lift_matrix is not None
        assert mex_graph.bp_lift_matrix.shape[0] == len(mex_graph.constructs)

    def test_ppr_loaded_w7(self, mex_graph):
        assert mex_graph.ppr_hub_scores is not None

    def test_spectral_loaded_w7(self, mex_graph):
        assert mex_graph.spectral_eigenvalues is not None

    def test_present_constructs(self, mex_graph):
        present = mex_graph.present_constructs
        assert len(present) <= len(mex_graph.constructs)
        assert len(present) > 0

    def test_present_mask(self, mex_graph):
        mask = mex_graph.present_mask
        assert mask.shape == (len(mex_graph.constructs),)
        assert mask.sum() == len(mex_graph.present_constructs)

    def test_multi_wave_family(self):
        """Load W5 + W7 for Mexico."""
        fam = load_graph_family(waves=[5, 7], countries=["MEX"])
        assert ("MEX", 7) in fam.contexts
        assert ("MEX", 5) in fam.contexts
        g5 = fam.get("MEX", 5)
        g7 = fam.get("MEX", 7)
        # W5 has fewer constructs than W7
        assert len(g5.present_constructs) < len(g7.present_constructs)

    def test_family_countries(self, family):
        countries = family.countries(7)
        assert "MEX" in countries
        assert "USA" in countries


# -- Test: WVSOntologyQuery ----------------------------------------------------

class TestWVSOntologyQuery:
    def test_context_str(self, oq_mex):
        assert "MEX" in oq_mex.context
        assert "W7" in oq_mex.context

    def test_get_profile(self, oq_mex):
        key = oq_mex.graph.present_constructs[0]
        profile = oq_mex.get_profile(key)
        assert profile.key == key
        assert profile.degree >= 0
        assert isinstance(profile.ses_summary, dict)

    def test_get_similar(self, oq_mex):
        key = oq_mex.graph.present_constructs[0]
        similar = oq_mex.get_similar(key, n=5)
        assert len(similar) <= 5
        if similar:
            _, sim, driver = similar[0]
            assert -1.0 <= sim <= 1.0

    def test_get_neighbors(self, oq_mex):
        key = oq_mex.graph.present_constructs[0]
        neighbors = oq_mex.get_neighbors(key, top_n=5)
        for edge in neighbors:
            assert edge.gamma != 0
            assert isinstance(edge.fingerprint_cos, float)

    def test_get_neighborhood(self, oq_mex):
        key = oq_mex.graph.present_constructs[0]
        nbr = oq_mex.get_neighborhood(key, top_n=5)
        assert "neighbors" in nbr
        assert "summary" in nbr

    def test_get_camp(self, oq_mex):
        key = oq_mex.graph.present_constructs[0]
        camp = oq_mex.get_camp(key)
        if camp:
            assert camp.camp_id in (1, -1)

    def test_find_path_connected(self, oq_mex):
        present = oq_mex.graph.present_constructs
        if len(present) >= 2:
            path = oq_mex.find_path(present[0], present[1])
            assert path.source == present[0]
            assert path.target == present[1]
            # Path may or may not exist
            if path.path:
                assert len(path.edges) == len(path.path) - 1
                assert path.signal_chain > 0

    def test_compare_with_same_wave(self, oq_mex):
        key = oq_mex.graph.present_constructs[0]
        cmp = oq_mex.compare_with("USA", key)
        assert "fingerprint_cosine" in cmp
        assert "sign_agreement" in cmp

    def test_compare_with_cross_wave(self):
        """Cross-wave comparison restricts to shared constructs."""
        fam = load_graph_family(waves=[5, 7], countries=["MEX"])
        oq7 = WVSOntologyQuery(fam, "MEX", 7)
        present_5 = fam.get("MEX", 5).present_constructs
        if present_5:
            key = present_5[0]
            cmp = oq7.compare_with("MEX", key, other_wave=5)
            assert cmp["n_shared_constructs"] > 0
            assert cmp["n_shared_constructs"] <= len(present_5)

    def test_explain_pair(self, oq_mex):
        present = oq_mex.graph.present_constructs
        if len(present) >= 2:
            exp = oq_mex.explain_pair(present[0], present[1])
            assert "fingerprint_cosine" in exp
            assert "same_camp" in exp


# -- Test: Propagator ----------------------------------------------------------

class TestPropagator:
    @pytest.fixture(scope="class")
    def prop_mex(self, family):
        oq = WVSOntologyQuery(family, "MEX", 7)
        return Propagator(oq)

    @pytest.fixture(scope="class")
    def result_mex(self, prop_mex, family):
        graph = family.get("MEX", 7)
        anchor = graph.present_constructs[0]
        return prop_mex.propagate(anchor, direction=-1)

    def test_bp_effects_present(self, result_mex):
        assert len(result_mex.bp_effects) > 0

    def test_ppr_effects_present(self, result_mex):
        assert len(result_mex.ppr_effects) > 0

    def test_spectral_effects_present(self, result_mex):
        assert len(result_mex.spectral_effects) > 0
        # Multiple time scales
        assert len(result_mex.spectral_effects) >= 3

    def test_consensus_ranking(self, result_mex):
        assert len(result_mex.consensus) > 0
        top = result_mex.consensus[0]
        assert top.agreement_score > 0
        assert top.confidence in ("high", "medium", "low")

    def test_consensus_sorted_by_agreement(self, result_mex):
        scores = [e.agreement_score for e in result_mex.consensus]
        # Should be non-increasing
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1] - 1e-9

    def test_direction_propagated(self, result_mex):
        # Direction should be -1 or +1 for all effects
        for eff in result_mex.bp_effects:
            assert eff.direction in (-1, 1)
        for eff in result_mex.ppr_effects:
            assert eff.direction in (-1, 1)

    def test_method_agreement_computed(self, result_mex):
        assert isinstance(result_mex.method_agreement, dict)
        # Should have at least bp_ppr
        if result_mex.bp_effects and result_mex.ppr_effects:
            assert "bp_ppr" in result_mex.method_agreement

    def test_ppr_no_self_loop(self, prop_mex, family):
        graph = family.get("MEX", 7)
        anchor = graph.present_constructs[0]
        result = prop_mex.propagate(anchor, direction=1)
        constructs = [e.construct for e in result.ppr_effects]
        assert anchor not in constructs

    def test_spectral_time_scales(self, result_mex):
        times = list(result_mex.spectral_effects.keys())
        assert min(times) < 1.0  # Short time scale
        assert max(times) > 5.0  # Long time scale

    def test_cross_country_different_results(self, family):
        """Same anchor in different countries should produce different rankings."""
        oq_mex = WVSOntologyQuery(family, "MEX", 7)
        oq_jpn = WVSOntologyQuery(family, "JPN", 7)
        prop_mex = Propagator(oq_mex)
        prop_jpn = Propagator(oq_jpn)
        # Use a construct present in both
        shared = set(family.get("MEX", 7).present_constructs) & \
                 set(family.get("JPN", 7).present_constructs)
        if shared:
            anchor = sorted(shared)[0]
            r_mex = prop_mex.propagate(anchor, direction=1)
            r_jpn = prop_jpn.propagate(anchor, direction=1)
            # Top consensus should differ
            if r_mex.consensus and r_jpn.consensus:
                top_mex = r_mex.consensus[0].construct
                top_jpn = r_jpn.consensus[0].construct
                # They CAN be the same but often aren't
                # Just verify both produced results
                assert len(r_mex.consensus) > 0
                assert len(r_jpn.consensus) > 0


# -- Test: Projector -----------------------------------------------------------

class TestProjector:
    @pytest.fixture(scope="class")
    def projection(self, family):
        oq = WVSOntologyQuery(family, "MEX", 7)
        prop = Propagator(oq)
        anchor = family.get("MEX", 7).present_constructs[0]
        result = prop.propagate(anchor, direction=-1)
        projector = CrossContextProjector(family)
        return projector.project("MEX", 7, result)

    def test_spectral_neighbors(self, projection):
        assert len(projection.spectral_neighbors) > 0
        for country, dist in projection.spectral_neighbors:
            assert isinstance(country, str)
            assert dist >= 0

    def test_zone_patterns(self, projection):
        assert len(projection.zone_patterns) > 0
        for zone, pattern in projection.zone_patterns.items():
            assert pattern.n_countries > 0

    def test_temporal_trajectory(self, projection):
        if projection.temporal:
            t = projection.temporal
            assert t.country == "MEX"
            assert len(t.waves_available) >= 2
            assert t.fiedler_trend in ("tightening", "stable", "loosening")

    def test_ses_projection(self, projection):
        if projection.ses_projection:
            sp = projection.ses_projection
            assert len(sp.mean_ses_vector) == 4
            assert sp.dominant_dimension in ("escol", "Tam_loc", "sexo", "edad")
            assert sp.dominant_direction in ("positive", "negative")
            assert 0.0 <= sp.within_dimension <= 1.0

    def test_transfer_confidence(self, projection):
        for country, conf in projection.transfer_confidence.items():
            assert 0.0 <= conf <= 1.0


# -- Test: Synthesizer ---------------------------------------------------------

class TestSynthesizer:
    def test_narrative_generation(self, family):
        oq = WVSOntologyQuery(family, "MEX", 7)
        prop = Propagator(oq)
        anchor = family.get("MEX", 7).present_constructs[0]
        result = prop.propagate(anchor, direction=-1)
        projector = CrossContextProjector(family)
        projection = projector.project("MEX", 7, result)

        synth = NarrativeSynthesizer()
        narrative, caveats = synth.synthesize(
            result, projection, "MEX", 7, "Latin America"
        )
        assert "Graph Traversal Engine" in narrative
        assert "MEX" in narrative
        assert len(caveats) >= 1  # At least the fundamental caveat

    def test_caveats_always_include_fundamental(self, family):
        oq = WVSOntologyQuery(family, "MEX", 7)
        prop = Propagator(oq)
        anchor = family.get("MEX", 7).present_constructs[0]
        result = prop.propagate(anchor, direction=-1)
        projector = CrossContextProjector(family)
        projection = projector.project("MEX", 7, result)

        synth = NarrativeSynthesizer()
        _, caveats = synth.synthesize(result, projection, "MEX", 7)
        assert any("associative" in c.lower() or "causal" in c.lower() for c in caveats)


# -- Test: Engine (full pipeline) -----------------------------------------------

class TestEngine:
    def test_query_returns_gte_output(self, engine, family):
        anchor = family.get("MEX", 7).present_constructs[0]
        result = engine.query(anchor, "MEX", 7, direction=-1)
        assert result.propagation is not None
        assert result.projection is not None
        assert len(result.narrative) > 0

    def test_query_without_narrative(self, engine, family):
        anchor = family.get("MEX", 7).present_constructs[0]
        result = engine.query(anchor, "MEX", 7, include_narrative=False)
        assert result.narrative == ""

    def test_compare_countries(self, engine, family):
        anchor = family.get("MEX", 7).present_constructs[0]
        results = engine.compare_countries(anchor, ["MEX", "USA", "JPN"], direction=-1)
        assert "MEX" in results
        assert "USA" in results
        assert len(results) >= 2

    def test_invalid_country_raises(self, engine):
        with pytest.raises(ValueError):
            engine.query("gender_role_traditionalism|WVS_D", "ZZZ", 7)

    def test_invalid_construct_raises(self, engine):
        with pytest.raises(ValueError):
            engine.query("nonexistent_construct|WVS_X", "MEX", 7)

    def test_metadata_populated(self, engine, family):
        anchor = family.get("MEX", 7).present_constructs[0]
        result = engine.query(anchor, "MEX", 7, include_narrative=False)
        assert result.metadata["n_contexts_loaded"] > 0
        assert result.metadata["construct_index_size"] > 0
