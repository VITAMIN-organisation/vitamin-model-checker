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
    """Solve a deadlock-free Game with Spot: each player's winning region and strategy.

    Spot quirks handled here (found by testing): True means player 0; `get_strategy`
    can return edge numbers that do not exist, read as no edge; and `solve_game` is
    right only for states reachable from its start, so one extra start state links
    to every state.
    """
    if spot is None:
        raise ImportError(
            "Spot is required for solve() "
            "(pip install spottl on Linux, or conda-forge elsewhere; "
            "see docs/algorithms/atl_star.md)"
        )
    if game.objective is None:
        raise ValueError(
            "Game.objective must be set before solving (arena.py leaves it None on purpose)"
        )
    if not game.arena.states:
        raise ValueError("game.arena must have at least one state")

    states = list(game.arena.states)
    state_index = {state: i for i, state in enumerate(states)}

    owner0 = game.player_states.get(0, set())
    owner1 = game.player_states.get(1, set())
    if not owner0.isdisjoint(owner1) or (owner0 | owner1) != game.arena.states:
        raise ValueError(
            "every arena state must belong to exactly one of player_states[0]/[1]"
        )

    # A `Strategy` records the action, not the successor, so Spot could win on an edge
    # the Strategy cannot tell from a losing one; with no nature player, reject it.
    for (source, symbol), targets in game.arena.transitions.items():
        if len(targets) > 1:
            raise ValueError(
                f"solve() requires a deterministic arena: state {source!r} has "
                f"{len(targets)} successors for action {symbol!r} ({sorted(map(str, targets))}); "
                "every (state, action) pair must lead to exactly one successor"
            )

    aut = spot.make_twa_graph(spot.make_bdd_dict())
    aut.new_states(
        len(states) + 1
    )  # +1 for the throwaway reachability-anchor state, placed last
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
            edge_number = aut.new_edge(
                state_index[source], state_index[target], true_cond, mark
            )
            edge_labels[edge_number] = key

    for state in game.arena.states:
        aut.new_edge(anchor, state_index[state], true_cond, [])

    # placing the anchor last means these zips naturally drop its own
    # winner/strategy entry, it was never a real arena state
    spot.set_state_players(aut, [state in owner0 for state in states] + [True])
    spot.solve_game(aut)

    winners = spot.get_state_winners(aut)
    strategy_edges = spot.get_strategy(aut)
    expected_length = (
        len(states) + 1
    )  # +1 for the anchor's own trailing entry, dropped below
    if len(winners) != expected_length or len(strategy_edges) != expected_length:
        raise RuntimeError(
            "spot.get_state_winners()/get_strategy() returned an unexpected number of "
            f"entries (expected {expected_length}, got {len(winners)}/{len(strategy_edges)}); "
            "the zip() below relies on this to safely drop the anchor's own trailing entry"
        )

    winning_regions: dict[int, set[Hashable]] = {0: set(), 1: set()}
    for state, player0_wins in zip(states, winners[:-1], strict=True):
        winning_regions[0 if player0_wins else 1].add(state)

    choices: dict[int, dict[Hashable, Hashable]] = {0: {}, 1: {}}
    for state, edge_number in zip(states, strategy_edges[:-1], strict=True):
        if edge_number not in edge_labels:
            continue
        _source, symbol, _target = edge_labels[edge_number]
        choices[0 if state in owner0 else 1][state] = symbol

    return GameSolution(
        winning_regions=winning_regions,
        strategies={0: Strategy(choices[0]), 1: Strategy(choices[1])},
    )


def _set_acceptance(aut, objective: AcceptanceCondition) -> None:
    """Set `aut`'s acceptance kind from `objective`; the caller sets the edge marks.
    A parity objective with no priorities is allowed: under the odd style every run
    accepts."""
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
