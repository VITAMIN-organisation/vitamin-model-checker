"""End-to-end: formula text -> parse() -> adapt() -> holds()/check(),
never a hand-built `Formula`. `test_parser.py` and `test_verifier.py` each
test their own module in isolation with a hand-built AST; nothing
previously exercised the two together."""

from __future__ import annotations

import pytest

spot = pytest.importorskip("spot")

from model_checker.algorithms.explicit.ATL_STAR.cgs_adapter import adapt
from model_checker.algorithms.explicit.ATL_STAR.verifier import (
    check,
    sat,
    witness,
)
from model_checker.parsers.formulas.ATL_STAR.grammar import (
    ATLStarParseError,
    parse,
)
from model_checker.tests.unit.algorithms.atl_star.toy_cgs import ToyCGS

pytestmark = pytest.mark.atl_star


def test_check_grand_coalition_can_force_eventually_granted():
    assert check(ToyCGS(), "<<1,2>> F granted") is True


def test_check_requester_alone_cannot_force_it_from_the_initial_state():
    assert check(ToyCGS(), "<<1>> F granted") is False


def test_check_at_an_explicit_state():
    assert check(ToyCGS(), "granted", state="s1") is True
    assert check(ToyCGS(), "granted", state="s0") is False


def test_check_rejects_an_unknown_state():
    with pytest.raises(ValueError, match="s99"):
        check(ToyCGS(), "granted", state="s99")


def test_check_rejects_an_out_of_range_agent_in_the_formula_text():
    # ToyCGS has 2 agents, check() must wire num_agents through to parse()
    # so this is caught at parse time, not silently misevaluated later.
    with pytest.raises(ATLStarParseError):
        check(ToyCGS(), "<<3>> F granted")


def test_nested_coalition_matches_flat_when_both_come_from_parsed_text():
    model = adapt(ToyCGS())
    nested = parse("<<1,2>> F <<1>> granted", num_agents=2)
    flat = parse("<<1,2>> F granted", num_agents=2)
    assert sat(nested, model) == sat(flat, model)


def test_witness_from_a_parsed_formula_gives_the_forcing_move():
    model = adapt(ToyCGS())
    formula = parse("<<1,2>> F granted", num_agents=2)
    result = witness(formula, model)
    assert result is not None
    assert dict(result.strategy.move(result.start)) == {1: "req", 2: "grant"}
