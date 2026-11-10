from __future__ import annotations

from collections.abc import Hashable
from collections.abc import Set as AbstractSet
from typing import TypeAlias, cast

from ..transition_system import TransitionSystem
from .game import Game

# One (player, action) pair per agent, a "frozen dict".
JointAction: TypeAlias = frozenset[tuple[Hashable, Hashable]]


def concurrent_to_turnbased(
    ts: TransitionSystem, controlled_players: AbstractSet[Hashable]
) -> Game:
    """Turn a concurrent transition system into a turn-based 2-player game: player 0
    (`controlled_players`) picks its part of each move, then player 1 the rest.
    `objective` is left for the caller, through `remap_priorities`."""
    arena = TransitionSystem()
    player1_states: set[Hashable] = set()

    for state in ts.states:
        arena.add_state(state, initial=state in ts.initial_states)

    for (source, symbol), targets in ts.transitions.items():
        joint_action = cast(JointAction, symbol)
        coalition_action, opponent_action, intermediate = _split_joint_action(
            source, joint_action, controlled_players
        )

        arena.add_transition(source, coalition_action, intermediate)
        player1_states.add(intermediate)
        for target in targets:
            arena.add_transition(intermediate, opponent_action, target)

    return Game(arena=arena, player_states={0: set(ts.states), 1: player1_states})


def _split_joint_action(
    source: Hashable,
    joint_action: JointAction,
    controlled_players: AbstractSet[Hashable],
) -> tuple[JointAction, JointAction, Hashable]:
    """Split a joint action into the coalition's part, the opponents' part,
    and the intermediate arena state."""
    coalition_action = frozenset(
        (player, action)
        for player, action in joint_action
        if player in controlled_players
    )
    opponent_action = frozenset(
        (player, action)
        for player, action in joint_action
        if player not in controlled_players
    )
    return coalition_action, opponent_action, (source, coalition_action)


def remap_priorities(
    priorities: dict[tuple[Hashable, Hashable, Hashable], int],
    controlled_players: AbstractSet[Hashable],
) -> dict[tuple[Hashable, Hashable, Hashable], int]:
    """Move the priorities of `ts` transitions onto the arena of
    `concurrent_to_turnbased`: only the second of the two arena steps keeps the
    color, so each real step still counts once."""
    remapped: dict[tuple[Hashable, Hashable, Hashable], int] = {}
    for (source, symbol, target), priority in priorities.items():
        joint_action = cast(JointAction, symbol)
        _coalition_action, opponent_action, intermediate = _split_joint_action(
            source, joint_action, controlled_players
        )
        remapped[(intermediate, opponent_action, target)] = priority
    return remapped
