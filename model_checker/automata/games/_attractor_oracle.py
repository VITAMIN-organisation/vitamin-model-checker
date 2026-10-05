"""Hand-written reachability solver, test oracle only.

Used to cross-validate `solver.py` (which delegates to Spot) against an
independent, dependency-free implementation. Not part of the public API.
"""

from __future__ import annotations

from collections.abc import Hashable

from ..transition_system import TransitionSystem
from .game import Game, GameSolution
from .strategy import Strategy


def attractor(
    arena: TransitionSystem,
    player_states: dict[int, set[Hashable]],
    player: int,
    target: set[Hashable],
) -> tuple[set[Hashable], Strategy]:
    """The reachability attractor for `player`: the least fixed point
    containing `target`, plus a positional winning strategy.

    Test oracle only, cross-validated against `solver.py`. A state owned by
    `player` joins as soon as one action leads into the attractor; an
    opponent state joins only once *every* action does. Assumes a
    deadlock-free arena.
    """
    attracted = set(target)
    choices: dict[Hashable, Hashable] = {}
    owned = player_states.get(player, set())

    # Indexed once by source state so the fixed-point loop below does an O(1)
    # lookup per state instead of rescanning every transition in the arena on
    # every single iteration.
    actions_by_state: dict[Hashable, set[Hashable]] = {}
    for source, symbol in arena.transitions:
        actions_by_state.setdefault(source, set()).add(symbol)

    changed = True
    while changed:
        changed = False
        for state in arena.states - attracted:
            actions = actions_by_state.get(state)
            if not actions:
                continue

            if state in owned:
                for action in actions:
                    successors = arena.successors(state, action)
                    if successors and successors <= attracted:
                        attracted.add(state)
                        choices[state] = action
                        changed = True
                        break
            elif all(arena.successors(state, action) <= attracted for action in actions):
                attracted.add(state)
                changed = True

    return attracted, Strategy(choices)


def solve_reachability(game: Game, player: int, target: set[Hashable]) -> GameSolution:
    """Solve a plain reachability objective: does `player` have a strategy
    forcing the arena into `target`? Test oracle only, simpler than the
    Büchi/co-Büchi/parity objectives `solver.py` handles. No opponent
    strategy is computed.
    """
    win_region, strategy = attractor(game.arena, game.player_states, player, target)
    opponent = 1 - player
    return GameSolution(
        winning_regions={player: win_region, opponent: game.arena.states - win_region},
        strategies={player: strategy},
    )
