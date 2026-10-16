"""Exact first-match pruning for the legacy CTL-backed LTL pipeline.

Legacy generated lists may omit an explicit fallback: uncovered states then
select the EXISTING IDLE action. This adapter never inserts transitions, never
retains IDLE alongside another selected action, and never calls CTL on a graph
made nonserial by an inadmissible candidate. It does not certify completeness
of the legacy strategy generator or general LTL-to-CTL equivalence.
"""
import copy

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.algorithms.explicit.NatATL.strategy_errors import (
    InadmissibleStrategy,
)
from model_checker.parsers.game_structures.cgs import cgs_actions
from model_checker.utils.literals import parse_state_set_literal


def process_transition_matrix_data(cgs, model, agents, *strategies):
    graph = [row[:] for row in cgs.graph]
    n_agents = cgs.get_number_of_agents()
    cgs_actions.validate_agent_numbers(agents, n_agents)
    if len(agents) != len(strategies) or len(set(agents)) != len(agents):
        raise ValueError("One strategy per distinct coalition agent is required")
    all_states = {str(s) for s in cgs.states}
    indices = {str(s): i for i, s in enumerate(cgs.states)}
    if len(graph) != len(all_states) or any(len(row) != len(all_states) for row in graph):
        raise ValueError("[MODEL] Invalid CGS dimensions")
    if any(not any(c not in (0, "0", "", None) for c in row) for row in graph):
        raise ValueError("[MODEL] Original CGS is non-total")
    guard_cache = {}
    for position, strategy in enumerate(strategies, 1):
        pairs = strategy.get("condition_action_pairs")
        if not isinstance(pairs, (list, tuple)) or not pairs:
            raise ValueError("Empty legacy strategy")
        covered = set()
        # Preserve only the documented implicit-IDLE fallback of legacy lists.
        for condition, action in [*pairs, ("T", "IDLE")]:
            if condition.strip() in ("T", "true"):
                matched = all_states
            else:
                if condition not in guard_cache:
                    result = model_checking(condition, model, preloaded_model=cgs)
                    if result.get("error") or not result.get("res", "").startswith("Result: "):
                        raise ValueError(f"Invalid strategy condition {condition!r}: {result}")
                    guard_cache[condition] = parse_state_set_literal(result["res"][8:])
                matched = guard_cache[condition]
            applicable = set(matched) - covered
            if not applicable:
                continue  # A false or shadowed guard does nothing, not IDLE everywhere.
            graph = modify_matrix(
                graph, applicable, action, position, agents, num_agents=n_agents,
                state_to_index=indices, in_place=True, allow_wildcards=True,
            )
            for state in applicable:
                if not any(c not in (0, "0", "", None) for c in graph[indices[state]]):
                    raise InadmissibleStrategy(
                        f"Action {action!r} is not enabled for agent {agents[position-1]} "
                        f"in state {state!r}"
                    )
            covered.update(applicable)
    return graph


def pruning(cgs, model, agents, formula, current_agents):
    """Reject inadmissible candidates; propagate parse/model/backend errors."""
    try:
        graph = process_transition_matrix_data(cgs, model, agents, *current_agents)
    except InadmissibleStrategy:
        return False
    pruned = copy.deepcopy(cgs)
    pruned.graph = graph
    result = model_checking(formula, model, preloaded_model=pruned)
    if result.get("error") or not result.get("res", "").startswith("Result: "):
        raise ValueError(f"CTL verification failed: {result}")
    states = parse_state_set_literal(result["res"][8:])
    return str(pruned.initial_state) in states
