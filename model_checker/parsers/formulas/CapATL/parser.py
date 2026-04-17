"""CapATL parser (PLY-based).

What it handles:
- CapATL formulas with coalition-prefixed temporal operators (U, R, X, F, G)
  and boolean connectives.
- Coalition syntax `<{1,2}, k>` with agent indices in [1, n_agent] and capacity bound k.
- Capability atoms of the form `K1 p`, `K2 (K3 p)`, and agent propositions `1is p`.
- Symbolic boolean operator `&&` and textual `and`, `not`;
  release/until/next/eventually/globally operators `R`, `U`, `X`, `F`, `G`.

What it rejects:
- Uppercase textual boolean keywords; uppercase is limited to modal letters U/R/X/F/G/K.
- Non-ASCII characters, invalid special characters, empty/None formulas, null bytes.
- Empty or malformed coalitions (e.g., `<>`, trailing commas, negative indices, or
  out-of-range agents).
- Formulas without capacity bounds (must use `<{coalition}, bound>` syntax).

Behavior:
- Returns an AST tuple on success or None on invalid input; does not raise for
  user-facing parse errors.
"""

import re
from typing import Optional

from ..parser_utils import (
    run_common_prechecks,
    validate_ast,
    validate_coalition,
    verify_token,
)
from ..shared_parser import BaseLogicParser

_COALITION_BOUND_REGEX = r"<\{((?:\d+,)*\d+)\},\s*(\d+)>"


class CapATLParser(BaseLogicParser):
    """Parser for CapATL formulas (coalition/capacity bounds and capability atoms).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set n_agent before parsing for coalition validation.
    """

    def __init__(self):
        """Initialize the CapATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens = [t for t in self.tokens if t != "WEAK"]

        self.tokens.extend(
            [
                "IS",
                "UNTIL",
                "RELEASE",
                "NEXT",
                "EVENTUALLY",
                "GLOBALLY",
                "KCAP",
                "PROP",
                "COALITION_BOUND",
                "AGENT",
            ]
        )

        self.max_coalition = 3
        self.build()

    # === Tokens ===
    def t_RELEASE(self, t):
        r"R|release\b"
        t.value = "R"
        return t

    def t_IS(self, t):
        r"is|IS"
        return t

    def t_KCAP(self, t):
        r"K|kcap"
        t.value = "K"
        return t

    # Coalition with capacity bound: <{1,2}, 3>
    def t_COALITION_BOUND(self, t):
        match = re.match(_COALITION_BOUND_REGEX, t.value)
        if match:
            t.value = (match.group(1), match.group(2))
        return t

    t_AGENT = r"\d+"
    t_PROP = r"[a-z][a-z0-9_]*"

    # === Grammar rules ===
    def p_expression_binary(self, p):
        """expression : expression AND expression"""
        p[0] = (p[2], p[1], p[3])

    def p_expression_ternary(self, p):
        """expression : COALITION_BOUND expression UNTIL expression
        | COALITION_BOUND expression RELEASE expression"""
        coalition_str = f"<{{{p[1][0]}}},{p[1][1]}>"
        coalition_only = f"<{p[1][0]}>"
        validate_coalition(coalition_only, self.max_coalition)
        p[0] = (coalition_str + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : COALITION_BOUND NEXT expression
        | COALITION_BOUND EVENTUALLY expression
        | COALITION_BOUND GLOBALLY expression"""
        coalition_str = f"<{{{p[1][0]}}},{p[1][1]}>"
        coalition_only = f"<{p[1][0]}>"
        validate_coalition(coalition_only, self.max_coalition)
        p[0] = (coalition_str + p[2], p[3])

    def p_expression_kcap(self, p):
        """expression : KCAP AGENT expression2"""
        p[0] = (p[1] + p[2], p[3])

    def p_expression_capformula_group(self, p):
        """expression2 : LPAREN expression2 RPAREN"""
        p[0] = p[2]

    def p_expression_capformula_and(self, p):
        """expression2 : expression2 AND expression2"""
        p[0] = (p[2], p[1], p[3])

    def p_expression_capformula_not(self, p):
        """expression2 : NOT expression2"""
        p[0] = (p[1], p[2])

    def p_expression_capformula_is(self, p):
        """expression2 : AGENT IS PROP"""
        p[0] = (p[1], p[3])

    def p_expression_capformula_kcap(self, p):
        """expression2 : KCAP AGENT expression2"""
        p[0] = (p[1] + p[2], p[3])

    # === Validation ===

    def parse(self, formula, n_agent=3, **kwargs):
        self.max_coalition = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        _ALLOWED_UPPERCASE_CHARS = {"U", "R", "X", "F", "G", "K", "I", "S"}

        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            allow_negative_agents=False,
            allowed_uppercase=_ALLOWED_UPPERCASE_CHARS,
            allowed_operators=set("<>(),!&|->{}"),
        )
        if not valid:
            return False, err

        has_capacity_bound = re.search(r"<\{[\d,]+\},\s*\d+>", formula)
        has_knowledge_op = re.search(r"K\d+\s*\(", formula, re.IGNORECASE)
        if not (has_capacity_bound or has_knowledge_op):
            return (
                False,
                "CapATL requires either capacity bounds <{coalition}, bound> or knowledge operators K(agent)",
            )

        return True, None

    def _post_validation(self, formula, result):
        if result is None:
            return False

        _VALID_OPERATORS = {
            "U",
            "R",
            "X",
            "F",
            "G",
            "&&",
            "AND",
            "NOT",
            "UNTIL",
            "RELEASE",
            "NEXT",
            "EVENTUALLY",
            "GLOBALLY",
            "!",
        }
        _COALITION_OPERATOR_PATTERN = re.compile(
            r"^<\{[\d,]+\},\s*\d+>(U|R|X|F|G|UNTIL|RELEASE|NEXT|EVENTUALLY|GLOBALLY)$",
            re.IGNORECASE,
        )
        _KCAP_PATTERN = re.compile(r"^K\d+$", re.IGNORECASE)

        if not validate_ast(
            result,
            _VALID_OPERATORS,
            coalition_pattern=_COALITION_OPERATOR_PATTERN,
            extra_atom_patterns=(_KCAP_PATTERN,),
        ):
            return False
        return True

    def verify(self, token_name, string):
        return verify_token(self.lexer, token_name, string, case_sensitive=False)


CapATLParser.t_COALITION_BOUND.__doc__ = _COALITION_BOUND_REGEX
