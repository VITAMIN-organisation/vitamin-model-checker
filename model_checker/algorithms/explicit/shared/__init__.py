"""
Shared utilities for model checking algorithms.

This module exports common functions used across multiple logic implementations
to avoid code duplication and ensure consistent behavior.
"""

from model_checker.algorithms.explicit.shared.atom_utils import (
    resolve_atom,
    resolve_atom_with_constants,
)
from model_checker.algorithms.explicit.shared.result_utils import (
    create_verification_result,
    format_model_checking_result,
    format_verification_result,
    verify_initial_state,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    normalize_state_set,
    state_names_to_indices,
    state_set_to_str,
    states_difference,
    states_intersection,
    states_union,
    value_for_cache_key,
)
from model_checker.algorithms.explicit.shared.trace_utils import (
    build_predecessor_map_bfs,
    build_predecessor_map_forward,
    extract_shortest_trace,
    format_trace_with_properties,
    reconstruct_counterexample_trace,
    reconstruct_trace_bfs,
    reconstruct_trace_from_predecessors,
)
from model_checker.algorithms.explicit.shared.verification_result import (
    StateTrace,
    StrategyTrace,
    VerificationResult,
)

__all__ = [
    # State utilities
    "normalize_state_set",
    "value_for_cache_key",
    "state_names_to_indices",
    "state_set_to_str",
    "states_intersection",
    "states_union",
    "states_difference",
    # Atom utilities
    "resolve_atom",
    "resolve_atom_with_constants",
    # Result utilities
    "verify_initial_state",
    "format_model_checking_result",
    "format_verification_result",
    "create_verification_result",
    # Verification result classes
    "VerificationResult",
    "StateTrace",
    "StrategyTrace",
    # Trace utilities
    "reconstruct_trace_from_predecessors",
    "reconstruct_trace_bfs",
    "reconstruct_counterexample_trace",
    "build_predecessor_map_bfs",
    "build_predecessor_map_forward",
    "extract_shortest_trace",
    "format_trace_with_properties",
]
