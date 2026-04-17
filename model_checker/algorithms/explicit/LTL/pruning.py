"""
Pruning module for LTL model checker.

Implements matrix-based pruning for LTL with game-theoretic solution concepts.
Reuses modify_matrix from NatATL.Memoryless (same CGS transition format).
"""

from model_checker.algorithms.explicit.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.Memoryless.matrix_utils import (
    modify_matrix,
)
from model_checker.engine.runner import parse_state_set_literal
from model_checker.parsers.game_structures.cgs import CGS, cgs_validation


def process_transition_matrix_data(cgs, model, agents, *strategies):
    graph = cgs.transition_matrix
    label_matrix = cgs.create_label_matrix(graph)
    actions_per_agent = cgs.get_actions(agents)
    agent_actions = {}
    for _i, agent_key in enumerate(actions_per_agent.keys()):
        agent_actions[f"actions_{agent_key}"] = actions_per_agent[agent_key]

    for strategy_index, strategy in enumerate(strategies, start=1):
        state_sets = set()
        temp = set()
        for iteration, (condition, action) in enumerate(
            strategy["condition_action_pairs"]
        ):
            # Cache model_checking results for conditions to avoid redundant CTL calls
            if not hasattr(cgs, "_condition_cache"):
                cgs._condition_cache = {}
            cache_key = (condition, model)
            if cache_key not in cgs._condition_cache:
                states = model_checking(condition, model, preloaded_model=cgs)
                cgs._condition_cache[cache_key] = states
            else:
                states = cgs._condition_cache[cache_key]
            state_set = parse_state_set_literal(states["res"].split(": ")[1])

            if iteration > 0:
                if state_set:
                    temp = state_sets
                    state_sets = state_set - temp
                else:
                    state_sets = set(cgs.get_states())
                    action = "I"
                graph = modify_matrix(
                    graph, label_matrix, state_sets, action, strategy_index, agents
                )
            else:
                if state_set:
                    state_sets = state_set
                else:
                    state_sets = set(cgs.get_states())
                    action = "I"
                graph = modify_matrix(
                    graph, label_matrix, state_sets, action, strategy_index, agents
                )

    return graph


def pruning(cgs, model, agents, formula, current_agents):
    if not hasattr(cgs, "_model_cache"):
        cgs._model_cache = {}
    if model not in cgs._model_cache:
        cgs_template = CGS()
        cgs_template.read_file(model)
        cgs._model_cache[model] = cgs_template

    # Create a new CGS instance and copy from cached model
    cgs1 = CGS()
    cached_cgs = cgs._model_cache[model]

    cgs1.graph = [row[:] for row in cached_cgs.graph]
    cgs1.states = (
        cached_cgs.states.copy()
        if hasattr(cached_cgs.states, "copy")
        else cached_cgs.states
    )
    cgs1.number_of_agents = cached_cgs.number_of_agents
    cgs1.atomic_propositions = (
        cached_cgs.atomic_propositions.copy()
        if hasattr(cached_cgs.atomic_propositions, "copy")
        else cached_cgs.atomic_propositions
    )
    cgs1.initial_state = cached_cgs.initial_state
    cgs1.matrix_prop = (
        [row[:] for row in cached_cgs.matrix_prop] if cached_cgs.matrix_prop else []
    )
    cgs1.actions = cached_cgs.actions[:] if cached_cgs.actions else []

    cgs1.graph = process_transition_matrix_data(cgs1, model, agents, *current_agents)
    try:
        cgs_validation.validate_nat_idle_requirements(
            cgs1.graph, cgs1.get_number_of_agents()
        )
    except ValueError as e:
        error_msg = str(e)
        if "Idle error" in error_msg or "All elements in row" in error_msg:
            pass
        else:
            raise
    result = model_checking(formula, model, preloaded_model=cgs1)
    if result.get("initial_state", "").endswith(": True"):
        return True
    return False
