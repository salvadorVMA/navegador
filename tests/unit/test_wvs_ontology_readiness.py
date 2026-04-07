"""
Unit tests for WVS ontology readiness — validates WVS data integrity
and cross-study alignment before building a WVS OntologyQuery.
"""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DATA = ROOT / "data" / "results"
NAVEGADOR_DATA = Path("/workspaces/navegador_data")
NAVEGADOR_DATA_RESULTS = NAVEGADOR_DATA / "data" / "results"
TDA = ROOT / "data" / "tda"

VALID_DIMS = {"escol", "Tam_loc", "sexo", "edad"}


class TestWVSConstructManifest(unittest.TestCase):
    """Validate wvs_construct_manifest.json structure."""

    @classmethod
    def setUpClass(cls):
        with open(DATA / "wvs_construct_manifest.json") as f:
            cls.manifest = json.load(f)

    def test_count(self):
        self.assertEqual(len(self.manifest), 56)

    def test_required_fields(self):
        for c in self.manifest:
            self.assertIn("key", c)
            self.assertIn("column", c)
            self.assertIn("type", c)
            self.assertIn("items", c)
            self.assertIsInstance(c["items"], list)
            self.assertGreater(len(c["items"]), 0)

    def test_no_duplicate_keys(self):
        keys = [c["key"] for c in self.manifest]
        self.assertEqual(len(keys), len(set(keys)))

    def test_alpha_values(self):
        for c in self.manifest:
            alpha = c.get("alpha")
            if alpha is not None:
                self.assertGreaterEqual(alpha, -1.0)
                self.assertLessEqual(alpha, 1.0)


class TestWVSFingerprints(unittest.TestCase):
    """Validate wvs_ses_fingerprints.json structure."""

    @classmethod
    def setUpClass(cls):
        with open(DATA / "wvs_ses_fingerprints.json") as f:
            raw = json.load(f)
        cls.fps = raw["fingerprints"]
        cls.meta = raw

    def test_count(self):
        self.assertEqual(len(self.fps), 56)

    def test_four_dimensions(self):
        for key, fp in self.fps.items():
            for dim in ("rho_escol", "rho_Tam_loc", "rho_sexo", "rho_edad"):
                self.assertIn(dim, fp, f"Missing {dim} in {key}")
                self.assertIsInstance(fp[dim], (int, float))

    def test_ses_magnitude_nonnegative(self):
        for key, fp in self.fps.items():
            self.assertGreaterEqual(fp["ses_magnitude"], 0.0, key)

    def test_dominant_dim_valid(self):
        for key, fp in self.fps.items():
            self.assertIn(fp["dominant_dim"], VALID_DIMS, key)


class TestWVSConstructMap(unittest.TestCase):
    """Validate wvs_losmex_construct_map_v2.json."""

    @classmethod
    def setUpClass(cls):
        with open(DATA / "wvs_losmex_construct_map_v2.json") as f:
            cls.cmap = json.load(f)
        cls.mappings = cls.cmap["mappings"]
        with open(DATA / "wvs_construct_manifest.json") as f:
            cls.manifest_keys = {c["key"] for c in json.load(f)}

    def test_mapping_count(self):
        self.assertEqual(len(self.mappings), 56)

    def test_grade_distribution_matches_summary(self):
        qs = self.cmap["quality_summary"]
        near_identical = sum(1 for m in self.mappings if m.get("match_quality") == "near_identical")
        same_concept = sum(1 for m in self.mappings if m.get("match_quality") == "same_concept")
        no_match = sum(1 for m in self.mappings if m.get("match_quality") == "no_match")
        self.assertEqual(near_identical, qs["near_identical"])
        self.assertEqual(same_concept, qs["same_concept"])
        self.assertEqual(no_match, qs["no_match"])

    def test_wvs_keys_resolve_to_manifest(self):
        for m in self.mappings:
            self.assertIn(m["wvs_key"], self.manifest_keys,
                          f"WVS key {m['wvs_key']} not in manifest")

    def test_polarity_valid(self):
        for m in self.mappings:
            bm = m.get("best_match")
            if bm and bm.get("polarity"):
                self.assertIn(bm["polarity"], {"same", "reversed", "unclear", "related"},
                              f"Invalid polarity in {m['wvs_key']}")

    def test_best_match_has_losmex_id(self):
        for m in self.mappings:
            bm = m.get("best_match")
            if m.get("match_quality") != "no_match":
                self.assertIsNotNone(bm, f"No best_match for {m['wvs_key']}")
                self.assertIn("losmex_id", bm, f"No losmex_id for {m['wvs_key']}")


@unittest.skipUnless(NAVEGADOR_DATA_RESULTS.exists(),
                     "navegador_data repo not available")
class TestWVSWithinSweep(unittest.TestCase):
    """Validate WVS MEX W7 within-survey sweep from navegador_data."""

    @classmethod
    def setUpClass(cls):
        with open(NAVEGADOR_DATA_RESULTS / "wvs_mex_w7_within_sweep.json") as f:
            raw = json.load(f)
        cls.estimates = raw["estimates"]
        cls.metadata = raw.get("metadata", {})

    def test_pair_count(self):
        self.assertEqual(len(self.estimates), 982)

    def test_gamma_range(self):
        for k, v in self.estimates.items():
            g = v["dr_gamma"]
            self.assertGreaterEqual(g, -1.0, k)
            self.assertLessEqual(g, 1.0, k)

    def test_ci_ordered(self):
        for k, v in self.estimates.items():
            self.assertLessEqual(v["dr_ci_lo"], v["dr_ci_hi"], k)

    def test_excl_zero_boolean(self):
        for k, v in self.estimates.items():
            self.assertIsInstance(v["excl_zero"], bool, k)


class TestGWAlignment(unittest.TestCase):
    """Validate GW alignment data."""

    @classmethod
    def setUpClass(cls):
        with open(TDA / "alignment" / "gw_alignment_summary.json") as f:
            cls.pairs = json.load(f)

    def test_pair_count(self):
        self.assertEqual(len(self.pairs), 2145)

    def test_distance_nonnegative(self):
        for p in self.pairs:
            self.assertGreaterEqual(p["gw_dist"], 0.0)

    def test_mexico_present(self):
        mex_pairs = [p for p in self.pairs
                     if p["country1"] == "MEX" or p["country2"] == "MEX"]
        self.assertGreater(len(mex_pairs), 0)

    def test_country_codes_three_letter(self):
        for p in self.pairs:
            self.assertEqual(len(p["country1"]), 3)
            self.assertEqual(len(p["country2"]), 3)


class TestTemporalTrajectory(unittest.TestCase):
    """Validate temporal trajectory and spectral features."""

    @classmethod
    def setUpClass(cls):
        with open(TDA / "temporal" / "temporal_trajectory.json") as f:
            cls.trajectory = json.load(f)
        with open(TDA / "temporal" / "spectral_features.json") as f:
            cls.spectral = json.load(f)

    def test_trajectory_has_waves(self):
        # trajectory may be a dict with wave keys or a list
        if isinstance(self.trajectory, dict):
            self.assertGreater(len(self.trajectory), 0)
        elif isinstance(self.trajectory, list):
            self.assertGreater(len(self.trajectory), 0)

    def test_spectral_features_present(self):
        self.assertIsInstance(self.spectral, (dict, list))
        if isinstance(self.spectral, dict):
            self.assertGreater(len(self.spectral), 0)

    def test_fiedler_values_numeric(self):
        # Check in spectral features for Fiedler values
        if isinstance(self.spectral, dict):
            for key, val in self.spectral.items():
                if isinstance(val, dict) and "fiedler" in val:
                    self.assertIsInstance(val["fiedler"], (int, float))

    def test_wave_years_valid(self):
        manifest = json.load(open(TDA / "temporal" / "manifest.json"))
        years = manifest.get("wave_years", {})
        for wave, year in years.items():
            self.assertGreaterEqual(year, 1981)
            self.assertLessEqual(year, 2022)


class TestWVSKGOntology(unittest.TestCase):
    """Validate the built wvs_kg_ontology.json."""

    @classmethod
    def setUpClass(cls):
        cls.kg_path = DATA / "wvs_kg_ontology.json"
        if not cls.kg_path.exists():
            raise unittest.SkipTest("wvs_kg_ontology.json not built yet")
        with open(cls.kg_path) as f:
            cls.kg = json.load(f)

    def test_construct_count(self):
        self.assertEqual(len(self.kg["constructs"]), 56)

    def test_bridge_count(self):
        self.assertEqual(len(self.kg["bridges"]), 395)

    def test_bridge_schema(self):
        required = {"from", "to", "gamma", "ci_lo", "ci_hi", "ci_width",
                     "excl_zero", "nmi", "fingerprint_dot", "fingerprint_cos"}
        for b in self.kg["bridges"]:
            self.assertTrue(required.issubset(b.keys()), f"Missing keys in bridge: {required - b.keys()}")

    def test_bridge_endpoints_resolve(self):
        construct_ids = {c["id"] for c in self.kg["constructs"]}
        for b in self.kg["bridges"]:
            self.assertIn(b["from"], construct_ids, f"Dangling from: {b['from']}")
            self.assertIn(b["to"], construct_ids, f"Dangling to: {b['to']}")

    def test_fingerprint_cos_computed(self):
        for b in self.kg["bridges"]:
            self.assertIsInstance(b["fingerprint_cos"], float)
            self.assertGreaterEqual(b["fingerprint_cos"], -1.01)
            self.assertLessEqual(b["fingerprint_cos"], 1.01)


class TestWVSOntologyQuery(unittest.TestCase):
    """Integration: OntologyQuery loaded with WVS data."""

    @classmethod
    def setUpClass(cls):
        fp_path = DATA / "wvs_ses_fingerprints_v2.json"
        kg_path = DATA / "wvs_kg_ontology.json"
        if not fp_path.exists() or not kg_path.exists():
            raise unittest.SkipTest("WVS KG/FP files not built yet")
        from opinion_ontology import OntologyQuery
        cls.oq = OntologyQuery(fp_path=fp_path, kg_path=kg_path, dataset="wvs")

    def test_get_profile(self):
        p = self.oq.get_profile("WVS_A|child_qualities_autonomy_self_expression")
        self.assertEqual(p["level"], "L1_construct")
        self.assertIsNone(p.get("error"))

    def test_get_similar(self):
        results = self.oq.get_similar("WVS_A|child_qualities_autonomy_self_expression", n=5)
        self.assertEqual(len(results), 5)
        keys = [r["key"] for r in results]
        self.assertNotIn("WVS_A|child_qualities_autonomy_self_expression", keys)

    def test_find_path_connected(self):
        # Pick two constructs known to be connected (both have bridges)
        connected = [k for k in self.oq._constructs if k in self.oq._bridges]
        if len(connected) < 2:
            self.skipTest("Not enough connected constructs")
        path = self.oq.find_path(connected[0], connected[1])
        self.assertIsNone(path.get("error"))
        self.assertIsNotNone(path["path"])
        self.assertGreater(path["signal_chain"], 0)

    def test_get_camp(self):
        connected = [k for k in self.oq._constructs if k in self.oq._bridges]
        if not connected:
            self.skipTest("No connected constructs")
        camp = self.oq.get_camp(connected[0])
        self.assertIn(camp.get("camp_id"), {1, -1, None})
        if camp["camp_id"] is not None:
            self.assertIn(camp["camp_name"], {"cosmopolitan", "tradition"})

    def test_get_neighborhood(self):
        connected = [k for k in self.oq._constructs if k in self.oq._bridges]
        if not connected:
            self.skipTest("No connected constructs")
        nh = self.oq.get_neighborhood(connected[0], top_n=5)
        self.assertIsNone(nh.get("error"))
        self.assertGreater(nh["neighborhood_summary"]["n_neighbors"], 0)


if __name__ == "__main__":
    unittest.main()
