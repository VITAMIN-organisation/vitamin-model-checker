"""Flattens a `Witness`'s own strategy into a JSON-ready structure.

`Witness.strategy` is keyed by `(cgs_state, automaton_state)` tuples and
valued by joint-action `frozenset`s, neither is valid JSON (`json.dumps`
raises on both a tuple-keyed dict and a `frozenset`). `export_strategy`
produces plain dicts/lists a caller can hand straight to `json.dumps`.

Two things `witness.strategy.choices` alone doesn't give a consumer:

- `choices` is the *whole* solved game's positional strategy (`_solve_coalition`
  solves from every state at once), not just the part reachable from
  `witness.start` — exporting it as-is would include positions a run starting
  at `start` can never reach, and would look identical regardless of which
  state the witness was actually requested for. `export_strategy` instead
  walks `witness.product_ts` from `start`, following only real transitions,
  so only reachable positions are exported.
- a position's `choices` entry is only the coalition's own partial move
  (e.g. `{(1, "A")}`), never the full joint action, the rest of the system
  is adversarial and free to respond however it likes, so one committed move
  can be consistent with more than one real successor. `export_strategy`
  therefore exports a transition *relation* (`transitions`, one row per real
  successor, carrying the full joint action that leads to it), not a single
  next-state column.

Nested witnesses (`Witness.nested`) are out of scope for now: callers
(`ATL_STAR._core_synthesize_strategy`) only ever build a `Witness` through
`verifier.require_simple_coalition`, which already rejects a formula with a
nested coalition before such a `Witness` could exist; `export_strategy`
itself also rejects one directly, in case it's ever called with a `Witness`
bypassing that check.
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
    """Validate and cast a `Strategy.choices` value into a joint action.

    Raises:
        ValueError: `value` isn't a joint action (a `frozenset` of
            `(agent, action)` pairs), e.g. a `Strategy` that didn't come
            from `witness()`/`check()`.
    """
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
    """Walk `witness` from `witness.start`, exporting only reachable
    positions, the coalition's move at each, and every real transition that
    move allows (see module docstring for why both of those need a walk,
    not a flat read of `witness.strategy.choices`).

    Raises:
        ValueError: `witness.nested` is non-empty (not supported yet); some
            reachable position's strategy entry isn't a joint action, is
            missing entirely, or leads only to `product.complete()`'s
            rejecting sink — each would otherwise silently cut the export
            short while still reporting the overall result as satisfied.
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
