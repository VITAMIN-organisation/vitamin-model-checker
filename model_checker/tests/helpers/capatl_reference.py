"""Brute-force CapATL checker for tests, sharing no code with the solver.

Paths are explicit, the capacity assignments a path allows and the paths an
agent cannot tell apart are enumerated, and strategies are searched on the
tree of state sequences up to a depth bound. A coalition member's own actions
are a function of the state sequence, so a strategy that picks one joint
coalition move per state sequence is one an agent can play without seeing
the other agents' actions.

Answers are three-valued: True or False only when the bounded search settles
the question, None otherwise. `<Y>F` and `<Y>U` can be proved True, `<Y>G`
and `<Y>R` can be proved False, and `<Y>X` is always settled.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import Any

from model_checker.algorithms.explicit.shared.atom_utils import (
    states_where_prop_holds,
)

Path = tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]  # states, joint actions
Assignment = tuple[str, ...]  # capacity of agent 1..n

WIN, LOSE, OPEN = "win", "lose", "open"


def _and3(values: Iterable[bool | None]) -> bool | None:
    result: bool | None = True
    for v in values:
        if v is False:
            return False
        if v is None:
            result = None
    return result


def _or3(values: Iterable[bool | None]) -> bool | None:
    result: bool | None = False
    for v in values:
        if v is True:
            return True
        if v is None:
            result = None
    return result


def _not3(v: bool | None) -> bool | None:
    return None if v is None else not v


class CapATLReference:
    """Evaluate a parsed CapATL formula on a capCGS model by enumeration."""

    def __init__(self, cgs: Any, depth: int):
        self.cgs = cgs
        self.depth = depth
        self.n = cgs.get_number_of_agents()
        self.agents = range(1, self.n + 1)
        self.capacities = {
            int(row[0]): list(row[1:]) for row in cgs.get_capacities_assignment()
        }
        self.gamma = {row[0]: set(row[1:]) for row in cgs.action_capacities}
        self.assignments: list[Assignment] = list(
            itertools.product(*(self.capacities[a] for a in self.agents))
        )
        self.transitions = self._transitions()
        self._strategic_memo: dict[tuple[int, str], bool | None] = {}

    def _actions_of(self, agent: int) -> set[str]:
        return set().union(*(self.gamma[c] for c in self.capacities[agent]))

    def _transitions(self) -> dict[str, list[tuple[tuple[str, ...], str]]]:
        """(joint action, target) pairs per source state, with `*` expanded."""
        result: dict[str, list[tuple[tuple[str, ...], str]]] = {}
        for i, row in enumerate(self.cgs.graph):
            source = str(self.cgs.get_state_name_by_index(i))
            moves = result.setdefault(source, [])
            for j, cell in enumerate(row):
                if cell == 0:
                    continue
                target = str(self.cgs.get_state_name_by_index(j))
                labels = ["*" * self.n] if cell == "*" else str(cell).split(",")
                for label in labels:
                    choices = [
                        (
                            sorted(self._actions_of(a))
                            if label[a - 1] == "*"
                            else [label[a - 1]]
                        )
                        for a in self.agents
                    ]
                    for alpha in itertools.product(*choices):
                        moves.append((alpha, target))
        return result

    def _compatible(self, alpha: tuple[str, ...], kappa: Assignment) -> bool:
        return all(alpha[a - 1] in self.gamma[kappa[a - 1]] for a in self.agents)

    def compatible_assignments(self, path: Path) -> set[Assignment]:
        """Complete capacity assignments that allow every joint action of the path."""
        _, actions = path
        return {
            k
            for k in self.assignments
            if all(self._compatible(al, k) for al in actions)
        }

    def indistinguishable(self, path: Path, agent: int) -> list[Path]:
        """Paths with the same states and the same actions of `agent`."""
        states, actions = path
        steps = []
        for i, alpha in enumerate(actions):
            steps.append(
                [
                    beta
                    for beta, target in self.transitions[states[i]]
                    if target == states[i + 1] and beta[agent - 1] == alpha[agent - 1]
                ]
            )
        return [(states, tuple(choice)) for choice in itertools.product(*steps)]

    def _capacity_formula(self, node: Any, kappa: Assignment) -> bool:
        if node == "true":
            return True
        if node == "false":
            return False
        op = node[0]
        if op == "is":
            return kappa[int(node[1]) - 1] == node[2]
        if op == "!":
            return not self._capacity_formula(node[1], kappa)
        left = self._capacity_formula(node[1], kappa)
        right = self._capacity_formula(node[2], kappa)
        if op == "&&":
            return left and right
        if op == "||":
            return left or right
        if op == "->":
            return (not left) or right
        raise ValueError(f"unknown capacity operator {op!r}")

    def state_formula(self, node: Any, path: Path) -> bool | None:
        """Whether node holds at the last position of path (a history from the start)."""
        last = path[0][-1]
        if isinstance(node, str):
            if node == "true":
                return True
            if node == "false":
                return False
            holds = states_where_prop_holds(self.cgs, node)
            if holds is None:
                raise ValueError(f"unknown atom {node!r}")
            return last in holds
        op = node[0]
        if op == "!":
            return _not3(self.state_formula(node[1], path))
        if op in ("&&", "||", "->"):
            left = self.state_formula(node[1], path)
            right = self.state_formula(node[2], path)
            if op == "&&":
                return _and3([left, right])
            if op == "||":
                return _or3([left, right])
            return _or3([_not3(left), right])
        if op.startswith("K"):
            agent = int(op[1:])
            return all(
                self._capacity_formula(node[1], kappa)
                for other in self.indistinguishable(path, agent)
                for kappa in self.compatible_assignments(other)
            )
        if op.startswith("<{"):
            key = (id(node), last)
            if key not in self._strategic_memo:
                self._strategic_memo[key] = self.strategic(node, last)
            return self._strategic_memo[key]
        raise ValueError(f"unknown operator {op!r}")

    def _status(self, node: Any, path: Path) -> str | None:
        """Whether an outcome prefix already satisfies or violates the temporal part."""
        op = node[0][node[0].index("}>") + 2 :]
        position = len(path[0])
        if op == "X":
            return (
                OPEN if position == 1 else _decided(self.state_formula(node[1], path))
            )
        if op in ("F", "U"):
            left = "true" if op == "F" else node[1]
            goal = self.state_formula(node[-1], path)
            if goal is True:
                return WIN
            stay = self.state_formula(left, path)
            if goal is False and stay is False:
                return LOSE
            return OPEN if goal is False and stay is True else None
        if op in ("G", "R"):
            release = "false" if op == "G" else node[1]
            keep = self.state_formula(node[-1], path)
            if keep is False:
                return LOSE
            stop = self.state_formula(release, path)
            if keep is True and stop is True:
                return WIN
            return OPEN if keep is True and stop is False else None
        raise ValueError(f"unknown temporal operator {op!r}")

    def strategic(self, node: Any, state: str) -> bool | None:
        """<Y>psi at state: some capacity per member, fixed for the whole strategy, wins."""
        coalition = sorted(int(a) for a in node[0][2 : node[0].index("}")].split(","))
        start: Path = ((state,), ())
        return _or3(
            self._search(
                node,
                coalition,
                dict(zip(coalition, caps, strict=True)),
                [start],
                self.depth,
            )
            for caps in itertools.product(*(self.capacities[a] for a in coalition))
        )

    def _search(
        self,
        node: Any,
        coalition: list[int],
        caps: dict[int, str],
        histories: list[Path],
        depth: int,
    ) -> bool | None:
        """Can one move per state sequence make every outcome of `histories` win?

        All histories share their state sequence. An outcome must be allowed by
        some complete capacity assignment; the coalition plays inside its capacities.
        """
        open_histories = []
        unknown = False
        for path in histories:
            status = self._status(node, path)
            if status == LOSE:
                return False
            if status == OPEN:
                open_histories.append(path)
            elif status is None:
                unknown = True
                open_histories.append(path)
        if not open_histories:
            return None if unknown else True
        if depth == 0:
            return None

        state = open_histories[0][0][-1]
        moves = self.transitions[state]
        allowed = [
            sorted({al[a - 1] for al, _ in moves} & self.gamma[caps[a]])
            for a in coalition
        ]
        results = []
        for beta in itertools.product(*allowed):
            successors: dict[str, list[Path]] = {}
            for states, actions in open_histories:
                for alpha, target in moves:
                    if any(
                        alpha[a - 1] != b for a, b in zip(coalition, beta, strict=True)
                    ):
                        continue
                    path = (states + (target,), actions + (alpha,))
                    if self.compatible_assignments(path):
                        successors.setdefault(target, []).append(path)
            if not successors:
                continue
            results.append(
                _and3(
                    self._search(node, coalition, caps, group, depth - 1)
                    for group in successors.values()
                )
            )
        return _or3(results)

    def satisfying_states(self, formula: Any) -> dict[str, bool | None]:
        """Value of the formula at each state, read as the path of length one."""
        return {
            str(s): self.state_formula(formula, ((str(s),), ()))
            for s in self.cgs.states
        }


def _decided(value: bool | None) -> str | None:
    if value is None:
        return None
    return WIN if value else LOSE
