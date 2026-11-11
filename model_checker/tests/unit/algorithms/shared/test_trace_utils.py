"""Trace helpers: turn an edge list into a path from the initial state to a target, or into a lasso.

A trace has at most MAX_TRACE_LENGTH states; a longer one gives None, not a
truncated trace.
"""

import pytest

from model_checker.algorithms.explicit.shared.trace_utils import (
    MAX_TRACE_LENGTH,
    find_lasso,
    reconstruct_trace_bfs,
)

_CHAIN = [("s0", "s1"), ("s1", "s2"), ("s2", "s3")]


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
def test_path_longer_than_the_limit_is_none():
    """A path of MAX_TRACE_LENGTH states is returned; one more state gives None."""
    n = MAX_TRACE_LENGTH
    edges = [(f"s{i}", f"s{i + 1}") for i in range(n + 1)]

    def trace_to(last: int):
        return reconstruct_trace_bfs(
            edges=edges, initial_state="s0", target_states={f"s{last}"}
        )

    assert len(trace_to(n - 1)) == n
    assert trace_to(n) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("edges", "allowed", "lasso"),
    [
        # s0 s1 s2, then s2 steps back to s1 (index 1).
        (_CHAIN[:2] + [("s2", "s1")], {"s0", "s1", "s2"}, (["s0", "s1", "s2"], 1)),
        # s1 comes first but is not allowed; s2 loops on itself (index 1).
        ([("s0", "s1"), ("s0", "s2"), ("s2", "s2")], {"s0", "s2"}, (["s0", "s2"], 1)),
        # s1 has no successor among the allowed states.
        (_CHAIN, {"s0", "s1"}, None),
        ([("s0", "s0")], {"s1"}, None),
    ],
    ids=["loop_after_a_prefix", "self_loop", "stuck", "start_not_allowed"],
)
def test_lasso_stays_inside_the_allowed_states(edges, allowed, lasso):
    """The lasso lists each state once, with the index its last state steps back to."""
    assert find_lasso(edges=edges, start="s0", allowed=allowed) == lasso


@pytest.mark.unit
def test_lasso_longer_than_the_limit_is_none():
    """A ring of MAX_TRACE_LENGTH states is returned; one more state gives None."""

    def lasso_on_ring(size: int):
        states = [f"s{i}" for i in range(size)]
        edges = [(state, states[(i + 1) % size]) for i, state in enumerate(states)]
        return find_lasso(edges=edges, start="s0", allowed=set(states))

    n = MAX_TRACE_LENGTH
    assert lasso_on_ring(n) == ([f"s{i}" for i in range(n)], 0)
    assert lasso_on_ring(n + 1) is None
