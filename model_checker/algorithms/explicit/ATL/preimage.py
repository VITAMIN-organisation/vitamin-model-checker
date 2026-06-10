"""Coalition pre-image computation for ATL (e.g. for <A>X)."""

from typing import Dict, List, Optional, Set, Tuple

from model_checker.algorithms.explicit.shared.bit_vector import (
    BIT_VECTOR_THRESHOLD,
    BitVectorStateSet,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_names_to_indices,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol, cgs_actions


def build_transition_cache(
    cgs: CGSProtocol, coalition: Optional[str] = None
) -> Dict[int, List[Tuple]]:
    """Cache outgoing transitions per state for faster pre-image computation."""
    cache = {}
    graph = cgs.graph
    agents = cgs_actions.get_agents_from_coalition(coalition) if coalition else None
    formatted_agents = cgs_actions.format_agents(agents) if agents else None
    num_agents = cgs.get_number_of_agents()

    for q in range(len(graph)):
        moves = []
        for j, mask in enumerate(graph[q]):
            if mask != 0:
                for prof in cgs.build_action_list(mask):
                    if formatted_agents is not None:
                        mA = tuple(
                            sorted(
                                cgs_actions.get_coalition_actions(
                                    {prof}, formatted_agents, num_agents
                                )
                            )
                        )
                        mo = tuple(
                            sorted(
                                cgs_actions._process_actions_for_agents(
                                    {prof},
                                    formatted_agents,
                                    num_agents,
                                    include_agents=False,
                                )
                            )
                        )
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
    """Group outgoing transitions at one state by coalition move."""
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

    formatted_agents = cgs_actions.format_agents(coalition_agents)
    num_agents = cgs.get_number_of_agents()
    for prof, next_index in joint_moves:
        coalition_move = tuple(
            sorted(
                cgs_actions.get_coalition_actions({prof}, formatted_agents, num_agents)
            )
        )
        opponent_move = tuple(
            sorted(
                cgs_actions._process_actions_for_agents(
                    {prof}, formatted_agents, num_agents, include_agents=False
                )
            )
        )
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
    """States where coalition can reach state_set in one step."""
    T_idx = state_names_to_indices(cgs, state_set)
    A = cgs_actions.get_agents_from_coalition(coalition)

    graph = cgs.graph
    num_states = len(graph)
    result = set()
    use_bit_vector = num_states >= BIT_VECTOR_THRESHOLD
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
