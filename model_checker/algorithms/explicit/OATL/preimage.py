"""Demon pre-image of OATL: states where the Demon, within its budget, can force a successor into a target set."""

import math
from collections.abc import Iterable
from dataclasses import dataclass

from model_checker.algorithms.explicit.shared.cost_utils import (
    cost_to_scalar,
    edge_cell_cost,
)
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    AGENT_ACTION_SEPARATOR,
    get_agents_from_coalition,
)


@dataclass(frozen=True)
class JointTransition:
    """One joint action from a state, its target, and the Demon's cost to erase it."""

    tokens: tuple[str, ...]
    target: int
    cost: float | None


@dataclass(frozen=True)
class CoalitionMove:
    """A coalition move at one state: its successors and the cost to erase all its joint actions.

    `uncosted_count` counts its joint actions that have no cost in the model.
    """

    targets: frozenset[int]
    erase_cost: float
    uncosted_count: int


def _erase_cost(cgs, action: str, state_name: str) -> float | None:
    try:
        costs = cgs.get_cost_for_action(action, state_name)
    except KeyError:
        return None
    # A cost vector (one entry per agent) is summed into one Demon cost.
    return cost_to_scalar(costs)


def _joint_transitions(
    cgs, edges_only: bool, agents: int
) -> list[tuple[JointTransition, ...]]:
    """Expand every transition cell once, with its cost when the model gives one.

    A `Transition_With_Costs` cell is an edge with its cost and no actions, as in
    the Kripke models of OL (ECAI 2023, Definition 2). It becomes one joint
    action that all agents choose together.
    """
    per_state = []
    for source, row in enumerate(cgs.graph):
        state_name = cgs.get_state_name_by_index(source)
        transitions = []
        for target, cell in enumerate(row):
            if cell in (0, "0"):
                continue
            if edges_only:
                transitions.append(
                    JointTransition(
                        tokens=(f"edge{target}",) * agents,
                        target=target,
                        cost=edge_cell_cost(cell),
                    )
                )
                continue
            for action in cgs.build_action_list(cell):
                transitions.append(
                    JointTransition(
                        tokens=tuple(action.split(AGENT_ACTION_SEPARATOR)),
                        target=target,
                        cost=_erase_cost(cgs, action, state_name),
                    )
                )
        per_state.append(tuple(transitions))
    return per_state


def _coalition_moves(
    transitions: Iterable[JointTransition], agent_positions: tuple[int, ...]
) -> tuple[CoalitionMove, ...]:
    """Group joint actions by the coalition's part; each group is one A-action."""
    targets: dict[tuple[str, ...], set[int]] = {}
    costs: dict[tuple[str, ...], dict[tuple[str, ...], float | None]] = {}
    for transition in transitions:
        move = tuple(transition.tokens[i] for i in agent_positions)
        targets.setdefault(move, set()).add(transition.target)
        costs.setdefault(move, {})[transition.tokens] = transition.cost
    return tuple(
        CoalitionMove(
            targets=frozenset(targets[move]),
            erase_cost=sum(c for c in costs[move].values() if c is not None),
            uncosted_count=sum(c is None for c in costs[move].values()),
        )
        for move in targets
    )


class DemonicPreimage:
    """OATL pre-image for one model check; transitions and A-actions are built once."""

    def __init__(self, cgs):
        self._edges_only = getattr(cgs, "usesCostsInsteadOfActions", False)
        self._agents = cgs.get_number_of_agents()
        self._transitions = _joint_transitions(cgs, self._edges_only, self._agents)
        self._moves_by_coalition: dict[str, list[tuple[CoalitionMove, ...]]] = {}
        # The Demon never erases a state's only joint action, so its cost is unused.
        self.uncosted = [
            f"{AGENT_ACTION_SEPARATOR.join(t.tokens)} at {cgs.get_state_name_by_index(s)}"
            for s, transitions in enumerate(self._transitions)
            if len(transitions) > 1
            for t in transitions
            if t.cost is None
        ]

    def _moves(self, coalition: str) -> list[tuple[CoalitionMove, ...]]:
        if coalition not in self._moves_by_coalition:
            positions = tuple(
                sorted(int(agent) - 1 for agent in get_agents_from_coalition(coalition))
            )
            if self._edges_only and len(positions) != self._agents:
                raise ValueError(
                    f"[MODEL] Coalition <{coalition}> needs the agents' actions, but "
                    "a Transition_With_Costs model gives only edge costs; use "
                    "Transition with Costs_for_actions"
                )
            self._moves_by_coalition[coalition] = [
                _coalition_moves(transitions, positions)
                for transitions in self._transitions
            ]
        return self._moves_by_coalition[coalition]

    def __call__(
        self,
        coalition: str,
        bound: int,
        target: set[int],
        uncosted_cost: float = math.inf,
    ) -> set[int]:
        """States where the Demon, with budget `bound`, forces some successor into `target`.

        Joint actions without a cost in the model cost `uncosted_cost` each.
        """
        result = set()
        for state, moves in enumerate(self._moves(coalition)):
            to_erase = [m for m in moves if m.targets.isdisjoint(target)]
            if len(to_erase) == len(moves):
                continue
            cost = sum(m.erase_cost for m in to_erase)
            uncosted = sum(m.uncosted_count for m in to_erase)
            if uncosted:
                cost += uncosted_cost * uncosted
            if cost <= bound:
                result.add(state)
        return result
