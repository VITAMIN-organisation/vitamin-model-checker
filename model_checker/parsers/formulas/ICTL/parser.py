"""ICTL parser (PLY): path quantifiers A and E over X, F, G, U and R."""

from model_checker.parsers.formulas.parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    until_operands,
    validate_ast,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser

_ICTL_VALID_OPERATORS = frozenset(
    {
        "EX",
        "AX",
        "EF",
        "AF",
        "EG",
        "AG",
        "EU",
        "AU",
        "ER",
        "AR",
        "UNTIL",
        "RELEASE",
        "AND",
        "OR",
        "NOT",
        "IMPLIES",
        "&&",
        "||",
        "!",
        "->",
    }
)


class ICTLParser(BaseLogicParser):
    """Parser for ICTL formulas."""

    def __init__(self):
        """Initialize the ICTL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(
            ["LBRACKET", "RBRACKET", "FORALL", "EXIST", "RELEASE", "PROP"]
        )
        self.precedence = (
            ("right", "IMPLIES"),
            ("left", "OR"),
            ("left", "AND"),
            ("right", "NOT"),
            ("right", "UNTIL", "RELEASE"),
            ("right", "GLOBALLY", "NEXT", "EVENTUALLY"),
        )
        self.build()

    # --- Specific Tokens ---
    t_LBRACKET = r"\["
    t_RBRACKET = r"\]"
    t_PROP = PROPOSITION_TOKEN_PATTERN

    def t_FORALL(self, t):
        r"A(?=[FGXUR\s(\[]|$)|\bforall\b"
        t.value = "A"
        return t

    def t_EXIST(self, t):
        r"E(?=[FGXUR\s(\[]|$)|\bexist\b"
        t.value = "E"
        return t

    def t_RELEASE(self, t):
        r"R(?![a-zA-Z0-9_])|release\b"
        t.value = "R"
        return t

    # --- Grammar Rules ---
    def p_expression_ternary(self, p):
        """expression : FORALL expression UNTIL expression
        | EXIST expression UNTIL expression
        | FORALL expression RELEASE expression
        | EXIST expression RELEASE expression
        | FORALL LPAREN expression UNTIL expression RPAREN
        | EXIST LPAREN expression UNTIL expression RPAREN
        | FORALL LPAREN expression RELEASE expression RPAREN
        | EXIST LPAREN expression RELEASE expression RPAREN
        | FORALL LBRACKET expression UNTIL expression RBRACKET
        | EXIST LBRACKET expression UNTIL expression RBRACKET
        | FORALL LBRACKET expression RELEASE expression RBRACKET
        | EXIST LBRACKET expression RELEASE expression RBRACKET"""
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : FORALL GLOBALLY expression
        | FORALL NEXT expression
        | FORALL EVENTUALLY expression
        | EXIST GLOBALLY expression
        | EXIST NEXT expression
        | EXIST EVENTUALLY expression"""
        p[0] = (p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    # --- Validation ---
    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_operators=set("<>(),[]!&|->"),
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True
        return validate_ast(result, _ICTL_VALID_OPERATORS)
