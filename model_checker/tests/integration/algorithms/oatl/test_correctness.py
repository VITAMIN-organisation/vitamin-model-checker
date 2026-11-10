"""OATL model checking tests; the least budget 3 on the attack model is the one stated in the OATL paper."""

import pytest

from model_checker.algorithms.explicit.OATL.OATL import (
    _core_oatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content

# Alice and Bob never hold root (r, s) while David holds resource 1 (g).
ATTACK_NEVER_COMPLETED = "!(r && s && g)"


def _one_agent_model(transitions, labelling, costs, prop_names=("p",)):
    return build_cgs_model_content(
        transitions=transitions,
        state_names=[f"s{i}" for i in range(len(transitions))],
        initial_state="s0",
        labelling=labelling,
        num_agents=1,
        prop_names=list(prop_names),
        costs_for_actions=costs,
    )


def _holds_initially(result) -> bool:
    assert "error" not in result, result
    return result["initial_state"].endswith(": True")


@pytest.mark.unit
@pytest.mark.model_checking
class TestOATLErrorHandling:
    """Error handling when inputs are invalid or models lack cost data."""

    def test_oatl_without_cost_model(self, cgs_simple_parser):
        """Plain CGS models are rejected: OATL requires costCGS."""
        result = _core_oatl_checking(cgs_simple_parser, "<1><5>F p")
        assert "error" in result
        assert "costCGS" in result["error"]["message"]

    def test_oatl_invalid_formula_syntax(self, oatl_model):
        """Reject formulas with invalid syntax."""
        result = _core_oatl_checking(oatl_model, "<1>F p")
        assert "error" in result
        assert result["error"]["type"] == "syntax"

    def test_oatl_negative_cost_bound(self, oatl_model):
        """Reject formulas with a negative cost bound."""
        result = _core_oatl_checking(oatl_model, "<1><-5>F p")
        assert "error" in result

    def test_oatl_nonexistent_atomic_proposition(self, oatl_model):
        """Error when formula uses an atomic proposition not in the model."""
        result = _core_oatl_checking(oatl_model, "<1><5>F nonexistent")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_missing_cost_that_decides_the_result_is_an_error(self, temp_file):
        """B has no cost and must be erased for X p to hold, so the check fails and names it."""
        content = _one_agent_model(
            transitions=[["0", "A", "B"], ["0", "*", "0"], ["0", "0", "*"]],
            labelling=[["0"], ["1"], ["0"]],
            costs={"A": "s0$1"},
        )
        result = model_checking("<1><5>X p", temp_file(content))
        assert "error" in result
        assert "B at s0" in result["error"]["message"]
        assert "['s0']" in result["error"]["message"]

    def test_edge_only_model_refuses_a_partial_coalition(self, test_data_dir):
        """Transition_With_Costs has no actions, so agent 1's choices alone are undefined."""
        model_file = (
            test_data_dir / "costCGS" / "OL" / "ol_edge_costs_2agents_3states.txt"
        )
        error = model_checking("<1><2>X goal", str(model_file))["error"]
        assert error["type"] == "model"
        assert "Coalition <1> needs the agents' actions" in error["message"]

    def test_missing_cost_that_cannot_change_the_result_is_ignored(self, temp_file):
        """B (no cost) misses p at first, but s2 then reaches p, so nothing is erased."""
        content = _one_agent_model(
            transitions=[["0", "A", "B"], ["0", "*", "0"], ["0", "*", "0"]],
            labelling=[["0"], ["1"], ["0"]],
            costs={"A": "s0$1"},
        )
        assert _holds_initially(model_checking("<1><5>F p", temp_file(content)))


@pytest.mark.semantic
@pytest.mark.model_checking
class TestOATLSemantics:
    """What the Demon's budget allows and how each temporal operator uses it."""

    @pytest.mark.parametrize(
        "formula",
        [
            f"<1,2><{{n}}>G {ATTACK_NEVER_COMPLETED}",
            f"<1,2><{{n}}>false R {ATTACK_NEVER_COMPLETED}",
            f"<1,2><{{n}}>(false R {ATTACK_NEVER_COMPLETED})",
        ],
    )
    @pytest.mark.parametrize(
        "bound,expected_states,holds",
        [
            (2, {"s1", "s5"}, False),
            (3, {"s0", "s1", "s2", "s5"}, True),
        ],
    )
    def test_least_budget_that_blocks_the_attack_is_3(
        self, oatl_model, formula, bound, expected_states, holds
    ):
        """Blocking Alice and Bob from s0 needs a cost-3 erasure, so budget 2 fails."""
        result = model_checking(formula.format(n=bound), oatl_model.filename)
        assert extract_states_from_result(result) == expected_states
        assert _holds_initially(result) is holds

    @pytest.mark.parametrize("bound,holds", [(4, False), (5, True)])
    def test_demon_pays_the_sum_over_every_move_that_misses_the_target(
        self, temp_file, bound, holds
    ):
        """At s0, move A reaches p; B (cost 2) and C (cost 3) miss it and must both be erased."""
        content = _one_agent_model(
            transitions=[["0", "A", "B,C"], ["0", "*", "0"], ["0", "0", "*"]],
            labelling=[["0"], ["1"], ["0"]],
            costs={"A": "s0$1", "B": "s0$2", "C": "s0$3"},
        )
        result = model_checking(f"<1><{bound}>X p", temp_file(content))
        assert _holds_initially(result) is holds

    @pytest.mark.parametrize("b_cost,holds", [("1", False), ("0", True)])
    def test_budget_0_erases_only_zero_cost_moves(self, temp_file, b_cost, holds):
        """At s0, move A reaches p and B misses it; with budget 0, B can be erased only if free."""
        content = _one_agent_model(
            transitions=[["0", "A", "B"], ["0", "*", "0"], ["0", "0", "*"]],
            labelling=[["0"], ["1"], ["0"]],
            costs={"A": "s0$1", "B": f"s0${b_cost}"},
        )
        result = model_checking("<1><0>X p", temp_file(content))
        assert _holds_initially(result) is holds

    def test_agents_outside_the_coalition_side_with_the_demon(self, temp_file):
        """Agent 1's only move reaches p if agent 2 helps, so nothing is erased."""
        content = build_cgs_model_content(
            transitions=[["0", "AA", "AB"], ["0", "*", "0"], ["0", "0", "*"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["1"], ["0"]],
            num_agents=2,
            prop_names=["p"],
            costs_for_actions={"AA": "s0$5", "AB": "s0$5"},
        )
        assert _holds_initially(model_checking("<1><1>X p", temp_file(content)))

    @pytest.mark.parametrize(
        "formula,holds",
        [
            ("<1><1>p U q", False),
            ("<1><2>p U q", True),
            ("<1><1>p W q", True),
        ],
    )
    def test_until_must_reach_q_while_weak_until_may_stay_in_p(
        self, temp_file, formula, holds
    ):
        """At s0 (p), A loops back (cost 2) and B goes to q.

        U needs A erased (budget 2); W accepts looping in p forever.
        """
        content = _one_agent_model(
            transitions=[["A", "B"], ["0", "*"]],
            labelling=[["1", "0"], ["0", "1"]],
            costs={"A": "s0$2", "B": "s0$1"},
            prop_names=("p", "q"),
        )
        assert _holds_initially(model_checking(formula, temp_file(content))) is holds
