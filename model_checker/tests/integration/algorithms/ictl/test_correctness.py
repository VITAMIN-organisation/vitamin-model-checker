"""Semantics and theory-alignment tests for ICTL model checking."""

from pathlib import Path

import numpy as np
import pytest

from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
from model_checker.algorithms.explicit.ICTL.ICTL import (
    model_checking,
    run_model_checking,
)
from model_checker.algorithms.explicit.ICTL.preimage import pre_image_all
from model_checker.algorithms.explicit.ICTL.util.graph import (
    get_preorder,
    labeled_pairs,
    read_file,
)
from model_checker.utils.literals import parse_state_set_literal

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_EXPERIMENT_MODEL = _FIXTURES / "experiment_2x3.txt"


def _states_from_result(result):
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


def _ax_chain_model_data():
    """Three-state P-chain where classical Pre_forall differs from ICTL AX."""
    graph = np.full((3, 3), "0", dtype=object)
    np.fill_diagonal(graph, "P,R")
    graph[0, 1] = "P,R"
    graph[1, 2] = "P"
    matrix_prop = np.array([[1, 0, 0], [1, 0, 0], [0, 0, 0]])
    return {
        "graph": graph,
        "states": np.array(["s0", "s1", "s2"]),
        "atomic_propositions": np.array(["e", "h", "c"]),
        "matrix_prop": matrix_prop,
        "initial_state": "s0",
        "states_counter": 3,
        "atomic_propositions_counter": 3,
    }


class TestPreorderClosure:
    def test_get_preorder_computes_transitive_closure(self):
        graph = np.array(
            [
                ["P", "P", "0"],
                ["0", "P", "P"],
                ["0", "0", "P"],
            ],
            dtype=object,
        )
        states = np.array(["s0", "s1", "s2"])
        preorder_edges = labeled_pairs(graph, states, lambda cell: cell in ("P", "P,R"))
        closure = get_preorder(preorder_edges, states)

        assert closure["s0"] == {"s0", "s1", "s2"}
        assert closure["s1"] == {"s1", "s2"}
        assert closure["s2"] == {"s2"}


class TestUpwardClosureOperators:
    def test_ax_restricts_classical_pre_forall(self):
        checker = ICTLModelChecker(_ax_chain_model_data())
        negated = checker.states_set - {"s0", "s1"}
        classical_ax = checker.states_set - pre_image_all(checker.edges, negated)
        ictl_ax = _states_from_result(run_model_checking("AX e", checker))

        assert classical_ax == {"s0", "s1"}
        assert ictl_ax == set()
        assert ictl_ax <= classical_ax

    def test_implication_uses_upward_closure(self):
        checker = ICTLModelChecker(_ax_chain_model_data())
        states = _states_from_result(run_model_checking("e -> h", checker))
        assert states == {"s2"}


class TestReleaseOperators:
    def test_existential_release_on_fixture(self):
        result = model_checking("E e R h", str(_EXPERIMENT_MODEL))
        assert _states_from_result(result) == {"s2"}

    def test_universal_release_on_fixture(self):
        result = model_checking("A e R h", str(_EXPERIMENT_MODEL))
        assert _states_from_result(result) == set()


class TestUntilOperators:
    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_satisfied"),
        [
            ("E e U h", {"s1", "s2", "s3", "s4", "s5"}, False),
            ("A e U h", {"s2", "s3", "s4", "s5"}, False),
            ("E e U c", set(), False),
        ],
    )
    def test_until_on_fixture(self, formula, expected_states, initial_satisfied):
        result = model_checking(formula, str(_EXPERIMENT_MODEL))
        assert _states_from_result(result) == expected_states
        assert result["initial_state"] == f"Initial state s0: {initial_satisfied}"


class TestFixtureSemantics:
    """Pinned results for the deterministic experiment_2x3 fixture."""

    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_satisfied"),
        [
            ("EX e", {"s0", "s1", "s3"}, True),
            ("EF e", {"s0", "s1", "s2", "s3", "s4", "s5"}, True),
            ("AG e", {"s1"}, False),
            ("!(e -> h)", {"s1", "s4"}, False),
            ("AX e", {"s0", "s3"}, True),
            ("EG e", {"s1"}, False),
            ("AF e", {"s0", "s1", "s2", "s3", "s4", "s5"}, True),
        ],
    )
    def test_formula_result(self, formula, expected_states, initial_satisfied):
        result = model_checking(formula, str(_EXPERIMENT_MODEL))
        assert _states_from_result(result) == expected_states
        assert result["initial_state"] == f"Initial state s0: {initial_satisfied}"


class TestVmiEntry:
    def test_model_checking_returns_standard_result(self):
        result = model_checking("EF e", str(_EXPERIMENT_MODEL))
        assert "error" not in result
        assert result["res"].startswith("Result:")
        assert result["formula"] == "EF e"
        assert result["model"] == str(_EXPERIMENT_MODEL)
        assert "raw_result" not in result


class TestValidation:
    def test_fixture_passes_validation(self):
        data = read_file(str(_EXPERIMENT_MODEL))
        assert data["initial_state"] == "s0"
        assert data["states_counter"] == 6
