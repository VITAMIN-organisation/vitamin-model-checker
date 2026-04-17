"""CGS API: get_number_of_agents error handling, get_actions validation and extraction."""

import pytest

from model_checker.tests.helpers.model_helpers import load_test_model


@pytest.mark.unit
class TestCGSNumberOfAgents:
    """get_number_of_agents error cases."""

    def test_get_number_of_agents_error_cases(self, test_data_dir):
        """Missing Number_of_agents section raises ValueError."""
        parser = load_test_model(test_data_dir, "invalid/missing_number_of_agents.txt")
        with pytest.raises(ValueError, match="Number_of_agents is missing"):
            parser.get_number_of_agents()


@pytest.mark.unit
class TestCGSGetActions:
    """get_actions validation and extraction from transitions."""

    def test_get_actions_validation(self, cgs_simple_parser):
        """get_actions returns dict of agent actions; no invalid-id branch exercised here."""
        num_agents = cgs_simple_parser.get_number_of_agents()
        all_agents = list(range(1, num_agents + 1))
        result = cgs_simple_parser.get_actions(all_agents)
        assert isinstance(result, dict)
        for _agent_key, agent_actions in result.items():
            assert "I" not in agent_actions

    def test_get_actions_extracts_from_transitions(self, cgs_simple_parser):
        num_agents = cgs_simple_parser.get_number_of_agents()
        agents = list(range(1, num_agents + 1))
        actions = cgs_simple_parser.get_actions(agents)
        all_action_strings = set()
        for row in cgs_simple_parser.graph:
            for elem in row:
                if elem != 0 and elem != "*":
                    for action in str(elem).split(","):
                        all_action_strings.add(action)
        for action_string in all_action_strings:
            for agent_num in agents:
                agent_index = agent_num - 1
                if (
                    agent_index < len(action_string)
                    and action_string[agent_index] != "I"
                ):
                    agent_key = f"agent{agent_num}"
                    expected_action = action_string[agent_index]
                    assert expected_action in actions[agent_key]
