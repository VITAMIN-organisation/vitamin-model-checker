"""Unit tests for NatATL memoryless matrix pruning."""

import copy

import pytest

from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.tests.helpers.model_helpers import load_cgs_from_content
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content


def _prune(
    graph,
    *,
    states=None,
    action="A",
    agent_index=1,
    agents=None,
    num_agents=2,
    state_to_index=None,
    in_place=False,
):
    """Call ``modify_matrix`` with common defaults for hand-built graphs."""
    if states is None:
        states = {"s0"}
    if agents is None:
        agents = [1]
    if state_to_index is None:
        state_to_index = {f"s{i}": i for i in range(len(graph))}
    return modify_matrix(
        graph,
        states=states,
        action=action,
        agent_index=agent_index,
        agents=agents,
        num_agents=num_agents,
        state_to_index=state_to_index,
        in_place=in_place,
    )


# graph, prune kwargs, expected {(row, col): value}, rows that must stay shared
MODIFY_MATRIX_CASES = [
    (
        [[0, "AC,AD", 0], [0, "II", 0], [0, 0, "II"]],
        {},
        {(0, 1): "A|C,A|D"},
        [1, 2],
    ),
    (
        [[0, "AC,BC", "AD,BD"], [0, "II", 0], [0, 0, "II"]],
        {},
        {(0, 1): "A|C", (0, 2): "A|D"},
        [],
    ),
    (
        [[0, "AI"], [0, "II"]],
        {"action": "I", "agent_index": 2, "agents": [1, 2]},
        {(0, 1): "A|IDLE"},
        [],
    ),
    (
        [[0, "BC"], [0, "II"]],
        {},
        {(0, 1): 0},
        [],
    ),
    (
        [[0, "AC"], [0, "BC"]],
        {},
        {(0, 1): "A|C"},
        [1],
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize(
    "graph,kwargs,expected_cells,shared_rows",
    MODIFY_MATRIX_CASES,
    ids=[
        "keeps_matching_compact_joint",
        "keeps_idle_and_required_action",
        "normalizes_idle_token",
        "clears_cell_when_no_joint_matches",
        "skips_rows_outside_states",
    ],
)
def test_modify_matrix_filters_joints(graph, kwargs, expected_cells, shared_rows):
    original_rows = {i: graph[i] for i in shared_rows}
    result = _prune(graph, **kwargs)
    for (i, j), value in expected_cells.items():
        assert result[i][j] == value
    for i, row in original_rows.items():
        assert result[i] is row


@pytest.mark.unit
def test_modify_matrix_empty_states_returns_full_copy():
    graph = [[0, "AC"], [0, "BC"]]
    result = _prune(graph, states=set())
    assert result == graph
    assert result is not graph
    assert result[0] is not graph[0]


@pytest.mark.unit
def test_modify_matrix_inplace_matches_copy():
    graph = [
        [0, "AC,AD", "BC,BD"],
        [0, "II", 0],
        [0, 0, "II"],
    ]
    kwargs = {"states": {"s0", "s1"}}
    copy_result = _prune(copy.deepcopy(graph), in_place=False, **kwargs)
    inplace_graph = copy.deepcopy(graph)
    inplace_result = _prune(inplace_graph, in_place=True, **kwargs)

    assert copy_result == inplace_result
    assert inplace_result is inplace_graph
    assert graph == [
        [0, "AC,AD", "BC,BD"],
        [0, "II", 0],
        [0, 0, "II"],
    ]


@pytest.mark.unit
def test_modify_matrix_matches_integration_model(temp_file):
    content = build_cgs_model_content(
        transitions=[
            ["0", "AC,AD", "BC,BD"],
            ["0", "II", "0"],
            ["0", "0", "II"],
        ],
        state_names=["s0", "s1", "s2"],
        initial_state="s0",
        labelling=[["0"], ["1"], ["0"]],
        num_agents=2,
        prop_names=["p"],
    )
    cgs = load_cgs_from_content(temp_file, content)
    pruned = _prune(
        cgs.graph,
        num_agents=cgs.get_number_of_agents(),
        state_to_index=cgs.state_to_index,
    )
    assert pruned[0][1] == "A|C,A|D"
    assert pruned[0][2] == 0
