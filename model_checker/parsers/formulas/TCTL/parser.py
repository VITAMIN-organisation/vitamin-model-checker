"""TCTL parser (PLY) for TimedCGS models, with freeze variables and clock constraints.

It rejects the next operator: "TCTL has no next-time operator [...] because if time
is dense then, by definition, there is no unique next time" (Alur, Courcoubetis,
Dill, Information and Computation 1993, p. 10).
"""

import re

from model_checker.parsers.formulas.parser_utils import (
    _MODAL_TOKEN_PREFIX,
    _MODAL_TOKEN_SUFFIX,
    normalize_formula_text,
    run_common_prechecks,
    until_operands,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.syntax_patterns import TCTL_TOL_PROPOSITION_TOKEN

# `X` alone is never a TCTL name (a name starts lowercase), so this cannot reject a
# valid formula; `xray` and `nextstate` stay names.
_NEXT_OPERATOR = re.compile(
    _MODAL_TOKEN_PREFIX + r"(?:[AE]\s*)?(?:X|next)" + _MODAL_TOKEN_SUFFIX
)


# --- AST nodes ---
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
    def __init__(self, constraints: str) -> None:
        super().__init__()
        self.constraints = constraints

    def __repr__(self) -> str:
        return self.constraints

    def __str__(self) -> str:
        return self.constraints


class BooleanConst(Expr):
    def __init__(self, value: bool) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return "true" if self.value else "false"


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
        reserved = {
            "implies": "IMPLIES",
            "true": "TRUE",
            "false": "FALSE",
            "forall": "FORALL",
            "exist": "EXIST",
            "and": "AND",
            "or": "OR",
            "not": "NOT",
        }
        t.type = reserved.get(t.value, "PROP")
        if t.type == "FORALL":
            t.value = "A"
        elif t.type == "EXIST":
            t.value = "E"
        return t

    t_PROP.__doc__ = TCTL_TOL_PROPOSITION_TOKEN

    def t_IMPLIES(self, t):
        r"->|implies\b"
        return t

    def t_FORALL(self, t):
        r"A(?=[FGXU\s(\[]|$)|forall\b"
        t.value = "A"
        return t

    def t_EXIST(self, t):
        r"E(?=[FGXU\s(\[]|$)|exist\b"
        t.value = "E"
        return t

    t_GEQ = r"\>\="
    t_LEQ = r"\<\="
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
        self._connective(p[0], p[1], p[2], p[3])

    def p_expression_ternary(self, p):
        """expression : FORALL expression UNTIL expression
        | EXIST expression UNTIL expression
        | FORALL LPAREN expression UNTIL expression RPAREN
        | EXIST LPAREN expression UNTIL expression RPAREN"""
        left, operator, right = until_operands(p)
        p[0] = QuantifiedPath(p[1], Binary(operator, left, right))
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : FORALL GLOBALLY expression
        | FORALL EVENTUALLY expression
        | EXIST GLOBALLY expression
        | EXIST EVENTUALLY expression"""
        p[0] = QuantifiedPath(p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    def p_expression_not(self, p):
        """expression : NOT expression"""
        p[0] = Unary(p[1], p[2])
        self._negation(p[0], p[2])

    def p_expression_boolean(self, p):
        """expression : FALSE
        | TRUE"""
        p[0] = BooleanConst(str(p[1]).lower() in {"true", "@"})

    def p_expression_freeze(self, p):
        """expression : PROP DOT expression"""
        self._check_proposition_name(p[1], kind="Clock")
        p[0] = FreezeExpr(p[1], p[3])
        self._prefix_over(p[0], f"{p[1]}.", p.lexpos(1), p[3])

    def p_expression_clock_constraint_on_expr(self, p):
        """expression : expression TIME_SEP expression"""
        p[0] = ClockExpr(p[1], p[3])
        self._attachment(p[0], p[3])

    def _proposition_node(self, name):
        return AtomicProp(name)

    def p_expression_time(self, p):
        """expression : PROP LEQ CONST
        | PROP LESS CONST
        | PROP GEQ CONST
        | PROP GREATER CONST
        """
        self._check_proposition_name(p[1], kind="Clock")
        p[0] = SimpleTimeExpr(p[1] + p[2] + p[3])

    # --- Validation ---
    def parse(self, formula, **kwargs):
        if isinstance(formula, str):
            formula = normalize_formula_text(formula)
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        next_op = _NEXT_OPERATOR.search(formula)
        if next_op:
            return (
                False,
                f"TCTL has no next operator ('{next_op.group(0)}' at position "
                f"{next_op.start() + 1}): time is dense, so there is no unique "
                "next state",
            )
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_operators=set("<>=!&|->:.() "),
        )
