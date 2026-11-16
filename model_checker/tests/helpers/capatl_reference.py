"""Brute-force CapATL checker for tests, searching strategies up to a depth bound:
None means the bound cut a play, here or in a nested operator, before it settled."""

from __future__ import annotations

import itertools
import re
from collections.abc import Iterable
from typing import Any, NamedTuple

from model_checker.algorithms.explicit.shared.atom_utils import (
    boolean_constant,
    states_where_prop_holds,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    normalize_action_token,
    parse_joint_action_cell,
)
from model_checker.parsers.syntax_patterns import (
    CAPATL_COALITION_TOKEN,
    spelling_to_symbol,
)

CONNECTIVES = spelling_to_symbol("NOT", "AND", "OR", "IMPLIES")
STRATEGIC_PATTERN = re.compile(rf"^{CAPATL_COALITION_TOKEN}([XFGUR])$")

Path = tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]  # states, joint actions
Assignment = tuple[str, ...]  # capacity of agent 1..n
Position = tuple[str, frozenset[frozenset[Assignment]]]  # state, C(h) per history

WIN, LOSE, OPEN = "win", "lose", "open"


class _Game(NamedTuple):
    """One strategic operator: its node, temporal operator, coalition, and whether a
    repeated position settles it (no K reads the play)."""

    node: Any
    op: str
    coalition: list[int]
    tracks_positions: bool


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


def _reads_knowledge(node: Any) -> bool:
    """Whether node has a K outside any nested strategic operator, which starts its
    own play and so does not read this one."""
    if isinstance(node, str):
        return False
    op = node[0]
    if op.startswith("K"):
        return True
    if op.startswith("<{"):
        return False
    return any(_reads_knowledge(child) for child in node[1:])


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
        self.gamma = {
            row[0]: {normalize_action_token(a) for a in row[1:]}
            for row in cgs.action_capacities
        }
        self.assignments: list[Assignment] = list(
            itertools.product(*(self.capacities[a] for a in self.agents))
        )
        self.transitions = self._transitions()
        self._strategic_memo: dict[tuple[Any, str], bool | None] = {}

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
                labels = parse_joint_action_cell(str(cell), self.n) or [["*"] * self.n]
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
        if isinstance(node, str):
            constant = boolean_constant(node)
            if constant is None:
                raise ValueError(f"unknown capacity formula leaf {node!r}")
            return constant
        op = CONNECTIVES.get(node[0], node[0])
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
            constant = boolean_constant(node)
            if constant is not None:
                return constant
            holds = states_where_prop_holds(self.cgs, node)
            if holds is None:
                raise ValueError(f"unknown atom {node!r}")
            return last in holds
        op = CONNECTIVES.get(node[0], node[0])
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
            key = (node, last)
            if key not in self._strategic_memo:
                self._strategic_memo[key] = self.strategic(node, last)
            return self._strategic_memo[key]
        raise ValueError(f"unknown operator {op!r}")

    def _status(self, op: str, node: Any, path: Path, assume: bool) -> str:
        """Whether an outcome prefix already satisfies or violates the temporal part,
        reading an operand the depth bound left open as `assume`."""

        def holds(operand: Any) -> bool:
            value = self.state_formula(operand, path)
            return assume if value is None else value

        if op == "X":
            if len(path[0]) == 1:
                return OPEN
            return WIN if holds(node[1]) else LOSE
        if op in ("F", "U"):
            if holds(node[-1]):
                return WIN
            return OPEN if op == "F" or holds(node[1]) else LOSE
        if op in ("G", "R"):
            if not holds(node[-1]):
                return LOSE
            return WIN if op == "R" and holds(node[1]) else OPEN
        raise ValueError(f"unknown temporal operator {op!r}")

    def strategic(self, node: Any, state: str) -> bool | None:
        """<Y>psi at state: some capacity per member, fixed for the whole strategy, wins."""
        # Temporal operators are monotone, so open values read as false or as true bound it.
        match = STRATEGIC_PATTERN.match(node[0])
        assert match is not None, node[0]
        coalition = sorted(int(a) for a in match.group(1).split(","))
        game = _Game(
            node,
            match.group(2),
            coalition,
            not any(_reads_knowledge(operand) for operand in node[1:]),
        )
        start: Path = ((state,), ())

        def wins(assume: bool) -> bool:
            return any(
                self._search(
                    game,
                    dict(zip(coalition, caps, strict=True)),
                    [start],
                    self.depth,
                    assume,
                    (),
                )
                for caps in itertools.product(*(self.capacities[a] for a in coalition))
            )

        if wins(False):
            return True
        return None if wins(True) else False

    def _search(
        self,
        game: _Game,
        caps: dict[int, str],
        histories: list[Path],
        depth: int,
        assume: bool,
        trail: tuple[Position, ...],
    ) -> bool:
        """Whether one coalition move per state sequence wins every history; `trail`
        holds the positions of the play so far."""
        coalition = game.coalition
        # The coalition sees only states and its own moves, so these histories share a move.
        open_histories = []
        for path in histories:
            status = self._status(game.op, game.node, path, assume)
            if status == LOSE:
                return False
            if status == OPEN:
                open_histories.append(path)
        if not open_histories:
            return True

        state = open_histories[0][0][-1]
        # Without K the future depends only on the state and the assignments still
        # allowed, so a repeated position loops forever: G and R win, F and U lose.
        if game.tracks_positions:
            position = (
                state,
                frozenset(
                    frozenset(self.compatible_assignments(h)) for h in open_histories
                ),
            )
            if position in trail:
                return game.op in ("G", "R")
            trail = trail + (position,)
        if depth == 0:
            return assume
        moves = self.transitions[state]
        allowed = [
            sorted({al[a - 1] for al, _ in moves} & self.gamma[caps[a]])
            for a in coalition
        ]

        def outcomes(beta: tuple[str, ...]) -> dict[str, list[Path]]:
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
            return successors

        return any(
            all(
                self._search(game, caps, group, depth - 1, assume, trail)
                for group in successors.values()
            )
            for successors in map(outcomes, itertools.product(*allowed))
            if successors
        )

    def satisfying_states(self, formula: Any) -> dict[str, bool | None]:
        """Value of the formula at each state, read as the path of length one."""
        return {
            str(s): self.state_formula(formula, ((str(s),), ()))
            for s in self.cgs.states
        }
