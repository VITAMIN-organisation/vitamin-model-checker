"""Turn a VITAMIN CGS into an `automata.TransitionSystem`.

- Joint actions: `|`-separated or one character per agent, as in
  `cgs_actions.parse_joint_action_cell`, which requires one token per agent. `I`
  and `IDLE` are the same idle action.
- Wildcard `*`: a self-loop for every action the CGS uses elsewhere, except the
  actions the state already has. A CGS with only `*` cells gets one all-`*` action.
- Edges come from `get_edges()` instead of a full matrix scan. Its self-edges can
  mean a diagonal entry or a wildcard, so those rows are scanned in full.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

from model_checker.automata import TransitionSystem
from model_checker.parsers.game_structures.cgs import cgs_actions
from model_checker.parsers.game_structures.cgs.protocols import CGSProtocol

WILDCARD = "*"

JointAction = frozenset[tuple[int, str]]


@dataclass(frozen=True)
class AdaptedCGS:
    """A CGS as a `TransitionSystem`, with its labels and players."""

    transition_system: TransitionSystem
    labels: dict[str, frozenset[str]]
    players: tuple[int, ...]
    propositions: frozenset[str]

    @property
    def states(self) -> frozenset[str]:
        return frozenset(cast("set[str]", self.transition_system.states))

    @property
    def initial_state(self) -> str:
        (state,) = self.transition_system.initial_states
        return cast(str, state)


def adapt(cgs: CGSProtocol) -> AdaptedCGS:
    """Build the transition system, labels and players of `cgs`."""
    num_agents = cgs.get_number_of_agents()
    players = tuple(range(1, num_agents + 1))
    state_names = [str(cgs.get_state_name_by_index(i)) for i in range(len(cgs.states))]
    initial_state = str(cgs.initial_state)
    if initial_state not in state_names:
        raise ValueError(f"initial_state {initial_state!r} is not among {state_names}")

    ts = TransitionSystem()
    for state in state_names:
        ts.add_state(state, initial=state == initial_state)

    known_actions: set[JointAction] = set()
    explicit_actions_by_source: dict[str, set[JointAction]] = {}
    wildcard_sources: list[str] = []

    edges = cgs.get_edges()
    self_referencing_sources = {source for source, target in edges if source == target}

    def _record(source: str, target: str, mask: object) -> None:
        if mask == WILDCARD:
            wildcard_sources.append(source)
            return
        for action in _joint_actions(mask, num_agents):
            known_actions.add(action)
            explicit_actions_by_source.setdefault(source, set()).add(action)
            ts.add_transition(source, action, target)

    for raw_source, raw_target in edges:
        if raw_source == raw_target:
            continue
        source_index = cgs.get_index_by_state_name(raw_source)
        target_index = cgs.get_index_by_state_name(raw_target)
        _record(
            state_names[source_index],
            state_names[target_index],
            cgs.graph[source_index][target_index],
        )

    for source in self_referencing_sources:
        source_index = cgs.get_index_by_state_name(source)
        for target_index, mask in enumerate(cgs.graph[source_index]):
            if mask == 0:
                continue
            _record(state_names[source_index], state_names[target_index], mask)

    wildcard_action = frozenset((agent, WILDCARD) for agent in range(1, num_agents + 1))
    for source in wildcard_sources:
        already_explicit = explicit_actions_by_source.get(source, set())
        for action in (known_actions or {wildcard_action}) - already_explicit:
            ts.add_transition(source, action, source)

    props = list(cgs.atomic_propositions)
    labels = {
        state: _labels_of(props, cgs.matrix_prop[index])
        for index, state in enumerate(state_names)
    }

    return AdaptedCGS(
        transition_system=ts,
        labels=labels,
        players=players,
        propositions=frozenset(str(p) for p in props),
    )


def _joint_actions(mask: object, num_agents: int) -> list[JointAction]:
    # The raw cell is parsed once: re-reading a normalized profile such as `IDLE`
    # for one agent would split it into characters.
    return [
        frozenset(enumerate(tokens, start=1))
        for tokens in cgs_actions.parse_joint_action_cell(str(mask), num_agents)
    ]


def _labels_of(props: list[object], row: Iterable[object]) -> frozenset[str]:
    """The propositions whose entry in the 0/1 label `row` is 1; the caller builds
    `props` once, since it is the same for every state."""
    return frozenset(str(props[i]) for i, value in enumerate(row) if value == 1)
