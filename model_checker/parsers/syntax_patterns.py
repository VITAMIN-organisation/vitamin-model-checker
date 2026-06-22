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
EMPTY_COALITION_RE = re.compile(r"<\s*>")

# ICTL: lowercase atoms or mixed-case with lowercase from the second character
# (avoids lexing EX, AX, EF, AG, ... as proposition names).
ICTL_PROPOSITION_TOKEN = (
    rf"(?:[a-z][{_ALNUM_UNDERSCORE}]*|[A-Z][a-z][{_ALNUM_UNDERSCORE}]*)"
)

# TCTL / TOL: same lexer constraint as ICTL (single-letter E/A/F/G/U/X/R/W stay operators).
TCTL_TOL_PROPOSITION_TOKEN = ICTL_PROPOSITION_TOKEN

# NatSL temporal atoms after F / !F (single letters a-h only).
NATSL_TEMPORAL_PROPOSITION_TOKEN = r"[a-h]"

# NatATL capacity coalitions: <{1,2}, 5>.
NATATL_CAPACITY_RE = re.compile(rf"<\{{({AGENT_LIST})\}},\s*(\d+)>")
NATATL_COALITION_TOKEN = rf"<\{{(?:\d+,)*\d+\}},\s*\d+>"

# OATL / RBATL coalition-bound suffix: <1,2><3>.
COALITION_BOUND_INNER_RE = re.compile(
    rf"<({AGENT_LIST})><({AGENT_LIST})>"
)

TRAILING_COALITION_COMMA_RE = re.compile(r"<\d+,>")
NEGATIVE_AGENT_IN_COALITION_RE = re.compile(r"<-\d+>")

# OL demonic cost prefix: <Jk> (e.g. <J5>); k must be a positive integer (no <J0>).
OL_DEMONIC_TOKEN = r"<J[1-9]\d*>"
OL_DEMONIC_BOUND_FULL_RE = re.compile(r"^<J([1-9]\d*)>$")
OL_DEMONIC_BOUND_PREFIX_RE = re.compile(r"^<J([1-9]\d*)>")
