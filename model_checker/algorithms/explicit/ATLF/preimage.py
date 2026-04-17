"""Pre-image computation for ATLF (real-valued semantics in [0,1])."""

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS


def _build_atom_dict(atom_values: List[Tuple[str, float]]) -> Dict[str, float]:
    """Build state -> value dict from list of (state, value) pairs."""
    return dict(atom_values)


def build_transition_cache(
    cgs: "CGS", coalition: str
) -> Dict[int, Dict[frozenset, List[int]]]:
    """Build per-state cache: coalition_move -> list of destination indices.

    Args:
        cgs: CGS model.
        coalition: Coalition string.

    Returns:
        Dict from state index to {coalition_move: [dest_indices]}.
    """
    agents = cgs.get_agents_from_coalition(coalition)
    graph = cgs.graph
    cache = {}

    for state_idx in range(len(graph)):
        moves_by_coalition = {}
        for dest_idx, action in enumerate(graph[state_idx]):
            if action != 0:
                action_list = cgs.build_action_list(action)
                for move in action_list:
                    coalition_move = frozenset(cgs.get_coalition_action({move}, agents))
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
    """Max over coalition moves of min over successors of atom value at state_idx.

    Args:
        cgs: CGS model.
        agents: Coalition agents.
        state_idx: State to evaluate.
        atom_dict: State name -> real value.
        transition_cache: Optional cache from build_transition_cache.
    """
    if transition_cache and state_idx in transition_cache:
        moves_by_coalition = transition_cache[state_idx]
    else:
        graph = cgs.graph
        moves_by_coalition = {}
        for dest_idx, action in enumerate(graph[state_idx]):
            if action != 0:
                action_list = cgs.build_action_list(action)
                for move in action_list:
                    coalition_move = frozenset(cgs.get_coalition_action({move}, agents))
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
    """Pre-image for ATLF: each state gets max-min value over coalition/successors.

    Args:
        cgs: CGS model.
        coalition: Coalition string.
        atom_values: List of (state, value) or string repr; defines successor values.
        transition_cache: Optional cache from build_transition_cache(cgs, coalition).

    Returns:
        List of (state, value) for the pre-image.
    """
    agents = cgs.get_agents_from_coalition(coalition)
    states = cgs.get_states()

    if isinstance(atom_values, str):
        import ast

        atom_values = ast.literal_eval(atom_values)

    atom_dict = _build_atom_dict(atom_values)
    if transition_cache is None:
        transition_cache = build_transition_cache(cgs, coalition)

    result = []
    for state_idx, state in enumerate(states):
        max_value = evaluate_max_strategy(
            cgs, agents, state_idx, atom_dict, transition_cache
        )
        result.append((state, max_value))

    return result
