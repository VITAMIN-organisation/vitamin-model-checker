"""CapATL parser (PLY-based).

What it handles:
- CapATL formulas with coalition-prefixed temporal operators (U, R, X, F, G)
  and boolean connectives.
- Coalition syntax `<{1,2}>` (paper-style agent set; no numeric formula bound).
- Capability atoms of the form `K1 p`, `K2 (K3 p)`, and agent propositions `1is p`.
- Symbolic boolean operator `&&` and textual `and`, `not`;
  release/until/next/eventually/globally operators `R`, `U`, `X`, `F`, `G`.

What it rejects:
- Weak Until (W): CapATL path formulas use X, U and R (G/F are supported sugar).
- NatATL-style `<{A}, k>` (numeric k is not part of CapATL; capacities live in the model).
- Uppercase textual boolean keywords; uppercase is limited to modal letters U/R/X/F/G/K.
- Non-ASCII characters, invalid special characters, empty/None formulas, null bytes.
- Empty or malformed coalitions (e.g., `<>`, trailing commas, negative indices, or
  out-of-range agents).
- Formulas without a coalition modality (must use `<{coalition}>` or knowledge ops).

Behavior:
- Returns an AST tuple on success or None on invalid input; does not raise for
  user-facing parse errors.
"""

import re

from model_checker.parsers.formulas.parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    validate_ast,
    validate_coalition,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser

_COALITION_REGEX = r"<\{((?:\d+,)*\d+)\}>"

_CAPATL_VALID_OPERATORS = frozenset(
    {
        "U",
        "R",
        "X",
        "F",
        "G",
        "&&",
        "AND",
        "||",
        "OR",
        "->",
        "IMPLIES",
        "NOT",
        "UNTIL",
        "RELEASE",
        "NEXT",
        "EVENTUALLY",
        "GLOBALLY",
        "!",
    }
)

_COALITION_OPERATOR_PATTERN = re.compile(
    r"^<\{[\d,]+\}>(U|R|X|F|G|UNTIL|RELEASE|NEXT|EVENTUALLY|GLOBALLY)$",
    re.IGNORECASE,
)

_KCAP_PATTERN = re.compile(r"^K\d+$", re.IGNORECASE)
_LEGACY_BOUND_PATTERN = re.compile(r"<\{[\d,]+\},\s*-?\d+>")


class CapATLParser(BaseLogicParser):
    """Parser for CapATL formulas (coalition modalities and capability atoms).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set n_agent before parsing for coalition validation.
    """

    def __init__(self):
        """Initialize the CapATL lexer and parser (PLY)."""
        super().__init__()
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
                "COALITION",
                "AGENT",
            ]
        )
        self.max_coalition = 0
        self.build()

    # --- Specific Tokens ---
    def t_RELEASE(self, t):
        r"R(?![a-zA-Z0-9_])|release\b"
        t.value = "R"
        return t

    def t_IS(self, t):
        r"is\b|IS\b"
        return t

    def t_KCAP(self, t):
        r"K(?![a-zA-Z0-9_])|kcap\b"
        t.value = "K"
        return t

    def t_COALITION(self, t):
        match = re.match(_COALITION_REGEX, t.value)
        if match:
            t.value = match.group(1)
        return t

    t_COALITION.__doc__ = _COALITION_REGEX

    t_AGENT = r"\d+"
    t_PROP = PROPOSITION_TOKEN_PATTERN

    # --- Grammar Rules ---
    def p_expression_binary(self, p):
        """expression : expression AND expression
        | expression OR expression
        | expression IMPLIES expression"""
        p[0] = (p[2], p[1], p[3])

    def p_expression_ternary(self, p):
        """expression : COALITION expression UNTIL expression
        | COALITION expression RELEASE expression"""
        coalition_str = f"<{{{p[1]}}}>"
        validate_coalition(f"<{p[1]}>", self.max_coalition)
        p[0] = (coalition_str + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : COALITION NEXT expression
        | COALITION EVENTUALLY expression
        | COALITION GLOBALLY expression"""
        coalition_str = f"<{{{p[1]}}}>"
        validate_coalition(f"<{p[1]}>", self.max_coalition)
        p[0] = (coalition_str + p[2], p[3])

    def p_expression_kcap(self, p):
        """expression : KCAP AGENT expression2"""
        p[0] = (p[1] + p[2], p[3])

    def p_expression_capformula_group(self, p):
        """expression2 : LPAREN expression2 RPAREN"""
        p[0] = p[2]

    def p_expression_capformula_binary(self, p):
        """expression2 : expression2 AND expression2
        | expression2 OR expression2
        | expression2 IMPLIES expression2"""
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

    # --- Validation ---
    def parse(self, formula, n_agent=0, **kwargs):
        self.max_coalition = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            allow_negative_agents=False,
            allowed_operators=set("<>(),!&|->{}"),
        )
        if not valid:
            return False, err

        if _LEGACY_BOUND_PATTERN.search(formula):
            return (
                False,
                "CapATL uses <{coalition}> without a numeric bound "
                "(capacities are defined in the capCGS model)",
            )

        has_coalition = re.search(r"<\{[\d,]+\}>", formula)
        has_knowledge_op = re.search(r"K\d+\s*\(", formula, re.IGNORECASE)
        if not (has_coalition or has_knowledge_op):
            return (
                False,
                "CapATL requires either coalition modalities <{coalition}> "
                "or knowledge operators K(agent)",
            )

        return True, None

    def _post_validation(self, formula, result):
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True

        if not validate_ast(
            result,
            _CAPATL_VALID_OPERATORS,
            coalition_pattern=_COALITION_OPERATOR_PATTERN,
            extra_atom_patterns=(_KCAP_PATTERN,),
        ):
            return False
        return True
