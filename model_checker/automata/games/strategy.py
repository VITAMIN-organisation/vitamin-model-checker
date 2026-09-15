from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass, field
from typing import cast


@dataclass
class Strategy:
    """A positional strategy: state -> action.

    `action` is generically `Hashable`, not necessarily a joint action:
    `games/_attractor_oracle.py` produces plain-symbol strategies,
    `arena.py`-based games produce joint actions.
    """

    choices: dict[Hashable, Hashable] = field(default_factory=dict)

    def move(self, state: Hashable) -> Hashable | None:
        """The action this strategy picks at `state`, or `None` if unset."""
        return self.choices.get(state)

    def project(self, player: Hashable) -> Strategy:
        """Project a joint-action strategy onto one player's own actions.

        Only valid when `choices` holds `arena.py`'s `JointAction` shape.
        """
        return Strategy({
            state: dict(cast(Iterable[tuple[Hashable, Hashable]], action))[player]
            for state, action in self.choices.items()
        })
