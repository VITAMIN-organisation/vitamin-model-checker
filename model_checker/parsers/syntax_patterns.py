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

# NatATL capacity coalitions: <{1,2}, 5>.
NATATL_CAPACITY_RE = re.compile(rf"<\{{({AGENT_LIST})\}},\s*(\d+)>")
NATATL_COALITION_TOKEN = rf"<\{{(?:\d+,)*\d+\}},\s*\d+>"

# OATL / RBATL coalition-bound suffix: <1,2><3>.
COALITION_BOUND_INNER_RE = re.compile(
    rf"<({AGENT_LIST})><({AGENT_LIST})>"
)

TRAILING_COALITION_COMMA_RE = re.compile(r"<\d+,>")
NEGATIVE_AGENT_IN_COALITION_RE = re.compile(r"<-\d+>")

# OL demonic cost prefix: <Jk> (e.g. <J5>).
OL_DEMONIC_TOKEN = r"<J[0-9]+>"
OL_DEMONIC_BOUND_FULL_RE = re.compile(r"^<J(\d+)>$")
OL_DEMONIC_BOUND_PREFIX_RE = re.compile(r"^<J(\d+)>")
