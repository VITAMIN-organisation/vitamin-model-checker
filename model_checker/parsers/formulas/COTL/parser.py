"""COTL formula parser: `<legion><budget>` before X, WX, F, G, U, R and W.

- The legion is a set of demon indices and may be empty (`<>`); the budget is an
  integer >= 0.
- WX is weak next. `<1><2> (p U q)` and `<1><2> p U q` are the same formula.
"""

import re

from model_checker.parsers.syntax_patterns import COTL_LEGION_BUDGET_TOKEN

from ..parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    until_operands,
    validate_agents,
)
from ..shared_parser import BaseLogicParser

_LEGION_BUDGET_RE = re.compile(r"^<(?P<legion>[\d,]*)><(?P<budget>\d+)>")
_LEGION_BUDGET_TOKEN_RE = re.compile(COTL_LEGION_BUDGET_TOKEN)


def parse_legion_budget(modality: str) -> tuple[tuple[int, ...], int]:
    """Split a modality such as `<1,3><2>X` into the sorted legion (1, 3) and budget 2."""
    match = _LEGION_BUDGET_RE.match(modality)
    if match is None:
        raise ValueError(f"COTL: '{modality}' does not start with <legion><budget>")
    members = match.group("legion")
    legion = tuple(sorted(int(i) for i in members.split(","))) if members else ()
    return legion, int(match.group("budget"))


class COTLParser(BaseLogicParser):
    """PLY parser for COTL; call parse(formula, n_agent=<number of demons>)."""

    precedence = (
        ("right", "IMPLIES"),
        ("left", "OR"),
        ("left", "AND"),
        ("right", "NOT"),
        ("right", "UNTIL", "RELEASE", "WEAK"),
        ("right", "GLOBALLY", "NEXT", "WEAK_NEXT", "EVENTUALLY"),
    )

    def __init__(self):
        super().__init__()
        self.tokens.extend(
            [
                "LEGION",
                "PROP",
                "UNTIL",
                "RELEASE",
                "WEAK",
                "GLOBALLY",
                "NEXT",
                "WEAK_NEXT",
                "EVENTUALLY",
            ]
        )
        self.number_of_demons = 0
        self.build()

    t_PROP = PROPOSITION_TOKEN_PATTERN
    t_LEGION = COTL_LEGION_BUDGET_TOKEN

    def t_WEAK_NEXT(self, t):
        r"WX(?![a-zA-Z0-9_])"
        return t

    def t_RELEASE(self, t):
        r"R(?![a-zA-Z0-9_])|release\b"
        t.value = "R"
        return t

    def t_WEAK(self, t):
        r"W(?![a-zA-Z0-9_])|weak\b"
        t.value = "W"
        return t

    def p_expression_legion_unary(self, p):
        """expression : LEGION NEXT expression
        | LEGION WEAK_NEXT expression
        | LEGION EVENTUALLY expression
        | LEGION GLOBALLY expression"""
        self._check_legion(p[1])
        p[0] = (p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    def p_expression_legion_binary(self, p):
        """expression : LEGION expression UNTIL expression
        | LEGION expression RELEASE expression
        | LEGION expression WEAK expression
        | LEGION LPAREN expression UNTIL expression RPAREN
        | LEGION LPAREN expression RELEASE expression RPAREN
        | LEGION LPAREN expression WEAK expression RPAREN"""
        self._check_legion(p[1])
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

    def _check_legion(self, token: str) -> None:
        legion, _ = parse_legion_budget(token)
        validate_agents(list(legion), self.number_of_demons, member="demon")

    def parse(self, formula, n_agent=0, **kwargs):
        """`n_agent` is the number of demons in the model."""
        self.number_of_demons = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(formula, coalition_required=False)
        if not valid:
            return False, err
        leftover = _LEGION_BUDGET_TOKEN_RE.sub("", formula)
        bad = re.search(r"(?:<[^<>]*>?)+", leftover)
        if bad:
            return False, (
                f"Invalid modality near '{bad.group(0)}': expected <legion><budget>, "
                "e.g. <1,2><3> X p or <><0> X p"
            )
        return True, None
