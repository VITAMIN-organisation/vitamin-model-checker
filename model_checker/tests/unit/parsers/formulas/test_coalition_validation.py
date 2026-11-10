"""Coalition lists are checked at parse time in every logic that has one.

Agents are numbered 1..n_agent. An empty list, a trailing comma, a negative agent,
agent 0 or an agent above n_agent is a syntax error, and a range error names the
agent. COTL's legion may be empty (the coalition with no demons), so COTL is left
out of the empty case.
"""

import pytest

from model_checker.tests.helpers.formula_cases import parse, parse_errors

# logic -> formula with `{c}` where the agent list goes
_COALITION = {
    "ATL": "<{c}>F p",
    "ATLF": "<{c}>F p",
    "IATL": "<{c}>F p",
    "OATL": "<{c}><2>F p",
    "COTL": "<{c}><2>F p",
    "RBATL": "<{c}><2>F p",
    "RABATL": "<{c}><2>F p",
    "NatATL": "<{{{c}}}, 2>F p",
    "NatATL_Recall": "<{{{c}}}, 2>F p",
    "NatATLF": "<{{{c}}}, 2>F p",
    "CapATL": "<{{{c}}}>F p",
    "Wallet_ATL": "<<{c}>>F p",
    "ATL_STAR": "<<{c}>> F p",
}


def _formula(logic: str, agents: str) -> str:
    return _COALITION[logic].format(c=agents)


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(_COALITION))
def test_every_agent_of_the_model_may_join(logic):
    """`<1>` and the grand coalition `<1,2>` parse with two agents."""
    assert parse(logic, _formula(logic, "1")) is not None
    assert parse(logic, _formula(logic, "1,2")) is not None


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(set(_COALITION) - {"COTL"}))
def test_empty_coalition_is_rejected(logic):
    """`<>` names no agent (docs/logic_knowledge_base.md rejects it in every logic but COTL)."""
    assert parse(logic, _formula(logic, "")) is None


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(_COALITION))
@pytest.mark.parametrize("agents", ["1,", "-1"])
def test_malformed_agent_list_is_rejected(logic, agents):
    """A trailing comma or a negative agent is a syntax error."""
    assert parse(logic, _formula(logic, agents)) is None


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(_COALITION))
@pytest.mark.parametrize("agent", ["0", "3"])
def test_agent_outside_the_model_is_rejected_by_number(logic, agent):
    """Agents run from 1 to n_agent = 2; the error names the bad agent."""
    [error, *_] = parse_errors(logic, _formula(logic, agent))
    assert agent in error, error


@pytest.mark.unit
@pytest.mark.parametrize("logic", sorted(_COALITION))
def test_model_with_no_agents_accepts_no_coalition(logic):
    """With n_agent = 0 even agent 1 is out of range."""
    assert parse(logic, _formula(logic, "1"), n_agent=0) is None


@pytest.mark.unit
def test_iatl_box_coalition_is_checked_like_the_diamond():
    """IATL's `[A]` takes the same agent list as `<A>`."""
    assert parse("IATL", "[1,2]G p") is not None
    assert parse("IATL", "[3]G p") is None
    assert parse("IATL", "[]G p") is None


@pytest.mark.unit
def test_iatl_n_agent_zero_is_not_overridden_by_max_coalition():
    """An explicit n_agent = 0 wins over max_coalition, so the check stays closed."""
    from model_checker.parsers.formula_parser_factory import FormulaParserFactory

    parser = FormulaParserFactory.get_parser_instance("IATL")
    assert parser.parse("<1>X p", n_agent=0, max_coalition=5) is None
    assert parser.parse("<1>X p", max_coalition=2) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula", ["<<0>>X p", "<<1,0>>F q", "<<1:wallet(0, >= 5)>>G q"]
)
def test_wallet_atl_rejects_agent_zero_in_coalition_and_guard(formula):
    """The wallet guard's agent is checked like a coalition member."""
    assert parse("Wallet_ATL", formula) is None


@pytest.mark.unit
def test_atl_star_checks_agents_inside_nested_coalitions():
    """An out-of-range agent is found under X, && and U, not only at the top."""
    for formula in ["<<1>>X <<5>>p", "<<1>>(p && <<5>>q)", "<<1>>(p U <<5>>q)"]:
        assert parse("ATL_STAR", formula) is None, formula
