"""Coalition pre-image computation for IATL over BCGS models.

Semantics follow Bozzelli et al. (KR 2025), Proposition 2:
- Pre_exists (Pre_d): some A-decision at s such that every successor
  consistent with that decision is in the target set.
- Pre_forall (Pre_f): every A-decision at s has some successor in the
  target set consistent with that decision.
"""

from collections.abc import Callable

from model_checker.parsers.game_structures.cgs import cgs_actions

MovesByCoalition = dict[tuple, list[tuple[tuple, int]]]
TransitionCache = dict[int, MovesByCoalition]


def group_moves_by_coalition(
    graph_row,
    num_agents: int,
    formatted_agents: set[int],
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
    transitions: list[tuple[tuple, int]],
    target_indices: set[int],
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


def _coalition_pre_image(
    graph_matrix,
    state_list,
    coalition: str,
    target_states: set[str],
    num_agents: int,
    transition_cache: TransitionCache | None,
    qualifies: Callable[[MovesByCoalition, set[int]], bool],
) -> set[str]:
    """Return states that reach target_states in one coalition step."""
    result: set[str] = set()
    targets = {str(state) for state in target_states}
    target_idx = {idx for idx, state in enumerate(state_list) if str(state) in targets}
    if not target_idx:
        return result

    formatted_agents = cgs_actions.format_agents(
        cgs_actions.get_agents_from_coalition(coalition)
    )

    for state_idx, row in enumerate(graph_matrix):
        if transition_cache is not None:
            moves_by_coalition = transition_cache[state_idx]
        else:
            moves_by_coalition = group_moves_by_coalition(
                row, num_agents, formatted_agents
            )
        if qualifies(moves_by_coalition, target_idx):
            result.add(str(state_list[state_idx]))

    return result


def _state_in_exists_pre_image(
    moves_by_coalition: MovesByCoalition,
    target_idx: set[int],
) -> bool:
    """Every opponent response from that move lands in the target for each coalition move"""
    for transitions in moves_by_coalition.values():
        if _all_opponent_moves_lead_to_target(transitions, target_idx):
            return True
    return False


def pre_image_exists(
    graph_matrix,
    state_list,
    coalition: str,
    target_states: set[str],
    num_agents: int,
    transition_cache: TransitionCache = None,
) -> set[str]:
    """
    exists: Some coalition choice + All opponent responses -> target
    Pre_d(A, X): existential coalition pre-image (<A>X)."""
    return _coalition_pre_image(
        graph_matrix,
        state_list,
        coalition,
        target_states,
        num_agents,
        transition_cache,
        _state_in_exists_pre_image,
    )


def _state_in_forall_pre_image(
    moves_by_coalition: MovesByCoalition,
    target_idx: set[int],
) -> bool:
    """Some successor from that move is in target for each coalition move"""
    if not moves_by_coalition:
        return False

    return all(
        any(dest in target_idx for _, dest in transitions)
        for transitions in moves_by_coalition.values()
    )


def pre_image_forall(
    graph_matrix,
    state_list,
    coalition: str,
    target_states: set[str],
    num_agents: int,
    transition_cache: TransitionCache = None,
) -> set[str]:
    """
    forall: All coalition choices + Some opponent successor -> target
    Pre_f(A, X): universal coalition pre-image ([A]X)."""
    return _coalition_pre_image(
        graph_matrix,
        state_list,
        coalition,
        target_states,
        num_agents,
        transition_cache,
        _state_in_forall_pre_image,
    )
