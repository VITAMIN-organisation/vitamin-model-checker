"""ATL core: pre-image cache, least/greatest fixpoint, convergence."""

import pytest

from model_checker.algorithms.explicit.ATL.preimage import (
    build_transition_cache,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)


@pytest.mark.unit
@pytest.mark.atl
class TestATLFixpoint:
    """Test ATL fixpoint computation for temporal operators."""

    @pytest.mark.parametrize(
        "fixpoint_type,initial_set,update_func,expected_condition",
        [
            ("least", {"s1", "s2"}, lambda s: s | {"s0"}, "subset"),
            ("least", {"s1"}, lambda s: s, "equal"),
            ("greatest", {"s0", "s1"}, lambda s: s, "equal"),
        ],
    )
    def test_fixpoint_computation(
        self, fixpoint_type, initial_set, update_func, expected_condition
    ):
        """Test fixpoint computation for temporal operators."""
        if fixpoint_type == "least":
            result = least_fixpoint(initial_set, update_func)
        else:
            result = greatest_fixpoint(initial_set, update_func)

        assert isinstance(result, set)
        if expected_condition == "subset":
            assert initial_set.issubset(result)
        elif expected_condition == "equal":
            assert result == initial_set


@pytest.mark.unit
@pytest.mark.atl
class TestATLTransitionCache:
    """Test ATL transition cache building."""

    @pytest.mark.parametrize(
        "coalition,check_tuple_structure",
        [
            (None, False),
            ("1", True),
        ],
    )
    def test_build_transition_cache(
        self, cgs_simple_parser, coalition, check_tuple_structure
    ):
        """Test transition cache building with and without coalition."""
        if coalition is not None:
            cache = build_transition_cache(cgs_simple_parser, coalition=coalition)
        else:
            cache = build_transition_cache(cgs_simple_parser)

        assert isinstance(cache, dict)
        assert len(cache) == len(cgs_simple_parser.states)
        for state_idx in range(len(cgs_simple_parser.states)):
            assert state_idx in cache
            moves = cache[state_idx]
            assert isinstance(moves, list)
            if check_tuple_structure and moves:
                assert isinstance(moves[0], tuple)
                assert len(moves[0]) == 3
