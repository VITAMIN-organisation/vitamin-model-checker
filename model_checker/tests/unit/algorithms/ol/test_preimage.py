"""OL pre-image: build_pre_set_array, get_pre_image, triangle_down."""

import pytest

from model_checker.algorithms.explicit.OL.preimage import (
    build_pre_set_array,
    get_pre_image,
    triangle_down,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.tests.helpers.model_helpers import (
    generate_cost_cgs_linear_chain_content,
    load_costcgs_from_content,
)


@pytest.mark.unit
@pytest.mark.model_checking
class TestOLPreImage:
    """Test OL pre-image helpers."""

    def test_build_pre_set_array_and_get_pre_image(self, temp_file):
        """On 3-state chain s0->s1->s2, predecessors of s1 are {s0}; of s2 are {s1, s2}."""
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        pre_sets = build_pre_set_array(cgs)
        assert len(pre_sets) == 3

        s1_idx = list(state_names_to_indices(cgs, {"s1"}))[0]
        pre_of_s1 = get_pre_image(pre_sets, {s1_idx})
        assert 0 in pre_of_s1

        s2_idx = list(state_names_to_indices(cgs, {"s2"}))[0]
        pre_of_s2 = get_pre_image(pre_sets, {s2_idx})
        assert 1 in pre_of_s2
        assert 2 in pre_of_s2

    def test_triangle_down_returns_state_set(self, temp_file):
        """triangle_down returns a set of state names within cost bound."""
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)
        pre_sets = build_pre_set_array(cgs)

        result = triangle_down(
            cgs, cost_bound=5, target_states={"s2"}, pre_sets=pre_sets
        )
        assert isinstance(result, set)
        assert result <= {"s0", "s1", "s2"}
        assert "s2" in result
