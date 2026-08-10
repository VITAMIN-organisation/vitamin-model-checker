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

    @pytest.mark.parametrize(
        "transitions",
        [
            [["0", "AC,BC", "AD,BD"], ["0", "II", "0"], ["0", "0", "II"]],
            [["0", "A|C,B|C", "A|D,B|D"], ["0", "I|I", "0"], ["0", "0", "I|I"]],
        ],
        ids=["compact", "explicit"],
    )
    def test_partial_coalition_next_matches_encoding(self, temp_file, transitions):
        """Agent 2 can force p next; agent 1 cannot; full coalition can.

        From s0, agent 2's choice of C vs D selects s1 (p) vs s2 (!p), while
        agent 1's A vs B does not determine the successor alone.
        """
        content = build_cgs_model_content(
            transitions=transitions,
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["1"], ["0"]],
            num_agents=2,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        agent1 = extract_states_from_result(_core_atl_checking(cgs, "<1>X p"))
        agent2 = extract_states_from_result(_core_atl_checking(cgs, "<2>X p"))
        full = extract_states_from_result(_core_atl_checking(cgs, "<1,2>X p"))

        assert "s0" not in agent1
        assert "s0" in agent2
        assert "s0" in full
