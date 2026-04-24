"""Plot benchmark summary JSON into analysis-focused charts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _import_matplotlib():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for plotting. Install with: pip install -e .[bench-viz]"
        ) from exc
    return plt


def _load_summary(summary_path: Path) -> dict[str, Any]:
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    if "cases" not in data or not isinstance(data["cases"], list):
        raise ValueError("Invalid summary JSON: expected top-level 'cases' list")
    return data


def _filter_cases(
    cases: list[dict[str, Any]],
    layout: str | None,
) -> list[dict[str, Any]]:
    if layout is None:
        return cases
    return [case for case in cases if case.get("layout") == layout]


def _group_mean(points: list[tuple[str, float]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for key, value in points:
        grouped.setdefault(key, []).append(value)
    return {k: (sum(v) / len(v) if v else 0.0) for k, v in grouped.items()}


def _plot_logic_runtime_at_state(
    plt: Any,
    cases: list[dict[str, Any]],
    output_dir: Path,
    fixed_states: int | None,
) -> None:
    if not cases:
        return
    if fixed_states is None:
        available_states = sorted({int(case["num_states"]) for case in cases})
        fixed_states = available_states[0]
    selected = [case for case in cases if int(case["num_states"]) == fixed_states]
    if not selected:
        return

    logic_means = _group_mean(
        [(str(case["logic"]), float(case["mean_seconds"])) for case in selected]
    )
    labels = sorted(logic_means)
    values = [logic_means[label] for label in labels]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values)
    ax.set_title(f"Mean runtime by logic at {fixed_states} states")
    ax.set_xlabel("Logic")
    ax.set_ylabel("Mean runtime (seconds)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / f"logic_runtime_states_{fixed_states}.png", dpi=150)
    plt.close(fig)


def _plot_scaling_by_logic(
    plt: Any, cases: list[dict[str, Any]], output_dir: Path
) -> None:
    if not cases:
        return
    by_logic: dict[str, dict[int, list[float]]] = {}
    for case in cases:
        logic = str(case["logic"])
        states = int(case["num_states"])
        runtime = float(case["mean_seconds"])
        by_logic.setdefault(logic, {}).setdefault(states, []).append(runtime)

    fig, ax = plt.subplots(figsize=(10, 5))
    for logic in sorted(by_logic):
        states_sorted = sorted(by_logic[logic])
        mean_runtimes = [
            sum(by_logic[logic][state]) / len(by_logic[logic][state])
            for state in states_sorted
        ]
        ax.plot(states_sorted, mean_runtimes, marker="o", label=logic)

    ax.set_title("Runtime scaling by state count")
    ax.set_xlabel("Number of states")
    ax.set_ylabel("Mean runtime (seconds)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "runtime_scaling_by_logic.png", dpi=150)
    plt.close(fig)


def _plot_variability_strip(
    plt: Any, cases: list[dict[str, Any]], output_dir: Path
) -> None:
    if not cases:
        return
    labels = sorted({str(case["logic"]) for case in cases})
    index_by_logic = {logic: idx for idx, logic in enumerate(labels)}

    x_points = [index_by_logic[str(case["logic"])] for case in cases]
    y_points = [float(case["cv_ratio"]) * 100.0 for case in cases]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(x_points, y_points, alpha=0.7)
    ax.set_title("Runtime variability by logic")
    ax.set_xlabel("Logic")
    ax.set_ylabel("Coefficient of variation (%)")
    ax.set_xticks(list(index_by_logic.values()))
    ax.set_xticklabels(labels, rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / "runtime_variability_by_logic.png", dpi=150)
    plt.close(fig)


def _plot_shape_runtime_box(
    plt: Any, cases: list[dict[str, Any]], output_dir: Path, shape_note: str
) -> None:
    if not cases:
        return
    by_shape: dict[str, list[float]] = {}
    for case in cases:
        by_shape.setdefault(str(case["shape"]), []).append(float(case["mean_seconds"]))

    labels = sorted(by_shape)
    if not labels:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot([by_shape[label] for label in labels], labels=labels)
    ax.set_title("Runtime by formula shape (heuristic)")
    ax.set_xlabel("Shape bucket")
    ax.set_ylabel("Mean runtime (seconds)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / "runtime_by_formula_shape.png", dpi=150)
    plt.close(fig)
    print(f"Shape chart note: {shape_note}")


def generate_plots(
    summary_path: str,
    out_dir: str,
    layout: str | None = None,
    fixed_states: int | None = None,
) -> None:
    plt = _import_matplotlib()
    summary_file = Path(summary_path)
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = _load_summary(summary_file)
    shape_note = str(
        data.get(
            "formula_shape_note",
            "shape is heuristic and not a parser-derived complexity metric",
        )
    )
    filtered_cases = _filter_cases(data["cases"], layout)
    if not filtered_cases:
        raise ValueError("No cases available after applying requested filters")

    _plot_logic_runtime_at_state(plt, filtered_cases, output_dir, fixed_states)
    _plot_scaling_by_logic(plt, filtered_cases, output_dir)
    _plot_variability_strip(plt, filtered_cases, output_dir)
    _plot_shape_runtime_box(plt, filtered_cases, output_dir, shape_note)

    print(f"Saved plots in: {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate benchmark analysis plots from *.summary.json"
    )
    parser.add_argument("--summary", required=True, help="Path to summary JSON file")
    parser.add_argument("--out-dir", required=True, help="Directory for PNG plots")
    parser.add_argument(
        "--layout",
        default=None,
        help="Optional layout filter before plotting (example: linear, cycle)",
    )
    parser.add_argument(
        "--fixed-states",
        type=int,
        default=None,
        help="Optional fixed state count for logic comparison chart",
    )
    args = parser.parse_args()

    generate_plots(
        summary_path=args.summary,
        out_dir=args.out_dir,
        layout=args.layout,
        fixed_states=args.fixed_states,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
