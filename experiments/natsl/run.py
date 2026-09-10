#!/usr/bin/env python3
"""Run the paper-oriented NatSL scalability experiment.

The experiment varies model scale, number of agents, and the universal natural-
strategy bound. Each point is executed in a separate process so that a timeout
is enforceable and recordable. The selected checker is the space-efficient
alternating implementation.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import itertools
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SELECTED_MODE = "space"
DEFAULT_STATES = 6
DEFAULT_PROPOSITIONS = ("phase", "signal", "goal")
DEFAULT_SCALES = ((6, 3), (10, 5), (14, 7), (18, 9))
RESULT_FIELDS = (
    "timestamp_utc", "run_id", "status", "mode", "scale_id", "agents",
    "universal_agents", "bound_k", "states", "atomic_propositions",
    "actions_per_universal_agent", "repetition", "timeout_seconds",
    "wall_seconds", "cpu_seconds", "peak_rss_mb", "satisfiable",
    "existential_candidates", "universal_profiles_checked",
    "unrestricted_opponent_checks", "unrestricted_opponent_shortcuts",
    "complete_profile_checks", "raw_domain_size_per_universal_agent",
    "raw_profile_space_upper_bound", "formula", "model_file", "error",
)


def _action_profiles(number_of_agents: int) -> Iterable[tuple[str, ...]]:
    """Agent 1 has one action; every universal agent has two."""
    alphabets = [("A",)] + [("C", "D")] * (number_of_agents - 1)
    return itertools.product(*alphabets)


def proposition_names(proposition_count: int) -> tuple[str, ...]:
    if proposition_count < 3:
        raise ValueError("At least phase, signal, and goal are required")
    return DEFAULT_PROPOSITIONS + tuple(
        f"obs{index}" for index in range(1, proposition_count - 2)
    )


def build_model(
    number_of_agents: int,
    number_of_states: int = DEFAULT_STATES,
    proposition_count: int = len(DEFAULT_PROPOSITIONS),
) -> str:
    """Build the fixed-size bounded-opponent benchmark family.

    Agent 2 is the critical opponent. At s0, C goes to s1 and D reaches the
    goal; at s1, C reaches the goal and D remains at s1. A constant opponent
    (bound 1) cannot avoid the goal, whereas ``phase -> D; T -> C`` (bound 2)
    can. Further opponents are behaviourally irrelevant but their bounded
    domains still contribute to the universally quantified product.
    """
    if number_of_agents < 2:
        raise ValueError("The bounded-opponent experiment requires at least two agents")
    if number_of_states < 3:
        raise ValueError("The benchmark requires at least three states")
    propositions = proposition_names(proposition_count)

    profiles = tuple(_action_profiles(number_of_agents))
    matrix: list[list[list[str]]] = [
        [[] for _ in range(number_of_states)] for _ in range(number_of_states)
    ]
    for state in range(number_of_states):
        for profile_tuple in profiles:
            profile = "".join(profile_tuple)
            critical_action = profile_tuple[1]
            if state == 0:
                destination = 1 if critical_action == "C" else 2
            elif state == 1:
                destination = 2 if critical_action == "C" else 1
            elif state == 2:
                destination = 3 if number_of_states > 3 else 2
            else:
                destination = state + 1 if state + 1 < number_of_states else 2
            matrix[state][destination].append(profile)

    transition_rows = [
        " ".join(",".join(cell) if cell else "0" for cell in row)
        for row in matrix
    ]
    zero_rows = [" ".join("0" for _ in range(number_of_states))] * number_of_states
    states = [f"s{index}" for index in range(number_of_states)]
    labels: list[str] = []
    for state in range(number_of_states):
        phase = int(state == 1)
        signal = int(state >= 3 and state % 2 == 1)
        goal = int(state == 2)
        extra_labels = [
            int((state + index) % (index + 2) == 0)
            for index in range(1, proposition_count - 2)
        ]
        labels.append(" ".join(str(value) for value in (phase, signal, goal, *extra_labels)))

    sections = [
        "Transition", *transition_rows,
        "Unknown_Transition_by", *zero_rows,
        "Name_State", " ".join(states),
        "Initial_State", "s0",
        "Atomic_propositions", " ".join(propositions),
        "Labelling", *labels,
        "Number_of_agents", str(number_of_agents),
    ]
    return "\n".join(sections) + "\n"


def build_formula(number_of_agents: int, bound: int) -> str:
    """Create E{1} followed by n-1 universal variables of bound k."""
    variables = "xyzuvwabcdefghijklmnopqrst"
    if number_of_agents > len(variables):
        raise ValueError(f"At most {len(variables)} agents are supported by the syntax")
    selected = variables[:number_of_agents]
    prefix = f"E{{1}}{selected[0]}" + "".join(
        f"A{{{bound}}}{variable}" for variable in selected[1:]
    )
    bindings = "".join(
        f"({variable},{agent})"
        for agent, variable in enumerate(selected, start=1)
    )
    return f"{prefix}:{bindings}Fgoal"


def raw_domain_size(bound: int, proposition_count: int = 3, actions: int = 2) -> int:
    """Count the syntactically generated one-agent strategies without enumeration."""
    if bound < 1:
        return 0
    guard_counts: dict[int, int] = {}
    max_literals = min(proposition_count, bound // 2)
    for literals in range(1, max_literals + 1):
        cost = 2 * literals - 1
        connectors = 1 if literals == 1 else 2
        count = math.comb(proposition_count, literals) * (2**literals) * connectors
        guard_counts[cost] = guard_counts.get(cost, 0) + count
    costs = tuple(sorted(guard_counts))

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def count_prefixes(remaining: int, used: tuple[int, ...]) -> int:
        total = 1
        for index, cost in enumerate(costs):
            available = guard_counts[cost] - used[index]
            if available <= 0 or cost > remaining:
                continue
            next_used = list(used)
            next_used[index] += 1
            total += available * actions * count_prefixes(remaining - cost, tuple(next_used))
        return total

    return actions * count_prefixes(bound - 1, (0,) * len(costs))


def _peak_rss_mb() -> float:
    try:
        import resource

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return value / (1024 * 1024) if sys.platform == "darwin" else value / 1024
    except ImportError:  # Windows
        import psutil

        memory = psutil.Process().memory_info()
        return getattr(memory, "peak_wset", memory.rss) / (1024 * 1024)


def worker(model: Path, formula: str) -> int:
    """Execute one isolated point and emit one marked JSON line."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from model_checker.algorithms.explicit.NatSL.core import model_checking

    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    result = model_checking(formula, model, mode=SELECTED_MODE)
    payload = {
        "wall_seconds": time.perf_counter() - wall_start,
        "cpu_seconds": time.process_time() - cpu_start,
        "peak_rss_mb": _peak_rss_mb(),
        "result": result,
    }
    print("NATSL_BENCHMARK_RESULT=" + json.dumps(payload, sort_keys=True))
    return 0


def _parse_worker_output(stdout: str) -> dict:
    marker = "NATSL_BENCHMARK_RESULT="
    for line in reversed(stdout.splitlines()):
        if line.startswith(marker):
            return json.loads(line[len(marker):])
    raise RuntimeError("Worker produced no machine-readable result")


def execute_point(
    agents: int, bound: int, repetition: int, model: Path, formula: str,
    timeout: float, run_id: str, states: int, propositions: int,
) -> dict:
    domain_size = raw_domain_size(bound, propositions)
    base = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id, "status": "error", "mode": SELECTED_MODE,
        "scale_id": f"S{states}-P{propositions}",
        "agents": agents, "universal_agents": agents - 1, "bound_k": bound,
        "states": states, "atomic_propositions": propositions,
        "actions_per_universal_agent": 2, "repetition": repetition,
        "timeout_seconds": timeout, "wall_seconds": "", "cpu_seconds": "",
        "peak_rss_mb": "", "satisfiable": "", "existential_candidates": "",
        "universal_profiles_checked": "", "unrestricted_opponent_checks": "",
        "unrestricted_opponent_shortcuts": "", "complete_profile_checks": "",
        "raw_domain_size_per_universal_agent": domain_size,
        "raw_profile_space_upper_bound": domain_size ** (agents - 1),
        "formula": formula, "model_file": str(model), "error": "",
    }
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", str(model), formula]
    outer_start = time.perf_counter()
    try:
        completed = subprocess.run(
            command, cwd=PROJECT_ROOT, text=True, capture_output=True,
            timeout=timeout, check=False,
        )
        outer_elapsed = time.perf_counter() - outer_start
        if completed.returncode != 0:
            base["wall_seconds"] = outer_elapsed
            base["error"] = (completed.stderr or completed.stdout).strip()[-2000:]
            return base
        payload = _parse_worker_output(completed.stdout)
        result = payload["result"]
        base.update(
            status="completed", wall_seconds=payload["wall_seconds"],
            cpu_seconds=payload["cpu_seconds"], peak_rss_mb=payload["peak_rss_mb"],
            satisfiable=result["Satisfiability"],
            existential_candidates=result["Existential candidates"],
            universal_profiles_checked=result["Universal profiles checked"],
            unrestricted_opponent_checks=result["Unrestricted-opponent checks"],
            unrestricted_opponent_shortcuts=result["Unrestricted-opponent shortcuts"],
            complete_profile_checks=result["Complete-profile checks"],
        )
    except subprocess.TimeoutExpired:
        base.update(status="timeout", wall_seconds=timeout, error="timeout")
    except Exception as exc:
        base.update(wall_seconds=time.perf_counter() - outer_start, error=repr(exc))
    return base


def append_row(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in RESULT_FIELDS})


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_summary(results_csv: Path, summary_csv: Path) -> list[dict]:
    grouped: dict[tuple[int, int, int, int], list[dict[str, str]]] = {}
    for row in read_rows(results_csv):
        key = (
            int(row["states"]), int(row["atomic_propositions"]),
            int(row["agents"]), int(row["bound_k"]),
        )
        grouped.setdefault(key, []).append(row)
    summary: list[dict] = []
    for (states, propositions, agents, bound), group in sorted(grouped.items()):
        completed = [row for row in group if row["status"] == "completed"]
        times = [float(row["wall_seconds"]) for row in completed]
        memories = [float(row["peak_rss_mb"]) for row in completed]
        checks = [int(row["universal_profiles_checked"]) for row in completed]
        statuses = {row["status"] for row in group}
        status = "completed" if statuses == {"completed"} else (
            "timeout" if "timeout" in statuses else "partial/error"
        )
        domain_size = raw_domain_size(bound, propositions)
        summary.append({
            "scale_id": f"S{states}-P{propositions}",
            "states": states, "atomic_propositions": propositions,
            "agents": agents, "universal_agents": agents - 1, "bound_k": bound,
            "status": status, "completed_repetitions": len(completed),
            "total_repetitions": len(group),
            "median_wall_seconds": statistics.median(times) if times else "",
            "min_wall_seconds": min(times) if times else "",
            "max_wall_seconds": max(times) if times else "",
            "median_peak_rss_mb": statistics.median(memories) if memories else "",
            "median_universal_profiles_checked": statistics.median(checks) if checks else "",
            "raw_domain_size_per_universal_agent": domain_size,
            "raw_profile_space_upper_bound": domain_size ** (agents - 1),
        })
    fields = tuple(summary[0]) if summary else ("agents", "bound_k", "status")
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)
    return summary


def plot_summary(summary: list[dict], output_dir: Path, timeout: float) -> None:
    """Create individual fixed-k/fixed-agent plots and compact summaries."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Plotting requires matplotlib and numpy") from exc

    agents = sorted({int(row["agents"]) for row in summary})
    bounds = sorted({int(row["bound_k"]) for row in summary})
    scales = sorted({
        (int(row["states"]), int(row["atomic_propositions"])) for row in summary
    })
    lookup = {
        (int(row["states"]), int(row["atomic_propositions"]),
         int(row["agents"]), int(row["bound_k"])): row
        for row in summary
    }
    by_k_dir, by_agents_dir, heatmaps_dir = (
        output_dir / "plots_by_k", output_dir / "plots_by_agents",
        output_dir / "heatmaps_by_scale",
    )
    for directory in (by_k_dir, by_agents_dir, heatmaps_dir):
        directory.mkdir(parents=True, exist_ok=True)

    def scale_label(scale: tuple[int, int]) -> str:
        return f"{scale[0]} states / {scale[1]} APs"

    def values_and_timeouts(rows: list[dict | None], x_values: list[int]):
        values, timeout_points = [], []
        for row, x_value in zip(rows, x_values):
            value = row.get("median_wall_seconds", "") if row else ""
            values.append(float(value) if value != "" else float("nan"))
            if row and row["status"] != "completed":
                timeout_points.append(x_value)
        return values, timeout_points

    def decorate(axis, xlabel: str, title: str) -> None:
        axis.set_yscale("log")
        axis.set_xlabel(xlabel)
        axis.set_ylabel("Median verification time (seconds, log scale)")
        axis.set_title(title)
        axis.grid(True, which="both", alpha=0.25)

    def save(fig, stem: Path) -> None:
        fig.tight_layout()
        fig.savefig(stem.with_suffix(".png"), dpi=220)
        fig.savefig(stem.with_suffix(".pdf"))
        plt.close(fig)

    def plot_scales(axis, x_values: list[int], fixed: int, by_bound: bool) -> None:
        for scale_index, scale in enumerate(scales):
            states, propositions = scale
            rows = [
                lookup.get((states, propositions, agent, fixed))
                if by_bound else lookup.get((states, propositions, fixed, bound))
                for agent, bound in (
                    [(agent, fixed) for agent in x_values]
                    if by_bound else [(fixed, bound) for bound in x_values]
                )
            ]
            values, timeout_points = values_and_timeouts(rows, x_values)
            line = axis.plot(x_values, values, marker="o", label=scale_label(scale))[0]
            if timeout_points:
                offset = (scale_index - (len(scales) - 1) / 2) * 0.025
                axis.scatter([x + offset for x in timeout_points], [timeout] * len(timeout_points),
                             marker="^", s=58, color=line.get_color())

    # Explicitly requested: one graph for each fixed k.
    for bound in bounds:
        fig, axis = plt.subplots(figsize=(7.2, 4.5))
        plot_scales(axis, agents, bound, by_bound=True)
        decorate(axis, "Number of agents", f"Verification time at k={bound}")
        axis.set_xticks(agents)
        axis.legend(title="Model scale")
        axis.text(0.01, 0.01, "Triangles denote timeout runs.",
                  transform=axis.transAxes, fontsize=8)
        save(fig, by_k_dir / f"runtime_k_{bound}")

    # Explicitly requested: one graph for each fixed number of agents.
    for agent_count in agents:
        fig, axis = plt.subplots(figsize=(7.2, 4.5))
        plot_scales(axis, bounds, agent_count, by_bound=False)
        decorate(axis, "Universal strategy-complexity bound k",
                 f"Verification time with {agent_count} agents")
        axis.set_xticks(bounds)
        axis.legend(title="Model scale")
        axis.text(0.01, 0.01, "Triangles denote timeout runs.",
                  transform=axis.transAxes, fontsize=8)
        save(fig, by_agents_dir / f"runtime_agents_{agent_count}")

    def subplot_grid(items: list[int], by_bound: bool, stem: str, title: str) -> None:
        columns = 2
        rows_count = math.ceil(len(items) / columns)
        fig, axes = plt.subplots(rows_count, columns, figsize=(12, 4.4 * rows_count),
                                 squeeze=False, sharey=True)
        for axis, item in zip(axes.flat, items):
            x_values = agents if by_bound else bounds
            plot_scales(axis, x_values, item, by_bound)
            decorate(
                axis,
                "Number of agents" if by_bound else "Bound k",
                f"k={item}" if by_bound else f"{item} agents",
            )
            axis.set_xticks(x_values)
        for axis in axes.flat[len(items):]:
            axis.set_visible(False)
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.suptitle(title, y=0.99)
        fig.legend(handles, labels, title="Model scale", loc="upper center",
                   bbox_to_anchor=(0.5, 0.95), ncol=min(len(scales), 4))
        fig.tight_layout(rect=(0, 0, 1, 0.86))
        fig.savefig((output_dir / stem).with_suffix(".png"), dpi=220)
        fig.savefig((output_dir / stem).with_suffix(".pdf"))
        plt.close(fig)

    subplot_grid(bounds, True, "summary_by_k",
                 "NatSL verification time: one panel per strategy bound")
    subplot_grid(agents, False, "summary_by_agents",
                 "NatSL verification time: one panel per agent count")

    # One pair of heatmaps for every state/AP scale.
    for states, propositions in scales:
        matrix = np.full((len(agents), len(bounds)), np.nan)
        annotations = [["" for _ in bounds] for _ in agents]
        search_matrix = np.zeros((len(agents), len(bounds)))
        search_annotations = [["" for _ in bounds] for _ in agents]
        for row_index, agent_count in enumerate(agents):
            for column_index, bound in enumerate(bounds):
                row = lookup.get((states, propositions, agent_count, bound))
                if row:
                    value = row.get("median_wall_seconds", "")
                    if value != "":
                        matrix[row_index, column_index] = math.log10(max(float(value), 1e-6))
                        annotations[row_index][column_index] = f"{float(value):.2g}s"
                    elif row["status"] == "timeout":
                        matrix[row_index, column_index] = math.log10(timeout)
                        annotations[row_index][column_index] = f">={timeout:g}s"
                profiles = raw_domain_size(bound, propositions) ** (agent_count - 1)
                search_matrix[row_index, column_index] = math.log10(max(profiles, 1))
                search_annotations[row_index][column_index] = f"{profiles:.2e}"

        for data, annotations_data, cmap, prefix, color_label, graph_title in (
            (matrix, annotations, "viridis", "runtime", "log10(seconds)",
             f"Verification time: {states} states / {propositions} APs"),
            (search_matrix, search_annotations, "magma", "strategy_space",
             "log10(number of profiles)",
             f"Raw profile-space upper bound: {states} states / {propositions} APs"),
        ):
            fig, axis = plt.subplots(figsize=(7.2, 4.2))
            image = axis.imshow(data, aspect="auto", cmap=cmap)
            axis.set_xticks(range(len(bounds)), bounds)
            axis.set_yticks(range(len(agents)), agents)
            axis.set_xlabel("Universal strategy-complexity bound k")
            axis.set_ylabel("Number of agents")
            axis.set_title(graph_title)
            for row_index in range(len(agents)):
                for column_index in range(len(bounds)):
                    label = annotations_data[row_index][column_index]
                    if label:
                        axis.text(column_index, row_index, label, ha="center",
                                  va="center", color="white", fontsize=8)
            fig.colorbar(image, ax=axis).set_label(color_label)
            save(fig, heatmaps_dir / f"{prefix}_S{states}_P{propositions}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", nargs="+", type=int, default=[2, 3, 4, 5])
    parser.add_argument("--bounds", nargs="+", type=int, default=[1, 2, 3, 4])
    parser.add_argument(
        "--scales", nargs="+", metavar="STATES:APS",
        help="Model scales, e.g. --scales 6:3 10:5 14:7 18:9",
    )
    parser.add_argument("--states", type=int, help="Backward-compatible single-scale state count")
    parser.add_argument("--propositions", type=int,
                        help="Atomic propositions for --states (default: ceil(states/2))")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output", type=Path,
        default=PROJECT_ROOT / "benchmark_results" / "local_run")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--quick", action="store_true", help="Run agents=2, k=1..2 once")
    parser.add_argument("--worker", nargs=2, metavar=("MODEL", "FORMULA"), help=argparse.SUPPRESS)
    return parser.parse_args()


def parse_scales(arguments: argparse.Namespace) -> list[tuple[int, int]]:
    if arguments.scales and arguments.states is not None:
        raise SystemExit("Use either --scales or --states, not both")
    if arguments.scales:
        parsed: list[tuple[int, int]] = []
        for item in arguments.scales:
            try:
                states_text, propositions_text = item.split(":", 1)
                parsed.append((int(states_text), int(propositions_text)))
            except (ValueError, TypeError) as exc:
                raise SystemExit(f"Invalid scale {item!r}; expected STATES:APS") from exc
    elif arguments.states is not None:
        propositions = arguments.propositions or math.ceil(arguments.states / 2)
        parsed = [(arguments.states, propositions)]
    else:
        if arguments.propositions is not None:
            raise SystemExit("--propositions requires --states")
        parsed = list(DEFAULT_SCALES)
    parsed = sorted(set(parsed))
    if any(states < 3 or propositions < 3 for states, propositions in parsed):
        raise SystemExit("Every scale requires at least 3 states and 3 propositions")
    return parsed


def main() -> int:
    arguments = parse_arguments()
    if arguments.worker:
        return worker(Path(arguments.worker[0]), arguments.worker[1])
    scales = parse_scales(arguments)
    if arguments.quick:
        arguments.agents, arguments.bounds, arguments.repetitions = [2], [1, 2], 1
        arguments.timeout = min(arguments.timeout, 60.0)
        scales = [(6, 3)]
    if any(value < 2 for value in arguments.agents):
        raise SystemExit("All agent counts must be at least 2")
    if any(value < 1 for value in arguments.bounds):
        raise SystemExit("All bounds must be positive")
    if arguments.repetitions < 1 or arguments.timeout <= 0:
        raise SystemExit("repetitions > 0 and timeout > 0 are required")

    output_dir = arguments.output.resolve()
    models_dir = output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    results_csv, summary_csv = output_dir / "results.csv", output_dir / "summary.csv"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    configuration = {
        "run_id": run_id,
        "selected_architecture": "space-efficient alternating depth-first",
        "mode": SELECTED_MODE, "agents": sorted(set(arguments.agents)),
        "bounds": sorted(set(arguments.bounds)),
        "scales": [
            {"states": states, "atomic_propositions": propositions}
            for states, propositions in scales
        ],
        "actions_per_universal_agent": 2, "repetitions": arguments.repetitions,
        "timeout_seconds": arguments.timeout, "python": sys.version,
        "python_executable": sys.executable, "platform": platform.platform(),
        "processor": platform.processor(), "logical_cpu_count": os.cpu_count(),
        "started_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        import psutil

        configuration["physical_cpu_count"] = psutil.cpu_count(logical=False)
        configuration["system_memory_gb"] = round(
            psutil.virtual_memory().total / (1024**3), 3
        )
    except ImportError:
        pass
    configuration_path = output_dir / "configuration.json"
    if not arguments.resume and (configuration_path.exists() or results_csv.exists()):
        raise SystemExit(
            f"Output directory already contains benchmark data: {output_dir}. "
            "Use --resume or select a different --output directory."
        )
    if arguments.resume and configuration_path.exists():
        existing_configuration = json.loads(configuration_path.read_text(encoding="utf-8"))
        comparison_keys = (
            "mode", "agents", "bounds", "scales",
            "actions_per_universal_agent", "repetitions", "timeout_seconds",
        )
        mismatches = [
            key for key in comparison_keys
            if existing_configuration.get(key) != configuration.get(key)
        ]
        if mismatches:
            raise SystemExit(
                "Cannot resume with a different configuration; mismatched fields: "
                + ", ".join(mismatches)
            )
    else:
        configuration_path.write_text(
            json.dumps(configuration, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    models: dict[tuple[int, int, int], Path] = {}
    for states, propositions in scales:
        for agents in sorted(set(arguments.agents)):
            model = models_dir / (
                f"bounded_opponent_S{states}_P{propositions}_{agents}_agents.txt"
            )
            model.write_text(
                build_model(agents, states, propositions), encoding="utf-8"
            )
            models[(states, propositions, agents)] = model

    completed_keys: set[tuple[int, int, int, int, int]] = set()
    if arguments.resume:
        for row in read_rows(results_csv):
            completed_keys.add((
                int(row["states"]), int(row["atomic_propositions"]),
                int(row["agents"]), int(row["bound_k"]), int(row["repetition"]),
            ))
    points = [
        (states, propositions, agents, bound, repetition)
        for states, propositions in scales
        for agents in sorted(set(arguments.agents))
        for bound in sorted(set(arguments.bounds))
        for repetition in range(1, arguments.repetitions + 1)
    ]
    for index, (states, propositions, agents, bound, repetition) in enumerate(points, start=1):
        key = (states, propositions, agents, bound, repetition)
        if key in completed_keys:
            print(f"[{index}/{len(points)}] skip S={states}, P={propositions}, "
                  f"n={agents}, k={bound}, r={repetition}")
            continue
        formula = build_formula(agents, bound)
        print(f"[{index}/{len(points)}] run S={states}, P={propositions}, "
              f"n={agents}, k={bound}, r={repetition}", flush=True)
        row = execute_point(
            agents, bound, repetition, models[(states, propositions, agents)], formula,
            arguments.timeout, run_id, states, propositions,
        )
        append_row(results_csv, row)
        print(f"  -> {row['status']} in {float(row['wall_seconds']):.3f}s; "
              f"universal profiles={row['universal_profiles_checked'] or 'n/a'}", flush=True)

    summary = write_summary(results_csv, summary_csv)
    if not arguments.no_plots:
        plot_summary(summary, output_dir, arguments.timeout)
    print(f"Results: {results_csv}")
    print(f"Summary: {summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
