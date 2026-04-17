"""Unit tests for shared state_utils (state_names_to_indices, state_indices_to_names)."""

import pytest

from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


@pytest.mark.unit
class TestStateNamesToIndices:
    """Test state_names_to_indices with valid and invalid state names."""

    def test_unknown_state_name_skipped_no_crash(self, temp_file):
        """Unknown state names are skipped; valid names are converted; no exception."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = state_names_to_indices(cgs, ["s0", "nonexistent_xyz", "s1"])

        assert isinstance(result, set)
        assert all(isinstance(i, int) for i in result)
        assert result == {0, 1}

    def test_all_unknown_state_names_returns_empty_set(self, temp_file):
        """When all names are unknown, returns empty set without raising."""
        content = build_cgs_model_content(
            transitions=[["0", "I"]],
            state_names=["s0"],
            initial_state="s0",
            labelling=[["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = state_names_to_indices(cgs, ["unknown_a", "unknown_b"])

        assert result == set()

    def test_empty_iterable_returns_empty_set(self, temp_file):
        """Empty iterable returns empty set."""
        content = build_cgs_model_content(
            transitions=[["0", "I"]],
            state_names=["s0"],
            initial_state="s0",
            labelling=[["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = state_names_to_indices(cgs, [])

        assert result == set()


@pytest.mark.unit
class TestStateIndicesToNames:
    """Test state_indices_to_names with valid and invalid indices."""

    def test_invalid_index_skipped_no_crash(self, temp_file):
        """Out-of-range indices are skipped; valid indices are converted; no exception."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = state_indices_to_names(cgs, [0, 99, 1])

        assert isinstance(result, set)
        assert all(isinstance(s, str) for s in result)
        assert result == {"s0", "s1"}
