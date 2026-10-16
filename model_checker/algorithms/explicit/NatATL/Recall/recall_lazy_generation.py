"""Bounded, cost-ordered enumeration of a CANONICAL NatATL recall fragment.

This module is intentionally independent of the old tree/unfolding solver.
Regex atoms are T and CGS propositions; boolean expressions use !, &&, ||;
regular expressions use ., |, and *. Grouping parentheses/brackets are
syntactic delimiters, not complexity tokens (explicit convention here).

The significant-pattern metric is recursive: ||T*|| = 1 and
||T*.r|| = ||r||. Otherwise it is the raw token count.
Unnecessary grouping and concatenation associativity do not affect cost.
A recall rule list ends with the explicit (T*, IDLE) fallback, of cost 1.
Do not claim completeness for regex syntax outside this canonical fragment.
"""

import re
from collections.abc import Iterator, Mapping, Sequence

from model_checker.algorithms.explicit.NatATL.Recall.history_automaton import (
    HistoryRegex,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
)

_BOOLEAN_TOKENS = re.compile(r"&&|\|\||!|\(|\)|[A-Za-z_][A-Za-z_0-9]*")


def regex_complexity(pattern: str) -> int:
    """Significant-pattern complexity of a recall guard.

    The paper gives the *recursive* clauses
      ||T*|| = 1,   ||T*.r|| = ||r||,   ||r|| = |r| otherwise.
    Concatenation associativity and grouping are normalized for the purpose
    of testing whether an outermost prefix contains T*; no regex operators
    hidden below a union or Kleene star are removed.
    """
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError("Empty history regex")
    tokens = HistoryRegex._lex(pattern.strip())

    def unwrap(part):
        while len(part) >= 2 and part[0][0] == "(":
            depth = 0
            for index, (kind, _) in enumerate(part):
                if kind == "(":
                    depth += 1
                elif kind == ")":
                    depth -= 1
                    if depth == 0:
                        if index == len(part) - 1:
                            part = part[1:-1]
                        else:
                            return part
                        break
            else:
                break
        return part

    def split_top(part, op):
        depth = 0
        pieces = []
        start = 0
        for i, (kind, _) in enumerate(part):
            if kind == "(":
                depth += 1
            elif kind == ")":
                depth -= 1
            elif depth == 0 and kind == op:
                pieces.append(part[start:i])
                start = i + 1
        pieces.append(part[start:])
        return pieces

    def is_tstar(part):
        part = unwrap(part)
        if not part or part[-1][0] != "*":
            return False
        operand = unwrap(part[:-1])
        return len(operand) == 1 and operand[0] in {
            ("guard", "T"), ("guard", "true")
        }

    def factors(part):
        # Only associatively flatten top-level concatenation, never across
        # unions or under a Kleene star.
        part = unwrap(part)
        if len(split_top(part, "|")) > 1:
            return [part]
        chunks = split_top(part, ".")
        if len(chunks) == 1:
            return [part]
        return [factor for chunk in chunks for factor in factors(chunk)]

    def raw_cost(part):
        size = 0
        for kind, value in part:
            if kind == "guard":
                body = value.strip()
                boolean_tokens = _BOOLEAN_TOKENS.findall(body)
                if re.sub(r"\s+", "", "".join(boolean_tokens)) != re.sub(r"\s+", "", body):
                    raise ValueError(f"Malformed Boolean guard {value!r}")
                size += sum(tok not in ("(", ")") for tok in boolean_tokens)
            elif kind in (".", "|", "*"):
                size += 1
        return size

    pieces = factors(tokens)
    # Strip ALL leading universal Kleene-star factors. Applying one free
    # prefix recursively may expose a second free prefix, or T* itself.
    while len(pieces) > 1 and is_tstar(pieces[0]):
        pieces.pop(0)

    if len(pieces) == 1 and is_tstar(pieces[0]):
        return 1

    size = sum(raw_cost(part) for part in pieces) + len(pieces) - 1
    if size < 1:
        raise ValueError("Empty significant history pattern")
    return size


def _boolean_exact_cost(cost: int, propositions: Sequence[str]) -> Iterator[str]:
    """Canonical Boolean guard ASTs of exact symbol cost."""
    if cost < 1:
        return
    if cost == 1:
        yield "T"
        for prop in dict.fromkeys(propositions):
            if prop not in ("T", "true", "false"):
                yield prop
        return
    for child in _boolean_exact_cost(cost - 1, propositions):
        yield f"!({child})"
    for left_cost in range(1, cost - 1):
        right_cost = cost - 1 - left_cost
        for left in _boolean_exact_cost(left_cost, propositions):
            for right in _boolean_exact_cost(right_cost, propositions):
                yield f"({left} && {right})"
                yield f"({left} || {right})"


def regex_exact_cost(cost: int, propositions: Sequence[str]) -> Iterator[str]:
    """Unprefixed, canonical regular expressions of exact cost."""
    if cost < 1:
        return
    if cost == 1:
        yield "T"
        for prop in dict.fromkeys(propositions):
            if prop not in ("T", "true", "false"):
                yield prop
        return

    # Boolean tests taking a single history letter; square brackets
    # disambiguate them from the regex grammar.
    for boolean in _boolean_exact_cost(cost, propositions):
        yield f"[{boolean}]"

    # Single negated atom can also use the recognizer's short form.
    if cost == 2:
        for prop in dict.fromkeys(propositions):
            if prop not in ("T", "true", "false"):
                yield f"!{prop}"

    # Kleene star has cost one plus its operand.
    for operand in regex_exact_cost(cost - 1, propositions):
        yield f"({operand})*"

    # Concatenation and alternative each cost one plus their operands.
    for left_cost in range(1, cost - 1):
        right_cost = cost - 1 - left_cost
        for left in regex_exact_cost(left_cost, propositions):
            for right in regex_exact_cost(right_cost, propositions):
                yield f"({left}.{right})"
                yield f"({left}|{right})"


def history_guards_exact_cost(
    cost: int, propositions: Sequence[str]
) -> Iterator[str]:
    """Generate nonfallback history guards of EXACT significant cost."""
    seen: set[str] = set()
    for regex in regex_exact_cost(cost, propositions):
        # T* is reserved for the final unconditional rule.
        for pattern in (regex, f"T*.{regex}"):
            if pattern == "T*" or pattern in seen:
                continue
            # Grouping-invariant significant cost may be smaller than the
            # raw grammar size, for instance (T)* costs 1, not 2.
            if regex_complexity(pattern) != cost:
                continue
            seen.add(pattern)
            yield pattern


def individual_exact_cost(
    cost: int,
    actions: Sequence[str],
    propositions: Sequence[str],
) -> Iterator[dict]:
    """Recall strategies of exact cost with an explicit (T*, IDLE) fallback."""
    available = tuple(dict.fromkeys(normalize_action_token(a) for a in actions))
    if not available or "IDLE" not in available:
        raise ValueError("Recall strategies require an available IDLE fallback")
    if cost < 1:
        return

    def extend(
        remaining: int,
        rules: tuple[tuple[str, str], ...],
        used_guards: frozenset[str],
    ) -> Iterator[dict]:
        if remaining == 1:
            yield {"condition_action_pairs": list(rules) + [("T*", "IDLE")]}
            return
        for guard_cost in range(1, remaining):
            for guard in history_guards_exact_cost(guard_cost, propositions):
                if guard in used_guards:
                    continue
                for action in available:
                    yield from extend(
                        remaining - guard_cost,
                        rules + ((guard, action),),
                        used_guards | {guard},
                    )

    yield from extend(cost, (), frozenset())


def collective_strategies(
    agents: Sequence[int],
    actions_by_agent: Mapping[int, Sequence[str]],
    propositions: Sequence[str],
    bound: int,
) -> Iterator[list[dict]]:
    """Yield joint recall strategies ordered by TOTAL complexity <= bound."""
    coalition = list(agents)
    if (
        not coalition
        or len(set(coalition)) != len(coalition)
        or any(not isinstance(a, int) or a < 1 for a in coalition)
    ):
        raise ValueError("Expected a nonempty coalition of distinct positive agents")
    if bound < 0:
        raise ValueError("Negative complexity bound")
    if any(a not in actions_by_agent for a in coalition):
        raise ValueError("Missing actions for an agent in the coalition")

    # Even when bound is too small, invalid fallback declarations are errors.
    action_lists = {}
    for agent in coalition:
        actions = tuple(
            dict.fromkeys(normalize_action_token(a) for a in actions_by_agent[agent])
        )
        if "IDLE" not in actions:
            raise ValueError(f"Agent {agent} has no IDLE fallback")
        action_lists[agent] = actions

    count = len(coalition)

    def assign(
        index: int, remaining: int, profile: list[dict]
    ) -> Iterator[list[dict]]:
        if index == count:
            if remaining == 0:
                yield list(profile)
            return
        others = count - index - 1
        for individual_cost in range(1, remaining - others + 1):
            for strategy in individual_exact_cost(
                individual_cost, action_lists[coalition[index]], propositions
            ):
                profile.append(strategy)
                yield from assign(index + 1, remaining - individual_cost, profile)
                profile.pop()

    for total_cost in range(count, bound + 1):
        yield from assign(0, total_cost, [])


def strategy_cost(strategy: dict) -> int:
    """Cost accounting for a single recall rule list."""
    pairs = strategy["condition_action_pairs"]
    if not pairs or pairs[-1] != ("T*", "IDLE"):
        raise ValueError("Missing explicit (T*, IDLE) final fallback")
    return sum(regex_complexity(guard) for guard, _ in pairs)


def profile_cost(profile: Sequence[dict]) -> int:
    return sum(strategy_cost(s) for s in profile)
