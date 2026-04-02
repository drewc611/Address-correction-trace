"""CLI entry point for the address correction tracer service."""

import argparse
import json
import os
import sys

from .corrector import AddressCorrector
from .service import AddressTracerService


def main():
    parser = argparse.ArgumentParser(
        prog="address_tracer",
        description="Address correction, evaluation, and tracing service.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -- correct ---------------------------------------------------------------
    correct_p = subparsers.add_parser("correct", help="Correct a single address")
    correct_p.add_argument("address", help="The address string to correct")
    correct_p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )

    # -- batch -----------------------------------------------------------------
    batch_p = subparsers.add_parser("batch", help="Process a file of addresses")
    batch_p.add_argument("file", help="Path to file with one address per line")
    batch_p.add_argument("-o", "--output", default=".", help="Output directory for results")

    # -- evaluate --------------------------------------------------------------
    eval_p = subparsers.add_parser("evaluate", help="Evaluate corrector against a golden dataset")
    eval_p.add_argument("dataset", help="Path to golden dataset JSON file")
    eval_p.add_argument("--threshold", type=float, default=0.5, help="Metric pass threshold (default: 0.5)")
    eval_p.add_argument("--identifier", default="", help="Label for this evaluation run")
    eval_p.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # -- dashboard -------------------------------------------------------------
    dash_p = subparsers.add_parser("dashboard", help="Run evaluation and generate HTML dashboard")
    dash_p.add_argument("dataset", help="Path to golden dataset JSON file")
    dash_p.add_argument("-o", "--output", default="dashboard.html", help="Output HTML file path")
    dash_p.add_argument("--title", default="Address Correction Evaluation", help="Dashboard title")
    dash_p.add_argument("--identifier", default="", help="Label for this evaluation run")

    # -- serve -----------------------------------------------------------------
    serve_p = subparsers.add_parser("serve", help="Start the HTTP service")
    serve_p.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    serve_p.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "correct":
        _cmd_correct(args)
    elif args.command == "batch":
        _cmd_batch(args)
    elif args.command == "evaluate":
        _cmd_evaluate(args)
    elif args.command == "dashboard":
        _cmd_dashboard(args)
    elif args.command == "serve":
        _cmd_serve(args)


def _cmd_correct(args):
    corrector = AddressCorrector()
    result = corrector.correct(args.address)
    if args.format == "json":
        print(result.trace.to_json())
    else:
        print(f"Input:     {result.trace.input_address}")
        print(f"Corrected: {result.corrected_address}")
        print(f"Status:    {result.trace.status}")
        print(f"Confidence: {result.trace.confidence}")
        if result.trace.corrections:
            print(f"\nCorrections ({len(result.trace.corrections)}):")
            for c in result.trace.corrections:
                print(f"  [{c.field}] {c.original!r} -> {c.corrected!r} ({c.rule})")


def _cmd_batch(args):
    if not os.path.isfile(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    corrector = AddressCorrector()
    os.makedirs(args.output, exist_ok=True)

    with open(args.file, "r") as f:
        addresses = [line.strip() for line in f if line.strip()]

    results = corrector.correct_batch(addresses)
    artifacts = [r.trace.to_dict() for r in results]
    output_path = os.path.join(args.output, "trace_artifacts.json")
    with open(output_path, "w") as f:
        json.dump(artifacts, f, indent=2)

    corrected_count = sum(1 for r in results if r.trace.status == "corrected")
    error_count = sum(1 for r in results if r.trace.status == "error")
    print(f"Processed {len(results)} addresses")
    print(f"  Corrected: {corrected_count}")
    print(f"  Unchanged: {len(results) - corrected_count - error_count}")
    print(f"  Errors:    {error_count}")
    print(f"Trace artifacts written to: {output_path}")


def _cmd_evaluate(args):
    from .service import AddressTracerService, default_metrics

    svc = AddressTracerService()
    metrics = default_metrics(threshold=args.threshold)
    eval_result = svc.evaluate_dataset(args.dataset, metrics=metrics, identifier=args.identifier)

    if args.format == "json":
        print(json.dumps(eval_result.to_dict(), indent=2))
    else:
        s = eval_result
        print(f"Evaluation: {s.identifier or 'unnamed'}")
        print(f"Total: {s.total}  Passed: {s.passed}  Failed: {s.failed}  Pass rate: {s.pass_rate:.1%}")
        print()
        for name, stats in s.metric_summaries.items():
            print(f"  {name:30s}  mean={stats['mean']:.3f}  min={stats['min']:.3f}  max={stats['max']:.3f}  pass_rate={stats['pass_rate']:.1%}")
        print()
        for tr in s.test_results:
            status = "PASS" if tr.success else "FAIL"
            print(f"  [{status}] {tr.name}: {tr.input[:60]}")
            for m in tr.metrics_data:
                flag = "+" if m.success else "x"
                print(f"         {flag} {m.metric_name}: {m.score:.3f} — {m.reason[:80]}")


def _cmd_dashboard(args):
    from .service import AddressTracerService

    svc = AddressTracerService()
    eval_result = svc.evaluate_dataset(args.dataset, identifier=args.identifier)
    path = svc.generate_dashboard(eval_result, args.output, title=args.title)
    print(f"Dashboard written to: {path}")


def _cmd_serve(args):
    from .server import run_server
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
