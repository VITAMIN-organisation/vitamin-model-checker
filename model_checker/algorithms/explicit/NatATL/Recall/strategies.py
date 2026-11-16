"""NatATL Recall strategies of one agent: ordered rule lists of (pattern, action),
ending in the rule (true*, IDLE)."""

from dataclasses import dataclass

from model_checker.algorithms.explicit.NatATL.Recall.patterns import (
    ANY_HISTORY,
    Pattern,
)
from model_checker.algorithms.explicit.shared.natural_strategies import (
    actions_in_all,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    CANONICAL_IDLE_TOKEN,
)

Rule = tuple[Pattern, str]
IDLE_RULE: Rule = (ANY_HISTORY, CANONICAL_IDLE_TOKEN)


@dataclass(frozen=True)
class RecallStrategy:
    """One agent's rules, the idle rule last, and their total size."""

    rules: tuple[Rule, ...]
    size: int

    def as_pairs(self) -> list[tuple[str, str]]:
        """The rules as (pattern text, action) pairs, as a result reports them."""
        return [(pattern.text, action) for pattern, action in self.rules]


def valid_rules(
    ends: dict[Pattern, frozenset[str]], available: dict[str, frozenset[str]]
) -> list[Rule]:
    """Every (pattern, action) rule whose action is available wherever a history
    matching the pattern ends; `ends` maps each pattern to those states. In the
    order of `ends`, then by action."""
    return [
        (pattern, action)
        for pattern, states in ends.items()
        for action in sorted(actions_in_all(states, available))
    ]


def agent_strategies(
    rules: list[Rule], max_size: int
) -> dict[int, list[RecallStrategy]]:
    """Every strategy of size at most `max_size`, keyed by size: an ordered list of
    rules with distinct patterns, then the idle rule (size 1)."""
    by_size: dict[int, list[RecallStrategy]] = {}

    def extend(chosen: tuple[Rule, ...], size: int) -> None:
        total = size + ANY_HISTORY.size
        by_size.setdefault(total, []).append(
            RecallStrategy(chosen + (IDLE_RULE,), total)
        )
        used = {pattern for pattern, _ in chosen}
        for pattern, action in rules:
            if size + pattern.size + ANY_HISTORY.size > max_size:
                break
            if pattern not in used:
                extend(chosen + ((pattern, action),), size + pattern.size)

    if max_size >= ANY_HISTORY.size:
        extend((), 0)
    return by_size
