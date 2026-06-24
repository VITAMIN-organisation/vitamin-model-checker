"""ATL prefilter for resource-bounded logics (OATL, RBATL, RABATL)."""

from collections.abc import Callable
from typing import Any

from model_checker.algorithms.explicit.ATL.ATL import _core_atl_checking
from model_checker.algorithms.explicit.shared.resource_bounded_to_atl import (
    resource_bounded_atl_to_atl,
)
from model_checker.engine.execution import execute_model_checking_with_parser


def run_atl_prefilter(
    formula: str,
    filename: str,
    full_checking: Callable[[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Run unbounded ATL first; skip the full checker when the formula is already false."""
    atl_result = execute_model_checking_with_parser(
        resource_bounded_atl_to_atl(formula),
        filename,
        "ATL",
        _core_atl_checking,
    )
    if "error" in atl_result:
        return atl_result
    if str(atl_result.get("initial_state", "")).endswith(": False"):
        return atl_result

    return full_checking(formula, filename)
