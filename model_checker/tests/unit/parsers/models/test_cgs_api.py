"""CGS API: get_number_of_agents error handling, action extraction from transitions."""

import pytest

from model_checker.parsers.game_structures.cgs import cgs_actions
from model_checker.parsers.game_structures.cgs.cgs import CGS


@pytest.mark.unit
class TestCGSNumberOfAgents:
    """get_number_of_agents error cases."""

    def test_get_number_of_agents_error_cases(self):
        """Unset Number_of_agents raises ValueError on the API accessor."""
        parser = CGS()
        with pytest.raises(ValueError, match="Number_of_agents is missing"):
            parser.get_number_of_agents()


@pytest.mark.unit
class TestCGSActionExtraction:
    """Action extraction from transition matrix via cgs_actions."""

    def test_extract_actions_returns_dict(self, cgs_simple_parser):
        """extract_actions_for_agents returns dict of agent actions."""
        num_agents = cgs_simple_parser.get_number_of_agents()
        all_agents = list(range(1, num_agents + 1))
        cgs_actions.validate_agent_numbers(all_agents, num_agents)
        result = cgs_actions.extract_actions_for_agents(
            cgs_simple_parser.graph, all_agents
        )
        assert isinstance(result, dict)
        for _agent_key, agent_actions in result.items():
            assert "I" not in agent_actions

    def test_extract_actions_from_transitions(self, cgs_simple_parser):
        num_agents = cgs_simple_parser.get_number_of_agents()
        agents = list(range(1, num_agents + 1))
        cgs_actions.validate_agent_numbers(agents, num_agents)
        actions = cgs_actions.extract_actions_for_agents(
            cgs_simple_parser.graph, agents
        )
        for row in cgs_simple_parser.graph:
            for elem in row:
                if elem in (0, "*", "0", ""):
                    continue
                for tokens in cgs_actions.parse_joint_action_cell(
                    str(elem), num_agents
                ):
                    for agent_num in agents:
                        agent_index = agent_num - 1
                        token = tokens[agent_index]
                        if token in (
                            cgs_actions.CANONICAL_IDLE_TOKEN,
                            "I",
                            "*",
                        ):
                            continue
                        agent_key = f"agent{agent_num}"
                        assert token in actions[agent_key]
