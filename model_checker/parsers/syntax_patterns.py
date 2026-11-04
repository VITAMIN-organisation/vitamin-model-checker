"""Shared regex building blocks for formula parsers and CGS validation."""

import re

_ALNUM_UNDERSCORE = r"a-zA-Z0-9_"
_LETTER = r"a-zA-Z"

# Atomic propositions and formula proposition tokens (Goal, safe_1).
PROPOSITION_TOKEN = rf"[{_LETTER}][{_ALNUM_UNDERSCORE}]*"
PROPOSITION_FULL_RE = re.compile(rf"^{PROPOSITION_TOKEN}$")
ATOMIC_PROPOSITION_NAME_RE = PROPOSITION_FULL_RE

# Agent indices inside coalitions.
AGENT_LIST = r"\d+(?:,\d+)*"
COALITION_ATL_TOKEN = rf"<{AGENT_LIST}>"
COALITION_UNIVERSAL_TOKEN = rf"\[{AGENT_LIST}\]"
EMPTY_COALITION_RE = re.compile(r"<\s*>")

# Comparison operators (clocks, wallets); longest-first so ``>=`` is not ``>``.
COMPARISON_OPERATORS = (">=", "<=", "==", ">", "<")
COMPARISON_OPS_ALT = "|".join(COMPARISON_OPERATORS)
POSITIVE_INT = r"[1-9]\d*"
NON_NEGATIVE_INT = r"(?:0|[1-9]\d*)"

# ICTL: lowercase atoms or mixed-case with lowercase from the second character
# (avoids lexing EX, AX, EF, AG, ... as proposition names).
ICTL_PROPOSITION_TOKEN = (
    rf"(?:[a-z][{_ALNUM_UNDERSCORE}]*|[A-Z][a-z][{_ALNUM_UNDERSCORE}]*)"
)

# TCTL / TOL: same lexer constraint as ICTL (single-letter E/A/F/G/U/X/R/W stay operators).
TCTL_TOL_PROPOSITION_TOKEN = ICTL_PROPOSITION_TOKEN

# Reserved words that must not be used as atomic proposition names (case-insensitive).
FORMULA_RESERVED_WORDS = frozenset(
    {
        "and",
        "or",
        "not",
        "implies",
        "until",
        "release",
        "globally",
        "next",
        "eventually",
        "always",
        "forall",
        "exist",
    }
)

# NatSL quantifier tokens; uppercase E/A cannot be temporal atoms (lexer ambiguity).
NATSL_QUANTIFIER_TOKENS = frozenset({"E", "A"})

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
NEGATIVE_AGENT_IN_COALITION_RE = re.compile(r"<-\d+>")

# OL demonic cost prefix: <Jk> (e.g. <J5>); k must be a positive integer (no <J0>).
OL_DEMONIC_TOKEN = rf"<J{POSITIVE_INT}>"
OL_DEMONIC_BOUND_FULL_RE = re.compile(rf"^<J({POSITIVE_INT})>$")
OL_DEMONIC_BOUND_PREFIX_RE = re.compile(rf"^<J({POSITIVE_INT})>")

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
