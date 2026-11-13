"""Helpers shared by formula parsers (ATL, CTL, NatATL, OATL, and others).

Coalition checks, lexer token checks, and pre-parse validation live here.
"""

import re
import unicodedata
from collections.abc import Sequence
from typing import Generic, NamedTuple, TypeVar

from model_checker.parsers.syntax_patterns import (
    AGENT_LIST,
    BOOLEAN_CONSTANTS,
    COALITION_ATL_TOKEN,
    EMPTY_COALITION_RE,
    FORMULA_RESERVED_WORDS,
    NAME_RE,
    NAME_TOKEN,
    NATATL_CAPACITY_RE,
    NATATL_COALITION_TOKEN,
    NEGATIVE_AGENT_IN_COALITION_RE,
    NOT_FOLLOWED_BY_NAME_CHAR,
    PROPOSITION_TOKEN,
    TRAILING_COALITION_COMMA_RE,
    operator_regex,
)

PROPOSITION_TOKEN_PATTERN = PROPOSITION_TOKEN

_INVALID_PROPOSITION_MSG = (
    "a name starts with a lowercase letter, then letters, digits or _ "
    f"({NAME_TOKEN})"
)

# Modal/path tokens must not be substrings of proposition identifiers (Goal, Flux).
_MODAL_TOKEN_PREFIX = r"(?:^|(?<![a-zA-Z0-9_]))"
_MODAL_TOKEN_SUFFIX = NOT_FOLLOWED_BY_NAME_CHAR

# Any spelling of these operators, as a whole word (`R`, `release`, not `Rx`).
_RELEASE_OR_WEAK = _MODAL_TOKEN_PREFIX + operator_regex("RELEASE", "WEAK")
_CTL_UNARY_RE = re.compile(
    _MODAL_TOKEN_PREFIX + operator_regex("NEXT", "EVENTUALLY", "GLOBALLY")
)
_CTL_UNTIL_RE = re.compile(_MODAL_TOKEN_PREFIX + operator_regex("UNTIL"))
_CTL_TEMPORAL_RE = re.compile(
    _MODAL_TOKEN_PREFIX + operator_regex("NEXT", "EVENTUALLY", "GLOBALLY", "UNTIL")
)
_CTL_QUANTIFIER_RE = re.compile(_MODAL_TOKEN_PREFIX + operator_regex("FORALL", "EXIST"))


def until_operands(p) -> tuple:
    """Return `(left, operator, right)` of the production `prefix x OP y` or
    `prefix ( x OP y )`, where `p[1]` is the prefix; both forms build one tree."""
    return tuple(p[2:5] if len(p) == 5 else p[3:6])


_V = TypeVar("_V")


class NodeMarks(Generic[_V]):
    """AST nodes marked during one parse, each with an optional value. It keeps the
    nodes, not their ids, because a freed node's id can be reused by a later one."""

    def __init__(self) -> None:
        self._marks: dict[int, tuple[object, _V | None]] = {}

    def mark(self, node: object, value: _V | None = None) -> None:
        self._marks[id(node)] = (node, value)

    def __contains__(self, node: object) -> bool:
        entry = self._marks.get(id(node))
        return entry is not None and entry[0] is node

    def value(self, node: object) -> _V | None:
        return self._marks[id(node)][1] if node in self else None


class OpenPrefix(NamedTuple):
    """A prefix whose scope is not closed by parentheses, such as `<1>F` in
    `<1>F p`; `operator` is set for a prefix over an Until, such as `<1> p U q`."""

    prefix: str
    position: int
    operator: str | None = None


def ambiguous_prefix_message(
    prefix: str, connective: str, operator: str | None = None
) -> str:
    """The error for a connective after an unclosed prefix, as in `AF p && q`, which
    has two readings; `operator` is the U, R or W of a prefix Until."""
    if operator is None:
        shown = f"{prefix} ... {connective} ..."
        both = f"{prefix} (... {connective} ...)"
        left = f"({prefix} ...) {connective} ..."
    else:
        shown = f"{prefix} ... {operator} ... {connective} ..."
        both = f"{prefix} (... {operator} (... {connective} ...))"
        left = f"({prefix} (... {operator} ...)) {connective} ..."
    return (
        f"'{shown}' is ambiguous: write {both} for {prefix} over both sides, "
        f"or {left} for {prefix} over the left side only"
    )


def ambiguous_prefix_error(open_prefix: OpenPrefix, connective: str) -> ValueError:
    prefix, position, operator = open_prefix
    message = ambiguous_prefix_message(prefix, connective, operator)
    return ValueError(f"{message} (position {position})")


class CoalitionValueError(Exception):
    """Bad coalition syntax or an agent index outside the allowed range."""


def normalize_formula_text(formula: str) -> str:
    """NFKC-normalize, strip BOM/nbsp, and collapse whitespace."""
    text = unicodedata.normalize("NFKC", formula)
    text = text.replace("\ufeff", "").replace("\u00a0", " ")
    return " ".join(text.strip().split())


def validate_proposition_identifier(
    name: str,
    *,
    reserved_words: frozenset[str] = FORMULA_RESERVED_WORDS,
    kind: str = "Atomic proposition",
) -> tuple[bool, str | None]:
    """Return (True, None) when name is a valid atomic proposition identifier.

    Applies the shared model/formula alphabet and rejects reserved keywords.
    `kind` names what the identifier is in the message: clocks and capacities,
    in models and formulas, follow the same rule.
    """
    # Reserved words first, so `True` is reported as the constant it spells.
    if name.lower() in reserved_words:
        return (
            False,
            f"{kind} {name!r} clashes with reserved keyword.",
        )
    if not NAME_RE.match(name):
        return (
            False,
            f"{kind} {name!r} is invalid: {_INVALID_PROPOSITION_MSG}.",
        )
    return True, None


def validate_natsl_temporal_atom(atom: str) -> tuple[bool, str | None]:
    """Validate the proposition after F, G or X in a NatSL goal; the constants `true`
    and `false` are accepted, as in every other logic."""
    if atom in BOOLEAN_CONSTANTS:
        return True, None
    return validate_proposition_identifier(atom)


_COALITION_RE = re.compile(COALITION_ATL_TOKEN)
_COALITION_AND_BOUND_RE = re.compile(rf"{COALITION_ATL_TOKEN}\s*{COALITION_ATL_TOKEN}")
# A coalition, not itself a bound (`<5>` of `<1><5>` comes right after `1>`),
# then a space and its bound.
_SPACED_BOUND_RE = re.compile(rf"(?<!\d>){COALITION_ATL_TOKEN}\s+{COALITION_ATL_TOKEN}")


_NEGATIVE_BOUND_RE = re.compile(r"\d><-\d")
_LEADING_ZERO_BOUND_RE = re.compile(rf"<{AGENT_LIST}><(?:\d+,)*0\d")


def coalition_bound_error(formula: str, missing_message: str) -> str | None:
    """The error for a coalition bound written with a leading zero (`<1><05>F p`,
    `<1><2,05>F p`), spaced off (`<1> <5>F p`) or missing (`<1> F p`,
    `<1> p until q`, whatever operator follows) or negative (`<1><-5>F p`), else
    None. A bare `0` is a valid bound."""
    if _NEGATIVE_BOUND_RE.search(formula):
        return "Bound must not be negative"
    if _LEADING_ZERO_BOUND_RE.search(formula):
        return "Bound cannot have leading zeros (e.g., use <1><5>, not <1><05>)"
    if _SPACED_BOUND_RE.search(formula):
        return (
            "The bound follows its coalition with no space: write <1><5>, not <1> <5>"
        )
    if _COALITION_RE.search(_COALITION_AND_BOUND_RE.sub(" ", formula)):
        return missing_message
    return None


def demonic_leading_zero_error(
    formula: str, leading_zero_re: re.Pattern[str]
) -> str | None:
    """The error for a Demon grade with a leading zero (`<J01>`, `{J01}`), else None."""
    leading_zero = leading_zero_re.search(formula)
    if leading_zero is None:
        return None
    bound, digits = leading_zero.group(0), leading_zero.group(1)
    fixed = bound.replace(digits, str(int(digits)))
    return f"Bound '{bound}' has a leading zero; write {fixed}"


def validate_release_weak_rejected(
    formula: str, logic_name: str
) -> tuple[bool, str | None]:
    """Reject R and W (or the words release and weak), glued (`<1><5>R p`) or infix
    (`<1><5> p R q`), for a logic whose solver lacks them; propositions such as
    ``r`` or ``p_weak`` stay valid."""
    prefix = rf"(?:{COALITION_ATL_TOKEN}|{NATATL_COALITION_TOKEN})"
    if re.search(rf"{prefix}.*?{_RELEASE_OR_WEAK}", formula):
        return (
            False,
            f"{logic_name} does not support Release (R) or Weak Until (W) operators",
        )
    return True, None


def validate_ctl_path_quantifiers(formula: str) -> tuple[bool, str | None]:
    """Reject a CTL temporal operator with no A or E before it; names such as `Goal`
    are not mistaken for `G`."""
    stripped = formula.strip()
    if not stripped:
        return True, None

    if _CTL_UNARY_RE.match(stripped):
        return (
            False,
            "Temporal operators (X, F, G) must be preceded by a quantifier (A or E)",
        )

    if _CTL_UNTIL_RE.match(stripped):
        return (
            False,
            "UNTIL operator (U) must be preceded by a quantifier (A or E)",
        )

    has_temporal = _CTL_TEMPORAL_RE.search(stripped)
    has_quantifier = _CTL_QUANTIFIER_RE.search(stripped)
    if has_temporal and not has_quantifier:
        return (
            False,
            "Temporal operators must be preceded by a path quantifier (A or E) in CTL",
        )
    return True, None


def validate_agents(
    agents: list[int], max_coalition: int, member: str = "agent"
) -> None:
    """Raise CoalitionValueError unless each agent is between 1 and `max_coalition`
    and listed once: a coalition is a set of agents (ATL, JACM 2002 p. 685).
    `member` names the agents in the duplicate message (COTL's are demons)."""
    limit = int(max_coalition)
    seen: set[int] = set()
    for agent in agents:
        if agent <= 0 or agent > limit:
            raise CoalitionValueError(
                f"Invalid coalition value {agent}: must be between 1 and {max_coalition}"
            )
        if agent in seen:
            raise CoalitionValueError(f"Duplicate {member} {agent} in coalition")
        seen.add(agent)


def validate_coalition(coalition_str: str, max_coalition: int) -> None:
    """Raise CoalitionValueError unless a coalition such as `<1,2,3>` passes
    `validate_agents`."""
    if coalition_str == "<>" or EMPTY_COALITION_RE.fullmatch(coalition_str):
        raise CoalitionValueError("Empty coalition '<>' is not allowed")
    if coalition_str.endswith(",>"):
        raise CoalitionValueError("Trailing comma in coalition is not allowed")

    coalition_values = re.findall(r"\d+", coalition_str)
    if not coalition_values:
        raise CoalitionValueError("Empty coalition not allowed")

    validate_agents([int(value) for value in coalition_values], max_coalition)


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

    When bound_limit is set, every bound number must be between 0 and that limit.
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
            if value > bound_limit:
                raise CoalitionValueError(
                    f"Invalid bound value {value}: must be between 0 and {bound_limit}"
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

    if int(k_value) < 1:
        raise CoalitionValueError(f"Invalid bound {k_value}: must be at least 1")
    # AGENT_LIST in the regex already rules out an empty list and a trailing comma.
    validate_agents(
        [int(value) for value in coalition_values.split(",")], max_coalition
    )

    return coalition_values, k_value


def validate_formula_basic(formula) -> tuple[bool, str | None]:
    """Reject empty or whitespace-only formulas."""
    if not formula or not formula.strip():
        return False, "Formula cannot be empty"
    return True, None


def validate_formula_unicode(formula) -> tuple[bool, str | None]:
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
) -> tuple[bool, str | None]:
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
    allowed_operators: set[str] | None = None,
    extra_invalid_regexes: Sequence[str] = (),
) -> tuple[bool, str | None]:
    """Run the standard checks before PLY parsing.

    Returns (True, None) if the formula passes, else (False, error_message).
    """
    valid, err = validate_formula_basic(formula)
    if not valid:
        return False, err

    if "\x00" in formula:
        return False, "Formula contains binary null character"

    if coalition_required:
        if EMPTY_COALITION_RE.search(formula):
            return False, "Empty coalition '<>' is not allowed"
        if TRAILING_COALITION_COMMA_RE.search(formula):
            return False, "Trailing comma in coalition is not allowed"
        if not allow_negative_agents and NEGATIVE_AGENT_IN_COALITION_RE.search(formula):
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


# Re-export for CGS modules that already import from parser_utils.
__all__ = [
    "CoalitionValueError",
    "PROPOSITION_TOKEN_PATTERN",
    "normalize_formula_text",
    "run_common_prechecks",
    "validate_agents",
    "validate_coalition",
    "validate_coalition_bound_token",
    "validate_ctl_path_quantifiers",
    "validate_natsl_temporal_atom",
    "validate_natatl_coalition",
    "validate_proposition_identifier",
    "validate_release_weak_rejected",
]
