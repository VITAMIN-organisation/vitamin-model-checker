"""Structural enumeration of Reg(B(Prop)) for NatATL recall.

This enumerator is used for the explicitly supported complete grammar.
Completeness scope and required assumptions are in docs/NatATL/RECALL_COMPLETENESS.md;
it makes no claim for additional syntax or alternative cost metrics.

Boolean alphabet: T, false, each proposition, !, &&, ||.
Regex constructors: propositional guard, concatenation '.', union '|', '*'.
Parentheses and [] are delimiters, not complexity tokens.
The *raw* size counts each Boolean/regex operator and atom as one.
The significant pattern size is 1 for T*, the raw size of r for T*.r,
and the raw size otherwise. Every nonempty history is a word over labels.

All derivations are enumerated in a fixed parenthesized concrete form.
Syntactic aliases (e.g. true for T, redundant parentheses) are normalized.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Sequence

from model_checker.algorithms.explicit.NatATL.Recall.recall_lazy_generation import (
    regex_complexity,
)

_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
_RESERVED = frozenset({"T", "true", "false"})


def _alphabet(propositions: Sequence[str]) -> tuple[str, ...]:
    atoms = ["T", "false"]
    for prop in propositions:
        if not isinstance(prop, str) or _IDENT.fullmatch(prop) is None:
            raise ValueError(f"Invalid atomic proposition {prop!r}")
        if prop in _RESERVED:
            raise ValueError(f"Reserved atomic proposition {prop!r}")
        if prop not in atoms:
            atoms.append(prop)
    return tuple(atoms)


def boolean_exact_size(size: int, propositions: Sequence[str]) -> Iterator[str]:
    """All normalized Boolean guard ASTs with exactly ``size`` tokens."""
    if not isinstance(size, int) or size < 1:
        return
    atoms = _alphabet(propositions)
    if size == 1:
        yield from atoms
        return
    for child in boolean_exact_size(size - 1, propositions):
        yield f"!({child})"
    for left_size in range(1, size - 1):
        right_size = size - left_size - 1
        for left in boolean_exact_size(left_size, propositions):
            for right in boolean_exact_size(right_size, propositions):
                yield f"({left} && {right})"
                yield f"({left} || {right})"


def regex_exact_raw_size(size: int, propositions: Sequence[str]) -> Iterator[str]:
    """Every normalized regex AST with exactly ``size`` raw tokens.

    Unlike significant complexity, *raw* size is compositional, including
    for subexpressions such as T*. In particular, raw |T*| = 2.
    """
    if not isinstance(size, int) or size < 1:
        return
    atoms = _alphabet(propositions)
    if size == 1:
        yield from atoms
        return
    for boolean in boolean_exact_size(size, propositions):
        yield f"[{boolean}]"
    for operand in regex_exact_raw_size(size - 1, propositions):
        # Normalize only the special (T)* spelling to T*: redundant
        # parentheses do not change its significant complexity (which is 1).
        # Its RAW size remains 2 when used inside a larger expression.
        yield "T*" if operand == "T" else f"({operand})*"
    for left_size in range(1, size - 1):
        right_size = size - left_size - 1
        for left in regex_exact_raw_size(left_size, propositions):
            for right in regex_exact_raw_size(right_size, propositions):
                yield f"({left}.{right})"
                yield f"({left}|{right})"


def _outer_parens(text: str) -> str:
    """Remove purely enclosing regex parentheses (not Boolean [] groups)."""
    while text.startswith("(") and text.endswith(")"):
        depth = 0
        closes_at_end = False
        for index, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    closes_at_end = index == len(text) - 1
                    break
        if not closes_at_end:
            break
        text = text[1:-1]
    return text


def _top_level_parts(pattern: str, operator: str) -> list[str]:
    depth = 0
    parts = []
    begin = 0
    in_boolean = False
    for index, char in enumerate(pattern):
        if char == "[":
            in_boolean = True
        elif char == "]":
            in_boolean = False
        elif not in_boolean:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == operator and depth == 0:
                parts.append(pattern[begin:index])
                begin = index + 1
    parts.append(pattern[begin:])
    return parts


def _has_free_prefix(pattern: str) -> bool:
    """Does the regex AST have T* as its first concatenated factor?

    Unnecessary parentheses and associativity must not change the cost.
    No prefix discount is available under a union or a star.
    """
    expression = _outer_parens(pattern)
    if len(_top_level_parts(expression, "|")) > 1:
        return False
    factors = _top_level_parts(expression, ".")
    if len(factors) <= 1:
        return False
    left = _outer_parens(factors[0])
    return left == "T*" or _has_free_prefix(left)


def history_guards_full_exact_cost(
    cost: int, propositions: Sequence[str]
) -> Iterator[str]:
    """All normalized recall guard ASTs with exact *significant* cost.

    T* is represented canonically as the special unconditional regex and
    costs 1, despite its raw two-token syntax. An initial T*. is free.
    Generate guards, not just the mandatory final rule: an earlier (T*, a)
    is permitted and must not be lost.
    """
    if not isinstance(cost, int) or cost < 1:
        return
    seen: set[str] = set()
    if cost == 1:
        seen.add("T*")
        yield "T*"
    for raw in regex_exact_raw_size(cost, propositions):
        for guard in (raw, "T*." + raw):
            # The raw expression T* has significant cost 1 (not 2).
            # It is emitted above; within a larger expression its raw
            # two-token size is retained, except for a free initial T*.
            if guard in seen:
                continue
            if guard == raw and _has_free_prefix(raw):
                # E.g., ((T*.p).q) is normalized to T*.(p.q),
                # which is emitted at the *smaller* significant cost.
                continue
            if regex_complexity(guard) != cost:
                continue
            seen.add(guard)
            yield guard
