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


def find_lasso(
    edges: list[tuple[str, str]],
    start: str,
    allowed: set[str],
) -> tuple[list[str], int] | None:
    """A lasso from start inside allowed: its states, each once, and the index the last one steps back to.

    The prefix is a shortest path to the nearest state that lies on a cycle
    inside allowed, and the loop is a shortest cycle through that state. None
    when start is outside allowed, when no such cycle is reachable inside
    allowed, or when the lasso has more than MAX_TRACE_LENGTH states.
    """
    if start not in allowed:
        return None

    inside = [(s, t) for s, t in edges if s in allowed and t in allowed]
    prefix = reconstruct_trace_bfs(
        inside, start, _states_on_a_cycle(_build_adjacency(inside), start)
    )
    if prefix is None:
        return None

    entry = prefix[-1]
    # A path from entry to a state that steps back to entry is itself a cycle.
    steps_back = {s for s, t in inside if t == entry}
    loop = reconstruct_trace_bfs(inside, entry, steps_back)
    if loop is None or len(prefix) + len(loop) - 1 > MAX_TRACE_LENGTH:
        return None
    return prefix + loop[1:], len(prefix) - 1


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
