"""CapATL model checking: capacity constraints, error cases."""

import pytest

from model_checker.algorithms.explicit.CapATL.CapATL import (
    _core_capatl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result
from model_checker.tests.integration.algorithms import capatl


@pytest.mark.unit
@pytest.mark.model_checking
class TestCapATLErrorHandling:
    """Test CapATL error handling for invalid inputs."""

    def test_capatl_invalid_formula_syntax(self, capatl_model):
        """Test CapATL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", capatl_model.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_capatl_nonexistent_atomic_proposition(self, capatl_model):
        """Test CapATL with non-existent atomic proposition."""
        result = _core_capatl_checking(capatl_model, "<{1,2}>F nonexistent")
        assert "error" in result or "does not exist" in result.get("res", "").lower()

    def test_capatl_invalid_coalition(self, capatl_model):
        """Test CapATL with invalid coalition (agent number out of range)."""
        result = _core_capatl_checking(capatl_model, "<{99}>F p")
        assert "error" in result

    def test_capatl_legacy_numeric_bound_rejected(self, capatl_model):
        """NatATL-style <{A}, k> is rejected; CapATL has no formula bound k."""
        result = _core_capatl_checking(capatl_model, "<{1,2},5>F p")
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_capatl_empty_coalition_rejected(self, capatl_model):
        """Empty coalition modality is invalid."""
        result = _core_capatl_checking(capatl_model, "<>F p")
        assert "error" in result or "Syntax error" in result.get("res", "")


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestCapATLSemantics:
    """Exact winning states on the 3-agent capacity fixture."""

    def test_capatl_eventually_winning_states(self, capatl_model):
        """Agent 1 can force g from every state (q0 via B**, q1 via q0, q2 already)."""
        result = _core_capatl_checking(capatl_model, "<{1}>F g")
        assert "error" not in result
        assert extract_states_from_result(result) == {"q0", "q1", "q2"}
        assert ": True" in result.get("initial_state", "")

    def test_capatl_next_winning_states(self, capatl_model):
        """X g holds at q0 (B** to q2) and at q2 (self-loop), not at q1."""
        result = _core_capatl_checking(capatl_model, "<{1}>X g")
        assert "error" not in result
        assert extract_states_from_result(result) == {"q0", "q2"}
        assert ": True" in result.get("initial_state", "")

    def test_capatl_globally_only_goal(self, capatl_model):
        """G g holds only where g already holds (q2)."""
        result = _core_capatl_checking(capatl_model, "<{1}>G g")
        assert "error" not in result
        assert extract_states_from_result(result) == {"q2"}
        assert ": False" in result.get("initial_state", "")

    def test_capatl_release_matches_globally_for_false_left(self, capatl_model):
        """false R phi is the dual of G phi; results should agree on the example model"""
        globally_result = _core_capatl_checking(capatl_model, "<{1}>G g")
        release_result = _core_capatl_checking(capatl_model, "<{1}>false R g")
        assert "error" not in globally_result
        assert "error" not in release_result
        assert extract_states_from_result(
            globally_result
        ) == extract_states_from_result(release_result)

    def test_capatl_synthetic_linear_chain(self, temp_file):
        """<{1}>F p holds in every state of a 4-state synthetic capCGS chain."""
        from model_checker.tests.helpers.synthetic_models import (
            generate_capcgs_linear_chain_model,
        )

        content = generate_capcgs_linear_chain_model(
            num_states=4, num_agents=2, prop_names=["p"]
        )
        model_path = temp_file(content)
        result = model_checking("<{1}>F p", model_path)
        assert "error" not in result, result
        assert extract_states_from_result(result) == {"s0", "s1", "s2", "s3"}
        assert ": True" in result.get("initial_state", "")
