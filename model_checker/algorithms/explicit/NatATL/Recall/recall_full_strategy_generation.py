"""Lazy, cost-ordered strategy enumeration over extended NatATL Recall guards.

This module is independent of the old unfolding solver and of the canonical
strategy generator.  Guard expressions are produced by
``history_guards_full_exact_cost``.  An individual strategy is an ordered list
of guarded actions ending with exactly (T*, IDLE); its cost is the sum of the
significant-pattern sizes.  A coalition's cost is additive.

The generator does NOT certify full-language model-checking completeness.
Global rule appropriateness must be checked against the CGS separately.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence

from model_checker.algorithms.explicit.NatATL.Recall.recall_full_regex_generation import (
    history_guards_full_exact_cost,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_lazy_generation import (
    profile_cost,
    strategy_cost,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
)


def individual_full_exact_cost(
    cost: int,
    actions: Sequence[str],
    propositions: Sequence[str],
) -> Iterator[dict]:
    """Generate individual rule lists of *exact* significant-pattern cost.

    No arbitrary rule-count or history-depth cutoff is imposed.  Guard/action
    pairs with a repeated guard are omitted: only the first such guard can
    affect behavior in an appropriate strategy, so duplicate guards are
    semantically redundant.  This is a normal form, not a claim that every
    raw syntax tree is enumerated verbatim.
    """
    available = tuple(dict.fromkeys(normalize_action_token(a) for a in actions))
    if not available or "IDLE" not in available:
        raise ValueError("Recall strategies require an IDLE fallback")
    if type(cost) is not int or cost < 1:
        return

    # Prefix generator: all rules except mandatory final (T*, IDLE).
    def extend(
        remaining: int,
        rules: tuple[tuple[str, str], ...],
        seen_guards: frozenset[str],
    ) -> Iterator[dict]:
        if remaining == 1:
            yield {"condition_action_pairs": [*rules, ("T*", "IDLE")]}
            return
        for guard_cost in range(1, remaining):
            for guard in history_guards_full_exact_cost(guard_cost, propositions):
                if guard in seen_guards:
                    continue
                for action in available:
                    yield from extend(
                        remaining - guard_cost,
                        (*rules, (guard, action)),
                        seen_guards | {guard},
                    )

    yield from extend(cost, (), frozenset())


def collective_full_strategies(
    agents: Sequence[int],
    actions_by_agent: Mapping[int, Sequence[str]],
    propositions: Sequence[str],
    bound: int,
) -> Iterator[list[dict]]:
    """Enumerate collective strategies in nondecreasing total cost <= bound.

    Agent identifiers are 1-based; coalition order is preserved in the output.
    The generator enumerates *candidate syntax*, not necessarily globally
    appropriate profiles.  The model checker must validate each candidate.
    """
    coalition = tuple(agents)
    if (
        not coalition
        or len(set(coalition)) != len(coalition)
        or any(type(a) is not int or a < 1 for a in coalition)
    ):
        raise ValueError("Expected a nonempty coalition of distinct positive agents")
    if type(bound) is not int or bound < 0:
        raise ValueError("The strategy bound must be a nonnegative integer")
    if any(a not in actions_by_agent for a in coalition):
        raise ValueError("Missing actions for a coalition member")

    inventories: dict[int, tuple[str, ...]] = {}
    for agent in coalition:
        normalized = tuple(
            dict.fromkeys(normalize_action_token(a) for a in actions_by_agent[agent])
        )
        if "IDLE" not in normalized:
            raise ValueError(f"Agent {agent} has no IDLE fallback")
        inventories[agent] = normalized

    n_agents = len(coalition)

    def assign(
        index: int,
        remaining: int,
        prefix: list[dict],
    ) -> Iterator[list[dict]]:
        if index == n_agents:
            if remaining == 0:
                yield list(prefix)
            return
        left = n_agents - index - 1
        for agent_cost in range(1, remaining - left + 1):
            for strategy in individual_full_exact_cost(
                agent_cost, inventories[coalition[index]], propositions
            ):
                prefix.append(strategy)
                yield from assign(index + 1, remaining - agent_cost, prefix)
                prefix.pop()

    for total_cost in range(n_agents, bound + 1):
        yield from assign(0, total_cost, [])


__all__ = [
    "individual_full_exact_cost",
    "collective_full_strategies",
    "strategy_cost",
    "profile_cost",
]
