"""Tests for OATL model checking (cost-bounded coalition strategies)."""

import pytest

from model_checker.algorithms.explicit.OATL.OATL import (
    _core_oatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    generate_cost_cgs_linear_chain_content,
    load_costcgs_from_content,
)
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content


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
        result = model_checking("<1>F p", oatl_model.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_oatl_negative_cost_bound(self, oatl_model):
        """Reject formulas with a negative cost bound."""
        result = _core_oatl_checking(oatl_model, "<1><-5>F p")
        assert "error" in result

    def test_oatl_nonexistent_atomic_proposition(self, oatl_model):
        """Error when formula uses an atomic proposition not in the model."""
        result = _core_oatl_checking(oatl_model, "<1><5>F nonexistent")
        assert "error" in result or "does not exist" in result.get("res", "").lower()


@pytest.mark.semantic
@pytest.mark.model_checking
class TestOATLSemantics:
    """Semantics of cost-bounded eventually on small chains."""

    def test_oatl_eventually_with_sufficient_cost_bound(self, temp_file):
        """Coalition <1> can reach p within per-step cost 5 on a 3-state chain.

        Model: s0 -> s1 -> s2 (self-loop at s2); p holds at s0 and s2;
        each step has cost 1. Satisfying set is {s0, s1, s2}.
        """
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        result = _core_oatl_checking(cgs, "<1><5>F p")
        states = extract_states_from_result(result)

        assert states == {
            "s0",
            "s1",
            "s2",
        }, f"OATL <1><5>F p on 3-state chain (p at s0,s2): expected {{s0,s1,s2}}, got {states}"

    def test_oatl_eventually_with_tight_cost_bound(self, temp_file):
        """Per-step cost 5 on s0->s1 and 1 on s1->s2; p only at s2.

        Bound 1: only {s1,s2}. Bound 5: also s0.
        """
        content = build_cgs_model_content(
            transitions=[["0", "A", "0"], ["0", "0", "A"], ["0", "0", "*"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
            costs_for_actions={"A": ["s0$5;s1$1"], "*": ["s2$1"]},
        )
        cgs = load_costcgs_from_content(temp_file, content)

        tight = _core_oatl_checking(cgs, "<1><1>F p")
        loose = _core_oatl_checking(cgs, "<1><5>F p")
        assert extract_states_from_result(tight) == {"s1", "s2"}
        assert ": False" in tight.get("initial_state", "")
        assert extract_states_from_result(loose) == {"s0", "s1", "s2"}
        assert ": True" in loose.get("initial_state", "")

    def test_oatl_three_agent_coalition(self, oatl_model):
        """Coalition <1,2,3> F g excludes s1 on the medium OATL fixture."""
        result = model_checking("<1,2,3><10>F g", oatl_model.filename)
        assert "error" not in result
        assert extract_states_from_result(result) == {
            "s0",
            "s2",
            "s3",
            "s4",
            "s5",
        }
        assert ": True" in result.get("initial_state", "")
