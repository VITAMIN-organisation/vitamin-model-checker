"""The brute-force CapATL checker gives the hand-computed answers on small models."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.tests.helpers.capatl_reference import CapATLReference
from model_checker.tests.helpers.model_helpers import load_test_model

EXAMPLE = "capCGS/CAPATL/capatl_3agents_3states_example.txt"
ONE_CAPACITY = "capCGS/CAPATL/capatl_one_capacity_per_strategy.txt"

# Only values the depth-4 search settles; None marks a state it leaves open.
CASES = [
    (EXAMPLE, "<{1}>X g", {"q0": True, "q1": False, "q2": True}),
    (EXAMPLE, "<{3}>X g", {"q0": False, "q1": False, "q2": True}),
    (EXAMPLE, "<{1,2}>X g", {"q0": True, "q1": False, "q2": True}),
    (EXAMPLE, "<{1,2,3}>X g", {"q0": True, "q1": True, "q2": True}),
    (EXAMPLE, "<{1}>a U g", {"q0": True, "q1": True, "q2": True}),
    (EXAMPLE, "<{3}>a U g", {"q0": None, "q1": None, "q2": True}),
    (EXAMPLE, "<{1,3}>a R g", {"q0": False, "q1": False, "q2": True}),
    (EXAMPLE, "<{1,2}>F g", {"q0": True, "q1": True, "q2": True}),
    (EXAMPLE, "K1(1 is c)", {"q0": True, "q1": True, "q2": True}),
    (EXAMPLE, "K3(3 is cap)", {"q0": False, "q1": False, "q2": False}),
    (EXAMPLE, "<{1,2,3}>X K2(3 is cap)", {"q0": False, "q1": True, "q2": False}),
    (
        EXAMPLE,
        "<{1,2}>F (K2(3 is cap) || K2(3 is cop))",
        {"q0": True, "q1": True, "q2": None},
    ),
    (
        ONE_CAPACITY,
        "<{2}>(!lost U goal)",
        {"s0": False, "sL": True, "sR": True, "goal": True, "bad": False},
    ),
    (
        ONE_CAPACITY,
        "<{1,2}>(!lost U goal)",
        {"s0": True, "sL": True, "sR": True, "goal": True, "bad": False},
    ),
]


@pytest.mark.integration
@pytest.mark.semantic
@pytest.mark.parametrize("model_path,formula,expected", CASES)
def test_reference_matches_hand_computation(
    test_data_dir, model_path, formula, expected
):
    """The brute-force search gives the hand-computed states on both models."""
    cgs = load_test_model(test_data_dir, model_path)
    tree = FormulaParserFactory.get_parser_instance("CapATL").parse(
        formula, n_agent=cgs.get_number_of_agents()
    )
    assert CapATLReference(cgs, depth=4).satisfying_states(tree) == expected
