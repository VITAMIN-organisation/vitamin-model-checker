"""NatATL parser (PLY): coalition and bound `<{1,2}, k>` before U, G, X and F.

The bound is required, so an ATL-style coalition without it is rejected.
"""

import re

from model_checker.parsers.syntax_patterns import (
    EMPTY_COALITION_RE,
    NATATL_COALITION_TOKEN,
    PROPOSITION_TOKEN,
)

from ..parser_utils import (
    run_common_prechecks,
    until_operands,
    validate_natatl_coalition,
)
from ..shared_parser import BaseLogicParser

MAX_PROP_LEN_POST_VALIDATION = 1000


class NatATLParser(BaseLogicParser):
    """`parse` returns an AST tuple, or None with the reason in `errors`."""

    def __init__(self):
        """Initialize the NatATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(["COALITION", "PROP"])
        self.max_coalition = 0
        self.build()

    # Canonical NatATL coalition: <{agents}, bound>
    t_COALITION = NATATL_COALITION_TOKEN
    t_PROP = PROPOSITION_TOKEN

    # --- Grammar Rules ---

    def p_expression_ternary(self, p):
        """expression : COALITION expression UNTIL expression
        | COALITION LPAREN expression UNTIL expression RPAREN"""
        coalition_str = p[1]
        coalition_values, k_value = validate_natatl_coalition(
            coalition_str, self.max_coalition
        )
        left, operator, right = until_operands(p)
        p[0] = (f"<{{{coalition_values}}},{k_value}>{operator}", left, right)
        self._prefix_until(p, p[0], p[1])

    def p_expression_unary(self, p):
        """expression : COALITION GLOBALLY expression
        | COALITION NEXT expression
        | COALITION EVENTUALLY expression"""
        coalition_str = p[1]
        coalition_values, k_value = validate_natatl_coalition(
            coalition_str, self.max_coalition
        )
        p[0] = (f"<{{{coalition_values}}},{k_value}>{p[2]}", p[3])
        self._prefix_unary(p, p[0], p[1] + p[2])

    def parse(self, formula, n_agent=0, **kwargs):
        self.max_coalition = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        valid, err = run_common_prechecks(
            formula,
            coalition_required=False,
            allow_hash_at=False,
            allow_negative_agents=False,
            allowed_operators=set("<>(),{}!&|->"),
        )
        if not valid:
            return False, err

        # Reject invalid coalition syntax before parsing
        if EMPTY_COALITION_RE.search(formula):
            return False, "Empty coalition '<>' is not allowed"
        if re.search(r"<\s*\d+\s*,\s*>", formula):
            return False, "Trailing comma in coalition is not allowed"

        return True, None

    def _post_validation(self, formula, result):
        too_long = (
            isinstance(result, str) and len(result) > MAX_PROP_LEN_POST_VALIDATION
        )
        return super()._post_validation(formula, result) and not too_long
