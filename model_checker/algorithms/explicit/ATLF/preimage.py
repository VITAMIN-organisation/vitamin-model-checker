"""Pre-image computation for ATLF (real-valued semantics in [0,1])."""

from typing import TYPE_CHECKING

from model_checker.parsers.game_structures.cgs import cgs_actions

if TYPE_CHECKING:
    from model_checker.parsers.game_structures.cgs.cgs import CGS

TransitionCache = dict[int, dict[frozenset, list[int]]]


def _moves_by_coalition_for_state(
    cgs: "CGS",
    state_idx: int,
    formatted_agents: set[int],
    num_agents: int,
) -> dict[frozenset, list[int]]:
    """Group outgoing transitions at one state by coalition move."""
    moves_by_coalition: dict[frozenset, list[int]] = {}

    for dest_idx, action in enumerate(cgs.graph[state_idx]):
        if action == 0:
            continue
        for move in cgs.build_action_list(action):
            coalition_move = frozenset(
                cgs_actions.get_coalition_actions({move}, formatted_agents, num_agents)
            )
            moves_by_coalition.setdefault(coalition_move, []).append(dest_idx)

    return moves_by_coalition


def build_transition_cache(cgs: "CGS", coalition: str) -> TransitionCache:
    """Build a per-state cache mapping coalition moves to destination indices."""
    agents = cgs_actions.get_agents_from_coalition(coalition)
    formatted_agents = cgs_actions.format_agents(agents)
    num_agents = cgs.get_number_of_agents()

    return {
        state_idx: _moves_by_coalition_for_state(
            cgs, state_idx, formatted_agents, num_agents
        )
        for state_idx in range(len(cgs.graph))
    }


def evaluate_max_strategy(
    cgs: "CGS",
    state_idx: int,
    atom_dict: dict[str, float],
    transition_cache: TransitionCache,
) -> float:
    """Return the max-min coalition strategy value at the given state."""
    moves_by_coalition = transition_cache[state_idx]

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
    atom_values: list[tuple[str, float]] | str,
    transition_cache: TransitionCache,
) -> list[tuple[str, float]]:
    """Compute the ATLF pre-image as a list of (state, value) pairs."""
    if isinstance(atom_values, str):
        import ast

        atom_values = ast.literal_eval(atom_values)

    atom_dict = dict(atom_values)
    result = []
    for state_idx, state in enumerate(cgs.states):
        max_value = evaluate_max_strategy(cgs, state_idx, atom_dict, transition_cache)
        result.append((state, max_value))

    return result
