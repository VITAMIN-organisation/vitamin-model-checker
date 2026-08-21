"""Wallet_ATL parser (PLY-based native subclass) - Standardized Robust Version."""

import re
import unicodedata

from model_checker.parsers.formulas.parser_utils import (
    run_common_prechecks,
    validate_ast,
    validate_proposition_identifier,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser

_WALLET_CONSTRAINT_OPS = frozenset({">=", "<=", "==", ">", "<"})
_COALITION_TEMPORAL_SPACING = re.compile(r">>(?=[FGXU])")

_WALLET_ATL_VALID_OPERATORS = frozenset(
    {
        "U",
        "X",
        "F",
        "G",
        "&&",
        "&",
        "and",
        "AND",
        "||",
        "|",
        "or",
        "OR",
        "!",
        "not",
        "NOT",
        "->",
        ">",
        "implies",
        "IMPLIES",
        "UNTIL",
        "NEXT",
        "EVENTUALLY",
        "GLOBALLY",
    }
)


def _validate_wallet_dict_ast(node, valid_operators) -> bool:
    """Walk a Wallet_ATL dict AST and reject unknown shapes or operators."""
    if not isinstance(node, dict):
        return False

    node_type = node.get("type")
    if node_type == "proposition":
        prop = node.get("proposition")
        if not isinstance(prop, str):
            return False
        valid, _ = validate_proposition_identifier(prop)
        return valid

    if node_type == "unary":
        operator = node.get("operator")
        if (
            operator not in valid_operators
            and str(operator).upper() not in valid_operators
        ):
            return False
        return _validate_wallet_dict_ast(node.get("formula"), valid_operators)

    if node_type == "binary":
        operator = node.get("operator")
        if (
            operator not in valid_operators
            and str(operator).upper() not in valid_operators
        ):
            return False
        return _validate_wallet_dict_ast(
            node.get("left"), valid_operators
        ) and _validate_wallet_dict_ast(node.get("right"), valid_operators)

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
        return _validate_wallet_dict_ast(node.get("formula"), valid_operators)

    return False


def _parse_coalition_logic(text):
    """Parse coalition specification with optional wallet constraints."""
    coalition_match = re.match(r"<<\s*([^:>]*)(?::(.*))?>>", text)
    if not coalition_match:
        raise SyntaxError("Invalid coalition specification")

    agents_part = coalition_match.group(1).strip()
    agents = [int(a.strip()) for a in agents_part.split(",") if a.strip().isdigit()]

    constraints = []
    constraints_part = coalition_match.group(2)

    if constraints_part:
        for constraint in re.split(r"\s*&&\s*", constraints_part.strip()):
            wallet_match = re.match(
                r"wallet\(\s*(\d+)\s*,\s*(>=|<=|==|>|<)\s*(\d+)\s*\)",
                constraint.strip(),
            )
            if wallet_match:
                constraints.append(
                    {
                        "agent": int(wallet_match.group(1)),
                        "operator": wallet_match.group(2),
                        "value": int(wallet_match.group(3)),
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
        r"<<\s*\d+(?:\s*,\s*\d+)*\s*(?::\s*wallet\(\s*\d+\s*,\s*(?:>=|<=|==|>|<)\s*\d+\s*\)(?:\s*&&\s*wallet\(\s*\d+\s*,\s*(?:>=|<=|==|>|<)\s*\d+\s*\))*)?\s*>>"
        t.value = _parse_coalition_logic(t.value)
        return t

    # --- Grammar Rules (Overrides) ---
    def p_expression_not(self, p):
        """expression : NOT expression"""
        p[0] = {
            "type": "unary",
            "operator": p[1],
            "formula": p[2],
        }

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

    def p_expression_ternary(self, p):
        """expression : COALITION temporal_body"""
        coalition_info = p[1]
        max_coalition = self.MAX_COALITION
        for agent in coalition_info["agents"]:
            if agent < 1 or agent > max_coalition:
                raise ValueError(
                    f"Invalid coalition value {agent}: must be between 1 and {max_coalition}"
                )
        for constraint in coalition_info["constraints"]:
            agent = constraint["agent"]
            if agent < 1 or agent > max_coalition:
                raise ValueError(
                    f"Invalid wallet constraint agent {agent}: "
                    f"must be between 1 and {max_coalition}"
                )
        p[0] = {
            "type": "coalition_wallet",
            "agents": coalition_info["agents"],
            "constraints": coalition_info["constraints"],
            "formula": p[2],
        }

    def p_temporal_body(self, p):
        """temporal_body : GLOBALLY expression
        | NEXT expression
        | EVENTUALLY expression
        | expression UNTIL expression"""
        if len(p) == 3:
            p[0] = {
                "type": "unary",
                "operator": p[1],
                "formula": p[2],
            }
        else:
            p[0] = {
                "type": "binary",
                "operator": p[2],
                "left": p[1],
                "right": p[4],
            }

    def p_expression_prop(self, p):
        """expression : PROP"""
        p[0] = {
            "type": "proposition",
            "proposition": p[1],
        }

    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = p[2]

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
        if result is None:
            return False
        if isinstance(result, dict):
            return _validate_wallet_dict_ast(result, _WALLET_ATL_VALID_OPERATORS)
        if isinstance(result, tuple):
            return validate_ast(result, _WALLET_ATL_VALID_OPERATORS)
        return False

    def parse(self, formula_text, max_coalition=None, n_agent=None, **kwargs):
        self.errors = []

        # normalize
        text = unicodedata.normalize("NFKC", formula_text)
        text = text.replace("\ufeff", "").replace("\u00a0", " ")
        text = " ".join(text.strip().split())
        normalized = _COALITION_TEMPORAL_SPACING.sub(">> ", text)

        valid, err = self._pre_validation(normalized)
        if not valid:
            if err:
                self.errors.append(err)
            return None

        if n_agent is not None and max_coalition is None:
            max_coalition = n_agent
        self.MAX_COALITION = max_coalition if max_coalition is not None else 0

        try:
            res = super().parse(normalized, **kwargs)
            if res is None:
                if not self.errors:
                    self.errors.append("Syntax or lexical error in formula")
                return None
            if not self._post_validation(normalized, res):
                return None
            return res
        except Exception as e:
            self.logger.debug("Wallet_ATL parse failed: %s", e)
            self.errors.append(str(e))
            return None
