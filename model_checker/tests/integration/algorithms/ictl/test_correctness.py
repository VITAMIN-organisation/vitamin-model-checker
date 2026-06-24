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
    read_file,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import greatest_fixpoint
from model_checker.algorithms.explicit.shared.graph_relations import labeled_pairs
from model_checker.utils.literals import parse_state_set_literal

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_EXPERIMENT_MODEL = _FIXTURES / "experiment_2x3.txt"


def _states_from_checker(checker, formula):
    result = run_model_checking(formula, checker)
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


def _ax_chain_model_data():
    """Three-state P-chain used for upward-closure propositional checks."""
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


def _figure5_countermodel_data():
    """Figure 5 (EUMAS25b): preorder countermodel for Proposition 3."""
    graph = np.array(
        [
            ["P,R", "P", "P"],
            ["0", "P,R", "0"],
            ["R", "0", "P,R"],
        ],
        dtype=object,
    )
    return {
        "graph": graph,
        "states": np.array(["s1", "s2", "s3"]),
        "atomic_propositions": np.array(["p"]),
        "matrix_prop": np.array([[0], [0], [1]]),
        "initial_state": "s1",
        "states_counter": 3,
        "atomic_propositions_counter": 1,
    }


def _a_top_until(checker, phi_states):
    """Paper encoding AF phi = A(T U phi)."""
    all_states = checker.states_set
    p: set[str] = set()
    t = set(phi_states)
    while t - p:
        p.update(t)
        t = pre_image_all(checker.edges, p) & all_states
    return p


def _a_bottom_release(checker, phi_states):
    """Paper encoding AG phi = A(bottom R phi)."""

    def update(q1):
        return phi_states & pre_image_all(checker.edges, q1)

    return greatest_fixpoint(checker.states_set, update)


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
    def test_ax_equals_pre_forall(self):
        checker = ICTLModelChecker(_ax_chain_model_data())
        e_states = {"s0", "s1"}
        paper_ax = pre_image_all(checker.edges, e_states)
        ictl_ax = _states_from_checker(checker, "AX e")

        assert paper_ax == {"s0", "s1"}
        assert ictl_ax == paper_ax

    def test_implication_uses_upward_closure(self):
        checker = ICTLModelChecker(_ax_chain_model_data())
        states = _states_from_checker(checker, "e -> h")
        assert states == {"s2"}


class TestSugarEncodings:
    """AF/AG sugar must match paper encodings A(T U phi) and A(bottom R phi)."""

    @pytest.mark.parametrize("atom", ["e", "h"])
    def test_af_matches_a_top_until_on_fixture(self, atom):
        data = read_file(str(_EXPERIMENT_MODEL))
        checker = ICTLModelChecker(data)
        phi_states = _states_from_checker(checker, atom)
        assert _states_from_checker(checker, f"AF {atom}") == _a_top_until(
            checker, phi_states
        )

    @pytest.mark.parametrize("atom", ["e", "h"])
    def test_ag_matches_a_bottom_release_on_fixture(self, atom):
        data = read_file(str(_EXPERIMENT_MODEL))
        checker = ICTLModelChecker(data)
        phi_states = _states_from_checker(checker, atom)
        assert _states_from_checker(checker, f"AG {atom}") == _a_bottom_release(
            checker, phi_states
        )


class TestPaperCountermodels:
    def test_figure5_proposition3_next_duality_fails_at_s1(self):
        checker = ICTLModelChecker(_figure5_countermodel_data())
        not_ax_p = _states_from_checker(checker, "!AX p")
        ex_not_p = _states_from_checker(checker, "EX !p")

        assert "s1" in not_ax_p
        assert "s1" not in ex_not_p


class TestReleaseOperators:
    def test_existential_release_on_fixture(self):
        checker = ICTLModelChecker(read_file(str(_EXPERIMENT_MODEL)))
        assert _states_from_checker(checker, "E e R h") == {"s2"}

    def test_universal_release_on_fixture(self):
        checker = ICTLModelChecker(read_file(str(_EXPERIMENT_MODEL)))
        assert _states_from_checker(checker, "A e R h") == set()


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
        assert "error" not in result
        assert (
            parse_state_set_literal(result["res"].removeprefix("Result: "))
            == expected_states
        )
        assert result["initial_state"] == f"Initial state s0: {initial_satisfied}"


class TestFixtureSemantics:
    """Pinned results for the deterministic experiment_2x3 fixture."""

    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_satisfied"),
        [
            ("EX e", {"s0", "s1", "s3"}, True),
            ("EF e", {"s0", "s1", "s2", "s3", "s4", "s5"}, True),
            ("AG e", set(), False),
            ("!(e -> h)", {"s1", "s4"}, False),
            ("AX e", {"s0", "s3"}, True),
            ("AX h", {"s4", "s5"}, False),
            ("EG e", {"s1"}, False),
            ("AF e", {"s0", "s1", "s3", "s4", "s5"}, True),
        ],
    )
    def test_formula_result(self, formula, expected_states, initial_satisfied):
        result = model_checking(formula, str(_EXPERIMENT_MODEL))
        assert "error" not in result
        assert (
            parse_state_set_literal(result["res"].removeprefix("Result: "))
            == expected_states
        )
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

    def test_figure5_countermodel_passes_validation(self):
        from model_checker.algorithms.explicit.ICTL.util.validation import (
            check_conditions_hold,
        )

        check_conditions_hold(_figure5_countermodel_data())
