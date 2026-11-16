"""Coalition games of CapATL on a capCGS model.

A complete capacity assignment gives one capacity to every agent. Sets of
assignments are bitmasks over `CapModel.assignments`.

The coalition picks one capacity per member before play and keeps it. It sees
the states and its own moves, not the opponents' moves, so it cannot tell
apart plays that differ only there. A game node is (state, plays): `plays`
holds one entry per such play still undecided. An entry keeps the assignments
the play allows (an opponent must keep one capacity along a play, so a play
needs at least one) and, per agent, the assignments that agent still
considers possible: those that allow some play with the same states and the
same moves of that agent. The coalition picks one move per node, which is a
strategy that depends only on what it has seen.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
    parse_joint_action_cell,
)

Move = tuple[str, ...]  # one action per agent, agent 1 first
Knowledge = tuple[
    int, ...
]  # per agent, agent 1 first, the assignments it considers possible
Play = tuple[int, Knowledge]  # the assignments the play allows, and the knowledge
Node = tuple[str, frozenset[Play]]
StateTest = Callable[[str, Knowledge], bool]
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
        self.all_assignments = (1 << len(self.assignments)) - 1
        # Before any move, every agent considers every assignment possible.
        self.initial_knowledge: Knowledge = tuple(
            self.all_assignments for _ in self.agents
        )
        self.moves = self._expand_transitions(cgs)
        self._allowed: dict[Move, int] = {}
        self._learned: dict[tuple[str, str, int, str], int] = {}

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

    def learned(self, state: str, target: str, agent: int, action: str) -> int:
        """Assignments that allow some step from `state` to `target` in which
        `agent` plays `action`: what the agent may still believe after it."""
        key = (state, target, agent, action)
        if key not in self._learned:
            mask = 0
            for move, t in self.moves[state]:
                if t == target and move[agent - 1] == action:
                    mask |= self.allowed(move)
            self._learned[key] = mask
        return self._learned[key]


class CoalitionGame:
    """The game of one coalition with fixed member capacities."""

    def __init__(
        self,
        model: CapModel,
        coalition: list[int],
        capacities: tuple[str, ...],
        observed: frozenset[int],
    ):
        """`observed`: the agents whose knowledge the formula asks about; the
        others keep every assignment, so fewer nodes are built."""
        self.model = model
        self.coalition = coalition
        self.observed = observed
        self.member_actions = {
            a: model.actions_of_capacity[c]
            for a, c in zip(coalition, capacities, strict=True)
        }
        self._choices: dict[str, list[list[tuple[Move, int, str]]]] = {}

    def start(self, state: str) -> Node:
        model = self.model
        return (state, frozenset({(model.all_assignments, model.initial_knowledge)}))

    def _choices_at(self, state: str) -> list[list[tuple[Move, int, str]]]:
        """Per coalition move allowed by the member capacities, the (joint move,
        allowed assignments, target) of each joint move that extends it."""
        if state not in self._choices:
            grouped: dict[Move, list[tuple[Move, int, str]]] = {}
            for move, target in self.model.moves[state]:
                choice = tuple(move[a - 1] for a in self.coalition)
                if all(
                    b in self.member_actions[a]
                    for a, b in zip(self.coalition, choice, strict=True)
                ):
                    grouped.setdefault(choice, []).append(
                        (move, self.model.allowed(move), target)
                    )
            self._choices[state] = list(grouped.values())
        return self._choices[state]

    def _step(
        self, state: str, move: Move, target: str, knowledge: Knowledge
    ) -> Knowledge:
        return tuple(
            (
                known & self.model.learned(state, target, a, move[a - 1])
                if a in self.observed
                else known
            )
            for a, known in zip(self.model.agents, knowledge, strict=True)
        )

    def successors(self, node: Node) -> list[list[Node]]:
        """For each coalition move, the nodes the opponents can lead to."""
        state, plays = node
        result = []
        for extensions in self._choices_at(state):
            targets: dict[str, set[Play]] = {}
            for move, allowed, target in extensions:
                for possible, knowledge in plays:
                    if possible & allowed:
                        targets.setdefault(target, set()).add(
                            (
                                possible & allowed,
                                self._step(state, move, target, knowledge),
                            )
                        )
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


def _winning_nodes(graph: Graph, reach: bool) -> set[Node]:
    """A node with no plays left has won. With `reach`, the nodes from which
    the coalition can force such a node (least fixpoint); otherwise those from
    which it can avoid every lost play forever (greatest fixpoint).

    Worklist form: each coalition move counts its targets not yet decided, so
    every edge is visited once.
    """
    usable: dict[Node, int] = {}  # moves with no lost target, per node
    waiting: dict[tuple[Node, int], int] = {}  # per move, targets still undecided
    predecessors: dict[Node, list[tuple[Node, int]]] = defaultdict(list)
    for node, options in graph.items():
        usable[node] = 0
        for i, targets in enumerate(options):
            if None in targets:
                continue
            reached = {t for t in targets if t is not None}
            usable[node] += 1
            waiting[(node, i)] = len(reached)
            for target in reached:
                predecessors[target].append((node, i))

    if reach:
        decided = {node for node in graph if not node[1]}
    else:  # decided: lost, some play cannot avoid a lost target
        decided = {node for node in graph if node[1] and usable[node] == 0}
    queue = list(decided)
    while queue:
        target = queue.pop()
        for node, i in predecessors[target]:
            if reach:
                waiting[(node, i)] -= 1
                newly = waiting[(node, i)] == 0
            else:
                newly = waiting.pop((node, i), None) is not None
                usable[node] -= newly
                newly = newly and usable[node] == 0
            if newly and node not in decided:
                decided.add(node)
                queue.append(node)
    return decided if reach else set(graph) - decided


def _winning_starts(
    game: CoalitionGame,
    states: Iterable[str],
    settle: Callable[[Node], Node | None],
    reach: bool,
) -> set[str]:
    """States whose start node wins (see `_winning_nodes`)."""
    starts = {s: settle(game.start(s)) for s in states}
    graph = _explore(game, (n for n in starts.values() if n is not None), settle)
    won = _winning_nodes(graph, reach)
    return {s for s, node in starts.items() if node in won}


def until_states(
    game: CoalitionGame, states: Iterable[str], stay: StateTest, goal: StateTest
) -> set[str]:
    """States from which the coalition can force `stay` until `goal`."""

    def settle(node: Node) -> Node | None:
        state, plays = node
        pending = frozenset(p for p in plays if not goal(state, p[1]))
        if all(stay(state, p[1]) for p in pending):
            return (state, pending)
        return None

    return _winning_starts(game, states, settle, reach=True)


def release_states(
    game: CoalitionGame, states: Iterable[str], release: StateTest, keep: StateTest
) -> set[str]:
    """States from which the coalition can keep `keep` up to and including a
    `release` state, or forever."""

    def settle(node: Node) -> Node | None:
        state, plays = node
        if not all(keep(state, p[1]) for p in plays):
            return None
        return (state, frozenset(p for p in plays if not release(state, p[1])))

    return _winning_starts(game, states, settle, reach=False)


def next_states(
    game: CoalitionGame, states: Iterable[str], goal: StateTest
) -> set[str]:
    """States from which the coalition can force `goal` in the next state."""
    return {
        s
        for s in states
        if any(
            all(
                goal(target, knowledge)
                for target, plays in targets
                for _, knowledge in plays
            )
            for targets in game.successors(game.start(s))
        )
    }
