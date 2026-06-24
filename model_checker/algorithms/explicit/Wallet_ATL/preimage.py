"""Wallet_ATL pre-image and wallet-constraint helpers."""

import re
from collections.abc import Iterable, Sequence
from typing import Any

from model_checker.algorithms.explicit.ATL.preimage import (
    build_transition_cache,
    pre,
)

WalletConstraint = tuple[int, tuple[str, int]]

_COALITION_PREFIX_RE = re.compile(
    r"^<<\s*(?P<agents>\d+(?:\s*,\s*\d+)*)\s*(?::\s*(?P<constraints>.*?))?\s*>>"
)
_CONSTRAINT_RE = re.compile(
    r"wallet\(\s*(?P<agent>\d+)\s*,\s*(?P<operator>>=|<=|==|>|<)\s*(?P<value>\d+)\s*\)"
)


def is_wallet_coalition_operator(value: Any) -> bool:
    """Return True when node value starts with Wallet_ATL coalition prefix `<<...>>`."""
    value_str = str(value)
    return value_str.startswith("<<") and ">>" in value_str


def _parse_constraints(raw_constraints: str | None) -> list[WalletConstraint]:
    if not raw_constraints:
        return []

    constraints: list[WalletConstraint] = []
    parts = [part.strip() for part in re.split(r"\s*&&\s*", raw_constraints) if part]

    for part in parts:
        match = _CONSTRAINT_RE.fullmatch(part)
        if not match:
            raise ValueError(f"Invalid wallet constraint '{part}'")
        constraints.append(
            (
                int(match.group("agent")),
                (match.group("operator"), int(match.group("value"))),
            )
        )

    return constraints


def extract_coalition_and_constraints(
    operator_token: str,
) -> tuple[str, list[int], list[WalletConstraint]]:
    """Extract coalition string, coalition agents and wallet constraints from `<<...>>Op`."""
    match = _COALITION_PREFIX_RE.match(str(operator_token))
    if not match:
        raise ValueError(f"Invalid Wallet_ATL coalition token '{operator_token}'")

    coalition_agents = [
        int(agent.strip())
        for agent in match.group("agents").split(",")
        if agent.strip()
    ]
    coalition = ",".join(str(agent) for agent in coalition_agents)
    constraints = _parse_constraints(match.group("constraints"))
    return coalition, coalition_agents, constraints


def apply_wallet_constraints(
    cgs,
    coalition_agents: Sequence[int],
    constraints: Sequence[WalletConstraint],
    states: Iterable[Any],
) -> set[str]:
    """Filter states that satisfy all coalition wallet constraints."""
    normalized_states = {str(s) for s in states}
    if not normalized_states or not constraints:
        return normalized_states

    constraint_map = dict(constraints)
    filtered_states: set[str] = set()

    for state in normalized_states:
        satisfies_all = True
        for agent in coalition_agents:
            condition = constraint_map.get(agent)
            if condition is None:
                continue
            try:
                if not cgs.check_wallet_constraint(state, agent, condition):
                    satisfies_all = False
                    break
            except (AttributeError, IndexError, ValueError):
                satisfies_all = False
                break

        if satisfies_all:
            filtered_states.add(state)

    return filtered_states


__all__ = [
    "WalletConstraint",
    "build_transition_cache",
    "pre",
    "is_wallet_coalition_operator",
    "extract_coalition_and_constraints",
    "apply_wallet_constraints",
]
