"""NatATL parser (PLY-based).

What it handles:
- NatATL formulas with canonical coalition syntax <{1,2}, k> on U/G/X/F
  operators and boolean connectives.
- Propositions matching [a-z][a-z0-9_]*.

What it rejects:
- Invalid coalition shapes (empty, trailing commas).
- Uppercase letters outside modal operators U/G/X/F.
- Missing coalitions for temporal operators.
- ATL-style coalitions <1,2> without explicit bound.

Behavior:
- Returns AST tuple/string on success or None on invalid input; raises
  ValueError/CoalitionValueError for coalition structure issues.
"""

import re
from typing import Optional

from ..parser_utils import (
    run_common_prechecks,
    validate_natatl_coalition,
)
from ..shared_parser import BaseLogicParser

MAX_PROP_LEN_POST_VALIDATION = 1000


class NatATLParser(BaseLogicParser):
    """Parser for NatATL formulas (coalition/bound syntax and temporal ops).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set max_coalition (n_agent) before parsing for coalition validation.
    """

    def __init__(self):
        """Initialize the NatATL lexer and parser (PLY)."""
        super().__init__()
        self.tokens.extend(["COALITION", "PROP"])
        self.max_coalition = 0
        self.build()

    # Canonical NatATL coalition: <{agents}, bound>
    t_COALITION = r"<\{(?:\d+,)*\d+\},\s*\d+>"
    t_PROP = r"[a-z][a-z0-9_]*"

    # --- Grammar Rules ---

    def p_expression_ternary(self, p):
        """expression : COALITION expression UNTIL expression
        | COALITION LPAREN expression UNTIL expression RPAREN"""
        coalition_str = p[1]
        coalition_values, k_value = validate_natatl_coalition(
            coalition_str, self.max_coalition
        )
        if len(p) == 5:
            p[0] = (f"<{{{coalition_values}}},{k_value}>{p[3]}", p[2], p[4])
        else:
            p[0] = (f"<{{{coalition_values}}},{k_value}>{p[4]}", p[3], p[5])

    def p_expression_unary(self, p):
        """expression : COALITION GLOBALLY expression
        | COALITION NEXT expression
        | COALITION EVENTUALLY expression"""
        coalition_str = p[1]
        coalition_values, k_value = validate_natatl_coalition(
            coalition_str, self.max_coalition
        )
        p[0] = (f"<{{{coalition_values}}},{k_value}>{p[2]}", p[3])

    def parse(self, formula, n_agent=0, **kwargs):
        self.max_coalition = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        _ALLOWED_UPPERCASE = {"U", "G", "X", "F"}

        valid, err = run_common_prechecks(
            formula,
            coalition_required=False,
            allow_hash_at=False,
            allow_negative_agents=False,
            allowed_uppercase=_ALLOWED_UPPERCASE,
            allowed_operators=set("<>(),{}!&|->"),
        )
        if not valid:
            return False, err

        # Reject invalid coalition syntax before parsing
        if re.search(r"<\s*>", formula):
            return False, "Empty coalition '<>' is not allowed"
        if re.search(r"<\s*\d+\s*,\s*>", formula):
            return False, "Trailing comma in coalition is not allowed"

        return True, None

    def _post_validation(self, formula, result):
        if result is None:
            return False

        if isinstance(result, str):
            if not re.match(r"^[a-z][a-z\d_]*$", result):
                return False
            if re.search(r"[UGXF]", formula):
                return False

        if isinstance(result, str) and len(result) > MAX_PROP_LEN_POST_VALIDATION:
            return False

        return True

    def p_error(self, p):
        super().p_error(p)
