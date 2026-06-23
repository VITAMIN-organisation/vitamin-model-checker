"""RBATL model checker entry point."""

from functools import partial

from model_checker.algorithms.explicit.shared.bounded_atl_solver import (
    run_bounded_atl_checking,
)
from model_checker.engine.atl_prefilter import run_atl_prefilter
from model_checker.engine.execution import create_model_checking_entry

_core_rbatl_checking = partial(
    run_bounded_atl_checking, cost_filter="rbatl", logic="RBATL"
)

model_checking = create_model_checking_entry(
    "RBATL", _core_rbatl_checking, prefilter_func=run_atl_prefilter
)
