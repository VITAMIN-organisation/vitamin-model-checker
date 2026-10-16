"""Validated snapshot of finite, deterministic, rectangular CGSs.

No transition is invented and wildcard syntax is rejected, not expanded. A
snapshot is private to a checking run, so mutation of the original model cannot
invalidate caches inside that run.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import product
from math import prod
from types import MappingProxyType
from typing import Any

from model_checker.parsers.game_structures.cgs.cgs_actions import (
    parse_joint_action_cell,
)


def _validate_transitions(cgs: Any) -> dict[str, dict[tuple[str, ...], str]]:
    """Validate total deterministic t(q, a1, ..., an) over local action sets.

    Returns a read-only-by-convention snapshot of each state's joint-action
    transition function, without changing the original model.

    ValueError is raised for a malformed, nondeterministic, non-rectangular,
    or partially defined transition relation. Wildcard cells are unsupported
    by the current Recall pipeline and therefore rejected explicitly.
    """
    states = tuple(str(state) for state in cgs.states)
    n_agents = cgs.get_number_of_agents()
    if not states or len(set(states)) != len(states):
        raise ValueError("CGS must contain unique, nonempty states")
    if type(n_agents) is not int or n_agents < 1:
        raise ValueError("Invalid number of CGS agents")
    if len(cgs.graph) != len(states) or any(
        len(row) != len(states) for row in cgs.graph
    ):
        raise ValueError("Invalid CGS transition-matrix dimensions")

    transitions: dict[str, dict[tuple[str, ...], str]] = {}
    for row_index, state in enumerate(states):
        successors: dict[tuple[str, ...], str] = {}
        for col_index, raw_cell in enumerate(cgs.graph[row_index]):
            if raw_cell in (0, "0", "", None):
                continue
            if not isinstance(raw_cell, str):
                raise ValueError(f"Malformed CGS transition cell at {state!r}")
            if "*" in raw_cell:
                raise ValueError(
                    f"Wildcard joint actions unsupported by strict NatATL at {state!r}"
                )
            destination = states[col_index]
            for joint in parse_joint_action_cell(
                raw_cell, n_agents, strict_arity=True
            ):
                profile = tuple(joint)
                if len(profile) != n_agents or any(not action for action in profile):
                    raise ValueError(f"Invalid joint action {profile!r} at {state!r}")
                old_target = successors.get(profile)
                if old_target is not None and old_target != destination:
                    raise ValueError(
                        f"Nondeterministic CGS at {state!r}: joint action "
                        f"{profile!r} leads to both {old_target!r} "
                        f"and {destination!r}"
                    )
                successors[profile] = destination

        if not successors:
            raise ValueError(f"Non-total CGS: no actions at state {state!r}")

        choices = tuple(
            frozenset(profile[i] for profile in successors)
            for i in range(n_agents)
        )
        required = prod(len(actions) for actions in choices)
        if len(successors) != required:
            missing = next(
                profile for profile in product(*(sorted(actions) for actions in choices))
                if profile not in successors
            )
            raise ValueError(
                f"Incomplete joint-action table at {state!r}: "
                f"{missing!r} is a legal combination of individually "
                f"available actions but has no successor"
            )
        transitions[state] = successors

    return transitions


@dataclass(frozen=True)
class CGSSnapshot:
    states: tuple[str, ...]
    propositions: tuple[str, ...]
    number_of_agents: int
    labels: Mapping
    successors: Mapping
    enabled: Mapping
    outgoing: Mapping
    transitions: Mapping


def prepare_cgs(cgs: Any) -> CGSSnapshot:
    """Parse/validate once; retain all complete joint actions and their targets."""
    try:
        transitions = _validate_transitions(cgs)
        states = tuple(transitions)
        props = tuple(str(p) for p in cgs.atomic_propositions)
        if len(set(props)) != len(props):
            raise ValueError("Duplicate CGS propositions")
        if len(cgs.matrix_prop) != len(states) or any(
            len(row) != len(props) for row in cgs.matrix_prop
        ):
            raise ValueError("Invalid CGS proposition-matrix dimensions")
        if any(str(flag) not in ("0", "1") for row in cgs.matrix_prop for flag in row):
            raise ValueError("CGS proposition labels must be 0 or 1")
        n = cgs.get_number_of_agents()
        labels = {s: frozenset(p for p, v in zip(props, cgs.matrix_prop[i], strict=True) if int(v))
                  for i, s in enumerate(states)}
        outgoing = {s: tuple((target, joint) for joint, target in row.items())
                    for s, row in transitions.items()}
        enabled = {s: MappingProxyType({a: frozenset(j[a-1] for j in row)
                                       for a in range(1, n+1)})
                   for s, row in transitions.items()}
        return CGSSnapshot(
            states, props, n, MappingProxyType(labels),
            MappingProxyType({s: frozenset(row.values()) for s, row in transitions.items()}),
            MappingProxyType(enabled), MappingProxyType(outgoing),
            MappingProxyType({s: MappingProxyType(row) for s, row in transitions.items()}),
        )
    except (ValueError, TypeError, IndexError) as exc:
        raise ValueError(f"[MODEL] {exc}") from exc
