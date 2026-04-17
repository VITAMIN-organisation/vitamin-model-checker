"""OATL parser (PLY-based).

Supported:
- OATL formulas with coalition and demonic bounds (`<1,2><5>F p`, `<1><3>G p`).
- Boolean connectives (&&, ||, !, ->) and temporal ops (U, R, W, G, X, F).

Rejects:
- Missing demonic bounds after a coalition (e.g., `<1>F p`).
- Malformed coalitions or invalid agent indices relative to n_agent.
- Non-ASCII, null bytes, or disallowed special characters in propositions.

Returns:
- AST tuple on success, or None on invalid input.
"""

import re
from typing import Optional

from ..parser_utils import (
    run_common_prechecks,
    validate_coalition_bound_token,
    verify_token,
)
from ..shared_parser import BaseLogicParser


class OATLParser(BaseLogicParser):
    """Parser for OATL formulas (coalition and demonic bounds, temporal ops).

    Use parse(formula) to get an AST tuple or None on invalid input.
    Set n_agent before parsing for coalition validation.
    """

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
        self.max_coalition = 100
        self.build()

    # === Tokens ===
    t_PROP = r"[a-z][a-z0-9_]*"
    t_COALITION_DEMONIC = r"<\d+(?:,\d+)*><[1-9]\d*>"

    def t_RELEASE(self, t):
        r"R|release\b"
        t.value = "R"
        return t

    def t_WEAK(self, t):
        r"W|weak\b"
        t.value = "W"
        return t

    # === Grammar ===
    def p_expression_ternary(self, p):
        """expression : COALITION_DEMONIC expression UNTIL expression
        | COALITION_DEMONIC expression WEAK expression
        | COALITION_DEMONIC expression RELEASE expression"""
        coalition_demonic_str = p[1]
        self._validate_coalition_demonic(coalition_demonic_str)
        p[0] = (p[1] + p[3], p[2], p[4])

    def p_expression_unary(self, p):
        """expression : COALITION_DEMONIC GLOBALLY expression
        | COALITION_DEMONIC NEXT expression
        | COALITION_DEMONIC EVENTUALLY expression"""
        coalition_demonic_str = p[1]
        self._validate_coalition_demonic(coalition_demonic_str)
        p[0] = (p[1] + p[2], p[3])

    def _validate_coalition_demonic(self, coalition_demonic_str):
        """Validate a demonic coalition token of the form <agents><bound>."""
        return validate_coalition_bound_token(
            coalition_demonic_str, self.max_coalition, bound_pattern=r"[1-9]\d*"
        )

    # === Validation ===
    def parse(self, formula, n_agent=100, **kwargs):
        self.max_coalition = n_agent
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        valid, err = run_common_prechecks(
            formula,
            allow_hash_at=True,
            coalition_required=True,
            allowed_uppercase={"F", "G", "X", "U", "R", "W"},
            extra_invalid_regexes=(),
        )
        if not valid:
            return False, err

        coalition_temporal_match = re.search(
            r"<\d+(?:,\d+)*><(?P<bound>\d+)>\s*(?P<op>[FGXURW])", formula
        )
        if coalition_temporal_match:
            bound_raw = coalition_temporal_match.group("bound")
            if int(bound_raw) == 0:
                return (
                    False,
                    "OATL bound must be a positive integer (>=1) for temporal operators",
                )
            if len(bound_raw) > 1 and bound_raw.startswith("0"):
                return (
                    False,
                    "OATL bound cannot have leading zeros (e.g., use <1><5>, not <1><05>)",
                )

        if re.search(r"<\d+(?:,\d+)*>\s*[FGXURW]", formula) and not re.search(
            r"<\d+(?:,\d+)*><[1-9]\d*>", formula
        ):
            return (
                False,
                "OATL temporal operators require a bound in the form <coalition><k> with k>=1 (e.g., <1><5>F p)",
            )
        return True, None

    def verify(self, token_name, string):
        return verify_token(self.lexer, token_name, string)
