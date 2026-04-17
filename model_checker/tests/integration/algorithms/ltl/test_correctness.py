"""LTL model checking: linear path properties and Nash equilibrium APIs."""

import pytest

from model_checker.algorithms.explicit.LTL.LTL import (
    model_checking,
    model_checking_exists_nash,
    model_checking_is_not_nash,
    model_checking_lose_some_nash,
    model_checking_wins_some_nash,
)
from model_checker.algorithms.explicit.LTL.strategies import (
    generate_guarded_action_pairs,
    generate_strategies,
    initialize,
)
from model_checker.tests.helpers.model_helpers import generate_linear_chain


@pytest.mark.unit
@pytest.mark.model_checking
class TestLTLErrorHandling:
    """Test LTL error handling for invalid inputs."""

    def test_ltl_invalid_formula_syntax(self, cgs_simple_parser):
        """Test LTL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", cgs_simple_parser.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_ltl_nonexistent_atomic_proposition(self, cgs_simple_parser):
        """Test LTL with non-existent atomic proposition."""
        result = model_checking("F nonexistent", cgs_simple_parser.filename)
        assert "error" in result or "does not exist" in result.get("res", "").lower()


@pytest.mark.integration
@pytest.mark.model_checking
class TestLTLCorrectness:
    """Test LTL model checking correctness for temporal operators."""

    def test_ltl_eventually_reachable_proposition(self, ctl_small_model):
        """Test F operator for eventually reachable proposition."""
        result = model_checking("F q", ctl_small_model.filename)
        assert "error" not in result
        assert "res" in result and result["res"].startswith("Result: ")
        assert "initial_state" in result and "Initial state" in result["initial_state"]
        assert result["initial_state"].strip().endswith("True")

    def test_ltl_globally_violated_proposition(self, ctl_small_model):
        """Test G operator for a proposition that does not hold on all paths."""
        result = model_checking("G p", ctl_small_model.filename)
        assert "error" not in result
        assert "res" in result and result["res"].startswith("Result: ")
        assert "initial_state" in result and "Initial state" in result["initial_state"]
        assert result["initial_state"].strip().endswith("False")

    def test_ltl_eventually_goal_on_minimal_model(self, ltl_minimal_model):
        """Test F operator for eventually reaching goal on the minimal LTL model."""
        result = model_checking("F goal", ltl_minimal_model.filename)
        assert "error" not in result
        assert "res" in result and result["res"].startswith("Result: ")
        assert "initial_state" in result and "Initial state" in result["initial_state"]
        assert result["initial_state"].strip().endswith("True")


@pytest.mark.semantic
@pytest.mark.model_checking
class TestLTLSemantics:
    """LTL semantics on a small model with known labelling."""

    def test_ltl_semantics_linear_chain(self, temp_file):
        """F p, F q, G q on a 3-state chain: s0->s1->s2; p at s0,s2, q at s2."""
        content = generate_linear_chain(
            3, num_agents=2, prop_names=["p", "q"], action_label="AC"
        )
        path = temp_file(content)

        for formula, expected in [("F p", True), ("F q", True), ("G q", False)]:
            result = model_checking(formula, path)
            assert "error" not in result
            assert "res" in result and result["res"].startswith("Result: ")
            assert "initial_state" in result
            assert (
                result["initial_state"]
                .strip()
                .endswith("True" if expected else "False")
            )

    @pytest.mark.parametrize(
        "formula,expected_satisfied",
        [
            ("F q", True),
            ("G p", False),
            ("F p", True),
        ],
    )
    def test_ltl_semantics_ctl_fixture(
        self, ctl_small_model, formula, expected_satisfied
    ):
        """Table-driven LTL semantics on the shared CTL fixture (CGS compatible)."""
        result = model_checking(formula, ctl_small_model.filename)
        assert "error" not in result
        assert "res" in result and result["res"].startswith("Result: ")
        assert "initial_state" in result
        suffix = "True" if expected_satisfied else "False"
        assert result["initial_state"].strip().endswith(suffix)


@pytest.mark.integration
@pytest.mark.model_checking
class TestLTLCounterexample:
    """When the formula does not hold at the initial state, result is False."""

    def test_ltl_counterexample_globally_false(self, temp_file):
        """G q is false at s0 on a chain where q holds only at the last state."""
        content = generate_linear_chain(
            3, num_agents=2, prop_names=["p", "q"], action_label="AC"
        )
        path = temp_file(content)
        result = model_checking("G q", path)
        assert "error" not in result
        assert "res" in result and "initial_state" in result
        assert result["initial_state"].strip().endswith("False")

    def test_ltl_counterexample_eventually_false_on_minimal(self, ltl_minimal_model):
        """Formula that cannot be satisfied on the minimal model yields False or error."""
        result = model_checking("G goal", ltl_minimal_model.filename)
        assert "error" in result or (
            "initial_state" in result
            and result["initial_state"].strip().endswith("False")
        )


@pytest.mark.integration
@pytest.mark.model_checking
class TestLTLNashFunctions:
    """Basic tests for LTL Nash equilibrium API (exists_nash)."""

    def test_model_checking_exists_nash_returns_result_dict(self, ctl_small_model):
        """model_checking_exists_nash runs without crash and returns Satisfiability and Complexity Bound."""
        result = model_checking_exists_nash(
            ctl_small_model.filename,
            "F q",
            k=2,
            agents=[1],
        )
        assert isinstance(result, dict)
        assert "Satisfiability" in result
        assert "Complexity Bound" in result
        assert result["Satisfiability"] in (True, False)
        assert 1 <= result["Complexity Bound"] <= 2

    def test_model_checking_wins_some_nash_returns_result_dict(self, ctl_small_model):
        """model_checking_wins_some_nash runs without crash and returns Satisfiability."""
        (
            agent_actions,
            actions_list,
            atomic_propositions,
            CTLformula,
            agents,
            cgs,
            _,
        ) = initialize(ctl_small_model.filename, "F q", 2, [1])
        cartesian = generate_guarded_action_pairs(
            1, agent_actions, actions_list, atomic_propositions
        )
        strategies_gen = generate_strategies(cartesian, 1, agents, [False])
        current_strategy = next(strategies_gen, None)
        if current_strategy is None:
            pytest.skip("No strategy generated for this model")
        result = model_checking_wins_some_nash(
            cgs,
            ctl_small_model.filename,
            agents,
            CTLformula,
            current_strategy,
            bound=1,
            agent_actions=agent_actions,
            atomic_propositions=atomic_propositions,
            target_agent=1,
        )
        assert isinstance(result, dict)
        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)

    def test_model_checking_lose_some_nash_returns_result_dict(self, ctl_small_model):
        """model_checking_lose_some_nash runs without crash and returns Satisfiability."""
        (
            agent_actions,
            actions_list,
            atomic_propositions,
            CTLformula,
            agents,
            cgs,
            _,
        ) = initialize(ctl_small_model.filename, "F q", 2, [1])
        cartesian = generate_guarded_action_pairs(
            1, agent_actions, actions_list, atomic_propositions
        )
        strategies_gen = generate_strategies(cartesian, 1, agents, [False])
        current_strategy = next(strategies_gen, None)
        if current_strategy is None:
            pytest.skip("No strategy generated for this model")
        result = model_checking_lose_some_nash(
            cgs,
            ctl_small_model.filename,
            agents,
            CTLformula,
            current_strategy,
            bound=1,
            agent_actions=agent_actions,
            atomic_propositions=atomic_propositions,
            target_agent=1,
        )
        assert isinstance(result, dict)
        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)

    def test_model_checking_is_not_nash_returns_result_dict(self, ctl_small_model):
        """model_checking_is_not_nash runs without crash and returns Satisfiability when given a strategy."""
        (
            agent_actions,
            actions_list,
            atomic_propositions,
            _,
            agents,
            cgs,
            _,
        ) = initialize(ctl_small_model.filename, "F q", 2, [1])
        cartesian = generate_guarded_action_pairs(
            1, agent_actions, actions_list, atomic_propositions
        )
        strategies_gen = generate_strategies(cartesian, 1, agents, [False])
        natural_strategy = next(strategies_gen, None)
        if natural_strategy is None:
            pytest.skip("No strategy generated for this model")
        result = model_checking_is_not_nash(
            ctl_small_model.filename,
            cgs,
            "F q",
            k=2,
            natural_strategies=natural_strategy,
            selected_agents=agents,
        )
        assert isinstance(result, dict)
        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)
        assert "Complexity Bound" in result
