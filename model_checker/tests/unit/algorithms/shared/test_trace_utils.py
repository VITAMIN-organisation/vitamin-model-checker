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
_ALL = {"s0", "s1", "s2", "s3"}
# s0's first successor starts a chain of 120 states; its second loops on itself.
_LONG_FIRST_BRANCH = [(f"s{i}", f"s{i + 1}") for i in range(120)] + [
    ("s120", "s120"),
    ("s0", "s121"),
    ("s121", "s121"),
]


def _ring_beside_a_self_loop(ring_size: int) -> list[tuple[str, str]]:
    """Edges s0 -> c0 on a ring of ring_size states, and s0 -> a -> b -> b."""
    ring = [(f"c{i}", f"c{(i + 1) % ring_size}") for i in range(ring_size)]
    return [("s0", "c0"), ("s0", "a"), ("a", "b"), ("b", "b")] + ring


def _states_of(edges: list[tuple[str, str]]) -> set[str]:
    return {state for edge in edges for state in edge}


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
        # s1 comes first but is a dead end; s2 loops on itself (index 1).
        ([("s0", "s1"), ("s0", "s2"), ("s2", "s2")], _ALL, (["s0", "s2"], 1)),
        # The cycle s1 s2 s3 is entered at s1, which s3 steps back to (index 1).
        (_CHAIN + [("s3", "s1")], _ALL, (["s0", "s1", "s2", "s3"], 1)),
        # s121 is the cycle state nearest to s0, and it loops on itself (index 1).
        (
            _LONG_FIRST_BRANCH,
            {f"s{i}" for i in range(122)},
            (["s0", "s121"], 1),
        ),
        # Via c0: 1 + 150 = 151 states, over the limit. Via b: s0 a b.
        (
            _ring_beside_a_self_loop(150),
            _states_of(_ring_beside_a_self_loop(150)),
            (["s0", "a", "b"], 2),
        ),
        # Via c0: 1 + 10 = 11 states. Via b: 3, the shorter.
        (
            _ring_beside_a_self_loop(10),
            _states_of(_ring_beside_a_self_loop(10)),
            (["s0", "a", "b"], 2),
        ),
        # s1 has no successor among the allowed states.
        (_CHAIN, {"s0", "s1"}, None),
        ([("s0", "s0")], {"s1"}, None),
    ],
    ids=[
        "loop_after_a_prefix",
        "self_loop",
        "first_successor_is_a_dead_end",
        "cycle_entered_in_the_middle",
        "long_first_branch",
        "nearest_cycle_too_long",
        "shorter_lasso_through_a_farther_cycle",
        "stuck",
        "start_not_allowed",
    ],
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
