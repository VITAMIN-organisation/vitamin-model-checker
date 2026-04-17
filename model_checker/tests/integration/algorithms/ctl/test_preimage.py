"""CTL pre-image: pre_image_exist, predecessor states."""

import pytest

from model_checker.algorithms.explicit.CTL.preimage import pre_image_exist


@pytest.mark.unit
@pytest.mark.model_checking
class TestCTLPreImageFunctions:
    """Test pre-image functions for correctness."""

    def test_pre_image_exist_simple_model(self, cgs_simple_parser):
        """Predecessors of s3 in simple model."""
        edges = cgs_simple_parser.get_edges()
        target = {"s3"}
        expected = {"s1", "s2", "s3"}
        predecessors = pre_image_exist(edges, target)
        assert (
            predecessors == expected
        ), f"pre_image_exist({target}) should return {expected} but got {predecessors}"
