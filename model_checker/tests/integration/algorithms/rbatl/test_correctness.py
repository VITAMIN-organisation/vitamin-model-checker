"""RBATL model checking: dual coalitions, CTL-like operators, error cases."""

import pytest

from model_checker.algorithms.explicit.RBATL.RBATL import (
    _core_rbatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result


@pytest.mark.unit
@pytest.mark.model_checking
class TestRBATLErrorHandling:
    """Test RBATL error handling for invalid inputs."""

    def test_rbatl_invalid_formula_syntax(self, rbatl_model):
        """Test RBATL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", rbatl_model.filename)
        assert "error" in result

    def test_rbatl_nonexistent_atomic_proposition(self, rbatl_model):
        """Test RBATL with non-existent atomic proposition."""
        result = _core_rbatl_checking(rbatl_model, "<1><2>F nonexistent")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_rbatl_invalid_coalition(self, rbatl_model):
        """Test RBATL with invalid coalition (agent number out of range)."""
        # Agent 99 doesn't exist in 3-agent model
        result = _core_rbatl_checking(rbatl_model, "<99><1>EF p")
        # Should error for invalid coalition
        assert "error" in result

    def test_rbatl_missing_dual_coalition(self, rbatl_model):
        """Test RBATL with missing dual coalition (should require two coalitions)."""
        result = _core_rbatl_checking(rbatl_model, "<1>EF p")
        assert "error" in result


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRBATLSemantics:
    """Exact state-set semantics on fixture model."""

    def test_rbatl_exact_state_set(self, rbatl_model):
        """<1><2>F r: in s0 and s2 the others can keep the state, where r is false."""
        result = _core_rbatl_checking(rbatl_model, "<1><2>F r")
        assert "error" not in result
        assert "res" in result
        states = extract_states_from_result(result)
        assert states == {"s1", "s3", "s4"}
        init_str = result.get("initial_state", "")
        assert ": False" in init_str

    def test_rbatl_true_false_constants(self, rbatl_model):
        """Boolean constants must resolve via the formula parser, not as atoms."""
        true_result = _core_rbatl_checking(rbatl_model, "<1><2>F true")
        assert "error" not in true_result, true_result
        assert extract_states_from_result(true_result) == {
            "s0",
            "s1",
            "s2",
            "s3",
            "s4",
            "s5",
        }

        false_result = _core_rbatl_checking(rbatl_model, "<1><2>F false")
        assert "error" not in false_result, false_result
        assert extract_states_from_result(false_result) == set()


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRBATLResultSet:
    """`res` is the exact bounded state set, also when the initial state is False."""

    def test_bound_below_every_loop_cost_gives_empty_set(self, rbatl_model):
        """r holds at s1, s3, s4, whose only move is a loop of cost 2 (`*** s1$2:2`, `s3$2:2`, `s4$2:2`).

        With bound 1 no loop is affordable, so no state keeps G r and the set is empty.
        Plain ATL `<1>G r` would list s1, s3 and s4.
        """
        result = model_checking("<1><1>G r", rbatl_model.filename)
        assert "error" not in result
        assert extract_states_from_result(result) == set()
        assert ": False" in result["initial_state"]

    def test_invalid_bound_is_reported_when_atl_is_false(self, rbatl_model):
        """A bound above 1000000 is an error whatever plain ATL says."""
        result = model_checking("<1><1000001>G r", rbatl_model.filename)
        assert "Invalid bound value 1000001" in result["error"]["message"]


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRBATLZeroBound:
    """Bound 0 keeps only the moves that cost 0."""

    @pytest.mark.parametrize(
        ("formula", "expected"),
        [("<1><0>F p", {"s2"}), ("<1><0>G q", {"s0", "s1"})],
    )
    def test_only_free_moves(self, chain_model, formula, expected):
        """Only the cost-0 self-loops are left, so s0 and s1 stay where they are."""
        result = model_checking(formula, chain_model.filename)
        assert extract_states_from_result(result) == expected

    def test_rover_mission_formula_runs(self, rover_model):
        """The rover paper's mission formula nests <1><0,0>; no repair fits (5,1)."""
        formula = (
            "<1,2><5,1>F(oc && rm && <1><0,0>F((pl || pr) && <1><0,0>F(oc && rm)))"
        )
        result = model_checking(formula, rover_model.filename)
        assert extract_states_from_result(result) == {"s4", "s5", "s6", "s7", "s8"}


@pytest.mark.unit
@pytest.mark.model_checking
@pytest.mark.semantic
class TestRBATLCumulativeBound:
    """The bound limits the summed cost of the coalition's moves along the path."""

    @pytest.mark.parametrize(
        ("formula", "expected"),
        [
            ("<1><1>F p", {"s1", "s2"}),
            ("<1><2>F p", {"s0", "s1", "s2"}),
            ("<1><1>(q U p)", {"s1", "s2"}),
            ("<1><1>G q", {"s0", "s1"}),
        ],
    )
    def test_chain_steps_add_up(self, chain_model, formula, expected):
        """From s0 two steps of cost 1 reach p, so bound 1 only works from s1; s2 has p without q."""
        result = model_checking(formula, chain_model.filename)
        assert extract_states_from_result(result) == expected

    def test_too_many_budgets_is_an_error_naming_the_bound(self, chain_model):
        """Every budget up to the bound is solved, so a huge bound fails fast instead of hanging."""
        error = model_checking("<1><1000000>F p", chain_model.filename)["error"]
        assert error["type"] == "validation"
        assert "Bound [1000000] needs 1000001 budgets" in error["message"]

    @pytest.mark.parametrize("formula", ["<1,2><3,1,5>F p", "<1,2><3,1,5>X p"])
    def test_bound_longer_than_the_costs_is_an_error(self, sensor_model, formula):
        """The sensor model has two resources, so a third bound component is named."""
        error = model_checking(formula, sensor_model.filename)["error"]
        assert error["type"] == "validation"
        assert "[3, 1, 5]" in error["message"]

    def test_moves_without_cost_do_not_hide_the_resources(self, temp_file):
        """The only move of s0 has no cost, but the model has one resource, and p
        already holds at s0."""
        model = (
            "Transition\nA\nName_State\ns0\nInitial_State\ns0\n"
            "Costs_for_actions\nZ s0$1\nAtomic_propositions\np\nLabelling\n1\n"
            "Number_of_agents\n1\n"
        )
        result = model_checking("<1><0>F p", temp_file(model))
        assert extract_states_from_result(result) == {"s0"}

    def test_globally_is_larger_than_the_seeded_least_fixpoint(self, loop_model):
        """s holds: every path stays at s for free or pays 1 once on t -> u. The seed
        of the paper's least fixpoint is {t, u}, and no free move from s stays in it."""
        holds = model_checking("<1><1>G q", loop_model.filename)
        seed = model_checking("<1><1>X <1><0>G q", loop_model.filename)
        assert extract_states_from_result(holds) == {"s", "t", "u"}
        assert extract_states_from_result(seed) == {"t", "u"}

    @pytest.mark.parametrize(("bound", "holds"), [("3,1", True), ("2,1", False)])
    def test_sensor_example_needs_three_energy(self, sensor_model, bound, holds):
        """The cheapest way to s6 spends (2,0), (0,1) and (1,0): (3,1) in total."""
        result = model_checking(f"<1,2><{bound}>F p", sensor_model.filename)
        assert result["initial_state"] == f"Initial state s0: {holds}"
