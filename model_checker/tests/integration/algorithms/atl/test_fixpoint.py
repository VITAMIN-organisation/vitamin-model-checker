"""ATL fixpoint: convergence and iteration bound for <A>F and <A>G."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import _core_atl_checking
from model_checker.algorithms.explicit.ATL.preimage import (
    build_transition_cache,
    pre,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result


def compute_atl_f_fixpoint_iterations(cgs, coalition, target_states):
    """Compute <A>F fixpoint (least fixpoint) with iteration tracking."""
    cache = build_transition_cache(cgs, coalition)
    T = target_states.copy()
    iterations = [T.copy()]

    while True:
        p_indices = state_names_to_indices(cgs, T)
        new_T = T | pre(cgs, coalition, T, cache, early_stop=p_indices)
        if new_T == T:
            break
        T = new_T
        iterations.append(T.copy())

    return T, iterations


def compute_atl_g_fixpoint_iterations(cgs, coalition, target_states):
    """Compute <A>G fixpoint (greatest fixpoint) with iteration tracking."""
    cache = build_transition_cache(cgs, coalition)
    all_states = set(cgs.get_states())
    T = all_states.copy()
    iterations = [T.copy()]

    while True:
        new_T = target_states & pre(cgs, coalition, T, cache)
        if new_T == T:
            break
        T = new_T
        iterations.append(T.copy())

    return T, iterations


def _states_where_prop_holds(cgs, prop):
    """Return set of state names where proposition prop holds."""
    matrix = cgs.get_matrix_proposition()
    ap = cgs.get_atomic_prop()
    if ap is None:
        return set()
    try:
        idx = list(ap).index(prop)
    except (ValueError, TypeError):
        return set()
    return {
        cgs.get_state_name_by_index(i)
        for i, row in enumerate(matrix)
        if int(row[idx]) == 1
    }


@pytest.mark.semantic
@pytest.mark.fixpoint
@pytest.mark.model_checking
class TestATLFixpointConvergence:
    """Test fixpoint convergence for ATL coalition F and G."""

    def test_atl_f_fixpoint_matches_implementation(self, cgs_simple_parser):
        """<1>F p fixpoint converges and matches _core_atl_checking result."""
        coalition = "1"
        phi_states = _states_where_prop_holds(cgs_simple_parser, "p")
        assert phi_states, "Model should have at least one state where p holds"

        final_result, iterations = compute_atl_f_fixpoint_iterations(
            cgs_simple_parser, coalition, phi_states
        )
        assert len(iterations) > 0
        assert len(iterations) <= len(cgs_simple_parser.states) + 1

        result = _core_atl_checking(cgs_simple_parser, "<1>F p")
        assert "error" not in result
        impl_states = extract_states_from_result(result)
        assert impl_states == final_result

    def test_atl_g_fixpoint_matches_implementation(self, cgs_simple_parser):
        """<1>G p fixpoint converges and matches _core_atl_checking result."""
        coalition = "1"
        phi_states = _states_where_prop_holds(cgs_simple_parser, "p")
        assert phi_states, "Model should have at least one state where p holds"

        final_result, iterations = compute_atl_g_fixpoint_iterations(
            cgs_simple_parser, coalition, phi_states
        )
        assert len(iterations) > 0
        assert len(iterations) <= len(cgs_simple_parser.states) + 1

        result = _core_atl_checking(cgs_simple_parser, "<1>G p")
        assert "error" not in result
        impl_states = extract_states_from_result(result)
        assert impl_states == final_result

    def test_atl_fixpoint_convergence_finite_steps(self, cgs_simple_parser):
        """<1>F p and <1>G p converge in at most |S|+1 iterations."""
        num_states = len(cgs_simple_parser.states)
        phi_states = _states_where_prop_holds(cgs_simple_parser, "p")
        if not phi_states:
            pytest.skip("No p-states in model")

        _, f_iterations = compute_atl_f_fixpoint_iterations(
            cgs_simple_parser, "1", phi_states
        )
        _, g_iterations = compute_atl_g_fixpoint_iterations(
            cgs_simple_parser, "1", phi_states
        )
        assert len(f_iterations) <= num_states + 1
        assert len(g_iterations) <= num_states + 1
