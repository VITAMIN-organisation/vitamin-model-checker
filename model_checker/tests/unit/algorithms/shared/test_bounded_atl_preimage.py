"""Bounded ATL pre-image: coalition forcing must check all compatible destinations."""

import pytest

from model_checker.algorithms.explicit.shared.bounded_atl_preimage import (
    _action_forces_all_to_target,
    build_transition_cache,
    compute_pre_states,
)
from model_checker.parsers.game_structures.cgs import cgs_actions
from model_checker.tests.helpers.model_helpers import load_test_model


@pytest.mark.unit
class TestBoundedAtlActionForces:
    def test_coalition_action_rejected_when_compatible_escape_exists(self):
        formatted = cgs_actions.format_agents([1])
        # Dest 0 in target has A|-; dest 1 outside target also has A|-.
        coalition_moves_by_column = [
            frozenset({"A|-"}),
            frozenset({"A|-"}),
        ]
        assert (
            _action_forces_all_to_target(
                "A|B",
                formatted,
                2,
                coalition_moves_by_column,
                {0},
                None,
                False,
            )
            is False
        )

    def test_coalition_action_accepted_when_all_compatible_dests_in_target(self):
        formatted = cgs_actions.format_agents([1])
        coalition_moves_by_column = [
            frozenset({"A|-"}),
            frozenset({"B|-"}),
        ]
        assert (
            _action_forces_all_to_target(
                "A|B",
                formatted,
                2,
                coalition_moves_by_column,
                {0},
                None,
                False,
            )
            is True
        )

    def test_wildcard_rejected_when_compatible_escape_exists(self):
        formatted = cgs_actions.format_agents([1])
        coalition_moves_by_column = [
            frozenset({"*|-"}),
            frozenset({"*|-"}),
        ]
        assert (
            _action_forces_all_to_target(
                "*",
                formatted,
                2,
                coalition_moves_by_column,
                {0},
                None,
                False,
            )
            is False
        )


@pytest.mark.unit
@pytest.mark.model_checking
class TestBoundedAtlPreImageIntegration:
    def test_pre_excludes_state_when_same_coalition_move_escapes_target(
        self, test_data_dir
    ):
        cgs = load_test_model(
            test_data_dir, "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
        )
        trans_cache = build_transition_cache(cgs, "1")
        only_s1 = compute_pre_states(
            cgs, "1", {"s1"}, [100, 100, 100], trans_cache, "rbatl"
        )
        all_reachable = compute_pre_states(
            cgs, "1", {"s1", "s3"}, [100, 100, 100], trans_cache, "rbatl"
        )
        assert "s0" not in only_s1
        assert "s0" in all_reachable
