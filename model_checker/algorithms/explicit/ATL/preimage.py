"""Coalition pre-image computation for ATL (e.g. for <A>X)."""

from typing import Dict, List, Optional, Set, Tuple

from model_checker.algorithms.explicit.shared.bit_vector import (
    BitVectorStateSet,
    should_use_bit_vectors,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol


def build_transition_cache(
    cgs: CGSProtocol, coalition: Optional[str] = None
) -> Dict[int, List[Tuple]]:
    """Build per-state transition cache for pre-image.

    Args:
        cgs: CGS model.
        coalition: Optional coalition string; if set, cache stores (coalition_action, opponent_action, next_state), else (profile, next_state).

    Returns:
        Dict from state index to list of transition tuples.
    """
    cache = {}
    graph = cgs.graph
    agents = cgs.get_agents_from_coalition(coalition) if coalition else None

    for q in range(len(graph)):
        moves = []
        for j, mask in enumerate(graph[q]):
            if mask != 0:
                for prof in cgs.build_action_list(mask):
                    if agents:
                        mA = tuple(sorted(cgs.get_coalition_action({prof}, agents)))
                        mo = tuple(sorted(cgs.get_opponent_moves({prof}, agents)))
                        moves.append((mA, mo, j))
                    else:
                        moves.append((prof, j))
        cache[q] = moves
    return cache


def _group_moves_by_coalition_for_state(
    cgs: CGSProtocol,
    state_index: int,
    coalition_agents: Set[str],
    graph: List[List[int]],
    transition_cache: Optional[Dict[int, List[Tuple]]],
    has_coalition_cache: bool,
) -> Dict[Tuple, List[Tuple]]:
    """Group outgoing transitions by coalition move for one state.

    Returns:
        Map from coalition move to list of (opponent_move, next_state_index).
    """
    moves_by_coalition: Dict[Tuple, List[Tuple]] = {}

    if has_coalition_cache and transition_cache is not None:
        for mA, mo, j in transition_cache[state_index]:
            moves_by_coalition.setdefault(mA, []).append((mo, j))
        return moves_by_coalition

    if transition_cache is not None:
        joint_moves = transition_cache[state_index]
    else:
        joint_moves: List[Tuple] = []
        for next_index, mask in enumerate(graph[state_index]):
            if mask != 0:
                for prof in cgs.build_action_list(mask):
                    joint_moves.append((prof, next_index))

    for prof, next_index in joint_moves:
        coalition_move = tuple(
            sorted(cgs.get_coalition_action({prof}, coalition_agents))
        )
        opponent_move = tuple(sorted(cgs.get_opponent_moves({prof}, coalition_agents)))
        moves_by_coalition.setdefault(coalition_move, []).append(
            (opponent_move, next_index)
        )

    return moves_by_coalition


def _all_opponent_moves_lead_to_target(
    transitions: List[Tuple[Tuple, int]],
    use_bit_vector: bool,
    target_bits: Optional[BitVectorStateSet],
    target_indices: Set[int],
) -> bool:
    """Return True if every opponent response from this coalition move lands in the target set."""
    opponent_moves = {mo for mo, _ in transitions}

    for opp in opponent_moves:
        destinations = [j for mo, j in transitions if mo == opp]
        if not destinations:
            return False
        if use_bit_vector:
            if target_bits is None:
                return False
            if any(j not in target_bits for j in destinations):
                return False
        else:
            if any(j not in target_indices for j in destinations):
                return False

    return True


def pre(
    cgs: CGSProtocol,
    coalition: str,
    state_set: Set[str],
    transition_cache: Optional[Dict] = None,
    early_stop: Optional[Set[int]] = None,
) -> Set[str]:
    """Pre-image Pre_A(T): states from which coalition can force one step into state_set.

    Args:
        cgs: CGS model.
        coalition: Coalition string (e.g. ``'1,2'``).
        state_set: Target state names.
        transition_cache: Optional pre-built cache from ``build_transition_cache``.
        early_stop: Optional state indices to include without recomputing.

    Returns:
        Set of state names in the pre-image.
    """
    T_idx = state_names_to_indices(cgs, state_set)
    A = cgs.get_agents_from_coalition(coalition)

    graph = cgs.graph
    num_states = len(graph)
    result = set()
    use_bit_vector = should_use_bit_vectors(num_states)
    if use_bit_vector:
        T_bits = BitVectorStateSet(num_states, T_idx)

    has_coalition_cache = (
        transition_cache
        and transition_cache.get(0)
        and transition_cache.get(0, [])
        and len(transition_cache[0][0]) == 3
    )

    for q in range(num_states):
        if early_stop is not None and q in early_stop:
            result.add(cgs.get_state_name_by_index(q))
            continue
        moves_by_coalition = _group_moves_by_coalition_for_state(
            cgs=cgs,
            state_index=q,
            coalition_agents=A,
            graph=graph,
            transition_cache=transition_cache,
            has_coalition_cache=has_coalition_cache,
        )

        for _, transitions in moves_by_coalition.items():
            if _all_opponent_moves_lead_to_target(
                transitions=transitions,
                use_bit_vector=use_bit_vector,
                target_bits=T_bits if use_bit_vector else None,
                target_indices=T_idx,
            ):
                result.add(cgs.get_state_name_by_index(q))
                break

    return result
