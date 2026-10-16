"""Retired finite-unfolding solver: import-compatible, fail-closed migration stub.

The old API received an already converted CTL formula, losing strategic scope.
It cannot be safely auto-translated back to a general NatATL formula. Use the
public Recall entry with the ORIGINAL NatATL formula; its finite product has
no arbitrary history-depth limit. Tree utilities remain for NatSL/tests.
"""
from typing import Any


def solve_natatl_recall(
    k: int, agent_actions: dict[str, list[str]], actions_list: list[list[str]],
    atomic_propositions: list[str], CTLformula: str, agents: list[int],
    model_parser: Any, filename: str,
) -> dict[str, Any]:
    raise ValueError(
        "[SEMANTIC] Legacy finite-unfolding Recall solver is retired. "
        "Use NatATL.Recall.natatl_recall.model_checking with the original NatATL formula."
    )
