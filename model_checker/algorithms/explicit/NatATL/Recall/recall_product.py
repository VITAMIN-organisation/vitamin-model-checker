"""Reachable finite product of a CGS and recall-guard automata.

This module checks a FIXED profile of recall strategies; it does not
enumerate strategies or perform temporal model checking.
Histories include the initial and current state labels.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.history_automaton import (
    HistoryRegex,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
)


@dataclass(frozen=True)
class ProductState:
    state: str
    memory: tuple[frozenset[int], ...]


@dataclass
class RecallProduct:
    initial: ProductState
    successors: dict[ProductState, frozenset[ProductState]]
    # Each edge retains its COMPLETE joint action, including opponent choices.
    edges: dict[ProductState, tuple[tuple[ProductState, tuple[str, ...]], ...]]
    labels: dict[ProductState, frozenset[str]]


def build_recall_product(
    cgs: Any,
    agents: list[int],
    strategies: list[dict],
    initial_state: str | None = None,
    *, context=None,
) -> RecallProduct:
    """Prune a finite CGS using ordered regular-history strategies.

    Agents use 1-based indices.  Every strategy is a list of
    (history_regex, action) pairs ending with an explicit T* fallback.
    Unchosen coalition actions are removed; opponents remain unrestricted.
    An action unavailable at a reachable history makes the profile invalid.
    """
    from model_checker.algorithms.explicit.NatATL.Recall.recall_context import (
        RecallContext,
    )
    context = RecallContext(cgs) if context is None else context
    view = context.snapshot
    n_agents = view.number_of_agents
    if len(agents) != len(strategies):
        raise ValueError("One strategy per coalition agent is required")
    if len(set(agents)) != len(agents) or any(
        not isinstance(a, int) or a < 1 or a > n_agents for a in agents
    ):
        raise ValueError("Invalid or repeated coalition agent")

    state_labels = view.labels

    # Compile monitors once per rule, preserving coalition and rule ordering.
    monitors: list[HistoryRegex] = []
    rule_spans: list[tuple[int, int, tuple[str, ...]]] = []
    for strategy in strategies:
        pairs = strategy.get("condition_action_pairs")
        if not isinstance(pairs, (list, tuple)) or not pairs:
            raise ValueError("Recall strategy has no rules")
        if pairs[-1][0].strip() != "T*":
            raise ValueError("Recall strategy requires explicit final T* fallback")
        start = len(monitors)
        actions = []
        for pattern, action in pairs:
            monitors.append(context.monitor(pattern))
            actions.append(normalize_action_token(action))
        rule_spans.append((start, len(monitors), tuple(actions)))

    # Shared validated transitions retain every complete opponent action profile.
    outgoing = view.outgoing

    start_name = str(cgs.initial_state if initial_state is None else initial_state)
    if start_name not in state_labels:
        raise ValueError(f"Unknown initial state {start_name!r}")

    # The initial state's labelling MUST be consumed by every monitor.
    initial = ProductState(
        start_name,
        tuple(m.step(m.initial, state_labels[start_name]) for m in monitors),
    )
    successors: dict[ProductState, frozenset[ProductState]] = {}
    edges: dict[ProductState, tuple[tuple[ProductState, tuple[str, ...]], ...]] = {}
    labels: dict[ProductState, frozenset[str]] = {}
    discovered = {initial}
    queue = deque([initial])

    while queue:
        node = queue.popleft()
        labels[node] = state_labels[node.state]

        selected = []

        for agent, (begin, end, actions) in zip(
            agents, rule_spans, strict=True
        ):
            # Enabled actions in the ORIGINAL CGS state.
            # Opponent actions remain unrestricted.
            enabled = {
                joint[agent - 1]
                for _, joint in outgoing[node.state]
            }

            # First rule with both:
            # 1. matching history guard;
            # 2. enabled action.
            first = next(
                (
                    i
                    for i, monitor in enumerate(
                        monitors[begin:end]
                    )
                    if monitor.is_accepting(
                        node.memory[begin + i]
                    )
                    and actions[i] in enabled
                ),
                None,
            )

            if first is None:
                raise ValueError(
                    "No enabled matching recall rule "
                    f"for agent {agent} at reachable "
                    f"state {node.state!r} "
                    "(not enabled)"
                )

            selected.append(actions[first])


        retained = []
        for dest, joint in outgoing[node.state]:
            if all(joint[agent - 1] == action
                   for agent, action in zip(agents, selected, strict=True)):
                successor = ProductState(
                    dest,
                    tuple(
                        monitor.step(mem, state_labels[dest])
                        for monitor, mem in zip(monitors, node.memory, strict=True)
                    ),
                )
                retained.append((successor, joint))
                if successor not in discovered:
                    discovered.add(successor)
                    queue.append(successor)

        if not retained:
            raise ValueError(
                f"Selected coalition action {tuple(selected)} not enabled "
                f"at reachable product state {node.state!r}"
            )
        edges[node] = tuple(retained)
        successors[node] = frozenset(dest for dest, _ in retained)

    return RecallProduct(initial, successors, edges, labels)

def build_validated_recall_product(
    cgs: Any,
    agents: list[int],
    strategies: list[dict],
    initial_state: str | None = None,
    *, context=None,
) -> RecallProduct:
    """Build a recall product after global strategy validation.

    Each guarded-action rule must be appropriate on every
    matching history of the original, unpruned CGS.
    """

    from model_checker.algorithms.explicit.NatATL.Recall.recall_appropriateness import (
        validate_recall_profile,
    )
    from model_checker.algorithms.explicit.NatATL.Recall.recall_context import (
        RecallContext,
    )
    context = RecallContext(cgs) if context is None else context
    # Step 1: Check that every guarded-action pair is globally
    # appropriate, independently of the chosen initial state.
    validate_recall_profile(
        cgs,
        agents,
        strategies,
        context=context,
    )

    # Step 2: Only admissible strategies reach product construction.
    return build_recall_product(
        cgs,
        agents,
        strategies,
        initial_state=initial_state,
        context=context,
    )
