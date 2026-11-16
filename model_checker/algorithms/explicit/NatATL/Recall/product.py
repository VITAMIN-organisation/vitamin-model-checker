"""The model restricted to a NatATL Recall profile: a CGS whose states pair a model
state with how far each rule's pattern has matched the history so far.

The CGS is finite, so CTL on it covers histories of every length.
"""

from collections import deque

import numpy as np

from model_checker.algorithms.explicit.NatATL.Recall.strategies import (
    RecallStrategy,
)
from model_checker.algorithms.explicit.shared.natural_strategies import (
    ANY_ACTION,
    keep_joint_actions,
)
from model_checker.parsers.game_structures.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    wildcard_joint_profile,
)

# A model state and, per coalition member and rule, the matched pattern positions.
Configuration = tuple[str, tuple[tuple[frozenset[int], ...], ...]]


def _read(profile, history_state: str, matches=None):
    """Pattern positions after reading `history_state`; from the start when
    `matches` is None."""
    return tuple(
        tuple(
            (
                pattern.start(history_state)
                if matches is None
                else pattern.step(matches[m][r], history_state)
            )
            for r, (pattern, _) in enumerate(strategy.rules)
        )
        for m, strategy in enumerate(profile)
    )


def _chosen_action(strategy: RecallStrategy, positions) -> str:
    """The action of the first rule whose pattern matches the history; the last
    rule, (true*, IDLE), matches every history."""
    return next(
        action
        for (pattern, action), matched in zip(strategy.rules, positions, strict=True)
        if pattern.accepts(matched)
    )


def _moves(cgs, parsed_rows, agents, profile, config: Configuration):
    """The (target state, matrix cell) pairs left in `config` by the profile."""
    state, matches = config
    wanted = [
        (agent - 1, _chosen_action(strategy, positions))
        for agent, strategy, positions in zip(agents, profile, matches, strict=True)
    ]
    row = parsed_rows[cgs.state_to_index[state]]
    for target, cell in zip(cgs.states, row, strict=True):
        kept = keep_joint_actions(cell, wanted)
        # A profile with `*` for every agent is the same edge to target as a bare `*`.
        if kept == ANY_ACTION:
            yield str(target), wildcard_joint_profile(cgs.get_number_of_agents())
        elif kept != 0 and kept != "0":
            yield str(target), kept


def build_product(
    cgs, parsed_rows, agents: list[int], profile: tuple[RecallStrategy, ...]
) -> CGS:
    """The CGS of the configurations reachable from the initial state under the
    profile, labelled like their model state; its initial state is `c0`."""
    initial = str(cgs.initial_state)
    start: Configuration = (initial, _read(profile, initial))
    index = {start: 0}
    edges: list[dict[int, str]] = []
    queue = deque([start])
    while queue:
        config = queue.popleft()
        out: dict[int, str] = {}
        for target, cell in _moves(cgs, parsed_rows, agents, profile, config):
            nxt: Configuration = (target, _read(profile, target, config[1]))
            if nxt not in index:
                index[nxt] = len(index)
                queue.append(nxt)
            out[index[nxt]] = cell
        edges.append(out)

    size = len(index)
    product = CGS()
    product.graph = [[out.get(j, 0) for j in range(size)] for out in edges]
    product.states = np.array([f"c{i}" for i in range(size)])
    product.initial_state = "c0"
    product.number_of_agents = cgs.number_of_agents
    # CTL only reads these; proposition lookup needs the model's array as it is.
    product.actions = cgs.actions
    product.atomic_propositions = cgs.atomic_propositions
    product.matrix_prop = [
        list(cgs.matrix_prop[cgs.state_to_index[state]]) for state, _ in index
    ]
    return product
