"""CTL semantics on small models: two-state cycles and deadlocks."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import _core_ctl_checking
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
    load_cgs_from_content,
)


def _assert_ctl_result(parser, formula, expected_states, error_msg=None):
    """Assert that the CTL formula yields exactly expected_states."""
    result = _core_ctl_checking(parser, formula)
    states = extract_states_from_result(result)
    if error_msg is None:
        error_msg = f"{formula} returned {states}, expected {expected_states}"
    assert states == expected_states, error_msg


def _build_two_state_cycle_content(state0_label, state1_label, initial_state="s0"):
    """Content string for 2-state cycle: s0 -> s1 -> s0."""
    return build_cgs_model_content(
        transitions=[["0", "AC"], ["AC", "0"]],
        state_names=["s0", "s1"],
        initial_state=initial_state,
        labelling=[state0_label, state1_label],
    )


def create_two_state_cycle_model(
    temp_file, state0_label, state1_label, initial_state="s0"
):
    """Build a CGS parser for the 2-state cycle s0 -> s1 -> s0."""
    content = _build_two_state_cycle_content(
        state0_label, state1_label, initial_state=initial_state
    )
    return load_cgs_from_content(temp_file, content)


def create_deadlock_model(
    temp_file, transitions, state_names, labelling, initial_state="s0"
):
    """Build a CGS parser from given transition matrix and labelling."""
    content = build_cgs_model_content(
        transitions=transitions,
        state_names=state_names,
        initial_state=initial_state,
        labelling=labelling,
    )
    return load_cgs_from_content(temp_file, content)


@pytest.mark.integration
@pytest.mark.edge_case
@pytest.mark.model_checking
class TestCTLCycles:
    """CTL two-state cycle: EG/AG/EF under alternating labelling."""

    @pytest.mark.parametrize(
        "state0_label, state1_label, expected_eg, expected_ag, expected_ef, description",
        [(["1"], ["0"], set(), None, {"s0", "s1"}, "alternating property")],
    )
    def test_two_state_cycle_variants(
        self,
        temp_file,
        state0_label,
        state1_label,
        expected_eg,
        expected_ag,
        expected_ef,
        description,
    ):
        """Test 2-state cycles under different labellings."""
        parser = create_two_state_cycle_model(temp_file, state0_label, state1_label)

        if expected_eg is not None:
            _assert_ctl_result(
                parser,
                "EG p",
                expected_eg,
                f"EG p mismatch for 2-state cycle ({description})",
            )
        if expected_ag is not None:
            _assert_ctl_result(
                parser,
                "AG p",
                expected_ag,
                f"AG p mismatch for 2-state cycle ({description})",
            )
        if expected_ef is not None:
            _assert_ctl_result(
                parser,
                "EF p",
                expected_ef,
                f"EF p mismatch for 2-state cycle ({description})",
            )


@pytest.mark.edge_case
@pytest.mark.model_checking
class TestCTLDeadlockStates:
    """CTL AX/AG on model with deadlock states."""

    @pytest.mark.parametrize(
        "transitions, state_names, labelling, expected_ax, expected_ag, description",
        [
            (
                [
                    ["0", "AC", "BC"],
                    ["0", "0", "0"],
                    ["0", "0", "0"],
                ],
                ["s0", "s1", "s2"],
                [["0"], ["1"], ["0"]],
                {"s1", "s2"},
                {"s1"},
                "two deadlocks reachable from s0",
            ),
        ],
    )
    def test_deadlock_models(
        self,
        temp_file,
        transitions,
        state_names,
        labelling,
        expected_ax,
        expected_ag,
        description,
    ):
        """Test models with deadlock states across scenarios."""
        parser = create_deadlock_model(
            temp_file,
            transitions=transitions,
            state_names=state_names,
            labelling=labelling,
        )

        _assert_ctl_result(
            parser, "AX p", expected_ax, f"AX p mismatch ({description})"
        )
        _assert_ctl_result(
            parser, "AG p", expected_ag, f"AG p mismatch ({description})"
        )
