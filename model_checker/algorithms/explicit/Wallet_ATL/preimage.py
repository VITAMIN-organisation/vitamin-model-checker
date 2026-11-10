"""Wallet_ATL pre-image and wallet-constraint helpers."""

from collections.abc import Iterable, Sequence
from typing import Any

from model_checker.algorithms.explicit.ATL.preimage import (
    TransitionCache,
    build_transition_cache,
    pre,
)
from model_checker.parsers.syntax_patterns import (
    WALLET_COALITION_PREFIX_RE,
    WALLET_CONSTRAINT_AND_RE,
    WALLET_CONSTRAINT_RE,
)

WalletConstraint = tuple[int, tuple[str, int]]


def build_feasible_transition_cache(cgs) -> TransitionCache:
    """The ATL transition cache without the joint moves that some agent cannot pay
    for at the source state, so `pre` only uses moves of the WCGS protocol
    (AAMAS26b Def. 3.1 and 4.1-4.3).

    A state that loses every move is an error: a WCGS is a game structure, which
    gives each agent at least one move per state (JACM 2002 Def. 2.1)."""
    cache: TransitionCache = {}
    stuck = []
    for index, moves in build_transition_cache(cgs).items():
        state = cgs.get_state_name_by_index(index)
        # A profile can lead to several targets; check it once per state.
        verdicts = {
            profile: cgs.is_profile_feasible(state, profile)
            for profile in {profile for profile, _ in moves}
        }
        feasible = [move for move in moves if verdicts[move[0]]]
        if moves and not feasible:
            stuck.append(str(state))
        cache[index] = feasible
    if stuck:
        raise ValueError(
            f"State(s) {stuck} have no feasible move: every transition needs a "
            "consumption action the acting agent cannot pay for."
        )
    return cache


def is_wallet_coalition_operator(value: Any) -> bool:
    """Return True when node value starts with Wallet_ATL coalition prefix `<<...>>`."""
    value_str = str(value)
    return value_str.startswith("<<") and ">>" in value_str


def _parse_constraints(raw_constraints: str | None) -> list[WalletConstraint]:
    if not raw_constraints:
        return []

    constraints: list[WalletConstraint] = []
    parts = [
        part.strip() for part in WALLET_CONSTRAINT_AND_RE.split(raw_constraints) if part
    ]

    for part in parts:
        match = WALLET_CONSTRAINT_RE.fullmatch(part)
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
) -> tuple[str, list[WalletConstraint]]:
    """Extract the coalition string and the wallet constraints from `<<...>>Op`."""
    match = WALLET_COALITION_PREFIX_RE.match(str(operator_token))
    if not match:
        raise ValueError(f"Invalid Wallet_ATL coalition token '{operator_token}'")

    coalition = ",".join(
        str(int(agent)) for agent in match.group("agents").split(",") if agent.strip()
    )
    return coalition, _parse_constraints(match.group("constraints"))


def apply_wallet_constraints(
    cgs,
    constraints: Sequence[WalletConstraint],
    states: Iterable[Any],
) -> set[str]:
    """The states where every wallet guard holds (wPre, AAMAS26b Algorithm 2)."""
    names = {str(state) for state in states}
    if not constraints:
        return names
    return {
        state
        for state in names
        if all(
            cgs.check_wallet_constraint(state, agent, condition)
            for agent, condition in constraints
        )
    }


__all__ = [
    "WalletConstraint",
    "pre",
    "is_wallet_coalition_operator",
    "extract_coalition_and_constraints",
    "apply_wallet_constraints",
]
