"""ICTL frames are checked when loaded: a bad frame gives wrong answers, so it must be refused.

Cells mark the transition relation R and the information preorder P. The preorder
must be a partial order, R must be serial, R and P must satisfy C1 and C2, and a
proposition true at a state stays true at every state above it.
"""

import numpy as np
import pytest

from model_checker.algorithms.explicit.ICTL.util.validation import check_conditions_hold
from model_checker.parsers.game_structures.birelational_matrix.birelational_matrix import (
    BirelationalMatrix,
)


def _frame(graph, labels=None, propositions=("p",)):
    model = BirelationalMatrix()
    model.graph = np.array(graph, dtype=object)
    model.states = [f"s{i}" for i in range(model.graph.shape[0])]
    model.atomic_propositions = list(propositions)
    model.matrix_prop = np.array(labels if labels is not None else [[1]] * len(graph))
    return model


@pytest.mark.unit
@pytest.mark.parametrize(
    "frame",
    [
        _frame([["P,R", "0"], ["0", "P,R"]]),
        _frame([["P,R", "P"], ["0", "P,R"]], labels=[[0], [1]]),
    ],
    ids=["two_isolated_states", "p_appears_higher_up"],
)
def test_valid_frame_is_accepted(frame):
    """A label may appear higher in the preorder; it may not vanish."""
    check_conditions_hold(frame)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (_frame([["P,R", "0", "0"], ["0", "P,R", "0"]]), "not squared"),
        (_frame([["0", "0"], ["P,R", "P,R"]]), "serial"),
        (_frame([["P", "P,R"], ["P,R", "0"]]), "reflective"),
        (_frame([["P,R", "P"], ["P", "P,R"]]), "antisymmetric"),
        (
            _frame([["P,R", "P", "0"], ["0", "P,R", "P"], ["0", "0", "P,R"]]),
            "transitive",
        ),
        (
            _frame([["P,R", "P", "R"], ["0", "P,R", "0"], ["0", "0", "P,R"]]),
            "condition C1",
        ),
        (
            _frame([["P,R", "P", "0"], ["0", "P,R", "R"], ["0", "0", "P,R"]]),
            "condition C2",
        ),
        (_frame([["P,R", "P"], ["0", "P,R"]], labels=[[1], [0]]), "Labeling function"),
        (_frame([["P,R"]], propositions=()), "no atoms"),
        (_frame([["P,R"]], labels=[[2]]), "boolean proposition"),
    ],
    ids=[
        "not_square",
        "state_without_successor",
        "preorder_not_reflexive",
        "preorder_not_antisymmetric",
        "preorder_not_transitive",
        "c1_s1_above_s0_cannot_follow_its_move",
        "c2_s0_below_s1_cannot_follow_its_move",
        "p_lost_going_up",
        "no_propositions",
        "label_not_0_or_1",
    ],
)
def test_invalid_frame_is_refused_with_the_broken_condition(frame, message):
    """Each condition has its own message, so the user knows what to fix."""
    with pytest.raises(AssertionError, match=message):
        check_conditions_hold(frame)
