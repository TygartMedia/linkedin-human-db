"""Tests for the analyze (capability tagging) stage — all on synthetic data."""

import os
import unittest

from humandb import analyze, config as config_mod, parse
from tests import synthetic


def _tagged():
    zpath = synthetic.make_export_zip()
    try:
        records = parse.parse_export(zpath)
    finally:
        os.unlink(zpath)
    cfg = config_mod.DEFAULT_CONFIG
    return analyze.tag_records(records, cfg["capabilities"], cfg["search_fields"])


class TestAnalyze(unittest.TestCase):
    def test_keywords_tag_position(self):
        records = _tagged()
        # Note: the synthetic set contains a duplicate Ava with a blank
        # position — pick the complete one.
        def one(name):
            return next(r for r in records if r["name"] == name and r["position"])
        self.assertIn("admin", one("Ava Rivera")["capabilities"])
        self.assertIn("operations", one("Ben Okafor")["capabilities"])
        self.assertIn("events", one("Cara Nguyen")["capabilities"])
        self.assertIn("hiring", one("Erin Walsh")["capabilities"])
        self.assertIn("technical", one("Finn Gallagher")["capabilities"])

    def test_evidence_is_recorded(self):
        records = _tagged()
        ava = next(r for r in records if r["name"] == "Ava Rivera")
        self.assertIn("admin", ava["capability_evidence"])
        self.assertTrue(any("position" in hit for hit in ava["capability_evidence"]["admin"]))

    def test_company_field_is_searched(self):
        records = _tagged()
        # "Cascade Restoration" in company -> local_services
        dev = next(r for r in records if r["name"] == "Dev Patel")
        self.assertIn("local_services", dev["capabilities"])

    def test_word_boundaries_avoid_false_positives(self):
        cfg = config_mod.DEFAULT_CONFIG
        recs = [{"name": "X", "position": "Waiting tables", "company": ""}]
        analyze.tag_records(recs, {"technical": ["IT"]}, ["position", "company"])
        self.assertNotIn("technical", recs[0]["capabilities"])

    def test_custom_capabilities_from_config(self):
        cfg = config_mod.DEFAULT_CONFIG
        recs = [{"name": "X", "position": "Licensed Drone Pilot, Part 107", "company": ""}]
        caps = dict(cfg["capabilities"])
        caps["drone_pilot"] = ["drone pilot", "Part 107", "UAV"]
        analyze.tag_records(recs, caps, ["position", "company"])
        self.assertIn("drone_pilot", recs[0]["capabilities"])

    def test_untagged_records_get_empty_lists(self):
        records = _tagged()
        noah = next(r for r in records if r["name"] == "Noah Kim")
        self.assertEqual(noah["capabilities"], [])
        self.assertEqual(noah["capability_evidence"], {})


if __name__ == "__main__":
    unittest.main()
