"""Cache of CTL results for NatATL Recall conditions, keyed by (condition, model_path),
so `legit_strategy_check` and `boolean_pruning` do not check one twice."""

from typing import Any

from model_checker.algorithms.explicit.CTL.CTL import model_checking


def ctl_model_checking_cached(
    condition: str,
    model_path: str,
    preloaded_model: Any | None = None,
) -> dict[str, Any]:
    """CTL `model_checking` of `condition`, cached on `preloaded_model`; without a
    preloaded model nothing is cached."""
    if not preloaded_model:
        return model_checking(condition, model_path, preloaded_model=preloaded_model)

    if not hasattr(preloaded_model, "_condition_cache"):
        preloaded_model._condition_cache = {}

    key = (condition, model_path)
    if key not in preloaded_model._condition_cache:
        preloaded_model._condition_cache[key] = model_checking(
            condition, model_path, preloaded_model=preloaded_model
        )
    return preloaded_model._condition_cache[key]
