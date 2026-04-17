"""Complex formulas: deeply nested CTL modalities."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import _core_ctl_checking
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
    load_cgs_from_content,
)


@pytest.mark.integration
@pytest.mark.complex
class TestCTLComplexFormulas:
    """Test CTL with deeply nested operators."""

    def test_triple_nested_temporal_operators(self, temp_file):
        """Verify EF(AG(EX p)) with three levels of nesting."""
        content = build_cgs_model_content(
            transitions=[["I", "a"], ["a", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["1"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = _core_ctl_checking(cgs, "EF(AG(EX p))")
        states = extract_states_from_result(result)

        assert states is not None
        assert len(states) >= 1
