"""
Re-export of trace-enabled solver entry points from solver.

Solve logic lives in solver.py; this module preserves backward compatibility
for imports of solve_tree_with_trace and extract_trace_for_result.
"""

from model_checker.algorithms.explicit.CTL.solver import (
    extract_trace_for_result,
    solve_tree_with_trace,
)

__all__ = ["solve_tree_with_trace", "extract_trace_for_result"]
