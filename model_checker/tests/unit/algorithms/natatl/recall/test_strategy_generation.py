"""NatATL Recall: strategy generation."""

from model_checker.algorithms.explicit.NatATL.Recall.strategy_generation import (
    generate_guarded_action_pairs,
    generate_strategies,
    is_duplicate,
)


class TestGenerateStrategies:
    """Test generate_strategies function."""

    def test_generate_single_agent_strategy(self):
        """Verify strategy generation for single agent."""
        cartesian_products = {"actions_agent1": [("p", "a"), ("q", "b")]}
        agents = [1]
        found_solution = False

        strategies = list(
            generate_strategies(cartesian_products, 1, agents, found_solution)
        )

        assert len(strategies) > 0
        assert all(isinstance(s, list) for s in strategies)

    def test_generate_multi_agent_strategies(self):
        """Verify strategy generation for multiple agents."""
        cartesian_products = {
            "actions_agent1": [("p", "a"), ("q", "b")],
            "actions_agent2": [("p", "c"), ("q", "d")],
        }
        agents = [1, 2]
        found_solution = False

        strategies = list(
            generate_strategies(cartesian_products, 1, agents, found_solution)
        )

        assert len(strategies) > 0
        for strategy in strategies:
            assert len(strategy) == 2

    def test_generate_respects_complexity_bound(self):
        """Verify strategy generation respects complexity bound."""
        cartesian_products = {"actions_agent1": [("p", "a"), ("q", "b"), ("r", "c")]}
        agents = [1]
        found_solution = False

        strategies_k1 = list(
            generate_strategies(cartesian_products, 1, agents, found_solution)
        )
        strategies_k2 = list(
            generate_strategies(cartesian_products, 2, agents, found_solution)
        )

        assert len(strategies_k2) >= len(strategies_k1)

    def test_generate_stops_when_solution_found(self):
        """Verify generation stops when solution is found."""
        cartesian_products = {"actions_agent1": [("p", "a"), ("q", "b")]}
        agents = [1]
        found_solution = True

        result = generate_strategies(cartesian_products, 1, agents, found_solution)

        assert result is None

    def test_generate_filters_duplicate_actions(self):
        """Verify strategies have unique actions per complexity level."""
        cartesian_products = {"actions_agent1": [("p", "a"), ("q", "a"), ("r", "b")]}
        agents = [1]
        found_solution = False

        strategies = list(
            generate_strategies(cartesian_products, 2, agents, found_solution)
        )

        for strategy in strategies:
            if strategy:
                pairs = strategy[0].get("condition_action_pairs", [])
                if len(pairs) > 1:
                    actions = [action for _, action in pairs]
                    assert len(actions) == len(set(actions))


class TestIsDuplicate:
    """Test is_duplicate function."""

    def test_detects_exact_duplicate(self):
        """Verify duplicate detection for identical strategies."""
        existing = [{"condition_action_pairs": [("p", "a"), ("q", "b")]}]
        new_strategy = {"condition_action_pairs": [("p", "a"), ("q", "b")]}

        assert is_duplicate(existing, new_strategy) is True

    def test_no_duplicate_for_different_strategy(self):
        """Verify no duplicate for different strategies."""
        existing = [{"condition_action_pairs": [("p", "a"), ("q", "b")]}]
        new_strategy = {"condition_action_pairs": [("p", "c"), ("q", "d")]}

        assert is_duplicate(existing, new_strategy) is False

    def test_no_duplicate_for_empty_list(self):
        """Verify no duplicate when existing list is empty."""
        existing = []
        new_strategy = {"condition_action_pairs": [("p", "a")]}

        assert is_duplicate(existing, new_strategy) is False

    def test_detects_duplicate_among_multiple(self):
        """Verify duplicate detection in list with multiple strategies."""
        existing = [
            {"condition_action_pairs": [("p", "a")]},
            {"condition_action_pairs": [("q", "b")]},
            {"condition_action_pairs": [("r", "c")]},
        ]
        new_strategy = {"condition_action_pairs": [("q", "b")]}

        assert is_duplicate(existing, new_strategy) is True

    def test_order_matters_in_duplicate_detection(self):
        """Verify duplicate detection considers pair order."""
        existing = [{"condition_action_pairs": [("p", "a"), ("q", "b")]}]
        new_strategy = {"condition_action_pairs": [("q", "b"), ("p", "a")]}

        assert is_duplicate(existing, new_strategy) is False


class TestGenerateGuardedActionPairs:
    """Test generate_guarded_action_pairs function."""

    def test_generate_single_agent_pairs(self):
        """Verify cartesian product for single agent."""
        regex_list = ["p", "q"]
        agent_actions = [["a", "b"]]

        result = generate_guarded_action_pairs(regex_list, agent_actions)

        assert "actions_agent1" in result
        assert len(result["actions_agent1"]) == 4
        assert ("p", "a") in result["actions_agent1"]
        assert ("p", "b") in result["actions_agent1"]
        assert ("q", "a") in result["actions_agent1"]
        assert ("q", "b") in result["actions_agent1"]

    def test_generate_multi_agent_pairs(self):
        """Verify cartesian product for multiple agents."""
        regex_list = ["p", "q"]
        agent_actions = [["a", "b"], ["c", "d"]]

        result = generate_guarded_action_pairs(regex_list, agent_actions)

        assert "actions_agent1" in result
        assert "actions_agent2" in result
        assert len(result["actions_agent1"]) == 4
        assert len(result["actions_agent2"]) == 4

    def test_generate_empty_regex_list(self):
        """Verify behavior with empty regex list."""
        regex_list = []
        agent_actions = [["a", "b"]]

        result = generate_guarded_action_pairs(regex_list, agent_actions)

        assert "actions_agent1" in result
        assert len(result["actions_agent1"]) == 0

    def test_generate_empty_action_list(self):
        """Verify behavior with empty action list."""
        regex_list = ["p", "q"]
        agent_actions = [[]]

        result = generate_guarded_action_pairs(regex_list, agent_actions)

        assert "actions_agent1" in result
        assert len(result["actions_agent1"]) == 0

    def test_generate_preserves_agent_order(self):
        """Verify agent numbering is sequential."""
        regex_list = ["p"]
        agent_actions = [["a"], ["b"], ["c"]]

        result = generate_guarded_action_pairs(regex_list, agent_actions)

        assert "actions_agent1" in result
        assert "actions_agent2" in result
        assert "actions_agent3" in result
