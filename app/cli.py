"""Command-line entry point: `python -m app.cli --help`."""
from __future__ import annotations

import argparse
from pathlib import Path

from app.core import milestone_1, milestone_2, milestone_3, milestone_4, milestone_5
from app.dashboard import serve_dashboard
from app.storage import Store


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="supply-co-usage-insight",
        description=(
            "For hospital administrators, analyzes which medical supplies are frequently "
            "used together across procedures, optimizing stock placement and procurement efficiency."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("hello", help="check that everything is wired up")

    analyze_p = sub.add_parser("analyze", help="run the 5-milestone co-usage mining pipeline")
    analyze_p.add_argument("--procedures", type=int, default=200, help="number of mock procedures to generate")
    analyze_p.add_argument("--min-support", type=float, default=0.10, help="minimum support threshold (0-1)")
    analyze_p.add_argument("--max-size", type=int, default=4, help="maximum bundle size")
    analyze_p.add_argument("--top", type=int, default=15, help="number of top bundles to display")
    analyze_p.add_argument(
        "--format",
        choices=("text", "markdown", "json"),
        default="text",
        help="report output format",
    )
    analyze_p.add_argument("--output", type=str, default="", help="optional file path to write the report")
    analyze_p.add_argument("--save", action="store_true", help="persist results to local JSON store")

    serve_p = sub.add_parser("serve", help="launch the interactive local web dashboard")
    serve_p.add_argument("--host", default="127.0.0.1", help="host to bind (default: 127.0.0.1)")
    serve_p.add_argument("--port", type=int, default=8000, help="port to bind (default: 8000)")

    args = parser.parse_args(argv)

    if args.command == "hello":
        print("Supply Co-usage Insight is ready. Open README.md for your milestones.")
        return

    if args.command == "analyze":
        procedures = milestone_1(n_procedures=args.procedures)
        itemsets = milestone_2(procedures, min_support=args.min_support, max_size=args.max_size)
        bundles = milestone_3(itemsets, min_size=2, top_n=args.top, total_procedures=len(procedures))
        evaluated = milestone_4(itemsets, bundles)
        report = milestone_5(evaluated, procedures=procedures, output_format=args.format)

        if args.save:
            Store().put("latest_bundles", evaluated)

        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"Report written to {args.output}")
        else:
            print(report)
        return

    if args.command == "serve":
        serve_dashboard(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
