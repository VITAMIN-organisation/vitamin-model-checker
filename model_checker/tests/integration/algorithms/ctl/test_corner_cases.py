"""Corner cases: single-state model with self-loop."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import _core_ctl_checking
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
    load_cgs_from_content,
)


@pytest.mark.integration
@pytest.mark.edge_case
class TestSingleStateModels:
    """Test model checking on single-state models."""

    def test_ctl_single_state_self_loop(self, temp_file):
        """Verify CTL operators on single state with self-loop."""
        content = build_cgs_model_content(
            transitions=[["I"]],
            state_names=["s0"],
            initial_state="s0",
            labelling=[["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result_ef = _core_ctl_checking(cgs, "EF p")
        result_eg = _core_ctl_checking(cgs, "EG p")
        result_af = _core_ctl_checking(cgs, "AF p")
        result_ag = _core_ctl_checking(cgs, "AG p")
        states_ef = extract_states_from_result(result_ef)
        states_eg = extract_states_from_result(result_eg)
        states_af = extract_states_from_result(result_af)
        states_ag = extract_states_from_result(result_ag)

        assert states_ef == {"s0"}
        assert states_eg == {"s0"}
        assert states_af == {"s0"}
        assert states_ag == {"s0"}
