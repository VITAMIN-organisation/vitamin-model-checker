"""CapATL parser (PLY): coalitions `<{1,2}>` and the knowledge operator `K1(...)`.

The knowledge operator follows AAMAS 2024 p. 125-126: the parentheses are required,
and the capacity formula inside holds only `agent is capacity` and connectives.
"""

import re

from model_checker.parsers.formulas.parser_utils import (
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    until_operands,
    validate_ast,
    validate_coalition,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.syntax_patterns import AGENT_LIST, CAPATL_COALITION_TOKEN

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
        "IS",
    }
)

_CAPATL_MODAL_OPS = r"U|R|X|F|G|UNTIL|RELEASE|NEXT|EVENTUALLY|GLOBALLY"
_COALITION_OPERATOR_PATTERN = re.compile(
    rf"^{CAPATL_COALITION_TOKEN}({_CAPATL_MODAL_OPS})$",
    re.IGNORECASE,
)

# K^a_cap of the paper, typed as `K1` or `kcap1`; `K1x` stays a proposition name.
_KCAP_TOKEN = r"(?:K|kcap)(\d+)(?![a-zA-Z0-9_])"
# Group 2 is empty when the operator has no parenthesis after it.
_KCAP_IN_FORMULA = re.compile(rf"(?<![a-zA-Z0-9_]){_KCAP_TOKEN}(\s*\()?")
# AST value of the knowledge operator after the lexer normalizes `kcap1` to `K1`.
KCAP_OPERATOR_PATTERN = re.compile(r"^K\d+$")
_AGENT_PATTERN = re.compile(r"^\d+$")
# Reject NatATL-looking `<{agents}, k>`; CapATL coalitions have no formula bound.
_FORMULA_BOUND_PATTERN = re.compile(rf"<{{{AGENT_LIST}}},\s*-?\d+>")


class CapATLParser(BaseLogicParser):
    """`parse` returns an AST tuple, or None with the reason in `errors`."""

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
        agent = re.sub(r"\D", "", t.value)
        # int() so that K01 and K1 are one operator.
        t.value = f"K{int(agent)}"
        return t

    t_KCAP.__doc__ = _KCAP_TOKEN

    def t_COALITION(self, t):
        match = re.match(CAPATL_COALITION_TOKEN, t.value)
        if match:
            t.value = match.group(1)
        return t

    t_COALITION.__doc__ = CAPATL_COALITION_TOKEN

    t_AGENT = r"\d+"
    t_PROP = PROPOSITION_TOKEN_PATTERN

    # --- Grammar Rules ---
    def p_expression_ternary(self, p):
        """expression : COALITION expression UNTIL expression
        | COALITION expression RELEASE expression
        | COALITION LPAREN expression UNTIL expression RPAREN
        | COALITION LPAREN expression RELEASE expression RPAREN"""
        coalition_str = f"<{{{p[1]}}}>"
        validate_coalition(f"<{p[1]}>", self.max_coalition)
        left, operator, right = until_operands(p)
        p[0] = (coalition_str + operator, left, right)
        self._prefix_until(p, p[0], coalition_str)

    def p_expression_unary(self, p):
        """expression : COALITION NEXT expression
        | COALITION EVENTUALLY expression
        | COALITION GLOBALLY expression"""
        coalition_str = f"<{{{p[1]}}}>"
        validate_coalition(f"<{p[1]}>", self.max_coalition)
        p[0] = (coalition_str + p[2], p[3])
        self._prefix_unary(p, p[0], coalition_str + p[2])

    def p_expression_kcap(self, p):
        """expression : KCAP LPAREN capformula RPAREN"""
        self._check_agent(p[1][1:], p[1])
        p[0] = (p[1], p[3])

    def p_capformula_group(self, p):
        """capformula : LPAREN capformula RPAREN"""
        p[0] = p[2]

    def p_capformula_binary(self, p):
        """capformula : capformula AND capformula
        | capformula OR capformula
        | capformula IMPLIES capformula"""
        p[0] = (p[2], p[1], p[3])

    def p_capformula_not(self, p):
        """capformula : NOT capformula"""
        p[0] = (p[1], p[2])

    def p_capformula_constant(self, p):
        """capformula : TRUE
        | FALSE"""
        p[0] = p[1]

    def p_capformula_is(self, p):
        """capformula : AGENT IS PROP"""
        self._check_agent(p[1], f"{p[1]} is {p[3]}")
        p[0] = ("is", p[1], p[3])

    def p_capformula_kcap(self, p):
        """capformula : KCAP LPAREN capformula RPAREN"""
        self._log_error(
            f"{p[1]}(...) inside a capacity formula: CapATL has no nested "
            "knowledge operator"
        )
        p[0] = (p[1], p[3])

    def p_capformula_prop(self, p):
        """capformula : PROP"""
        self._log_error(
            f"'{p[1]}' inside K(...): a capacity formula holds only "
            "'agent is capacity', !, &&, ||, ->, true and false"
        )
        p[0] = p[1]

    def _check_agent(self, agent: str, where: str) -> None:
        if not 1 <= int(agent) <= self.max_coalition:
            self._log_error(
                f"Agent {agent} in '{where}' must be between 1 and "
                f"{self.max_coalition}"
            )

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

        if _FORMULA_BOUND_PATTERN.search(formula):
            return (
                False,
                "CapATL uses <{coalition}> without a numeric bound "
                "(capacities are defined in the capCGS model)",
            )

        kcaps = list(_KCAP_IN_FORMULA.finditer(formula))
        for kcap in kcaps:
            if kcap.group(2) is None:
                op = kcap.group(0)
                return (
                    False,
                    f"'{op}' needs parentheses around its capacity formula, "
                    f"as in {op}(1 is c)",
                )

        has_coalition = re.search(r"<\{[\d,]+\}>", formula)
        if not (has_coalition or kcaps):
            return (
                False,
                "CapATL requires either coalition modalities <{coalition}> "
                "or knowledge operators K1(...)",
            )

        return True, None

    def _post_validation(self, formula, result):
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True
        return validate_ast(
            result,
            _CAPATL_VALID_OPERATORS,
            coalition_pattern=_COALITION_OPERATOR_PATTERN,
            extra_atom_patterns=(KCAP_OPERATOR_PATTERN, _AGENT_PATTERN),
        )
