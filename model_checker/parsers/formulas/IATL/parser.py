"""IATL parser (PLY-based).

Coalition syntax matches the rest of the project:
- Existential: ``<1>``, ``<1,2>`` (same as ATL)
- Universal: ``[1]``, ``[1,2]`` (IATL-specific dual modality)

Temporal operators: U, R, G, X, F and boolean connectives ``&&``, ``||``, ``!``, ``->``.
"""

import re
from typing import Optional

from model_checker.parsers.formulas.parser_utils import (
    CoalitionValueError,
    run_common_prechecks,
    validate_ast,
    validate_coalition,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.syntax_patterns import ICTL_PROPOSITION_TOKEN

_COALITION_EXIST_PATTERN = re.compile(
    r"^<\d+(?:,\d+)*>(U|G|X|F|R|UNTIL|GLOBALLY|NEXT|EVENTUALLY|RELEASE)$",
    re.IGNORECASE,
)
_COALITION_UNIVERSAL_PATTERN = re.compile(
    r"^\[\d+(?:,\d+)*\](U|G|X|F|R|UNTIL|GLOBALLY|NEXT|EVENTUALLY|RELEASE)$",
    re.IGNORECASE,
)


def _validate_universal_coalition(coalition_str: str, max_coalition: int) -> None:
    """Validate ``[1,2]`` coalition strings using shared agent-range checks."""
    if coalition_str == "[]" or coalition_str.endswith(",]"):
        raise CoalitionValueError("Empty coalition or trailing comma not allowed")
    inner = coalition_str[1:-1]
    validate_coalition(f"<{inner}>", max_coalition)


class IATLParser(BaseLogicParser):
    """Parser for IATL formulas over BCGS models."""

    def __init__(self) -> None:
        super().__init__()
        self.tokens.extend(["PROP", "COALITION", "COALITION_UNIVERSAL"])
        self.n_agent = 0
        self.build()

    def t_RELEASE(self, t):
        r"R|release\b"
        t.value = "R"
        return t

    t_COALITION = r"<\d+(?:,\d+)*>"
    t_COALITION_UNIVERSAL = r"\[\d+(?:,\d+)*\]"
    t_PROP = ICTL_PROPOSITION_TOKEN

    def p_expression_ternary(self, p):
        """expression : COALITION expression UNTIL expression
        | COALITION expression RELEASE expression
        | COALITION_UNIVERSAL expression UNTIL expression
        | COALITION_UNIVERSAL expression RELEASE expression
        | COALITION LPAREN expression UNTIL expression RPAREN
        | COALITION LPAREN expression RELEASE expression RPAREN
        | COALITION_UNIVERSAL LPAREN expression UNTIL expression RPAREN
        | COALITION_UNIVERSAL LPAREN expression RELEASE expression RPAREN"""
        coalition_str = p[1]
        if coalition_str.startswith("["):
            _validate_universal_coalition(coalition_str, self.n_agent)
        else:
            validate_coalition(coalition_str, self.n_agent)
        if len(p) == 5:
            p[0] = (p[1] + p[3], p[2], p[4])
        else:
            p[0] = (p[1] + p[4], p[3], p[5])

    def p_expression_unary(self, p):
        """expression : COALITION GLOBALLY expression
        | COALITION NEXT expression
        | COALITION EVENTUALLY expression
        | COALITION_UNIVERSAL GLOBALLY expression
        | COALITION_UNIVERSAL NEXT expression
        | COALITION_UNIVERSAL EVENTUALLY expression"""
        coalition_str = p[1]
        if coalition_str.startswith("["):
            _validate_universal_coalition(coalition_str, self.n_agent)
        else:
            validate_coalition(coalition_str, self.n_agent)
        p[0] = (p[1] + p[2], p[3])

    def parse(self, formula, n_agent=0, **kwargs):
        self.n_agent = n_agent or kwargs.get("max_coalition", 0)
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            allow_negative_agents=False,
            allowed_operators=set("<>(),!&|->[]"),
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False

        valid_operators = {
            "U",
            "R",
            "G",
            "X",
            "F",
            "&&",
            "||",
            "->",
            "AND",
            "OR",
            "NOT",
            "IMPLIES",
            "UNTIL",
            "RELEASE",
            "GLOBALLY",
            "NEXT",
            "EVENTUALLY",
            "!",
        }

        try:
            return validate_ast(
                result,
                valid_operators,
                coalition_pattern=_COALITION_EXIST_PATTERN,
                extra_atom_patterns=(_COALITION_UNIVERSAL_PATTERN,),
            )
        except Exception:
            return False
