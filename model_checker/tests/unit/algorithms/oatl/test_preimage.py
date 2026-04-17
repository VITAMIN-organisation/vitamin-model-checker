"""OATL pre-image: get_pre_image for one-step predecessors."""

import pytest

from model_checker.algorithms.explicit.OATL.preimage import get_pre_image
from model_checker.tests.helpers.model_helpers import (
    generate_cost_cgs_linear_chain_content,
    load_costcgs_from_content,
)


@pytest.mark.unit
@pytest.mark.model_checking
class TestOATLPreImage:
    """Test OATL get_pre_image (one-step predecessor set)."""

    def test_get_pre_image_linear_chain(self, temp_file):
        """On s0->s1->s2 chain, pre-image of {s1} is {s0}; of {s2} contains s1 and s2."""
        content = generate_cost_cgs_linear_chain_content(num_states=3, num_agents=1)
        cgs = load_costcgs_from_content(temp_file, content)

        result_s1 = get_pre_image(cgs, {"s1"})
        assert result_s1 == {"s0"}

        result_s2 = get_pre_image(cgs, {"s2"})
        assert "s1" in result_s2
        assert "s2" in result_s2
        assert result_s2 <= {"s0", "s1", "s2"}
