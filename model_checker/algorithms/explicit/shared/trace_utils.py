"""Build witness and counterexample paths from predecessor maps."""

from collections import deque

from model_checker.parsers.game_structures.cgs import CGSProtocol

MAX_TRACE_LENGTH = 100


def _build_adjacency(edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Build a forward adjacency list from an edge list."""
    adjacency: dict[str, list[str]] = {}
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)
    return adjacency


def reconstruct_trace_from_predecessors(
    initial_state: str,
    target_states: set[str],
    predecessors: dict[str, str],
    max_length: int = MAX_TRACE_LENGTH,
) -> list[str] | None:
    """Walk backward from a target state to the initial state using predecessors."""
    if not target_states:
        return None

    if initial_state in target_states:
        return [initial_state]

    for target in target_states:
        current = target
        path = [current]
        visited = {current}

        while current != initial_state and len(path) < max_length:
            if current not in predecessors:
                break
            current = predecessors[current]
            if current in visited:
                break
            path.append(current)
            visited.add(current)

        if current == initial_state:
            path.reverse()
            return path

    return None


def reconstruct_trace_bfs(
    edges: list[tuple[str, str]],
    initial_state: str,
    target_states: set[str],
    max_length: int = MAX_TRACE_LENGTH,
) -> list[str] | None:
    """Shortest path from the initial state to any target, using forward BFS."""
    if not target_states:
        return None

    if initial_state in target_states:
        return [initial_state]

    adjacency = _build_adjacency(edges)
    queue = deque([(initial_state, [initial_state])])
    visited = {initial_state}

    while queue:
        current, path = queue.popleft()

        if len(path) > max_length:
            continue

        if current in target_states:
            return path

        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None


def build_predecessor_map_bfs(
    edges: list[tuple[str, str]], target_states: set[str]
) -> dict[str, str]:
    """Map each state to one predecessor, searching backward from targets."""
    reverse_adj: dict[str, list[str]] = {}
    for source, target in edges:
        reverse_adj.setdefault(target, []).append(source)

    predecessors: dict[str, str] = {}
    queue = deque(target_states)
    visited = set(target_states)

    while queue:
        current = queue.popleft()
        for predecessor in reverse_adj.get(current, []):
            if predecessor not in visited:
                visited.add(predecessor)
                predecessors[predecessor] = current
                queue.append(predecessor)

    return predecessors


def reverse_adjacency(graph: dict, nodes: set | None = None) -> dict:
    """Build a predecessor adjacency list from a forward graph."""
    if nodes is None:
        nodes = set(graph.keys())
        for successors in graph.values():
            nodes.update(successors)
    reverse = {node: [] for node in nodes}
    for source, successors in graph.items():
        for target in successors:
            reverse[target].append(source)
    return reverse


def any_backward_path(
    starts,
    reverse_graph: dict,
    *,
    is_goal,
    allows_node,
    sort_neighbors=None,
) -> bool:
    """True if some backward path from starts reaches a goal node."""

    def dfs(node, on_path: frozenset) -> bool:
        if not allows_node(node):
            return False
        if is_goal(node):
            return True
        extended = on_path | {node}
        neighbors = reverse_graph.get(node, [])
        if sort_neighbors is not None:
            neighbors = sort_neighbors(neighbors)
        for predecessor in neighbors:
            if predecessor not in extended and dfs(predecessor, extended):
                return True
        return False

    return any(dfs(start, frozenset()) for start in starts)


def collect_backward_paths(
    starts,
    reverse_graph: dict,
    *,
    is_goal,
    allows_node,
    sort_neighbors=None,
) -> list[list]:
    """All simple backward paths from starts to goal nodes."""
    paths: list[list] = []

    def dfs(node, path: list) -> None:
        if not allows_node(node):
            return
        new_path = path + [node]
        if is_goal(node):
            paths.append(new_path)
            return
        neighbors = reverse_graph.get(node, [])
        if sort_neighbors is not None:
            neighbors = sort_neighbors(neighbors)
        for predecessor in neighbors:
            if predecessor not in path:
                dfs(predecessor, new_path)

    for start in starts:
        dfs(start, [])
    return paths


def build_predecessor_map_forward(
    edges: list[tuple[str, str]], initial_state: str
) -> dict[str, str]:
    """Map each reachable state to the predecessor found by forward BFS."""
    adjacency = _build_adjacency(edges)
    predecessors: dict[str, str] = {}
    queue = deque([initial_state])
    visited = {initial_state}

    while queue:
        current = queue.popleft()
        for successor in adjacency.get(current, []):
            if successor not in visited:
                visited.add(successor)
                predecessors[successor] = current
                queue.append(successor)

    return predecessors


def extract_shortest_trace(
    initial_state: str,
    target_states: set[str],
    all_states: set[str],
    edges: list[tuple[str, str]],
    max_length: int = MAX_TRACE_LENGTH,
) -> list[str] | None:
    """Shortest path to a valid target state, or None if there is no path."""
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
    trace: list[str], cgs: CGSProtocol, highlight_props: list[str] | None = None
) -> str:
    """Format a path as ``state [props] -> ...``."""
    if not trace:
        return "(empty trace)"

    result = []
    for state in trace:
        props_at_state = _get_props_at_state(cgs, state)
        visible = (
            [p for p in props_at_state if p in highlight_props]
            if highlight_props
            else props_at_state
        )
        result.append(f"{state} [{', '.join(visible)}]" if visible else state)

    return " -> ".join(result)


def _get_props_at_state(cgs, state: str) -> list[str]:
    """Return proposition names that hold in the given state."""
    try:
        state_idx = cgs.get_index_by_state_name(state)
        props = []

        if hasattr(cgs, "matrix_prop") and cgs.matrix_prop:
            prop_row = cgs.matrix_prop[state_idx]
            atomic_props = cgs.atomic_propositions

            for prop_idx, value in enumerate(prop_row):
                if value == 1 and prop_idx < len(atomic_props):
                    props.append(str(atomic_props[prop_idx]))

        return props
    except (IndexError, ValueError):
        return []
