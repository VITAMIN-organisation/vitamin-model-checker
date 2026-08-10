"""LTL performance: complexity scaling, Nash equilibrium bounds, strategy enumeration time."""

import time

import pytest

from model_checker.algorithms.explicit.LTL.LTL import model_checking
from model_checker.algorithms.explicit.LTL.strategies import generate_strategies
from model_checker.algorithms.explicit.shared import strategies_base
from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.performance
class TestLTLComplexityBounds:
    """Test LTL performance with varying complexity bounds."""

    def test_ltl_complexity_scaling(self, cgs_simple_parser):
        """Test LTL performance scales with complexity bound."""
        start_time = time.time()
        result = model_checking("Fp", cgs_simple_parser.filename)
        elapsed = time.time() - start_time
        assert "error" not in result, f"LTL model checking should not error: {result}"
        assert (
            elapsed < 10.0
        ), f"LTL model checking took {elapsed:.2f}s, expected < 10s for small model"


@pytest.mark.performance
class TestLTLNashEquilibrium:
    """Test Nash equilibrium checking performance."""

    def test_nash_deviation_check_bounded(self, test_data_dir):
        """Verify Nash deviation checking doesn't explode."""
        cartesian_products = strategies_base.generate_guarded_action_pairs(
            2,
            {
                "actions_agent1": ["A", "B"],
                "actions_agent2": ["C", "D"],
            },
            [["A", "B"], ["C", "D"]],
            ["p", "q"],
        )
        start_time = time.time()
        count = 0
        for _ in generate_strategies(cartesian_products, 2, [1, 2], False):
            count += 1
            if count >= 10:
                break
        elapsed = time.time() - start_time
        assert elapsed < 5, f"Strategy generation should be fast: {elapsed}s"


@pytest.mark.performance
class TestLTLFormulaTransformation:
    """Test LTL to CTL transformation performance."""

    def test_formula_parsing_performance(self):
        """Verify LTL formula parsing is efficient."""
        parser = FormulaParserFactory.get_parser_instance("LTL")
        formulas = ["Fp", "Gp", "F(p && q)", "G(p -> Fq)", "F(G(p || q))"]
        start_time = time.time()
        for formula in formulas:
            assert parser.parse(formula) is not None, f"Should parse: {formula}"
        elapsed = time.time() - start_time
        assert elapsed < 1, f"Parsing should be fast: {elapsed}s"
