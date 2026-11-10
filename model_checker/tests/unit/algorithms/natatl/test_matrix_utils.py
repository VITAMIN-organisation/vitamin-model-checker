"""NatATL memoryless: fixing one agent's action in some states prunes the transition matrix.

Only the rows of the given states change; there each cell keeps the joint actions
where the agent plays the fixed action, and a cell left with none becomes 0.
"""

import copy

import pytest

from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)


def _prune(
    graph,
    *,
    states=frozenset({"s0"}),
    action="A",
    agent_index=1,
    agents=(1,),
    in_place=False,
):
    return modify_matrix(
        graph,
        states=set(states),
        action=action,
        agent_index=agent_index,
        agents=list(agents),
        num_agents=2,
        state_to_index={f"s{i}": i for i in range(len(graph))},
        in_place=in_place,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("graph", "kwargs", "expected"),
    [
        (
            [[0, "AC,AD", 0], [0, "II", 0], [0, 0, "II"]],
            {},
            [[0, "A|C,A|D", 0], [0, "II", 0], [0, 0, "II"]],
        ),
        (
            [[0, "AC,BC", "AD,BD"], [0, "II", 0], [0, 0, "II"]],
            {},
            [[0, "A|C", "A|D"], [0, "II", 0], [0, 0, "II"]],
        ),
        ([[0, "BC"], [0, "II"]], {}, [[0, 0], [0, "II"]]),
        ([[0, "AC"], [0, "BC"]], {}, [[0, "A|C"], [0, "BC"]]),
        (
            [[0, "*", "AC"], [0, "II", 0], [0, 0, "II"]],
            {},
            [[0, "*", "A|C"], [0, "II", 0], [0, 0, "II"]],
        ),
        (
            [[0, "AI"], [0, "II"]],
            {"action": "I", "agent_index": 2, "agents": (1, 2)},
            [[0, "A|IDLE"], [0, "II"]],
        ),
    ],
    ids=[
        "keeps_matching_joints",
        "drops_the_other_action",
        "empties_a_cell_with_no_match",
        "leaves_other_states_alone",
        "keeps_a_wildcard_cell",
        "fixes_the_second_agent_to_idle",
    ],
)
def test_pruned_matrix(graph, kwargs, expected):
    """Agent 1 plays A in s0 unless the case says otherwise."""
    assert _prune(graph, **kwargs) == expected


@pytest.mark.unit
def test_no_states_returns_an_unchanged_copy():
    """With no state to fix, the result equals the input but is a separate matrix."""
    graph = [[0, "AC"], [0, "BC"]]
    result = _prune(graph, states=set())
    assert result == graph
    result[0][1] = "changed"
    assert graph[0][1] == "AC"


@pytest.mark.unit
def test_in_place_and_copy_give_the_same_matrix():
    """in_place changes the input; the default leaves it as it was. s1's II is rewritten as IDLE|IDLE."""
    graph = [[0, "AC,AD", "BC,BD"], [0, "II", 0], [0, 0, "II"]]
    original = copy.deepcopy(graph)
    copied = _prune(graph, states={"s0", "s1"})
    assert graph == original
    in_place = _prune(graph, states={"s0", "s1"}, in_place=True)
    assert in_place is graph
    assert in_place == copied == [[0, "A|C,A|D", 0], [0, "IDLE|IDLE", 0], [0, 0, "II"]]
