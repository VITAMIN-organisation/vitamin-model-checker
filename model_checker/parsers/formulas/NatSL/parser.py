"""NatSL parser (PLY-based).

What it handles:
- NatSL formulas with quantifier lists, optional bounds, bindings, and simple
  temporal expressions (F, !F).

Behavior:
- Returns an AST tuple on success; logs syntax issues at debug level.
"""

from typing import Optional

from ..parser_utils import run_common_prechecks
from ..shared_parser import BaseLogicParser


class NatSLParser(BaseLogicParser):
    """Parser for NatSL formulas (quantifier lists, bounds, bindings, F/!F).

    Use parse(formula) to get an AST tuple or None on invalid input.
    """

    def __init__(self):
        """Initialize the NatSL lexer and parser (PLY)."""
        super().__init__()
        to_remove = {"WEAK", "RELEASE"}
        self.tokens = [t for t in self.tokens if t not in to_remove]

        self.tokens.extend(
            [
                "COLON",
                "COMMA",
                "EXIST",
                "FORALL",
                "PROP",
                "AGENT",
                "BOUND",
            ]
        )

        self.build(start="formula")

    # === Tokens ===

    t_COLON = r":"
    t_COMMA = r","
    t_AGENT = r"\d+"
    t_BOUND = r"\{\d+\}"

    def t_EXIST(self, t):
        r"E"
        return t

    def t_FORALL(self, t):
        r"A"
        return t

    def t_PROP(self, t):
        r"[a-z][a-z0-9_]*"
        reserved = {
            "eventually": "EVENTUALLY",
            "not": "NOT",
        }
        if t.value in reserved:
            t.type = reserved[t.value]
        else:
            t.type = "PROP"
        return t

    # === Grammar ===
    def p_formula(self, p):
        """formula : quantifiers COLON binding_pairs temporal_expression"""
        p[0] = (p[1], p[3], p[4])

    def p_quantifiers(self, p):
        """quantifiers : quantifier
        | quantifiers quantifier"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    # Quantifier with optional bound (defaults to 1 when absent)
    def p_quantifier(self, p):
        """quantifier : EXIST opt_bound PROP
        | FORALL opt_bound PROP"""
        p[0] = (p[1], p[3], p[2])

    # Optional bound: extract number if present, else use 1
    def p_opt_bound(self, p):
        """opt_bound : BOUND
        | empty"""
        if len(p) == 2 and p[1] is not None:
            p[0] = int(p[1][1:-1])  # "{3}" -> 3
        else:
            p[0] = 1

    def p_empty(self, p):
        "empty :"
        p[0] = None

    def p_binding_pairs(self, p):
        """binding_pairs : binding_pair
        | binding_pairs binding_pair"""
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_binding_pair(self, p):
        """binding_pair : LPAREN PROP COMMA AGENT RPAREN"""
        p[0] = (p[2], p[4])

    def p_temporal_expression(self, p):
        """temporal_expression : negation_expression
        | EVENTUALLY PROP"""
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = ("F", p[2])

    def p_negation_expression(self, p):
        """negation_expression : NOT EVENTUALLY PROP"""
        p[0] = ("!", "F", p[3])

    # === Validation ===
    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        return run_common_prechecks(
            formula,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_uppercase={"E", "A", "F"},
            allowed_operators=set(":(),!{}"),
        )
