"""NatATL parser and conversion: canonical coalition syntax.

Tests cover:
- Capacity syntax <{A}, k>Op phi (only accepted surface form)
- Rejection of ATL-style coalitions without an explicit bound
"""

import pytest

from model_checker.algorithms.explicit.NatATL.NatATLtoCTL import (
    get_agents_from_natatl,
    get_k_value,
    natatl_to_ctl,
)
from model_checker.parsers.formulas.NatATL.parser import NatATLParser


@pytest.mark.unit
class TestNatATLParserCapacitySyntax:
    def test_parses_capacity_syntax_ast(self):
        """<{1,2}, k> must parse to an AST that retains coalition and bound in the modal."""
        parser = NatATLParser()

        capacity = "<{1,2}, 5>F p"

        ast_capacity = parser.parse(capacity, n_agent=2)

        assert ast_capacity == ("<{1,2},5>F", "p")

    def test_rejects_atl_style_coalition_without_bound(self):
        """<1,2>F p without <{...}, k> is invalid NatATL."""
        parser = NatATLParser()

        assert parser.parse("<1,2>F p", n_agent=2) is None

    def test_invalid_coalition_agent_out_of_range_rejected(self):
        """Coalitions with agent index > n_agent must be rejected."""
        parser = NatATLParser()

        # Agent 3 is out of range when n_agent=2
        formula = "<{3}, 5>F p"
        result = parser.parse(formula, n_agent=2)

        assert result is None

    def test_rejects_uppercase_prop_not_allowed_by_prechecks(self):
        """Uppercase proposition letters (beyond U/G/X/F) should fail validation."""
        parser = NatATLParser()

        # 'P' is not in the allowed uppercase set {U,G,X,F}
        formula = "<{1}, 5>F P"
        result = parser.parse(formula, n_agent=1)

        assert result is None


@pytest.mark.unit
class TestNatATLCapacityConversion:
    def test_capacity_formula_preserves_agents_and_k(self):
        """Capacity syntax must drive CTL conversion, agents, and k consistently."""
        formula = "<{1,2}, 5>F p"

        ctl = natatl_to_ctl(formula)
        agents = get_agents_from_natatl(formula)
        k = get_k_value(formula)

        assert ctl == "AF p"
        assert agents == [1, 2]
        assert k == 5

    def test_non_canonical_formula_rejected_by_conversion(self):
        """natatl_to_ctl and get_k_value require <{agents}, k> syntax."""
        formula = "<1,2>F p"

        with pytest.raises(ValueError):
            natatl_to_ctl(formula)
        with pytest.raises(ValueError):
            get_k_value(formula)
