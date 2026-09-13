"""Tests for the scoring stage — all on synthetic data."""

import unittest
from datetime import date

from humandb import analyze, config as config_mod, score


def _cfg():
    import copy
    return copy.deepcopy(config_mod.DEFAULT_CONFIG)


class TestScore(unittest.TestCase):
    def test_capability_fit_uses_wishlist_weights(self):
        cfg = _cfg()
        cfg["wishlist"] = {"admin": 3, "operations": 1}
        rec = {"capabilities": ["admin"]}
        self.assertEqual(score.capability_fit(rec, cfg["wishlist"]), 0.75)
        rec2 = {"capabilities": ["admin", "operations"]}
        self.assertEqual(score.capability_fit(rec2, cfg["wishlist"]), 1.0)
        rec3 = {"capabilities": ["press"]}
        self.assertEqual(score.capability_fit(rec3, cfg["wishlist"]), 0.0)

    def test_completeness_counts_filled_fields(self):
        full = {"position": "x", "company": "x", "email": "x", "location": "x", "url": "x"}
        self.assertEqual(score.completeness(full), 1.0)
        sparse = {"position": "", "company": "", "email": "", "location": "", "url": "x"}
        self.assertEqual(score.completeness(sparse), 0.2)

    def test_recency_curve(self):
        today = date(2026, 9, 12)
        fresh = {"connected_on": "12 Sep 2026"}
        old = {"connected_on": "09 Aug 2012"}
        unknown = {"connected_on": ""}
        self.assertEqual(score.recency(fresh, 365, 3650, today=today), 1.0)
        self.assertEqual(score.recency(old, 365, 3650, today=today), 0.0)
        self.assertEqual(score.recency(unknown, 365, 3650, today=today), 0.5)

    def test_scores_sort_descending_and_explain(self):
        cfg = _cfg()
        cfg["wishlist"] = {"admin": 1}
        recs = [
            {"name": "Low", "capabilities": [], "position": "", "company": "",
             "email": "", "location": "", "url": "", "connected_on": ""},
            {"name": "High", "capabilities": ["admin"], "position": "Virtual Assistant",
             "company": "Acme", "email": "h@example.com", "location": "Tacoma",
             "url": "https://www.linkedin.com/in/high", "connected_on": "12 Sep 2026"},
        ]
        out = score.score_records(recs, cfg, today=date(2026, 9, 12))
        self.assertEqual(out[0]["name"], "High")
        self.assertIn("score_breakdown", out[0])
        self.assertGreater(out[0]["score"], out[1]["score"])

    def test_end_to_end_tag_then_score(self):
        cfg = _cfg()
        recs = [
            {"name": "Ava", "position": "Virtual Assistant", "company": "Harbor Admin Co",
             "email": "a@example.com", "location": "Seattle",
             "url": "https://www.linkedin.com/in/ava", "connected_on": "12 Jan 2024",
             "first": "Ava", "last": "Rivera"},
        ]
        analyze.tag_records(recs, cfg["capabilities"], cfg["search_fields"])
        score.score_records(recs, cfg, today=date(2026, 9, 12))
        self.assertIn("admin", recs[0]["capabilities"])
        self.assertGreater(recs[0]["score"], 0.5)


if __name__ == "__main__":
    unittest.main()
