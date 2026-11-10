from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum, auto


class AcceptanceKind(Enum):
    """Büchi, co-Büchi, or parity."""

    BUCHI = auto()
    CO_BUCHI = auto()
    PARITY = auto()


class ParityKind(Enum):
    MAX = auto()
    MIN = auto()


class ParityStyle(Enum):
    EVEN = auto()
    ODD = auto()


@dataclass(frozen=True)
class AcceptanceCondition:
    """A Büchi, co-Büchi or parity condition, with a priority per transition
    `(source, label, target)`."""

    kind: AcceptanceKind
    parity_kind: ParityKind | None = None
    parity_style: ParityStyle | None = None
    priorities: dict[tuple[Hashable, Hashable, Hashable], int] = field(
        default_factory=dict
    )


def priority_from_mark(mark) -> int | None:
    """The priority of a Spot edge mark, or None if the edge is unmarked."""
    colors = list(mark.sets())
    if not colors:
        return None
    if len(colors) > 1:
        raise ValueError(
            f"edge has {len(colors)} acceptance marks {colors}; automata's "
            "per-transition priority model (Büchi/co-Büchi/parity) expects at most one"
        )
    return colors[0]
