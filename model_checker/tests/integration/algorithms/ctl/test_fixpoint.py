"""CTL fixpoint: convergence, iteration count, intermediate values, cycles and deadlocks (EF/AF/EG/AG)."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import _core_ctl_checking
from model_checker.algorithms.explicit.CTL.preimage import pre_image_exist
from model_checker.tests.helpers.model_helpers import extract_states_from_result


def compute_ef_fixpoint_iterations(cgs, target_states):
    """
    Compute EF fixpoint with iteration tracking.

    EF phi = least fixpoint: T = phi union EX T
    Returns: (final_result, iterations_list)
    """
    T = target_states.copy()
    iterations = [T.copy()]
    edges = cgs.get_edges()

    while True:
        new_T = T.union(pre_image_exist(edges, T))
        if new_T == T:
            break
        T = new_T
        iterations.append(T.copy())

    return T, iterations


def compute_eg_fixpoint_iterations(cgs, target_states):
    """
    Compute EG fixpoint with iteration tracking.

    EG phi = greatest fixpoint: T = phi intersect EX T
    Returns: (final_result, iterations_list)
    """
    all_states = set(cgs.states)
    T = all_states.copy()  # Start with all states (greatest fixpoint)
    iterations = [T.copy()]
    edges = cgs.get_edges()

    while True:
        new_T = target_states.intersection(pre_image_exist(edges, T))
        if new_T == T:
            break
        T = new_T
        iterations.append(T.copy())

    return T, iterations


def compute_af_fixpoint_iterations(cgs, target_states):
    """
    Compute AF fixpoint with iteration tracking.

    AF phi = not EG(not phi)
    Returns: (final_result, iterations_list)
    """
    all_states = set(cgs.states)
    not_target = all_states - target_states
    eg_result, iterations = compute_eg_fixpoint_iterations(cgs, not_target)
    af_result = all_states - eg_result
    return af_result, iterations


def compute_ag_fixpoint_iterations(cgs, target_states):
    """
    Compute AG fixpoint with iteration tracking.

    AG phi = not EF(not phi)
    Returns: (final_result, iterations_list)
    """
    all_states = set(cgs.states)
    not_target = all_states - target_states
    ef_result, iterations = compute_ef_fixpoint_iterations(cgs, not_target)
    ag_result = all_states - ef_result
    return ag_result, iterations


@pytest.mark.semantic
@pytest.mark.fixpoint
@pytest.mark.model_checking
class TestCTLFixpointConvergence:
    """Test fixpoint convergence for CTL operators."""

    @pytest.mark.parametrize(
        "operator,formula,compute_fn,expected_final,expected_iterations,monotonicity",
        [
            (
                "EF",
                "EF p",
                compute_ef_fixpoint_iterations,
                {"s0", "s1", "s2", "s3"},
                [
                    {"s0", "s3"},
                    {"s0", "s1", "s2", "s3"},
                ],
                "increasing",
            ),
            (
                "EG",
                "EG p",
                compute_eg_fixpoint_iterations,
                {"s3"},
                [
                    {"s0", "s1", "s2", "s3"},
                    {"s0", "s3"},
                    {"s3"},
                ],
                "decreasing",
            ),
        ],
    )
    def test_fixpoint_convergence_simple(
        self,
        cgs_simple_parser,
        operator,
        formula,
        compute_fn,
        expected_final,
        expected_iterations,
        monotonicity,
    ):
        """Table-driven convergence checks on the simple model."""
        target = {"s0", "s3"}  # States where p holds in the simple model

        final_result, iterations = compute_fn(cgs_simple_parser, target)

        assert len(iterations) > 0, f"{operator} should have at least one iteration"

        if expected_iterations is not None:
            assert iterations[: len(expected_iterations)] == expected_iterations, (
                f"{operator} iterations mismatch: expected {expected_iterations}, "
                f"got {iterations}"
            )

        if monotonicity == "increasing":
            for i in range(len(iterations) - 1):
                assert iterations[i].issubset(iterations[i + 1]), (
                    f"{operator} fixpoint should be monotonic increasing: "
                    f"iteration {i} = {iterations[i]}, iteration {i + 1} = {iterations[i + 1]}"
                )
        elif monotonicity == "decreasing":
            for i in range(len(iterations) - 1):
                assert iterations[i].issuperset(iterations[i + 1]), (
                    f"{operator} fixpoint should be monotonic decreasing: "
                    f"iteration {i} = {iterations[i]}, iteration {i + 1} = {iterations[i + 1]}"
                )

        result = _core_ctl_checking(cgs_simple_parser, formula)
        impl_states = extract_states_from_result(result)
        assert impl_states == final_result, (
            f"{operator} implementation result {impl_states} doesn't match "
            f"fixpoint computation {final_result}"
        )

        assert (
            final_result == expected_final
        ), f"{operator} expected final states {expected_final}, got {final_result}"

    def test_fixpoint_convergence_finite_steps(self, cgs_simple_parser):
        """Test that all fixpoints converge in finite steps.

        This is a fundamental property: fixpoints must converge in at most |S| iterations
        where |S| is the number of states.
        """
        num_states = len(cgs_simple_parser.states)
        target = {"s0", "s3"}

        _, ef_iterations = compute_ef_fixpoint_iterations(cgs_simple_parser, target)
        _, eg_iterations = compute_eg_fixpoint_iterations(cgs_simple_parser, target)
        _, af_iterations = compute_af_fixpoint_iterations(cgs_simple_parser, target)
        _, ag_iterations = compute_ag_fixpoint_iterations(cgs_simple_parser, target)

        assert len(ef_iterations) <= num_states + 1, (
            f"EF fixpoint should converge in at most {num_states + 1} iterations, "
            f"got {len(ef_iterations)}"
        )
        assert len(eg_iterations) <= num_states + 1, (
            f"EG fixpoint should converge in at most {num_states + 1} iterations, "
            f"got {len(eg_iterations)}"
        )
        assert len(af_iterations) <= num_states + 1, (
            f"AF fixpoint should converge in at most {num_states + 1} iterations, "
            f"got {len(af_iterations)}"
        )
        assert len(ag_iterations) <= num_states + 1, (
            f"AG fixpoint should converge in at most {num_states + 1} iterations, "
            f"got {len(ag_iterations)}"
        )
