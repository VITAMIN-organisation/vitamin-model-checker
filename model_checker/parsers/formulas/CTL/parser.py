"""CTL parser (PLY-based).

What it handles:
- CTL formulas with path quantifiers (A/E) combined with temporal operators (X, F, G, U).
- Boolean connectives (AND/OR/NOT/IMPLIES) and parentheses/brackets for grouping.
- Propositions matching [a-z][a-z0-9_]*.

What it rejects:
- Unicode or disallowed special characters (only (), [], logical operators allowed).
- Temporal operators (X, F, G, U) without a preceding path quantifier (A/E).
- Propositions whose first character is not a lowercase letter, or invalid identifiers.

Behavior:
- Returns an AST tuple on success or None on invalid input; does not raise for
  user-facing parse errors.
"""

import re
from typing import Optional

from ..parser_utils import run_common_prechecks
from ..shared_parser import BaseLogicParser


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
    t_PROP = r"[a-z][a-z0-9_]*"

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

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        valid, err = run_common_prechecks(
            formula,
            coalition_required=False,
            allow_hash_at=False,
            allow_negative_agents=False,
            allowed_uppercase=None,  # uppercase allowed for operators/quantifiers
            allowed_operators=set("<>(),[]!&|->"),
        )
        if not valid:
            return False, err

        if re.match(r"^\s*[XFG]", formula):
            return (
                False,
                "Temporal operators (X, F, G) must be preceded by a quantifier (A or E)",
            )
        if re.match(r"^\s*U\b", formula):
            return False, "UNTIL operator (U) must be preceded by a quantifier (A or E)"

        has_temporal = re.search(r"(X|F|G|U)", formula)
        has_quantifier = re.search(r"(A|E|forall|exist)", formula, re.IGNORECASE)
        if has_temporal and not has_quantifier:
            return (
                False,
                "Temporal operators must be preceded by a path quantifier (A or E) in CTL",
            )

        return True, None

    def _post_validation(self, formula, result):
        if result is None:
            return False

        _VALID_OPERATORS = {
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

        def _validate_result(r):
            if isinstance(r, str):
                if r in _VALID_OPERATORS or r.upper() in _VALID_OPERATORS:
                    return True
                return bool(re.match(r"^[a-z][a-z0-9_]*$", r))
            if isinstance(r, tuple):
                return all(_validate_result(item) for item in r)
            return False

        return _validate_result(result)
