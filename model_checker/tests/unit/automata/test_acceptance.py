"""Pure-Python tests for AcceptanceCondition/AcceptanceKind/ParityKind/ParityStyle.
No Spot dependency, these are plain dataclasses/enums."""

from dataclasses import FrozenInstanceError

import pytest

from model_checker.automata.acceptance import (
    AcceptanceCondition,
    AcceptanceKind,
    ParityKind,
    ParityStyle,
    priority_from_mark,
)


def test_acceptance_kind_is_restricted_to_buchi_cobuchi_parity():
    # deliberately not Spot's full generality (no Rabin/Streett/generalized-Buchi/etc.)
    assert {kind.name for kind in AcceptanceKind} == {"BUCHI", "CO_BUCHI", "PARITY"}


def test_buchi_condition_needs_no_parity_fields():
    cond = AcceptanceCondition(kind=AcceptanceKind.BUCHI)
    assert cond.kind is AcceptanceKind.BUCHI
    assert cond.parity_kind is None
    assert cond.parity_style is None
    assert cond.priorities == {}


def test_parity_condition_holds_orientation_and_priorities():
    cond = AcceptanceCondition(
        kind=AcceptanceKind.PARITY,
        parity_kind=ParityKind.MAX,
        parity_style=ParityStyle.ODD,
        priorities={("s0", "a", "s1"): 1, ("s1", "b", "s0"): 2},
    )
    assert cond.kind is AcceptanceKind.PARITY
    assert cond.parity_kind is ParityKind.MAX
    assert cond.parity_style is ParityStyle.ODD
    assert cond.priorities == {("s0", "a", "s1"): 1, ("s1", "b", "s0"): 2}


def test_parity_has_all_four_orientations():
    orientations = {
        (kind, style) for kind in ParityKind for style in ParityStyle
    }
    assert len(orientations) == 4


def test_default_priorities_are_not_shared_between_instances():
    a = AcceptanceCondition(kind=AcceptanceKind.BUCHI)
    b = AcceptanceCondition(kind=AcceptanceKind.BUCHI)
    assert a.priorities is not b.priorities


def test_acceptance_condition_is_frozen():
    cond = AcceptanceCondition(kind=AcceptanceKind.CO_BUCHI)
    with pytest.raises(FrozenInstanceError):
        # setattr(), not `cond.kind = ...`, so static analyzers don't flag this
        # line as an error, the whole point of the test is that it IS invalid.
        cond.kind = AcceptanceKind.BUCHI


def test_equal_conditions_compare_equal():
    a = AcceptanceCondition(kind=AcceptanceKind.PARITY, parity_kind=ParityKind.MIN,
                             parity_style=ParityStyle.EVEN, priorities={("s0", "a", "s0"): 0})
    b = AcceptanceCondition(kind=AcceptanceKind.PARITY, parity_kind=ParityKind.MIN,
                             parity_style=ParityStyle.EVEN, priorities={("s0", "a", "s0"): 0})
    assert a == b


def test_priority_from_mark_returns_none_for_unmarked_edge():
    class FakeMark:
        def sets(self):
            return []

    assert priority_from_mark(FakeMark()) is None


def test_priority_from_mark_returns_the_single_color():
    class FakeMark:
        def sets(self):
            return [2]

    assert priority_from_mark(FakeMark()) == 2


def test_priority_from_mark_rejects_more_than_one_color():
    # a generalized-Büchi automaton can mark one edge with more than one
    # color, outside our restricted per-transition priority model
    class FakeMark:
        def sets(self):
            return [0, 1]

    with pytest.raises(ValueError, match="expects at most one"):
        priority_from_mark(FakeMark())
