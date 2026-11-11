"""ATL parser (PLY): coalitions `<1,2>`, with agents 1 to `n_agent`, before U, G, X
and F."""

from model_checker.parsers.formulas.parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    until_operands,
    validate_coalition,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.syntax_patterns import COALITION_ATL_TOKEN


class ATLParser(BaseLogicParser):
    """`parse` returns an AST tuple, or None with the reason in `errors`."""

    def __init__(self):
        """Initialize the ATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(["COALITION", "PROP"])
        self.n_agent = 0
        self.build()

    # --- Specific Tokens ---
    t_COALITION = COALITION_ATL_TOKEN
    t_PROP = PROPOSITION_TOKEN_PATTERN

    # --- Grammar Rules ---
    def p_expression_ternary(self, p):
        """expression : COALITION expression UNTIL expression
        | COALITION LPAREN expression UNTIL expression RPAREN"""
        coalition_str = p[1]
        validate_coalition(coalition_str, self.n_agent)
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : COALITION GLOBALLY expression
        | COALITION NEXT expression
        | COALITION EVENTUALLY expression"""
        coalition_str = p[1]
        validate_coalition(coalition_str, self.n_agent)
        p[0] = (p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    # --- Validation ---
    def parse(self, formula, n_agent=0, **kwargs):
        self.n_agent = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            allow_negative_agents=False,
            allowed_operators=None,
        )
