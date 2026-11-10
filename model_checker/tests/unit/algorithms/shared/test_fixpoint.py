"""Least and greatest fixpoints, the loop behind every F, G and U operator."""

import pytest

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)

# A chain s0 -> s1 -> s2 -> s3; pred adds the state before each member.
_PRED = {"s1": "s0", "s2": "s1", "s3": "s2"}


def _add_predecessors(states: set[str]) -> set[str]:
    return states | {_PRED[s] for s in states if s in _PRED}


@pytest.mark.unit
def test_least_fixpoint_grows_until_nothing_is_added():
    """Backward reachability from s2 on the chain is s0, s1, s2, and never s3."""
    assert least_fixpoint({"s2"}, _add_predecessors) == {"s0", "s1", "s2"}


@pytest.mark.unit
def test_greatest_fixpoint_shrinks_until_nothing_is_removed():
    """Keeping only states whose successor is kept removes the dead end s3, then s2, s1, s0."""
    successor = {"s0": "s1", "s1": "s2", "s2": "s3"}

    def keep_with_kept_successor(states: set[str]) -> set[str]:
        return {s for s in states if successor.get(s) in states}

    assert (
        greatest_fixpoint({"s0", "s1", "s2", "s3"}, keep_with_kept_successor) == set()
    )


@pytest.mark.unit
def test_greatest_fixpoint_keeps_a_cycle():
    """s0 <-> s1 support each other, s2 has no successor and goes."""
    successor = {"s0": "s1", "s1": "s0"}

    def keep_with_kept_successor(states: set[str]) -> set[str]:
        return {s for s in states if successor.get(s) in states}

    assert greatest_fixpoint({"s0", "s1", "s2"}, keep_with_kept_successor) == {
        "s0",
        "s1",
    }


@pytest.mark.unit
def test_fixpoint_of_an_empty_start():
    """The least fixpoint from nothing with nothing to add is empty."""
    assert least_fixpoint(set(), _add_predecessors) == set()
