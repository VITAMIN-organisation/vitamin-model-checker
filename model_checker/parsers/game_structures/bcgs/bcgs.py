"""BCGS (Birelational Concurrent Game Structure) model parser for IATL."""

import numpy as np

from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cgs import cgs_parser


class BCGS(CGS):
    """Parser and in-memory representation for an IATL BCGS model file."""

    def __init__(self) -> None:
        super().__init__()

    def _reset_state(self) -> None:
        super()._reset_state()
        self.preorder = np.array([])

    def _parse_lines(self, lines: list[str]) -> None:
        super()._parse_lines(lines)

        preorder_list = []
        current_section = None
        for line in lines:
            stripped = line.strip()
            if stripped == "Preorder":
                current_section = "Preorder"
                continue
            elif (
                stripped in cgs_parser.SECTION_HEADERS
                or stripped in cgs_parser.EXTENSION_SECTION_HEADERS
            ) and stripped != "Preorder":
                current_section = None
                continue

            if current_section == "Preorder" and stripped:
                preorder_list.append([int(x) for x in stripped.split()])

        if preorder_list:
            self.preorder = np.array(preorder_list, dtype=int)
        if hasattr(self, "graph") and self.graph:
            self.graph = np.array(self.graph, dtype=object)
        if hasattr(self, "matrix_prop") and self.matrix_prop:
            self.matrix_prop = np.array(self.matrix_prop, dtype=int)

    def validate_model_structure(self) -> None:
        super().validate_model_structure()
        from model_checker.algorithms.explicit.IATL.util.validation import (
            check_conditions_hold,
        )

        check_conditions_hold(self)
