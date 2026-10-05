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
    """A Büchi, co-Büchi, or parity acceptance condition.

    `priorities` is keyed per-transition (`(source, label, target)`),
    matching Spot's own per-edge acceptance marks. `PARITY` also needs
    `parity_kind`/`parity_style`.
    """

    kind: AcceptanceKind
    parity_kind: ParityKind | None = None
    parity_style: ParityStyle | None = None
    priorities: dict[tuple[Hashable, Hashable, Hashable], int] = field(default_factory=dict)


def priority_from_mark(mark) -> int | None:
    """Convert a Spot edge acceptance mark to its single priority, or `None` if unmarked.

    Raises:
        ValueError: if `mark` carries more than one color.
    """
    colors = list(mark.sets())
    if not colors:
        return None
    if len(colors) > 1:
        raise ValueError(
            f"edge has {len(colors)} acceptance marks {colors}; automata's "
            "per-transition priority model (Büchi/co-Büchi/parity) expects at most one"
        )
    return colors[0]
