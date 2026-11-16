"""Natural memoryless strategies: ordered rule lists ending in a true rule, sized
by their condition symbols; see docs/algorithms/natatl.md."""

import itertools
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, TypeVar

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.shared.atom_utils import (
    states_where_prop_holds,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    initial_state_holds,
)
from model_checker.parsers.game_structures.cgs import cgs_validation
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    parse_joint_action_cell,
)

TRUE_CONDITION = "true"
ANY_ACTION = "*"

# Memoryless and recall strategies share the search over coalition profiles.
Strategy = TypeVar("Strategy")


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


def condition_text(condition: Condition) -> str:
    """The condition text, in parentheses when it is a binary formula."""
    return f"({condition.text})" if " " in condition.text else condition.text


def enumerate_conditions(cgs, max_size: int) -> list[Condition]:
    """The smallest condition (size at most max_size) for each set of states, empty
    and full sets excluded: conditions with the same states give the same strategies."""
    if max_size < 1:
        return []
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
            keep(
                Condition(f"!{condition_text(inner)}", all_states - inner.states, size)
            )
        for left_size in range(1, size - 1):
            right_size = size - 1 - left_size
            for left, right in itertools.product(
                by_size.get(left_size, []), by_size.get(right_size, [])
            ):
                text_left, text_right = condition_text(left), condition_text(right)
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
            if cell == ANY_ACTION:
                actions.add(ANY_ACTION)
            elif isinstance(cell, list):
                actions.update(joint[agent - 1] for joint in cell)
        every_action |= actions - {ANY_ACTION}
    return {
        state: frozenset(every_action if ANY_ACTION in actions else actions)
        for state, actions in per_state.items()
    }


def actions_in_all(states, available: dict[str, frozenset[str]]) -> frozenset[str]:
    """The actions available in every one of `states`; empty when `states` is."""
    if not states:
        return frozenset()
    return frozenset.intersection(*(available[state] for state in states))


def agent_strategies(
    conditions: list[Condition],
    available: dict[str, frozenset[str]],
    max_size: int,
) -> dict[int, list[NaturalStrategy]]:
    """Every strategy of one agent up to max_size, keyed by size, keeping the smallest
    one per state-to-action choice; a rule must match first on some states left."""
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
            for action in sorted(actions_in_all(left, available)):
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
            for action in sorted(actions_in_all(region, available)):
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


def _coalition_profiles(
    per_agent: list[dict[int, list[Strategy]]], max_size: int
) -> Iterator[tuple[int, tuple[Strategy, ...]]]:
    """Strategy profiles with their total size, smallest total first, up to max_size."""
    count = len(per_agent)
    for total in range(count, max_size + 1):
        for sizes in _compositions(total, count):
            lists = [per_agent[i].get(size, []) for i, size in enumerate(sizes)]
            for profile in itertools.product(*lists):
                yield total, profile


def smallest_winning_profile(
    per_agent: list[dict[int, list[Strategy]]],
    k: int,
    wins: Callable[[tuple[Strategy, ...]], bool],
    rule_pairs: Callable[[Strategy], list],
    initial_state: str,
) -> dict[str, Any]:
    """The NatATL result for the smallest profile up to total size k that wins, with
    its rules as (condition, action) pairs per member."""
    result: dict[str, Any] = {"Satisfiability": False, "Complexity Bound": k}
    for total, profile in _coalition_profiles(per_agent, k):
        if wins(profile):
            result = {
                "Satisfiability": True,
                "Complexity Bound": total,
                "Winning Strategy per agent": [
                    {"condition_action_pairs": rule_pairs(strategy)}
                    for strategy in profile
                ],
            }
            break
    is_sat = result["Satisfiability"]
    result["res"] = f"Result: {is_sat}"
    result["initial_state"] = f"Initial state {initial_state}: {is_sat}"
    return result


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
    if str(cell).strip() == ANY_ACTION:
        return ANY_ACTION
    return parse_joint_action_cell(str(cell), num_agents)


def restrict_to_profile(states, parsed_rows, agents: list[int], profile) -> list[list]:
    """The transition matrix (from parse_rows) keeping only the joint actions where
    every coalition agent plays its strategy's action."""
    choices = [dict(strategy.choice) for strategy in profile]
    graph = []
    for state, row in zip(states, parsed_rows, strict=True):
        wanted = [
            (agent - 1, choice[state])
            for agent, choice in zip(agents, choices, strict=True)
        ]
        graph.append([keep_joint_actions(cell, wanted) for cell in row])
    return graph


def goal_holds_on(model, ctl_formula: str, model_path: str) -> bool:
    """True when the CTL goal holds at the initial state of the restricted `model`;
    a state with no move is a loss, as CTL would read the dead end as a win for AF."""
    if cgs_validation.validate_total_transitions(model.graph, model.states):
        return False
    result = model_checking(ctl_formula, model_path, preloaded_model=model)
    return initial_state_holds(result, ctl_formula)


def keep_joint_actions(cell, wanted: list[tuple[int, str]]):
    """A parsed cell as matrix text keeping the joint actions where each agent index
    in `wanted` plays its action: 0 when none is left, 0 and `*` cells unchanged."""
    if not isinstance(cell, list):
        return cell
    kept = [
        joint
        for joint in cell
        if all(joint[index] in (action, ANY_ACTION) for index, action in wanted)
    ]
    return ",".join("|".join(joint) for joint in kept) if kept else 0
