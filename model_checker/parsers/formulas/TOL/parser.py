"""TOL parser entry point (BaseLogicParser with Expr AST from tol_ply_parser)."""

from typing import Any, Optional

from model_checker.parsers.formulas.parser_utils import (
    run_common_prechecks,
    validate_ast,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser

from .tol_ply_parser import do_parsing
from .tol_ply_parser import verify as tol_verify

_TOL_VALID_OPERATORS = frozenset(
    {
        "U",
        "X",
        "F",
        "G",
        "&&",
        "AND",
        "NOT",
        "UNTIL",
        "NEXT",
        "EVENTUALLY",
        "GLOBALLY",
        "!",
        "->",
    }
)

_TOL_ALLOWED_OPERATORS = set("<>(),!&|->{} ")


class TOLParser(BaseLogicParser):
    """Parser for TOL formulas over timedCGS models."""

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
            allowed_operators=_TOL_ALLOWED_OPERATORS,
        )

    def _post_validation(self, formula, result) -> bool:
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True
        return validate_ast(result, _TOL_VALID_OPERATORS)

    def parse(self, formula: str, **kwargs: Any) -> Any:
        self.errors = []
        valid, err = self._pre_validation(formula)
        if not valid:
            if err:
                self.errors.append(err)
            return None
        result = do_parsing(formula.strip())
        if result is None:
            if not self.errors:
                self.errors.append("Syntax error in formula")
            return None
        if not self._post_validation(formula, result):
            return None
        return result

    def verify(self, name: str, string: str) -> bool:
        return tol_verify(name, string)

    def build(self, **kwargs: Any) -> None:
        """TOL uses tol_ply_parser; no PLY tables on this class."""


verify = tol_verify
