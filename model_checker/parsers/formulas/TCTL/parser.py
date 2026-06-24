from model_checker.parsers.formulas.parser_utils import (
    run_common_prechecks,
    validate_ast,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser

from .tctl_ply_parser import do_parsingTCTL, verifyTCTL

_TCTL_VALID_OPERATORS = frozenset(
    {
        "EF",
        "AF",
        "EG",
        "AG",
        "EU",
        "AU",
        "UNTIL",
        "AND",
        "OR",
        "NOT",
        "IMPLIES",
        "&&",
        "||",
        "!",
        "->",
    }
)


class TCTLParser(BaseLogicParser):
    """Parser for TCTL formulas (Expr AST via tctl_ply_parser)."""

    def __init__(self):
        super().__init__()

    def _pre_validation(self, formula):
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_operators=set("<>(),!&|->:=. "),
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True
        return validate_ast(result, _TCTL_VALID_OPERATORS)

    def parse(self, formula: str, **kwargs) -> tuple | None:
        self.errors = []
        valid, err = self._pre_validation(formula)
        if not valid:
            if err:
                self.errors.append(err)
            return None
        result = do_parsingTCTL(formula)
        if result is None:
            if not self.errors:
                self.errors.append("Syntax error in formula")
            return None
        if not self._post_validation(formula, result):
            return None
        return result

    def verify(self, token_name: str, string: str) -> bool:
        return verifyTCTL(token_name, string)

    def build(self, **kwargs) -> None:
        """TCTL uses tctl_ply_parser; no PLY tables on this class."""
