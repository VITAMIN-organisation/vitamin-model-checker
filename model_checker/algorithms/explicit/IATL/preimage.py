"""Coalition pre-image computation for IATL over BCGS models.

Semantics follow Bozzelli et al. (KR 2025), Proposition 2:
- Pre_exists (Pre_d): some A-decision at s such that every successor
  consistent with that decision is in the target set.
- Pre_forall (Pre_f): every A-decision at s has some successor in the
  target set consistent with that decision.
"""

from typing import Dict, List, Set, Tuple

from model_checker.parsers.game_structures.cgs import cgs_actions

MovesByCoalition = Dict[Tuple, List[Tuple[Tuple, int]]]
TransitionCache = Dict[int, MovesByCoalition]


def group_moves_by_coalition(
    graph_row,
    num_agents: int,
    formatted_agents: Set[int],
) -> MovesByCoalition:
    """Group outgoing transitions from one state by coalition move."""
    moves_by_coalition: MovesByCoalition = {}
    for dest_idx, cell in enumerate(graph_row):
        if cell == "0":
            continue
        for joint in cgs_actions.parse_joint_action_cell(str(cell), num_agents):
            coalition_move = tuple(sorted(joint[agent] for agent in formatted_agents))
            opponent_move = tuple(
                sorted(
                    joint[agent]
                    for agent in range(num_agents)
                    if agent not in formatted_agents
                )
            )
            moves_by_coalition.setdefault(coalition_move, []).append(
                (opponent_move, dest_idx)
            )
    return moves_by_coalition


def _all_opponent_moves_lead_to_target(
    transitions: List[Tuple[Tuple, int]],
    target_indices: Set[int],
) -> bool:
    """Return True if every opponent response lands in the target set."""
    opponent_moves = {move for move, _ in transitions}
    for opponent_move in opponent_moves:
        destinations = [dest for move, dest in transitions if move == opponent_move]
        if not destinations or any(dest not in target_indices for dest in destinations):
            return False
    return True


def build_transition_cache(
    graph_matrix,
    num_agents: int,
    coalition: str,
) -> TransitionCache:
    """Cache coalition-grouped outgoing moves per state for repeated pre-images."""
    formatted_agents = cgs_actions.format_agents(
        cgs_actions.get_agents_from_coalition(coalition)
    )
    return {
        state_idx: group_moves_by_coalition(row, num_agents, formatted_agents)
        for state_idx, row in enumerate(graph_matrix)
    }


def pre_image_exists(
    graph_matrix,
    state_list,
    coalition: str,
    target_states: Set[str],
    num_agents: int,
    transition_cache: TransitionCache = None,
) -> Set[str]:
    """Pre_d(A, X): existential coalition pre-image (<A>X)."""
    targets = {str(state) for state in target_states}
    target_idx = {idx for idx, state in enumerate(state_list) if str(state) in targets}
    if not target_idx:
        return set()

    formatted_agents = cgs_actions.format_agents(
        cgs_actions.get_agents_from_coalition(coalition)
    )
    result: Set[str] = set()

    for state_idx, row in enumerate(graph_matrix):
        if transition_cache is not None:
            moves_by_coalition = transition_cache[state_idx]
        else:
            moves_by_coalition = group_moves_by_coalition(
                row, num_agents, formatted_agents
            )
        for transitions in moves_by_coalition.values():
            if _all_opponent_moves_lead_to_target(transitions, target_idx):
                result.add(str(state_list[state_idx]))
                break

    return result


def pre_image_forall(
    graph_matrix,
    state_list,
    coalition: str,
    target_states: Set[str],
    num_agents: int,
    transition_cache: TransitionCache = None,
) -> Set[str]:
    """Pre_f(A, X): universal coalition pre-image ([A]X)."""
    targets = {str(state) for state in target_states}
    target_idx = {idx for idx, state in enumerate(state_list) if str(state) in targets}
    if not target_idx:
        return set()

    formatted_agents = cgs_actions.format_agents(
        cgs_actions.get_agents_from_coalition(coalition)
    )
    result: Set[str] = set()

    for state_idx, row in enumerate(graph_matrix):
        if transition_cache is not None:
            moves_by_coalition = transition_cache[state_idx]
        else:
            moves_by_coalition = group_moves_by_coalition(
                row, num_agents, formatted_agents
            )
        if not moves_by_coalition:
            continue
        if all(
            any(dest in target_idx for _, dest in transitions)
            for transitions in moves_by_coalition.values()
        ):
            result.add(str(state_list[state_idx]))

    return result
