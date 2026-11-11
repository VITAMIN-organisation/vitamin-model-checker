"""LTL parser (PLY): the temporal operators X, F, G and U with connectives."""

from ..parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
)
from ..shared_parser import BaseLogicParser


class LTLParser(BaseLogicParser):
    """Parser for LTL formulas (temporal operators X, F, G, U and boolean connectives).

    Use parse(formula) to get an AST tuple or None on invalid input.
    """

    def __init__(self):
        """Initialize the LTL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(["PROP"])
        self.build()

    t_PROP = PROPOSITION_TOKEN_PATTERN

    # --- Grammar Rules ---

    def p_expression_until(self, p):
        "expression : expression UNTIL expression"
        p[0] = ("U", p[1], p[3])

    def p_expression_unary_temporal(self, p):
        """expression : NEXT expression
        | GLOBALLY expression
        | EVENTUALLY expression"""
        p[0] = (p[1], p[2])

    # --- Validation ---

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
        )
