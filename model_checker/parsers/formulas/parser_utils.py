"""Helpers shared by formula parsers (ATL, CTL, NatATL, OATL, and others).

Coalition checks, lexer token checks, and pre-parse validation live here.
"""

import re
from typing import Any, Optional, Sequence, Set

from model_checker.parsers.syntax_patterns import (
    AGENT_LIST,
    ATOMIC_PROPOSITION_NAME_RE,
    NATATL_CAPACITY_RE,
    NEGATIVE_AGENT_IN_COALITION_RE,
    PROPOSITION_FULL_RE,
    PROPOSITION_TOKEN,
    TRAILING_COALITION_COMMA_RE,
)

# Backward-compatible names used by logic parsers.
PROPOSITION_TOKEN_PATTERN = PROPOSITION_TOKEN
PROPOSITION_AST_PATTERN = PROPOSITION_FULL_RE


class CoalitionValueError(Exception):
    """Bad coalition syntax or an agent index outside the allowed range."""

    pass


def verify_token(
    lexer: Any,
    token_name: str,
    string: str,
    case_sensitive: bool = True,
) -> bool:
    """Return True if the lexer finds at least one token of the given type in string."""
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
    """Check ATL-style coalitions like "<1,2,3>".

    "<>" is allowed (empty coalition). Each agent index must be from 1 to
    max_coalition. Raises CoalitionValueError on failure.
    """
    if coalition_str == "<>":
        return
    if coalition_str.endswith(",>"):
        raise CoalitionValueError("Trailing comma in coalition is not allowed")

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
    """Match coalition_str against pattern, then validate the agent list inside "<...>"."""
    match = re.match(pattern, coalition_str)
    if not match:
        raise CoalitionValueError("Invalid coalition format")

    coalition_only = "<" + match.group(1) + ">"
    validate_coalition(coalition_only, max_coalition)
    return coalition_only, match


def validate_coalition_bound_token(
    coalition_bound_str,
    max_coalition,
    bound_pattern=None,
    bound_limit=None,
):
    """Check tokens like "<1,2><3>" (coalition plus bound suffix).

    When bound_limit is set, every bound number must be between 1 and that limit.
    """
    if bound_pattern is None:
        bound_pattern = AGENT_LIST
    pattern = rf"<({AGENT_LIST})><({bound_pattern})>"
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


def validate_natatl_coalition(
    coalition_str: str, max_coalition: int
) -> tuple[str, str]:
    """Check NatATL capacity syntax only: <{1,2}, 5>.

    Returns (agent_list, k) where agent_list is "1,2" and k is the bound as a string.
    """
    capacity_match = NATATL_CAPACITY_RE.match(coalition_str)
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
    """Reject empty or whitespace-only formulas."""
    if not formula or not formula.strip():
        return False, "Formula cannot be empty"
    return True, None


def validate_formula_unicode(formula) -> tuple[bool, Optional[str]]:
    """Reject non-ASCII characters (formulas must be plain ASCII)."""
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
    """Reject characters that are not letters, digits, whitespace, or allowed operators."""
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

        # Treat || as one operator, not two stray | characters.
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
    allowed_operators: Optional[Set[str]] = None,
    extra_invalid_regexes: Sequence[str] = (),
) -> tuple[bool, Optional[str]]:
    """Run the standard checks before PLY parsing.

    Returns (True, None) if the formula passes, else (False, error_message).
    """
    valid, err = validate_formula_basic(formula)
    if not valid:
        return False, err

    if "\x00" in formula:
        return False, "Formula contains binary null character"

    if coalition_required:
        if TRAILING_COALITION_COMMA_RE.search(formula):
            return False, "Trailing comma in coalition is not allowed"
        if not allow_negative_agents and NEGATIVE_AGENT_IN_COALITION_RE.search(
            formula
        ):
            return False, "Negative agent indices are not allowed"

    valid, err = validate_formula_unicode(formula)
    if not valid:
        return False, err

    valid, err = validate_formula_special_chars(
        formula, allowed_operators=allowed_operators, allow_hash_at=allow_hash_at
    )
    if not valid:
        return False, err

    for pattern in extra_invalid_regexes:
        if re.search(pattern, formula):
            return False, f"Formula contains forbidden pattern: {pattern}"

    return True, None


def validate_ast(
    result, valid_operators, coalition_pattern=None, extra_atom_patterns=()
):
    """Walk the parse tree and ensure every leaf is a known operator, coalition, or proposition."""

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
            return _is_valid_atom(node) or bool(PROPOSITION_AST_PATTERN.match(node))
        if isinstance(node, tuple):
            return all(_walk(child) for child in node)
        return False

    return _walk(result)


# Re-export for CGS modules that already import from parser_utils.
__all__ = [
    "ATOMIC_PROPOSITION_NAME_RE",
    "CoalitionValueError",
    "PROPOSITION_AST_PATTERN",
    "PROPOSITION_TOKEN_PATTERN",
    "run_common_prechecks",
    "validate_ast",
    "validate_coalition",
    "validate_coalition_bound_token",
    "validate_natatl_coalition",
    "verify_token",
]
