from model_checker.parsers.formulas.parser_utils import (
    run_common_prechecks,
    validate_ast,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser

from .ictl_ply_parser import do_parsingICTL, verifyICTL

_ICTL_VALID_OPERATORS = frozenset(
    {
        "EX",
        "AX",
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


class ICTLParser(BaseLogicParser):
    """VMI Wrapper for the standalone ICTL parser."""

    def __init__(self):
        super().__init__()
        self.lexer = None
        self.parser = None

    def build(self, **kwargs):
        pass

    def _pre_validation(self, formula):
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
        )

    def _post_validation(self, formula, result):
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True
        return validate_ast(result, _ICTL_VALID_OPERATORS)

    def parse(self, formula: str, **kwargs) -> tuple | None:
        self.errors = []
        valid, err = self._pre_validation(formula)
        if not valid:
            if err:
                self.errors.append(err)
            return None
        result = do_parsingICTL(formula)
        if result is None:
            if not self.errors:
                self.errors.append("Syntax error in formula")
            return None
        if not self._post_validation(formula, result):
            return None
        return result

    def verify(self, token_name: str, string: str) -> bool:
        return verifyICTL(token_name, string)
