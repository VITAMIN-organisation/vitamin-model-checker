"""Pre-image computation for ATLF (real-valued semantics in [0,1])."""

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from model_checker.parsers.game_structures.cgs import cgs_actions

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def build_transition_cache(
    cgs: "CGS", coalition: str
) -> Dict[int, Dict[frozenset, List[int]]]:
    """Build a per-state cache mapping coalition moves to destination indices."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    formatted_agents = cgs_actions.format_agents(agents)
    num_agents = cgs.get_number_of_agents()
    graph = cgs.graph
    cache = {}

    for state_idx in range(len(graph)):
        moves_by_coalition = {}
        for dest_idx, action in enumerate(graph[state_idx]):
            if action != 0:
                action_list = cgs.build_action_list(action)
                for move in action_list:
                    coalition_move = frozenset(
                        cgs_actions.get_coalition_actions(
                            {move}, formatted_agents, num_agents
                        )
                    )
                    if coalition_move not in moves_by_coalition:
                        moves_by_coalition[coalition_move] = []
                    moves_by_coalition[coalition_move].append(dest_idx)
        cache[state_idx] = moves_by_coalition

    return cache


def evaluate_max_strategy(
    cgs: "CGS",
    agents: List[str],
    state_idx: int,
    atom_dict: Dict[str, float],
    transition_cache: Dict = None,
) -> float:
    """Return the max-min coalition strategy value at the given state."""
    if transition_cache and state_idx in transition_cache:
        moves_by_coalition = transition_cache[state_idx]
    else:
        graph = cgs.graph
        formatted_agents = cgs_actions.format_agents(agents)
        num_agents = cgs.get_number_of_agents()
        moves_by_coalition = {}
        for dest_idx, action in enumerate(graph[state_idx]):
            if action != 0:
                action_list = cgs.build_action_list(action)
                for move in action_list:
                    coalition_move = frozenset(
                        cgs_actions.get_coalition_actions(
                            {move}, formatted_agents, num_agents
                        )
                    )
                    if coalition_move not in moves_by_coalition:
                        moves_by_coalition[coalition_move] = []
                    moves_by_coalition[coalition_move].append(dest_idx)

    if not moves_by_coalition:
        return 0.0

    max_value = 0.0
    for _coalition_move, destinations in moves_by_coalition.items():
        min_value = float("inf")
        for dest_idx in destinations:
            dest_state = cgs.get_state_name_by_index(dest_idx)
            val = atom_dict.get(dest_state, 0.0)
            if val < min_value:
                min_value = val
        if min_value > max_value:
            max_value = min_value

    return max_value if max_value != float("inf") else 0.0


def pre(
    cgs: "CGS",
    coalition: str,
    atom_values: Union[List[Tuple[str, float]], str],
    transition_cache: Optional[Dict] = None,
) -> List[Tuple[str, float]]:
    """Compute the ATLF pre-image as a list of (state, value) pairs."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    states = cgs.states

    if isinstance(atom_values, str):
        import ast

        atom_values = ast.literal_eval(atom_values)

    atom_dict = dict(atom_values)
    if transition_cache is None:
        transition_cache = build_transition_cache(cgs, coalition)

    result = []
    for state_idx, state in enumerate(states):
        max_value = evaluate_max_strategy(
            cgs, agents, state_idx, atom_dict, transition_cache
        )
        result.append((state, max_value))

    return result
