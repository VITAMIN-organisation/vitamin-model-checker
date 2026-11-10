from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable
from dataclasses import replace
from typing import cast

from .acceptance import (
    AcceptanceCondition,
    AcceptanceKind,
    ParityStyle,
    priority_from_mark,
)
from .automaton import Automaton, spot
from .transition_system import TransitionSystem

try:
    # conda-forge Spot and pip `spottl` both expose `buddy` once `spot` is imported,
    # which `automaton` does above.
    import buddy
except ImportError:  # pragma: no cover
    buddy = None


def _symbol_as_label(source: Hashable, symbol: Hashable) -> Iterable[str]:
    # symbols are AP names or AP-name collections by contract; the
    # Hashable type of a transition symbol cannot express that
    return cast("Iterable[str]", symbol)


def product(
    automaton: Automaton,
    transition_system: TransitionSystem,
    label: Callable[[Hashable, Hashable], Iterable[str]] = _symbol_as_label,
) -> tuple[TransitionSystem, AcceptanceCondition]:
    """The product of an automaton and a transition system, with its acceptance
    condition. States are `(ts_state, automaton_state)`; `label` gives the
    propositions true on a transition, and the original symbols are kept."""

    if spot is None or buddy is None:
        raise ImportError(
            "Spot is required for product() "
            "(pip install spottl on Linux, or conda-forge elsewhere; "
            "see docs/ATL_STAR/algorithm.md)"
        )
    spot_mod, buddy_mod = spot, buddy

    graph = automaton.graph
    bdict = graph.get_dict()
    # Bare names; they are quoted in Spot text below, or `Granted` reads as `G(ranted)`.
    aps = [ap.ap_name() for ap in graph.ap()]

    # The BDD depends only on (source, symbol), and one ts_state meets several
    # automaton states in the BFS, so caching avoids rebuilding the same BDD.
    valuation_cache: dict[tuple[Hashable, Hashable], object] = {}

    def valuation_bdd(source, symbol):
        key = (source, symbol)
        cached = valuation_cache.get(key)
        if cached is not None:
            return cached
        raw_label = label(source, symbol)
        true_aps = {raw_label} if isinstance(raw_label, str) else set(raw_label)
        literals = " & ".join(f'"{ap}"' if ap in true_aps else f'!"{ap}"' for ap in aps)
        formula = spot_mod.formula(literals) if literals else spot_mod.formula("1")
        result = spot_mod.formula_to_bdd(formula, bdict, graph)
        valuation_cache[key] = result
        return result

    def enabled_edges(state, source, symbol):
        valuation = valuation_bdd(source, symbol)
        for candidate in graph.out(state):
            if (candidate.cond & valuation) != buddy_mod.bddfalse:
                yield candidate

    aut_init = graph.get_init_state_number()
    initial_pairs: list[tuple[Hashable, int]] = [
        (s0, aut_init) for s0 in transition_system.initial_states
    ]

    # Indexed once by source state so the BFS below does an O(1) lookup per
    # popped state instead of rescanning every transition in the system.
    by_source: dict[Hashable, list[tuple[Hashable, set[Hashable]]]] = {}
    for (source, symbol), targets in transition_system.transitions.items():
        by_source.setdefault(source, []).append((symbol, targets))

    result = TransitionSystem()
    for pair in initial_pairs:
        result.add_state(pair, initial=True)

    priorities: dict[tuple[Hashable, Hashable, Hashable], int] = {}

    frontier: list[tuple[Hashable, int]] = list(initial_pairs)
    visited: set[tuple[Hashable, int]] = set(initial_pairs)
    while frontier:
        ts_state, aut_state = frontier.pop()
        for symbol, targets in by_source.get(ts_state, []):
            for edge in enabled_edges(aut_state, ts_state, symbol):
                priority = priority_from_mark(edge.acc)
                for ts_target in targets:
                    product_state = (ts_target, edge.dst)
                    product_source = (ts_state, aut_state)
                    result.add_transition(product_source, symbol, product_state)
                    if priority is not None:
                        priorities[(product_source, symbol, product_state)] = priority
                    if product_state not in visited:
                        visited.add(product_state)
                        frontier.append(product_state)

    objective = automaton._classify(priorities)
    return result, objective


def complete(
    product_ts: TransitionSystem,
    objective: AcceptanceCondition,
    transition_system: TransitionSystem,
) -> tuple[TransitionSystem, AcceptanceCondition]:
    """Send each move the product lacks to one rejecting sink, so `solve()` gets a
    deadlock-free game. The sink's color is the losing one for `objective`, and the
    inputs are left unchanged."""
    real_symbols_by_state: dict[Hashable, set[Hashable]] = {}
    for source, symbol in transition_system.transitions:
        real_symbols_by_state.setdefault(source, set()).add(symbol)

    completed = TransitionSystem(
        states=set(product_ts.states),
        initial_states=set(product_ts.initial_states),
        alphabet=set(product_ts.alphabet),
        transitions={
            key: set(targets) for key, targets in product_ts.transitions.items()
        },
    )
    completed_priorities = dict(objective.priorities)

    sink = object()
    missing = False
    for product_state in list(completed.states):
        system_state, _automaton_state = product_state
        for symbol in real_symbols_by_state.get(system_state, ()):
            if (product_state, symbol) not in completed.transitions:
                completed.add_transition(product_state, symbol, sink)
                missing = True

    if missing:
        sink_priority = _rejecting_sink_priority(objective)
        for symbol in completed.alphabet:
            completed.add_transition(sink, symbol, sink)
            if sink_priority is not None:
                completed_priorities[(sink, symbol, sink)] = sink_priority

    return completed, replace(objective, priorities=completed_priorities)


def _rejecting_sink_priority(objective: AcceptanceCondition) -> int | None:
    """The color to mark a forever-self-looping sink with so it always
    rejects under `objective`, or `None` to leave it unmarked. See
    `complete()`'s docstring for the reasoning per acceptance kind."""
    if objective.kind is AcceptanceKind.BUCHI:
        return None
    if objective.kind is AcceptanceKind.CO_BUCHI:
        return 0
    if objective.kind is AcceptanceKind.PARITY:
        if objective.parity_style is None:
            raise ValueError(
                "a PARITY objective needs parity_style set to pick a rejecting sink color"
            )
        return 0 if objective.parity_style is ParityStyle.ODD else 1
    raise ValueError(f"unsupported acceptance kind {objective.kind!r}")
