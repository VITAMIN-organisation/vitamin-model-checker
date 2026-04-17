"""
Condition generation utilities for NatATL Recall strategies.

This module provides functions for generating boolean conditions, negated conditions,
stories (regex patterns with Kleene star), and composed regular expressions used
in recall strategy conditions.
"""

import logging
from itertools import product
from typing import List, Set

logger = logging.getLogger(__name__)


def generate_conditions(
    atomic_props: List[str], connectives: List[str], max_complexity: int
) -> List[str]:
    """
    Generate boolean conditions by combining atomic propositions with connectives.

    Unlike the shared version which yields lazily, this returns a complete list
    for use in regex generation pipelines.

    Args:
        atomic_props: List of atomic proposition names
        connectives: List of connective operators (['and', 'or'])
        max_complexity: Maximum complexity bound for conditions

    Returns:
        List of condition strings
    """
    conditions: Set[str] = set()

    def generate_condition(k: int, condition: List[str]) -> None:
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
    conditions: List[str], max_complexity: int
) -> List[str]:
    """
    Generate all negation variants of conditions within complexity bounds.

    For recall strategies, also considers Kleene star (*) in complexity calculation.
    """
    negated_conditions: Set[str] = set()
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


def generate_stories(conditions: List[str], max_complexity: int) -> List[str]:
    """
    Generate "story" patterns - regex sequences with Kleene star.

    Stories represent history patterns like "a then a* then b" meaning
    "a followed by zero or more a's followed by b". These are essential
    for recall strategies that depend on execution history.

    Args:
        conditions: List of condition strings to expand with Kleene star
        max_complexity: Maximum complexity bound

    Returns:
        List of story patterns containing at least one Kleene star
    """
    stories: Set[str] = set()
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
    patterns: Set[str], composition_ops: List[str], max_complexity: int
) -> List[str]:
    """
    Generate composed regular expressions from patterns.

    Combines patterns using composition operators (like sequencing '.')
    to create more complex regex patterns for recall conditions.

    Args:
        patterns: Set of base patterns to compose
        composition_ops: List of composition operators (e.g., ['.'])
        max_complexity: Maximum complexity bound

    Returns:
        List of composed regular expression strings
    """
    expressions: Set[str] = set()

    def generate_expression(k: int, expression: List[str]) -> None:
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


def create_reg_exp(max_complexity: int, atomic_propositions: List[str]) -> List[str]:
    """
    Create regular expressions for recall strategy conditions.

    Generates all possible regex patterns from atomic propositions up to
    the given complexity. This includes:
    - Simple propositions and their negations
    - Stories (sequences with Kleene star for repetition)
    - Composed expressions

    Args:
        max_complexity: Maximum complexity bound (k value from formula)
        atomic_propositions: List of atomic props from the model

    Returns:
        List of regex pattern strings
    """
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
