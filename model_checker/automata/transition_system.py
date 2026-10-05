from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field


@dataclass
class TransitionSystem:
    """A labeled transition system: states, alphabet, and transition relation."""

    states: set[Hashable] = field(default_factory=set)
    initial_states: set[Hashable] = field(default_factory=set)
    alphabet: set[Hashable] = field(default_factory=set)
    transitions: dict[tuple[Hashable, Hashable], set[Hashable]] = field(default_factory=dict)

    def add_state(self, state: Hashable, *, initial: bool = False) -> None:
        """Add `state`, optionally marking it as an initial state."""
        self.states.add(state)
        if initial:
            self.initial_states.add(state)

    def add_transition(self, source: Hashable, symbol: Hashable, target: Hashable) -> None:
        """Add a transition, implicitly adding `source`/`target` as states."""
        self.add_state(source)
        self.add_state(target)
        self.alphabet.add(symbol)
        self.transitions.setdefault((source, symbol), set()).add(target)

    def successors(self, state: Hashable, symbol: Hashable) -> set[Hashable]:
        """The set of states reachable from `state` on `symbol`."""
        return self.transitions.get((state, symbol), set())
