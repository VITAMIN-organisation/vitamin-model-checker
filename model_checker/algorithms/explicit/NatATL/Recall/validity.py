"""Where the histories matching a NatATL Recall pattern end: a rule's action must be
available at each of those states."""

from collections import deque

from model_checker.algorithms.explicit.NatATL.Recall.patterns import Pattern
from model_checker.algorithms.explicit.shared.natural_strategies import ANY_ACTION


def successors(states, parsed_rows) -> dict[str, frozenset[str]]:
    """The states each state has a transition to; parsed_rows comes from parse_rows."""
    names = [str(s) for s in states]
    return {
        source: frozenset(
            target
            for target, cell in zip(names, row, strict=True)
            if cell == ANY_ACTION or (isinstance(cell, list) and cell)
        )
        for source, row in zip(names, parsed_rows, strict=True)
    }


def last_states(pattern: Pattern, succ: dict[str, frozenset[str]]) -> frozenset[str]:
    """The last states of the histories that match `pattern`, over histories that
    start in any state."""
    start = {(state, pattern.start(state)) for state in succ}
    seen = {pair for pair in start if pair[1]}
    queue = deque(seen)
    while queue:
        state, positions = queue.popleft()
        for target in succ[state]:
            pair = (target, pattern.step(positions, target))
            if pair[1] and pair not in seen:
                seen.add(pair)
                queue.append(pair)
    return frozenset(state for state, positions in seen if pattern.accepts(positions))
