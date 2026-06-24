"""OL cost-bounded semantics via shortest-path computations.

Operator meaning under demonic linear cost bounds:
  F: min accumulated cost to reach phi is within the bound.
  G: phi holds and min cost to leave phi exceeds the bound.
  X: every transition within the step bound stays in phi.
  U: min cost to reach psi with the prefix in phi is within the bound.
  R: dual of (not phi) U (not psi); W: psi R (phi or psi).
"""

from model_checker.algorithms.explicit.shared.cost_utils import transition_cell_cost
from model_checker.algorithms.explicit.shared.state_utils import state_names_to_indices


def _min_cost_to_targets(cgs, target_indices: set[int]) -> list[float]:
    """Minimum accumulated cost from each state to any target index."""
    n = len(cgs.graph)
    min_cost = [float("inf")] * n
    for idx in target_indices:
        min_cost[idx] = 0.0

    for _ in range(n):
        updated = False
        for i in range(n):
            for j in range(n):
                cell = cgs.graph[i][j]
                if cell in (0, "0"):
                    continue
                candidate = transition_cell_cost(cgs, i, cell) + min_cost[j]
                if candidate < min_cost[i]:
                    min_cost[i] = candidate
                    updated = True
        if not updated:
            break
    return min_cost


def states_within_cost(cgs, target_states: set[str], max_cost: int) -> set[str]:
    """States that can reach target_states with accumulated cost <= max_cost."""
    if not target_states:
        return set()
    target_indices = state_names_to_indices(cgs, target_states)
    if not target_indices:
        return set()
    min_cost = _min_cost_to_targets(cgs, target_indices)
    return {
        cgs.get_state_name_by_index(i)
        for i, cost in enumerate(min_cost)
        if cost <= max_cost
    }


def states_with_next_in(cgs, target_states: set[str], max_step_cost: int) -> set[str]:
    """States where every step within max_step_cost stays in target_states."""
    target_indices = state_names_to_indices(cgs, target_states)
    if not target_indices:
        return set()

    result: set[str] = set()
    for i in range(len(cgs.graph)):
        has_affordable_step = False
        for j in range(len(cgs.graph)):
            cell = cgs.graph[i][j]
            if cell in (0, "0"):
                continue
            if transition_cell_cost(cgs, i, cell) > max_step_cost:
                continue
            has_affordable_step = True
            if j not in target_indices:
                break
        else:
            if has_affordable_step:
                result.add(cgs.get_state_name_by_index(i))
    return result


def states_globally_in(cgs, phi_states: set[str], max_cost: int) -> set[str]:
    """States in phi where the adversary cannot reach outside phi within max_cost."""
    phi = {str(s) for s in phi_states}
    all_states = {str(s) for s in cgs.all_states_set}
    violation_targets = all_states - phi
    if not violation_targets:
        return phi
    reach_violation = states_within_cost(cgs, violation_targets, max_cost)
    return phi - reach_violation


def _min_cost_until(cgs, phi_states: set[str], psi_states: set[str]) -> list[float]:
    """Minimum cost to reach psi while visiting only phi on the prefix."""
    n = len(cgs.graph)
    phi_indices = state_names_to_indices(cgs, phi_states)
    psi_indices = state_names_to_indices(cgs, psi_states)
    allowed = phi_indices | psi_indices

    min_cost = [float("inf")] * n
    for idx in psi_indices:
        min_cost[idx] = 0.0

    for _ in range(n):
        updated = False
        for i in range(n):
            if i in psi_indices or i not in phi_indices:
                continue
            for j in range(n):
                cell = cgs.graph[i][j]
                if cell in (0, "0") or j not in allowed:
                    continue
                candidate = transition_cell_cost(cgs, i, cell) + min_cost[j]
                if candidate < min_cost[i]:
                    min_cost[i] = candidate
                    updated = True
        if not updated:
            break
    return min_cost


def states_until(
    cgs, phi_states: set[str], psi_states: set[str], max_cost: int
) -> set[str]:
    """States from which psi is reachable within max_cost while phi holds on the prefix."""
    min_cost = _min_cost_until(cgs, phi_states, psi_states)
    return {
        cgs.get_state_name_by_index(i)
        for i, cost in enumerate(min_cost)
        if cost <= max_cost
    }


def states_release(
    cgs, phi_states: set[str], psi_states: set[str], max_cost: int
) -> set[str]:
    """phi R psi as the dual of (not phi) U (not psi) under the same cost bound."""
    all_states = {str(s) for s in cgs.all_states_set}
    phi = {str(s) for s in phi_states}
    psi = {str(s) for s in psi_states}
    witness = states_until(cgs, all_states - phi, all_states - psi, max_cost)
    return all_states - witness


def states_weak(
    cgs, phi_states: set[str], psi_states: set[str], max_cost: int
) -> set[str]:
    """phi W psi equals psi R (phi or psi) under the same cost bound."""
    psi = {str(s) for s in psi_states}
    phi_or_psi = {str(s) for s in phi_states} | psi
    return states_release(cgs, phi_or_psi, psi, max_cost)
