"""CTL model checking: total transitions, until operators, error handling."""

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


class TestCTLEUAuSemantics:
    """CTL EU and AU operators (explicit semantics tests)."""

    def test_eu_operator_exact_states(self, cgs_simple_parser):
        """E[p U q] on atl_2agents_4states_simple is {s0,s1,s3}."""
        result = _core_ctl_checking(cgs_simple_parser, "E[p U q]")
        assert "error" not in result
        assert extract_states_from_result(result) == {"s0", "s1", "s3"}

    def test_au_operator_exact_states(self, cgs_simple_parser):
        """A[p U q] on atl_2agents_4states_simple is {s1,s3}."""
        result = _core_ctl_checking(cgs_simple_parser, "A[p U q]")
        assert "error" not in result
        assert extract_states_from_result(result) == {"s1", "s3"}


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
