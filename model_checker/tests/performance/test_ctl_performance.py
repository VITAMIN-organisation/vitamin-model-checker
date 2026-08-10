"""CTL performance: large state spaces, linear/cyclic/fully-connected graphs, fixpoint and pre-image."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import _core_ctl_checking
from model_checker.algorithms.explicit.CTL.preimage import pre_image_exist
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    generate_cycle_model,
    generate_fully_connected_model,
    generate_linear_chain,
    generate_sparse_graph_model,
    load_cgs_from_content,
)
from model_checker.tests.performance.performance_helpers import (
    run_model_checking_with_timeout,
)


def compute_fixpoint_iterations(cgs, target_states, operator="EF"):
    """Compute fixpoint iterations for tracking convergence.

    Args:
        operator: CTL operator ("EF", "EG", "AF", "AG")
    """
    edges = cgs.get_edges()
    all_states = set(cgs.states)

    if operator == "EF":
        seed = target_states.copy()
        step = lambda T: T.union(pre_image_exist(edges, T))
        invert = False
    elif operator == "EG":
        seed = all_states.copy()
        step = lambda T: target_states.intersection(pre_image_exist(edges, T))
        invert = False
    elif operator == "AF":
        not_target = all_states - target_states
        seed = all_states.copy()
        step = lambda T: not_target.intersection(pre_image_exist(edges, T))
        invert = True
    elif operator == "AG":
        not_target = all_states - target_states
        seed = not_target.copy()
        step = lambda T: T.union(pre_image_exist(edges, T))
        invert = True
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
    return (all_states - T if invert else T), iterations


def _model_content_for_ctl(layout, num_states, num_agents=2):
    """Build model content for CTL performance cases."""
    if layout == "linear":
        return generate_linear_chain(num_states, num_agents, action_label="AC")
    if layout == "cycle":
        return generate_cycle_model(num_states, num_agents)
    if layout == "fully_connected":
        return generate_fully_connected_model(num_states, num_agents)
    if layout == "linear_pq":
        return generate_linear_chain(
            num_states, num_agents, prop_names=["p", "q"], action_label="AC"
        )
    raise ValueError(f"Unknown layout: {layout}")


def _expected_states(kind, num_states):
    """Resolve an expected-state kind for a model with ``num_states`` states."""
    if kind == "all":
        return {f"s{i}" for i in range(num_states)}
    if kind == "empty":
        return set()
    if kind == "terminal":
        return {f"s{num_states - 1}"}
    if kind == "ex_linear":
        return {f"s{num_states - 2}", f"s{num_states - 1}"}
    raise ValueError(f"Unknown expected kind: {kind}")


def _fixpoint_targets(kind, num_states):
    """Resolve fixpoint seed states for a model with ``num_states`` states."""
    if kind == "ends":
        return {"s0", f"s{num_states - 1}"}
    if kind == "all":
        return {f"s{i}" for i in range(num_states)}
    raise ValueError(f"Unknown target kind: {kind}")


# layout, num_states, formula, max_time, expected_kind, fixpoint_op, fixpoint_target_kind
CTL_PERFORMANCE_CASES = [
    ("linear", 100, "EF p", 5.0, "all", "EF", "ends"),
    ("cycle", 100, "EG p", 5.0, "all", "EG", "all"),
    ("linear", 100, "AF p", 5.0, "all", "AF", "ends"),
    ("linear", 100, "AG p", 5.0, "terminal", "AG", "ends"),
    ("fully_connected", 100, "EX p", 2.0, "all", None, None),
    ("fully_connected", 100, "AX p", 2.0, "empty", None, None),
    ("linear_pq", 100, "E[p U q]", 5.0, "terminal", None, None),
    ("linear", 200, "EF p", 10.0, "all", "EF", "ends"),
]


@pytest.mark.performance
@pytest.mark.model_checking
class TestCTLPerformanceLargeModels:
    """Performance tests for CTL operators with large state spaces."""

    @pytest.mark.parametrize(
        "layout,num_states,formula,max_time,expected,fixpoint_op,target_kind",
        CTL_PERFORMANCE_CASES,
        ids=[
            "ef_linear_100",
            "eg_cycle_100",
            "af_linear_100",
            "ag_linear_100",
            "ex_fully_connected_100",
            "ax_fully_connected_100",
            "eu_linear_100",
            "ef_linear_200",
        ],
    )
    def test_ctl_operator_scales(
        self,
        temp_file,
        layout,
        num_states,
        formula,
        max_time,
        expected,
        fixpoint_op,
        target_kind,
    ):
        """CTL operators complete within time bound and match expected states."""
        parser = load_cgs_from_content(
            temp_file, _model_content_for_ctl(layout, num_states)
        )
        states, _ = run_model_checking_with_timeout(
            parser, _core_ctl_checking, formula, max_time
        )
        assert states == _expected_states(expected, num_states), (
            f"{formula} expected {_expected_states(expected, num_states)}, "
            f"got {states}"
        )
        if fixpoint_op is not None:
            _, iterations = compute_fixpoint_iterations(
                parser, _fixpoint_targets(target_kind, num_states), fixpoint_op
            )
            assert iterations <= num_states, (
                f"{fixpoint_op} fixpoint should converge in at most "
                f"{num_states} iterations, got {iterations}"
            )

    def test_sparse_graph_150_states(self, temp_file):
        """Multiple operators complete on a sparse 150-state graph."""
        parser = load_cgs_from_content(
            temp_file, generate_sparse_graph_model(150, connectivity=0.2)
        )
        for formula in ("EF p", "EG p", "AF p", "AG p", "EX p", "AX p"):
            run_model_checking_with_timeout(parser, _core_ctl_checking, formula, 10.0)

    def test_fixpoint_convergence_guarantee(self, temp_file):
        """Fixpoints converge in at most |S| iterations on a linear chain."""
        num_states = 100
        parser = load_cgs_from_content(
            temp_file, generate_linear_chain(num_states, action_label="AC")
        )
        target_states = _fixpoint_targets("ends", num_states)
        for op in ("EF", "EG", "AF", "AG"):
            _, iterations = compute_fixpoint_iterations(parser, target_states, op)
            assert iterations <= num_states, (
                f"{op} fixpoint should converge in at most {num_states} iterations, "
                f"got {iterations}"
            )

    def test_correctness_large_models(self, temp_file):
        """Linear-chain results match manually verifiable EF/EX properties."""
        num_states = 100
        parser = load_cgs_from_content(
            temp_file, generate_linear_chain(num_states, action_label="AC")
        )
        for formula, expected in (
            ("EF p", "all"),
            ("EX p", "ex_linear"),
        ):
            states = extract_states_from_result(_core_ctl_checking(parser, formula))
            assert states is not None
            assert states == _expected_states(expected, num_states), (
                f"{formula} expected {_expected_states(expected, num_states)}, "
                f"got {states}"
            )
