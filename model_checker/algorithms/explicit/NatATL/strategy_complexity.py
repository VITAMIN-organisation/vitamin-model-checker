"""NatATL memoryless complexity, Natural Strategic Ability, Section 4.1."""

import re

_TOKEN = re.compile(
    r"\s*(&&|\|\||!|\(|\)|[A-Za-z_][A-Za-z_0-9]*)"
)


def guard_complexity(guard: str) -> int:
    """Count propositional symbols, excluding parentheses."""
    tokens = []
    pos = 0

    while pos < len(guard):
        match = _TOKEN.match(guard, pos)

        if match is None:
            if guard[pos:].isspace():
                break
            raise ValueError(
                f"Invalid guard near {guard[pos:]!r}"
            )

        tokens.append(match.group(1))
        pos = match.end()

    if not tokens:
        raise ValueError("Empty guard")

    index = 0

    def factor():
        nonlocal index

        if index >= len(tokens):
            raise ValueError("Missing Boolean operand")

        token = tokens[index]
        index += 1

        if token == "!" or token.lower() == "not":
            factor()

        elif token == "(":
            expression(0)

            if index >= len(tokens) or tokens[index] != ")":
                raise ValueError("Unclosed parenthesis")

            index += 1

        elif (
            token.lower() in ("and", "or")
            or token in ("&&", "||", ")")
        ):
            raise ValueError(f"Unexpected token {token}")

    def expression(min_precedence):
        nonlocal index
        factor()

        while index < len(tokens):
            operator = tokens[index].lower()
            precedence = {
                "&&": 2,
                "and": 2,
                "||": 1,
                "or": 1,
            }.get(operator, -1)

            if precedence < min_precedence:
                break

            index += 1
            expression(precedence + 1)

    expression(0)

    if index != len(tokens):
        raise ValueError(
            f"Unexpected suffix: {tokens[index:]}"
        )

    return sum(
        token not in ("(", ")")
        for token in tokens
    )


def individual_complexity(
    rules: list[tuple[str, str]],
) -> int:
    return sum(
        guard_complexity(guard)
        for guard, _action in rules
    )


def collective_complexity(
    profile: dict[int, list[tuple[str, str]]],
) -> int:
    return sum(
        individual_complexity(rules)
        for rules in profile.values()
    )
