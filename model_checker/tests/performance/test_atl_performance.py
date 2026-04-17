"""ATL performance: large state spaces, correctness, convergence, coalition pre-image."""

import time

import pytest

from model_checker.algorithms.explicit.ATL.ATL import (
    _core_atl_checking,
)
from model_checker.algorithms.explicit.ATL.preimage import pre
from model_checker.tests.helpers.model_helpers import (
    generate_cycle_model,
    generate_linear_chain,
    load_cgs_from_content,
)
from model_checker.tests.performance.performance_helpers import (
    run_model_checking_with_timeout,
)


def compute_atl_fixpoint_iterations(cgs, target_states, coalition, operator="F"):
    """Compute ATL fixpoint iterations for convergence checks."""
    if operator == "F":
        T = target_states.copy()
        iterations = 0
        while True:
            pre_result = pre(cgs, coalition, T)
            new_T = target_states.union(pre_result)
            if new_T == T:
                break
            T = new_T
            iterations += 1
        return T, iterations
    if operator == "G":
        all_states = set(cgs.states)
        T = all_states.copy()
        iterations = 0
        while True:
            pre_result = pre(cgs, coalition, T)
            new_T = target_states.intersection(pre_result)
            if new_T == T:
                break
            T = new_T
            iterations += 1
        return T, iterations
    return None, 0


def _model_content_for_layout(layout, num_states, num_agents, **kwargs):
    if layout == "linear":
        return generate_linear_chain(
            num_states, num_agents, action_label="AC", **kwargs
        )
    if layout == "cycle":
        return generate_cycle_model(num_states, num_agents)
    raise ValueError(f"Unknown layout: {layout}")


ATL_PERFORMANCE_CASES = [
    (100, 2, "linear", "<1>F p", 10.0, None),
    (100, 2, "cycle", "<1>G p", 10.0, None),
    (100, 2, "linear", "<1>X p", 5.0, None),
    (100, 2, "linear", "<1>(p U q)", 10.0, {"prop_names": ["p", "q"], "dense_p": True}),
    (100, 3, "linear", "<1,2>F p", 15.0, None),
    (200, 2, "linear", "<1>F p", 20.0, None),
]


@pytest.mark.performance
@pytest.mark.model_checking
class TestATLPerformanceLargeModels:
    """Performance tests for ATL operators with large state spaces."""

    @pytest.mark.parametrize(
        "num_states,num_agents,layout,formula,max_time,model_kwargs",
        ATL_PERFORMANCE_CASES,
        ids=[
            "F_linear_100",
            "G_cycle_100",
            "X_linear_100",
            "U_linear_100",
            "multi_agent_100",
            "F_linear_200",
        ],
    )
    def test_atl_operator_scales(
        self, temp_file, num_states, num_agents, layout, formula, max_time, model_kwargs
    ):
        """ATL operators complete within time bound."""
        kwargs = model_kwargs or {}
        model_content = _model_content_for_layout(
            layout, num_states, num_agents, **kwargs
        )
        parser = load_cgs_from_content(temp_file, model_content)
        states, _ = run_model_checking_with_timeout(
            parser, _core_atl_checking, formula, max_time
        )
        assert (
            len(states) > 0 or formula == "<1>X p"
        ), "Formula should hold in some states"
        if formula == "<1>(p U q)":
            assert len(states) == num_states

    def test_atl_f_fixpoint_convergence(self, temp_file):
        """<1>F fixpoint converges in at most num_states iterations."""
        num_states, num_agents = 100, 2
        model_content = generate_linear_chain(num_states, num_agents, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)
        target_states = {"s0", f"s{num_states - 1}"}
        _, iterations = compute_atl_fixpoint_iterations(parser, target_states, "1", "F")
        assert iterations <= num_states

    def test_atl_g_fixpoint_convergence(self, temp_file):
        """<1>G fixpoint converges in at most num_states iterations."""
        num_states, num_agents = 100, 2
        model_content = generate_cycle_model(num_states, num_agents)
        parser = load_cgs_from_content(temp_file, model_content)
        target_states = {f"s{i}" for i in range(num_states)}
        _, iterations = compute_atl_fixpoint_iterations(parser, target_states, "1", "G")
        assert iterations <= num_states

    def test_atl_fixpoint_convergence_guarantee(self, temp_file):
        """ATL fixpoints converge in at most |S| iterations."""
        num_states, num_agents = 100, 2
        model_content = generate_linear_chain(num_states, num_agents, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)
        target_states = {"s0", f"s{num_states - 1}"}
        for op in ["F", "G"]:
            _, iterations = compute_atl_fixpoint_iterations(
                parser, target_states, "1", op
            )
            assert (
                iterations <= num_states
            ), f"<1>{op} fixpoint got {iterations} iterations"

    def test_atl_pre_image_scalability(self, temp_file):
        """Pre-image computation scales with state space."""
        num_states, num_agents = 150, 2
        model_content = generate_linear_chain(num_states, num_agents, action_label="AC")
        parser = load_cgs_from_content(temp_file, model_content)
        target_states = {f"s{i}" for i in range(num_states // 2, num_states)}
        start_time = time.time()
        pre_result = pre(parser, "1", target_states)
        elapsed_time = time.time() - start_time
        assert isinstance(pre_result, set)
        assert elapsed_time < 5.0, f"Pre-image took {elapsed_time:.2f}s"
