"""Birelational Matrix parser for ICTL."""

from model_checker.parsers.game_structures.cgs.cgs import CGS
import numpy as np


class BirelationalMatrix(CGS):
    """Parser and in-memory representation for an ICTL birelational model file."""

    def _parse_lines(self, lines: list[str]) -> None:
        super()._parse_lines(lines)
        if getattr(self, "number_of_agents", None) is None:
            self.number_of_agents = 1
        if hasattr(self, "graph") and self.graph:
            self.graph = np.array(self.graph, dtype=object)
        if hasattr(self, "matrix_prop") and self.matrix_prop:
            self.matrix_prop = np.array(self.matrix_prop, dtype=int)

    def validate_model_structure(self) -> None:
        super().validate_model_structure()
        from model_checker.algorithms.explicit.ICTL.util.validation import (
            check_conditions_hold,
        )

        check_conditions_hold(self)
