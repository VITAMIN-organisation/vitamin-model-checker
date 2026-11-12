"""Shared regex building blocks for formula parsers and CGS validation."""

import re
from typing import NamedTuple

_ALNUM_UNDERSCORE = r"a-zA-Z0-9_"
_LETTER = r"a-zA-Z"

# A proposition, clock or capacity name, in models and formulas (safe_1, gOAL).
NAME_TOKEN = rf"[a-z][{_ALNUM_UNDERSCORE}]*"
NAME_RE = re.compile(rf"^{NAME_TOKEN}$")

# The lexer's word token is wider than NAME_RE so that `Goal` or `Fp` is read as
# one word and the name check refuses it by name, instead of `F` and `p`.
PROPOSITION_TOKEN = rf"[{_LETTER}][{_ALNUM_UNDERSCORE}]*"

# CGS actions may start with a capital (`A`, `block_a1`).
ACTION_NAME_RE = re.compile(rf"^{PROPOSITION_TOKEN}$")

# Agent indices inside coalitions.
AGENT_LIST = r"\d+(?:,\d+)*"
COALITION_ATL_TOKEN = rf"<{AGENT_LIST}>"
COALITION_UNIVERSAL_TOKEN = rf"\[{AGENT_LIST}\]"
EMPTY_COALITION_RE = re.compile(r"<\s*>")

# Comparison operators (clocks, wallets); longest-first so ``>=`` is not ``>``.
COMPARISON_OPERATORS = (">=", "<=", "==", ">", "<")
COMPARISON_OPS_ALT = "|".join(COMPARISON_OPERATORS)
NON_NEGATIVE_INT = r"(?:0|[1-9]\d*)"

# IATL, TCTL, TOL: a word token that does not swallow EX, AX, EF, AG, ...; it
# still reads `Goal` whole so the name check can refuse it by name.
ICTL_PROPOSITION_TOKEN = rf"(?:{NAME_TOKEN}|[A-Z][a-z][{_ALNUM_UNDERSCORE}]*)"

# TCTL / TOL: same lexer constraint as ICTL (single-letter E/A/F/G/U/X/R/W stay operators).
TCTL_TOL_PROPOSITION_TOKEN = ICTL_PROPOSITION_TOKEN

# The boolean constants, written in lowercase in formulas and AST leaves.
BOOLEAN_CONSTANTS = frozenset({"true", "false"})


class OperatorSpelling(NamedTuple):
    """The symbol an operator token stands for and its word spellings."""

    symbol: str
    words: tuple[str, ...]


# The one list of word spellings, by token name. Words are lowercase only. A logic
# lexes only the tokens it declares, but every word here is reserved in all logics
# (KB "Names and keywords", whose word table a test checks against this one).
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

# A letter operator ends where a name would go on (`U` in `p U q`, not in `Up`).
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


# Reserved words that must not be used as atomic proposition names (case-insensitive,
# so `True` and `FALSE` are refused as well: no parser reads them as names).
FORMULA_RESERVED_WORDS = (
    frozenset(word for row in OPERATOR_WORDS.values() for word in row.words)
    | BOOLEAN_CONSTANTS
)

# CapATL's knowledge operator is `K1(...)` or `kcap1(...)`. The lexer reads `kcap`
# with digits as the operator, so in CapATL only the bare `kcap` needs reserving;
# the other logics have no such operator and keep `kcap` as a name.
CAPATL_KNOWLEDGE_WORD = "kcap"
CAPATL_RESERVED_WORDS = FORMULA_RESERVED_WORDS | {CAPATL_KNOWLEDGE_WORD}
# `kcap1`, `kcap42`: the operator itself, so a CapCGS model may not use it as a
# name (no CapATL formula could reach it). `kcap1x` is an ordinary name.
CAPATL_KNOWLEDGE_NAME_RE = re.compile(rf"{CAPATL_KNOWLEDGE_WORD}\d+")

# NatATL capacity coalitions: <{1,2}, 5>.
NATATL_CAPACITY_RE = re.compile(rf"<{{({AGENT_LIST})}},\s*(\d+)>")
NATATL_COALITION_TOKEN = rf"<{{{AGENT_LIST}}},\s*\d+>"

# CapATL paper-style agent set: <{1,2}> (no numeric formula bound).
CAPATL_COALITION_TOKEN = rf"<{{({AGENT_LIST})}}>"

# OATL: <coalition><n>, n >= 0 is the Demon's budget per step.
OATL_COALITION_BUDGET_TOKEN = rf"<{AGENT_LIST}><{NON_NEGATIVE_INT}>"

# COTL: <legion><n>; the legion of demons may be empty, n >= 0.
COTL_LEGION_BUDGET_TOKEN = rf"<(?:{AGENT_LIST})?><{NON_NEGATIVE_INT}>"

# RBATL resource bound: <1,2><3> (bound may be a list; 0 rejected later).
COALITION_BOUND_TOKEN = rf"<{AGENT_LIST}><{AGENT_LIST}>"
COALITION_BOUND_INNER_RE = re.compile(rf"<({AGENT_LIST})><({AGENT_LIST})>")

TRAILING_COALITION_COMMA_RE = re.compile(r"<\d+,>")
# Not after `<1>`: `<1><-5>` is a negative bound, reported by `coalition_bound_error`.
NEGATIVE_AGENT_IN_COALITION_RE = re.compile(r"(?<!\d>)<-\d+>")

# OL demonic cost prefix: <Jk> (e.g. <J5>); ECAI 2023 takes k in N0, so <J0> is valid.
OL_DEMONIC_TOKEN = rf"<J{NON_NEGATIVE_INT}>"
OL_DEMONIC_BOUND_PREFIX_RE = re.compile(rf"^<J({NON_NEGATIVE_INT})>")

# Wallet_ATL: <<1,2:wallet(1, >= 5)>>.
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
