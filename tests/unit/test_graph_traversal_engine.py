"""
Unit tests for the Graph Traversal Engine (Phase 0 + Phase 1).

Tests cover:
  - Context dataclasses and Fingerprint operations
  - Data loader: weight matrices, fingerprints, camps, MP outputs, TDA features
  - WVSOntologyQuery: profiles, neighbors, paths, camps, cross-country comparison
  - Edge cases: missing data, empty graphs, unreachable paths

Uses real data (requires pre-computed Phase 0 outputs in data/gte/).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure project root is on path
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


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def manifest():
    return load_manifest()


@pytest.fixture(scope="module")
def mex_graph(manifest):
    return load_context_graph("MEX", 7, manifest=manifest)


@pytest.fixture(scope="module")
def family():
    """Load a small family for cross-country tests."""
    return load_graph_family(
        countries=["MEX", "USA", "DEU", "JPN", "BRA"],
        load_mp=True,
    )


@pytest.fixture(scope="module")
def oq_mex(family):
    return WVSOntologyQuery(family, country="MEX", wave=7)


@pytest.fixture(scope="module")
def oq_usa(family):
    return WVSOntologyQuery(family, country="USA", wave=7)


# ── Test: Context Dataclasses ──────────────────────────────────────────────

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
        fp = Fingerprint(
            rho_escol=0.5, rho_Tam_loc=-0.3,
            rho_sexo=0.1, rho_edad=-0.2,
            ses_magnitude=0.3, dominant_dim="escol",
        )
        v = fp.to_vec()
        assert v.shape == (4,)
        np.testing.assert_allclose(v, [0.5, -0.3, 0.1, -0.2])

    def test_to_unit_vec(self):
        fp = Fingerprint(
            rho_escol=0.6, rho_Tam_loc=0.0,
            rho_sexo=0.0, rho_edad=0.8,
            ses_magnitude=0.5, dominant_dim="edad",
        )
        uv = fp.to_unit_vec()
        assert uv is not None
        np.testing.assert_almost_equal(np.linalg.norm(uv), 1.0)

    def test_zero_fingerprint_returns_none(self):
        fp = Fingerprint(
            rho_escol=0.0, rho_Tam_loc=0.0,
            rho_sexo=0.0, rho_edad=0.0,
            ses_magnitude=0.0, dominant_dim="",
        )
        assert fp.to_unit_vec() is None

    def test_frozen(self):
        fp = Fingerprint(
            rho_escol=0.5, rho_Tam_loc=0.0,
            rho_sexo=0.0, rho_edad=0.0,
            ses_magnitude=0.25, dominant_dim="escol",
        )
        with pytest.raises(AttributeError):
            fp.rho_escol = 0.9


class TestCampAssignment:
    def test_camp_fields(self):
        camp = CampAssignment(
            camp_id=1, camp_name="cosmopolitan",
            confidence=0.85, frustrated_ratio=0.05,
            n_triangles=100, is_boundary=False,
        )
        assert camp.camp_id == 1
        assert not camp.is_boundary


# ── Test: Data Loader ──────────────────────────────────────────────────────

class TestManifest:
    def test_manifest_structure(self, manifest):
        assert "countries" in manifest
        assert "construct_index" in manifest
        assert "country_zone" in manifest
        assert len(manifest["countries"]) == 66
        assert manifest["n_constructs"] == 55

    def test_construct_key_format(self, manifest):
        for key in manifest["construct_index"]:
            assert "|" in key, f"Construct key should have | separator: {key}"
            name, domain = key.split("|", 1)
            assert domain.startswith("WVS_"), f"Domain should start with WVS_: {domain}"


class TestLoadContextGraph:
    def test_mex_loads(self, mex_graph):
        assert mex_graph.context.country == "MEX"
        assert mex_graph.context.wave == 7
        assert mex_graph.context.zone == "Latin America"

    def test_weight_matrix_shape(self, mex_graph):
        assert mex_graph.weight_matrix.shape == (55, 55)

    def test_weight_matrix_symmetric(self, mex_graph):
        W = mex_graph.weight_matrix
        # Where both values are non-NaN, they should be equal (symmetric)
        mask = ~np.isnan(W) & ~np.isnan(W.T)
        np.testing.assert_allclose(W[mask], W.T[mask], atol=1e-10)

    def test_diagonal_is_nan_or_zero(self, mex_graph):
        diag = np.diag(mex_graph.weight_matrix)
        assert all(np.isnan(d) or d == 0.0 for d in diag)

    def test_fingerprints_loaded(self, mex_graph):
        assert len(mex_graph.fingerprints) == 55
        for key, fp in mex_graph.fingerprints.items():
            assert isinstance(fp, Fingerprint)
            assert fp.ses_magnitude >= 0

    def test_camps_loaded(self, mex_graph):
        assert len(mex_graph.camps) == 55
        camp_ids = {c.camp_id for c in mex_graph.camps.values()}
        assert camp_ids == {-1, 1}  # Both camps present

    def test_fiedler_positive(self, mex_graph):
        assert mex_graph.fiedler_value > 0

    def test_significant_edges_positive(self, mex_graph):
        assert mex_graph.n_significant_edges > 0

    def test_bp_lift_loaded(self, mex_graph):
        assert mex_graph.bp_lift_matrix is not None
        assert mex_graph.bp_lift_matrix.shape == (55, 55)

    def test_ppr_scores_loaded(self, mex_graph):
        assert mex_graph.ppr_hub_scores is not None
        assert len(mex_graph.ppr_hub_scores) == 55

    def test_spectral_loaded(self, mex_graph):
        assert mex_graph.spectral_eigenvalues is not None
        assert len(mex_graph.spectral_eigenvalues) == 55


class TestContextGraphMethods:
    def test_construct_index_found(self, mex_graph):
        idx = mex_graph.construct_index("gender_role_traditionalism|WVS_D")
        assert idx >= 0

    def test_construct_index_not_found(self, mex_graph):
        idx = mex_graph.construct_index("nonexistent|WVS_Z")
        assert idx == -1

    def test_get_edge_exists(self, mex_graph):
        # gender_role_traditionalism should have at least one edge
        key = "gender_role_traditionalism|WVS_D"
        neighbors = mex_graph.get_significant_neighbors(key)
        assert len(neighbors) > 0
        neighbor_key = neighbors[0][0]
        edge = mex_graph.get_edge(key, neighbor_key)
        assert edge is not None
        assert isinstance(edge, float)

    def test_get_edge_missing(self, mex_graph):
        edge = mex_graph.get_edge("nonexistent|WVS_Z", "also_nonexistent|WVS_Z")
        assert edge is None

    def test_significant_neighbors_sorted(self, mex_graph):
        key = "gender_role_traditionalism|WVS_D"
        neighbors = mex_graph.get_significant_neighbors(key)
        gammas = [abs(g) for _, g in neighbors]
        assert gammas == sorted(gammas, reverse=True)

    def test_significant_neighbors_threshold(self, mex_graph):
        key = "gender_role_traditionalism|WVS_D"
        all_n = mex_graph.get_significant_neighbors(key, min_abs_gamma=0.0)
        high_n = mex_graph.get_significant_neighbors(key, min_abs_gamma=0.02)
        assert len(high_n) <= len(all_n)
        for _, g in high_n:
            assert abs(g) >= 0.02


class TestLoadGraphFamily:
    def test_family_contexts(self, family):
        assert len(family.contexts) == 5  # MEX, USA, DEU, JPN, BRA

    def test_family_spectral_distances(self, family):
        assert family.spectral_distances is not None
        assert family.spectral_countries is not None
        # Should be square
        n = len(family.spectral_countries)
        assert family.spectral_distances.shape == (n, n)

    def test_spectral_neighbors(self, family):
        neighbors = family.spectral_neighbors("MEX", n=3)
        assert len(neighbors) <= 3
        for country, dist in neighbors:
            assert isinstance(country, str)
            assert dist >= 0

    def test_family_descriptions(self, family):
        assert family.construct_descriptions is not None
        assert len(family.construct_descriptions) == 56

    def test_family_get(self, family):
        graph = family.get("MEX", 7)
        assert graph is not None
        assert graph.context.country == "MEX"

    def test_family_get_missing(self, family):
        graph = family.get("XYZ", 7)
        assert graph is None

    def test_family_countries(self, family):
        countries = family.countries(wave=7)
        assert "MEX" in countries
        assert "USA" in countries
        assert len(countries) == 5


# ── Test: WVSOntologyQuery ─────────────────────────────────────────────────

class TestWVSOntologyQuery:
    def test_init(self, oq_mex):
        assert oq_mex.context == "MEX_W7"

    def test_init_missing_country(self, family):
        with pytest.raises(ValueError, match="No context graph"):
            WVSOntologyQuery(family, country="XYZ", wave=7)


class TestGetProfile:
    def test_known_construct(self, oq_mex):
        profile = oq_mex.get_profile("gender_role_traditionalism|WVS_D")
        assert profile.key == "gender_role_traditionalism|WVS_D"
        assert profile.context_str == "MEX_W7"
        assert profile.fingerprint is not None
        assert profile.camp is not None
        assert profile.degree > 0
        assert len(profile.ses_summary) == 4

    def test_ses_summary_has_all_dims(self, oq_mex):
        profile = oq_mex.get_profile("gender_role_traditionalism|WVS_D")
        for dim in ["escol", "Tam_loc", "sexo", "edad"]:
            assert dim in profile.ses_summary


class TestGetSimilar:
    def test_returns_list(self, oq_mex):
        similar = oq_mex.get_similar("gender_role_traditionalism|WVS_D", n=5)
        assert len(similar) <= 5
        for key, sim, driver in similar:
            assert isinstance(key, str)
            assert -1 <= sim <= 1

    def test_sorted_descending(self, oq_mex):
        similar = oq_mex.get_similar("gender_role_traditionalism|WVS_D", n=10)
        sims = [s for _, s, _ in similar]
        assert sims == sorted(sims, reverse=True)


class TestGetNeighbors:
    def test_returns_edges(self, oq_mex):
        edges = oq_mex.get_neighbors("gender_role_traditionalism|WVS_D")
        assert len(edges) > 0
        for e in edges:
            assert e.source == "gender_role_traditionalism|WVS_D"
            assert isinstance(e.gamma, float)

    def test_threshold_filters(self, oq_mex):
        all_e = oq_mex.get_neighbors("gender_role_traditionalism|WVS_D")
        high_e = oq_mex.get_neighbors(
            "gender_role_traditionalism|WVS_D", min_abs_gamma=0.02
        )
        assert len(high_e) <= len(all_e)

    def test_top_n_limits(self, oq_mex):
        edges = oq_mex.get_neighbors(
            "gender_role_traditionalism|WVS_D", top_n=3
        )
        assert len(edges) <= 3


class TestGetNeighborhood:
    def test_neighborhood_structure(self, oq_mex):
        nh = oq_mex.get_neighborhood(
            "gender_role_traditionalism|WVS_D", min_abs_gamma=0.01
        )
        assert nh["key"] == "gender_role_traditionalism|WVS_D"
        assert nh["context"] == "MEX_W7"
        assert len(nh["neighbors"]) > 0
        summary = nh["summary"]
        assert summary["n_neighbors"] > 0
        assert "domain_distribution" in summary
        assert "strongest_edge" in summary


class TestGetCamp:
    def test_known_construct(self, oq_mex):
        camp = oq_mex.get_camp("gender_role_traditionalism|WVS_D")
        assert camp is not None
        assert camp.camp_id in (-1, 1)
        assert camp.camp_name in ("cosmopolitan", "tradition")

    def test_unknown_construct(self, oq_mex):
        camp = oq_mex.get_camp("nonexistent|WVS_Z")
        assert camp is None

    def test_camp_members(self, oq_mex):
        cosmo = oq_mex.get_camp_members(1)
        trad = oq_mex.get_camp_members(-1)
        assert len(cosmo) > 0
        assert len(trad) > 0
        assert len(cosmo) + len(trad) == 55

    def test_frustrated_nodes(self, oq_mex):
        frustrated = oq_mex.get_frustrated_nodes(min_frustrated_ratio=0.05)
        # May or may not have frustrated nodes, but should return list
        assert isinstance(frustrated, list)


class TestFindPath:
    def test_path_exists(self, oq_mex):
        path = oq_mex.find_path(
            "gender_role_traditionalism|WVS_D",
            "science_skepticism|WVS_I",
        )
        assert len(path.path) >= 2
        assert path.path[0] == "gender_role_traditionalism|WVS_D"
        assert path.path[-1] == "science_skepticism|WVS_I"
        assert path.signal_chain > 0
        assert path.path_sign in (-1, 1)

    def test_path_edges_match(self, oq_mex):
        path = oq_mex.find_path(
            "gender_role_traditionalism|WVS_D",
            "democratic_values_importance|WVS_E",
        )
        assert len(path.edges) == len(path.path) - 1
        # Edges should chain correctly
        for i, edge in enumerate(path.edges):
            assert edge.source == path.path[i]
            assert edge.target == path.path[i + 1]

    def test_signal_chain_product(self, oq_mex):
        path = oq_mex.find_path(
            "gender_role_traditionalism|WVS_D",
            "democratic_values_importance|WVS_E",
        )
        product = 1.0
        for e in path.edges:
            product *= abs(e.gamma)
        np.testing.assert_almost_equal(path.signal_chain, product, decimal=10)

    def test_direct_edge_returned(self, oq_mex):
        # Use a pair known to have a direct edge
        key = "gender_role_traditionalism|WVS_D"
        neighbors = oq_mex.get_neighbors(key, top_n=1)
        if neighbors:
            path = oq_mex.find_path(key, neighbors[0].target)
            assert path.direct_edge is not None

    def test_unknown_construct_raises(self, oq_mex):
        with pytest.raises(ValueError):
            oq_mex.find_path("nonexistent|WVS_Z", "gender_role_traditionalism|WVS_D")

    def test_attenuation_warning(self, oq_mex):
        # Long paths should have attenuation warning
        path = oq_mex.find_path(
            "gender_role_traditionalism|WVS_D",
            "science_skepticism|WVS_I",
        )
        # Just check the flag exists and is bool
        assert isinstance(path.attenuation_warning, bool)


class TestExplainPair:
    def test_explain_known_pair(self, oq_mex):
        result = oq_mex.explain_pair(
            "gender_role_traditionalism|WVS_D",
            "democratic_values_importance|WVS_E",
        )
        assert result["context"] == "MEX_W7"
        assert isinstance(result["fingerprint_cosine"], float)
        # shared_driver may be None if one fingerprint is zero-magnitude
        assert result["same_camp"] is not None

    def test_explain_has_path_info(self, oq_mex):
        result = oq_mex.explain_pair(
            "gender_role_traditionalism|WVS_D",
            "democratic_values_importance|WVS_E",
        )
        assert result["path_length"] is not None
        assert result["signal_chain"] is not None


class TestCompareWith:
    def test_compare_mex_usa(self, oq_mex):
        result = oq_mex.compare_with(
            "USA", "gender_role_traditionalism|WVS_D"
        )
        assert result["context_a"] == "MEX_W7"
        assert result["context_b"] == "USA_W7"
        assert isinstance(result["fingerprint_cosine"], float)
        assert isinstance(result["camp_agreement"], bool)
        assert isinstance(result["neighbor_jaccard"], float)
        assert isinstance(result["sign_agreement"], float)

    def test_compare_missing_country(self, oq_mex):
        result = oq_mex.compare_with(
            "XYZ", "gender_role_traditionalism|WVS_D"
        )
        assert "error" in result

    def test_compare_different_countries(self, oq_mex):
        """Different countries may have different camps for same construct."""
        r1 = oq_mex.compare_with("USA", "gender_role_traditionalism|WVS_D")
        r2 = oq_mex.compare_with("JPN", "gender_role_traditionalism|WVS_D")
        # Just verify both return valid results
        assert "fingerprint_cosine" in r1
        assert "fingerprint_cosine" in r2


# ── Test: Fingerprint Sign Prediction ──────────────────────────────────────

class TestFingerprintSignPrediction:
    """
    Test the core geometric property: fingerprint dot product predicts γ sign.
    In los_mex this holds at 99.4%. Check it per-country.
    """
    def test_sign_prediction_mex(self, oq_mex):
        """Fingerprint dot product should predict γ sign at high accuracy for MEX."""
        graph = oq_mex.graph
        agree = 0
        total = 0
        for i, key_i in enumerate(graph.constructs):
            fp_i = graph.fingerprints.get(key_i)
            if not fp_i:
                continue
            vi = fp_i.to_vec()
            for j in range(i + 1, len(graph.constructs)):
                key_j = graph.constructs[j]
                fp_j = graph.fingerprints.get(key_j)
                if not fp_j:
                    continue
                gamma = graph.weight_matrix[i, j]
                if np.isnan(gamma) or abs(gamma) < 1e-10:
                    continue
                vj = fp_j.to_vec()
                dot = np.dot(vi, vj)
                if abs(dot) < 1e-10:
                    continue
                total += 1
                if np.sign(dot) == np.sign(gamma):
                    agree += 1

        accuracy = agree / total if total > 0 else 0
        # Should be >90% for Mexico (99.4% was los_mex; WVS may be slightly lower)
        assert accuracy > 0.85, f"Sign prediction accuracy {accuracy:.1%} < 85%"


# ── Test: Phase 0 Output Files ─────────────────────────────────────────────

class TestPhase0Outputs:
    def test_fingerprint_files_exist(self):
        fp_dir = ROOT / "data" / "gte" / "fingerprints"
        files = list(fp_dir.glob("*.json"))
        # 66 country files + 1 summary
        assert len(files) >= 67

    def test_camp_files_exist(self):
        camp_dir = ROOT / "data" / "gte" / "camps"
        files = list(camp_dir.glob("*.json"))
        assert len(files) >= 66

    def test_construct_descriptions_exist(self):
        path = ROOT / "data" / "gte" / "construct_descriptions.json"
        assert path.exists()
        with open(path) as f:
            data = json.load(f)
        assert data["n_constructs"] >= 55

    def test_fingerprint_structure(self):
        fp_path = ROOT / "data" / "gte" / "fingerprints" / "MEX.json"
        with open(fp_path) as f:
            data = json.load(f)
        assert data["country"] == "MEX"
        assert data["wave"] == 7
        assert data["n_constructs"] > 0
        # Check one construct
        first_key = list(data["constructs"].keys())[0]
        fp = data["constructs"][first_key]
        assert "rho_escol" in fp
        assert "rho_Tam_loc" in fp
        assert "ses_magnitude" in fp
        assert "dominant_dim" in fp

    def test_camp_structure(self):
        camp_path = ROOT / "data" / "gte" / "camps" / "MEX.json"
        with open(camp_path) as f:
            data = json.load(f)
        assert data["country"] == "MEX"
        assert "fiedler_value" in data
        assert "structural_balance" in data
        assert "constructs" in data
        first_key = list(data["constructs"].keys())[0]
        camp = data["constructs"][first_key]
        assert camp["camp_id"] in (-1, 1)
        assert camp["camp_name"] in ("cosmopolitan", "tradition")
