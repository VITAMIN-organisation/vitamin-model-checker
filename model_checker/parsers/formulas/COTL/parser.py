"""COTL parser (PLY-based).

Supported:
- Same surface as OATL: coalition and demonic bounds (`<1,2><5>F p`).
- Boolean connectives (&&, ||, !, ->) and temporal ops (U, R, W, G, X, F).

Rejects:
- Missing demonic bounds after a coalition (e.g., `<1>F p`).
- Malformed coalitions or invalid agent indices relative to n_agent.
- Non-ASCII, null bytes, or disallowed special characters in propositions.

Returns:
- AST tuple on success, or None on invalid input.
"""

import re

from ..OATL.parser import OATLParser
from ..parser_utils import (
    BOOLEAN_AST_OPERATORS,
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    validate_ast,
    validate_coalition_bound_token,
)
from ..shared_parser import BaseLogicParser

_COTL_COALITION_OPERATOR_PATTERN = re.compile(
    r"^<\d+(?:,\d+)*><[1-9]\d*>(F|G|X|U|R|W|UNTIL|RELEASE|WEAK|NEXT|EVENTUALLY|GLOBALLY)$",
    re.IGNORECASE,
)
_COTL_VALID_OPERATORS = (
    frozenset(
        {
            "U",
            "X",
            "F",
            "G",
            "R",
            "W",
            "UNTIL",
            "RELEASE",
            "WEAK",
            "NEXT",
            "EVENTUALLY",
            "GLOBALLY",
        }
    )
    | BOOLEAN_AST_OPERATORS
)


class COTLParser(OATLParser):
    """OATL surface syntax with Release/Weak Until; used by the COTL checker."""

    def __init__(self):
        """Initialize COTL lexer/parser with R/W tokens and productions."""
        BaseLogicParser.__init__(self)
        self.tokens.extend(
            [
                "COALITION_DEMONIC",
                "PROP",
                "UNTIL",
                "RELEASE",
                "WEAK",
                "GLOBALLY",
                "NEXT",
                "EVENTUALLY",
            ]
        )
        self.max_coalition = 0
        self.build()

    t_PROP = PROPOSITION_TOKEN_PATTERN
    t_COALITION_DEMONIC = r"<\d+(?:,\d+)*><[1-9]\d*>"

    def t_RELEASE(self, t):
        r"R(?![a-zA-Z0-9_])|release\b"
        t.value = "R"
        return t

    def t_WEAK(self, t):
        r"W(?![a-zA-Z0-9_])|weak\b"
        t.value = "W"
        return t

    def p_expression_ternary(self, p):
        """expression : COALITION_DEMONIC expression UNTIL expression
        | COALITION_DEMONIC expression WEAK expression
        | COALITION_DEMONIC expression RELEASE expression"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_pattern=r"[1-9]\d*"
        )
        p[0] = (p[1] + p[3], p[2], p[4])

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            extra_invalid_regexes=(),
        )
        if not valid:
            return False, err
        return self._coalition_bound_pre_validation(formula)

    def _post_validation(self, formula, result):
        if result is None:
            return False
        return validate_ast(
            result,
            _COTL_VALID_OPERATORS,
            coalition_pattern=_COTL_COALITION_OPERATOR_PATTERN,
        )
