"""Benchmark runner based on pyperf."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import warnings
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable

from model_checker.benchmarking.adapters import (
    get_model_checker,
    get_model_content,
)
from model_checker.benchmarking.cases import get_benchmark_cases
from model_checker.benchmarking.schemas import BenchmarkCase


@dataclass(frozen=True)
class CaseMetrics:
    """Derived metrics for one benchmark case."""

    case: BenchmarkCase
    mean_seconds: float
    stddev_seconds: float
    cv_ratio: float
    per_state_seconds: float
    shape: str


def _import_pyperf():
    try:
        import pyperf  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "pyperf is required. Install benchmark extras with: pip install -e .[bench]"
        ) from exc
    return pyperf


def _is_worker() -> bool:
    """Return True when running inside a pyperf worker process."""
    return "--worker" in sys.argv


def _safe_mean(values: Iterable[float]) -> float:
    seq = list(values)
    return (sum(seq) / len(seq)) if seq else 0.0


def _format_seconds(seconds: float) -> str:
    if seconds >= 1.0:
        return f"{seconds:.2f} s"
    if seconds >= 1e-3:
        return f"{seconds * 1e3:.2f} ms"
    if seconds >= 1e-6:
        return f"{seconds * 1e6:.2f} us"
    return f"{seconds * 1e9:.2f} ns"


def _classify_formula_shape(formula: str) -> str:
    cleaned = formula.replace(" ", "").upper()
    if "X" in cleaned:
        return "next-step"
    if "F" in cleaned:
        return "reachability"
    if "G" in cleaned:
        return "safety"
    if "U" in cleaned:
        return "until"
    if "R" in cleaned:
        return "release"
    return "other"


def _extract_formula_features(formula: str) -> dict[str, int]:
    cleaned = formula.replace(" ", "").upper()
    paren_depth = 0
    max_paren_depth = 0
    for char in cleaned:
        if char == "(":
            paren_depth += 1
            max_paren_depth = max(max_paren_depth, paren_depth)
        elif char == ")":
            paren_depth = max(paren_depth - 1, 0)
    return {
        "token_length": len(cleaned),
        "count_X": cleaned.count("X"),
        "count_F": cleaned.count("F"),
        "count_G": cleaned.count("G"),
        "count_U": cleaned.count("U"),
        "count_R": cleaned.count("R"),
        "coalition_markers": cleaned.count("<"),
        "max_paren_depth": max_paren_depth,
    }


def _classify_cv(cv_ratio: float) -> str:
    cv_percent = cv_ratio * 100.0
    if cv_percent < 5.0:
        return "very stable"
    if cv_percent <= 10.0:
        return "acceptable"
    return "noisy"


def _print_case_summary(metrics: CaseMetrics) -> None:
    case = metrics.case
    cv_percent = metrics.cv_ratio * 100.0
    stability = _classify_cv(metrics.cv_ratio)
    print(
        "  -> "
        f"logic={case.logic} "
        f"shape={metrics.shape} "
        f"formula='{case.formula}' "
        f"layout={case.layout} "
        f"states={case.num_states} "
        f"mean={_format_seconds(metrics.mean_seconds)} "
        f"std={_format_seconds(metrics.stddev_seconds)} "
        f"variability={cv_percent:.1f}%({stability}) "
        f"per_state={_format_seconds(metrics.per_state_seconds)}",
        flush=True,
    )


def _extract_metrics(case: BenchmarkCase, benchmark: Any) -> CaseMetrics:
    mean_seconds = float(benchmark.mean())
    stddev_seconds = float(benchmark.stdev())
    cv_ratio = (stddev_seconds / mean_seconds) if mean_seconds > 0 else 0.0
    per_state_seconds = (
        mean_seconds / float(case.num_states) if case.num_states > 0 else mean_seconds
    )
    return CaseMetrics(
        case=case,
        mean_seconds=mean_seconds,
        stddev_seconds=stddev_seconds,
        cv_ratio=cv_ratio,
        per_state_seconds=per_state_seconds,
        shape=case.formula_shape_hint or _classify_formula_shape(case.formula),
    )


def _build_group_row(
    group_type: str, group_name: str, group_metrics: list[CaseMetrics]
) -> dict[str, str]:
    mean_runtime = _safe_mean(m.mean_seconds for m in group_metrics)
    mean_cv_percent = _safe_mean(m.cv_ratio for m in group_metrics) * 100.0
    mean_per_state = _safe_mean(m.per_state_seconds for m in group_metrics)
    row: dict[str, str] = {
        "group": group_type,
        "name": group_name,
        "case_count": str(len(group_metrics)),
        "avg_runtime": _format_seconds(mean_runtime),
        "runtime_variability": f"{mean_cv_percent:.1f}%",
        "avg_runtime_per_state": _format_seconds(mean_per_state),
        "slowest_case_by_mean": "-",
        "highest_variability_case": "-",
    }
    if group_type == "logic":
        slowest = max(group_metrics, key=lambda m: m.mean_seconds)
        noisiest = max(group_metrics, key=lambda m: m.cv_ratio)
        row["slowest_case_by_mean"] = slowest.case.name
        row["highest_variability_case"] = noisiest.case.name
    return row


def _print_group_summaries(metrics_list: list[CaseMetrics]) -> None:
    if not metrics_list:
        return

    table_rows: list[dict[str, str]] = []
    by_logic: dict[str, list[CaseMetrics]] = {}
    for metrics in metrics_list:
        by_logic.setdefault(metrics.case.logic, []).append(metrics)
    for logic in sorted(by_logic):
        table_rows.append(_build_group_row("logic", logic, by_logic[logic]))

    by_shape: dict[str, list[CaseMetrics]] = {}
    for metrics in metrics_list:
        by_shape.setdefault(metrics.shape, []).append(metrics)
    for shape in sorted(by_shape):
        table_rows.append(_build_group_row("shape", shape, by_shape[shape]))

    headers = [
        "group",
        "name",
        "case_count",
        "avg_runtime",
        "runtime_variability",
        "avg_runtime_per_state",
        "slowest_case_by_mean",
        "highest_variability_case",
    ]
    widths = {h: max(len(h), max(len(row[h]) for row in table_rows)) for h in headers}

    print("\n=== Benchmark summary table ===", flush=True)
    header_line = " | ".join(f"{h:{widths[h]}}" for h in headers)
    separator = "-+-".join("-" * widths[h] for h in headers)
    print(header_line, flush=True)
    print(separator, flush=True)
    for row in table_rows:
        print(
            " | ".join(f"{row[h]:{widths[h]}}" for h in headers),
            flush=True,
        )


def _write_summary_json(output: str, metrics_list: list[CaseMetrics]) -> None:
    summary_path = Path(f"{output}.summary.json")
    payload = {
        "version": 1,
        "formula_shape_method": "heuristic_operator_presence",
        "formula_shape_note": (
            "shape is inferred from operator presence (X/F/G/U/R) and is not an AST-level complexity metric"
        ),
        "cases": [
            {
                "name": m.case.name,
                "logic": m.case.logic,
                "formula": m.case.formula,
                "layout": m.case.layout,
                "num_states": m.case.num_states,
                "shape": m.shape,
                "formula_family": m.case.formula_family,
                "formula_features": _extract_formula_features(m.case.formula),
                "mean_seconds": m.mean_seconds,
                "stddev_seconds": m.stddev_seconds,
                "cv_ratio": m.cv_ratio,
                "per_state_seconds": m.per_state_seconds,
            }
            for m in metrics_list
        ],
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved summary metrics to: {summary_path}", flush=True)


def _run_single_case(runner: Any, case: BenchmarkCase, model_path: str) -> Any:
    checker = get_model_checker(case.logic)

    def _run(
        checker=checker,
        formula=case.formula,
        case_name=case.name,
        model_path=model_path,
    ) -> None:
        result = checker(formula, model_path)
        if "error" in result:
            raise RuntimeError(
                f"Benchmark case failed: {case_name} -> {result.get('error')}"
            )

    return runner.bench_func(case.name, _run)


def _run_case_with_live_progress(
    runner: Any, case: BenchmarkCase, model_path: str, expected_seconds: float
) -> Any:
    done = threading.Event()
    progress_start = time.monotonic()

    def _render_progress() -> None:
        dot_count = 0
        while not done.is_set():
            dots = "..." * (dot_count % 3 + 1)
            elapsed = time.monotonic() - progress_start
            eta = max(expected_seconds - elapsed, 0.0)
            print(
                f"\r{case.name} {dots} [running | eta~{eta:.1f}s]",
                end="",
                flush=True,
            )
            dot_count += 1
            time.sleep(0.1)
        print(f"\r{case.name} ... [done]   ", flush=True)

    progress_thread = threading.Thread(target=_render_progress, daemon=True)
    print(f"\r{case.name} ... [running]", end="", flush=True)
    progress_thread.start()
    try:
        capture = StringIO()
        with redirect_stdout(capture):
            benchmark = _run_single_case(runner, case, model_path)
    finally:
        done.set()
        progress_thread.join(timeout=1.0)
    return benchmark


class RunnerFactory:
    """Factory for creating and configuring pyperf.Runner."""

    @staticmethod
    def create_runner() -> Any:
        """Create a pyperf Runner with stability-tuned defaults.

        Settings:
            min_time=0.2  - each sample runs at least 0.2s to reduce noise.
            warmups=5     - five warm-up rounds to stabilise CPU caches.
        """
        warnings.filterwarnings(
            "ignore",
            message=".*pkg_resources is deprecated.*",
            category=UserWarning,
        )

        pyperf = _import_pyperf()
        runner = pyperf.Runner(min_time=0.2, warmups=5)
        runner.metadata["benchmark_tool"] = "model_checker-benchmark"
        return runner


def _build_case_file(case: BenchmarkCase, output_dir: Path) -> Path:
    """Write a generated model file to *output_dir* and return its path."""
    content = get_model_content(case.logic, case.layout, case.num_states)
    file_name = f"{case.logic}_{case.layout}_{case.num_states}.txt"
    case_path = output_dir / file_name
    case_path.write_text(content, encoding="utf-8")
    return case_path


def run_benchmarks(
    runner: Any,
    logic: str | None = None,
    output: str | None = None,
) -> int:
    """Run pyperf benchmarks for selected cases.

    Args:
        runner: A configured pyperf.Runner instance.
        logic: Optional logic name filter.  Falls back to the
            ``VMC_BENCH_LOGIC`` environment variable (set by the
            CLI for worker-process synchronisation).
        output: Optional path for the pyperf JSON suite.

    Returns:
        Number of benchmark cases executed.
    """
    if logic is None:
        logic = os.environ.get("VMC_BENCH_LOGIC")

    cases = get_benchmark_cases(logic=logic)
    if not cases:
        raise ValueError(f"No benchmark cases found for logic: {logic}")

    is_main = not _is_worker()
    total = len(cases)

    if is_main:
        logic_label = logic if logic else "all logics"
        print(f"[*] Benchmarking {total} cases for: {logic_label}")

    benchmarks = []
    metrics_list: list[CaseMetrics] = []
    avg_case_seconds = 4.0
    with TemporaryDirectory(prefix="model_checker-benchmark-") as temp_dir:
        temp_path = Path(temp_dir)
        runner.metadata["case_count"] = str(total)

        for idx, case in enumerate(cases, start=1):
            model_path = str(_build_case_file(case, temp_path))
            case_start = time.monotonic()
            if is_main:
                print("", flush=True)
                benchmark = _run_case_with_live_progress(
                    runner, case, model_path, expected_seconds=avg_case_seconds
                )
            else:
                benchmark = _run_single_case(runner, case, model_path)
            if benchmark is not None:
                benchmarks.append(benchmark)
                if is_main:
                    metrics = _extract_metrics(case, benchmark)
                    metrics_list.append(metrics)
                    _print_case_summary(metrics)
            if is_main:
                elapsed_case = max(time.monotonic() - case_start, 0.01)
                completed = float(idx)
                avg_case_seconds = (
                    (avg_case_seconds * (completed - 1.0)) + elapsed_case
                ) / completed

        if output and benchmarks:
            import pyperf

            output_path = Path(output)
            if output_path.exists():
                output_path.unlink()
            suite = pyperf.BenchmarkSuite(benchmarks)
            suite.dump(output)
            if is_main:
                print(f"\nSaved benchmark suite to: {output}")
                _write_summary_json(output, metrics_list)

    if is_main:
        _print_group_summaries(metrics_list)
        print(f"\nCompleted benchmark run with {len(metrics_list)} measured cases.")

    return total


def compare_results(baseline: str, result: str) -> int:
    """Compare two pyperf JSON suites."""
    command = [
        sys.executable,
        "-m",
        "pyperf",
        "compare_to",
        baseline,
        result,
    ]
    completed = subprocess.run(command, check=False)
    return completed.returncode
