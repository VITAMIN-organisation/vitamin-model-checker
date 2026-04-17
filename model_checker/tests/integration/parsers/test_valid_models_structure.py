"""Valid models: dimensions, state/atomic_prop/action operations (minimal set for coverage)."""

import pytest

from model_checker.tests.helpers.model_helpers import load_test_model

SINGLE_MODEL = "CGS/ATL/atl_2agents_4states_simple.txt"
COST_MODEL_FOR_ACTIONS = "costCGS/OL/ol_2agents_medium_6states_costs.txt"


def _assert_model_dimensions_consistent(parser):
    """Transition matrix square; labelling rows/cols match states and propositions."""
    num_states = len(parser.states)
    num_props = len(parser.atomic_propositions)
    if len(parser.graph) != num_states:
        raise AssertionError(
            f"Transition matrix has {len(parser.graph)} rows, expected {num_states}"
        )
    bad_row = next(
        (i for i, row in enumerate(parser.graph) if len(row) != num_states), None
    )
    if bad_row is not None:
        raise AssertionError(
            f"Transition matrix row {bad_row} has {len(parser.graph[bad_row])} columns, "
            f"expected {num_states}"
        )
    if len(parser.matrix_prop) != num_states:
        raise AssertionError(
            f"Labelling matrix has {len(parser.matrix_prop)} rows, expected {num_states}"
        )
    bad_prop_row = next(
        (i for i, row in enumerate(parser.matrix_prop) if len(row) != num_props),
        None,
    )
    if bad_prop_row is not None:
        raise AssertionError(
            f"Labelling matrix row {bad_prop_row} has {len(parser.matrix_prop[bad_prop_row])} columns, "
            f"expected {num_props}"
        )


@pytest.mark.integration
@pytest.mark.all_models
class TestAllValidModelsDimensionalConsistency:
    """Test dimensional consistency on a representative set of models."""

    def test_matrix_dimensions(self, cgs_simple_parser):
        """Transition and labelling dimensions are consistent with states and propositions."""
        _assert_model_dimensions_consistent(cgs_simple_parser)

    def test_action_string_lengths_match_agents(self, cost_ol_model):
        """Action strings in transition matrix match number of agents (costCGS sample)."""
        num_agents = cost_ol_model.get_number_of_agents()
        for _row_idx, row in enumerate(cost_ol_model.graph):
            for _col_idx, elem in enumerate(row):
                if elem != 0 and elem != "*":
                    for action in str(elem).split(","):
                        assert len(action) == num_agents


@pytest.mark.integration
@pytest.mark.all_models
class TestAllValidModelsStateOperations:
    """Test state-related operations on a representative set of models."""

    @pytest.mark.parametrize("model_path", [SINGLE_MODEL])
    def test_state_index_and_name_consistency(self, test_data_dir, model_path):
        """Test that state index and name accessors maintain consistency for all models."""
        parser = load_test_model(test_data_dir, model_path)

        for state in parser.states:
            state_idx = parser.get_index_by_state_name(state)
            assert state_idx >= 0, f"State '{state}' not found in state list"
            assert state_idx < len(
                parser.states
            ), f"State index {state_idx} out of range for state '{state}'"

            retrieved_state = parser.get_state_name_by_index(state_idx)
            assert retrieved_state == state, (
                f"State name mismatch: expected '{state}', "
                f"got '{retrieved_state}' at index {state_idx}"
            )


@pytest.mark.integration
@pytest.mark.all_models
class TestAllValidModelsAtomicPropositionOperations:
    """Test atomic proposition operations on a representative set of models."""

    @pytest.mark.parametrize("model_path", [SINGLE_MODEL])
    def test_atomic_proposition_index_consistency(self, test_data_dir, model_path):
        """Test that atomic proposition index accessors maintain consistency for all models."""
        parser = load_test_model(test_data_dir, model_path)

        if len(parser.atomic_propositions) > 0:
            for prop in parser.atomic_propositions:
                prop_index = parser.get_atom_index(prop)
                assert (
                    prop_index is not None
                ), f"Atomic proposition '{prop}' not found in atomic propositions list"
                assert 0 <= prop_index < len(parser.atomic_propositions), (
                    f"Atomic proposition index {prop_index} out of range "
                    f"for '{prop}'"
                )
                assert parser.atomic_propositions[prop_index] == prop, (
                    f"Atomic proposition mismatch: expected '{prop}', "
                    f"got '{parser.atomic_propositions[prop_index]}' at index {prop_index}"
                )


@pytest.mark.integration
@pytest.mark.all_models
class TestAllValidModelsActionOperations:
    """Test action-related operations on a representative set of models."""

    @pytest.mark.parametrize("model_path", [SINGLE_MODEL])
    def test_get_actions_returns_valid_structure(self, test_data_dir, model_path):
        """Test that get_actions() returns valid structure for all models."""
        parser = load_test_model(test_data_dir, model_path)

        num_agents = parser.get_number_of_agents()
        agents = list(range(1, num_agents + 1))
        actions = parser.get_actions(agents)

        assert isinstance(
            actions, dict
        ), f"get_actions() should return dict, got {type(actions)}"
        assert (
            len(actions) == num_agents
        ), f"get_actions() returned {len(actions)} agents, expected {num_agents}"

        for agent_num in agents:
            agent_key = f"agent{agent_num}"
            assert (
                agent_key in actions
            ), f"Agent {agent_num} missing from actions dictionary"
            assert isinstance(
                actions[agent_key], list
            ), f"Actions for {agent_key} should be list, got {type(actions[agent_key])}"
