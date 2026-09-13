"""Tests for the report stage + the full CLI pipeline — all on synthetic data."""

import json
import os
import tempfile
import unittest

from humandb import analyze, cli, config as config_mod, parse, report, score
from tests import synthetic


def _pipeline_records():
    zpath = synthetic.make_export_zip()
    try:
        records = parse.parse_export(zpath)
    finally:
        os.unlink(zpath)
    cfg = config_mod.DEFAULT_CONFIG
    analyze.tag_records(records, cfg["capabilities"], cfg["search_fields"])
    score.score_records(records, cfg)
    return records, cfg


class TestReport(unittest.TestCase):
    def test_writes_all_outputs(self):
        records, cfg = _pipeline_records()
        with tempfile.TemporaryDirectory() as outdir:
            paths = report.write_outputs(records, cfg, outdir)
            for p in paths.values():
                self.assertTrue(os.path.exists(p))
            with open(paths["json"], encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["meta"]["count"], len(records))
            with open(paths["summary"], encoding="utf-8") as f:
                summary = f.read()
            self.assertIn("Contacts:", summary)
            self.assertIn("Coverage gaps", summary)

    def test_summary_flags_gaps(self):
        records, cfg = _pipeline_records()
        summary = report.build_summary(records, cfg, {})
        # 'press' has 1 contact (Gia Rossi) in the wishlist? No — check the
        # default wishlist: admin/operations/outreach/local_services.
        # local_services has Dev + Olivia = 2 -> gap (< 3).
        self.assertIn("local_services", summary)


class TestCLI(unittest.TestCase):
    def test_run_end_to_end(self):
        zpath = synthetic.make_export_zip()
        try:
            with tempfile.TemporaryDirectory() as outdir:
                cli.main([
                    "run", "--export", zpath, "--out", outdir,
                    "--config", os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "config.yaml"),
                ])
                for fname in ("contacts.json", "contacts.csv", "summary.md"):
                    self.assertTrue(os.path.exists(os.path.join(outdir, fname)),
                                    fname)
                with open(os.path.join(outdir, "contacts.json"), encoding="utf-8") as f:
                    data = json.load(f)
                self.assertGreater(data["meta"]["count"], 0)
                first = data["contacts"][0]
                self.assertIn("score", first)
                self.assertIn("capabilities", first)
        finally:
            os.unlink(zpath)


if __name__ == "__main__":
    unittest.main()
