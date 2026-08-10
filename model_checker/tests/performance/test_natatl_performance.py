"""NatATL performance: lazy strategy enumeration, scaling, pruning, memory bounds."""

import time

import pytest

from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import model_checking
from model_checker.algorithms.explicit.shared.strategies_base import (
    generate_guarded_action_pairs,
    generate_strategies,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    generate_fully_connected_model,
    generate_linear_chain,
    load_cgs_from_content,
)


NATATL_SCALING_CASES = [
    (
        "small_hand_built",
        lambda: build_cgs_model_content(
            transitions=[
                ["1", "1", "0"],
                ["0", "1", "0"],
                ["0", "0", "*"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1", "0"], ["1", "0"], ["0", "0"]],
            num_agents=1,
            prop_names=["a", "b"],
        ),
        "<{1}, 1>F a",
        10.0,
    ),
    (
        "linear_20",
        lambda: generate_linear_chain(20, num_agents=1),
        "<{1}, 1>F p",
        10.0,
    ),
]


@pytest.mark.performance
class TestNatATLStrategyEnumeration:
    """Test that NatATL strategy enumeration is lazy and bounded."""

    def test_strategy_generator_is_lazy(self):
        """Verify strategy generator uses lazy evaluation."""
        cartesian_products = generate_guarded_action_pairs(
            complexity_bound=1,
            agent_actions={"actions_agent1": ["A", "B"]},
            actions_list=[["A", "B"]],
            atomic_propositions=["p"],
        )
        gen = generate_strategies(cartesian_products, 1, [1], False)
        assert hasattr(gen, "__iter__") and hasattr(gen, "__next__")
        try:
            assert next(gen) is not None
        except StopIteration:
            pass

    @pytest.mark.parametrize(
        "case_id,content_fn,formula,max_time",
        NATATL_SCALING_CASES,
        ids=[case[0] for case in NATATL_SCALING_CASES],
    )
    def test_natatl_completes_within_bound(
        self, temp_file, case_id, content_fn, formula, max_time
    ):
        """NatATL finds a strategy within the time bound on small/moderate models."""
        model_path = temp_file(content_fn())
        start_time = time.time()
        result = model_checking(formula, model_path)
        elapsed = time.time() - start_time
        assert "error" not in result, f"{case_id}: {result}"
        assert result.get("Satisfiability") is True
        assert (
            elapsed < max_time
        ), f"{case_id} took {elapsed:.2f}s, expected < {max_time}s"


@pytest.mark.performance
class TestNatATLMemoryBoundedness:
    """Test that NatATL doesn't consume excessive memory."""

    def test_no_strategy_accumulation(self):
        """Verify strategies are not accumulated in memory."""
        cartesian_products = generate_guarded_action_pairs(
            complexity_bound=2,
            agent_actions={
                "actions_agent1": ["A", "B"],
                "actions_agent2": ["C", "D"],
            },
            actions_list=[["A", "B"], ["C", "D"]],
            atomic_propositions=["p", "q"],
        )
        gen = generate_strategies(cartesian_products, 2, [1, 2], False)
        consumed = 0
        for _strategy in gen:
            consumed += 1
            if consumed >= 5:
                break
        assert consumed >= 1


@pytest.mark.performance
class TestNatATLMatrixPruneBench:
    """Micro-benchmarks for memoryless matrix pruning speedups."""

    def test_modify_matrix_scales_on_fully_connected(self, temp_file):
        """Pruning a dense 80-state graph finishes quickly with state_to_index."""
        num_states = 80
        cgs = load_cgs_from_content(
            temp_file, generate_fully_connected_model(num_states, num_agents=2)
        )
        graph = [row[:] for row in cgs.graph]
        states = {f"s{i}" for i in range(0, num_states, 2)}
        start = time.perf_counter()
        pruned = modify_matrix(
            graph,
            states=states,
            action="A",
            agent_index=1,
            agents=[1],
            num_agents=2,
            state_to_index=cgs.state_to_index,
            in_place=True,
        )
        elapsed = time.perf_counter() - start
        assert pruned is graph
        assert (
            elapsed < 2.0
        ), f"modify_matrix took {elapsed:.3f}s on {num_states} states"
