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
    model.states = ["s0", "s1"]
    model.atomic_propositions = ["p"]
    model.matrix_prop = np.array([[1], [1]], dtype=int)
    return model


@pytest.mark.unit
def test_ictl_rejects_non_antisymmetric_preorder():
    graph = np.array([["P,R", "P"], ["P", "P,R"]], dtype=object)
    with pytest.raises(AssertionError, match="antisymmetric"):
        check_conditions_hold(_minimal_ictl_data(graph))


@pytest.mark.unit
def test_ictl_rejects_c1_c2_violation():
    graph = np.array([["P,R", "P,R"], ["P,R", "P,R"]], dtype=object)
    with pytest.raises(AssertionError, match="C1 and C2"):
        _check_inference_constraints(graph)


@pytest.mark.unit
def test_ictl_rejects_c3_violation():
    graph = np.array(
        [["R", "R", "R"], ["R", "R", "R"], ["R", "R", "R"]],
        dtype=object,
    )
    with pytest.raises(AssertionError, match="condition C3"):
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
