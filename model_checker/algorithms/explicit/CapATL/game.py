"""Coalition games of CapATL on a capCGS model.

A complete capacity assignment gives one capacity to every agent. Sets of
assignments are bitmasks over `CapModel.assignments`.

The coalition picks one capacity per member before play and keeps it. It sees
the states and its own moves, not the opponents' moves, so it cannot tell
apart plays that differ only there. A game node is (state, plays): `plays`
holds one entry per such play still undecided, namely the assignments that
play allows (an opponent must keep one capacity along a play, so a play needs
at least one). The coalition picks one move per node, which is a strategy
that depends only on what it has seen.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Iterable
from typing import Any

from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
    parse_joint_action_cell,
)

Move = tuple[str, ...]  # one action per agent, agent 1 first
Play = int  # bitmask of the assignments the play so far allows
Node = tuple[str, frozenset[Play]]
StateTest = Callable[[str], bool]
# Per node, one list per coalition move of the nodes it leads to; None is a lost play.
Graph = dict[Node, list[list[Node | None]]]


class CapModel:
    """Transitions with `*` expanded, and the assignments each joint move allows.

    The capCGS loader has checked that every agent has a capacity and that
    every assigned capacity has an action line.
    """

    def __init__(self, cgs: Any):
        self.agents = range(1, cgs.get_number_of_agents() + 1)
        self.actions_of_capacity = {
            row[0]: {normalize_action_token(a) for a in row[1:]}
            for row in cgs.action_capacities
        }
        self.capacities = {
            int(row[0]): list(row[1:]) for row in cgs.get_capacities_assignment()
        }
        self.assignments = list(
            itertools.product(*(self.capacities[a] for a in self.agents))
        )
        self.moves = self._expand_transitions(cgs)
        self._allowed: dict[Move, int] = {}

    def _expand_transitions(self, cgs: Any) -> dict[str, list[tuple[Move, str]]]:
        agent_actions = [
            sorted(
                set().union(*(self.actions_of_capacity[c] for c in self.capacities[a]))
            )
            for a in self.agents
        ]
        moves: dict[str, list[tuple[Move, str]]] = {}
        for i, row in enumerate(cgs.graph):
            out = moves.setdefault(str(cgs.get_state_name_by_index(i)), [])
            for j, cell in enumerate(row):
                if cell == 0:
                    continue
                target = str(cgs.get_state_name_by_index(j))
                joints = parse_joint_action_cell(str(cell), len(self.agents)) or [
                    ["*"] * len(self.agents)
                ]
                for joint in joints:
                    choices = [
                        agent_actions[k] if token == "*" else [token]
                        for k, token in enumerate(joint)
                    ]
                    out.extend((move, target) for move in itertools.product(*choices))
        return moves

    def allowed(self, move: Move) -> int:
        """Assignments under which every agent may play its action in `move`."""
        if move not in self._allowed:
            mask = 0
            for i, kappa in enumerate(self.assignments):
                if all(
                    action in self.actions_of_capacity[capacity]
                    for action, capacity in zip(move, kappa, strict=True)
                ):
                    mask |= 1 << i
            self._allowed[move] = mask
        return self._allowed[move]


class CoalitionGame:
    """The game of one coalition with fixed member capacities."""

    def __init__(
        self, model: CapModel, coalition: list[int], capacities: tuple[str, ...]
    ):
        self.model = model
        self.coalition = coalition
        self.member_actions = {
            a: model.actions_of_capacity[c]
            for a, c in zip(coalition, capacities, strict=True)
        }
        self._choices: dict[str, list[list[tuple[int, str]]]] = {}

    def start(self, state: str) -> Node:
        return (state, frozenset({(1 << len(self.model.assignments)) - 1}))

    def _choices_at(self, state: str) -> list[list[tuple[int, str]]]:
        """Per coalition move allowed by the member capacities, the (allowed
        assignments, target) of each joint move that extends it."""
        if state not in self._choices:
            grouped: dict[Move, list[tuple[int, str]]] = {}
            for move, target in self.model.moves[state]:
                choice = tuple(move[a - 1] for a in self.coalition)
                if all(
                    b in self.member_actions[a]
                    for a, b in zip(self.coalition, choice, strict=True)
                ):
                    grouped.setdefault(choice, []).append(
                        (self.model.allowed(move), target)
                    )
            self._choices[state] = list(grouped.values())
        return self._choices[state]

    def successors(self, node: Node) -> list[list[Node]]:
        """For each coalition move, the nodes the opponents can lead to."""
        state, plays = node
        result = []
        for extensions in self._choices_at(state):
            targets: dict[str, set[Play]] = {}
            for allowed, target in extensions:
                for play in plays:
                    if play & allowed:
                        targets.setdefault(target, set()).add(play & allowed)
            if targets:
                result.append([(t, frozenset(p)) for t, p in targets.items()])
        return result


def _explore(
    game: CoalitionGame, starts: Iterable[Node], settle: Callable[[Node], Node | None]
) -> Graph:
    """Nodes reachable from the settled `starts` through `settle`, which drops
    decided plays (None: lost)."""
    graph: Graph = {}
    stack = list(starts)
    while stack:
        node = stack.pop()
        if node in graph:
            continue
        options = []
        if node[1]:
            for targets in game.successors(node):
                settled = [settle(t) for t in targets]
                options.append(settled)
                stack.extend(t for t in settled if t is not None and t not in graph)
        graph[node] = options
    return graph


def _forces(options: list[list[Node | None]], nodes: set[Node]) -> bool:
    """Some coalition move leads only to `nodes`."""
    return any(all(t in nodes for t in targets) for targets in options)


def _winning_starts(
    game: CoalitionGame,
    states: Iterable[str],
    settle: Callable[[Node], Node | None],
    reach: bool,
) -> set[str]:
    """States whose start node wins: a node with no plays left has won; with
    `reach` the others must get there (least fixpoint), else stay safe forever
    (greatest fixpoint)."""
    starts = {s: settle(game.start(s)) for s in states}
    graph = _explore(game, (n for n in starts.values() if n is not None), settle)
    if reach:
        won = least_fixpoint(
            {n for n in graph if not n[1]},
            lambda w: w | {n for n, options in graph.items() if _forces(options, w)},
        )
    else:
        won = greatest_fixpoint(
            set(graph),
            lambda w: {n for n in w if not n[1] or _forces(graph[n], w)},
        )
    return {s for s, node in starts.items() if node in won}


def until_states(
    game: CoalitionGame, states: Iterable[str], stay: StateTest, goal: StateTest
) -> set[str]:
    """States from which the coalition can force `stay` until `goal`."""

    def settle(node: Node) -> Node | None:
        if goal(node[0]):
            return (node[0], frozenset())
        return node if stay(node[0]) else None

    return _winning_starts(game, states, settle, reach=True)


def release_states(
    game: CoalitionGame, states: Iterable[str], release: StateTest, keep: StateTest
) -> set[str]:
    """States from which the coalition can keep `keep` up to and including a
    `release` state, or forever."""

    def settle(node: Node) -> Node | None:
        if not keep(node[0]):
            return None
        return (node[0], frozenset()) if release(node[0]) else node

    return _winning_starts(game, states, settle, reach=False)


def next_states(
    game: CoalitionGame, states: Iterable[str], goal: StateTest
) -> set[str]:
    """States from which the coalition can force `goal` in the next state."""
    return {
        s
        for s in states
        if any(
            all(goal(t[0]) for t in targets)
            for targets in game.successors(game.start(s))
        )
    }
