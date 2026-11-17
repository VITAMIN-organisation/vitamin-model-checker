"""TCTL model checking."""

from model_checker.algorithms.explicit.shared.timed_ast_operators import (
    timed_model_checking,
)
from model_checker.algorithms.explicit.TCTL.solver import solve_tree

# Path quantifiers range over time-divergent paths only.
model_checking = timed_model_checking("TCTL", solve_tree, track_divergence=True)
