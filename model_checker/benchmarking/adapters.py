"""Adapters from benchmark cases to model checker callables and models."""

import logging

from model_checker.discovery import discover_logic_resource
from model_checker.benchmarking.generators import (
    generate_capcgs_linear_chain_model,
    generate_cost_cgs_linear_chain_content,
    generate_cycle_model,
    generate_linear_chain_model,
    generate_natatl_linear_chain_model,
)
from model_checker.registries import get_benchmark_group

logger = logging.getLogger(__name__)


def get_model_checker(logic: str):
    """Return model_checking(formula, filename) for the given logic name.

    Uses standard entry points discoverable via 'vitamin.benchmarks'.
    """
    try:
        return discover_logic_resource(
            logic_name=logic,
            group="vitamin.benchmarks",
            resource_type_label="Benchmark logic",
        )
    except (ImportError, LookupError) as e:
        raise ValueError(f"Unknown logic for benchmark: '{logic}': {e}")


def get_model_content(logic: str, layout: str, num_states: int) -> str:
    """Generate model text for the given logic, layout, and state count."""
    num_agents = 2

    group = get_benchmark_group(logic)

    if group == "CGS":
        if layout == "linear":
            return generate_linear_chain_model(num_states, num_agents)
        if layout == "cycle":
            return generate_cycle_model(num_states, num_agents)
        raise ValueError(f"Unsupported layout {layout!r} for CGS-based logic {logic!r}")

    if group == "natATL":
        if layout != "linear":
            raise ValueError(
                f"Logic {logic!r} (natATL) only supports linear layout (got {layout!r})"
            )
        return generate_natatl_linear_chain_model(num_states, num_agents)

    if group == "capCGS":
        if layout != "linear":
            raise ValueError(
                f"Logic {logic!r} (capCGS) only supports linear layout (got {layout!r})"
            )
        return generate_capcgs_linear_chain_model(num_states, num_agents)

    if group == "costCGS":
        if layout != "linear":
            raise ValueError(
                f"Logic {logic!r} (costCGS) only supports linear layout (got {layout!r})"
            )
        return generate_cost_cgs_linear_chain_content(num_states, num_agents)

    raise ValueError(
        f"Unknown benchmark group {group!r} for logic {logic!r}. "
        "Add it to a model family or benchmark_group in metadata."
    )
