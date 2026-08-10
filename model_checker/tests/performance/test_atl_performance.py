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
        seed = target_states.copy()
        step = lambda T: target_states.union(pre(cgs, coalition, T))
    elif operator == "G":
        seed = set(cgs.states)
        step = lambda T: target_states.intersection(pre(cgs, coalition, T))
    else:
        return None, 0

    T = seed
    iterations = 0
    while True:
        new_T = step(T)
        if new_T == T:
            break
        T = new_T
        iterations += 1
    return T, iterations


def _model_content_for_layout(layout, num_states, num_agents, **kwargs):
    if layout == "linear":
        return generate_linear_chain(
            num_states, num_agents, action_label="AC", **kwargs
        )
    if layout == "cycle":
        return generate_cycle_model(num_states, num_agents)
    raise ValueError(f"Unknown layout: {layout}")


# num_states, num_agents, layout, formula, max_time, model_kwargs, min_states, exact_all
ATL_PERFORMANCE_CASES = [
    (100, 2, "linear", "<1>F p", 10.0, None, 1, False),
    (100, 2, "cycle", "<1>G p", 10.0, None, 1, False),
    (100, 2, "linear", "<1>X p", 5.0, None, 0, False),
    (
        100,
        2,
        "linear",
        "<1>(p U q)",
        10.0,
        {"prop_names": ["p", "q"], "dense_p": True},
        None,
        True,
    ),
    (100, 3, "linear", "<1,2>F p", 15.0, None, 1, False),
    (200, 2, "linear", "<1>F p", 20.0, None, 1, False),
]

ATL_FIXPOINT_CASES = [
    ("linear", 100, "1", "F", "ends"),
    ("cycle", 100, "1", "G", "all"),
]


def _fixpoint_targets(kind, num_states):
    if kind == "ends":
        return {"s0", f"s{num_states - 1}"}
    if kind == "all":
        return {f"s{i}" for i in range(num_states)}
    raise ValueError(f"Unknown target kind: {kind}")


@pytest.mark.performance
@pytest.mark.model_checking
class TestATLPerformanceLargeModels:
    """Performance tests for ATL operators with large state spaces."""

    @pytest.mark.parametrize(
        "num_states,num_agents,layout,formula,max_time,model_kwargs,min_states,exact_all",
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
        self,
        temp_file,
        num_states,
        num_agents,
        layout,
        formula,
        max_time,
        model_kwargs,
        min_states,
        exact_all,
    ):
        """ATL operators complete within time bound."""
        kwargs = model_kwargs or {}
        parser = load_cgs_from_content(
            temp_file,
            _model_content_for_layout(layout, num_states, num_agents, **kwargs),
        )
        states, _ = run_model_checking_with_timeout(
            parser, _core_atl_checking, formula, max_time
        )
        if exact_all:
            assert len(states) == num_states
        else:
            assert (
                len(states) >= min_states
            ), f"{formula} should hold in at least {min_states} states"

    @pytest.mark.parametrize(
        "layout,num_states,coalition,operator,target_kind",
        ATL_FIXPOINT_CASES,
        ids=["F_linear_100", "G_cycle_100"],
    )
    def test_atl_fixpoint_convergence(
        self, temp_file, layout, num_states, coalition, operator, target_kind
    ):
        """ATL F/G fixpoints converge in at most |S| iterations."""
        parser = load_cgs_from_content(
            temp_file, _model_content_for_layout(layout, num_states, 2)
        )
        _, iterations = compute_atl_fixpoint_iterations(
            parser,
            _fixpoint_targets(target_kind, num_states),
            coalition,
            operator,
        )
        assert iterations <= num_states

    def test_atl_fixpoint_convergence_guarantee(self, temp_file):
        """Both F and G fixpoints converge in at most |S| iterations on one model."""
        num_states = 100
        parser = load_cgs_from_content(
            temp_file, generate_linear_chain(num_states, 2, action_label="AC")
        )
        target_states = _fixpoint_targets("ends", num_states)
        for op in ("F", "G"):
            _, iterations = compute_atl_fixpoint_iterations(
                parser, target_states, "1", op
            )
            assert (
                iterations <= num_states
            ), f"<1>{op} fixpoint got {iterations} iterations"

    def test_atl_pre_image_scalability(self, temp_file):
        """Pre-image computation scales with state space."""
        num_states = 150
        parser = load_cgs_from_content(
            temp_file, generate_linear_chain(num_states, 2, action_label="AC")
        )
        target_states = {f"s{i}" for i in range(num_states // 2, num_states)}
        start_time = time.time()
        pre_result = pre(parser, "1", target_states)
        elapsed_time = time.time() - start_time
        assert isinstance(pre_result, set)
        assert elapsed_time < 5.0, f"Pre-image took {elapsed_time:.2f}s"
