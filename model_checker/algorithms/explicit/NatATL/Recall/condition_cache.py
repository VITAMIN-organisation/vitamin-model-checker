"""
Condition caching for NatATL Recall to avoid redundant CTL model_checking calls.

When the same (condition, model_path) is evaluated in legit_strategy_check and
boolean_pruning across strategies, the result is cached. Key: (condition, model_path).
"""

from typing import Any, Dict, Optional

from model_checker.algorithms.explicit.CTL import model_checking


def ctl_model_checking_cached(
    condition: str,
    model_path: str,
    preloaded_model: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Run CTL model_checking for a condition with caching.

    Uses (condition, model_path) as cache key. On hit, returns cached result.
    On miss, calls model_checking, stores and returns.

    Args:
        condition: CTL condition formula string
        model_path: Path to model file
        preloaded_model: Optional CGS to avoid re-reading the file

    Returns:
        Same dict as CTL model_checking (res, initial_state, etc.)
    """
    if not preloaded_model:
        # Fallback to a global or don't cache if no model object is available
        return model_checking(condition, model_path, preloaded_model=preloaded_model)

    if not hasattr(preloaded_model, "_condition_cache"):
        preloaded_model._condition_cache = {}

    key = (condition, model_path)
    if key not in preloaded_model._condition_cache:
        preloaded_model._condition_cache[key] = model_checking(
            condition, model_path, preloaded_model=preloaded_model
        )
    return preloaded_model._condition_cache[key]
