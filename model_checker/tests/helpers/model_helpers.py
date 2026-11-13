"""Load fixture models, load models from text, and read the state set out of a result."""

import ast
from pathlib import Path

import pytest

from model_checker.models.model_factory import create_model_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS
from model_checker.parsers.game_structures.fuzzy_cgs.fuzzy_cgs import FuzzyCGS
from model_checker.tests.helpers.synthetic_models import (
    build_cgs_model_content,
    generate_cost_cgs_linear_chain_content,
    generate_cycle_model,
    generate_fully_connected_model,
    generate_linear_chain,
    generate_sparse_graph_model,
)


def assert_parse_structure(result, expected_structure=None, description=""):
    """Assert that parse result has correct structure."""
    assert result is not None, f"Parse result should not be None: {description}"

    if isinstance(result, str):
        return

    assert isinstance(result, tuple), (
        f"Parse result should be a tuple, got {type(result).__name__}: {description}"
    )

    assert len(result) >= 2, (
        f"Parse result tuple should have at least 2 elements, got {len(result)}: {description}"
    )


def load_test_model(test_data_dir, model_path: str):
    """Load fixtures/<model_path> with the parser the factory picks; fail the test if it does not load.

    The parser's .filename is set, for entry points that take a path.
    """
    path_str = str(test_data_dir / Path(*model_path.split("/")))
    try:
        parser = create_model_parser(path_str)
        parser.read_file(path_str)
        parser.filename = path_str
        return parser
    except Exception as e:
        pytest.fail(
            f"Failed to load model {model_path}\n"
            f"Error type: {type(e).__name__}\n"
            f"Error message: {str(e)}"
        )


def load_cgs_from_content(temp_file, content):
    """Load CGS from string content via a temp file."""
    parser = CGS()
    file_path = temp_file(content)
    parser.filename = str(file_path)
    parser.read_file(file_path)
    return parser


def load_costcgs_from_content(temp_file, content):
    """Load costCGS from string content via a temp file."""
    parser = CostCGS()
    file_path = temp_file(content)
    parser.read_file(file_path)
    return parser


def load_fuzzycgs_from_content(temp_file, content):
    """Load fuzzyCGS from string content via a temp file."""
    parser = FuzzyCGS()
    parser.read_file(temp_file(content))
    return parser


def extract_states_from_result(result):
    """Parse "Result: {state_set}" from model_checking dict; returns set or None."""
    if "error" in result:
        return None
    res_str = result.get("res", "")
    if "Result:" not in res_str:
        return None
    states_str = res_str.split("Result:")[1].strip()
    try:
        states = ast.literal_eval(states_str)
        if isinstance(states, set):
            return states
        if isinstance(states, (list, tuple)):
            return set(states)
        return None
    except (ValueError, SyntaxError, TypeError):
        return None


__all__ = [
    "load_test_model",
    "load_cgs_from_content",
    "load_costcgs_from_content",
    "extract_states_from_result",
    "build_cgs_model_content",
    "generate_linear_chain",
    "generate_cycle_model",
    "generate_fully_connected_model",
    "generate_sparse_graph_model",
    "generate_cost_cgs_linear_chain_content",
    "assert_parse_structure",
]
