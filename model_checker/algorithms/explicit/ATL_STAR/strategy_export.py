"""Flattens a `Witness`'s own strategy into a JSON-ready structure.

`Witness.strategy` is keyed by `(cgs_state, automaton_state)` tuples and
valued by joint-action `frozenset`s, neither is valid JSON (`json.dumps`
raises on both a tuple-keyed dict and a `frozenset`). `export_strategy`
produces plain dicts/lists a caller can hand straight to `json.dumps`.

Nested witnesses (`Witness.nested`) are out of scope for now, only the
coalition's own strategy is exported — `synthesize_strategy` enforces this
by rejecting any formula with a nested coalition before a `Witness` with a
non-empty `nested` could ever be produced.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import TypedDict, cast

from model_checker.parsers.formulas.ATL_STAR.grammar import parse
from model_checker.parsers.game_structures.cgs.protocols import CGSProtocol

from .cgs_adapter import adapt
from .verifier import Witness, require_simple_coalition, witness


class StrategyRow(TypedDict):
    state: str
    memory: int
    agent: Hashable
    action: Hashable


def export_strategy(witness: Witness) -> list[StrategyRow]:
    """Flatten `witness.strategy` into one row per `(state, memory, agent)`.

    Each row records one agent's move within the coalition's joint action
    at that position. Row order isn't meaningful.

    Raises:
        ValueError: some position's action isn't a joint action (a
            `frozenset` of `(agent, action)` pairs), e.g. a `Strategy`
            that didn't come from `witness()`/`check()`.
    """
    rows: list[StrategyRow] = []
    for key, joint_action in witness.strategy.choices.items():
        # `Strategy.choices` is generically `dict[Hashable, Hashable]` (shared across
        # every kind of strategy automata_mc produces); both the key and the value
        # have the concrete shapes `witness()` always builds, which static typing
        # can't see -- same cast idiom `Strategy.project()` itself already uses.
        state, memory = cast("tuple[str, int]", key)
        is_joint_action = isinstance(joint_action, frozenset) and all(
            isinstance(entry, tuple) and len(entry) == 2 for entry in joint_action
        )
        if not is_joint_action:
            raise ValueError(
                f"export_strategy requires a joint-action strategy (a frozenset "
                f"of (agent, action) pairs), got {joint_action!r} at state {state!r}"
            )
        for agent, action in cast("frozenset[tuple[Hashable, Hashable]]", joint_action):
            rows.append(
                {"state": state, "memory": memory, "agent": agent, "action": action}
            )
    return rows


def synthesize_strategy(
    cgs: CGSProtocol, formula_text: str, state: str | None = None
) -> list[StrategyRow] | None:
    """Parse `formula_text`, adapt `cgs`, and return the coalition's own
    witness strategy at `state` (default: `cgs`'s own initial state) as
    JSON-serializable rows, or `None` if the formula doesn't hold there.

    Only supports a formula whose outermost operator is a single coalition
    with no further coalition nested inside its path formula (see
    `verifier.require_simple_coalition`) — broader shapes (nested
    coalitions, top-level boolean combinations of coalitions) are rejected
    with a clear error, deferred to a later iteration.

    Raises:
        ATLStarParseError: `formula_text` is malformed, or a coalition
            names an agent id outside `cgs`'s own agents.
        ValueError: `formula_text` doesn't parse to a single, non-nested
            coalition formula, `state` isn't a state of `cgs`, or an agent
            in the coalition isn't among `cgs`'s agents.
    """
    model = adapt(cgs)
    formula = require_simple_coalition(
        parse(formula_text, num_agents=len(model.players))
    )
    result = witness(formula, model, state=state)
    if result is None:
        return None
    return export_strategy(result)
