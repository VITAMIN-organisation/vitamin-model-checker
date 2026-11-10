"""NatATL models need an idle move: every state must let each agent play I (or IDLE)."""

import pytest

from model_checker.parsers.game_structures.cgs.cgs_validation import (
    validate_nat_idle_requirements,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "graph",
    [
        [["IDLE|IDLE", "A|B"], [0, "I|I"]],
        [["I|I", 0], [0, "I|I"]],
    ],
)
def test_matrix_with_an_idle_move_in_every_row_is_accepted(graph):
    """`I` and `IDLE` both count as the idle action."""
    validate_nat_idle_requirements(graph, 2)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("graph", "message"),
    [
        ([[0, 0, 0], ["I|I|I", "I|I|Z", "I|Z|Z"]], "All elements in row 0 are 0"),
        ([[], ["I|I|I", "I|I|Z", "I|Z|Z"]], "All elements in row 0 are 0"),
        ([["Z|Z|Z", "Z|Z|Z", "Z|Z|Z"]], "Idle error in row 0"),
        ([["IDLE|Z|Z", "Z|Z|Z", "Z|Z|Z"]], "Idle error in row 0"),
    ],
)
def test_row_without_moves_or_without_idle_is_refused(graph, message):
    """A state with no move, or one where some agent cannot idle, names its row."""
    with pytest.raises(ValueError, match=message):
        validate_nat_idle_requirements(graph, 3)
