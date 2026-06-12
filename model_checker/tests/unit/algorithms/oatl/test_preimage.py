"""OATL pre-image: pre_indices for one-step predecessors."""

import pytest

from model_checker.algorithms.explicit.shared.oatl_index_preimage import (
    build_pre_by_index,
    pre_indices,
)
from model_checker.algorithms.explicit.shared.state_utils import state_names_to_indices
from model_checker.tests.helpers.model_helpers import (
    generate_cost_cgs_linear_chain_content,
    load_costcgs_from_content,
)


@pytest.mark.unit
@pytest.mark.model_checking
class TestOATLPreImage:
    """Test OATL pre_indices (one-step predecessor set)."""

    def test_get_pre_image_linear_chain(self, temp_file):
        """On s0->s1->s2 chain, pre-image of {s1} is {s0}; of {s2} contains s1 and s2."""
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        solve_context = {
            "graph": cgs.graph,
            "pre_by_index": build_pre_by_index(cgs.graph),
        }

        target_indices_s1 = state_names_to_indices(cgs, {"s1"})
        result_s1 = {
            str(cgs.get_state_name_by_index(idx))
            for idx in pre_indices(target_indices_s1, solve_context["pre_by_index"])
        }
        assert result_s1 == {"s0"}

        target_indices_s2 = state_names_to_indices(cgs, {"s2"})
        result_s2 = {
            str(cgs.get_state_name_by_index(idx))
            for idx in pre_indices(target_indices_s2, solve_context["pre_by_index"])
        }
        assert "s1" in result_s2
        assert "s2" in result_s2
        assert result_s2 <= {"s0", "s1", "s2"}
