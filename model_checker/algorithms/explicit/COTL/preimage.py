"""One-step operators of COTL: the states from which a legion of demons can steer the path into a target set."""

import heapq
import math
from dataclasses import dataclass

from model_checker.parsers.game_structures.obstruction_model.obstruction_model import (
    ObstructionModel,
)


@dataclass(frozen=True)
class LegionChoice:
    """A legion action at one state: its cost and the successor sets the other demons can leave."""

    cost: int
    outcomes: frozenset[frozenset[int]]


def _cheapest_unlisted_action(
    member_actions: list[dict[str, int]], listed: set[tuple[str, ...]]
) -> int | None:
    """Cost of the cheapest legion action not in `listed`, or None if every action is listed.

    Best-first search over actions sorted by cost; it pops at most len(listed) + 1 actions.
    """
    ordered = [
        sorted(a.items(), key=lambda item: (item[1], item[0])) for a in member_actions
    ]

    def cost(index: tuple[int, ...]) -> int:
        return sum(ordered[m][i][1] for m, i in enumerate(index))

    start: tuple[int, ...] = (0,) * len(ordered)
    frontier: list[tuple[int, tuple[int, ...]]] = [(cost(start), start)]
    seen: set[tuple[int, ...]] = {start}
    while frontier:
        total, index = heapq.heappop(frontier)
        if tuple(ordered[m][i][0] for m, i in enumerate(index)) not in listed:
            return total
        for m in range(len(index)):
            if index[m] + 1 < len(ordered[m]):
                following = index[:m] + (index[m] + 1,) + index[m + 1 :]
                if following not in seen:
                    seen.add(following)
                    heapq.heappush(frontier, (cost(following), following))
    return None


def _choices_at(
    model: ObstructionModel, state: int, members: tuple[int, ...]
) -> tuple[LegionChoice, ...]:
    successors = model.successors[state]
    member_actions = [model.actions_of(state, d) for d in members]
    # Demons with no declared action here only idle, so they add a factor of 1.
    curses_per_action = math.prod(
        len(declared) + 1
        for d, declared in model.demon_actions[state].items()
        if d not in members
    )

    posts_by_action: dict[tuple[str, ...], list[frozenset[int]]] = {}
    for curse, disabled in model.curses[state].items():
        action = tuple(curse[d] for d in members)
        posts_by_action.setdefault(action, []).append(successors - disabled)

    choices = []
    for action, posts in posts_by_action.items():
        outcomes = set(posts)
        # A curse the model does not list disables nothing.
        if len(posts) < curses_per_action:
            outcomes.add(successors)
        cost = sum(costs[a] for costs, a in zip(member_actions, action, strict=True))
        choices.append(LegionChoice(cost, frozenset(outcomes)))

    # Legion actions that no listed curse extends all leave every edge enabled,
    # so only the cheapest of them is kept.
    unlisted_cost = _cheapest_unlisted_action(member_actions, set(posts_by_action))
    if unlisted_cost is not None:
        choices.append(LegionChoice(unlisted_cost, frozenset({successors})))
    return tuple(choices)


class LegionSteps:
    """One-step operators for one model; each legion's choices are built once."""

    def __init__(self, model: ObstructionModel):
        self._model = model
        self._choices: dict[tuple[int, ...], list[tuple[LegionChoice, ...]]] = {}

    def _choices_for(self, legion: tuple[int, ...]) -> list[tuple[LegionChoice, ...]]:
        if legion not in self._choices:
            members = tuple(d - 1 for d in legion)
            self._choices[legion] = [
                _choices_at(self._model, s, members)
                for s in range(len(self._model.successors))
            ]
        return self._choices[legion]

    def _step(
        self, legion: tuple[int, ...], budget: int, target: set[int], may_stop: bool
    ) -> set[int]:
        result = set()
        for state, choices in enumerate(self._choices_for(legion)):
            for choice in choices:
                if choice.cost <= budget and all(
                    (post or may_stop) and post <= target for post in choice.outcomes
                ):
                    result.add(state)
                    break
        return result

    def next_in(
        self, legion: tuple[int, ...], budget: int, target: set[int]
    ) -> set[int]:
        """States where the legion can force a next state, and every next state is in target."""
        return self._step(legion, budget, target, may_stop=False)

    def next_in_or_stop(
        self, legion: tuple[int, ...], budget: int, target: set[int]
    ) -> set[int]:
        """States where the legion can make every next state, if any, be in target."""
        return self._step(legion, budget, target, may_stop=True)
