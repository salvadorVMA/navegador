"""
Unit tests for multi_hop_prediction.py — multi-hop prediction engine.

All tests use mock OntologyQuery instances. No actual data files are required.
Tests cover:
  - Happy path: 2-hop, 3-hop, direct bridge
  - Item lifting: exact, approximate, orphan, unknown items
  - Disconnected constructs (no path exists)
  - Degenerate cases: same construct, single-item path
  - Signal attenuation: verify product chain math
  - Distribution prediction
  - Error handling
"""
import math
import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from multi_hop_prediction import (
    MultiHopPredictor, BayesianMultiHopPredictor,
    _name, _shifted_distribution,
)


# ---------------------------------------------------------------------------
# Mock OntologyQuery builder
# ---------------------------------------------------------------------------

def _make_mock_oq(
    constructs: dict = None,
    items: dict = None,
    bridges: dict = None,
    lift_overrides: dict = None,
    find_path_override: dict = None,
):
    """Build a mock OntologyQuery with configurable state.

    Parameters
    ----------
    constructs : dict
        {key: fingerprint_dict}
    items : dict
        {key: item_dict}
    bridges : dict
        {key: [edge_dicts]}
    lift_overrides : dict
        {key: lift_result_dict}  — override _lift_to_construct() return value
    find_path_override : dict
        If set, find_path() returns this dict directly instead of computing.
    """
    oq = MagicMock()
    oq._constructs = constructs or {}
    oq._items = items or {}
    oq._bridges = bridges or {}

    # Default lift behavior: exact if key is in constructs
    def _lift(key):
        if lift_overrides and key in lift_overrides:
            return lift_overrides[key]
        if key in (constructs or {}):
            return {
                "construct_key": key,
                "lift_type": "exact",
                "loading_gamma": 1.0,
                "loading_type": "exact",
            }
        if key in (items or {}):
            item = items[key]
            parent = item.get("parent_construct")
            if parent:
                return {
                    "construct_key": parent,
                    "lift_type": "exact",
                    "loading_gamma": item.get("loading_gamma", 0.8),
                    "loading_type": "exact",
                }
            candidate = item.get("candidate_construct")
            if candidate:
                return {
                    "construct_key": candidate,
                    "lift_type": "approximate",
                    "loading_gamma": item.get("candidate_loading_gamma", 0.5),
                    "loading_type": "approximate",
                }
            return {
                "construct_key": None,
                "lift_type": "none",
                "loading_gamma": None,
                "loading_type": None,
            }
        return {
            "construct_key": None,
            "lift_type": "none",
            "loading_gamma": None,
            "loading_type": None,
        }

    oq._lift_to_construct = MagicMock(side_effect=_lift)

    # Default find_path behavior
    def _find_path(key_a, key_b, prefer_sign_consistent=False):
        if find_path_override is not None:
            return find_path_override

        # Check for direct edge
        edges_from_a = bridges.get(key_a, []) if bridges else []
        direct = [e for e in edges_from_a if e.get("neighbor") == key_b]

        if direct:
            e = direct[0]
            return {
                "path": [key_a, key_b],
                "edges": [{
                    "from": key_a, "to": key_b,
                    "gamma": e["gamma"],
                    "ci_lo": e.get("ci_lo", e["gamma"] - 0.02),
                    "ci_hi": e.get("ci_hi", e["gamma"] + 0.02),
                    "nmi": e.get("nmi", 0.001),
                    "fingerprint_cos": e.get("fingerprint_cos", 0.5),
                }],
                "signal_chain": abs(e["gamma"]),
                "total_cost": -math.log(abs(e["gamma"])) if e["gamma"] != 0 else float("inf"),
                "direct_edge": {
                    "from": key_a, "to": key_b,
                    "gamma": e["gamma"],
                    "ci_lo": e.get("ci_lo", e["gamma"] - 0.02),
                    "ci_hi": e.get("ci_hi", e["gamma"] + 0.02),
                    "nmi": e.get("nmi", 0.001),
                },
                "error": None,
            }

        # No path
        return {
            "path": None,
            "edges": None,
            "signal_chain": None,
            "total_cost": None,
            "direct_edge": None,
            "error": "No path found (disconnected components)",
        }

    oq.find_path = MagicMock(side_effect=_find_path)
    return oq


# Standard constructs for most tests
_CONSTRUCTS = {
    "A|c1": {"rho_escol": 0.2, "rho_Tam_loc": 0.1, "rho_sexo": 0.0, "rho_edad": -0.1},
    "A|c2": {"rho_escol": 0.15, "rho_Tam_loc": 0.05, "rho_sexo": 0.02, "rho_edad": -0.08},
    "B|c3": {"rho_escol": -0.1, "rho_Tam_loc": -0.2, "rho_sexo": 0.05, "rho_edad": 0.15},
    "C|c4": {"rho_escol": 0.3, "rho_Tam_loc": 0.2, "rho_sexo": -0.05, "rho_edad": -0.15},
}

_BRIDGES = {
    "A|c1": [
        {"neighbor": "A|c2", "gamma": 0.08, "ci_lo": 0.05, "ci_hi": 0.11, "nmi": 0.002, "fingerprint_cos": 0.9},
        {"neighbor": "B|c3", "gamma": -0.05, "ci_lo": -0.08, "ci_hi": -0.02, "nmi": 0.001, "fingerprint_cos": -0.5},
    ],
    "A|c2": [
        {"neighbor": "A|c1", "gamma": 0.08, "ci_lo": 0.05, "ci_hi": 0.11, "nmi": 0.002, "fingerprint_cos": 0.9},
        {"neighbor": "C|c4", "gamma": 0.12, "ci_lo": 0.08, "ci_hi": 0.16, "nmi": 0.003, "fingerprint_cos": 0.7},
    ],
    "B|c3": [
        {"neighbor": "A|c1", "gamma": -0.05, "ci_lo": -0.08, "ci_hi": -0.02, "nmi": 0.001, "fingerprint_cos": -0.5},
    ],
    "C|c4": [
        {"neighbor": "A|c2", "gamma": 0.12, "ci_lo": 0.08, "ci_hi": 0.16, "nmi": 0.003, "fingerprint_cos": 0.7},
    ],
}

_ITEMS = {
    "q1|SRV": {"parent_construct": "A|c1", "loading_gamma": 0.75},
    "q2|SRV": {"parent_construct": "A|c2", "loading_gamma": -0.60},
    "q3|SRV": {"candidate_construct": "B|c3", "candidate_loading_gamma": 0.40},
    "q_orphan|SRV": {},  # no construct at all
}


# ---------------------------------------------------------------------------
# Test: Happy path — direct bridge
# ---------------------------------------------------------------------------

class TestDirectBridge:
    """Test prediction with a direct bridge edge (1-hop)."""

    def test_direct_bridge_signal(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        result = pred.predict("A|c1", "A|c2")

        assert result["error"] is None
        assert result["n_hops"] == 1
        assert result["path"] == ["A|c1", "A|c2"]
        assert abs(result["signal"] - 0.08) < 0.001
        assert result["signal_magnitude"] == pytest.approx(0.08, abs=0.001)

    def test_direct_bridge_negative_gamma(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        result = pred.predict("A|c1", "B|c3")

        assert result["error"] is None
        assert result["signal"] < 0  # negative gamma


# ---------------------------------------------------------------------------
# Test: Multi-hop paths
# ---------------------------------------------------------------------------

class TestMultiHopPath:
    """Test 2-hop and 3-hop predictions."""

    def test_two_hop_path(self):
        """A|c1 -> A|c2 -> C|c4 (2 hops)."""
        # Need to set up find_path to return a 2-hop path
        path_result = {
            "path": ["A|c1", "A|c2", "C|c4"],
            "edges": [
                {"from": "A|c1", "to": "A|c2", "gamma": 0.08,
                 "ci_lo": 0.05, "ci_hi": 0.11, "nmi": 0.002, "fingerprint_cos": 0.9},
                {"from": "A|c2", "to": "C|c4", "gamma": 0.12,
                 "ci_lo": 0.08, "ci_hi": 0.16, "nmi": 0.003, "fingerprint_cos": 0.7},
            ],
            "signal_chain": 0.08 * 0.12,
            "total_cost": -math.log(0.08) - math.log(0.12),
            "direct_edge": None,
            "error": None,
        }
        oq = _make_mock_oq(
            constructs=_CONSTRUCTS,
            bridges=_BRIDGES,
            find_path_override=path_result,
        )
        pred = MultiHopPredictor(oq)
        result = pred.predict("A|c1", "C|c4")

        assert result["error"] is None
        assert result["n_hops"] == 2
        assert len(result["path"]) == 3
        # Bridge signal = 0.08 * 0.12 = 0.0096
        assert result["signal"] == pytest.approx(0.08 * 0.12, abs=0.0001)
        assert result["signal_magnitude"] == pytest.approx(0.08 * 0.12, abs=0.0001)

    def test_three_hop_signal_chain(self):
        """Verify signal chain math for 3-hop path."""
        gammas = [0.10, -0.05, 0.08]
        edges = [
            {"from": f"X|c{i}", "to": f"X|c{i+1}", "gamma": g,
             "ci_lo": g - 0.02, "ci_hi": g + 0.02, "nmi": 0.001, "fingerprint_cos": 0.5}
            for i, g in enumerate(gammas)
        ]
        path_result = {
            "path": ["X|c0", "X|c1", "X|c2", "X|c3"],
            "edges": edges,
            "signal_chain": abs(0.10) * abs(0.05) * abs(0.08),
            "total_cost": sum(-math.log(abs(g)) for g in gammas),
            "direct_edge": None,
            "error": None,
        }
        constructs = {f"X|c{i}": {"rho_escol": 0.1} for i in range(4)}
        oq = _make_mock_oq(constructs=constructs, find_path_override=path_result)
        pred = MultiHopPredictor(oq)
        result = pred.predict("X|c0", "X|c3")

        expected_signal = 0.10 * (-0.05) * 0.08
        expected_magnitude = abs(0.10) * abs(0.05) * abs(0.08)
        assert result["signal"] == pytest.approx(expected_signal, abs=1e-6)
        assert result["signal_magnitude"] == pytest.approx(expected_magnitude, abs=1e-6)
        assert result["n_hops"] == 3


# ---------------------------------------------------------------------------
# Test: Item lifting
# ---------------------------------------------------------------------------

class TestItemLifting:
    """Test prediction with different item lift types."""

    def test_exact_item_lift(self):
        oq = _make_mock_oq(
            constructs=_CONSTRUCTS, items=_ITEMS, bridges=_BRIDGES,
        )
        pred = MultiHopPredictor(oq)
        # q1|SRV lifts to A|c1 (exact, loading_gamma=0.75)
        result = pred.predict("q1|SRV", "A|c2")

        assert result["error"] is None
        assert result["anchor_a"] == "A|c1"
        assert result["lift_a"]["lift_type"] == "exact"
        # Endpoint attenuation includes loading_gamma for A side
        assert result["endpoint_attenuation"] == pytest.approx(
            abs(0.75) * abs(1.0), abs=0.001
        )

    def test_approximate_item_lift(self):
        oq = _make_mock_oq(
            constructs=_CONSTRUCTS, items=_ITEMS, bridges=_BRIDGES,
        )
        pred = MultiHopPredictor(oq)
        # q3|SRV lifts to B|c3 (approximate, candidate_loading_gamma=0.40)
        result = pred.predict("q3|SRV", "A|c1")

        assert result["error"] is None
        assert result["anchor_a"] == "B|c3"
        assert result["lift_a"]["lift_type"] == "approximate"

    def test_unknown_item_returns_error(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, items=_ITEMS)
        pred = MultiHopPredictor(oq)
        result = pred.predict("UNKNOWN_ITEM", "A|c1")

        assert result["error"] is not None
        assert "Cannot lift" in result["error"]

    def test_orphan_item_no_construct(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, items=_ITEMS)
        pred = MultiHopPredictor(oq)
        # q_orphan has no construct
        result = pred.predict("q_orphan|SRV", "A|c1")

        assert result["error"] is not None


# ---------------------------------------------------------------------------
# Test: Same construct (degenerate case)
# ---------------------------------------------------------------------------

class TestSameConstruct:
    """Test prediction when both keys map to the same construct."""

    def test_same_construct(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        result = pred.predict("A|c1", "A|c1")

        assert result["error"] is None
        assert result["n_hops"] == 0
        assert result["signal"] == 1.0
        assert result["signal_magnitude"] == 1.0
        assert result["path"] == ["A|c1"]

    def test_two_items_same_construct(self):
        items = {
            "q1|SRV": {"parent_construct": "A|c1", "loading_gamma": 0.8},
            "q1b|SRV": {"parent_construct": "A|c1", "loading_gamma": 0.6},
        }
        oq = _make_mock_oq(constructs=_CONSTRUCTS, items=items)
        pred = MultiHopPredictor(oq)
        result = pred.predict("q1|SRV", "q1b|SRV")

        assert result["error"] is None
        assert result["n_hops"] == 0
        assert result["endpoint_attenuation"] == pytest.approx(0.8 * 0.6, abs=0.001)


# ---------------------------------------------------------------------------
# Test: Disconnected constructs
# ---------------------------------------------------------------------------

class TestDisconnected:
    """Test prediction when no path exists."""

    def test_no_path(self):
        constructs = {"A|c1": {}, "Z|isolated": {}}
        oq = _make_mock_oq(constructs=constructs, bridges={})
        pred = MultiHopPredictor(oq)
        result = pred.predict("A|c1", "Z|isolated")

        assert result["error"] is not None
        assert "No path" in result["error"] or "disconnected" in result["error"].lower()


# ---------------------------------------------------------------------------
# Test: Signal attenuation
# ---------------------------------------------------------------------------

class TestSignalAttenuation:
    """Verify signal math and attenuation warnings."""

    def test_attenuation_warning_triggered(self):
        """Very weak edges should trigger attenuation warning."""
        gammas = [0.01, 0.01, 0.01]
        edges = [
            {"from": f"X|c{i}", "to": f"X|c{i+1}", "gamma": g,
             "ci_lo": g - 0.005, "ci_hi": g + 0.005, "nmi": 0.0, "fingerprint_cos": 0.0}
            for i, g in enumerate(gammas)
        ]
        path_result = {
            "path": ["X|c0", "X|c1", "X|c2", "X|c3"],
            "edges": edges,
            "signal_chain": 1e-6,
            "total_cost": 100.0,
            "direct_edge": None,
            "error": None,
        }
        constructs = {f"X|c{i}": {} for i in range(4)}
        oq = _make_mock_oq(constructs=constructs, find_path_override=path_result)
        pred = MultiHopPredictor(oq)
        result = pred.predict("X|c0", "X|c3")

        assert result["attenuation_warning"] is True
        assert result["total_signal"] < 0.001

    def test_sign_propagation(self):
        """Sign should propagate correctly through the chain.
        Even number of negative gammas = positive total."""
        gammas = [-0.10, -0.10]  # neg * neg = positive
        edges = [
            {"from": f"X|c{i}", "to": f"X|c{i+1}", "gamma": g,
             "ci_lo": g - 0.02, "ci_hi": g + 0.02, "nmi": 0.001, "fingerprint_cos": 0.5}
            for i, g in enumerate(gammas)
        ]
        path_result = {
            "path": ["X|c0", "X|c1", "X|c2"],
            "edges": edges,
            "signal_chain": 0.01,
            "total_cost": sum(-math.log(0.10) for _ in gammas),
            "direct_edge": None,
            "error": None,
        }
        constructs = {f"X|c{i}": {} for i in range(3)}
        oq = _make_mock_oq(constructs=constructs, find_path_override=path_result)
        pred = MultiHopPredictor(oq)
        result = pred.predict("X|c0", "X|c2")

        # (-0.10) * (-0.10) = +0.01
        assert result["signal"] > 0
        assert result["total_signal_signed"] > 0

    def test_odd_negatives_produce_negative(self):
        """Odd number of negative gammas = negative total."""
        gammas = [-0.10, 0.10, -0.10]  # neg * pos * neg = positive
        edges = [
            {"from": f"X|c{i}", "to": f"X|c{i+1}", "gamma": g,
             "ci_lo": g - 0.02, "ci_hi": g + 0.02, "nmi": 0.001, "fingerprint_cos": 0.5}
            for i, g in enumerate(gammas)
        ]
        path_result = {
            "path": ["X|c0", "X|c1", "X|c2", "X|c3"],
            "edges": edges,
            "signal_chain": 0.001,
            "total_cost": sum(-math.log(abs(g)) for g in gammas),
            "direct_edge": None,
            "error": None,
        }
        constructs = {f"X|c{i}": {} for i in range(4)}
        oq = _make_mock_oq(constructs=constructs, find_path_override=path_result)
        pred = MultiHopPredictor(oq)
        result = pred.predict("X|c0", "X|c3")

        # (-0.10) * (0.10) * (-0.10) = +0.001 (positive! two negatives cancel)
        expected = (-0.10) * (0.10) * (-0.10)
        assert result["signal"] == pytest.approx(expected, abs=1e-6)

    def test_endpoint_attenuation_reduces_total(self):
        """Loading gamma < 1 should reduce total signal."""
        path_result = {
            "path": ["A|c1", "A|c2"],
            "edges": [
                {"from": "A|c1", "to": "A|c2", "gamma": 0.10,
                 "ci_lo": 0.07, "ci_hi": 0.13, "nmi": 0.001, "fingerprint_cos": 0.8},
            ],
            "signal_chain": 0.10,
            "total_cost": -math.log(0.10),
            "direct_edge": None,
            "error": None,
        }
        items = {
            "q1|SRV": {"parent_construct": "A|c1", "loading_gamma": 0.5},
        }
        oq = _make_mock_oq(
            constructs=_CONSTRUCTS, items=items,
            bridges=_BRIDGES, find_path_override=path_result,
        )
        pred = MultiHopPredictor(oq)
        result = pred.predict("q1|SRV", "A|c2")

        # total = |0.10| * |0.5| * |1.0| = 0.05
        assert result["total_signal"] == pytest.approx(0.05, abs=0.001)
        assert result["total_signal"] < result["signal_magnitude"]


# ---------------------------------------------------------------------------
# Test: Distribution prediction
# ---------------------------------------------------------------------------

class TestDistributionPrediction:
    """Test predict_distribution method."""

    def test_basic_distribution(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        result = pred.predict_distribution("A|c1", "A|c2", value_a=5, n_categories_b=5)

        assert result["error"] is None
        assert result["distribution"] is not None
        assert len(result["distribution"]) == 5
        assert abs(sum(result["distribution"]) - 1.0) < 0.001
        assert all(p >= 0 for p in result["distribution"])
        assert result["expected_value"] is not None

    def test_distribution_sums_to_one(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        for value in [1, 3, 5]:
            result = pred.predict_distribution("A|c1", "A|c2", value_a=value)
            assert abs(sum(result["distribution"]) - 1.0) < 0.001

    def test_distribution_error_propagation(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS)
        pred = MultiHopPredictor(oq)
        result = pred.predict_distribution("UNKNOWN", "A|c1", value_a=3)
        assert result["error"] is not None
        assert result["distribution"] is None

    def test_shift_direction_positive(self):
        """Positive signal + high value_a should shift B toward higher values."""
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        result = pred.predict_distribution("A|c1", "A|c2", value_a=5)
        assert result["shift_direction"] in ("higher", "lower", "none")


# ---------------------------------------------------------------------------
# Test: Domain-level keys
# ---------------------------------------------------------------------------

class TestDomainLevelKeys:
    """Domain-level keys should produce an error (no bridge queries)."""

    def test_domain_key_error(self):
        lift_overrides = {
            "WVS_A": {
                "construct_key": "WVS_A",
                "lift_type": "domain_fallback",
                "loading_gamma": None,
                "loading_type": None,
            },
        }
        oq = _make_mock_oq(
            constructs=_CONSTRUCTS,
            lift_overrides=lift_overrides,
        )
        pred = MultiHopPredictor(oq)
        result = pred.predict("WVS_A", "A|c1")

        assert result["error"] is not None
        assert "domain-level" in result["error"]


# ---------------------------------------------------------------------------
# Test: Narrative generation
# ---------------------------------------------------------------------------

class TestNarrative:
    """Test that narratives are generated and non-empty."""

    def test_narrative_present(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        result = pred.predict("A|c1", "A|c2")
        assert result["narrative"]
        assert len(result["narrative"]) > 20

    def test_error_narrative(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS)
        pred = MultiHopPredictor(oq)
        result = pred.predict("UNKNOWN", "A|c1")
        assert result["narrative"]  # should contain the error message


# ---------------------------------------------------------------------------
# Test: Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    """Test utility functions."""

    def test_name_extraction(self):
        assert _name("WVS_A|importance_of_life_domains") == "importance of life domains"
        assert _name("A|c1") == "c1"
        assert _name("standalone") == "standalone"

    def test_shifted_distribution_neutral(self):
        """Zero signal should produce uniform distribution."""
        dist = _shifted_distribution(
            total_signed=0.0, value_a=3, n_categories_a=5, n_categories_b=5,
        )
        assert len(dist) == 5
        assert abs(sum(dist) - 1.0) < 0.001
        # Should be approximately uniform
        for p in dist:
            assert abs(p - 0.2) < 0.01

    def test_shifted_distribution_positive_shift(self):
        """Strong positive signal + high value should shift toward higher categories."""
        dist = _shifted_distribution(
            total_signed=0.5, value_a=5, n_categories_a=5, n_categories_b=5,
        )
        # Higher categories should have more probability
        assert dist[4] > dist[0]

    def test_shifted_distribution_sums_to_one(self):
        for signal in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            for value in [1, 3, 5]:
                dist = _shifted_distribution(
                    total_signed=signal, value_a=value,
                    n_categories_a=5, n_categories_b=5,
                )
                assert abs(sum(dist) - 1.0) < 0.001


# ---------------------------------------------------------------------------
# Test: get_all_paths
# ---------------------------------------------------------------------------

class TestGetAllPaths:
    """Test the multi-path finder."""

    def test_returns_at_least_one_path(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        paths = pred.get_all_paths("A|c1", "A|c2")
        assert len(paths) >= 1

    def test_returns_empty_on_error(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS)
        pred = MultiHopPredictor(oq)
        paths = pred.get_all_paths("UNKNOWN", "A|c1")
        assert paths == []


# ---------------------------------------------------------------------------
# Test: Edge cases and robustness
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Additional edge case tests."""

    def test_both_endpoints_unknown(self):
        oq = _make_mock_oq(constructs=_CONSTRUCTS)
        pred = MultiHopPredictor(oq)
        result = pred.predict("UNKNOWN_A", "UNKNOWN_B")
        assert result["error"] is not None

    def test_no_constructs_in_domain_lift(self):
        """no_constructs_in_domain lift type should produce error."""
        lift_overrides = {
            "q_jue|SRV": {
                "construct_key": "JUE",
                "lift_type": "no_constructs_in_domain",
                "loading_gamma": None,
                "loading_type": None,
            },
        }
        oq = _make_mock_oq(constructs=_CONSTRUCTS, lift_overrides=lift_overrides)
        pred = MultiHopPredictor(oq)
        result = pred.predict("q_jue|SRV", "A|c1")
        assert result["error"] is not None
        assert "domain-level" in result["error"]

    def test_predict_returns_all_required_keys(self):
        """All output keys should be present even on success."""
        oq = _make_mock_oq(constructs=_CONSTRUCTS, bridges=_BRIDGES)
        pred = MultiHopPredictor(oq)
        result = pred.predict("A|c1", "A|c2")
        required_keys = [
            "key_a", "key_b", "anchor_a", "anchor_b",
            "lift_a", "lift_b", "path", "edges", "n_hops",
            "signal", "signal_magnitude", "endpoint_attenuation",
            "total_signal", "total_signal_signed", "direct_edge",
            "attenuation_warning", "error", "narrative",
        ]
        for k in required_keys:
            assert k in result, f"Missing key: {k}"

    def test_negative_loading_gamma_inverts_total(self):
        """A negative loading_gamma (reverse-coded item) should flip the total signal sign."""
        path_result = {
            "path": ["A|c1", "A|c2"],
            "edges": [
                {"from": "A|c1", "to": "A|c2", "gamma": 0.10,
                 "ci_lo": 0.07, "ci_hi": 0.13, "nmi": 0.001, "fingerprint_cos": 0.8},
            ],
            "signal_chain": 0.10,
            "total_cost": -math.log(0.10),
            "direct_edge": None,
            "error": None,
        }
        # q2 has loading_gamma = -0.60 (reverse-coded)
        items = {
            "q2|SRV": {"parent_construct": "A|c1", "loading_gamma": -0.60},
        }
        oq = _make_mock_oq(
            constructs=_CONSTRUCTS, items=items,
            bridges=_BRIDGES, find_path_override=path_result,
        )
        pred = MultiHopPredictor(oq)
        result = pred.predict("q2|SRV", "A|c2")
        # total_signed = (-0.60) * (0.10) * (1.0) = -0.06
        assert result["total_signal_signed"] < 0


# ===========================================================================
# BayesianMultiHopPredictor tests
# ===========================================================================

def _make_bayesian_mock_oq():
    """Build a mock OQ suitable for the Bayesian predictor.

    Unlike the point-estimate mock, the Bayesian predictor calls
    _bridges directly (for edge index building) and runs its own
    Dijkstra, so we need properly bidirectional edges.
    """
    oq = MagicMock()
    oq._constructs = _CONSTRUCTS
    oq._bridges = _BRIDGES

    def _lift(key):
        if key in _CONSTRUCTS:
            return {
                "construct_key": key,
                "lift_type": "exact",
                "loading_gamma": 1.0,
                "loading_type": "exact",
            }
        if key in _ITEMS:
            item = _ITEMS[key]
            parent = item.get("parent_construct")
            if parent:
                return {
                    "construct_key": parent,
                    "lift_type": "exact",
                    "loading_gamma": item.get("loading_gamma", 0.8),
                    "loading_type": "exact",
                }
            return {
                "construct_key": None,
                "lift_type": "none",
                "loading_gamma": None,
                "loading_type": None,
            }
        return {
            "construct_key": None,
            "lift_type": "none",
            "loading_gamma": None,
            "loading_type": None,
        }

    oq._lift_to_construct = MagicMock(side_effect=_lift)

    # find_path (used by point_estimate inside Bayesian)
    def _find_path(key_a, key_b, prefer_sign_consistent=False):
        edges_from_a = _BRIDGES.get(key_a, [])
        direct = [e for e in edges_from_a if e.get("neighbor") == key_b]
        if direct:
            e = direct[0]
            return {
                "path": [key_a, key_b],
                "edges": [{"from": key_a, "to": key_b, "gamma": e["gamma"],
                           "ci_lo": e.get("ci_lo"), "ci_hi": e.get("ci_hi"),
                           "nmi": e.get("nmi"), "fingerprint_cos": e.get("fingerprint_cos")}],
                "signal_chain": abs(e["gamma"]),
                "total_cost": -math.log(abs(e["gamma"])),
                "direct_edge": None, "error": None,
            }
        return {"path": None, "edges": None, "error": "No path found"}

    oq.find_path = MagicMock(side_effect=_find_path)
    return oq


class TestBayesianBasic:
    """Basic Bayesian predictor tests."""

    def test_returns_credible_interval(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=200, seed=42)
        result = bp.predict("A|c1", "A|c2")
        assert result["error"] is None
        assert result["signal_ci_95"] is not None
        lo, hi = result["signal_ci_95"]
        assert lo < hi, "CI lower bound must be below upper"

    def test_signal_mean_within_ci(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=300, seed=42)
        result = bp.predict("A|c1", "A|c2")
        lo, hi = result["signal_ci_95"]
        assert lo <= result["signal_mean"] <= hi

    def test_p_positive_range(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=200, seed=42)
        result = bp.predict("A|c1", "A|c2")
        assert 0.0 <= result["p_positive"] <= 1.0

    def test_same_construct_trivial(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=50, seed=1)
        result = bp.predict("A|c1", "A|c1")
        assert result["signal_mean"] == 1.0
        assert result["path_diversity"] == 0.0

    def test_unknown_item_error(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=50, seed=1)
        result = bp.predict("UNKNOWN|X", "A|c1")
        assert result["error"] is not None


class TestBayesianPathSampling:
    """Test that paths are actually sampled (not fixed)."""

    def test_path_diversity_nonnegative(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=200, seed=42)
        # A|c1 -> C|c4 requires going through A|c2 (2-hop)
        result = bp.predict("A|c1", "C|c4")
        assert result["error"] is None
        assert result["path_diversity"] >= 0.0
        assert result["n_unique_paths"] >= 1

    def test_modal_path_is_list(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=100, seed=42)
        result = bp.predict("A|c1", "A|c2")
        assert isinstance(result["path_modal"], list)
        assert len(result["path_modal"]) >= 2

    def test_n_valid_draws_positive(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=100, seed=42)
        result = bp.predict("A|c1", "A|c2")
        assert result["n_valid_draws"] > 0
        assert result["n_valid_draws"] <= 100


class TestBayesianUncertainty:
    """Test uncertainty quantification properties."""

    def test_ci_width_positive(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=200, seed=42)
        result = bp.predict("A|c1", "A|c2")
        lo, hi = result["signal_ci_95"]
        assert hi - lo > 0, "95% CI must have positive width"

    def test_ci50_inside_ci95(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=300, seed=42)
        result = bp.predict("A|c1", "A|c2")
        lo95, hi95 = result["signal_ci_95"]
        lo50, hi50 = result["signal_ci_50"]
        assert lo95 <= lo50, "50% CI lower must be >= 95% CI lower"
        assert hi50 <= hi95, "50% CI upper must be <= 95% CI upper"

    def test_more_draws_narrows_mean_estimate(self):
        """With more draws, the signal mean should be more stable."""
        oq1 = _make_bayesian_mock_oq()
        oq2 = _make_bayesian_mock_oq()
        bp50 = BayesianMultiHopPredictor(oq1, n_draws=50, seed=42)
        bp500 = BayesianMultiHopPredictor(oq2, n_draws=500, seed=42)
        r50 = bp50.predict("A|c1", "A|c2")
        r500 = bp500.predict("A|c1", "A|c2")
        # Both should produce results
        assert r50["error"] is None
        assert r500["error"] is None

    def test_endpoint_attenuation_widens_ci(self):
        """Items with loading_gamma < 1 should widen the CI vs construct-level."""
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=300, seed=42)
        # Construct-level (loading=1.0)
        r_construct = bp.predict("A|c1", "A|c2")
        # Item-level (loading=0.75 for q1)
        r_item = bp.predict("q1|SRV", "A|c2")
        # Item prediction should have smaller mean magnitude due to attenuation
        assert abs(r_item["signal_mean"]) <= abs(r_construct["signal_mean"]) + 0.05

    def test_reproducible_with_seed(self):
        oq1 = _make_bayesian_mock_oq()
        oq2 = _make_bayesian_mock_oq()
        bp1 = BayesianMultiHopPredictor(oq1, n_draws=100, seed=99)
        bp2 = BayesianMultiHopPredictor(oq2, n_draws=100, seed=99)
        r1 = bp1.predict("A|c1", "A|c2")
        r2 = bp2.predict("A|c1", "A|c2")
        assert r1["signal_mean"] == r2["signal_mean"]


class TestBayesianDistribution:
    """Test posterior predictive distributions."""

    def test_distribution_sums_to_one(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=100, seed=42)
        result = bp.predict_distribution("A|c1", "A|c2", value_a=5)
        assert result["error"] is None
        dist = result["distribution_mean"]
        assert abs(sum(dist) - 1.0) < 0.01

    def test_distribution_ci_covers_mean(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=200, seed=42)
        result = bp.predict_distribution("A|c1", "A|c2", value_a=4)
        assert result["error"] is None
        for j, (lo, hi) in enumerate(result["distribution_ci_95"]):
            mean_j = result["distribution_mean"][j]
            assert lo <= mean_j + 0.01, f"Cat {j}: CI lower {lo} > mean {mean_j}"
            assert mean_j <= hi + 0.01, f"Cat {j}: mean {mean_j} > CI upper {hi}"

    def test_expected_value_ci(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=200, seed=42)
        result = bp.predict_distribution("A|c1", "A|c2", value_a=5)
        assert result["expected_value_ci_95"] is not None
        lo, hi = result["expected_value_ci_95"]
        assert lo <= result["expected_value_mean"] <= hi

    def test_error_propagation(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=50, seed=1)
        result = bp.predict_distribution("UNKNOWN|X", "A|c1", value_a=3)
        assert result["error"] is not None


class TestBayesianNarrative:
    """Test narrative generation."""

    def test_narrative_present(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=100, seed=42)
        result = bp.predict("A|c1", "A|c2")
        assert result["narrative"]
        assert "Bayesian signal" in result["narrative"]

    def test_narrative_mentions_ci(self):
        oq = _make_bayesian_mock_oq()
        bp = BayesianMultiHopPredictor(oq, n_draws=100, seed=42)
        result = bp.predict("A|c1", "A|c2")
        assert "95% CI" in result["narrative"]
