
"""Lazy generation of natural memoryless strategy profiles."""

from collections.abc import Iterator, Mapping, Sequence


def guards_exact_cost(
    cost: int,
    propositions: Sequence[str],
) -> Iterator[str]:
    """Generate Boolean guards of exactly the specified complexity."""

    if cost < 1:
        return

    # Base case: atomic propositions have complexity 1.
    # T is reserved for the mandatory final fallback rule.
    if cost == 1:
        for prop in dict.fromkeys(propositions):
            if prop != "T":
                yield prop
        return

    # Negation: |!phi| = 1 + |phi|
    for child in guards_exact_cost(cost - 1, propositions):
        yield f"!({child})"

    # Binary Boolean operators:
    # |phi && psi| = |phi| + 1 + |psi|
    # |phi || psi| = |phi| + 1 + |psi|
    for left_cost in range(1, cost - 1):
        right_cost = cost - 1 - left_cost

        for left in guards_exact_cost(left_cost, propositions):
            for right in guards_exact_cost(right_cost, propositions):
                yield f"({left} && {right})"
                yield f"({left} || {right})"


def individual_exact_cost(
    cost: int,
    actions: Sequence[str],
    propositions: Sequence[str],
) -> Iterator[list[tuple[str, str]]]:
    """Generate ordered individual strategies of exact cost."""

    if cost < 1:
        return

    # Mandatory final rule
    if cost == 1:
        for action in dict.fromkeys(actions):
            yield [("T", action)]
        return

    for first_cost in range(1, cost):
        for guard in guards_exact_cost(first_cost, propositions):

            for action in dict.fromkeys(actions):
                for tail in individual_exact_cost(
                    cost - first_cost,
                    actions,
                    propositions,
                ):
                    yield [(guard, action), *tail]


def collective_strategies(
    agents: Sequence[int],
    actions_by_agent: Mapping[int, Sequence[str]],
    propositions: Sequence[str],
    bound: int,
) -> Iterator[list[dict]]:
    """
    Generate collective strategies in increasing total complexity.

    No list of candidate strategies is materialized in advance.
    Each yielded profile has total cost <= bound.
    """

    if bound < 0:
        raise ValueError("Complexity bound must be nonnegative")

    agents = tuple(agents)

    if len(set(agents)) != len(agents):
        raise ValueError("Repeated coalition agents")

    for agent in agents:
        if agent not in actions_by_agent or not actions_by_agent[agent]:
            raise ValueError(f"Missing actions for agent {agent}")

    if not agents:
        yield []
        return

    def at_cost(
        index: int,
        remaining: int,
        profile: list[dict],
    ) -> Iterator[list[dict]]:

        if index == len(agents):
            if remaining == 0:
                yield list(profile)
            return

        unassigned = len(agents) - index - 1

        # Distribute global budget among coalition agents
        for individual_cost in range(
            1, remaining - unassigned + 1
        ):
            for rules in individual_exact_cost(
                individual_cost,
                actions_by_agent[agents[index]],
                propositions,
            ):
                profile.append({
                    "condition_action_pairs": rules
                })

                yield from at_cost(
                    index + 1,
                    remaining - individual_cost,
                    profile,
                )

                profile.pop()

    # Iterative deepening over collective complexity
    for total_cost in range(len(agents), bound + 1):
        yield from at_cost(0, total_cost, [])
