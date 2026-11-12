"""IATL parser (PLY-based).

Coalition syntax matches the rest of the project:
- Existential: ``<1>``, ``<1,2>`` (same as ATL)
- Universal: ``[1]``, ``[1,2]`` (IATL-specific dual modality)

Temporal operators: U, R, G, X, F and boolean connectives ``&&``, ``||``, ``!``, ``->``.
"""

from model_checker.parsers.formulas.parser_utils import (
    CoalitionValueError,
    run_common_prechecks,
    until_operands,
    validate_coalition,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser, word_rule
from model_checker.parsers.syntax_patterns import (
    COALITION_ATL_TOKEN,
    COALITION_UNIVERSAL_TOKEN,
    ICTL_PROPOSITION_TOKEN,
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
        self.tokens.extend(["PROP", "COALITION", "COALITION_UNIVERSAL", "RELEASE"])
        self.n_agent = 0
        self.build()

    t_RELEASE = word_rule("RELEASE")

    t_COALITION = COALITION_ATL_TOKEN
    t_COALITION_UNIVERSAL = COALITION_UNIVERSAL_TOKEN
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
        left, operator, right = until_operands(p)
        p[0] = (p[1] + operator, left, right)
        self._prefix_until(p, p[0], p[1])

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
        self._prefix_unary(p, p[0], p[1] + p[2])

    def parse(self, formula, n_agent=None, max_coalition=None, **kwargs):
        if n_agent is not None:
            self.n_agent = n_agent
        elif max_coalition is not None:
            self.n_agent = max_coalition
        else:
            self.n_agent = 0
        return super().parse(formula, **kwargs)

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=True,
            allow_negative_agents=False,
            allowed_operators=set("<>(),!&|->[]"),
        )
