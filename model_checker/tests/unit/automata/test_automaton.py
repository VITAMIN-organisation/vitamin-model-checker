"""Automaton: which acceptance condition a Spot automaton has, and from_ltl's normal form.

Needs Spot (`pip install spottl` on Linux, conda-forge elsewhere; no win-64 build).
"""

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import AcceptanceKind, ParityKind, ParityStyle
from model_checker.automata.automaton import Automaton


@pytest.mark.parametrize(
    ("formula", "options", "kind", "orientation"),
    [
        ("GFa & GFb", ("parity",), AcceptanceKind.BUCHI, (None, None)),
        ("FGa", ("parity",), AcceptanceKind.CO_BUCHI, (None, None)),
        (
            "FGa | GFb",
            ("parity", "deterministic"),
            AcceptanceKind.PARITY,
            (ParityKind.MIN, ParityStyle.EVEN),
        ),
    ],
)
def test_condition_kind_and_orientation(formula, options, kind, orientation):
    """GF is Büchi, FG co-Büchi, and their disjunction needs a real parity condition."""
    cond = Automaton(graph=spot.translate(formula, *options)).acceptance_condition()
    assert cond.kind is kind
    assert (cond.parity_kind, cond.parity_style) == orientation


def test_priorities_are_keyed_by_the_automatons_own_edges():
    """Each marked edge is (source, label, target) with states of this automaton."""
    aut = Automaton(graph=spot.translate("GFa & GFb", "parity"))
    priorities = aut.acceptance_condition().priorities
    assert priorities
    states = range(aut.graph.num_states())
    assert all(
        source in states and target in states for source, _, target in priorities
    )


def test_automaton_with_no_marked_edge_has_no_priorities():
    """G a never needs an acceptance mark."""
    aut = Automaton(graph=spot.translate("Ga", "parity", "deterministic"))
    assert aut.acceptance_condition().priorities == {}


def test_rabin_condition_is_refused():
    """A two-pair Rabin automaton is none of Büchi, co-Büchi or parity.

    Built by hand: every LTL formula tried that is not parity also marks an edge
    twice, which fails an earlier check instead.
    """
    graph = spot.make_twa_graph(spot.make_bdd_dict())
    graph.new_states(2)
    graph.set_init_state(0)
    graph.set_acceptance(4, "Rabin 2")
    true = spot.formula_to_bdd(spot.formula("1"), graph.get_dict(), graph)
    for source, target, color in [(0, 1, 0), (1, 0, 1), (0, 0, 2), (1, 1, 3)]:
        graph.new_edge(source, target, true, [color])
    with pytest.raises(ValueError, match="unsupported acceptance condition"):
        Automaton(graph=graph).acceptance_condition()


@pytest.mark.parametrize(
    "formula", ["GFa & GFb", "GFa | FGb", "FGa", "Ga", "GFa & GFb & GFc"]
)
def test_from_ltl_gives_a_deterministic_max_odd_parity_automaton(formula):
    """The solver expects max-odd parity whatever the formula's own shape."""
    aut = Automaton.from_ltl(formula)
    is_parity, is_max, is_odd = aut.graph.acc().is_parity()
    assert (is_parity, is_max, is_odd) == (True, True, True)
    assert aut.graph.prop_universal()
    cond = aut.acceptance_condition()
    if cond.kind is AcceptanceKind.PARITY:
        assert (cond.parity_kind, cond.parity_style) == (
            ParityKind.MAX,
            ParityStyle.ODD,
        )


def test_from_ltl_keeps_the_language():
    """Normalizing must not change which words are accepted."""
    formula = "GFa & FGb"
    assert spot.are_equivalent(
        Automaton.from_ltl(formula).graph, spot.translate(formula)
    )
