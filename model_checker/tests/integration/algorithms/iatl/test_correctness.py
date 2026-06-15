"""Semantics and theory-alignment tests for IATL model checking."""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.IATL.checker import IATLModelChecker
from model_checker.algorithms.explicit.IATL.IATL import model_checking
from model_checker.algorithms.explicit.IATL.util.graph import read_file
from model_checker.utils.literals import parse_state_set_literal

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "CGS"
    / "IATL"
    / "iatl_2agents_2states_minimal.txt"
)


def _states_from_result(result):
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


def _custom_preorder_model_text():
    return """\
Transition
II,II AA,AA
0 II,II
Preorder
1 0
0 1
Name_State
alpha beta
Initial_State
beta
Atomic_propositions
p
Labelling
1
0
Number_of_agents
2
"""


class TestFixtureSemantics:
    """Pinned state sets on the minimal two-state BCGS fixture."""

    @pytest.mark.parametrize(
        ("formula", "expected_states", "initial_satisfied"),
        [
            ("<1>X p", {"s0"}, True),
            ("[1]X p", set(), False),
            ("<1>F p", {"s0"}, True),
            ("<1>G p", {"s0"}, True),
            ("<1>p U p", {"s0"}, True),
            ("<1>p R p", {"s0"}, True),
            ("[1]p R p", {"s0"}, True),
            ("[1]F p", {"s0"}, True),
            ("[1]G p", set(), False),
            ("[1]p U p", {"s0"}, True),
            ("!p", {"s1"}, False),
            ("p -> p", {"s0", "s1"}, True),
        ],
    )
    def test_formula_result(self, formula, expected_states, initial_satisfied):
        result = model_checking(formula, str(_FIXTURE))
        assert _states_from_result(result) == expected_states
        assert result["initial_state"] == f"Initial state s0: {initial_satisfied}"


class TestCoalitionPreimages:
    def test_pre_d_and_pre_f_on_fixture(self):
        data = read_file(str(_FIXTURE))
        checker = IATLModelChecker(data)
        targets = {"s0"}
        assert "s0" in checker.pre_exists("1", targets)
        assert "s0" not in checker.pre_forall("1", targets)


class TestUpwardClosure:
    def test_universal_next_restricts_pre_forall(self, tmp_path):
        model_path = tmp_path / "iatl_upset_next.txt"
        model_path.write_text(_custom_preorder_model_text(), encoding="utf-8")
        checker = IATLModelChecker(read_file(str(model_path)))
        pre_forall = checker.pre_forall("1", {"p"})
        assert pre_forall == set()
        assert checker.states_with_upset_in(pre_forall) == set()

    def test_intuitionistic_not_respects_preorder(self, tmp_path):
        model_path = tmp_path / "iatl_custom_states.txt"
        model_path.write_text(_custom_preorder_model_text(), encoding="utf-8")
        result = model_checking("!p", str(model_path))
        states = _states_from_result(result)
        assert states == {"beta"}
        assert "alpha" not in states


class TestValidation:
    def test_fixture_passes_validation(self):
        data = read_file(str(_FIXTURE))
        assert data["states_counter"] == 2
        assert data["number_of_agents"] == 2
