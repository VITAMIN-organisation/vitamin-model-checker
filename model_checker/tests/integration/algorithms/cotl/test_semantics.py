"""COTL semantic tests: invariants that hold for any cost-bounded coalition model.

Tests assert universal laws (e.g. Sat(F phi) contains phi-states, result subset of S)
rather than exact state sets. One fixture model is used; invariants are model-agnostic.
Shared helpers and fixture live in cotl_test_helpers and conftest.
"""

import pytest

from model_checker.tests.integration.algorithms.cotl import (
    cotl_test_helpers as h,
)


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestCOTLSemantics:
    """Semantic invariants for COTL operators (F, G)."""

    def test_eventually_contains_phi_states(self, cotl_model_path):
        """Sat(<C><k>F phi) contains every state where phi holds (any model, any atom)."""
        atoms = h.atomic_propositions(cotl_model_path)
        if not atoms:
            pytest.skip("Model has no atomic propositions")
        for prop in atoms:
            _, sat_f = h.check_and_get_states(f"<1><5>F {prop}", cotl_model_path)
            phi_states = h.states_where_prop_holds(cotl_model_path, prop)
            assert phi_states <= sat_f, (
                f"F {prop}: states where {prop} holds {phi_states} "
                f"must be contained in result {sat_f}"
            )

    def test_globally_subset_of_phi_states(self, cotl_model_path):
        """Sat(<C><k>G phi) is a subset of states where phi holds (any model, any atom)."""
        atoms = h.atomic_propositions(cotl_model_path)
        if not atoms:
            pytest.skip("Model has no atomic propositions")
        prop = atoms[0]
        _, sat_g = h.check_and_get_states(f"<1><3>G {prop}", cotl_model_path)
        phi_states = h.states_where_prop_holds(cotl_model_path, prop)
        assert (
            sat_g <= phi_states
        ), f"G {prop} result {sat_g} must be subset of {prop}-states {phi_states}"
