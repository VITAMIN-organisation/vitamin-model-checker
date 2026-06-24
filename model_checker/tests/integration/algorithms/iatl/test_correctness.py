"""Semantics and theory-alignment tests for IATL model checking."""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.IATL.checker import IATLModelChecker
from model_checker.algorithms.explicit.IATL.IATL import model_checking
from model_checker.algorithms.explicit.IATL.solver import solve_tree
from model_checker.algorithms.explicit.IATL.util.graph import read_file
from model_checker.algorithms.explicit.shared.fixpoint_iter import greatest_fixpoint
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.literals import parse_state_set_literal

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "CGS"
    / "IATL"
    / "iatl_2agents_2states_minimal.txt"
)
_FIGURE2_MODEL = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "CGS"
    / "IATL"
    / "iatl_figure2_proposition1.txt"
)


def _states_from_checker(checker, formula):
    parser = FormulaParserFactory.get_parser_instance("IATL")
    parsed = parser.parse(formula, n_agent=checker.data["number_of_agents"])
    assert parsed is not None, parser.errors
    root = checker.build_tree(parsed)
    assert root is not None
    solve_tree(checker, root)
    return parse_state_set_literal(root.value)


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


def _coalition_top_until(checker, coalition, phi_states):
    pset: set[str] = set()
    t = set(phi_states)
    while t - pset:
        pset |= t
        t = checker.pre_forall(coalition, pset)
    return pset


def _coalition_bottom_release(checker, coalition, phi_states):
    def update(current):
        return phi_states & checker.pre_forall(coalition, current)

    return greatest_fixpoint(checker.states_set.copy(), update)


def _coalition_exists_top_until(checker, coalition, phi_states):
    pset: set[str] = set()
    t = set(phi_states)
    while t - pset:
        pset |= t
        t = checker.pre_exists(coalition, pset)
    return pset


def _coalition_exists_bottom_release(checker, coalition, phi_states):
    def update(current):
        return phi_states & checker.pre_exists(coalition, current)

    return greatest_fixpoint(checker.states_set.copy(), update)


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
        assert "error" not in result
        assert (
            parse_state_set_literal(result["res"].removeprefix("Result: "))
            == expected_states
        )
        assert result["initial_state"] == f"Initial state s0: {initial_satisfied}"


class TestCoalitionPreimages:
    def test_pre_d_and_pre_f_on_fixture(self):
        checker = IATLModelChecker(read_file(str(_FIXTURE)))
        targets = {"s0"}
        assert "s0" in checker.pre_exists("1", targets)
        assert "s0" not in checker.pre_forall("1", targets)


class TestUniversalNext:
    def test_forall_next_equals_pre_f(self):
        checker = IATLModelChecker(read_file(str(_FIXTURE)))
        p_states = {"s0"}
        paper_next = checker.pre_forall("1", p_states)
        impl = _states_from_checker(checker, "[1]X p")
        assert impl == paper_next


class TestSugarEncodings:
    """F/G sugar must match paper encodings on the minimal fixture."""

    def test_exists_eventually_matches_top_until(self):
        checker = IATLModelChecker(read_file(str(_FIXTURE)))
        phi_states = _states_from_checker(checker, "p")
        assert _states_from_checker(checker, "<1>F p") == _coalition_exists_top_until(
            checker, "1", phi_states
        )

    def test_forall_eventually_matches_top_until(self):
        checker = IATLModelChecker(read_file(str(_FIXTURE)))
        phi_states = _states_from_checker(checker, "p")
        assert _states_from_checker(checker, "[1]F p") == _coalition_top_until(
            checker, "1", phi_states
        )

    def test_exists_globally_matches_bottom_release(self):
        checker = IATLModelChecker(read_file(str(_FIXTURE)))
        phi_states = _states_from_checker(checker, "p")
        assert _states_from_checker(
            checker, "<1>G p"
        ) == _coalition_exists_bottom_release(checker, "1", phi_states)

    def test_forall_globally_matches_bottom_release(self):
        checker = IATLModelChecker(read_file(str(_FIXTURE)))
        phi_states = _states_from_checker(checker, "p")
        assert _states_from_checker(checker, "[1]G p") == _coalition_bottom_release(
            checker, "1", phi_states
        )


class TestUpwardClosure:
    def test_intuitionistic_not_respects_preorder(self, tmp_path):
        model_path = tmp_path / "iatl_custom_states.txt"
        model_path.write_text(_custom_preorder_model_text(), encoding="utf-8")
        checker = IATLModelChecker(read_file(str(model_path)))
        states = _states_from_checker(checker, "!p")
        assert states == {"beta"}
        assert "alpha" not in states


class TestExcludedMiddleCountermodel:
    """Grand coalition cannot force p or !p next at s0, yet both claims hold in IATL.

    Classical ATL cannot satisfy !<1,2>X p && !<1,2>X !p. IATL can, because s1 has
    undetermined p under the information preorder (see iatl_figure2_proposition1.txt).
    """

    _EXCLUDED_MIDDLE_FORMULA = "!<1,2>X p && !<1,2>X !p"

    def test_countermodel_passes_validation(self):
        data = read_file(str(_FIGURE2_MODEL))
        assert data["initial_state"] == "s0"
        assert data["states_counter"] == 3

    def test_excluded_middle_formula_holds_at_s0(self):
        checker = IATLModelChecker(read_file(str(_FIGURE2_MODEL)))
        satisfied = _states_from_checker(checker, self._EXCLUDED_MIDDLE_FORMULA)
        assert "s0" in satisfied

    def test_s1_has_undetermined_p(self):
        checker = IATLModelChecker(read_file(str(_FIGURE2_MODEL)))
        p_states = _states_from_checker(checker, "p")
        not_p_states = _states_from_checker(checker, "!p")
        assert "s1" not in p_states
        assert "s1" not in not_p_states

    def test_excluded_middle_via_vmi_entry(self):
        result = model_checking(self._EXCLUDED_MIDDLE_FORMULA, str(_FIGURE2_MODEL))
        assert "error" not in result
        states = parse_state_set_literal(result["res"].removeprefix("Result: "))
        assert "s0" in states
        assert result["initial_state"] == "Initial state s0: True"


class TestValidation:
    def test_fixture_passes_validation(self):
        data = read_file(str(_FIXTURE))
        assert data["states_counter"] == 2
        assert data["number_of_agents"] == 2
