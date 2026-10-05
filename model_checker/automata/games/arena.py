from __future__ import annotations

from collections.abc import Hashable
from typing import TypeAlias, cast

from ..transition_system import TransitionSystem
from .game import Game

# One (player, action) pair per agent, a "frozen dict".
JointAction: TypeAlias = frozenset[tuple[Hashable, Hashable]]


def concurrent_to_turnbased(ts: TransitionSystem, controlled_players: set[Hashable]) -> Game:
    """Turn a concurrent, joint-action-labeled `TransitionSystem` into a
    turn-based 2-player Game: `controlled_players` forms player 0's
    coalition, everyone else is player 1.

    Unfolds each simultaneous move in two steps via a fresh intermediate
    state: the coalition picks its partial action, then the environment
    picks the rest.

    `Game.objective` is left `None`, wire it up separately (typically from
    `product()`'s result, remapped through `remap_priorities` first, since
    one `ts` transition becomes two arena transitions here).
    """
    arena = TransitionSystem()
    player1_states: set[Hashable] = set()

    for state in ts.states:
        arena.add_state(state, initial=state in ts.initial_states)

    for (source, symbol), targets in ts.transitions.items():
        joint_action = cast(JointAction, symbol)
        coalition_action, opponent_action, intermediate = _split_joint_action(source, joint_action, controlled_players)

        arena.add_transition(source, coalition_action, intermediate)
        player1_states.add(intermediate)
        for target in targets:
            arena.add_transition(intermediate, opponent_action, target)

    return Game(arena=arena, player_states={0: set(ts.states), 1: player1_states})


def _split_joint_action(
    source: Hashable, joint_action: JointAction, controlled_players: set[Hashable]
) -> tuple[JointAction, JointAction, Hashable]:
    """Split a joint action into the coalition's part, the opponents' part,
    and the intermediate arena state."""
    coalition_action = frozenset((player, action) for player, action in joint_action if player in controlled_players)
    opponent_action = frozenset((player, action) for player, action in joint_action if player not in controlled_players)
    return coalition_action, opponent_action, (source, coalition_action)


def remap_priorities(
    priorities: dict[tuple[Hashable, Hashable, Hashable], int],
    controlled_players: set[Hashable],
) -> dict[tuple[Hashable, Hashable, Hashable], int]:
    """Remap a `ts`-keyed `AcceptanceCondition.priorities` dict onto the
    arena `concurrent_to_turnbased(ts, controlled_players)` returns.

    Each `ts` transition unfolds into two arena edges; only the second
    (intermediate -> target) corresponds 1:1 to it, so only it carries the
    priority, this still preserves Büchi/co-Büchi/parity semantics, since
    every real `ts` step contributes its color exactly once either way.
    """
    remapped: dict[tuple[Hashable, Hashable, Hashable], int] = {}
    for (source, symbol, target), priority in priorities.items():
        joint_action = cast(JointAction, symbol)
        _coalition_action, opponent_action, intermediate = _split_joint_action(source, joint_action, controlled_players)
        remapped[(intermediate, opponent_action, target)] = priority
    return remapped
