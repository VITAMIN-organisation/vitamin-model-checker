"""COTL model checking: exact state-set on example model, error handling.

Semantic invariants (F contains phi-states, G subset of phi-states, etc.)
live in test_semantics.py.
"""

import pytest

from model_checker.algorithms.explicit.COTL.COTL import model_checking
from model_checker.tests.integration.algorithms.cotl import (
    cotl_test_helpers as h,
)

CORRECTNESS_CASES = [
    ("example", "<1><5>F g", {"s0", "s2", "s3", "s4", "s5"}, True),
]


@pytest.mark.integration
@pytest.mark.model_checking
class TestCOTLErrorHandling:
    """COTL must reject invalid inputs with appropriate errors."""

    def test_invalid_formula_syntax(self, cotl_model_path):
        """Invalid formula yields an error (syntax or in result message)."""
        result = model_checking("INVALID_FORMULA", str(cotl_model_path))
        assert "error" in result or "syntax" in result.get("res", "").lower()


@pytest.mark.integration
@pytest.mark.model_checking
class TestCOTLCorrectness:
    """Exact state-set correctness on example COTL model."""

    @pytest.mark.parametrize(
        "model_id, formula, expected_states, initial_expected",
        CORRECTNESS_CASES,
    )
    def test_exact_state_sets(
        self,
        model_id,
        formula,
        expected_states,
        initial_expected,
        cotl_model_path,
    ):
        """Model checker returns the exact expected state set for each model."""
        path = cotl_model_path
        result, states = h.check_and_get_states(formula, path)
        assert (
            states == expected_states
        ), f"{model_id} {formula}: expected {expected_states}, got {states}"
        s0 = h.initial_state_name_from_path(path)
        assert (s0 in states) is initial_expected


@pytest.mark.integration
@pytest.mark.model_checking
class TestCOTLDeterminism:
    """Assert COTL output is deterministic (state_set_to_str uses sorted order); regression guard against str(set) or other non-deterministic serialization."""

    def test_same_formula_same_model_produces_identical_result(self, cotl_model_path):
        """Running the same formula on the same model multiple times yields identical state sets."""
        formula = "<1><5>F g"
        path = str(cotl_model_path)
        state_sets = []
        for _ in range(10):
            result = model_checking(formula, path)
            assert "error" not in result
            state_sets.append(h.result_states(result))
        first = state_sets[0]
        for i, st in enumerate(state_sets[1:], start=1):
            assert st == first, f"Run {i + 1} produced {st}, expected {first}"
