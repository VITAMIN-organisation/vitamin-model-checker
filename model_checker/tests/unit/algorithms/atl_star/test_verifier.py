"""ATL* verifier on the toy CGS of toy_cgs.py.

Agent 1 requests, agent 2 grants. From s0 only req|grant reaches s1, where
`granted` holds; every other joint action stays at s0, and s1 always returns to
s0. So only the two agents together can force `granted` from s0.
"""

from __future__ import annotations

import pytest

spot = pytest.importorskip("spot")

from model_checker.algorithms.explicit.ATL_STAR.cgs_adapter import adapt
from model_checker.algorithms.explicit.ATL_STAR.verifier import (
    check,
    holds,
    sat,
    witness,
)
from model_checker.parsers.formulas.ATL_STAR.formula import (
    And,
    Coalition,
    Next,
    Not,
    Prop,
    True_,
    Until,
)
from model_checker.parsers.formulas.ATL_STAR.grammar import ATLStarParseError
from model_checker.tests.unit.algorithms.atl_star.toy_cgs import (
    CollidingMarkerToyCGS,
    ToyCGS,
)

pytestmark = pytest.mark.atl_star

_BOTH, _REQ, _GRANT = frozenset({1, 2}), frozenset({1}), frozenset({2})
_F_GRANTED = Until(True_(), Prop("granted"))


@pytest.fixture
def model():
    return adapt(ToyCGS())


@pytest.mark.parametrize(
    ("formula", "states"),
    [
        (Coalition(_BOTH, _F_GRANTED), {"s0", "s1"}),
        (Coalition(_REQ, _F_GRANTED), {"s1"}),
        (Coalition(_GRANT, _F_GRANTED), {"s1"}),
        (Coalition(_BOTH, Next(Prop("granted"))), {"s0"}),
    ],
    ids=["both_force_F", "requester_alone", "granter_alone", "both_force_X"],
)
def test_who_can_force_what(model, formula, states):
    """Alone, either agent is blocked by the other; F granted holds at s1 without any move."""
    assert sat(formula, model) == states


@pytest.mark.parametrize("name", ["granted", "Granted", "Fuel", "Xray"])
def test_proposition_starting_with_an_operator_letter_reaches_spot_whole(name):
    """Unquoted, Spot would read `Granted` as `G ranted` and give a wrong verdict."""
    cgs = ToyCGS()
    cgs.atomic_propositions = [name]
    formula = Coalition(_BOTH, Until(True_(), Prop(name)))
    assert sat(formula, adapt(cgs)) == {"s0", "s1"}


def test_fresh_marker_never_collides_with_a_model_proposition():
    """The model already has a proposition named like the first marker; the answer must stay {s1}."""
    inner = Coalition(_GRANT, _F_GRANTED)
    formula = Coalition(_REQ, And(inner, Not(Prop("__atl_star_elim_0"))))
    assert sat(formula, adapt(CollidingMarkerToyCGS())) == {"s1"}


@pytest.mark.parametrize(
    "formula",
    [
        Next(Prop("granted")),
        Prop("missing"),
        Coalition(_REQ, Prop("missing")),
        Coalition(frozenset({5}), Prop("granted")),
        Coalition(frozenset({1, 5}), Prop("granted")),
    ],
    ids=[
        "bare_next",
        "unknown_name",
        "unknown_name_inside",
        "agent_5",
        "agent_5_among_valid",
    ],
)
def test_formula_the_model_cannot_answer_is_refused(model, formula):
    """A path formula without a coalition, an undeclared name, or an agent the model lacks."""
    with pytest.raises(ValueError):
        sat(formula, model)


def test_holds_checks_the_initial_state_unless_told_otherwise(model):
    """`granted` is false at s0 (the initial state) and true at s1."""
    assert holds(Prop("granted"), model) is False
    assert holds(Prop("granted"), model, state="s1") is True
    with pytest.raises(ValueError, match="s99"):
        holds(Prop("granted"), model, state="s99")


def test_check_parses_the_text_with_the_models_agent_count():
    """check() is the text entry point; agent 3 is caught by the parser, not misread."""
    assert check(ToyCGS(), "<<1,2>> F granted") is True
    assert check(ToyCGS(), "<<1>> F granted") is False
    assert check(ToyCGS(), "granted", state="s1") is True
    with pytest.raises(ATLStarParseError):
        check(ToyCGS(), "<<3>> F granted")


def test_witness_gives_the_only_forcing_move(model):
    """req|grant is the one joint action from s0 to s1."""
    result = witness(Coalition(_BOTH, _F_GRANTED), model)
    assert dict(result.strategy.move(result.start)) == {1: "req", 2: "grant"}
    assert result.strategy.project(1).move(result.start) == "req"


def test_witness_is_none_when_the_coalition_cannot_force(model):
    """Agent 1 alone cannot force X granted from s0."""
    assert witness(Coalition(_REQ, Next(Prop("granted"))), model) is None


def test_witness_exists_where_the_goal_already_holds(model):
    """At s1 F granted holds with no move needed."""
    assert witness(Coalition(_BOTH, _F_GRANTED), model, state="s1") is not None


@pytest.mark.parametrize(
    ("formula", "state", "name"),
    [
        (Coalition(frozenset({5}), Prop("granted")), None, "5"),
        (Coalition(_BOTH, _F_GRANTED), "s99", "s99"),
    ],
)
def test_witness_refuses_an_unknown_agent_or_state(model, formula, state, name):
    """The message names the agent or state."""
    with pytest.raises(ValueError, match=name):
        witness(formula, model, state=state) if state else witness(formula, model)


def test_nested_coalition_keeps_its_own_witness(model):
    """In <<1,2>> X <<1,2>> F granted, the inner coalition's req|grant strategy survives at s0 and s1."""
    formula = Coalition(_BOTH, Next(Coalition(_BOTH, _F_GRANTED)))
    result = witness(formula, model)
    for state in ("s0", "s1"):
        [inner] = result.nested_witnesses_at(state)
        assert dict(inner.strategy.move(inner.start)) == {1: "req", 2: "grant"}
        assert inner.nested == {}


def test_advance_follows_the_forcing_move(model):
    """Playing req|grant from s0 lands in s1; an action the model lacks returns None."""
    result = witness(Coalition(_BOTH, _F_GRANTED), model)
    assert result.advance(result.strategy.move(result.start)).start[0] == "s1"
    assert result.advance(frozenset({(1, "bogus"), (2, "grant")})) is None


def test_advance_off_the_winning_path_reaches_a_dead_end(model):
    """For X granted, staying at s0 once is allowed, a second time leaves only the rejecting sink."""
    result = witness(Coalition(_BOTH, Next(Prop("granted"))), model)
    idle = frozenset({(1, "idle"), (2, "deny")})
    off_path = result.advance(idle)
    assert off_path.start[0] == "s0"
    assert off_path.advance(idle) is None


def test_advance_switches_to_the_nested_witness(model):
    """After the outer X step the inner F granted already holds, so the inner strategy takes over."""
    formula = Coalition(_BOTH, Next(Coalition(_BOTH, _F_GRANTED)))
    result = witness(formula, model)
    advanced = result.advance(result.strategy.move(result.start))
    assert dict(advanced.strategy.move(advanced.start)) == {1: "req", 2: "grant"}
