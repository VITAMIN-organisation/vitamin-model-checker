"""Exact pruning for bounded memoryless natural strategies.

The default is first-match appropriateness (Natural Strategic Ability, note 3).
The stronger global rule condition is an explicit option, never a silent change
in the meaning of an existing bounded query. No IDLE alternatives are inserted.
"""
import ast
import copy
from typing import Any

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.algorithms.explicit.NatATL.boolean_guards import BooleanGuard
from model_checker.algorithms.explicit.NatATL.strategy_errors import (
    InadmissibleStrategy,
)
from model_checker.parsers.game_structures.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_actions import normalize_action_token
from model_checker.parsers.game_structures.cgs.semantic_snapshot import prepare_cgs


def compile_memoryless_profile(snapshot, agents, strategies, *,
                               appropriateness="first-match", guard_cache=None):
    """Return coalition actions by state, validating against the ORIGINAL CGS.

    The return value can be used as an exact behavioural cache key only after
    this validation. Guard caches are local to one fixed snapshot/checking run.
    """
    if appropriateness not in ("first-match", "global"):
        raise ValueError("Unknown appropriateness mode")
    if len(agents) != len(strategies) or len(set(agents)) != len(agents):
        raise ValueError("One strategy per distinct coalition agent is required")
    if any(type(a) is not int or a < 1 or a > snapshot.number_of_agents for a in agents):
        raise ValueError("Invalid coalition agent")
    cache = {} if guard_cache is None else guard_cache
    all_states = set(snapshot.states)
    selections = {s: [] for s in snapshot.states}
    for agent, strategy in zip(agents, strategies, strict=True):
        if not isinstance(strategy, dict):
            raise ValueError("Malformed memoryless strategy")
        rules = strategy.get("condition_action_pairs")
        if not isinstance(rules, (list, tuple)) or not rules:
            raise ValueError("Missing explicit (T, action) fallback")
        if any(not isinstance(r, (tuple, list)) or len(r) != 2 for r in rules):
            raise ValueError("Malformed guarded-action pair")
        if not isinstance(rules[-1][0], str) or rules[-1][0].strip() != "T":
            raise ValueError("Missing explicit (T, action) fallback")
        covered = set()
        selected = {}
        for condition, action in rules:
            if not isinstance(condition, str) or not isinstance(action, str) or not action.strip():
                raise ValueError("Malformed guard or action")
            if condition not in cache:
                guard = BooleanGuard(condition, set(snapshot.propositions))
                cache[condition] = frozenset(s for s in snapshot.states if guard(snapshot.labels[s]))
            matched = set(cache[condition])
            applicable = matched - covered
            required = matched if appropriateness == "global" else applicable
            token = normalize_action_token(action)
            for state in sorted(required):
                if token not in snapshot.enabled[state][agent]:
                    raise InadmissibleStrategy(
                        f"Action {action!r} is not enabled for agent {agent} in state {state!r} "
                        f"under {appropriateness} appropriateness"
                    )
            for state in applicable:
                selected[state] = token
            covered.update(applicable)
        if covered != all_states:
            raise InadmissibleStrategy("Incomplete strategy: states not covered")
        for state in snapshot.states:
            selections[state].append(selected[state])
    return {state: tuple(actions) for state, actions in selections.items()}


def process_transition_matrix_data_fixed(
    cgs: CGS, model_path: str, agents: list[int], *strategies: dict[str, Any],
    appropriateness="first-match", snapshot=None, guard_cache=None,
) -> list[list]:
    """Materialize the exact pruned matrix; model_path is retained for API compatibility."""
    view = prepare_cgs(cgs) if snapshot is None else snapshot
    selected = compile_memoryless_profile(
        view, agents, strategies, appropriateness=appropriateness, guard_cache=guard_cache
    )
    indices = {s: i for i, s in enumerate(view.states)}
    graph: list[list[int | str]] = [
        [0 for _ in view.states] for _ in view.states
    ]
    for state in view.states:
        for target, joint in view.outgoing[state]:
            if all(joint[a-1] == action for a, action in zip(agents, selected[state], strict=True)):
                i, j = indices[state], indices[target]
                value = "|".join(joint)
                previous = graph[i][j]
                if previous == 0:
                    graph[i][j] = value
                elif isinstance(previous, str):
                    graph[i][j] = previous + "," + value
                else:
                    raise ValueError("Invalid pruned transition cell")
    return graph

def pruning(
    cgs: CGS, model_path: str, agents: list[int], formula: str, current_agents: list
) -> bool:
    """Prune the model to a strategy profile and run CTL on the result.

    Returns True when the initial state satisfies the formula on the pruned model.
    """
    # Isolate pruned model from the shared CGS used across strategy candidates.
    cgs1 = copy.deepcopy(cgs)
    cgs1.graph = process_transition_matrix_data_fixed(
        cgs, model_path, agents, *current_agents
    )

    # Use in-memory CTL model checking
    result = model_checking(formula, model_path, preloaded_model=cgs1)


    # Reject backend errors instead of interpreting them as False.
    if not isinstance(result, dict) or result.get("error"):
        raise ValueError(f"CTL verification failed: {result}")

    res = result.get("res")

    if not isinstance(res, str) or not res.startswith("Result: "):
        raise ValueError(f"Malformed CTL result: {result}")

    # Extract the satisfying states returned by CTL.
    serialized_states = res[len("Result: "):].strip()

    if serialized_states in ("set()", "{}", "()"):
        satisfying_states = set()
    else:
        try:
            parsed = ast.literal_eval(serialized_states)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(
                f"Invalid CTL state set: {res}"
            ) from exc

        if not isinstance(parsed, (set, tuple, list)):
            raise ValueError(f"Invalid CTL state set: {res}")

        satisfying_states = {
            str(state) for state in parsed
        }

    # Truth must hold at the actual initial state.
    initial = str(cgs1.initial_state)
    satisfied = initial in satisfying_states

    expected = f"Initial state {initial}: {satisfied}"

    if result.get("initial_state") != expected:
        raise ValueError(
            "Inconsistent CTL initial-state result: "
            f"expected {expected!r}, "
            f"got {result.get('initial_state')!r}"
        )

    if (
        "satisfied" in result
        and result["satisfied"] is not satisfied
    ):
        raise ValueError("Inconsistent CTL satisfaction flag")

    return satisfied
