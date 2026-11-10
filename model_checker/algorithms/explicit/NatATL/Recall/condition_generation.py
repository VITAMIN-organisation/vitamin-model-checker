"""Conditions for NatATL Recall strategies: boolean and negated conditions, stories
(with Kleene star) and composed regular expressions."""

import logging
from itertools import product

logger = logging.getLogger(__name__)


def generate_conditions(
    atomic_props: list[str], connectives: list[str], max_complexity: int
) -> list[str]:
    """All conditions of `atomic_props` and `connectives` up to `max_complexity`, as
    a list (the shared generator yields them lazily)."""
    conditions: set[str] = set()

    def generate_condition(k: int, condition: list[str]) -> None:
        if k == 0:
            condition_str = " && ".join(condition)
            conditions.add(condition_str)
        else:
            for p in atomic_props:
                if p not in condition:
                    new_condition = condition + [p]
                    if len(new_condition) == 1:
                        generate_condition(k - 1, new_condition)
                    elif len(new_condition) > 1:
                        new_condition.sort()

                        num_connectives = len(new_condition) - 1
                        for ops in product(connectives, repeat=num_connectives):
                            new_condition_str = new_condition[0]
                            for i, op in enumerate(ops):
                                new_condition_str += f" {op} {new_condition[i + 1]}"

                            complexity = len(new_condition_str.split())
                            if complexity <= max_complexity:
                                generate_condition(k - 1, [new_condition_str])

    for k in range(1, max_complexity + 1):
        generate_condition(k, [])

    return list(conditions)


def generate_negated_conditions(
    conditions: list[str], max_complexity: int
) -> list[str]:
    """All negations of the conditions within the complexity bound, where a Kleene
    star also counts toward complexity."""
    negated_conditions: set[str] = set()
    for condition in conditions:
        atomic_props = condition.split(" && ")
        for combo in product(["", "!"], repeat=len(atomic_props)):
            negated_props = [
                f"{combo[i]}{atomic_props[i]}" for i in range(len(atomic_props))
            ]
            new_str = " && ".join(negated_props)
            complexity = len(new_str.split())
            if "!" in new_str:
                complexity += 1
            if "*" in new_str:
                complexity += 1
            if complexity <= max_complexity:
                negated_conditions.add(new_str)
    return list(negated_conditions)


def generate_stories(conditions: list[str], max_complexity: int) -> list[str]:
    """Expand `conditions` into stories up to `max_complexity`: history patterns with at
    least one Kleene star, such as "a then a* then b", which recall strategies need.
    """
    stories: set[str] = set()
    for condition in conditions:
        atomic_props = condition.split(" && ")
        for combo in product(["", "*"], repeat=len(atomic_props)):
            story = [
                f"{atomic_props[i]}{combo[i]}" if combo[i] != "" else atomic_props[i]
                for i in range(len(atomic_props))
            ]
            new_str = " && ".join(story)
            complexity = len(new_str.split())
            if "*" in new_str:
                complexity += 1
            if "!" in new_str:
                complexity += 1
            if complexity <= max_complexity and "*" in new_str:
                stories.add(new_str)
    return list(stories)


def generate_regular_expressions(
    patterns: set[str], composition_ops: list[str], max_complexity: int
) -> list[str]:
    """Compose `patterns` with `composition_ops` (such as `.` for sequencing) into
    regular expressions up to `max_complexity`."""
    expressions: set[str] = set()

    def generate_expression(k: int, expression: list[str]) -> None:
        if k == 0:
            condition_str = " && ".join(expression)
            expressions.add(condition_str)
        else:
            for p in patterns:
                if p not in expression:
                    new_condition = expression + [p]
                    if len(new_condition) == 1:
                        generate_expression(k - 1, new_condition)
                    elif len(new_condition) > 1:
                        num_slots = len(new_condition) - 1
                        for ops in product(composition_ops, repeat=num_slots):
                            new_condition_str = new_condition[0]
                            for i, op in enumerate(ops):
                                new_condition_str += f" {op} {new_condition[i + 1]}"

                            complexity = (
                                len(new_condition_str.split())
                                + new_condition_str.count("!")
                                + new_condition_str.count("*")
                            )
                            if complexity <= max_complexity:
                                generate_expression(k - 1, [new_condition_str])

    for k in range(1, max_complexity + 1):
        generate_expression(k, [])

    return list(expressions)


def create_reg_exp(max_complexity: int, atomic_propositions: list[str]) -> list[str]:
    """Return every recall-condition regex over `atomic_propositions` up to
    `max_complexity`, the formula's `k`: propositions and their negations, stories,
    and their compositions."""
    connectives = ["and", "or"]
    composition_operators = ["."]

    logger.debug("Current complexity bound k: %d", max_complexity)

    conditions = generate_conditions(atomic_propositions, connectives, max_complexity)
    negated_conditions = generate_negated_conditions(conditions, max_complexity)
    stories = generate_stories(negated_conditions, max_complexity)

    all_conditions = set(negated_conditions) | set(stories)

    regular_expressions = generate_regular_expressions(
        all_conditions, composition_operators, max_complexity
    )
    return regular_expressions
