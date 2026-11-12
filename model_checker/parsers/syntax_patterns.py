"""Shared regex building blocks for formula parsers and CGS validation."""

import re
from typing import NamedTuple

_ALNUM_UNDERSCORE = r"a-zA-Z0-9_"
_LETTER = r"a-zA-Z"

# Proposition, clock and capacity names start lowercase (safe_1, gOAL).
NAME_TOKEN = rf"[a-z][{_ALNUM_UNDERSCORE}]*"
NAME_RE = re.compile(rf"^{NAME_TOKEN}$")

# Wider than NAME_TOKEN so `Fp` lexes as one word and the name check rejects it,
# instead of reading `F` and `p`.
PROPOSITION_TOKEN = rf"[{_LETTER}][{_ALNUM_UNDERSCORE}]*"

# CGS actions may start with a capital (`A`).
ACTION_NAME_RE = re.compile(rf"^{PROPOSITION_TOKEN}$")

AGENT_LIST = r"\d+(?:,\d+)*"
COALITION_ATL_TOKEN = rf"<{AGENT_LIST}>"
COALITION_UNIVERSAL_TOKEN = rf"\[{AGENT_LIST}\]"
EMPTY_COALITION_RE = re.compile(r"<\s*>")

# Longest first, so `>=` is not read as `>`.
COMPARISON_OPERATORS = (">=", "<=", "==", ">", "<")
COMPARISON_OPS_ALT = "|".join(COMPARISON_OPERATORS)
NON_NEGATIVE_INT = r"(?:0|[1-9]\d*)"

# Does not swallow EX, AG, ...; still reads `Goal` whole so the name check rejects it.
ICTL_PROPOSITION_TOKEN = rf"(?:{NAME_TOKEN}|[A-Z][a-z][{_ALNUM_UNDERSCORE}]*)"

TCTL_TOL_PROPOSITION_TOKEN = ICTL_PROPOSITION_TOKEN

BOOLEAN_CONSTANTS = frozenset({"true", "false"})


class OperatorSpelling(NamedTuple):
    """The symbol an operator token stands for and its word spellings."""

    symbol: str
    words: tuple[str, ...]


# Words are lowercase only and reserved in every logic, even one that does not use
# the operator. A test checks this table against the KB "Names and keywords".
OPERATOR_WORDS: dict[str, OperatorSpelling] = {
    "AND": OperatorSpelling("&&", ("and",)),
    "OR": OperatorSpelling("||", ("or",)),
    "NOT": OperatorSpelling("!", ("not",)),
    "IMPLIES": OperatorSpelling("->", ("implies",)),
    "UNTIL": OperatorSpelling("U", ("until",)),
    "GLOBALLY": OperatorSpelling("G", ("globally", "always")),
    "NEXT": OperatorSpelling("X", ("next",)),
    "EVENTUALLY": OperatorSpelling("F", ("eventually",)),
    "RELEASE": OperatorSpelling("R", ("release",)),
    "WEAK": OperatorSpelling("W", ("weak",)),
    "FORALL": OperatorSpelling("A", ("forall",)),
    "EXIST": OperatorSpelling("E", ("exist",)),
    "TIME_SEP": OperatorSpelling(":", ("with",)),
    "IS": OperatorSpelling("is", ("is",)),
}

NOT_FOLLOWED_BY_NAME_CHAR = rf"(?![{_ALNUM_UNDERSCORE}])"


def spelling_regex(spelling: str) -> str:
    """Regex of one spelling; a letter spelling must end the word (`and`, not `android`)."""
    suffix = NOT_FOLLOWED_BY_NAME_CHAR if spelling.isalpha() else ""
    return re.escape(spelling) + suffix


def spelling_to_symbol(*tokens: str) -> dict[str, str]:
    """Map every spelling of `tokens` to its symbol (`not` and `!` to `!`)."""
    return {
        spelling: row.symbol
        for row in (OPERATOR_WORDS[token] for token in tokens)
        for spelling in (row.symbol, *row.words)
    }


def operator_regex(*tokens: str) -> str:
    """Regex group of every spelling of `tokens` (`R`, `release`, `W`, `weak`)."""
    return "(?:" + "|".join(map(spelling_regex, spelling_to_symbol(*tokens))) + ")"


# Checked case-insensitively, so `True` is rejected as a name too.
FORMULA_RESERVED_WORDS = (
    frozenset(word for row in OPERATOR_WORDS.values() for word in row.words)
    | BOOLEAN_CONSTANTS
)

# `kcap` plus digits lexes as CapATL's K operator, so only bare `kcap` is reserved,
# and only in CapATL.
CAPATL_KNOWLEDGE_WORD = "kcap"
CAPATL_RESERVED_WORDS = FORMULA_RESERVED_WORDS | {CAPATL_KNOWLEDGE_WORD}
# A CapCGS name like `kcap1` could never appear in a formula; `kcap1x` is fine.
CAPATL_KNOWLEDGE_NAME_RE = re.compile(rf"{CAPATL_KNOWLEDGE_WORD}\d+")

# NatATL: <{1,2}, 5>
NATATL_CAPACITY_RE = re.compile(rf"<{{({AGENT_LIST})}},\s*(\d+)>")
NATATL_COALITION_TOKEN = rf"<{{{AGENT_LIST}}},\s*\d+>"

# CapATL: <{1,2}>
CAPATL_COALITION_TOKEN = rf"<{{({AGENT_LIST})}}>"

# OATL: <1,2><n>, n is the demon's budget per step.
OATL_COALITION_BUDGET_TOKEN = rf"<{AGENT_LIST}><{NON_NEGATIVE_INT}>"

# COTL: <legion><n>, the legion may be empty.
COTL_LEGION_BUDGET_TOKEN = rf"<(?:{AGENT_LIST})?><{NON_NEGATIVE_INT}>"

# RBATL: <1,2><3>; a 0 bound is rejected later.
COALITION_BOUND_TOKEN = rf"<{AGENT_LIST}><{AGENT_LIST}>"
COALITION_BOUND_INNER_RE = re.compile(rf"<({AGENT_LIST})><({AGENT_LIST})>")

TRAILING_COALITION_COMMA_RE = re.compile(r"<\d+,>")
# Skips `<1><-5>`: that is a negative bound, reported by `coalition_bound_error`.
NEGATIVE_AGENT_IN_COALITION_RE = re.compile(r"(?<!\d>)<-\d+>")

# OL: <J5>; <J0> is valid (ECAI 2023 takes k in N0).
OL_DEMONIC_TOKEN = rf"<J{NON_NEGATIVE_INT}>"
OL_DEMONIC_BOUND_PREFIX_RE = re.compile(rf"^<J({NON_NEGATIVE_INT})>")

# Wallet_ATL: <<1,2:wallet(1, >= 5)>>
_WALLET_ATOM = rf"wallet\(\s*\d+\s*,\s*(?:{COMPARISON_OPS_ALT})\s*\d+\s*\)"
WALLET_COALITION_TOKEN = (
    rf"<<\s*\d+(?:\s*,\s*\d+)*\s*(?::\s*{_WALLET_ATOM}"
    rf"(?:\s*&&\s*{_WALLET_ATOM})*)?\s*>>"
)
WALLET_COALITION_HEADER_RE = re.compile(r"<<\s*([^:>]*)(?::(.*))?>>")
WALLET_COALITION_PREFIX_RE = re.compile(
    r"^<<\s*(?P<agents>\d+(?:\s*,\s*\d+)*)\s*(?::\s*(?P<constraints>.*?))?\s*>>"
)
WALLET_CONSTRAINT_AND_RE = re.compile(r"\s*&&\s*")
WALLET_CONSTRAINT_RE = re.compile(
    rf"wallet\(\s*(?P<agent>\d+)\s*,\s*(?P<operator>{COMPARISON_OPS_ALT})\s*(?P<value>\d+)\s*\)"
)
