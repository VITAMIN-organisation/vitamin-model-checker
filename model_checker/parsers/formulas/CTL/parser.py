"""CTL parser (PLY-based).

What it handles:
- CTL formulas with path quantifiers (A/E) combined with temporal operators (X, F, G, U).
- Boolean connectives (AND/OR/NOT/IMPLIES) and parentheses/brackets for grouping.
- Propositions matching [a-zA-Z][a-zA-Z0-9_]*.

What it rejects:
- Unicode or disallowed special characters (only (), [], logical operators allowed).
- Temporal operators (X, F, G, U) without a preceding path quantifier (A/E).
- Invalid proposition identifiers or reserved words used as proposition names.

Behavior:
- Returns an AST tuple on success or None on invalid input; does not raise for
  user-facing parse errors.
"""

from ..parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    validate_ast,
    validate_ctl_path_quantifiers,
)
from ..shared_parser import BaseLogicParser

_CTL_VALID_OPERATORS = {
    "EX",
    "AX",
    "EF",
    "AF",
    "EG",
    "AG",
    "EU",
    "AU",
    "E",
    "A",
    "U",
    "G",
    "F",
    "X",
    "!",
    "&&",
    "||",
    "->",
    "AND",
    "OR",
    "NOT",
    "IMPLIES",
    "UNTIL",
    "GLOBALLY",
    "NEXT",
    "EVENTUALLY",
    "FORALL",
    "EXIST",
}


class CTLParser(BaseLogicParser):
    """Parser for CTL formulas (path quantifiers A/E and temporal operators X, F, G, U).

    Use parse(formula) to get an AST tuple or None on invalid input.
    """

    def __init__(self):
        """Initialize the CTL lexer and parser (PLY)."""
        super().__init__()
        # Add CTL specific tokens
        self.tokens.extend(["LBRACKET", "RBRACKET", "FORALL", "EXIST", "PROP"])
        self.build()

    # --- CTL Specific Tokens ---
    t_LBRACKET = r"\["
    t_RBRACKET = r"\]"
    t_PROP = PROPOSITION_TOKEN_PATTERN

    def t_FORALL(self, t):
        r"A|forall"
        return t

    def t_EXIST(self, t):
        r"E|exist"
        return t

    # --- Grammar Rules ---

    def p_expression_ternary(self, p):
        """expression : FORALL expression UNTIL expression
        | EXIST expression UNTIL expression
        | FORALL LPAREN expression UNTIL expression RPAREN
        | EXIST LPAREN expression UNTIL expression RPAREN
        | FORALL LBRACKET expression UNTIL expression RBRACKET
        | EXIST LBRACKET expression UNTIL expression RBRACKET"""
        if len(p) == 5:
            p[0] = (p[1] + p[3], p[2], p[4])
        else:
            p[0] = (p[1] + p[4], p[3], p[5])

    def p_expression_unary(self, p):
        """expression : FORALL GLOBALLY expression
        | FORALL NEXT expression
        | FORALL EVENTUALLY expression
        | EXIST GLOBALLY expression
        | EXIST NEXT expression
        | EXIST EVENTUALLY expression"""
        p[0] = (p[1] + p[2], p[3])

    def p_expression_group_bracket(self, p):
        """expression : LBRACKET expression RBRACKET"""
        p[0] = p[2]

    # --- Validation ---

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            coalition_required=False,
            allow_hash_at=False,
            allow_negative_agents=False,
            allowed_operators=set("<>(),[]!&|->"),
        )
        if not valid:
            return False, err

        return validate_ctl_path_quantifiers(formula)

    def _post_validation(self, formula, result):
        if result is None:
            return False
        return validate_ast(result, _CTL_VALID_OPERATORS)
