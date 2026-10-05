from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field

from ..acceptance import AcceptanceCondition
from ..transition_system import TransitionSystem
from .strategy import Strategy


@dataclass
class Game:
    """A turn-based 2-player game: an arena, its player partition, and a
    winning objective. The shared contract between `arena.py` and
    `solver.py`."""

    arena: TransitionSystem = field(default_factory=TransitionSystem)
    player_states: dict[int, set[Hashable]] = field(default_factory=dict)
    objective: AcceptanceCondition | None = None


@dataclass
class GameSolution:
    """A solved game's winning region and strategy, per player. Solvers
    always return both together, never just a region or a boolean."""

    winning_regions: dict[int, set[Hashable]] = field(default_factory=dict)
    strategies: dict[int, Strategy] = field(default_factory=dict)
