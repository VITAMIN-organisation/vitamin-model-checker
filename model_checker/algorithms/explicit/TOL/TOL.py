"""TOL model checking."""

from model_checker.algorithms.explicit.shared.timed_ast_operators import (
    timed_model_checking,
)
from model_checker.algorithms.explicit.TOL.solver import solve_tree

model_checking = timed_model_checking("TOL", solve_tree, track_divergence=False)
