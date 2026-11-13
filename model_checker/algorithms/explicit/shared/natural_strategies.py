"""Natural memoryless strategies: rule lists whose first matching condition picks the
action, ending in a rule guarded by true.

A strategy's size is the number of symbols in its conditions, with true counting
1; a coalition's size is the sum over its members. See docs/algorithms/natatl.md.
"""

import itertools
from collections.abc import Iterator
from dataclasses import dataclass

from model_checker.algorithms.explicit.shared.atom_utils import (
    states_where_prop_holds,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    parse_joint_action_cell,
)

TRUE_CONDITION = "true"
_ANY_ACTION = "*"


@dataclass(frozen=True)
class Condition:
    """A Boolean condition over the propositions, the states where it holds, and its
    size in symbols."""

    text: str
    states: frozenset[str]
    size: int


@dataclass(frozen=True)
class NaturalStrategy:
    """One agent's rule list and the action it plays in each state."""

    rules: tuple[tuple[str, str], ...]
    choice: tuple[tuple[str, str], ...]
    size: int


def _wrap(condition: Condition) -> str:
    """The condition text, in parentheses when it is a binary formula."""
    return f"({condition.text})" if " " in condition.text else condition.text


def enumerate_conditions(cgs, max_size: int) -> list[Condition]:
    """The smallest condition for each set of states that some Boolean formula over
    the propositions of size at most max_size defines, empty and full sets excluded.

    Two conditions with the same states give the same strategies, so the smaller
    one is enough.
    """
    all_states = frozenset(cgs.states)
    smallest: dict[frozenset[str], Condition] = {}
    by_size: dict[int, list[Condition]] = {}

    def keep(condition: Condition) -> None:
        if condition.states not in smallest:
            smallest[condition.states] = condition
            by_size.setdefault(condition.size, []).append(condition)

    for prop in cgs.atomic_propositions:
        states = states_where_prop_holds(cgs, str(prop))
        if states is None:
            raise ValueError(f"Proposition {prop!r} has no Labelling column.")
        keep(Condition(str(prop), frozenset(states), 1))

    for size in range(2, max_size + 1):
        for inner in by_size.get(size - 1, []):
            keep(Condition(f"!{_wrap(inner)}", all_states - inner.states, size))
        for left_size in range(1, size - 1):
            right_size = size - 1 - left_size
            for left, right in itertools.product(
                by_size.get(left_size, []), by_size.get(right_size, [])
            ):
                text_left, text_right = _wrap(left), _wrap(right)
                keep(
                    Condition(
                        f"{text_left} && {text_right}",
                        left.states & right.states,
                        size,
                    )
                )
                keep(
                    Condition(
                        f"{text_left} || {text_right}",
                        left.states | right.states,
                        size,
                    )
                )

    return [
        c
        for size in sorted(by_size)
        for c in by_size[size]
        if c.states and c.states != all_states
    ]


def available_actions(states, parsed_rows, agent: int) -> dict[str, frozenset[str]]:
    """The actions agent (numbered from 1) can play in each state; a `*` cell or
    token allows every action of the agent. parsed_rows comes from parse_rows."""
    per_state: dict[str, set[str]] = {}
    every_action: set[str] = set()
    for state, row in zip(states, parsed_rows, strict=True):
        actions = per_state.setdefault(state, set())
        for cell in row:
            if cell == _ANY_ACTION:
                actions.add(_ANY_ACTION)
            elif isinstance(cell, list):
                actions.update(joint[agent - 1] for joint in cell)
        every_action |= actions - {_ANY_ACTION}
    return {
        state: frozenset(every_action if _ANY_ACTION in actions else actions)
        for state, actions in per_state.items()
    }


def agent_strategies(
    conditions: list[Condition],
    available: dict[str, frozenset[str]],
    max_size: int,
) -> dict[int, list[NaturalStrategy]]:
    """Every natural strategy of one agent up to max_size, keyed by size, keeping the
    smallest strategy for each state-to-action choice.

    A rule is kept only when the states where it matches first are not empty, are
    not all the states left (true would be smaller), and allow its action.
    """
    found: dict[tuple[tuple[str, str], ...], NaturalStrategy] = {}
    all_states = frozenset(available)
    # Rule lists in another order can reach the same partial choice (the states left
    # follow from it); continuing from the cheaper one is enough.
    reached: dict[frozenset, int] = {}

    def extend(rules, choice, left, size) -> None:
        partial = frozenset(choice.items())
        if reached.get(partial, size + 1) <= size:
            return
        reached[partial] = size
        last_size = size + 1
        if last_size <= max_size:
            for action in sorted(frozenset.intersection(*(available[s] for s in left))):
                full = dict(choice)
                full.update(dict.fromkeys(left, action))
                full_key = tuple(sorted(full.items()))
                if full_key not in found or found[full_key].size > last_size:
                    found[full_key] = NaturalStrategy(
                        rules + ((TRUE_CONDITION, action),), full_key, last_size
                    )
        for condition in conditions:
            new_size = size + condition.size
            if new_size + 1 > max_size:
                break
            region = condition.states & left
            if not region or region == left:
                continue
            for action in sorted(
                frozenset.intersection(*(available[s] for s in region))
            ):
                extend(
                    rules + ((condition.text, action),),
                    {**choice, **dict.fromkeys(region, action)},
                    left - region,
                    new_size,
                )

    extend((), {}, all_states, 0)
    by_size: dict[int, list[NaturalStrategy]] = {}
    for strategy in found.values():
        by_size.setdefault(strategy.size, []).append(strategy)
    return by_size


def coalition_profiles(
    per_agent: list[dict[int, list[NaturalStrategy]]], max_size: int
) -> Iterator[tuple[int, tuple[NaturalStrategy, ...]]]:
    """Strategy profiles with their total size, smallest total first, up to max_size."""
    count = len(per_agent)
    for total in range(count, max_size + 1):
        for sizes in _compositions(total, count):
            lists = [per_agent[i].get(size, []) for i, size in enumerate(sizes)]
            for profile in itertools.product(*lists):
                yield total, profile


def _compositions(total: int, parts: int) -> Iterator[tuple[int, ...]]:
    """Every way to write total as an ordered sum of parts positive integers."""
    if parts == 1:
        yield (total,)
        return
    for first in range(1, total - parts + 2):
        for rest in _compositions(total - first, parts - 1):
            yield (first, *rest)


def parse_rows(cgs) -> list[list]:
    """The transition matrix with each joint action cell parsed into its joint
    actions; an empty cell stays as it is and a `*` cell becomes `*`."""
    num_agents = cgs.get_number_of_agents()
    return [[_parse_cell(cell, num_agents) for cell in row] for row in cgs.graph]


def _parse_cell(cell, num_agents: int):
    if cell == 0 or cell == "0":
        return cell
    if str(cell).strip() == _ANY_ACTION:
        return _ANY_ACTION
    return parse_joint_action_cell(str(cell), num_agents)


def restrict_to_profile(states, parsed_rows, agents: list[int], profile) -> list[list]:
    """The transition matrix keeping, in each state, only the joint actions where
    every coalition agent plays its strategy's action; parsed_rows comes from
    parse_rows."""
    choices = [dict(strategy.choice) for strategy in profile]
    graph = []
    for state, row in zip(states, parsed_rows, strict=True):
        wanted = [
            (agent - 1, choice[state])
            for agent, choice in zip(agents, choices, strict=True)
        ]
        new_row = []
        for cell in row:
            if not isinstance(cell, list):
                new_row.append(cell)
                continue
            kept = [
                joint
                for joint in cell
                if all(
                    joint[index] in (action, _ANY_ACTION) for index, action in wanted
                )
            ]
            new_row.append(",".join("|".join(joint) for joint in kept) if kept else 0)
        graph.append(new_row)
    return graph
