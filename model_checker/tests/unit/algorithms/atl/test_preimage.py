"""ATL coalition pre-image: pre() for one-step forcing."""

import pytest

from model_checker.algorithms.explicit.ATL.preimage import pre
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


@pytest.mark.unit
@pytest.mark.model_checking
class TestATLPreImage:
    """Test ATL coalition pre-image function pre()."""

    def test_pre_single_agent_force_next(self, temp_file):
        """Pre_A({s1}) on a 2-state chain where from s0 only successor is s1; from s1 self-loop."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = pre(cgs, "1", {"s1"})
        assert result == {"s0", "s1"}, (
            f"From s0 coalition 1 can force s1; from s1 can stay in s1. "
            f"Expected {{s0, s1}}, got {result}"
        )

    def test_pre_target_subset_of_states(self, cgs_simple_parser):
        """pre() returns a subset of model states and includes target states that self-loop."""
        result = pre(cgs_simple_parser, "1", {"s3"})
        assert isinstance(result, set)
        assert all(isinstance(s, str) for s in result)
        assert result <= cgs_simple_parser.all_states_set
        assert "s3" in result
