"""LTL performance: complexity scaling, Nash equilibrium bounds, strategy enumeration time."""

import time


class TestLTLComplexityBounds:
    """Test LTL performance with varying complexity bounds."""

    def test_ltl_complexity_scaling(self, cgs_simple_parser):
        """Test LTL performance scales with complexity bound."""
        from model_checker.algorithms.explicit.LTL.LTL import (
            model_checking,
        )

        full_path = cgs_simple_parser.filename

        start_time = time.time()
        result = model_checking("Fp", full_path)
        elapsed = time.time() - start_time

        assert "error" not in result, f"LTL model checking should not error: {result}"
        assert (
            elapsed < 10.0
        ), f"LTL model checking took {elapsed:.2f}s, expected < 10s for small model"


class TestLTLNashEquilibrium:
    """Test Nash equilibrium checking performance."""

    def test_nash_deviation_check_bounded(self, test_data_dir):
        """Verify Nash deviation checking doesn't explode."""
        from model_checker.algorithms.explicit.LTL.strategies import (
            generate_guarded_action_pairs,
        )
        from model_checker.algorithms.explicit.shared.strategies_base import (
            generate_strategies,
        )

        atomic_props = ["p", "q"]
        agent_actions = {
            "actions_agent1": ["A", "B"],
            "actions_agent2": ["C", "D"],
        }
        actions_list = [["A", "B"], ["C", "D"]]

        start_time = time.time()

        cartesian_products = generate_guarded_action_pairs(
            k=2,
            agent_actions=agent_actions,
            actions_list=actions_list,
            atomic_propositions=atomic_props,
        )

        agents = [1, 2]
        found_solution = False

        gen = generate_strategies(cartesian_products, 2, agents, found_solution)
        count = 0
        for _ in gen:
            count += 1
            if count >= 10:
                break

        elapsed = time.time() - start_time

        assert elapsed < 5, f"Strategy generation should be fast: {elapsed}s"


class TestLTLFormulaTransformation:
    """Test LTL to CTL transformation performance."""

    def test_formula_parsing_performance(self):
        """Verify LTL formula parsing is efficient."""
        from model_checker.parsers.formula_parser_factory import (
            FormulaParserFactory,
        )

        parser = FormulaParserFactory.get_parser_instance("LTL")

        formulas = [
            "Fp",
            "Gp",
            "F(p && q)",
            "G(p -> Fq)",
            "F(G(p || q))",
        ]

        start_time = time.time()
        for formula in formulas:
            result = parser.parse(formula)
            assert result is not None, f"Should parse: {formula}"

        elapsed = time.time() - start_time

        assert elapsed < 1, f"Parsing should be fast: {elapsed}s"
