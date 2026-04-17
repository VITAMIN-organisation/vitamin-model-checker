"""ATL semantics: coalition operators, expected state sets vs output."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import _core_atl_checking
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
    load_cgs_from_content,
)


@pytest.mark.semantic
@pytest.mark.model_checking
class TestATLCoalitionSemantics:
    """Test ATL coalition pre-image computation semantics."""

    def test_single_agent_can_force_next(self, temp_file):
        """Verify <1>X p when agent 1 can force next state to satisfy p."""
        content = build_cgs_model_content(
            transitions=[["0", "a", "0"], ["0", "I", "0"], ["0", "0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["1"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = _core_atl_checking(cgs, "<1>X p")
        states = extract_states_from_result(result)

        assert "s0" in states or "s1" in states

    def test_coalition_eventually_reachable(self, temp_file):
        """Verify <1>F p for eventually reachable proposition."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = _core_atl_checking(cgs, "<1>F p")
        states = extract_states_from_result(result)

        assert states == {"s0", "s1"}
