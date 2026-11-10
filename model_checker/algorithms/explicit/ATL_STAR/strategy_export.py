"""Turn a `Witness` strategy into dicts and lists that `json.dumps` accepts.

- Only positions reachable from `witness.start` are exported, found by walking
  `witness.product_ts`; `strategy.choices` covers the whole game.
- A coalition move fixes only its own part of the joint action, so each position
  lists one transition per real successor.
- Nested witnesses are rejected.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import TypedDict, cast

from .verifier import Witness


class Position(TypedDict):
    state: str
    memory: int


class StrategyMove(TypedDict):
    state: str
    memory: int
    agent: Hashable
    action: Hashable


class StrategyTransition(TypedDict):
    source: Position
    joint_action: list[tuple[Hashable, Hashable]]
    target: Position


class StrategyExport(TypedDict):
    start: Position
    moves: list[StrategyMove]
    transitions: list[StrategyTransition]


def _as_joint_action(
    value: Hashable, *, position: tuple[str, int]
) -> frozenset[tuple[Hashable, Hashable]]:
    """`value` as a joint action; ValueError if it is not one."""
    is_joint_action = isinstance(value, frozenset) and all(
        isinstance(entry, tuple) and len(entry) == 2 for entry in value
    )
    if not is_joint_action:
        raise ValueError(
            f"export_strategy requires a joint-action strategy (a frozenset "
            f"of (agent, action) pairs), got {value!r} at position {position!r}"
        )
    return cast("frozenset[tuple[Hashable, Hashable]]", value)


def export_strategy(witness: Witness) -> StrategyExport:
    """Export the part of the strategy that a run from `witness.start` can reach.

    Raises ValueError if the witness has nested witnesses or the strategy has a gap,
    instead of returning an export that is silently incomplete.
    """
    if witness.nested:
        raise ValueError(
            "export_strategy does not support nested coalition witnesses yet"
        )

    outgoing: dict[Hashable, list[tuple[Hashable, Hashable]]] = {}
    for (source, symbol), targets in witness.product_ts.transitions.items():
        for target in targets:
            outgoing.setdefault(source, []).append((symbol, target))

    moves: list[StrategyMove] = []
    transitions: list[StrategyTransition] = []
    seen: set[Hashable] = {witness.start}
    frontier: list[Hashable] = [witness.start]

    while frontier:
        position = frontier.pop()
        state, memory = cast("tuple[str, int]", position)
        coalition_action = witness.strategy.choices.get(position)
        if coalition_action is None:
            raise ValueError(f"no strategy choice at reachable position {position!r}")
        coalition_action = _as_joint_action(coalition_action, position=(state, memory))

        for agent, action in sorted(coalition_action):
            moves.append(
                {"state": state, "memory": memory, "agent": agent, "action": action}
            )

        for symbol, target in outgoing.get(position, []):
            full_action = cast("frozenset[tuple[Hashable, Hashable]]", symbol)
            if not coalition_action.issubset(full_action):
                continue
            if not isinstance(target, tuple):
                raise ValueError(
                    f"winning strategy reaches the rejecting sink from {position!r}"
                )
            target_state, target_memory = cast("tuple[str, int]", target)
            transitions.append(
                {
                    "source": {"state": state, "memory": memory},
                    "joint_action": sorted(full_action),
                    "target": {"state": target_state, "memory": target_memory},
                }
            )
            if target not in seen:
                seen.add(target)
                frontier.append(target)

    start_state, start_memory = witness.start
    return {
        "start": {"state": start_state, "memory": start_memory},
        "moves": moves,
        "transitions": transitions,
    }
