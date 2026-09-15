"""Adapts a VITAMIN `CGS` (matching `CGSProtocol`) into an `automata.TransitionSystem`.

Action cells hold comma-separated joint-action profiles, each either
`|`-separated (one token per agent) or one character per agent, both
real formats, per VITAMIN's own `cgs_actions.parse_joint_action_cell`.
Extra tokens beyond `number_of_agents` are dropped, not an error;
`"I"`/`"IDLE"` normalize to one canonical idle token.

A wildcard (`"*"`) cell means "self-loop on the source state, for any
action" (per `cgs_utils.get_edges`/`graph_relations.labeled_pairs`,
regardless of which column it's in). Materialized as an explicit
self-loop for every action already used elsewhere in the CGS, added after
the whole graph is built, and skipped for any action the source already
has a real destination for.

Reads `cgs.graph` via `get_edges()` instead of a raw O(states^2) scan of
the dense state x state matrix (cached on a real VITAMIN `CGS` until
`cgs.graph` changes). Since VITAMIN's `get_edges()` collapses a wildcard's
target to its own source regardless of column, a self-referencing edge is
ambiguous (genuine diagonal self-loop, a wildcard, or both) and can't be
trusted from `get_edges()` alone, those states fall back to a full row
scan; `source != target` edges are read directly (unambiguous).
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass

from model_checker.automata import TransitionSystem
from model_checker.parsers.game_structures.cgs.protocols import CGSProtocol

AGENT_ACTION_SEPARATOR = "|"
WILDCARD = "*"
IDLE_TOKENS = {"I", "IDLE"}
CANONICAL_IDLE_TOKEN = "IDLE"

# `adapt()` only reads a subset of `CGSProtocol`'s surface (get_edges(),
# build_action_list(), etc.) — see its own docstring for the exact
# convention `get_edges()` must follow for wildcard cells.

JointAction = frozenset[tuple[int, str]]


@dataclass(frozen=True)
class AdaptedCGS:
    """The `TransitionSystem` view of a CGS, plus what `product()` and
    `concurrent_to_turnbased()` need beyond a bare transition relation."""

    transition_system: TransitionSystem
    labels: dict[Hashable, frozenset[str]]
    players: tuple[int, ...]


def adapt(cgs: CGSProtocol) -> AdaptedCGS:
    """Build the `TransitionSystem`, per-state AP labels, and player ids for `cgs`.

    Raises:
        ValueError: a joint-action profile has fewer tokens/characters than
            `cgs.get_number_of_agents()`, or `cgs.initial_state` doesn't name
            a real state.
    """
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
        for profile in cgs.build_action_list(mask):
            action = _joint_action(profile, num_agents)
            known_actions.add(action)
            explicit_actions_by_source.setdefault(source, set()).add(action)
            ts.add_transition(source, action, target)

    for raw_source, raw_target in edges:
        if raw_source == raw_target:
            continue
        source_index = cgs.get_index_by_state_name(raw_source)
        target_index = cgs.get_index_by_state_name(raw_target)
        _record(state_names[source_index], state_names[target_index], cgs.graph[source_index][target_index])


    for source in self_referencing_sources:
        source_index = cgs.get_index_by_state_name(source)
        for target_index, mask in enumerate(cgs.graph[source_index]):
            if mask == 0:
                continue
            _record(state_names[source_index], state_names[target_index], mask)

    for source in wildcard_sources:
        already_explicit = explicit_actions_by_source.get(source, set())
        for action in known_actions - already_explicit:
            ts.add_transition(source, action, source)

    props = list(cgs.atomic_propositions)
    labels = {state: _labels_of(props, cgs.matrix_prop[index]) for index, state in enumerate(state_names)}

    return AdaptedCGS(transition_system=ts, labels=labels, players=players)


def _joint_action(profile: str, num_agents: int) -> JointAction:
    if AGENT_ACTION_SEPARATOR in profile:
        tokens = [_normalize_action_token(t) for t in profile.split(AGENT_ACTION_SEPARATOR)]
    else:
        tokens = [_normalize_action_token(c) for c in profile]
    if len(tokens) < num_agents:
        raise ValueError(
            f"Joint action profile {profile!r} has {len(tokens)} token(s)/character(s); "
            f"expected at least {num_agents} (one per agent, {AGENT_ACTION_SEPARATOR}-separated "
            "or one character each)."
        )
    return frozenset((agent, token) for agent, token in enumerate(tokens[:num_agents], start=1))


def _normalize_action_token(token: str) -> str:
    stripped = str(token).strip()
    return CANONICAL_IDLE_TOKEN if stripped in IDLE_TOKENS else stripped


def _labels_of(props: list[object], row: object) -> frozenset[str]:
    """`props`: `cgs.atomic_propositions`, converted to a list once by the
    caller, it's identical for every state, so redoing it per state (once
    was the original shape here) is pure waste at the CGS's own scale."""
    return frozenset(str(props[i]) for i, value in enumerate(row) if value == 1)
