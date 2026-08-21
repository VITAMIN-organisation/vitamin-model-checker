"""TCTL parser (PLY-based native subclass).

What it handles:
- TCTL formulas over TimedCGS models (freeze variables, clock constraints).
- AST generation using specialized Expr nodes.
"""

from typing import Any

from model_checker.parsers.formulas.parser_utils import run_common_prechecks
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.syntax_patterns import TCTL_TOL_PROPOSITION_TOKEN


# ==========================================
# AST Nodes
# ==========================================
class Expr:
    def __init__(self) -> None:
        self.satisfying_regions: set = set()
        self.constraints = None


class Unary(Expr):
    def __init__(self, op: str, operand: Expr) -> None:
        super().__init__()
        self.op = op
        self.operand = operand

    def __repr__(self) -> str:
        return f"{self.op}({self.operand})"


class Binary(Expr):
    def __init__(self, op: str, left: Expr, right: Expr) -> None:
        super().__init__()
        self.op = op
        self.right = right
        self.left = left

    def __repr__(self) -> str:
        return f"{self.op} {self.left},{self.right}"


class AtomicProp(Expr):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class QuantifiedPath(Expr):
    def __init__(self, quantifier: str, formula: Expr) -> None:
        super().__init__()
        self.quantifier = quantifier
        self.formula = formula

    def __repr__(self) -> str:
        return f"{self.quantifier}({self.formula})"


class FreezeExpr(Expr):
    def __init__(self, clock: str, operand: Expr) -> None:
        super().__init__()
        self.clock = clock
        self.operand = operand

    def __repr__(self) -> str:
        return f"{self.clock}.({self.operand})"


class ClockExpr(Expr):
    def __init__(self, subject: Expr, constraints: Expr) -> None:
        super().__init__()
        self.subject = subject
        self.constraints = str(constraints)

    def __repr__(self) -> str:
        return f"{self.subject}: {self.constraints}"

    def __str__(self) -> str:
        return f"{self.subject}: {self.constraints}"


class SimpleTimeExpr(Expr):
    def __init__(self, constraints: tuple) -> None:
        super().__init__()
        self.constraints = constraints

    def __repr__(self) -> str:
        return "".join(self.constraints)

    def __str__(self) -> str:
        return "".join(self.constraints)


class TCTLParser(BaseLogicParser):
    """Parser for TCTL formulas using specialized AST nodes."""

    def __init__(self):
        super().__init__()
        self.tokens.extend(
            [
                "FORALL",
                "EXIST",
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

        self.precedence = (
            ("right", "IMPLIES"),
            ("left", "OR"),
            ("left", "AND"),
            ("right", "NOT"),
        )
        self.build()

    # --- Specific Tokens ---
    def t_PROP(self, t):
        reserved = {"implies": "IMPLIES"}
        t.type = reserved.get(t.value, "PROP")
        return t

    t_PROP.__doc__ = TCTL_TOL_PROPOSITION_TOKEN

    def t_FORALL(self, t):
        r"A|forall"
        return t

    def t_EXIST(self, t):
        r"E|exist"
        return t

    t_LEQ = r"\<\="
    t_GEQ = r"\>\="
    t_GREATER = r"\>"
    t_LESS = r"\<"
    t_CONST = r"\d+"
    t_TIME_SEP = r":"
    t_DOT = r"\."

    # --- Grammar Rules (Overrides) ---
    def p_expression_binary(self, p):
        """expression : expression AND expression
        | expression OR expression
        | expression IMPLIES expression"""
        p[0] = Binary(p[2], p[1], p[3])

    def p_expression_ternary(self, p):
        """expression : FORALL expression UNTIL expression
        | EXIST expression UNTIL expression
        | FORALL LPAREN expression UNTIL expression RPAREN
        | EXIST LPAREN expression UNTIL expression RPAREN"""
        if len(p) == 5:
            p[0] = QuantifiedPath(p[1], Binary(p[3], p[2], p[4]))
        else:
            p[0] = QuantifiedPath(p[1], Binary(p[4], p[3], p[5]))

    def p_expression_unary(self, p):
        """expression : FORALL GLOBALLY expression
        | FORALL EVENTUALLY expression
        | EXIST GLOBALLY expression
        | EXIST EVENTUALLY expression"""
        p[0] = QuantifiedPath(p[1] + p[2], p[3])

    def p_expression_not(self, p):
        """expression : NOT expression"""
        p[0] = Unary(p[1], p[2])

    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = p[2]

    def p_expression_freeze(self, p):
        """expression : PROP DOT expression"""
        p[0] = FreezeExpr(p[1], p[3])

    def p_expression_clock_constraint_on_expr(self, p):
        """expression : expression TIME_SEP expression"""
        p[0] = ClockExpr(p[1], p[3])

    def p_expression_prop(self, p):
        """expression : PROP"""
        p[0] = AtomicProp(p[1])

    def p_expression_time(self, p):
        """expression : PROP LEQ CONST
        | PROP LESS CONST
        | PROP GEQ CONST
        | PROP GREATER CONST
        """
        p[0] = SimpleTimeExpr(p[1] + p[2] + p[3])

    # --- Validation ---
    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        import unicodedata

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
            allowed_operators=set("<>=!&|->:.() "),
        )
        return valid, err

    def _post_validation(self, formula, result):
        return result is not None


def verifyTCTL(token_name: str, string: Any) -> bool:
    """Helper to verify tokens for the solver, leveraging the factory cache."""
    from model_checker.parsers.formula_parser_factory import FormulaParserFactory

    parser = FormulaParserFactory.get_parser_instance("TCTL")
    return parser.verify(token_name, string)
