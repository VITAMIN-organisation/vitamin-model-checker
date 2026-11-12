"""Common token definitions shared across all logic parsers."""

# Boolean + core temporal names. A logic with RELEASE or WEAK adds the token itself.
COMMON_TOKEN_NAMES = [
    "LPAREN",
    "RPAREN",
    "AND",
    "OR",
    "NOT",
    "IMPLIES",
    "UNTIL",
    "GLOBALLY",
    "NEXT",
    "EVENTUALLY",
    "FALSE",
    "TRUE",
]
