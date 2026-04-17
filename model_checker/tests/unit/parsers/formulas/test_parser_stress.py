"""Parser stress tests: long formulas, deep nesting, many propositions."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
@pytest.mark.parser
class TestFormulaParserStress:
    """Stress-test shared formula parsers with long and deeply nested inputs."""

    @pytest.mark.parametrize("logic_type", ["CTL", "ATL", "LTL"])
    def test_long_repeated_until_formula(self, logic_type):
        """Parse a long formula with many repeated temporal operators."""
        parser = FormulaParserFactory.get_parser_instance(logic_type)
        if logic_type == "CTL":
            # CTL requires a path quantifier to scope temporal operators.
            base = "E[p U q]"
        elif logic_type == "ATL":
            # ATL requires a coalition to scope temporal operators.
            base = "<1>(p U q)"
        else:
            base = "p U q"
        # Build a long right-associated chain
        formula = " and ".join([base] * 50)
        kwargs = {"n_agent": 2} if logic_type == "ATL" else {}
        result = parser.parse(formula, **kwargs)
        assert result is not None

    @pytest.mark.parametrize("logic_type", ["CTL"])
    def test_deeply_nested_next_and_globally(self, logic_type):
        """Parse a deeply nested combination of X/G (or EX/EG) operators without crashing."""
        parser = FormulaParserFactory.get_parser_instance(logic_type)
        depth = 30
        inner = "p"
        for _ in range(depth):
            inner = f"EX ({inner})"
        formula = f"EF ({inner})"
        result = parser.parse(formula)
        assert result is not None
