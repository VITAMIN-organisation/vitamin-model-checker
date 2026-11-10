"""Wallet_ATL: `<<A : wallet(i, op v)>>` guards a coalition on agent i's wallet.

The tree keeps the agents, each guard as (agent, operator, value), and the
temporal formula under the coalition.
"""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _parse(formula: str, max_coalition: int = 2):
    parser = FormulaParserFactory.get_parser_instance("Wallet_ATL")
    return parser.parse(formula, max_coalition=max_coalition)


@pytest.mark.unit
def test_guarded_coalition_tree():
    """Agents, guard and formula all reach the tree."""
    assert _parse("<<1,2:wallet(1, >= 50)>>G safe") == {
        "type": "coalition_wallet",
        "agents": [1, 2],
        "constraints": [{"agent": 1, "operator": ">=", "value": 50}],
        "formula": {
            "type": "unary",
            "operator": "G",
            "formula": {"type": "proposition", "proposition": "safe"},
        },
    }


@pytest.mark.unit
def test_until_is_binary_under_the_coalition_and_keeps_the_guard():
    """`<<1:wallet(1, >= 5)>> p U q` is one coalition node over a binary U."""
    tree = _parse("<<1:wallet(1, >= 5)>> p U q", max_coalition=1)
    assert tree["constraints"] == [{"agent": 1, "operator": ">=", "value": 5}]
    assert tree["formula"] == {
        "type": "binary",
        "operator": "U",
        "left": {"type": "proposition", "proposition": "p"},
        "right": {"type": "proposition", "proposition": "q"},
    }


@pytest.mark.unit
@pytest.mark.parametrize("op", [">=", ">", "<=", "<", "=="])
def test_guard_takes_each_comparison(op):
    """The five comparisons parse and keep their operator."""
    tree = _parse(f"<<1:wallet(1, {op} 5)>>F q", max_coalition=1)
    assert tree["constraints"] == [{"agent": 1, "operator": op, "value": 5}]


@pytest.mark.unit
@pytest.mark.parametrize("op", ["=", "=>", "!=", "??"])
def test_guard_with_another_operator_is_rejected(op):
    """`=` is not a comparison here, and `=>` is not `>=`."""
    assert _parse(f"<<1:wallet(1, {op} 5)>>F q", max_coalition=1) is None


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["F p", "G q", "X p", "p U q"])
def test_temporal_operator_needs_a_coalition(formula):
    """Wallet_ATL has no path quantifier: a bare `F p` is not a state formula."""
    assert _parse(formula) is None


@pytest.mark.unit
def test_guard_outside_the_coalition_is_refused():
    """Agent 2 is not in <<1>>: an error that names it, where the guard used to be
    silently dropped."""
    parser = FormulaParserFactory.get_parser_instance("Wallet_ATL")
    assert parser.parse("<<1:wallet(2, >= 100)>>X goal", max_coalition=2) is None
    assert any("agent 2" in error for error in parser.errors), parser.errors
