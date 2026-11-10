"""Joint actions in transition cells: `AC` and `A|C` are one profile, one token per agent."""

import pytest

from model_checker.parsers.game_structures.cgs import cgs_actions


@pytest.mark.unit
@pytest.mark.parametrize(
    ("cell", "num_agents", "profiles"),
    [
        ("AC,AD", 2, ["A|C", "A|D"]),
        ("A|C,A|D", 2, ["A|C", "A|D"]),
        ("AC,BC", 2, ["A|C", "B|C"]),
        ("*", 2, ["*|*"]),
        ("*", 3, ["*|*|*"]),
        ("a", 1, ["a"]),
        ("I", 1, ["IDLE"]),
        ("IDLE|MOVE", 2, ["IDLE|MOVE"]),
    ],
)
def test_cell_expands_to_pipe_profiles(cell, num_agents, profiles):
    """Compact and piped cells, `*` and the idle `I` all become `x|y` profiles."""
    assert cgs_actions.build_action_list(cell, num_agents) == profiles


@pytest.mark.unit
@pytest.mark.parametrize(("cell", "num_agents"), [("A", 2), ("A|B", 3), ("I", 2)])
def test_profile_with_too_few_tokens_is_refused(cell, num_agents):
    """A profile must give every agent an action; the message names the cell."""
    with pytest.raises(ValueError, match=f"in cell '{cell}'"):
        cgs_actions.build_action_list(cell, num_agents)


@pytest.mark.unit
def test_actions_per_agent_come_from_every_cell():
    """Agent 1 plays the first letters, agent 2 the second; `*` cells add nothing."""
    graph = [["AC", "*"], [0, "BD"]]
    actions = cgs_actions.extract_actions_for_agents(graph, [1, 2])
    assert {agent: sorted(acts) for agent, acts in actions.items()} == {
        "agent1": ["A", "B"],
        "agent2": ["C", "D"],
    }


@pytest.mark.unit
def test_actions_of_one_agent_only():
    """Asking for agent 2 alone still reads its token from 2-agent profiles."""
    actions = cgs_actions.extract_actions_for_agents([["AC", 0], [0, "BD"]], [2])
    assert sorted(actions["agent2"]) == ["C", "D"]
    assert list(actions) == ["agent2"]


@pytest.mark.unit
@pytest.mark.parametrize("agent", [0, 3])
def test_agent_number_outside_the_model_is_refused(agent):
    """Agents run from 1 to the model's count; the message names the number."""
    with pytest.raises(ValueError, match=f"Invalid agent number: {agent}"):
        cgs_actions.validate_agent_numbers([agent], 2)
