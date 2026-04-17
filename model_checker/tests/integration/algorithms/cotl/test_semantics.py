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
    """Semantic invariants for COTL operators (F, G, X, U)."""

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

    def test_until_operator_returns_state_set(self, cotl_model_path):
        """<C><k> phi U psi runs without error and returns a state set."""
        atoms = h.atomic_propositions(cotl_model_path)
        if len(atoms) < 2:
            pytest.skip("Model needs at least two propositions for U")
        p, q = atoms[0], atoms[1]
        _, sat_u = h.check_and_get_states(f"<1><5>{p} U {q}", cotl_model_path)
        assert sat_u is not None
        parser = h.load_cotl_parser_from_file(cotl_model_path)
        all_states = {
            parser.get_state_name_by_index(i) for i in range(len(parser.states))
        }
        assert sat_u <= all_states

    def test_release_operator_returns_state_set(self, cotl_model_path):
        """<C><k> phi R psi runs without error and returns a state set."""
        atoms = h.atomic_propositions(cotl_model_path)
        if len(atoms) < 2:
            pytest.skip("Model needs at least two propositions for R")
        p, q = atoms[0], atoms[1]
        _, sat_r = h.check_and_get_states(f"<1><5>{p} R {q}", cotl_model_path)
        assert sat_r is not None
        parser = h.load_cotl_parser_from_file(cotl_model_path)
        all_states = {
            parser.get_state_name_by_index(i) for i in range(len(parser.states))
        }
        assert sat_r <= all_states

    def test_weak_operator_returns_state_set(self, cotl_model_path):
        """<C><k> phi W psi runs without error and returns a state set."""
        atoms = h.atomic_propositions(cotl_model_path)
        if len(atoms) < 2:
            pytest.skip("Model needs at least two propositions for W")
        p, q = atoms[0], atoms[1]
        _, sat_w = h.check_and_get_states(f"<1><5>{p} W {q}", cotl_model_path)
        assert sat_w is not None
        parser = h.load_cotl_parser_from_file(cotl_model_path)
        all_states = {
            parser.get_state_name_by_index(i) for i in range(len(parser.states))
        }
        assert sat_w <= all_states
