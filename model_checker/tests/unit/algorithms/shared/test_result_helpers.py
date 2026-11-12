"""Shared helpers every solver uses to turn state sets into results."""

import pytest

from model_checker.algorithms.explicit.shared.result_formatters import (
    initial_state_holds,
    states_of_result,
    verify_initial_state,
)
from model_checker.algorithms.explicit.shared.state_utils import (
    state_indices_to_names,
    state_names_to_indices,
)
from model_checker.algorithms.explicit.shared.verification_result import (
    StateTrace,
    VerificationResult,
)
from model_checker.tests.helpers.model_helpers import load_cgs_from_content
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content
from model_checker.utils.error_handler import (
    unresolved_leaves_error,
    value_error_to_response,
)
from model_checker.utils.literals import parse_state_set_literal


@pytest.fixture
def three_state_cgs(temp_file):
    content = build_cgs_model_content(
        transitions=[["I", "0", "0"], ["0", "I", "0"], ["0", "0", "I"]],
        state_names=["s0", "s1", "s2"],
        initial_state="s0",
        prop_names=["p"],
        labelling=[["0"], ["1"], ["0"]],
        num_agents=1,
    )
    return load_cgs_from_content(temp_file, content)


@pytest.mark.unit
def test_state_names_and_indices_round_trip(three_state_cgs):
    """Indices follow Name_State order, so s2 is 2 even when listed first."""
    cgs = three_state_cgs
    assert state_names_to_indices(cgs, ["s2", "s0"]) == {0, 2}
    assert state_indices_to_names(cgs, [2, 0]) == {"s0", "s2"}


@pytest.mark.unit
def test_unknown_state_name_or_index_is_an_error_naming_it(three_state_cgs):
    """A name or index the model lacks is a bug in the caller, not an empty result."""
    cgs = three_state_cgs
    with pytest.raises(IndexError, match="s9"):
        state_names_to_indices(cgs, ["s0", "s9"])
    with pytest.raises(IndexError, match="-1"):
        state_indices_to_names(cgs, [0, -1])


@pytest.mark.unit
def test_inner_ctl_result_reads_its_states_and_verdict():
    """LTL and NatATL read CTL results through these helpers while pruning."""
    result = {"res": "Result: ('s0', 's2')", "initial_state": "Initial state s0: True"}
    assert states_of_result(result, "p") == {"s0", "s2"}
    assert initial_state_holds(result, "p") is True


@pytest.mark.unit
@pytest.mark.parametrize("read", [states_of_result, initial_state_holds])
def test_inner_ctl_error_raises_instead_of_reading_as_empty_or_false(read):
    """An error from a nested CTL check would otherwise prune the model to nothing, or say False."""
    error = {
        "res": "Error: bad",
        "initial_state": "",
        "error": {"type": "syntax", "message": "bad"},
    }
    with pytest.raises(ValueError, match="Internal CTL check of 'A' failed: bad"):
        read(error, "A")


@pytest.mark.unit
def test_inner_error_keeps_its_type_for_the_outer_classifier():
    """A semantic error inside pruning stays semantic in the result the user sees."""
    error = {
        "res": "",
        "initial_state": "",
        "error": {"type": "semantic", "message": "x"},
    }
    with pytest.raises(ValueError) as raised:
        states_of_result(error, "p")
    assert value_error_to_response(str(raised.value))["error"]["type"] == "semantic"


@pytest.mark.unit
def test_result_without_a_state_set_raises():
    """A result that is not `Result: ...` must not read as the empty set."""
    with pytest.raises(ValueError, match="returned 'nonsense'"):
        states_of_result({"res": "nonsense", "initial_state": ""}, "p")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("leaves", "message"),
    [
        (
            {"p", "zz", "true"},
            "Proposition(s) 'zz' not among the model's declared propositions ['p']",
        ),
        ({"p", "true"}, "This logic does not evaluate the constant(s) 'true'"),
        ({"p"}, "This logic could not resolve the name(s) 'p' in the model"),
    ],
    ids=["undeclared_name", "unsupported_constant", "declared_but_unresolved"],
)
def test_unresolved_leaf_error_names_the_cause(leaves, message):
    """Undeclared names come first, then constants the logic cannot evaluate, then any other leaf."""
    error = unresolved_leaves_error(leaves, ["p"])["error"]
    assert (error["type"], error["message"]) == ("semantic", message)


@pytest.mark.unit
def test_trace_dict_is_the_shape_callers_read():
    """CTL returns this dict as `trace`; the Workbench reads states, type, description and cycle_start_index."""
    trace = StateTrace(
        states=["s0", "s1"],
        trace_type="counterexample",
        description="Violation found",
        cycle_start_index=1,
    )
    assert trace.to_dict() == {
        "states": ["s0", "s1"],
        "type": "counterexample",
        "description": "Violation found",
        "length": 2,
        "cycle_start_index": 1,
    }
    assert str(trace).startswith("Counterexample: s0 -> s1 -> (back to s1)")
    path = StateTrace(states=["s0", "s1"], trace_type="witness")
    assert path.to_dict()["cycle_start_index"] is None


@pytest.mark.unit
def test_lasso_must_loop_back_to_one_of_its_states():
    """A trace of two states has indices 0 and 1, so index 2 is refused by name."""
    with pytest.raises(ValueError, match="cycle_start_index 2 is outside the 2 states"):
        StateTrace(states=["s0", "s1"], trace_type="witness", cycle_start_index=2)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("states", "satisfied", "initial_line"),
    [
        ({"s0", "s1"}, True, "Initial state s0: True"),
        (set(), False, "Initial state s0: False"),
    ],
)
def test_compact_result_has_the_states_and_the_initial_verdict(
    states, satisfied, initial_line
):
    """The compact result is the standard {res, initial_state} pair, and res reads back as the state set."""
    compact = VerificationResult(
        states=states, satisfied=satisfied, initial_state="s0"
    ).to_compact_dict()
    assert set(compact) == {"res", "initial_state"}
    assert compact["initial_state"] == initial_line
    assert parse_state_set_literal(compact["res"].removeprefix("Result: ")) == states


@pytest.mark.unit
@pytest.mark.parametrize(
    ("initial", "result", "holds"),
    [
        ("s1", "('s10',)", False),
        ("s1", "('s10', 's1')", True),
        ("s0", "()", False),
        ("s0", "set()", False),
        ("s0", {"s0"}, True),
    ],
)
def test_initial_state_is_matched_as_a_whole_name(initial, result, holds):
    """`s1` is not in `('s10',)`: the result is parsed, not searched as text."""
    assert verify_initial_state(initial, result) is holds
