"""ICTL parser (PLY-based native subclass).

What it handles:
- ICTL formulas with path quantifiers (A/E) combined with temporal operators (X, F, G, U, R).
- Boolean connectives (AND/OR/NOT/IMPLIES).
- Propositions matching [a-zA-Z][a-zA-Z0-9_]*.
"""

from typing import Any

from model_checker.parsers.formulas.parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
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
        self.tokens.extend(["FORALL", "EXIST", "RELEASE", "PROP"])
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
    t_PROP = PROPOSITION_TOKEN_PATTERN

    def t_FORALL(self, t):
        r"A|forall\b"
        t.value = "A"
        return t

    def t_EXIST(self, t):
        r"E|exist\b"
        t.value = "E"
        return t

    def t_RELEASE(self, t):
        r"R|release\b"
        t.value = "R"
        return t

    # --- Grammar Rules ---
    def p_expression_ternary(self, p):
        """expression : FORALL expression UNTIL expression
        | EXIST expression UNTIL expression
        | FORALL expression RELEASE expression
        | EXIST expression RELEASE expression"""
        p[0] = (p[1] + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : FORALL GLOBALLY expression
        | FORALL NEXT expression
        | FORALL EVENTUALLY expression
        | EXIST GLOBALLY expression
        | EXIST NEXT expression
        | EXIST EVENTUALLY expression"""
        p[0] = (p[1] + p[2], p[3])

    # --- Validation ---
    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True
        return validate_ast(result, _ICTL_VALID_OPERATORS)


def verifyICTL(token_name: str, string: Any) -> bool:
    """Helper to verify tokens for the solver"""
    from model_checker.parsers.formula_parser_factory import FormulaParserFactory

    parser = FormulaParserFactory.get_parser_instance("ICTL")
    return parser.verify(token_name, string)
