"""Global appropriateness checks for NatATL recall guarded-action rules.

A pair (r, action) is appropriate only if 'action' is enabled at the last
state of EVERY finite CGS history matching regex r (Section 6.1 of
Jamroga--Malvone--Murano, Natural Strategic Ability).

This validator explores a finite CGS x regex-monitor product from *every*
CGS state, without applying the strategy being validated. Consequently it
also checks histories that a particular proposed strategy cannot reach.
No finite unfolding bound is used.

A checked strategy must end in the explicit (T*, IDLE) fallback.
"""

from collections import deque
from collections.abc import Mapping, Sequence
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.history_automaton import (
    HistoryRegex,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
)


class InappropriateRecallRule(ValueError):
    """An action is unavailable after a history recognized by its guard."""


def _read_cgs(cgs):
    """Legacy tuple adapter; new verification runs share RecallContext instead."""
    from model_checker.parsers.game_structures.cgs.semantic_snapshot import prepare_cgs
    v = prepare_cgs(cgs)
    return v.states, v.propositions, v.number_of_agents, v.labels, v.successors, v.enabled


def _check_rule(
    *,
    states: tuple[str, ...],
    propositions: tuple[str, ...],
    labels: Mapping,
    successors: Mapping,
    enabled: Mapping,
    agent: int,
    pattern: str,
    action: str,
    monitor=None,
) -> None:
    monitor = HistoryRegex(pattern, propositions) if monitor is None else monitor

    # All legal histories may start at any model state. The current state's
    # labelling is consumed immediately, just as in build_recall_product().
    pending = deque()
    seen = set()
    for state in states:
        memory = monitor.step(monitor.initial, labels[state])
        key = (state, memory)
        if key not in seen:
            seen.add(key)
            pending.append((state, memory, (state,)))

    while pending:
        state, memory, history = pending.popleft()
        if monitor.is_accepting(memory) and action not in enabled[state][agent]:
            raise InappropriateRecallRule(
                f"Inappropriate recall rule for agent {agent}: "
                f"({pattern!r}, {action!r}) matches history {history!r}, "
                f"but {action!r} is not enabled in state {state!r}"
            )
        for target in successors[state]:
            new_memory = monitor.step(memory, labels[target])
            key = (target, new_memory)
            if key not in seen:
                seen.add(key)
                pending.append((target, new_memory, history + (target,)))


def validate_recall_profile(
    cgs: Any,
    agents: Sequence[int],
    strategies: Sequence[dict],
    *, context=None,
) -> None:
    """Raise ValueError if any recall rule is globally inappropriate.

    Important: this checks all matching histories of the unpruned CGS,
    not merely those reachable under the supplied profile.
    """
    from model_checker.algorithms.explicit.NatATL.Recall.recall_context import (
        RecallContext,
    )
    context = RecallContext(cgs) if context is None else context
    v = context.snapshot
    states, props, count = v.states, v.propositions, v.number_of_agents
    labels, successors, enabled = v.labels, v.successors, v.enabled
    if len(agents) != len(strategies) or not agents:
        raise ValueError("Expected one strategy for each coalition member")
    if len(set(agents)) != len(agents) or any(
        not isinstance(a, int) or a < 1 or a > count for a in agents
    ):
        raise ValueError("Invalid or repeated coalition agent")

    for agent, strategy in zip(agents, strategies, strict=True):
        if not isinstance(strategy, dict):
            raise ValueError("Malformed recall strategy")
        rules = strategy.get("condition_action_pairs")
        if not isinstance(rules, (list, tuple)) or not rules:
            raise ValueError("Empty recall rule list")
        for item in rules:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError("Malformed recall guarded-action pair")
        if rules[-1][0].strip() != "T*" or (
            normalize_action_token(rules[-1][1]) != "IDLE"
        ):
            raise ValueError("Recall requires final (T*, IDLE) fallback")

        for pattern, action in rules:
            token = normalize_action_token(action)
            key = (agent, pattern, token)
            if key in context.rule_results:
                context.stats["Appropriateness Cache Hits"] += 1
                error = context.rule_results[key]
                if error is not None:
                    raise InappropriateRecallRule(error)
                continue
            context.stats["Appropriateness Checks"] += 1
            try:
                _check_rule(
                    states=states, propositions=props, labels=labels,
                    successors=successors, enabled=enabled, agent=agent,
                    pattern=pattern, action=token, monitor=context.monitor(pattern),
                )
            except InappropriateRecallRule as exc:
                context.rule_results[key] = str(exc)
                raise
            else:
                context.rule_results[key] = None
