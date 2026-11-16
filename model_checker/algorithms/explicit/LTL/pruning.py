"""Matrix-based pruning for the LTL solution concepts, reusing the rule application
of NatATL Memoryless."""

from model_checker.algorithms.explicit.NatATL.Memoryless.pruning import (
    apply_first_matching_rules,
)
from model_checker.algorithms.explicit.shared.natural_strategies import goal_holds_on
from model_checker.parsers.game_structures.cgs import CGS


def process_transition_matrix_data(cgs, model, agents, *strategies):
    graph = [row[:] for row in cgs.graph]

    for strategy_index, strategy in enumerate(strategies, start=1):
        graph, _ = apply_first_matching_rules(
            cgs, model, agents, strategy_index, strategy, graph
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
    return goal_holds_on(cgs1, formula, model)
