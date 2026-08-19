"""TOL parser (PLY-based native subclass).

What it handles:
- TOL formulas over TimedCGS models with Demonic operators and time variables.
- AST generation using specialized Expr nodes.
"""

import re
import unicodedata
from typing import Any

from model_checker.parsers.formulas.parser_utils import run_common_prechecks
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.syntax_patterns import TCTL_TOL_PROPOSITION_TOKEN


# ==========================================
# AST Nodes
# ==========================================
class Expr:
    def __init__(self):
        self.satisfying_states = set()
        self.constraints = None


class Unary(Expr):
    def __init__(self, op: str, operand: Expr):
        super().__init__()
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"{self.op}({self.operand})"


class Binary(Expr):
    def __init__(self, op: str, left: Expr, right: Expr):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"{self.op} {self.left},{self.right}"


class AtomicProp(Expr):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class DemonicOp(Expr):
    def __init__(self, demonic_cost: str, op: str, operand: Expr):
        super().__init__()
        self.demonic_cost = demonic_cost
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"{self.demonic_cost}{self.op}({self.operand})"


class DemonicBinary(Expr):
    def __init__(self, demonic_cost: str, op: str, left: Expr, right: Expr):
        super().__init__()
        self.demonic_cost = demonic_cost
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"{self.demonic_cost}{self.op}({self.left},{self.right})"


class FreezeExpr(Expr):
    def __init__(self, clock: str, operand: Expr):
        super().__init__()
        self.clock = clock
        self.operand = operand

    def __repr__(self):
        return f"{self.clock}.({self.operand})"


class ClockExpr(Expr):
    def __init__(self, subject: Expr, constraints: Expr):
        super().__init__()
        self.subject = subject
        self.constraints = str(constraints)

    def __repr__(self):
        return f"{self.subject}: {self.constraints}"

    def __str__(self):
        return f"{self.subject}: {self.constraints}"


class SimpleTimeExpr(Expr):
    def __init__(self, constraints: tuple):
        super().__init__()
        self.constraints = constraints

    def __repr__(self):
        return "".join(self.constraints)

    def __str__(self):
        return "".join(self.constraints)


class DemonicValueError(Exception):
    pass


class TOLParser(BaseLogicParser):
    """Parser for TOL formulas using specialized AST nodes."""

    def __init__(self):
        super().__init__()
        self.tokens.extend(
            [
                "WEAK",
                "RELEASE",
                "DEMONIC",
                "GREATER",
                "LESS",
                "LEQ",
                "GEQ",
                "CONST",
                "TIME_SEP",
                "DOT",
                "PROP",
            ]
        )
        self.precedence = (("right", "NOT"),)
        self.build()

    # --- Specific Tokens ---
    def t_PROP(self, t):
        reserved = {
            "implies": "IMPLIES",
            "with": "TIME_SEP",
            "not": "NOT",
            "or": "OR",
            "and": "AND",
            "globally": "GLOBALLY",
            "G": "GLOBALLY",
        }
        t.type = reserved.get(t.value, "PROP")
        return t

    t_PROP.__doc__ = TCTL_TOL_PROPOSITION_TOKEN

    t_WEAK = r"W|weak\b"
    t_FALSE = r"\#|false\b"
    t_TRUE = r"\@|true\b"

    def t_RELEASE(self, t):
        r"R(?![a-zA-Z0-9_])|release\b"
        t.value = "R"
        return t

    t_DEMONIC = r"{J[1-9]\d*}"
    t_LESS = r"\<"
    t_LEQ = r"\<\="
    t_GREATER = r"\>"
    t_GEQ = r"\>\="
    t_CONST = r"\d+"
    t_TIME_SEP = r":|,|with"
    t_DOT = r"\."

    # --- Grammar Rules (Overrides) ---
    def p_expression_binary(self, p):
        """expression : expression AND expression
        | expression OR expression
        | expression IMPLIES expression"""
        p[0] = Binary(p[2], p[1], p[3])

    def p_expression_ternary(self, p):
        """expression : DEMONIC expression UNTIL expression
        | DEMONIC expression WEAK expression
        | DEMONIC expression RELEASE expression"""
        demonic_cost = re.findall(r"\d+", p[1])[0]
        try:
            int(demonic_cost)
        except ValueError:
            raise DemonicValueError(
                f"Provided cost ({demonic_cost}) is not an int."
            ) from None
        p[0] = DemonicBinary(p[1], p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : DEMONIC GLOBALLY expression
        | DEMONIC NEXT expression
        | DEMONIC EVENTUALLY expression"""
        demonic_cost = re.findall(r"\d+", p[1])[0]
        try:
            int(demonic_cost)
        except ValueError:
            raise DemonicValueError(
                f"Provided cost ({demonic_cost}) is not an int."
            ) from None
        p[0] = DemonicOp(p[1], p[2], p[3])

    def p_expression_not(self, p):
        """expression : NOT expression"""
        p[0] = Unary(p[1], p[2])

    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = p[2]

    def p_expression_boolean(self, p):
        """expression : FALSE
        | TRUE"""
        p[0] = p[1]

    def p_expression_freeze(self, p):
        """expression : PROP DOT expression"""
        p[0] = FreezeExpr(p[1], p[3])

    def p_expression_clock_constraint_on_expr(self, p):
        """expression : expression TIME_SEP expression"""
        p[0] = ClockExpr(p[1], p[3])

    def p_expression_time_atomic_constraint(self, p):
        """expression : PROP LEQ CONST
        | PROP LESS CONST
        | PROP GEQ CONST
        | PROP GREATER CONST
        """
        p[0] = SimpleTimeExpr(p[1] + p[2] + p[3])

    def p_expression_prop(self, p):
        """expression : PROP"""
        p[0] = AtomicProp(p[1])

    # --- Validation ---
    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        if isinstance(formula, str):
            s = unicodedata.normalize("NFKC", formula)
            s = s.replace("\ufeff", "").replace("\u00a0", " ")
            s = " ".join(s.strip().split())
        else:
            s = formula

        valid, err = run_common_prechecks(
            s,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_operators=set("<>(),!&|->{}. "),
        )
        return True, None

    def _post_validation(self, formula, result):
        return result is not None


def verifyTOL(token_name: str, string: Any) -> bool:
    """Helper to verify tokens for the solver"""
    from model_checker.parsers.formula_parser_factory import FormulaParserFactory

    parser = FormulaParserFactory.get_parser_instance("TOL")
    return parser.verify(token_name, string)
