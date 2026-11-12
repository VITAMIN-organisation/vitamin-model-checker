"""RBATL parser (PLY): coalition and resource bound `<1,2><5>` before U, G, X and F.

R and W are rejected because the solver does not evaluate them.
"""

from model_checker.parsers.syntax_patterns import COALITION_BOUND_TOKEN

from ..parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    has_coalition_without_bound,
    run_common_prechecks,
    until_operands,
    validate_coalition_bound_token,
    validate_release_weak_rejected,
)
from ..shared_parser import BaseLogicParser

_DEFAULT_BOUND_LIMIT = 1_000_000


class RBATLParser(BaseLogicParser):
    """`parse` returns an AST tuple, or None with the reason in `errors`."""

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
        self.bound_limit = _DEFAULT_BOUND_LIMIT
        self.build()

    t_PROP = PROPOSITION_TOKEN_PATTERN
    t_COALITION_BOUND = COALITION_BOUND_TOKEN

    # === Grammar ===
    def p_expression_ternary(self, p):
        """expression : COALITION_BOUND expression UNTIL expression
        | COALITION_BOUND LPAREN expression UNTIL expression RPAREN"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_limit=self.bound_limit
        )
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : COALITION_BOUND GLOBALLY expression
        | COALITION_BOUND NEXT expression
        | COALITION_BOUND EVENTUALLY expression"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_limit=self.bound_limit
        )
        p[0] = (p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    # === Validation ===

    def parse(self, formula, n_agent=0, max_bound=None, **kwargs):
        self.max_coalition = n_agent
        self.bound_limit = max_bound if max_bound is not None else _DEFAULT_BOUND_LIMIT
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

        if has_coalition_without_bound(formula):
            return (
                False,
                "RBATL requires a resource bound (e.g., <1><5>) for temporal operators",
            )
        return True, None
