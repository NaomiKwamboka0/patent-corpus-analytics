"""Command line interface: generate | analyze | report | all."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generate import generate_corpus
from .pipeline import run_pipeline
from .visualize import render_all


def _cmd_generate(args):
    rows = generate_corpus(args.data_dir, count=args.count, seed=args.seed)
    print(f"Generated {len(rows)} patents into {Path(args.data_dir) / 'patents'}")


def _cmd_analyze(args):
    out = run_pipeline(Path(args.data_dir) / "patents", args.output)
    agg = out["aggregations"]
    print(f"Analyzed {agg['corpus_size']} patents -> {args.output}")
    print(f"  topics: {agg['topic_counts']}")
    print(f"  unique cited prior art: {agg['total_unique_cited_patents']}")
    print(f"  most cited: {agg['most_cited_patent_number']} "
          f"({agg['max_citers_per_cited']} citers)")


def _cmd_report(args):
    output = json.loads(Path(args.output).read_text(encoding="utf-8"))
    charts = render_all(output["aggregations"], args.charts_dir)
    print(f"Wrote {len(charts)} charts to {args.charts_dir}")
    for c in charts:
        print(f"  {c}")


def _cmd_all(args):
    _cmd_generate(args)
    _cmd_analyze(args)
    _cmd_report(args)


def build_parser() -> argparse.ArgumentParser:
    # Shared options live on a parent parser so they are accepted both before
    # and after the subcommand (e.g. `analyze --output report.json`).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-dir", default="data", help="corpus directory")
    common.add_argument("--output", default="examples/output.json", help="output JSON path")
    common.add_argument("--charts-dir", default="examples/charts", help="charts directory")
    common.add_argument("--count", type=int, default=120, help="patents to generate")
    common.add_argument("--seed", type=int, default=42, help="generation seed")

    p = argparse.ArgumentParser(prog="patent-analytics", parents=[common],
                                description="Patent corpus analytics pipeline")
    sub = p.add_subparsers(dest="command", required=True)
    for name, func in [("generate", _cmd_generate), ("analyze", _cmd_analyze),
                       ("report", _cmd_report), ("all", _cmd_all)]:
        sp = sub.add_parser(name, parents=[common])
        sp.set_defaults(func=func)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
