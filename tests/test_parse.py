"""Tests for the parse stage — all on synthetic data."""

import os
import tempfile
import unittest

from humandb import parse
from tests import synthetic


class TestParse(unittest.TestCase):
    def test_parses_official_export(self):
        zpath = synthetic.make_export_zip()
        try:
            records = parse.parse_export(zpath)
            self.assertEqual(len(records), len(synthetic.FAKE_CONTACTS))
            ava = next(r for r in records if r["name"] == "Ava Rivera")
            self.assertEqual(ava["position"], "Virtual Assistant")
            self.assertEqual(ava["company"], "Harbor Admin Co")
            self.assertEqual(ava["email"], "ava@example.com")
            self.assertEqual(ava["url"], "https://www.linkedin.com/in/ava-rivera-123")
            self.assertEqual(ava["connected_on"], "12 Jan 2024")
        finally:
            os.unlink(zpath)

    def test_normalizes_url(self):
        zpath = synthetic.make_export_zip()
        try:
            records = parse.parse_export(zpath)
            urls = [r["url"] for r in records if r["name"] == "Ava Rivera"]
            # trailing slash stripped -> both Avas share one normalized URL
            self.assertEqual(urls[0], urls[1])
        finally:
            os.unlink(zpath)

    def test_refuses_non_export_zip(self):
        zpath = synthetic.make_bad_zip()
        try:
            with self.assertRaises(parse.NotAnOfficialExport):
                parse.parse_export(zpath)
        finally:
            os.unlink(zpath)

    def test_refuses_wrong_header(self):
        zpath = synthetic.make_export_zip(
            header=["Name", "Email", "Stuff"]
        )
        try:
            with self.assertRaises(parse.NotAnOfficialExport):
                parse.parse_export(zpath)
        finally:
            os.unlink(zpath)


if __name__ == "__main__":
    unittest.main()
