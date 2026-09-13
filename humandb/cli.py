"""Command-line interface. One entry point, one subcommand per stage,
plus `run` for the whole pipeline."""

import argparse
import json
import os
import sys

from . import __version__, analyze, config as config_mod, dedupe, parse, report, score
from .llm_plugin import NoOpEnricher


def _load_config(path):
    if path is None:
        # In a repo checkout, use the shipped config.yaml; in an installed
        # package, fall back to built-in defaults.
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(here, "config.yaml")
        if os.path.exists(candidate):
            path = candidate
        else:
            return config_mod.default()
    return config_mod.load(path)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["contacts"] if isinstance(data, dict) and "contacts" in data else data


def cmd_parse(args):
    records = parse.parse_export(args.export)
    _write_json(args.out, records)
    print(f"parsed {len(records)} contacts -> {args.out}")


def cmd_dedupe(args):
    previous = dedupe.load_previous(args.prev)
    fresh = _read_json(args.input)
    merged, stats = dedupe.merge_records(previous, fresh)
    _write_json(args.out, merged)
    print(f"kept={stats['kept']} added={stats['added']} enriched={stats['enriched']} -> {args.out}")


def cmd_analyze(args):
    cfg = _load_config(args.config)
    records = _read_json(args.input)
    analyze.tag_records(records, cfg["capabilities"], cfg["search_fields"])
    tagged = sum(1 for r in records if r.get("capabilities"))
    _write_json(args.out, records)
    print(f"tagged {tagged}/{len(records)} contacts -> {args.out}")


def cmd_score(args):
    cfg = _load_config(args.config)
    records = _read_json(args.input)
    score.score_records(records, cfg)
    _write_json(args.out, records)
    top = records[0] if records else {}
    print(f"scored {len(records)} contacts -> {args.out} (top: {top.get('name', '—')} {top.get('score', '')})")


def cmd_report(args):
    cfg = _load_config(args.config)
    records = _read_json(args.input)
    paths = report.write_outputs(records, cfg, args.out)
    print("wrote:")
    for k, p in paths.items():
        print(f"  {k}: {p}")


def cmd_run(args):
    cfg = _load_config(args.config)
    os.makedirs(args.out, exist_ok=True)

    records = parse.parse_export(args.export)
    print(f"parse: {len(records)} contacts")

    stats = {}
    if args.prev:
        previous = dedupe.load_previous(args.prev)
        records, stats = dedupe.merge_records(previous, records)
        print(f"dedupe: kept={stats['kept']} added={stats['added']} enriched={stats['enriched']}")

    analyze.tag_records(records, cfg["capabilities"], cfg["search_fields"])
    tagged = sum(1 for r in records if r.get("capabilities"))
    print(f"analyze: tagged {tagged}/{len(records)} contacts")

    enricher = NoOpEnricher()  # plug your own CapabilityEnricher here (see llm_plugin.py)
    records = enricher.enrich(records, cfg["capabilities"])

    score.score_records(records, cfg)
    print(f"score: ranked {len(records)} contacts")

    paths = report.write_outputs(records, cfg, args.out, stats=stats)
    print("report:")
    for k, p in paths.items():
        print(f"  {k}: {p}")


def build_parser():
    p = argparse.ArgumentParser(
        prog="humandb",
        description="Turn your LinkedIn data export into a capability database.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("parse", help="parse the export zip -> records JSON")
    sp.add_argument("--export", required=True, help="path to LinkedIn export zip")
    sp.add_argument("--out", required=True, help="output JSON path")
    sp.set_defaults(func=cmd_parse)

    sp = sub.add_parser("dedupe", help="merge fresh records against a previous run")
    sp.add_argument("--input", required=True, help="fresh records JSON")
    sp.add_argument("--prev", required=True, help="previous contacts.json")
    sp.add_argument("--out", required=True, help="output JSON path")
    sp.set_defaults(func=cmd_dedupe)

    sp = sub.add_parser("analyze", help="tag capabilities (keyword pass)")
    sp.add_argument("--input", required=True, help="records JSON")
    sp.add_argument("--out", required=True, help="output JSON path")
    sp.add_argument("--config", default=None)
    sp.set_defaults(func=cmd_analyze)

    sp = sub.add_parser("score", help="rank against the wishlist")
    sp.add_argument("--input", required=True, help="tagged records JSON")
    sp.add_argument("--out", required=True, help="output JSON path")
    sp.add_argument("--config", default=None)
    sp.set_defaults(func=cmd_score)

    sp = sub.add_parser("report", help="emit CSV + JSON + markdown summary")
    sp.add_argument("--input", required=True, help="scored records JSON")
    sp.add_argument("--out", required=True, help="output directory")
    sp.add_argument("--config", default=None)
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("run", help="full pipeline: parse -> dedupe -> analyze -> score -> report")
    sp.add_argument("--export", required=True, help="path to LinkedIn export zip")
    sp.add_argument("--out", required=True, help="output directory")
    sp.add_argument("--config", default=None)
    sp.add_argument("--prev", default=None, help="previous run's contacts.json (for re-exports)")
    sp.set_defaults(func=cmd_run)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
