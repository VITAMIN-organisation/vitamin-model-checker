"""Tests for product(), backed by real Spot automata.
Requires Spot, see environment.yml / tests/test_automaton.py. Skipped
entirely if spot isn't importable."""

from dataclasses import replace

# ruff: noqa: E402  -- imports deliberately follow importorskip("spot") below, to skip this whole file cleanly if Spot isn't installed
import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import AcceptanceKind
from model_checker.automata.automaton import Automaton
from model_checker.automata.games.arena import concurrent_to_turnbased
from model_checker.automata.games.solver import solve
from model_checker.automata.product import complete, product
from model_checker.automata.transition_system import TransitionSystem


def _toy_system():
    ts = TransitionSystem()
    ts.add_transition("s0", frozenset({"a"}), "s1")
    ts.add_transition("s1", frozenset({"a", "b"}), "s1")
    ts.add_state("s0", initial=True)
    return ts


def test_product_pairs_states_and_only_keeps_compatible_transitions():
    automaton = Automaton(graph=spot.translate("a & Fb", "parity", "deterministic"))
    result, _ = product(automaton, _toy_system())

    aut_init = automaton.graph.get_init_state_number()
    assert result.initial_states == {("s0", aut_init)}
    # every reachable product state pairs a real ts_state with a real automaton state
    for ts_state, aut_state in result.states:
        assert ts_state in {"s0", "s1"}
        assert 0 <= aut_state < automaton.graph.num_states()
    # the self-loop on {"a","b"} keeps stepping the automaton until it's stable —
    # find that fixed point directly instead of assuming which raw state number
    # Spot assigns it, which is an implementation detail that varies by version
    s1_states = [state for state in result.states if state[0] == "s1"]
    fixed_points = [
        state
        for state in s1_states
        if result.successors(state, frozenset({"a", "b"})) == {state}
    ]
    assert len(fixed_points) == 1
    assert result.successors(fixed_points[0], frozenset({"a", "b"})) == {fixed_points[0]}


def test_product_returns_automaton_acceptance_as_objective():
    automaton = Automaton(graph=spot.translate("GFa", "parity"))
    result, objective = product(automaton, _toy_system())
    assert objective.kind is AcceptanceKind.BUCHI
    # every accepting transition is keyed exactly as the product TransitionSystem
    # keys its own transitions: (product_source, symbol, product_target)
    assert objective.priorities
    for source, symbol, target in objective.priorities:
        assert target in result.successors(source, symbol)


def test_product_priorities_only_mark_edges_the_underlying_automaton_marks():
    # "Fb" is satisfied once "b" is ever seen; only the post-"b" self-loop
    # should carry an acceptance mark, not the initial "still waiting" loop
    automaton = Automaton(graph=spot.translate("Fb", "parity", "deterministic"))
    ts = TransitionSystem()
    ts.add_transition("s0", frozenset(), "s0")
    ts.add_transition("s0", frozenset({"b"}), "s1")
    ts.add_transition("s1", frozenset(), "s1")
    ts.add_state("s0", initial=True)

    _, objective = product(automaton, ts)
    assert objective.priorities
    aut_init = automaton.graph.get_init_state_number()
    assert (("s0", aut_init), frozenset(), ("s0", aut_init)) not in objective.priorities


def test_product_requires_spot():
    import importlib

    # NOT `import automata.product as product_module`: since automata's
    # top-level __init__ does `from .product import product`, the package's
    # own `product` attribute is the *function*, and `import a.b as x` binds
    # `x` via attribute lookup on `a`, it would silently rebind to the
    # function, not the submodule. `importlib.import_module` looks the
    # submodule up by its fully-qualified name instead, sidestepping that.
    product_module = importlib.import_module("model_checker.automata.product")

    original_spot, original_buddy = product_module.spot, product_module.buddy
    product_module.spot = None
    try:
        with pytest.raises(ImportError):
            product(Automaton(graph=object()), _toy_system())
    finally:
        product_module.spot, product_module.buddy = original_spot, original_buddy


def test_product_drops_transitions_incompatible_with_automaton_state():
    # automaton only ever accepts "a" true; a symbol without "a" must not
    # produce any outgoing product transition from the paired automaton state
    automaton = Automaton(graph=spot.translate("Ga", "parity", "deterministic"))
    ts = TransitionSystem()
    ts.add_transition("s0", frozenset(), "s1")  # "a" false
    ts.add_state("s0", initial=True)

    result, _ = product(automaton, ts)
    aut_init = automaton.graph.get_init_state_number()
    assert result.successors(("s0", aut_init), frozenset()) == set()


def test_complete_redirects_a_missing_transition_to_a_rejecting_sink():
    product_ts = TransitionSystem()
    product_ts.add_transition(("s0", 0), frozenset(), ("s0", 0))
    product_ts.add_state(("s0", 0), initial=True)
    underlying = TransitionSystem()
    underlying.add_transition("s0", frozenset(), "s0")
    underlying.add_transition("s0", frozenset({"a"}), "s0")  # a real action product() dropped

    completed, priorities = complete(product_ts, {}, underlying)

    missing = [
        target
        for target in completed.successors(("s0", 0), frozenset({"a"}))
        if target != ("s0", 0)
    ]
    assert len(missing) == 1
    (sink,) = missing
    # the edge *into* the sink is unmarked, a finite prefix, harmless to
    # any acceptance condition; it's the sink's own self-loop that must
    # reject, since that's what recurs forever once you're trapped there
    assert (("s0", 0), frozenset({"a"}), sink) not in priorities
    assert priorities[(sink, frozenset({"a"}), sink)] == 0
    assert priorities[(sink, frozenset(), sink)] == 0
    assert completed.successors(sink, frozenset()) == {sink}
    assert completed.successors(sink, frozenset({"a"})) == {sink}


def test_complete_is_a_noop_when_nothing_is_missing():
    product_ts = TransitionSystem()
    product_ts.add_transition(("s0", 0), frozenset(), ("s0", 0))
    product_ts.add_state(("s0", 0), initial=True)
    underlying = TransitionSystem()
    underlying.add_transition("s0", frozenset(), "s0")  # exactly what product_ts already has

    completed, priorities = complete(product_ts, {}, underlying)

    assert completed.states == product_ts.states
    assert completed.transitions == product_ts.transitions
    assert priorities == {}


def test_complete_leaves_its_inputs_untouched():
    product_ts = TransitionSystem()
    product_ts.add_transition(("s0", 0), frozenset(), ("s0", 0))
    product_ts.add_state(("s0", 0), initial=True)
    underlying = TransitionSystem()
    underlying.add_transition("s0", frozenset(), "s0")
    underlying.add_transition("s0", frozenset({"a"}), "s0")
    original_states = set(product_ts.states)
    original_transitions = {k: set(v) for k, v in product_ts.transitions.items()}

    complete(product_ts, {}, underlying)

    assert product_ts.states == original_states
    assert product_ts.transitions == original_transitions


def test_complete_makes_a_next_shaped_automaton_solvable_instead_of_deadlocking():
    # "X(b)" is a partial transition function: once past the first step, an
    # automaton state exists only for continuations where "b" held then,
    # any ts action from a state where "b" is false has no automaton edge to
    # follow, so product() leaves a genuine deadlock for solve() to choke on.
    automaton = Automaton.from_ltl("X(b)")
    ts = TransitionSystem()
    ts.add_transition("s0", frozenset({"b"}), "s0")
    ts.add_transition("s0", frozenset(), "s0")
    ts.add_state("s0", initial=True)

    product_ts, objective = product(automaton, ts)
    completed, priorities = complete(product_ts, objective.priorities, ts)

    game = concurrent_to_turnbased(
        _as_single_agent_symbols(completed), controlled_players={"p"}
    )
    game.objective = replace(objective, priorities=priorities)
    # must not raise despite the underlying automaton being incomplete
    solve(game)


def _as_single_agent_symbols(ts: TransitionSystem) -> TransitionSystem:
    """`concurrent_to_turnbased` expects joint-action symbols; wrap each
    plain symbol as a single-agent joint action for this test's arena."""
    wrapped = TransitionSystem()
    for state in ts.states:
        wrapped.add_state(state, initial=state in ts.initial_states)
    for (source, symbol), targets in ts.transitions.items():
        for target in targets:
            wrapped.add_transition(source, frozenset({("p", symbol)}), target)
    return wrapped
