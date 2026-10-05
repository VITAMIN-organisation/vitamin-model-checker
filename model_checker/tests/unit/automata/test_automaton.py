"""Tests for Automaton.acceptance_condition(), backed by real Spot automata.

Requires Spot: `pip install spottl` on Linux, or conda-forge elsewhere (see
docs/ATL_STAR/algorithm.md) — Spot has no win-64 build either way, so run
from WSL on Windows. Skipped entirely if spot isn't importable.
"""

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import AcceptanceKind, ParityKind, ParityStyle
from model_checker.automata.automaton import Automaton


def test_buchi_formula_classifies_as_buchi():
    aut = Automaton(graph=spot.translate("GFa & GFb", "parity"))
    cond = aut.acceptance_condition()
    assert cond.kind is AcceptanceKind.BUCHI
    assert cond.parity_kind is None
    assert cond.parity_style is None
    # priorities are keyed by the raw automaton's own (state, label, state)
    # edges, not by any product/TS transition
    assert cond.priorities
    for source, _label, target in cond.priorities:
        assert 0 <= source < aut.graph.num_states()
        assert 0 <= target < aut.graph.num_states()


def test_acceptance_condition_priorities_omit_unmarked_edges():
    # a self-loop that can never contribute to acceptance (e.g. "Ga") should
    # produce no marked edges at all
    aut = Automaton(graph=spot.translate("Ga", "parity", "deterministic"))
    cond = aut.acceptance_condition()
    assert cond.priorities == {}


def test_genuine_parity_formula_classifies_with_orientation():
    # needs real parity (generalized-Streett 1 1), not Büchi/co-Büchi
    aut = Automaton(graph=spot.translate("FGa | GFb", "parity", "deterministic"))
    cond = aut.acceptance_condition()
    assert cond.kind is AcceptanceKind.PARITY
    assert cond.parity_kind is ParityKind.MIN
    assert cond.parity_style is ParityStyle.EVEN


def test_co_buchi_formula_classifies_as_co_buchi():
    aut = Automaton(graph=spot.translate("FGa", "parity"))
    cond = aut.acceptance_condition()
    assert cond.kind is AcceptanceKind.CO_BUCHI
    assert cond.parity_kind is None
    assert cond.parity_style is None


def test_acceptance_condition_rejects_unsupported_shapes():
    # A genuine 2-pair Rabin condition is neither Büchi, co-Büchi, nor
    # parity-classifiable. Built directly rather than via an LTL formula:
    # every LTL shape tried that fails is_parity() also marks some edge with
    # more than one color, tripping priority_from_mark's guard first, this
    # isolates the "unsupported" branch from that other, separately-tested
    # guard.
    aut_graph = spot.make_twa_graph(spot.make_bdd_dict())
    aut_graph.new_states(2)
    aut_graph.set_init_state(0)
    aut_graph.set_acceptance(4, "Rabin 2")
    true_cond = spot.formula_to_bdd(spot.formula("1"), aut_graph.get_dict(), aut_graph)
    aut_graph.new_edge(0, 1, true_cond, [0])
    aut_graph.new_edge(1, 0, true_cond, [1])
    aut_graph.new_edge(0, 0, true_cond, [2])
    aut_graph.new_edge(1, 1, true_cond, [3])

    aut = Automaton(graph=aut_graph)
    with pytest.raises(ValueError, match="unsupported acceptance condition"):
        aut.acceptance_condition()


def test_acceptance_condition_requires_spot_graph():
    # a plain object without .acc() should fail loudly, not silently misclassify
    aut = Automaton(graph=object())
    with pytest.raises(AttributeError):
        aut.acceptance_condition()


def test_acceptance_condition_requires_spot():
    import model_checker.automata.automaton as automaton_module

    original_spot = automaton_module.spot
    automaton_module.spot = None
    try:
        with pytest.raises(ImportError):
            Automaton(graph=object()).acceptance_condition()
    finally:
        automaton_module.spot = original_spot


@pytest.mark.parametrize("formula", ["GFa & GFb", "GFa | FGb", "FGa", "Ga", "GFa & GFb & GFc"])
def test_from_ltl_always_returns_max_odd_deterministic_parity(formula):
    # translate(f, "parity", "deterministic") alone doesn't guarantee
    # max-odd, from_ltl must normalize regardless of the formula shape
    aut = Automaton.from_ltl(formula)
    is_parity, is_max, is_odd = aut.graph.acc().is_parity()
    assert (is_parity, is_max, is_odd) == (True, True, True)
    assert aut.graph.prop_universal()


def test_from_ltl_preserves_language():
    formula = "GFa & FGb"
    aut = Automaton.from_ltl(formula)
    assert spot.are_equivalent(aut.graph, spot.translate(formula))


def test_from_ltl_classifies_as_parity_with_max_odd_orientation():
    aut = Automaton.from_ltl("GFa & GFb & GFc")
    cond = aut.acceptance_condition()
    assert cond.kind is AcceptanceKind.PARITY
    assert cond.parity_kind is ParityKind.MAX
    assert cond.parity_style is ParityStyle.ODD


def test_from_ltl_requires_spot():
    import model_checker.automata.automaton as automaton_module

    original_spot = automaton_module.spot
    automaton_module.spot = None
    try:
        with pytest.raises(ImportError):
            Automaton.from_ltl("GFa")
    finally:
        automaton_module.spot = original_spot
