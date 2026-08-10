"""Transition matrix updates for NatATL memoryless strategy pruning."""

from model_checker.parsers.game_structures.cgs.cgs_actions import (
    AGENT_ACTION_SEPARATOR,
    CANONICAL_IDLE_TOKEN,
    JOINT_CHOICE_SEPARATOR,
    normalize_action_token,
    parse_joint_action_cell,
)


def _row_indices_for_states(
    state_to_index: dict[str, int], states: set[str]
) -> list[int]:
    """Return sorted row indices for states present in ``state_to_index``."""
    rows = [state_to_index[state] for state in states if state in state_to_index]
    rows.sort()
    return rows


def _filter_joint_cell(
    elem: str,
    *,
    tuple_idx: int,
    allowed_tokens: set[str],
    agent_count: int,
) -> str | int:
    """Keep matching joint profiles in one cell; return 0 when none match."""
    kept = []
    for tokens in parse_joint_action_cell(elem, agent_count):
        if tuple_idx < len(tokens) and tokens[tuple_idx] in allowed_tokens:
            kept.append(AGENT_ACTION_SEPARATOR.join(tokens))
    return JOINT_CHOICE_SEPARATOR.join(kept) if kept else 0


def modify_matrix(
    graph: list[list],
    states: set[str],
    action: str,
    agent_index: int,
    agents: list[int],
    num_agents: int | None = None,
    *,
    state_to_index: dict[str, int],
    in_place: bool = False,
) -> list[list]:
    """Keep only transitions where one agent plays action in the given states.

    Joint profiles in each cell may use compact form (``AC``) or explicit form
    (``A|C``); both are read as per-agent token vectors. Matching joints are
    written back in pipe-separated form.

    Row selection uses ``state_to_index`` (O(|states|)) instead of scanning the
    label matrix. When ``in_place`` is True, matching rows are updated in the
    input graph; callers should copy the graph once before the first in-place
    prune if the original must stay unchanged.
    """
    rows_to_update = _row_indices_for_states(state_to_index, states)
    if not rows_to_update:
        if in_place:
            return graph
        return [row.copy() for row in graph]

    tuple_idx = agents[agent_index - 1] - 1
    required_token = normalize_action_token(action)
    allowed_tokens = {CANONICAL_IDLE_TOKEN, required_token}
    agent_count = num_agents if num_agents is not None else max(agents, default=0)

    target_graph = graph if in_place else list(graph)
    for i in rows_to_update:
        row = graph[i] if in_place else graph[i][:]
        for j, elem in enumerate(row):
            if not isinstance(elem, str) or elem == "*":
                continue
            row[j] = _filter_joint_cell(
                elem,
                tuple_idx=tuple_idx,
                allowed_tokens=allowed_tokens,
                agent_count=agent_count,
            )

        if not in_place:
            target_graph[i] = row

    return target_graph
