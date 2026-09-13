"""Tests for the dedupe/merge stage — all on synthetic data."""

import unittest

from humandb import dedupe, parse
from tests import synthetic


def _records():
    import os
    zpath = synthetic.make_export_zip()
    try:
        return parse.parse_export(zpath)
    finally:
        os.unlink(zpath)


class TestDedupe(unittest.TestCase):
    def test_url_match_merges_and_enriches(self):
        records = _records()
        # Split: first 10 as "previous", the two Ava dupes as "fresh".
        previous = [r for r in records if r["name"] != "Ava Rivera"][:9]
        fresh = [r for r in records if r["name"] == "Ava Rivera"]
        merged, stats = dedupe.merge_records(previous, fresh)
        self.assertEqual(stats["added"], 1)  # one Ava, merged not duplicated
        avas = [r for r in merged if r["name"] == "Ava Rivera"]
        self.assertEqual(len(avas), 1)
        # The fresh dupe had position blank but an alternate email; the
        # previous record already had position + email, so nothing to enrich.
        self.assertEqual(avas[0]["position"], "Virtual Assistant")

    def test_blank_fields_get_filled(self):
        previous = [{"name": "Sam Taylor", "url": "", "email": "",
                     "company": "Harbor Admin Co", "position": "Office Manager",
                     "first": "Sam", "last": "Taylor", "location": "", "connected_on": ""}]
        fresh = [{"name": "Sam Taylor", "url": "", "email": "sam@example.com",
                  "company": "Harbor Admin Co", "position": "Office Manager",
                  "first": "Sam", "last": "Taylor", "location": "", "connected_on": ""}]
        merged, stats = dedupe.merge_records(previous, fresh)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["email"], "sam@example.com")
        self.assertEqual(stats["enriched"], 1)

    def test_name_company_fallback_matches_without_url(self):
        previous = [{"name": "Sam Taylor", "url": "", "email": "",
                     "company": "Harbor Admin Co", "position": "",
                     "first": "Sam", "last": "Taylor", "location": "", "connected_on": ""}]
        fresh = [{"name": "sam  taylor", "url": "", "email": "sam@example.com",
                  "company": "harbor admin co.", "position": "Office Manager",
                  "first": "sam", "last": "taylor", "location": "", "connected_on": ""}]
        merged, stats = dedupe.merge_records(previous, fresh)
        self.assertEqual(len(merged), 1)
        self.assertEqual(stats["added"], 0)

    def test_distinct_people_stay_distinct(self):
        records = _records()
        merged, stats = dedupe.merge_records([], records)
        # 15 rows, but 2 Ava dupes + 2 Sam dupes collapse -> 13 unique
        self.assertEqual(len(merged), 13)
        self.assertEqual(stats["added"], 13)


if __name__ == "__main__":
    unittest.main()
