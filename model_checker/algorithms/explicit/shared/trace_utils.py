"""
Trace reconstruction utilities for witness and counterexample generation.

This module provides functions to reconstruct traces (paths) through the state
space based on predecessor information collected during model checking.
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from model_checker.parsers.game_structures.cgs import CGSProtocol


def reconstruct_trace_from_predecessors(
    initial_state: str,
    target_states: Set[str],
    predecessors: Dict[str, str],
    max_length: int = 100,
) -> Optional[List[str]]:
    """
    Reconstruct a trace from initial state to one of the target states.

    Uses backward search from a target state to the initial state using
    the predecessors map, then reverses the path.

    Args:
        initial_state: Starting state name
        target_states: Set of goal state names
        predecessors: Map from state to its predecessor (state -> predecessor)
        max_length: Maximum trace length to prevent infinite loops

    Returns:
        List of state names forming the path, or None if no path exists
    """
    if not target_states:
        return None

    # Find a target state that's reachable from initial state
    # by checking if we can trace back to initial state
    for target in target_states:
        current = target
        path = [current]
        visited = {current}

        # Trace backwards to initial state
        while current != initial_state and len(path) < max_length:
            if current not in predecessors:
                break  # No path from this target

            current = predecessors[current]
            if current in visited:
                break  # Cycle detected

            path.append(current)
            visited.add(current)

        # Check if we reached the initial state
        if current == initial_state:
            path.reverse()  # Reverse to get forward path
            return path

    return None


def reconstruct_trace_bfs(
    edges: List[Tuple[str, str]],
    initial_state: str,
    target_states: Set[str],
    max_length: int = 100,
) -> Optional[List[str]]:
    """
    Reconstruct a trace using BFS from initial state to target states.

    This is an alternative to using pre-computed predecessors. It performs
    BFS from the initial state to find the shortest path to any target.

    Args:
        edges: List of (source, target) state transitions
        initial_state: Starting state name
        target_states: Set of goal state names
        max_length: Maximum trace length to prevent infinite loops

    Returns:
        List of state names forming the shortest path, or None if no path exists
    """
    if not target_states:
        return None

    if initial_state in target_states:
        return [initial_state]

    # Build adjacency list for forward search
    adjacency: Dict[str, List[str]] = {}
    for source, target in edges:
        if source not in adjacency:
            adjacency[source] = []
        adjacency[source].append(target)

    # BFS to find shortest path
    queue = deque([(initial_state, [initial_state])])
    visited = {initial_state}

    while queue:
        current, path = queue.popleft()

        if len(path) > max_length:
            continue

        if current in target_states:
            return path

        if current not in adjacency:
            continue

        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None


def reconstruct_counterexample_trace(
    edges: List[Tuple[str, str]],
    initial_state: str,
    violating_states: Set[str],
    max_length: int = 100,
) -> Optional[List[str]]:
    """
    Reconstruct a counterexample trace to a property violation.

    Finds a path from the initial state to a state where the property
    is violated. This is used for negative results (formula doesn't hold).

    Args:
        edges: List of (source, target) state transitions
        initial_state: Starting state name
        violating_states: Set of states where property is violated
        max_length: Maximum trace length

    Returns:
        List of state names showing path to violation, or None if unreachable
    """
    return reconstruct_trace_bfs(edges, initial_state, violating_states, max_length)


def build_predecessor_map_bfs(
    edges: List[Tuple[str, str]], target_states: Set[str]
) -> Dict[str, str]:
    """
    Build a predecessor map using backward BFS from target states.

    For each state reachable from target states (going backward),
    records one predecessor that leads toward a target.

    Args:
        edges: List of (source, target) state transitions
        target_states: Set of goal state names

    Returns:
        Dictionary mapping each reachable state to a predecessor
    """
    # Build reverse adjacency list for backward search
    reverse_adj: Dict[str, List[str]] = {}
    for source, target in edges:
        if target not in reverse_adj:
            reverse_adj[target] = []
        reverse_adj[target].append(source)

    predecessors: Dict[str, str] = {}
    queue = deque(target_states)
    visited = set(target_states)

    # Backward BFS from targets
    while queue:
        current = queue.popleft()

        if current not in reverse_adj:
            continue

        for predecessor in reverse_adj[current]:
            if predecessor not in visited:
                visited.add(predecessor)
                predecessors[predecessor] = current
                queue.append(predecessor)

    return predecessors


def build_predecessor_map_forward(
    edges: List[Tuple[str, str]], initial_state: str
) -> Dict[str, str]:
    """
    Build a predecessor map using forward BFS from initial state.

    For each state reachable from the initial state,
    records the predecessor from which it was first reached.

    Args:
        edges: List of (source, target) state transitions
        initial_state: Starting state name

    Returns:
        Dictionary mapping each reachable state to its predecessor
    """
    # Build forward adjacency list
    adjacency: Dict[str, List[str]] = {}
    for source, target in edges:
        if source not in adjacency:
            adjacency[source] = []
        adjacency[source].append(target)

    predecessors: Dict[str, str] = {}
    queue = deque([initial_state])
    visited = {initial_state}

    # Forward BFS from initial state
    while queue:
        current = queue.popleft()

        if current not in adjacency:
            continue

        for successor in adjacency[current]:
            if successor not in visited:
                visited.add(successor)
                predecessors[successor] = current
                queue.append(successor)

    return predecessors


def extract_shortest_trace(
    initial_state: str,
    target_states: Set[str],
    all_states: Set[str],
    edges: List[Tuple[str, str]],
    max_length: int = 100,
) -> Optional[List[str]]:
    """
    Extract the shortest trace from initial state to any target state.

    Convenience function that handles the complete trace extraction process.

    Args:
        initial_state: Starting state name
        target_states: Set of goal state names
        all_states: Set of all valid state names (for validation)
        edges: List of (source, target) state transitions
        max_length: Maximum trace length

    Returns:
        List of state names forming the shortest path, or None if no path exists
    """
    # Validate inputs
    if initial_state not in all_states:
        return None

    if not target_states:
        return None

    # Filter target states to only valid ones
    valid_targets = target_states.intersection(all_states)
    if not valid_targets:
        return None

    # Use BFS to find shortest path
    return reconstruct_trace_bfs(edges, initial_state, valid_targets, max_length)


def format_trace_with_properties(
    trace: List[str], cgs: CGSProtocol, highlight_props: Optional[List[str]] = None
) -> str:
    """
    Format a trace with atomic propositions that hold at each state.

    Args:
        trace: List of state names
        cgs: CGS model instance
        highlight_props: Optional list of propositions to highlight

    Returns:
        Formatted string showing trace with properties
    """
    if not trace:
        return "(empty trace)"

    result = []
    for state in trace:
        props_at_state = _get_props_at_state(cgs, state)

        if highlight_props:
            highlighted = [p for p in props_at_state if p in highlight_props]
            if highlighted:
                result.append(f"{state} [{', '.join(highlighted)}]")
            else:
                result.append(state)
        else:
            if props_at_state:
                result.append(f"{state} [{', '.join(props_at_state)}]")
            else:
                result.append(state)

    return " -> ".join(result)


def _get_props_at_state(cgs, state: str) -> List[str]:
    """
    Get list of atomic propositions that hold at a given state.

    Args:
        cgs: CGS model instance
        state: State name

    Returns:
        List of proposition names that hold at the state
    """
    try:
        state_idx = cgs.get_index_by_state_name(state)
        props = []

        if hasattr(cgs, "matrix_prop") and cgs.matrix_prop:
            prop_row = cgs.matrix_prop[state_idx]
            atomic_props = cgs.get_atomic_prop()

            for prop_idx, value in enumerate(prop_row):
                if value == 1 and prop_idx < len(atomic_props):
                    props.append(str(atomic_props[prop_idx]))

        return props
    except (IndexError, ValueError):
        return []
