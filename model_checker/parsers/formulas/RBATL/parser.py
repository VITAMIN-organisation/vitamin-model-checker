"""RBATL parser (PLY-based).

Supported:
- Resource-bounded ATL with coalition-bound operators like `<1,2><5>F p` and `<1><3>G p`.
- Boolean connectives (&&, ||, !, ->) and temporal ops (U, G, X, F).

Rejects:
- Release (R) and Weak Until (W) (solver does not evaluate them).
- Coalitions missing a bound (e.g., `<1>F p`).
- Invalid or out-of-range coalition members relative to n_agent.
- Non-ASCII, null bytes, or disallowed special characters.

Returns:
- AST tuple on success, or None on invalid input.
"""

import re

from ..parser_utils import (
    BOOLEAN_AST_OPERATORS,
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    validate_ast,
    validate_coalition_bound_token,
    validate_release_weak_rejected,
)
from ..shared_parser import BaseLogicParser

_RBATL_COALITION_OPERATOR_PATTERN = re.compile(
    r"^<\d+(?:,\d+)*><\d+(?:,\d+)*>(F|G|X|U|UNTIL|NEXT|EVENTUALLY|GLOBALLY)$",
    re.IGNORECASE,
)
_RBATL_VALID_OPERATORS = (
    frozenset({"U", "X", "F", "G", "UNTIL", "NEXT", "EVENTUALLY", "GLOBALLY"})
    | BOOLEAN_AST_OPERATORS
)


class RBATLParser(BaseLogicParser):
    """Parser for RBATL formulas (coalition-bound operators and temporal ops).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set n_agent before parsing for coalition validation.
    """

    def __init__(self):
        """Initialize the RBATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(
            [
                "COALITION_BOUND",
                "PROP",
                "UNTIL",
                "GLOBALLY",
                "NEXT",
                "EVENTUALLY",
            ]
        )
        self.max_coalition = 0
        self.bound_limit = 1_000_000
        self.build()

    t_PROP = PROPOSITION_TOKEN_PATTERN
    t_COALITION_BOUND = r"<\d+(?:,\d+)*><\d+(?:,\d+)*>"

    # === Grammar ===
    def p_expression_ternary(self, p):
        """expression : COALITION_BOUND expression UNTIL expression"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_limit=self.bound_limit
        )
        p[0] = (p[1] + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : COALITION_BOUND GLOBALLY expression
        | COALITION_BOUND NEXT expression
        | COALITION_BOUND EVENTUALLY expression"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_limit=self.bound_limit
        )
        p[0] = (p[1] + p[2], p[3])

    # === Validation ===

    def parse(self, formula, n_agent=0, max_bound=None, **kwargs):
        self.max_coalition = n_agent
        if max_bound is not None:
            self.bound_limit = max_bound

        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            allow_negative_agents=False,
            allowed_operators=None,
        )
        if not valid:
            return False, err

        valid, err = validate_release_weak_rejected(formula, "RBATL")
        if not valid:
            return False, err

        if re.search(r"<\d+(?:,\d+)*>\s*[FGXURW]", formula) and not re.search(
            r"<\d+(?:,\d+)*><\d+(?:,\d+)*>", formula
        ):
            return (
                False,
                "RBATL requires a resource bound (e.g., <1><5>) for temporal operators",
            )
        return True, None

    def _post_validation(self, formula, result):
        if result is None:
            return False
        return validate_ast(
            result,
            _RBATL_VALID_OPERATORS,
            coalition_pattern=_RBATL_COALITION_OPERATOR_PATTERN,
        )
