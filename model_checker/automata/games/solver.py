from __future__ import annotations

from collections.abc import Hashable

from ..acceptance import AcceptanceCondition, AcceptanceKind, ParityKind, ParityStyle
from .game import Game, GameSolution
from .strategy import Strategy

try:
    import spot
except ImportError:  # pragma: no cover
    spot = None


def solve(game: Game) -> GameSolution:
    """Solve a Game via Spot's game-solving convention.

    Spot's SWIG bindings have no docstrings; facts here are easy to get
    backwards: `set_state_players`/`get_state_winners` use **True = player
    0**, and `get_strategy(aut)` returns per-state 1-based edge numbers for
    both players at once. `0` means no edge, but for a losing owner Spot can
    also return other numbers with no matching edge in `aut` at all (seen on
    genuine 3+-color parity games, SWIG surfaces them as huge unsigned
    values, e.g. a C++ `-5` as `4294967291`); any edge number absent from
    `edge_labels` is treated the same as `0`. Assumes a deadlock-free arena.

    `spot.solve_game` only computes correct winners for states reachable
    from the one state it's told is initial (confirmed empirically,
    undocumented); everything else silently defaults to a loss, even though
    winning regions are otherwise a whole-graph fixed point. So every state
    in `game.arena.states` — not just the ones marked initial, since a
    winning state that's simply never declared initial would otherwise be
    silently misreported as a loss — gets bridged from a throwaway state via
    an unmarked edge and solving anchors there instead, invisible in the
    returned `GameSolution`, and harmless to any acceptance condition, since
    an unmarked one-off prefix can't affect what recurs infinitely often.

    Raises:
        ImportError: if Spot isn't importable.
        ValueError: if `objective` is unset, the arena has no state at all,
            `player_states` isn't a proper partition, or the arena is
            nondeterministic (some `(state, action)` has more than one
            successor).
    """
    if spot is None:
        raise ImportError("Spot is required for solve() "
                           "(pip install spottl on Linux, or conda-forge elsewhere; "
                           "see docs/ATL_STAR/algorithm.md)")
    if game.objective is None:
        raise ValueError("Game.objective must be set before solving (arena.py leaves it None on purpose)")
    if not game.arena.states:
        raise ValueError("game.arena must have at least one state")

    states = list(game.arena.states)
    state_index = {state: i for i, state in enumerate(states)}

    owner0 = game.player_states.get(0, set())
    owner1 = game.player_states.get(1, set())
    if not owner0.isdisjoint(owner1) or (owner0 | owner1) != game.arena.states:
        raise ValueError("every arena state must belong to exactly one of player_states[0]/[1]")

    # A `Strategy` records only the chosen action, not which successor it
    # led to (see strategy.py), so an arena where one action from a state
    # has more than one possible target would let Spot "win" via a specific
    # edge that the returned Strategy can't actually tell apart from a
    # losing one sharing the same action. Rejected outright rather than
    # solved unsoundly: this game model is 2-player, total-information,
    # with no third "nature" player to own leftover nondeterminism.
    for (source, symbol), targets in game.arena.transitions.items():
        if len(targets) > 1:
            raise ValueError(
                f"solve() requires a deterministic arena: state {source!r} has "
                f"{len(targets)} successors for action {symbol!r} ({sorted(map(str, targets))}); "
                "every (state, action) pair must lead to exactly one successor"
            )

    aut = spot.make_twa_graph(spot.make_bdd_dict())
    aut.new_states(len(states) + 1)  # +1 for the throwaway reachability-anchor state, placed last
    anchor = len(states)
    aut.set_init_state(anchor)

    _set_acceptance(aut, game.objective)
    true_cond = spot.formula_to_bdd(spot.formula("1"), aut.get_dict(), aut)

    edge_labels: dict[int, tuple[Hashable, Hashable, Hashable]] = {}
    for (source, symbol), targets in game.arena.transitions.items():
        for target in targets:
            key = (source, symbol, target)
            priority = game.objective.priorities.get(key)
            mark = [priority] if priority is not None else []
            edge_number = aut.new_edge(state_index[source], state_index[target], true_cond, mark)
            edge_labels[edge_number] = key

    for state in game.arena.states:
        aut.new_edge(anchor, state_index[state], true_cond, [])

    # placing the anchor last means these zips naturally drop its own
    # winner/strategy entry, it was never a real arena state
    spot.set_state_players(aut, [state in owner0 for state in states] + [True])
    spot.solve_game(aut)

    winners = spot.get_state_winners(aut)
    strategy_edges = spot.get_strategy(aut)
    expected_length = len(states) + 1  # +1 for the anchor's own trailing entry, dropped below
    if len(winners) != expected_length or len(strategy_edges) != expected_length:
        raise RuntimeError(
            "spot.get_state_winners()/get_strategy() returned an unexpected number of "
            f"entries (expected {expected_length}, got {len(winners)}/{len(strategy_edges)}); "
            "the zip() below relies on this to safely drop the anchor's own trailing entry"
        )

    winning_regions: dict[int, set[Hashable]] = {0: set(), 1: set()}
    for state, player0_wins in zip(states, winners):  # noqa: B905, deliberately not strict, see the length check above
        winning_regions[0 if player0_wins else 1].add(state)

    choices: dict[int, dict[Hashable, Hashable]] = {0: {}, 1: {}}
    for state, edge_number in zip(states, strategy_edges):  # noqa: B905, see above
        if edge_number not in edge_labels:
            continue
        _source, symbol, _target = edge_labels[edge_number]
        choices[0 if state in owner0 else 1][state] = symbol

    return GameSolution(
        winning_regions=winning_regions,
        strategies={0: Strategy(choices[0]), 1: Strategy(choices[1])},
    )


def _set_acceptance(aut, objective: AcceptanceCondition) -> None:
    """Configure `aut`'s acceptance kind from `objective`. Edge marks are
    applied separately by the caller, from `objective.priorities`.

    A PARITY objective with no priorities at all is well-defined, not an
    error: with a single color, the acceptance formula reduces to `Fin(0)`
    (odd styles) or `Inf(0)` (even styles), confirmed empirically, and
    exactly what you want for e.g. a translated "always true" LTL formula,
    where no transition ever needs marking and every run should accept
    under an odd style (the orientation `Automaton.from_ltl` always uses).
    """
    if objective.kind is AcceptanceKind.BUCHI:
        aut.set_buchi()
    elif objective.kind is AcceptanceKind.CO_BUCHI:
        aut.set_co_buchi()
    elif objective.kind is AcceptanceKind.PARITY:
        num_colors = max(objective.priorities.values(), default=-1) + 1
        num_colors = max(num_colors, 1)
        kind = "max" if objective.parity_kind is ParityKind.MAX else "min"
        style = "odd" if objective.parity_style is ParityStyle.ODD else "even"
        aut.set_acceptance(num_colors, f"parity {kind} {style} {num_colors}")
    else:
        raise ValueError(f"unsupported acceptance kind {objective.kind!r}")
