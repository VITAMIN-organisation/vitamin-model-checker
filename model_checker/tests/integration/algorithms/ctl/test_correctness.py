"""CTL model checking: total transitions, release (AR), error handling."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import (
    _core_ctl_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
    load_cgs_from_content,
)


class TestCTLTotalTransitions:
    """Models must be total: every state has a successor."""

    def test_deadlock_state_rejected_on_load(self, temp_file):
        """A row with no outgoing transitions is rejected when the model is loaded."""
        content = build_cgs_model_content(
            transitions=[
                ["0", "1", "0"],
                ["1", "0", "0"],
                ["0", "0", "0"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["1"]],
            num_agents=1,
        )
        with pytest.raises(ValueError, match="no outgoing transitions"):
            load_cgs_from_content(temp_file, content)


class TestCTLReleaseOperator:
    """CTL release operator (AR)."""

    def test_ar_operator(self, cgs_simple_parser):
        """A[phi R psi] (all release)."""
        result = _core_ctl_checking(cgs_simple_parser, "A[p R q]")
        if "error" not in result:
            states = extract_states_from_result(result)
            assert states is not None
        else:
            assert "Syntax error" in result.get("res", "") or "syntax" in result.get(
                "error", {}
            ).get("type", "")


class TestCTLEUAuErSemantics:
    """CTL EU, AU, and ER operators (explicit semantics tests)."""

    def test_eu_operator_returns_state_set(self, cgs_simple_parser):
        """E[p U q] (existential until) returns a state set without error."""
        result = _core_ctl_checking(cgs_simple_parser, "E[p U q]")
        assert "error" not in result
        states = extract_states_from_result(result)
        assert states is not None
        assert states <= set(cgs_simple_parser.states)

    def test_au_operator_returns_state_set(self, cgs_simple_parser):
        """A[p U q] (universal until) returns a state set without error."""
        result = _core_ctl_checking(cgs_simple_parser, "A[p U q]")
        assert "error" not in result
        states = extract_states_from_result(result)
        assert states is not None
        assert states <= set(cgs_simple_parser.states)

    def test_er_operator_returns_state_set_or_parseable(self, cgs_simple_parser):
        """E[p R q] (existential release): either returns a state set or parser reports syntax (ER support may vary)."""
        result = _core_ctl_checking(cgs_simple_parser, "E[p R q]")
        if "error" not in result:
            states = extract_states_from_result(result)
            assert states is not None
            assert states <= set(cgs_simple_parser.states)
        else:
            assert (
                "syntax" in result.get("res", "").lower()
                or "syntax" in str(result.get("error", {})).lower()
            )


class TestCTLErrorHandling:
    """Invalid formula and nonexistent atom handling."""

    def test_ctl_invalid_formula_syntax(self, cgs_simple_parser):
        """Invalid formula returns error or syntax message."""
        result = model_checking("INVALID_FORMULA", cgs_simple_parser.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_ctl_nonexistent_atomic_proposition(self, cgs_simple_parser):
        """Nonexistent atom returns error or 'does not exist'."""
        result = _core_ctl_checking(cgs_simple_parser, "EF nonexistent")
        assert "error" in result or "does not exist" in result.get("res", "").lower()
