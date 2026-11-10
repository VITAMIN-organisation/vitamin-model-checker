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
    """Test oracle: the states from which `player` can force the game into `target`,
    with a winning strategy."""
    attracted = set(target)
    choices: dict[Hashable, Hashable] = {}
    owned = player_states.get(player, set())

    # Indexed once by source, so the fixed-point loop does not rescan the arena.
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
            elif all(
                arena.successors(state, action) <= attracted for action in actions
            ):
                attracted.add(state)
                changed = True

    return attracted, Strategy(choices)


def solve_reachability(game: Game, player: int, target: set[Hashable]) -> GameSolution:
    """Test oracle: solve a reachability game for `player` toward `target`."""
    win_region, strategy = attractor(game.arena, game.player_states, player, target)
    opponent = 1 - player
    return GameSolution(
        winning_regions={player: win_region, opponent: game.arena.states - win_region},
        strategies={player: strategy},
    )
