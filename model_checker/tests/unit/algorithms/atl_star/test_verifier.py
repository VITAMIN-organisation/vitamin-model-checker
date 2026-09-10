from __future__ import annotations

# ruff: noqa: E402  -- imports deliberately follow importorskip("spot") below,
# to skip this whole file cleanly if Spot isn't installed
import pytest

spot = pytest.importorskip("spot")

from model_checker.algorithms.explicit.ATL_STAR.cgs_adapter import adapt
from model_checker.algorithms.explicit.ATL_STAR.verifier import holds, sat, witness
from model_checker.parsers.formulas.ATL_STAR.formula import (
    And,
    Coalition,
    Next,
    Not,
    Prop,
    True_,
    Until,
)
from model_checker.tests.unit.algorithms.atl_star.toy_cgs import ToyCGS


@pytest.fixture
def model():
    return adapt(ToyCGS())


def test_prop(model):
    assert sat(Prop("granted"), model) == {"s1"}


def test_true(model):
    assert sat(True_(), model) == {"s0", "s1"}


def test_not(model):
    assert sat(Not(Prop("granted")), model) == {"s0"}


def test_and(model):
    assert sat(And(True_(), Prop("granted")), model) == {"s1"}


def test_bare_temporal_operator_at_top_level_raises(model):
    with pytest.raises(ValueError):
        sat(Next(Prop("granted")), model)


def test_grand_coalition_can_force_eventually_granted(model):
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    assert sat(formula, model) == {"s0", "s1"}


def test_requester_alone_cannot_force_granted_from_s0(model):
    # F(granted) is trivially true at s1 itself (no strategy needed, it
    # already holds), but agent 1 alone can't force *reaching* s1 from s0
    # since agent 2 can always deny.
    formula = Coalition(frozenset({1}), Until(True_(), Prop("granted")))
    assert sat(formula, model) == {"s1"}


def test_granter_alone_cannot_force_granted_from_s0(model):
    formula = Coalition(frozenset({2}), Until(True_(), Prop("granted")))
    assert sat(formula, model) == {"s1"}


def test_grand_coalition_next_granted_only_from_s0(model):
    formula = Coalition(frozenset({1, 2}), Next(Prop("granted")))
    assert sat(formula, model) == {"s0"}


def test_and_inside_path_formula(model):
    formula = Coalition(frozenset({1, 2}), And(True_(), Prop("granted")))
    assert sat(formula, model) == {"s1"}


def test_not_inside_path_formula(model):
    formula = Coalition(frozenset({1, 2}), Not(Prop("granted")))
    assert sat(formula, model) == {"s0"}


def test_nested_coalition_matches_equivalent_flat_formula(model):
    nested = Coalition(
        frozenset({1, 2}), Until(True_(), Coalition(frozenset({1}), Prop("granted")))
    )
    flat = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    assert sat(nested, model) == sat(flat, model)


def test_holds_defaults_to_model_initial_state(model):
    assert holds(Prop("granted"), model) is False
    assert holds(Not(Prop("granted")), model) is True


def test_holds_at_explicit_state(model):
    assert holds(Prop("granted"), model, state="s1") is True


def test_holds_rejects_an_unknown_state(model):
    with pytest.raises(ValueError, match="s99"):
        holds(Prop("granted"), model, state="s99")


def test_sat_coalition_rejects_agent_ids_outside_the_model(model):
    formula = Coalition(frozenset({5}), Prop("granted"))
    with pytest.raises(ValueError, match="5"):
        sat(formula, model)


def test_sat_coalition_rejects_a_mix_of_valid_and_invalid_agent_ids(model):
    formula = Coalition(frozenset({1, 5}), Prop("granted"))
    with pytest.raises(ValueError, match="5"):
        sat(formula, model)


def test_witness_gives_the_grand_coalitions_only_forcing_move_at_s0(model):
    # req|grant is s0's only transition to s1 (granted), every other joint
    # action self-loops on s0 forever, so it's the *only* winning move here.
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    result = witness(formula, model)
    assert result is not None
    action = result.strategy.move(result.start)
    assert dict(action) == {1: "req", 2: "grant"}


def test_witness_strategy_projects_onto_each_agent(model):
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    result = witness(formula, model)
    assert result.strategy.project(1).move(result.start) == "req"
    assert result.strategy.project(2).move(result.start) == "grant"


def test_witness_is_none_when_the_coalition_cannot_force_the_formula(model):
    # Agent 1 alone can't force Next(granted) from s0, agent 2 can always deny.
    formula = Coalition(frozenset({1}), Next(Prop("granted")))
    assert witness(formula, model) is None


def test_witness_at_a_state_where_the_formula_already_holds(model):
    # No move needed: granted already holds at s1 itself.
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    result = witness(formula, model, state="s1")
    assert result is not None


def test_witness_rejects_agent_ids_outside_the_model(model):
    formula = Coalition(frozenset({5}), Prop("granted"))
    with pytest.raises(ValueError, match="5"):
        witness(formula, model)


def test_witness_rejects_an_unknown_state(model):
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    with pytest.raises(ValueError, match="s99"):
        witness(formula, model, state="s99")


def test_witness_has_no_nested_entries_without_a_nested_coalition(model):
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    result = witness(formula, model)
    assert result.nested == {}
    assert result.nested_witnesses_at("s0") == []


def test_witness_exposes_a_nested_coalitions_own_witness(model):
    # The grand coalition can force F(granted) from *every* toy-CGS state, so
    # <<1,2>> X <<1,2>> F granted is trivially true for the outer step (any
    # move keeps the fresh proposition true at the next state), what this
    # actually tests is that the inner coalition's own req|grant strategy
    # survives elimination instead of being discarded.
    formula = Coalition(
        frozenset({1, 2}),
        Next(Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))),
    )
    result = witness(formula, model)
    assert result is not None

    for state in ("s0", "s1"):
        nested_here = result.nested_witnesses_at(state)
        assert len(nested_here) == 1
        inner = nested_here[0]
        assert dict(inner.strategy.move(inner.start)) == {1: "req", 2: "grant"}
        assert inner.nested == {}  # no further nesting inside F granted itself


def test_advance_follows_the_grand_coalitions_forcing_move_to_s1(model):
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    result = witness(formula, model)
    move = result.strategy.move(result.start)  # the full joint action: grand coalition == everyone
    advanced = result.advance(move)
    assert advanced is not None
    assert advanced.start[0] == "s1"


def test_advance_returns_none_for_an_unrecognized_action(model):
    formula = Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))
    result = witness(formula, model)
    bogus = frozenset({(1, "bogus"), (2, "grant")})
    assert result.advance(bogus) is None


def test_advance_hits_the_rejecting_sink_off_the_winning_path(model):
    # Next(granted) only cares about the *second* letter of the trace, so
    # Automaton.from_ltl("X(granted)") only has a real edge once it's
    # checking a state where "granted" holds, deviating from the winning
    # req|grant move (self-looping on s0 instead) reaches a product state
    # with no real automaton edge left at all, only complete()'s sink.
    formula = Coalition(frozenset({1, 2}), Next(Prop("granted")))
    result = witness(formula, model)
    assert result is not None

    off_path = result.advance(frozenset({(1, "idle"), (2, "deny")}))
    assert off_path is not None
    assert off_path.start[0] == "s0"

    dead_end = off_path.advance(frozenset({(1, "idle"), (2, "deny")}))
    assert dead_end is None


def test_advance_switches_into_a_nested_witness_when_one_becomes_available(model):
    formula = Coalition(
        frozenset({1, 2}),
        Next(Coalition(frozenset({1, 2}), Until(True_(), Prop("granted")))),
    )
    result = witness(formula, model)
    move = result.strategy.move(result.start)
    advanced = result.advance(move)
    assert advanced is not None
    # The fresh proposition already held at whichever state the outer move
    # led to (the grand coalition can force F granted from every toy
    # state), so advance() should switch into that inner witness instead of
    # continuing the (now-satisfied, don't-care) outer one.
    assert dict(advanced.strategy.move(advanced.start)) == {1: "req", 2: "grant"}
