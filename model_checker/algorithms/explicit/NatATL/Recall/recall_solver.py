"""Bounded generate--validate--check for natural Recall strategies.

Operands are truth sets of ORIGINAL CGS states. The extended grammar enumerator
is exhaustive up to the significant-pattern cost for its explicitly defined
Reg(B(Prop)) basis (see docs/NatATL/RECALL_COMPLETENESS.md). The canonical generator
is a strict fragment and does not certify negative answers on exhaustion.
This backend is used by VITAMIN's public Recall compositional entry point.
"""

from __future__ import annotations

from collections.abc import Iterable, Set
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.recall_appropriateness import (
    InappropriateRecallRule,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_full_strategy_generation import (
    collective_full_strategies,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_lazy_generation import (
    collective_strategies,
    profile_cost,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_product import (
    build_validated_recall_product,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_temporal import (
    check_initial,
)


def solve_bounded_recall(
    cgs: Any,
    agents: Iterable[int],
    bound: int,
    operator: str,
    left_states: Set[str],
    right_states: Set[str] | None = None,
    *,
    initial_state: str | None = None,
    generator: str = "canonical",
    certify_restricted_exhaustion: bool = False,
    context=None,
) -> dict[str, Any]:
    """Find a globally appropriate bounded strategy for a universal objective.

    ``left_states`` and ``right_states`` are subsets of ORIGINAL CGS state IDs.
    ``right_states`` is required precisely for U and W.

    Agents use 1-based indices. No path length or search-candidate cap is used.
    A candidate must be globally appropriate before building the reachable
    product, and all the opponent responses are retained.

    The extended generator exhausts the supported Boolean/regular grammar;
    after complete enumeration, ``certify_restricted_exhaustion=True`` gives
    a definitive FALSE *for that grammar only*. The default remains
    conservative for direct callers and the canonical generator.
    The flag does not claim completeness for arbitrary additions to the grammar.
    """
    if generator not in ("canonical", "extended") or not isinstance(generator, str):
        raise ValueError("generator must be 'canonical' or 'extended'")
    if type(certify_restricted_exhaustion) is not bool:
        raise ValueError("certify_restricted_exhaustion must be a Boolean")
    if certify_restricted_exhaustion and generator != "extended":
        raise ValueError(
            "certified exhaustion requires generator='extended'; "
            "the canonical generator does not cover the supported Recall grammar"
        )
    scope = ("canonical_recall_fragment" if generator == "canonical"
             else "extended_recall_fragment")
    enumerate_profiles = (collective_strategies if generator == "canonical"
                          else collective_full_strategies)

    coalition = list(agents)
    if not coalition or len(set(coalition)) != len(coalition):
        raise ValueError("Expected a nonempty coalition of distinct agents")
    if any(type(agent) is not int for agent in coalition):
        raise ValueError("Coalition agents must be integer indices")
    if type(bound) is not int or bound < 0:
        raise ValueError("The recall complexity bound must be a nonnegative integer")
    if not isinstance(operator, str) or operator.upper() not in {"X", "F", "G", "U", "W"}:
        raise ValueError(f"Unsupported temporal operator: {operator!r}")
    op = operator.upper()
    if (op in {"U", "W"}) != (right_states is not None):
        raise ValueError(f"Incorrect operands for temporal operator {op}")

    # Read and validate the CGS once. The available actions are extracted with
    # the TOTAL number of agents, not the coalition cardinality.
    from model_checker.algorithms.explicit.NatATL.Recall.recall_context import (
        RecallContext,
    )
    context = RecallContext(cgs) if context is None else context
    view = context.snapshot
    names, props, n_agents, enabled = view.states, view.propositions, view.number_of_agents, view.enabled
    if any(agent < 1 or agent > n_agents for agent in coalition):
        raise ValueError(f"Coalition agent out of range 1..{n_agents}")
    universe = set(names)
    left = set(left_states)
    right = set(right_states) if right_states is not None else None
    if not left <= universe or (right is not None and not right <= universe):
        raise ValueError("A temporal operand names an unknown CGS state")
    start = str(cgs.initial_state if initial_state is None else initial_state)
    if start not in universe:
        raise ValueError(f"Unknown initial state {start!r}")

    action_inventory = {
        agent: sorted(set().union(*(enabled[state][agent] for state in names)))
        for agent in coalition
    }
    context.require_idle(coalition)

    checked = 0
    appropriate = 0
    # Costs grow from |A| through bound in either generator.
    for profile in enumerate_profiles(
        coalition, action_inventory, props, bound
    ):
        checked += 1
        try:
            product = build_validated_recall_product(
                cgs, coalition, profile, initial_state=start, context=context
            )
        except InappropriateRecallRule:
            # Inadmissible candidates are expected during enumeration.
            continue

        appropriate += 1
        left_product = {
            node for node in product.successors if node.state in left
        }
        right_product = (
            {node for node in product.successors if node.state in right}
            if right is not None else None
        )
        if check_initial(product, op, left_product, right_product):
            cost = profile_cost(profile)
            result = {
                "Satisfiability": True,
                "Status": "WITNESS_FOUND",
                "Complexity Bound": bound,
                "Witness Complexity": cost,
                "Winning Strategy per agent": profile,
                "Coalition": coalition,
                "Candidates Examined": checked,
                "Admissible Candidates": appropriate,
                "res": "Result: True",
                "initial_state": f"Initial state {start}: True",
                "Search Scope": scope,
                "Full Language Complete": False,
            }
            if certify_restricted_exhaustion:
                result["Restricted Fragment Complete"] = True
            return result

    if certify_restricted_exhaustion:
        return {
            "Satisfiability": False,
            "Status": "NO_WITNESS_IN_COMPLETE_SUPPORTED_GRAMMAR",
            "Complexity Bound": bound,
            "Coalition": coalition,
            "Candidates Examined": checked,
            "Admissible Candidates": appropriate,
            "res": "Result: False",
            "initial_state": f"Initial state {start}: False",
            "Search Scope": scope,
            "Restricted Fragment Complete": True,
            "Supported Grammar Complete": True,
            "Negative Certificate": "EXHAUSTIVE_BOUNDED_RECALL_ENUMERATION",
            "Full Language Complete": False,
        }

    return {
        # No proof of a negative answer for the ENTIRE NatATL recall grammar.
        "Satisfiability": None,
        "Status": ("NO_WITNESS_IN_CANONICAL_FRAGMENT"
                   if generator == "canonical"
                   else "NO_WITNESS_IN_EXTENDED_FRAGMENT"),
        "Complexity Bound": bound,
        "Coalition": coalition,
        "Candidates Examined": checked,
        "Admissible Candidates": appropriate,
        "res": f"Result: Inconclusive ({generator} recall fragment exhausted)",
        "initial_state": f"Initial state {start}: Inconclusive",
        "Search Scope": scope,
        "Full Language Complete": False,
    }
