"""Reading an edge's acceptance color from a Spot mark: none, one, or an unsupported several."""

import pytest

from model_checker.automata.acceptance import priority_from_mark


class _Mark:
    def __init__(self, colors):
        self._colors = colors

    def sets(self):
        return self._colors


@pytest.mark.parametrize(("colors", "priority"), [([], None), ([2], 2)])
def test_unmarked_or_single_color_edge(colors, priority):
    """An unmarked edge has no priority; a marked edge has its one color."""
    assert priority_from_mark(_Mark(colors)) == priority


def test_edge_with_two_colors_is_refused():
    """Generalized Büchi can mark an edge twice; the games here use one color per edge."""
    with pytest.raises(ValueError, match="expects at most one"):
        priority_from_mark(_Mark([0, 1]))
