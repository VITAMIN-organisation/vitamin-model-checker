"""Trace helpers: turn a predecessor map or an edge list into a path from the initial state to a target.

Traces are cut at MAX_TRACE_LENGTH states; a longer path gives None, not a
truncated path.
"""

import pytest

from model_checker.algorithms.explicit.shared.trace_utils import (
    MAX_TRACE_LENGTH,
    build_predecessor_map_bfs,
    build_predecessor_map_forward,
    extract_shortest_trace,
    reconstruct_trace_bfs,
    reconstruct_trace_from_predecessors,
)

_CHAIN = [("s0", "s1"), ("s1", "s2"), ("s2", "s3")]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("targets", "predecessors", "trace"),
    [
        ({"s3"}, {"s1": "s0", "s2": "s1", "s3": "s2"}, ["s0", "s1", "s2", "s3"]),
        ({"s5"}, {"s1": "s0", "s2": "s1"}, None),
        ({"s1"}, {"s1": "s2", "s2": "s1"}, None),
        ({"s0", "s3"}, {"s1": "s0"}, ["s0"]),
    ],
    ids=["chain", "target_unreachable", "predecessor_cycle", "initial_is_a_target"],
)
def test_trace_from_a_predecessor_map(targets, predecessors, trace):
    """Follow predecessors back to s0; a cycle that never reaches s0 gives None."""
    assert (
        reconstruct_trace_from_predecessors(
            initial_state="s0", target_states=targets, predecessors=predecessors
        )
        == trace
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("edges", "trace"),
    [
        (_CHAIN + [("s1", "s4")], ["s0", "s1", "s2", "s3"]),
        (_CHAIN + [("s0", "s3")], ["s0", "s3"]),
        ([("s0", "s1"), ("s2", "s3")], None),
    ],
    ids=["side_branch_ignored", "shortest_path_wins", "unreachable"],
)
def test_breadth_first_trace_is_a_shortest_path(edges, trace):
    """BFS from s0 to s3 returns a path with the fewest steps."""
    assert (
        reconstruct_trace_bfs(edges=edges, initial_state="s0", target_states={"s3"})
        == trace
    )


@pytest.mark.unit
@pytest.mark.parametrize("builder", ["predecessors", "bfs"])
def test_trace_longer_than_the_limit_is_none(builder):
    """A path of MAX_TRACE_LENGTH states is returned; one more state gives None."""
    n = MAX_TRACE_LENGTH
    predecessors = {f"s{i + 1}": f"s{i}" for i in range(n + 1)}
    edges = [(f"s{i}", f"s{i + 1}") for i in range(n + 1)]

    def trace_to(last: int):
        if builder == "predecessors":
            return reconstruct_trace_from_predecessors(
                initial_state="s0",
                target_states={f"s{last}"},
                predecessors=predecessors,
            )
        return reconstruct_trace_bfs(
            edges=edges, initial_state="s0", target_states={f"s{last}"}
        )

    assert len(trace_to(n - 1)) == n
    assert trace_to(n) is None


@pytest.mark.unit
def test_predecessor_maps_point_one_step_toward_or_away_from_the_target():
    """Backward BFS maps each state to its next step to s3; forward BFS to the state before it."""
    assert build_predecessor_map_bfs(edges=_CHAIN, target_states={"s3"}) == {
        "s2": "s3",
        "s1": "s2",
        "s0": "s1",
    }
    assert build_predecessor_map_forward(edges=_CHAIN, initial_state="s0") == {
        "s1": "s0",
        "s2": "s1",
        "s3": "s2",
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    ("initial", "trace"), [("s0", ["s0", "s2"]), ("invalid", None)]
)
def test_shortest_trace_from_the_initial_state(initial, trace):
    """s0 -> s2 directly beats s0 -> s1 -> s2; an unknown initial state has no trace."""
    edges = [("s0", "s1"), ("s1", "s2"), ("s0", "s2")]
    assert (
        extract_shortest_trace(
            initial_state=initial,
            target_states={"s2"},
            all_states={"s0", "s1", "s2"},
            edges=edges,
        )
        == trace
    )
