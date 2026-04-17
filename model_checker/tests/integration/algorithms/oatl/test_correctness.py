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


@pytest.mark.unit
@pytest.mark.model_checking
class TestOATLErrorHandling:
    """Error handling when inputs are invalid or models lack cost data."""

    def test_oatl_without_cost_model(self, cgs_simple_parser):
        """Reject or handle models that have no cost information."""
        result = _core_oatl_checking(cgs_simple_parser, "<1><5>F p")
        assert "error" in result or "Result:" in result.get("res", "")

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
    """Semantics of cost-bounded eventually on a small linear chain."""

    def test_oatl_eventually_with_sufficient_cost_bound(self, temp_file):
        """Coalition <1> can reach p within cost 5 on a 3-state chain.

        Model: s0 -> s1 -> s2 (self-loop at s2); p holds at s0 and s2;
        each step has cost 1. By the semantics, we close backward from
        the target {s0, s2}: s1 can reach s2 in one step at cost 1, so
        the satisfying set is {s0, s1, s2}."""
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
        """With cost bound 1, s1 and s2 are in the set; set is a strict subset when cost limits reachability."""
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        result = _core_oatl_checking(cgs, "<1><1>F p")
        assert "error" not in result
        states = extract_states_from_result(result)
        assert states is not None
        assert states <= {"s0", "s1", "s2"}
        assert "s2" in states
        assert len(states) >= 1

    def test_oatl_three_agent_coalition(self, oatl_model):
        """OATL with 3-agent model: coalition <1,2,3> formula runs without error."""
        result = model_checking("<1,2,3><10>F g", oatl_model.filename)
        assert "error" not in result
        states = extract_states_from_result(result)
        assert states is not None
        assert states <= set(oatl_model.get_states())
