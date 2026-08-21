"""OATL pre-image: pre_indices for one-step predecessors and cost scalarization."""

import pytest

from model_checker.algorithms.explicit.OATL.OATL import _core_oatl_checking
from model_checker.algorithms.explicit.OATL.preimage import (
    _get_cached_cost,
)
from model_checker.algorithms.explicit.shared.cost_utils import cost_to_scalar
from model_checker.algorithms.explicit.shared.oatl_index_preimage import (
    build_pre_by_index,
    pre_indices,
)
from model_checker.algorithms.explicit.shared.state_utils import state_names_to_indices
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
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


@pytest.mark.unit
@pytest.mark.model_checking
class TestOATLCostScalar:
    """Flat multi-resource costs are summed for the scalar affordability check."""

    def test_flat_vector_cost_is_summed_like_shared_helper(self):
        assert cost_to_scalar([1, 2, 3]) == 6.0
        assert cost_to_scalar([[1, 2, 3]]) == 6.0

    def test_next_rejects_when_summed_vector_exceeds_bound(self, temp_file):
        """Cost [1, 100] is 101, so bound 5 cannot afford the step to p."""
        content = build_cgs_model_content(
            transitions=[["0", "A"], ["0", "*"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            prop_names=["p"],
            num_agents=1,
            costs_for_actions={"A": "s0$1:100", "*": "s1$0:0"},
        )
        cgs = load_costcgs_from_content(temp_file, content)
        if hasattr(cgs, "_oatl_cost_cache"):
            cgs._oatl_cost_cache.clear()

        raw = cgs.get_cost_for_action("A", "s0")
        assert raw == [1, 100]
        assert _get_cached_cost(cgs, "A", "s0") == 101.0

        states = extract_states_from_result(_core_oatl_checking(cgs, "<1><5>X p"))
        assert "s0" not in states
        assert "s1" in states
