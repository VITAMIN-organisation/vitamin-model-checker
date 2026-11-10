"""Shared helpers every solver uses to turn state sets into results."""

import pytest

from model_checker.algorithms.explicit.shared.result_formatters import (
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
from model_checker.utils.literals import parse_state_set_literal


@pytest.mark.unit
def test_state_names_and_indices_round_trip(temp_file):
    """Indices follow Name_State order, so s2 is 2 even when listed first."""
    content = build_cgs_model_content(
        transitions=[["I", "0", "0"], ["0", "I", "0"], ["0", "0", "I"]],
        state_names=["s0", "s1", "s2"],
        initial_state="s0",
        prop_names=["p"],
        labelling=[["0"], ["1"], ["0"]],
        num_agents=1,
    )
    cgs = load_cgs_from_content(temp_file, content)
    assert state_names_to_indices(cgs, ["s2", "s0"]) == {0, 2}
    assert state_indices_to_names(cgs, [2, 0]) == {"s0", "s2"}


@pytest.mark.unit
def test_trace_dict_is_the_shape_callers_read():
    """CTL returns this dict as `trace`; the Workbench reads states, type, description and length."""
    trace = StateTrace(
        states=["s0", "s1"], trace_type="counterexample", description="Violation found"
    )
    assert trace.to_dict() == {
        "states": ["s0", "s1"],
        "type": "counterexample",
        "description": "Violation found",
        "length": 2,
    }


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
