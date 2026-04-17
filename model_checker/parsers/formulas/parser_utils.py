"""Shared utility functions for logic formula parsers.

Provides coalition validation, token verification, and common prechecks
used by ATL, NatATL, OATL, and other parsers.
"""

import re
from typing import Any, Optional, Sequence, Set


class CoalitionValueError(Exception):
    """Raised when a coalition string or bound is invalid (format or range)."""

    pass


def verify_token(
    lexer: Any,
    token_name: str,
    string: str,
    case_sensitive: bool = True,
) -> bool:
    """Check whether a token of the given type appears in the string.

    Args:
        lexer: PLY lexer instance.
        token_name: Token type name (e.g. COALITION, PROP).
        string: Input string to scan.
        case_sensitive: If False, compare token value and string in lower case.

    Returns:
        True if the token appears in the string, else False.
    """
    lexer.input(string)
    for token in lexer:
        if token.type == token_name:
            if case_sensitive:
                if token.value in string:
                    return True
            else:
                token_value = (
                    token.value.lower()
                    if isinstance(token.value, str)
                    else str(token.value)
                )
                string_lower = string.lower()
                if token_value in string_lower:
                    return True
    return False


def validate_coalition(coalition_str: str, max_coalition: int) -> None:
    """Validate coalition string format and agent numbers.

    Args:
        coalition_str: String like "<1,2,3>".
        max_coalition: Maximum allowed agent number (1-based).

    Raises:
        CoalitionValueError: If format is invalid or any agent is out of range.
    """
    if coalition_str == "<>" or coalition_str.endswith(",>"):
        raise CoalitionValueError("Empty coalition or trailing comma not allowed")

    coalition_values = re.findall(r"\d+", coalition_str)
    if not coalition_values:
        raise CoalitionValueError("Empty coalition not allowed")

    for value in coalition_values:
        agent_num = int(value)
        if agent_num <= 0 or agent_num > int(max_coalition):
            raise CoalitionValueError(
                f"Invalid coalition value {value}: must be between 1 and {max_coalition}"
            )


def validate_coalition_pattern(coalition_str, pattern, max_coalition):
    """Validate a coalition pattern (e.g., coalition-bound or coalition-demonic)."""
    match = re.match(pattern, coalition_str)
    if not match:
        raise CoalitionValueError("Invalid coalition format")

    coalition_only = "<" + match.group(1) + ">"
    validate_coalition(coalition_only, max_coalition)
    return coalition_only, match


def validate_coalition_bound_token(
    coalition_bound_str,
    max_coalition,
    bound_pattern=r"\d+(?:,\d+)*",
    bound_limit=None,
):
    """Validate a coalition-bound token of the form <coalition><bound>."""
    pattern = rf"<(\d+(?:,\d+)*)><({bound_pattern})>"
    coalition_only, match = validate_coalition_pattern(
        coalition_bound_str, pattern, max_coalition
    )

    if bound_limit is not None:
        bound_values = [int(value) for value in match.group(2).split(",")]
        for value in bound_values:
            if value <= 0 or value > bound_limit:
                raise CoalitionValueError(
                    f"Invalid bound value {value}: must be between 1 and {bound_limit}"
                )

    return coalition_only


def validate_natatl_coalition(coalition_str: str, max_coalition: int) -> tuple[str, str]:
    """Validate NatATL coalition format.

    Accepts only canonical capacity syntax: <{1,2}, 5>.

    Returns:
        (coalition_values, k_value) where coalition_values is a comma-separated
        list of agent indices without braces, and k_value is the (string) bound.
    """
    capacity_match = re.match(r"<\{((?:\d+,)*\d+)\},\s*(\d+)>", coalition_str)
    if not capacity_match:
        raise CoalitionValueError(
            f"Invalid NatATL coalition format: {coalition_str} "
            "(expected <{agent,...}, bound>, e.g. <{1,2}, 3>)"
        )
    coalition_values = capacity_match.group(1)
    k_value = capacity_match.group(2)

    if not coalition_values or coalition_values.strip() == "":
        raise CoalitionValueError("Empty coalition not allowed")
    if coalition_values.endswith(","):
        raise CoalitionValueError("Trailing comma in coalition not allowed")

    agent_list = [v.strip() for v in coalition_values.split(",") if v.strip()]
    if not agent_list:
        raise CoalitionValueError("Empty coalition not allowed")

    for value in agent_list:
        agent_num = int(value)
        if agent_num <= 0 or agent_num > int(max_coalition):
            raise CoalitionValueError(
                f"Invalid coalition value {value}: must be between 1 and {max_coalition}"
            )

    return coalition_values, k_value


def validate_formula_basic(formula) -> tuple[bool, Optional[str]]:
    """Basic formula validation: reject empty formulas."""
    if not formula or not formula.strip():
        return False, "Formula cannot be empty"
    return True, None


def validate_formula_unicode(formula) -> tuple[bool, Optional[str]]:
    """Validate formula doesn't contain unicode characters."""
    for idx, c in enumerate(formula):
        if ord(c) > 127:
            return (
                False,
                f"Invalid character '{c}' at position {idx + 1}: Non-ASCII characters are not allowed",
            )
    return True, None


def validate_formula_special_chars(
    formula, allowed_operators=None, allow_hash_at=False
) -> tuple[bool, Optional[str]]:
    """Validate formula doesn't contain invalid special characters."""
    if allowed_operators is None:
        allowed_operators = set("<>(),!&|->")

    invalid_special = set("@#$%^*+=[]{}|\\;:'\"?/~`")

    i = 0
    while i < len(formula):
        c = formula[i]
        if c.isalnum() or c == "_" or c.isspace():
            i += 1
            continue

        if c in allowed_operators:
            i += 1
            continue

        if allow_hash_at and c in ["#", "@"]:
            i += 1
            continue

        # Check if | is part of || operator
        if c == "|" and i + 1 < len(formula) and formula[i + 1] == "|":
            i += 2
            continue

        if c in invalid_special:
            return False, f"Invalid character '{c}' at position {i + 1}"

        i += 1

    return True, None


def run_common_prechecks(
    formula: str,
    *,
    allow_hash_at: bool = False,
    coalition_required: bool = True,
    allow_negative_agents: bool = False,
    allowed_uppercase: Optional[Set[str]] = None,
    allowed_operators: Optional[Set[str]] = None,
    extra_invalid_regexes: Sequence[str] = (),
) -> tuple[bool, Optional[str]]:
    """Run shared pre-parse checks (basic, unicode, special chars, coalition, regex).

    Returns:
        (bool, Optional[str]): (is_valid, error_message)
    """
    valid, err = validate_formula_basic(formula)
    if not valid:
        return False, err

    if "\x00" in formula:
        return False, "Formula contains binary null character"

    if coalition_required:
        if "<>" in formula:
            return False, "Empty coalition '<>' is not allowed"
        if re.search(r"<\d+,>", formula):
            return False, "Trailing comma in coalition is not allowed"
        if not allow_negative_agents and re.search(r"<-\d+", formula):
            return False, "Negative agent indices are not allowed"

    valid, err = validate_formula_unicode(formula)
    if not valid:
        return False, err

    valid, err = validate_formula_special_chars(
        formula, allowed_operators=allowed_operators, allow_hash_at=allow_hash_at
    )
    if not valid:
        return False, err

    if allowed_uppercase is not None:
        uppercase_letters = set(re.findall(r"[A-Z]", formula))
        illegal = uppercase_letters - set(allowed_uppercase)
        if illegal:
            chars = ", ".join(sorted(illegal))
            return False, f"Illegal uppercase characters: {chars}"

    for pattern in extra_invalid_regexes:
        if re.search(pattern, formula):
            return False, f"Formula contains forbidden pattern: {pattern}"

    return True, None


def validate_ast(
    result, valid_operators, coalition_pattern=None, extra_atom_patterns=()
):
    """Validate parsed AST nodes against allowed operators and patterns."""

    def _is_valid_atom(node_str):
        if node_str in valid_operators or node_str.upper() in valid_operators:
            return True
        if coalition_pattern and coalition_pattern.match(node_str):
            return True
        for pat in extra_atom_patterns:
            if pat.match(node_str):
                return True
        return False

    def _walk(node):
        if isinstance(node, str):
            return _is_valid_atom(node) or bool(
                re.match(r"^[a-z][a-z0-9_]*$", node)
                or re.match(r"^\d+[a-z0-9_]*$", node)
            )
        if isinstance(node, tuple):
            return all(_walk(child) for child in node)
        return False

    return _walk(result)
