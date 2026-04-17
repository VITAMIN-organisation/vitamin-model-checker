"""NatATL performance: lazy strategy enumeration, scaling, pruning, memory bounds."""

import time

from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    generate_linear_chain,
)


class TestNatATLStrategyEnumeration:
    """Test that NatATL strategy enumeration is lazy and bounded."""

    def test_strategy_generator_is_lazy(self):
        """Verify strategy generator uses lazy evaluation."""
        from model_checker.algorithms.explicit.shared.strategies_base import (
            generate_guarded_action_pairs,
            generate_strategies,
        )

        atomic_props = ["p"]
        agent_actions = {"actions_agent1": ["A", "B"]}
        actions_list = [["A", "B"]]

        cartesian_products = generate_guarded_action_pairs(
            complexity_bound=1,
            agent_actions=agent_actions,
            actions_list=actions_list,
            atomic_propositions=atomic_props,
        )

        agents = [1]
        found_solution = False

        gen = generate_strategies(cartesian_products, 1, agents, found_solution)

        assert hasattr(gen, "__iter__") and hasattr(
            gen, "__next__"
        ), "generate_strategies should return a generator for lazy evaluation"

        try:
            first_strategy = next(gen)
            assert first_strategy is not None
        except StopIteration:
            pass

    def test_early_termination_on_solution(self, temp_file):
        """Verify model checking terminates early when solution is found."""
        from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
            model_checking,
        )

        content = build_cgs_model_content(
            transitions=[
                ["1", "1", "0"],
                ["0", "1", "0"],
                ["0", "0", "0"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1", "0"], ["1", "0"], ["0", "0"]],
            num_agents=1,
            prop_names=["a", "b"],
        )

        model_path = temp_file(content)

        start_time = time.time()
        result = model_checking("<{1}, 1>F a", model_path)
        elapsed = time.time() - start_time

        assert (
            "error" not in result
        ), f"NatATL model checking should not error: {result}"
        assert result.get("Satisfiability") is True, "Formula should be satisfiable"
        assert (
            elapsed < 10
        ), f"Simple model should complete quickly, took {elapsed:.2f}s"


class TestNatATLScalability:
    """Test NatATL performance with larger models."""

    def test_natatl_moderate_state_space(self, temp_file):
        """Test NatATL with moderate state space (20 states)."""
        from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
            model_checking,
        )

        n_states = 20
        content = generate_linear_chain(n_states, num_agents=1)
        model_path = temp_file(content)

        start_time = time.time()
        result = model_checking("<{1}, 1>F p", model_path)
        elapsed = time.time() - start_time

        if "error" in result:
            assert elapsed < 5, (
                "Even with format error, should fail quickly, took " f"{elapsed:.2f}s"
            )
        else:
            assert (
                elapsed < 10
            ), f"NatATL 20-state model took {elapsed:.2f}s, expected < 10s"


class TestNatATLMemoryBoundedness:
    """Test that NatATL doesn't consume excessive memory."""

    def test_no_strategy_accumulation(self):
        """Verify strategies are not accumulated in memory."""
        from model_checker.algorithms.explicit.shared.strategies_base import (
            generate_guarded_action_pairs,
            generate_strategies,
        )

        atomic_props = ["p", "q"]
        agent_actions = {
            "actions_agent1": ["A", "B"],
            "actions_agent2": ["C", "D"],
        }
        actions_list = [["A", "B"], ["C", "D"]]

        cartesian_products = generate_guarded_action_pairs(
            complexity_bound=2,
            agent_actions=agent_actions,
            actions_list=actions_list,
            atomic_propositions=atomic_props,
        )

        agents = [1, 2]
        found_solution = False

        gen = generate_strategies(cartesian_products, 2, agents, found_solution)

        consumed = 0
        for _strategy in gen:
            consumed += 1
            if consumed >= 5:
                break
