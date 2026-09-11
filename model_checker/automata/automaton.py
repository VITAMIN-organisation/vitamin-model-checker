from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

from .acceptance import (
    AcceptanceCondition,
    AcceptanceKind,
    ParityKind,
    ParityStyle,
    priority_from_mark,
)

try:
    import spot
except ImportError:
    spot = None


@dataclass
class Automaton:
    """Wraps a `spot.twa_graph` automaton."""

    graph: Any

    @staticmethod
    def from_ltl(formula: str) -> Automaton:
        """Build a deterministic, max-odd parity automaton from an LTL formula.

        `change_parity` runs unconditionally (its orientation is rarely
        already max-odd), a safe no-op otherwise.

        Raises:
            ImportError: if Spot isn't importable.
        """
        if spot is None:
            raise ImportError("Spot is required for Automaton.from_ltl() "
                               "(pip install spottl on Linux, or conda-forge elsewhere; "
                               "see docs/ATL_STAR/algorithm.md)")

        graph = spot.translate(formula, "parity", "deterministic")
        graph = spot.change_parity(graph, spot.parity_kind_max, spot.parity_style_odd)
        return Automaton(graph=graph)

    def acceptance_condition(self) -> AcceptanceCondition:
        """Classify this automaton's acceptance condition.

        `priorities` here is keyed by this automaton's own state numbers
        `product()` builds its own instead of reusing this one.

        Raises:
            ValueError: if the acceptance is neither Büchi, co-Büchi, nor parity.
        """
        if spot is None:
            raise ImportError("Spot is required for Automaton.acceptance_condition() "
                               "(pip install spottl on Linux, or conda-forge elsewhere; "
                               "see docs/ATL_STAR/algorithm.md)")

        return self._classify(self._priorities())

    def _classify(self, priorities: dict[tuple[Hashable, Hashable, Hashable], int]) -> AcceptanceCondition:
        """Classify this automaton's acceptance kind/orientation, attaching
        `priorities` as given rather than always recomputing our own, lets
        `product()` reuse this without paying for `_priorities()` twice."""
        acc = self.graph.acc()

        if acc.is_buchi():
            return AcceptanceCondition(kind=AcceptanceKind.BUCHI, priorities=priorities)
        if acc.is_co_buchi():
            return AcceptanceCondition(kind=AcceptanceKind.CO_BUCHI, priorities=priorities)

        is_parity, is_max, is_odd = acc.is_parity()
        if is_parity:
            return AcceptanceCondition(
                kind=AcceptanceKind.PARITY,
                parity_kind=ParityKind.MAX if is_max else ParityKind.MIN,
                parity_style=ParityStyle.ODD if is_odd else ParityStyle.EVEN,
                priorities=priorities,
            )

        raise ValueError(
            f"unsupported acceptance condition {acc.name()!r}: automata is "
            "deliberately restricted to Büchi/co-Büchi/parity"
        )

    def _priorities(self) -> dict[tuple[Hashable, Hashable, Hashable], int]:
        """Collect this automaton's own per-transition priorities."""
        bdict = self.graph.get_dict()
        priorities: dict[tuple[Hashable, Hashable, Hashable], int] = {}
        for state in range(self.graph.num_states()):
            for edge in self.graph.out(state):
                priority = priority_from_mark(edge.acc)
                if priority is not None:
                    label = str(spot.bdd_to_formula(edge.cond, bdict))
                    priorities[(edge.src, label, edge.dst)] = priority
        return priorities
