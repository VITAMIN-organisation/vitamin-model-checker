"""OATL parser (PLY): coalition and Demon budget `<1,2><5>` (budget 0 allowed) before
X, F, G, U, R and W.
"""

import re

from model_checker.parsers.syntax_patterns import (
    AGENT_LIST,
    NON_NEGATIVE_INT,
    OATL_COALITION_BUDGET_TOKEN,
)

from ..parser_utils import (
    BOOLEAN_AST_OPERATORS,
    PROPOSITION_TOKEN_PATTERN,
    run_common_prechecks,
    until_operands,
    validate_ast,
    validate_coalition_bound_token,
)
from ..shared_parser import BaseLogicParser

_OATL_MODAL_OPS = r"F|G|X|U|R|W|UNTIL|RELEASE|WEAK|NEXT|EVENTUALLY|GLOBALLY"
_OATL_COALITION_OPERATOR_PATTERN = re.compile(
    rf"^{OATL_COALITION_BUDGET_TOKEN}({_OATL_MODAL_OPS})$",
    re.IGNORECASE,
)
_OATL_VALID_OPERATORS = (
    frozenset(
        {
            "U",
            "R",
            "W",
            "X",
            "F",
            "G",
            "UNTIL",
            "RELEASE",
            "WEAK",
            "NEXT",
            "EVENTUALLY",
            "GLOBALLY",
        }
    )
    | BOOLEAN_AST_OPERATORS
)
_MISSING_BOUND_TEMPORAL_RE = re.compile(rf"<{AGENT_LIST}>\s*[FGXURW]")
_COALITION_BOUND_PROBE_RE = re.compile(
    rf"<{AGENT_LIST}><(?P<bound>\d+)>\s*(?P<op>[FGXURW])"
)
_BOUND_PRESENT_RE = re.compile(rf"<{AGENT_LIST}><\d+>")


class OATLParser(BaseLogicParser):
    """`parse` returns an AST tuple, or None with the reason in `errors`."""

    def __init__(self):
        """Initialize the OATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(
            [
                "COALITION_DEMONIC",
                "PROP",
                "UNTIL",
                "RELEASE",
                "WEAK",
                "GLOBALLY",
                "NEXT",
                "EVENTUALLY",
            ]
        )
        self.max_coalition = 0
        self.build()

    # === Tokens ===
    t_PROP = PROPOSITION_TOKEN_PATTERN
    t_COALITION_DEMONIC = OATL_COALITION_BUDGET_TOKEN
    # Budget 0 is valid: the Demon can then erase only zero-cost actions.
    _bound_pattern = NON_NEGATIVE_INT
    _min_bound = 0

    def t_RELEASE(self, t):
        r"R(?![a-zA-Z0-9_])|release\b"
        t.value = "R"
        return t

    def t_WEAK(self, t):
        r"W(?![a-zA-Z0-9_])|weak\b"
        t.value = "W"
        return t

    # === Grammar ===
    def p_expression_ternary(self, p):
        """expression : COALITION_DEMONIC expression UNTIL expression
        | COALITION_DEMONIC expression RELEASE expression
        | COALITION_DEMONIC expression WEAK expression
        | COALITION_DEMONIC LPAREN expression UNTIL expression RPAREN
        | COALITION_DEMONIC LPAREN expression RELEASE expression RPAREN
        | COALITION_DEMONIC LPAREN expression WEAK expression RPAREN"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_pattern=self._bound_pattern
        )
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : COALITION_DEMONIC GLOBALLY expression
        | COALITION_DEMONIC NEXT expression
        | COALITION_DEMONIC EVENTUALLY expression"""
        validate_coalition_bound_token(
            p[1], self.max_coalition, bound_pattern=self._bound_pattern
        )
        p[0] = (p[1] + p[2], p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    # === Validation ===
    def parse(self, formula, n_agent=0, **kwargs):
        self.max_coalition = n_agent
        return super().parse(formula, **kwargs)

    def _coalition_bound_pre_validation(self, formula) -> tuple[bool, str | None]:
        coalition_temporal_match = _COALITION_BOUND_PROBE_RE.search(formula)
        if coalition_temporal_match:
            bound_raw = coalition_temporal_match.group("bound")
            if int(bound_raw) < self._min_bound:
                return (
                    False,
                    f"Bound must be an integer >= {self._min_bound} for temporal operators",
                )
            if len(bound_raw) > 1 and bound_raw.startswith("0"):
                return (
                    False,
                    "Bound cannot have leading zeros (e.g., use <1><5>, not <1><05>)",
                )

        if _MISSING_BOUND_TEMPORAL_RE.search(formula) and not _BOUND_PRESENT_RE.search(
            formula
        ):
            return (
                False,
                f"Temporal operators require a bound in the form <coalition><k> with k>={self._min_bound} (e.g., <1><5>F p)",
            )
        return True, None

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            extra_invalid_regexes=(),
        )
        if not valid:
            return False, err

        return self._coalition_bound_pre_validation(formula)

    def _post_validation(self, formula, result):
        if result is None:
            return False
        return validate_ast(
            result,
            _OATL_VALID_OPERATORS,
            coalition_pattern=_OATL_COALITION_OPERATOR_PATTERN,
        )
