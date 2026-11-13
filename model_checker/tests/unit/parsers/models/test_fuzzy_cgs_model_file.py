"""Reading a fuzzyCGS model file: labels are numbers between 0 and 1."""

import pytest

from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_fuzzycgs_from_content,
)


def _load(temp_file, second_label):
    """A two-state fuzzyCGS whose labels for p are 1 and `second_label`."""
    content = build_cgs_model_content(
        transitions=[["III", "0"], ["0", "III"]],
        state_names=["s0", "s1"],
        initial_state="s0",
        prop_names=["p"],
        labelling=[["1"], [second_label]],
        num_agents=1,
    )
    return load_fuzzycgs_from_content(temp_file, content)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("label", "value"), [("0", 0.0), ("1", 1.0), ("0.25", 0.25), ("1.0", 1.0)]
)
def test_label_between_0_and_1_is_read_as_a_float(temp_file, label, value):
    """0 and 1 still load, so a Boolean CGS file is a valid fuzzyCGS file."""
    model = _load(temp_file, label)
    assert model.matrix_prop == [[1.0], [value]]


@pytest.mark.unit
@pytest.mark.parametrize("label", ["-0.1", "1.5", "abc", "nan", "inf"])
def test_label_outside_0_and_1_is_refused_with_its_position(temp_file, label):
    """ATLF computes !p as 1 - p, so 1.5 would give -0.5; the message gives the
    value, row and column."""
    with pytest.raises(
        ValueError,
        match=f"Invalid labelling matrix value: '{label}' at row 1, column 0",
    ):
        _load(temp_file, label)
