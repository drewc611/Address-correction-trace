"""CLI entry point for the address correction tracer."""

import argparse
import json
import os
import sys

from .corrector import AddressCorrector


def main():
    parser = argparse.ArgumentParser(
        prog="address_tracer",
        description="Validate, correct, and trace changes to mailing addresses.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # correct command
    correct_parser = subparsers.add_parser("correct", help="Correct a single address")
    correct_parser.add_argument("address", help="The address string to correct")
    correct_parser.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )

    # batch command
    batch_parser = subparsers.add_parser("batch", help="Process a file of addresses")
    batch_parser.add_argument("file", help="Path to file with one address per line")
    batch_parser.add_argument("-o", "--output", default=".", help="Output directory for results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    corrector = AddressCorrector()

    if args.command == "correct":
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

    elif args.command == "batch":
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)

        os.makedirs(args.output, exist_ok=True)

        with open(args.file, "r") as f:
            addresses = [line.strip() for line in f if line.strip()]

        results = corrector.correct_batch(addresses)

        # Write combined trace artifact
        artifacts = [r.trace.to_dict() for r in results]
        output_path = os.path.join(args.output, "trace_artifacts.json")
        with open(output_path, "w") as f:
            json.dump(artifacts, f, indent=2)

        print(f"Processed {len(results)} addresses")
        corrected_count = sum(1 for r in results if r.trace.status == "corrected")
        error_count = sum(1 for r in results if r.trace.status == "error")
        print(f"  Corrected: {corrected_count}")
        print(f"  Unchanged: {len(results) - corrected_count - error_count}")
        print(f"  Errors:    {error_count}")
        print(f"Trace artifacts written to: {output_path}")


if __name__ == "__main__":
    main()
