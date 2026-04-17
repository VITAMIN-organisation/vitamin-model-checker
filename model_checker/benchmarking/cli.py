"""CLI for vitamin model checker benchmarks."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from model_checker.benchmarking.plot_summary import generate_plots
from model_checker.benchmarking.runner import compare_results, run_benchmarks


def _is_pyperf_worker_process() -> bool:
    """Return True when CLI is executing inside a pyperf worker."""
    return "--worker" in sys.argv


def _resolve_output_path(output_path: Path) -> Path | None:
    current = output_path
    while current.exists():
        choice = input(
            f"Output file {current} already exists. "
            "[o]verwrite, [n]ew name, or [c]ancel? "
        ).strip().lower()
        if choice in {"o", "overwrite"}:
            current.unlink()
            summary_path = Path(f"{current}.summary.json")
            if summary_path.exists():
                summary_path.unlink()
            return current
        if choice in {"n", "new"}:
            new_name = input("Enter new output file path: ").strip()
            if not new_name:
                print("Empty path. Please provide a valid file path.", file=sys.stderr)
                continue
            current = Path(new_name)
            continue
        if choice in {"c", "cancel", ""}:
            return None
        print("Invalid choice. Please enter o, n, or c.", file=sys.stderr)
    return current


def _preflight_output_argument(argv: list[str]) -> list[str]:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--mode", choices=("run", "compare"), default="run")
    pre_parser.add_argument("-o", "--output", default=None)
    pre_args, _ = pre_parser.parse_known_args(argv)

    if pre_args.mode == "compare" or not pre_args.output:
        return argv

    output_path = Path(pre_args.output)
    if not output_path.exists():
        return argv
    if not sys.stdin.isatty():
        print(
            "Benchmark canceled: output file exists. "
            "Please run in interactive mode to choose overwrite/new name.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    resolved_output = _resolve_output_path(output_path)
    if resolved_output is None:
        print("Benchmark canceled by user.", file=sys.stderr)
        raise SystemExit(1)

    updated = list(argv)
    for index, token in enumerate(updated):
        if token == "--output" and index + 1 < len(updated):
            updated[index + 1] = str(resolved_output)
            return updated
        if token == "-o" and index + 1 < len(updated):
            updated[index + 1] = str(resolved_output)
            return updated
        if token.startswith("--output="):
            updated[index] = f"--output={resolved_output}"
            return updated
    return updated


def _print_basic_help() -> None:
    print("usage: model_checker-benchmark [--mode {run,compare}] [--logic LOGIC]")
    print("                     [--output PATH] [--baseline PATH] [--result PATH]")
    print("                     [--export-plots DIR]")
    print("")
    print("Basic options:")
    print("  --mode {run,compare}  run benchmarks or compare two result files")
    print("  --logic LOGIC         run benchmarks for one logic")
    print("  --output PATH         write pyperf JSON output to PATH")
    print("  --baseline PATH       baseline file for compare mode")
    print("  --result PATH         candidate file for compare mode")
    print("  --export-plots DIR    export analysis charts from <output>.summary.json")
    print("  -h, --help            show this help message and exit")


def main() -> int:
    from model_checker.benchmarking.runner import RunnerFactory

    if not _is_pyperf_worker_process():
        if "--help" in sys.argv or "-h" in sys.argv:
            _print_basic_help()
            return 0
        sys.argv[1:] = _preflight_output_argument(sys.argv[1:])

    if "--copy-env" not in sys.argv:
        sys.argv.append("--copy-env")
    if "--raw-pyperf" not in sys.argv and "--quiet" not in sys.argv:
        sys.argv.append("--quiet")

    runner = RunnerFactory.create_runner()
    parser = runner.argparser
    parser.description = "Run pyperf benchmarks for vitamin model checker logics."

    parser.add_argument(
        "--mode",
        choices=("run", "compare"),
        default="run",
        help="run: execute benchmarks, compare: compare two JSON result files",
    )
    parser.add_argument(
        "--logic",
        default=None,
        help="Run only one logic (example: CTL, ATL, COTL).",
    )
    parser.add_argument(
        "--baseline",
        default=None,
        help="Baseline pyperf JSON file for mode=compare.",
    )
    parser.add_argument(
        "--result",
        default=None,
        help="Candidate pyperf JSON file for mode=compare.",
    )
    parser.add_argument(
        "--export-plots",
        default=None,
        help="Output directory for analysis plots (requires --output and bench-viz extra).",
    )
    args = runner.parse_args()

    if args.mode == "compare":
        if not args.baseline or not args.result:
            parser.error("--baseline and --result are required when --mode=compare")
        return compare_results(args.baseline, args.result)

    # Propagate logic filter to worker processes via environment.
    # pyperf spawns workers as subprocesses; --copy-env ensures they
    # inherit this variable so run_benchmarks() filters identically.
    if args.logic:
        os.environ["VMC_BENCH_LOGIC"] = args.logic

    try:
        case_count = run_benchmarks(
            runner,
            logic=args.logic,
            output=args.output,
        )
    except Exception as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    if args.export_plots and not _is_pyperf_worker_process():
        if not args.output:
            parser.error("--output is required when --export-plots is set")
        try:
            summary_path = f"{args.output}.summary.json"
            generate_plots(
                summary_path=summary_path,
                out_dir=args.export_plots,
            )
            print(
                f"Exported plots from {Path(summary_path)} to {Path(args.export_plots)}"
            )
        except Exception as exc:
            print(f"Plot export failed: {exc}", file=sys.stderr)
            return 1

    if not _is_pyperf_worker_process():
        print(f"\nCompleted {case_count} benchmark cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
