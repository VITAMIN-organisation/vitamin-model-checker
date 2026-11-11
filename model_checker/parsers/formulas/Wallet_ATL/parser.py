"""Wallet_ATL parser (PLY-based native subclass) - Standardized Robust Version."""

import re

from model_checker.parsers.formulas.parser_utils import (
    normalize_formula_text,
    run_common_prechecks,
    validate_agents,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.syntax_patterns import (
    COMPARISON_OPERATORS,
    WALLET_COALITION_HEADER_RE,
    WALLET_COALITION_TOKEN,
    WALLET_CONSTRAINT_AND_RE,
    WALLET_CONSTRAINT_RE,
)

_WALLET_CONSTRAINT_OPS = frozenset(COMPARISON_OPERATORS)
_COALITION_TEMPORAL_SPACING = re.compile(r">>(?=[FGXU])")

# Upper case only: the lexer leaves word connectives as typed (`and`).
_WALLET_ATL_VALID_OPERATORS = frozenset(
    {
        "U",
        "X",
        "F",
        "G",
        "&&",
        "AND",
        "||",
        "OR",
        "!",
        "NOT",
        "->",
        "IMPLIES",
        "UNTIL",
        "NEXT",
        "EVENTUALLY",
        "GLOBALLY",
    }
)


def _validate_wallet_dict_ast(node) -> bool:
    """Walk a Wallet_ATL dict AST and reject unknown shapes or operators."""
    if not isinstance(node, dict):
        return False

    node_type = node.get("type")
    if node_type == "proposition":
        return isinstance(node.get("proposition"), str)

    if node_type in ("unary", "binary"):
        if str(node.get("operator")).upper() not in _WALLET_ATL_VALID_OPERATORS:
            return False
        if node_type == "unary":
            return _validate_wallet_dict_ast(node.get("formula"))
        return _validate_wallet_dict_ast(
            node.get("left")
        ) and _validate_wallet_dict_ast(node.get("right"))

    if node_type == "coalition_wallet":
        agents = node.get("agents")
        constraints = node.get("constraints")
        if not isinstance(agents, list) or not agents:
            return False
        if not all(isinstance(agent, int) and agent >= 1 for agent in agents):
            return False
        if not isinstance(constraints, list):
            return False
        for constraint in constraints:
            if not isinstance(constraint, dict):
                return False
            agent = constraint.get("agent")
            operator = constraint.get("operator")
            value = constraint.get("value")
            if not isinstance(agent, int) or agent < 1:
                return False
            if operator not in _WALLET_CONSTRAINT_OPS:
                return False
            if not isinstance(value, int):
                return False
        return _validate_wallet_dict_ast(node.get("formula"))

    return False


def _parse_coalition_logic(text):
    """Parse coalition specification with optional wallet constraints."""
    coalition_match = WALLET_COALITION_HEADER_RE.match(text)
    if not coalition_match:
        raise SyntaxError("Invalid coalition specification")

    agents_part = coalition_match.group(1).strip()
    agents = [int(a.strip()) for a in agents_part.split(",") if a.strip().isdigit()]

    constraints = []
    constraints_part = coalition_match.group(2)

    if constraints_part:
        for constraint in WALLET_CONSTRAINT_AND_RE.split(constraints_part.strip()):
            wallet_match = WALLET_CONSTRAINT_RE.match(constraint.strip())
            if wallet_match:
                constraints.append(
                    {
                        "agent": int(wallet_match.group("agent")),
                        "operator": wallet_match.group("operator"),
                        "value": int(wallet_match.group("value")),
                    }
                )
            elif constraint.strip():
                raise SyntaxError(f"Invalid wallet constraint: {constraint}")

    return {
        "agents": agents,
        "constraints": constraints,
    }


class Wallet_ATLParser(BaseLogicParser):
    """Parser for Wallet_ATL formulas using dict AST."""

    def __init__(self, **kwargs):
        super().__init__()
        self.tokens.extend(["COALITION", "PROP"])
        self.MAX_COALITION = 0
        self.precedence = (
            ("right", "IMPLIES"),
            ("left", "OR"),
            ("left", "AND"),
            ("right", "NOT"),
            ("right", "UNTIL"),
            ("right", "GLOBALLY", "NEXT", "EVENTUALLY"),
        )
        self.build()

    # --- Specific Tokens ---
    def t_PROP(self, t):
        r"[a-zA-Z][a-zA-Z0-9_]*"
        return t

    def t_COALITION(self, t):
        t.value = _parse_coalition_logic(t.value)
        return t

    t_COALITION.__doc__ = WALLET_COALITION_TOKEN

    # --- Grammar Rules (Overrides) ---
    def p_expression_not(self, p):
        """expression : NOT expression"""
        p[0] = {
            "type": "unary",
            "operator": p[1],
            "formula": p[2],
        }
        self._negation(p[0], p[2])

    def p_expression_binary(self, p):
        """expression : expression AND expression
        | expression OR expression
        | expression IMPLIES expression"""
        p[0] = {
            "type": "binary",
            "operator": p[2],
            "left": p[1],
            "right": p[3],
        }
        self._connective(p[0], p[1], p[2], p[3])

    def p_expression_ternary(self, p):
        """expression : COALITION temporal_body"""
        coalition_info = p[1]
        validate_agents(coalition_info["agents"], self.MAX_COALITION)
        for constraint in coalition_info["constraints"]:
            agent = constraint["agent"]
            # AAMAS26b's syntax ranges guards over all agents but Def. 4.5 only
            # over the coalition; rejecting the rest avoids picking one reading.
            if agent not in coalition_info["agents"]:
                coalition = ",".join(str(a) for a in coalition_info["agents"])
                raise ValueError(
                    f"Wallet guard on agent {agent}, which is not in the coalition "
                    f"<<{coalition}>>: guards apply to coalition agents only"
                )
        p[0] = {
            "type": "coalition_wallet",
            "agents": coalition_info["agents"],
            "constraints": coalition_info["constraints"],
            "formula": p[2],
        }
        body = p[2]
        if body not in self._grouped:
            # The coalition as written, wallet guards included.
            source = p.lexer.lexdata[p.lexpos(1) :]
            token = re.match(WALLET_COALITION_TOKEN, source)
            if token is None:
                raise ValueError(f"Invalid wallet coalition at: {source!r}")
            prefix = token.group(0)
            if body["type"] == "unary":
                prefix += body["operator"]
                self._prefix_over(p[0], prefix, p.lexpos(1), body["formula"])
            else:
                self._prefix_over(
                    p[0], prefix, p.lexpos(1), body["right"], body["operator"]
                )

    def p_temporal_body(self, p):
        """temporal_body : GLOBALLY expression
        | NEXT expression
        | EVENTUALLY expression
        | expression UNTIL expression
        | LPAREN expression UNTIL expression RPAREN"""
        if len(p) == 3:
            p[0] = {
                "type": "unary",
                "operator": p[1],
                "formula": p[2],
            }
        else:
            # <<A>> phi U psi and <<A>> (phi U psi) build the same tree.
            left, operator, right = p[1:4] if len(p) == 4 else p[2:5]
            p[0] = {
                "type": "binary",
                "operator": operator,
                "left": left,
                "right": right,
            }
            if len(p) == 6:
                self._grouped.mark(p[0])

    def _proposition_node(self, name):
        return {"type": "proposition", "proposition": name}

    # --- Validation ---
    def _pre_validation(self, formula):
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_operators=set("<>(),!&|->:="),
        )

    def _post_validation(self, formula, result) -> bool:
        return _validate_wallet_dict_ast(result)

    def parse(self, formula_text, max_coalition=None, n_agent=None, **kwargs):
        text = normalize_formula_text(formula_text)
        text = _COALITION_TEMPORAL_SPACING.sub(">> ", text)

        if n_agent is not None and max_coalition is None:
            max_coalition = n_agent
        self.MAX_COALITION = max_coalition if max_coalition is not None else 0

        return super().parse(text, **kwargs)
