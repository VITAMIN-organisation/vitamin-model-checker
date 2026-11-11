"""Build witness and counterexample paths and lassos from an edge list."""

from collections import deque

from model_checker.parsers.game_structures.cgs import CGSProtocol

MAX_TRACE_LENGTH = 100


def _build_adjacency(edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Build a forward adjacency list from an edge list."""
    adjacency: dict[str, list[str]] = {}
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)
    return adjacency


def reconstruct_trace_bfs(
    edges: list[tuple[str, str]],
    initial_state: str,
    target_states: set[str],
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

        if len(path) > MAX_TRACE_LENGTH:
            continue

        if current in target_states:
            return path

        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None


def find_lasso(
    edges: list[tuple[str, str]],
    start: str,
    allowed: set[str],
) -> tuple[list[str], int] | None:
    """A lasso from start inside allowed: its states, each once, and the index the last one steps back to.

    The walk takes the first successor in allowed at each step. None when start
    is outside allowed, when the walk reaches a state with no successor in
    allowed, or when it passes MAX_TRACE_LENGTH states.
    """
    if start not in allowed:
        return None

    adjacency = _build_adjacency(edges)
    path = [start]
    index_of = {start: 0}

    while len(path) <= MAX_TRACE_LENGTH:
        successor = next(
            (state for state in adjacency.get(path[-1], []) if state in allowed), None
        )
        if successor is None:
            return None
        if successor in index_of:
            return path, index_of[successor]
        index_of[successor] = len(path)
        path.append(successor)

    return None


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
