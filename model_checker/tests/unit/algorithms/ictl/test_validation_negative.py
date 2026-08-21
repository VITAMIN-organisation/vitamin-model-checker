"""ICTL birelational model validation negative cases."""

import numpy as np
import pytest

from model_checker.algorithms.explicit.ICTL.util.validation import (
    _check_inference_constraints,
    check_conditions_hold,
)
from model_checker.parsers.game_structures.birelational_matrix.birelational_matrix import (
    BirelationalMatrix,
)


def _minimal_ictl_data(graph):
    model = BirelationalMatrix()
    model.graph = graph
    model.states = [f"s{i}" for i in range(graph.shape[0])]
    model.atomic_propositions = ["p"]
    model.matrix_prop = np.ones((graph.shape[0], 1), dtype=int)
    return model


@pytest.mark.unit
def test_ictl_rejects_non_antisymmetric_preorder():
    graph = np.array([["P,R", "P"], ["P", "P,R"]], dtype=object)
    with pytest.raises(AssertionError, match="antisymmetric"):
        check_conditions_hold(_minimal_ictl_data(graph))


@pytest.mark.unit
def test_ictl_rejects_c1_violation():
    # s0 <= s1 and s0 -> s2, but s1 has no R-successor above s2.
    graph = np.array(
        [
            ["P,R", "P", "R"],
            ["0", "P,R", "0"],
            ["0", "0", "P,R"],
        ],
        dtype=object,
    )
    with pytest.raises(AssertionError, match="condition C1"):
        _check_inference_constraints(graph)


@pytest.mark.unit
def test_ictl_rejects_c2_violation():
    # s0 <= s1 and s1 -> s2, but s0 has no R-successor below s2.
    graph = np.array(
        [
            ["P,R", "P", "0"],
            ["0", "P,R", "R"],
            ["0", "0", "P,R"],
        ],
        dtype=object,
    )
    with pytest.raises(AssertionError, match="condition C2"):
        _check_inference_constraints(graph)


@pytest.mark.unit
def test_ictl_rejects_non_reflexive_preorder():
    graph = np.array([["P", "P,R"], ["P,R", "0"]], dtype=object)
    with pytest.raises(AssertionError, match="reflective"):
        check_conditions_hold(_minimal_ictl_data(graph))


@pytest.mark.unit
def test_ictl_rejects_non_serial_graph():
    graph = np.array([["0", "0"], ["P,R", "P,R"]], dtype=object)
    with pytest.raises(AssertionError, match="serial"):
        check_conditions_hold(_minimal_ictl_data(graph))
