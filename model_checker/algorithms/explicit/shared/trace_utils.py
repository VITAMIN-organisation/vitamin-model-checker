"""Build witness and counterexample paths and lassos from an edge list."""

from collections import deque
from collections.abc import Iterator

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


def _states_on_a_cycle(adjacency: dict[str, list[str]], start: str) -> set[str]:
    """The states reachable from start that lie on a cycle.

    Iterative Tarjan over strongly connected components, so a long chain does
    not hit the recursion limit.
    """
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    work: list[tuple[str, Iterator[str]]] = []
    cyclic: set[str] = set()

    def visit(state: str) -> None:
        index[state] = low[state] = len(index)
        stack.append(state)
        on_stack.add(state)
        work.append((state, iter(adjacency.get(state, []))))

    visit(start)
    while work:
        state, successors = work[-1]
        for successor in successors:
            if successor not in index:
                visit(successor)
                break
            if successor in on_stack:
                low[state] = min(low[state], index[successor])
        else:
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[state])
            if low[state] == index[state]:
                component = set()
                member = None
                while member != state:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.add(member)
                if len(component) > 1 or state in adjacency.get(state, []):
                    cyclic.update(component)

    return cyclic


def _breadth_first(
    adjacency: dict[str, list[str]], root: str, max_depth: int
) -> dict[str, tuple[int, str | None]]:
    """Map each state within max_depth steps of root to its depth and parent."""
    tree: dict[str, tuple[int, str | None]] = {root: (0, None)}
    queue = deque([root])
    while queue:
        state = queue.popleft()
        depth = tree[state][0]
        if depth == max_depth:
            continue
        for successor in adjacency.get(state, []):
            if successor not in tree:
                tree[successor] = (depth + 1, state)
                queue.append(successor)
    return tree


def _tree_path(tree: dict[str, tuple[int, str | None]], state: str) -> list[str]:
    """Return the tree path from the root to state."""
    path: list[str] = []
    current: str | None = state
    while current is not None:
        path.append(current)
        current = tree[current][1]
    return path[::-1]


def find_lasso(
    edges: list[tuple[str, str]],
    start: str,
    allowed: set[str],
) -> tuple[list[str], int] | None:
    """Return the shortest lasso from start inside allowed, or None.

    The lasso is its states, each once, and the index its last state steps back
    to. None when no lasso has at most MAX_TRACE_LENGTH states.
    """
    if start not in allowed:
        return None

    inside = [(s, t) for s, t in edges if s in allowed and t in allowed]
    adjacency = _build_adjacency(inside)
    predecessors: dict[str, set[str]] = {}
    for source, target in inside:
        predecessors.setdefault(target, set()).add(source)
    on_a_cycle = _states_on_a_cycle(adjacency, start)
    from_start = _breadth_first(adjacency, start, MAX_TRACE_LENGTH - 1)
    best: tuple[list[str], int] | None = None
    best_size = MAX_TRACE_LENGTH + 1
    # Entries come in depth order and a cycle adds at least one state.
    for entry, (depth, _) in from_start.items():
        if depth + 1 >= best_size:
            break
        if entry not in on_a_cycle:
            continue
        from_entry = _breadth_first(adjacency, entry, best_size - depth - 2)
        steps_back = next((s for s in from_entry if s in predecessors[entry]), None)
        if steps_back is not None:
            loop = _tree_path(from_entry, steps_back)
            best = (_tree_path(from_start, entry) + loop[1:], depth)
            best_size = len(best[0])
    return best


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
