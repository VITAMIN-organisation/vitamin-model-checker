"""Fuzzy Concurrent Game Structure (fuzzyCGS) parser.

A CGS whose Labelling cells are truth degrees in [0, 1]; used by ATLF.
"""

import math

from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS


class FuzzyCGS(CGS):
    """A fuzzyCGS model: the CGS sections, with each label a real number in [0, 1]."""

    def parse_labelling_row(self, row: list[str], row_index: int) -> list[float]:
        """One Labelling row as floats. A value outside [0, 1] is rejected because
        ATLF reads it as a truth degree and computes `!p` as `1 - p`."""
        values = []
        for col_index, item in enumerate(row):
            try:
                value = float(item)
            except ValueError:
                value = math.nan
            if not 0.0 <= value <= 1.0:
                raise cgs_parser.invalid_label_error(
                    item,
                    row_index,
                    col_index,
                    "A fuzzyCGS labelling matrix must contain numbers between 0 and 1.",
                )
            values.append(value)
        return values
